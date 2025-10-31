"""Example usage of the Synthetic Data Generator."""

import asyncio
from uuid import UUID

# Mock example - in real usage, these would be MCP tool calls
async def example_sales_data_generation():
    """Example: Generate sales dataset."""
    
    print("=== Example 1: Sales Data Generation ===\n")
    
    # Step 1: Extract schema from natural language
    print("Step 1: Extracting schema...")
    schema_request = {
        "user_input": (
            "Generate 10,000 rows of sales data with the following fields: "
            "customer_name (string), customer_email (email, unique), "
            "product_name (string), product_category (enum: Electronics, Clothing, Food, Books), "
            "quantity (integer, 1-10), unit_price (float, 10-1000), "
            "total_amount (float, derived from quantity * unit_price), "
            "order_date (date), status (enum: pending, shipped, delivered)"
        )
    }
    
    # In real usage: extract_schema(schema_request)
    print(f"  Input: {schema_request['user_input'][:80]}...")
    print("  ✓ Schema extracted successfully\n")
    
    # Step 2: Create job
    print("Step 2: Creating generation job...")
    job_spec = {
        "total_rows": 10000,
        "chunk_size": 1000,
        "output_format": "csv",
        "uniqueness_fields": ["customer_email"]
    }
    
    # In real usage: create_job(schema, **job_spec)
    print(f"  Total rows: {job_spec['total_rows']}")
    print(f"  Chunk size: {job_spec['chunk_size']}")
    print(f"  Format: {job_spec['output_format']}")
    print("  ✓ Job created with ID: abc-123-def\n")
    
    # Step 3: Generate chunks
    print("Step 3: Generating data chunks...")
    total_chunks = job_spec['total_rows'] // job_spec['chunk_size']
    
    for i in range(total_chunks):
        # In real usage: generate_chunk(job_id, chunk_id=i)
        progress = ((i + 1) / total_chunks) * 100
        print(f"  Chunk {i+1}/{total_chunks} completed ({progress:.1f}%)")
        await asyncio.sleep(0.1)  # Simulate processing time
    
    print("  ✓ All chunks generated\n")
    
    # Step 4: Merge and download
    print("Step 4: Merging chunks and preparing download...")
    # In real usage: merge_and_download(job_id)
    print("  ✓ Dataset ready: ./output/sales_data_10000.csv")
    print("  File size: 2.5 MB")
    print("  Checksum: abc123def456...\n")


async def example_user_profile_generation():
    """Example: Generate user profile dataset with constraints."""
    
    print("\n=== Example 2: User Profile Generation ===\n")
    
    print("Step 1: Defining schema with constraints...")
    schema = {
        "fields": [
            {
                "name": "user_id",
                "type": "uuid",
                "constraints": {"unique": True, "nullable": False}
            },
            {
                "name": "username",
                "type": "string",
                "constraints": {"unique": True, "min_length": 3, "max_length": 20}
            },
            {
                "name": "email",
                "type": "email",
                "constraints": {"unique": True, "nullable": False}
            },
            {
                "name": "age",
                "type": "integer",
                "constraints": {"min_value": 18, "max_value": 80}
            },
            {
                "name": "country",
                "type": "enum",
                "constraints": {"enum_values": ["USA", "UK", "Canada", "Australia", "India"]}
            },
            {
                "name": "registration_date",
                "type": "datetime",
                "constraints": {"nullable": False}
            },
            {
                "name": "is_active",
                "type": "boolean",
                "constraints": {"default": True}
            }
        ]
    }
    
    print("  ✓ Schema defined with 7 fields")
    print("  ✓ Uniqueness constraints: user_id, username, email\n")
    
    print("Step 2: Creating job with smaller chunks...")
    job_spec = {
        "total_rows": 5000,
        "chunk_size": 500,
        "output_format": "json",
        "uniqueness_fields": ["user_id", "username", "email"],
        "seed": 42  # For reproducibility
    }
    
    print(f"  Rows: {job_spec['total_rows']}")
    print(f"  Chunks: {job_spec['total_rows'] // job_spec['chunk_size']}")
    print("  ✓ Job created\n")
    
    print("Step 3: Validating schema...")
    # In real usage: validate_schema(schema)
    print("  ✓ Schema validation passed\n")
    
    print("Step 4: Starting generation...")
    print("  ✓ Generation complete\n")


async def example_job_control():
    """Example: Job control operations."""
    
    print("\n=== Example 3: Job Control Operations ===\n")
    
    print("Scenario: Long-running job that needs to be paused\n")
    
    print("Starting job...")
    # Generate a few chunks
    for i in range(3):
        print(f"  Chunk {i+1} generated")
        await asyncio.sleep(0.1)
    
    print("\nUser requests pause...")
    # In real usage: control_job(job_id, action="pause")
    print("  ✓ Job paused at chunk 3\n")
    
    print("Checking job progress...")
    # In real usage: get_job_progress(job_id)
    print("  Status: PAUSED")
    print("  Progress: 3/10 chunks (30%)")
    print("  Rows: 3000/10000\n")
    
    await asyncio.sleep(0.5)
    
    print("Resuming job...")
    # In real usage: control_job(job_id, action="resume")
    print("  ✓ Job resumed\n")
    
    print("Continuing generation...")
    for i in range(3, 10):
        print(f"  Chunk {i+1} generated")
        await asyncio.sleep(0.1)
    
    print("\n  ✓ Job completed successfully\n")


async def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("  SYNTHETIC DATA GENERATOR - USAGE EXAMPLES")
    print("="*60 + "\n")
    
    await example_sales_data_generation()
    await example_user_profile_generation()
    await example_job_control()
    
    print("="*60)
    print("  Examples completed!")
    print("  For real usage, connect to the MCP server and use the tools.")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
