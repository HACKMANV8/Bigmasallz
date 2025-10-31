from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum
import uuid


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(BaseModel):
    """Job model for tracking data generation tasks."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = Field(default=JobStatus.PENDING)
    total_rows: int = Field(..., gt=0)
    total_chunks: int = Field(..., gt=0)
    completed_chunks: int = Field(default=0)
    rows_generated: int = Field(default=0)
    rows_deduplicated: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    results: Optional[Any] = None


class JobStatusResponse(BaseModel):
    """Response model for job status endpoint."""

    job_id: str
    status: JobStatus
    total_chunks: int
    completed_chunks: int
    progress_percentage: float = Field(ge=0.0, le=100.0)
    rows_generated: int
    rows_deduplicated: int
    created_at: datetime
    estimated_completion: Optional[datetime] = None
    results: Optional[Any] = None
    error_message: Optional[str] = None


class JobMetrics(BaseModel):
    """Job performance metrics."""

    job_id: str
    duration_seconds: Optional[float] = None
    rows_per_second: Optional[float] = None
    chunks_per_second: Optional[float] = None
    deduplication_rate: Optional[float] = None
    llm_calls: int = 0
    total_tokens: int = 0
