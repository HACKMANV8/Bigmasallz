# Frontend ↔ Server API Reference (Planned)

This document consolidates the HTTP endpoints that the frontend will use to interact with the synthetic dataset generator. The routes align with the FastAPI plan documented in `README_ENDPOINTS.md`. Use this as the contract while we build the frontend and implement the API layer in parallel.

> **Status**: Endpoints are in the design phase. Payloads and responses below represent the intended interface.

## Base URL

- Local development: `http://localhost:8080`
- Staging/Production: TBD (add environment-specific URLs once provisioned)

## Authentication

- MVP assumes internal/trusted usage (no auth). Add headers section once auth scheme is finalized.

## Endpoint Summary

| Method | Path | Purpose |
|--------|------|---------|
| GET    | `/health/live` | Liveness probe (simple status)
| GET    | `/health/ready` | Readiness probe (Gemini + storage checks)
| POST   | `/schema/extract` | Convert natural-language request to structured schema
| POST   | `/schema/validate` | Validate schema object before job creation
| POST   | `/jobs` | Create a synthetic data generation job
| GET    | `/jobs` | List jobs (filterable by status)
| GET    | `/jobs/{job_id}` | Retrieve job details and progress
| POST   | `/jobs/{job_id}/control` | Pause, resume, cancel, or retry job
| POST   | `/jobs/{job_id}/chunks/{chunk_id}` | Trigger generation of a specific chunk
| GET    | `/jobs/{job_id}/chunks/{chunk_id}` | Preview stored chunk data (JSON sample)
| POST   | `/jobs/{job_id}/download` | Merge chunks and prepare final dataset
| GET    | `/jobs/{job_id}/download` | Download merged dataset file
| GET    | `/jobs/{job_id}/events` | (Planned) Real-time updates via SSE/WebSocket

## Detailed Contracts

### 1. Health Checks

#### `GET /health/live`
- **Purpose**: Quick container liveness check.
- **Response**: `{ "status": "ok" }`

#### `GET /health/ready`
- **Purpose**: Startup readiness indicator.
- **Response**:
  ```json
  {
    "status": "ok",
    "checks": {
      "gemini": "reachable",
      "storage": "ready",
      "job_manager": "ready"
    }
  }
  ```

### 2. Schema Operations

#### `POST /schema/extract`
- **Request**:
  ```json
  {
    "user_input": "Generate 5,000 ecommerce transactions with customer, product, amount (10-500), and purchase_date",
    "context": {},
    "example_data": null
  }
  ```
- **Response**: `SchemaExtractionResponse` (fields, constraints, suggestions, warnings).

#### `POST /schema/validate`
- **Request**: Schema object as returned by `extract_schema`.
- **Response**:
  ```json
  {
    "valid": true,
    "issues": []
  }
  ```

### 3. Job Lifecycle

#### `POST /jobs`
- **Request**:
  ```json
  {
    "schema": { ... },
    "total_rows": 10000,
    "chunk_size": 1000,
    "output_format": "csv",
    "uniqueness_fields": ["order_id"],
    "seed": 42
  }
  ```
- **Response**:
  ```json
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "total_rows": 10000,
    "chunk_size": 1000,
    "total_chunks": 10
  }
  ```

#### `GET /jobs`
- **Query Params**: `status` (optional), `limit` (default 20), `offset` (default 0)
- **Response**: List of job summaries with pagination info.

#### `GET /jobs/{job_id}`
- **Response**: Detailed job state including progress percentage, timestamps, error (if any).

#### `POST /jobs/{job_id}/control`
- **Request**:
  ```json
  {
    "action": "pause",
    "reason": "User requested pause"
  }
  ```
- **Response**: `{ "success": true, "status": "paused" }`

### 4. Chunk Operations

#### `POST /jobs/{job_id}/chunks/{chunk_id}`
- **Purpose**: Generate a specific chunk.
- **Response**:
  ```json
  {
    "chunk_id": 3,
    "rows_generated": 1000,
    "job_progress": {
      "chunks_completed": 4,
      "total_chunks": 10,
      "rows_generated": 4000,
      "progress_percentage": 40.0,
      "status": "generating"
    }
  }
  ```

#### `GET /jobs/{job_id}/chunks/{chunk_id}`
- **Purpose**: Return JSON preview (first N rows) for UI display.

### 5. Dataset Delivery

#### `POST /jobs/{job_id}/download`
- **Request**:
  ```json
  {
    "format": "csv",
    "force_remerge": false
  }
  ```
- **Response**: `DatasetDownloadInfo` containing file metadata and checksum.

#### `GET /jobs/{job_id}/download`
- **Response**: File stream (`Content-Disposition: attachment`). Frontend should handle download prompts.

### 6. Real-Time Updates (Planned)

#### `GET /jobs/{job_id}/events`
- Server-Sent Events or WebSocket channel to push progress updates. Implementation TBD.

## Frontend Integration Notes

- **State Management**: Maintain job IDs client-side after creation. Poll `/jobs/{job_id}` or subscribe to `/events` for updates.
- **Error Handling**: Surface `error_message` from job detail responses when `status` is `failed`.
- **Chunk Preview**: Use chunk preview to drive data samples, but inform users that final dataset comes from the download endpoint.
- **Retry Logic**: On chunk generation errors, invoke `/jobs/{job_id}/control` with `"retry"`.
- **File Downloads**: For browsers, initiate a standard fetch + blob save or use the `<a download>` pattern.

## Example Flow for Frontend

1. **Schema Step**
   - POST `/schema/extract`
   - Allow user edits, then POST `/schema/validate`
2. **Job Setup**
   - POST `/jobs`
   - Store returned `job_id`
3. **Generation**
   - Loop chunk IDs or trigger background generation (future)
   - Poll `/jobs/{job_id}` for status updates
4. **Completion**
   - POST `/jobs/{job_id}/download`
   - GET `/jobs/{job_id}/download` to fetch file

## TODOs / Open Questions

- Authentication and rate limiting strategy
- Background job orchestration to auto-run all chunks after job creation
- SSE/WebSocket implementation details
- Pagination contracts for `/jobs` (limit/offset vs cursor)
- Chunk preview limits (row count, payload size)

Update this document as the FastAPI implementation solidifies and the frontend consumes the new endpoints.
