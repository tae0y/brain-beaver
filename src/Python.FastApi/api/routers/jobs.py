"""
Job 관련 API 라우터

작업 상태 조회, 관리 API를 제공합니다.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db_session_dependency
from core.logging import get_logger
from schemas.jobs import JobResponse, JobListResponse, JobStatistics
from schemas.common import ResponseDTO
from pipeline.orchestrator import PipelineOrchestrator
from domain.jobs.models import JobManager, JobKind, JobState

router = APIRouter(prefix="/jobs", tags=["Jobs"])
logger = get_logger(__name__)
orchestrator = PipelineOrchestrator()
job_manager = JobManager()


@router.get("", response_model=ResponseDTO[JobListResponse])
async def list_jobs(
    kind: Optional[JobKind] = Query(None, description="작업 유형 필터"),
    state: Optional[JobState] = Query(None, description="작업 상태 필터"),
    limit: int = Query(50, ge=1, le=200, description="최대 조회 수"),
    offset: int = Query(0, ge=0, description="시작 위치"),
    db: Session = Depends(get_db_session_dependency)
):
    """
    작업 목록 조회 API
    
    등록된 작업들의 목록을 조회합니다.
    """
    try:
        from core.models import Job as JobModel
        
        query = db.query(JobModel)
        
        # 필터 적용
        if kind:
            query = query.filter(JobModel.kind == kind.value)
        
        if state:
            query = query.filter(JobModel.state == state.value)
        
        # 정렬 및 페이징
        query = query.order_by(JobModel.created_at.desc())
        total = query.count()
        jobs = query.offset(offset).limit(limit).all()
        
        # 활성 작업 수 계산
        active_jobs = db.query(JobModel).filter(
            JobModel.state == JobState.RUNNING.value
        ).count()
        
        # 응답 데이터 구성
        job_responses = []
        for job in jobs:
            job_data = orchestrator.get_job_status(job.id)
            if job_data:
                job_responses.append(JobResponse(**job_data))
        
        return ResponseDTO(
            status="success",
            message="Jobs retrieved successfully",
            data=JobListResponse(
                jobs=job_responses,
                total=total,
                active=active_jobs
            )
        )
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.get("/{job_id}", response_model=ResponseDTO[JobResponse])
async def get_job(
    job_id: int,
    db: Session = Depends(get_db_session_dependency)
):
    """
    단일 작업 조회 API
    
    지정된 작업의 상세 정보를 조회합니다.
    """
    try:
        job_status = orchestrator.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return ResponseDTO(
            status="success",
            message="Job retrieved successfully",
            data=JobResponse(**job_status)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get job: {str(e)}")


@router.post("/{job_id}/cancel", response_model=ResponseDTO[dict])
async def cancel_job(
    job_id: int,
    db: Session = Depends(get_db_session_dependency)
):
    """
    작업 취소 API
    
    실행 중이거나 대기 중인 작업을 취소합니다.
    """
    try:
        success = orchestrator.cancel_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="Job cannot be canceled (not found or already finished)"
            )
        
        logger.info(f"Job canceled", extra={"job_id": job_id})
        
        return ResponseDTO(
            status="success",
            message="Job canceled successfully",
            data={"job_id": job_id, "canceled": True}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get("/active/list", response_model=ResponseDTO[List[JobResponse]])
async def list_active_jobs():
    """
    활성 작업 목록 조회 API
    
    현재 실행 중인 작업들의 목록을 조회합니다.
    """
    try:
        active_jobs_data = orchestrator.get_active_jobs()
        active_jobs = [JobResponse(**job_data) for job_data in active_jobs_data]
        
        return ResponseDTO(
            status="success",
            message="Active jobs retrieved successfully",
            data=active_jobs
        )
        
    except Exception as e:
        logger.error(f"Failed to list active jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list active jobs: {str(e)}")


@router.get("/statistics/summary", response_model=ResponseDTO[JobStatistics])
async def get_job_statistics(
    db: Session = Depends(get_db_session_dependency)
):
    """
    작업 통계 조회 API
    
    전체 작업에 대한 통계 정보를 제공합니다.
    """
    try:
        stats = job_manager.get_job_statistics(db)
        
        return ResponseDTO(
            status="success",
            message="Job statistics retrieved successfully",
            data=JobStatistics(**stats)
        )
        
    except Exception as e:
        logger.error(f"Failed to get job statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get job statistics: {str(e)}")


@router.delete("/cleanup", response_model=ResponseDTO[dict])
async def cleanup_old_jobs(
    older_than_days: int = Query(7, ge=1, le=365, description="보관 기간 (일)"),
    confirm: bool = Query(False, description="삭제 확인"),
    db: Session = Depends(get_db_session_dependency)
):
    """
    오래된 작업 정리 API
    
    지정된 기간보다 오래된 완료/실패 작업들을 삭제합니다.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="This operation requires confirmation. Set confirm=true"
        )
    
    try:
        # 삭제 전 통계 확인
        from core.models import Job as JobModel
        from sqlalchemy import and_
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        
        count_query = db.query(JobModel).filter(
            and_(
                JobModel.state.in_([JobState.SUCCEEDED.value, JobState.FAILED.value]),
                JobModel.finished_at < cutoff_date
            )
        )
        
        jobs_to_delete = count_query.count()
        
        # 실제 삭제 수행
        job_manager.cleanup_finished_jobs(older_than_days, db)
        
        logger.info(f"Cleaned up {jobs_to_delete} old jobs", extra={
            "older_than_days": older_than_days,
            "cutoff_date": cutoff_date.isoformat()
        })
        
        return ResponseDTO(
            status="success",
            message=f"Cleaned up {jobs_to_delete} old jobs",
            data={
                "deleted_jobs": jobs_to_delete,
                "older_than_days": older_than_days,
                "cutoff_date": cutoff_date.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to cleanup old jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to cleanup old jobs: {str(e)}")