from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List
import os
import secrets


class Settings(BaseSettings):
    APP_NAME: str = "Multi-Agent Platform"
    VERSION: str = "2.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./multi_agent.db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 300

    SECRET_KEY: str = ""  # Must be set via environment variable
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    API_KEY_HEADER: str = "X-API-Key"
    ENABLE_API_KEY_AUTH: bool = True

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True

    WS_MAX_CONNECTIONS: int = 100
    WS_HEARTBEAT_INTERVAL: int = 30

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"

    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None

    WEBHOOK_ENABLED: bool = False
    WEBHOOK_SECRET: Optional[str] = None

    UPLOAD_DIR: str = "/tmp/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024

    ENABLE_BILLING: bool = True
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    FREE_PLAN_TOKEN_LIMIT: int = 100000
    FREE_PLAN_TASK_LIMIT: int = 100
    PRO_PLAN_TOKEN_LIMIT: int = 5000000
    PRO_PLAN_TASK_LIMIT: int = 5000

    LLM_DEFAULT_PROVIDER: str = "openai"
    LLM_DEFAULT_MODEL: str = "gpt-4o-mini"
    LLM_MAX_ITERATIONS: int = 10
    LLM_REQUEST_TIMEOUT: int = 120
    EXECUTION_MAX_CONCURRENT: int = 5
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    TRUSTED_HOSTS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def model_post_init(self, __context) -> None:
        if not self.SECRET_KEY:
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "SECRET_KEY must be set in production. "
                    "Generate one: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            else:
                self.SECRET_KEY = secrets.token_hex(32)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
