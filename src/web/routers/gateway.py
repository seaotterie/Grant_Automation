"""
Human Gateway API Router
REST API endpoints for human review of screening results.

The gateway sits between automated screening (Tool 1) and deep intelligence
(Tool 2). It lets humans review AI screening scores, make pass/reject/investigate
decisions, and send selected opportunities to deep analysis.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import logging
import uuid

router = APIRouter(prefix="/api/gateway", tags=["gateway"])
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory session store (single-user MVP — persists for server lifetime)
# ---------------------------------------------------------------------------

_sessions: Dict[str, "GatewaySession"] = {}


class GatewaySession:
    """Holds screening results and human decisions for one review session."""

    def __init__(self, session_id: str, screening_results: List[Dict[str, Any]],
                 organization: Dict[str, Any]):
        self.session_id = session_id
        self.created_at = datetime.utcnow()
        self.organization = organization
        # Store each opportunity with its screening score + decision state
        self.items: Dict[str, Dict[str, Any]] = {}
        for opp in screening_results:
            opp_id = opp.get("opportunity_id", str(uuid.uuid4()))
            self.items[opp_id] = {
                **opp,
                "decision": None,       # "pass" | "reject" | "investigate" | None
                "decision_reason": None,
                "decided_at": None,
                "investigation_notes": None,
                "selected_depth": "essentials",  # default deep-analysis depth
            }

    def summary(self) -> Dict[str, Any]:
        decisions = [it["decision"] for it in self.items.values()]
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "total_opportunities": len(self.items),
            "decided": sum(1 for d in decisions if d is not None),
            "passed": sum(1 for d in decisions if d == "pass"),
            "rejected": sum(1 for d in decisions if d == "reject"),
            "investigating": sum(1 for d in decisions if d == "investigate"),
            "pending": sum(1 for d in decisions if d is None),
        }


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    """Create a new gateway review session from screening results."""
    screening_results: List[Dict[str, Any]] = Field(
        ..., description="List of scored opportunities from screening tool"
    )
    organization: Dict[str, Any] = Field(
        default_factory=dict, description="Organization profile context"
    )


class DecisionRequest(BaseModel):
    """Record a human decision on an opportunity."""
    decision: str = Field(
        ..., description="pass | reject | investigate"
    )
    reason: Optional[str] = Field(
        None, description="Optional reason for the decision"
    )
    selected_depth: Optional[str] = Field(
        None, description="Deep analysis depth: essentials | premium"
    )


class InvestigateRequest(BaseModel):
    """Request a targeted AI investigation of a specific concern."""
    question: str = Field(
        ..., description="Specific question or concern to investigate"
    )


class BatchDecisionRequest(BaseModel):
    """Apply the same decision to multiple opportunities at once."""
    opportunity_ids: List[str]
    decision: str = Field(..., description="pass | reject")
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/sessions")
async def create_session(request: CreateSessionRequest):
    """Create a new review session from screening results."""
    session_id = f"gw_{uuid.uuid4().hex[:12]}"
    session = GatewaySession(session_id, request.screening_results, request.organization)
    _sessions[session_id] = session

    logger.info(
        f"Gateway session created: {session_id} with "
        f"{len(session.items)} opportunities"
    )

    return {
        "session_id": session_id,
        **session.summary(),
        "opportunities": _format_opportunities(session),
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get full session state including all opportunities and decisions."""
    session = _get_session(session_id)
    return {
        **session.summary(),
        "organization": session.organization,
        "opportunities": _format_opportunities(session),
    }


@router.get("/sessions/{session_id}/summary")
async def get_session_summary(session_id: str):
    """Get just the decision summary counts."""
    session = _get_session(session_id)
    return session.summary()


@router.put("/sessions/{session_id}/opportunities/{opportunity_id}/decision")
async def record_decision(session_id: str, opportunity_id: str, request: DecisionRequest):
    """Record a pass/reject/investigate decision for an opportunity."""
    session = _get_session(session_id)

    if opportunity_id not in session.items:
        raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

    if request.decision not in ("pass", "reject", "investigate"):
        raise HTTPException(status_code=400, detail="Decision must be pass, reject, or investigate")

    item = session.items[opportunity_id]
    item["decision"] = request.decision
    item["decision_reason"] = request.reason
    item["decided_at"] = datetime.utcnow().isoformat()

    if request.selected_depth:
        item["selected_depth"] = request.selected_depth

    logger.info(
        f"Decision recorded: session={session_id}, opp={opportunity_id}, "
        f"decision={request.decision}"
    )

    return {
        "opportunity_id": opportunity_id,
        "decision": request.decision,
        "summary": session.summary(),
    }


@router.post("/sessions/{session_id}/batch-decision")
async def batch_decision(session_id: str, request: BatchDecisionRequest):
    """Apply the same decision to multiple opportunities."""
    session = _get_session(session_id)

    if request.decision not in ("pass", "reject"):
        raise HTTPException(status_code=400, detail="Batch decision must be pass or reject")

    updated = []
    for opp_id in request.opportunity_ids:
        if opp_id in session.items:
            session.items[opp_id]["decision"] = request.decision
            session.items[opp_id]["decision_reason"] = request.reason
            session.items[opp_id]["decided_at"] = datetime.utcnow().isoformat()
            updated.append(opp_id)

    return {
        "updated": len(updated),
        "opportunity_ids": updated,
        "summary": session.summary(),
    }


