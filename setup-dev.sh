#!/bin/bash

# SynthAIx Development Setup Script

set -e

echo "🔧 Setting up SynthAIx development environment..."

# Create virtual environment for backend
echo "📦 Setting up backend..."
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install pytest black pylint
deactivate
cd ..

# Create virtual environment for frontend
echo "📦 Setting up frontend..."
cd frontend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install pytest
deactivate
cd ..

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/chroma_db
mkdir -p logs

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OPENAI_API_KEY"
echo "2. Start Redis: redis-server"
echo "3. Start backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "4. Start frontend: cd frontend && source venv/bin/activate && streamlit run app.py"
echo ""
