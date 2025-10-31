#!/bin/bash

# Startup script for Synthetic Data Generator
# This script starts both the API server and Streamlit frontend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Synthetic Data Generator${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo "Creating .env from template..."
    cat > .env << EOF
# Gemini API Configuration
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
GEMINI_MAX_RETRIES=3
GEMINI_TIMEOUT=60

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_TOKENS_PER_MINUTE=1000000

# Job Configuration
JOB_MAX_CONCURRENT_JOBS=5
JOB_CLEANUP_DAYS=7

# Storage Configuration
STORAGE_TYPE=disk

# Logging
LOG_LEVEL=INFO

# Optional: Langfuse Telemetry
LANGFUSE_ENABLED=false
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_BASE_URL=https://cloud.langfuse.com
EOF
    echo -e "${YELLOW}Please edit .env and add your GEMINI_API_KEY${NC}"
    exit 1
fi

# Check if GEMINI_API_KEY is set
if grep -q "GEMINI_API_KEY=your_api_key_here" .env; then
    echo -e "${RED}❌ Error: Please set your GEMINI_API_KEY in .env file${NC}"
    exit 1
fi

# Create necessary directories
mkdir -p logs temp output vector_store

echo -e "${GREEN}✓${NC} Environment configured"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    kill $API_PID $STREAMLIT_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start API server in background
echo -e "${GREEN}Starting API Server...${NC}"
uvicorn src.api_server.app:app --reload --host 0.0.0.0 --port 8080 > logs/api.log 2>&1 &
API_PID=$!

# Wait for API to be ready
echo -n "Waiting for API server to start"
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✓${NC} API Server running on http://localhost:8080"
        echo -e "  📚 API Docs: http://localhost:8080/docs"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""

# Start Streamlit in background
echo -e "${GREEN}Starting Streamlit Frontend...${NC}"
streamlit run streamlit_app.py --server.headless true > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!

# Wait for Streamlit to be ready
echo -n "Waiting for Streamlit to start"
for i in {1..30}; do
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✓${NC} Streamlit running on http://localhost:8501"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "📱 Streamlit UI:  ${GREEN}http://localhost:8501${NC}"
echo -e "🔧 API Server:    ${GREEN}http://localhost:8080${NC}"
echo -e "📚 API Docs:      ${GREEN}http://localhost:8080/docs${NC}"
echo ""
echo -e "Logs:"
echo -e "  API:       ${YELLOW}logs/api.log${NC}"
echo -e "  Streamlit: ${YELLOW}logs/streamlit.log${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running
wait
