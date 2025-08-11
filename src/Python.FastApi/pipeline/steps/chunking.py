"""
텍스트 청킹 (분절) 단계

긴 문서를 처리 가능한 크기의 청크로 분할합니다.
- 토큰 수 기반 분할
- 의미 단위 보존 (문단, 문장)
- 오버랩 지원
- 다양한 분할 전략
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass
from abc import ABC, abstractmethod

import tiktoken

from core.config import settings
from core.logging import get_logger, log_execution_time

logger = get_logger(__name__)


@dataclass
class Chunk:
    """청크 데이터 클래스"""
    text: str
    token_count: int
    start_char: int
    end_char: int
    hash: str
    metadata: Dict[str, Any] = None


@dataclass
class ChunkingResult:
    """청킹 결과"""
    chunks: List[Chunk]
    total_tokens: int
    avg_tokens_per_chunk: float
    overlap_tokens: int


class ChunkingStrategy(ABC):
    """청킹 전략 추상 클래스"""
    
    @abstractmethod
    def chunk(self, text: str, max_tokens: int, overlap_tokens: int = 0) -> List[Chunk]:
        pass


class TokenBasedChunking(ChunkingStrategy):
    """토큰 수 기반 청킹"""
    
    def __init__(self, encoding_name: str = "cl100k_base"):
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception:
            logger.warning(f"Failed to load encoding {encoding_name}, using fallback")
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        self.encoding_name = encoding_name
    
    def chunk(self, text: str, max_tokens: int, overlap_tokens: int = 0) -> List[Chunk]:
        """토큰 수 기반으로 텍스트 분할"""
        if not text.strip():
            return []
        
        # 전체 텍스트를 토큰화
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)
        
        if total_tokens <= max_tokens:
            # 단일 청크로 충분
            return [self._create_chunk(text, 0, len(text), tokens)]
        
        chunks = []
        start_token = 0
        
        while start_token < total_tokens:
            # 현재 청크의 토큰 범위 계산
            end_token = min(start_token + max_tokens, total_tokens)
            chunk_tokens = tokens[start_token:end_token]
            
            # 토큰을 텍스트로 디코드
            chunk_text = self.encoding.decode(chunk_tokens)
            
            # 문자 위치 계산 (근사치)
            start_char = self._estimate_char_position(text, start_token, tokens)
            end_char = start_char + len(chunk_text)
            
            chunk = self._create_chunk(chunk_text, start_char, end_char, chunk_tokens)
            chunks.append(chunk)
            
            # 다음 청크 시작 위치 (오버랩 고려)
            start_token = end_token - overlap_tokens
            
            # 무한 루프 방지
            if start_token >= end_token - 10:  # 최소 10토큰은 진행
                break
        
        return chunks
    
    def _estimate_char_position(self, text: str, token_position: int, all_tokens: List[int]) -> int:
        """토큰 위치에서 문자 위치 추정"""
        if token_position == 0:
            return 0
        
        # 토큰 일부를 디코드하여 문자 위치 추정
        partial_tokens = all_tokens[:token_position]
        partial_text = self.encoding.decode(partial_tokens)
        return len(partial_text)
    
    def _create_chunk(self, text: str, start_char: int, end_char: int, tokens: List[int]) -> Chunk:
        """청크 객체 생성"""
        return Chunk(
            text=text.strip(),
            token_count=len(tokens),
            start_char=start_char,
            end_char=end_char,
            hash=self._calculate_hash(text),
            metadata={"encoding": self.encoding_name}
        )
    
    def _calculate_hash(self, text: str) -> str:
        """텍스트 해시 계산"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()


