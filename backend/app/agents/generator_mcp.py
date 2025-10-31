"""
MCP Generator Agent - Worker agent that uses GitHub Copilot (via MCP) for data generation.
No API rate limits! Uses unlimited GitHub Student tokens.
"""

import json
import time
import asyncio
from typing import List, Dict, Any, Optional
from ..core.config import settings
from ..core.logging import get_logger
from ..models.schemas import DataSchema, SchemaField
from ..tools.deduplication import DeduplicationTool
from ..mcp.client import get_mcp_client

logger = get_logger(__name__)


class MCPGeneratorAgent:
    """
    Worker agent that generates synthetic data using GitHub Copilot via MCP.
    Uses unlimited tokens from GitHub Student Pro account!
    Each agent instance runs in a separate thread for parallel processing.
    """
    
    def __init__(self, agent_id: int, schema: DataSchema, enable_deduplication: bool = True):
        """
        Initialize the MCP generator agent.
        
        Args:
            agent_id: Unique identifier for this agent
            schema: Data schema to generate
            enable_deduplication: Whether to use deduplication tool
        """
        self.agent_id = agent_id
        self.schema = schema
        self.enable_deduplication = enable_deduplication
        
        # Get MCP client (singleton)
        self.mcp_client = get_mcp_client()
        
        # Initialize deduplication tool if enabled
        self.dedupe_tool = DeduplicationTool() if enable_deduplication else None
        
        # Metrics
        self.tokens_used = 0  # We have unlimited tokens! 🎉
        self.api_calls = 0
        self.total_response_time = 0.0
        self.duplicates_removed = 0
        
        logger.info(
            f"MCP Generator Agent {agent_id} initialized with unlimited tokens!",
            extra={"extra_fields": {"agent_id": agent_id}}
        )
    
    def _convert_schema_to_mcp_format(self) -> Dict[str, Any]:
        """
        Convert DataSchema to MCP-compatible format.
        
        Returns:
            Schema dictionary for MCP tools
        """
        return {
            "fields": [
                {
                    "name": field.name,
                    "type": field.type,
                    "description": field.description or f"The {field.name} field",
                    "constraints": field.constraints or {}
                }
                for field in self.schema.fields
            ]
        }
    
    def generate_chunk(self, chunk_id: int, num_rows: int) -> Dict[str, Any]:
        """
        Generate a chunk of synthetic data using GitHub Copilot.
        
        Args:
            chunk_id: Unique chunk identifier
            num_rows: Number of rows to generate
            
        Returns:
            Dict with chunk_id, status, rows_generated, data, etc.
        """
        start_time = time.time()
        
        logger.info(
            f"Agent {self.agent_id} starting chunk {chunk_id} with {num_rows} rows",
            extra={"extra_fields": {
                "agent_id": self.agent_id,
                "chunk_id": chunk_id,
                "num_rows": num_rows
            }}
        )
        
        try:
            # Convert schema to MCP format
            mcp_schema = self._convert_schema_to_mcp_format()
            
            # Generate data using MCP (GitHub Copilot)
            generated_data = asyncio.run(self._generate_with_copilot(
                mcp_schema,
                num_rows,
                chunk_id
            ))
            
            # Validate data
            if not isinstance(generated_data, list):
                raise ValueError(f"Expected list, got {type(generated_data)}")
            
            # Deduplicate if enabled
            if self.enable_deduplication and self.dedupe_tool:
                original_count = len(generated_data)
                generated_data = self.dedupe_tool.deduplicate(generated_data)
                duplicates_removed = original_count - len(generated_data)
                self.duplicates_removed += duplicates_removed
                
                logger.info(
                    f"Agent {self.agent_id} removed {duplicates_removed} duplicates from chunk {chunk_id}",
                    extra={"extra_fields": {
                        "agent_id": self.agent_id,
                        "chunk_id": chunk_id,
                        "duplicates_removed": duplicates_removed
                    }}
                )
            
            # Update metrics
            elapsed_time = time.time() - start_time
            self.api_calls += 1
            self.total_response_time += elapsed_time
            
            logger.info(
                f"Agent {self.agent_id} completed chunk {chunk_id} in {elapsed_time:.2f}s",
                extra={"extra_fields": {
                    "agent_id": self.agent_id,
                    "chunk_id": chunk_id,
                    "rows_generated": len(generated_data),
                    "elapsed_time": elapsed_time
                }}
            )
            
            return {
                "chunk_id": chunk_id,
                "status": "completed",
                "rows_generated": len(generated_data),
                "duplicates_removed": duplicates_removed if self.enable_deduplication else 0,
                "data": generated_data,
                "elapsed_time": elapsed_time
            }
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            
            logger.error(
                f"Agent {self.agent_id} failed chunk {chunk_id}: {str(e)}",
                extra={"extra_fields": {
                    "agent_id": self.agent_id,
                    "chunk_id": chunk_id,
                    "error": str(e)
                }},
                exc_info=True
            )
            
            return {
                "chunk_id": chunk_id,
                "status": "failed",
                "rows_generated": 0,
                "duplicates_removed": 0,
                "data": [],
                "error": str(e),
                "elapsed_time": elapsed_time
            }
    
    async def _generate_with_copilot(
        self,
        schema: Dict[str, Any],
        num_rows: int,
        chunk_id: int,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate data using GitHub Copilot via MCP with retries.
        
        Args:
            schema: Schema in MCP format
            num_rows: Number of rows to generate
            chunk_id: Chunk identifier
            max_retries: Maximum number of retries
            
        Returns:
            List of generated data rows
        """
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Agent {self.agent_id} attempting Copilot generation (attempt {attempt + 1}/{max_retries})",
                    extra={"extra_fields": {
                        "agent_id": self.agent_id,
                        "chunk_id": chunk_id,
                        "attempt": attempt + 1
                    }}
                )
                
                # Call MCP tool to generate data with Copilot
                result = await self.mcp_client.generate_data_chunk(
                    schema=schema,
                    num_rows=num_rows,
                    chunk_id=f"agent_{self.agent_id}_chunk_{chunk_id}",
                    enable_deduplication=False  # We handle deduplication separately
                )
                
                # Validate result
                if not isinstance(result, list):
                    raise ValueError(f"Expected list from Copilot, got {type(result)}")
                
                if len(result) == 0:
                    raise ValueError("Copilot returned empty data")
                
                # Validate each row has required fields
                field_names = {field["name"] for field in schema["fields"]}
                for i, row in enumerate(result):
                    if not isinstance(row, dict):
                        raise ValueError(f"Row {i} is not a dictionary: {type(row)}")
                    
                    missing_fields = field_names - set(row.keys())
                    if missing_fields:
                        raise ValueError(f"Row {i} missing fields: {missing_fields}")
                
                logger.info(
                    f"Agent {self.agent_id} successfully generated {len(result)} rows with Copilot",
                    extra={"extra_fields": {
                        "agent_id": self.agent_id,
                        "chunk_id": chunk_id,
                        "rows_generated": len(result)
                    }}
                )
                
                return result
            
            except Exception as e:
                logger.warning(
                    f"Agent {self.agent_id} Copilot generation attempt {attempt + 1} failed: {str(e)}",
                    extra={"extra_fields": {
                        "agent_id": self.agent_id,
                        "chunk_id": chunk_id,
                        "attempt": attempt + 1,
                        "error": str(e)
                    }}
                )
                
                if attempt == max_retries - 1:
                    raise
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        raise RuntimeError(f"Failed to generate data after {max_retries} attempts")


# Helper function to create MCP agent instead of regular agent
def create_mcp_agent(agent_id: int, schema: DataSchema, enable_deduplication: bool = True) -> MCPGeneratorAgent:
    """
    Create an MCP-based generator agent.
    
    Args:
        agent_id: Agent identifier
        schema: Data schema
        enable_deduplication: Enable deduplication
        
    Returns:
        MCPGeneratorAgent instance
    """
    return MCPGeneratorAgent(
        agent_id=agent_id,
        schema=schema,
        enable_deduplication=enable_deduplication
    )
