"""
공통 응답 스키마
"""

from typing import Any, Optional, Generic, TypeVar, Dict, List
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar('T')


class ResponseDTO(GenericModel, Generic[T]):
    """일반적인 API 응답 형식"""
    status: str
    message: str
    data: Optional[T] = None


class HealthCheckResponse(BaseModel):
    """헬스 체크 응답"""
    status: str
    timestamp: str
    version: str
    services: Dict[str, Any]


class MetricsResponse(BaseModel):
    """메트릭 응답"""
    metrics: str  # Prometheus 형식 텍스트


class ErrorResponse(BaseModel):
    """에러 응답"""
    status: str = "error"
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None