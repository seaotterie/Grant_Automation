"""
BAML Validator
Validation utilities for BAML (Basically A Markup Language) structured outputs.

BAML ensures structured, typed outputs from AI tools, eliminating parsing errors.
This validator helps ensure tool outputs comply with expected schemas.
"""

from typing import Any, Dict, Optional, Type, get_type_hints, get_origin, get_args
from dataclasses import is_dataclass, fields
from datetime import datetime
from enum import Enum


class ValidationError(Exception):
    """Raised when BAML validation fails."""
    pass


class BAMLValidator:
    """
    Validator for BAML-style structured outputs.

    Factor 4: Ensures tools return predictable, structured data
    that eliminates parsing errors.
    """

    @staticmethod
    def validate_dataclass(obj: Any, expected_type: Type) -> tuple[bool, Optional[str]]:
        """
        Validate that an object matches expected dataclass structure.

        Args:
            obj: Object to validate
            expected_type: Expected dataclass type

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not is_dataclass(expected_type):
            return False, f"{expected_type} is not a dataclass"

        if not isinstance(obj, expected_type):
            return False, f"Expected {expected_type.__name__}, got {type(obj).__name__}"

        # Validate all fields
        for field in fields(expected_type):
            if not hasattr(obj, field.name):
                return False, f"Missing field: {field.name}"

            field_value = getattr(obj, field.name)
            field_type = field.type

            # Skip None values for Optional fields
            if field_value is None:
                origin = get_origin(field_type)
                if origin is not type(None):  # Not Optional
                    continue

            # Validate field type
            is_valid, error = BAMLValidator._validate_field_type(
                field_value,
                field_type,
                field.name
            )

            if not is_valid:
                return False, error

        return True, None

    @staticmethod
    def _validate_field_type(
        value: Any,
        expected_type: Type,
        field_name: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a single field's type.

        Args:
            value: Field value
            expected_type: Expected type
            field_name: Field name for error messages

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Handle Optional types
        origin = get_origin(expected_type)
        if origin is type(None):
            return True, None

        # Handle Union types (e.g., Optional[str] = Union[str, None])
        if origin is type(None) or str(origin) == "typing.Union":
            args = get_args(expected_type)
            for arg in args:
                if arg is type(None):
                    if value is None:
                        return True, None
                    continue
                if isinstance(value, arg):
                    return True, None
            return False, f"Field '{field_name}' value {value} doesn't match any Union type"

        # Handle List types
        if origin is list:
            if not isinstance(value, list):
                return False, f"Field '{field_name}' should be list, got {type(value).__name__}"
            return True, None

        # Handle Dict types
        if origin is dict:
            if not isinstance(value, dict):
                return False, f"Field '{field_name}' should be dict, got {type(value).__name__}"
            return True, None

        # Handle basic types
        if not isinstance(value, expected_type):
            return False, f"Field '{field_name}' should be {expected_type.__name__}, got {type(value).__name__}"

        return True, None

    @staticmethod
    def validate_schema(data: Dict[str, Any], schema: Dict[str, Type]) -> tuple[bool, Optional[str]]:
        """
        Validate data against a schema definition.

        Args:
            data: Data dictionary to validate
            schema: Schema definition (field_name -> type)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for missing required fields
        for field_name, field_type in schema.items():
            if field_name not in data:
                return False, f"Missing required field: {field_name}"

            value = data[field_name]

            # Validate type
            is_valid, error = BAMLValidator._validate_field_type(
                value,
                field_type,
                field_name
            )

            if not is_valid:
                return False, error

        return True, None

    @staticmethod
    def validate_enum(value: Any, enum_class: Type[Enum]) -> tuple[bool, Optional[str]]:
        """
        Validate that a value is a valid enum member.

        Args:
            value: Value to validate
            enum_class: Enum class

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, enum_class):
            try:
                enum_class(value)
            except ValueError:
                valid_values = [e.value for e in enum_class]
                return False, f"Invalid enum value. Must be one of: {valid_values}"

        return True, None

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any],
        required_fields: list[str]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that all required fields are present.

        Args:
            data: Data dictionary
            required_fields: List of required field names

        Returns:
            Tuple of (is_valid, error_message)
        """
        missing = [field for field in required_fields if field not in data]

        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"

        return True, None

    @staticmethod
    def validate_string_not_empty(value: str, field_name: str) -> tuple[bool, Optional[str]]:
        """
        Validate that a string is not empty.

        Args:
            value: String value
            field_name: Field name for error messages

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, str):
            return False, f"Field '{field_name}' must be a string"

        if not value or not value.strip():
            return False, f"Field '{field_name}' cannot be empty"

        return True, None

    @staticmethod
    def validate_number_range(
        value: float,
        field_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that a number is within a specified range.

        Args:
            value: Numeric value
            field_name: Field name for error messages
            min_value: Minimum allowed value (optional)
            max_value: Maximum allowed value (optional)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, (int, float)):
            return False, f"Field '{field_name}' must be a number"

        if min_value is not None and value < min_value:
            return False, f"Field '{field_name}' must be >= {min_value}"

        if max_value is not None and value > max_value:
            return False, f"Field '{field_name}' must be <= {max_value}"

        return True, None

    @staticmethod
    def validate_list_not_empty(value: list, field_name: str) -> tuple[bool, Optional[str]]:
        """
        Validate that a list is not empty.

        Args:
            value: List value
            field_name: Field name for error messages

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, list):
            return False, f"Field '{field_name}' must be a list"

        if not value:
            return False, f"Field '{field_name}' cannot be empty"

        return True, None


def validate_tool_output(output: Any, expected_type: Type) -> None:
    """
    Validate tool output against expected type.

    Raises ValidationError if validation fails.

    Args:
        output: Tool output to validate
        expected_type: Expected output type

    Raises:
        ValidationError: If validation fails
    """
    if is_dataclass(expected_type):
        is_valid, error = BAMLValidator.validate_dataclass(output, expected_type)
    else:
        is_valid, error = BAMLValidator._validate_field_type(
            output,
            expected_type,
            "output"
        )

    if not is_valid:
        raise ValidationError(f"Tool output validation failed: {error}")


# Example BAML schema definitions for common tool outputs

NONPROFIT_PROFILE_SCHEMA = {
    "ein": str,
    "name": str,
    "ntee_code": str,
    "state": str,
    "revenue": float,
    "assets": float,
    "founded_year": int,
}

OPPORTUNITY_SCHEMA = {
    "opportunity_id": str,
    "title": str,
    "funder": str,
    "amount_min": float,
    "amount_max": float,
    "deadline": str,
    "eligibility": list,
}

GRANT_INTELLIGENCE_SCHEMA = {
    "foundation_ein": str,
    "total_grants_paid": float,
    "grant_count": int,
    "avg_grant_size": float,
    "largest_grant": float,
    "smallest_grant": float,
    "grant_focus_areas": list,
}