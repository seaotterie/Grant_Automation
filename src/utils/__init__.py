"""
Utility Modules

Version 2.0: Added EIN resolution for 990-PF screening enhancement
"""

# EIN Resolution (Phase 1, Week 2)
from .ein_resolution import (
    EINResolver,
    EINResolutionResult,
    EINConfidence,
    resolve_ein_simple,
    get_ein_confidence_weight,
)

__all__ = [
    "EINResolver",
    "EINResolutionResult",
    "EINConfidence",
    "resolve_ein_simple",
    "get_ein_confidence_weight",
]

__version__ = "2.0.0"