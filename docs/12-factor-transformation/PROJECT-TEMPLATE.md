# Project Starter Template: 12-Factor AI Agent Projects

## Overview

This template provides a complete starting point for new 12-factor compliant AI agent projects. Based on the Catalynx transformation, it includes all essential components, configurations, and patterns needed to build production-ready AI systems from day one.

## Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** (for BAML)
- **Docker** (for containerization)
- **Git** (for version control)

### Project Initialization
```bash
# Create new project
mkdir my-ai-agent-project
cd my-ai-agent-project

# Copy template structure (customize as needed)
git clone https://github.com/your-org/12factor-ai-template .

# Initialize environment
./scripts/setup.sh
```

---

## Directory Structure Template

```
my-ai-agent-project/
├── README.md                          # Project overview and setup
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Python project configuration
├── Dockerfile                         # Container configuration
├── docker-compose.yml                 # Local development
├── docker-compose.prod.yml            # Production deployment
├── .github/
│   └── workflows/
│       ├── ci.yml                     # Continuous integration
│       ├── cd.yml                     # Continuous deployment
│       └── security.yml               # Security scanning
├── .gitignore                         # Git ignore rules
├── .env.example                       # Environment variables template
├── pytest.ini                         # Test configuration
├── setup.cfg                          # Code style configuration
├── baml/                              # BAML schemas and functions
│   ├── baml_src/
│   │   ├── functions/                 # BAML function definitions
│   │   │   ├── __init__.baml
│   │   │   ├── data_processing.baml
│   │   │   ├── analysis.baml
│   │   │   └── validation.baml
│   │   ├── types/                     # BAML type definitions
│   │   │   ├── __init__.baml
│   │   │   ├── base_types.baml
│   │   │   ├── domain_types.baml
│   │   │   └── response_types.baml
│   │   └── clients/                   # BAML client configurations
│   │       ├── __init__.baml
│   │       └── ai_clients.baml
│   ├── baml.toml                      # BAML project configuration
│   └── .bamlrc                        # BAML runtime configuration
├── src/                               # Application source code
│   ├── __init__.py
│   ├── main.py                        # Application entry point
│   ├── core/                          # Core framework components
│   │   ├── __init__.py
│   │   ├── tool_registry.py           # Tool registration system
│   │   ├── base_tool.py               # Base tool interface
│   │   ├── state_manager.py           # State management
│   │   ├── error_handler.py           # Error handling
│   │   └── config.py                  # Configuration management
│   ├── tools/                         # Individual micro-tools
│   │   ├── __init__.py
│   │   ├── data_validator_tool.py     # Example tool
│   │   ├── ai_analyzer_tool.py        # Example AI tool
│   │   └── report_generator_tool.py   # Example output tool
│   ├── workflows/                     # Workflow orchestration
│   │   ├── __init__.py
│   │   ├── workflow_engine.py         # Workflow execution engine
│   │   ├── workflow_parser.py         # YAML workflow parser
│   │   └── definitions/               # Workflow definitions
│   │       ├── basic_analysis.yaml
│   │       └── comprehensive_analysis.yaml
│   ├── web/                           # Web interface (optional)
│   │   ├── __init__.py
│   │   ├── api.py                     # FastAPI application
│   │   ├── models.py                  # Pydantic models
│   │   ├── routes/                    # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── tools.py
│   │   │   ├── workflows.py
│   │   │   └── health.py
│   │   └── static/                    # Frontend assets
│   │       ├── index.html
│   │       ├── css/
│   │       └── js/
│   ├── triggers/                      # Multi-channel triggers
│   │   ├── __init__.py
│   │   ├── trigger_manager.py         # Unified trigger system
│   │   ├── web_handler.py             # Web trigger handler
│   │   ├── api_handler.py             # API trigger handler
│   │   └── cli_handler.py             # CLI trigger handler
│   ├── monitoring/                    # Observability
│   │   ├── __init__.py
│   │   ├── metrics.py                 # Prometheus metrics
│   │   ├── logging.py                 # Structured logging
│   │   └── health_checks.py           # Health monitoring
│   └── cli/                           # Command line interface
│       ├── __init__.py
│       ├── main.py                    # CLI entry point
│       └── commands/                  # CLI commands
│           ├── __init__.py
│           ├── analyze.py
│           └── status.py
├── tests/                             # Test suite
│   ├── __init__.py
│   ├── conftest.py                    # Test configuration
│   ├── unit/                          # Unit tests
│   │   ├── __init__.py
│   │   ├── test_tools/
│   │   ├── test_workflows/
│   │   └── test_core/
│   ├── integration/                   # Integration tests
│   │   ├── __init__.py
│   │   ├── test_workflow_execution.py
│   │   └── test_api_endpoints.py
│   ├── e2e/                          # End-to-end tests
│   │   ├── __init__.py
│   │   └── test_complete_workflows.py
│   └── fixtures/                      # Test data and fixtures
│       ├── sample_data.json
│       └── mock_responses.py
├── config/                            # Configuration files
│   ├── settings.yaml                  # Application settings
│   ├── logging.yaml                   # Logging configuration
│   └── environments/                  # Environment-specific configs
│       ├── development.yaml
│       ├── staging.yaml
│       └── production.yaml
├── scripts/                           # Utility scripts
│   ├── setup.sh                       # Initial setup script
│   ├── deploy.sh                      # Deployment script
│   ├── migrate.py                     # Database migration
│   └── validate_config.py             # Configuration validation
├── docs/                              # Project documentation
│   ├── README.md                      # Main documentation
│   ├── API.md                         # API documentation
│   ├── DEPLOYMENT.md                  # Deployment guide
│   └── DEVELOPMENT.md                 # Development guide
└── monitoring/                        # Monitoring configuration
    ├── prometheus.yml                 # Prometheus configuration
    ├── grafana/                       # Grafana dashboards
    │   ├── dashboards/
    │   └── provisioning/
    └── alerts/                        # Alert rules
        └── alerting_rules.yml
```

