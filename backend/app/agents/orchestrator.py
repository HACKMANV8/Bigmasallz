"""
Orchestrator Agent - Manages parallel data generation with worker agents.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from ..core.config import settings
from ..core.logging import get_logger
from ..models.schemas import DataSchema, JobStatus
from ..agents.generator_mcp import MCPGeneratorAgent
from ..utils.job_manager import JobManager

logger = get_logger(__name__)


class OrchestratorAgent:
    """
    Orchestrator agent that manages parallel data generation.
    Delegates chunks to worker agents using ThreadPoolExecutor.
    """
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.job_manager = JobManager()
        self.executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
        logger.info(f"Orchestrator initialized with {settings.MAX_WORKERS} workers")
    
    def calculate_chunk_size(self, total_rows: int, requested_chunk_size: int = None) -> int:
        """
        Calculate optimal chunk size based on total rows and configuration.
        
        Args:
            total_rows: Total rows to generate
            requested_chunk_size: User-requested chunk size (optional)
            
        Returns:
            Optimal chunk size
        """
        if requested_chunk_size:
            chunk_size = max(
                settings.MIN_CHUNK_SIZE,
                min(requested_chunk_size, settings.MAX_CHUNK_SIZE)
            )
        else:
            # Auto-calculate based on total rows
            if total_rows <= 1000:
                chunk_size = 100
            elif total_rows <= 10000:
                chunk_size = 500
            else:
                chunk_size = 1000
            
            chunk_size = min(chunk_size, settings.MAX_CHUNK_SIZE)
        
        return chunk_size
    
    async def generate_data_async(
        self,
        job_id: str,
        schema: DataSchema,
        total_rows: int,
        chunk_size: int,
        enable_deduplication: bool = True
    ) -> None:
        """
        Asynchronously generate data using parallel worker agents.
        
        Args:
            job_id: Unique job identifier
            schema: Data schema to generate
            total_rows: Total rows to generate
            chunk_size: Rows per chunk
            enable_deduplication: Enable duplicate detection
        """
        logger.info(
            f"Starting data generation for job {job_id}",
            extra={"extra_fields": {
                "job_id": job_id,
                "total_rows": total_rows,
                "chunk_size": chunk_size
            }}
        )
        
        # Update job status
        self.job_manager.update_job_status(job_id, JobStatus.IN_PROGRESS)
        
        try:
            # Calculate number of chunks
            num_chunks = (total_rows + chunk_size - 1) // chunk_size
            
            # Create worker agents (using MCP + GitHub Copilot!)
            agents = [
                MCPGeneratorAgent(
                    agent_id=i,
                    schema=schema,
                    enable_deduplication=enable_deduplication
                )
                for i in range(min(num_chunks, settings.MAX_WORKERS))
            ]
            
            # Submit tasks to executor
            futures = []
            for chunk_id in range(num_chunks):
                # Calculate rows for this chunk
                rows_in_chunk = min(chunk_size, total_rows - (chunk_id * chunk_size))
                
                # Select agent (round-robin)
                agent = agents[chunk_id % len(agents)]
                
                # Submit task
                future = self.executor.submit(
                    agent.generate_chunk,
                    chunk_id,
                    rows_in_chunk
                )
                futures.append((future, chunk_id))
                
                logger.debug(f"Submitted chunk {chunk_id} to agent {agent.agent_id}")
            
            # Process completed chunks
            for future, chunk_id in futures:
                try:
                    # Wait for chunk completion
                    chunk_result = future.result(timeout=300)  # 5 minute timeout per chunk
                    
                    # Update job with chunk result
                    self.job_manager.update_chunk(job_id, chunk_id, chunk_result)
                    
                except Exception as e:
                    logger.error(
                        f"Chunk {chunk_id} failed: {str(e)}",
                        extra={"extra_fields": {"job_id": job_id, "chunk_id": chunk_id}},
                        exc_info=True
                    )
                    
                    # Update job with failure
                    self.job_manager.update_chunk(job_id, chunk_id, {
                        "chunk_id": chunk_id,
                        "status": "failed",
                        "rows_generated": 0,
                        "duplicates_removed": 0,
                        "error": str(e)
                    })
            
            # Aggregate metrics from all agents
            total_metrics = {
                "tokens_used": sum(agent.tokens_used for agent in agents),
                "api_calls": sum(agent.api_calls for agent in agents),
                "avg_response_time": (
                    sum(agent.total_response_time for agent in agents) / 
                    sum(agent.api_calls for agent in agents)
                    if sum(agent.api_calls for agent in agents) > 0
                    else 0.0
                ),
                "total_duplicates_removed": sum(agent.duplicates_removed for agent in agents)
            }
            
            # Finalize job
            self.job_manager.finalize_job(job_id, total_metrics)
            
            logger.info(
                f"Completed data generation for job {job_id}",
                extra={"extra_fields": {"job_id": job_id, "metrics": total_metrics}}
            )
        
        except Exception as e:
            logger.error(
                f"Fatal error in job {job_id}: {str(e)}",
                extra={"extra_fields": {"job_id": job_id}},
                exc_info=True
            )
            
            # Mark job as failed
            job_data = self.job_manager.get_job(job_id)
            if job_data:
                job_data["error"] = str(e)
                self.job_manager.update_job_status(job_id, JobStatus.FAILED)
    
    def start_generation(
        self,
        schema: DataSchema,
        total_rows: int,
        chunk_size: int = None,
        enable_deduplication: bool = True
    ) -> str:
        """
        Start async data generation and return job ID.
        
        Args:
            schema: Data schema to generate
            total_rows: Total rows to generate
            chunk_size: Rows per chunk (optional)
            enable_deduplication: Enable duplicate detection
            
        Returns:
            Job ID
        """
        # Calculate chunk size
        chunk_size = self.calculate_chunk_size(total_rows, chunk_size)
        
        # Create job
        job_id = self.job_manager.create_job(
            schema=schema.model_dump(),
            total_rows=total_rows,
            chunk_size=chunk_size
        )
        
        # Start generation in background
        asyncio.create_task(
            self.generate_data_async(
                job_id=job_id,
                schema=schema,
                total_rows=total_rows,
                chunk_size=chunk_size,
                enable_deduplication=enable_deduplication
            )
        )
        
        return job_id
    
    def get_job_status(self, job_id: str):
        """
        Get job status.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobStatusResponse or None
        """
        return self.job_manager.get_job_status_response(job_id)
    
    def shutdown(self):
        """Shutdown the orchestrator and cleanup resources."""
        logger.info("Shutting down orchestrator")
        self.executor.shutdown(wait=True)
