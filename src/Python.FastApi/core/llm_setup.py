"""
LLM 프로바이더 초기화 및 설정

애플리케이션 시작 시 LLM 프로바이더들을 초기화하고 등록합니다.
"""

from core.config import settings, LLMProvider
from core.logging import get_logger
from pipeline.adapters.llm_interface import llm_manager
from pipeline.adapters.openai_provider import OpenAIProvider
from pipeline.adapters.ollama_provider import OllamaProvider

logger = get_logger(__name__)


def initialize_llm_providers():
    """LLM 프로바이더 초기화 및 등록"""
    logger.info("Initializing LLM providers...")
    
    providers_initialized = 0
    
    # OpenAI 프로바이더 초기화
    if settings.openai_api_key:
        try:
            openai_provider = OpenAIProvider(settings.openai_api_key)
            is_primary = settings.llm_provider == LLMProvider.OPENAI
            llm_manager.register_provider(openai_provider, is_primary=is_primary)
            providers_initialized += 1
            logger.info("OpenAI provider registered", extra={
                "is_primary": is_primary,
                "models": len(openai_provider.available_models)
            })
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI provider: {e}")
    else:
        logger.info("OpenAI API key not provided, skipping OpenAI provider")
    
    # Ollama 프로바이더 초기화
    try:
        ollama_provider = OllamaProvider(settings.ollama_host)
        is_primary = settings.llm_provider == LLMProvider.OLLAMA
        
        # Ollama 사용 가능성 확인
        if ollama_provider.is_available():
            llm_manager.register_provider(ollama_provider, is_primary=is_primary)
            providers_initialized += 1
            logger.info("Ollama provider registered", extra={
                "host": settings.ollama_host,
                "is_primary": is_primary,
                "models": len(ollama_provider.available_models)
            })
        else:
            logger.warning("Ollama server not available, skipping Ollama provider")
    except Exception as e:
        logger.warning(f"Failed to initialize Ollama provider: {e}")
    
    # 프로바이더 등록 결과 확인
    if providers_initialized == 0:
        logger.error("No LLM providers available! Some features will not work.")
        raise RuntimeError("No LLM providers could be initialized")
    
    logger.info(f"LLM provider initialization completed", extra={
        "providers_initialized": providers_initialized,
        "primary_provider": settings.llm_provider.value,
        "available_providers": [p["name"] for p in llm_manager.get_available_providers()]
    })


async def health_check_providers():
    """모든 프로바이더 헬스 체크"""
    logger.info("Performing LLM provider health check...")
    
    try:
        health_results = await llm_manager.health_check_all()
        
        healthy_count = sum(1 for result in health_results.values() if result.get("available", False))
        total_count = len(health_results)
        
        logger.info("LLM provider health check completed", extra={
            "total_providers": total_count,
            "healthy_providers": healthy_count,
            "health_results": health_results
        })
        
        return health_results
        
    except Exception as e:
        logger.error(f"LLM provider health check failed: {e}")
        return {}


def get_provider_status():
    """현재 프로바이더 상태 반환"""
    return {
        "configured_provider": settings.llm_provider.value,
        "available_providers": llm_manager.get_available_providers(),
        "chat_model": settings.llm_model_chat,
        "embedding_model": settings.llm_model_embed
    }