"""Schema extraction and validation endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.api import QuotaExceededError
from src.services.generation_service import get_generation_service
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
generation_service = get_generation_service()


class SchemaExtractRequest(BaseModel):
    """Request model for schema extraction."""
    user_input: str
    context: Optional[dict] = None
    example_data: Optional[str] = None


class SchemaExtractResponse(BaseModel):
    """Response model for schema extraction."""

    schema: dict[str, Any]
    confidence: float
    suggestions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


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
        response = generation_service.extract_schema_from_prompt(
            user_input=request.user_input,
            context=request.context,
            example_data=request.example_data,
        )

        return SchemaExtractResponse(
            schema=response.schema.model_dump(mode="json"),
            confidence=response.confidence,
            suggestions=response.suggestions,
            warnings=response.warnings,
        )

    except QuotaExceededError as exc:
        logger.warning("Schema extraction hit Gemini quota limits: %s", exc)
        headers = {}
        retry_after = getattr(exc, "retry_after", None)
        if retry_after:
            headers["Retry-After"] = str(int(retry_after))
        raise HTTPException(
            status_code=429,
            detail="Gemini quota exceeded. Please retry after the quota resets.",
            headers=headers or None,
        ) from exc
    except ValueError as exc:
        logger.warning("Schema extraction validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Schema extraction failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to extract schema") from exc


@router.post("/validate", response_model=SchemaValidateResponse)
async def validate_schema(request: SchemaValidateRequest):
    """Validate a schema object."""
    try:
        # Basic validation logic - you can enhance this
        issues = generation_service.validate_schema(request.schema)

        return SchemaValidateResponse(
            valid=len(issues) == 0,
            errors=issues,
            warnings=[],
        )

    except ValueError as exc:
        logger.warning("Schema validation input error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Schema validation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Validation error") from exc