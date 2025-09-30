"""Tests for EIN Validator Tool"""

import pytest
from tools.ein_validator_tool.app.ein_tool import EINValidatorTool, EINValidatorInput, EINValidationStatus


@pytest.mark.asyncio
async def test_valid_ein():
    tool = EINValidatorTool()
    ein_input = EINValidatorInput(ein="12-3456789")
    result = await tool.execute(ein_input=ein_input)
    assert result.is_success()
    assert result.data.is_valid_format is True
    assert result.data.validation_status == EINValidationStatus.VALID


@pytest.mark.asyncio
async def test_invalid_ein_format():
    tool = EINValidatorTool()
    ein_input = EINValidatorInput(ein="12-345")
    result = await tool.execute(ein_input=ein_input)
    assert result.is_success()
    assert result.data.is_valid_format is False
    assert result.data.validation_status == EINValidationStatus.INVALID_FORMAT


@pytest.mark.asyncio
async def test_invalid_ein_prefix():
    tool = EINValidatorTool()
    ein_input = EINValidatorInput(ein="00-1234567")
    result = await tool.execute(ein_input=ein_input)
    assert result.is_success()
    assert result.data.is_valid_format is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
