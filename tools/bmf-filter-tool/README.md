# BMF Filter Tool - 12-Factor Implementation
*🟢 Beginner Level - Working Implementation Following 12-Factor Agents Framework*

## What This Tool Does

The BMF Filter Tool demonstrates the 12-factor agents framework by filtering IRS nonprofit organizations from the existing Catalynx intelligence database. This is a **working implementation** integrated with the existing Catalynx platform.

**Think of it like**: A specialized search engine for nonprofits that follows 12-factor principles - you give it criteria, it finds matching organizations using structured input/output.

## Integration with Catalynx

This tool integrates directly with the existing Catalynx platform:
- **Database**: Uses existing `data/nonprofit_intelligence.db` (2M+ records)
- **Environment**: Extends existing `.env` configuration
- **Architecture**: Demonstrates 12-factor patterns alongside existing processors
- **Performance**: Benchmarked against existing BMF processor

## 12-Factor Agents Principles (Human Layer Framework)

This tool implements the [Human Layer 12-Factor Agents Framework](https://github.com/humanlayer/12-factor-agents):

**Factor 1: Natural Language to Tool Calls** - Converts "Find education orgs in VA" → structured database queries
**Factor 2: Own Your Prompts** - BAML schema provides full prompt control, deterministic structure
**Factor 3: Own Your Context Window** - Minimal context usage, database handles heavy lifting
**Factor 4: Tools as Structured Outputs** - Forces LLM to output well-formed JSON, eliminating parsing errors
**Factor 5: Unify Execution and Business State** - Agent state unified with nonprofit database workflows
**Factor 6: Launch/Pause/Resume with Simple APIs** - Single async execute() method, workflow integration
**Factor 10: Small, Focused Agents** - Single responsibility: filter 700K BMF records to ~10 organizations
**Factor 12: Stateless Reducer Model** - Pure function: BMFFilterCriteria → BMFFilterResult

### Key Innovation: Factor 4 Implementation

The core innovation is treating the tool as a **structured output generator**:
- LLM generates `BMFFilterIntent`
- Tool executes deterministic database query
- Returns structured `BMFFilterResult` with guaranteed JSON format
- **Eliminates "2 AM JSON parsing errors"** common in LLM applications

## Tool Structure (Following Official HumanLayer Conventions)

```
tools/bmf-filter-tool/
├── README.md              # This file
├── .env.tool               # Tool-specific environment configuration
├── 12factors.toml         # Tool metadata and compliance tracking
├── pyproject.toml         # Python dependencies and build config
├── baml_src/              # BAML schemas and AI definitions
│   ├── bmf_filter.baml    # Tool input/output definitions
│   ├── clients.baml       # LLM client configurations
│   └── generators.baml    # Code generation settings
├── app/                   # Implementation code
│   ├── __init__.py
│   ├── generated/         # BAML generated types (auto-created)
│   ├── bmf_filter.py      # Core tool logic
│   ├── agent.py           # LLM integration
│   ├── server.py          # HTTP service
│   └── main.py            # Entry point and examples
└── tests/                 # Test suite
    ├── test_tool.py       # Unit tests
    ├── test_integration.py # Integration tests
    └── test_performance.py # Performance benchmarks
```

## Quick Start

### 1. Environment Setup
```bash
# Activate existing Catalynx environment
cd /path/to/Grant_Automation

# Install BAML (if not already installed)
pip install baml-py>=0.60.0

# Install tool dependencies
pip install -e tools/bmf-filter-tool/
```

### 2. Configuration
```bash
# Copy tool environment template
cp tools/bmf-filter-tool/.env.tool.example tools/bmf-filter-tool/.env.tool

# Edit tool-specific settings
# All settings extend existing Catalynx .env configuration
```

### 3. Run Examples
```bash
# Run tool examples with real Catalynx data
python tools/bmf-filter-tool/app/main.py

# Start HTTP service
python tools/bmf-filter-tool/app/server.py

# Test with curl
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Find education nonprofits in Virginia with revenue over 500K"}'
```

## Key Learning Demonstrations

### 1. Structured Input/Output (Factor 4)
```python
# LLM produces this structured intent
intent = BMFFilterIntent(
    criteria=BMFFilterCriteria(
        states=["VA"],
        ntee_codes=["P20"],
        revenue_min=500000
    ),
    what_youre_looking_for="Education nonprofits in Virginia with significant funding"
)

# Tool executes deterministically and returns structured result
result = await tool.execute(intent)
# result.organizations, result.summary, result.execution_metadata
```

### 2. Comparison with Existing Architecture
This tool demonstrates 12-factor patterns alongside existing Catalynx processors:

**Existing BMF Processor**: Monolithic, mixed concerns, configuration scattered
**12-Factor Tool**: Single purpose, structured I/O, environment config, stateless

### 3. Performance Benchmarking
- **Database**: Same 2M+ record intelligence database
- **Query Performance**: Measured against existing BMF processor
- **Memory Usage**: Stateless vs stateful comparison
- **Startup Time**: Fast startup/shutdown demonstration

## Integration Examples

### Example 1: Direct Tool Usage
```python
from app.bmf_filter import BMFFilterTool
from app.generated.baml_types import BMFFilterIntent, BMFFilterCriteria

tool = BMFFilterTool()
intent = BMFFilterIntent(
    criteria=BMFFilterCriteria(states=["VA"], revenue_min=1000000),
    what_youre_looking_for="Large Virginia nonprofits"
)
result = await tool.execute(intent)
```

### Example 2: Agent with Natural Language
```python
from app.agent import BMFFilterAgent

agent = BMFFilterAgent()
result = await agent.process_natural_language_request(
    "Find health organizations in DC with assets over $2M"
)
```

### Example 3: HTTP API Integration
```bash
# Start service on port 8001
python app/server.py

# Use in workflows or other tools
curl -X POST http://localhost:8001/filter \
  -H "Content-Type: application/json" \
  -d '{"intent": "bmf_filter", "criteria": {...}}'
```

## Development and Testing

### Run Tests
```bash
# Unit tests
pytest tools/bmf-filter-tool/tests/test_tool.py

# Integration tests with real database
pytest tools/bmf-filter-tool/tests/test_integration.py

# Performance benchmarks
pytest tools/bmf-filter-tool/tests/test_performance.py
```

### Development Mode
```bash
# Install in development mode
pip install -e tools/bmf-filter-tool/[dev]

# Auto-reload server for development
uvicorn app.server:app --reload --port 8001
```

## Architecture Comparison

| Aspect | Existing Processor | 12-Factor Tool |
|--------|-------------------|----------------|
| **Purpose** | Multi-purpose BMF processing | Single-purpose filtering only |
| **Input** | Mixed formats, scattered config | Structured BAML schemas |
| **State** | Maintains state between calls | Completely stateless |
| **Config** | Hardcoded + scattered env vars | All config from environment |
| **Testing** | Complex integration testing | Simple unit + integration tests |
| **Deployment** | Coupled to main application | Independent HTTP service |
| **Reusability** | Tightly coupled | Composable with other tools |

## Next Steps

This tool demonstrates the 12-factor pattern and provides a foundation for:

1. **Learning**: Understanding 12-factor agent principles
2. **Migration**: Pathway for transforming existing processors
3. **Orchestration**: Building workflows with multiple 12-factor tools
4. **Performance**: Comparing architectural approaches
5. **Scalability**: Independent scaling and deployment

The implementation shows how 12-factor principles can work alongside existing successful systems while providing clear benefits for modularity, testing, and maintainability.