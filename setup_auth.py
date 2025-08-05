#!/usr/bin/env python3
"""
Authentication Setup Script
Quick setup script for the Grant Research authentication system.
"""

import sys
from pathlib import Path

# Add src to path so we can import our modules
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.auth.cli_auth import auth_cli

if __name__ == '__main__':
    auth_cli()