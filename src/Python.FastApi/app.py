import os
import logging
import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from common.system.otlp_tracing import configure_oltp_grpc_tracing as configure_otel_otlp
from concepts.conceptshandler import router as concepts_router
from networks.networkshandler import router as networks_router
from references.referenceshandler import router as references_router
from extract.extracthandler import router as extract_router

tags_metadata = [
    {"name":"Extract", "description":"데이터 추출과 관련된 요청을 처리한다."},
    {"name":"Networks", "description":"네트워크 관련 CRUD 요청을 처리한다."},
    {"name":"References", "description":"참고자료 관련 CRUD 요청을 처리한다."},
    {"name":"Concepts", "description":"주요개념 관련 CRUD 요청을 처리한다."}
]
app = FastAPI(
    openapi_tags= tags_metadata,
    #root_path="/swagger"
)

origins = [
    "http://127.0.0.1:8111"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(concepts_router)
app.include_router(networks_router)
app.include_router(references_router)
app.include_router(extract_router)

logging.basicConfig(level=logging.INFO)
tracer = configure_otel_otlp(
    endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:18889")
)
logger = logging.getLogger(__name__)

# FastAPI OpenTelemetry 계측 활성화
FastAPIInstrumentor.instrument_app(app)

@app.get("/")
def rootPage() -> str:
    logger.info("HOME PAGE ACCESS")
    return "Python.FastAPI Backend Server"

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