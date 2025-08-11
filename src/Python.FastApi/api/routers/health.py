"""
헬스 체크 API 라우터

시스템 상태 모니터링을 위한 엔드포인트를 제공합니다.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from core.config import settings
from core.database import db_manager
from core.logging import get_logger, metrics
from core.llm_setup import health_check_providers
from schemas.common import HealthCheckResponse, MetricsResponse, ResponseDTO

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)


@router.get("/healthz", response_model=HealthCheckResponse)
async def liveness_check():
    """
    Liveness 체크 (Kubernetes 준비)
    
    애플리케이션이 살아있고 기본적인 기능이 작동하는지 확인합니다.
    """
    try:
        timestamp = datetime.utcnow().isoformat()
        
        # 기본 서비스 상태 확인
        services = {
            "api": {"status": "healthy", "timestamp": timestamp}
        }
        
        # 데이터베이스 연결 확인
        try:
            db_healthy = db_manager.check_connection()
            services["database"] = {
                "status": "healthy" if db_healthy else "unhealthy",
                "connection": db_healthy
            }
        except Exception as e:
            services["database"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
        
        # 전체 상태 결정
        overall_status = "healthy" if all(
            service.get("status") == "healthy" 
            for service in services.values()
        ) else "unhealthy"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=timestamp,
            version=settings.app_version,
            services=services
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/readyz", response_model=HealthCheckResponse)
async def readiness_check():
    """
    Readiness 체크 (Kubernetes 준비)
    
    애플리케이션이 요청을 받을 준비가 되었는지 확인합니다.
    """
    try:
        timestamp = datetime.utcnow().isoformat()
        
        services = {
            "api": {"status": "ready", "timestamp": timestamp}
        }
        
        # 데이터베이스 준비 상태
        try:
            db_healthy = db_manager.check_connection()
            services["database"] = {
                "status": "ready" if db_healthy else "not_ready",
                "connection": db_healthy
            }
            
            # 테이블 존재 여부 확인
            from core.database import DatabaseOperations
            tables_exist = (
                DatabaseOperations.check_table_exists("documents") and
                DatabaseOperations.check_table_exists("jobs") and
                DatabaseOperations.check_table_exists("chunks")
            )
            services["database"]["tables_ready"] = tables_exist
            
            if not tables_exist:
                services["database"]["status"] = "not_ready"
                
        except Exception as e:
            services["database"] = {
                "status": "not_ready",
                "error": str(e)
            }
        
        # LLM 프로바이더 준비 상태
        try:
            llm_health = await health_check_providers()
            healthy_providers = sum(
                1 for result in llm_health.values() 
                if result.get("available", False)
            )
            
            services["llm_providers"] = {
                "status": "ready" if healthy_providers > 0 else "not_ready",
                "healthy_providers": healthy_providers,
                "total_providers": len(llm_health),
                "details": llm_health
            }
            
        except Exception as e:
            services["llm_providers"] = {
                "status": "not_ready",
                "error": str(e)
            }
        
        # 전체 준비 상태 결정
        overall_status = "ready" if all(
            service.get("status") == "ready"
            for service in services.values()
        ) else "not_ready"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=timestamp,
            version=settings.app_version,
            services=services
        )
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Readiness check failed")


@router.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """
    Prometheus 메트릭 엔드포인트
    
    시스템 메트릭을 Prometheus 형식으로 반환합니다.
    """
    try:
        if not settings.enable_metrics:
            raise HTTPException(status_code=404, detail="Metrics disabled")
        
        metrics_text = metrics.get_metrics()
        return PlainTextResponse(content=metrics_text, media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@router.get("/status", response_model=ResponseDTO[dict])
async def get_system_status():
    """
    시스템 상태 종합 정보
    
    전체 시스템의 상태를 종합적으로 제공합니다.
    """
    try:
        # 기본 정보
        system_info = {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # 설정 정보 (민감한 정보 제외)
        config_info = {
            "parallel_workers": settings.parallel_workers,
            "batch_size": settings.batch_size,
            "llm_provider": settings.llm_provider.value,
            "enable_metrics": settings.enable_metrics,
            "log_level": settings.log_level
        }
        
        # 데이터베이스 상태
        db_info = {"connected": False, "error": None}
        try:
            db_info["connected"] = db_manager.check_connection()
            
            if db_info["connected"]:
                from core.database import DatabaseOperations
                db_info["document_count"] = DatabaseOperations.get_table_row_count("documents")
                db_info["job_count"] = DatabaseOperations.get_table_row_count("jobs")
                
        except Exception as e:
            db_info["error"] = str(e)
        
        # LLM 프로바이더 상태
        llm_info = {}
        try:
            from core.llm_setup import get_provider_status
            llm_info = get_provider_status()
        except Exception as e:
            llm_info = {"error": str(e)}
        
        # Job 통계
        job_stats = {}
        try:
            from domain.jobs.models import JobManager
            job_manager = JobManager()
            job_stats = job_manager.get_job_statistics()
        except Exception as e:
            job_stats = {"error": str(e)}
        
        return ResponseDTO(
            status="success",
            message="System status retrieved",
            data={
                "system": system_info,
                "config": config_info,
                "database": db_info,
                "llm_providers": llm_info,
                "job_statistics": job_stats
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get system status")


@router.get("/version", response_model=ResponseDTO[dict])
async def get_version():
    """
    애플리케이션 버전 정보
    """
    return ResponseDTO(
        status="success",
        message="Version information",
        data={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value
        }
    )