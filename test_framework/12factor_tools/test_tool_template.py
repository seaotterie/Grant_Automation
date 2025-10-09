"""
12-Factor Tool Test Template
Template for testing 12-factor compliant tools with BAML output validation

Usage:
1. Copy this file and rename to test_{tool_name}.py
2. Update TOOL_NAME, TOOL_MODULE_PATH, and expected outputs
3. Add tool-specific test cases
4. Run with pytest: pytest test_framework/12factor_tools/test_{tool_name}.py

Example:
    pytest test_framework/12factor_tools/test_bmf_filter_tool.py -v
"""

import pytest
import sys
from pathlib import Path
from typing import Any, Dict, Optional
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import BAML client for output validation
from baml_client.types import (
    # Add specific BAML types for your tool here
    # Example: NTEEScoreResult, CompositeScoreResult, etc.
)

# Tool configuration - UPDATE THESE FOR EACH TOOL
TOOL_NAME = "example-tool"  # e.g., "bmf-filter-tool"
TOOL_MODULE_PATH = "tools.example_tool.app.example_tool"  # e.g., "tools.bmf_filter_tool.app.bmf_filter"
TOOL_CLASS_NAME = "ExampleTool"  # e.g., "BMFFilterTool"

# 12-Factor Compliance Checks
EXPECTED_12_FACTORS = {
    "codebase": True,  # Factor 1: One codebase tracked in revision control
    "dependencies": True,  # Factor 2: Explicitly declare and isolate dependencies
    "config": True,  # Factor 3: Store config in the environment
    "structured_outputs": True,  # Factor 4: Tools as Structured Outputs (CORE)
    "build_run_separation": True,  # Factor 5: Strictly separate build and run stages
    "stateless": True,  # Factor 6: Execute as stateless processes (CORE)
    "port_binding": True,  # Factor 7: Export services via port binding (or function calls)
    "concurrency": True,  # Factor 8: Scale out via the process model
    "disposability": True,  # Factor 9: Maximize robustness with fast startup
    "single_responsibility": True,  # Factor 10: Small, Focused Agents (CORE)
    "autonomous": True,  # Factor 11: Autonomous operation
    "api_first": True,  # Factor 12: API First design
}


class TestToolCompliance:
    """Test 12-factor compliance for the tool"""

    @pytest.fixture
    def tool_config_path(self):
        """Path to tool's 12factors.toml configuration"""
        tool_dir = project_root / "tools" / TOOL_NAME
        return tool_dir / "12factors.toml"

    def test_12factors_config_exists(self, tool_config_path):
        """Verify 12factors.toml configuration file exists"""
        assert tool_config_path.exists(), f"Missing 12factors.toml at {tool_config_path}"

    def test_tool_has_required_structure(self):
        """Verify tool has required directory structure"""
        tool_dir = project_root / "tools" / TOOL_NAME

        # Required files
        assert (tool_dir / "12factors.toml").exists(), "Missing 12factors.toml"
        assert (tool_dir / "app").is_dir(), "Missing app/ directory"

        # Optional but recommended
        recommended_files = ["README.md", "requirements.txt", ".env.example"]
        for file in recommended_files:
            if not (tool_dir / file).exists():
                print(f"Warning: Recommended file missing: {file}")

    def test_factor_4_structured_outputs(self):
        """
        Factor 4: Tools as Structured Outputs
        Verify tool returns structured, validated outputs (not raw strings/dicts)
        """
        # This test should verify that tool outputs are BAML-validated dataclasses
        # Implementation depends on specific tool
        pass

    def test_factor_6_stateless_execution(self):
        """
        Factor 6: Stateless Processes
        Verify tool maintains no state between executions
        """
        # Execute tool twice with same inputs, verify identical outputs
        # No state should persist between runs
        pass

    def test_factor_10_single_responsibility(self):
        """
        Factor 10: Single Responsibility
        Verify tool does one thing and does it well
        """
        # Review tool's public methods - should have clear, focused purpose
        pass


