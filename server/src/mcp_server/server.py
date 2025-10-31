"""MCP Server for Synthetic Data Generation.

This module implements the Model Context Protocol server with tools for:
- Schema extraction from natural language
- Job creation and management
- Chunked data generation
- Progress tracking
- Dataset download
"""

import asyncio
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from pydantic import AnyUrl

from src.core.models import (
    SchemaExtractionRequest,
    JobSpecification,
    JobStatus,
    OutputFormat,
    StorageType,
    ChunkGenerationRequest,
    ChunkGenerationResponse,
    JobControlRequest,
    DatasetDownloadInfo,
)
from src.core.job_manager import get_job_manager
from src.api.gemini_client import get_gemini_client
from src.storage.handlers import get_storage_handler
from src.utils.logger import get_logger
from src.config import settings

logger = get_logger(__name__)

# Initialize MCP server
app = Server(settings.mcp_server.name)

# Get singleton instances
job_manager = get_job_manager()
gemini_client = get_gemini_client()
storage_handler = get_storage_handler()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools."""
    return [
        Tool(
            name="extract_schema",
            description=(
                "Extract structured data schema from natural language description. "
                "Analyzes user requirements and generates a complete schema with field "
                "types, constraints, and sample values."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": "Natural language description of the dataset to generate"
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional additional context"
                    },
                    "example_data": {
                        "type": "string",
                        "description": "Optional example data to guide schema extraction"
                    }
                },
                "required": ["user_input"]
            }
        ),
        Tool(
            name="create_job",
            description=(
                "Create a new synthetic data generation job. Takes a validated schema "
                "and job parameters (row count, format, etc.) and creates a job that "
                "can be executed in chunks."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {
                        "type": "object",
                        "description": "Data schema (from extract_schema)"
                    },
                    "total_rows": {
                        "type": "integer",
                        "description": "Total number of rows to generate"
                    },
                    "chunk_size": {
                        "type": "integer",
                        "description": "Number of rows per chunk (default: 1000)"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["csv", "json", "parquet"],
                        "description": "Output file format"
                    },
                    "uniqueness_fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields that must have unique values"
                    },
                    "seed": {
                        "type": "integer",
                        "description": "Random seed for reproducibility"
                    }
                },
                "required": ["schema", "total_rows"]
            }
        ),
        Tool(
            name="generate_chunk",
            description=(
                "Generate a single chunk of synthetic data for a job. This is the core "
                "generation function that uses the LLM to create realistic data following "
                "the schema and constraints."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Job ID (UUID)"
                    },
                    "chunk_id": {
                        "type": "integer",
                        "description": "Chunk number to generate"
                    }
                },
                "required": ["job_id", "chunk_id"]
            }
        ),
        Tool(
            name="get_job_progress",
            description=(
                "Get current progress and status of a generation job. Returns detailed "
                "information about rows generated, chunks completed, status, and estimated "
                "completion time."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Job ID (UUID)"
                    }
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="control_job",
            description=(
                "Control job execution: pause, resume, cancel, or retry. Allows users "
                "to manage running jobs and handle failures."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Job ID (UUID)"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["pause", "resume", "cancel", "retry"],
                        "description": "Control action to perform"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional reason for the action"
                    }
                },
                "required": ["job_id", "action"]
            }
        ),
        Tool(
            name="list_jobs",
            description=(
                "List all generation jobs with optional status filtering. Useful for "
                "tracking multiple concurrent jobs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "schema_validation", "generating", "paused", "completed", "failed", "cancelled"],
                        "description": "Optional status filter"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of jobs to return (default: 100)"
                    }
                }
            }
        ),
        Tool(
            name="merge_and_download",
            description=(
                "Merge all completed chunks into a final dataset file and prepare for "
                "download. Returns download information including file path and checksum."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Job ID (UUID)"
                    }
                },
                "required": ["job_id"]
            }
        ),
        Tool(
            name="validate_schema",
            description=(
                "Validate a schema for correctness and feasibility. Checks for issues "
                "like invalid constraints, circular dependencies, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "schema": {
                        "type": "object",
                        "description": "Schema to validate"
                    }
                },
                "required": ["schema"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls."""
    try:
        if name == "extract_schema":
            return await handle_extract_schema(arguments)
        elif name == "create_job":
            return await handle_create_job(arguments)
        elif name == "generate_chunk":
            return await handle_generate_chunk(arguments)
        elif name == "get_job_progress":
            return await handle_get_job_progress(arguments)
        elif name == "control_job":
            return await handle_control_job(arguments)
        elif name == "list_jobs":
            return await handle_list_jobs(arguments)
        elif name == "merge_and_download":
            return await handle_merge_and_download(arguments)
        elif name == "validate_schema":
            return await handle_validate_schema(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_extract_schema(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle schema extraction from natural language."""
    logger.info("Extracting schema from user input")
    
    request = SchemaExtractionRequest(
        user_input=arguments["user_input"],
        context=arguments.get("context"),
        example_data=arguments.get("example_data")
    )
    
    # Use Gemini to extract schema
    response = gemini_client.extract_schema(request)
    
    # Format response
    result = {
        "schema": response.schema.model_dump(mode='json'),
        "confidence": response.confidence,
        "suggestions": response.suggestions,
        "warnings": response.warnings
    }
    
    import json
    return [TextContent(
        type="text",
        text=f"Schema extracted successfully:\n\n{json.dumps(result, indent=2)}"
    )]


async def handle_create_job(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle job creation."""
    logger.info("Creating new data generation job")
    
    from src.core.models import DataSchema, FieldDefinition, FieldConstraint, FieldType
    
    # Parse schema
    schema_data = arguments["schema"]
    fields = []
    for field_data in schema_data["fields"]:
        constraints = FieldConstraint(**field_data.get("constraints", {}))
        field = FieldDefinition(
            name=field_data["name"],
            type=FieldType(field_data["type"]),
            description=field_data.get("description"),
            constraints=constraints,
            sample_values=field_data.get("sample_values", []),
            depends_on=field_data.get("depends_on"),
            generation_hint=field_data.get("generation_hint")
        )
        fields.append(field)
    
    schema = DataSchema(
        fields=fields,
        description=schema_data.get("description"),
        relationships=schema_data.get("relationships"),
        metadata=schema_data.get("metadata", {})
    )
    
    # Create job specification
    spec = JobSpecification(
        schema=schema,
        total_rows=arguments["total_rows"],
        chunk_size=arguments.get("chunk_size", settings.generation.default_chunk_size),
        output_format=OutputFormat(arguments.get("output_format", "csv")),
        storage_type=StorageType(settings.storage.type),
        uniqueness_fields=arguments.get("uniqueness_fields", []),
        seed=arguments.get("seed")
    )
    
    # Create job
    job_state = job_manager.create_job(spec)
    job_manager.validate_schema(job_state.specification.job_id)
    
    import json
    result = {
        "job_id": str(job_state.specification.job_id),
        "total_rows": spec.total_rows,
        "chunk_size": spec.chunk_size,
        "total_chunks": job_state.progress.total_chunks,
        "status": job_state.progress.status.value,
        "message": "Job created successfully. Use generate_chunk to start generating data."
    }
    
    return [TextContent(
        type="text",
        text=f"Job created:\n\n{json.dumps(result, indent=2)}"
    )]


async def handle_generate_chunk(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle chunk generation."""
    job_id = UUID(arguments["job_id"])
    chunk_id = arguments["chunk_id"]
    
    logger.info(f"Generating chunk {chunk_id} for job {job_id}")
    
    # Get job
    job = job_manager.get_job(job_id)
    if not job:
        return [TextContent(type="text", text=f"Job {job_id} not found")]
    
    # Update status if this is the first chunk
    if job.progress.status == JobStatus.PENDING:
        job_manager.update_job_status(job_id, JobStatus.GENERATING)
    
    # Calculate rows for this chunk
    remaining_rows = job.specification.total_rows - job.progress.rows_generated
    chunk_rows = min(job.specification.chunk_size, remaining_rows)
    
    # Collect existing values for uniqueness
    existing_values = {}
    if job.specification.uniqueness_fields:
        for field_name in job.specification.uniqueness_fields:
            existing_values[field_name] = []
            # TODO: Collect existing values from previous chunks
    
    try:
        # Generate data using Gemini
        data = gemini_client.generate_data_chunk(
            schema=job.specification.schema,
            num_rows=chunk_rows,
            existing_values=existing_values if existing_values else None,
            seed=job.specification.seed
        )
        
        # Store chunk
        metadata = storage_handler.store_chunk(
            job_id=job_id,
            chunk_id=chunk_id,
            data=data,
            format=job.specification.output_format
        )
        
        # Update job progress
        job_manager.add_chunk(job_id, metadata)
        
        # Check if job is complete
        if job.progress.chunks_completed >= job.progress.total_chunks:
            job_manager.update_job_status(job_id, JobStatus.COMPLETED)
        
        import json
        result = {
            "chunk_id": chunk_id,
            "rows_generated": len(data),
            "job_progress": {
                "chunks_completed": job.progress.chunks_completed,
                "total_chunks": job.progress.total_chunks,
                "rows_generated": job.progress.rows_generated,
                "total_rows": job.specification.total_rows,
                "progress_percentage": job.progress.progress_percentage,
                "status": job.progress.status.value
            }
        }
        
        return [TextContent(
            type="text",
            text=f"Chunk generated:\n\n{json.dumps(result, indent=2)}"
        )]
        
    except Exception as e:
        logger.error(f"Error generating chunk: {e}")
        job_manager.update_job_status(job_id, JobStatus.FAILED, str(e))
        return [TextContent(type="text", text=f"Error generating chunk: {str(e)}")]


async def handle_get_job_progress(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle job progress query."""
    job_id = UUID(arguments["job_id"])
    
    job = job_manager.get_job(job_id)
    if not job:
        return [TextContent(type="text", text=f"Job {job_id} not found")]
    
    import json
    result = {
        "job_id": str(job_id),
        "status": job.progress.status.value,
        "rows_generated": job.progress.rows_generated,
        "total_rows": job.specification.total_rows,
        "chunks_completed": job.progress.chunks_completed,
        "total_chunks": job.progress.total_chunks,
        "progress_percentage": job.progress.progress_percentage,
        "started_at": str(job.progress.started_at) if job.progress.started_at else None,
        "completed_at": str(job.progress.completed_at) if job.progress.completed_at else None,
        "error_message": job.progress.error_message
    }
    
    return [TextContent(
        type="text",
        text=f"Job progress:\n\n{json.dumps(result, indent=2)}"
    )]


async def handle_control_job(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle job control actions."""
    job_id = UUID(arguments["job_id"])
    action = arguments["action"]
    reason = arguments.get("reason")
    
    request = JobControlRequest(
        job_id=job_id,
        action=action,
        reason=reason
    )
    
    success = job_manager.control_job(request)
    
    if success:
        return [TextContent(
            type="text",
            text=f"Job {job_id} {action} successful"
        )]
    else:
        return [TextContent(
            type="text",
            text=f"Failed to {action} job {job_id}"
        )]


async def handle_list_jobs(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle job listing."""
    status_str = arguments.get("status")
    status = JobStatus(status_str) if status_str else None
    limit = arguments.get("limit", 100)
    
    jobs = job_manager.list_jobs(status=status, limit=limit)
    
    import json
    result = {
        "total": len(jobs),
        "jobs": [
            {
                "job_id": str(job.specification.job_id),
                "status": job.progress.status.value,
                "total_rows": job.specification.total_rows,
                "rows_generated": job.progress.rows_generated,
                "progress_percentage": job.progress.progress_percentage,
                "created_at": str(job.specification.created_at)
            }
            for job in jobs
        ]
    }
    
    return [TextContent(
        type="text",
        text=f"Jobs:\n\n{json.dumps(result, indent=2)}"
    )]


async def handle_merge_and_download(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle dataset merging and download preparation."""
    job_id = UUID(arguments["job_id"])
    
    job = job_manager.get_job(job_id)
    if not job:
        return [TextContent(type="text", text=f"Job {job_id} not found")]
    
    if job.progress.status != JobStatus.COMPLETED:
        return [TextContent(
            type="text",
            text=f"Job {job_id} is not completed yet (status: {job.progress.status.value})"
        )]
    
    # Merge chunks
    output_path = settings.storage.output_path / f"{job_id}.{job.specification.output_format.value}"
    merged_path = storage_handler.merge_chunks(
        job_id=job_id,
        chunks=job.chunks,
        output_path=output_path,
        format=job.specification.output_format
    )
    
    # Calculate file size and checksum
    import hashlib
    file_size = merged_path.stat().st_size
    
    with open(merged_path, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    
    import json
    result = {
        "job_id": str(job_id),
        "file_path": str(merged_path),
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "format": job.specification.output_format.value,
        "total_rows": job.progress.rows_generated,
        "checksum": checksum,
        "message": f"Dataset ready for download at: {merged_path}"
    }
    
    return [TextContent(
        type="text",
        text=f"Dataset merged:\n\n{json.dumps(result, indent=2)}"
    )]


async def handle_validate_schema(arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle schema validation."""
    from src.core.models import DataSchema, FieldDefinition, FieldConstraint, FieldType
    
    schema_data = arguments["schema"]
    
    # Parse schema
    fields = []
    for field_data in schema_data["fields"]:
        constraints = FieldConstraint(**field_data.get("constraints", {}))
        field = FieldDefinition(
            name=field_data["name"],
            type=FieldType(field_data["type"]),
            description=field_data.get("description"),
            constraints=constraints,
            sample_values=field_data.get("sample_values", []),
            depends_on=field_data.get("depends_on"),
            generation_hint=field_data.get("generation_hint")
        )
        fields.append(field)
    
    schema = DataSchema(
        fields=fields,
        description=schema_data.get("description"),
        relationships=schema_data.get("relationships"),
        metadata=schema_data.get("metadata", {})
    )
    
    # Validate
    issues = schema.validate_constraints()
    
    import json
    if issues:
        result = {
            "valid": False,
            "issues": issues
        }
    else:
        result = {
            "valid": True,
            "message": "Schema is valid",
            "field_count": len(schema.fields)
        }
    
    return [TextContent(
        type="text",
        text=f"Schema validation:\n\n{json.dumps(result, indent=2)}"
    )]


def main():
    """Run the MCP server."""
    import mcp
    logger.info(f"Starting MCP server: {settings.mcp_server.name}")
    mcp.server.stdio.stdio_server()(app)


if __name__ == "__main__":
    main()