class SentenceBasedChunking(ChunkingStrategy):
    """문장 기반 청킹 (의미 단위 보존)"""
    
    def __init__(self, encoding_name: str = "cl100k_base"):
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # 문장 분리 패턴 (한국어 + 영어)
        self.sentence_patterns = [
            r'[.!?]+\s+',  # 영어 문장 끝
            r'[.!?]+\n',   # 줄바꿈과 함께
            r'[。！？]+\s*',  # 일본어/중국어 문장 부호
            r'\.{3,}\s*',  # 생략 부호
        ]
        
        self.sentence_regex = re.compile('|'.join(self.sentence_patterns), re.MULTILINE)
    
    def chunk(self, text: str, max_tokens: int, overlap_tokens: int = 0) -> List[Chunk]:
        """문장 경계를 고려한 청킹"""
        if not text.strip():
            return []
        
        # 문장으로 분할
        sentences = self._split_sentences(text)
        
        if not sentences:
            # 문장 분할 실패 시 토큰 기반으로 fallback
            token_chunker = TokenBasedChunking(self.encoding.name)
            return token_chunker.chunk(text, max_tokens, overlap_tokens)
        
        chunks = []
        current_chunk = ""
        current_tokens = 0
        start_char = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.encoding.encode(sentence))
            
            # 현재 청크에 추가했을 때 최대 토큰을 초과하는지 확인
            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                # 현재 청크 완성
                chunk = self._create_chunk(current_chunk, start_char, start_char + len(current_chunk))
                chunks.append(chunk)
                
                # 오버랩 처리
                if overlap_tokens > 0 and chunks:
                    overlap_text = self._get_overlap_text(current_chunk, overlap_tokens)
                    current_chunk = overlap_text + " " + sentence
                    current_tokens = len(self.encoding.encode(current_chunk))
                else:
                    current_chunk = sentence
                    current_tokens = sentence_tokens
                    start_char += len(chunk.text)
            else:
                # 현재 청크에 추가
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_tokens += sentence_tokens
        
        # 마지막 청크 처리
        if current_chunk:
            chunk = self._create_chunk(current_chunk, start_char, start_char + len(current_chunk))
            chunks.append(chunk)
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """텍스트를 문장으로 분할"""
        sentences = []
        last_end = 0
        
        for match in self.sentence_regex.finditer(text):
            # 문장 추출
            sentence = text[last_end:match.end()].strip()
            if sentence:
                sentences.append(sentence)
            last_end = match.end()
        
        # 마지막 남은 텍스트
        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                sentences.append(remaining)
        
        # 너무 짧은 문장들을 병합
        return self._merge_short_sentences(sentences)
    
    def _merge_short_sentences(self, sentences: List[str], min_length: int = 20) -> List[str]:
        """너무 짧은 문장들 병합"""
        if not sentences:
            return sentences
        
        merged = []
        current = sentences[0]
        
        for next_sentence in sentences[1:]:
            if len(current) < min_length and len(merged) == 0:
                # 첫 번째가 너무 짧으면 다음과 병합
                current += " " + next_sentence
            elif len(next_sentence) < min_length:
                # 다음 문장이 너무 짧으면 현재와 병합
                current += " " + next_sentence
            else:
                merged.append(current)
                current = next_sentence
        
        merged.append(current)
        return merged
    
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """오버랩할 텍스트 추출"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= overlap_tokens:
            return text
        
        overlap_tokens_list = tokens[-overlap_tokens:]
        return self.encoding.decode(overlap_tokens_list)
    
    def _create_chunk(self, text: str, start_char: int, end_char: int) -> Chunk:
        """청크 객체 생성"""
        tokens = self.encoding.encode(text.strip())
        return Chunk(
            text=text.strip(),
            token_count=len(tokens),
            start_char=start_char,
            end_char=end_char,
            hash=hashlib.sha256(text.encode('utf-8')).hexdigest()
        )


class ParagraphBasedChunking(ChunkingStrategy):
    """문단 기반 청킹"""
    
    def __init__(self, encoding_name: str = "cl100k_base"):
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def chunk(self, text: str, max_tokens: int, overlap_tokens: int = 0) -> List[Chunk]:
        """문단 경계를 고려한 청킹"""
        if not text.strip():
            return []
        
        # 문단으로 분할 (빈 줄 기준)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        if not paragraphs:
            # 문단 분할 실패 시 문장 기반으로 fallback
            sentence_chunker = SentenceBasedChunking(self.encoding.name)
            return sentence_chunker.chunk(text, max_tokens, overlap_tokens)
        
        chunks = []
        current_chunk = ""
        current_tokens = 0
        start_char = 0
        
        for paragraph in paragraphs:
            paragraph_tokens = len(self.encoding.encode(paragraph))
            
            # 단일 문단이 최대 토큰을 초과하는 경우
            if paragraph_tokens > max_tokens:
                # 현재 청크가 있으면 먼저 완성
                if current_chunk:
                    chunk = self._create_chunk(current_chunk, start_char, start_char + len(current_chunk))
                    chunks.append(chunk)
                    start_char += len(chunk.text) + 2  # \n\n
                    current_chunk = ""
                    current_tokens = 0
                
                # 긴 문단을 문장 기준으로 분할
                sentence_chunker = SentenceBasedChunking(self.encoding.name)
                paragraph_chunks = sentence_chunker.chunk(paragraph, max_tokens, overlap_tokens)
                
                for pchunk in paragraph_chunks:
                    pchunk.start_char += start_char
                    pchunk.end_char += start_char
                    chunks.append(pchunk)
                    start_char = pchunk.end_char + 2
                
            elif current_tokens + paragraph_tokens > max_tokens and current_chunk:
                # 현재 청크 완성
                chunk = self._create_chunk(current_chunk, start_char, start_char + len(current_chunk))
                chunks.append(chunk)
                start_char += len(chunk.text) + 2
                
                current_chunk = paragraph
                current_tokens = paragraph_tokens
            else:
                # 현재 청크에 추가
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_tokens += paragraph_tokens
        
        # 마지막 청크
        if current_chunk:
            chunk = self._create_chunk(current_chunk, start_char, start_char + len(current_chunk))
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, text: str, start_char: int, end_char: int) -> Chunk:
        """청크 객체 생성"""
        tokens = self.encoding.encode(text.strip())
        return Chunk(
            text=text.strip(),
            token_count=len(tokens),
            start_char=start_char,
            end_char=end_char,
            hash=hashlib.sha256(text.encode('utf-8')).hexdigest()
        )


class DocumentChunker:
    """
    문서 청킹 메인 클래스
    
    다양한 청킹 전략을 제공하고 설정에 따라 적절한 전략을 선택합니다.
    """
    
    def __init__(self):
        self.max_tokens = settings.chunk_max_tokens
        self.overlap_tokens = settings.chunk_overlap_tokens
        self.min_tokens = settings.chunk_min_tokens
        
        self.strategies = {
            'token': TokenBasedChunking(),
            'sentence': SentenceBasedChunking(), 
            'paragraph': ParagraphBasedChunking()
        }
        
        logger.info("DocumentChunker initialized", extra={
            "max_tokens": self.max_tokens,
            "overlap_tokens": self.overlap_tokens,
            "min_tokens": self.min_tokens,
            "available_strategies": list(self.strategies.keys())
        })
    
    @log_execution_time("문서 청킹")
    def chunk_document(self, text: str, strategy: str = 'sentence') -> ChunkingResult:
        """
        문서를 청크로 분할
        
        Args:
            text: 분할할 텍스트
            strategy: 청킹 전략 ('token', 'sentence', 'paragraph')
            
        Returns:
            ChunkingResult: 청킹 결과
        """
        if not text.strip():
            return ChunkingResult(chunks=[], total_tokens=0, avg_tokens_per_chunk=0, overlap_tokens=0)
        
        # 전략 선택
        chunking_strategy = self.strategies.get(strategy, self.strategies['sentence'])
        
        # 청킹 수행
        chunks = chunking_strategy.chunk(text, self.max_tokens, self.overlap_tokens)
        
        # 너무 작은 청크 필터링
        filtered_chunks = [chunk for chunk in chunks if chunk.token_count >= self.min_tokens]
        
        # 통계 계산
        total_tokens = sum(chunk.token_count for chunk in filtered_chunks)
        avg_tokens = total_tokens / len(filtered_chunks) if filtered_chunks else 0
        
        logger.info("Document chunked", extra={
            "strategy": strategy,
            "original_length": len(text),
            "chunk_count": len(filtered_chunks),
            "total_tokens": total_tokens,
            "avg_tokens_per_chunk": round(avg_tokens, 1),
            "filtered_out": len(chunks) - len(filtered_chunks)
        })
        
        return ChunkingResult(
            chunks=filtered_chunks,
            total_tokens=total_tokens,
            avg_tokens_per_chunk=avg_tokens,
            overlap_tokens=self.overlap_tokens
        )
    
    def estimate_chunk_count(self, text: str) -> int:
        """텍스트의 예상 청크 수 계산"""
        if not text.strip():
            return 0
        
        # 토큰 수 추정 (정확한 계산은 비용이 크므로)
        estimated_tokens = len(text) // 3  # 영어 기준 대략적인 추정
        return max(1, estimated_tokens // self.max_tokens)
    
    def validate_chunks(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """청크 품질 검증"""
        if not chunks:
            return {"valid": False, "issues": ["No chunks generated"]}
        
        issues = []
        stats = {
            "token_counts": [chunk.token_count for chunk in chunks],
            "text_lengths": [len(chunk.text) for chunk in chunks]
        }
        
        # 토큰 수 검증
        for i, chunk in enumerate(chunks):
            if chunk.token_count > self.max_tokens:
                issues.append(f"Chunk {i} exceeds max tokens: {chunk.token_count}")
            elif chunk.token_count < self.min_tokens:
                issues.append(f"Chunk {i} below min tokens: {chunk.token_count}")
        
        # 중복 검증
        hashes = [chunk.hash for chunk in chunks]
        if len(set(hashes)) != len(hashes):
            issues.append("Duplicate chunks detected")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "stats": stats,
            "chunk_count": len(chunks),
            "avg_tokens": sum(stats["token_counts"]) / len(stats["token_counts"]) if chunks else 0
        }