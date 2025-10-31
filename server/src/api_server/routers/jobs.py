"""Job management and data generation endpoints."""

import asyncio
import csv
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.api.gemini_client import get_gemini_client
from src.config import settings
from src.core.job_manager import get_job_manager
from src.core.models import (
    DataSchema,
    JobControlRequest,
    JobSpecification,
    JobState,
    JobStatus,
    OutputFormat,
    StorageType,
)
from src.storage.handlers import get_storage_handler
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class CreateJobRequest(BaseModel):
    """Request model for creating a generation job."""
    schema: DataSchema
    total_rows: int
    chunk_size: int = 1000
    output_format: OutputFormat = OutputFormat.CSV
    storage_type: StorageType = StorageType.DISK
    uniqueness_fields: list[str] = []
    seed: int | None = None


class CreateJobResponse(BaseModel):
    """Response model for job creation."""
    job_id: UUID
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status."""
    job_id: UUID
    status: JobStatus
    rows_generated: int
    total_rows: int
    chunks_completed: int
    total_chunks: int
    progress_percentage: float
    error_message: str | None = None


class ListJobsResponse(BaseModel):
    """Response model for listing jobs."""
    jobs: list[JobState]
    total: int


@router.post("/create", response_model=CreateJobResponse)
async def create_job(request: CreateJobRequest, background_tasks: BackgroundTasks):
    """Create a new data generation job and start processing.
    
    Args:
        request: Job creation request
        background_tasks: FastAPI background tasks
        
    Returns:
        Job creation response with job ID
    """
    try:
        job_manager = get_job_manager()

        # Validate schema
        issues = request.schema.validate_constraints()
        if issues:
            raise HTTPException(
                status_code=400,
                detail=f"Schema validation failed: {', '.join(issues)}"
            )

        # Create job specification
        specification = JobSpecification(
            schema=request.schema,
            total_rows=request.total_rows,
            chunk_size=request.chunk_size,
            output_format=request.output_format,
            storage_type=request.storage_type,
            uniqueness_fields=request.uniqueness_fields,
            seed=request.seed
        )

        # Create job
        job_state = job_manager.create_job(specification)

        # Start generation in background
        background_tasks.add_task(generate_data, job_state.specification.job_id)

        logger.info(f"Created job {job_state.specification.job_id}")

        return CreateJobResponse(
            job_id=job_state.specification.job_id,
            status=job_state.progress.status,
            message=f"Job created successfully. Generating {request.total_rows} rows."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: UUID):
    """Get status of a specific job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status information
    """
    try:
        job_manager = get_job_manager()
        job = job_manager.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return JobStatusResponse(
            job_id=job.specification.job_id,
            status=job.progress.status,
            rows_generated=job.progress.rows_generated,
            total_rows=job.specification.total_rows,
            chunks_completed=job.progress.chunks_completed,
            total_chunks=job.progress.total_chunks,
            progress_percentage=job.progress.progress_percentage,
            error_message=job.progress.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/{job_id}", response_model=JobState)
async def get_job_details(job_id: UUID):
    """Get detailed information about a job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Complete job state
    """
    try:
        job_manager = get_job_manager()
        job = job_manager.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job details: {str(e)}")


@router.get("/", response_model=ListJobsResponse)
async def list_jobs(status: JobStatus | None = None, limit: int = 100):
    """List all jobs with optional filtering.
    
    Args:
        status: Optional status filter
        limit: Maximum number of jobs to return
        
    Returns:
        List of jobs
    """
    try:
        job_manager = get_job_manager()
        jobs = job_manager.list_jobs(status=status, limit=limit)

        return ListJobsResponse(
            jobs=jobs,
            total=len(jobs)
        )

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.post("/{job_id}/control")
async def control_job(job_id: UUID, request: JobControlRequest):
    """Control job execution (pause, resume, cancel).
    
    Args:
        job_id: Job identifier
        request: Control request
        
    Returns:
        Success message
    """
    try:
        # Ensure job_id matches
        if request.job_id != job_id:
            raise HTTPException(
                status_code=400,
                detail="Job ID in path does not match request body"
            )

        job_manager = get_job_manager()
        success = job_manager.control_job(request)

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to {request.action} job {job_id}"
            )

        return {"message": f"Job {job_id} {request.action} successful"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to control job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to control job: {str(e)}")


@router.get("/{job_id}/download")
async def download_job_output(job_id: UUID):
    """Download the generated dataset.
    
    Args:
        job_id: Job identifier
        
    Returns:
        File response with generated data
    """
    try:
        job_manager = get_job_manager()
        job = job_manager.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        if job.progress.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Job is not completed yet. Current status: {job.progress.status}"
            )

        # Get output file path
        output_path = settings.output_dir / f"{job_id}.csv"

        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Output file not found")

        return FileResponse(
            path=output_path,
            filename=f"synthetic_data_{job_id}.csv",
            media_type="text/csv"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download job output: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download output: {str(e)}")


@router.get("/{job_id}/preview")
async def preview_job_output(job_id: UUID, rows: int = 10):
    """Preview the first few rows of generated data.
    
    Args:
        job_id: Job identifier
        rows: Number of rows to preview (default 10, max 100)
        
    Returns:
        Preview data as JSON
    """
    try:
        rows = min(rows, 100)  # Limit preview size

        job_manager = get_job_manager()
        job = job_manager.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        if job.progress.rows_generated == 0:
            raise HTTPException(status_code=400, detail="No data generated yet")

        # Get output file path
        output_path = settings.output_dir / f"{job_id}.csv"

        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Output file not found")

        # Read preview rows
        preview_data = []
        with open(output_path) as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= rows:
                    break
                preview_data.append(row)

        return {
            "job_id": str(job_id),
            "total_rows": job.progress.rows_generated,
            "preview_rows": len(preview_data),
            "data": preview_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to preview job output: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preview output: {str(e)}")


async def generate_data(job_id: UUID):
    """Background task to generate data for a job.
    
    Args:
        job_id: Job identifier
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        logger.error(f"Job {job_id} not found")
        return

    try:
        logger.info(f"Starting data generation for job {job_id}")
        job_manager.update_job_status(job_id, JobStatus.GENERATING)

        gemini_client = get_gemini_client()
        storage_handler = get_storage_handler(job.specification.storage_type)

        # Track unique values
        unique_values = {
            field: []
            for field in job.specification.uniqueness_fields
        }

        # Generate chunks
        total_chunks = job.progress.total_chunks
        remaining_rows = job.specification.total_rows

        for chunk_id in range(total_chunks):
            # Check if job is paused or cancelled
            job = job_manager.get_job(job_id)
            if job.progress.status == JobStatus.PAUSED:
                logger.info(f"Job {job_id} paused at chunk {chunk_id}")
                while job.progress.status == JobStatus.PAUSED:
                    await asyncio.sleep(1)
                    job = job_manager.get_job(job_id)

            if job.progress.status == JobStatus.CANCELLED:
                logger.info(f"Job {job_id} cancelled at chunk {chunk_id}")
                return

            # Calculate rows for this chunk
            rows_in_chunk = min(job.specification.chunk_size, remaining_rows)

            logger.info(f"Generating chunk {chunk_id + 1}/{total_chunks} ({rows_in_chunk} rows)")

            # Generate data
            data = gemini_client.generate_data_chunk(
                schema=job.specification.schema,
                num_rows=rows_in_chunk,
                existing_values=unique_values if unique_values else None,
                seed=job.specification.seed
            )

            # Update unique values
            for field in job.specification.uniqueness_fields:
                if field in data[0]:
                    unique_values[field].extend([row[field] for row in data])

            # Store chunk
            chunk_metadata = storage_handler.store_chunk(
                job_id=job_id,
                chunk_id=chunk_id,
                data=data,
                format=job.specification.output_format
            )

            # Update job
            job_manager.add_chunk(job_id, chunk_metadata)

            remaining_rows -= rows_in_chunk

        # Consolidate chunks into final output
        logger.info(f"Consolidating chunks for job {job_id}")
        output_path = settings.output_dir / f"{job_id}.csv"
        storage_handler.merge_chunks(
            job_id=job_id,
            chunks=job.chunks,
            output_path=output_path,
            format=job.specification.output_format
        )

        # Mark job as completed
        job_manager.update_job_status(job_id, JobStatus.COMPLETED)
        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Error generating data for job {job_id}: {e}")
        job_manager.update_job_status(job_id, JobStatus.FAILED, error=str(e))
