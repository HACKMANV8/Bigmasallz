"""Data models for the synthetic data generation tool."""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class FieldType(str, Enum):
    """Supported field types for schema."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    UUID = "uuid"
    ENUM = "enum"
    JSON = "json"
    ARRAY = "array"


class OutputFormat(str, Enum):
    """Supported output formats."""
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"


class JobStatus(str, Enum):
    """Job status states."""
    PENDING = "pending"
    SCHEMA_VALIDATION = "schema_validation"
    GENERATING = "generating"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StorageType(str, Enum):
    """Storage backend types."""
    MEMORY = "memory"
    DISK = "disk"
    CLOUD = "cloud"


class FieldConstraint(BaseModel):
    """Constraints for a field."""
    unique: bool = False
    nullable: bool = True
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[str]] = None
    format: Optional[str] = None
    default: Optional[Any] = None


class FieldDefinition(BaseModel):
    """Definition of a single field in the schema."""
    name: str
    type: FieldType
    description: Optional[str] = None
    constraints: FieldConstraint = Field(default_factory=FieldConstraint)
    sample_values: List[Any] = Field(default_factory=list)
    depends_on: Optional[List[str]] = None  # Field dependencies
    generation_hint: Optional[str] = None  # Hint for LLM on how to generate


class DataSchema(BaseModel):
    """Schema definition for the dataset."""
    fields: List[FieldDefinition]
    description: Optional[str] = None
    relationships: Optional[Dict[str, List[str]]] = None  # Field relationships
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_field(self, name: str) -> Optional[FieldDefinition]:
        """Get field definition by name."""
        for field in self.fields:
            if field.name == name:
                return field
        return None
    
    def validate_constraints(self) -> List[str]:
        """Validate schema constraints and return any issues."""
        issues = []
        field_names = {f.name for f in self.fields}
        
        # Check for duplicate field names
        if len(field_names) != len(self.fields):
            issues.append("Duplicate field names detected")
        
        # Check field dependencies
        for field in self.fields:
            if field.depends_on:
                for dep in field.depends_on:
                    if dep not in field_names:
                        issues.append(f"Field '{field.name}' depends on non-existent field '{dep}'")
        
        return issues


class ChunkMetadata(BaseModel):
    """Metadata for a generated chunk."""
    chunk_id: int
    job_id: UUID
    rows_generated: int
    storage_location: str
    timestamp: datetime = Field(default_factory=datetime.now)
    checksum: Optional[str] = None
    size_bytes: Optional[int] = None


class JobSpecification(BaseModel):
    """Specification for a data generation job."""
    job_id: UUID = Field(default_factory=uuid4)
    schema: DataSchema
    total_rows: int
    chunk_size: int = 1000
    output_format: OutputFormat = OutputFormat.CSV
    storage_type: StorageType = StorageType.DISK
    uniqueness_fields: List[str] = Field(default_factory=list)
    seed: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class JobProgress(BaseModel):
    """Progress tracking for a job."""
    job_id: UUID
    status: JobStatus
    rows_generated: int = 0
    chunks_completed: int = 0
    total_chunks: int
    current_chunk: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress_percentage: float = 0.0
    estimated_completion: Optional[datetime] = None
    
    def update_progress(self):
        """Update progress percentage."""
        if self.total_chunks > 0:
            self.progress_percentage = (self.chunks_completed / self.total_chunks) * 100


class JobState(BaseModel):
    """Complete state of a generation job."""
    specification: JobSpecification
    progress: JobProgress
    chunks: List[ChunkMetadata] = Field(default_factory=list)
    schema_validated: bool = False
    can_resume: bool = True
    
    def add_chunk(self, chunk: ChunkMetadata):
        """Add completed chunk and update progress."""
        self.chunks.append(chunk)
        self.progress.chunks_completed += 1
        self.progress.rows_generated += chunk.rows_generated
        self.progress.update_progress()


class SchemaExtractionRequest(BaseModel):
    """Request for schema extraction from natural language."""
    user_input: str
    context: Optional[Dict[str, Any]] = None
    example_data: Optional[str] = None


class SchemaExtractionResponse(BaseModel):
    """Response from schema extraction."""
    schema: DataSchema
    confidence: float
    suggestions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ChunkGenerationRequest(BaseModel):
    """Request for chunk generation."""
    job_id: UUID
    chunk_id: int
    schema: DataSchema
    num_rows: int
    existing_values: Optional[Dict[str, List[Any]]] = None  # For uniqueness
    seed: Optional[int] = None


class ChunkGenerationResponse(BaseModel):
    """Response from chunk generation."""
    chunk_id: int
    data: List[Dict[str, Any]]
    rows_generated: int
    metadata: ChunkMetadata
    issues: List[str] = Field(default_factory=list)


class DatasetDownloadInfo(BaseModel):
    """Information for downloading completed dataset."""
    job_id: UUID
    download_url: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: int
    format: OutputFormat
    total_rows: int
    expires_at: Optional[datetime] = None
    checksum: str


class JobControlRequest(BaseModel):
    """Request to control job execution."""
    job_id: UUID
    action: str  # "pause", "resume", "cancel", "retry"
    reason: Optional[str] = None


class ProgressUpdateNotification(BaseModel):
    """Notification of job progress update."""
    job_id: UUID
    progress: JobProgress
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
