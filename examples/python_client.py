#!/usr/bin/env python3
"""
Example Python client for SynthAIx API.
Demonstrates how to integrate SynthAIx into your applications.
"""

import requests
import time
import json
from typing import Dict, Any, List, Optional


class SynthAIxClient:
    """Python client for SynthAIx API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the SynthAIx backend
        """
        self.base_url = base_url
        self.api_prefix = "/api/v1"
    
    def translate_schema(self, prompt: str) -> Dict[str, Any]:
        """
        Translate natural language prompt to schema.
        
        Args:
            prompt: Natural language description of desired data
            
        Returns:
            Schema translation response
            
        Example:
            >>> client = SynthAIxClient()
            >>> result = client.translate_schema("Generate user records with name and email")
            >>> print(result['schema'])
        """
        url = f"{self.base_url}{self.api_prefix}/schema/translate"
        response = requests.post(url, json={"prompt": prompt})
        response.raise_for_status()
        return response.json()
    
    def generate_data(
        self,
        schema: Dict[str, Any],
        total_rows: int,
        chunk_size: Optional[int] = None,
        enable_deduplication: bool = True
    ) -> str:
        """
        Start data generation job.
        
        Args:
            schema: Data schema
            total_rows: Number of rows to generate
            chunk_size: Rows per chunk (optional)
            enable_deduplication: Enable duplicate detection
            
        Returns:
            Job ID
            
        Example:
            >>> schema = {"fields": [{"name": "id", "type": "uuid"}]}
            >>> job_id = client.generate_data(schema, 1000)
        """
        url = f"{self.base_url}{self.api_prefix}/data/generate"
        
        payload = {
            "schema": schema,
            "total_rows": total_rows,
            "enable_deduplication": enable_deduplication
        }
        
        if chunk_size:
            payload["chunk_size"] = chunk_size
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()["job_id"]
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get job status.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status information
            
        Example:
            >>> status = client.get_job_status(job_id)
            >>> print(f"Progress: {status['progress_percentage']}%")
        """
        url = f"{self.base_url}{self.api_prefix}/jobs/{job_id}/status"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(
        self,
        job_id: str,
        poll_interval: int = 2,
        timeout: int = 300,
        callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Wait for job completion with polling.
        
        Args:
            job_id: Job identifier
            poll_interval: Seconds between status checks
            timeout: Maximum wait time in seconds
            callback: Optional callback function called on each status update
            
        Returns:
            Final job status with data
            
        Raises:
            TimeoutError: If job doesn't complete within timeout
            RuntimeError: If job fails
            
        Example:
            >>> def progress_callback(status):
            ...     print(f"Progress: {status['progress_percentage']}%")
            >>> result = client.wait_for_completion(job_id, callback=progress_callback)
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            
            if callback:
                callback(status)
            
            if status["status"] == "completed":
                return status
            elif status["status"] == "failed":
                raise RuntimeError(f"Job failed: {status.get('error', 'Unknown error')}")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Job did not complete within {timeout} seconds")
    
    def generate_and_wait(
        self,
        prompt: str,
        total_rows: int,
        callback: Optional[callable] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Complete flow: translate schema, generate data, and wait for results.
        
        Args:
            prompt: Natural language description
            total_rows: Number of rows to generate
            callback: Optional progress callback
            **kwargs: Additional arguments for generate_data
            
        Returns:
            List of generated data rows
            
        Example:
            >>> data = client.generate_and_wait(
            ...     "Generate user records with name and email",
            ...     total_rows=100
            ... )
            >>> print(f"Generated {len(data)} rows")
        """
        # Translate schema
        print("Translating schema...")
        schema_result = self.translate_schema(prompt)
        schema = schema_result["schema"]
        print(f"Schema inferred with confidence: {schema_result['confidence']:.2%}")
        
        # Start generation
        print(f"Starting generation of {total_rows} rows...")
        job_id = self.generate_data(schema, total_rows, **kwargs)
        print(f"Job created: {job_id}")
        
        # Wait for completion
        print("Waiting for completion...")
        result = self.wait_for_completion(job_id, callback=callback)
        
        print(f"✅ Completed! Generated {len(result['data'])} rows")
        return result["data"]


# Example usage
def main():
    """Example usage of the client."""
    
    # Initialize client
    client = SynthAIxClient()
    
    # Progress callback
    def show_progress(status):
        progress = status["progress_percentage"]
        completed = status["completed_rows"]
        total = status["total_rows"]
        print(f"Progress: {progress:.1f}% ({completed}/{total} rows)")
    
    # Example 1: Simple generation
    print("\n=== Example 1: Simple Generation ===")
    try:
        data = client.generate_and_wait(
            "Generate user records with username, email, and registration date",
            total_rows=50,
            callback=show_progress
        )
        
        print("\nFirst 3 records:")
        for i, row in enumerate(data[:3], 1):
            print(f"{i}. {row}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Custom schema
    print("\n\n=== Example 2: Custom Schema ===")
    custom_schema = {
        "fields": [
            {"name": "id", "type": "uuid"},
            {"name": "price", "type": "float", "constraints": {"min": 10, "max": 1000}},
            {"name": "status", "type": "string"}
        ]
    }
    
    try:
        job_id = client.generate_data(
            schema=custom_schema,
            total_rows=20,
            enable_deduplication=False
        )
        
        result = client.wait_for_completion(job_id, callback=show_progress)
        
        print(f"\nGenerated {len(result['data'])} rows")
        print(f"Metrics: {result['metrics']}")
    
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
