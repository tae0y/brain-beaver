"""
OpenAI API 프로바이더 구현

OpenAI API를 통해 텍스트 생성 및 임베딩을 제공합니다.
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
import time
import openai
from openai import AsyncOpenAI

from core.config import settings
from core.logging import get_logger
from .llm_interface import (
    LLMProviderInterface, RetryableLLMProvider,
    LLMRequest, LLMResponse, EmbeddingRequest, EmbeddingResponse
)

logger = get_logger(__name__)


class OpenAIProvider(RetryableLLMProvider, LLMProviderInterface):
    """OpenAI API 프로바이더"""
    
    def __init__(self, api_key: str = None):
        super().__init__(max_retries=3, base_delay=1.0)
        
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # AsyncOpenAI 클라이언트 초기화
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # 기본 모델 설정
        self.default_chat_model = settings.llm_model_chat
        self.default_embedding_model = settings.llm_model_embed
        
        # 사용 가능한 모델 목록
        self._available_models = [
            # 채팅 모델
            "gpt-4-turbo-preview", "gpt-4", "gpt-4-32k",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
            # 임베딩 모델
            "text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"
        ]
        
        logger.info("OpenAI provider initialized", extra={
            "default_chat_model": self.default_chat_model,
            "default_embedding_model": self.default_embedding_model,
            "available_models_count": len(self._available_models)
        })
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    @property
    def available_models(self) -> List[str]:
        return self._available_models
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """텍스트 생성"""
        start_time = time.time()
        
        model = request.model or self.default_chat_model
        max_tokens = request.max_tokens or settings.llm_max_tokens
        temperature = request.temperature
        
        # 메시지 구성
        messages = []
        
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        
        messages.append({"role": "user", "content": request.prompt})
        
        try:
            response = await self._execute_with_retry(
                self._make_chat_request,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # 응답 구성
            llm_response = LLMResponse(
                text=response.choices[0].message.content,
                model=response.model,
                provider=self.provider_name,
                token_usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                latency_ms=latency_ms,
                metadata={"finish_reason": response.choices[0].finish_reason}
            )
            
            logger.debug("OpenAI text generated successfully", extra={
                "model": model,
                "prompt_length": len(request.prompt),
                "response_length": len(llm_response.text),
                "latency_ms": latency_ms,
                "total_tokens": response.usage.total_tokens
            })
            
            return llm_response
            
        except Exception as e:
            logger.error(f"OpenAI text generation failed: {e}", extra={
                "model": model,
                "prompt_length": len(request.prompt),
                "latency_ms": (time.time() - start_time) * 1000
            })
            raise
    
    async def _make_chat_request(self, **kwargs):
        """채팅 요청 실행"""
        return await self.client.chat.completions.create(**kwargs)
    
    async def generate_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """단일 임베딩 생성"""
        if isinstance(request.texts, list):
            # 리스트인 경우 첫 번째 요소만 처리
            text = request.texts[0]
        else:
            text = request.texts
        
        start_time = time.time()
        model = request.model or self.default_embedding_model
        
        try:
            response = await self._execute_with_retry(
                self._make_embedding_request,
                model=model,
                input=text
            )
            
            latency_ms = (time.time() - start_time) * 1000
            embedding = response.data[0].embedding
            
            embedding_response = EmbeddingResponse(
                embeddings=embedding,
                model=response.model,
                provider=self.provider_name,
                dimension=len(embedding),
                token_usage={"total_tokens": response.usage.total_tokens},
                latency_ms=latency_ms
            )
            
            logger.debug("OpenAI embedding generated successfully", extra={
                "model": model,
                "text_length": len(text),
                "dimension": len(embedding),
                "latency_ms": latency_ms,
                "total_tokens": response.usage.total_tokens
            })
            
            return embedding_response
            
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {e}", extra={
                "model": model,
                "text_length": len(text),
                "latency_ms": (time.time() - start_time) * 1000
            })
            raise
    
    async def _make_embedding_request(self, **kwargs):
        """임베딩 요청 실행"""
        return await self.client.embeddings.create(**kwargs)
    
    async def batch_generate_embeddings(self, requests: List[EmbeddingRequest]) -> List[EmbeddingResponse]:
        """배치 임베딩 생성"""
        if not requests:
            return []
        
        start_time = time.time()
        
        # 모든 텍스트를 하나의 배치로 모음
        texts = []
        for req in requests:
            if isinstance(req.texts, list):
                texts.extend(req.texts)
            else:
                texts.append(req.texts)
        
        model = requests[0].model or self.default_embedding_model
        
        try:
            response = await self._execute_with_retry(
                self._make_embedding_request,
                model=model,
                input=texts
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # 응답을 개별 요청에 맞게 분할
            responses = []
            text_idx = 0
            
            for req in requests:
                if isinstance(req.texts, list):
                    # 리스트인 경우 해당 개수만큼 임베딩 수집
                    embeddings = []
                    for _ in req.texts:
                        embeddings.append(response.data[text_idx].embedding)
                        text_idx += 1
                else:
                    # 단일 텍스트인 경우
                    embeddings = response.data[text_idx].embedding
                    text_idx += 1
                
                embedding_response = EmbeddingResponse(
                    embeddings=embeddings,
                    model=response.model,
                    provider=self.provider_name,
                    dimension=len(response.data[0].embedding),
                    token_usage={"total_tokens": response.usage.total_tokens // len(requests)},
                    latency_ms=latency_ms
                )
                responses.append(embedding_response)
            
            logger.info("OpenAI batch embeddings generated successfully", extra={
                "model": model,
                "batch_size": len(requests),
                "total_texts": len(texts),
                "latency_ms": latency_ms,
                "total_tokens": response.usage.total_tokens
            })
            
            return responses
            
        except Exception as e:
            logger.error(f"OpenAI batch embedding generation failed: {e}", extra={
                "model": model,
                "batch_size": len(requests),
                "total_texts": len(texts),
                "latency_ms": (time.time() - start_time) * 1000
            })
            raise
    
    def is_available(self) -> bool:
        """사용 가능 여부 확인"""
        return bool(self.api_key)
    
    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        try:
            # 간단한 임베딩 요청으로 헬스 체크
            test_request = EmbeddingRequest(texts="test", model=self.default_embedding_model)
            start_time = time.time()
            
            await self.generate_embedding(test_request)
            
            latency = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "available": True,
                "models": self.available_models,
                "provider": self.provider_name
            }
            
        except Exception as e:
            logger.warning(f"OpenAI health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "available": False,
                "provider": self.provider_name
            }
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """OpenAI 특화 재시도 가능 에러 판단"""
        if hasattr(error, 'status_code'):
            # HTTP 상태 코드 기반 판단
            retryable_codes = [429, 500, 502, 503, 504]
            return error.status_code in retryable_codes
        
        return super()._is_retryable_error(error)