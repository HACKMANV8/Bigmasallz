# Synthetic Dataset Generator 🚀

A powerful synthetic dataset generation tool using LLMs (Large Language Models) and MCP (Model Context Protocol) that generates reasonably sized datasets with Google's Gemini API.

## 🌟 Features

- **Natural Language Schema Extraction**: Describe your dataset in plain English and get a structured schema
- **Chunked Generation**: Generate large datasets (10K+ rows) in manageable chunks
- **Multiple Output Formats**: Export to CSV, JSON, or Parquet
- **Resumable Jobs**: Pause, resume, or retry generation jobs
- **Smart Validation**: Built-in field type validation and constraint checking
- **Uniqueness Constraints**: Ensure fields have unique values across the entire dataset
- **Progress Tracking**: Real-time progress updates and estimated completion time
- **Flexible Storage**: In-memory, disk, or cloud storage options

## 📋 Project Flow

### 1. **User Input and Schema Parsing**
   - User specifies data requirements in natural language
   - LLM extracts structured schema with field types, constraints, and sample values

### 2. **Dataset Specification and Job Setup**
   - Confirm/edit schema with user
   - Set parameters: row count, file format, uniqueness constraints
   - Submit generation job to MCP server

### 3. **Chunked Data Generation**
   - Generate data in batches (500-1000 rows per chunk)
   - Store chunks in temporary storage
   - Track progress and allow pause/resume/abort
   - Maintain uniqueness across chunks

### 4. **Streaming or Batched Download**
   - Merge chunks when complete
   - Provide downloadable file with checksum
   - Support resumption and modifications

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Google Gemini API key

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd HACKMAN_Project
```

2. **Install dependencies**:
```bash
pip install -e .
```

3. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

4. **Create required directories**:
```bash
mkdir -p temp output logs
```

### Running the Server

Start the MCP server:

```bash
python main.py server
```

Or use the command-line script:

```bash
synthetic-data-gen server
```

## 📖 Usage Examples

### Example 1: Generate Sales Data

```python
# 1. Extract Schema from Natural Language
extract_schema(
    user_input="Generate 10,000 rows of sales data with customer name, product, amount (between $10-$1000), and date fields"
)

# Response will include a structured schema with field definitions

# 2. Create Job
create_job(
    schema={
        "fields": [
            {"name": "customer_name", "type": "string"},
            {"name": "product", "type": "string"},
            {"name": "amount", "type": "float", "constraints": {"min_value": 10, "max_value": 1000}},
            {"name": "date", "type": "date"}
        ]
    },
    total_rows=10000,
    chunk_size=1000,
    output_format="csv"
)

# 3. Generate Chunks (repeat for each chunk)
generate_chunk(job_id="<job-id>", chunk_id=0)
generate_chunk(job_id="<job-id>", chunk_id=1)
# ... continue until all chunks are generated

# 4. Get Progress
get_job_progress(job_id="<job-id>")

# 5. Merge and Download
merge_and_download(job_id="<job-id>")
```

### Example 2: Generate User Data with Uniqueness

```python
# Create job with unique email field
create_job(
    schema={
        "fields": [
            {"name": "user_id", "type": "uuid"},
            {"name": "email", "type": "email", "constraints": {"unique": true}},
            {"name": "name", "type": "string"},
            {"name": "age", "type": "integer", "constraints": {"min_value": 18, "max_value": 80}}
        ]
    },
    total_rows=5000,
    uniqueness_fields=["email"],
    output_format="json"
)
```

### Example 3: Pause and Resume Job

```python
# Start generating
generate_chunk(job_id="<job-id>", chunk_id=0)

# Pause the job
control_job(job_id="<job-id>", action="pause", reason="User requested pause")

# Resume later
control_job(job_id="<job-id>", action="resume")

# Continue generating
generate_chunk(job_id="<job-id>", chunk_id=1)
```

## 🛠️ Configuration

Edit `.env` file to configure:

```bash
# Gemini API
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-pro

# Storage
STORAGE_TYPE=disk  # Options: memory, disk, cloud
TEMP_STORAGE_PATH=./temp
OUTPUT_STORAGE_PATH=./output

# Generation
DEFAULT_CHUNK_SIZE=1000
MAX_CHUNK_SIZE=5000
DEFAULT_OUTPUT_FORMAT=csv

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

## 📁 Project Structure

```
HACKMAN_Project/
├── src/
│   ├── api/                 # API clients (Gemini)
│   │   ├── __init__.py
│   │   └── gemini_client.py
│   ├── core/                # Core models and logic
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── job_manager.py
│   ├── mcp_server/          # MCP server implementation
│   │   ├── __init__.py
│   │   └── server.py
│   ├── storage/             # Storage handlers
│   │   ├── __init__.py
│   │   └── handlers.py
│   ├── utils/               # Utilities
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── validators.py
│   ├── __init__.py
│   └── config.py            # Configuration management
├── tests/                   # Test files
├── temp/                    # Temporary chunk storage
├── output/                  # Final dataset output
├── logs/                    # Application logs
├── main.py                  # Entry point
├── pyproject.toml           # Project dependencies
├── .env.example             # Environment template
├── .gitignore
└── README.md
```

## 🔧 MCP Tools

The server exposes the following MCP tools:

| Tool | Description |
|------|-------------|
| `extract_schema` | Extract structured schema from natural language |
| `create_job` | Create a new data generation job |
| `generate_chunk` | Generate a single chunk of data |
| `get_job_progress` | Get current job progress and status |
| `control_job` | Pause, resume, cancel, or retry a job |
| `list_jobs` | List all jobs with optional filtering |
| `merge_and_download` | Merge chunks and prepare dataset for download |
| `validate_schema` | Validate schema for correctness |

## 🎯 Supported Field Types

- `string` - Text data
- `integer` - Whole numbers
- `float` - Decimal numbers
- `boolean` - True/False values
- `date` - Date (YYYY-MM-DD)
- `datetime` - Date and time
- `email` - Email addresses
- `phone` - Phone numbers
- `uuid` - Universally unique identifiers
- `enum` - Predefined set of values
- `json` - JSON objects
- `array` - Lists of values

## 🔒 Field Constraints

- `unique` - Ensure field has unique values
- `nullable` - Allow null values
- `min_value` / `max_value` - Numeric range
- `min_length` / `max_length` - String/array length
- `pattern` - Regex pattern matching
- `enum_values` - Allowed values for enum type
- `format` - Format specification

## 📊 Output Formats

- **CSV** - Comma-separated values (default)
- **JSON** - JSON array of objects
- **Parquet** - Columnar format (requires pandas & pyarrow)

## 🧪 Testing

Run tests:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=src tests/
```

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Make sure all dependencies are installed:
   ```bash
   pip install -e .
   ```

2. **Gemini API errors**: Check your API key and rate limits

3. **Memory issues with large datasets**: Use disk storage instead of memory:
   ```bash
   STORAGE_TYPE=disk
   ```

4. **Chunk generation timeout**: Reduce chunk size:
   ```bash
   DEFAULT_CHUNK_SIZE=500
   ```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Google Gemini API for LLM capabilities
- Model Context Protocol (MCP) for tool integration
- The open-source community

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Made with ❤️ by the HACKMAN Team**