---

## Essential Configuration Files

### BAML Project Configuration
```toml
# baml/baml.toml
[project]
name = "my-ai-agent"
version = "1.0.0"
description = "12-Factor AI Agent Project"

[client.openai]
provider = "openai"
model = "gpt-4"
api_key = { env = "OPENAI_API_KEY" }

[client.anthropic]
provider = "anthropic"
model = "claude-3-sonnet-20240229"
api_key = { env = "ANTHROPIC_API_KEY" }

[generate]
target_dir = "baml_client"
version = "0.56.0"
```

### Python Project Configuration
```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-ai-agent"
version = "1.0.0"
description = "12-Factor AI Agent Project"
authors = [{name = "Your Name", email = "your.email@example.com"}]
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "asyncio>=3.4.3",
    "aiohttp>=3.9.0",
    "PyYAML>=6.0.1",
    "prometheus-client>=0.19.0",
    "structlog>=23.2.0",
    "click>=8.1.7",
    "python-multipart>=0.0.6",
    "python-jose[cryptography]>=3.3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.1.0",
    "mypy>=1.7.0",
    "pre-commit>=3.6.0",
]

[project.scripts]
my-ai-agent = "src.cli.main:cli"

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.isort]
profile = "black"
src_paths = ["src", "tests"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=html --cov-report=term-missing"
asyncio_mode = "auto"
```

### Environment Variables Template
```bash
# .env.example
# Copy to .env and fill in actual values

# Application Settings
APP_NAME=my-ai-agent
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# AI Model Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///./app.db
# DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Redis Configuration (for caching/sessions)
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# External APIs
EXTERNAL_API_KEY=your_external_api_key
EXTERNAL_API_BASE_URL=https://api.example.com

# Monitoring
PROMETHEUS_PORT=8001
LOG_LEVEL=INFO
ENABLE_METRICS=true

# Human-in-the-Loop
EXPERT_NOTIFICATION_EMAIL=expert@example.com
EXPERT_TIMEOUT_MINUTES=30
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for BAML
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install BAML CLI globally
RUN npm install -g @boundaryml/baml

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy BAML configuration and compile schemas
COPY baml/ ./baml/
RUN cd baml && baml compile

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000 8001

# Default command
CMD ["python", "-m", "uvicorn", "src.web.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Initial BAML Schema Setup

### Base Types
```baml
// baml/baml_src/types/base_types.baml

// Common enums
enum ConfidenceLevel {
  VERY_LOW    // 0.0 - 0.2
  LOW         // 0.2 - 0.4
  MEDIUM      // 0.4 - 0.6
  HIGH        // 0.6 - 0.8
  VERY_HIGH   // 0.8 - 1.0
}

enum ProcessingStatus {
  PENDING
  IN_PROGRESS
  COMPLETED
  FAILED
  PAUSED
}

