import os
import logging
import uvicorn
from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware
from concepts.conceptshandler import router as concepts_router
from networks.networkshandler import router as networks_router
from references.referenceshandler import router as references_router
from extract.extracthandler import router as extract_router

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

from prometheus_client import Histogram

# ************************************************************
# App 정의
# 
# ************************************************************
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


# ************************************************************
# App 미들웨어, 라우터 등록
# 
# ************************************************************
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

resource = Resource(attributes={"service.name": "Python.FastAPI"})

# set the tracer provider
tracer = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer)

# Use the OTLPSpanExporter to send traces to Tempo
endpoint = "bws_tempo:4317"
endpoint_http = "http://bws_tempo:4318/v1/trace"
tracer.add_span_processor(BatchSpanProcessor(
    OTLPSpanExporter(
        endpoint=endpoint,
        insecure=True,
    )
))

LoggingInstrumentor().instrument(set_logging_format=True)
FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)


# ************************************************************
# Home Page
# 
# ************************************************************
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