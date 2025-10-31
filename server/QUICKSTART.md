# Running the Synthetic Data Generator

This guide explains how to run the complete Synthetic Data Generator application with both API server and Streamlit frontend.

## Prerequisites

- Python 3.10 or higher
- UV package manager (recommended) or pip
- Google Gemini API key

## Quick Start

### 1. Install Dependencies

Using UV (recommended):
```bash
uv sync
```

Using pip:
```bash
pip install -e .
```

### 2. Configure Environment

Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash

# Optional: Langfuse telemetry
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
```

### 3. Start the API Server

In terminal 1:
```bash
uvicorn src.api_server.app:app --reload --host 0.0.0.0 --port 8080
```

The API server will be available at:
- API: http://localhost:8080
- Interactive docs: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

### 4. Start the Streamlit Frontend

In terminal 2:
```bash
streamlit run streamlit_app.py
```

The Streamlit app will open in your browser at http://localhost:8501

## Using the Application

### Create a Dataset

1. Go to the **Create Dataset** page
2. Choose your input method:
   - **Natural Language**: Describe your dataset in plain English
   - **JSON Schema**: Provide a structured schema definition
3. Configure generation parameters:
   - Total rows to generate
   - Chunk size (for processing)
   - Output format (CSV, JSON, or Parquet)
4. Click **Generate Dataset**

#### Example Natural Language Inputs

```
Generate customer data with full name, email address, phone number, 
age between 18-80, registration date from the last 2 years, and 
account status (active, inactive, suspended)
```

```
Create employee records including employee ID, first name, last name, 
department (Engineering, Sales, Marketing, HR), hire date, salary 
between 40000-150000, and performance rating (1-5)
```

```
Generate e-commerce orders with order ID, customer name, product name, 
quantity, unit price, total amount, order date, and status 
(pending, shipped, delivered, cancelled)
```

### Monitor Jobs

1. Go to the **Monitor Jobs** page
2. Enter your job ID (provided when you create a dataset)
3. Watch real-time progress updates
4. Control job execution:
   - Pause/Resume generation
   - Cancel jobs
5. Preview generated data
6. Download completed datasets

### Browse Jobs

1. Go to the **Browse Jobs** page
2. Filter jobs by status
3. View all your generation jobs
4. Click on any job to monitor it

## API Endpoints

### Schema Extraction
```bash
POST /schema/extract
```
Extract structured schema from natural language description.

**Request:**
```json
{
  "user_input": "Generate customer data with name, email, and age",
  "context": {},
  "example_data": null
}
```

### Create Job
```bash
POST /jobs/create
```
Create a new data generation job.

**Request:**
```json
{
  "schema": {
    "fields": [
      {
        "name": "id",
        "type": "uuid",
        "description": "Unique identifier"
      },
      {
        "name": "name",
        "type": "string",
        "description": "Customer name"
      }
    ]
  },
  "total_rows": 1000,
  "chunk_size": 100,
  "output_format": "csv"
}
```

### Get Job Status
```bash
GET /jobs/{job_id}/status
```
Get the current status of a job.

### List Jobs
```bash
GET /jobs/?status=completed&limit=50
```
List all jobs with optional filtering.

### Download Dataset
```bash
GET /jobs/{job_id}/download
```
Download the generated dataset file.

### Preview Data
```bash
GET /jobs/{job_id}/preview?rows=10
```
Preview the first N rows of generated data.

## Architecture

```
┌─────────────────────┐
│  Streamlit Frontend │
│   (Port 8501)       │
└──────────┬──────────┘
           │ HTTP
           ▼
┌─────────────────────┐
│   FastAPI Server    │
│   (Port 8080)       │
└──────────┬──────────┘
           │
           ├──► Gemini API (Schema & Data Generation)
           ├──► Job Manager (Job State & Progress)
           ├──► Storage Handler (Disk/Memory Storage)
           └──► Vector Store (Optional: ChromaDB)
```

## File Structure

```
server/
├── src/
│   ├── api/
│   │   └── gemini_client.py       # Gemini API integration
│   ├── api_server/
│   │   ├── app.py                 # FastAPI application
│   │   └── routers/
│   │       ├── health.py          # Health check endpoints
│   │       ├── schema.py          # Schema extraction endpoints
│   │       └── jobs.py            # Job management endpoints
│   ├── core/
│   │   ├── job_manager.py         # Job lifecycle management
│   │   └── models.py              # Pydantic models
│   ├── storage/
│   │   ├── handlers.py            # Storage implementations
│   │   └── vector_store.py        # Vector database
│   └── utils/
│       ├── logger.py              # Logging utilities
│       └── validators.py          # Data validation
├── streamlit_app.py               # Streamlit frontend
├── pyproject.toml                 # Dependencies
└── .env                           # Environment variables
```

## Configuration

Edit `src/config.py` or use environment variables:

```python
# Gemini API
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-1.5-flash
GEMINI_MAX_RETRIES=3
GEMINI_TIMEOUT=60

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_TOKENS_PER_MINUTE=1000000

# Job Management
JOB_MAX_CONCURRENT_JOBS=5
JOB_CLEANUP_DAYS=7

# Storage
STORAGE_TYPE=disk
TEMP_PATH=./temp
OUTPUT_PATH=./output

# Logging
LOG_LEVEL=INFO
```

## Troubleshooting

### API Server Not Starting
- Check if port 8080 is available
- Verify your Gemini API key is set
- Check logs for error messages

### Streamlit Can't Connect to API
- Ensure API server is running on port 8080
- Check if firewall is blocking connections
- Verify API_BASE_URL in streamlit_app.py

### Job Generation Fails
- Check your Gemini API quota
- Verify schema is valid
- Check job logs in `./logs` directory

### Out of Memory Errors
- Reduce chunk_size parameter
- Use disk storage instead of memory
- Generate fewer rows per job

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
ruff check .
```

### Type Checking
```bash
mypy src/
```

## Production Deployment

### Using Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

# Start API server
CMD ["uvicorn", "src.api_server.app:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Environment Variables for Production
```env
GEMINI_API_KEY=production_key
LOG_LEVEL=WARNING
STORAGE_TYPE=cloud
JOB_CLEANUP_DAYS=30
```

## Support

For issues and questions:
- Check the [documentation](./README.md)
- Review [API documentation](./README_ENDPOINTS.md)
- See [examples](./examples/)

## License

MIT License - see LICENSE file for details
