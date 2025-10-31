# MCP Architecture Guide

This document explains how the Model Context Protocol (MCP) server inside the synthetic dataset generator is organized, how tools are exposed, and how clients (LLM agents or other MCP-compatible runtimes) should interact with it.

## Overview

```
Client (LLM / MCP runtime)
    │
    ├── mcp.connect() over stdio/JSON-RPC
    │
    ├── list_tools() ──> discover available operations
    │
    ├── call_tool("extract_schema", ...)
    ├── call_tool("create_job", ...)
    ├── call_tool("generate_chunk", ...)
    └── ... other tool invocations ...

Synthetic Dataset Generator MCP Server (src/mcp_server/server.py)
    ├── JobManager singleton (job lifecycle & persistence)
    ├── GeminiClient singleton (schema + data generation)
    └── StorageHandler (chunk persistence & merging)
```

- Transport: JSON-RPC over stdio (default). Alternative transports (e.g., sockets) can be configured by the host MCP runtime.
- Protocol: Conforms to the [Model Context Protocol](https://modelcontextprotocol.io/).
- Tool count: 8 fully implemented tools covering schema extraction, validation, job creation, chunk generation, progress tracking, control, listing, and dataset download.

## Bootstrapping the Server

- Entry point: `python main.py server`
- Internally, `main.py` imports `src.mcp_server.server.main`, which composes the MCP `Server` instance and starts the stdio loop via `mcp.server.stdio.stdio_server()(app)`.
- Configuration and logging are initialized during module import (`src/utils/logger.py`, `src/config.py`).

## Tool Inventory

Each tool surfaced by `list_tools()` maps directly to a handler function.

| Tool Name | Handler | Purpose |
|-----------|---------|---------|
| `extract_schema` | `handle_extract_schema` | Convert natural-language prompt into structured schema.
| `create_job` | `handle_create_job` | Persist a job specification (schema + generation parameters).
| `generate_chunk` | `handle_generate_chunk` | Generate and store a data chunk using Gemini.
| `get_job_progress` | `handle_get_job_progress` | Retrieve live job progress and status.
| `control_job` | `handle_control_job` | Pause/resume/cancel/retry job execution.
| `list_jobs` | `handle_list_jobs` | Enumerate jobs with optional status filter.
| `merge_and_download` | `handle_merge_and_download` | Merge chunks and prepare final dataset.
| `validate_schema` | `handle_validate_schema` | Validate schema constraints before job creation.

### Tool Request/Response Flow

1. **Discovery**
   - Client calls `list_tools()` to enumerate available tool names, descriptions, and JSON Schemas describing the expected input payload for each tool.

2. **Validation**
   - MCP layer enforces the JSON Schema before delivering the payload to the handler.
   - Handlers deserialize payloads into Pydantic models (`SchemaExtractionRequest`, `JobSpecification`, etc.) to prevent malformed data from reaching core logic.

3. **Execution**
   - Handlers invoke domain services:
     - `GeminiClient` for LLM operations
     - `JobManager` for persistence and state transitions
     - `StorageHandler` for chunk I/O
   - Most handlers are synchronous but run inside the async MCP loop. Long-running operations (e.g., chunk generation) are still sequential; future async tasks can be introduced if we parallelize generation.

4. **Response Formatting**
   - Handler returns rich JSON text (`TextContent`) describing results. Downstream clients can parse the JSON portions to extract structured data.
   - Errors propagate as string messages; job status updates to `FAILED` with error details.

## Internal Components & Interactions

### Job Manager (`src/core/job_manager.py`)
- Maintains an in-memory dictionary of `JobState` objects keyed by UUID.
- Persists each job state to `temp/jobs/<job_id>.json` for crash recovery.
- Coordinates job status transitions and progress updates when chunks complete or when control actions occur.

### Gemini Client (`src/api/gemini_client.py`)
- Wraps Google Gemini API (via `google-generativeai`).
- Enforces rate limits (requests and tokens per minute) and retries with exponential backoff (Tenacity).
- Generates prompts for schema extraction and chunked data generation.
- Parses JSON responses into in-house models.

### Storage Handlers (`src/storage/handlers.py`)
- `DiskStorageHandler` (default) writes chunk files under `temp/<job_id>` and merges them into `output/<job_id>.<format>`.
- `MemoryStorageHandler` available for lightweight usage/testing.
- Future: `CloudStorageHandler` placeholder for S3/GCS support.

### Configuration & Logging
- Settings loaded via `src/config.py` (`pydantic-settings`) from environment variables.
- Logging set up via `src/utils/logger.py` with console + file handlers.

## Typical MCP Workflow

1. **Schema Extraction**
   - Client sends natural-language dataset description to `extract_schema`.
   - Gemini returns schema with fields, constraints, sample values, suggestions.

2. **Job Creation**
   - Client optionally validates schema via `validate_schema`.
   - Client calls `create_job` with schema + parameters (row count, chunk size, format, uniqueness fields).
   - Job Manager persists job state, returns job ID.

3. **Chunk Generation Loop**
   - Client iterates `chunk_id` values: call `generate_chunk` for each.
   - Handler triggers Gemini, stores chunk, updates progress, completes job once all chunks are generated.
   - Client polls `get_job_progress` or `list_jobs` to monitor status.

4. **Control Actions**
   - Client can call `control_job` to pause/resume/cancel/retry.
   - Job Manager records status changes and persists them.

5. **Dataset Assembly**
   - After job completion, client calls `merge_and_download`.
   - Storage handler merges chunks and returns dataset metadata (path, checksum, size). Client can fetch the file from disk or, in future, via HTTP endpoint.

## Sequence Diagram (Conceptual)

```
Client                     MCP Server             Job Manager        Storage     Gemini
  |                            |                       |               |           |
  | list_tools()               |                       |               |           |
  |--------------------------->|                       |               |           |
  |<---------------------------|                       |               |           |
  | call_tool(extract_schema)  |                       |               |           |
  |--------------------------->| handle_extract_schema |               |           |
  |                            |---------------------->|               |           |
  |                            |    prompt             |               |           |
  |                            |--------------------------------------->|           |
  |                            |                            data <-----|           |
  |                            |<-----------------------------------------------   |
  |<---------------------------|                                                |   |
  | call_tool(create_job)      |                                                |   |
  |--------------------------->| handle_create_job                              |   |
  |                            |---------------------->| create state           |   |
  |                            |<----------------------| persist                |   |
  |<---------------------------|                                                |   |
  | call_tool(generate_chunk)  |                                                |   |
  |--------------------------->| handle_generate_chunk                          |   |
  |                            |---------------------->| job lookup             |   |
  |                            |                                                |   |
  |                            |--------------------------------------->| prompt |   |
  |                            |<---------------------------------------| data   |   |
  |                            |---------------------->| add_chunk               |   |
  |                            |---------------------->| persist job             |   |
  |                            |---------------------->| store chunk ------------->| file
  |<---------------------------|                                                |   |
  | ... repeat ...             |                                                |   |
```

## Error Handling

- **LLM errors**: Retries attempted automatically; after final failure, job status becomes `FAILED` with the error message.
- **Validation errors**: Responses include descriptive strings; schema validation issues returned as arrays.
- **Storage errors**: Chunk operations log and propagate exceptions; job marked failed when storage write fails.

## Extensibility Points

- Add new MCP tools by registering additional handlers in `src/mcp_server/server.py`.
- Introduce background task management or concurrency features by extending `JobManager`.
- Swap storage backends via `get_storage_handler()` factory, controlled by environment config.
- Replace Gemini or support multiple models by augmenting `GeminiClient` with strategy pattern.

## Tips for MCP Client Authors

- Always begin with `list_tools()` to confirm capabilities.
- Validate JSON responses (the server often embeds JSON inside text content).
- Queue chunk generation sequentially; the current system does not deduplicate identical chunk requests.
- For long-running jobs, poll `get_job_progress` or call `list_jobs` with filters.
- Handle error strings gracefully and surface them to users.

## References

- Implementation: `src/mcp_server/server.py`
- Models: `src/core/models.py`
- Job management: `src/core/job_manager.py`
- Gemini integration: `src/api/gemini_client.py`
- Storage: `src/storage/handlers.py`
- Utilities: `src/utils/logger.py`, `src/utils/validators.py`

Keep this document updated as new tools or architectural changes are introduced.
