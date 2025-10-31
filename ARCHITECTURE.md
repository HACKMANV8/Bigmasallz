# 📊 SynthAIx System Architecture Diagrams

## 1. High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│                         👤 USER INTERFACE                            │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              Streamlit Frontend (Port 8501)                 │    │
│  │                                                              │    │
│  │  📝 Step 1: Natural Language Input                          │    │
│  │  ✅ Step 2: Schema Confirmation (Human-in-the-Loop)         │    │
│  │  📊 Step 3: Live Progress Tracking                          │    │
│  │  💾 Step 4: Results & Download                              │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ⬇ HTTP REST                             │
└───────────────────────────────────────────────────────────────────────┘
                                 ⬇
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│                      🔧 BACKEND ORCHESTRATION                        │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │             FastAPI Backend (Port 8000)                     │    │
│  │                                                              │    │
│  │  /api/v1/schema/translate  ← OpenAI structured output      │    │
│  │  /api/v1/data/generate     ← Job creation                  │    │
│  │  /api/v1/jobs/{id}/status  ← Status polling                │    │
│  │                                                              │    │
│  │  ┌──────────────────────────────────────────────────┐      │    │
│  │  │         Orchestrator Agent                        │      │    │
│  │  │  • Splits jobs into chunks                        │      │    │
│  │  │  • Manages ThreadPoolExecutor (20 workers)        │      │    │
│  │  │  • Aggregates results                             │      │    │
│  │  │  • Tracks metrics                                 │      │    │
│  │  └──────────────────────────────────────────────────┘      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ⬇                                       │
└───────────────────────────────────────────────────────────────────────┘
                                 ⬇
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│                    🤖 PARALLEL WORKER AGENTS                         │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       ┌──────────┐      │
│  │ Agent #1 │  │ Agent #2 │  │ Agent #3 │  ...  │ Agent #20│      │
│  │ -------- │  │ -------- │  │ -------- │       │ -------- │      │
│  │ Gen 500  │  │ Gen 500  │  │ Gen 500  │       │ Gen 500  │      │
│  │ rows     │  │ rows     │  │ rows     │       │ rows     │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘       └────┬─────┘      │
│       │             │             │                    │             │
│       └─────────────┴─────────────┴────────────────────┘            │
│                              ⬇                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │           🔍 Deduplication Tool (ChromaDB)                  │    │
│  │  • Generate embeddings                                      │    │
│  │  • Query for similar vectors                                │    │
│  │  • Filter duplicates (threshold: 0.85)                      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
                                 ⬇
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│                     💾 DATA PERSISTENCE                              │
│                                                                       │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │     Redis      │  │    ChromaDB      │  │   OpenAI API     │   │
│  │  (Job State)   │  │  (Vector Store)  │  │  (Generation)    │   │
│  │                │  │                  │  │                  │   │
│  │ • Job status   │  │ • Embeddings     │  │ • gpt-4o-mini    │   │
│  │ • Progress     │  │ • Similarity     │  │ • Structured     │   │
│  │ • Chunks       │  │ • Dedup check    │  │   output         │   │
│  └────────────────┘  └──────────────────┘  └──────────────────┘   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## 2. Data Flow Sequence

```
User
  │
  │ 1. Enter prompt: "Generate financial transactions..."
  ▼
Streamlit Frontend
  │
  │ POST /schema/translate
  ▼
FastAPI Backend
  │
  │ OpenAI API call
  ▼
OpenAI GPT-4o-mini
  │
  │ Returns structured JSON schema
  ▼
FastAPI Backend
  │
  │ Schema response
  ▼
Streamlit Frontend
  │
  │ 2. User confirms schema (Human-in-the-Loop)
  │
  │ POST /data/generate
  ▼
FastAPI Backend
  │
  │ Create job, calculate chunks
  ▼
Orchestrator Agent
  │
  │ Split into 20 chunks
  ├────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
  ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼
Gen  Gen  Gen  Gen  Gen  Gen  Gen  Gen  Gen  Gen  Gen  (Parallel)
#1   #2   #3   #4   #5   #6   #7   #8   #9   #10  ...
  │    │    │    │    │    │    │    │    │    │    │
  │    │    │    │    │    │    │    │    │    │    │
  └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
                    │
                    ▼
          Deduplication Tool
                    │
                    │ Check ChromaDB for duplicates
                    ▼
              ChromaDB
                    │
                    │ Return unique rows only
                    ▼
            Orchestrator Agent
                    │
                    │ Aggregate all chunks
                    ▼
              Job Manager
                    │
                    │ Save to Redis
                    ▼
                  Redis
                    │
                    │ 3. Frontend polls: GET /jobs/{id}/status
                    ▼
          Streamlit Frontend
                    │
                    │ Display progress bar, metrics
                    │
                    │ 4. Job completes
                    ▼
                  User
                    │
                    │ Download CSV/JSON/Excel
                    ▼
                 💾 Local file
```

## 3. Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Components                           │
│                                                                   │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │   Input    │→ │ Confirmation │→ │    Progress Tracker     │  │
│  │   Screen   │  │    Screen    │  │  • Progress bar         │  │
│  │            │  │  • Edit JSON │  │  • Chunk visualization  │  │
│  │  Prompt    │  │  • Params    │  │  • Agent metrics        │  │
│  └────────────┘  └──────────────┘  └────────────────────────┘  │
│         │              │                      │                  │
│         └──────────────┴──────────────────────┘                 │
│                        │                                         │
│                 api_client.py                                    │
└────────────────────────┼────────────────────────────────────────┘
                         │ HTTP
