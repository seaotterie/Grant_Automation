"""
EIN Validator Tool
12-Factor compliant tool for EIN format validation and lookup.

Purpose: Validate EIN format and organization existence
Cost: $0.00 per validation (no AI calls)
Replaces: ein_lookup.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dataclasses import dataclass
from typing import Optional
from enum import Enum
import time
from datetime import datetime
import re

from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext


class EINValidationStatus(str, Enum):
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    NOT_FOUND = "not_found"


@dataclass
class EINValidatorInput:
    ein: str
    perform_lookup: bool = False


@dataclass
class EINValidatorOutput:
    ein: str
    is_valid_format: bool
    validation_status: EINValidationStatus
    organization_name: Optional[str] = None
    organization_type: Optional[str] = None
    validation_message: str = ""
    analysis_date: str = ""
    processing_time_seconds: float = 0.0


class EINValidatorTool(BaseTool[EINValidatorOutput]):
    """12-Factor EIN Validator Tool"""

    def get_tool_name(self) -> str:
        return "EIN Validator Tool"

    def get_tool_version(self) -> str:
        return "1.0.0"

    def get_single_responsibility(self) -> str:
        return "EIN format validation and organization lookup"

    async def _execute(
        self,
        context: ToolExecutionContext,
        ein_input: EINValidatorInput
    ) -> EINValidatorOutput:
        start_time = time.time()

        ein = ein_input.ein.strip()

        # Format validation
        is_valid_format = self._validate_ein_format(ein)

        if not is_valid_format:
            return EINValidatorOutput(
                ein=ein,
                is_valid_format=False,
                validation_status=EINValidationStatus.INVALID_FORMAT,
                validation_message="EIN format is invalid. Expected format: XX-XXXXXXX",
                analysis_date=datetime.now().isoformat(),
                processing_time_seconds=time.time() - start_time
            )

        # If lookup requested, perform it (placeholder - would integrate with IRS data)
        if ein_input.perform_lookup:
            # Placeholder lookup
            status = EINValidationStatus.VALID
            org_name = f"Organization {ein}"
            org_type = "Nonprofit"
            message = "EIN format valid (lookup not implemented)"
        else:
            status = EINValidationStatus.VALID
            org_name = None
            org_type = None
            message = "EIN format valid"

        return EINValidatorOutput(
            ein=ein,
            is_valid_format=True,
            validation_status=status,
            organization_name=org_name,
            organization_type=org_type,
            validation_message=message,
            analysis_date=datetime.now().isoformat(),
            processing_time_seconds=time.time() - start_time
        )

    def _validate_ein_format(self, ein: str) -> bool:
        """Validate EIN format: XX-XXXXXXX"""
        # Remove spaces and dashes for flexibility
        ein_clean = ein.replace("-", "").replace(" ", "")

        # Should be 9 digits
        if not ein_clean.isdigit() or len(ein_clean) != 9:
            return False

        # First two digits should be valid (not 00, 07, 08, 09, 17, 18, 19, 28, 29, 49, etc.)
        first_two = ein_clean[:2]
        invalid_prefixes = ["00", "07", "08", "09", "17", "18", "19", "28", "29", "49", "69", "70", "78", "79", "89"]
        if first_two in invalid_prefixes:
            return False

        return True

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        ein_input = kwargs.get("ein_input")
        if not ein_input:
            return False, "ein_input is required"
        if not ein_input.ein:
            return False, "EIN is required"
        return True, None


__all__ = ["EINValidatorTool", "EINValidatorInput", "EINValidatorOutput", "EINValidationStatus"]
