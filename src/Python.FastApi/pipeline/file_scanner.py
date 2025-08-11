"""
파일 스캐너 및 증분 처리

파일 시스템을 스캔하여 문서 메타데이터를 수집하고,
해시 기반 증분 처리를 통해 변경된 파일만 처리합니다.
"""

import os
import hashlib
import glob
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from core.models import Document
from core.database import get_db_session
from core.config import settings
from core.logging import get_logger, log_execution_time, track_metric, log_context

logger = get_logger(__name__)


@dataclass
class FileInfo:
    """파일 정보 데이터 클래스"""
    path: str
    size: int
    mtime: datetime
    content_hash: str
    title: Optional[str] = None
    meta: Optional[Dict] = None


@dataclass 
class ScanResult:
    """스캔 결과 데이터 클래스"""
    total_files: int
    new_files: int
    changed_files: int
    unchanged_files: int
    deleted_files: int
    errors: List[str]


class FileScanner:
    """
    파일 시스템 스캐너
    
    지정된 디렉토리를 재귀적으로 스캔하여 처리 대상 파일들을 찾고,
    데이터베이스와 비교하여 변경 사항을 감지합니다.
    """
    
    def __init__(self):
        self.extensions = settings.file_extensions_list
        self.ignore_patterns = settings.file_ignore_patterns_list
        
        logger.info("FileScanner initialized", extra={
            "extensions": self.extensions,
            "ignore_patterns": self.ignore_patterns
        })
    
    @log_execution_time("파일 스캔")
    def scan_directory(self, root_path: str, recursive: bool = True) -> ScanResult:
        """
        디렉토리 스캔 및 증분 처리
        
        Args:
            root_path: 스캔할 루트 디렉토리
            recursive: 하위 디렉토리 포함 여부
            
        Returns:
            ScanResult: 스캔 결과 통계
        """
        root_path = Path(root_path).resolve()
        
        if not root_path.exists():
            raise ValueError(f"Directory does not exist: {root_path}")
        
        logger.info(f"Starting directory scan", extra={
            "root_path": str(root_path),
            "recursive": recursive
        })
        
        # 파일 시스템에서 파일 목록 수집
        current_files = self._collect_files(root_path, recursive)
        logger.info(f"Found {len(current_files)} files", extra={
            "file_count": len(current_files)
        })
        
        # 데이터베이스와 비교하여 변경 사항 감지
        with get_db_session() as session:
            scan_result = self._process_files(session, root_path, current_files)
        
        # 메트릭 업데이트
        track_metric('documents_processed', 
                    {'source_type': 'file', 'status': 'scanned'}, 
                    scan_result.total_files)
        
        logger.info("Directory scan completed", extra={
            "root_path": str(root_path),
            "total_files": scan_result.total_files,
            "new_files": scan_result.new_files,
            "changed_files": scan_result.changed_files,
            "unchanged_files": scan_result.unchanged_files,
            "deleted_files": scan_result.deleted_files,
            "error_count": len(scan_result.errors)
        })
        
        return scan_result
    
    def _collect_files(self, root_path: Path, recursive: bool) -> List[FileInfo]:
        """파일 시스템에서 대상 파일들 수집"""
        files = []
        errors = []
        
        try:
            # glob 패턴 생성
            patterns = []
            for ext in self.extensions:
                if recursive:
                    patterns.append(f"**/*{ext}")
                else:
                    patterns.append(f"*{ext}")
            
            for pattern in patterns:
                for file_path in root_path.glob(pattern):
                    if self._should_ignore(file_path, root_path):
                        continue
                    
                    try:
                        file_info = self._get_file_info(file_path)
                        files.append(file_info)
                    except Exception as e:
                        error_msg = f"Failed to process file {file_path}: {e}"
                        errors.append(error_msg)
                        logger.warning(error_msg, extra={"file_path": str(file_path)})
        
        except Exception as e:
            logger.error(f"Failed to collect files from {root_path}: {e}")
            errors.append(str(e))
        
        return files
    
    def _should_ignore(self, file_path: Path, root_path: Path) -> bool:
        """파일이 무시 패턴에 해당하는지 확인"""
        relative_path = file_path.relative_to(root_path)
        path_parts = relative_path.parts
        
        # 각 경로 부분이 무시 패턴에 해당하는지 확인
        for part in path_parts:
            for pattern in self.ignore_patterns:
                if pattern in part:
                    return True
        
        # 숨김 파일/디렉토리 무시
        for part in path_parts:
            if part.startswith('.') and part not in ['.md', '.txt']:
                return True
        
        return False
    
    def _get_file_info(self, file_path: Path) -> FileInfo:
        """파일 정보 수집"""
        stat = file_path.stat()
        
        # 파일 해시 계산
        content_hash = self._calculate_file_hash(file_path)
        
        # 제목 추출 (파일명에서)
        title = file_path.stem
        
        # 메타데이터 추출 (frontmatter 등)
        meta = self._extract_metadata(file_path)
        
        return FileInfo(
            path=str(file_path),
            size=stat.st_size,
            mtime=datetime.fromtimestamp(stat.st_mtime),
            content_hash=content_hash,
            title=title,
            meta=meta
        )
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """파일 내용의 SHA256 해시 계산"""
        hash_sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_sha256.update(chunk)
        except Exception as e:
            logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            # 파일 접근 실패 시 경로와 수정시간으로 대체 해시 생성
            fallback = f"{file_path}{file_path.stat().st_mtime}"
            hash_sha256.update(fallback.encode())
        
        return hash_sha256.hexdigest()
    
    def _extract_metadata(self, file_path: Path) -> Optional[Dict]:
        """파일에서 메타데이터 추출 (frontmatter 등)"""
        if file_path.suffix not in ['.md', '.mdx']:
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # 처음 1000자만 읽기
            
            # 간단한 frontmatter 파싱
            if content.startswith('---\n'):
                end_idx = content.find('\n---\n', 4)
                if end_idx > 0:
                    frontmatter = content[4:end_idx]
                    meta = {}
                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            meta[key.strip()] = value.strip()
                    return meta
        except Exception as e:
            logger.debug(f"Failed to extract metadata from {file_path}: {e}")
        
        return None
    
    def _process_files(self, session: Session, root_path: Path, current_files: List[FileInfo]) -> ScanResult:
        """파일 목록을 데이터베이스와 비교하여 처리"""
        errors = []
        new_files = 0
        changed_files = 0
        unchanged_files = 0
        
        # 현재 파일 경로 집합
        current_paths = {info.path for info in current_files}
        
        # 기존 데이터베이스 문서들 조회 (해당 루트 경로 하위)
        root_str = str(root_path)
        existing_docs = session.query(Document).filter(
            and_(
                Document.source_type == 'file',
                Document.path.like(f"{root_str}%")
            )
        ).all()
        
        existing_paths = {doc.path for doc in existing_docs}
        existing_by_path = {doc.path: doc for doc in existing_docs}
        
        # 새 파일과 변경된 파일 처리
        for file_info in current_files:
            try:
                if file_info.path in existing_by_path:
                    # 기존 파일 - 변경 여부 확인
                    existing_doc = existing_by_path[file_info.path]
                    if existing_doc.content_hash != file_info.content_hash:
                        # 파일 변경됨 - 업데이트
                        self._update_document(session, existing_doc, file_info)
                        changed_files += 1
                        logger.debug(f"File changed: {file_info.path}")
                    else:
                        unchanged_files += 1
                        logger.debug(f"File unchanged: {file_info.path}")
                else:
                    # 새 파일 - 생성
                    self._create_document(session, file_info)
                    new_files += 1
                    logger.debug(f"New file: {file_info.path}")
            except Exception as e:
                error_msg = f"Failed to process file {file_info.path}: {e}"
                errors.append(error_msg)
                logger.error(error_msg, exc_info=True)
        
        # 삭제된 파일 처리
        deleted_paths = existing_paths - current_paths
        deleted_files = 0
        
        for deleted_path in deleted_paths:
            try:
                doc = existing_by_path[deleted_path]
                session.delete(doc)
                deleted_files += 1
                logger.debug(f"File deleted: {deleted_path}")
            except Exception as e:
                error_msg = f"Failed to delete document {deleted_path}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # 변경사항 커밋
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            error_msg = f"Failed to commit changes: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
            raise
        
        return ScanResult(
            total_files=len(current_files),
            new_files=new_files,
            changed_files=changed_files,
            unchanged_files=unchanged_files,
            deleted_files=deleted_files,
            errors=errors
        )
    
    def _create_document(self, session: Session, file_info: FileInfo):
        """새 문서 레코드 생성"""
        document = Document(
            source_type='file',
            uri=file_info.path,
            path=file_info.path,
            mtime=file_info.mtime,
            size=file_info.size,
            content_hash=file_info.content_hash,
            title=file_info.title,
            meta=file_info.meta,
            status='pending'
        )
        session.add(document)
    
    def _update_document(self, session: Session, document: Document, file_info: FileInfo):
        """기존 문서 레코드 업데이트"""
        document.mtime = file_info.mtime
        document.size = file_info.size
        document.content_hash = file_info.content_hash
        document.title = file_info.title
        document.meta = file_info.meta
        document.status = 'pending'  # 재처리 필요
        document.error_message = None
        document.updated_at = datetime.utcnow()
    
    def get_pending_documents(self, root_path: str = None, limit: int = None) -> List[Document]:
        """처리 대기 중인 문서 목록 반환"""
        with get_db_session() as session:
            query = session.query(Document).filter(
                and_(
                    Document.source_type == 'file',
                    Document.status == 'pending'
                )
            )
            
            if root_path:
                query = query.filter(Document.path.like(f"{root_path}%"))
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
    
    def mark_document_processed(self, document_id: int, success: bool = True, error_message: str = None):
        """문서 처리 상태 업데이트"""
        with get_db_session() as session:
            document = session.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = 'processed' if success else 'failed'
                document.error_message = error_message
                document.updated_at = datetime.utcnow()
                session.commit()
                
                track_metric('documents_processed', 
                           {'source_type': 'file', 'status': document.status}, 1)