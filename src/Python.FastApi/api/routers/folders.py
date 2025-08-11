"""
폴더 관련 API 라우터

파일 시스템 스캔 및 처리 API를 제공합니다.
"""

from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from core.database import get_db_session_dependency
from core.logging import get_logger, log_context_manager
from schemas.jobs import FolderScanRequest, FolderProcessRequest, JobResponse
from schemas.common import ResponseDTO
from pipeline.orchestrator import PipelineOrchestrator, PipelineConfig
from pipeline.steps.summarize import SummaryType
from domain.documents.repository import DocumentRepository

router = APIRouter(prefix="/folders", tags=["Folders"])
logger = get_logger(__name__)
orchestrator = PipelineOrchestrator()


@router.post("/scan", response_model=ResponseDTO[JobResponse])
async def scan_folder(
    request: FolderScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session_dependency)
):
    """
    폴더 스캔 API
    
    지정된 폴더를 스캔하여 처리 대상 파일들을 데이터베이스에 등록합니다.
    """
    try:
        with log_context_manager(
            operation="folder_scan",
            root_path=request.root_path,
            recursive=request.recursive
        ):
            logger.info("Starting folder scan", extra={
                "root_path": request.root_path,
                "recursive": request.recursive
            })
            
            # 비동기 스캔 작업 시작
            job_id = await orchestrator.scan_folder(
                root_path=request.root_path,
                recursive=request.recursive
            )
            
            # 작업 상태 조회
            job_status = orchestrator.get_job_status(job_id)
            if not job_status:
                raise HTTPException(status_code=500, detail="Failed to create scan job")
            
            logger.info("Folder scan job created", extra={
                "job_id": job_id,
                "root_path": request.root_path
            })
            
            return ResponseDTO(
                status="success",
                message="Folder scan started successfully",
                data=JobResponse(**job_status)
            )
            
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Folder not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied to access folder")
    except Exception as e:
        logger.error(f"Folder scan failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Folder scan failed: {str(e)}")


@router.post("/process", response_model=ResponseDTO[JobResponse])
async def process_folder(
    request: FolderProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session_dependency)
):
    """
    폴더 처리 API
    
    스캔된 파일들을 처리하여 청크, 요약, 임베딩을 생성합니다.
    """
    try:
        with log_context_manager(
            operation="folder_process",
            root_path=request.root_path,
            batch_size=request.batch_size
        ):
            logger.info("Starting folder processing", extra={
                "root_path": request.root_path,
                "chunking_strategy": request.chunking_strategy,
                "generate_summaries": request.generate_summaries,
                "generate_embeddings": request.generate_embeddings,
                "batch_size": request.batch_size,
                "max_concurrent": request.max_concurrent
            })
            
            # 처리 설정 구성
            config = PipelineConfig(
                chunking_strategy=request.chunking_strategy,
                summary_type=SummaryType.BRIEF,
                generate_embeddings=request.generate_embeddings,
                generate_summaries=request.generate_summaries,
                batch_size=request.batch_size,
                max_concurrent=request.max_concurrent
            )
            
            # 비동기 처리 작업 시작
            job_id = await orchestrator.process_folder(
                root_path=request.root_path,
                config=config
            )
            
            # 작업 상태 조회
            job_status = orchestrator.get_job_status(job_id)
            if not job_status:
                raise HTTPException(status_code=500, detail="Failed to create process job")
            
            logger.info("Folder processing job created", extra={
                "job_id": job_id,
                "root_path": request.root_path
            })
            
            return ResponseDTO(
                status="success",
                message="Folder processing started successfully",
                data=JobResponse(**job_status)
            )
            
    except Exception as e:
        logger.error(f"Folder processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Folder processing failed: {str(e)}")


@router.get("/status", response_model=ResponseDTO[dict])
async def get_folder_status(
    path: str = None,
    db: Session = Depends(get_db_session_dependency)
):
    """
    폴더 상태 조회 API
    
    지정된 폴더 또는 전체 문서의 처리 상태를 조회합니다.
    """
    try:
        doc_repo = DocumentRepository(db)
        
        if path:
            documents = doc_repo.find_by_path_prefix(path)
        else:
            # 전체 통계
            stats = doc_repo.get_statistics()
            
            return ResponseDTO(
                status="success",
                message="Document statistics retrieved",
                data=stats
            )
        
        # 경로별 통계
        status_counts = {}
        for doc in documents:
            status = doc.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        folder_stats = {
            "path": path,
            "total_documents": len(documents),
            "by_status": status_counts,
            "recent_documents": [
                {
                    "id": doc.id,
                    "uri": doc.uri,
                    "status": doc.status,
                    "updated_at": doc.updated_at.isoformat()
                }
                for doc in sorted(documents, key=lambda x: x.updated_at, reverse=True)[:10]
            ]
        }
        
        return ResponseDTO(
            status="success",
            message="Folder status retrieved",
            data=folder_stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get folder status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get folder status: {str(e)}")


@router.delete("/reset", response_model=ResponseDTO[dict])
async def reset_folder(
    path: str,
    confirm: bool = False,
    db: Session = Depends(get_db_session_dependency)
):
    """
    폴더 리셋 API
    
    지정된 폴더의 모든 처리 결과를 삭제하고 상태를 초기화합니다.
    (개발/테스트 환경에서만 사용)
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="This operation requires confirmation. Set confirm=true"
        )
    
    try:
        doc_repo = DocumentRepository(db)
        documents = doc_repo.find_by_path_prefix(path)
        
        reset_count = 0
        for doc in documents:
            # 문서 상태를 pending으로 리셋
            doc_repo.update_status(doc.id, "pending")
            reset_count += 1
        
        logger.info(f"Reset {reset_count} documents in path: {path}")
        
        return ResponseDTO(
            status="success",
            message=f"Reset {reset_count} documents",
            data={
                "path": path,
                "reset_count": reset_count
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to reset folder: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to reset folder: {str(e)}")