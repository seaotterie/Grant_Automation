"""
Tests for Network Intelligence Tool
"""

import pytest
from tools.network_intelligence_tool.app import (
    NetworkIntelligenceTool,
    analyze_network_intelligence,
    NetworkIntelligenceInput,
    NETWORK_INTELLIGENCE_COST
)


def test_tool_metadata():
    """Test tool metadata"""
    tool = NetworkIntelligenceTool()
    assert tool.get_tool_name() == "Network Intelligence Tool"
    assert tool.get_tool_version() == "1.0.0"
    assert "network" in tool.get_single_responsibility().lower()


def test_cost_estimation():
    """Test cost estimation"""
    tool = NetworkIntelligenceTool()
    assert tool.get_cost_estimate() == NETWORK_INTELLIGENCE_COST


@pytest.mark.asyncio
async def test_basic_network_analysis():
    """Test basic network analysis"""
    tool = NetworkIntelligenceTool()

    board_members = [
        {"name": "John Smith", "title": "Board Chair", "affiliations": "XYZ Foundation, ABC Corp"},
        {"name": "Jane Doe", "title": "Board Member", "affiliations": "Community Foundation"},
        {"name": "Bob Johnson", "title": "Treasurer", "affiliations": ""}
    ]

    network_input = NetworkIntelligenceInput(
        organization_ein="12-3456789",
        organization_name="Test Nonprofit",
        board_members=board_members
    )

    result = await tool.execute(network_input=network_input)

    assert result.is_success()
    network = result.data

    # Should have board profiles
    assert len(network.board_member_profiles) == 3
    assert all(p.name for p in network.board_member_profiles)

    # Should have network analysis
    assert network.network_analysis is not None
    assert network.network_analysis.network_size > 0


@pytest.mark.asyncio
async def test_funder_connection_analysis():
    """Test funder connection analysis"""
    tool = NetworkIntelligenceTool()

    board_members = [
        {"name": "John Smith", "title": "Board Chair", "affiliations": "Target Foundation, ABC Corp"},
        {"name": "Jane Doe", "title": "Board Member", "affiliations": "Community Foundation"}
    ]

    network_input = NetworkIntelligenceInput(
        organization_ein="12-3456789",
        organization_name="Test Nonprofit",
        board_members=board_members,
        target_funder_name="Target Foundation",
        target_funder_board=["John Smith", "Mary Johnson"]
    )

    result = await tool.execute(network_input=network_input)

    assert result.is_success()
    network = result.data

    # Should have funder analysis
    assert network.funder_connection_analysis is not None
    assert network.funder_connection_analysis.funder_name == "Target Foundation"


def test_input_validation():
    """Test input validation"""
    tool = NetworkIntelligenceTool()

    # Missing network_input
    is_valid, error = tool.validate_inputs()
    assert not is_valid

    # Valid input
    network_input = NetworkIntelligenceInput(
        organization_ein="12-3456789",
        organization_name="Test",
        board_members=[{"name": "Test", "affiliations": ""}]
    )

    is_valid, error = tool.validate_inputs(network_input=network_input)
    assert is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
