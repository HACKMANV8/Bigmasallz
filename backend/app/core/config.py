"""
Core configuration settings for SynthAIx backend.
Manages environment variables and application settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "SynthAIx"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:8501", "http://localhost:3000"]
    
    # Google Gemini Configuration (LEGACY - now using MCP + Copilot!)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"  # Fast and efficient model
    GEMINI_TEMPERATURE: float = 0.3
    GEMINI_MAX_TOKENS: int = 8192  # Gemini has much higher token limits
    
    # MCP Configuration (NEW!)
    USE_MCP: bool = True  # Use GitHub Copilot via MCP instead of API-based LLMs
    MCP_SERVER_PATH: Optional[str] = None  # Auto-detected if None
    
    # Generation Configuration - SUPERCHARGED with Copilot! 🚀
    # No rate limits = massive parallelization possible!
    MAX_WORKERS: int = 1000  # Was 20, now 1000! Unlimited Copilot tokens!
    DEFAULT_CHUNK_SIZE: int = 50  # Smaller chunks for better parallelization
    MAX_CHUNK_SIZE: int = 100  # Keep chunks smaller for faster feedback
    MIN_CHUNK_SIZE: int = 10
    
    # Stats Update Configuration
    STATS_UPDATE_INTERVAL: float = 0.5  # Update frontend every 0.5 seconds for real-time feel
    
    # ChromaDB Configuration
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "synthaix_dedupe"
    SIMILARITY_THRESHOLD: float = 0.85
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Redis (for job state management)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra env vars (for backward compatibility)


# Global settings instance
settings = Settings()
