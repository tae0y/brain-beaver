"""
Ollama 로컬 LLM 프로바이더 구현

로컬에서 실행되는 Ollama 서버를 통해 텍스트 생성 및 임베딩을 제공합니다.
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Union
import httpx
import ollama

from core.config import settings
from core.logging import get_logger
from .llm_interface import (
    LLMProviderInterface, RetryableLLMProvider,
    LLMRequest, LLMResponse, EmbeddingRequest, EmbeddingResponse
)

logger = get_logger(__name__)


class OllamaProvider(RetryableLLMProvider, LLMProviderInterface):
    """Ollama 로컬 LLM 프로바이더"""
    
    def __init__(self, host: str = None):
        super().__init__(max_retries=2, base_delay=0.5)
        
        self.host = host or settings.ollama_host
        self.client = ollama.AsyncClient(host=self.host)
        
        # 기본 모델 설정
        self.default_chat_model = settings.llm_model_chat
        self.default_embedding_model = "nomic-embed-text"  # Ollama에서 일반적으로 사용되는 임베딩 모델
        
        # 사용 가능한 모델들 (동적으로 로드)
        self._available_models = []
        self._last_model_check = 0
        self._model_check_interval = 300  # 5분
        
        logger.info("Ollama provider initialized", extra={
            "host": self.host,
            "default_chat_model": self.default_chat_model,
            "default_embedding_model": self.default_embedding_model
        })
    
    @property
    def provider_name(self) -> str:
        return "ollama"
    
    @property
    def available_models(self) -> List[str]:
        current_time = time.time()
        
        # 캐시된 모델 목록이 있고 아직 유효하면 반환
        if self._available_models and (current_time - self._last_model_check) < self._model_check_interval:
            return self._available_models
        
        # 모델 목록 새로 가져오기 (동기식으로 처리)
        try:
            models = ollama.list()
            self._available_models = [model['name'] for model in models['models']]
            self._last_model_check = current_time
            logger.debug(f"Updated Ollama model list: {self._available_models}")
        except Exception as e:
            logger.warning(f"Failed to fetch Ollama models: {e}")
            # 기본 모델 목록 반환
            if not self._available_models:
                self._available_models = [self.default_chat_model, self.default_embedding_model]
        
        return self._available_models
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """텍스트 생성"""
        start_time = time.time()
        
        model = request.model or self.default_chat_model
        
        # 메시지 구성
        messages = []
        
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        
        messages.append({"role": "user", "content": request.prompt})
        
        # Ollama 옵션 설정
        options = {}
        if request.max_tokens:
            options["num_predict"] = request.max_tokens
        if request.temperature is not None:
            options["temperature"] = request.temperature
        
        try:
            response = await self._execute_with_retry(
                self._make_chat_request,
                model=model,
                messages=messages,
                options=options
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Ollama 응답에서 텍스트 추출
            response_text = response['message']['content']
            
            # 토큰 사용량 정보 (Ollama는 정확한 토큰 수를 제공하지 않으므로 추정)
            estimated_prompt_tokens = len(request.prompt.split()) * 1.3  # 대략적인 추정
            estimated_completion_tokens = len(response_text.split()) * 1.3
            
            llm_response = LLMResponse(
                text=response_text,
                model=model,
                provider=self.provider_name,
                token_usage={
                    "prompt_tokens": int(estimated_prompt_tokens),
                    "completion_tokens": int(estimated_completion_tokens),
                    "total_tokens": int(estimated_prompt_tokens + estimated_completion_tokens)
                },
                latency_ms=latency_ms,
                metadata={
                    "done": response.get('done', True),
                    "eval_count": response.get('eval_count', 0),
                    "eval_duration": response.get('eval_duration', 0)
                }
            )
            
            logger.debug("Ollama text generated successfully", extra={
                "model": model,
                "prompt_length": len(request.prompt),
                "response_length": len(response_text),
                "latency_ms": latency_ms,
                "eval_count": response.get('eval_count', 0)
            })
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Ollama text generation failed: {e}", extra={
                "model": model,
                "prompt_length": len(request.prompt),
                "latency_ms": (time.time() - start_time) * 1000
            })
            raise
    
    async def _make_chat_request(self, **kwargs):
        """채팅 요청 실행"""
        return await self.client.chat(**kwargs)
    
    async def generate_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """단일 임베딩 생성"""
        if isinstance(request.texts, list):
            text = request.texts[0]
        else:
            text = request.texts
        
        start_time = time.time()
        model = request.model or self.default_embedding_model
        
        try:
            response = await self._execute_with_retry(
                self._make_embeddings_request,
                model=model,
                prompt=text
            )
            
            latency_ms = (time.time() - start_time) * 1000
            embedding = response['embedding']
            
            embedding_response = EmbeddingResponse(
                embeddings=embedding,
                model=model,
                provider=self.provider_name,
                dimension=len(embedding),
                token_usage={
                    "total_tokens": int(len(text.split()) * 1.3)  # 추정
                },
                latency_ms=latency_ms
            )
            
            logger.debug("Ollama embedding generated successfully", extra={
                "model": model,
                "text_length": len(text),
                "dimension": len(embedding),
                "latency_ms": latency_ms
            })
            
            return embedding_response
            
        except Exception as e:
            logger.error(f"Ollama embedding generation failed: {e}", extra={
                "model": model,
                "text_length": len(text),
                "latency_ms": (time.time() - start_time) * 1000
            })
            raise
    
    async def _make_embeddings_request(self, **kwargs):
        """임베딩 요청 실행"""
        return await self.client.embeddings(**kwargs)
    
    async def batch_generate_embeddings(self, requests: List[EmbeddingRequest]) -> List[EmbeddingResponse]:
        """배치 임베딩 생성 (Ollama는 개별 요청으로 처리)"""
        if not requests:
            return []
        
        start_time = time.time()
        responses = []
        
        # Ollama는 배치 처리를 지원하지 않으므로 개별적으로 처리
        for request in requests:
            try:
                response = await self.generate_embedding(request)
                responses.append(response)
            except Exception as e:
                logger.error(f"Failed to generate embedding in batch: {e}")
                # 실패한 경우 빈 임베딩으로 대체 (선택사항)
                raise
        
        total_latency = (time.time() - start_time) * 1000
        
        logger.info("Ollama batch embeddings generated successfully", extra={
            "batch_size": len(requests),
            "total_latency_ms": total_latency,
            "avg_latency_ms": total_latency / len(requests)
        })
        
        return responses
    
    def is_available(self) -> bool:
        """Ollama 서버 사용 가능 여부 확인"""
        try:
            # 간단한 동기 요청으로 확인
            response = ollama.list()
            return True
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        try:
            start_time = time.time()
            
            # 모델 목록 조회로 헬스 체크
            models = await self.client.list()
            
            latency = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "available": True,
                "models": [model['name'] for model in models['models']],
                "model_count": len(models['models']),
                "provider": self.provider_name,
                "host": self.host
            }
            
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "available": False,
                "provider": self.provider_name,
                "host": self.host
            }
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Ollama 특화 재시도 가능 에러 판단"""
        error_message = str(error).lower()
        
        # Ollama 특유의 재시도 가능한 에러들
        ollama_retryable = [
            'connection refused', 'timeout', 'server error',
            'model loading', 'temporary failure'
        ]
        
        if any(keyword in error_message for keyword in ollama_retryable):
            return True
        
        return super()._is_retryable_error(error)
    
    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """모델 다운로드"""
        try:
            logger.info(f"Pulling Ollama model: {model_name}")
            
            result = await self.client.pull(model_name)
            
            logger.info(f"Successfully pulled model: {model_name}")
            
            # 모델 목록 캐시 무효화
            self._last_model_check = 0
            
            return {
                "status": "success",
                "model": model_name,
                "message": f"Model {model_name} pulled successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return {
                "status": "error",
                "model": model_name,
                "error": str(e)
            }
    
    async def delete_model(self, model_name: str) -> Dict[str, Any]:
        """모델 삭제"""
        try:
            logger.info(f"Deleting Ollama model: {model_name}")
            
            await self.client.delete(model_name)
            
            logger.info(f"Successfully deleted model: {model_name}")
            
            # 모델 목록 캐시 무효화
            self._last_model_check = 0
            
            return {
                "status": "success",
                "model": model_name,
                "message": f"Model {model_name} deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            return {
                "status": "error",
                "model": model_name,
                "error": str(e)
            }