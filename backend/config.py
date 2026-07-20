from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Multi-Agent Platform"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    
    # Database - PostgreSQL for production
    DATABASE_URL: str = "sqlite:///./multi_agent.db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False
    
    # Redis - Caching & Rate Limiting
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 300  # 5 minutes
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # API Keys
    API_KEY_HEADER: str = "X-API-Key"
    ENABLE_API_KEY_AUTH: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # WebSocket
    WS_MAX_CONNECTIONS: int = 100
    WS_HEARTBEAT_INTERVAL: int = 30
    
    # Celery - Task Queue
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: Optional[str] = None
    
    # Webhooks
    WEBHOOK_ENABLED: bool = False
    WEBHOOK_SECRET: Optional[str] = None
    
    # File Storage
    UPLOAD_DIR: str = "/tmp/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Billing
    ENABLE_BILLING: bool = True
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    FREE_PLAN_TOKEN_LIMIT: int = 100000
    FREE_PLAN_TASK_LIMIT: int = 100
    PRO_PLAN_TOKEN_LIMIT: int = 5000000
    PRO_PLAN_TASK_LIMIT: int = 5000

    # LLM Execution
    LLM_DEFAULT_PROVIDER: str = "openai"
    LLM_DEFAULT_MODEL: str = "gpt-4o-mini"
    LLM_MAX_ITERATIONS: int = 10
    LLM_REQUEST_TIMEOUT: int = 120
    EXECUTION_MAX_CONCURRENT: int = 5
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
