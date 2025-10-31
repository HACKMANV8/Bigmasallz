"""Test suite for validators."""

import pytest

from src.core.models import FieldConstraint, FieldDefinition, FieldType
from src.utils.validators import validate_field_value


def test_string_validation():
    """Test string field validation."""
    field = FieldDefinition(
        name="username",
        type=FieldType.STRING,
        constraints=FieldConstraint(
            min_length=3,
            max_length=20
        )
    )

    # Valid
    is_valid, error = validate_field_value("john_doe", field)
    assert is_valid is True
    assert error is None

    # Too short
    is_valid, error = validate_field_value("ab", field)
    assert is_valid is False

    # Too long
    is_valid, error = validate_field_value("a" * 30, field)
    assert is_valid is False


def test_integer_validation():
    """Test integer field validation."""
    field = FieldDefinition(
        name="age",
        type=FieldType.INTEGER,
        constraints=FieldConstraint(
            min_value=18,
            max_value=100
        )
    )

    # Valid
    is_valid, error = validate_field_value(25, field)
    assert is_valid is True

    # Too small
    is_valid, error = validate_field_value(10, field)
    assert is_valid is False

    # Too large
    is_valid, error = validate_field_value(150, field)
    assert is_valid is False


def test_email_validation():
    """Test email field validation."""
    field = FieldDefinition(
        name="email",
        type=FieldType.EMAIL
    )

    # Valid
    is_valid, error = validate_field_value("user@example.com", field)
    assert is_valid is True

    # Invalid
    is_valid, error = validate_field_value("not-an-email", field)
    assert is_valid is False


def test_enum_validation():
    """Test enum field validation."""
    field = FieldDefinition(
        name="status",
        type=FieldType.ENUM,
        constraints=FieldConstraint(
            enum_values=["active", "inactive", "pending"]
        )
    )

    # Valid
    is_valid, error = validate_field_value("active", field)
    assert is_valid is True

    # Invalid
    is_valid, error = validate_field_value("invalid", field)
    assert is_valid is False


def test_nullable_validation():
    """Test nullable constraint."""
    field = FieldDefinition(
        name="optional_field",
        type=FieldType.STRING,
        constraints=FieldConstraint(nullable=True)
    )

    # Null is OK
    is_valid, error = validate_field_value(None, field)
    assert is_valid is True

    # Now make it non-nullable
    field.constraints.nullable = False
    is_valid, error = validate_field_value(None, field)
    assert is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
