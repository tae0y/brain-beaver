"""
LLM 프로바이더 인터페이스

다양한 LLM 프로바이더들을 통합하는 추상화 계층을 제공합니다.
- OpenAI API
- Ollama 로컬 모델
- 향후 다른 프로바이더 확장 가능
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import time
import asyncio
from contextlib import asynccontextmanager

from core.logging import get_logger, track_metric, track_duration

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """지원되는 LLM 프로바이더"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    LOCAL = "local"


@dataclass
class LLMRequest:
    """LLM 요청 데이터"""
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.1
    model: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class LLMResponse:
    """LLM 응답 데이터"""
    text: str
    model: str
    provider: str
    token_usage: Dict[str, int] = None
    latency_ms: float = 0
    metadata: Dict[str, Any] = None


@dataclass
class EmbeddingRequest:
    """임베딩 요청 데이터"""
    texts: Union[str, List[str]]
    model: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class EmbeddingResponse:
    """임베딩 응답 데이터"""
    embeddings: Union[List[float], List[List[float]]]
    model: str
    provider: str
    dimension: int
    token_usage: Dict[str, int] = None
    latency_ms: float = 0


class LLMProviderInterface(ABC):
    """LLM 프로바이더 추상 인터페이스"""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """프로바이더 이름"""
        pass
    
    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """사용 가능한 모델 목록"""
        pass
    
    @abstractmethod
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """텍스트 생성"""
        pass
    
    @abstractmethod
    async def generate_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """임베딩 생성"""
        pass
    
    @abstractmethod
    async def batch_generate_embeddings(self, requests: List[EmbeddingRequest]) -> List[EmbeddingResponse]:
        """배치 임베딩 생성"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """프로바이더 사용 가능 여부"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        pass


