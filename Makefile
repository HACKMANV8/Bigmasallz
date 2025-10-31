# Makefile for SynthAIx

.PHONY: help install start stop restart logs clean test format lint docs build deploy

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "SynthAIx - Makefile Commands"
	@echo "=============================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation and Setup
install: ## Install development environment
	@echo "Setting up development environment..."
	./setup-dev.sh

setup: ## Create .env file from template
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created. Please edit it and add your OPENAI_API_KEY"; \
	else \
		echo ".env file already exists"; \
	fi

# Docker Operations
build: ## Build Docker images
	@echo "Building Docker images..."
	docker-compose build

start: ## Start all services
	@echo "Starting SynthAIx..."
	docker-compose up -d
	@echo "Services started. Frontend: http://localhost:8501"

stop: ## Stop all services
	@echo "Stopping SynthAIx..."
	docker-compose down

restart: ## Restart all services
	@echo "Restarting SynthAIx..."
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

logs-frontend: ## View frontend logs only
	docker-compose logs -f frontend

ps: ## Show running services
	docker-compose ps

# Development
dev-backend: ## Run backend in development mode
	@echo "Starting backend in dev mode..."
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run frontend in development mode
	@echo "Starting frontend in dev mode..."
	cd frontend && source venv/bin/activate && streamlit run app.py

# Testing
test: ## Run all tests
	@echo "Running tests..."
	cd backend && source venv/bin/activate && pytest
	cd frontend && source venv/bin/activate && pytest

test-backend: ## Run backend tests only
	@echo "Running backend tests..."
	cd backend && source venv/bin/activate && pytest -v

test-frontend: ## Run frontend tests only
	@echo "Running frontend tests..."
	cd frontend && source venv/bin/activate && pytest -v

test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	cd backend && source venv/bin/activate && pytest --cov=app --cov-report=html

# Code Quality
format: ## Format code with black
	@echo "Formatting code..."
	cd backend && source venv/bin/activate && black app/
	cd frontend && source venv/bin/activate && black .

lint: ## Lint code with pylint
	@echo "Linting code..."
	cd backend && source venv/bin/activate && pylint app/
	cd frontend && source venv/bin/activate && pylint *.py

type-check: ## Check types with mypy
	@echo "Type checking..."
	cd backend && source venv/bin/activate && mypy app/

# Cleanup
clean: ## Remove containers, volumes, and temporary files
	@echo "Cleaning up..."
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

clean-data: ## Remove persistent data (ChromaDB, Redis)
	@echo "Removing persistent data..."
	rm -rf data/chroma_db/*
	docker-compose down -v

# Health Checks
health: ## Check service health
	@echo "Checking service health..."
	@curl -s http://localhost:8000/api/v1/health | jq . || echo "Backend not responding"
	@curl -s http://localhost:8501/_stcore/health || echo "Frontend not responding"

ping-backend: ## Ping backend API
	curl http://localhost:8000/api/v1/health

ping-frontend: ## Ping frontend
	curl http://localhost:8501/_stcore/health

# Documentation
docs: ## Open API documentation in browser
	@echo "Opening API docs..."
	@open http://localhost:8000/docs 2>/dev/null || xdg-open http://localhost:8000/docs 2>/dev/null || echo "Please open http://localhost:8000/docs manually"

docs-serve: ## Serve documentation locally
	@echo "Serving documentation..."
	@cd docs && python -m http.server 8080

# Database
db-reset: ## Reset ChromaDB (clear all vectors)
	@echo "Resetting ChromaDB..."
	rm -rf data/chroma_db/*
	docker-compose restart backend

redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

redis-flush: ## Flush Redis database
	docker-compose exec redis redis-cli FLUSHALL

# Deployment
deploy-prod: ## Deploy to production
	@echo "Deploying to production..."
	docker-compose -f docker-compose.prod.yml up -d --build

deploy-staging: ## Deploy to staging
	@echo "Deploying to staging..."
	docker-compose -f docker-compose.staging.yml up -d --build

# Monitoring
monitor: ## Show resource usage
	docker stats

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/bash

# Quick Actions
quick-start: setup build start ## Quick start: setup, build, and start
	@echo "✅ SynthAIx is running!"
	@echo "   Frontend: http://localhost:8501"
	@echo "   Backend:  http://localhost:8000"
	@echo "   API Docs: http://localhost:8000/docs"

update: ## Pull latest changes and rebuild
	@echo "Updating SynthAIx..."
	git pull
	docker-compose down
	docker-compose up -d --build

backup: ## Backup ChromaDB data
	@echo "Backing up data..."
	@mkdir -p backups
	tar -czf backups/synthaix_backup_$$(date +%Y%m%d_%H%M%S).tar.gz data/

restore: ## Restore from latest backup
	@echo "Restoring from latest backup..."
	@latest=$$(ls -t backups/*.tar.gz | head -1); \
	if [ -n "$$latest" ]; then \
		tar -xzf $$latest; \
		echo "Restored from $$latest"; \
	else \
		echo "No backup found"; \
	fi

# Information
version: ## Show version information
	@echo "SynthAIx Version 1.0.0"
	@echo "Python: $$(python3 --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"

info: ## Show project information
	@echo "SynthAIx Project Information"
	@echo "============================"
	@echo "Backend:  FastAPI + OpenAI"
	@echo "Frontend: Streamlit"
	@echo "Database: Redis + ChromaDB"
	@echo "Workers:  20 (configurable)"
	@echo ""
	@echo "Ports:"
	@echo "  - 8000: Backend API"
	@echo "  - 8501: Frontend UI"
	@echo "  - 6379: Redis"
