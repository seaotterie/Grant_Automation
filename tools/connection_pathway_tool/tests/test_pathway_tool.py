"""
Tests for Connection Pathway Tool.
"""

import pytest
import asyncio
from datetime import datetime
from dataclasses import asdict

from src.core.tool_framework import ToolExecutionContext
from tools.connection_pathway_tool.app.pathway_tool import ConnectionPathwayTool
from tools.connection_pathway_tool.app.pathway_models import (
    ConnectionPathwayInput,
    ConnectionPathwayOutput,
    PathwayStrength,
)


def _make_context() -> ToolExecutionContext:
    return ToolExecutionContext(
        tool_name="connection_pathway",
        tool_version="1.0.0",
        execution_id="test-001",
    )


@pytest.mark.asyncio
async def test_direct_connection(pathway_db):
    """
    Alice is at both seeker (11-1111111) and funder (99-9999999).
    Should find a degree-1 (direct) pathway.
    """
    tool = ConnectionPathwayTool()
    inp = ConnectionPathwayInput(
        profile_id="profile_001",
        target_funder_ein="99-9999999",
        target_funder_name="Target Foundation",
        include_cultivation_strategy=False,
        seeker_org_name="Seeker Nonprofit",
    )
    ctx = _make_context()

    output: ConnectionPathwayOutput = await tool._execute(
        ctx, input_data=inp, db_path=pathway_db
    )

    assert output.total_pathways_found >= 1

    # At least one pathway should be degree 1 (Alice)
    direct = [p for p in output.pathways if p.degree == 1]
    assert len(direct) >= 1, "Expected at least one direct (degree-1) pathway"
    assert direct[0].strength == PathwayStrength.DIRECT
    assert direct[0].aggregate_strength >= 0.9

    # Best pathway should be direct
    assert output.best_pathway is not None
    assert output.best_pathway["degree"] == 1

    # Proximity score should be in the 80-100 band
    assert output.network_proximity_score >= 80.0


@pytest.mark.asyncio
async def test_two_hop_pathway(pathway_db):
    """
    Bob (seeker) -> Intermediary Org -> Carol -> Funder.
    Should find a degree-2 pathway.
    """
    tool = ConnectionPathwayTool()
    inp = ConnectionPathwayInput(
        profile_id="profile_001",
        target_funder_ein="99-9999999",
        target_funder_name="Target Foundation",
        max_hops=2,
        include_cultivation_strategy=False,
        seeker_org_name="Seeker Nonprofit",
    )
    ctx = _make_context()

    output: ConnectionPathwayOutput = await tool._execute(
        ctx, input_data=inp, db_path=pathway_db
    )

    # Should find both degree-1 (Alice) and degree-2 (Bob -> Carol) pathways
    two_hop = [p for p in output.pathways if p.degree == 2]
    assert len(two_hop) >= 1, "Expected at least one two-hop pathway (Bob->Carol)"

    # Verify the two-hop has proper strength
    for pw in two_hop:
        assert pw.strength == PathwayStrength.STRONG
        assert 0.6 <= pw.aggregate_strength <= 1.0

    # Coverage summary should mention both
    assert "direct" in output.coverage_summary.lower() or "two-hop" in output.coverage_summary.lower()


@pytest.mark.asyncio
async def test_no_pathways(no_connection_db):
    """
    Seeker has people but funder has no people in the DB.
    Should return score around 5 and no pathways.
    """
    tool = ConnectionPathwayTool()
    inp = ConnectionPathwayInput(
        profile_id="profile_001",
        target_funder_ein="99-9999999",
        target_funder_name="Target Foundation",
        include_cultivation_strategy=False,
        seeker_org_name="Seeker Nonprofit",
    )
    ctx = _make_context()

    output: ConnectionPathwayOutput = await tool._execute(
        ctx, input_data=inp, db_path=no_connection_db
    )

    assert output.total_pathways_found == 0
    assert output.pathways == []
    assert output.best_pathway is None
    assert output.network_proximity_score == 5.0
    assert "no pathways" in output.coverage_summary.lower()
    assert len(output.recommendations) >= 1


@pytest.mark.asyncio
async def test_network_proximity_scoring(pathway_db):
    """
    Verify that proximity scores fall in the correct bands based on
    best pathway degree.
    """
    tool = ConnectionPathwayTool()

    # With max_hops=4, should find direct (Alice) as best → 80-100 band
    inp = ConnectionPathwayInput(
        profile_id="profile_001",
        target_funder_ein="99-9999999",
        target_funder_name="Target Foundation",
        max_hops=4,
        include_cultivation_strategy=False,
    )
    ctx = _make_context()
    output = await tool._execute(ctx, input_data=inp, db_path=pathway_db)

    # Best pathway is degree 1 → score 80-100
    assert 80.0 <= output.network_proximity_score <= 100.0

    # Verify the scoring utility directly
    from tools.connection_pathway_tool.app.pathway_models import IntroductionPathway

    # Degree 2 only → should be 55-80
    fake_pw = IntroductionPathway(
        pathway_id="fake1",
        degree=2,
        strength=PathwayStrength.STRONG,
        aggregate_strength=0.8,
        nodes=[],
        connection_basis="test",
    )
    score_2 = tool._compute_proximity_score([fake_pw])
    assert 55.0 <= score_2 <= 80.0

    # Degree 3 only → should be 30-55
    fake_pw_3 = IntroductionPathway(
        pathway_id="fake2",
        degree=3,
        strength=PathwayStrength.MODERATE,
        aggregate_strength=0.5,
        nodes=[],
        connection_basis="test",
    )
    score_3 = tool._compute_proximity_score([fake_pw_3])
    assert 30.0 <= score_3 <= 55.0

    # Degree 4 only → should be 15-30
    fake_pw_4 = IntroductionPathway(
        pathway_id="fake3",
        degree=4,
        strength=PathwayStrength.WEAK,
        aggregate_strength=0.3,
        nodes=[],
        connection_basis="test",
    )
    score_4 = tool._compute_proximity_score([fake_pw_4])
    assert 15.0 <= score_4 <= 30.0


@pytest.mark.asyncio
async def test_fallback_to_memberships(empty_people_db):
    """
    When people table is empty, the tool should fall back to
    network_memberships and still find pathways.
    """
    tool = ConnectionPathwayTool()
    inp = ConnectionPathwayInput(
        profile_id="profile_001",
        target_funder_ein="99-9999999",
        target_funder_name="Target Foundation",
        include_cultivation_strategy=False,
        seeker_org_name="Seeker Nonprofit",
    )
    ctx = _make_context()

    output: ConnectionPathwayOutput = await tool._execute(
        ctx, input_data=inp, db_path=empty_people_db
    )

    # Amy Lin is at both seeker and funder via network_memberships
    assert output.total_pathways_found >= 1

    direct = [p for p in output.pathways if p.degree == 1]
    assert len(direct) >= 1, "Fallback should find Amy Lin as a direct connection"

    # Verify proximity score is in the direct band
    assert output.network_proximity_score >= 80.0