// Base result type for all tools
class ToolResult {
  success: bool
  data: object?
  errors: string[]
  confidence: float
  execution_metadata: ExecutionMetadata
}

class ExecutionMetadata {
  tool_name: string
  version: string
  execution_time_ms: int
  model_used: string?
  token_usage: TokenUsage?
  timestamp: string
}

class TokenUsage {
  prompt_tokens: int
  completion_tokens: int
  total_tokens: int
  estimated_cost: float
}

// Validation types
class ValidationResult {
  is_valid: bool
  issues: ValidationIssue[]
  recommendations: string[]
  confidence: float
}

class ValidationIssue {
  field_name: string
  issue_type: IssueType
  severity: SeverityLevel
  description: string
  suggested_fix: string
}

enum IssueType {
  MISSING_REQUIRED_FIELD
  INVALID_FORMAT
  OUT_OF_RANGE
  INCONSISTENT_DATA
  DUPLICATE_VALUE
}

enum SeverityLevel {
  LOW
  MEDIUM
  HIGH
  CRITICAL
}
```

### Domain-Specific Types
```baml
// baml/baml_src/types/domain_types.baml

// Example domain types - customize for your use case
class DataEntity {
  id: string
  name: string
  type: EntityType
  attributes: object
  metadata: EntityMetadata
}

enum EntityType {
  ORGANIZATION
  PERSON
  DOCUMENT
  EVENT
  LOCATION
}

class EntityMetadata {
  created_at: string
  updated_at: string
  source: string
  reliability: ReliabilityLevel
  tags: string[]
}

enum ReliabilityLevel {
  VERIFIED
  HIGH
  MEDIUM
  LOW
  UNVERIFIED
}

class AnalysisRequest {
  entity: DataEntity
  analysis_type: AnalysisType
  parameters: AnalysisParameters
  context: AnalysisContext?
}

enum AnalysisType {
  BASIC
  COMPREHENSIVE
  COMPARATIVE
  PREDICTIVE
  CUSTOM
}

class AnalysisParameters {
  depth: AnalysisDepth
  focus_areas: string[]
  time_range: TimeRange?
  comparison_entities: string[]
}

enum AnalysisDepth {
  SURFACE
  MODERATE
  DEEP
  EXHAUSTIVE
}

class TimeRange {
  start_date: string
  end_date: string
  granularity: TimeGranularity
}

enum TimeGranularity {
  DAILY
  WEEKLY
  MONTHLY
  QUARTERLY
  YEARLY
}

class AnalysisContext {
  previous_analyses: AnalysisResult[]
  related_entities: DataEntity[]
  constraints: AnalysisConstraint[]
}

class AnalysisConstraint {
  type: ConstraintType
  value: string
  description: string
}

enum ConstraintType {
  TIME_LIMIT
  RESOURCE_LIMIT
  DATA_SENSITIVITY
  REGULATORY
  BUSINESS_RULE
}
```

### Function Templates
```baml
// baml/baml_src/functions/data_processing.baml

function validate_entity_data {
  client GPT4o
  prompt #"
    Validate the following entity data for completeness and accuracy:

    Entity: {{ entity }}
    Type: {{ entity_type }}

    Check for:
    - Required fields based on entity type
    - Data format validity
    - Logical consistency
    - Completeness score

    Provide structured validation results.
  "#

  response ValidationResult {
    is_valid: bool
    issues: ValidationIssue[]
    recommendations: string[]
    confidence: float
  }
}

function analyze_entity {
  client GPT4o
  prompt #"
    Perform {{ analysis_type }} analysis on the following entity:

    Entity: {{ entity }}
    Parameters: {{ parameters }}
    {% if context %}Context: {{ context }}{% endif %}

    Focus areas: {{ parameters.focus_areas | join(", ") }}

    Provide comprehensive analysis results with insights and recommendations.
  "#

  response AnalysisResult {
    summary: string
    insights: Insight[]
    recommendations: Recommendation[]
    confidence: float
    supporting_evidence: Evidence[]
    next_steps: string[]
  }
}

class AnalysisResult {
  summary: string
  insights: Insight[]
  recommendations: Recommendation[]
  confidence: float
  supporting_evidence: Evidence[]
  next_steps: string[]
}

class Insight {
  category: string
  description: string
  importance: ImportanceLevel
  confidence: float
  supporting_data: string[]
}

