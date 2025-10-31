from fastapi import APIRouter, HTTPException, status, Response
from fastapi.responses import StreamingResponse
import logging
import io
import csv
import json

from app.models.job import JobStatusResponse
from app.services.job_service import JobService

logger = logging.getLogger(__name__)
router = APIRouter()
job_service = JobService()


@router.get(
    "/{job_id}/status",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get job status",
    description="Retrieves the current status and progress of a data generation job.",
)
async def get_job_status(job_id: str):
    """
    Get status and progress of a data generation job.
    
    This endpoint is polled by the frontend to track job progress in real-time.
    
    Args:
        job_id: Job ID to query
        
    Returns:
        Job status with progress information
        
    Raises:
        HTTPException: If job not found
    """
    try:
        logger.debug(f"Fetching status for job {job_id}")
        
        job_status = await job_service.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch job status: {str(e)}"
        )


@router.get(
    "/{job_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download generated data",
    description="Downloads the generated data in CSV or JSON format.",
)
async def download_job_results(
    job_id: str,
    format: str = "csv"
):
    """
    Download generated data results.
    
    Args:
        job_id: Job ID to download
        format: Output format (csv or json)
        
    Returns:
        Generated data file
    """
    try:
        job = await job_service.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        if job.status.value != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is not completed yet. Current status: {job.status.value}"
            )
        
        if not job.results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No results available for this job"
            )
        
        data = job.results.get("data", [])
        
        if format.lower() == "csv":
            return await _generate_csv_response(data, job_id)
        elif format.lower() == "json":
            return await _generate_json_response(data, job_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format}. Use 'csv' or 'json'"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading job results: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download results: {str(e)}"
        )


async def _generate_csv_response(data: list, job_id: str):
    """Generate CSV response."""
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data to download"
        )
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    
    # Create streaming response
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=synthaix_{job_id}.csv"
        }
    )


async def _generate_json_response(data: list, job_id: str):
    """Generate JSON response."""
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data to download"
        )
    
    json_str = json.dumps(data, indent=2)
    
    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=synthaix_{job_id}.json"
        }
    )


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="List all jobs",
    description="Lists all data generation jobs with their current status.",
)
async def list_jobs(
    limit: int = 100,
    offset: int = 0,
    status_filter: str = None
):
    """
    List all jobs with optional filtering.
    
    Args:
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        status_filter: Filter by job status
        
    Returns:
        List of jobs
    """
    try:
        jobs = await job_service.list_jobs(
            limit=limit,
            offset=offset,
            status_filter=status_filter
        )
        
        return {
            "jobs": jobs,
            "total": len(jobs),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )
