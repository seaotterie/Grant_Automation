"""
Canonical risk assessment enums shared across all Catalynx tools.

Consolidates four previously-duplicate `RiskLevel` definitions into a single
`str, Enum` covering the full 5-value spectrum used by the risk intelligence
and dossier builder tools. Tools that previously exposed only 4 values
(LOW, MEDIUM, HIGH, CRITICAL) can continue to emit those same values — the
broader enum is a strict superset.
"""

from enum import Enum


class RiskLevel(str, Enum):
    """Canonical 5-level risk scale used across the platform.

    All values serialize as lowercase strings, so outputs are JSON-compatible
    without custom encoders.
    """
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


__all__ = ["RiskLevel"]
