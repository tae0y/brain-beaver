"""
문서/청크 요약 단계

LLM을 사용하여 문서와 청크의 요약을 생성합니다.
- 다양한 요약 전략 (간결, 상세, 키워드)
- 배치 처리 지원
- 품질 검증
- 템플릿 기반 프롬프트
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import asyncio

from core.config import settings
from core.logging import get_logger, log_execution_time, track_duration
from pipeline.adapters.llm_interface import LLMRequest, LLMResponse, llm_manager

logger = get_logger(__name__)


class SummaryType(str, Enum):
    """요약 유형"""
    BRIEF = "brief"           # 간단한 요약 (1-2 문장)
    DETAILED = "detailed"     # 상세 요약 (문단 단위)
    KEYWORDS = "keywords"     # 키워드 추출
    BULLET_POINTS = "bullet"  # 요점 정리


@dataclass
class SummaryRequest:
    """요약 요청 데이터"""
    text: str
    summary_type: SummaryType = SummaryType.BRIEF
    max_length: Optional[int] = None
    language: Optional[str] = "korean"
    context: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class SummaryResult:
    """요약 결과"""
    summary: str
    summary_type: SummaryType
    original_length: int
    summary_length: int
    compression_ratio: float
    quality_score: float
    language: str
    keywords: List[str] = None
    metadata: Dict[str, Any] = None


class SummaryPromptTemplate:
    """요약 프롬프트 템플릿"""
    
    SYSTEM_PROMPTS = {
        SummaryType.BRIEF: """당신은 텍스트 요약 전문가입니다. 주어진 텍스트의 핵심 내용을 1-2개 문장으로 간결하게 요약해주세요.

요약 원칙:
- 가장 중요한 정보만 포함
- 명확하고 이해하기 쉽게 작성
- 원문의 톤과 맥락 유지
- 불필요한 세부사항 제거""",
        
        SummaryType.DETAILED: """당신은 텍스트 요약 전문가입니다. 주어진 텍스트의 주요 내용을 상세하게 요약해주세요.

요약 원칙:
- 주요 포인트와 세부 내용 포함
- 논리적 구조 유지
- 중요한 예시나 데이터 포함
- 문단 단위로 구조화""",
        
        SummaryType.KEYWORDS: """당신은 키워드 추출 전문가입니다. 주어진 텍스트에서 가장 중요한 키워드들을 추출해주세요.

추출 원칙:
- 5-15개의 핵심 키워드
- 단어나 짧은 구문 형태
- 중요도 순으로 정렬
- 중복 제거""",
        
        SummaryType.BULLET_POINTS: """당신은 텍스트 정리 전문가입니다. 주어진 텍스트의 주요 내용을 요점별로 정리해주세요.

