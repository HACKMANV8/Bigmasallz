import logging
from typing import Optional
import json

from app.models.schema import (
    SchemaTranslationRequest,
    SchemaTranslationResponse,
    DataSchema,
    ColumnSchema,
    ColumnType,
)
from app.utils.llm_client import LLMClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class SchemaService:
    """Service for schema translation and validation."""

    def __init__(self):
        self.llm_client = LLMClient()

    async def translate_prompt_to_schema(
        self, prompt: str, context: Optional[str] = None
    ) -> SchemaTranslationResponse:
        """
        Translate natural language prompt to structured schema.

        Uses LLM structured output mode to guarantee valid JSON schema.

        Args:
            prompt: Natural language description
            context: Additional context

        Returns:
            SchemaTranslationResponse with inferred schema
        """
        try:
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(prompt, context)

            logger.info("Calling LLM for schema translation with structured output")

            # Use structured output mode
            response = await self.llm_client.generate_structured_output(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema=self._get_output_schema(),
                model=settings.SCHEMA_MODEL,
            )

            # Parse response
            schema_data = response.get("schema", {})
            inferred_count = response.get("inferred_count")

            # Convert to DataSchema
            columns = [
                ColumnSchema(
                    name=col["name"],
                    type=ColumnType(col["type"]),
                    description=col["description"],
                    constraints=col.get("constraints"),
                    examples=col.get("examples"),
                )
                for col in schema_data.get("columns", [])
            ]

            schema = DataSchema(
                columns=columns, metadata=schema_data.get("metadata")
            )

            logger.info(f"Successfully translated schema with {len(columns)} columns")

            return SchemaTranslationResponse(
                schema=schema,
                inferred_count=inferred_count,
                confidence=response.get("confidence", 1.0),
            )

        except Exception as e:
            logger.error(f"Error translating schema: {str(e)}", exc_info=True)
            raise

    def validate_schema(self, schema: dict) -> tuple[bool, Optional[list]]:
        """
        Validate a schema for correctness.

        Args:
            schema: Schema dictionary to validate

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        # Check required fields
        if "columns" not in schema:
            errors.append("Schema must have 'columns' field")
            return False, errors

        columns = schema.get("columns", [])
        if not columns:
            errors.append("Schema must have at least one column")
            return False, errors

        # Validate each column
        for idx, col in enumerate(columns):
            if "name" not in col:
                errors.append(f"Column {idx} missing 'name' field")
            if "type" not in col:
                errors.append(f"Column {idx} missing 'type' field")
            else:
                try:
                    ColumnType(col["type"])
                except ValueError:
                    errors.append(
                        f"Column {idx} has invalid type: {col['type']}"
                    )

        return len(errors) == 0, errors if errors else None

    def _build_system_prompt(self) -> str:
        """Build system prompt for schema translation."""
        return """You are a data schema expert. Your task is to analyze natural language descriptions 
and convert them into structured JSON schemas for synthetic data generation.

You must return a JSON object with the following structure:
{
  "schema": {
    "columns": [
      {
        "name": "column_name",
        "type": "string|integer|float|boolean|datetime|date|email|phone|url|uuid|json",
        "description": "Clear description of this column",
        "constraints": {"min": 0, "max": 100, "pattern": "regex"},  // optional
        "examples": ["example1", "example2"]  // optional
      }
    ],
    "metadata": {}  // optional additional info
  },
  "inferred_count": 10000,  // if mentioned in prompt
  "confidence": 0.95
}

Be precise, comprehensive, and infer reasonable data types and constraints from context."""

    def _build_user_prompt(
        self, prompt: str, context: Optional[str] = None
    ) -> str:
        """Build user prompt for schema translation."""
        user_prompt = f"Convert the following description into a data schema:\n\n{prompt}"

        if context:
            user_prompt += f"\n\nAdditional context:\n{context}"

        return user_prompt

    def _get_output_schema(self) -> dict:
        """Get JSON schema for structured output."""
        return {
            "type": "object",
            "properties": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "columns": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {
                                        "type": "string",
                                        "enum": [
                                            "string",
                                            "integer",
                                            "float",
                                            "boolean",
                                            "datetime",
                                            "date",
                                            "email",
                                            "phone",
                                            "url",
                                            "uuid",
                                            "json",
                                        ],
                                    },
                                    "description": {"type": "string"},
                                    "constraints": {"type": "object"},
                                    "examples": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": ["name", "type", "description"],
                            },
                        },
                        "metadata": {"type": "object"},
                    },
                    "required": ["columns"],
                },
                "inferred_count": {"type": "integer"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
            "required": ["schema"],
        }
