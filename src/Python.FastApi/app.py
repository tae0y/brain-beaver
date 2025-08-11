import os
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from concepts.conceptshandler import router as concepts_router
from networks.networkshandler import router as networks_router
from references.referenceshandler import router as references_router
from extract.extracthandler import router as extract_router

# New imports for the reimplemented system
from core.config import settings, create_temp_dirs
from core.database import init_database, close_database
from core.logging import init_observability
from core.llm_setup import initialize_llm_providers
from api.routers import folders, jobs, health

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

from prometheus_client import Histogram

# ************************************************************
# Lifespan 이벤트 관리
# 
# ************************************************************
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Starting BrainBeaver application...")
    
    try:
        # 1. 관측성 시스템 초기화
        init_observability()
        
        # 2. 임시 디렉토리 생성
        create_temp_dirs(settings)
        
        # 3. 데이터베이스 초기화
        init_database()
        
        # 4. LLM 프로바이더 초기화
        initialize_llm_providers()
        
        logging.info("BrainBeaver application started successfully")
        
    except Exception as e:
        logging.error(f"Failed to initialize application: {e}")
        raise
    
    yield  # 애플리케이션 실행
    
    # Shutdown
    logging.info("Shutting down BrainBeaver application...")
    try:
        close_database()
        logging.info("Application shutdown completed")
    except Exception as e:
        logging.error(f"Error during shutdown: {e}")


# ************************************************************
# App 정의
# 
# ************************************************************
tags_metadata = [
    {"name": "Health", "description": "시스템 헬스 체크 및 모니터링"},
    {"name": "Folders", "description": "파일 시스템 스캔 및 처리"},
    {"name": "Jobs", "description": "비동기 작업 관리"},
    {"name": "Extract", "description": "데이터 추출과 관련된 요청을 처리한다."},
    {"name": "Networks", "description": "네트워크 관련 CRUD 요청을 처리한다."},
    {"name": "References", "description": "참고자료 관련 CRUD 요청을 처리한다."},
    {"name": "Concepts", "description": "주요개념 관련 CRUD 요청을 처리한다."}
]

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Knowledge graph processing system with incremental file processing and web crawling",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)


# ************************************************************
# App 미들웨어, 라우터 등록
# 
# ************************************************************
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# New API routers (reimplemented system)
app.include_router(health.router)
app.include_router(folders.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")

# Legacy API routers (existing system)
app.include_router(concepts_router)
app.include_router(networks_router)
app.include_router(references_router)
app.include_router(extract_router)


# ************************************************************
# App 로깅, 모니터링 설정
# 
# - OpenTelemetry 활용방안
#   - [ ] Grafana + Prometheus + Loki + Tempo
#   - [ ] OpenTelemetry Collector + Something Behind
#   - [ ] Something Ahead + Aspire Dashboard
# - refered from https://github.com/blueswen/fastapi-observability/tree/main
# ************************************************************
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#resource = Resource(attributes={"service.name": "Python.FastAPI"})
#
## set the tracer provider
#tracer = TracerProvider(resource=resource)
#trace.set_tracer_provider(tracer)
#
## Use the OTLPSpanExporter to send traces to Tempo
#endpoint = "bws_tempo:4317"
#endpoint_http = "http://bws_tempo:4318/v1/trace"
#tracer.add_span_processor(BatchSpanProcessor(
#    OTLPSpanExporter(
#        endpoint=endpoint,
#        insecure=True,
#    )
#))
#
#LoggingInstrumentor().instrument(set_logging_format=True)
#FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)


# ************************************************************
# Home Page
# 
# ************************************************************
@app.get("/")
def rootPage() -> dict:
    logger.info("HOME PAGE ACCESS")
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment.value,
        "message": "BrainBeaver Knowledge Graph Processing System"
    }

if __name__ == "__main__":
    """
    디버깅을 위해 역으로 파이썬 안에서 Uvicorn을 호출한다.
    """
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.environ.get("UVICORN_PORT", 8111)),
        reload=True
    )