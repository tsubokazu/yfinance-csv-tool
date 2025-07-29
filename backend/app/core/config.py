"""
Application configuration using Pydantic Settings
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os
from pathlib import Path

# ������n���ǣ���֗
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    """
    Application settings with environment variable support
    """
    # Application
    PROJECT_NAME: str = "yfinance Trading Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True)
    
    # API
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-here-change-in-production", env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Supabase
    SUPABASE_URL: str = Field(default="", env="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field(default="", env="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: str = Field(default="", env="SUPABASE_SERVICE_KEY")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # OpenAI
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    
    # Database (optional direct connection)
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    # Sentry
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Cache Settings
    CACHE_TTL_MINUTES: int = Field(default=5, env="CACHE_TTL_MINUTES")
    CACHE_TTL_HOURS: int = Field(default=1, env="CACHE_TTL_HOURS")
    CACHE_TTL_DAYS: int = Field(default=1, env="CACHE_TTL_DAYS")
    
    # File Paths
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    
    @field_validator("CORS_ORIGINS", mode='before')
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("ENVIRONMENT")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Set debug based on environment
        if self.ENVIRONMENT == "production":
            self.DEBUG = False

# Create settings instance
settings = Settings()

# Export commonly used settings
PROJECT_NAME = settings.PROJECT_NAME
VERSION = settings.VERSION
API_V1_STR = settings.API_V1_STR