enum ImportanceLevel {
  CRITICAL
  HIGH
  MEDIUM
  LOW
  INFORMATIONAL
}

class Recommendation {
  title: string
  description: string
  priority: PriorityLevel
  effort_required: EffortLevel
  expected_impact: ImpactLevel
  timeline: string
  dependencies: string[]
}

enum PriorityLevel {
  URGENT
  HIGH
  MEDIUM
  LOW
  DEFERRED
}

enum EffortLevel {
  MINIMAL
  LOW
  MODERATE
  HIGH
  EXTENSIVE
}

enum ImpactLevel {
  TRANSFORMATIONAL
  MAJOR
  MODERATE
  MINOR
  NEGLIGIBLE
}

class Evidence {
  type: EvidenceType
  description: string
  source: string
  reliability: ReliabilityLevel
  timestamp: string
}

enum EvidenceType {
  QUANTITATIVE_DATA
  QUALITATIVE_OBSERVATION
  EXPERT_OPINION
  HISTORICAL_PATTERN
  EXTERNAL_REFERENCE
}
```

---

## Basic Tool Registry Implementation

### Base Tool Interface
```python
# src/core/base_tool.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import time
import logging

@dataclass
class ToolMetadata:
    name: str
    version: str
    description: str
    baml_schema: str
    estimated_duration: int  # seconds
    dependencies: List[str]
    requires_human_input: bool = False
    resource_requirements: Optional[Dict[str, Any]] = None

