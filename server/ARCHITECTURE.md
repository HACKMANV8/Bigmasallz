# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User / LLM Client                       │
│                     (Natural Language Input)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ MCP Protocol
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Server                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  MCP Tools                                                 │ │
│  │  • extract_schema                                          │ │
│  │  • create_job                                              │ │
│  │  • generate_chunk                                          │ │
│  │  • get_job_progress                                        │ │
│  │  • control_job                                             │ │
│  │  • list_jobs                                               │ │
│  │  • merge_and_download                                      │ │
│  │  • validate_schema                                         │ │
│  └───────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Gemini     │ │     Job      │ │   Storage    │
    │   Client     │ │   Manager    │ │   Handler    │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
           │                │                │
           ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Gemini     │ │ Job State    │ │  Disk/       │
    │   API        │ │ Persistence  │ │  Memory/     │
    │              │ │              │ │  Cloud       │
    └──────────────┘ └──────────────┘ └──────────────┘
```

## Component Details

### 1. MCP Server (`src/mcp_server/`)

**Purpose**: Exposes tools via Model Context Protocol for LLM interaction

**Key Features**:
- 8 MCP tools for complete workflow
- Async request handling
- Error handling and validation
- JSON-based communication

**Tools**:
- `extract_schema`: NL → Structured schema
- `create_job`: Schema → Job specification
- `generate_chunk`: Job → Data chunk
- `get_job_progress`: Job monitoring
- `control_job`: Job lifecycle management
- `list_jobs`: Job discovery
- `merge_and_download`: Final dataset assembly
- `validate_schema`: Schema validation

### 2. Gemini Client (`src/api/`)

**Purpose**: Interface with Google Gemini API for LLM operations

**Key Features**:
- Retry logic with exponential backoff
- Rate limiting (requests & tokens per minute)
- Prompt templating for:
  - Schema extraction
  - Data generation
- JSON response parsing
- Error handling

**Methods**:
- `extract_schema()`: NL → Schema
- `generate_data_chunk()`: Schema → Data rows

### 3. Job Manager (`src/core/job_manager.py`)

**Purpose**: Manage job lifecycle and state

**Key Features**:
- Job creation and tracking
- State persistence (disk-based)
- Progress calculation
- Status management
- Job control (pause/resume/cancel)
- Cleanup of old jobs

**States**:
- PENDING → SCHEMA_VALIDATION → GENERATING → COMPLETED
- PAUSED (can resume)
- FAILED (can retry)
- CANCELLED (terminal)

### 4. Storage Handler (`src/storage/`)

**Purpose**: Manage chunk and dataset storage

**Implementations**:

**a) DiskStorageHandler** (default):
- Chunks stored in `temp/<job_id>/chunk_*.{csv,json,parquet}`
- Merged output in `output/<job_id>.{format}`
- Checksum validation
- Efficient file merging

**b) MemoryStorageHandler**:
- In-memory storage for small datasets
- Configurable max chunks limit
- Fast access, limited capacity

**c) CloudStorageHandler** (TODO):
- AWS S3 / GCS integration
- For large-scale deployments

### 5. Core Models (`src/core/models.py`)

**Purpose**: Type-safe data structures

**Key Models**:
- `DataSchema`: Field definitions, constraints, relationships
- `FieldDefinition`: Name, type, constraints, samples
- `JobSpecification`: Schema, row count, format, storage
- `JobState`: Spec + Progress + Chunks
- `JobProgress`: Status, completion %, timing
- `ChunkMetadata`: Location, size, checksum

### 6. Validators (`src/utils/validators.py`)

**Purpose**: Data validation

**Features**:
- Type-specific validation (string, int, float, email, etc.)
- Constraint checking (min/max, length, pattern, enum)
- Row validation
- Nullable handling

### 7. Configuration (`src/config.py`)

**Purpose**: Centralized configuration management

**Uses**:
- Pydantic Settings
- Environment variables
- Type-safe config objects
- Organized by concern (Gemini, MCP, Storage, etc.)

## Data Flow

### Schema Extraction Flow

```
User Input (NL)
    │
    ▼
