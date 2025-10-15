"""
Deep Intelligence Tool Package
"""

from .intelligence_tool import (
    DeepIntelligenceTool,
    analyze_opportunity,
    analyze_opportunities_batch
)
from .intelligence_models import (
    AnalysisDepth,
    DeepIntelligenceInput,
    DeepIntelligenceOutput,
    SuccessProbability,
    RiskLevel,
    DEPTH_FEATURES
)

__all__ = [
    "DeepIntelligenceTool",
    "analyze_opportunity",
    "analyze_opportunities_batch",
    "AnalysisDepth",
    "DeepIntelligenceInput",
    "DeepIntelligenceOutput",
    "SuccessProbability",
    "RiskLevel",
    "DEPTH_FEATURES",
]
