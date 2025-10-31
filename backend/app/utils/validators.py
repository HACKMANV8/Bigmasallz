"""Data validators and validation utilities."""

import logging
from typing import Any, Dict, List, Optional, Tuple
import re
from datetime import datetime
from email.utils import parseaddr

from app.models.schema import ColumnType, ColumnSchema

logger = logging.getLogger(__name__)


class DataValidator:
    """Validator for synthetic data quality and constraints."""

    @staticmethod
    def validate_row(
        row: Dict[str, Any], schema_columns: List[ColumnSchema]
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate a single data row against schema.

        Args:
            row: Data row to validate
            schema_columns: Schema column definitions

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check all required columns are present
        expected_columns = {col.name for col in schema_columns}
        actual_columns = set(row.keys())

        missing = expected_columns - actual_columns
        if missing:
            errors.append(f"Missing columns: {missing}")

        # Validate each column
        for col in schema_columns:
            if col.name not in row:
                continue

            value = row[col.name]

            # Type validation
            type_valid, type_error = DataValidator._validate_type(
                value, col.type, col.name
            )
            if not type_valid:
                errors.append(type_error)
                continue

            # Constraint validation
            if col.constraints:
                constraint_valid, constraint_error = (
                    DataValidator._validate_constraints(
                        value, col.constraints, col.name
                    )
                )
                if not constraint_valid:
                    errors.append(constraint_error)

        return len(errors) == 0, errors if errors else None

    @staticmethod
    def _validate_type(
        value: Any, col_type: ColumnType, col_name: str
    ) -> Tuple[bool, Optional[str]]:
        """Validate value type."""
        try:
            if col_type == ColumnType.STRING:
                if not isinstance(value, str):
                    return False, f"{col_name}: Expected string, got {type(value)}"

            elif col_type == ColumnType.INTEGER:
                if not isinstance(value, int) or isinstance(value, bool):
                    return False, f"{col_name}: Expected integer, got {type(value)}"

            elif col_type == ColumnType.FLOAT:
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    return (
                        False,
                        f"{col_name}: Expected float, got {type(value)}",
                    )

            elif col_type == ColumnType.BOOLEAN:
                if not isinstance(value, bool):
                    return False, f"{col_name}: Expected boolean, got {type(value)}"

            elif col_type == ColumnType.DATETIME:
                # Try parsing datetime string
                if isinstance(value, str):
                    try:
                        datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        return (
                            False,
                            f"{col_name}: Invalid datetime format: {value}",
                        )
                else:
                    return (
                        False,
                        f"{col_name}: Expected datetime string, got {type(value)}",
                    )

            elif col_type == ColumnType.DATE:
                if isinstance(value, str):
                    try:
                        datetime.strptime(value, "%Y-%m-%d")
                    except ValueError:
                        return False, f"{col_name}: Invalid date format: {value}"
                else:
                    return (
                        False,
                        f"{col_name}: Expected date string, got {type(value)}",
                    )

            elif col_type == ColumnType.EMAIL:
                if not isinstance(value, str) or not DataValidator._is_valid_email(
                    value
                ):
                    return False, f"{col_name}: Invalid email: {value}"

            elif col_type == ColumnType.PHONE:
                if not isinstance(value, str):
                    return False, f"{col_name}: Expected phone string"

            elif col_type == ColumnType.URL:
                if not isinstance(value, str) or not DataValidator._is_valid_url(
                    value
                ):
                    return False, f"{col_name}: Invalid URL: {value}"

            elif col_type == ColumnType.UUID:
                if not isinstance(value, str) or not DataValidator._is_valid_uuid(
                    value
                ):
                    return False, f"{col_name}: Invalid UUID: {value}"

            elif col_type == ColumnType.JSON:
                if not isinstance(value, (dict, list)):
                    return False, f"{col_name}: Expected JSON object or array"

            return True, None

        except Exception as e:
            logger.error(f"Type validation error: {str(e)}")
            return False, f"{col_name}: Validation error: {str(e)}"

    @staticmethod
    def _validate_constraints(
        value: Any, constraints: Dict[str, Any], col_name: str
    ) -> Tuple[bool, Optional[str]]:
        """Validate value constraints."""
        try:
            # Min/max for numbers
            if "min" in constraints:
                if isinstance(value, (int, float)) and value < constraints["min"]:
                    return (
                        False,
                        f"{col_name}: Value {value} below minimum {constraints['min']}",
                    )

            if "max" in constraints:
                if isinstance(value, (int, float)) and value > constraints["max"]:
                    return (
                        False,
                        f"{col_name}: Value {value} above maximum {constraints['max']}",
                    )

            # Length constraints for strings
            if "min_length" in constraints:
                if (
                    isinstance(value, str)
                    and len(value) < constraints["min_length"]
                ):
                    return (
                        False,
                        f"{col_name}: Length below minimum {constraints['min_length']}",
                    )

            if "max_length" in constraints:
                if (
                    isinstance(value, str)
                    and len(value) > constraints["max_length"]
                ):
                    return (
                        False,
                        f"{col_name}: Length above maximum {constraints['max_length']}",
                    )

            # Pattern matching
            if "pattern" in constraints and isinstance(value, str):
                pattern = constraints["pattern"]
                if not re.match(pattern, value):
                    return (
                        False,
                        f"{col_name}: Value doesn't match pattern {pattern}",
                    )

            # Enum values
            if "enum" in constraints:
                if value not in constraints["enum"]:
                    return (
                        False,
                        f"{col_name}: Value not in allowed values: {constraints['enum']}",
                    )

            return True, None

        except Exception as e:
            logger.error(f"Constraint validation error: {str(e)}")
            return False, f"{col_name}: Constraint validation error: {str(e)}"

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Check if string is a valid email."""
        try:
            name, addr = parseaddr(email)
            return "@" in addr and "." in addr.split("@")[1]
        except:
            return False

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if string is a valid URL."""
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        return bool(url_pattern.match(url))

    @staticmethod
    def _is_valid_uuid(uuid_str: str) -> bool:
        """Check if string is a valid UUID."""
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        return bool(uuid_pattern.match(uuid_str))

    @staticmethod
    def validate_batch(
        rows: List[Dict[str, Any]], schema_columns: List[ColumnSchema]
    ) -> Tuple[List[Dict[str, Any]], List[Tuple[int, List[str]]]]:
        """
        Validate a batch of rows.

        Args:
            rows: List of data rows
            schema_columns: Schema columns

        Returns:
            Tuple of (valid_rows, errors) where errors is list of (index, error_messages)
        """
        valid_rows = []
        errors = []

        for idx, row in enumerate(rows):
            is_valid, error_messages = DataValidator.validate_row(
                row, schema_columns
            )

            if is_valid:
                valid_rows.append(row)
            else:
                errors.append((idx, error_messages))

        logger.debug(
            f"Validated batch: {len(valid_rows)} valid, {len(errors)} invalid"
        )

        return valid_rows, errors
