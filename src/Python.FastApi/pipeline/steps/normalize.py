"""
문서 정규화 단계

다양한 형식의 문서를 표준화된 텍스트로 변환합니다.
- Markdown frontmatter 제거/보존
- HTML 태그 정리
- 인코딩 정규화
- 메타데이터 추출
"""

import re
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from core.logging import get_logger, log_execution_time

logger = get_logger(__name__)


@dataclass
class NormalizedContent:
    """정규화된 컨텐츠 결과"""
    text: str
    title: Optional[str] = None
    metadata: Dict[str, Any] = None
    word_count: int = 0
    character_count: int = 0


class DocumentNormalizer:
    """
    문서 정규화 처리기
    
    다양한 문서 형식을 처리하여 일관된 텍스트 형태로 변환합니다.
    """
    
    def __init__(self, preserve_frontmatter: bool = False, clean_whitespace: bool = True):
        self.preserve_frontmatter = preserve_frontmatter
        self.clean_whitespace = clean_whitespace
        
        # 정규표현식 패턴들 미리 컴파일
        self.frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        self.html_tag_pattern = re.compile(r'<[^>]+>')
        self.multiple_newlines = re.compile(r'\n\s*\n\s*\n', re.MULTILINE)
        self.multiple_spaces = re.compile(r'[ \t]+')
        
        logger.debug("DocumentNormalizer initialized", extra={
            "preserve_frontmatter": preserve_frontmatter,
            "clean_whitespace": clean_whitespace
        })
    
    @log_execution_time("문서 정규화")
    def normalize_file(self, file_path: str) -> NormalizedContent:
        """파일을 읽어서 정규화"""
        path = Path(file_path)
        
        # 파일 읽기
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # UTF-8 실패 시 다른 인코딩 시도
            try:
                with open(path, 'r', encoding='cp949') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(path, 'r', encoding='latin-1') as f:
                    content = f.read()
        
        return self.normalize_content(content, file_path=str(path))
    
    def normalize_content(self, content: str, file_path: str = None) -> NormalizedContent:
        """텍스트 컨텐츠 정규화"""
        original_length = len(content)
        
        # 메타데이터 추출
        metadata = {}
        title = None
        
        # Frontmatter 처리
        content, frontmatter_data = self._extract_frontmatter(content)
        if frontmatter_data:
            metadata.update(frontmatter_data)
            title = frontmatter_data.get('title')
        
        # 파일 경로에서 제목 추출 (frontmatter에 없는 경우)
        if not title and file_path:
            title = Path(file_path).stem
        
        # HTML 태그 제거
        content = self._clean_html_tags(content)
        
        # 공백 정규화
        if self.clean_whitespace:
            content = self._normalize_whitespace(content)
        
        # 통계 계산
        word_count = len(content.split())
        character_count = len(content)
        
        logger.debug("Content normalized", extra={
            "original_length": original_length,
            "normalized_length": character_count,
            "word_count": word_count,
            "title": title,
            "has_metadata": bool(metadata)
        })
        
        return NormalizedContent(
            text=content,
            title=title,
            metadata=metadata,
            word_count=word_count,
            character_count=character_count
        )
    
    def _extract_frontmatter(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """YAML frontmatter 추출"""
        metadata = {}
        
        match = self.frontmatter_pattern.match(content)
        if match:
            frontmatter_text = match.group(1)
            content = content[match.end():]
            
            # 간단한 YAML 파싱 (key: value 형태만)
            for line in frontmatter_text.split('\n'):
                line = line.strip()
                if ':' in line and not line.startswith('#'):
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    # 타입 변환 시도
                    if value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    elif value.isdigit():
                        value = int(value)
                    elif self._is_float(value):
                        value = float(value)
                    
                    metadata[key] = value
            
            if self.preserve_frontmatter:
                # frontmatter를 텍스트 끝에 메타데이터로 추가
                content = content + "\n\n--- Metadata ---\n" + frontmatter_text
        
        return content, metadata
    
    def _clean_html_tags(self, content: str) -> str:
        """HTML 태그 제거"""
        # 일부 태그는 의미있는 텍스트로 변환
        content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)
        content = re.sub(r'<hr\s*/?>', '\n---\n', content, flags=re.IGNORECASE)
        content = re.sub(r'<p\s*>', '\n', content, flags=re.IGNORECASE)
        content = re.sub(r'</p>', '\n', content, flags=re.IGNORECASE)
        
        # 나머지 HTML 태그 제거
        content = self.html_tag_pattern.sub('', content)
        
        # HTML 엔티티 디코딩
        content = self._decode_html_entities(content)
        
        return content
    
    def _normalize_whitespace(self, content: str) -> str:
        """공백 정규화"""
        # 연속된 공백을 단일 공백으로
        content = self.multiple_spaces.sub(' ', content)
        
        # 연속된 줄바꿈을 최대 2개로 제한
        content = self.multiple_newlines.sub('\n\n', content)
        
        # 줄 끝 공백 제거
        content = '\n'.join(line.rstrip() for line in content.split('\n'))
        
        # 전체 텍스트 앞뒤 공백 제거
        content = content.strip()
        
        return content
    
    def _decode_html_entities(self, content: str) -> str:
        """HTML 엔티티 디코딩"""
        entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
            '&nbsp;': ' ',
            '&#x27;': "'",
            '&#x2F;': '/',
        }
        
        for entity, char in entities.items():
            content = content.replace(entity, char)
        
        return content
    
    def _is_float(self, value: str) -> bool:
        """문자열이 float인지 확인"""
        try:
            float(value)
            return '.' in value
        except ValueError:
            return False
    
    def extract_title_from_content(self, content: str) -> Optional[str]:
        """컨텐츠에서 제목 추출"""
        lines = content.split('\n')
        
        for line in lines[:10]:  # 처음 10줄만 확인
            line = line.strip()
            
            # Markdown 헤딩
            if line.startswith('#'):
                return line.lstrip('#').strip()
            
            # 빈 줄이 아닌 첫 번째 줄을 제목으로 간주
            if line:
                # 너무 길거나 특수 문자가 많으면 제목이 아닐 가능성
                if len(line) < 100 and line.count('`') < 3:
                    return line
        
        return None
    
    def validate_content(self, content: str) -> Dict[str, Any]:
        """컨텐츠 품질 검증"""
        issues = []
        
        # 최소 길이 확인
        if len(content) < 50:
            issues.append("Content too short (< 50 characters)")
        
        # 최대 길이 확인
        if len(content) > 500000:  # 500KB
            issues.append("Content too long (> 500KB)")
        
        # 언어 추론 (간단한 방식)
        ascii_ratio = sum(1 for c in content if ord(c) < 128) / len(content)
        korean_char_count = sum(1 for c in content if '가' <= c <= '힣')
        korean_ratio = korean_char_count / len(content)
        
        language = "unknown"
        if korean_ratio > 0.1:
            language = "korean"
        elif ascii_ratio > 0.9:
            language = "english"
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "language": language,
            "ascii_ratio": round(ascii_ratio, 3),
            "korean_ratio": round(korean_ratio, 3),
            "line_count": len(content.split('\n'))
        }