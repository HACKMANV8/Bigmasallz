#!/usr/bin/env python3
"""Main entry point for the Synthetic Dataset Generation Tool."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_server.server import main as run_mcp_server
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Synthetic Dataset Generation Tool using LLMs"
    )
    parser.add_argument(
        "command",
        choices=["server", "api", "version"],
        help="Command to execute"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host interface for API server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for API server"
    )

    args = parser.parse_args()

    if args.command == "server":
        logger.info("Starting MCP server...")
        run_mcp_server()
    elif args.command == "api":
        import uvicorn

        logger.info("Starting FastAPI server on %s:%s", args.host, args.port)
        uvicorn.run(
            "src.api_server.app:app",
            host=args.host,
            port=args.port,
            reload=False,
            log_level="info",
        )
    elif args.command == "version":
        from src import __version__
        print(f"Synthetic Dataset Generator v{__version__}")


if __name__ == "__main__":
    main()
