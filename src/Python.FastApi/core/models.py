"""
데이터베이스 모델 정의

이 모듈은 브레인비버 재구현 프로젝트의 핵심 데이터 모델을 정의합니다.
- documents: 파일/웹 문서 메타데이터 및 처리 상태
- chunks: 문서에서 분절된 텍스트 청크
- summaries: 문서/청크별 요약
- embeddings: 청크별 벡터 임베딩
- links: 청크간 연결 관계 (명시적/의미적)
- jobs: 비동기 작업 상태 관리
- url_cache: 웹 크롤링 캐시 (ETag, Last-Modified 기반 증분 처리)
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Boolean, Column, Integer, BigInteger, String, Text, DateTime, 
    JSON, Float, CheckConstraint, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# pgvector 지원을 위한 조건부 임포트
ENABLE_PGVECTOR = os.getenv("ENABLE_PGVECTOR", "false").lower() == "true"

if ENABLE_PGVECTOR:
    try:
        from pgvector.sqlalchemy import Vector
    except ImportError:
        ENABLE_PGVECTOR = False
        Vector = None
else:
    Vector = None

Base = declarative_base()


class Document(Base):
    """
    문서 메타데이터 및 처리 상태
    
    파일과 웹 문서 모두를 통합 관리하며, 증분 처리를 위한
    해시 기반 변경 감지를 지원합니다.
    """
    __tablename__ = "documents"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_type = Column(String(10), CheckConstraint("source_type IN ('file', 'web')"), nullable=False)
    uri = Column(String(2000), unique=True, nullable=False, index=True)  # 파일 경로 또는 URL 식별자
    
    # 파일 특화 필드
    path = Column(String(2000), nullable=True)  # 파일 시스템 경로
    
    # 웹 특화 필드  
    url = Column(String(2000), nullable=True)  # 웹 URL
    
    # 공통 메타데이터
    mtime = Column(DateTime, nullable=True)  # 수정 시간
    size = Column(BigInteger, nullable=True)  # 파일 크기
    content_hash = Column(String(64), nullable=False, index=True)  # SHA256 해시
    title = Column(String(500), nullable=True)
    meta = Column(JSON, nullable=True)  # 추가 메타데이터 (frontmatter, HTML meta 등)
    
    # 처리 상태
    status = Column(String(20), CheckConstraint("status IN ('pending', 'processed', 'failed')"), 
                   default='pending', nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    
    # 타임스탬프
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # 관계
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """
    문서에서 분절된 텍스트 청크
    
    토큰 길이 기반 분절을 통해 LLM 처리에 최적화된 크기로 나누어집니다.
    """
    __tablename__ = "chunks"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_id = Column(BigInteger, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    ordinal = Column(Integer, nullable=False)  # 문서 내 청크 순서
    text = Column(Text, nullable=False)
    token_len = Column(Integer, nullable=False)
    hash = Column(String(64), nullable=False, index=True)  # 청크 내용 해시 (중복 감지용)
    
    # 타임스탬프
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # 관계
    document = relationship("Document", back_populates="chunks")
    embeddings = relationship("Embedding", back_populates="chunk", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="chunk", cascade="all, delete-orphan")
    
    # 송신 링크 (이 청크에서 출발)
    outgoing_links = relationship("Link", foreign_keys="Link.src_chunk_id", back_populates="src_chunk", cascade="all, delete-orphan")
    # 수신 링크 (이 청크로 도착)  
    incoming_links = relationship("Link", foreign_keys="Link.dst_chunk_id", back_populates="dst_chunk", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('document_id', 'ordinal', name='uq_chunk_document_ordinal'),
        Index('ix_chunks_document_ordinal', 'document_id', 'ordinal'),
    )


class Summary(Base):
    """
    문서/청크별 요약
    
    LLM을 통한 자동 요약을 저장하며, 다양한 모델/버전을 지원합니다.
    """
    __tablename__ = "summaries"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_id = Column(BigInteger, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    chunk_id = Column(BigInteger, ForeignKey('chunks.id', ondelete='CASCADE'), nullable=True, index=True)  # NULL = 전체 문서 요약
    model = Column(String(100), nullable=False)  # "gpt-4", "ollama:llama2" 등
    text = Column(Text, nullable=False)
    
    # 타임스탬프
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # 관계
    document = relationship("Document", back_populates="summaries")
    chunk = relationship("Chunk", back_populates="summaries")


class Embedding(Base):
    """
    청크별 벡터 임베딩
    
    pgvector 지원 시 Vector 타입을 사용하고, 미지원 시 JSON으로 저장합니다.
    """
    __tablename__ = "embeddings"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chunk_id = Column(BigInteger, ForeignKey('chunks.id', ondelete='CASCADE'), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # "openai", "ollama", "local" 등
    model = Column(String(100), nullable=False)   # "text-embedding-3-large" 등
    dim = Column(Integer, nullable=False)  # 벡터 차원
    
    # pgvector 사용 가능 시 Vector, 아니면 JSON
    if ENABLE_PGVECTOR and Vector:
        vector = Column(Vector, nullable=False)
        vector_json = Column(JSON, nullable=True)  # 백업/호환성용
    else:
        vector = Column(JSON, nullable=False)  # List[float] as JSON
        vector_json = Column(JSON, nullable=True)
    
    # 타임스탬프
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # 관계
    chunk = relationship("Chunk", back_populates="embeddings")
    
    __table_args__ = (
        UniqueConstraint('chunk_id', 'provider', 'model', name='uq_embedding_chunk_provider_model'),
        Index('ix_embeddings_provider_model', 'provider', 'model'),
    )


class Link(Base):
    """
    청크간 연결 관계
    
    명시적 링크(문서 내 참조)와 의미적 링크(벡터 유사도 기반)를 관리합니다.
    """
    __tablename__ = "links"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    src_chunk_id = Column(BigInteger, ForeignKey('chunks.id', ondelete='CASCADE'), nullable=False, index=True)
    dst_chunk_id = Column(BigInteger, ForeignKey('chunks.id', ondelete='CASCADE'), nullable=False, index=True)
    score = Column(Float, nullable=False)  # 유사도 점수 또는 가중치
    link_type = Column(String(20), CheckConstraint("link_type IN ('explicit', 'semantic')"), nullable=False)
    metadata = Column(JSON, nullable=True)  # 링크 생성 세부 정보
    
    # 타임스탬프
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # 관계
    src_chunk = relationship("Chunk", foreign_keys=[src_chunk_id], back_populates="outgoing_links")
    dst_chunk = relationship("Chunk", foreign_keys=[dst_chunk_id], back_populates="incoming_links")
    
    __table_args__ = (
        UniqueConstraint('src_chunk_id', 'dst_chunk_id', 'link_type', name='uq_link_src_dst_type'),
        Index('ix_links_src_chunk', 'src_chunk_id'),
        Index('ix_links_dst_chunk', 'dst_chunk_id'),
        Index('ix_links_score', 'score'),
    )


class Job(Base):
    """
    비동기 작업 상태 관리
    
    파일 스캔, 처리, 크롤링 등의 장시간 작업을 추적합니다.
    """
    __tablename__ = "jobs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    kind = Column(String(20), CheckConstraint("kind IN ('scan', 'process', 'crawl')"), nullable=False, index=True)
    params = Column(JSON, nullable=False)  # 작업 매개변수
    
    # 상태 관리
    state = Column(String(20), CheckConstraint("state IN ('queued', 'running', 'succeeded', 'failed', 'canceled')"), 
                  default='queued', nullable=False, index=True)
    
    # 진행률
    progress = Column(Float, default=0.0, nullable=False)  # 0.0 ~ 1.0
    total = Column(Integer, default=0, nullable=False)
    succeeded = Column(Integer, default=0, nullable=False)
    failed = Column(Integer, default=0, nullable=False)
    
    # 에러 정보
    error = Column(Text, nullable=True)
    
    # 타임스탬프
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('ix_jobs_kind_state', 'kind', 'state'),
        Index('ix_jobs_created_at', 'created_at'),
    )


class URLCache(Base):
    """
    웹 크롤링 캐시
    
    HTTP 캐시 헤더 (ETag, Last-Modified)를 활용한 증분 크롤링을 지원합니다.
    """
    __tablename__ = "url_cache"
    
    url = Column(String(2000), primary_key=True)
    url_hash = Column(String(64), nullable=False, unique=True, index=True)  # URL 해시
    etag = Column(String(200), nullable=True)  # HTTP ETag 헤더
    last_modified = Column(String(100), nullable=True)  # HTTP Last-Modified 헤더
    fetched_at = Column(DateTime, nullable=False)
    status_code = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=True)  # 컨텐츠 SHA256 해시
    
    # 타임스탬프
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index('ix_url_cache_fetched_at', 'fetched_at'),
        Index('ix_url_cache_status_code', 'status_code'),
    )