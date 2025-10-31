# Streamlit Frontend

## Description

Production-grade Streamlit frontend for SynthAIx synthetic data generator.

## Features

- 🎨 Modern, clean UI
- 📱 Responsive design
- 🚀 Real-time progress tracking
- 📊 Data preview
- 💾 CSV/JSON download
- ⚡ Fast and lightweight

## Installation

```bash
pip install -r requirements.txt
```

## Running Locally

```bash
# Make sure backend is running on port 8000
streamlit run app.py
```

The app will be available at http://localhost:8501

## Configuration

Create `.streamlit/secrets.toml` for custom API URL:

```toml
API_URL = "http://localhost:8000"
```

## Docker

```bash
docker build -t synthaix-frontend .
docker run -p 8501:8501 synthaix-frontend
```

## Environment Variables

- `API_URL` - Backend API URL (default: http://localhost:8000)

## Usage

1. **Describe**: Enter natural language description of your dataset
2. **Edit**: Review and modify the generated schema
3. **Configure**: Set generation parameters (rows, workers, etc.)
4. **Generate**: Watch real-time progress and download results

## Advantages over Next.js

- ✅ No npm/node dependencies
- ✅ Pure Python stack
- ✅ Faster development
- ✅ Smaller Docker image
- ✅ Better for data science workflows
- ✅ Built-in data visualization
