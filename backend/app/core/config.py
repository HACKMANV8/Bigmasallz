from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "SynthAIx"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    ENABLE_DOCS: bool = True

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # CORS - Accept comma-separated string or list
    CORS_ORIGINS: str = "http://localhost:8501,http://localhost:8000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list."""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

    # LLM Configuration
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_MODEL: str = "gpt-4-turbo"
    SCHEMA_MODEL: str = "gpt-4-turbo"
    GENERATION_MODEL: str = "gpt-4-turbo"
    LLM_TIMEOUT: int = 60

    # Generation Settings
    MAX_WORKERS: int = 20
    DEFAULT_CHUNK_SIZE: int = 500
    MIN_CHUNK_SIZE: int = 100
    MAX_CHUNK_SIZE: int = 2000
    MAX_CHUNK_RETRIES: int = 3

    # Deduplication
    DEDUPLICATION_THRESHOLD: float = 0.85
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    VECTOR_DIMENSION: int = 1536

    # ChromaDB
    CHROMADB_PATH: str = "./data/chromadb"
    CHROMADB_COLLECTION_PREFIX: str = "synthaix_"

    # Database (optional)
    DATABASE_URL: str = ""
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis (optional)
    REDIS_URL: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"
    STRUCTURED_LOGGING: bool = True

    # Security
    SECRET_KEY: str = "change-this-in-production"
    TOKEN_EXPIRE_HOURS: int = 24
    ENABLE_API_KEY_AUTH: bool = False

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_INTERVAL: int = 60
    SENTRY_DSN: str = ""

    # Development
    AUTO_RELOAD: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
