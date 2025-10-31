"""
API Routes for SynthAIx backend.
"""

from fastapi import APIRouter, HTTPException, BackgroundTask
from typing import Dict, Any
import json
from openai import OpenAI
from ..core.config import settings
from ..core.logging import get_logger
from ..models.schemas import (
    SchemaTranslateRequest,
    SchemaTranslateResponse,
    DataGenerateRequest,
    DataGenerateResponse,
    JobStatusResponse,
    DataSchema,
    JobStatus
)
from ..agents.orchestrator import OrchestratorAgent

logger = get_logger(__name__)
router = APIRouter()

# Global orchestrator instance
orchestrator = OrchestratorAgent()


@router.post("/schema/translate", response_model=SchemaTranslateResponse)
async def translate_schema(request: SchemaTranslateRequest) -> SchemaTranslateResponse:
    """
    Translate natural language prompt to structured JSON schema.
    Uses OpenAI's structured output mode to guarantee valid schema.
    
    Args:
        request: Schema translation request with natural language prompt
        
    Returns:
        Inferred schema with confidence score
    """
    logger.info(
        "Translating schema from prompt",
        extra={"extra_fields": {"prompt_length": len(request.prompt)}}
    )
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        system_prompt = """You are a data schema expert. Convert natural language descriptions into structured JSON schemas for synthetic data generation.

Return a JSON object with:
1. "fields": Array of field definitions with name, type, description, and constraints
2. "interpretation": Your understanding of the user's request
3. "confidence": Confidence score (0.0-1.0)

Supported field types: string, integer, float, boolean, date, datetime, email, phone, url, uuid

Example output:
{
  "fields": [
    {
      "name": "transaction_id",
      "type": "uuid",
      "description": "Unique transaction identifier"
    },
    {
      "name": "amount",
      "type": "float",
      "description": "Transaction amount in USD",
      "constraints": {"min": 0.01, "max": 10000.0}
    }
  ],
  "interpretation": "Financial transaction data with ID and amount",
  "confidence": 0.95
}"""
        
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a schema for: {request.prompt}"}
            ],
            temperature=0.3,  # Lower temperature for more consistent schemas
            response_format={"type": "json_object"}
        )
        
        # Parse response
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Validate and construct response
        schema = DataSchema(
            fields=result.get("fields", []),
            metadata=result.get("metadata", {})
        )
        
        return SchemaTranslateResponse(
            schema=schema,
            interpretation=result.get("interpretation", "Schema generated successfully"),
            confidence=result.get("confidence", 0.9)
        )
    
    except Exception as e:
        logger.error(f"Schema translation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to translate schema: {str(e)}"
        )


@router.post("/data/generate", response_model=DataGenerateResponse)
async def generate_data(request: DataGenerateRequest) -> DataGenerateResponse:
    """
    Start asynchronous synthetic data generation.
    Creates a job and returns job ID for status tracking.
    
    Args:
        request: Data generation request with schema and row count
        
    Returns:
        Job ID and initial status
    """
    logger.info(
        "Starting data generation",
        extra={"extra_fields": {
            "total_rows": request.total_rows,
            "num_fields": len(request.schema.fields)
        }}
    )
    
    try:
        # Start generation
        job_id = orchestrator.start_generation(
            schema=request.schema,
            total_rows=request.total_rows,
            chunk_size=request.chunk_size,
            enable_deduplication=request.enable_deduplication
        )
        
        return DataGenerateResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message=f"Job created successfully. Generating {request.total_rows} rows."
        )
    
    except Exception as e:
        logger.error(f"Failed to start generation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start data generation: {str(e)}"
        )


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get current status of a data generation job.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Complete job status with progress and metrics
    """
    logger.debug(f"Fetching status for job {job_id}")
    
    try:
        status = orchestrator.get_job_status(job_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        
        return status
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring.
    
    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get system metrics for monitoring.
    
    Returns:
        System-wide metrics
    """
    # This could be expanded to include Prometheus metrics
    return {
        "service": settings.APP_NAME,
        "max_workers": settings.MAX_WORKERS,
        "model": settings.OPENAI_MODEL
    }
