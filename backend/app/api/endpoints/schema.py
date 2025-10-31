from fastapi import APIRouter, HTTPException, status
import logging

from app.models.schema import SchemaTranslationRequest, SchemaTranslationResponse
from app.services.schema_service import SchemaService

logger = logging.getLogger(__name__)
router = APIRouter()
schema_service = SchemaService()


@router.post(
    "/translate",
    response_model=SchemaTranslationResponse,
    status_code=status.HTTP_200_OK,
    summary="Translate natural language to schema",
    description="Converts a natural language prompt into a structured JSON schema for data generation.",
)
async def translate_schema(request: SchemaTranslationRequest):
    """
    Translate natural language prompt to structured schema.
    
    This endpoint uses LLM structured output mode to ensure valid JSON schema
    responses, eliminating hallucination issues.
    
    Args:
        request: Schema translation request with prompt
        
    Returns:
        Inferred data schema with column definitions
        
    Raises:
        HTTPException: If schema translation fails
    """
    try:
        logger.info(f"Translating schema from prompt: {request.prompt[:100]}...")
        
        result = await schema_service.translate_prompt_to_schema(
            prompt=request.prompt,
            context=request.context
        )
        
        logger.info(f"Successfully translated schema with {len(result.schema.columns)} columns")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in schema translation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error translating schema: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to translate schema: {str(e)}"
        )


@router.post(
    "/validate",
    status_code=status.HTTP_200_OK,
    summary="Validate schema",
    description="Validates a data schema for correctness and compatibility.",
)
async def validate_schema(schema: dict):
    """
    Validate a data schema.
    
    Args:
        schema: Schema to validate
        
    Returns:
        Validation result
    """
    try:
        is_valid, errors = schema_service.validate_schema(schema)
        
        return {
            "valid": is_valid,
            "errors": errors if not is_valid else None,
            "message": "Schema is valid" if is_valid else "Schema validation failed"
        }
        
    except Exception as e:
        logger.error(f"Error validating schema: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate schema: {str(e)}"
        )
