# 📁 SynthAIx Project Structure

```
synthaix/
│
├── 📄 README.md                    # Main documentation
├── 📄 CONTRIBUTING.md              # Contribution guidelines
├── 📄 CHANGELOG.md                 # Version history
├── 📄 LICENSE                      # MIT License
├── 📄 .gitignore                   # Git ignore rules
├── 📄 .env.example                 # Environment template
├── 📄 docker-compose.yml           # Docker orchestration
├── 📄 pyproject.toml               # Project configuration
├── 🔧 start.sh                     # Quick start script
├── 🔧 setup-dev.sh                 # Development setup
│
├── 📂 backend/                     # FastAPI Backend
│   ├── 📄 Dockerfile               # Backend container
│   ├── 📄 requirements.txt         # Python dependencies
│   │
│   └── 📂 app/                     # Application code
│       ├── 📄 __init__.py
│       ├── 📄 main.py              # FastAPI app entry
│       │
│       ├── 📂 agents/              # AI Agents
│       │   ├── 📄 __init__.py
│       │   ├── 📄 generator.py     # Worker agent
│       │   └── 📄 orchestrator.py  # Orchestrator agent
│       │
│       ├── 📂 api/                 # API Layer
│       │   ├── 📄 __init__.py
│       │   └── 📄 routes.py        # REST endpoints
│       │
│       ├── 📂 core/                # Core Configuration
│       │   ├── 📄 __init__.py
│       │   ├── 📄 config.py        # Settings
│       │   └── 📄 logging.py       # Structured logging
│       │
│       ├── 📂 models/              # Data Models
│       │   ├── 📄 __init__.py
│       │   └── 📄 schemas.py       # Pydantic models
│       │
│       ├── 📂 tools/               # AI Tools
│       │   ├── 📄 __init__.py
│       │   └── 📄 deduplication.py # ChromaDB dedupe
│       │
│       └── 📂 utils/               # Utilities
│           ├── 📄 __init__.py
│           └── 📄 job_manager.py   # Job state mgmt
│
├── 📂 frontend/                    # Streamlit Frontend
│   ├── 📄 Dockerfile               # Frontend container
│   ├── 📄 requirements.txt         # Python dependencies
│   ├── 📄 app.py                   # Main Streamlit app
│   │
│   ├── 📂 components/              # UI Components
│   │   └── 📄 visualizations.py    # Charts & graphs
│   │
│   └── 📂 utils/                   # Frontend Utils
│       └── 📄 api_client.py        # Backend API client
│
├── 📂 docs/                        # Documentation
│   ├── 📄 API.md                   # API reference
│   └── 📄 DEPLOYMENT.md            # Deployment guide
│
├── 📂 tests/                       # Test Suites
│   └── 📄 test_backend.py          # Backend tests
│
├── 📂 config/                      # Configuration Files
│
└── 📂 data/                        # Data Persistence
    └── 📂 chroma_db/               # Vector database
```

## 📊 Component Overview

### Backend Components

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **Agents** | AI orchestration and generation | `generator.py`, `orchestrator.py` |
| **API** | RESTful endpoints | `routes.py` |
| **Core** | Configuration and logging | `config.py`, `logging.py` |
| **Models** | Data validation | `schemas.py` |
| **Tools** | Deduplication and utilities | `deduplication.py` |
| **Utils** | Job management | `job_manager.py` |

### Frontend Components

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **Main App** | User interface | `app.py` |
| **Components** | Reusable UI elements | `visualizations.py` |
| **Utils** | API communication | `api_client.py` |

### Infrastructure

| Component | Purpose | Files |
|-----------|---------|-------|
| **Docker** | Containerization | `Dockerfile`, `docker-compose.yml` |
| **Config** | Environment setup | `.env.example` |
| **Scripts** | Automation | `start.sh`, `setup-dev.sh` |
| **Docs** | Documentation | `README.md`, `docs/` |

## 🔄 Data Flow

```
User Input (Streamlit)
    ↓
API Client (utils/api_client.py)
    ↓
FastAPI Routes (api/routes.py)
    ↓
Orchestrator Agent (agents/orchestrator.py)
    ↓
Generator Agents (agents/generator.py) [Parallel]
    ↓
OpenAI API (External)
    ↓
Deduplication Tool (tools/deduplication.py)
    ↓
ChromaDB (Vector Database)
    ↓
Job Manager (utils/job_manager.py)
    ↓
Redis (Job State)
    ↓
Response → Frontend → User
```

## 📦 Dependencies

### Backend
- **Framework**: FastAPI, Uvicorn
- **AI**: OpenAI SDK
- **Database**: Redis, ChromaDB
- **Validation**: Pydantic
- **Async**: httpx

### Frontend
- **UI**: Streamlit
- **Visualization**: Plotly
- **Data**: Pandas
- **HTTP**: requests

### Infrastructure
- **Container**: Docker, Docker Compose
- **Language**: Python 3.11+
- **Cache**: Redis 7.2
- **Vector DB**: ChromaDB 0.4

## 🚀 Entry Points

| Service | Entry Point | Port |
|---------|-------------|------|
| **Backend** | `app/main.py` | 8000 |
| **Frontend** | `app.py` | 8501 |
| **Redis** | System | 6379 |

## 📝 Configuration Files

- `.env` - Environment variables (create from `.env.example`)
- `pyproject.toml` - Project metadata and tool config
- `docker-compose.yml` - Service orchestration
- `requirements.txt` - Python dependencies

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
pytest tests/

# Integration tests
pytest tests/integration/
```

## 📚 Documentation

- `README.md` - Overview and quick start
- `docs/API.md` - API reference
- `docs/DEPLOYMENT.md` - Deployment guide
- `CONTRIBUTING.md` - Contribution guidelines
- `CHANGELOG.md` - Version history

---

**Total Files**: 40+
**Total Lines of Code**: 5000+
**Languages**: Python, Shell, YAML, Markdown
**Architecture**: Microservices with Docker
