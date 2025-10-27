"""
API Configuration Management

Centralized configuration for the API layer using environment variables.
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Quantitative Trading API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    API_KEY_HEADER: str = "X-API-Key"
    ENABLE_AUTH: bool = False

    # Database (future expansion)
    DATABASE_URL: str = "sqlite:///./trading.db"

    # Configuration and logs paths
    CONFIG_DIR: str = "./config"
    LOGS_DIR: str = "./logs"

    # Trading
    DEFAULT_SYMBOLS: List[str] = ["AAPL", "MSFT", "GOOGL"]
    MAX_SYMBOLS_PER_REQUEST: int = 50

    # Scheduler
    SCHEDULER_CONFIG_PATH: str = "./config/scheduler_config.json"

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
