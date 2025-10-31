"""Test configuration and fixtures."""

import pytest
import asyncio
from typing import Generator

from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "schema": {
            "columns": [
                {
                    "name": "user_id",
                    "type": "string",
                    "description": "Unique user identifier",
                },
                {
                    "name": "email",
                    "type": "email",
                    "description": "User email address",
                },
                {
                    "name": "age",
                    "type": "integer",
                    "description": "User age",
                    "constraints": {"min": 18, "max": 100},
                },
            ]
        },
        "inferred_count": 100,
        "confidence": 0.95,
    }


@pytest.fixture
def sample_schema():
    """Sample data schema for testing."""
    from app.models.schema import DataSchema, ColumnSchema, ColumnType

    return DataSchema(
        columns=[
            ColumnSchema(
                name="id",
                type=ColumnType.STRING,
                description="Unique ID",
            ),
            ColumnSchema(
                name="name",
                type=ColumnType.STRING,
                description="Person name",
            ),
            ColumnSchema(
                name="age",
                type=ColumnType.INTEGER,
                description="Person age",
                constraints={"min": 18, "max": 100},
            ),
        ]
    )


@pytest.fixture
def sample_generated_data():
    """Sample generated data for testing."""
    return [
        {"id": "1", "name": "Alice Smith", "age": 30},
        {"id": "2", "name": "Bob Johnson", "age": 25},
        {"id": "3", "name": "Carol Williams", "age": 45},
    ]
