# FastAPI Endpoint Plan for Synthetic Dataset Generator

## Purpose

Document the roadmap for exposing the existing MCP-based synthetic data generation workflow through a FastAPI HTTP interface. This plan lets us parallelize API implementation while preserving the current MCP integration.

## Guiding Principles

- **Parity with MCP tools**: Each REST endpoint should map cleanly to the existing MCP toolset (`extract_schema`, `create_job`, etc.).
- **Stateless HTTP surface**: Keep request/response contracts self-contained so clients outside the MCP ecosystem can interact without session state.
- **Reuse domain models**: Leverage `src/core/models.py` Pydantic models to avoid divergence.
- **Async-first**: Implement asynchronous FastAPI handlers to align with existing async MCP patterns and long-running operations.
- **Observability & safety**: Provide structured logging, error surfaces, and request validation.

## Proposed Architecture

```
FastAPI app (new)
├── Routers
│   ├── /schema         → schema_router.py
│   ├── /jobs           → jobs_router.py
│   ├── /chunks         → chunks_router.py
│   ├── /storage        → storage_router.py (optional, pending features)
│   └── /health         → health_router.py
├── Dependencies
│   ├── JobManager dependency injection (singleton)
│   ├── GeminiClient dependency injection (singleton)
│   └── StorageHandler factory (from config)
└── Shared
    ├── Response models (FastAPI-facing)
    ├── Error handlers & middleware
    └── Background tasks for long-running jobs
```

- Create new module `src/api_server/` to isolate FastAPI code.
- Mirror MCP tool functionality inside dedicated router modules.
- Reuse existing settings and logging utilities.
- Provide container entrypoint `uvicorn.run("src.api_server.app:app", host=..., port=...)`.

## Endpoint Inventory (Draft)

| Endpoint | Method | Purpose | Request Model | Response Model |
|----------|--------|---------|---------------|----------------|
| `/health/live` | GET | Liveness probe | – | `{ status: "ok" }` |
| `/health/ready` | GET | Readiness probe incl. Gemini key validation | – | `{ status: "ok", checks: {...} }` |
| `/schema/extract` | POST | Run natural-language schema extraction | `SchemaExtractionRequest` | `SchemaExtractionResponse` |
| `/schema/validate` | POST | Validate schema constraints before job creation | `DataSchema` | `{ valid: bool, issues?: list[str] }` |
| `/jobs` | POST | Create generation job | `JobSpecificationInput` (schema + job params) | `JobStateSummary` |
| `/jobs` | GET | List jobs (optional status filter, pagination) | Query params (`status`, `limit`, `offset`) | `JobsListResponse` |
| `/jobs/{job_id}` | GET | Retrieve current job state & progress | – | `JobStateDetail` |
| `/jobs/{job_id}/control` | POST | Pause/resume/cancel/retry job | `JobControlRequest` | `{ success: bool, status: JobStatus }` |
| `/jobs/{job_id}/chunks/{chunk_id}` | POST | Trigger chunk generation | `ChunkGenerationPayload` (optional overrides) | `ChunkGenerationResponse` |
| `/jobs/{job_id}/chunks/{chunk_id}` | GET | Fetch stored chunk data (preview / JSON only initially) | Query `format` | `ChunkPreviewResponse` |
| `/jobs/{job_id}/download` | POST | Merge & prepare dataset, optionally start background task | `{ format?, force_remerge? }` | `DatasetDownloadInfo` |
| `/jobs/{job_id}/download` | GET | Stream merged dataset file | Query `format` | File response |
| `/jobs/{job_id}/events` | GET (SSE/WebSocket) | Real-time progress updates (stretch goal) | – | Event stream |

### Supporting Models

Create FastAPI-specific request/response schemas that wrap or alias existing core models where needed:

- `JobSpecificationInput`: Accepts schema dict, chunk size, output format, uniqueness fields, seed.
- `JobStateSummary`, `JobStateDetail`: Present sanitized job state, including progress stats.
- `ChunkGenerationPayload`: Allows optional override of chunk size or uniqueness field hints per request.
- `ErrorResponse`: Standard error contract.

## Implementation Phases

1. **Scaffolding & Bootstrap**
   - [ ] Add `src/api_server/` package with `app.py` (FastAPI instance) and router placeholders.
   - [ ] Configure logging & settings reuse.
   - [ ] Provide CLI entrypoint (`python main.py api-server`) or dedicated script.

2. **Core Endpoints (MVP)**
   - [ ] `/health/*`
   - [ ] `/schema/extract`, `/schema/validate`
   - [ ] `/jobs` POST + GET list
   - [ ] `/jobs/{job_id}` GET

3. **Job Operations**
   - [ ] `/jobs/{job_id}/control`
   - [ ] `/jobs/{job_id}/chunks/{chunk_id}` POST
   - [ ] Persisted chunk preview GET (optional)

4. **Dataset Delivery**
   - [ ] `/jobs/{job_id}/download` POST (merge)
   - [ ] `/jobs/{job_id}/download` GET (file streaming)
   - [ ] Background task and status tracking for large merges

5. **Enhancements (Future)**
   - [ ] Event streaming via Server-Sent Events or WebSockets
   - [ ] Authentication & rate limiting (FastAPI dependencies)
   - [ ] Multi-tenant job ownership
   - [ ] Pagination and filtering improvements
   - [ ] Cloud storage signed URLs when storage type is `cloud`

## Open Questions / Decisions Needed

1. **Authentication**: Do we need API keys or OAuth for the MVP, or is this internal-only?
2. **Chunk Preview**: Should chunk preview be limited to JSON? Add CSV sample streaming?
3. **Concurrency Control**: Do we rely solely on `JobManager` limits or introduce FastAPI background tasks with queueing?
4. **Error Surfaces**: Should we mirror MCP error messages or craft HTTP-specific ones?
5. **Client Compatibility**: Will downstream clients expect long polling, SSE, or WebSockets for updates?

## Next Steps for Parallel Workstreams

- **API Team**: Use this plan to scaffold the FastAPI surface and create router skeletons.
- **Core Team**: Ensure `JobManager`, storage handlers, and Gemini client expose any hooks needed for HTTP usage (e.g., chunk previews, cancellation checks).
- **DevOps**: Prepare deployment target (containerization, environment variables, reverse proxy config). Consider running MCP server and FastAPI app side by side.

## References

- Current MCP server implementation: `src/mcp_server/server.py`
- Domain models and job logic: `src/core/models.py`, `src/core/job_manager.py`
- Storage handling: `src/storage/handlers.py`
- Configuration & logging: `src/config.py`, `src/utils/logger.py`

---

This document will evolve as we lock in requirements and start implementing the FastAPI endpoints. Updates should include finalized request/response schemas, sample payloads, and dependency diagrams once scaffolding begins.
