"""
Tests for the Human Gateway API — session management, decisions, and investigation.
"""

import pytest
from unittest.mock import patch, AsyncMock

from src.web.routers.gateway import (
    GatewaySession,
    _sessions,
    router,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_SCREENING_RESULTS = [
    {
        "opportunity_id": "opp-001",
        "opportunity_title": "Youth Education Grant",
        "title": "Youth Education Grant",
        "funder": "Smith Foundation",
        "funder_type": "foundation",
        "overall_score": 0.85,
        "strategic_fit_score": 0.90,
        "eligibility_score": 0.80,
        "timing_score": 0.75,
        "financial_score": 0.85,
        "competition_score": 0.70,
        "confidence_level": "high",
        "one_sentence_summary": "Strong alignment with youth education mission.",
        "key_strengths": ["Mission alignment", "Geographic match"],
        "key_concerns": ["Competitive field"],
        "reasoning": "Good fit overall.",
    },
    {
        "opportunity_id": "opp-002",
        "opportunity_title": "Community Health Initiative",
        "title": "Community Health Initiative",
        "funder": "HHS",
        "funder_type": "government",
        "overall_score": 0.62,
        "strategic_fit_score": 0.55,
        "eligibility_score": 0.70,
        "timing_score": 0.80,
        "financial_score": 0.60,
        "competition_score": 0.50,
        "confidence_level": "medium",
        "one_sentence_summary": "Moderate fit, outside core mission area.",
        "key_strengths": ["Large award size"],
        "key_concerns": ["Mission drift risk", "High competition"],
        "reasoning": "Tangential fit.",
    },
    {
        "opportunity_id": "opp-003",
        "opportunity_title": "Arts Enrichment Program",
        "title": "Arts Enrichment Program",
        "funder": "NEA",
        "funder_type": "government",
        "overall_score": 0.41,
        "strategic_fit_score": 0.30,
        "eligibility_score": 0.50,
        "timing_score": 0.60,
        "financial_score": 0.40,
        "competition_score": 0.30,
        "confidence_level": "medium",
        "one_sentence_summary": "Poor fit with organization mission.",
        "key_strengths": [],
        "key_concerns": ["No mission alignment"],
        "reasoning": "Not recommended.",
    },
]

SAMPLE_ORG = {
    "name": "Youth Education Alliance",
    "mission": "Quality education for underserved youth",
}


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear sessions before each test."""
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
def session():
    """Create a pre-populated session."""
    s = GatewaySession("test-session", SAMPLE_SCREENING_RESULTS, SAMPLE_ORG)
    _sessions["test-session"] = s
    return s


# ---------------------------------------------------------------------------
# GatewaySession unit tests
# ---------------------------------------------------------------------------

class TestGatewaySession:

    def test_creates_items_from_results(self, session):
        assert len(session.items) == 3
        assert "opp-001" in session.items
        assert session.items["opp-001"]["decision"] is None

    def test_summary_initial(self, session):
        s = session.summary()
        assert s["total_opportunities"] == 3
        assert s["pending"] == 3
        assert s["passed"] == 0
        assert s["rejected"] == 0

    def test_summary_after_decisions(self, session):
        session.items["opp-001"]["decision"] = "pass"
        session.items["opp-003"]["decision"] = "reject"
        s = session.summary()
        assert s["passed"] == 1
        assert s["rejected"] == 1
        assert s["pending"] == 1
        assert s["decided"] == 2


# ---------------------------------------------------------------------------
# API endpoint tests (using FastAPI TestClient)
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Create a test client for the gateway router."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestCreateSession:

    def test_create_session(self, client):
        resp = client.post("/api/gateway/sessions", json={
            "screening_results": SAMPLE_SCREENING_RESULTS,
            "organization": SAMPLE_ORG,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_opportunities"] == 3
        assert body["pending"] == 3
        assert len(body["opportunities"]) == 3
        # Should be sorted by score descending
        scores = [o["overall_score"] for o in body["opportunities"]]
        assert scores == sorted(scores, reverse=True)

    def test_create_empty_session(self, client):
        resp = client.post("/api/gateway/sessions", json={
            "screening_results": [],
        })
        assert resp.status_code == 200
        assert resp.json()["total_opportunities"] == 0


class TestDecisions:

    def test_pass_decision(self, client, session):
        resp = client.put(
            "/api/gateway/sessions/test-session/opportunities/opp-001/decision",
            json={"decision": "pass"},
        )
        assert resp.status_code == 200
        assert resp.json()["decision"] == "pass"
        assert resp.json()["summary"]["passed"] == 1

    def test_reject_decision(self, client, session):
        resp = client.put(
            "/api/gateway/sessions/test-session/opportunities/opp-003/decision",
            json={"decision": "reject", "reason": "Not aligned with mission"},
        )
        assert resp.status_code == 200
        assert session.items["opp-003"]["decision"] == "reject"
        assert session.items["opp-003"]["decision_reason"] == "Not aligned with mission"

    def test_investigate_decision(self, client, session):
        resp = client.put(
            "/api/gateway/sessions/test-session/opportunities/opp-002/decision",
            json={"decision": "investigate"},
        )
        assert resp.status_code == 200
        assert resp.json()["summary"]["investigating"] == 1

    def test_invalid_decision(self, client, session):
        resp = client.put(
            "/api/gateway/sessions/test-session/opportunities/opp-001/decision",
            json={"decision": "maybe"},
        )
        assert resp.status_code == 400

    def test_decision_unknown_opportunity(self, client, session):
        resp = client.put(
            "/api/gateway/sessions/test-session/opportunities/opp-999/decision",
            json={"decision": "pass"},
        )
        assert resp.status_code == 404

    def test_decision_unknown_session(self, client):
        resp = client.put(
            "/api/gateway/sessions/no-such-session/opportunities/opp-001/decision",
            json={"decision": "pass"},
        )
        assert resp.status_code == 404

    def test_change_decision(self, client, session):
        # First pass, then reject
        client.put(
            "/api/gateway/sessions/test-session/opportunities/opp-001/decision",
            json={"decision": "pass"},
        )
        resp = client.put(
            "/api/gateway/sessions/test-session/opportunities/opp-001/decision",
            json={"decision": "reject"},
        )
        assert resp.json()["summary"]["passed"] == 0
        assert resp.json()["summary"]["rejected"] == 1


class TestBatchDecision:

    def test_batch_reject(self, client, session):
        resp = client.post(
            "/api/gateway/sessions/test-session/batch-decision",
            json={
                "opportunity_ids": ["opp-002", "opp-003"],
                "decision": "reject",
                "reason": "Low priority",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["updated"] == 2
        assert resp.json()["summary"]["rejected"] == 2


class TestPassedOpportunities:

    def test_get_passed_with_cost(self, client, session):
        session.items["opp-001"]["decision"] = "pass"
        session.items["opp-001"]["selected_depth"] = "premium"
        session.items["opp-002"]["decision"] = "pass"
        session.items["opp-002"]["selected_depth"] = "essentials"

        resp = client.get("/api/gateway/sessions/test-session/passed")
        assert resp.status_code == 200
        body = resp.json()
        assert body["passed_count"] == 2
        assert body["estimated_cost"] == 10.00  # $8 + $2


class TestInvestigation:

    def test_investigate_without_ai(self, client, session):
        """When AI is not available, returns context-only response."""
        resp = client.post(
            "/api/gateway/sessions/test-session/investigate/opp-002",
            json={"question": "Is this funder known for education grants?"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["opportunity_id"] == "opp-002"
        assert "question" in body["answer"] or "investigation" in body["answer"].lower() or len(body["answer"]) > 0

    def test_investigate_stores_notes(self, client, session):
        client.post(
            "/api/gateway/sessions/test-session/investigate/opp-001",
            json={"question": "First question"},
        )
        client.post(
            "/api/gateway/sessions/test-session/investigate/opp-001",
            json={"question": "Second question"},
        )
        notes = session.items["opp-001"]["investigation_notes"]
        assert len(notes) == 2
        assert notes[0]["question"] == "First question"
        assert notes[1]["question"] == "Second question"


class TestListSessions:

    def test_list_empty(self, client):
        resp = client.get("/api/gateway/sessions")
        assert resp.status_code == 200
        assert resp.json()["sessions"] == []

    def test_list_with_session(self, client, session):
        resp = client.get("/api/gateway/sessions")
        assert resp.status_code == 200
        assert len(resp.json()["sessions"]) == 1
        assert resp.json()["sessions"][0]["session_id"] == "test-session"
