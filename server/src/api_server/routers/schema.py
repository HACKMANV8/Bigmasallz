"""Schema extraction and validation endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.api.gemini_client import get_gemini_client
from src.core.models import SchemaExtractionRequest
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class SchemaExtractRequest(BaseModel):
    """Request model for schema extraction."""
    user_input: str
    context: dict | None = None
    example_data: str | None = None


class SchemaExtractResponse(BaseModel):
    """Response model for schema extraction."""
    schema: dict
    metadata: dict = Field(default_factory=dict)


class SchemaValidateRequest(BaseModel):
    """Request model for schema validation."""
    schema: dict


class SchemaValidateResponse(BaseModel):
    """Response model for schema validation."""
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


@router.post("/extract", response_model=SchemaExtractResponse)
async def extract_schema(request: SchemaExtractRequest):
    """Extract structured schema from natural language description."""
    try:
        gemini_client = get_gemini_client()

        # Create MCP-style request
        extraction_request = SchemaExtractionRequest(
            user_input=request.user_input,
            context=request.context or {},
            example_data=request.example_data
        )

        # Call Gemini client to extract schema (synchronous call - not async)
        schema_result = gemini_client.extract_schema(extraction_request)

        # Convert the schema to dict format
        schema_dict = schema_result.schema.model_dump(mode="json")

        return SchemaExtractResponse(
            schema=schema_dict,
            metadata={
                "extracted_at": datetime.utcnow().isoformat() + "Z",
                "source": "gemini",
                "confidence": schema_result.confidence,
                "suggestions": schema_result.suggestions,
                "warnings": schema_result.warnings
            }
        )

    except Exception as e:
        logger.error(f"Schema extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract schema: {str(e)}")


@router.post("/validate", response_model=SchemaValidateResponse)
async def validate_schema(request: SchemaValidateRequest):
    """Validate a schema object."""
    try:
        # Basic validation logic - you can enhance this
        errors = []
        warnings = []

        schema = request.schema

        # Check required fields
        if not isinstance(schema, dict):
            errors.append("Schema must be an object")

        if "fields" not in schema:
            errors.append("Schema must contain 'fields' property")

        if "fields" in schema and not isinstance(schema["fields"], list):
            errors.append("Schema 'fields' must be an array")

        # Validate individual fields
        if "fields" in schema and isinstance(schema["fields"], list):
            for i, field in enumerate(schema["fields"]):
                if not isinstance(field, dict):
                    errors.append(f"Field {i} must be an object")
                    continue

                if "name" not in field:
                    errors.append(f"Field {i} missing required 'name' property")

                if "type" not in field:
                    errors.append(f"Field {i} missing required 'type' property")

        return SchemaValidateResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")
