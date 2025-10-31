"""
API client utilities for communicating with the backend.
"""

import requests
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class APIClient:
    """Client for SynthAIx backend API."""
    
    def __init__(self, base_url: str = None):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL for the API (defaults to env var or localhost)
        """
        self.base_url = base_url or os.getenv(
            "BACKEND_URL", 
            "http://localhost:8000"
        )
        self.api_prefix = "/api/v1"
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        timeout: int = None,  # Changed to None for no timeout
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to the API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            timeout: Request timeout in seconds (None for no timeout)
            **kwargs: Additional request arguments
            
        Returns:
            Response JSON
        """
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise Exception(f"API request timed out after {timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection error: {str(e)}. Is the backend running?")
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def translate_schema(self, prompt: str) -> Dict[str, Any]:
        """
        Translate natural language prompt to schema.
        
        Args:
            prompt: Natural language description
            
        Returns:
            Schema translation response
        """
        return self._make_request(
            "POST",
            "/schema/translate",
            timeout=None,  # No timeout
            json={"prompt": prompt}
        )
    
    def generate_data(
        self,
        schema: Dict[str, Any],
        total_rows: int,
        chunk_size: Optional[int] = None,
        enable_deduplication: bool = True
    ) -> Dict[str, Any]:
        """
        Start data generation job.
        
        Args:
            schema: Data schema
            total_rows: Total rows to generate
            chunk_size: Rows per chunk (optional)
            enable_deduplication: Enable duplicate detection
            
        Returns:
            Job creation response
        """
        payload = {
            "schema": schema,
            "total_rows": total_rows,
            "enable_deduplication": enable_deduplication
        }
        
        if chunk_size:
            payload["chunk_size"] = chunk_size
        
        return self._make_request(
            "POST",
            "/data/generate",
            json=payload
        )
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status response
        """
        return self._make_request(
            "GET",
            f"/jobs/{job_id}/status",
            timeout=None  # No timeout for status checks
        )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check API health.
        
        Returns:
            Health check response
        """
        return self._make_request(
            "GET",
            "/health",
            timeout=None  # No timeout
        )
