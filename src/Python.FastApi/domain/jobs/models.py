"""
Job 도메인 모델 및 상태 관리

비동기 작업의 생명주기를 관리합니다.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.orm import Session

from core.models import Job as JobModel
from core.database import get_db_session
from core.logging import get_logger

logger = get_logger(__name__)


class JobKind(str, Enum):
    """작업 유형"""
    SCAN = "scan"       # 파일 스캔
    PROCESS = "process" # 파일 처리
    CRAWL = "crawl"     # 웹 크롤링


class JobState(str, Enum):
    """작업 상태"""
    QUEUED = "queued"       # 대기 중
    RUNNING = "running"     # 실행 중
    SUCCEEDED = "succeeded" # 성공
    FAILED = "failed"       # 실패
    CANCELED = "canceled"   # 취소됨


@dataclass
class JobProgress:
    """작업 진행 상황"""
    current: int
    total: int
    succeeded: int
    failed: int
    
    @property
    def progress_percent(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100
    
    @property
    def success_rate(self) -> float:
        if self.current == 0:
            return 0.0
        return (self.succeeded / self.current) * 100


class JobManager:
    """Job 생명주기 관리"""
    
    def __init__(self):
        pass
    
    def create_job(self, kind: JobKind, params: Dict[str, Any], session: Session = None) -> JobModel:
        """새 작업 생성"""
        with (session or get_db_session()) as db:
            job = JobModel(
                kind=kind.value,
                params=params,
                state=JobState.QUEUED.value,
                progress=0.0,
                total=0,
                succeeded=0,
                failed=0,
                created_at=datetime.utcnow()
            )
            
            db.add(job)
            db.commit()
            db.refresh(job)
            
            logger.info(f"Job created", extra={
                "job_id": job.id,
                "kind": kind.value,
                "params": params
            })
            
            return job
    
    def get_job(self, job_id: int, session: Session = None) -> Optional[JobModel]:
        """작업 조회"""
        with (session or get_db_session()) as db:
            return db.query(JobModel).filter(JobModel.id == job_id).first()
    
    def update_job_state(self, job_id: int, state: JobState, error: str = None, session: Session = None):
        """작업 상태 업데이트"""
        with (session or get_db_session()) as db:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if job:
                old_state = job.state
                job.state = state.value
                job.error = error
                
                if state == JobState.RUNNING and not job.started_at:
                    job.started_at = datetime.utcnow()
                elif state in [JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELED]:
                    job.finished_at = datetime.utcnow()
                
                db.commit()
                
                logger.info(f"Job state updated", extra={
                    "job_id": job_id,
                    "old_state": old_state,
                    "new_state": state.value,
                    "error": error
                })
    
    def update_job_progress(self, job_id: int, progress: JobProgress, session: Session = None):
        """작업 진행률 업데이트"""
        with (session or get_db_session()) as db:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if job:
                job.progress = progress.progress_percent / 100.0
                job.total = progress.total
                job.succeeded = progress.succeeded
                job.failed = progress.failed
                
                db.commit()
    
    def get_pending_jobs(self, kind: JobKind = None, limit: int = None, session: Session = None) -> List[JobModel]:
        """대기 중인 작업 목록"""
        with (session or get_db_session()) as db:
            query = db.query(JobModel).filter(JobModel.state == JobState.QUEUED.value)
            
            if kind:
                query = query.filter(JobModel.kind == kind.value)
            
            query = query.order_by(JobModel.created_at)
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
    
    def get_active_jobs(self, session: Session = None) -> List[JobModel]:
        """실행 중인 작업 목록"""
        with (session or get_db_session()) as db:
            return db.query(JobModel).filter(JobModel.state == JobState.RUNNING.value).all()
    
    def cancel_job(self, job_id: int, session: Session = None) -> bool:
        """작업 취소"""
        with (session or get_db_session()) as db:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if job and job.state in [JobState.QUEUED.value, JobState.RUNNING.value]:
                job.state = JobState.CANCELED.value
                job.finished_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Job canceled", extra={"job_id": job_id})
                return True
            return False
    
    def cleanup_finished_jobs(self, older_than_days: int = 7, session: Session = None):
        """완료된 작업 정리"""
        with (session or get_db_session()) as db:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            
            deleted = db.query(JobModel).filter(
                JobModel.state.in_([JobState.SUCCEEDED.value, JobState.FAILED.value]),
                JobModel.finished_at < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"Cleaned up {deleted} old jobs")
    
    def get_job_statistics(self, session: Session = None) -> Dict[str, Any]:
        """작업 통계"""
        from sqlalchemy import func
        
        with (session or get_db_session()) as db:
            # 상태별 카운트
            state_stats = dict(
                db.query(JobModel.state, func.count(JobModel.id))
                .group_by(JobModel.state)
                .all()
            )
            
            # 종류별 카운트
            kind_stats = dict(
                db.query(JobModel.kind, func.count(JobModel.id))
                .group_by(JobModel.kind)
                .all()
            )
            
            # 최근 완료 작업의 평균 실행 시간
            recent_jobs = db.query(JobModel).filter(
                JobModel.state == JobState.SUCCEEDED.value,
                JobModel.started_at.isnot(None),
                JobModel.finished_at.isnot(None)
            ).order_by(JobModel.finished_at.desc()).limit(100).all()
            
            avg_duration = 0
            if recent_jobs:
                durations = [
                    (job.finished_at - job.started_at).total_seconds()
                    for job in recent_jobs
                ]
                avg_duration = sum(durations) / len(durations)
            
            return {
                "by_state": state_stats,
                "by_kind": kind_stats,
                "total_jobs": sum(state_stats.values()),
                "active_jobs": state_stats.get(JobState.RUNNING.value, 0),
                "avg_duration_seconds": round(avg_duration, 2)
            }