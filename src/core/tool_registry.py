"""
Tool Registry System
Centralized registry for all 12-factor tools in the Catalynx platform.

Responsibilities:
- Tool discovery and registration
- Tool metadata management
- Tool availability checking
- Tool version tracking
"""

import tomli
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ToolStatus(Enum):
    """Tool operational status"""
    OPERATIONAL = "operational"
    DEPRECATED = "deprecated"
    IN_DEVELOPMENT = "in_development"
    MAINTENANCE = "maintenance"


@dataclass
class ToolMetadata:
    """Metadata for a 12-factor tool"""
    name: str
    version: str
    description: str
    tool_path: Path
    status: ToolStatus = ToolStatus.OPERATIONAL

    # 12-Factor Compliance
    single_responsibility: str = ""
    structured_output_format: str = ""
    dependencies: List[str] = field(default_factory=list)

    # Tool Configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # Performance Metrics
    avg_execution_time_ms: Optional[float] = None
    cost_per_execution: Optional[float] = None

    # Integration
    replaces_processors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate tool metadata"""
        if not self.name:
            raise ValueError("Tool name is required")
        if not self.version:
            raise ValueError("Tool version is required")


class ToolRegistry:
    """
    Central registry for 12-factor tools.

    Features:
    - Auto-discovery of tools with 12factors.toml
    - Tool metadata caching
    - Version tracking
    - Status management
    """

    def __init__(self, tools_directory: Path = None):
        """
        Initialize tool registry.

        Args:
            tools_directory: Root directory containing tools (default: project_root/tools/)
        """
        if tools_directory is None:
            # Default to project_root/tools/
            project_root = Path(__file__).parent.parent.parent
            tools_directory = project_root / "tools"

        self.tools_directory = tools_directory
        self._tools: Dict[str, ToolMetadata] = {}
        self._discover_tools()

    def _discover_tools(self) -> None:
        """
        Auto-discover tools by scanning for 12factors.toml files.
        """
        if not self.tools_directory.exists():
            raise FileNotFoundError(f"Tools directory not found: {self.tools_directory}")

        # Find all tool directories with 12factors.toml
        for tool_path in self.tools_directory.iterdir():
            if not tool_path.is_dir():
                continue

            config_file = tool_path / "12factors.toml"
            if config_file.exists():
                try:
                    metadata = self._load_tool_metadata(tool_path, config_file)
                    self._tools[metadata.name] = metadata
                except Exception as e:
                    print(f"Warning: Failed to load tool from {tool_path}: {e}")

    def _load_tool_metadata(self, tool_path: Path, config_file: Path) -> ToolMetadata:
        """
        Load tool metadata from 12factors.toml file.

        Args:
            tool_path: Path to tool directory
            config_file: Path to 12factors.toml file

        Returns:
            ToolMetadata object
        """
        with open(config_file, "rb") as f:
            config = tomli.load(f)

        tool_config = config.get("tool", {})

        return ToolMetadata(
            name=tool_config.get("name", tool_path.name),
            version=tool_config.get("version", "unknown"),
            description=tool_config.get("description", ""),
            tool_path=tool_path,
            status=ToolStatus.OPERATIONAL,  # Default status
            single_responsibility=tool_config.get("single_responsibility", ""),
            structured_output_format=tool_config.get("structured_output_format", ""),
            dependencies=tool_config.get("dependencies", []),
            config=config
        )

    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        """
        Get tool metadata by name.

        Args:
            name: Tool name

        Returns:
            ToolMetadata if found, None otherwise
        """
        return self._tools.get(name)

    def list_tools(self, status: Optional[ToolStatus] = None) -> List[ToolMetadata]:
        """
        List all registered tools, optionally filtered by status.

        Args:
            status: Filter by tool status (optional)

        Returns:
            List of ToolMetadata objects
        """
        tools = list(self._tools.values())

        if status:
            tools = [t for t in tools if t.status == status]

        return sorted(tools, key=lambda t: t.name)

    def get_operational_tools(self) -> List[ToolMetadata]:
        """Get all operational tools."""
        return self.list_tools(status=ToolStatus.OPERATIONAL)

    def get_tool_count(self) -> int:
        """Get total number of registered tools."""
        return len(self._tools)

    def get_tool_by_path(self, tool_path: Path) -> Optional[ToolMetadata]:
        """
        Get tool metadata by tool directory path.

        Args:
            tool_path: Path to tool directory

        Returns:
            ToolMetadata if found, None otherwise
        """
        for tool in self._tools.values():
            if tool.tool_path == tool_path:
                return tool
        return None

    def register_tool(self, metadata: ToolMetadata) -> None:
        """
        Manually register a tool.

        Args:
            metadata: Tool metadata to register
        """
        self._tools[metadata.name] = metadata

    def update_tool_status(self, name: str, status: ToolStatus) -> bool:
        """
        Update tool status.

        Args:
            name: Tool name
            status: New status

        Returns:
            True if updated, False if tool not found
        """
        tool = self.get_tool(name)
        if tool:
            tool.status = status
            return True
        return False

    def get_tools_by_responsibility(self, keyword: str) -> List[ToolMetadata]:
        """
        Find tools by responsibility keyword.

        Args:
            keyword: Keyword to search in single_responsibility field

        Returns:
            List of matching tools
        """
        keyword_lower = keyword.lower()
        return [
            tool for tool in self._tools.values()
            if keyword_lower in tool.single_responsibility.lower()
        ]

    def generate_inventory_report(self) -> str:
        """
        Generate a comprehensive inventory report of all tools.

        Returns:
            Formatted report string
        """
        operational = len(self.get_operational_tools())
        total = self.get_tool_count()

        report = [
            "=" * 80,
            "CATALYNX TOOL REGISTRY - INVENTORY REPORT",
            "=" * 80,
            f"\nTotal Tools: {total}",
            f"Operational: {operational}",
            f"In Development: {len(self.list_tools(ToolStatus.IN_DEVELOPMENT))}",
            f"Deprecated: {len(self.list_tools(ToolStatus.DEPRECATED))}",
            "\n" + "=" * 80,
            "OPERATIONAL TOOLS",
            "=" * 80,
        ]

        for tool in self.get_operational_tools():
            report.append(f"\n{tool.name} (v{tool.version})")
            report.append(f"  Description: {tool.description}")
            report.append(f"  Path: {tool.tool_path}")
            report.append(f"  Responsibility: {tool.single_responsibility}")
            report.append(f"  Output Format: {tool.structured_output_format}")

        return "\n".join(report)


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_registry(tools_directory: Path = None) -> ToolRegistry:
    """
    Get the global tool registry instance (singleton pattern).

    Args:
        tools_directory: Tools directory path (only used on first call)

    Returns:
        ToolRegistry instance
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = ToolRegistry(tools_directory)

    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (mainly for testing)."""
    global _global_registry
    _global_registry = None


if __name__ == "__main__":
    # Example usage
    registry = get_registry()
    print(registry.generate_inventory_report())
