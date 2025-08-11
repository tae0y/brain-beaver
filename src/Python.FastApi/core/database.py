"""
데이터베이스 연결 및 세션 관리

SQLAlchemy를 통한 PostgreSQL 연결을 관리하며,
비동기 처리와 커넥션 풀링을 지원합니다.
"""

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

from core.config import settings
from core.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    데이터베이스 연결 관리자
    
    커넥션 풀과 세션 팩토리를 관리하며,
    애플리케이션 시작/종료 시 연결 생성/해제를 담당합니다.
    """
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self):
        """데이터베이스 엔진 및 세션 팩토리 초기화"""
        if self._initialized:
            return
        
        logger.info(f"Initializing database connection to {settings.database_url}")
        
        # PostgreSQL 엔진 생성
        self.engine = create_engine(
            settings.database_url,
            poolclass=QueuePool,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,  # 연결 상태 확인
            pool_recycle=3600,   # 1시간마다 연결 재생성
            echo=settings.debug,  # SQL 로그 출력 (디버그 시에만)
        )
        
        # 세션 팩토리 생성
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self._initialized = True
        logger.info("Database connection initialized successfully")
    
    def create_tables(self):
        """테이블 생성 (개발용 - 프로덕션에서는 Alembic 사용)"""
        if not self._initialized:
            self.initialize()
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def check_connection(self) -> bool:
        """데이터베이스 연결 상태 확인"""
        if not self._initialized:
            return False
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.engine:
            logger.info("Closing database connections...")
            self.engine.dispose()
            logger.info("Database connections closed")


# 전역 데이터베이스 관리자 인스턴스
db_manager = DatabaseManager()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 컨텍스트 매니저
    
    자동으로 트랜잭션을 관리하고 예외 발생 시 롤백을 수행합니다.
    
    Usage:
        with get_db_session() as session:
            # 데이터베이스 작업 수행
            user = session.query(User).first()
    """
    if not db_manager._initialized:
        db_manager.initialize()
    
    session = db_manager.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session_dependency():
    """
    FastAPI 의존성 주입용 데이터베이스 세션 팩토리
    
    FastAPI 라우터에서 다음과 같이 사용:
        @app.get("/users/")
        def get_users(db: Session = Depends(get_db_session_dependency)):
            return db.query(User).all()
    """
    if not db_manager._initialized:
        db_manager.initialize()
    
    session = db_manager.SessionLocal()
    try:
        yield session
    finally:
        session.close()


class DatabaseOperations:
    """
    공통 데이터베이스 작업을 위한 유틸리티 클래스
    """
    
    @staticmethod
    def execute_raw_sql(sql: str, params: dict = None) -> list:
        """원시 SQL 실행"""
        with get_db_session() as session:
            result = session.execute(text(sql), params or {})
            return result.fetchall()
    
    @staticmethod
    def check_table_exists(table_name: str) -> bool:
        """테이블 존재 여부 확인"""
        sql = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        );
        """
        result = DatabaseOperations.execute_raw_sql(sql, {"table_name": table_name})
        return result[0][0] if result else False
    
    @staticmethod
    def get_table_row_count(table_name: str) -> int:
        """테이블 행 수 조회"""
        sql = f"SELECT COUNT(*) FROM {table_name}"
        result = DatabaseOperations.execute_raw_sql(sql)
        return result[0][0] if result else 0
    
    @staticmethod
    def vacuum_analyze(table_name: str = None):
        """테이블 최적화 (VACUUM ANALYZE)"""
        with get_db_session() as session:
            if table_name:
                session.execute(text(f"VACUUM ANALYZE {table_name}"))
            else:
                session.execute(text("VACUUM ANALYZE"))
            session.commit()


def init_database():
    """
    애플리케이션 시작 시 데이터베이스 초기화
    
    - 연결 확인
    - 필요 시 테이블 생성 (개발 환경)
    - pgvector extension 활성화 (설정된 경우)
    """
    logger.info("Initializing database...")
    
    # 데이터베이스 매니저 초기화
    db_manager.initialize()
    
    # 연결 확인
    if not db_manager.check_connection():
        raise Exception("Failed to connect to database")
    
    # pgvector extension 활성화 (필요한 경우)
    if settings.enable_pgvector:
        try:
            with get_db_session() as session:
                session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                session.commit()
                logger.info("pgvector extension enabled")
        except SQLAlchemyError as e:
            logger.warning(f"Failed to enable pgvector extension: {e}")
    
    # 개발 환경에서는 테이블 자동 생성 (프로덕션에서는 Alembic 사용)
    if settings.environment.value == "development":
        logger.info("Development mode: creating tables if not exist")
        db_manager.create_tables()
    
    logger.info("Database initialization completed")


def close_database():
    """애플리케이션 종료 시 데이터베이스 연결 해제"""
    logger.info("Closing database connections...")
    db_manager.close()
    logger.info("Database connections closed")