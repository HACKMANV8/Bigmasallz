# SynthAIx Examples

This directory contains example scripts demonstrating how to use SynthAIx in various scenarios.

## Available Examples

### 1. Python Client (`python_client.py`)

Basic Python client for interacting with the SynthAIx API.

**Features:**
- Schema translation
- Data generation
- Job status tracking
- Progress callbacks

**Usage:**
```bash
python examples/python_client.py
```

**Example:**
```python
from python_client import SynthAIxClient

client = SynthAIxClient()
data = client.generate_and_wait(
    "Generate user records with name and email",
    total_rows=100
)
```

### 2. Data Science Workflow (`data_science_workflow.py`)

Integration with pandas and data science workflows.

**Examples included:**
- E-commerce analytics
- Customer churn prediction
- IoT time series data
- A/B test experiments

**Usage:**
```bash
python examples/data_science_workflow.py
```

**Prerequisites:**
```bash
pip install pandas requests
```

## Quick Start

1. **Start SynthAIx:**
   ```bash
   docker-compose up -d
   ```

2. **Install dependencies:**
   ```bash
   pip install -r examples/requirements.txt
   ```

3. **Run an example:**
   ```bash
   python examples/python_client.py
   ```

## Use Cases

### E-commerce
Generate transaction data for:
- Sales analytics
- Revenue forecasting
- Customer behavior analysis
- Inventory optimization

### Machine Learning
Generate training data for:
- Classification models
- Regression models
- Time series forecasting
- Anomaly detection

### Testing
Generate test data for:
- API testing
- Database testing
- Performance testing
- Load testing

### Prototyping
Quick data generation for:
- MVP development
- Demo applications
- Proof of concepts
- Client presentations

## Custom Integration

### REST API

Direct API calls:
```python
import requests

# Translate schema
response = requests.post(
    "http://localhost:8000/api/v1/schema/translate",
    json={"prompt": "your prompt here"}
)
schema = response.json()["schema"]

# Generate data
response = requests.post(
    "http://localhost:8000/api/v1/data/generate",
    json={
        "schema": schema,
        "total_rows": 1000
    }
)
job_id = response.json()["job_id"]

# Get status
response = requests.get(
    f"http://localhost:8000/api/v1/jobs/{job_id}/status"
)
status = response.json()
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

async function generateData(prompt, rows) {
    // Translate schema
    const schemaResponse = await axios.post(
        'http://localhost:8000/api/v1/schema/translate',
        { prompt }
    );
    
    // Generate data
    const genResponse = await axios.post(
        'http://localhost:8000/api/v1/data/generate',
        {
            schema: schemaResponse.data.schema,
            total_rows: rows
        }
    );
    
    return genResponse.data.job_id;
}
```

### cURL

```bash
# Translate
SCHEMA=$(curl -s -X POST "http://localhost:8000/api/v1/schema/translate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "user records"}' | jq -c '.schema')

# Generate
JOB_ID=$(curl -s -X POST "http://localhost:8000/api/v1/data/generate" \
  -H "Content-Type: application/json" \
  -d "{\"schema\": $SCHEMA, \"total_rows\": 100}" | jq -r '.job_id')

# Status
curl "http://localhost:8000/api/v1/jobs/$JOB_ID/status" | jq
```

## Tips

### Performance Optimization

1. **Batch Processing**: Generate large datasets in batches
2. **Parallel Jobs**: Run multiple jobs concurrently
3. **Caching**: Cache schemas for repeated use
4. **Disable Dedup**: Turn off deduplication for faster generation

### Error Handling

```python
try:
    data = client.generate_and_wait(prompt, rows)
except TimeoutError:
    print("Generation took too long")
except RuntimeError as e:
    print(f"Generation failed: {e}")
except requests.exceptions.RequestException as e:
    print(f"API error: {e}")
```

### Production Considerations

1. **Rate Limiting**: Implement exponential backoff
2. **Monitoring**: Track job success rates
3. **Validation**: Validate generated data
4. **Logging**: Log all API interactions

## Contributing

Have an example to share? Submit a PR!

Requirements:
- Well-documented code
- Error handling
- Example output
- Usage instructions

## Support

- **Documentation**: See `/docs`
- **API Reference**: http://localhost:8000/docs
- **Issues**: GitHub Issues
