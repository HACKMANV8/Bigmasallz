"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class FieldType(str, Enum):
    """Supported data types for schema fields."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    UUID = "uuid"


class SchemaField(BaseModel):
    """Definition of a single field in the data schema."""
    name: str = Field(..., description="Field name")
    type: FieldType = Field(..., description="Field data type")
    description: Optional[str] = Field(None, description="Field description")
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Field constraints")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "transaction_amount",
                "type": "float",
                "description": "Transaction amount in USD",
                "constraints": {"min": 0, "max": 10000}
            }
        }


class DataSchema(BaseModel):
    """Complete schema definition for data generation."""
    fields: List[SchemaField] = Field(..., description="List of schema fields")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator("fields")
    def validate_fields(cls, v):
        if not v:
            raise ValueError("Schema must contain at least one field")
        field_names = [f.name for f in v]
        if len(field_names) != len(set(field_names)):
            raise ValueError("Field names must be unique")
        return v


class SchemaTranslateRequest(BaseModel):
    """Request to translate natural language to schema."""
    prompt: str = Field(..., description="Natural language description of desired data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Generate financial transactions with date, amount, merchant name, and category"
            }
        }


class SchemaTranslateResponse(BaseModel):
    """Response containing inferred schema."""
    schema: DataSchema
    interpretation: str = Field(..., description="LLM's interpretation of the prompt")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataGenerateRequest(BaseModel):
    """Request to generate synthetic data."""
    schema: DataSchema = Field(..., description="Confirmed data schema")
    total_rows: int = Field(..., ge=1, le=1000000, description="Total rows to generate")
    chunk_size: Optional[int] = Field(None, ge=10, le=1000, description="Rows per chunk")
    enable_deduplication: bool = Field(True, description="Enable duplicate detection")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema": {
                    "fields": [
                        {"name": "id", "type": "uuid"},
                        {"name": "amount", "type": "float"}
                    ]
                },
                "total_rows": 10000,
                "enable_deduplication": True
            }
        }


class DataGenerateResponse(BaseModel):
    """Response containing job ID for async generation."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Initial job status")
    message: str = Field(..., description="Status message")


class ChunkProgress(BaseModel):
    """Progress information for a single chunk."""
    chunk_id: int
    status: JobStatus
    rows_generated: int
    duplicates_removed: int
    error: Optional[str] = None


class AgentMetrics(BaseModel):
    """Metrics for agent performance."""
    tokens_used: int = 0
    api_calls: int = 0
    avg_response_time: float = 0.0
    deduplication_rate: float = 0.0
    total_duplicates_removed: int = 0


class JobStatusResponse(BaseModel):
    """Complete job status information."""
    job_id: str
    status: JobStatus
    total_rows: int
    completed_rows: int
    progress_percentage: float
    chunks: List[ChunkProgress]
    metrics: AgentMetrics
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    estimated_time_remaining: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
