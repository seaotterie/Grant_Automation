"""
Data Validator Tool
12-Factor compliant tool for workflow data validation.

Purpose: Validate data completeness and quality for workflows
Cost: $0.00 per validation (no AI calls)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dataclasses import dataclass
from typing import Optional, Any, Dict, List
from enum import Enum
import time
from datetime import datetime

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    field_name: str
    severity: ValidationSeverity
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None


@dataclass
class DataValidatorInput:
    data: Dict[str, Any]
    required_fields: List[str]
    optional_fields: Optional[List[str]] = None
    field_types: Optional[Dict[str, type]] = None
    custom_validators: Optional[Dict[str, callable]] = None


@dataclass
class DataValidatorOutput:
    is_valid: bool
    completeness_score: float  # 0-1
    quality_score: float  # 0-1
    issues: List[ValidationIssue]
    validated_data: Dict[str, Any]
    analysis_date: str
    processing_time_seconds: float


class DataValidatorTool(BaseTool[DataValidatorOutput]):
    """12-Factor Data Validator Tool"""

    def get_tool_name(self) -> str:
        return "Data Validator Tool"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "Validate data completeness and quality for workflows"

    async def _execute(
        self,
        context: ToolExecutionContext,
        validator_input: DataValidatorInput
    ) -> DataValidatorOutput:
        start_time = time.time()

        issues = []
        data = validator_input.data

        # Check required fields
        for field in validator_input.required_fields:
            if field not in data or data[field] is None or data[field] == "":
                issues.append(ValidationIssue(
                    field_name=field,
                    severity=ValidationSeverity.ERROR,
                    message=f"Required field '{field}' is missing or empty",
                    expected="Non-empty value",
                    actual=str(data.get(field))
                ))

        # Check field types
        if validator_input.field_types:
            for field, expected_type in validator_input.field_types.items():
                if field in data and data[field] is not None:
                    if not isinstance(data[field], expected_type):
                        issues.append(ValidationIssue(
                            field_name=field,
                            severity=ValidationSeverity.WARNING,
                            message=f"Field '{field}' has incorrect type",
                            expected=expected_type.__name__,
                            actual=type(data[field]).__name__
                        ))

        # Calculate scores
        total_fields = len(validator_input.required_fields) + len(validator_input.optional_fields or [])
        present_fields = sum(1 for f in (validator_input.required_fields + (validator_input.optional_fields or []))
                           if f in data and data[f] is not None and data[f] != "")
        completeness_score = present_fields / total_fields if total_fields > 0 else 0

        errors = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        quality_score = 1.0 - (errors / max(len(validator_input.required_fields), 1))

        is_valid = len([i for i in issues if i.severity == ValidationSeverity.ERROR]) == 0

        return DataValidatorOutput(
            is_valid=is_valid,
            completeness_score=completeness_score,
            quality_score=quality_score,
            issues=issues,
            validated_data=data,
            analysis_date=datetime.now().isoformat(),
            processing_time_seconds=time.time() - start_time
        )

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        validator_input = kwargs.get("validator_input")
        if not validator_input:
            return False, "validator_input is required"
        return True, None


__all__ = ["DataValidatorTool", "DataValidatorInput", "DataValidatorOutput", "ValidationIssue", "ValidationSeverity"]
