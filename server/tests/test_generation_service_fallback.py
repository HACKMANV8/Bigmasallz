"""Integration tests covering GenerationService fallback behaviour."""

from __future__ import annotations

import pytest
import tempfile
from pathlib import Path

from src.api import QuotaExceededError
from src.core.models import (
    DataSchema,
    FieldConstraint,
    FieldDefinition,
    FieldType,
    JobSpecification,
    SchemaExtractionResponse,
)
from src.config import settings
from src.services import generation_service as gs_module


class AlwaysQuotaGeminiClient:
    """Stub Gemini client that always raises quota errors."""

    def extract_schema(self, request):  # type: ignore[override]
        raise QuotaExceededError("quota", retry_after=30.0, quota_metric="test_metric")

    def generate_data_chunk(self, **kwargs):  # type: ignore[override]
        raise QuotaExceededError("quota", retry_after=30.0, quota_metric="test_metric")


@pytest.fixture()
def service_with_fallback(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setattr(settings, "job_persistence_path", temp_dir)
    monkeypatch.setattr("src.core.job_manager.JobManager._load_jobs", lambda self: None)
    monkeypatch.setattr("src.core.job_manager.JobManager._persist_job", lambda self, job: None)
    dummy_client = AlwaysQuotaGeminiClient()
    monkeypatch.setattr(gs_module, "get_gemini_client", lambda: dummy_client)
    # Reset singleton to avoid leaking stub into other tests
    monkeypatch.setattr(gs_module, "_generation_service", None)
    service = gs_module.GenerationService()
    service.job_manager.jobs.clear()
    service.job_manager.persistence_path = Path(temp_dir)
    return service


def test_extract_schema_uses_fallback(service_with_fallback):
    response: SchemaExtractionResponse = service_with_fallback.extract_schema_from_prompt(
        user_input="food, calories and protein"
    )

    assert any("Gemini quota" in warning for warning in response.warnings)
    assert response.schema.metadata.get("fallback", {}).get("reason") == "quota_exceeded"
    assert response.confidence <= 0.6


def test_generate_chunk_uses_fallback(service_with_fallback):
    schema = DataSchema(
        fields=[
            FieldDefinition(
                name="item_id",
                type=FieldType.UUID,
                description="Identifier",
                constraints=FieldConstraint(unique=True, nullable=False),
            ),
            FieldDefinition(
                name="name",
                type=FieldType.STRING,
                description="Name",
                constraints=FieldConstraint(unique=False, nullable=False),
            ),
        ],
        description="Fallback dataset",
        metadata={},
    )

    specification = JobSpecification(schema=schema, total_rows=5)
    service_with_fallback.job_manager.create_job(specification)

    chunk_response = service_with_fallback.generate_chunk(
        job_id=specification.job_id,
        chunk_id=1,
    )

    assert chunk_response.rows_generated == 5
    assert any("Gemini quota exceeded" in issue for issue in chunk_response.issues)
    unique_values = {row["item_id"] for row in chunk_response.data}
    assert len(unique_values) == 5
