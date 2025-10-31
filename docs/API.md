# API Reference - SynthAIx

## Overview

SynthAIx provides a RESTful API for scalable synthetic data generation with AI orchestration.

**Base URL:** `http://localhost:8000/api/v1`

**Content Type:** `application/json`

---

## Authentication

Currently, the API does not require authentication. In production, implement:
- API keys via headers
- OAuth2 with JWT tokens
- Rate limiting per client

---

## Error Handling

All errors return consistent JSON format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Request body validation failed |
| 500 | Internal Server Error |

---

## Endpoints

### 1. Translate Schema

Convert natural language prompt to structured JSON schema.

**Endpoint:** `POST /schema/translate`

**Request Body:**

```json
{
  "prompt": "string"  // Natural language description
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/schema/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate customer records with name, email, phone, and registration date"
  }'
```

**Response:** `200 OK`

```json
{
  "schema": {
    "fields": [
      {
        "name": "customer_name",
        "type": "string",
        "description": "Customer full name",
        "constraints": {}
      },
      {
        "name": "email",
        "type": "email",
        "description": "Customer email address",
        "constraints": {}
      },
      {
        "name": "phone",
        "type": "phone",
        "description": "Customer phone number",
        "constraints": {}
      },
      {
        "name": "registration_date",
        "type": "date",
        "description": "Date of registration",
        "constraints": {}
      }
    ],
    "metadata": {}
  },
  "interpretation": "Customer registration data with contact information",
  "confidence": 0.92
}
```

**Field Types:**

- `string` - Text data
- `integer` - Whole numbers
- `float` - Decimal numbers
- `boolean` - True/False
- `date` - Date (YYYY-MM-DD)
- `datetime` - Timestamp
- `email` - Email address
- `phone` - Phone number
- `url` - URL
- `uuid` - UUID v4

---

### 2. Generate Data

Start asynchronous synthetic data generation job.

**Endpoint:** `POST /data/generate`

**Request Body:**

```json
{
  "schema": {
    "fields": [
      {
        "name": "string",
        "type": "string",
        "description": "string (optional)",
        "constraints": {} // optional
      }
    ],
    "metadata": {} // optional
  },
  "total_rows": 10000,        // Required: 1-1000000
  "chunk_size": 500,          // Optional: 10-1000
  "enable_deduplication": true // Optional: default true
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/data/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "schema": {
      "fields": [
        {"name": "id", "type": "uuid"},
        {"name": "amount", "type": "float", "constraints": {"min": 0, "max": 10000}}
      ]
    },
    "total_rows": 10000,
    "enable_deduplication": true
  }'
```

**Response:** `200 OK`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Job created successfully. Generating 10000 rows."
}
```

**Parameters:**

- `total_rows`: Total number of rows to generate (1-1,000,000)
- `chunk_size`: Rows per parallel chunk (10-1000). Auto-calculated if omitted.
- `enable_deduplication`: Use vector-based duplicate detection

---

### 3. Get Job Status

Retrieve current status of a data generation job.

**Endpoint:** `GET /jobs/{job_id}/status`

**Path Parameters:**

- `job_id` (string): Unique job identifier from generate response

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/status"
```

**Response:** `200 OK`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "in_progress",
  "total_rows": 10000,
  "completed_rows": 3500,
  "progress_percentage": 35.0,
  "chunks": [
    {
      "chunk_id": 0,
      "status": "completed",
      "rows_generated": 500,
      "duplicates_removed": 12,
      "error": null
    },
    {
      "chunk_id": 1,
      "status": "in_progress",
      "rows_generated": 0,
      "duplicates_removed": 0,
      "error": null
    }
  ],
  "metrics": {
    "tokens_used": 45000,
    "api_calls": 7,
    "avg_response_time": 2.3,
    "deduplication_rate": 0.08,
    "total_duplicates_removed": 280
  },
  "data": null,
  "error": null,
  "created_at": "2025-10-31T12:00:00.000Z",
  "updated_at": "2025-10-31T12:02:15.000Z",
  "estimated_time_remaining": 45.2
}
```

**Status Values:**

- `pending`: Job created, not started
- `in_progress`: Currently generating
- `completed`: Successfully completed
- `failed`: Generation failed
- `cancelled`: Job was cancelled

**When Completed:**

```json
{
  "status": "completed",
  "data": [
    {"id": "uuid-here", "amount": 123.45},
    {"id": "uuid-here", "amount": 678.90}
  ],
  ...
}
```

---

### 4. Health Check

Service health status for monitoring.

**Endpoint:** `GET /health`

**Example Request:**

```bash
curl "http://localhost:8000/api/v1/health"
```

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "service": "SynthAIx",
  "version": "1.0.0"
}
```

