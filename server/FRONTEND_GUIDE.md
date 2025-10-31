# 🎲 Synthetic Data Generator - Complete Application

## What We've Built

A complete **Synthetic Data Generation Platform** with:

1. **RESTful API Server** (FastAPI) - Backend service for data generation
2. **Streamlit Web UI** - Interactive frontend for users
3. **LLM-Powered Schema Extraction** - Natural language to structured schema
4. **Job Management System** - Async generation with progress tracking
5. **Storage Layer** - Disk and memory storage handlers

---

## 🚀 Quick Start

### Option 1: Start Everything at Once

```bash
./start.sh
```

This will start both the API server and Streamlit frontend automatically.

### Option 2: Start Services Individually

**Terminal 1 - API Server:**
```bash
uv run uvicorn src.api_server.app:app --reload --host 0.0.0.0 --port 8080
```

**Terminal 2 - Streamlit Frontend:**
```bash
uv run streamlit run streamlit_app.py
```

### Access Points

- 🌐 **Streamlit UI**: http://localhost:8501
- 🔧 **API Server**: http://localhost:8080
- 📚 **API Docs**: http://localhost:8080/docs
- 📖 **ReDoc**: http://localhost:8080/redoc

---

## 📱 Using the Streamlit Frontend

### 1. Create Dataset Page

#### Natural Language Input
Simply describe what data you want:

```
Generate 1000 customer records with:
- Full name
- Email address (valid format)
- Phone number (US format)
- Age between 18-80
- Registration date from the last 2 years
- Account status (active, inactive, suspended)
- Account balance between $0-10000
```

The AI will extract a structured schema from your description!

#### JSON Schema Input
Provide a detailed schema:

```json
{
  "fields": [
    {
      "name": "customer_id",
      "type": "uuid",
      "description": "Unique customer identifier"
    },
    {
      "name": "full_name",
      "type": "string",
      "description": "Customer full name"
    },
    {
      "name": "email",
      "type": "email",
      "description": "Customer email address"
    },
    {
      "name": "age",
      "type": "integer",
      "description": "Customer age",
      "constraints": {
        "min_value": 18,
        "max_value": 80
      }
    }
  ]
}
```

### 2. Monitor Jobs Page

- **Real-time Progress**: Watch your data being generated
- **Live Metrics**: See rows generated, chunks completed, progress %
- **Job Control**: Pause, resume, or cancel jobs
- **Data Preview**: View sample data as it's generated
- **Download**: Get your completed dataset

### 3. Browse Jobs Page

- View all your generation jobs
- Filter by status (pending, generating, completed, failed)
- Click to monitor any job

---

## 🔌 API Endpoints

### Schema Extraction

```bash
curl -X POST "http://localhost:8080/schema/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Generate employee data with name, email, department, and salary"
  }'
```

**Response:**
```json
{
  "schema": {
    "fields": [
      {
        "name": "employee_id",
        "type": "uuid",
        "description": "Unique employee identifier"
      },
      {
        "name": "name",
        "type": "string",
        "description": "Employee full name"
      },
      {
        "name": "email",
        "type": "email",
        "description": "Employee email address"
      }
    ]
  }
}
```

### Create Generation Job

```bash
curl -X POST "http://localhost:8080/jobs/create" \
  -H "Content-Type: application/json" \
  -d '{
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
          "description": "Person name"
        }
      ]
    },
    "total_rows": 1000,
    "chunk_size": 100,
    "output_format": "csv"
  }'
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Job created successfully. Generating 1000 rows."
}
```

### Get Job Status

```bash
curl "http://localhost:8080/jobs/550e8400-e29b-41d4-a716-446655440000/status"
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "generating",
  "rows_generated": 500,
  "total_rows": 1000,
  "chunks_completed": 5,
  "total_chunks": 10,
  "progress_percentage": 50.0
}
```

### List All Jobs

```bash
curl "http://localhost:8080/jobs/?limit=50"
```

### Preview Data

```bash
curl "http://localhost:8080/jobs/550e8400-e29b-41d4-a716-446655440000/preview?rows=10"
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_rows": 1000,
  "preview_rows": 10,
  "data": [
    {
      "id": "a3b4c5d6-e7f8-9012-3456-789abcdef012",
      "name": "John Doe"
    }
  ]
}
```

### Download Dataset

```bash
curl "http://localhost:8080/jobs/550e8400-e29b-41d4-a716-446655440000/download" \
  --output dataset.csv
```

### Control Job

```bash
# Pause
curl -X POST "http://localhost:8080/jobs/550e8400-e29b-41d4-a716-446655440000/control" \
  -H "Content-Type: application/json" \
  -d '{"job_id": "550e8400-e29b-41d4-a716-446655440000", "action": "pause"}'

# Resume
curl -X POST "http://localhost:8080/jobs/550e8400-e29b-41d4-a716-446655440000/control" \
  -H "Content-Type: application/json" \
  -d '{"job_id": "550e8400-e29b-41d4-a716-446655440000", "action": "resume"}'

# Cancel
curl -X POST "http://localhost:8080/jobs/550e8400-e29b-41d4-a716-446655440000/control" \
  -H "Content-Type: application/json" \
  -d '{"job_id": "550e8400-e29b-41d4-a716-446655440000", "action": "cancel"}'
```

---

## 📂 Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Streamlit Frontend                  │
│            http://localhost:8501                     │
│  - Create Dataset UI                                 │
│  - Monitor Jobs UI                                   │
│  - Browse Jobs UI                                    │
└───────────────────┬──────────────────────────────────┘
                    │ REST API Calls
                    ▼
