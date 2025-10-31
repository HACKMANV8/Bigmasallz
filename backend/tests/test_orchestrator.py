"""Tests for the orchestrator service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.orchestrator import OrchestratorService
from app.models.data import DataGenerationRequest
from app.models.schema import DataSchema


@pytest.mark.asyncio
async def test_create_generation_job(sample_schema):
    """Test job creation."""
    orchestrator = OrchestratorService()

    request = DataGenerationRequest(
        schema=sample_schema,
        total_rows=1000,
        chunk_size=100,
        max_workers=10,
    )

    job = await orchestrator.create_generation_job(request)

    assert job is not None
    assert job.total_rows == 1000
    assert job.total_chunks == 10  # 1000 rows / 100 chunk_size
    assert job.job_id in orchestrator._active_jobs


@pytest.mark.asyncio
async def test_cancel_job(sample_schema):
    """Test job cancellation."""
    orchestrator = OrchestratorService()

    request = DataGenerationRequest(
        schema=sample_schema,
        total_rows=1000,
    )

    job = await orchestrator.create_generation_job(request)

    # Cancel the job
    success = await orchestrator.cancel_job(job.job_id)

    assert success is True
    assert orchestrator._active_jobs[job.job_id]["cancelled"] is True


@pytest.mark.asyncio
async def test_cancel_nonexistent_job():
    """Test cancelling a job that doesn't exist."""
    orchestrator = OrchestratorService()

    success = await orchestrator.cancel_job("nonexistent-job-id")

    assert success is False


def test_chunk_calculation():
    """Test chunk size calculation logic."""
    from app.core.config import settings

    # Test that chunk size is clamped to min/max
    assert settings.MIN_CHUNK_SIZE <= settings.DEFAULT_CHUNK_SIZE <= settings.MAX_CHUNK_SIZE
