#!/bin/bash

# Quick Start Script for Synthetic Data Generator

set -e

echo "=================================================="
echo "  Synthetic Data Generator - Quick Start"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version detected"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -e .
echo "✓ Dependencies installed"
echo ""

# Create directories
echo "Creating required directories..."
mkdir -p temp output logs
touch temp/.gitkeep output/.gitkeep
echo "✓ Directories created"
echo ""

# Setup environment file
if [ ! -f ".env" ]; then
    echo "Setting up environment file..."
    cp .env.example .env
    echo "⚠ Please edit .env and add your GEMINI_API_KEY"
    echo ""
    echo "To get your API key, visit:"
    echo "  https://makersuite.google.com/app/apikey"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Check if API key is set
if grep -q "your_gemini_api_key_here" .env 2>/dev/null || ! grep -q "GEMINI_API_KEY=" .env 2>/dev/null; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ⚠ ACTION REQUIRED"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Please set your Gemini API key in .env:"
    echo "  1. Get API key: https://makersuite.google.com/app/apikey"
    echo "  2. Edit .env file: nano .env"
    echo "  3. Replace 'your_gemini_api_key_here' with your actual key"
    echo ""
    echo "After setting the API key, run:"
    echo "  python main.py server"
    echo ""
else
    echo "✓ Gemini API key is configured"
    echo ""
    
    # Run tests
    echo "Running quick validation..."
    python main.py version
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✅ Setup Complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Next steps:"
    echo "  1. Start the server: python main.py server"
    echo "  2. Run examples: python examples/usage_examples.py"
    echo "  3. Read docs: cat README_FULL.md"
    echo ""
    echo "For help, see SETUP.md"
    echo ""
fi

echo "=================================================="
