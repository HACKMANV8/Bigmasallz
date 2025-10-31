"""
Generator Agent - Worker agent responsible for generating synthetic data chunks using Google Gemini.
"""

import json
import time
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from ..core.config import settings
from ..core.logging import get_logger
from ..models.schemas import DataSchema, SchemaField
from ..tools.deduplication import DeduplicationTool

logger = get_logger(__name__)


class GeneratorAgent:
    """
    Worker agent that generates synthetic data using OpenAI's API.
    Each agent instance runs in a separate thread for parallel processing.
    """
    
    def __init__(self, agent_id: int, schema: DataSchema, enable_deduplication: bool = True):
        """
        Initialize the generator agent with Google Gemini.
        
        Args:
            agent_id: Unique identifier for this agent
            schema: Data schema to generate
            enable_deduplication: Whether to use deduplication tool
        """
        self.agent_id = agent_id
        self.schema = schema
        self.enable_deduplication = enable_deduplication
        
        # Initialize Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Initialize deduplication tool if enabled
        self.dedupe_tool = DeduplicationTool() if enable_deduplication else None
        
        # Metrics
        self.tokens_used = 0
        self.api_calls = 0
        self.total_response_time = 0.0
        self.duplicates_removed = 0
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for data generation."""
        return """You are a JSON data generator. Generate ONLY valid JSON - no explanations, no markdown, no extra text.

CRITICAL RULES:
1. Return ONLY a JSON object with a "data" array
2. Each string value must be properly escaped
3. No line breaks inside string values
4. No trailing commas
5. All objects must be complete and well-formed
6. Keep string values SHORT and simple to avoid truncation"""
    
    def _build_user_prompt(self, num_rows: int) -> str:
        """
        Build the user prompt for data generation.
        
        Args:
            num_rows: Number of rows to generate
            
        Returns:
            Formatted prompt string
        """
        schema_description = []
        for field in self.schema.fields:
            field_desc = f"- {field.name} ({field.type})"
            if field.description:
                field_desc += f": {field.description}"
            if field.constraints:
                field_desc += f" | Constraints: {json.dumps(field.constraints)}"
            schema_description.append(field_desc)
        
        # Build example object structure
        example_obj = {field.name: f"<{field.type}_value>" for field in self.schema.fields}
        
        prompt = f"""Generate {num_rows} rows of synthetic data with the following schema:

{chr(10).join(schema_description)}

CRITICAL: Return ONLY a valid JSON object in this EXACT format:
{{
  "data": [
    {json.dumps(example_obj, indent=4)},
    ... ({num_rows} total objects)
  ]
}}

Rules:
- Use "data" as the array key
- Each object must have ALL fields from the schema
- All strings must be properly escaped
- No trailing commas
- No comments in JSON"""
        
        return prompt
    
    def generate_chunk(
        self, 
        chunk_id: int, 
        num_rows: int,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate a chunk of synthetic data with retry logic.
        
        Args:
            chunk_id: Unique identifier for this chunk
            num_rows: Number of rows to generate
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with generation results
        """
        logger.info(
            f"Agent {self.agent_id} generating chunk {chunk_id} with {num_rows} rows",
            extra={"extra_fields": {"agent_id": self.agent_id, "chunk_id": chunk_id}}
        )
        
        start_time = time.time()
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Call Gemini API
                prompt = f"{self._build_system_prompt()}\n\n{self._build_user_prompt(num_rows)}"
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=settings.GEMINI_TEMPERATURE,
                        max_output_tokens=settings.GEMINI_MAX_TOKENS,
                    )
                )
                
                # Track metrics
                self.api_calls += 1
                # Estimate tokens (Gemini doesn't provide usage directly in same way)
                estimated_tokens = len(prompt.split()) + len(response.text.split())
                self.tokens_used += estimated_tokens
                
                response_time = time.time() - start_time
                self.total_response_time += response_time
                
                # Parse response
                content = response.text
                
                # Clean content before parsing
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                data = json.loads(content)
                
                # Handle different response formats
                if isinstance(data, dict) and "data" in data:
                    rows = data["data"]
                elif isinstance(data, dict) and "rows" in data:
                    rows = data["rows"]
                elif isinstance(data, list):
                    rows = data
                else:
                    # Try to extract first list found
                    for value in data.values():
                        if isinstance(value, list):
                            rows = value
                            break
                    else:
                        raise ValueError("Could not find data array in response")
                
                # Validate rows
                if not isinstance(rows, list):
                    raise ValueError(f"Expected list of rows, got {type(rows)}")
                
                if len(rows) == 0:
                    raise ValueError("Generated empty data array")
                
                # Apply deduplication if enabled
                duplicates_count = 0
                if self.enable_deduplication and self.dedupe_tool:
                    rows, duplicates_count = self.dedupe_tool.check_duplicates(rows)
                    self.duplicates_removed += duplicates_count
                    logger.info(
                        f"Deduplication: {duplicates_count} duplicates removed from chunk {chunk_id}",
                        extra={"extra_fields": {
                            "chunk_id": chunk_id, 
                            "duplicates": duplicates_count,
                            "unique_rows": len(rows)
                        }}
                    )
                
                result = {
                    "chunk_id": chunk_id,
                    "status": "completed",
                    "rows_generated": len(rows),
                    "duplicates_removed": duplicates_count,
                    "data": rows,
                    "response_time": response_time,
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0,
                    "attempts": attempt + 1
                }
                
                logger.info(
                    f"Agent {self.agent_id} completed chunk {chunk_id} (attempt {attempt + 1})",
                    extra={"extra_fields": result}
                )
                
                return result
                
            except json.JSONDecodeError as e:
                last_error = f"JSON parsing error: {str(e)}"
                logger.warning(
                    f"Agent {self.agent_id} chunk {chunk_id} attempt {attempt + 1} failed: {last_error}",
                    extra={"extra_fields": {"agent_id": self.agent_id, "chunk_id": chunk_id, "attempt": attempt + 1}}
                )
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
                
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Agent {self.agent_id} chunk {chunk_id} attempt {attempt + 1} failed: {last_error}",
                    extra={"extra_fields": {"agent_id": self.agent_id, "chunk_id": chunk_id, "attempt": attempt + 1}}
                )
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        # All retries failed
        logger.error(
            f"Agent {self.agent_id} failed to generate chunk {chunk_id} after {max_retries} attempts: {last_error}",
            extra={"extra_fields": {"agent_id": self.agent_id, "chunk_id": chunk_id}},
            exc_info=True
        )
        
        return {
            "chunk_id": chunk_id,
            "status": "failed",
            "rows_generated": 0,
            "duplicates_removed": 0,
            "data": [],
            "error": last_error,
            "response_time": time.time() - start_time,
            "attempts": max_retries
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get agent performance metrics.
        
        Returns:
            Dictionary with metrics
        """
        avg_response_time = (
            self.total_response_time / self.api_calls 
            if self.api_calls > 0 
            else 0.0
        )
        
        metrics = {
            "agent_id": self.agent_id,
            "tokens_used": self.tokens_used,
            "api_calls": self.api_calls,
            "avg_response_time": avg_response_time,
            "duplicates_removed": self.duplicates_removed
        }
        
        # Add deduplication stats if available
        if self.dedupe_tool:
            metrics["deduplication_stats"] = self.dedupe_tool.get_stats()
        
        return metrics