┌──────────────────────────────────────────────────────┐
│              FastAPI Backend Server                  │
│            http://localhost:8080                     │
│                                                       │
│  Routers:                                            │
│  ├─ /health       - Health checks                   │
│  ├─ /schema       - Schema extraction                │
│  └─ /jobs         - Job management                   │
└───────────┬────────────────────────────────┬─────────┘
            │                                │
            ▼                                ▼
┌───────────────────────┐      ┌──────────────────────┐
│   Gemini API Client   │      │    Job Manager       │
│                       │      │                      │
│  - Schema extraction  │      │  - Job state         │
│  - Data generation    │      │  - Progress tracking │
│  - LLM interactions   │      │  - Job control       │
└───────────────────────┘      └──────────┬───────────┘
                                          │
                                          ▼
                              ┌──────────────────────┐
                              │  Storage Handlers    │
                              │                      │
                              │  - Disk storage      │
                              │  - Memory storage    │
                              │  - Chunk management  │
                              └──────────────────────┘
```

---

## 🎯 Example Use Cases

### 1. E-commerce Orders

**Description:**
```
Generate 5000 e-commerce orders with:
- Order ID
- Customer name
- Product name
- Quantity (1-10)
- Unit price ($10-500)
- Total amount (calculated)
- Order date (last 90 days)
- Status (pending, shipped, delivered, cancelled)
- Payment method (credit card, debit card, PayPal, crypto)
```

### 2. User Profiles

**Description:**
```
Create 10000 user profiles with:
- User ID (UUID)
- Username (unique, 5-20 characters)
- Email (valid format)
- First name and last name
- Date of birth (ages 18-80)
- Country (realistic distribution)
- Joined date (last 3 years)
- Account status (active, inactive, banned)
- Profile completion percentage (0-100)
```

### 3. IoT Sensor Data

**Description:**
```
Generate 50000 IoT sensor readings with:
- Sensor ID (from 100 sensors)
- Timestamp (last 7 days, every 5 minutes)
- Temperature (-20 to 50 Celsius)
- Humidity (0-100%)
- Pressure (900-1100 hPa)
- Battery level (0-100%)
- Signal strength (RSSI: -100 to -30)
- Status (online, offline, error)
```

### 4. Financial Transactions

**Description:**
```
Create 20000 financial transactions with:
- Transaction ID
- Account number
- Transaction type (deposit, withdrawal, transfer, payment)
- Amount ($1-10000)
- Currency (USD, EUR, GBP, JPY)
- Date and time (last 6 months)
- Merchant name (for payments)
- Status (pending, completed, failed, reversed)
- Description
```

---

## ⚙️ Configuration

Edit `.env` or `src/config.py`:

```env
# Gemini API
GEMINI_API_KEY=your_actual_api_key_here
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

---

## 🔍 Monitoring & Debugging

### View Logs

```bash
# API Server logs
tail -f logs/api.log

# Streamlit logs
tail -f logs/streamlit.log

# Application logs
tail -f logs/app.log
```

### Check Job Status Programmatically

```python
import requests

job_id = "your-job-id"
response = requests.get(f"http://localhost:8080/jobs/{job_id}/status")
status = response.json()

print(f"Status: {status['status']}")
print(f"Progress: {status['progress_percentage']:.1f}%")
print(f"Rows: {status['rows_generated']}/{status['total_rows']}")
```

---

## 🎨 Features

✅ **Natural Language Schema Extraction** - Describe data in plain English  
✅ **Async Job Processing** - Generate large datasets without blocking  
✅ **Progress Tracking** - Real-time updates on generation status  
✅ **Job Control** - Pause, resume, cancel jobs  
✅ **Multiple Formats** - CSV, JSON, Parquet output  
✅ **Data Preview** - See generated data before download  
✅ **Job Persistence** - Jobs survive restarts  
✅ **Error Handling** - Robust error recovery  
✅ **Rate Limiting** - Respect API quotas  
✅ **Chunked Generation** - Memory-efficient processing  

---

## 🚦 Status Codes

| Status | Description |
|--------|-------------|
| `pending` | Job created, waiting to start |
| `generating` | Actively generating data |
| `paused` | Job paused by user |
| `completed` | All data generated successfully |
| `failed` | Error occurred during generation |
| `cancelled` | Job cancelled by user |

---

## 📊 Performance Tips

1. **Chunk Size**: Use 100-1000 rows per chunk for optimal performance
2. **Storage**: Use disk storage for large datasets (>10k rows)
3. **Rate Limiting**: Adjust based on your API quota
4. **Concurrent Jobs**: Limit to 3-5 concurrent jobs
5. **Field Complexity**: Simpler schemas generate faster

---

## 🐛 Troubleshooting

### API Server Won't Start
```bash
# Check if port is in use
lsof -i :8080

# View error logs
tail -f logs/api.log
```

### Streamlit Connection Issues
- Ensure API server is running
- Check CORS settings in `src/api_server/app.py`
- Verify `API_BASE_URL` in `streamlit_app.py`

### Generation Failures
- Check Gemini API key and quota
- Validate schema constraints
- Review job error messages
- Check logs for details

---

## 📚 Additional Documentation

- [Complete README](./README.md)
- [API Endpoints](./README_ENDPOINTS.md)
- [Architecture Details](./ARCHITECTURE.md)
- [Quick Start Guide](./QUICKSTART.md)

---

## 🎉 You're All Set!

Start generating synthetic data:
```bash
./start.sh
```

Then open http://localhost:8501 and start creating datasets! 🚀
