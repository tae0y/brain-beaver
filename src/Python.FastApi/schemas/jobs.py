"""
Job 관련 Pydantic 스키마
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from domain.jobs.models import JobKind, JobState


class JobCreateRequest(BaseModel):
    """작업 생성 요청"""
    kind: JobKind
    params: Dict[str, Any]


class JobProgress(BaseModel):
    """작업 진행률"""
    percentage: float = Field(ge=0, le=100, description="진행률 (%)")
    current: int = Field(ge=0, description="현재 처리된 항목 수")
    total: int = Field(ge=0, description="전체 항목 수")
    succeeded: int = Field(ge=0, description="성공한 항목 수")
    failed: int = Field(ge=0, description="실패한 항목 수")


class JobResponse(BaseModel):
    """작업 응답"""
    id: int
    kind: JobKind
    state: JobState
    progress: JobProgress
    params: Dict[str, Any]
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration: Optional[float] = Field(None, description="실행 시간 (초)")
    
    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """작업 목록 응답"""
    jobs: List[JobResponse]
    total: int
    active: int


class FolderScanRequest(BaseModel):
    """폴더 스캔 요청"""
    root_path: str = Field(description="스캔할 폴더 경로")
    recursive: bool = Field(default=True, description="하위 폴더 포함 여부")


class FolderProcessRequest(BaseModel):
    """폴더 처리 요청"""
    root_path: Optional[str] = Field(None, description="처리할 폴더 경로 (없으면 전체)")
    chunking_strategy: str = Field(default="sentence", description="청킹 전략")
    generate_summaries: bool = Field(default=True, description="요약 생성 여부")
    generate_embeddings: bool = Field(default=True, description="임베딩 생성 여부")
    batch_size: int = Field(default=10, ge=1, le=100, description="배치 크기")
    max_concurrent: int = Field(default=5, ge=1, le=20, description="최대 동시 처리 수")


class JobStatistics(BaseModel):
    """작업 통계"""
    by_state: Dict[str, int]
    by_kind: Dict[str, int]
    total_jobs: int
    active_jobs: int
    avg_duration_seconds: float