"""
Base Tool Class
Foundation for all 12-factor compliant tools in Catalynx.

12-Factor Principles Implemented:
- Factor 4: Tools as Structured Outputs
- Factor 6: Stateless Execution
- Factor 10: Single Responsibility
- Factor 12: API First Design
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Generic, TypeVar
from datetime import datetime
from enum import Enum
import logging
import time


# Generic type for tool output
T = TypeVar('T')


class ToolStatus(Enum):
    """Tool execution status"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ERROR = "error"


@dataclass
class ToolExecutionContext:
    """
    Execution context for tool runs.
    Captures environment and configuration for a single execution.
    """
    tool_name: str
    tool_version: str
    execution_id: str
    start_time: datetime = field(default_factory=datetime.now)
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult(Generic[T]):
    """
    Structured output from tool execution.

    Factor 4 Implementation: All tools return structured, typed results
    that eliminate parsing errors and provide predictable interfaces.
    """
    status: ToolStatus
    data: Optional[T] = None
    error: Optional[str] = None
    warnings: list[str] = field(default_factory=list)

    # Execution Metrics
    execution_time_ms: float = 0.0
    cost_usd: Optional[float] = None

    # Metadata
    tool_name: str = ""
    tool_version: str = ""
    execution_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    # Quality Metrics
    data_quality_score: Optional[float] = None
    completeness_percentage: Optional[float] = None

    # Additional Context
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ToolStatus.SUCCESS

    def is_partial(self) -> bool:
        """Check if execution had partial success."""
        return self.status == ToolStatus.PARTIAL

    def has_errors(self) -> bool:
        """Check if execution had errors."""
        return self.status in [ToolStatus.ERROR, ToolStatus.FAILURE]

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "warnings": self.warnings,
            "execution_time_ms": self.execution_time_ms,
            "cost_usd": self.cost_usd,
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "execution_id": self.execution_id,
            "timestamp": self.timestamp.isoformat(),
            "data_quality_score": self.data_quality_score,
            "completeness_percentage": self.completeness_percentage,
            "metadata": self.metadata
        }


class BaseTool(ABC, Generic[T]):
    """
    Abstract base class for all 12-factor tools.

    12-Factor Compliance:
    - Factor 6: Stateless - No persistent state between executions
    - Factor 10: Single Responsibility - Each tool does one thing well
    - Factor 12: API First - Programmatic interface is primary

    Subclasses must implement:
    - _execute(): Core tool logic
    - get_tool_name(): Tool identifier
    - get_tool_version(): Version string
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize tool with configuration.

        Args:
            config: Tool-specific configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_tool_name(self) -> str:
        """
        Get tool name.

        Returns:
            Tool name string
        """
        pass

    @abstractmethod
    def get_tool_version(self) -> str:
        """
        Get tool version.

        Returns:
            Version string (e.g., "1.0.0")
        """
        pass

    @abstractmethod
    async def _execute(self, context: ToolExecutionContext, **kwargs) -> T:
        """
        Core tool execution logic (implemented by subclasses).

        Factor 6: This method should be stateless - no side effects
        between invocations.

        Args:
            context: Execution context
            **kwargs: Tool-specific parameters

        Returns:
            Structured tool output (type T)

        Raises:
            Exception: On execution failure
        """
        pass

    async def execute(self, execution_id: Optional[str] = None, **kwargs) -> ToolResult[T]:
        """
        Execute tool with structured output.

        Factor 4: Returns structured ToolResult, eliminating parsing errors.

        Args:
            execution_id: Optional execution identifier
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with structured output
        """
        # Generate execution ID if not provided
        if execution_id is None:
            execution_id = f"{self.get_tool_name()}_{int(time.time() * 1000)}"

        # Create execution context
        context = ToolExecutionContext(
            tool_name=self.get_tool_name(),
            tool_version=self.get_tool_version(),
            execution_id=execution_id,
            config=self.config
        )

        # Track execution time
        start_time = time.time()

        try:
            # Execute tool logic
            self.logger.info(f"Starting execution: {execution_id}")
            data = await self._execute(context, **kwargs)

            execution_time_ms = (time.time() - start_time) * 1000

            # Create success result
            result = ToolResult(
                status=ToolStatus.SUCCESS,
                data=data,
                execution_time_ms=execution_time_ms,
                tool_name=self.get_tool_name(),
                tool_version=self.get_tool_version(),
                execution_id=execution_id
            )

            self.logger.info(
                f"Execution completed: {execution_id} "
                f"({execution_time_ms:.2f}ms)"
            )

            return result

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000

            # Log error
            self.logger.error(
                f"Execution failed: {execution_id} - {str(e)}",
                exc_info=True
            )

            # Create error result
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e),
                execution_time_ms=execution_time_ms,
                tool_name=self.get_tool_name(),
                tool_version=self.get_tool_version(),
                execution_id=execution_id
            )

    def validate_inputs(self, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Validate tool inputs before execution.

        Override in subclasses for custom validation.

        Args:
            **kwargs: Tool inputs to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None

    def get_cost_estimate(self, **kwargs) -> Optional[float]:
        """
        Estimate execution cost (e.g., API calls).

        Override in subclasses that have cost estimation.

        Args:
            **kwargs: Tool inputs

        Returns:
            Estimated cost in USD, or None if not applicable
        """
        return None

    def get_single_responsibility(self) -> str:
        """
        Get tool's single responsibility statement.

        Factor 10: Tools should have clear, focused responsibility.

        Returns:
            Responsibility description
        """
        return "Override in subclass to define responsibility"

    async def health_check(self) -> bool:
        """
        Check if tool is healthy and ready to execute.

        Returns:
            True if healthy, False otherwise
        """
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get tool metadata.

        Returns:
            Dictionary of metadata
        """
        return {
            "name": self.get_tool_name(),
            "version": self.get_tool_version(),
            "responsibility": self.get_single_responsibility(),
            "config": self.config
        }


class SyncBaseTool(ABC):
    """
    Synchronous version of BaseTool for tools that don't need async.

    Use this for simpler tools that don't perform I/O operations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_tool_name(self) -> str:
        pass

    @abstractmethod
    def get_tool_version(self) -> str:
        pass

    @abstractmethod
    def _execute(self, context: ToolExecutionContext, **kwargs) -> Any:
        """Synchronous execution logic."""
        pass

    def execute(self, execution_id: Optional[str] = None, **kwargs) -> ToolResult:
        """Synchronous execution wrapper."""
        if execution_id is None:
            execution_id = f"{self.get_tool_name()}_{int(time.time() * 1000)}"

        context = ToolExecutionContext(
            tool_name=self.get_tool_name(),
            tool_version=self.get_tool_version(),
            execution_id=execution_id,
            config=self.config
        )

        start_time = time.time()

        try:
            data = self._execute(context, **kwargs)
            execution_time_ms = (time.time() - start_time) * 1000

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=data,
                execution_time_ms=execution_time_ms,
                tool_name=self.get_tool_name(),
                tool_version=self.get_tool_version(),
                execution_id=execution_id
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Execution failed: {execution_id} - {str(e)}", exc_info=True)

            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e),
                execution_time_ms=execution_time_ms,
                tool_name=self.get_tool_name(),
                tool_version=self.get_tool_version(),
                execution_id=execution_id
            )
