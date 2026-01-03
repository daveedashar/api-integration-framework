"""Core configuration."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_env: str = "development"
    app_debug: bool = False
    app_secret_key: str = "change-me"
    
    database_url: str = "postgresql+asyncpg://localhost/integrations_db"
    redis_url: str = "redis://localhost:6379/0"
    
    default_rate_limit: int = 100
    rate_limit_window: int = 60
    
    default_max_retries: int = 3
    default_retry_delay: int = 5
    exponential_backoff: bool = True
    
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 30
    
    encryption_key: str = ""
    
    allowed_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"


settings = Settings()
