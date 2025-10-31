# SynthAIx Quick Start Guide

Get SynthAIx up and running in minutes!

## Prerequisites

- **Docker & Docker Compose** (Recommended) OR
- **Python 3.11+** and **Node.js 18+** (For local development)
- **OpenAI API Key** (Required)

## Option 1: Quick Start with Docker (Recommended)

### 1. Clone and Setup

```bash
# Navigate to project directory
cd /home/neonpulse/Dev/codezz/hackthons/hackman_v8/final

# Create environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env
# Set OPENAI_API_KEY=your-actual-key-here
```

### 2. Start All Services

```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Generate Your First Dataset

1. Visit http://localhost:3000
2. Enter a description: "Generate 1000 customer records with name, email, age, and city"
3. Review and confirm the schema
4. Configure generation parameters
5. Start generation and watch progress
6. Download results as CSV or JSON

### 5. Stop Services

```bash
docker-compose down
```

---

## Option 2: Local Development Setup

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp ../.env.example .env
nano .env  # Add your OPENAI_API_KEY

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

### Frontend Setup

```bash
# Open new terminal and navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start frontend server
npm run dev
```

Frontend will be available at http://localhost:3000

---

## Configuration Options

### Environment Variables

Edit `.env` file:

```env
# LLM Configuration
OPENAI_API_KEY=sk-your-key-here          # Required
DEFAULT_LLM_PROVIDER=openai               # openai or anthropic
DEFAULT_MODEL=gpt-4-turbo-preview         # Model to use

# Generation Settings
MAX_WORKERS=20                            # Parallel workers (1-50)
DEFAULT_CHUNK_SIZE=500                    # Rows per chunk (100-2000)
DEDUPLICATION_THRESHOLD=0.85              # Similarity threshold (0.0-1.0)

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
LOG_LEVEL=INFO

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Testing the API Directly

### 1. Translate Schema

```bash
curl -X POST http://localhost:8000/api/schema/translate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Generate customer data with name, email, age, and signup date"
  }'
```

### 2. Generate Data

```bash
curl -X POST http://localhost:8000/api/data/generate \
  -H "Content-Type: application/json" \
  -d '{
    "schema": {
      "columns": [
        {"name": "name", "type": "string", "description": "Customer name"},
        {"name": "email", "type": "email", "description": "Email address"},
        {"name": "age", "type": "integer", "description": "Customer age"}
      ]
    },
    "total_rows": 100,
    "chunk_size": 50,
    "max_workers": 5
  }'
```

### 3. Check Job Status

```bash
# Replace JOB_ID with actual job ID from previous response
curl http://localhost:8000/api/jobs/JOB_ID/status
```

### 4. Download Results

```bash
# Download as CSV
curl http://localhost:8000/api/jobs/JOB_ID/download?format=csv -O

# Download as JSON
curl http://localhost:8000/api/jobs/JOB_ID/download?format=json -O
```

---

## Common Use Cases

### 1. Small Dataset (Quick Test)

```json
{
  "prompt": "Generate 100 user records with ID, username, and email",
  "total_rows": 100,
  "chunk_size": 50,
  "max_workers": 2
}
```

### 2. Medium Dataset (Typical Use)

```json
{
  "prompt": "Generate 10,000 e-commerce transactions with product, price, quantity, and timestamp",
  "total_rows": 10000,
  "chunk_size": 500,
  "max_workers": 20
}
```

### 3. Large Dataset (High Scale)

```json
{
  "prompt": "Generate 100,000 IoT sensor readings with device_id, temperature, humidity, and timestamp",
  "total_rows": 100000,
  "chunk_size": 1000,
  "max_workers": 50
}
```

---

## Troubleshooting

### Issue: "OpenAI API key not found"

**Solution**: Ensure `OPENAI_API_KEY` is set in `.env` file

```bash
# Check if set
echo $OPENAI_API_KEY

# Set manually
export OPENAI_API_KEY=sk-your-key-here
```

### Issue: "Cannot connect to backend"

**Solution**: 
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify port is not in use: `lsof -i :8000`
3. Check Docker logs: `docker-compose logs backend`

### Issue: "ChromaDB initialization failed"

**Solution**: 
1. Ensure `data/chromadb` directory exists
2. Check write permissions: `chmod 755 data/chromadb`
3. Clear existing data: `rm -rf data/chromadb/*`

### Issue: "Frontend cannot connect to API"

**Solution**:
1. Verify `NEXT_PUBLIC_API_URL` in `.env.local`
2. Check CORS settings in backend config
3. Ensure backend is accessible from browser

### Issue: "Generation is slow"

**Solution**:
1. Increase `max_workers` (default: 20, max: 50)
2. Increase `chunk_size` for larger rows
3. Check LLM API rate limits
4. Monitor system resources (CPU, memory)

---

## Performance Tuning

### Optimal Settings for Different Scales

**Small Jobs (< 1,000 rows)**
```env
MAX_WORKERS=5
DEFAULT_CHUNK_SIZE=100
```

**Medium Jobs (1,000-10,000 rows)**
```env
MAX_WORKERS=20
DEFAULT_CHUNK_SIZE=500
```

**Large Jobs (> 10,000 rows)**
```env
MAX_WORKERS=50
DEFAULT_CHUNK_SIZE=1000
```

### Rate Limit Considerations

OpenAI API limits (as of 2025):
- GPT-4: ~10,000 requests/min (Pay-as-you-go)
- Embeddings: ~3,000 requests/min

Adjust `max_workers` to stay within limits:
```
max_workers ≤ (rate_limit_per_min × 60) / time_per_chunk
```

---

## Next Steps

1. **Explore Examples**: Check `examples/` directory for sample prompts
2. **Read Documentation**: See `ARCHITECTURE.md` for detailed system design
3. **Customize Schemas**: Edit generated schemas before generation
4. **Export Data**: Download in CSV or JSON format
5. **Scale Up**: Deploy to cloud for production use

---

## Useful Commands

```bash
# Development
make dev              # Start development servers
make test             # Run all tests
make lint             # Lint code
make format           # Format code

# Docker
make docker-build     # Build Docker images
make docker-up        # Start containers
make docker-down      # Stop containers
make docker-logs      # View logs

# Cleanup
make clean            # Clean generated files
make clean-all        # Deep clean (includes Docker)
```

---

## Support

- **Documentation**: See `/docs` directory
- **API Reference**: http://localhost:8000/docs
- **Issues**: File issues on GitHub
- **Email**: support@synthaix.dev

---

## Quick Reference Card

| Action | Command |
|--------|---------|
| Start services | `docker-compose up -d` |
| View logs | `docker-compose logs -f` |
| Stop services | `docker-compose down` |
| Check health | `curl http://localhost:8000/health` |
| Access frontend | http://localhost:3000 |
| Access API docs | http://localhost:8000/docs |
| Run tests | `cd backend && pytest` |
| Format code | `cd backend && black app/` |

---

Happy generating! 🚀