class RetryableLLMProvider(ABC):
    """재시도 가능한 LLM 프로바이더 기본 클래스"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def _execute_with_retry(self, operation, *args, **kwargs):
        """지수 백오프와 함께 재시도 실행"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    break
                
                delay = self.base_delay * (2 ** attempt)
                logger.warning(f"LLM request failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                logger.info(f"Retrying in {delay:.1f} seconds...")
                
                await asyncio.sleep(delay)
        
        logger.error(f"LLM request failed after {self.max_retries + 1} attempts")
        raise last_exception
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """재시도 가능한 에러인지 판단"""
        # 네트워크 에러, 타임아웃, 레이트 리밋 등은 재시도 가능
        error_message = str(error).lower()
        retryable_keywords = [
            'timeout', 'connection', 'network', 'rate limit', 'server error',
            '429', '500', '502', '503', '504'
        ]
        
        return any(keyword in error_message for keyword in retryable_keywords)


class LLMManager:
    """
    LLM 프로바이더 관리자
    
    여러 프로바이더를 관리하고 로드 밸런싱, 폴백 등을 처리합니다.
    """
    
    def __init__(self):
        self.providers: Dict[str, LLMProviderInterface] = {}
        self.primary_provider = None
        self.fallback_providers = []
        
    def register_provider(self, provider: LLMProviderInterface, is_primary: bool = False):
        """프로바이더 등록"""
        self.providers[provider.provider_name] = provider
        
        if is_primary:
            self.primary_provider = provider.provider_name
        else:
            self.fallback_providers.append(provider.provider_name)
        
        logger.info(f"LLM provider registered: {provider.provider_name}", extra={
            "is_primary": is_primary,
            "available_models": provider.available_models
        })
    
    def get_provider(self, provider_name: str = None) -> LLMProviderInterface:
        """프로바이더 반환"""
        if provider_name:
            provider = self.providers.get(provider_name)
            if not provider:
                raise ValueError(f"Provider not found: {provider_name}")
            return provider
        
        # 기본 프로바이더 반환
        if self.primary_provider:
            return self.providers[self.primary_provider]
        
        # 사용 가능한 첫 번째 프로바이더 반환
        for provider in self.providers.values():
            if provider.is_available():
                return provider
        
        raise RuntimeError("No available LLM provider")
    
    async def generate_text_with_fallback(self, request: LLMRequest, preferred_provider: str = None) -> LLMResponse:
        """폴백과 함께 텍스트 생성"""
        providers_to_try = []
        
        # 선호 프로바이더가 있으면 먼저 시도
        if preferred_provider and preferred_provider in self.providers:
            providers_to_try.append(preferred_provider)
        
        # 기본 프로바이더 추가
        if self.primary_provider and self.primary_provider not in providers_to_try:
            providers_to_try.append(self.primary_provider)
        
        # 폴백 프로바이더들 추가
        for provider_name in self.fallback_providers:
            if provider_name not in providers_to_try:
                providers_to_try.append(provider_name)
        
        last_error = None
        
        for provider_name in providers_to_try:
            provider = self.providers.get(provider_name)
            if not provider or not provider.is_available():
                continue
            
            try:
                with track_duration('llm_duration', {'provider': provider_name, 'model': request.model or 'default'}):
                    response = await provider.generate_text(request)
                    
                    track_metric('llm_requests', {
                        'provider': provider_name,
                        'model': response.model,
                        'status': 'success'
                    })
                    
                    return response
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Text generation failed with {provider_name}: {e}")
                
                track_metric('llm_requests', {
                    'provider': provider_name,
                    'model': request.model or 'unknown',
                    'status': 'error'
                })
        
        # 모든 프로바이더 실패
        logger.error("All LLM providers failed for text generation")
        if last_error:
            raise last_error
        else:
            raise RuntimeError("No available LLM provider for text generation")
    
    async def generate_embedding_with_fallback(self, request: EmbeddingRequest, preferred_provider: str = None) -> EmbeddingResponse:
        """폴백과 함께 임베딩 생성"""
        providers_to_try = []
        
        if preferred_provider and preferred_provider in self.providers:
            providers_to_try.append(preferred_provider)
        
        if self.primary_provider and self.primary_provider not in providers_to_try:
            providers_to_try.append(self.primary_provider)
        
        for provider_name in self.fallback_providers:
            if provider_name not in providers_to_try:
                providers_to_try.append(provider_name)
        
        last_error = None
        
        for provider_name in providers_to_try:
            provider = self.providers.get(provider_name)
            if not provider or not provider.is_available():
                continue
            
            try:
                with track_duration('llm_duration', {'provider': provider_name, 'model': request.model or 'default'}):
                    response = await provider.generate_embedding(request)
                    
                    track_metric('llm_requests', {
                        'provider': provider_name,
                        'model': response.model,
                        'status': 'success'
                    })
                    
                    return response
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Embedding generation failed with {provider_name}: {e}")
                
                track_metric('llm_requests', {
                    'provider': provider_name,
                    'model': request.model or 'unknown',
                    'status': 'error'
                })
        
        logger.error("All LLM providers failed for embedding generation")
        if last_error:
            raise last_error
        else:
            raise RuntimeError("No available LLM provider for embedding generation")
    
    async def batch_generate_embeddings(self, 
                                      requests: List[EmbeddingRequest], 
                                      preferred_provider: str = None,
                                      batch_size: int = 10) -> List[EmbeddingResponse]:
        """배치 임베딩 생성"""
        provider = self.get_provider(preferred_provider)
        
        # 배치 크기에 따라 분할 처리
        responses = []
        
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            
            try:
                batch_responses = await provider.batch_generate_embeddings(batch)
                responses.extend(batch_responses)
                
                track_metric('llm_requests', {
                    'provider': provider.provider_name,
                    'model': batch[0].model or 'default',
                    'status': 'success'
                }, len(batch))
                
            except Exception as e:
                logger.error(f"Batch embedding generation failed: {e}")
                
                track_metric('llm_requests', {
                    'provider': provider.provider_name,
                    'model': batch[0].model or 'unknown',
                    'status': 'error'
                }, len(batch))
                
                raise
        
        return responses
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """사용 가능한 프로바이더 목록"""
        providers = []
        
        for name, provider in self.providers.items():
            providers.append({
                "name": name,
                "available": provider.is_available(),
                "models": provider.available_models,
                "is_primary": name == self.primary_provider
            })
        
        return providers
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """모든 프로바이더 헬스 체크"""
        results = {}
        
        for name, provider in self.providers.items():
            try:
                health = await provider.health_check()
                results[name] = health
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "available": False
                }
        
        return results


# 전역 LLM 관리자 인스턴스
llm_manager = LLMManager()