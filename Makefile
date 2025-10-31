.PHONY: help install dev test lint format clean docker-build docker-up docker-down docker-logs

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RESET  := \033[0m

help: ## Show this help message
	@echo '$(GREEN)SynthAIx - Available Commands$(RESET)'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}'

# =============================================================================
# Installation & Setup
# =============================================================================

install: ## Install all dependencies (backend + frontend)
	@echo "$(GREEN)Installing backend dependencies...$(RESET)"
	cd backend && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	@echo "$(GREEN)Installing frontend dependencies...$(RESET)"
	cd frontend && npm install
	@echo "$(GREEN)Creating .env file from template...$(RESET)"
	cp -n .env.example .env || true
	@echo "$(GREEN)✓ Installation complete!$(RESET)"

setup: install ## Alias for install
	@echo "$(GREEN)✓ Setup complete!$(RESET)"

# =============================================================================
# Development
# =============================================================================

dev-backend: ## Start backend development server
	cd backend && . venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	cd frontend && npm run dev

dev: ## Start both backend and frontend in development mode
	@echo "$(GREEN)Starting development servers...$(RESET)"
	@trap 'kill 0' EXIT; \
	make dev-backend & \
	make dev-frontend & \
	wait

# =============================================================================
# Testing
# =============================================================================

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd backend && . venv/bin/activate && pytest -v

test-frontend: ## Run frontend tests
	cd frontend && npm test

test-coverage: ## Run tests with coverage report
	cd backend && . venv/bin/activate && pytest --cov=app --cov-report=html --cov-report=term
	cd frontend && npm run test:coverage

# =============================================================================
# Code Quality
# =============================================================================

lint: lint-backend lint-frontend ## Run linting for all code

lint-backend: ## Lint backend code
	cd backend && . venv/bin/activate && ruff check app/

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint

format: format-backend format-frontend ## Format all code

format-backend: ## Format backend code with black
	cd backend && . venv/bin/activate && black app/ && ruff check --fix app/

format-frontend: ## Format frontend code with prettier
	cd frontend && npm run format

typecheck: ## Run type checking
	cd backend && . venv/bin/activate && mypy app/
	cd frontend && npm run typecheck

# =============================================================================
# Docker
# =============================================================================

docker-build: ## Build Docker images
	@echo "$(GREEN)Building Docker images...$(RESET)"
	docker-compose build

docker-up: ## Start all services with Docker Compose
	@echo "$(GREEN)Starting Docker containers...$(RESET)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services started!$(RESET)"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

docker-down: ## Stop all Docker containers
	@echo "$(YELLOW)Stopping Docker containers...$(RESET)"
	docker-compose down

docker-restart: docker-down docker-up ## Restart all Docker containers

docker-logs: ## View Docker container logs
	docker-compose logs -f

docker-logs-backend: ## View backend logs only
	docker-compose logs -f backend

docker-logs-frontend: ## View frontend logs only
	docker-compose logs -f frontend

docker-clean: ## Remove all Docker containers, volumes, and images
	@echo "$(YELLOW)Cleaning up Docker resources...$(RESET)"
	docker-compose down -v --rmi all

docker-shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

docker-shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

# =============================================================================
# Database
# =============================================================================

db-up: ## Start database with Docker Compose
	docker-compose --profile with-db up -d postgres

db-migrate: ## Run database migrations
	cd backend && . venv/bin/activate && alembic upgrade head

db-reset: ## Reset database
	cd backend && . venv/bin/activate && alembic downgrade base && alembic upgrade head

db-shell: ## Open database shell
	docker-compose exec postgres psql -U synthaix -d synthaix

# =============================================================================
# Production
# =============================================================================

prod-up: ## Start production environment with nginx
	@echo "$(GREEN)Starting production environment...$(RESET)"
	docker-compose --profile production up -d

prod-down: ## Stop production environment
	docker-compose --profile production down

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean all generated files and caches
	@echo "$(YELLOW)Cleaning up...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.log" -delete
	rm -rf backend/htmlcov backend/.coverage
	rm -rf frontend/coverage
	@echo "$(GREEN)✓ Cleanup complete!$(RESET)"

clean-all: clean docker-clean ## Deep clean including Docker resources
	rm -rf backend/venv
	rm -rf backend/data
	@echo "$(GREEN)✓ Deep cleanup complete!$(RESET)"

# =============================================================================
# Utilities
# =============================================================================

check-env: ## Check if .env file exists and is configured
	@if [ -f .env ]; then \
		echo "$(GREEN)✓ .env file exists$(RESET)"; \
		if grep -q "your-.*-key-here" .env; then \
			echo "$(YELLOW)⚠ Warning: Some API keys still need to be configured in .env$(RESET)"; \
		else \
			echo "$(GREEN)✓ API keys appear to be configured$(RESET)"; \
		fi \
	else \
		echo "$(YELLOW)⚠ .env file not found. Run 'make install' first.$(RESET)"; \
		exit 1; \
	fi

health-check: ## Check health of running services
	@echo "$(GREEN)Checking service health...$(RESET)"
	@curl -sf http://localhost:8000/health || echo "$(YELLOW)⚠ Backend not responding$(RESET)"
	@curl -sf http://localhost:3000 > /dev/null || echo "$(YELLOW)⚠ Frontend not responding$(RESET)"

logs: ## View all logs
	tail -f backend/logs/*.log frontend/.next/trace || true

.DEFAULT_GOAL := help
