"""
Database Configuration
Centralized database path configuration for all components.
"""

import os
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Database paths (relative to project root)
NONPROFIT_INTELLIGENCE_DB = os.path.join(PROJECT_ROOT, "data", "nonprofit_intelligence.db")
CATALYNX_DB = os.path.join(PROJECT_ROOT, "data", "catalynx.db")

# Backwards compatibility - string paths
NONPROFIT_INTELLIGENCE_DB_PATH = str(NONPROFIT_INTELLIGENCE_DB)
CATALYNX_DB_PATH = str(CATALYNX_DB)

# Environment variable overrides (optional)
NONPROFIT_INTELLIGENCE_DB = os.getenv("NONPROFIT_INTELLIGENCE_DB", NONPROFIT_INTELLIGENCE_DB)
CATALYNX_DB = os.getenv("CATALYNX_DB", CATALYNX_DB)


def get_nonprofit_intelligence_db() -> str:
    """Get nonprofit intelligence database path."""
    return str(NONPROFIT_INTELLIGENCE_DB)


def get_catalynx_db() -> str:
    """Get Catalynx application database path."""
    return str(CATALYNX_DB)
