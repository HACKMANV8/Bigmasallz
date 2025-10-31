"""Offline fallback generator when Gemini is unavailable.

This module provides lightweight heuristics for extracting schemas and generating
synthetic data without relying on the Gemini API. It is intentionally conservative
and focuses on producing sensible defaults so the application remains functional
when remote quota limits are reached.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

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


@dataclass
class FallbackFieldBlueprint:
    """Configuration used to build fallback fields."""

    name: str
    field_type: FieldType
    description: str
    sample_values: list[Any]
    generation_hint: str
    constraints: FieldConstraint


class FallbackGenerator:
    """Simple rule-based generator used when Gemini cannot be reached."""

    _FIELD_SPLIT_PATTERN = re.compile(r"\s*(?:,|\band\b|\bplus\b|\n|/|\|)\s*", re.IGNORECASE)

    _NUMERIC_KEYWORDS: tuple[str, ...] = (
        "age",
        "amount",
        "balance",
        "budget",
        "calorie",
        "calories",
        "carb",
        "count",
        "duration",
        "height",
        "length",
        "level",
        "percent",
        "percentage",
        "price",
        "protein",
        "quantity",
        "score",
        "sizes",
        "speed",
        "steps",
        "temperature",
        "total",
        "weight",
        "width",
    )

    _FLOAT_KEYWORDS: tuple[str, ...] = (
        "price",
        "percent",
        "percentage",
        "ratio",
        "protein",
        "temperature",
        "score",
        "rating",
    )

    _BOOLEAN_KEYWORDS: tuple[str, ...] = (
        "is_",
        "has_",
        "with_",
        "active",
        "enabled",
        "flag",
    )

    _DATE_KEYWORDS: tuple[str, ...] = (
        "date",
        "day",
        "dob",
        "birthday",
        "scheduled",
    )

    _DATETIME_KEYWORDS: tuple[str, ...] = (
        "timestamp",
        "datetime",
        "updated",
        "created",
        "logged",
    )

    _EMAIL_KEYWORDS: tuple[str, ...] = ("email", "mail", "contact")
    _PHONE_KEYWORDS: tuple[str, ...] = ("phone", "tel", "mobile")
    _UUID_KEYWORDS: tuple[str, ...] = ("uuid", "guid")

    _STRING_SAMPLE_LIBRARY: dict[str, list[str]] = {
        "food": [
            "Grilled Salmon",
            "Quinoa Bowl",
            "Roasted Chickpeas",
            "Avocado Toast",
            "Berry Smoothie",
        ],
        "name": [
            "Aurora Vega",
            "Derek Chen",
            "Imani Brooks",
            "Noah Ruiz",
            "Sasha Patel",
        ],
        "city": [
            "New York",
            "Chicago",
            "Seattle",
            "Austin",
            "Denver",
        ],
        "company": [
            "Acme Analytics",
            "Nimbus Labs",
            "Summit Foods",
            "Brightbyte",
            "Atlas Ventures",
        ],
    }

    def extract_schema(self, request: SchemaExtractionRequest) -> SchemaExtractionResponse:
        """Build a schema using simple heuristics."""
        blueprint_fields = self._derive_fields(request.user_input)

        if not blueprint_fields:
            logger.debug("Fallback schema generation found no explicit fields; using default column")
            blueprint_fields = [self._default_field("item")]

        schema = DataSchema(
            fields=[self._build_field_definition(blueprint) for blueprint in blueprint_fields],
            description="Schema generated via offline heuristics",
            metadata={"generator": "fallback", "source": "quota"},
        )

        warnings = [
            "Gemini quota was exceeded. Schema generated using offline heuristics.",
            "Review field names and types to ensure they match your intended dataset.",
        ]

        suggestions = [
            "Adjust field descriptions or constraints manually if they need to be more specific.",
            "Consider providing example data to improve automatic inference in fallback mode.",
        ]

        return SchemaExtractionResponse(
            schema=schema,
            confidence=0.55,
            suggestions=suggestions,
            warnings=warnings,
        )

    def generate_data_chunk(
        self,
        *,
        schema: DataSchema,
        num_rows: int,
        existing_values: dict[str, list[Any]] | None = None,
        seed: int | None = None,
    ) -> list[dict[str, Any]]:
        """Generate data rows that adhere to the inferred schema."""
        rng = random.Random(seed)
        rows: list[dict[str, Any]] = []

        uniqueness_sets = {
            field_name: set(values or [])
            for field_name, values in (existing_values or {}).items()
        }

        for index in range(num_rows):
            row: dict[str, Any] = {}
            for field in schema.fields:
                unique = field.constraints.unique or field.name in uniqueness_sets
                value = self._generate_value(field, rng, index)

                if unique:
                    uniqueness_sets.setdefault(field.name, set())
                    attempts = 0
                    while value in uniqueness_sets[field.name] and attempts < 20:
                        value = self._generate_value(field, rng, index + attempts + 1)
                        attempts += 1
                    if value in uniqueness_sets[field.name]:
                        value = self._make_unique_value(field, rng, index + attempts + 1)
                    uniqueness_sets[field.name].add(value)

                row[field.name] = value
            rows.append(row)

        return rows

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _derive_fields(self, user_input: str) -> list[FallbackFieldBlueprint]:
        """Extract candidate fields from the user request."""
        tokens = [token.strip() for token in self._FIELD_SPLIT_PATTERN.split(user_input) if token.strip()]

        blueprints: list[FallbackFieldBlueprint] = []
        seen = set()
        for token in tokens:
            normalized = self._normalize_field_name(token)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            blueprints.append(self._field_from_token(normalized, token))

        return blueprints

    def _normalize_field_name(self, token: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", token.strip().lower()).strip("_")
        if not slug:
            return ""
        if slug[0].isdigit():
            slug = f"field_{slug}"
        return slug

    def _field_from_token(self, field_name: str, original_label: str) -> FallbackFieldBlueprint:
        field_type = self._infer_field_type(field_name)
        constraints = self._create_constraints(field_name, field_type)
        samples = self._build_sample_values(field_name, field_type)

        generation_hint = self._build_generation_hint(field_name, field_type, samples)
        description = f"Auto-generated field derived from '{original_label}'"

        return FallbackFieldBlueprint(
            name=field_name,
            field_type=field_type,
            description=description,
            sample_values=samples,
            generation_hint=generation_hint,
            constraints=constraints,
        )

    def _default_field(self, name: str) -> FallbackFieldBlueprint:
        return FallbackFieldBlueprint(
            name=name,
            field_type=FieldType.STRING,
            description="Generic item name",
            sample_values=["Example Item", "Sample Item"],
            generation_hint="Provide varied descriptive names for each row.",
            constraints=FieldConstraint(unique=False, nullable=False),
        )

    def _infer_field_type(self, field_name: str) -> FieldType:
        name = field_name.lower()

        if any(keyword in name for keyword in self._UUID_KEYWORDS) or name.endswith("_id"):
            return FieldType.UUID
        if any(keyword in name for keyword in self._EMAIL_KEYWORDS):
            return FieldType.EMAIL
        if any(keyword in name for keyword in self._PHONE_KEYWORDS):
            return FieldType.PHONE
        if any(keyword in name for keyword in self._DATETIME_KEYWORDS):
            return FieldType.DATETIME
        if any(keyword in name for keyword in self._DATE_KEYWORDS):
            return FieldType.DATE
        if any(keyword in name for keyword in self._BOOLEAN_KEYWORDS):
            return FieldType.BOOLEAN
        if any(keyword in name for keyword in self._NUMERIC_KEYWORDS):
            if any(keyword in name for keyword in self._FLOAT_KEYWORDS):
                return FieldType.FLOAT
            return FieldType.INTEGER

        return FieldType.STRING

    def _create_constraints(self, field_name: str, field_type: FieldType) -> FieldConstraint:
        unique = field_type in {FieldType.UUID, FieldType.EMAIL}
        if field_name.endswith("_id"):
            unique = True

        nullable = False if field_type in {FieldType.STRING, FieldType.INTEGER, FieldType.FLOAT} else True
        constraints = FieldConstraint(unique=unique, nullable=nullable)

        if field_type in {FieldType.INTEGER, FieldType.FLOAT}:
            constraints.min_value = 0
            if "calorie" in field_name or "protein" in field_name or "price" in field_name:
                constraints.max_value = 1000

        if field_type == FieldType.STRING and field_name.endswith("name"):
            constraints.max_length = 80

        if field_type == FieldType.EMAIL:
            constraints.pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        return constraints

    def _build_sample_values(self, field_name: str, field_type: FieldType) -> list[Any]:
        base_name = field_name.lower()

        if field_type == FieldType.STRING:
            for keyword, samples in self._STRING_SAMPLE_LIBRARY.items():
                if keyword in base_name:
                    return samples
            return [f"{field_name.replace('_', ' ').title()} A", f"{field_name.replace('_', ' ').title()} B"]

        if field_type == FieldType.INTEGER:
            return [42, 108]

        if field_type == FieldType.FLOAT:
            return [12.5, 87.3]

        if field_type == FieldType.BOOLEAN:
            return [True, False]

        if field_type == FieldType.DATE:
            today = date.today()
            return [str(today), str(today - timedelta(days=7))]

        if field_type == FieldType.DATETIME:
            now = datetime.now(timezone.utc)
            return [
                now.replace(tzinfo=None).isoformat(timespec="seconds"),
                (now - timedelta(hours=6)).replace(tzinfo=None).isoformat(timespec="seconds"),
            ]

        if field_type == FieldType.EMAIL:
            return ["user@example.com", "contact@example.com"]

        if field_type == FieldType.PHONE:
            return ["+1-555-123-4567", "+1-555-987-6543"]

        if field_type == FieldType.UUID:
            return [str(uuid4()), str(uuid4())]

        return []

    def _build_generation_hint(
        self,
        field_name: str,
        field_type: FieldType,
        sample_values: list[Any],
    ) -> str:
        if field_type == FieldType.STRING:
            return "Produce concise, human-readable labels related to the dataset theme."
        if field_type == FieldType.INTEGER:
            return "Use realistic whole numbers and stay within reasonable bounds."
        if field_type == FieldType.FLOAT:
            return "Use decimal values with one or two decimal places."
        if field_type == FieldType.BOOLEAN:
            return "Alternate between true and false while reflecting plausible outcomes."
        if field_type == FieldType.DATE:
            return "Return ISO formatted dates (YYYY-MM-DD)."
        if field_type == FieldType.DATETIME:
            return "Return ISO timestamps with timezone omitted (YYYY-MM-DDTHH:MM:SS)."
        if field_type == FieldType.EMAIL:
            return "Generate professional-looking email addresses."
        if field_type == FieldType.PHONE:
            return "Generate E.164 formatted phone numbers."
        if field_type == FieldType.UUID:
            return "Return RFC 4122 version 4 UUIDs."
        return "Provide realistic JSON-compatible values."

    def _build_field_definition(self, blueprint: FallbackFieldBlueprint) -> FieldDefinition:
        return FieldDefinition(
            name=blueprint.name,
            type=blueprint.field_type,
            description=blueprint.description,
            constraints=blueprint.constraints,
            sample_values=blueprint.sample_values,
            generation_hint=blueprint.generation_hint,
        )

    def _generate_value(self, field: FieldDefinition, rng: random.Random, index: int) -> Any:
        if field.type == FieldType.STRING:
            return self._generate_string(field, rng, index)
        if field.type == FieldType.INTEGER:
            return self._generate_integer(field, rng)
        if field.type == FieldType.FLOAT:
            return round(rng.uniform(0, 500), 2)
        if field.type == FieldType.BOOLEAN:
            return rng.choice([True, False])
        if field.type == FieldType.DATE:
            base = date.today() - timedelta(days=rng.randint(0, 180))
            return base.isoformat()
        if field.type == FieldType.DATETIME:
            dt = datetime.now(timezone.utc) - timedelta(hours=rng.randint(0, 240), minutes=rng.randint(0, 59))
            return dt.replace(tzinfo=None, microsecond=0).isoformat()
        if field.type == FieldType.EMAIL:
            return f"user{index + rng.randint(1, 9999)}@example.com"
        if field.type == FieldType.PHONE:
            return f"+1-555-{rng.randint(100, 999)}-{rng.randint(1000, 9999)}"
        if field.type == FieldType.UUID:
            return str(uuid4())

        if field.constraints.enum_values:
            return rng.choice(field.constraints.enum_values)
        if field.sample_values:
            return rng.choice(field.sample_values)

        return rng.randint(1, 100)

    def _generate_string(self, field: FieldDefinition, rng: random.Random, index: int) -> str:
        if field.sample_values:
            seed_offset = index % len(field.sample_values)
            return field.sample_values[seed_offset]
        base = field.name.replace("_", " ").title()
        return f"{base} {index + 1}"

    def _generate_integer(self, field: FieldDefinition, rng: random.Random) -> int:
        min_value = field.constraints.min_value
        max_value = field.constraints.max_value

        lower = int(min_value) if isinstance(min_value, (int, float)) else 0
        upper = int(max_value) if isinstance(max_value, (int, float)) else lower + 500
        if upper <= lower:
            upper = lower + 100
        return rng.randint(lower, upper)

    def _make_unique_value(self, field: FieldDefinition, rng: random.Random, index: int) -> Any:
        """Guarantee a unique value even when samples are exhausted."""
        base = field.name.replace("_", " ").title()
        if field.type == FieldType.STRING:
            return f"{base} {index + rng.randint(100, 999)}"
        if field.type == FieldType.INTEGER:
            upper = int(field.constraints.max_value or 1000)
            return upper + index + rng.randint(1, 50)
        if field.type == FieldType.FLOAT:
            upper = float(field.constraints.max_value or 1000.0)
            return round(upper + rng.uniform(1, 10) + index, 2)
        if field.type == FieldType.UUID:
            return str(uuid4())
        if field.type == FieldType.EMAIL:
            return f"user{index + rng.randint(1000, 9999)}@example.com"
        if field.type == FieldType.PHONE:
            return f"+1-555-{rng.randint(200, 998)}-{rng.randint(1000, 9999)}"
        return rng.randint(1, 10_000)


def build_fallback_generator() -> FallbackGenerator:
    """Convenience factory to mirror dependency helpers used elsewhere."""
    return FallbackGenerator()
