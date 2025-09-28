"""
BMF Filter Tool - 12-Factor Implementation
==========================================

A demonstration of 12-factor agents framework applied to nonprofit data filtering.

This tool integrates with the existing Catalynx platform while demonstrating
clean 12-factor principles:

- Factor 3: Config from Environment
- Factor 4: Tools are Structured Outputs
- Factor 6: Stateless Processes
- Factor 7: Port Binding
- Factor 9: Disposability

Key Components:
- BMFFilterTool: Core filtering logic
- BMFFilterAgent: LLM integration
- Server: HTTP API service
- Main: CLI interface and examples
"""

__version__ = "1.0.0"
__author__ = "Catalynx Development"

# Import main components for easy access
from .bmf_filter import BMFFilterTool

__all__ = ["BMFFilterTool"]