extract_schema tool
    │
    ▼
Gemini Client
    │ (prompt engineering)
    ▼
Gemini API
    │ (LLM processing)
    ▼
Structured Schema JSON
    │ (parsing & validation)
    ▼
DataSchema object
    │
    ▼
User (for confirmation)
```

### Job Creation & Execution Flow

```
DataSchema + Parameters
    │
    ▼
create_job tool
    │
    ▼
Job Manager
    │ (create JobSpecification)
    ▼
JobState (PENDING)
    │ (persist to disk)
    ▼
Job ID returned
    │
    ▼
For each chunk:
    │
    ▼
generate_chunk tool
    │
    ▼
Gemini Client
    │ (generate data rows)
    ▼
Storage Handler
    │ (store chunk)
    ▼
Job Manager
    │ (update progress)
    ▼
ChunkMetadata
    │
    ▼
Progress update
    │
    ▼
[Repeat until complete]
    │
    ▼
merge_and_download tool
    │
    ▼
Storage Handler
    │ (merge all chunks)
    ▼
Final Dataset File
```

## Key Design Decisions

### 1. Chunked Generation
**Why**: 
- Avoid LLM token limits
- Enable progress tracking
- Support pause/resume
- Better error recovery

### 2. MCP Protocol
**Why**:
- Standard interface for LLMs
- Tool-based interaction
- Type-safe parameters
- Clear separation of concerns

### 3. Pydantic Models
**Why**:
- Type safety
- Validation
- JSON serialization
- Clear contracts

### 4. Job Persistence
**Why**:
- Survive server restarts
- Support long-running jobs
- Enable audit trails
- Facilitate debugging

### 5. Storage Abstraction
**Why**:
- Support multiple backends
- Easy to swap implementations
- Test with memory, deploy with disk/cloud

### 6. Rate Limiting
**Why**:
- Avoid API throttling
- Cost control
- Predictable behavior

## Scalability Considerations

### Current Design (Single Machine)
- Suitable for: 10K - 100K row datasets
- Bottleneck: Gemini API rate limits
- Storage: Disk-based

### Future Enhancements

**For larger datasets (1M+ rows)**:
1. Parallel chunk generation
2. Multiple API keys rotation
3. Cloud storage (S3/GCS)
4. Distributed job queue (Celery/Redis)
5. Database for job state (PostgreSQL)

**For production deployments**:
1. REST API wrapper around MCP server
2. Web UI for non-LLM users
3. Authentication & authorization
4. Monitoring & observability
5. Cost tracking per job

## Error Handling Strategy

1. **API Errors**: Retry with exponential backoff
2. **Validation Errors**: Clear messages to user
3. **Storage Errors**: Fail chunk, retry logic
4. **Job Failures**: Save state, enable retry
5. **System Errors**: Log, alert, graceful degradation

## Security Considerations

1. **API Keys**: Environment variables, never in code
2. **File Access**: Restricted to temp/output dirs
3. **Input Validation**: Schema validation, constraint checking
4. **Rate Limiting**: Prevent abuse
5. **Logging**: No sensitive data in logs

## Testing Strategy

1. **Unit Tests**: Core models, validators, utilities
2. **Integration Tests**: API client, storage handlers
3. **E2E Tests**: Full workflow simulation
4. **Mock Tests**: Gemini API responses
5. **Load Tests**: Large dataset generation

## Monitoring & Observability

Current:
- File-based logging
- Job state persistence
- Progress tracking

Future:
- Structured logging (JSON)
- Metrics (Prometheus)
- Tracing (OpenTelemetry)
- Dashboards (Grafana)
- Alerts (PagerDuty)

---

**Last Updated**: October 31, 2025
