#!/usr/bin/env python3
"""Quick test script to verify SynthAIx is working"""

import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Health: {resp.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_schema_translation():
    """Test schema translation"""
    print("\n📋 Testing schema translation...")
    try:
        resp = requests.post(
            f"{BASE_URL}/schema/translate",
            json={"prompt": "user data with name and age"},
            timeout=60
        )
        schema = resp.json()
        print(f"✅ Schema: {json.dumps(schema['schema'], indent=2)}")
        return schema['schema']
    except Exception as e:
        print(f"❌ Schema translation failed: {e}")
        return None

def test_data_generation(schema):
    """Test data generation with small dataset"""
    print("\n🤖 Testing data generation (20 rows)...")
    try:
        # Start generation
        resp = requests.post(
            f"{BASE_URL}/data/generate",
            json={
                "schema": schema,
                "total_rows": 20,
                "chunk_size": 10,
                "enable_deduplication": False
            },
            timeout=300
        )
        job_data = resp.json()
        job_id = job_data['job_id']
        print(f"📝 Job created: {job_id}")
        
        # Poll for completion
        print("⏳ Waiting for completion...")
        for i in range(60):  # Max 2 minutes
            time.sleep(2)
            status_resp = requests.get(
                f"{BASE_URL}/jobs/{job_id}/status",
                timeout=10
            )
            status = status_resp.json()
            
            progress = status.get('progress', 0)
            print(f"   Progress: {progress:.1f}% ({status.get('completed_chunks', 0)}/{status.get('total_chunks', 0)} chunks)")
            
            if status['status'] == 'completed':
                print(f"✅ Generation completed!")
                print(f"   Total rows: {len(status.get('data', []))}")
                print(f"   Sample: {json.dumps(status['data'][:2], indent=2)}")
                return True
            elif status['status'] == 'failed':
                print(f"❌ Generation failed: {status.get('error')}")
                return False
        
        print("❌ Timeout waiting for completion")
        return False
        
    except Exception as e:
        print(f"❌ Data generation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SynthAIx Quick Test\n" + "="*50)
    
    # Run tests
    if not test_health():
        print("\n❌ Backend is not running!")
        exit(1)
    
    schema = test_schema_translation()
    if not schema:
        print("\n❌ Schema translation failed!")
        exit(1)
    
    if test_data_generation(schema):
        print("\n" + "="*50)
        print("🎉 All tests passed! SynthAIx is working!")
    else:
        print("\n" + "="*50)
        print("❌ Data generation test failed")
        exit(1)
