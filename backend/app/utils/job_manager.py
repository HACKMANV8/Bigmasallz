"""
Job Manager - Handles job state management and persistence.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import redis
from ..core.config import settings
from ..core.logging import get_logger
from ..models.schemas import JobStatus, JobStatusResponse, ChunkProgress, AgentMetrics

logger = get_logger(__name__)


class JobManager:
    """
    Manages job state using Redis for persistence.
    Handles concurrent access and state updates.
    """
    
    def __init__(self):
        """Initialize the job manager with Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis for job management")
            self.use_redis = True
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Using in-memory storage.")
            self.use_redis = False
            self._jobs: Dict[str, Dict[str, Any]] = {}
    
    def _get_job_key(self, job_id: str) -> str:
        """Generate Redis key for a job."""
        return f"synthaix:job:{job_id}"
    
    def create_job(
        self, 
        schema: Dict[str, Any], 
        total_rows: int,
        chunk_size: int
    ) -> str:
        """
        Create a new job and return its ID.
        
        Args:
            schema: Data schema dictionary
            total_rows: Total rows to generate
            chunk_size: Rows per chunk
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        num_chunks = (total_rows + chunk_size - 1) // chunk_size
        
        job_data = {
            "job_id": job_id,
            "status": JobStatus.PENDING.value,
            "schema": schema,
            "total_rows": total_rows,
            "chunk_size": chunk_size,
            "num_chunks": num_chunks,
            "completed_rows": 0,
            "chunks": [],
            "metrics": {
                "tokens_used": 0,
                "api_calls": 0,
                "avg_response_time": 0.0,
                "deduplication_rate": 0.0,
                "total_duplicates_removed": 0,
                "chunks_completed": 0,
                "chunks_in_progress": 0,
                "chunks_failed": 0,
                "rows_per_second": 0.0,
                "estimated_time_remaining": 0.0
            },
            "data": [],
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "start_time": None,
            "end_time": None
        }
        
        # Initialize chunk progress
        for i in range(num_chunks):
            job_data["chunks"].append({
                "chunk_id": i,
                "status": JobStatus.PENDING.value,
                "rows_generated": 0,
                "duplicates_removed": 0,
                "error": None
            })
        
        self._save_job(job_id, job_data)
        logger.info(f"Created job {job_id} for {total_rows} rows in {num_chunks} chunks")
        
        return job_id
    
    def _save_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """Save job data to storage."""
        if self.use_redis:
            try:
                self.redis_client.setex(
                    self._get_job_key(job_id),
                    86400,  # 24 hour TTL
                    json.dumps(job_data)
                )
            except Exception as e:
                logger.error(f"Error saving job to Redis: {str(e)}")
        else:
            self._jobs[job_id] = job_data
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve job data.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job data dictionary or None if not found
        """
        if self.use_redis:
            try:
                data = self.redis_client.get(self._get_job_key(job_id))
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Error retrieving job from Redis: {str(e)}")
        else:
            return self._jobs.get(job_id)
        
        return None
    
    def update_job_status(self, job_id: str, status: JobStatus) -> None:
        """
        Update job status.
        
        Args:
            job_id: Job identifier
            status: New status
        """
        job_data = self.get_job(job_id)
        if job_data:
            job_data["status"] = status.value
            job_data["updated_at"] = datetime.utcnow().isoformat()
            
            if status == JobStatus.IN_PROGRESS and not job_data.get("start_time"):
                job_data["start_time"] = datetime.utcnow().isoformat()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job_data["end_time"] = datetime.utcnow().isoformat()
            
            self._save_job(job_id, job_data)
            logger.info(f"Job {job_id} status updated to {status.value}")
    
    def update_chunk(
        self, 
        job_id: str, 
        chunk_id: int, 
        chunk_result: Dict[str, Any]
    ) -> None:
        """
        Update chunk progress and aggregate data.
        
        Args:
            job_id: Job identifier
            chunk_id: Chunk identifier
            chunk_result: Chunk generation result
        """
        job_data = self.get_job(job_id)
        if not job_data:
            logger.error(f"Job {job_id} not found for chunk update")
            return
        
        # Update chunk info
        if chunk_id < len(job_data["chunks"]):
            job_data["chunks"][chunk_id].update({
                "status": chunk_result.get("status", JobStatus.COMPLETED.value),
                "rows_generated": chunk_result.get("rows_generated", 0),
                "duplicates_removed": chunk_result.get("duplicates_removed", 0),
                "error": chunk_result.get("error")
            })
        
        # Aggregate data
        if "data" in chunk_result and chunk_result["data"]:
            job_data["data"].extend(chunk_result["data"])
        
        # Update completed rows
        job_data["completed_rows"] = len(job_data["data"])
        
        # Update real-time metrics
        chunks_completed = sum(1 for c in job_data["chunks"] if c["status"] == "completed")
        chunks_in_progress = sum(1 for c in job_data["chunks"] if c["status"] == "in_progress")
        chunks_failed = sum(1 for c in job_data["chunks"] if c["status"] == "failed")
        
        job_data["metrics"]["chunks_completed"] = chunks_completed
        job_data["metrics"]["chunks_in_progress"] = chunks_in_progress
        job_data["metrics"]["chunks_failed"] = chunks_failed
        
        # Calculate rows per second and ETA
        if job_data["start_time"]:
            start_dt = datetime.fromisoformat(job_data["start_time"])
            elapsed = (datetime.utcnow() - start_dt).total_seconds()
            if elapsed > 0:
                rows_per_second = job_data["completed_rows"] / elapsed
                job_data["metrics"]["rows_per_second"] = round(rows_per_second, 2)
                
                # Estimate time remaining
                remaining_rows = job_data["total_rows"] - job_data["completed_rows"]
                if rows_per_second > 0:
                    eta_seconds = remaining_rows / rows_per_second
                    job_data["metrics"]["estimated_time_remaining"] = round(eta_seconds, 1)
        
        # Update metrics
        if "tokens_used" in chunk_result:
            job_data["metrics"]["tokens_used"] += chunk_result["tokens_used"]
        if chunk_result.get("status") == "completed":
            job_data["metrics"]["api_calls"] += 1
        
        job_data["metrics"]["total_duplicates_removed"] += chunk_result.get("duplicates_removed", 0)
        
        # Update timestamp
        job_data["updated_at"] = datetime.utcnow().isoformat()
        
        self._save_job(job_id, job_data)
        logger.debug(f"Updated chunk {chunk_id} for job {job_id}")
    
    def finalize_job(self, job_id: str, metrics: Dict[str, Any]) -> None:
        """
        Finalize job with aggregated metrics.
        
        Args:
            job_id: Job identifier
            metrics: Final metrics
        """
        job_data = self.get_job(job_id)
        if not job_data:
            return
        
        # Update final metrics
        job_data["metrics"].update(metrics)
        
        # Calculate deduplication rate
        total_generated = sum(c["rows_generated"] for c in job_data["chunks"])
        total_duplicates = job_data["metrics"]["total_duplicates_removed"]
        if total_generated > 0:
            job_data["metrics"]["deduplication_rate"] = total_duplicates / total_generated
        
        # Set final status
        failed_chunks = sum(1 for c in job_data["chunks"] if c["status"] == "failed")
        if failed_chunks > 0:
            job_data["status"] = JobStatus.FAILED.value
            job_data["error"] = f"{failed_chunks} chunks failed"
        else:
            job_data["status"] = JobStatus.COMPLETED.value
        
        job_data["end_time"] = datetime.utcnow().isoformat()
        job_data["updated_at"] = datetime.utcnow().isoformat()
        
        self._save_job(job_id, job_data)
        logger.info(f"Finalized job {job_id} with status {job_data['status']}")
    
    def get_job_status_response(self, job_id: str) -> Optional[JobStatusResponse]:
        """
        Get formatted job status response.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobStatusResponse or None
        """
        job_data = self.get_job(job_id)
        if not job_data:
            return None
        
        # Calculate progress
        progress_percentage = (
            (job_data["completed_rows"] / job_data["total_rows"]) * 100
            if job_data["total_rows"] > 0
            else 0.0
        )
        
        # Estimate time remaining
        estimated_time_remaining = None
        if job_data.get("start_time") and job_data["completed_rows"] > 0:
            start_time = datetime.fromisoformat(job_data["start_time"])
            elapsed_time = (datetime.utcnow() - start_time).total_seconds()
            rows_per_second = job_data["completed_rows"] / elapsed_time if elapsed_time > 0 else 0
            if rows_per_second > 0:
                remaining_rows = job_data["total_rows"] - job_data["completed_rows"]
                estimated_time_remaining = remaining_rows / rows_per_second
        
        # Build response
        chunks = [
            ChunkProgress(
                chunk_id=c["chunk_id"],
                status=JobStatus(c["status"]),
                rows_generated=c["rows_generated"],
                duplicates_removed=c["duplicates_removed"],
                error=c.get("error")
            )
            for c in job_data["chunks"]
        ]
        
        metrics = AgentMetrics(**job_data["metrics"])
        
        return JobStatusResponse(
            job_id=job_id,
            status=JobStatus(job_data["status"]),
            total_rows=job_data["total_rows"],
            completed_rows=job_data["completed_rows"],
            progress_percentage=progress_percentage,
            chunks=chunks,
            metrics=metrics,
            data=job_data["data"] if job_data["status"] == JobStatus.COMPLETED.value else None,
            error=job_data.get("error"),
            created_at=datetime.fromisoformat(job_data["created_at"]),
            updated_at=datetime.fromisoformat(job_data["updated_at"]),
            estimated_time_remaining=estimated_time_remaining
        )
