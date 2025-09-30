"""
Workflow Engine
Executes multi-tool workflows with dependency management and error handling.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import logging

from .workflow_parser import WorkflowDefinition, WorkflowStep
from src.core.tool_registry import get_registry


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class StepResult:
    """Result of a single workflow step execution."""
    step_name: str
    status: WorkflowStatus
    output: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowResult:
    """Result of complete workflow execution."""
    workflow_name: str
    status: WorkflowStatus
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    total_execution_time_ms: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    error: Optional[str] = None


class WorkflowEngine:
    """
    Executes workflows with dependency management.

    Features:
    - Parallel execution of independent steps
    - Dependency resolution
    - Error handling and retry logic
    - Context variable substitution
    """

    def __init__(self):
        """Initialize workflow engine."""
        self.logger = logging.getLogger(__name__)
        self.tool_registry = get_registry()

    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        Execute a complete workflow.

        Args:
            workflow: Workflow definition to execute
            context: Execution context variables

        Returns:
            WorkflowResult with all step results
        """
        context = context or {}

        result = WorkflowResult(
            workflow_name=workflow.name,
            status=WorkflowStatus.RUNNING
        )

        start_time = datetime.now()

        try:
            # Execute workflow steps
            step_results = await self._execute_steps(workflow.steps, context)
            result.step_results = step_results

            # Determine overall status
            if all(r.status == WorkflowStatus.COMPLETED for r in step_results.values()):
                result.status = WorkflowStatus.COMPLETED
            elif any(r.status == WorkflowStatus.FAILED for r in step_results.values()):
                # Check if any non-optional steps failed
                failed_required = any(
                    r.status == WorkflowStatus.FAILED
                    for step in workflow.steps
                    for r in [step_results.get(step.name)]
                    if r and not step.optional
                )
                result.status = WorkflowStatus.FAILED if failed_required else WorkflowStatus.PARTIAL
            else:
                result.status = WorkflowStatus.PARTIAL

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}", exc_info=True)
            result.status = WorkflowStatus.FAILED
            result.error = str(e)

        finally:
            result.end_time = datetime.now()
            result.total_execution_time_ms = (
                (result.end_time - start_time).total_seconds() * 1000
            )

        return result

    async def _execute_steps(
        self,
        steps: List[WorkflowStep],
        context: Dict[str, Any]
    ) -> Dict[str, StepResult]:
        """
        Execute workflow steps with dependency resolution.

        Args:
            steps: List of steps to execute
            context: Execution context

        Returns:
            Dictionary of step results (step_name -> StepResult)
        """
        results: Dict[str, StepResult] = {}
        pending_steps = list(steps)
        completed_steps = set()

        while pending_steps:
            # Find steps ready to execute (dependencies satisfied)
            ready_steps = [
                step for step in pending_steps
                if all(dep in completed_steps for dep in step.depends_on)
            ]

            if not ready_steps:
                # Circular dependency or missing dependency
                raise ValueError("Circular dependency detected or missing dependencies")

            # Execute ready steps in parallel
            tasks = [
                self._execute_step(step, context, results)
                for step in ready_steps
            ]

            step_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for step, step_result in zip(ready_steps, step_results):
                if isinstance(step_result, Exception):
                    # Handle exception
                    results[step.name] = StepResult(
                        step_name=step.name,
                        status=WorkflowStatus.FAILED,
                        error=str(step_result)
                    )
                else:
                    results[step.name] = step_result

                completed_steps.add(step.name)
                pending_steps.remove(step)

        return results

    async def _execute_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
        previous_results: Dict[str, StepResult]
    ) -> StepResult:
        """
        Execute a single workflow step.

        Args:
            step: Step to execute
            context: Execution context
            previous_results: Results from previous steps

        Returns:
            StepResult
        """
        self.logger.info(f"Executing step: {step.name}")

        start_time = datetime.now()

        try:
            # Resolve input variables
            inputs = self._resolve_inputs(step.inputs, context, previous_results)

            # Get tool from registry
            tool_metadata = self.tool_registry.get_tool(step.tool)
            if not tool_metadata:
                raise ValueError(f"Tool not found: {step.tool}")

            # TODO: Load and execute actual tool
            # For now, return placeholder result
            self.logger.warning(f"Tool execution not yet implemented: {step.tool}")

            output = {
                "step": step.name,
                "tool": step.tool,
                "inputs": inputs,
                "status": "placeholder"
            }

            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            return StepResult(
                step_name=step.name,
                status=WorkflowStatus.COMPLETED,
                output=output,
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            self.logger.error(f"Step execution failed: {step.name} - {e}", exc_info=True)

            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            return StepResult(
                step_name=step.name,
                status=WorkflowStatus.FAILED,
                error=str(e),
                execution_time_ms=execution_time_ms
            )

    def _resolve_inputs(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
        previous_results: Dict[str, StepResult]
    ) -> Dict[str, Any]:
        """
        Resolve variable references in step inputs.

        Supports:
        - ${context.variable_name} - Context variables
        - ${steps.step_name.output} - Previous step outputs

        Args:
            inputs: Step inputs with potential variable references
            context: Execution context
            previous_results: Results from previous steps

        Returns:
            Resolved inputs dictionary
        """
        resolved = {}

        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Variable reference
                var_path = value[2:-1]  # Remove ${ and }

                if var_path.startswith("context."):
                    # Context variable
                    var_name = var_path[8:]  # Remove "context."
                    resolved[key] = context.get(var_name)

                elif var_path.startswith("steps."):
                    # Previous step output
                    parts = var_path[6:].split(".")  # Remove "steps."
                    if len(parts) >= 2:
                        step_name = parts[0]
                        output_path = ".".join(parts[1:])

                        step_result = previous_results.get(step_name)
                        if step_result and step_result.output:
                            # Navigate output path
                            value = step_result.output
                            for part in output_path.split("."):
                                if isinstance(value, dict):
                                    value = value.get(part)
                                else:
                                    value = getattr(value, part, None)
                            resolved[key] = value
                else:
                    resolved[key] = value
            else:
                resolved[key] = value

        return resolved