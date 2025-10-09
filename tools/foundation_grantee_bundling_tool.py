"""
Foundation Grantee Bundling Tool - Import Wrapper
Provides Python-compatible import path for hyphenated tool directory

This module wraps the foundation-grantee-bundling-tool directory to enable
Python imports despite the hyphenated directory name.
"""

import sys
from pathlib import Path

# Add the hyphenated tool directory to Python path
tool_dir = Path(__file__).parent / "foundation-grantee-bundling-tool"
if str(tool_dir) not in sys.path:
    sys.path.insert(0, str(tool_dir))

# Import and re-export all components
from app.bundling_tool import FoundationGranteeBundlingTool
from app.bundling_models import (
    # Input models
    GranteeBundlingInput,
    CoFundingAnalysisInput,

    # Output models - Bundling
    FundingSource,
    BundledGrantee,
    FoundationOverlap,
    ThematicCluster,
    GranteeBundlingOutput,

    # Output models - Co-funding
    FunderSimilarity,
    PeerFunderGroup,
    FunderRecommendation,
    CoFundingAnalysisOutput,

    # Enums
    FundingStability,
    RecommendationType,
)
from app.cofunding_analyzer import CoFundingAnalyzer

__all__ = [
    # Main tool class
    "FoundationGranteeBundlingTool",

    # Input models
    "GranteeBundlingInput",
    "CoFundingAnalysisInput",

    # Bundling output models
    "FundingSource",
    "BundledGrantee",
    "FoundationOverlap",
    "ThematicCluster",
    "GranteeBundlingOutput",

    # Co-funding output models
    "FunderSimilarity",
    "PeerFunderGroup",
    "FunderRecommendation",
    "CoFundingAnalysisOutput",

    # Enums
    "FundingStability",
    "RecommendationType",

    # Co-funding analyzer
    "CoFundingAnalyzer",
]
