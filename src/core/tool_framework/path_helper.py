#!/usr/bin/env python3
"""
Path Helper for 12-Factor Tools
Centralizes path management to eliminate sys.path.insert() anti-pattern
"""

from pathlib import Path
import sys
from typing import Optional


def setup_tool_paths(tool_file: Optional[str] = None) -> Path:
    """
    Setup import paths for 12-factor tools.

    This function centralizes path management to avoid the anti-pattern of
    using `sys.path.insert(0, str(project_root))` in 46+ files across tools.

    Args:
        tool_file: The __file__ variable from the calling tool module.
                  If not provided, calculates from this file's location.

    Returns:
        Path: Project root directory

    Example:
        ```python
        from src.core.tool_framework.path_helper import setup_tool_paths

        # In a tool file
        project_root = setup_tool_paths(__file__)

        # Now you can import from src
        from src.core.openai_service import OpenAIService
        ```

    Note:
        - Only adds path if not already in sys.path
        - Call this once at the top of your tool module
        - Replaces the pattern: `sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))`
    """
    if tool_file:
        # Called from a tool: tools/tool_name/app/tool.py
        # Need to go up 4 levels: app -> tool_name -> tools -> project_root
        tool_path = Path(tool_file).resolve()
        project_root = tool_path.parent.parent.parent.parent
    else:
        # Called from this file: src/core/tool_framework/path_helper.py
        # Need to go up 3 levels: tool_framework -> core -> src -> project_root
        project_root = Path(__file__).resolve().parent.parent.parent.parent

    # Add project root to sys.path if not already present
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

    return project_root


def get_project_root() -> Path:
    """
    Get the project root directory without modifying sys.path.

    Returns:
        Path: Project root directory

    Example:
        ```python
        from src.core.tool_framework.path_helper import get_project_root

        root = get_project_root()
        data_dir = root / "data"
        ```
    """
    return Path(__file__).resolve().parent.parent.parent.parent


def get_tool_directory(tool_file: str) -> Path:
    """
    Get the tool's root directory.

    Args:
        tool_file: The __file__ variable from the tool module

    Returns:
        Path: Tool root directory (e.g., tools/tool_name/)

    Example:
        ```python
        from src.core.tool_framework.path_helper import get_tool_directory

        tool_dir = get_tool_directory(__file__)
        config_file = tool_dir / "12factors.toml"
        ```
    """
    # Assuming tool structure: tools/tool_name/app/tool.py
    return Path(tool_file).resolve().parent.parent


def get_data_directory() -> Path:
    """
    Get the project data directory.

    Returns:
        Path: Project data directory
    """
    return get_project_root() / "data"


def get_tools_directory() -> Path:
    """
    Get the tools root directory.

    Returns:
        Path: Tools root directory
    """
    return get_project_root() / "tools"


# Module-level setup (optional - called automatically on import)
# This allows existing code to just import this module without calling functions
_project_root = setup_tool_paths()


__all__ = [
    'setup_tool_paths',
    'get_project_root',
    'get_tool_directory',
    'get_data_directory',
    'get_tools_directory',
]
