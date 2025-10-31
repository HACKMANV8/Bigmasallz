"""Job management endpoints for the Synthetic Data Generator API."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.core.models import ChunkMetadata, JobControlRequest, JobProgress, JobState, JobStatus
from src.services.generation_service import get_generation_service
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
generation_service = get_generation_service()


class JobProgressDetail(BaseModel):
    """Lightweight progress summary for a job."""

    status: JobStatus
    rows_generated: int
    total_rows: int
    chunks_completed: int
    total_chunks: int
    progress_percentage: float
    current_chunk: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    paused_at: datetime | None = None
    estimated_completion: datetime | None = None
    error_message: str | None = None


class ChunkMetadataModel(BaseModel):
    """Serialized chunk metadata."""

    chunk_id: int
    job_id: UUID
    rows_generated: int
    storage_location: str
    timestamp: datetime
    checksum: str | None = None
    size_bytes: int | None = None


class JobCreateRequest(BaseModel):
    """Request payload for creating a generation job."""

    schema: dict[str, Any]
    total_rows: int = Field(gt=0)
    chunk_size: int | None = Field(default=None, gt=0)
    output_format: str | None = Field(default=None)
    storage_type: str | None = Field(default=None)
    uniqueness_fields: list[str] | None = None
    seed: int | None = None
    name: str | None = None
    description: str | None = None
    created_by: str | None = None
    metadata: dict[str, Any] | None = None
    auto_start: bool = Field(default=True, description="Start generation immediately after job creation")


class JobCreateResponse(BaseModel):
    """Response payload after creating a job."""

    job_id: UUID
    status: JobStatus
    total_rows: int
    chunk_size: int
    total_chunks: int
    output_format: str
    storage_type: str
    uniqueness_fields: list[str] = Field(default_factory=list)
    seed: int | None = None
    job_progress: JobProgressDetail
    message: str = "Job created successfully. Use /jobs/{job_id}/chunks to generate data."
    auto_started: bool = False


class JobSummary(BaseModel):
    """Summary representation for job listings."""

    job_id: UUID
    status: JobStatus
    total_rows: int
    rows_generated: int
    progress_percentage: float
    chunk_size: int
    output_format: str
    created_at: datetime


class JobListResponse(BaseModel):
    """Response for job list endpoint."""

    total: int
    jobs: list[JobSummary]


class JobDetailResponse(BaseModel):
    """Full job detail representation."""

    job_id: UUID
    status: JobStatus
    total_rows: int
    chunk_size: int
    output_format: str
    storage_type: str
    uniqueness_fields: list[str] = Field(default_factory=list)
    seed: int | None = None
    created_at: datetime
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    schema: dict[str, Any]
    schema_validated: bool
    can_resume: bool
    job_progress: JobProgressDetail
    chunks: list[ChunkMetadataModel] = Field(default_factory=list)
    download_url: str | None = None


class JobProgressResponse(BaseModel):
    """Response for job progress endpoint."""

    job_id: UUID
    job_progress: JobProgressDetail


class ChunkGenerateRequest(BaseModel):
    """Payload for triggering chunk generation."""

    chunk_id: int = Field(gt=0)


class ChunkGenerateResponse(BaseModel):
    """Response after generating a chunk."""

    job_id: UUID
    chunk_id: int
    rows_generated: int
    issues: list[str] = Field(default_factory=list)
    chunk_metadata: ChunkMetadataModel
    job_progress: JobProgressDetail


class JobControlRequestModel(BaseModel):
    """Payload for job control actions."""

    action: Literal["pause", "resume", "cancel", "retry"]
    reason: str | None = None


class JobControlResponse(BaseModel):
    """Response after controlling a job."""

    success: bool
    message: str


class JobMergeResponse(BaseModel):
    """Response containing dataset download information."""

    job_id: UUID
    file_path: str | None = None
    file_size_bytes: int | None = None
    file_size_mb: float | None = None
    format: str
    total_rows: int
    checksum: str
    download_url: str | None = None


def _run_job_background(job_id: UUID):
    """Execute job generation in the background."""
    try:
        generation_service.run_job(job_id)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Background execution failed for job %s: %s", job_id, exc, exc_info=True)


def _build_progress_model(progress: JobProgress, total_rows: int) -> JobProgressDetail:
    return JobProgressDetail(
        status=progress.status,
        rows_generated=progress.rows_generated,
        total_rows=total_rows,
        chunks_completed=progress.chunks_completed,
        total_chunks=progress.total_chunks,
        progress_percentage=progress.progress_percentage,
        current_chunk=progress.current_chunk,
        started_at=progress.started_at,
        completed_at=progress.completed_at,
        paused_at=progress.paused_at,
        estimated_completion=progress.estimated_completion,
        error_message=progress.error_message,
    )


def _build_chunk_model(metadata: ChunkMetadata) -> ChunkMetadataModel:
    return ChunkMetadataModel(
        chunk_id=metadata.chunk_id,
        job_id=metadata.job_id,
        rows_generated=metadata.rows_generated,
        storage_location=metadata.storage_location,
        timestamp=metadata.timestamp,
        checksum=metadata.checksum,
        size_bytes=metadata.size_bytes,
    )


def _build_job_detail(job: JobState) -> JobDetailResponse:
    return JobDetailResponse(
        job_id=job.specification.job_id,
        status=job.progress.status,
        total_rows=job.specification.total_rows,
        chunk_size=job.specification.chunk_size,
        output_format=job.specification.output_format.value,
        storage_type=job.specification.storage_type.value,
        uniqueness_fields=list(job.specification.uniqueness_fields),
        seed=job.specification.seed,
        created_at=job.specification.created_at,
        created_by=job.specification.created_by,
        metadata=job.specification.metadata,
        schema=job.specification.schema.model_dump(mode="json"),
        schema_validated=job.schema_validated,
        can_resume=job.can_resume,
        job_progress=_build_progress_model(job.progress, job.specification.total_rows),
        chunks=[_build_chunk_model(chunk) for chunk in job.chunks],
        download_url=(
            f"/jobs/{job.specification.job_id}/download"
            if job.progress.status == JobStatus.COMPLETED
            else None
        ),
    )


def _build_job_summary(job: JobState) -> JobSummary:
    return JobSummary(
        job_id=job.specification.job_id,
        status=job.progress.status,
        total_rows=job.specification.total_rows,
        rows_generated=job.progress.rows_generated,
        progress_percentage=job.progress.progress_percentage,
        chunk_size=job.specification.chunk_size,
        output_format=job.specification.output_format.value,
        created_at=job.specification.created_at,
    )


@router.post("/", response_model=JobCreateResponse)
async def create_job(request: JobCreateRequest, background_tasks: BackgroundTasks) -> JobCreateResponse:
    """Create a new generation job."""
    try:
        job_state = generation_service.create_generation_job(
            schema=request.schema,
            total_rows=request.total_rows,
            chunk_size=request.chunk_size,
            output_format=request.output_format,
            uniqueness_fields=request.uniqueness_fields,
            seed=request.seed,
            name=request.name,
            description=request.description,
            created_by=request.created_by,
            metadata=request.metadata,
            storage_type=request.storage_type,
        )
    except ValueError as exc:
        logger.warning("Job creation validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Job creation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create job") from exc

    auto_started = False
    if request.auto_start:
        background_tasks.add_task(_run_job_background, job_state.specification.job_id)
        auto_started = True

    return JobCreateResponse(
        job_id=job_state.specification.job_id,
        status=job_state.progress.status,
        total_rows=job_state.specification.total_rows,
        chunk_size=job_state.specification.chunk_size,
        total_chunks=job_state.progress.total_chunks,
        output_format=job_state.specification.output_format.value,
        storage_type=job_state.specification.storage_type.value,
        uniqueness_fields=list(job_state.specification.uniqueness_fields),
        seed=job_state.specification.seed,
        job_progress=_build_progress_model(job_state.progress, job_state.specification.total_rows),
        message=(
            "Job created and generation started"
            if auto_started
            else "Job created successfully. Start generation when ready."
        ),
        auto_started=auto_started,
    )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    status: JobStatus | None = Query(default=None, description="Optional status filter"),
    limit: int = Query(default=100, ge=1, le=500),
) -> JobListResponse:
    """List generation jobs with optional filters."""
    jobs = generation_service.list_jobs(status=status, limit=limit)
    return JobListResponse(total=len(jobs), jobs=[_build_job_summary(job) for job in jobs])


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: UUID) -> JobDetailResponse:
    """Retrieve a job by its identifier."""
    job = generation_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return _build_job_detail(job)


@router.get("/{job_id}/progress", response_model=JobProgressResponse)
async def get_job_progress(job_id: UUID) -> JobProgressResponse:
    """Retrieve progress information for a job."""
    job = generation_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return JobProgressResponse(
        job_id=job_id,
        job_progress=_build_progress_model(job.progress, job.specification.total_rows),
    )


@router.post("/{job_id}/chunks", response_model=ChunkGenerateResponse)
async def generate_chunk(job_id: UUID, request: ChunkGenerateRequest) -> ChunkGenerateResponse:
    """Generate a specific chunk for the given job."""
    try:
        response = generation_service.generate_chunk(job_id=job_id, chunk_id=request.chunk_id)
        job = generation_service.get_job(job_id)
        if not job:
            raise RuntimeError(f"Job {job_id} missing after chunk generation")
    except ValueError as exc:
        logger.warning("Chunk generation validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Chunk generation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate chunk") from exc

    return ChunkGenerateResponse(
        job_id=job_id,
        chunk_id=request.chunk_id,
        rows_generated=response.rows_generated,
        issues=response.issues,
        chunk_metadata=_build_chunk_model(response.metadata),
        job_progress=_build_progress_model(job.progress, job.specification.total_rows),
    )


@router.post("/{job_id}/control", response_model=JobControlResponse)
async def control_job(job_id: UUID, request: JobControlRequestModel) -> JobControlResponse:
    """Pause, resume, cancel, or retry a job."""
    job = generation_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    control_request = JobControlRequest(job_id=job_id, action=request.action, reason=request.reason)
    success = generation_service.control_job(control_request)

    message = f"Job {job_id} {request.action} successful" if success else f"Failed to {request.action} job {job_id}"
    status_code = 200 if success else 409

    if not success:
        raise HTTPException(status_code=status_code, detail=message)

    return JobControlResponse(success=True, message=message)


@router.post("/{job_id}/merge", response_model=JobMergeResponse)
async def merge_job(job_id: UUID) -> JobMergeResponse:
    """Merge generated chunks and prepare dataset download."""
    try:
        download_info = generation_service.merge_job_dataset(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Dataset merge failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to merge dataset") from exc

    file_size_mb: float | None = None
    if download_info.file_size_bytes is not None:
        file_size_mb = round(download_info.file_size_bytes / (1024 * 1024), 2)

    return JobMergeResponse(
        job_id=download_info.job_id,
        file_path=download_info.file_path,
        file_size_bytes=download_info.file_size_bytes,
        file_size_mb=file_size_mb,
        format=download_info.format.value,
        total_rows=download_info.total_rows,
        checksum=download_info.checksum,
        download_url=download_info.download_url,
    )


@router.post("/{job_id}/run", response_model=JobControlResponse)
async def run_job(job_id: UUID, background_tasks: BackgroundTasks) -> JobControlResponse:
    """Trigger background generation for a job."""
    job = generation_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.progress.status == JobStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Job already completed")

    if job.progress.status == JobStatus.GENERATING:
        raise HTTPException(status_code=409, detail="Job is already generating")

    background_tasks.add_task(_run_job_background, job_id)
    return JobControlResponse(success=True, message=f"Job {job_id} generation started")


@router.get("/{job_id}/download")
async def download_job(job_id: UUID) -> FileResponse:
    """Download the merged dataset for a completed job."""
    job = generation_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    download_info = generation_service.merge_job_dataset(job_id)
    if not download_info.file_path:
        raise HTTPException(status_code=500, detail="Dataset file unavailable")

    file_path = Path(download_info.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset file not found on disk")

    media_type = {
        "csv": "text/csv",
        "json": "application/json",
        "parquet": "application/octet-stream",
    }.get(download_info.format.value, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type=media_type,
    )
