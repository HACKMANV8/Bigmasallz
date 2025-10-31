"""Test suite for core models."""

import pytest
from datetime import datetime
from uuid import UUID

from src.core.models import (
    FieldType,
    FieldDefinition,
    FieldConstraint,
    DataSchema,
    JobSpecification,
    OutputFormat,
    StorageType,
    JobProgress,
    JobStatus,
    ChunkMetadata,
)


def test_field_definition_creation():
    """Test creating a field definition."""
    constraints = FieldConstraint(
        unique=True,
        nullable=False,
        min_value=0,
        max_value=100
    )
    
    field = FieldDefinition(
        name="age",
        type=FieldType.INTEGER,
        description="User age",
        constraints=constraints,
        sample_values=[25, 30, 45]
    )
    
    assert field.name == "age"
    assert field.type == FieldType.INTEGER
    assert field.constraints.unique is True
    assert field.constraints.min_value == 0


def test_schema_validation():
    """Test schema constraint validation."""
    fields = [
        FieldDefinition(
            name="id",
            type=FieldType.INTEGER,
            depends_on=None
        ),
        FieldDefinition(
            name="user_id",
            type=FieldType.INTEGER,
            depends_on=["id"]  # Valid dependency
        ),
        FieldDefinition(
            name="invalid_field",
            type=FieldType.STRING,
            depends_on=["nonexistent"]  # Invalid dependency
        )
    ]
    
    schema = DataSchema(fields=fields)
    issues = schema.validate_constraints()
    
    assert len(issues) > 0
    assert any("nonexistent" in issue for issue in issues)


def test_job_specification():
    """Test job specification creation."""
    schema = DataSchema(
        fields=[
            FieldDefinition(name="name", type=FieldType.STRING),
            FieldDefinition(name="age", type=FieldType.INTEGER)
        ]
    )
    
    spec = JobSpecification(
        schema=schema,
        total_rows=10000,
        chunk_size=1000,
        output_format=OutputFormat.CSV,
        storage_type=StorageType.DISK
    )
    
    assert spec.total_rows == 10000
    assert spec.chunk_size == 1000
    assert isinstance(spec.job_id, UUID)


def test_job_progress_update():
    """Test job progress tracking."""
    progress = JobProgress(
        job_id=UUID("12345678-1234-5678-1234-567812345678"),
        status=JobStatus.GENERATING,
        total_chunks=10,
        rows_generated=3000,
        chunks_completed=3
    )
    
    progress.update_progress()
    assert progress.progress_percentage == 30.0


def test_chunk_metadata():
    """Test chunk metadata creation."""
    metadata = ChunkMetadata(
        chunk_id=1,
        job_id=UUID("12345678-1234-5678-1234-567812345678"),
        rows_generated=1000,
        storage_location="/tmp/chunk_1.csv",
        checksum="abc123"
    )
    
    assert metadata.chunk_id == 1
    assert metadata.rows_generated == 1000
    assert isinstance(metadata.timestamp, datetime)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
