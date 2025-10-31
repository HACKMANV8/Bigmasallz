"""Health check endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.gemini_client import get_gemini_client
from src.storage.handlers import get_storage_handler
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    checks: dict = {}


@router.get("/live", response_model=HealthResponse)
async def liveness_check():
    """Simple liveness probe."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness probe with dependency checks."""
    checks = {}
    overall_status = "ok"
    
    try:
        # Check Gemini API connectivity
        gemini_client = get_gemini_client()
        # You might want to add a simple test call here
        checks["gemini"] = "reachable"
    except Exception as e:
        logger.error(f"Gemini check failed: {e}")
        checks["gemini"] = "failed"
        overall_status = "degraded"
    
    try:
        # Check storage handler
        storage_handler = get_storage_handler()
        checks["storage"] = "ready"
    except Exception as e:
        logger.error(f"Storage check failed: {e}")
        checks["storage"] = "failed"
        overall_status = "degraded"
    
    if overall_status == "degraded":
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return HealthResponse(status=overall_status, checks=checks)