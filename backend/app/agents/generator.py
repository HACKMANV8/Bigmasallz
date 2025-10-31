"""
Generator Agent - Worker agent responsible for generating synthetic data chunks.
"""

import json
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
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
        Initialize the generator agent.
        
        Args:
            agent_id: Unique identifier for this agent
            schema: Data schema to generate
            enable_deduplication: Whether to use deduplication tool
        """
        self.agent_id = agent_id
        self.schema = schema
        self.enable_deduplication = enable_deduplication
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Initialize deduplication tool if enabled
        self.dedupe_tool = DeduplicationTool() if enable_deduplication else None
        
        # Metrics
        self.tokens_used = 0
        self.api_calls = 0
        self.total_response_time = 0.0
        self.duplicates_removed = 0
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for data generation."""
        return """You are a synthetic data generator. Generate realistic, diverse, and high-quality data according to the provided schema.

Guidelines:
- Generate unique, varied data to avoid repetitive patterns
- Follow all field constraints strictly
- Use realistic values appropriate for each field type
- Ensure data is internally consistent
- Return ONLY valid JSON array format
- Do not include any explanations or markdown formatting"""
    
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
        
        prompt = f"""Generate {num_rows} rows of synthetic data with the following schema:

{chr(10).join(schema_description)}

Return the data as a JSON array of objects. Each object should have all the specified fields."""
        
        return prompt
    
    def generate_chunk(
        self, 
        chunk_id: int, 
        num_rows: int
    ) -> Dict[str, Any]:
        """
        Generate a chunk of synthetic data.
        
        Args:
            chunk_id: Unique identifier for this chunk
            num_rows: Number of rows to generate
            
        Returns:
            Dictionary with generation results
        """
        logger.info(
            f"Agent {self.agent_id} generating chunk {chunk_id} with {num_rows} rows",
            extra={"extra_fields": {"agent_id": self.agent_id, "chunk_id": chunk_id}}
        )
        
        start_time = time.time()
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": self._build_user_prompt(num_rows)}
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            
            # Track metrics
            self.api_calls += 1
            if hasattr(response, 'usage'):
                self.tokens_used += response.usage.total_tokens
            
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            # Parse response
            content = response.choices[0].message.content
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
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
            logger.info(
                f"Agent {self.agent_id} completed chunk {chunk_id}",
                extra={"extra_fields": result}
            )
            
            return result
        
        except Exception as e:
            logger.error(
                f"Agent {self.agent_id} failed to generate chunk {chunk_id}: {str(e)}",
                extra={"extra_fields": {"agent_id": self.agent_id, "chunk_id": chunk_id}},
                exc_info=True
            )
            
            return {
                "chunk_id": chunk_id,
                "status": "failed",
                "rows_generated": 0,
                "duplicates_removed": 0,
                "data": [],
                "error": str(e),
                "response_time": time.time() - start_time
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
