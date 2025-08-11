"""
Document 도메인 리포지토리

문서 관련 데이터 액세스 로직을 캡슐화하여
비즈니스 로직과 데이터 액세스를 분리합니다.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from core.models import Document, Chunk, Summary, Link
from core.database import get_db_session


class DocumentRepository:
    """문서 리포지토리"""
    
    def __init__(self, session: Session = None):
        self.session = session or get_db_session()
    
    def create(self, **kwargs) -> Document:
        """새 문서 생성"""
        document = Document(**kwargs)
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document
    
    def get_by_id(self, document_id: int) -> Optional[Document]:
        """ID로 문서 조회"""
        return self.session.query(Document).filter(Document.id == document_id).first()
    
    def get_by_uri(self, uri: str) -> Optional[Document]:
        """URI로 문서 조회"""
        return self.session.query(Document).filter(Document.uri == uri).first()
    
    def get_by_hash(self, content_hash: str) -> List[Document]:
        """해시로 문서 목록 조회 (중복 감지용)"""
        return self.session.query(Document).filter(Document.content_hash == content_hash).all()
    
    def find_by_status(self, status: str, source_type: str = None, limit: int = None) -> List[Document]:
        """상태별 문서 조회"""
        query = self.session.query(Document).filter(Document.status == status)
        
        if source_type:
            query = query.filter(Document.source_type == source_type)
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def find_by_path_prefix(self, path_prefix: str) -> List[Document]:
        """경로 접두사로 문서 조회"""
        return self.session.query(Document).filter(
            and_(
                Document.source_type == 'file',
                Document.path.like(f"{path_prefix}%")
            )
        ).all()
    
    def update_status(self, document_id: int, status: str, error_message: str = None):
        """문서 상태 업데이트"""
        document = self.get_by_id(document_id)
        if document:
            document.status = status
            document.error_message = error_message
            document.updated_at = datetime.utcnow()
            self.session.commit()
    
    def update(self, document: Document, **kwargs):
        """문서 정보 업데이트"""
        for key, value in kwargs.items():
            if hasattr(document, key):
                setattr(document, key, value)
        
        document.updated_at = datetime.utcnow()
        self.session.commit()
    
    def delete(self, document_id: int) -> bool:
        """문서 삭제"""
        document = self.get_by_id(document_id)
        if document:
            self.session.delete(document)
            self.session.commit()
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """문서 통계 조회"""
        total_docs = self.session.query(func.count(Document.id)).scalar()
        
        status_stats = dict(
            self.session.query(Document.status, func.count(Document.id))
            .group_by(Document.status)
            .all()
        )
        
        source_type_stats = dict(
            self.session.query(Document.source_type, func.count(Document.id))
            .group_by(Document.source_type)
            .all()
        )
        
        return {
            'total_documents': total_docs,
            'by_status': status_stats,
            'by_source_type': source_type_stats
        }
    
    def get_recent_documents(self, limit: int = 10) -> List[Document]:
        """최근 생성된 문서 목록"""
        return (
            self.session.query(Document)
            .order_by(desc(Document.created_at))
            .limit(limit)
            .all()
        )
    
    def search(self, query: str, source_type: str = None) -> List[Document]:
        """제목 또는 메타데이터에서 검색"""
        search_filter = or_(
            Document.title.ilike(f"%{query}%"),
            Document.uri.ilike(f"%{query}%")
        )
        
        db_query = self.session.query(Document).filter(search_filter)
        
        if source_type:
            db_query = db_query.filter(Document.source_type == source_type)
        
        return db_query.all()
    
    def get_with_chunks(self, document_id: int) -> Optional[Document]:
        """청크와 함께 문서 조회"""
        return (
            self.session.query(Document)
            .filter(Document.id == document_id)
            .first()
        )
    
    def get_processing_candidates(self, batch_size: int = 50) -> List[Document]:
        """처리 후보 문서들 조회 (배치 처리용)"""
        return (
            self.session.query(Document)
            .filter(Document.status == 'pending')
            .order_by(Document.created_at)
            .limit(batch_size)
            .all()
        )


class ChunkRepository:
    """청크 리포지토리"""
    
    def __init__(self, session: Session = None):
        self.session = session or get_db_session()
    
    def create_chunks(self, document_id: int, chunks_data: List[Dict[str, Any]]) -> List[Chunk]:
        """문서의 청크들 일괄 생성"""
        chunks = []
        
        for i, chunk_data in enumerate(chunks_data):
            chunk = Chunk(
                document_id=document_id,
                ordinal=i,
                **chunk_data
            )
            chunks.append(chunk)
            self.session.add(chunk)
        
        self.session.commit()
        return chunks
    
    def get_by_document_id(self, document_id: int) -> List[Chunk]:
        """문서의 모든 청크 조회"""
        return (
            self.session.query(Chunk)
            .filter(Chunk.document_id == document_id)
            .order_by(Chunk.ordinal)
            .all()
        )
    
    def delete_by_document_id(self, document_id: int):
        """문서의 모든 청크 삭제"""
        self.session.query(Chunk).filter(Chunk.document_id == document_id).delete()
        self.session.commit()
    
    def get_by_hash(self, content_hash: str) -> List[Chunk]:
        """해시로 중복 청크 찾기"""
        return self.session.query(Chunk).filter(Chunk.hash == content_hash).all()
    
    def get_statistics(self) -> Dict[str, Any]:
        """청크 통계"""
        total_chunks = self.session.query(func.count(Chunk.id)).scalar()
        avg_token_len = self.session.query(func.avg(Chunk.token_len)).scalar()
        
        return {
            'total_chunks': total_chunks,
            'average_token_length': round(avg_token_len, 2) if avg_token_len else 0
        }


class DocumentService:
    """문서 도메인 서비스"""
    
    def __init__(self):
        self.document_repo = DocumentRepository()
        self.chunk_repo = ChunkRepository()
    
    def process_document_update(self, document_id: int, chunks_data: List[Dict[str, Any]]):
        """문서 업데이트 처리 (청크 재생성 포함)"""
        with get_db_session() as session:
            # 기존 청크 삭제
            self.chunk_repo.delete_by_document_id(document_id)
            
            # 새 청크 생성
            if chunks_data:
                self.chunk_repo.create_chunks(document_id, chunks_data)
            
            # 문서 상태 업데이트
            self.document_repo.update_status(document_id, 'processed')
    
    def get_document_with_stats(self, document_id: int) -> Optional[Dict[str, Any]]:
        """통계 정보와 함께 문서 조회"""
        document = self.document_repo.get_by_id(document_id)
        if not document:
            return None
        
        chunks = self.chunk_repo.get_by_document_id(document_id)
        
        # 링크 통계 (구현 예정)
        # summaries 통계 (구현 예정)
        
        return {
            'document': document,
            'chunk_count': len(chunks),
            'total_tokens': sum(chunk.token_len for chunk in chunks),
            'chunks': chunks
        }