# Synthetic Dataset Generator - Setup Guide

## 📦 Installation Steps

### 1. Prerequisites

Ensure you have the following installed:
- Python 3.10 or higher
- pip (Python package installer)
- Git (for cloning the repository)

Check your Python version:
```bash
python --version
# or
python3 --version
```

### 2. Clone or Download the Project

```bash
git clone <repository-url>
cd HACKMAN_Project
```

### 3. Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/Mac
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
# Install the package in editable mode
pip install -e .

# Or install with all optional dependencies
pip install -e ".[dev,cloud]"
```

This will install:
- MCP (Model Context Protocol)
- Google Generative AI (Gemini)
- Pydantic for validation
- Pandas and PyArrow for data processing
- Email validator
- Tenacity for retries
- Other utilities

### 5. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

**Required Configuration:**
```bash
# Get your Gemini API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_actual_api_key_here
```

On Windows you can set the key for the current PowerShell session with:

```powershell
$env:GEMINI_API_KEY = "your_actual_api_key_here"
```

Or for classic Command Prompt:

```cmd
set GEMINI_API_KEY=your_actual_api_key_here
```

**Optional Configuration:**
```bash
# Adjust these based on your needs
GEMINI_MODEL=gemini-1.5-pro
DEFAULT_CHUNK_SIZE=1000
STORAGE_TYPE=disk
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

### 6. Create Required Directories

```bash
mkdir -p temp output logs
```

### 7. Verify Installation

Run a quick test:

```bash
# Check version
python main.py version

# Run example
python examples/usage_examples.py
```

### 8. Run Tests (Optional)

```bash
# Install dev dependencies if not already installed
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src tests/
```

## 🚀 Running the Server

### Start the MCP Server

```bash
python main.py server
```

The server will start and wait for MCP tool calls.

### Using with MCP Clients

Configure your MCP client (like Claude Desktop) to connect to this server:

**Example MCP Client Configuration:**

```json
{
  "mcpServers": {
    "synthetic-data-generator": {
      "command": "python",
      "args": ["/path/to/HACKMAN_Project/main.py", "server"],
      "env": {
        "GEMINI_API_KEY": "your-api-key"
      }
    }
  }
}
```

## 🔧 Troubleshooting

### Issue: Import Errors

**Solution:**
```bash
# Reinstall in development mode
pip install -e .

# Or install specific missing package
pip install google-generativeai
```

### Issue: Gemini API Key Error

**Solution:**
1. Verify your API key is correct in `.env`
2. Check you have API access at https://makersuite.google.com/
3. Ensure the key has not expired

### Issue: Permission Denied on temp/output directories

**Solution:**
```bash
# Fix directory permissions
chmod 755 temp output logs
```

### Issue: Rate Limit Errors

**Solution:**
Adjust in `.env`:
```bash
RATE_LIMIT_REQUESTS_PER_MINUTE=30
DEFAULT_CHUNK_SIZE=500
```

## 📚 Next Steps

1. **Read the Documentation**: Check `README_FULL.md` for detailed usage examples
2. **Try Examples**: Run `python examples/usage_examples.py`
3. **Run Tests**: `pytest tests/`
4. **Start Building**: Connect your MCP client and start generating data!

## 🆘 Getting Help

- Check the documentation: `README_FULL.md`
- Review examples: `examples/`
- Check logs: `logs/app.log`
- Open an issue on GitHub

## 🔄 Updating

To update the project:

```bash
git pull origin main
pip install -e . --upgrade
```

## 🧹 Cleaning Up

To clean temporary files:

```bash
# Remove temporary chunks
rm -rf temp/*

# Remove generated outputs
rm -rf output/*

# Remove logs
rm -rf logs/*

# Keep .gitkeep files
touch temp/.gitkeep output/.gitkeep
```

## ✅ Installation Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -e .`)
- [ ] `.env` file created with GEMINI_API_KEY
- [ ] temp, output, logs directories created
- [ ] Tests passing (`pytest`)
- [ ] Example runs successfully
- [ ] Server starts without errors

## 🎉 Success!

If all steps completed successfully, you're ready to generate synthetic datasets!

Try this:

```bash
python main.py server
```

Then use your MCP client to call tools like:
- `extract_schema` - Extract schema from natural language
- `create_job` - Create a generation job
- `generate_chunk` - Generate data chunks
- `merge_and_download` - Get your final dataset

Happy data generating! 🚀
