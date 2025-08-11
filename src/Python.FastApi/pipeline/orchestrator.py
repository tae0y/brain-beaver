"""
파이프라인 오케스트레이터

전체 문서 처리 파이프라인을 조정하고 관리합니다.
- 단계별 처리 흐름 관리
- 에러 처리 및 복구
- 진행률 추적
- 배치 처리 최적화
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.models import Document, Chunk, Summary, Embedding
from core.database import get_db_session
from core.config import settings
from core.logging import get_logger, log_execution_time, track_duration, track_metric
from domain.jobs.models import JobManager, JobKind, JobState, JobProgress
from domain.documents.repository import DocumentRepository, ChunkRepository
from pipeline.file_scanner import FileScanner
from pipeline.steps.normalize import DocumentNormalizer, NormalizedContent
from pipeline.steps.chunking import DocumentChunker, ChunkingResult
from pipeline.steps.summarize import DocumentSummarizer, SummaryRequest, SummaryType
from pipeline.adapters.llm_interface import llm_manager, EmbeddingRequest

logger = get_logger(__name__)


@dataclass
class ProcessingResult:
    """처리 결과"""
    success: bool
    document_id: int
    chunks_created: int
    summaries_created: int
    embeddings_created: int
    error_message: Optional[str] = None
    processing_time: float = 0


@dataclass
class PipelineConfig:
    """파이프라인 설정"""
    chunking_strategy: str = "sentence"
    summary_type: SummaryType = SummaryType.BRIEF
    generate_embeddings: bool = True
    generate_summaries: bool = True
    batch_size: int = 10
    max_concurrent: int = 5
    retry_failed: bool = True
    skip_unchanged: bool = True


class DocumentProcessor:
    """단일 문서 처리기"""
    
    def __init__(self):
        self.normalizer = DocumentNormalizer()
        self.chunker = DocumentChunker()
        self.summarizer = DocumentSummarizer()
        self.document_repo = DocumentRepository()
        self.chunk_repo = ChunkRepository()
    
    async def process_document(self, document: Document, config: PipelineConfig) -> ProcessingResult:
        """단일 문서 전체 처리 파이프라인"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Processing document", extra={
                "document_id": document.id,
                "source_type": document.source_type,
                "uri": document.uri
            })
            
            # 1. 문서 정규화
            normalized = await self._normalize_document(document)
            if not normalized:
                return ProcessingResult(
                    success=False,
                    document_id=document.id,
                    chunks_created=0,
                    summaries_created=0,
                    embeddings_created=0,
                    error_message="Document normalization failed"
                )
            
            # 2. 청킹
            chunking_result = await self._chunk_document(normalized, config)
            if not chunking_result.chunks:
                return ProcessingResult(
                    success=False,
                    document_id=document.id,
                    chunks_created=0,
                    summaries_created=0,
                    embeddings_created=0,
                    error_message="Document chunking failed"
                )
            
            # 3. 데이터베이스에 청크 저장
            chunks_created = await self._save_chunks(document.id, chunking_result)
            
            # 4. 요약 생성 (옵션)
            summaries_created = 0
            if config.generate_summaries:
                summaries_created = await self._generate_summaries(document, chunking_result, config)
            
            # 5. 임베딩 생성 (옵션)
            embeddings_created = 0
            if config.generate_embeddings:
                embeddings_created = await self._generate_embeddings(document.id, chunking_result)
            
            # 6. 문서 상태 업데이트
            self.document_repo.update_status(document.id, "processed")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info("Document processed successfully", extra={
                "document_id": document.id,
                "chunks_created": chunks_created,
                "summaries_created": summaries_created,
                "embeddings_created": embeddings_created,
                "processing_time": processing_time
            })
            
            return ProcessingResult(
                success=True,
                document_id=document.id,
                chunks_created=chunks_created,
                summaries_created=summaries_created,
                embeddings_created=embeddings_created,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = str(e)
            
            logger.error(f"Document processing failed", extra={
                "document_id": document.id,
                "error": error_msg,
                "processing_time": processing_time
            }, exc_info=True)
            
            # 실패 상태로 업데이트
            self.document_repo.update_status(document.id, "failed", error_msg)
            
            return ProcessingResult(
                success=False,
                document_id=document.id,
                chunks_created=0,
                summaries_created=0,
                embeddings_created=0,
                error_message=error_msg,
                processing_time=processing_time
            )
    
    async def _normalize_document(self, document: Document) -> Optional[NormalizedContent]:
        """문서 정규화"""
        try:
            if document.source_type == "file":
                return self.normalizer.normalize_file(document.path)
            else:
                # 웹 문서의 경우 URL에서 컨텐츠 읽기 (구현 필요)
                # 여기서는 임시로 빈 컨텐츠 반환
                return None
        except Exception as e:
            logger.error(f"Document normalization failed: {e}")
            return None
    
    async def _chunk_document(self, normalized: NormalizedContent, config: PipelineConfig) -> ChunkingResult:
        """문서 청킹"""
        try:
            with track_duration('pipeline_step_duration', {'step': 'chunking'}):
                return self.chunker.chunk_document(normalized.text, config.chunking_strategy)
        except Exception as e:
            logger.error(f"Document chunking failed: {e}")
            return ChunkingResult(chunks=[], total_tokens=0, avg_tokens_per_chunk=0, overlap_tokens=0)
    
    async def _save_chunks(self, document_id: int, chunking_result: ChunkingResult) -> int:
        """청크 데이터베이스 저장"""
        try:
            chunks_data = []
            for chunk in chunking_result.chunks:
                chunks_data.append({
                    "text": chunk.text,
                    "token_len": chunk.token_count,
                    "hash": chunk.hash
                })
            
            # 기존 청크 삭제 후 새로 생성
            self.chunk_repo.delete_by_document_id(document_id)
            chunks = self.chunk_repo.create_chunks(document_id, chunks_data)
            
            track_metric('chunks_created', {}, len(chunks))
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Failed to save chunks: {e}")
            return 0
    
    async def _generate_summaries(self, document: Document, chunking_result: ChunkingResult, config: PipelineConfig) -> int:
        """요약 생성"""
        try:
            summaries_created = 0
            
            # 문서 전체 요약
            if chunking_result.chunks:
                full_text = " ".join(chunk.text for chunk in chunking_result.chunks[:5])  # 처음 5개 청크만
                
                summary_request = SummaryRequest(
                    text=full_text,
                    summary_type=config.summary_type,
                    language="korean"
                )
                
                summary_result = await self.summarizer.summarize(summary_request)
                
                # 데이터베이스에 저장
                with get_db_session() as session:
                    summary = Summary(
                        document_id=document.id,
                        chunk_id=None,  # 전체 문서 요약
                        model=summary_result.metadata.get('model', 'unknown'),
                        text=summary_result.summary
                    )
                    session.add(summary)
                    session.commit()
                    summaries_created += 1
            
            return summaries_created
            
        except Exception as e:
            logger.error(f"Failed to generate summaries: {e}")
            return 0
    
    async def _generate_embeddings(self, document_id: int, chunking_result: ChunkingResult) -> int:
        """임베딩 생성"""
        try:
            embeddings_created = 0
            
            # 청크 텍스트들을 배치로 임베딩 생성
            texts = [chunk.text for chunk in chunking_result.chunks]
            embedding_requests = [EmbeddingRequest(texts=text) for text in texts]
            
            # 배치 임베딩 생성
            embedding_responses = await llm_manager.batch_generate_embeddings(
                embedding_requests, 
                batch_size=settings.batch_size
            )
            
            # 데이터베이스에 저장
            with get_db_session() as session:
                chunks = self.chunk_repo.get_by_document_id(document_id)
                
                for i, (chunk, embedding_response) in enumerate(zip(chunks, embedding_responses)):
                    embedding = Embedding(
                        chunk_id=chunk.id,
                        provider=embedding_response.provider,
                        model=embedding_response.model,
                        dim=embedding_response.dimension,
                        vector=embedding_response.embeddings  # JSON으로 저장
                    )
                    session.add(embedding)
                    embeddings_created += 1
                
                session.commit()
            
            return embeddings_created
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return 0


class PipelineOrchestrator:
    """
    파이프라인 오케스트레이터
    
    전체 문서 처리 파이프라인을 조정합니다.
    """
    
    def __init__(self):
        self.job_manager = JobManager()
        self.file_scanner = FileScanner()
        self.document_processor = DocumentProcessor()
        self.document_repo = DocumentRepository()
    
    @log_execution_time("파일 스캔 작업")
    async def scan_folder(self, root_path: str, recursive: bool = True) -> int:
        """폴더 스캔 작업 실행"""
        # Job 생성
        job = self.job_manager.create_job(
            JobKind.SCAN,
            {
                "root_path": root_path,
                "recursive": recursive,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        try:
            self.job_manager.update_job_state(job.id, JobState.RUNNING)
            
            # 파일 스캔 실행
            scan_result = self.file_scanner.scan_directory(root_path, recursive)
            
            # 진행률 업데이트
            progress = JobProgress(
                current=scan_result.total_files,
                total=scan_result.total_files,
                succeeded=scan_result.new_files + scan_result.changed_files + scan_result.unchanged_files,
                failed=len(scan_result.errors)
            )
            self.job_manager.update_job_progress(job.id, progress)
            
            # 성공 처리
            self.job_manager.update_job_state(job.id, JobState.SUCCEEDED)
            
            logger.info("Folder scan completed", extra={
                "job_id": job.id,
                "root_path": root_path,
                "scan_result": {
                    "total_files": scan_result.total_files,
                    "new_files": scan_result.new_files,
                    "changed_files": scan_result.changed_files,
                    "unchanged_files": scan_result.unchanged_files,
                    "deleted_files": scan_result.deleted_files,
                    "errors": len(scan_result.errors)
                }
            })
            
            return job.id
            
        except Exception as e:
            error_msg = str(e)
            self.job_manager.update_job_state(job.id, JobState.FAILED, error_msg)
            logger.error(f"Folder scan failed: {error_msg}", extra={"job_id": job.id})
            raise
    
    @log_execution_time("파일 처리 작업")
    async def process_folder(self, root_path: str = None, config: PipelineConfig = None) -> int:
        """폴더 처리 작업 실행"""
        config = config or PipelineConfig()
        
        # Job 생성
        job = self.job_manager.create_job(
            JobKind.PROCESS,
            {
                "root_path": root_path,
                "config": {
                    "chunking_strategy": config.chunking_strategy,
                    "summary_type": config.summary_type.value,
                    "generate_embeddings": config.generate_embeddings,
                    "generate_summaries": config.generate_summaries,
                    "batch_size": config.batch_size,
                    "max_concurrent": config.max_concurrent
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        try:
            self.job_manager.update_job_state(job.id, JobState.RUNNING)
            
            # 처리 대상 문서 조회
            if root_path:
                documents = self.document_repo.find_by_path_prefix(root_path)
            else:
                documents = self.document_repo.find_by_status("pending")
            
            pending_docs = [doc for doc in documents if doc.status == "pending"]
            
            if not pending_docs:
                self.job_manager.update_job_state(job.id, JobState.SUCCEEDED)
                logger.info("No pending documents to process", extra={"job_id": job.id})
                return job.id
            
            # 초기 진행률 설정
            progress = JobProgress(current=0, total=len(pending_docs), succeeded=0, failed=0)
            self.job_manager.update_job_progress(job.id, progress)
            
            # 배치 처리
            processed_count = 0
            successful_count = 0
            failed_count = 0
            
            # 세마포어로 동시 처리 수 제한
            semaphore = asyncio.Semaphore(config.max_concurrent)
            
            async def process_with_semaphore(doc):
                async with semaphore:
                    return await self.document_processor.process_document(doc, config)
            
            # 배치 단위로 처리
            for i in range(0, len(pending_docs), config.batch_size):
                batch = pending_docs[i:i + config.batch_size]
                
                # 배치 처리
                tasks = [process_with_semaphore(doc) for doc in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 결과 처리
                for result in batch_results:
                    processed_count += 1
                    
                    if isinstance(result, Exception):
                        failed_count += 1
                        logger.error(f"Document processing exception: {result}")
                    elif result.success:
                        successful_count += 1
                    else:
                        failed_count += 1
                
                # 진행률 업데이트
                progress = JobProgress(
                    current=processed_count,
                    total=len(pending_docs),
                    succeeded=successful_count,
                    failed=failed_count
                )
                self.job_manager.update_job_progress(job.id, progress)
                
                logger.info(f"Batch processed", extra={
                    "job_id": job.id,
                    "batch_size": len(batch),
                    "progress": f"{processed_count}/{len(pending_docs)}"
                })
            
            # 최종 상태 결정
            final_state = JobState.SUCCEEDED if failed_count == 0 else JobState.FAILED
            error_msg = f"Processing completed with {failed_count} failures" if failed_count > 0 else None
            
            self.job_manager.update_job_state(job.id, final_state, error_msg)
            
            logger.info("Folder processing completed", extra={
                "job_id": job.id,
                "total_documents": len(pending_docs),
                "successful": successful_count,
                "failed": failed_count,
                "final_state": final_state.value
            })
            
            return job.id
            
        except Exception as e:
            error_msg = str(e)
            self.job_manager.update_job_state(job.id, JobState.FAILED, error_msg)
            logger.error(f"Folder processing failed: {error_msg}", extra={"job_id": job.id}, exc_info=True)
            raise
    
    def get_job_status(self, job_id: int) -> Optional[Dict[str, Any]]:
        """작업 상태 조회"""
        job = self.job_manager.get_job(job_id)
        if not job:
            return None
        
        return {
            "id": job.id,
            "kind": job.kind,
            "state": job.state,
            "progress": {
                "percentage": job.progress * 100,
                "current": job.succeeded + job.failed,
                "total": job.total,
                "succeeded": job.succeeded,
                "failed": job.failed
            },
            "params": job.params,
            "error": job.error,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "duration": self._calculate_duration(job)
        }
    
    def _calculate_duration(self, job) -> Optional[float]:
        """작업 수행 시간 계산 (초)"""
        if job.started_at:
            end_time = job.finished_at or datetime.utcnow()
            return (end_time - job.started_at).total_seconds()
        return None
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """활성 작업 목록"""
        jobs = self.job_manager.get_active_jobs()
        return [self.get_job_status(job.id) for job in jobs]
    
    def cancel_job(self, job_id: int) -> bool:
        """작업 취소"""
        return self.job_manager.cancel_job(job_id)