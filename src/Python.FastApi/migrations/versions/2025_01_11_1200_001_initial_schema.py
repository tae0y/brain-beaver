"""Initial schema creation

Revision ID: 001
Revises: 
Create Date: 2025-01-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import os

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# pgvector 지원 여부 확인
ENABLE_PGVECTOR = os.getenv("ENABLE_PGVECTOR", "false").lower() == "true"

def upgrade() -> None:
    # pgvector extension 생성 (선택사항)
    if ENABLE_PGVECTOR:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # documents 테이블 생성
    op.create_table('documents',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('source_type', sa.String(length=10), nullable=False),
        sa.Column('uri', sa.String(length=2000), nullable=False),
        sa.Column('path', sa.String(length=2000), nullable=True),
        sa.Column('url', sa.String(length=2000), nullable=True),
        sa.Column('mtime', sa.DateTime(), nullable=True),
        sa.Column('size', sa.BigInteger(), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("source_type IN ('file', 'web')", name='ck_documents_source_type'),
        sa.CheckConstraint("status IN ('pending', 'processed', 'failed')", name='ck_documents_status'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_documents_uri', 'documents', ['uri'], unique=True)
    op.create_index('ix_documents_content_hash', 'documents', ['content_hash'])
    op.create_index('ix_documents_status', 'documents', ['status'])

    # chunks 테이블 생성
    op.create_table('chunks',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('ordinal', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('token_len', sa.Integer(), nullable=False),
        sa.Column('hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'ordinal', name='uq_chunk_document_ordinal')
    )
    op.create_index('ix_chunks_document_id', 'chunks', ['document_id'])
    op.create_index('ix_chunks_hash', 'chunks', ['hash'])
    op.create_index('ix_chunks_document_ordinal', 'chunks', ['document_id', 'ordinal'])

    # summaries 테이블 생성
    op.create_table('summaries',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('chunk_id', sa.BigInteger(), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_summaries_document_id', 'summaries', ['document_id'])
    op.create_index('ix_summaries_chunk_id', 'summaries', ['chunk_id'])

    # embeddings 테이블 생성
    if ENABLE_PGVECTOR:
        # pgvector 지원 시
        op.create_table('embeddings',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('chunk_id', sa.BigInteger(), nullable=False),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('model', sa.String(length=100), nullable=False),
            sa.Column('dim', sa.Integer(), nullable=False),
            sa.Column('vector', postgresql.ARRAY(sa.Float()), nullable=False),  # pgvector는 런타임에 처리
            sa.Column('vector_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('chunk_id', 'provider', 'model', name='uq_embedding_chunk_provider_model')
        )
    else:
        # JSON 저장 방식
        op.create_table('embeddings',
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('chunk_id', sa.BigInteger(), nullable=False),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('model', sa.String(length=100), nullable=False),
            sa.Column('dim', sa.Integer(), nullable=False),
            sa.Column('vector', sa.JSON(), nullable=False),
            sa.Column('vector_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('chunk_id', 'provider', 'model', name='uq_embedding_chunk_provider_model')
        )
    
    op.create_index('ix_embeddings_chunk_id', 'embeddings', ['chunk_id'])
    op.create_index('ix_embeddings_provider_model', 'embeddings', ['provider', 'model'])

    # links 테이블 생성
    op.create_table('links',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('src_chunk_id', sa.BigInteger(), nullable=False),
        sa.Column('dst_chunk_id', sa.BigInteger(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('link_type', sa.String(length=20), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("link_type IN ('explicit', 'semantic')", name='ck_links_link_type'),
        sa.ForeignKeyConstraint(['dst_chunk_id'], ['chunks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['src_chunk_id'], ['chunks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('src_chunk_id', 'dst_chunk_id', 'link_type', name='uq_link_src_dst_type')
    )
    op.create_index('ix_links_src_chunk', 'links', ['src_chunk_id'])
    op.create_index('ix_links_dst_chunk', 'links', ['dst_chunk_id'])
    op.create_index('ix_links_score', 'links', ['score'])

    # jobs 테이블 생성
    op.create_table('jobs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('params', sa.JSON(), nullable=False),
        sa.Column('state', sa.String(length=20), nullable=False),
        sa.Column('progress', sa.Float(), nullable=False),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.Column('succeeded', sa.Integer(), nullable=False),
        sa.Column('failed', sa.Integer(), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("kind IN ('scan', 'process', 'crawl')", name='ck_jobs_kind'),
        sa.CheckConstraint("state IN ('queued', 'running', 'succeeded', 'failed', 'canceled')", name='ck_jobs_state'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_jobs_kind', 'jobs', ['kind'])
    op.create_index('ix_jobs_state', 'jobs', ['state'])
    op.create_index('ix_jobs_kind_state', 'jobs', ['kind', 'state'])
    op.create_index('ix_jobs_created_at', 'jobs', ['created_at'])

    # url_cache 테이블 생성
    op.create_table('url_cache',
        sa.Column('url', sa.String(length=2000), nullable=False),
        sa.Column('url_hash', sa.String(length=64), nullable=False),
        sa.Column('etag', sa.String(length=200), nullable=True),
        sa.Column('last_modified', sa.String(length=100), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('url')
    )
    op.create_index('ix_url_cache_url_hash', 'url_cache', ['url_hash'], unique=True)
    op.create_index('ix_url_cache_fetched_at', 'url_cache', ['fetched_at'])
    op.create_index('ix_url_cache_status_code', 'url_cache', ['status_code'])


def downgrade() -> None:
    op.drop_table('url_cache')
    op.drop_table('jobs')
    op.drop_table('links')
    op.drop_table('embeddings')
    op.drop_table('summaries')
    op.drop_table('chunks')
    op.drop_table('documents')
    
    if ENABLE_PGVECTOR:
        op.execute("DROP EXTENSION IF EXISTS vector;")