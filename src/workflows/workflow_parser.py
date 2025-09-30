"""
Workflow Parser
Parses YAML workflow definitions into executable workflow objects.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    name: str
    tool: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    optional: bool = False
    retry_count: int = 0
    timeout_seconds: Optional[int] = None


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    name: str
    description: str
    version: str
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowParser:
    """
    Parses YAML workflow definitions.

    Example workflow YAML:
    ```yaml
    name: "Deep Intelligence Workflow"
    description: "Complete grant intelligence analysis"
    version: "1.0.0"

    steps:
      - name: "Parse 990"
        tool: "xml-990-parser-tool"
        inputs:
          ein: "${context.ein}"

      - name: "Analyze Financials"
        tool: "form990-analysis-tool"
        depends_on: ["Parse 990"]
        inputs:
          form_data: "${steps.parse_990.output}"
    ```
    """

    @staticmethod
    def parse_file(workflow_file: Path) -> WorkflowDefinition:
        """
        Parse workflow from YAML file.

        Args:
            workflow_file: Path to workflow YAML file

        Returns:
            WorkflowDefinition object

        Raises:
            ValueError: If YAML is invalid
            FileNotFoundError: If file doesn't exist
        """
        if not workflow_file.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_file}")

        with open(workflow_file, 'r') as f:
            data = yaml.safe_load(f)

        return WorkflowParser.parse_dict(data)

    @staticmethod
    def parse_dict(data: Dict[str, Any]) -> WorkflowDefinition:
        """
        Parse workflow from dictionary.

        Args:
            data: Workflow data dictionary

        Returns:
            WorkflowDefinition object

        Raises:
            ValueError: If data is invalid
        """
        # Validate required fields
        required_fields = ["name", "description", "version", "steps"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Parse steps
        steps = []
        for step_data in data["steps"]:
            step = WorkflowParser._parse_step(step_data)
            steps.append(step)

        return WorkflowDefinition(
            name=data["name"],
            description=data["description"],
            version=data["version"],
            steps=steps,
            metadata=data.get("metadata", {})
        )

    @staticmethod
    def _parse_step(step_data: Dict[str, Any]) -> WorkflowStep:
        """Parse a single workflow step."""
        if "name" not in step_data or "tool" not in step_data:
            raise ValueError("Step must have 'name' and 'tool' fields")

        return WorkflowStep(
            name=step_data["name"],
            tool=step_data["tool"],
            inputs=step_data.get("inputs", {}),
            depends_on=step_data.get("depends_on", []),
            optional=step_data.get("optional", False),
            retry_count=step_data.get("retry_count", 0),
            timeout_seconds=step_data.get("timeout_seconds")
        )

    @staticmethod
    def validate_workflow(workflow: WorkflowDefinition) -> tuple[bool, Optional[str]]:
        """
        Validate workflow definition.

        Args:
            workflow: Workflow to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for circular dependencies
        for step in workflow.steps:
            if step.name in step.depends_on:
                return False, f"Step '{step.name}' depends on itself"

        # Check that all dependencies exist
        step_names = {step.name for step in workflow.steps}
        for step in workflow.steps:
            for dep in step.depends_on:
                if dep not in step_names:
                    return False, f"Step '{step.name}' depends on non-existent step '{dep}'"

        return True, None