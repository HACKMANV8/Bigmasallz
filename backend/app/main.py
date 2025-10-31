from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.endpoints import schema, data, jobs

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting SynthAIx API server")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Max workers: {settings.MAX_WORKERS}")
    yield
    # Shutdown
    logger.info("Shutting down SynthAIx API server")


# Create FastAPI application
app = FastAPI(
    title="SynthAIx API",
    description="Scalable Synthetic Data Generator with AI-powered orchestration",
    version="1.0.0",
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "synthaix-api",
        "version": "1.0.0",
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "SynthAIx API",
        "version": "1.0.0",
        "description": "Scalable Synthetic Data Generator",
        "endpoints": {
            "schema_translation": "/api/schema/translate",
            "data_generation": "/api/data/generate",
            "job_status": "/api/jobs/{job_id}/status",
            "documentation": "/docs",
        },
    }


# Include routers
app.include_router(schema.router, prefix="/api/schema", tags=["Schema"])
app.include_router(data.router, prefix="/api/data", tags=["Data Generation"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.AUTO_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
