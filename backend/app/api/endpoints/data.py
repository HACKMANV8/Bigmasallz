from fastapi import APIRouter, HTTPException, BackgroundTasks, status
import logging

from app.models.data import DataGenerationRequest, DataGenerationResponse
from app.services.orchestrator import OrchestratorService

logger = logging.getLogger(__name__)
router = APIRouter()
orchestrator = OrchestratorService()


@router.post(
    "/generate",
    response_model=DataGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate synthetic data",
    description="Initiates a parallel data generation job based on the provided schema.",
)
async def generate_data(
    request: DataGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate synthetic data using parallel worker agents.
    
    This endpoint creates a job and delegates data generation to parallel
    worker threads, each acting as a specialized Generator Agent.
    
    Args:
        request: Data generation request with schema and parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Job information with ID for status tracking
        
    Raises:
        HTTPException: If job creation fails
    """
    try:
        logger.info(
            f"Initiating data generation: {request.total_rows} rows, "
            f"chunk_size={request.chunk_size}, max_workers={request.max_workers}"
        )
        
        # Create job and start generation
        job = await orchestrator.create_generation_job(request)
        
        # Start generation in background
        background_tasks.add_task(
            orchestrator.execute_generation_job,
            job.job_id
        )
        
        logger.info(f"Job {job.job_id} created and started in background")
        
        return DataGenerationResponse(
            job_id=job.job_id,
            status=job.status.value,
            total_rows=job.total_rows,
            total_chunks=job.total_chunks,
            created_at=job.created_at.isoformat(),
        )
        
    except ValueError as e:
        logger.error(f"Validation error in data generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating generation job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create generation job: {str(e)}"
        )


@router.post(
    "/{job_id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel generation job",
    description="Attempts to cancel a running data generation job.",
)
async def cancel_generation(job_id: str):
    """
    Cancel a running data generation job.
    
    Args:
        job_id: Job ID to cancel
        
    Returns:
        Cancellation status
    """
    try:
        success = await orchestrator.cancel_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found or cannot be cancelled"
            )
        
        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancellation initiated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}"
        )
