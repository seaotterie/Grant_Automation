"""Tests for Data Validator Tool"""

import pytest
from tools.data_validator_tool.app.validator_tool import DataValidatorTool, DataValidatorInput


@pytest.mark.asyncio
async def test_valid_data():
    tool = DataValidatorTool()
    validator_input = DataValidatorInput(
        data={"name": "Test", "ein": "12-3456789"},
        required_fields=["name", "ein"]
    )
    result = await tool.execute(validator_input=validator_input)
    assert result.is_success()
    assert result.data.is_valid is True


@pytest.mark.asyncio
async def test_missing_required_field():
    tool = DataValidatorTool()
    validator_input = DataValidatorInput(
        data={"name": "Test"},
        required_fields=["name", "ein"]
    )
    result = await tool.execute(validator_input=validator_input)
    assert result.is_success()
    assert result.data.is_valid is False
    assert len(result.data.issues) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