---

### 5. Metrics

System-wide metrics for monitoring.

**Endpoint:** `GET /metrics`

**Response:** `200 OK`

```json
{
  "service": "SynthAIx",
  "max_workers": 20,
  "model": "gpt-4o-mini"
}
```

---

## Polling Best Practices

For job status tracking:

1. **Initial Wait**: Wait 2-3 seconds before first poll
2. **Poll Interval**: Check every 2-5 seconds
3. **Exponential Backoff**: Increase interval for long jobs
4. **Timeout**: Set reasonable timeout (e.g., 5 minutes for 10k rows)

**Example Python:**

```python
import time
import requests

def wait_for_job(job_id, max_wait=300):
    url = f"http://localhost:8000/api/v1/jobs/{job_id}/status"
    start = time.time()
    
    while time.time() - start < max_wait:
        response = requests.get(url)
        status = response.json()
        
        if status["status"] in ["completed", "failed"]:
            return status
        
        time.sleep(2)  # Poll every 2 seconds
    
    raise TimeoutError("Job did not complete in time")
```

---

## Rate Limits

**Default Limits:**
- 100 requests per minute per IP
- 10 concurrent generation jobs per IP

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1635724800
```

---

## Examples

### Complete Flow Example

```python
import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

# 1. Translate schema from prompt
schema_response = requests.post(
    f"{BASE_URL}/schema/translate",
    json={"prompt": "Generate financial transactions"}
)
schema = schema_response.json()["schema"]

# 2. Start generation
gen_response = requests.post(
    f"{BASE_URL}/data/generate",
    json={
        "schema": schema,
        "total_rows": 1000,
        "enable_deduplication": True
    }
)
job_id = gen_response.json()["job_id"]

# 3. Poll for completion
while True:
    status = requests.get(f"{BASE_URL}/jobs/{job_id}/status").json()
    
    print(f"Progress: {status['progress_percentage']:.1f}%")
    
    if status["status"] == "completed":
        data = status["data"]
        print(f"Generated {len(data)} rows")
        break
    elif status["status"] == "failed":
        print(f"Failed: {status['error']}")
        break
    
    time.sleep(2)
```

### cURL Examples

**Generate 100 rows:**
```bash
# Translate schema
SCHEMA=$(curl -s -X POST "http://localhost:8000/api/v1/schema/translate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "user records with name and email"}' | jq -c '.schema')

# Generate data
JOB_ID=$(curl -s -X POST "http://localhost:8000/api/v1/data/generate" \
  -H "Content-Type: application/json" \
  -d "{\"schema\": $SCHEMA, \"total_rows\": 100}" | jq -r '.job_id')

# Check status
curl "http://localhost:8000/api/v1/jobs/$JOB_ID/status" | jq
```

---

## WebSocket Support (Future)

**Planned:** Real-time status updates via WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/jobs/{job_id}');

ws.onmessage = (event) => {
  const status = JSON.parse(event.data);
  console.log('Progress:', status.progress_percentage);
};
```

---

## OpenAPI/Swagger

Interactive API documentation available at:

**URL:** http://localhost:8000/docs

Features:
- Try-it-out functionality
- Request/response examples
- Schema validation
- Authentication testing