class TestToolFunctionality:
    """Test core functionality of the tool"""

    @pytest.fixture
    async def tool_instance(self):
        """Create tool instance for testing"""
        # Import tool class dynamically
        module_path, class_name = TOOL_MODULE_PATH.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        tool_class = getattr(module, TOOL_CLASS_NAME)

        # Instantiate tool
        tool = tool_class()
        yield tool

        # Cleanup if needed
        if hasattr(tool, "cleanup"):
            await tool.cleanup()

    @pytest.mark.asyncio
    async def test_tool_execute_basic(self, tool_instance):
        """Test basic tool execution"""
        # UPDATE THIS WITH ACTUAL TOOL INPUT
        test_input = {
            "example_field": "example_value"
        }

        # Execute tool
        result = await tool_instance.execute(test_input)

        # Basic assertions
        assert result is not None, "Tool returned None"
        assert hasattr(result, "success"), "Result missing 'success' field"

    @pytest.mark.asyncio
    async def test_tool_output_structure(self, tool_instance):
        """Test that tool output matches expected BAML schema"""
        # UPDATE THIS WITH ACTUAL TOOL INPUT
        test_input = {
            "example_field": "example_value"
        }

        # Execute tool
        result = await tool_instance.execute(test_input)

        # Verify output structure
        # UPDATE WITH EXPECTED BAML TYPE
        # assert isinstance(result, ExpectedBAMLType), f"Expected ExpectedBAMLType, got {type(result)}"

        # Verify required fields exist
        # UPDATE WITH ACTUAL REQUIRED FIELDS
        required_fields = ["field1", "field2", "field3"]
        for field in required_fields:
            assert hasattr(result, field), f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_tool_handles_invalid_input(self, tool_instance):
        """Test tool error handling with invalid input"""
        # UPDATE WITH INVALID INPUT FOR YOUR TOOL
        invalid_input = {}

        # Should raise validation error or return error result
        with pytest.raises(Exception):
            await tool_instance.execute(invalid_input)

    @pytest.mark.asyncio
    async def test_tool_performance(self, tool_instance):
        """Test tool execution performance"""
        import time

        # UPDATE WITH ACTUAL TOOL INPUT
        test_input = {
            "example_field": "example_value"
        }

        # Measure execution time
        start = time.time()
        result = await tool_instance.execute(test_input)
        duration = time.time() - start

        # UPDATE WITH EXPECTED PERFORMANCE THRESHOLD (seconds)
        max_duration = 5.0  # 5 seconds
        assert duration < max_duration, f"Tool took {duration:.2f}s, expected < {max_duration}s"


class TestToolIntegration:
    """Test tool integration with system components"""

    def test_tool_imports_cleanly(self):
        """Test that tool can be imported without errors"""
        try:
            module_path, class_name = TOOL_MODULE_PATH.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            tool_class = getattr(module, TOOL_CLASS_NAME)
            assert tool_class is not None
        except ImportError as e:
            pytest.fail(f"Failed to import tool: {e}")

    def test_tool_in_registry(self):
        """Test that tool is registered in ToolRegistry"""
        from src.core.tool_registry import ToolRegistry

        registry = ToolRegistry()
        tools = registry.list_tools()

        # UPDATE WITH ACTUAL TOOL ID
        tool_id = TOOL_NAME.replace("-", "_")
        tool_names = [t["id"] for t in tools]

        assert tool_id in tool_names, f"Tool {tool_id} not found in registry. Available: {tool_names}"

    @pytest.mark.asyncio
    async def test_tool_via_api(self):
        """Test tool execution via REST API (if applicable)"""
        # This requires the FastAPI server to be running
        # Skip if server not available
        pytest.skip("API integration test - requires running server")


class TestToolBAMLValidation:
    """Test BAML schema validation for tool outputs"""

    def test_baml_schema_exists(self):
        """Verify BAML schema is defined for tool outputs"""
        # Check that expected BAML types are available
        # UPDATE WITH ACTUAL BAML TYPES
        try:
            # Example: from baml_client.types import ExpectedOutputType
            pass
        except ImportError as e:
            pytest.fail(f"BAML types not available: {e}")

    @pytest.mark.asyncio
    async def test_output_validates_against_baml(self, tool_instance):
        """Test that tool output validates against BAML schema"""
        # UPDATE WITH ACTUAL TOOL INPUT
        test_input = {
            "example_field": "example_value"
        }

        # Execute tool
        result = await tool_instance.execute(test_input)

        # Validate against BAML schema
        # UPDATE WITH ACTUAL BAML VALIDATOR
        # from src.core.tool_framework.baml_validator import BAMLValidator
        # validator = BAMLValidator()
        # is_valid, errors = validator.validate(result, ExpectedBAMLSchema)
        # assert is_valid, f"BAML validation failed: {errors}"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for 12-factor tool tests"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_api: marks tests that require running API server"
    )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
