"""Job management system for data generation tasks."""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from collections import deque

from src.core.models import (
    JobSpecification,
    JobState,
    JobProgress,
    JobStatus,
    ChunkMetadata,
    JobControlRequest
)
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class JobManager:
    """Manages data generation jobs lifecycle and state."""
    
    def __init__(self):
        """Initialize job manager."""
        self.jobs: Dict[UUID, JobState] = {}
        self.job_queue: deque = deque()
        self.active_jobs: Dict[UUID, asyncio.Task] = {}
        self.max_concurrent_jobs = settings.job.max_concurrent_jobs
        self.persistence_path = settings.job.persistence_path
        
        # Create persistence directory
        self.persistence_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing jobs from disk
        self._load_jobs()
        
        logger.info(f"Initialized JobManager with {len(self.jobs)} existing jobs")
    
    def create_job(self, specification: JobSpecification) -> JobState:
        """Create a new job.
        
        Args:
            specification: Job specification
            
        Returns:
            Created job state
        """
        # Calculate total chunks needed
        total_chunks = (specification.total_rows + specification.chunk_size - 1) // specification.chunk_size
        
        # Create job progress
        progress = JobProgress(
            job_id=specification.job_id,
            status=JobStatus.PENDING,
            total_chunks=total_chunks,
            rows_generated=0,
            chunks_completed=0
        )
        
        # Create job state
        job_state = JobState(
            specification=specification,
            progress=progress,
            chunks=[],
            schema_validated=False,
            can_resume=True
        )
        
        # Store job
        self.jobs[specification.job_id] = job_state
        self._persist_job(job_state)
        
        logger.info(f"Created job {specification.job_id} for {specification.total_rows} rows")
        return job_state
    
    def get_job(self, job_id: UUID) -> Optional[JobState]:
        """Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job state or None if not found
        """
        return self.jobs.get(job_id)
    
    def update_job_status(self, job_id: UUID, status: JobStatus, error: Optional[str] = None):
        """Update job status.
        
        Args:
            job_id: Job identifier
            status: New status
            error: Optional error message
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found for status update")
            return
        
        job.progress.status = status
        
        if status == JobStatus.GENERATING and not job.progress.started_at:
            job.progress.started_at = datetime.now()
        elif status == JobStatus.COMPLETED:
            job.progress.completed_at = datetime.now()
            job.progress.progress_percentage = 100.0
        elif status == JobStatus.PAUSED:
            job.progress.paused_at = datetime.now()
        elif status == JobStatus.FAILED:
            job.progress.error_message = error
            job.progress.completed_at = datetime.now()
        
        self._persist_job(job)
        logger.info(f"Job {job_id} status updated to {status}")
    
    def add_chunk(self, job_id: UUID, chunk: ChunkMetadata):
        """Add completed chunk to job.
        
        Args:
            job_id: Job identifier
            chunk: Chunk metadata
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found for chunk addition")
            return
        
        job.add_chunk(chunk)
        self._persist_job(job)
        
        logger.info(
            f"Job {job_id}: Chunk {chunk.chunk_id} completed "
            f"({job.progress.chunks_completed}/{job.progress.total_chunks}, "
            f"{job.progress.progress_percentage:.1f}%)"
        )
    
    def validate_schema(self, job_id: UUID):
        """Mark job schema as validated.
        
        Args:
            job_id: Job identifier
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found for schema validation")
            return
        
        job.schema_validated = True
        self._persist_job(job)
        logger.info(f"Job {job_id} schema validated")
    
    def control_job(self, request: JobControlRequest) -> bool:
        """Control job execution (pause, resume, cancel).
        
        Args:
            request: Job control request
            
        Returns:
            True if action was successful
        """
        job = self.jobs.get(request.job_id)
        if not job:
            logger.warning(f"Job {request.job_id} not found for control action")
            return False
        
        if request.action == "pause":
            if job.progress.status == JobStatus.GENERATING:
                self.update_job_status(request.job_id, JobStatus.PAUSED)
                return True
            else:
                logger.warning(f"Cannot pause job {request.job_id} in status {job.progress.status}")
                return False
        
        elif request.action == "resume":
            if job.progress.status == JobStatus.PAUSED:
                self.update_job_status(request.job_id, JobStatus.GENERATING)
                job.progress.paused_at = None
                self._persist_job(job)
                return True
            else:
                logger.warning(f"Cannot resume job {request.job_id} in status {job.progress.status}")
                return False
        
        elif request.action == "cancel":
            if job.progress.status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
                self.update_job_status(request.job_id, JobStatus.CANCELLED)
                job.can_resume = False
                self._persist_job(job)
                return True
            else:
                logger.warning(f"Cannot cancel job {request.job_id} in status {job.progress.status}")
                return False
        
        elif request.action == "retry":
            if job.progress.status == JobStatus.FAILED and job.can_resume:
                # Reset to last successful chunk
                job.progress.status = JobStatus.PENDING
                job.progress.error_message = None
                self._persist_job(job)
                return True
            else:
                logger.warning(f"Cannot retry job {request.job_id}")
                return False
        
        return False
    
    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> List[JobState]:
        """List jobs with optional filtering.
        
        Args:
            status: Optional status filter
            limit: Maximum number of jobs to return
            
        Returns:
            List of job states
        """
        jobs = list(self.jobs.values())
        
        if status:
            jobs = [j for j in jobs if j.progress.status == status]
        
        # Sort by created date (newest first)
        jobs.sort(key=lambda j: j.specification.created_at, reverse=True)
        
        return jobs[:limit]
    
    def cleanup_old_jobs(self, days: int = None):
        """Clean up old completed/failed jobs.
        
        Args:
            days: Number of days to keep jobs (default from config)
        """
        if days is None:
            days = settings.job.cleanup_days
        
        cutoff_date = datetime.now() - timedelta(days=days)
        jobs_to_remove = []
        
        for job_id, job in self.jobs.items():
            if job.progress.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                if job.specification.created_at < cutoff_date:
                    jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            self._remove_job(job_id)
        
        logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
    
    def _persist_job(self, job: JobState):
        """Persist job state to disk.
        
        Args:
            job: Job state to persist
        """
        try:
            job_file = self.persistence_path / f"{job.specification.job_id}.json"
            with open(job_file, 'w') as f:
                json.dump(job.model_dump(mode='json'), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to persist job {job.specification.job_id}: {e}")
    
    def _load_jobs(self):
        """Load jobs from disk."""
        try:
            for job_file in self.persistence_path.glob("*.json"):
                try:
                    with open(job_file, 'r') as f:
                        job_data = json.load(f)
                        job = JobState(**job_data)
                        self.jobs[job.specification.job_id] = job
                except Exception as e:
                    logger.error(f"Failed to load job from {job_file}: {e}")
        except Exception as e:
            logger.error(f"Failed to load jobs: {e}")
    
    def _remove_job(self, job_id: UUID):
        """Remove job from memory and disk.
        
        Args:
            job_id: Job identifier
        """
        # Remove from memory
        if job_id in self.jobs:
            del self.jobs[job_id]
        
        # Remove from disk
        job_file = self.persistence_path / f"{job_id}.json"
        if job_file.exists():
            job_file.unlink()
        
        logger.info(f"Removed job {job_id}")


# Global job manager instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get or create global job manager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
