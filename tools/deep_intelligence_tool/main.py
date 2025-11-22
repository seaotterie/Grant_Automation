"""
Deep Intelligence Tool - Main Entry Point
12-Factor tool for comprehensive grant opportunity analysis
"""

from .app.intelligence_tool import DeepIntelligenceTool

# Export the tool class so it can be discovered by the tool registry
__all__ = ['DeepIntelligenceTool']
