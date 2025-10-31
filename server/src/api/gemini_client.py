"""Gemini API client for LLM operations."""

import json
import time
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.core.models import (
    DataSchema,
    FieldConstraint,
    FieldDefinition,
    FieldType,
    SchemaExtractionRequest,
    SchemaExtractionResponse,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

try:
    from langfuse import Langfuse  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    Langfuse = None


class GeminiClient:
    """Client for interacting with Google Gemini API."""

    def __init__(self, api_key: str | None = None):
        """Initialize Gemini client.
        
        Args:
            api_key: Optional API key, uses settings if not provided
        """
        self.api_key = api_key or settings.gemini_api_key
        genai.configure(api_key=self.api_key)

        self.model_name = settings.gemini_model
        self.max_retries = settings.gemini_max_retries
        self.timeout = settings.gemini_timeout

        # Rate limiting
        self.requests_per_minute = settings.rate_limit_requests_per_minute
        self.tokens_per_minute = settings.rate_limit_tokens_per_minute
        self.request_times: list[float] = []

        self._langfuse_client = self._init_langfuse()

        logger.info(f"Initialized Gemini client with model: {self.model_name}")

    def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        current_time = time.time()
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if current_time - t < 60]

        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.request_times = []

        self.request_times.append(current_time)

    def _init_langfuse(self):
        """Initialise Langfuse telemetry client if configured."""
        config = settings.langfuse

        if not config.enabled:
            logger.debug("Langfuse telemetry disabled by configuration")
            return None

        if Langfuse is None:
            logger.warning(
                "Langfuse telemetry enabled but 'langfuse' package is not installed"
            )
            return None

        try:
            init_kwargs: dict[str, Any] = {
                "public_key": config.public_key,
                "secret_key": config.secret_key,
            }
            if config.base_url:
                init_kwargs["host"] = config.base_url

            client = Langfuse(**init_kwargs)
            if not hasattr(client, "trace"):
                logger.warning(
                    "Langfuse client does not expose 'trace'; telemetry will be disabled"
                )
                return None

            logger.info("Langfuse telemetry enabled")
            return client
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(f"Failed to initialise Langfuse telemetry: {exc}")
            return None

    def _start_trace(self, name: str, inputs: dict[str, Any] | None = None):
        """Create a Langfuse trace if telemetry is enabled."""
        if not self._langfuse_client:
            return None

        try:
            trace_callable = getattr(self._langfuse_client, "trace", None)
            if not callable(trace_callable):
                return None

            trace = trace_callable(
                name=name,
                input=inputs,
                metadata={"model": self.model_name},
            )
            return trace
        except Exception as exc:  # pragma: no cover - telemetry should not break core flow
            logger.warning(f"Unable to start Langfuse trace '{name}': {exc}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _generate_content(self, prompt: str, **kwargs) -> str:
        """Generate content with retry logic.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text content
        """
        self._check_rate_limit()

        model = genai.GenerativeModel(self.model_name)

        generation_config = GenerationConfig(
            temperature=kwargs.get("temperature", 0.7),
            top_p=kwargs.get("top_p", 0.95),
            top_k=kwargs.get("top_k", 40),
            max_output_tokens=kwargs.get("max_output_tokens", 8192),
        )

        try:
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options={"timeout": self.timeout}
            )

            if response.text:
                return response.text
            else:
                logger.error("Empty response from Gemini API")
                raise ValueError("Empty response from Gemini API")

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise

    def extract_schema(self, request: SchemaExtractionRequest) -> SchemaExtractionResponse:
        """Extract structured schema from natural language description.
        
        Args:
            request: Schema extraction request
            
        Returns:
            Extracted schema with confidence and suggestions
        """
        logger.info(f"Extracting schema from user input: {request.user_input[:100]}...")

        prompt = self._build_schema_extraction_prompt(request)
        trace = self._start_trace(
            name="gemini.extract_schema",
            inputs={
                "prompt": prompt,
                "user_input_preview": request.user_input[:200],
                "has_context": bool(request.context),
                "has_example_data": bool(request.example_data),
            },
        )

        response_text: str | None = None

        # Parse JSON response
        try:
            response_text = self._generate_content(prompt, temperature=0.3)

            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            schema_data = json.loads(response_text)

            # Convert to proper models
            fields = []
            for field_data in schema_data.get("fields", []):
                constraint_data = field_data.get("constraints", {})
                constraints = FieldConstraint(
                    unique=constraint_data.get("unique", False),
                    nullable=constraint_data.get("nullable", True),
                    min_value=constraint_data.get("min_value"),
                    max_value=constraint_data.get("max_value"),
                    min_length=constraint_data.get("min_length"),
                    max_length=constraint_data.get("max_length"),
                    pattern=constraint_data.get("pattern"),
                    enum_values=constraint_data.get("enum_values"),
                    format=constraint_data.get("format"),
                    default=constraint_data.get("default")
                )

                field = FieldDefinition(
                    name=field_data["name"],
                    type=FieldType(field_data["type"]),
                    description=field_data.get("description"),
                    constraints=constraints,
                    sample_values=field_data.get("sample_values", []),
                    depends_on=field_data.get("depends_on"),
                    generation_hint=field_data.get("generation_hint")
                )
                fields.append(field)

            schema = DataSchema(
                fields=fields,
                description=schema_data.get("description"),
                relationships=schema_data.get("relationships"),
                metadata=schema_data.get("metadata", {})
            )

            result = SchemaExtractionResponse(
                schema=schema,
                confidence=schema_data.get("confidence", 0.85),
                suggestions=schema_data.get("suggestions", []),
                warnings=schema_data.get("warnings", [])
            )

            if trace:
                output_payload: dict[str, Any] = {
                    "confidence": result.confidence,
                    "field_count": len(schema.fields),
                    "field_names": [field.name for field in schema.fields],
                }
                if result.warnings:
                    output_payload["warnings"] = result.warnings
                if result.suggestions:
                    output_payload["suggestions"] = result.suggestions[:3]
                trace.end(
                    output=output_payload
                )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse schema JSON: {e}")
            logger.debug(f"Response text: {response_text}")
            if trace:
                metadata: dict[str, Any] = {}
                if response_text:
                    metadata["raw_response_preview"] = response_text[:500]
                trace.end(error=str(e), metadata=metadata or None)
            raise ValueError(f"Failed to parse schema from LLM response: {e}")
        except Exception as exc:
            if trace:
                metadata: dict[str, Any] = {}
                if response_text:
                    metadata["raw_response_preview"] = response_text[:500]
                trace.end(error=str(exc), metadata=metadata or None)
            raise

    def generate_data_chunk(
        self,
        schema: DataSchema,
        num_rows: int,
        existing_values: dict[str, list[Any]] | None = None,
        seed: int | None = None
    ) -> list[dict[str, Any]]:
        """Generate a chunk of synthetic data.
        
        Args:
            schema: Data schema to follow
            num_rows: Number of rows to generate
            existing_values: Existing values for uniqueness constraints
            seed: Random seed for reproducibility
            
        Returns:
            List of generated data rows
        """
        logger.info(f"Generating {num_rows} rows of data")

        prompt = self._build_data_generation_prompt(schema, num_rows, existing_values, seed)
        trace = self._start_trace(
            name="gemini.generate_data_chunk",
            inputs={
                "prompt": prompt,
                "num_rows": num_rows,
                "seed": seed,
                "field_names": [field.name for field in schema.fields],
                "existing_value_counts": {
                    key: len(values) for key, values in (existing_values or {}).items()
                },
            },
        )

        response_text: str | None = None

        # Parse JSON response
        try:
            response_text = self._generate_content(prompt, temperature=0.8)

            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            data = json.loads(response_text)

            # Handle both array and object with "data" key
            if isinstance(data, dict) and "data" in data:
                data = data["data"]

            if trace:
                preview_count = min(3, len(data))
                trace.end(
                    output={
                        "rows_generated": len(data),
                        "preview": data[:preview_count],
                    }
                )

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse data JSON: {e}")
            logger.debug(f"Response text: {response_text[:500]}...")
            if trace:
                metadata: dict[str, Any] = {}
                if response_text:
                    metadata["raw_response_preview"] = response_text[:500]
                trace.end(error=str(e), metadata=metadata or None)
            raise ValueError(f"Failed to parse data from LLM response: {e}")
        except Exception as exc:
            if trace:
                metadata: dict[str, Any] = {}
                if response_text:
                    metadata["raw_response_preview"] = response_text[:500]
                trace.end(error=str(exc), metadata=metadata or None)
            raise

    def _build_schema_extraction_prompt(self, request: SchemaExtractionRequest) -> str:
        """Build prompt for schema extraction."""
        prompt = f"""You are an expert data engineer. Extract a structured data schema from the following user request.

User Request: {request.user_input}

"""

        if request.context:
            prompt += f"\nAdditional Context: {json.dumps(request.context, indent=2)}\n"

        if request.example_data:
            prompt += f"\nExample Data: {request.example_data}\n"

        prompt += """
Please analyze the request and generate a JSON schema with the following structure:

{
  "description": "Brief description of the dataset",
  "fields": [
    {
      "name": "field_name",
      "type": "string|integer|float|boolean|date|datetime|email|phone|uuid|enum|json|array",
      "description": "Description of the field",
      "constraints": {
        "unique": false,
        "nullable": true,
        "min_value": null,
        "max_value": null,
        "min_length": null,
        "max_length": null,
        "pattern": null,
        "enum_values": null,
        "format": null,
        "default": null
      },
      "sample_values": ["example1", "example2"],
      "depends_on": null,
      "generation_hint": "How to generate this field"
    }
  ],
  "relationships": {},
  "metadata": {},
  "confidence": 0.95,
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "warnings": ["Warning 1"]
}

Important:
- Infer appropriate data types and constraints
- Include realistic sample values
- Identify field dependencies
- Provide generation hints for complex fields
- Set confidence between 0 and 1
- Add suggestions for improvements
- List any warnings or ambiguities

Return ONLY the JSON schema, no additional text.
"""
        return prompt

    def _build_data_generation_prompt(
        self,
        schema: DataSchema,
        num_rows: int,
        existing_values: dict[str, list[Any]] | None,
        seed: int | None
    ) -> str:
        """Build prompt for data generation."""
        schema_json = {
            "description": schema.description,
            "fields": [
                {
                    "name": f.name,
                    "type": f.type.value,
                    "description": f.description,
                    "constraints": {
                        "unique": f.constraints.unique,
                        "nullable": f.constraints.nullable,
                        "min_value": f.constraints.min_value,
                        "max_value": f.constraints.max_value,
                        "min_length": f.constraints.min_length,
                        "max_length": f.constraints.max_length,
                        "pattern": f.constraints.pattern,
                        "enum_values": f.constraints.enum_values,
                        "format": f.constraints.format,
                        "default": f.constraints.default
                    },
                    "sample_values": f.sample_values,
                    "generation_hint": f.generation_hint
                }
                for f in schema.fields
            ]
        }

        prompt = f"""You are a synthetic data generator. Generate {num_rows} rows of realistic data following this schema:

Schema:
{json.dumps(schema_json, indent=2)}

"""

        if existing_values:
            prompt += f"\nExisting Values (avoid duplicates for unique fields):\n{json.dumps(existing_values, indent=2)}\n"

        if seed:
            prompt += f"\nRandom Seed: {seed}\n"

        prompt += f"""
Requirements:
- Generate EXACTLY {num_rows} rows
- Follow all field types and constraints strictly
- Ensure unique values for fields marked as unique
- Generate realistic, coherent data
- Maintain relationships between dependent fields
- Use appropriate formats for dates, emails, phones, etc.
- Return data as a JSON array of objects

Example output format:
[
  {{"field1": "value1", "field2": 123, "field3": "2024-01-01"}},
  {{"field1": "value2", "field2": 456, "field3": "2024-01-02"}}
]

Return ONLY the JSON array, no additional text or explanations.
"""
        return prompt


# Global client instance
_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    """Get or create global Gemini client instance."""
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