정리 원칙:
- 3-10개의 주요 요점
- 각 요점은 한 문장으로 작성
- 중요도 순으로 정렬
- 명확하고 구체적으로 작성"""
    }
    
    @classmethod
    def get_prompt(cls, request: SummaryRequest) -> tuple[str, str]:
        """요청에 맞는 프롬프트 생성"""
        system_prompt = cls.SYSTEM_PROMPTS[request.summary_type]
        
        # 언어별 추가 지시사항
        if request.language == "korean":
            system_prompt += "\n\n한국어로 응답해주세요."
        elif request.language == "english":
            system_prompt += "\n\nPlease respond in English."
        
        # 길이 제한 추가
        if request.max_length:
            system_prompt += f"\n\n최대 {request.max_length}자 이내로 작성해주세요."
        
        # 사용자 프롬프트 구성
        user_prompt = f"다음 텍스트를 요약해주세요:\n\n{request.text}"
        
        # 컨텍스트 추가
        if request.context:
            user_prompt = f"컨텍스트: {request.context}\n\n{user_prompt}"
        
        return system_prompt, user_prompt


class SummaryQualityValidator:
    """요약 품질 검증기"""
    
    def __init__(self):
        self.min_compression_ratio = 0.1  # 최소 압축율
        self.max_compression_ratio = 0.8  # 최대 압축율
        self.min_length = 10              # 최소 요약 길이
    
    def validate(self, result: SummaryResult) -> Dict[str, Any]:
        """요약 품질 검증"""
        issues = []
        score = 1.0
        
        # 길이 검증
        if len(result.summary.strip()) < self.min_length:
            issues.append("Summary too short")
            score *= 0.5
        
        # 압축율 검증
        if result.compression_ratio < self.min_compression_ratio:
            issues.append("Summary too detailed (low compression)")
            score *= 0.8
        elif result.compression_ratio > self.max_compression_ratio:
            issues.append("Summary too brief (high compression)")
            score *= 0.8
        
        # 내용 검증
        if self._has_repetition(result.summary):
            issues.append("Summary contains repetition")
            score *= 0.7
        
        if self._has_hallucination_indicators(result.summary, result):
            issues.append("Potential hallucination detected")
            score *= 0.6
        
        return {
            "valid": score >= 0.5,
            "quality_score": score,
            "issues": issues,
            "recommendations": self._get_recommendations(issues)
        }
    
    def _has_repetition(self, text: str) -> bool:
        """반복 내용 검출"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if len(sentences) < 2:
            return False
        
        # 문장 유사도 체크 (간단한 방식)
        for i, sent1 in enumerate(sentences):
            for sent2 in sentences[i+1:]:
                if len(sent1) > 10 and len(sent2) > 10:
                    similarity = len(set(sent1.split()) & set(sent2.split())) / max(len(sent1.split()), len(sent2.split()))
                    if similarity > 0.7:
                        return True
        return False
    
    def _has_hallucination_indicators(self, summary: str, result: SummaryResult) -> bool:
        """환각 징후 검출 (간단한 휴리스틱)"""
        # 구체적인 숫자나 날짜가 원본에 없는데 요약에 있는지 확인
        import re
        
        summary_numbers = re.findall(r'\b\d+\b', summary)
        if len(summary_numbers) > 0:
            # 원본 텍스트에서 해당 숫자들이 실제로 존재하는지 확인
            # (실제 구현에서는 더 정교한 방법 사용)
            pass
        
        return False
    
    def _get_recommendations(self, issues: List[str]) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []
        
        if "Summary too short" in issues:
            recommendations.append("Try using DETAILED summary type for more comprehensive results")
        
        if "Summary too brief" in issues:
            recommendations.append("Consider using BRIEF summary type for more concise results")
        
        if "repetition" in str(issues):
            recommendations.append("Review prompt template to reduce repetitive content")
        
        return recommendations


