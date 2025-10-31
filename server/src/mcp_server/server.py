"""MCP Server for Synthetic Data Generation.

This module implements the Model Context Protocol server with tools for:
- Schema extraction from natural language
- Job creation and management
- Chunked data generation
- Progress tracking
- Dataset download
"""

from typing import Any
from uuid import UUID

from mcp.server import Server
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

from src.config import settings
from src.core.models import (
    JobControlRequest,
    JobStatus,
)
from src.services.generation_service import get_generation_service
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize MCP server
app = Server(settings.mcp_server.name)

# Shared generation service
generation_service = get_generation_service()


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
                    "storage_type": {
                        "type": "string",
                        "enum": ["disk", "memory", "cloud"],
                        "description": "Optional storage backend override"
                    },
                    "uniqueness_fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields that must have unique values"
                    },
                    "seed": {
                        "type": "integer",
                        "description": "Random seed for reproducibility"
                    },
                    "name": {
                        "type": "string",
                        "description": "Optional human-friendly job name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description for the job"
                    },
                    "created_by": {
                        "type": "string",
                        "description": "Identifier for the user or agent creating the job"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata to persist with the job"
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


async def handle_extract_schema(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle schema extraction from natural language."""
    logger.info("Extracting schema from user input")

    response = generation_service.extract_schema_from_prompt(
        user_input=arguments["user_input"],
        context=arguments.get("context"),
        example_data=arguments.get("example_data"),
    )

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


async def handle_create_job(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle job creation."""
    logger.info("Creating new data generation job")

    job_state = generation_service.create_generation_job(
        schema=arguments["schema"],
        total_rows=arguments["total_rows"],
        chunk_size=arguments.get("chunk_size"),
        output_format=arguments.get("output_format"),
        uniqueness_fields=arguments.get("uniqueness_fields"),
        seed=arguments.get("seed"),
        name=arguments.get("name"),
        description=arguments.get("description"),
        created_by=arguments.get("created_by"),
        metadata=arguments.get("metadata"),
        storage_type=arguments.get("storage_type"),
    )

    import json
    result = {
        "job_id": str(job_state.specification.job_id),
        "total_rows": job_state.specification.total_rows,
        "chunk_size": job_state.specification.chunk_size,
        "total_chunks": job_state.progress.total_chunks,
        "status": job_state.progress.status.value,
        "output_format": job_state.specification.output_format.value,
        "storage_type": job_state.specification.storage_type.value,
        "message": "Job created successfully. Use generate_chunk to start generating data."
    }

    return [TextContent(
        type="text",
        text=f"Job created:\n\n{json.dumps(result, indent=2)}"
    )]


async def handle_generate_chunk(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle chunk generation."""
    job_id = UUID(arguments["job_id"])
    chunk_id = arguments["chunk_id"]

    logger.info(f"Generating chunk {chunk_id} for job {job_id}")
    try:
        response = generation_service.generate_chunk(job_id=job_id, chunk_id=chunk_id)
        job = generation_service.get_job(job_id)
        if not job:
            raise RuntimeError(f"Job {job_id} missing after chunk generation")

        import json
        result = {
            "chunk_id": chunk_id,
            "rows_generated": response.rows_generated,
            "issues": response.issues,
            "chunk_metadata": response.metadata.model_dump(mode="json"),
            "job_progress": {
                "chunks_completed": job.progress.chunks_completed,
                "total_chunks": job.progress.total_chunks,
                "rows_generated": job.progress.rows_generated,
                "total_rows": job.specification.total_rows,
                "progress_percentage": job.progress.progress_percentage,
                "status": job.progress.status.value,
            },
        }

        return [TextContent(
            type="text",
            text=f"Chunk generated:\n\n{json.dumps(result, indent=2)}"
        )]

    except Exception as e:
        logger.error(f"Error generating chunk: {e}")
        return [TextContent(type="text", text=f"Error generating chunk: {str(e)}")]


async def handle_get_job_progress(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle job progress query."""
    job_id = UUID(arguments["job_id"])

    job = generation_service.get_job(job_id)
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


async def handle_control_job(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle job control actions."""
    job_id = UUID(arguments["job_id"])
    action = arguments["action"]
    reason = arguments.get("reason")

    request = JobControlRequest(
        job_id=job_id,
        action=action,
        reason=reason
    )

    success = generation_service.control_job(request)

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


async def handle_list_jobs(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle job listing."""
    status_str = arguments.get("status")
    status = JobStatus(status_str) if status_str else None
    limit = arguments.get("limit", 100)

    jobs = generation_service.list_jobs(status=status, limit=limit)

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


async def handle_merge_and_download(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle dataset merging and download preparation."""
    job_id = UUID(arguments["job_id"])

    try:
        download_info = generation_service.merge_job_dataset(job_id)
    except ValueError as exc:
        return [TextContent(type="text", text=str(exc))]

    import json
    result = {
        "job_id": str(download_info.job_id),
        "file_path": download_info.file_path,
        "file_size_bytes": download_info.file_size_bytes,
        "file_size_mb": round(download_info.file_size_bytes / (1024 * 1024), 2)
        if download_info.file_size_bytes is not None
        else None,
        "format": download_info.format.value,
        "total_rows": download_info.total_rows,
        "checksum": download_info.checksum,
        "download_url": download_info.download_url,
        "message": f"Dataset ready for download at: {download_info.file_path}",
    }

    return [TextContent(
        type="text",
        text=f"Dataset merged:\n\n{json.dumps(result, indent=2)}"
    )]


async def handle_validate_schema(arguments: dict[str, Any]) -> list[TextContent]:
    """Handle schema validation."""
    issues = generation_service.validate_schema(arguments["schema"])

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
            "field_count": len(arguments["schema"].get("fields", []))
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
