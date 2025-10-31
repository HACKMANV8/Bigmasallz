"""FastMCP Server for GitHub Copilot to generate synthetic CSV datasets.

This server provides tools that allow GitHub Copilot (as the MCP client) to:
1. Extract schema from natural language descriptions
2. Generate CSV datasets directly using Copilot's models

The server acts as a bridge, providing context and structure for Copilot
to generate high-quality synthetic data.
"""

import csv
import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("synthetic-data-copilot")


@mcp.tool()
def extract_schema_from_description(
    description: str,
    num_rows: int = 100,
    example_data: str | None = None,
) -> str:
    """Extract a CSV schema from a natural language description.
    
    This tool helps structure the data generation request by providing:
    - Field names and types
    - Constraints and relationships
    - Sample values for guidance
    - Generation instructions
    
    Args:
        description: Natural language description of the dataset to generate.
                    Example: "Generate car dealership inventory with make, model, year, price"
        num_rows: Number of rows to generate (default: 100)
        example_data: Optional example data to guide the schema (CSV format or JSON)
    
    Returns:
        A JSON schema that describes the structure for CSV generation, including:
        - fields: List of field definitions with name, type, description, constraints
        - relationships: How fields relate to each other
        - generation_hints: Tips for generating realistic data
        - csv_headers: The exact column names for the CSV file
    """
    
    schema_template = {
        "description": description,
        "num_rows": num_rows,
        "output_format": "csv",
        "fields": [],
        "relationships": [],
        "generation_hints": [],
        "csv_headers": []
    }
    
    # Add example data context if provided
    context = f"""
Dataset Description: {description}
Target Rows: {num_rows}

TASK: Analyze this description and create a detailed schema for CSV generation.

OUTPUT REQUIREMENTS:
1. Identify all fields mentioned or implied in the description
2. For each field, specify:
   - name: Field name (use snake_case)
   - type: Data type (string, integer, float, boolean, date, email, phone, etc.)
   - description: What this field represents
   - constraints: Any rules (min, max, unique, required, format, enum values)
   - sample_values: 3-5 example values that show the expected format/range
   - generation_hint: Specific instructions for generating this field

3. Identify relationships between fields (e.g., "sale_price must be <= msrp")
4. Provide generation hints for creating realistic, coherent data
5. List the exact CSV column headers in order

IMPORTANT: The schema should enable generating diverse, realistic data that matches
real-world patterns. Include enough detail that an LLM can generate the data without
additional context.
"""
    
    if example_data:
        context += f"\n\nEXAMPLE DATA FOR REFERENCE:\n{example_data}\n"
    
    return json.dumps({
        "status": "schema_extraction_ready",
        "task": context,
        "template": schema_template,
        "next_step": "Populate the template with detailed field definitions based on the description"
    }, indent=2)


@mcp.tool()
def generate_csv_dataset(
    schema_json: str,
    output_path: str | None = None,
) -> str:
    """Generate a CSV dataset based on the provided schema.
    
    This tool coordinates the generation of synthetic CSV data. It takes a complete
    schema (from extract_schema_from_description) and guides the generation process.
    
    Args:
        schema_json: JSON string containing the complete schema with:
            - fields: List of field definitions
            - num_rows: Number of rows to generate
            - csv_headers: Column names
            - generation_hints: Instructions for realistic data
            - relationships: Field constraints and dependencies
        output_path: Optional path where to save the CSV file
                    (default: output/<random_id>.csv)
    
    Returns:
        Instructions and context for generating the CSV data, including:
        - The complete schema
        - Generation strategy
        - Validation requirements
        - Output format specification
    """
    
    try:
        schema = json.loads(schema_json)
    except json.JSONDecodeError as e:
        return json.dumps({
            "status": "error",
            "message": f"Invalid JSON schema: {str(e)}"
        }, indent=2)
    
    # Determine output path
    if not output_path:
        import uuid
        output_dir = Path("/home/dikshith/Hackman-Main/Bigmasallz/server/output")
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / f"{uuid.uuid4()}.csv")
    
    num_rows = schema.get("num_rows", 100)
    fields = schema.get("fields", [])
    headers = schema.get("csv_headers", [field.get("name") for field in fields])
    
    # Create generation instructions
    generation_guide = f"""
DATASET GENERATION TASK
=======================

Description: {schema.get('description', 'Generate synthetic dataset')}
Rows to Generate: {num_rows}
Output Path: {output_path}

CSV STRUCTURE:
{', '.join(headers)}

FIELD SPECIFICATIONS:
"""
    
    for i, field in enumerate(fields, 1):
        generation_guide += f"""
{i}. {field.get('name')}
   Type: {field.get('type')}
   Description: {field.get('description', 'N/A')}
   Constraints: {json.dumps(field.get('constraints', {}))}
   Sample Values: {', '.join(str(v) for v in field.get('sample_values', []))}
   Generation Hint: {field.get('generation_hint', 'Generate realistic values')}
"""
    
    if schema.get('relationships'):
        generation_guide += "\nRELATIONSHIPS AND CONSTRAINTS:\n"
        for rel in schema['relationships']:
            generation_guide += f"- {rel}\n"
    
    if schema.get('generation_hints'):
        generation_guide += "\nGENERATION HINTS:\n"
        for hint in schema['generation_hints']:
            generation_guide += f"- {hint}\n"
    
    generation_guide += f"""

GENERATION STRATEGY:
1. Generate {num_rows} rows of data following all field specifications
2. Ensure data is realistic and follows real-world patterns
3. Respect all constraints and relationships between fields
4. Maintain consistency within each row
5. Create diversity across rows while staying within realistic bounds

OUTPUT FORMAT:
- Standard CSV with comma delimiter
- Include header row with column names: {', '.join(headers)}
- Quote fields containing commas or newlines
- Use proper CSV escaping for special characters

VALIDATION REQUIREMENTS:
- All required fields must have values
- Unique fields must not have duplicates
- Numeric fields must be within specified ranges
- Dates must be in valid format
- Relationships between fields must be maintained

TASK: Generate the complete CSV dataset now with {num_rows} rows.
Save it to: {output_path}

Generate the data starting with the header row, then {num_rows} data rows.
Make it realistic, diverse, and production-ready.
"""
    
    return json.dumps({
        "status": "generation_ready",
        "output_path": output_path,
        "num_rows": num_rows,
        "headers": headers,
        "generation_guide": generation_guide,
        "schema": schema,
        "next_step": "Generate the CSV content and save to the output path"
    }, indent=2)