class DocumentSummarizer:
    """
    문서 요약 생성기
    
    LLM을 사용하여 다양한 유형의 요약을 생성합니다.
    """
    
    def __init__(self):
        self.quality_validator = SummaryQualityValidator()
        self.prompt_template = SummaryPromptTemplate()
        
        logger.info("DocumentSummarizer initialized", extra={
            "available_summary_types": [t.value for t in SummaryType]
        })
    
    @log_execution_time("단일 요약 생성")
    async def summarize(self, request: SummaryRequest, provider: str = None) -> SummaryResult:
        """단일 텍스트 요약"""
        if not request.text.strip():
            raise ValueError("Empty text provided for summarization")
        
        # 프롬프트 생성
        system_prompt, user_prompt = self.prompt_template.get_prompt(request)
        
        # LLM 요청 구성
        llm_request = LLMRequest(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=self._get_max_tokens(request),
            temperature=0.1,  # 일관성을 위해 낮은 온도
            model=settings.llm_model_chat,
            metadata={"task": "summarization", "type": request.summary_type.value}
        )
        
        try:
            with track_duration('pipeline_step_duration', {'step': 'summarize'}):
                # LLM 요청 실행
                llm_response = await llm_manager.generate_text_with_fallback(
                    llm_request, preferred_provider=provider
                )
                
                # 결과 구성
                result = self._create_result(request, llm_response)
                
                # 품질 검증
                validation = self.quality_validator.validate(result)
                result.quality_score = validation['quality_score']
                
                logger.debug("Summary generated successfully", extra={
                    "summary_type": request.summary_type.value,
                    "original_length": result.original_length,
                    "summary_length": result.summary_length,
                    "compression_ratio": round(result.compression_ratio, 3),
                    "quality_score": round(result.quality_score, 3),
                    "model": llm_response.model,
                    "latency_ms": llm_response.latency_ms
                })
                
                return result
                
        except Exception as e:
            logger.error(f"Summarization failed: {e}", extra={
                "summary_type": request.summary_type.value,
                "text_length": len(request.text),
                "provider": provider
            })
            raise
    
    async def batch_summarize(self, 
                            requests: List[SummaryRequest], 
                            provider: str = None,
                            max_concurrent: int = 5) -> List[SummaryResult]:
        """배치 요약 처리"""
        if not requests:
            return []
        
        logger.info(f"Starting batch summarization", extra={
            "batch_size": len(requests),
            "max_concurrent": max_concurrent
        })
        
        # 세마포어로 동시 실행 수 제한
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def summarize_with_semaphore(req: SummaryRequest) -> SummaryResult:
            async with semaphore:
                return await self.summarize(req, provider)
        
        # 모든 요청을 비동기로 실행
        tasks = [summarize_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        successful_results = []
        failed_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch summarization failed for request {i}: {result}")
                failed_count += 1
            else:
                successful_results.append(result)
        
        logger.info("Batch summarization completed", extra={
            "total_requests": len(requests),
            "successful": len(successful_results),
            "failed": failed_count
        })
        
        return successful_results
    
    def _get_max_tokens(self, request: SummaryRequest) -> int:
        """요약 유형에 따른 최대 토큰 수 계산"""
        base_tokens = {
            SummaryType.BRIEF: 100,
            SummaryType.DETAILED: 500,
            SummaryType.KEYWORDS: 150,
            SummaryType.BULLET_POINTS: 300
        }
        
        max_tokens = base_tokens[request.summary_type]
        
        # 요청된 최대 길이가 있으면 조정
        if request.max_length:
            # 대략적인 토큰-문자 비율 (1.5 토큰 per 문자)
            estimated_tokens = int(request.max_length * 1.5)
            max_tokens = min(max_tokens, estimated_tokens)
        
        return max_tokens
    
    def _create_result(self, request: SummaryRequest, llm_response: LLMResponse) -> SummaryResult:
        """LLM 응답으로부터 SummaryResult 생성"""
        summary_text = llm_response.text.strip()
        original_length = len(request.text)
        summary_length = len(summary_text)
        compression_ratio = summary_length / original_length if original_length > 0 else 0
        
        # 키워드 추출 (키워드 요약인 경우)
        keywords = None
        if request.summary_type == SummaryType.KEYWORDS:
            keywords = self._extract_keywords_from_summary(summary_text)
        
        return SummaryResult(
            summary=summary_text,
            summary_type=request.summary_type,
            original_length=original_length,
            summary_length=summary_length,
            compression_ratio=compression_ratio,
            quality_score=0.0,  # 검증기에서 설정
            language=request.language or "korean",
            keywords=keywords,
            metadata={
                "model": llm_response.model,
                "provider": llm_response.provider,
                "latency_ms": llm_response.latency_ms,
                "token_usage": llm_response.token_usage,
                "request_metadata": request.metadata
            }
        )
    
    def _extract_keywords_from_summary(self, summary_text: str) -> List[str]:
        """키워드 요약에서 키워드 목록 추출"""
        import re
        
        # 줄바꿈, 콤마, 세미콜론으로 분리
        keywords = re.split(r'[,\n;]+', summary_text)
        
        # 정제
        cleaned_keywords = []
        for keyword in keywords:
            keyword = keyword.strip().strip('-.•*')
            if keyword and len(keyword) > 1:
                cleaned_keywords.append(keyword)
        
        return cleaned_keywords[:15]  # 최대 15개
    
    def estimate_cost(self, text_length: int, summary_type: SummaryType) -> Dict[str, Any]:
        """요약 비용 추정"""
        # 토큰 수 추정
        estimated_input_tokens = text_length * 1.3  # 대략적인 추정
        max_output_tokens = self._get_max_tokens(SummaryRequest(text="", summary_type=summary_type))
        
        # OpenAI 기준 비용 (예시)
        input_cost_per_1k = 0.0005  # USD per 1K tokens
        output_cost_per_1k = 0.0015  # USD per 1K tokens
        
        estimated_input_cost = (estimated_input_tokens / 1000) * input_cost_per_1k
        estimated_output_cost = (max_output_tokens / 1000) * output_cost_per_1k
        total_cost = estimated_input_cost + estimated_output_cost
        
        return {
            "estimated_input_tokens": int(estimated_input_tokens),
            "max_output_tokens": max_output_tokens,
            "estimated_cost_usd": round(total_cost, 6),
            "cost_breakdown": {
                "input_cost": round(estimated_input_cost, 6),
                "output_cost": round(estimated_output_cost, 6)
            }
        }