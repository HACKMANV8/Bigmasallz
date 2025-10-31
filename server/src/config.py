"""Configuration management for the synthetic data generation tool."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeminiConfig(BaseModel):
    """Gemini API configuration."""
    api_key: str
    model: str = "gemini-1.5-pro"
    max_retries: int = 3
    timeout: int = 120
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40


class MCPServerConfig(BaseModel):
    """MCP Server configuration."""
    host: str = "localhost"
    port: int = 8000
    name: str = "synthetic-data-generator"


class StorageConfig(BaseModel):
    """Storage configuration."""
    type: Literal["memory", "disk", "cloud"] = "disk"
    temp_path: Path = Path("./temp")
    output_path: Path = Path("./output")
    max_memory_chunks: int = 100

    # Cloud storage options
    cloud_bucket: str | None = None
    cloud_region: str | None = None
    aws_access_key: str | None = None
    aws_secret_key: str | None = None
    gcs_project_id: str | None = None
    gcs_credentials_path: Path | None = None


class GenerationConfig(BaseModel):
    """Data generation configuration."""
    default_chunk_size: int = 1000
    max_chunk_size: int = 5000
    min_chunk_size: int = 100
    default_output_format: Literal["csv", "json", "parquet"] = "csv"


class JobConfig(BaseModel):
    """Job management configuration."""
    persistence_path: Path = Path("./temp/jobs")
    cleanup_days: int = 7
    max_concurrent_jobs: int = 5


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    tokens_per_minute: int = 50000


class LangfuseConfig(BaseModel):
    """Langfuse telemetry configuration."""
    enabled: bool = False
    public_key: str | None = None
    secret_key: str | None = None
    base_url: str | None = None


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-pro"
    gemini_max_retries: int = 3
    gemini_timeout: int = 120

    # MCP Server
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 8000
    mcp_server_name: str = "synthetic-data-generator"

    # Storage
    storage_type: Literal["memory", "disk", "cloud"] = "disk"
    temp_storage_path: str = "./temp"
    output_storage_path: str = "./output"
    max_memory_chunks: int = 100

    # Cloud Storage (optional)
    cloud_storage_bucket: str | None = None
    cloud_storage_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    gcs_project_id: str | None = None
    gcs_credentials_path: str | None = None

    # Generation
    default_chunk_size: int = 1000
    max_chunk_size: int = 5000
    min_chunk_size: int = 100
    default_output_format: Literal["csv", "json", "parquet"] = "csv"

    # Job Management
    job_persistence_path: str = "./temp/jobs"
    job_cleanup_days: int = 7
    max_concurrent_jobs: int = 5

    # Rate Limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_tokens_per_minute: int = 50000

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    # Langfuse telemetry
    langfuse_enabled: bool = False
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_base_url: str | None = None

    @property
    def gemini(self) -> GeminiConfig:
        """Get Gemini configuration."""
        return GeminiConfig(
            api_key=self.gemini_api_key,
            model=self.gemini_model,
            max_retries=self.gemini_max_retries,
            timeout=self.gemini_timeout
        )

    @property
    def mcp_server(self) -> MCPServerConfig:
        """Get MCP server configuration."""
        return MCPServerConfig(
            host=self.mcp_server_host,
            port=self.mcp_server_port,
            name=self.mcp_server_name
        )

    @property
    def storage(self) -> StorageConfig:
        """Get storage configuration."""
        return StorageConfig(
            type=self.storage_type,
            temp_path=Path(self.temp_storage_path),
            output_path=Path(self.output_storage_path),
            max_memory_chunks=self.max_memory_chunks,
            cloud_bucket=self.cloud_storage_bucket,
            cloud_region=self.cloud_storage_region,
            aws_access_key=self.aws_access_key_id,
            aws_secret_key=self.aws_secret_access_key,
            gcs_project_id=self.gcs_project_id,
            gcs_credentials_path=Path(self.gcs_credentials_path) if self.gcs_credentials_path else None
        )

    @property
    def generation(self) -> GenerationConfig:
        """Get generation configuration."""
        return GenerationConfig(
            default_chunk_size=self.default_chunk_size,
            max_chunk_size=self.max_chunk_size,
            min_chunk_size=self.min_chunk_size,
            default_output_format=self.default_output_format
        )

    @property
    def job(self) -> JobConfig:
        """Get job configuration."""
        return JobConfig(
            persistence_path=Path(self.job_persistence_path),
            cleanup_days=self.job_cleanup_days,
            max_concurrent_jobs=self.max_concurrent_jobs
        )

    @property
    def rate_limit(self) -> RateLimitConfig:
        """Get rate limit configuration."""
        return RateLimitConfig(
            requests_per_minute=self.rate_limit_requests_per_minute,
            tokens_per_minute=self.rate_limit_tokens_per_minute
        )

    @property
    def langfuse(self) -> LangfuseConfig:
        """Get Langfuse telemetry configuration."""
        enabled = bool(
            self.langfuse_enabled and self.langfuse_public_key and self.langfuse_secret_key
        )
        return LangfuseConfig(
            enabled=enabled,
            public_key=self.langfuse_public_key,
            secret_key=self.langfuse_secret_key,
            base_url=self.langfuse_base_url,
        )


# Global settings instance
settings = Settings()
