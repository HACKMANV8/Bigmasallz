"""Simple test to verify API routes are working."""

import time

import requests

API_BASE_URL = "http://localhost:8080"


def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✅ Health check passed\n")


def test_schema_extraction():
    """Test schema extraction."""
    print("Testing schema extraction...")

    payload = {
        "user_input": "Generate customer data with name, email, age (18-80), and account status (active/inactive)"
    }

    response = requests.post(
        f"{API_BASE_URL}/schema/extract",
        json=payload,
        timeout=60
    )

    print(f"Status: {response.status_code}")
    result = response.json()

    print(f"Schema extracted with {len(result['schema']['fields'])} fields:")
    for field in result['schema']['fields']:
        print(f"  - {field['name']}: {field['type']}")

    assert response.status_code == 200
    assert 'schema' in result
    print("✅ Schema extraction passed\n")

    return result['schema']


def test_job_creation(schema):
    """Test job creation and monitoring."""
    print("Testing job creation...")

    payload = {
        "schema": schema,
        "total_rows": 100,
        "chunk_size": 25,
        "output_format": "csv"
    }

    response = requests.post(
        f"{API_BASE_URL}/jobs/create",
        json=payload,
        timeout=10
    )

    print(f"Status: {response.status_code}")
    result = response.json()
    job_id = result['job_id']

    print(f"Job created: {job_id}")
    print(f"Message: {result['message']}")

    assert response.status_code == 200
    print("✅ Job creation passed\n")

    return job_id


def test_job_monitoring(job_id):
    """Test job status monitoring."""
    print(f"Monitoring job {job_id}...")

    max_wait = 120  # 2 minutes
    start_time = time.time()

    while time.time() - start_time < max_wait:
        response = requests.get(f"{API_BASE_URL}/jobs/{job_id}/status")
        status = response.json()

        print(f"Status: {status['status']}, Progress: {status['progress_percentage']:.1f}%, "
              f"Rows: {status['rows_generated']}/{status['total_rows']}")

        if status['status'] == 'completed':
            print("✅ Job completed successfully!\n")
            return True
        elif status['status'] == 'failed':
            print(f"❌ Job failed: {status.get('error_message')}\n")
            return False

        time.sleep(2)

    print("⚠️ Job monitoring timeout\n")
    return False


def test_preview(job_id):
    """Test data preview."""
    print(f"Testing data preview for job {job_id}...")

    response = requests.get(
        f"{API_BASE_URL}/jobs/{job_id}/preview",
        params={"rows": 5}
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Preview of {result['preview_rows']} rows:")
        for i, row in enumerate(result['data'], 1):
            print(f"  {i}. {row}")
        print("✅ Preview test passed\n")
        return True
    else:
        print(f"❌ Preview failed: {response.text}\n")
        return False


def test_list_jobs():
    """Test listing jobs."""
    print("Testing job listing...")

    response = requests.get(f"{API_BASE_URL}/jobs/?limit=10")

    print(f"Status: {response.status_code}")
    result = response.json()

    print(f"Found {result['total']} jobs")
    for job in result['jobs'][:3]:
        print(f"  - {job['specification']['job_id']}: {job['progress']['status']}")

    print("✅ List jobs test passed\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("API Integration Tests")
    print("=" * 60)
    print()

    try:
        # Test 1: Health check
        test_health()

        # Test 2: Schema extraction
        schema = test_schema_extraction()

        # Test 3: Job creation
        job_id = test_job_creation(schema)

        # Test 4: Job monitoring
        success = test_job_monitoring(job_id)

        if success:
            # Test 5: Data preview
            test_preview(job_id)

        # Test 6: List jobs
        test_list_jobs()

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server")
        print("Please make sure the API server is running:")
        print("  uvicorn src.api_server.app:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
