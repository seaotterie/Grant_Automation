"""
Pytest configuration for Financial Intelligence Tool tests
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Add tool's app directory to Python path to resolve hyphenated directory name
tool_root = Path(__file__).parent.parent
sys.path.insert(0, str(tool_root))
