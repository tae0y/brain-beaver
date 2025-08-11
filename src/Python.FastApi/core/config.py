"""
설정 관리 시스템

환경변수 + INI 파일을 통한 계층적 설정 관리를 제공합니다.
우선순위: ENV > config.prod.ini|config.dev.ini > config.ini > defaults

주요 기능:
- Dev/Prod 환경별 설정 분리
- 환경변수 오버라이드
- 타입 검증 및 기본값
- 비밀키 분리 관리
"""

import os
import configparser
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field, validator
from enum import Enum


class Environment(str, Enum):
    """실행 환경"""
    DEV = "development"
    PROD = "production"
    TEST = "test"


class LLMProvider(str, Enum):
    """LLM 프로바이더"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    LOCAL = "local"


class Settings(BaseSettings):
    """
    애플리케이션 설정
    
    환경변수와 INI 파일을 조합하여 설정을 로드합니다.
    """
    
    # ===================
    # 기본 환경 설정
    # ===================
    environment: Environment = Field(default=Environment.DEV, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    app_name: str = Field(default="BrainBeaver", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION")
    
    # ===================
    # 데이터베이스 설정
    # ===================
    database_url: str = Field(
        default="postgresql://root:root@localhost:5432/bwsdb", 
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    enable_pgvector: bool = Field(default=False, env="ENABLE_PGVECTOR")
    
    # ===================
    # 런타임/병렬처리 설정  
    # ===================
    parallel_workers: int = Field(default=4, env="PARALLEL_WORKERS")
    batch_size: int = Field(default=10, env="BATCH_SIZE")
    queue_max: int = Field(default=1000, env="QUEUE_MAX")
    retry_max: int = Field(default=3, env="RETRY_MAX")
    timeout_sec: int = Field(default=30, env="TIMEOUT_SEC")
    
    @validator('parallel_workers')
    def validate_parallel_workers(cls, v):
        if v < 1 or v > 64:
            raise ValueError('parallel_workers must be between 1 and 64')
        return v
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        if v < 1 or v > 1000:
            raise ValueError('batch_size must be between 1 and 1000')
        return v
    
    # ===================
    # 크롤링 설정
    # ===================
    crawl_depth: int = Field(default=2, env="CRAWL_DEPTH")
    crawl_rate_limit_per_domain: int = Field(default=2, env="CRAWL_RATE_LIMIT_PER_DOMAIN")
    crawl_delay_ms: int = Field(default=300, env="CRAWL_DELAY_MS")
    crawl_allowed_domains: str = Field(default="", env="CRAWL_ALLOWED_DOMAINS")  # 콤마 구분
    crawl_max_pages: int = Field(default=1000, env="CRAWL_MAX_PAGES")
    crawl_timeout_sec: int = Field(default=10, env="CRAWL_TIMEOUT_SEC")
    
    @property
    def crawl_allowed_domains_list(self) -> List[str]:
        """허용 도메인 목록 반환"""
        if not self.crawl_allowed_domains.strip():
            return []
        return [domain.strip() for domain in self.crawl_allowed_domains.split(',') if domain.strip()]
    
    # ===================
    # LLM 설정
    # ===================  
    llm_provider: LLMProvider = Field(default=LLMProvider.OLLAMA, env="LLM_PROVIDER")
    llm_model_chat: str = Field(default="llama2", env="LLM_MODEL_CHAT")
    llm_model_embed: str = Field(default="text-embedding-3-large", env="LLM_MODEL_EMBED")
    llm_max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    llm_temperature: float = Field(default=0.1, env="LLM_TEMPERATURE")
    
    # API 키들 (주의: 환경변수로만 설정)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    
    # ===================
    # 청킹 설정  
    # ===================
    chunk_max_tokens: int = Field(default=512, env="CHUNK_MAX_TOKENS")
    chunk_overlap_tokens: int = Field(default=50, env="CHUNK_OVERLAP_TOKENS")
    chunk_min_tokens: int = Field(default=50, env="CHUNK_MIN_TOKENS")
    
    # ===================
    # 파일 처리 설정
    # ===================
    file_extensions: str = Field(default=".md,.mdx,.txt,.rst", env="FILE_EXTENSIONS")
    file_ignore_patterns: str = Field(default=".git,node_modules,__pycache__,.venv", env="FILE_IGNORE_PATTERNS")
    
    @property 
    def file_extensions_list(self) -> List[str]:
        """처리할 파일 확장자 목록"""
        return [ext.strip() for ext in self.file_extensions.split(',') if ext.strip()]
    
    @property
    def file_ignore_patterns_list(self) -> List[str]:
        """무시할 패턴 목록"""
        return [pattern.strip() for pattern in self.file_ignore_patterns.split(',') if pattern.strip()]
    
    # ===================
    # 로깅/관측성 설정
    # ===================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8090, env="METRICS_PORT")
    
    # OpenTelemetry
    otel_exporter_endpoint: Optional[str] = Field(default=None, env="OTEL_EXPORTER_ENDPOINT")
    otel_service_name: str = Field(default="brainbeaver-api", env="OTEL_SERVICE_NAME")
    
    # ===================
    # 보안 설정
    # ===================
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://bws_vite:5173", 
        env="CORS_ORIGINS"
    )
    api_rate_limit: int = Field(default=100, env="API_RATE_LIMIT")  # requests per minute
    
    @property
    def cors_origins_list(self) -> List[str]:
        """CORS 허용 오리진 목록"""
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
    
    # ===================
    # 기타 설정
    # ===================
    temp_dir: str = Field(default="/tmp/brainbeaver", env="TEMP_DIR")
    cache_ttl_sec: int = Field(default=3600, env="CACHE_TTL_SEC")  # 1시간
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class ConfigLoader:
    """
    설정 파일 로더
    
    INI 파일들을 환경에 맞게 병합하여 로드합니다.
    """
    
    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path(__file__).parent.parent / "properties"
        self.config_data: Dict[str, Any] = {}
        self._load_configs()
    
    def _load_configs(self):
        """설정 파일들을 로드하고 병합"""
        config = configparser.ConfigParser()
        
        # 기본 설정 로드 (config.ini 또는 config.properties)
        base_files = ["config.ini", "config.properties"]
        for filename in base_files:
            base_file = self.config_dir / filename
            if base_file.exists():
                config.read(base_file, encoding='utf-8')
                break
        
        # 환경별 설정 로드
        env = os.getenv("ENVIRONMENT", "development")
        env_file = self.config_dir / f"config.{env}.ini"
        if env_file.exists():
            config.read(env_file, encoding='utf-8')
        
        # ConfigParser 데이터를 딕셔너리로 변환
        for section_name in config.sections():
            section_dict = {}
            for key, value in config.items(section_name):
                # 타입 변환 시도
                section_dict[key.upper()] = self._parse_value(value)
            self.config_data[section_name.lower()] = section_dict
    
    def _parse_value(self, value: str) -> Any:
        """문자열 값을 적절한 타입으로 변환"""
        # 불린 값
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 정수 값
        try:
            if '.' not in value:
                return int(value)
        except ValueError:
            pass
        
        # 실수 값
        try:
            return float(value)
        except ValueError:
            pass
        
        # 문자열 그대로 반환
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """특정 섹션의 설정값들 반환"""
        return self.config_data.get(section.lower(), {})
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """특정 설정값 반환"""
        section_data = self.get_section(section)
        return section_data.get(key.upper(), default)
    
    def update_env_from_config(self):
        """INI 설정을 환경변수로 설정 (기존 환경변수 우선)"""
        for section, settings in self.config_data.items():
            for key, value in settings.items():
                env_key = f"{section.upper()}_{key}" if section != 'default' else key
                if env_key not in os.environ:
                    os.environ[env_key] = str(value)


def get_settings() -> Settings:
    """
    애플리케이션 설정 인스턴스 반환
    
    싱글톤 패턴으로 구현하여 설정 로딩 비용을 최소화합니다.
    """
    if not hasattr(get_settings, '_instance'):
        # INI 설정을 환경변수로 먼저 로드
        config_loader = ConfigLoader()
        config_loader.update_env_from_config()
        
        # Pydantic Settings로 최종 설정 생성
        get_settings._instance = Settings()
    
    return get_settings._instance


def create_temp_dirs(settings: Settings):
    """필요한 임시 디렉토리들 생성"""
    temp_dir = Path(settings.temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 하위 디렉토리들
    (temp_dir / "downloads").mkdir(exist_ok=True)
    (temp_dir / "processing").mkdir(exist_ok=True)
    (temp_dir / "cache").mkdir(exist_ok=True)


# 전역 설정 인스턴스
settings = get_settings()