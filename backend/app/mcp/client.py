"""
MCP Client - Communicate with the MCP server for data generation
Uses GitHub Copilot (unlimited tokens) instead of OpenAI/Gemini APIs
"""

import json
import subprocess
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client to communicate with the MCP server running in VS Code.
    The MCP server uses GitHub Copilot for data generation.
    """
    
    def __init__(self, server_path: str = None):
        """
        Initialize MCP client.
        
        Args:
            server_path: Path to the compiled MCP server (dist/index.js)
        """
        if server_path is None:
            # Default to mcp-server/dist/index.js (go up to project root)
            # Path: backend/app/mcp/client.py -> backend/app/mcp -> backend/app -> backend -> project_root
            base_dir = Path(__file__).parent.parent.parent.parent
            server_path = base_dir / "mcp-server" / "dist" / "index.js"
        
        self.server_path = Path(server_path)
        if not self.server_path.exists():
            raise FileNotFoundError(
                f"MCP server not found at {self.server_path}. "
                f"Run 'npm run build' in the mcp-server directory."
            )
        
        self.process: Optional[subprocess.Popen] = None
        logger.info(f"MCP Client initialized with server at {self.server_path}")
    
    async def start_server(self):
        """Start the MCP server process."""
        if self.process is not None:
            logger.warning("MCP server already running")
            return
        
        try:
            self.process = subprocess.Popen(
                ["node", str(self.server_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            logger.info("MCP server started successfully")
            
            # Wait a bit for server to initialize
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    async def stop_server(self):
        """Stop the MCP server process."""
        if self.process is None:
            return
        
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
            logger.info("MCP server stopped")
        except subprocess.TimeoutExpired:
            self.process.kill()
            logger.warning("MCP server killed after timeout")
        finally:
            self.process = None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool and return the result.
        
        Args:
            tool_name: Name of the tool (e.g., "generate_data_chunk")
            arguments: Tool arguments as a dictionary
        
        Returns:
            Tool result (parsed JSON)
        """
        if self.process is None:
            await self.start_server()
        
        # Prepare the request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            
            # Read response
            response_line = self.process.stdout.readline()
            response = json.loads(response_line)
            
            # Check for errors
            if "error" in response:
                error = response["error"]
                raise Exception(f"MCP tool error: {error.get('message', error)}")
            
            # Extract result
            result = response.get("result", {})
            
            # Parse content if it's text
            if isinstance(result, dict) and "content" in result:
                content = result["content"]
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if isinstance(first_content, dict) and first_content.get("type") == "text":
                        text = first_content.get("text", "")
                        # Try to parse as JSON
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            return text
            
            return result
            
        except Exception as e:
            logger.error(f"MCP tool call failed: {e}")
            raise
    
    async def translate_schema(self, prompt: str) -> Dict[str, Any]:
        """
        Convert natural language to a data schema.
        
        Args:
            prompt: Natural language description (e.g., "user data with name and email")
        
        Returns:
            Schema dictionary with fields
        """
        logger.info(f"Translating schema: {prompt}")
        result = await self.call_tool("translate_schema", {"prompt": prompt})
        logger.info(f"Schema translated successfully")
        return result
    
    async def generate_data_chunk(
        self,
        schema: Dict[str, Any],
        num_rows: int,
        chunk_id: str = "chunk_0",
        enable_deduplication: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic data using GitHub Copilot.
        
        Args:
            schema: Data schema with fields
            num_rows: Number of rows to generate
            chunk_id: Unique identifier for this chunk
            enable_deduplication: Whether to enable deduplication
        
        Returns:
            List of generated data rows
        """
        logger.info(f"Generating {num_rows} rows with Copilot (chunk: {chunk_id})")
        
        result = await self.call_tool("generate_data_chunk", {
            "schema": schema,
            "num_rows": num_rows,
            "chunk_id": chunk_id,
            "enable_deduplication": enable_deduplication
        })
        
        logger.info(f"Generated {len(result)} rows successfully")
        return result
    
    async def check_duplicates(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for and remove duplicate rows.
        
        Args:
            data: List of data rows
        
        Returns:
            Dictionary with unique_rows and duplicates_removed count
        """
        logger.info(f"Checking {len(data)} rows for duplicates")
        result = await self.call_tool("check_duplicates", {"data": data})
        logger.info(f"Removed {result.get('duplicates_removed', 0)} duplicates")
        return result
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.start_server()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.stop_server()


# Singleton instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """
    Get or create the global MCP client instance.
    
    Returns:
        MCPClient instance
    """
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client
