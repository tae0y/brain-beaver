import logging
from opentelemetry import metrics, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

def configure_oltp_grpc_tracing(endpoint: str = None) -> trace.Tracer:
    # 리소스 설정
    resource = Resource.create({
        "service.name": "python-fastapi-service",
        "service.instance.id": "instance-1"
    })

    # 트레이스 설정
    trace_provider = TracerProvider(resource=resource)
    otlp_span_exporter = OTLPSpanExporter(endpoint=endpoint)
    span_processor = BatchSpanProcessor(otlp_span_exporter)
    trace_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(trace_provider)

    # 메트릭 설정
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint)
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # 로깅 설정
    logger_provider = LoggerProvider(resource=resource)
    set_logger_provider(logger_provider)

    otlp_log_exporter = OTLPLogExporter(endpoint=endpoint)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(otlp_log_exporter)
    )
    
    handler = LoggingHandler(
        level=logging.NOTSET,
        logger_provider=logger_provider
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] - %(message)s")
    )

    # 루트 로거에 핸들러 추가
    logging.getLogger().addHandler(handler)

    return trace.get_tracer(__name__)