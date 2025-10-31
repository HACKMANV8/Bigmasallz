from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.models.schema import DataSchema


class DataGenerationRequest(BaseModel):
    """Request model for data generation endpoint."""

    schema: DataSchema = Field(..., description="Data schema to generate from")
    total_rows: int = Field(..., gt=0, le=1000000, description="Total rows to generate")
    chunk_size: Optional[int] = Field(
        default=None, description="Rows per chunk (auto-calculated if not provided)"
    )
    max_workers: Optional[int] = Field(
        default=None, description="Maximum parallel workers"
    )
    deduplication_threshold: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Similarity threshold for deduplication"
    )
    seed: Optional[int] = Field(
        default=None, description="Random seed for reproducibility"
    )


class DataGenerationResponse(BaseModel):
    """Response model for data generation endpoint."""

    job_id: str
    status: str
    total_rows: int
    total_chunks: int
    created_at: str
    message: str = "Data generation job started successfully"


class GeneratedDataChunk(BaseModel):
    """Model for a chunk of generated data."""

    chunk_id: int
    rows: List[Dict[str, Any]]
    row_count: int
    deduplicated_count: int = 0


class GeneratedDataResult(BaseModel):
    """Final result model for completed data generation."""

    job_id: str
    data: List[Dict[str, Any]]
    total_rows: int
    unique_rows: int
    deduplicated_count: int
    download_url: Optional[str] = None
    format: str = "json"