@router.get("/sessions/{session_id}/passed")
async def get_passed_opportunities(session_id: str):
    """Get all opportunities marked as 'pass' — ready for deep analysis."""
    session = _get_session(session_id)

    passed = [
        {
            "opportunity_id": opp_id,
            "title": item.get("opportunity_title", item.get("title", "")),
            "funder": item.get("funder", ""),
            "overall_score": item.get("overall_score", 0),
            "selected_depth": item.get("selected_depth", "essentials"),
            "decision_reason": item.get("decision_reason"),
        }
        for opp_id, item in session.items.items()
        if item["decision"] == "pass"
    ]

    # Estimate cost
    cost_map = {"essentials": 2.00, "premium": 8.00}
    total_cost = sum(cost_map.get(p["selected_depth"], 2.00) for p in passed)

    return {
        "session_id": session_id,
        "passed_count": len(passed),
        "estimated_cost": total_cost,
        "opportunities": passed,
    }


@router.post("/sessions/{session_id}/investigate/{opportunity_id}")
async def investigate_opportunity(
    session_id: str,
    opportunity_id: str,
    request: InvestigateRequest,
):
    """
    Targeted AI investigation of a specific concern about an opportunity.
    Uses Claude to answer a focused question using the opportunity context.
    """
    session = _get_session(session_id)

    if opportunity_id not in session.items:
        raise HTTPException(status_code=404, detail=f"Opportunity {opportunity_id} not found")

    item = session.items[opportunity_id]

    # Try to use Claude for investigation
    try:
        from src.core.anthropic_service import get_anthropic_service, PipelineStage

        anthropic = get_anthropic_service()
        if not anthropic.is_available:
            raise RuntimeError("Anthropic API not available")

        opp_context = (
            f"Opportunity: {item.get('opportunity_title', item.get('title', 'Unknown'))}\n"
            f"Funder: {item.get('funder', 'Unknown')}\n"
            f"Description: {item.get('description', item.get('one_sentence_summary', 'No description'))}\n"
            f"Overall Score: {item.get('overall_score', 'N/A')}\n"
            f"Key Strengths: {item.get('key_strengths', [])}\n"
            f"Key Concerns: {item.get('key_concerns', [])}\n"
        )

        org_context = ""
        if session.organization:
            org_context = (
                f"\nOrganization: {session.organization.get('name', 'Unknown')}\n"
                f"Mission: {session.organization.get('mission', 'Unknown')}\n"
            )

        system = (
            "You are a grant research analyst. A human reviewer is examining "
            "an AI-screened opportunity and has a specific question. Answer "
            "concisely and honestly based on the available context. If you "
            "don't have enough information, say so."
        )
        user = f"{opp_context}{org_context}\nQuestion: {request.question}"

        result = await anthropic.create_completion(
            messages=[{"role": "user", "content": user}],
            system=system,
            stage=PipelineStage.FAST_SCREENING,  # Use haiku for quick investigation
            max_tokens=512,
            temperature=0.2,
        )

        investigation_result = result.get("content", "No response generated.")

    except Exception as e:
        logger.warning(f"AI investigation failed, returning context-only response: {e}")
        investigation_result = (
            f"AI investigation unavailable. Here's what we know:\n"
            f"- Score: {item.get('overall_score', 'N/A')}\n"
            f"- Strengths: {', '.join(item.get('key_strengths', ['Unknown']))}\n"
            f"- Concerns: {', '.join(item.get('key_concerns', ['Unknown']))}\n"
            f"\nYour question: {request.question}\n"
            f"Please review the opportunity details manually."
        )

    # Store investigation notes
    existing_notes = item.get("investigation_notes") or []
    if isinstance(existing_notes, str):
        existing_notes = [existing_notes]
    existing_notes.append({
        "question": request.question,
        "answer": investigation_result,
        "timestamp": datetime.utcnow().isoformat(),
    })
    item["investigation_notes"] = existing_notes

    return {
        "opportunity_id": opportunity_id,
        "question": request.question,
        "answer": investigation_result,
        "total_investigations": len(existing_notes),
    }


@router.get("/sessions")
async def list_sessions():
    """List all gateway sessions."""
    return {
        "sessions": [s.summary() for s in _sessions.values()]
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id: str) -> GatewaySession:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return _sessions[session_id]


def _format_opportunities(session: GatewaySession) -> List[Dict[str, Any]]:
    """Format opportunities for API response, sorted by score descending."""
    opps = []
    for opp_id, item in session.items.items():
        opps.append({
            "opportunity_id": opp_id,
            "title": item.get("opportunity_title", item.get("title", "")),
            "funder": item.get("funder", ""),
            "funder_type": item.get("funder_type", ""),
            "overall_score": item.get("overall_score", 0),
            "strategic_fit_score": item.get("strategic_fit_score", 0),
            "eligibility_score": item.get("eligibility_score", 0),
            "timing_score": item.get("timing_score", 0),
            "financial_score": item.get("financial_score", 0),
            "competition_score": item.get("competition_score", 0),
            "confidence_level": item.get("confidence_level", ""),
            "one_sentence_summary": item.get("one_sentence_summary", ""),
            "key_strengths": item.get("key_strengths", []),
            "key_concerns": item.get("key_concerns", []),
            "reasoning": item.get("reasoning", ""),
            "decision": item.get("decision"),
            "decision_reason": item.get("decision_reason"),
            "decided_at": item.get("decided_at"),
            "selected_depth": item.get("selected_depth", "essentials"),
            "investigation_notes": item.get("investigation_notes"),
        })
    opps.sort(key=lambda x: x["overall_score"], reverse=True)
    return opps