┌────────────────────────┼────────────────────────────────────────┐
│                        ▼                                         │
│                   routes.py                                      │
│                        │                                         │
│     ┌──────────────────┼──────────────────┐                    │
│     │                  │                   │                    │
│     ▼                  ▼                   ▼                    │
│  translate()      generate()         get_status()               │
│     │                  │                   │                    │
│     │                  ▼                   │                    │
│     │          orchestrator.py             │                    │
│     │                  │                   │                    │
│     │          ┌───────┴────────┐          │                    │
│     │          ▼                ▼          │                    │
│     │   generator.py    job_manager.py    │                    │
│     │          │                │          │                    │
│     │          ▼                ▼          ▼                    │
│     │   deduplication.py     Redis       Redis                 │
│     │          │                                                │
│     │          ▼                                                │
│     │      ChromaDB                                             │
│     │                                                           │
│     ▼                                                           │
│  OpenAI                                                         │
│                    Backend Components                           │
└─────────────────────────────────────────────────────────────────┘
```

## 4. Request/Response Flow

```
Schema Translation:
─────────────────

Request:  {"prompt": "Generate financial transactions..."}
   ↓
OpenAI:   Structured output mode, JSON schema
   ↓
Response: {
            "schema": {"fields": [...]},
            "interpretation": "...",
            "confidence": 0.95
          }


Data Generation:
───────────────

Request:  {
            "schema": {...},
            "total_rows": 10000,
            "chunk_size": 500,
            "enable_deduplication": true
          }
   ↓
Backend:  Create job → Split into 20 chunks
   ↓
Response: {
            "job_id": "550e8400-...",
            "status": "pending",
            "message": "Job created successfully..."
          }


Status Polling:
──────────────

Request:  GET /jobs/{job_id}/status
   ↓
Backend:  Query Redis for job state
   ↓
Response: {
            "job_id": "550e8400-...",
            "status": "in_progress",
            "progress_percentage": 45.0,
            "completed_rows": 4500,
            "chunks": [
              {"chunk_id": 0, "status": "completed", ...},
              {"chunk_id": 1, "status": "in_progress", ...}
            ],
            "metrics": {
              "tokens_used": 45000,
              "api_calls": 9,
              "avg_response_time": 2.3,
              "deduplication_rate": 0.08
            },
            "estimated_time_remaining": 45.2
          }
```

## 5. Parallel Execution Timeline

```
Time →
─────────────────────────────────────────────────────────────────

Chunk 0:  ██████████████████ ✓ (500 rows, 2.5s)
Chunk 1:  ██████████████████ ✓ (500 rows, 2.3s)
Chunk 2:  ██████████████████ ✓ (500 rows, 2.7s)
Chunk 3:  ██████████████████ ✓ (500 rows, 2.4s)
Chunk 4:  ██████████████████ ✓ (500 rows, 2.6s)
...
Chunk 19: ██████████████████ ✓ (500 rows, 2.5s)

Total time: ~3 seconds (parallel)
vs. ~50 seconds (sequential)

Speedup: 16.7x faster! ⚡
```

## 6. Deduplication Process

```
Generated Data
      ↓
┌─────────────────────────────────┐
│   New Row: {id: 1, amount: 100} │
└─────────────────────────────────┘
      ↓
┌─────────────────────────────────┐
│  1. Generate embedding vector    │
│     [0.123, -0.456, 0.789, ...] │
└─────────────────────────────────┘
      ↓
┌─────────────────────────────────┐
│  2. Query ChromaDB              │
│     Find top 5 similar vectors   │
└─────────────────────────────────┘
      ↓
┌─────────────────────────────────┐
│  3. Calculate similarities      │
│     Row A: 0.92 (duplicate!)    │
│     Row B: 0.73 (unique)        │
│     Row C: 0.68 (unique)        │
└─────────────────────────────────┘
      ↓
┌─────────────────────────────────┐
│  4. Filter if similarity > 0.85 │
│     → This row is duplicate     │
│     → Discard                   │
└─────────────────────────────────┘
```

## 7. Technology Stack Layers

```
┌─────────────────────────────────────────────────┐
│               Presentation Layer                 │
│                  (Streamlit)                     │
│  • User Interface                                │
│  • Real-time visualizations                      │
│  • Progress tracking                             │
└─────────────────────────────────────────────────┘
                      ↕
┌─────────────────────────────────────────────────┐
│                API Gateway Layer                 │
│                   (FastAPI)                      │
│  • RESTful endpoints                             │
│  • Request validation                            │
│  • Error handling                                │
└─────────────────────────────────────────────────┘
                      ↕
┌─────────────────────────────────────────────────┐
│              Business Logic Layer                │
│          (Orchestrator & Generators)             │
│  • Job management                                │
│  • Parallel processing                           │
│  • Metrics collection                            │
└─────────────────────────────────────────────────┘
                      ↕
┌─────────────────────────────────────────────────┐
│               Data Access Layer                  │
│         (Redis, ChromaDB, OpenAI)                │
│  • State persistence                             │
│  • Vector storage                                │
│  • AI generation                                 │
└─────────────────────────────────────────────────┘
```

---

**These diagrams provide a visual understanding of SynthAIx's architecture and data flow.**
