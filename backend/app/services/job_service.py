import logging
from typing import Dict, Optional, List
from datetime import datetime

from app.models.job import Job, JobStatus, JobStatusResponse
from app.models.data import GeneratedDataResult

logger = logging.getLogger(__name__)


class JobService:
    """Service for managing job state and queries."""

    def __init__(self):
        # In-memory job storage (use Redis or DB in production)
        self._jobs: Dict[str, Job] = {}

    async def create_job(
        self, total_rows: int, total_chunks: int
    ) -> Job:
        """
        Create a new job.

        Args:
            total_rows: Total rows to generate
            total_chunks: Total chunks to process

        Returns:
            Created job
        """
        job = Job(
            total_rows=total_rows,
            total_chunks=total_chunks,
            status=JobStatus.PENDING,
        )

        self._jobs[job.job_id] = job
        logger.info(f"Created job {job.job_id}: {total_rows} rows, {total_chunks} chunks")

        return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)

    async def update_job(self, job_id: str, **updates) -> Optional[Job]:
        """
        Update job fields.

        Args:
            job_id: Job ID
            **updates: Fields to update

        Returns:
            Updated job or None
        """
        job = self._jobs.get(job_id)
        if not job:
            return None

        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)

        return job

    async def increment_completed_chunks(
        self, job_id: str, rows_added: int = 0, deduplicated: int = 0
    ) -> Optional[Job]:
        """
        Increment completed chunks counter.

        Args:
            job_id: Job ID
            rows_added: Rows added in this chunk
            deduplicated: Rows deduplicated in this chunk

        Returns:
            Updated job
        """
        job = self._jobs.get(job_id)
        if not job:
            return None

        job.completed_chunks += 1
        job.rows_generated += rows_added
        job.rows_deduplicated += deduplicated

        # Update status
        if job.status == JobStatus.PENDING:
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()

        if job.completed_chunks >= job.total_chunks:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()

        return job

    async def mark_job_failed(
        self, job_id: str, error_message: str
    ) -> Optional[Job]:
        """
        Mark job as failed.

        Args:
            job_id: Job ID
            error_message: Error message

        Returns:
            Updated job
        """
        job = self._jobs.get(job_id)
        if not job:
            return None

        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.utcnow()

        logger.error(f"Job {job_id} failed: {error_message}")

        return job

    async def set_job_results(
        self, job_id: str, results: GeneratedDataResult
    ) -> Optional[Job]:
        """
        Set job results.

        Args:
            job_id: Job ID
            results: Generated data results

        Returns:
            Updated job
        """
        job = self._jobs.get(job_id)
        if not job:
            return None

        job.results = results.dict()
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()

        return job

    async def get_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """
        Get job status response.

        Args:
            job_id: Job ID

        Returns:
            Job status response
        """
        job = self._jobs.get(job_id)
        if not job:
            return None

        progress = (
            (job.completed_chunks / job.total_chunks * 100)
            if job.total_chunks > 0
            else 0
        )

        # Estimate completion time
        estimated_completion = None
        if (
            job.status == JobStatus.PROCESSING
            and job.started_at
            and job.completed_chunks > 0
        ):
            elapsed = (datetime.utcnow() - job.started_at).total_seconds()
            avg_time_per_chunk = elapsed / job.completed_chunks
            remaining_chunks = job.total_chunks - job.completed_chunks
            estimated_seconds = avg_time_per_chunk * remaining_chunks
            estimated_completion = datetime.utcnow().timestamp() + estimated_seconds

        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            total_chunks=job.total_chunks,
            completed_chunks=job.completed_chunks,
            progress_percentage=round(progress, 2),
            rows_generated=job.rows_generated,
            rows_deduplicated=job.rows_deduplicated,
            created_at=job.created_at,
            estimated_completion=(
                datetime.fromtimestamp(estimated_completion)
                if estimated_completion
                else None
            ),
            results=job.results,
            error_message=job.error_message,
        )

    async def list_jobs(
        self,
        limit: int = 100,
        offset: int = 0,
        status_filter: Optional[str] = None,
    ) -> List[Job]:
        """
        List jobs with optional filtering.

        Args:
            limit: Maximum number of jobs
            offset: Number to skip
            status_filter: Filter by status

        Returns:
            List of jobs
        """
        jobs = list(self._jobs.values())

        # Filter by status
        if status_filter:
            try:
                status_enum = JobStatus(status_filter.lower())
                jobs = [j for j in jobs if j.status == status_enum]
            except ValueError:
                pass  # Invalid status filter, return all

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        # Apply pagination
        return jobs[offset : offset + limit]

    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a job.

        Args:
            job_id: Job ID

        Returns:
            True if deleted, False if not found
        """
        if job_id in self._jobs:
            del self._jobs[job_id]
            logger.info(f"Deleted job {job_id}")
            return True
        return False
