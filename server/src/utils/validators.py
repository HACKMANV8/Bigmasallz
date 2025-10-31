"""Validation utilities for data and schema."""

import re
from datetime import datetime
from typing import Any, List, Optional
from email_validator import validate_email, EmailNotValidError

from src.core.models import FieldType, FieldDefinition, FieldConstraint
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Validation error exception."""
    pass


def validate_field_value(
    value: Any,
    field: FieldDefinition
) -> tuple[bool, Optional[str]]:
    """Validate a single field value against its definition.
    
    Args:
        value: The value to validate
        field: Field definition with type and constraints
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    constraints = field.constraints
    
    # Check nullable
    if value is None:
        if not constraints.nullable:
            return False, f"Field '{field.name}' cannot be null"
        return True, None
    
    # Type-specific validation
    try:
        if field.type == FieldType.STRING:
            return _validate_string(value, constraints)
        elif field.type == FieldType.INTEGER:
            return _validate_integer(value, constraints)
        elif field.type == FieldType.FLOAT:
            return _validate_float(value, constraints)
        elif field.type == FieldType.BOOLEAN:
            return _validate_boolean(value)
        elif field.type == FieldType.DATE:
            return _validate_date(value)
        elif field.type == FieldType.DATETIME:
            return _validate_datetime(value)
        elif field.type == FieldType.EMAIL:
            return _validate_email_field(value)
        elif field.type == FieldType.PHONE:
            return _validate_phone(value)
        elif field.type == FieldType.UUID:
            return _validate_uuid(value)
        elif field.type == FieldType.ENUM:
            return _validate_enum(value, constraints)
        elif field.type == FieldType.JSON:
            return True, None  # Already parsed JSON
        elif field.type == FieldType.ARRAY:
            return _validate_array(value, constraints)
        else:
            return False, f"Unknown field type: {field.type}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def _validate_string(value: Any, constraints: FieldConstraint) -> tuple[bool, Optional[str]]:
    """Validate string value."""
    if not isinstance(value, str):
        return False, "Value must be a string"
    
    if constraints.min_length and len(value) < constraints.min_length:
        return False, f"String length must be at least {constraints.min_length}"
    
    if constraints.max_length and len(value) > constraints.max_length:
        return False, f"String length must not exceed {constraints.max_length}"
    
    if constraints.pattern and not re.match(constraints.pattern, value):
        return False, f"String does not match pattern: {constraints.pattern}"
    
    return True, None


def _validate_integer(value: Any, constraints: FieldConstraint) -> tuple[bool, Optional[str]]:
    """Validate integer value."""
    if not isinstance(value, int) or isinstance(value, bool):
        try:
            value = int(value)
        except (ValueError, TypeError):
            return False, "Value must be an integer"
    
    if constraints.min_value is not None and value < constraints.min_value:
        return False, f"Value must be at least {constraints.min_value}"
    
    if constraints.max_value is not None and value > constraints.max_value:
        return False, f"Value must not exceed {constraints.max_value}"
    
    return True, None


def _validate_float(value: Any, constraints: FieldConstraint) -> tuple[bool, Optional[str]]:
    """Validate float value."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        try:
            value = float(value)
        except (ValueError, TypeError):
            return False, "Value must be a number"
    
    if constraints.min_value is not None and value < constraints.min_value:
        return False, f"Value must be at least {constraints.min_value}"
    
    if constraints.max_value is not None and value > constraints.max_value:
        return False, f"Value must not exceed {constraints.max_value}"
    
    return True, None


def _validate_boolean(value: Any) -> tuple[bool, Optional[str]]:
    """Validate boolean value."""
    if not isinstance(value, bool):
        if isinstance(value, str):
            if value.lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                return False, "Value must be a boolean"
        else:
            return False, "Value must be a boolean"
    return True, None


def _validate_date(value: Any) -> tuple[bool, Optional[str]]:
    """Validate date value."""
    if isinstance(value, str):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True, None
        except ValueError:
            return False, "Date must be in YYYY-MM-DD format"
    return False, "Date must be a string in YYYY-MM-DD format"


def _validate_datetime(value: Any) -> tuple[bool, Optional[str]]:
    """Validate datetime value."""
    if isinstance(value, str):
        # Try common datetime formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
        ]
        for fmt in formats:
            try:
                datetime.strptime(value, fmt)
                return True, None
            except ValueError:
                continue
        return False, "Datetime format not recognized"
    return False, "Datetime must be a string"


def _validate_email_field(value: Any) -> tuple[bool, Optional[str]]:
    """Validate email value."""
    if not isinstance(value, str):
        return False, "Email must be a string"
    
    try:
        validate_email(value, check_deliverability=False)
        return True, None
    except EmailNotValidError as e:
        return False, f"Invalid email: {str(e)}"


def _validate_phone(value: Any) -> tuple[bool, Optional[str]]:
    """Validate phone number value."""
    if not isinstance(value, str):
        return False, "Phone number must be a string"
    
    # Basic phone validation - allow digits, spaces, dashes, parentheses, plus
    pattern = r'^[\d\s\-\(\)\+]+$'
    if not re.match(pattern, value):
        return False, "Invalid phone number format"
    
    # Check if it has enough digits
    digits = re.sub(r'\D', '', value)
    if len(digits) < 10:
        return False, "Phone number must have at least 10 digits"
    
    return True, None


def _validate_uuid(value: Any) -> tuple[bool, Optional[str]]:
    """Validate UUID value."""
    if not isinstance(value, str):
        return False, "UUID must be a string"
    
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, value.lower()):
        return False, "Invalid UUID format"
    
    return True, None


def _validate_enum(value: Any, constraints: FieldConstraint) -> tuple[bool, Optional[str]]:
    """Validate enum value."""
    if not constraints.enum_values:
        return False, "Enum values not specified"
    
    if value not in constraints.enum_values:
        return False, f"Value must be one of: {', '.join(map(str, constraints.enum_values))}"
    
    return True, None


def _validate_array(value: Any, constraints: FieldConstraint) -> tuple[bool, Optional[str]]:
    """Validate array value."""
    if not isinstance(value, list):
        return False, "Value must be an array"
    
    if constraints.min_length and len(value) < constraints.min_length:
        return False, f"Array length must be at least {constraints.min_length}"
    
    if constraints.max_length and len(value) > constraints.max_length:
        return False, f"Array length must not exceed {constraints.max_length}"
    
    return True, None


def validate_row(row: dict, schema: Any) -> List[str]:
    """Validate an entire row against schema.
    
    Args:
        row: Data row as dictionary
        schema: DataSchema object
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Check all required fields are present
    for field in schema.fields:
        if field.name not in row and not field.constraints.nullable:
            errors.append(f"Missing required field: {field.name}")
            continue
        
        if field.name in row:
            is_valid, error_msg = validate_field_value(row[field.name], field)
            if not is_valid:
                errors.append(f"{field.name}: {error_msg}")
    
    return errors