class BaseTool(ABC):
    """Base class for all 12-factor tools"""

    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata
        self.logger = logging.getLogger(f"tools.{metadata.name}")

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool with given inputs.

        Args:
            inputs: Dictionary of input parameters

        Returns:
            Dictionary with structure:
            {
                "success": bool,
                "data": Any,
                "errors": List[str],
                "confidence": float,
                "execution_metadata": Dict[str, Any]
            }
        """
        pass

    @abstractmethod
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate that inputs contain required parameters"""
        pass

    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata"""
        return self.metadata

    def _create_result(self,
                      success: bool,
                      data: Any = None,
                      errors: List[str] = None,
                      confidence: float = 1.0) -> Dict[str, Any]:
        """Create standardized tool result"""
        return {
            "success": success,
            "data": data,
            "errors": errors or [],
            "confidence": confidence,
            "execution_metadata": {
                "tool_name": self.metadata.name,
                "version": self.metadata.version,
                "timestamp": time.time(),
                "estimated_duration": self.metadata.estimated_duration
            }
        }
```

### Tool Registry
```python
# src/core/tool_registry.py
from typing import Dict, List, Optional, Set
from .base_tool import BaseTool
import logging

class ToolRegistry:
    """Registry for managing 12-factor tools"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self.logger = logging.getLogger("core.tool_registry")

    def register_tool(self, tool: BaseTool) -> bool:
        """Register a tool in the registry"""
        try:
            tool_name = tool.metadata.name

            # Validate tool
            if not self._validate_tool(tool):
                return False

            # Register tool
            self._tools[tool_name] = tool
            self._dependencies[tool_name] = set(tool.metadata.dependencies)

            self.logger.info(f"Registered tool: {tool_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register tool {tool.metadata.name}: {e}")
            return False

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tools"""
        return list(self._tools.keys())

    def get_dependencies(self, tool_name: str) -> Set[str]:
        """Get dependencies for a tool"""
        return self._dependencies.get(tool_name, set())

    def validate_dependencies(self, tool_name: str) -> bool:
        """Validate that all dependencies are available"""
        if tool_name not in self._dependencies:
            return False

        dependencies = self._dependencies[tool_name]
        return all(dep in self._tools for dep in dependencies)

    def get_execution_order(self, tools: List[str]) -> List[str]:
        """Get execution order based on dependencies"""
        # Topological sort
        order = []
        remaining = set(tools)

        while remaining:
            # Find tools with no remaining dependencies
            ready = {tool for tool in remaining
                    if self._dependencies.get(tool, set()).issubset(set(order))}

            if not ready:
                raise ValueError(f"Circular dependency detected in tools: {remaining}")

            # Add ready tools to order
            for tool in ready:
                order.append(tool)
                remaining.remove(tool)

        return order

    def _validate_tool(self, tool: BaseTool) -> bool:
        """Validate tool before registration"""
        # Check required attributes
        if not hasattr(tool, 'metadata'):
            self.logger.error(f"Tool missing metadata: {tool}")
            return False

        # Check for duplicate names
        if tool.metadata.name in self._tools:
            self.logger.error(f"Tool already registered: {tool.metadata.name}")
            return False

        # Validate BAML schema exists (basic check)
        if not tool.metadata.baml_schema:
            self.logger.warning(f"Tool has no BAML schema: {tool.metadata.name}")

        return True

# Global registry instance
tool_registry = ToolRegistry()
```

### Example Tool Implementation
```python
# src/tools/data_validator_tool.py
from src.core.base_tool import BaseTool, ToolMetadata
from src.core.tool_registry import tool_registry
from typing import Dict, Any
import baml_client

class DataValidatorTool(BaseTool):
    """Example tool for validating entity data"""

    def __init__(self):
        metadata = ToolMetadata(
            name="data_validator_tool",
            version="1.0.0",
            description="Validates entity data for completeness and accuracy",
            baml_schema="validate_entity_data",
            estimated_duration=30,
            dependencies=[],
            requires_human_input=False
        )
        super().__init__(metadata)

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data validation"""

        if not self.validate_inputs(inputs):
            return self._create_result(
                success=False,
                errors=["Invalid inputs: missing required fields"]
            )

        try:
            # Use BAML for validation
            result = await baml_client.validate_entity_data(
                entity=inputs["entity"],
                entity_type=inputs.get("entity_type", "unknown")
            )

            return self._create_result(
                success=True,
                data={
                    "is_valid": result.is_valid,
                    "issues": [issue.dict() for issue in result.issues],
                    "recommendations": result.recommendations,
                    "validation_confidence": result.confidence
                },
                confidence=result.confidence
            )

        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return self._create_result(
                success=False,
                errors=[f"Validation error: {str(e)}"]
            )

    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate required inputs"""
        required = ["entity"]
        return all(field in inputs for field in required)

# Auto-register tool
tool_registry.register_tool(DataValidatorTool())
```

---

## Minimal Workflow Examples

### Basic Analysis Workflow
```yaml
# src/workflows/definitions/basic_analysis.yaml
workflow: basic_entity_analysis
description: "Basic analysis workflow for entity data"
estimated_duration: 300  # 5 minutes
estimated_cost: 1.00

inputs:
  - name: entity_data
    type: object
    required: true
  - name: analysis_depth
    type: enum
    values: [surface, moderate, deep]
    default: moderate

steps:
  - name: validate_data
    tool: data_validator_tool
    inputs:
      entity: "{{ entity_data }}"
      entity_type: "{{ entity_data.type }}"
    outputs:
      validation_result: data

  - name: analyze_entity
    tool: entity_analyzer_tool
    depends_on: [validate_data]
    condition: "{{ validation_result.is_valid }}"
    inputs:
      entity: "{{ entity_data }}"
      analysis_type: "basic"
      parameters:
        depth: "{{ analysis_depth }}"
        focus_areas: ["overview", "key_attributes"]
    outputs:
      analysis_result: data

  - name: generate_summary
    tool: summary_generator_tool
    depends_on: [analyze_entity]
    inputs:
      analysis_data: "{{ analysis_result }}"
      format: "brief"
    outputs:
      summary: data

quality_gates:
  - gate: data_quality
    condition: "{{ validation_result.validation_confidence }} > 0.7"
    failure_action: request_data_improvement

  - gate: analysis_confidence
    condition: "{{ analysis_result.confidence }} > 0.6"
    failure_action: flag_for_review
```

### Comprehensive Analysis Workflow
```yaml
# src/workflows/definitions/comprehensive_analysis.yaml
workflow: comprehensive_entity_analysis
description: "Comprehensive analysis with human validation"
estimated_duration: 1800  # 30 minutes
estimated_cost: 5.00

extends: basic_entity_analysis

additional_inputs:
  - name: include_predictions
    type: boolean
    default: false
  - name: expert_validation
    type: boolean
    default: true

additional_steps:
  - name: deep_analysis
    tool: entity_analyzer_tool
    depends_on: [analyze_entity]
    inputs:
      entity: "{{ entity_data }}"
      analysis_type: "comprehensive"
      parameters:
        depth: "deep"
        focus_areas: ["detailed_attributes", "relationships", "patterns"]
    outputs:
      deep_analysis: data

  - name: predictive_analysis
    tool: predictive_analyzer_tool
    depends_on: [deep_analysis]
    condition: "{{ include_predictions }}"
    inputs:
      entity: "{{ entity_data }}"
      base_analysis: "{{ deep_analysis }}"
    outputs:
      predictions: data

  - name: expert_validation
    tool: expert_validator_tool
    depends_on: [deep_analysis, predictive_analysis]
    condition: "{{ expert_validation }}"
    inputs:
      analysis_package: {
        "entity": "{{ entity_data }}",
        "basic_analysis": "{{ analysis_result }}",
        "deep_analysis": "{{ deep_analysis }}",
        "predictions": "{{ predictions }}"
      }
      expert_type: "domain_specialist"
      timeout: 1800
    outputs:
      expert_feedback: data

  - name: generate_comprehensive_report
    tool: report_generator_tool
    depends_on: [expert_validation]
    inputs:
      report_type: "comprehensive"
      data: {
        "entity": "{{ entity_data }}",
        "analysis": "{{ deep_analysis }}",
        "predictions": "{{ predictions }}",
        "expert_feedback": "{{ expert_feedback }}"
      }
    outputs:
      final_report: data

human_checkpoints:
  - checkpoint: expert_review
    required_for: ["comprehensive", "critical"]
    timeout: 1800
    fallback_strategy: "proceed_with_notation"

parallel_execution:
  - group: detailed_analysis
    tools:
      - deep_analysis
      - predictive_analysis
    max_parallel: 2
```

---

## Testing Framework Setup

### Test Configuration
```python
# tests/conftest.py
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from src.core.tool_registry import tool_registry
from src.workflows.workflow_engine import WorkflowEngine

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def clean_registry() -> AsyncGenerator:
    """Provide a clean tool registry for testing"""
    # Store original tools
    original_tools = tool_registry._tools.copy()
    original_deps = tool_registry._dependencies.copy()

    # Clear registry
    tool_registry._tools.clear()
    tool_registry._dependencies.clear()

    yield tool_registry

    # Restore original state
    tool_registry._tools = original_tools
    tool_registry._dependencies = original_deps

@pytest.fixture
def sample_entity():
    """Sample entity data for testing"""
    return {
        "id": "test-entity-001",
        "name": "Test Entity",
        "type": "ORGANIZATION",
        "attributes": {
            "category": "test",
            "status": "active"
        },
        "metadata": {
            "created_at": "2025-01-01T00:00:00Z",
            "source": "test_data",
            "reliability": "HIGH"
        }
    }

@pytest.fixture
def workflow_engine():
    """Workflow engine instance for testing"""
    return WorkflowEngine()

@pytest.fixture
def mock_baml_response():
    """Mock BAML response for testing"""
    class MockResponse:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    return MockResponse
```

### Unit Test Template
```python
# tests/unit/test_tools/test_data_validator_tool.py
import pytest
from unittest.mock import patch, AsyncMock
from src.tools.data_validator_tool import DataValidatorTool

class TestDataValidatorTool:

    @pytest.fixture
    def tool(self):
        return DataValidatorTool()

    def test_tool_metadata(self, tool):
        """Test tool metadata is correctly set"""
        assert tool.metadata.name == "data_validator_tool"
        assert tool.metadata.version == "1.0.0"
        assert tool.metadata.baml_schema == "validate_entity_data"
        assert not tool.metadata.requires_human_input

    def test_input_validation_success(self, tool, sample_entity):
        """Test successful input validation"""
        inputs = {"entity": sample_entity}
        assert tool.validate_inputs(inputs) is True

    def test_input_validation_failure(self, tool):
        """Test input validation with missing required fields"""
        inputs = {"wrong_field": "value"}
        assert tool.validate_inputs(inputs) is False

    @pytest.mark.asyncio
    @patch('baml_client.validate_entity_data')
    async def test_successful_execution(self, mock_baml, tool, sample_entity, mock_baml_response):
        """Test successful tool execution"""
        # Mock BAML response
        mock_response = mock_baml_response(
            is_valid=True,
            issues=[],
            recommendations=["Data quality is good"],
            confidence=0.9
        )
        mock_baml.return_value = mock_response

        inputs = {"entity": sample_entity}
        result = await tool.execute(inputs)

        assert result["success"] is True
        assert result["data"]["is_valid"] is True
        assert result["confidence"] == 0.9
        assert "execution_metadata" in result
        mock_baml.assert_called_once()

    @pytest.mark.asyncio
    async def test_execution_with_invalid_inputs(self, tool):
        """Test execution with invalid inputs"""
        inputs = {}
        result = await tool.execute(inputs)

        assert result["success"] is False
        assert "Invalid inputs" in result["errors"][0]
        assert result["data"] is None

    @pytest.mark.asyncio
    @patch('baml_client.validate_entity_data')
    async def test_execution_with_baml_error(self, mock_baml, tool, sample_entity):
        """Test execution when BAML call fails"""
        mock_baml.side_effect = Exception("BAML API error")

        inputs = {"entity": sample_entity}
        result = await tool.execute(inputs)

        assert result["success"] is False
        assert "Validation error" in result["errors"][0]
        assert result["data"] is None
```

### Integration Test Template
```python
# tests/integration/test_workflow_execution.py
import pytest
from src.workflows.workflow_engine import WorkflowEngine
from src.workflows.workflow_parser import WorkflowParser

class TestWorkflowExecution:

    @pytest.fixture
    def workflow_engine(self):
        return WorkflowEngine()

    @pytest.fixture
    def workflow_parser(self):
        return WorkflowParser()

    @pytest.mark.asyncio
    async def test_basic_workflow_execution(self, workflow_engine, workflow_parser, sample_entity):
        """Test complete basic analysis workflow"""

        # Load workflow definition
        workflow_def = workflow_parser.parse_workflow(
            "src/workflows/definitions/basic_analysis.yaml"
        )

        # Execute workflow
        inputs = {
            "entity_data": sample_entity,
            "analysis_depth": "moderate"
        }

        result = await workflow_engine.execute_workflow(
            workflow_def=workflow_def,
            inputs=inputs,
            workflow_id="test_basic_001"
        )

        # Validate results
        assert result.status == WorkflowStatus.COMPLETED
        assert len(result.completed_steps) > 0
        assert "summary" in result.step_outputs.get("generate_summary", {})

    @pytest.mark.asyncio
    async def test_workflow_with_failed_quality_gate(self, workflow_engine, workflow_parser):
        """Test workflow behavior when quality gate fails"""

        # Use entity data that will fail validation
        invalid_entity = {"id": "invalid", "name": ""}

        workflow_def = workflow_parser.parse_workflow(
            "src/workflows/definitions/basic_analysis.yaml"
        )

        inputs = {
            "entity_data": invalid_entity,
            "analysis_depth": "moderate"
        }

        result = await workflow_engine.execute_workflow(
            workflow_def=workflow_def,
            inputs=inputs,
            workflow_id="test_failed_gate_001"
        )

        # Workflow should handle failure gracefully
        assert result.status in [WorkflowStatus.FAILED, WorkflowStatus.COMPLETED]
        assert len(result.error_context) > 0 if result.status == WorkflowStatus.FAILED else True
```

---

## Setup Scripts

### Initial Setup Script
```bash
#!/bin/bash
# scripts/setup.sh

set -e

echo "🚀 Setting up 12-Factor AI Agent Project..."

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11+ is required"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"

# Install BAML CLI
echo "🔧 Installing BAML CLI..."
npm install -g @boundaryml/baml

# Setup BAML project
echo "🏗️ Setting up BAML schemas..."
cd baml
baml compile
cd ..

# Setup pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
pre-commit install

# Create environment file
if [ ! -f .env ]; then
    echo "📄 Creating environment file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual configuration values"
fi

# Initialize database (if applicable)
echo "🗄️ Initializing database..."
python scripts/migrate.py

# Run initial tests
echo "🧪 Running initial tests..."
pytest tests/unit/ -v

echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Update BAML schemas in baml/baml_src/"
echo "3. Implement your domain-specific tools"
echo "4. Define your workflows in src/workflows/definitions/"
echo "5. Run 'python -m src.cli.main --help' to see available commands"
echo ""
echo "To start development:"
echo "source venv/bin/activate"
echo "python -m uvicorn src.web.api:app --reload"
```

### Configuration Validation Script
```python
# scripts/validate_config.py
#!/usr/bin/env python3
"""
Configuration validation script for 12-Factor AI Agent projects
"""

import os
import sys
import yaml
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class ConfigValidator:
    """Validate project configuration"""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("🔍 Validating project configuration...")

        self.validate_environment_variables()
        self.validate_baml_configuration()
        self.validate_dependencies()
        self.validate_directory_structure()
        self.validate_docker_configuration()

        self.print_results()
        return len(self.errors) == 0

    def validate_environment_variables(self):
        """Validate required environment variables"""
        required_env_vars = [
            "OPENAI_API_KEY",
            "SECRET_KEY",
            "JWT_SECRET_KEY"
        ]

        for var in required_env_vars:
            if not os.getenv(var):
                self.errors.append(f"Missing required environment variable: {var}")

        # Check database URL format
        db_url = os.getenv("DATABASE_URL", "")
        if db_url and not (db_url.startswith("sqlite:") or db_url.startswith("postgresql:")):
            self.warnings.append("DATABASE_URL format may be invalid")

    def validate_baml_configuration(self):
        """Validate BAML configuration"""
        baml_config = Path("baml/baml.toml")
        if not baml_config.exists():
            self.errors.append("BAML configuration file not found: baml/baml.toml")
            return

        try:
            # Check if BAML compiles
            result = subprocess.run(
                ["baml", "compile"],
                cwd="baml",
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                self.errors.append(f"BAML compilation failed: {result.stderr}")
        except FileNotFoundError:
            self.errors.append("BAML CLI not found. Run: npm install -g @boundaryml/baml")

    def validate_dependencies(self):
        """Validate Python dependencies"""
        try:
            import fastapi
            import pydantic
            import uvicorn
        except ImportError as e:
            self.errors.append(f"Missing required Python dependency: {e}")

        # Check versions
        try:
            import pydantic
            if pydantic.VERSION < "2.0.0":
                self.warnings.append("Pydantic version < 2.0.0 may cause compatibility issues")
        except (ImportError, AttributeError):
            pass

    def validate_directory_structure(self):
        """Validate required directory structure"""
        required_dirs = [
            "src/core",
            "src/tools",
            "src/workflows",
            "baml/baml_src/functions",
            "baml/baml_src/types",
            "tests/unit",
            "tests/integration",
            "config"
        ]

        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                self.warnings.append(f"Recommended directory missing: {dir_path}")

        required_files = [
            "src/core/tool_registry.py",
            "src/core/base_tool.py",
            "baml/baml_src/types/base_types.baml"
        ]

        for file_path in required_files:
            if not Path(file_path).exists():
                self.errors.append(f"Required file missing: {file_path}")

    def validate_docker_configuration(self):
        """Validate Docker configuration"""
        if not Path("Dockerfile").exists():
            self.warnings.append("Dockerfile not found - Docker deployment unavailable")

        if not Path("docker-compose.yml").exists():
            self.warnings.append("docker-compose.yml not found - local Docker development unavailable")

    def print_results(self):
        """Print validation results"""
        if self.errors:
            print("\n❌ Configuration Errors:")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print("\n⚠️  Configuration Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All configuration checks passed!")
        elif not self.errors:
            print("\n✅ Configuration is valid (with warnings)")
        else:
            print(f"\n❌ Configuration validation failed with {len(self.errors)} errors")

if __name__ == "__main__":
    validator = ConfigValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)
```

---

## Usage Examples

### Quick Start Commands
```bash
# Initialize new project
git clone <template-repo> my-ai-project
cd my-ai-project
./scripts/setup.sh

# Validate configuration
python scripts/validate_config.py

# Run development server
source venv/bin/activate
python -m uvicorn src.web.api:app --reload

# Execute workflow via CLI
python -m src.cli.main analyze --entity-id "test-001" --workflow "basic_analysis"

# Run tests
pytest tests/ -v --cov=src

# Build and run with Docker
docker-compose up --build
```

### Customization Checklist
- [ ] Update BAML schemas in `baml/baml_src/` for your domain
- [ ] Implement domain-specific tools in `src/tools/`
- [ ] Define business workflows in `src/workflows/definitions/`
- [ ] Customize CLI commands in `src/cli/commands/`
- [ ] Update configuration in `config/settings.yaml`
- [ ] Modify web interface in `src/web/` (if needed)
- [ ] Add monitoring dashboards in `monitoring/grafana/`
- [ ] Update deployment configuration in `docker-compose.prod.yml`

This project template provides a complete, production-ready foundation for building 12-factor compliant AI agent systems. All components follow the principles and patterns established in the Catalynx transformation, enabling rapid development of scalable, maintainable AI applications.