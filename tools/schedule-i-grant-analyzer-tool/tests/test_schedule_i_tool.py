"""Tests for Schedule I Grant Analyzer Tool"""

import pytest
from tools.schedule_i_grant_analyzer_tool.app import (
    ScheduleIGrantAnalyzerTool,
    ScheduleIGrantAnalyzerInput,
    SCHEDULE_I_ANALYZER_COST
)


def test_tool_metadata():
    tool = ScheduleIGrantAnalyzerTool()
    assert tool.get_tool_name() == "Schedule I Grant Analyzer Tool"
    assert tool.get_cost_estimate() == SCHEDULE_I_ANALYZER_COST


@pytest.mark.asyncio
async def test_basic_analysis():
    tool = ScheduleIGrantAnalyzerTool()

    grants = [
        {"recipient_name": "University A", "amount": 50000, "purpose": "Education program", "state": "VA"},
        {"recipient_name": "Hospital B", "amount": 25000, "purpose": "Health services", "state": "MD"},
        {"recipient_name": "Museum C", "amount": 10000, "purpose": "Arts program", "state": "VA"}
    ]

    analyzer_input = ScheduleIGrantAnalyzerInput(
        foundation_ein="12-3456789",
        foundation_name="Test Foundation",
        grants=grants,
        tax_year=2023
    )

    result = await tool.execute(analyzer_input=analyzer_input)

    assert result.is_success()
    output = result.data
    assert len(output.processed_grants) == 3
    assert output.granting_patterns.total_grants == 3
    assert output.granting_patterns.total_amount == 85000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
