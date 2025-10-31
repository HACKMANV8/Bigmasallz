import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import asyncio

from app.models.data import (
    DataGenerationRequest,
    GeneratedDataChunk,
    GeneratedDataResult,
)
from app.models.job import Job
from app.services.job_service import JobService
from app.agents.generator_agent import GeneratorAgent
from app.tools.deduplication import DeduplicationTool
from app.core.config import settings

logger = logging.getLogger(__name__)


class OrchestratorService:
    """
    Orchestrator service for managing parallel data generation.

    This is the core "brain" that coordinates worker agents and manages
    the parallel chunking strategy.
    """

    def __init__(self):
        self.job_service = JobService()
        self.dedup_tool = DeduplicationTool()
        self._active_jobs: Dict[str, bool] = {}

    async def create_generation_job(
        self, request: DataGenerationRequest
    ) -> Job:
        """
        Create a new data generation job.

        Args:
            request: Data generation request

        Returns:
            Created job
        """
        # Calculate chunk size and workers
        chunk_size = request.chunk_size or settings.DEFAULT_CHUNK_SIZE
        chunk_size = max(
            settings.MIN_CHUNK_SIZE, min(chunk_size, settings.MAX_CHUNK_SIZE)
        )

        max_workers = request.max_workers or settings.MAX_WORKERS
        max_workers = min(max_workers, settings.MAX_WORKERS)

        # Calculate total chunks
        total_chunks = (request.total_rows + chunk_size - 1) // chunk_size

        logger.info(
            f"Creating job: {request.total_rows} rows, "
            f"chunk_size={chunk_size}, "
            f"total_chunks={total_chunks}, "
            f"max_workers={max_workers}"
        )

        # Create job
        job = await self.job_service.create_job(
            total_rows=request.total_rows, total_chunks=total_chunks
        )

        # Store job configuration
        self._active_jobs[job.job_id] = {
            "request": request,
            "chunk_size": chunk_size,
            "max_workers": max_workers,
            "cancelled": False,
        }

        return job

    async def execute_generation_job(self, job_id: str):
        """
        Execute a data generation job with parallel workers.

        This method runs the actual parallel chunking strategy.

        Args:
            job_id: Job ID to execute
        """
        try:
            job_config = self._active_jobs.get(job_id)
            if not job_config:
                logger.error(f"Job {job_id} not found in active jobs")
                return

            request: DataGenerationRequest = job_config["request"]
            chunk_size = job_config["chunk_size"]
            max_workers = job_config["max_workers"]

            logger.info(f"Starting job {job_id} with {max_workers} workers")

            # Initialize deduplication for this job
            collection_name = f"{settings.CHROMADB_COLLECTION_PREFIX}{job_id}"
            await self.dedup_tool.initialize_collection(collection_name)

            # Generate chunk tasks
            chunks_to_generate = []
            remaining_rows = request.total_rows

            chunk_id = 0
            while remaining_rows > 0:
                current_chunk_size = min(chunk_size, remaining_rows)
                chunks_to_generate.append((chunk_id, current_chunk_size))
                remaining_rows -= current_chunk_size
                chunk_id += 1

            # Execute chunks in parallel using ThreadPoolExecutor
            all_data = []
            total_deduplicated = 0

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all chunk tasks
                future_to_chunk = {
                    executor.submit(
                        self._generate_chunk_sync,
                        job_id,
                        chunk_id,
                        chunk_size,
                        request,
                        collection_name,
                    ): chunk_id
                    for chunk_id, chunk_size in chunks_to_generate
                }

                # Process completed chunks
                for future in as_completed(future_to_chunk):
                    chunk_id = future_to_chunk[future]

                    # Check if job was cancelled
                    if job_config.get("cancelled"):
                        logger.info(f"Job {job_id} was cancelled")
                        await self.job_service.mark_job_failed(
                            job_id, "Job cancelled by user"
                        )
                        return

                    try:
                        chunk_result: GeneratedDataChunk = future.result()
                        all_data.extend(chunk_result.rows)
                        total_deduplicated += chunk_result.deduplicated_count

                        # Update job progress
                        await self.job_service.increment_completed_chunks(
                            job_id,
                            rows_added=chunk_result.row_count,
                            deduplicated=chunk_result.deduplicated_count,
                        )

                        logger.info(
                            f"Job {job_id}: Chunk {chunk_id} completed "
                            f"({chunk_result.row_count} rows, "
                            f"{chunk_result.deduplicated_count} deduplicated)"
                        )

                    except Exception as e:
                        logger.error(
                            f"Chunk {chunk_id} failed: {str(e)}", exc_info=True
                        )
                        # Continue with other chunks

            # Store final results
            result = GeneratedDataResult(
                job_id=job_id,
                data=all_data,
                total_rows=len(all_data),
                unique_rows=len(all_data),
                deduplicated_count=total_deduplicated,
                download_url=f"/api/jobs/{job_id}/download",
            )

            await self.job_service.set_job_results(job_id, result)

            logger.info(
                f"Job {job_id} completed: {len(all_data)} rows generated, "
                f"{total_deduplicated} deduplicated"
            )

        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
            await self.job_service.mark_job_failed(job_id, str(e))

        finally:
            # Cleanup
            if job_id in self._active_jobs:
                del self._active_jobs[job_id]

    def _generate_chunk_sync(
        self,
        job_id: str,
        chunk_id: int,
        chunk_size: int,
        request: DataGenerationRequest,
        collection_name: str,
    ) -> GeneratedDataChunk:
        """
        Synchronous wrapper for chunk generation (runs in thread).

        Args:
            job_id: Job ID
            chunk_id: Chunk ID
            chunk_size: Number of rows in chunk
            request: Generation request
            collection_name: Deduplication collection name

        Returns:
            Generated chunk
        """
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(
                self._generate_chunk(
                    job_id, chunk_id, chunk_size, request, collection_name
                )
            )
        finally:
            loop.close()

    async def _generate_chunk(
        self,
        job_id: str,
        chunk_id: int,
        chunk_size: int,
        request: DataGenerationRequest,
        collection_name: str,
    ) -> GeneratedDataChunk:
        """
        Generate a single chunk of data.

        Args:
            job_id: Job ID
            chunk_id: Chunk ID
            chunk_size: Number of rows to generate
            request: Generation request
            collection_name: Deduplication collection name

        Returns:
            Generated chunk with data
        """
        # Create generator agent
        agent = GeneratorAgent(
            schema=request.schema,
            dedup_tool=self.dedup_tool,
            collection_name=collection_name,
            dedup_threshold=request.deduplication_threshold
            or settings.DEDUPLICATION_THRESHOLD,
        )

        # Generate data
        rows = await agent.generate_data(chunk_size)

        return GeneratedDataChunk(
            chunk_id=chunk_id,
            rows=rows,
            row_count=len(rows),
            deduplicated_count=agent.deduplicated_count,
        )

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled, False if not found
        """
        if job_id in self._active_jobs:
            self._active_jobs[job_id]["cancelled"] = True
            logger.info(f"Job {job_id} cancellation requested")
            return True
        return False
