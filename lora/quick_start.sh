#!/bin/bash

# Quick Start Script for LoRA Fine-tuning
# This script helps you get started quickly

echo "=========================================="
echo "LoRA Fine-tuning Quick Start"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

echo "✓ pip found"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
echo "This may take a few minutes..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Dependencies installed successfully!"
else
    echo ""
    echo "❌ Failed to install dependencies. Please check the error messages above."
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete! 🎉"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Prepare your dataset (CSV file with ~5000 rows)"
echo "   Format: instruction,response OR question,answer OR text"
echo ""
echo "2. Validate your dataset:"
echo "   python3 prepare_dataset.py --csv_path your_data.csv --validate"
echo ""
echo "3. Start training:"
echo "   python3 train_lora.py --csv_path your_data.csv"
echo ""
echo "4. Test your model:"
echo "   python3 inference.py --interactive"
echo ""
echo "For more information, see README.md"
echo ""
