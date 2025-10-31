"""Tests for the offline fallback generator."""

from __future__ import annotations

import pytest

from src.core.models import DataSchema, FieldConstraint, FieldDefinition, FieldType, SchemaExtractionRequest
from src.services.fallback_generator import build_fallback_generator


def test_fallback_extracts_schema_from_simple_prompt():
    generator = build_fallback_generator()

    response = generator.extract_schema(
        SchemaExtractionRequest(user_input="food, calories and protein")
    )

    field_map = {field.name: field.type for field in response.schema.fields}

    assert "food" in field_map
    assert field_map["food"] == FieldType.STRING
    assert field_map["calories"] in {FieldType.INTEGER, FieldType.FLOAT}
    assert field_map["protein"] in {FieldType.INTEGER, FieldType.FLOAT}
    assert any("Gemini quota" in warning for warning in response.warnings)
    assert response.confidence < 1


def test_fallback_generates_unique_rows_for_unique_fields():
    generator = build_fallback_generator()

    schema = DataSchema(
        fields=[
            FieldDefinition(
                name="item_id",
                type=FieldType.UUID,
                description="Synthetic identifier",
                constraints=FieldConstraint(unique=True, nullable=False),
            ),
            FieldDefinition(
                name="food",
                type=FieldType.STRING,
                description="Food name",
                constraints=FieldConstraint(unique=False, nullable=False),
                sample_values=["Grilled Salmon", "Berry Smoothie"],
            ),
            FieldDefinition(
                name="calories",
                type=FieldType.INTEGER,
                description="Calorie count",
                constraints=FieldConstraint(unique=False, nullable=False, min_value=0, max_value=600),
            ),
        ],
        description="Testing schema",
        metadata={},
    )

    rows = generator.generate_data_chunk(schema=schema, num_rows=10, seed=42)

    assert len(rows) == 10
    assert len({row["item_id"] for row in rows}) == 10
    assert all(row["calories"] >= 0 for row in rows)
    assert all(isinstance(row["food"], str) for row in rows)


@pytest.mark.parametrize(
    "field_name, expected_type",
    [
        ("order_date", FieldType.DATE),
        ("updated_timestamp", FieldType.DATETIME),
        ("contact_email", FieldType.EMAIL),
        ("is_active", FieldType.BOOLEAN),
    ],
)
def test_infer_field_types(field_name: str, expected_type: FieldType):
    generator = build_fallback_generator()
    response = generator.extract_schema(
        SchemaExtractionRequest(user_input=f"{field_name}, value")
    )
    field_map = {field.name: field.type for field in response.schema.fields}
    assert field_map[field_name] == expected_type
