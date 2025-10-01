"""
Tool Loader for Workflow Engine
Dynamically loads and executes tools for workflow execution.
"""

import importlib
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Type
from dataclasses import dataclass
import logging

from src.core.tool_registry import ToolRegistry, ToolMetadata
from src.core.tool_framework import BaseTool, ToolResult, ToolExecutionContext


@dataclass
class ToolLoadResult:
    """Result of loading a tool"""
    success: bool
    tool_instance: Optional[BaseTool] = None
    error: Optional[str] = None
    tool_metadata: Optional[ToolMetadata] = None


class ToolLoader:
    """
    Dynamically loads and instantiates tools for workflow execution.

    Features:
    - Tool registry integration
    - Dynamic module loading
    - Instance caching (optional)
    - Error handling and validation
    """

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        cache_instances: bool = True
    ):
        """
        Initialize tool loader.

        Args:
            registry: Tool registry (creates new if None)
            cache_instances: Whether to cache tool instances
        """
        self.logger = logging.getLogger(__name__)
        self.registry = registry or ToolRegistry()
        self.cache_instances = cache_instances
        self._instance_cache: Dict[str, BaseTool] = {}

    def load_tool(
        self,
        tool_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> ToolLoadResult:
        """
        Load a tool by name.

        Args:
            tool_name: Name of tool to load (from registry)
            config: Optional tool configuration

        Returns:
            ToolLoadResult with tool instance or error
        """
        # Check cache first
        if self.cache_instances and tool_name in self._instance_cache:
            self.logger.debug(f"Using cached tool instance: {tool_name}")
            return ToolLoadResult(
                success=True,
                tool_instance=self._instance_cache[tool_name],
                tool_metadata=self.registry.get_tool(tool_name)
            )

        # Get tool metadata from registry
        metadata = self.registry.get_tool(tool_name)
        if not metadata:
            return ToolLoadResult(
                success=False,
                error=f"Tool not found in registry: {tool_name}"
            )

        self.logger.info(f"Loading tool: {tool_name} (version {metadata.version})")

        try:
            # Load tool module and class
            tool_instance = self._load_tool_instance(metadata, config)

            # Cache if enabled
            if self.cache_instances:
                self._instance_cache[tool_name] = tool_instance

            return ToolLoadResult(
                success=True,
                tool_instance=tool_instance,
                tool_metadata=metadata
            )

        except Exception as e:
            self.logger.error(f"Failed to load tool {tool_name}: {e}", exc_info=True)
            return ToolLoadResult(
                success=False,
                error=str(e),
                tool_metadata=metadata
            )

    def _load_tool_instance(
        self,
        metadata: ToolMetadata,
        config: Optional[Dict[str, Any]]
    ) -> BaseTool:
        """
        Load and instantiate a tool from its metadata.

        Args:
            metadata: Tool metadata
            config: Optional tool configuration

        Returns:
            BaseTool instance

        Raises:
            ImportError: If tool module cannot be loaded
            AttributeError: If tool class not found
            Exception: If tool instantiation fails
        """
        # Get integration config from 12factors.toml
        integration_config = metadata.config.get("tool", {}).get("integration", {})

        # Determine module path
        module_path = integration_config.get("module_path")
        class_name = integration_config.get("class_name")

        if not module_path or not class_name:
            raise ValueError(
                f"Tool {metadata.name} missing integration.module_path or integration.class_name in 12factors.toml"
            )

        # Add tool directory to Python path
        tool_app_dir = metadata.tool_path / "app"
        if tool_app_dir.exists() and str(tool_app_dir) not in sys.path:
            sys.path.insert(0, str(tool_app_dir))

        # Convert module path to proper format
        # "tools.xml-990-parser-tool.app.parser_tool" -> "parser_tool"
        # or handle absolute imports
        if module_path.startswith("tools."):
            # Extract just the module name from the app directory
            parts = module_path.split(".")
            module_name = parts[-1]  # Get last part (e.g., "parser_tool")
        else:
            module_name = module_path

        try:
            # Try importing from tool's app directory
            module = importlib.import_module(module_name)
        except ImportError:
            # Try full module path
            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                raise ImportError(
                    f"Failed to import tool module '{module_path}' or '{module_name}': {e}"
                )

        # Get tool class
        if not hasattr(module, class_name):
            raise AttributeError(
                f"Module {module_name} does not have class {class_name}"
            )

        tool_class = getattr(module, class_name)

        # Validate it's a BaseTool subclass
        if not issubclass(tool_class, BaseTool):
            raise TypeError(
                f"{class_name} is not a subclass of BaseTool"
            )

        # Merge configs (tool config + provided config)
        merged_config = {**(metadata.config.get("tool", {}).get("config", {})), **(config or {})}

        # Instantiate tool
        try:
            tool_instance = tool_class(config=merged_config if merged_config else None)
        except Exception as e:
            raise Exception(f"Failed to instantiate {class_name}: {e}")

        self.logger.info(
            f"Successfully loaded {metadata.name} v{metadata.version} "
            f"({class_name})"
        )

        return tool_instance

    async def execute_tool(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Load and execute a tool in one call.

        Args:
            tool_name: Name of tool to execute
            inputs: Tool inputs (kwargs)
            context: Execution context
            config: Optional tool configuration

        Returns:
            ToolResult from tool execution
        """
        # Load tool
        load_result = self.load_tool(tool_name, config)

        if not load_result.success:
            # Return failed ToolResult
            from src.core.tool_framework import ToolResult
            return ToolResult(
                is_success=False,
                error=load_result.error
            )

        tool_instance = load_result.tool_instance

        # Create context if not provided
        if context is None:
            context = ToolExecutionContext(
                tool_name=tool_name,
                tool_version=load_result.tool_metadata.version if load_result.tool_metadata else "unknown"
            )

        # Execute tool
        try:
            result = await tool_instance.execute(**inputs)
            return result

        except Exception as e:
            self.logger.error(f"Tool execution failed: {tool_name} - {e}", exc_info=True)
            from src.core.tool_framework import ToolResult
            return ToolResult(
                is_success=False,
                error=f"Tool execution error: {str(e)}"
            )

    def clear_cache(self) -> None:
        """Clear cached tool instances."""
        self._instance_cache.clear()
        self.logger.info("Tool instance cache cleared")

    def get_cached_tools(self) -> list[str]:
        """Get list of cached tool names."""
        return list(self._instance_cache.keys())


# Global tool loader instance
_global_loader: Optional[ToolLoader] = None


def get_tool_loader() -> ToolLoader:
    """Get global tool loader instance."""
    global _global_loader
    if _global_loader is None:
        _global_loader = ToolLoader()
    return _global_loader


def reset_tool_loader() -> None:
    """Reset global tool loader (useful for testing)."""
    global _global_loader
    _global_loader = None
