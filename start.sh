#!/bin/bash

# SynthAIx Startup Script

set -e

echo "🤖 Starting SynthAIx..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "❗ Please edit .env and add your OPENAI_API_KEY before continuing"
    exit 1
fi

# Check if OpenAI API key is set
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "❗ Please set your OPENAI_API_KEY in .env file"
    exit 1
fi

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Pull latest images (optional)
echo "📦 Pulling latest images..."
docker-compose pull

# Build services
echo "🔨 Building services..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check backend health
echo "🏥 Checking backend health..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Backend failed to start. Check logs with: docker-compose logs backend"
    exit 1
fi

# Check frontend health
echo "🏥 Checking frontend health..."
sleep 3

if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    echo "✅ Frontend is healthy!"
else
    echo "⚠️  Frontend may still be starting. Check logs with: docker-compose logs frontend"
fi

echo ""
echo "✅ SynthAIx is running!"
echo ""
echo "📍 Access points:"
echo "   Frontend:  http://localhost:8501"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📊 View logs with: docker-compose logs -f"
echo "🛑 Stop with: docker-compose down"
echo ""
