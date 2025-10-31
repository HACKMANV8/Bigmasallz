"""FastAPI server for Synthetic Data Generation Tool."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api_server.routers import health, schema, jobs
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Synthetic Data Generator API",
        description="HTTP API for generating synthetic datasets using LLMs",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Next.js dev server
            "http://localhost:3001",  # Next.js alternative port
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(schema.router, prefix="/schema", tags=["schema"])
    app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup."""
        logger.info("Starting Synthetic Data Generator API server")
        # Initialize any startup tasks here
        
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        logger.info("Shutting down Synthetic Data Generator API server")
        # Cleanup tasks here
    
    return app

# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api_server.app:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )