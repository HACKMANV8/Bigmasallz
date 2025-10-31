# SynthAIx Backend

FastAPI backend for the SynthAIx synthetic data generation platform.

## Features

- **Schema Translation**: Convert natural language to structured schemas
- **Parallel Data Generation**: Generate data using concurrent worker agents
- **Deduplication**: FastMCP tool with ChromaDB vector embeddings
- **Job Management**: Track and monitor generation jobs
- **REST API**: Full RESTful API with OpenAPI documentation

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-key-here
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4-turbo-preview
MAX_WORKERS=20
```

## Running

### Development

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```bash
docker build -t synthaix-backend .
docker run -p 8000:8000 --env-file .env synthaix-backend
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_orchestrator.py -v
```

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes
│   ├── core/             # Configuration & logging
│   ├── models/           # Pydantic models
│   ├── services/         # Business logic
│   ├── agents/           # Worker agents
│   ├── tools/            # FastMCP tools
│   ├── utils/            # Utilities
│   └── main.py           # Application entry
├── tests/                # Test suite
├── Dockerfile            # Docker configuration
├── requirements.txt      # Dependencies
└── pyproject.toml        # Project configuration
```

## License

MIT License
