# SynthAIx Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-31

### Added
- 🎉 Initial release of SynthAIx
- FastAPI backend with RESTful API
- Streamlit frontend with human-in-the-loop workflow
- Natural language to schema translation using OpenAI
- Parallel data generation with ThreadPoolExecutor (20 workers)
- Vector-based deduplication using ChromaDB
- Redis-backed job state management
- Real-time progress tracking and monitoring
- Agent performance metrics dashboard
- Docker containerization with docker-compose
- Comprehensive documentation (README, API, DEPLOYMENT)
- Health check and metrics endpoints
- Structured JSON logging
- Example test suite

### Features
- **Schema Translation**: Convert natural language prompts to structured schemas
- **Parallel Generation**: Generate up to 1M rows with configurable parallelism
- **Deduplication**: Semantic similarity-based duplicate detection
- **Progress Tracking**: Real-time progress bars and chunk visualization
- **Metrics**: Token usage, API calls, speed, deduplication rate
- **Export Options**: Download as CSV, JSON, or Excel

### API Endpoints
- `POST /api/v1/schema/translate` - Translate natural language to schema
- `POST /api/v1/data/generate` - Start data generation job
- `GET /api/v1/jobs/{job_id}/status` - Get job status
- `GET /api/v1/health` - Health check
- `GET /api/v1/metrics` - System metrics

### Documentation
- Comprehensive README with architecture diagrams
- API reference documentation
- Deployment guide for Docker, AWS, GCP, Azure
- Contributing guidelines
- Example test suite

### Infrastructure
- Docker images for backend and frontend
- Docker Compose orchestration
- Redis for job state
- ChromaDB for vector storage
- Environment variable configuration
- Automated health checks

## [Unreleased]

### Planned
- WebSocket support for real-time updates
- Authentication and authorization
- Rate limiting per user
- Support for more LLM providers
- Custom field generators
- Export to databases
- Scheduled generation jobs
- ML-based duplicate detection improvements
- Multi-language UI support

---

## Version History

- **1.0.0** (2025-10-31) - Initial release

---

For detailed changes, see the [commit history](https://github.com/yourusername/synthaix/commits/main).