@mcp.tool()
def save_csv_content(
    csv_content: str,
    output_path: str,
    validate: bool = True,
) -> str:
    """Save generated CSV content to a file and optionally validate it.
    
    Args:
        csv_content: The complete CSV content including header and data rows
        output_path: Path where to save the CSV file
        validate: Whether to validate the CSV structure (default: True)
    
    Returns:
        Confirmation with file details including row count, size, and validation results
    """
    
    try:
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the CSV content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # Validate if requested
        validation_results = {}
        if validate:
            with open(output_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                if len(rows) < 2:
                    validation_results["error"] = "CSV must have at least header and one data row"
                else:
                    headers = rows[0]
                    data_rows = rows[1:]
                    
                    validation_results = {
                        "valid": True,
                        "header_count": len(headers),
                        "data_row_count": len(data_rows),
                        "columns": headers,
                        "sample_first_row": data_rows[0] if data_rows else [],
                        "sample_last_row": data_rows[-1] if data_rows else [],
                    }
                    
                    # Check for consistent column counts
                    inconsistent_rows = []
                    for i, row in enumerate(data_rows, 1):
                        if len(row) != len(headers):
                            inconsistent_rows.append(i)
                    
                    if inconsistent_rows:
                        validation_results["warnings"] = [
                            f"Rows with inconsistent column count: {inconsistent_rows[:10]}"
                        ]
        
        # Get file stats
        file_size = output_file.stat().st_size
        
        return json.dumps({
            "status": "success",
            "output_path": str(output_file),
            "file_size_bytes": file_size,
            "file_size_kb": round(file_size / 1024, 2),
            "validation": validation_results,
            "message": f"CSV dataset saved successfully to {output_file}"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to save CSV: {str(e)}"
        }, indent=2)


@mcp.tool()
def get_example_schemas() -> str:
    """Get example schemas for common dataset types.
    
    Returns examples of complete schemas for:
    - Car dealership inventory
    - E-commerce customers
    - Employee records
    - Financial transactions
    - Healthcare patients
    
    Use these as templates or reference when creating your own schemas.
    """
    
    examples = {
        "car_dealership": {
            "description": "Car dealership inventory with vehicle details",
            "num_rows": 100,
            "csv_headers": ["car_id", "vin", "make", "model", "year", "body_style", 
                           "mileage", "fuel_type", "transmission", "msrp", "sale_price", 
                           "is_new", "listing_date", "features"],
            "fields": [
                {
                    "name": "car_id",
                    "type": "uuid",
                    "description": "Unique identifier for the car",
                    "constraints": {"unique": True, "required": True},
                    "sample_values": ["a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"],
                    "generation_hint": "Generate a valid UUID v4"
                },
                {
                    "name": "make",
                    "type": "string",
                    "description": "Car manufacturer",
                    "constraints": {"required": True},
                    "sample_values": ["Toyota", "Honda", "Ford", "Tesla", "BMW"],
                    "generation_hint": "Use popular car brands, mix of luxury and mainstream"
                },
                {
                    "name": "year",
                    "type": "integer",
                    "description": "Model year",
                    "constraints": {"min": 2015, "max": 2025, "required": True},
                    "sample_values": [2023, 2024, 2022],
                    "generation_hint": "Recent years should be more common"
                }
            ],
            "relationships": [
                "sale_price should be less than or equal to msrp",
                "is_new should be True if year >= 2024 and mileage < 100",
                "listing_date should be within the last 2 years"
            ],
            "generation_hints": [
                "Mix of new and used vehicles",
                "Realistic pricing based on make and year",
                "Features should match the vehicle type and price range"
            ]
        }
    }
    
    return json.dumps(examples, indent=2)


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
