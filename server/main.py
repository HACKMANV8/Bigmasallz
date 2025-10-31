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
        choices=["server", "version"],
        help="Command to execute"
    )

    args = parser.parse_args()

    if args.command == "server":
        logger.info("Starting MCP server...")
        run_mcp_server()
    elif args.command == "version":
        from src import __version__
        print(f"Synthetic Dataset Generator v{__version__}")


if __name__ == "__main__":
    main()
