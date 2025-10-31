from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ColumnType(str, Enum):
    """Supported column data types."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    UUID = "uuid"
    JSON = "json"


class ColumnSchema(BaseModel):
    """Schema definition for a single column."""

    name: str = Field(..., description="Column name")
    type: ColumnType = Field(..., description="Data type")
    description: str = Field(..., description="Column description")
    constraints: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional constraints (min, max, pattern, etc.)"
    )
    examples: Optional[List[str]] = Field(
        default=None, description="Example values"
    )


class DataSchema(BaseModel):
    """Complete schema for synthetic data generation."""

    columns: List[ColumnSchema] = Field(..., description="List of column definitions")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional schema metadata"
    )


class SchemaTranslationRequest(BaseModel):
    """Request model for schema translation endpoint."""

    prompt: str = Field(
        ...,
        description="Natural language description of desired data schema",
        min_length=10,
        max_length=5000,
    )
    context: Optional[str] = Field(
        default=None, description="Additional context or requirements"
    )


class SchemaTranslationResponse(BaseModel):
    """Response model for schema translation endpoint."""

    schema: DataSchema = Field(..., description="Inferred data schema")
    inferred_count: Optional[int] = Field(
        default=None, description="Inferred number of rows to generate"
    )
    confidence: float = Field(
        default=1.0, description="Confidence score of the inference", ge=0.0, le=1.0
    )
