"""
로깅 및 관측성 시스템

구조화된 로깅과 메트릭 수집을 통해 운영 관측성을 제공합니다.
- JSON 형태의 구조화 로그
- Prometheus 메트릭 수집
- OpenTelemetry 분산 추적 (선택사항)
- 성능 및 에러 모니터링
"""

import json
import time
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime
from functools import wraps
from contextlib import contextmanager

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from prometheus_client.metrics import MetricWrapperBase

from core.config import settings


class JSONFormatter(logging.Formatter):
    """
    JSON 형태의 로그 포매터
    
    구조화된 로그 메시지를 생성하여 로그 분석을 용이하게 합니다.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        # 기본 로그 정보
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 예외 정보 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 추가 필드들 병합 (extra 파라미터로 전달된 것들)
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message'):
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """
    텍스트 형태의 로그 포매터 (개발용)
    """
    
    def __init__(self):
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        super().__init__(fmt)


def setup_logging():
    """
    애플리케이션 로깅 설정
    
    설정에 따라 JSON 또는 텍스트 형태의 로그를 구성합니다.
    """
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 콘솔 핸들러 생성
    console_handler = logging.StreamHandler(sys.stdout)
    
    # 포맷터 설정
    if settings.log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logging.info("Logging system initialized", extra={
        "log_level": settings.log_level,
        "log_format": settings.log_format
    })


class LogContext:
    """
    로그 컨텍스트 관리
    
    요청/작업별 공통 정보를 로그에 자동으로 포함시킵니다.
    """
    
    def __init__(self):
        self.context: Dict[str, Any] = {}
    
    def set(self, **kwargs):
        """컨텍스트 정보 설정"""
        self.context.update(kwargs)
    
    def clear(self):
        """컨텍스트 초기화"""
        self.context.clear()
    
    def get_extra(self) -> Dict[str, Any]:
        """로그용 extra 딕셔너리 반환"""
        return self.context.copy()


# 전역 로그 컨텍스트
log_context = LogContext()


def get_logger(name: str = None) -> logging.Logger:
    """
    컨텍스트 정보를 포함한 로거 반환
    
    Args:
        name: 로거 이름 (기본값: 호출하는 모듈명)
    
    Returns:
        설정된 로거 인스턴스
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return logging.getLogger(name)


@contextmanager
def log_context_manager(**context):
    """
    로그 컨텍스트 임시 설정용 컨텍스트 매니저
    
    Usage:
        with log_context_manager(job_id="123", user_id="456"):
            logger.info("작업 시작")  # job_id, user_id가 자동 포함
    """
    original = log_context.context.copy()
    try:
        log_context.set(**context)
        yield
    finally:
        log_context.context = original


def log_execution_time(func_name: str = None):
    """
    함수 실행 시간을 로그로 기록하는 데코레이터
    
    Usage:
        @log_execution_time("파일 처리")
        def process_file(path):
            # 파일 처리 로직
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            logger = get_logger(func.__module__)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"{name} completed", 
                    extra={
                        "function": name,
                        "duration_seconds": round(duration, 3),
                        "status": "success",
                        **log_context.get_extra()
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{name} failed", 
                    extra={
                        "function": name,
                        "duration_seconds": round(duration, 3),
                        "status": "error",
                        "error": str(e),
                        **log_context.get_extra()
                    },
                    exc_info=True
                )
                raise
        return wrapper
    return decorator


class MetricsCollector:
    """
    Prometheus 메트릭 수집기
    
    애플리케이션의 주요 지표들을 수집하고 /metrics 엔드포인트를 통해 노출합니다.
    """
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # 문서 처리 메트릭
        self.documents_processed = Counter(
            'brainbeaver_documents_processed_total',
            'Total number of documents processed',
            ['source_type', 'status'],
            registry=self.registry
        )
        
        self.chunks_created = Counter(
            'brainbeaver_chunks_created_total',
            'Total number of chunks created',
            registry=self.registry
        )
        
        # 작업 처리 시간 메트릭
        self.job_duration = Histogram(
            'brainbeaver_job_duration_seconds',
            'Job processing time in seconds',
            ['kind', 'status'],
            registry=self.registry
        )
        
        self.pipeline_step_duration = Histogram(
            'brainbeaver_pipeline_step_duration_seconds',
            'Pipeline step processing time in seconds',
            ['step'],
            registry=self.registry
        )
        
        # 시스템 상태 메트릭
        self.active_jobs = Gauge(
            'brainbeaver_active_jobs',
            'Number of currently active jobs',
            ['kind'],
            registry=self.registry
        )
        
        self.queue_size = Gauge(
            'brainbeaver_queue_size',
            'Number of jobs in queue',
            ['kind'],
            registry=self.registry
        )
        
        # 에러 메트릭
        self.errors_total = Counter(
            'brainbeaver_errors_total',
            'Total number of errors',
            ['component', 'error_type'],
            registry=self.registry
        )
        
        # LLM API 메트릭
        self.llm_requests = Counter(
            'brainbeaver_llm_requests_total',
            'Total LLM API requests',
            ['provider', 'model', 'status'],
            registry=self.registry
        )
        
        self.llm_duration = Histogram(
            'brainbeaver_llm_request_duration_seconds',
            'LLM API request duration',
            ['provider', 'model'],
            registry=self.registry
        )
        
        # 크롤링 메트릭
        self.pages_crawled = Counter(
            'brainbeaver_pages_crawled_total',
            'Total pages crawled',
            ['domain', 'status'],
            registry=self.registry
        )
        
        self.crawl_rate_limits = Counter(
            'brainbeaver_crawl_rate_limits_total',
            'Total rate limit hits during crawling',
            ['domain'],
            registry=self.registry
        )
    
    def get_metrics(self) -> str:
        """Prometheus 형태의 메트릭 문자열 반환"""
        return generate_latest(self.registry).decode('utf-8')


# 전역 메트릭 수집기
metrics = MetricsCollector()


def track_metric(metric_name: str, labels: Dict[str, str] = None, value: float = 1):
    """
    메트릭 추적 헬퍼 함수
    
    Args:
        metric_name: 메트릭 이름
        labels: 라벨 딕셔너리
        value: 메트릭 값 (Counter는 1, Gauge는 실제 값)
    """
    labels = labels or {}
    
    try:
        metric = getattr(metrics, metric_name, None)
        if metric:
            if hasattr(metric, 'labels'):
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)
    except Exception as e:
        logger = get_logger(__name__)
        logger.warning(f"Failed to track metric {metric_name}: {e}")


@contextmanager
def track_duration(histogram_name: str, labels: Dict[str, str] = None):
    """
    실행 시간을 히스토그램으로 추적하는 컨텍스트 매니저
    
    Usage:
        with track_duration('pipeline_step_duration', {'step': 'chunking'}):
            # 청킹 로직 실행
            pass
    """
    labels = labels or {}
    start_time = time.time()
    
    try:
        yield
    finally:
        duration = time.time() - start_time
        try:
            histogram = getattr(metrics, histogram_name, None)
            if histogram and hasattr(histogram, 'labels'):
                histogram.labels(**labels).observe(duration)
        except Exception as e:
            logger = get_logger(__name__)
            logger.warning(f"Failed to track duration metric {histogram_name}: {e}")


def init_observability():
    """관측성 시스템 초기화"""
    setup_logging()
    
    logger = get_logger(__name__)
    logger.info("Observability system initialized", extra={
        "metrics_enabled": settings.enable_metrics,
        "log_format": settings.log_format
    })