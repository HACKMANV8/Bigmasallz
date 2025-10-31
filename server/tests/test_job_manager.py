"""Tests for job manager helper behaviours."""

from typing import Iterator

import pytest

from src.config import settings
from src.core import job_manager as job_manager_module
from src.core.job_manager import JobManager
from src.core.models import DataSchema, FieldDefinition, FieldType, JobSpecification


@pytest.fixture()
def isolated_job_manager(tmp_path, monkeypatch) -> Iterator[JobManager]:
    """Provide a fresh job manager instance with isolated persistence."""
    persistence_dir = tmp_path / "jobs"
    original_persistence = settings.job_persistence_path
    monkeypatch.setattr(settings, "job_persistence_path", str(persistence_dir))
    monkeypatch.setattr(job_manager_module, "_job_manager", None)
    manager = job_manager_module.get_job_manager()
    yield manager
    monkeypatch.setattr(settings, "job_persistence_path", original_persistence)
    monkeypatch.setattr(job_manager_module, "_job_manager", None)


def _create_mock_job(manager: JobManager) -> JobSpecification:
    schema = DataSchema(fields=[FieldDefinition(name="id", type=FieldType.INTEGER)])
    specification = JobSpecification(schema=schema, total_rows=10, chunk_size=5)
    manager.create_job(specification)
    return specification


def test_set_current_chunk_tracks_progress(isolated_job_manager: JobManager):
    job_spec = _create_mock_job(isolated_job_manager)
    job_id = job_spec.job_id

    job = isolated_job_manager.get_job(job_id)
    assert job is not None
    assert job.progress.current_chunk is None

    isolated_job_manager.set_current_chunk(job_id, 2)
    job = isolated_job_manager.get_job(job_id)
    assert job is not None
    assert job.progress.current_chunk == 2

    isolated_job_manager.set_current_chunk(job_id, None)
    job = isolated_job_manager.get_job(job_id)
    assert job is not None
    assert job.progress.current_chunk is None
