"""
Example test suite for the backend.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test health endpoint returns 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestSchemaTranslation:
    """Test schema translation endpoint."""
    
    def test_translate_schema_success(self):
        """Test successful schema translation."""
        response = client.post(
            "/api/v1/schema/translate",
            json={"prompt": "Generate user records with name and email"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "schema" in data
        assert "fields" in data["schema"]
        assert len(data["schema"]["fields"]) > 0
    
    def test_translate_schema_empty_prompt(self):
        """Test schema translation with empty prompt."""
        response = client.post(
            "/api/v1/schema/translate",
            json={"prompt": ""}
        )
        # Should still work but might have low confidence
        assert response.status_code in [200, 422]


class TestDataGeneration:
    """Test data generation endpoint."""
    
    def test_generate_data_creates_job(self):
        """Test that data generation creates a job."""
        schema = {
            "fields": [
                {"name": "id", "type": "uuid"},
                {"name": "name", "type": "string"}
            ]
        }
        
        response = client.post(
            "/api/v1/data/generate",
            json={
                "schema": schema,
                "total_rows": 10,
                "enable_deduplication": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
    
    def test_generate_data_invalid_schema(self):
        """Test data generation with invalid schema."""
        response = client.post(
            "/api/v1/data/generate",
            json={
                "schema": {"fields": []},  # Empty fields
                "total_rows": 10
            }
        )
        assert response.status_code == 422


class TestJobStatus:
    """Test job status endpoint."""
    
    def test_get_nonexistent_job(self):
        """Test getting status of non-existent job."""
        response = client.get("/api/v1/jobs/fake-job-id/status")
        assert response.status_code == 404
    
    def test_get_job_status_after_creation(self):
        """Test getting status immediately after job creation."""
        # Create job first
        schema = {
            "fields": [
                {"name": "id", "type": "uuid"}
            ]
        }
        
        create_response = client.post(
            "/api/v1/data/generate",
            json={
                "schema": schema,
                "total_rows": 10,
                "enable_deduplication": False
            }
        )
        
        job_id = create_response.json()["job_id"]
        
        # Get status
        status_response = client.get(f"/api/v1/jobs/{job_id}/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert status_data["status"] in ["pending", "in_progress", "completed"]


@pytest.fixture
def sample_schema():
    """Sample schema for testing."""
    return {
        "fields": [
            {
                "name": "transaction_id",
                "type": "uuid",
                "description": "Unique transaction ID"
            },
            {
                "name": "amount",
                "type": "float",
                "description": "Transaction amount",
                "constraints": {"min": 0, "max": 10000}
            },
            {
                "name": "date",
                "type": "date",
                "description": "Transaction date"
            }
        ]
    }


def test_integration_flow(sample_schema):
    """Test complete flow from schema to generation."""
    # 1. Translate schema
    translate_response = client.post(
        "/api/v1/schema/translate",
        json={"prompt": "Generate financial transactions"}
    )
    assert translate_response.status_code == 200
    
    # 2. Generate data
    gen_response = client.post(
        "/api/v1/data/generate",
        json={
            "schema": sample_schema,
            "total_rows": 5,
            "enable_deduplication": False
        }
    )
    assert gen_response.status_code == 200
    job_id = gen_response.json()["job_id"]
    
    # 3. Check status
    status_response = client.get(f"/api/v1/jobs/{job_id}/status")
    assert status_response.status_code == 200
