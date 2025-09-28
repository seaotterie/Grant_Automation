# BMF Filter Tool
*🟢 Beginner Level - Following 12-Factor Agents Structure*

## What This Tool Does

The BMF Filter Tool finds IRS nonprofit organizations based on criteria like state, revenue, and focus area.

**Think of it like**: A search engine for nonprofits - you give it criteria, it finds matching organizations.

## Why This Tool Exists (12-Factor Principle)

**Before**: One big processor that filtered + analyzed + scored + reported everything.

**After**: This tool ONLY filters. Other tools handle other steps.

**12-Factor Principle**: Tools are "structured outputs from your LLM that trigger deterministic code"

## Tool Structure (Following 12-Factor Conventions)

```
bmf-filter-tool/
├── README.md              # This file
├── .env                   # Environment configuration
├── 12factors.toml         # Tool configuration
├── pyproject.toml         # Python dependencies
├── baml_src/              # BAML definitions
│   ├── bmf_filter.baml    # Tool schema
│   ├── clients.baml       # LLM clients
│   └── generators.baml    # Code generation
└── app/                   # Implementation
    ├── __init__.py
    ├── bmf_filter.py      # Main tool logic
    ├── agent.py           # Agent integration
    ├── server.py          # HTTP server
    └── main.py            # Entry point
```

## Configuration Files

### .env
```bash
# Database configuration
BMF_DATABASE_PATH=data/nonprofit_intelligence.db

# Performance settings
BMF_CACHE_ENABLED=true
BMF_MAX_RESULTS=1000
BMF_TIMEOUT_SECONDS=30

# Server settings
BMF_FILTER_PORT=8001
LOG_LEVEL=INFO

# Optional: LLM for enhanced filtering
OPENAI_API_KEY=your_key_here
```

### 12factors.toml
```toml
[tool]
name = "bmf-filter"
version = "1.0.0"
description = "Filter IRS nonprofit data by criteria"

[tool.capabilities]
primary = "bmf_filtering"
secondary = ["nonprofit_discovery", "data_filtering"]

[tool.dependencies]
database = "bmf_organizations"
cache = "optional"

[tool.performance]
max_concurrent = 10
timeout_seconds = 30
cache_ttl = 3600
```

### pyproject.toml
```toml
[project]
name = "bmf-filter-tool"
version = "1.0.0"
description = "12-Factor BMF filtering tool"
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "aiosqlite>=0.19.0",
    "pydantic>=2.0.0",
    "baml-py>=0.60.0"
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
```

## BAML Schema Definition

### baml_src/bmf_filter.baml
```baml
// BMF Filter Tool Schema - Following 12-Factor Pattern

// Tool Intent (Factor 4: Tools are structured outputs)
class BMFFilterIntent {
    intent "bmf_filter"
    criteria BMFFilterCriteria
    what_youre_looking_for string @description("Human description of search goal")
}

// Filter criteria structure
class BMFFilterCriteria {
    states string[]? @description("State codes like VA, MD, DC")
    revenue_min int? @description("Minimum annual revenue")
    revenue_max int? @description("Maximum annual revenue")
    ntee_codes string[]? @description("NTEE codes like P20=Education, B25=Health")
    asset_min int? @description("Minimum assets")
    asset_max int? @description("Maximum assets")
    organization_name string? @description("Partial name search")
    limit int? @default(100) @description("Max results")
}

// Tool output structure
class BMFFilterResult {
    intent "bmf_filter_result"
    organizations BMFOrganization[]
    summary BMFSearchSummary
    execution_metadata BMFExecutionData
}

class BMFOrganization {
    ein string @description("Employer ID Number")
    name string
    city string?
    state string
    ntee_code string @description("Nonprofit category code")
    revenue int? @description("Annual revenue")
    assets int? @description("Total assets")
    match_reasons string[] @description("Why this org matched criteria")
}

class BMFSearchSummary {
    total_found int
    criteria_summary string @description("Human readable search description")
    top_matches_description string @description("Summary of best matches")
}

class BMFExecutionData {
    execution_time_ms float
    cache_hit bool
    database_query_time_ms float
    results_truncated bool
}
```

### baml_src/clients.baml
```baml
client<llm> OpenAI {
    provider openai
    options {
        model gpt-4
        api_key env.OPENAI_API_KEY
    }
}

client<llm> OpenAILite {
    provider openai
    options {
        model gpt-3.5-turbo
        api_key env.OPENAI_API_KEY
    }
}
```

### baml_src/generators.baml
```baml
generator lang_python {
    output_type python/pydantic
    output_dir "../app/generated"
    version "0.60.0"
}
```

## Tool Implementation

### app/bmf_filter.py
```python
"""
BMF Filter Tool - 12-Factor Implementation
Focuses ONLY on filtering BMF data based on criteria
"""

import os
import time
import asyncio
import aiosqlite
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from app.generated.baml_types import (
    BMFFilterIntent, BMFFilterCriteria, BMFFilterResult,
    BMFOrganization, BMFSearchSummary, BMFExecutionData
)

class BMFFilterTool:
    """
    12-Factor Tool: BMF Data Filtering

    This tool implements Factor 4: "Tools are structured outputs"
    - Takes structured input (BMFFilterIntent)
    - Returns structured output (BMFFilterResult)
    - Executes deterministic code
    """

    def __init__(self):
        # Factor 3: Config from environment
        self.database_path = os.getenv("BMF_DATABASE_PATH", "data/nonprofit_intelligence.db")
        self.cache_enabled = os.getenv("BMF_CACHE_ENABLED", "true").lower() == "true"
        self.max_results = int(os.getenv("BMF_MAX_RESULTS", "1000"))
        self.timeout_seconds = int(os.getenv("BMF_TIMEOUT_SECONDS", "30"))

        # Simple cache (in production: use Redis/external cache)
        self._cache: Dict[str, BMFFilterResult] = {}

    async def execute(self, intent: BMFFilterIntent) -> BMFFilterResult:
        """
        Execute BMF filtering based on structured intent

        This follows the 12-factor pattern:
        1. LLM produces structured output (BMFFilterIntent)
        2. This deterministic code executes the intent
        3. Returns structured result (BMFFilterResult)
        """
        start_time = time.time()

        # Check cache first
        cache_key = self._make_cache_key(intent.criteria)
        if self.cache_enabled and cache_key in self._cache:
            cached_result = self._cache[cache_key]
            # Update timing but keep cached data
            cached_result.execution_metadata.cache_hit = True
            cached_result.execution_metadata.execution_time_ms = (time.time() - start_time) * 1000
            return cached_result

        # Execute database query
        db_start = time.time()
        organizations = await self._query_database(intent.criteria)
        db_time = (time.time() - db_start) * 1000

        # Limit results
        results_truncated = len(organizations) > (intent.criteria.limit or 100)
        if intent.criteria.limit:
            organizations = organizations[:intent.criteria.limit]

        # Generate summary
        summary = BMFSearchSummary(
            total_found=len(organizations),
            criteria_summary=self._summarize_criteria(intent.criteria),
            top_matches_description=self._describe_top_matches(organizations)
        )

        # Create execution metadata
        execution_data = BMFExecutionData(
            execution_time_ms=(time.time() - start_time) * 1000,
            cache_hit=False,
            database_query_time_ms=db_time,
            results_truncated=results_truncated
        )

        # Create result
        result = BMFFilterResult(
            organizations=organizations,
            summary=summary,
            execution_metadata=execution_data
        )

        # Cache result
        if self.cache_enabled:
            self._cache[cache_key] = result

        return result

    def _make_cache_key(self, criteria: BMFFilterCriteria) -> str:
        """Create cache key from search criteria"""
        key_parts = [
            f"states:{','.join(criteria.states or [])}",
            f"revenue:{criteria.revenue_min}-{criteria.revenue_max}",
            f"ntee:{','.join(criteria.ntee_codes or [])}",
            f"assets:{criteria.asset_min}-{criteria.asset_max}",
            f"name:{criteria.organization_name or ''}",
            f"limit:{criteria.limit}"
        ]
        return "|".join(key_parts)

    async def _query_database(self, criteria: BMFFilterCriteria) -> List[BMFOrganization]:
        """Execute database query based on criteria"""

        # Build SQL query
        query = """
        SELECT ein, name, city, state, ntee_code, revenue_amount, asset_amount
        FROM bmf_organizations
        WHERE 1=1
        """
        params = []

        # Add filters
        if criteria.states:
            placeholders = ','.join('?' * len(criteria.states))
            query += f" AND state IN ({placeholders})"
            params.extend(criteria.states)

        if criteria.revenue_min is not None:
            query += " AND revenue_amount >= ?"
            params.append(criteria.revenue_min)

        if criteria.revenue_max is not None:
            query += " AND revenue_amount <= ?"
            params.append(criteria.revenue_max)

        if criteria.ntee_codes:
            placeholders = ','.join('?' * len(criteria.ntee_codes))
            query += f" AND ntee_code IN ({placeholders})"
            params.extend(criteria.ntee_codes)

        if criteria.asset_min is not None:
            query += " AND asset_amount >= ?"
            params.append(criteria.asset_min)

        if criteria.asset_max is not None:
            query += " AND asset_amount <= ?"
            params.append(criteria.asset_max)

        if criteria.organization_name:
            query += " AND name LIKE ?"
            params.append(f"%{criteria.organization_name}%")

        # Order and limit
        query += " ORDER BY revenue_amount DESC"
        if criteria.limit:
            query += " LIMIT ?"
            params.append(min(criteria.limit, self.max_results))

        # Execute query
        organizations = []
        async with aiosqlite.connect(self.database_path) as db:
            async with db.execute(query, params) as cursor:
                async for row in cursor:
                    # Determine match reasons
                    match_reasons = self._get_match_reasons(row, criteria)

                    org = BMFOrganization(
                        ein=row[0],
                        name=row[1],
                        city=row[2],
                        state=row[3],
                        ntee_code=row[4],
                        revenue=row[5],
                        assets=row[6],
                        match_reasons=match_reasons
                    )
                    organizations.append(org)

        return organizations

    def _get_match_reasons(self, row, criteria: BMFFilterCriteria) -> List[str]:
        """Explain why this organization matched the search criteria"""
        reasons = []

        if criteria.states and row[3] in criteria.states:
            reasons.append(f"Located in {row[3]}")

        if criteria.ntee_codes and row[4] in criteria.ntee_codes:
            reasons.append(f"NTEE code {row[4]} matches focus area")

        if criteria.revenue_min and row[5] and row[5] >= criteria.revenue_min:
            reasons.append(f"Revenue ${row[5]:,} meets minimum")

        if criteria.revenue_max and row[5] and row[5] <= criteria.revenue_max:
            reasons.append(f"Revenue ${row[5]:,} within maximum")

        if criteria.organization_name and criteria.organization_name.lower() in row[1].lower():
            reasons.append("Name matches search term")

        return reasons

    def _summarize_criteria(self, criteria: BMFFilterCriteria) -> str:
        """Create human-readable summary of search criteria"""
        parts = []

        if criteria.states:
            parts.append(f"in {', '.join(criteria.states)}")

        if criteria.ntee_codes:
            parts.append(f"with focus areas {', '.join(criteria.ntee_codes)}")

        if criteria.revenue_min or criteria.revenue_max:
            if criteria.revenue_min and criteria.revenue_max:
                parts.append(f"revenue ${criteria.revenue_min:,} - ${criteria.revenue_max:,}")
            elif criteria.revenue_min:
                parts.append(f"revenue over ${criteria.revenue_min:,}")
            else:
                parts.append(f"revenue under ${criteria.revenue_max:,}")

        if criteria.organization_name:
            parts.append(f"name containing '{criteria.organization_name}'")

        return f"Organizations {' '.join(parts)}" if parts else "All organizations"

    def _describe_top_matches(self, organizations: List[BMFOrganization]) -> str:
        """Describe the top matching organizations"""
        if not organizations:
            return "No matching organizations found"

        if len(organizations) == 1:
            org = organizations[0]
            return f"Found {org.name} in {org.state}"

        top_3 = organizations[:3]
        names = [org.name for org in top_3]

        if len(organizations) <= 3:
            return f"Found {', '.join(names)}"
        else:
            return f"Top matches include {', '.join(names)} and {len(organizations)-3} others"
```

### app/agent.py
```python
"""
Agent integration for BMF Filter Tool
Handles LLM interaction and tool orchestration
"""

import asyncio
from baml_py import b
from app.bmf_filter import BMFFilterTool
from app.generated.baml_types import BMFFilterIntent, BMFFilterResult

class BMFFilterAgent:
    """
    12-Factor Agent that uses BMF Filter Tool

    This demonstrates Factor 4: Tools are structured outputs
    - LLM generates BMFFilterIntent
    - Tool executes deterministic filtering
    - Agent handles the orchestration
    """

    def __init__(self):
        self.tool = BMFFilterTool()

    async def process_natural_language_request(self, user_request: str) -> BMFFilterResult:
        """
        Convert natural language request to tool execution

        Example: "Find education nonprofits in Virginia with revenue over $500K"
        -> BMFFilterIntent with appropriate criteria
        -> Execute tool
        -> Return structured results
        """

        # Use LLM to convert natural language to structured intent
        intent = await b.ExtractBMFFilterIntent(user_request)

        # Execute the tool with structured intent
        result = await self.tool.execute(intent)

        return result

    async def validate_and_execute(self, intent: BMFFilterIntent) -> BMFFilterResult:
        """
        Validate intent and execute tool
        Useful when you already have structured input
        """

        # Validate criteria
        if not self._validate_criteria(intent.criteria):
            raise ValueError("Invalid search criteria")

        # Execute tool
        return await self.tool.execute(intent)

    def _validate_criteria(self, criteria) -> bool:
        """Basic validation of search criteria"""

        # Check state codes are valid
        if criteria.states:
            valid_states = {"AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
                          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
                          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
                          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"}

            invalid_states = set(criteria.states) - valid_states
            if invalid_states:
                return False

        # Check revenue range makes sense
        if criteria.revenue_min and criteria.revenue_max:
            if criteria.revenue_min > criteria.revenue_max:
                return False

        # Check limit is reasonable
        if criteria.limit and criteria.limit > 10000:
            return False

        return True

# BAML function definition (would be in baml_src/)
"""
function ExtractBMFFilterIntent(user_request: string) -> BMFFilterIntent {
    client OpenAI
    prompt #"
        The user wants to search for nonprofit organizations.
        Convert their request into a structured search intent.

        User request: {{ user_request }}

        Extract the search criteria and create a BMFFilterIntent.
        If they mention:
        - States/locations -> states array
        - Revenue/budget/income -> revenue_min/max
        - Focus areas like education, health -> ntee_codes (P20=education, B25=health)
        - Size/assets -> asset_min/max
        - Organization names -> organization_name

        Also include what_youre_looking_for as a clear description.
    "#
}
"""
```

### app/server.py
```python
"""
HTTP Server for BMF Filter Tool
Factor 7: Port binding - export services via port binding
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from app.bmf_filter import BMFFilterTool
from app.agent import BMFFilterAgent
from app.generated.baml_types import BMFFilterIntent, BMFFilterResult

# Create FastAPI app
app = FastAPI(
    title="BMF Filter Tool",
    description="12-Factor tool for filtering IRS nonprofit data",
    version="1.0.0"
)

# Initialize tool and agent
tool = BMFFilterTool()
agent = BMFFilterAgent()

@app.post("/filter", response_model=BMFFilterResult)
async def filter_bmf_data(intent: BMFFilterIntent):
    """
    Execute BMF filtering with structured intent

    This endpoint accepts structured input and returns structured output,
    following Factor 4: Tools are structured outputs
    """
    try:
        result = await tool.execute(intent)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=BMFFilterResult)
async def search_natural_language(request: dict):
    """
    Process natural language search request

    Accepts: {"query": "Find education nonprofits in Virginia"}
    Returns: Structured BMFFilterResult
    """
    try:
        user_query = request.get("query", "")
        if not user_query:
            raise HTTPException(status_code=400, detail="Query is required")

        result = await agent.process_natural_language_request(user_query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "tool": "bmf-filter",
        "version": "1.0.0"
    }

@app.get("/capabilities")
async def get_capabilities():
    """Return tool capabilities"""
    return {
        "tool_name": "bmf-filter",
        "capabilities": ["bmf_filtering", "nonprofit_discovery", "data_filtering"],
        "input_type": "BMFFilterIntent",
        "output_type": "BMFFilterResult",
        "max_results": tool.max_results
    }

if __name__ == "__main__":
    # Factor 7: Port binding
    port = int(os.getenv("BMF_FILTER_PORT", "8001"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
```

### app/main.py
```python
"""
Main entry point for BMF Filter Tool
Demonstrates different ways to use the tool
"""

import asyncio
import os
from app.bmf_filter import BMFFilterTool
from app.agent import BMFFilterAgent
from app.generated.baml_types import BMFFilterIntent, BMFFilterCriteria

async def example_direct_tool_usage():
    """Example: Using the tool directly with structured input"""

    print("=== Direct Tool Usage ===")

    tool = BMFFilterTool()

    # Create structured intent
    intent = BMFFilterIntent(
        criteria=BMFFilterCriteria(
            states=["VA", "MD"],
            ntee_codes=["P20"],  # Education
            revenue_min=500000,
            limit=5
        ),
        what_youre_looking_for="Education nonprofits in Virginia/Maryland with significant funding"
    )

    # Execute tool
    result = await tool.execute(intent)

    print(f"Found: {result.summary.criteria_summary}")
    print(f"Results: {result.summary.total_found} organizations")
    print(f"Time: {result.execution_metadata.execution_time_ms:.1f}ms")
    print()

    for org in result.organizations[:3]:
        print(f"  {org.name} ({org.state})")
        print(f"  EIN: {org.ein}, Revenue: ${org.revenue:,}" if org.revenue else f"  EIN: {org.ein}")
        print(f"  Match reasons: {', '.join(org.match_reasons)}")
        print()

async def example_agent_usage():
    """Example: Using the agent with natural language"""

    print("=== Agent Usage (Natural Language) ===")

    agent = BMFFilterAgent()

    # Natural language request
    user_request = "Find health organizations in Washington DC with revenue between $1M and $5M"

    # Agent converts to structured intent and executes
    result = await agent.process_natural_language_request(user_request)

    print(f"User asked: {user_request}")
    print(f"Found: {result.summary.top_matches_description}")
    print(f"Execution time: {result.execution_metadata.execution_time_ms:.1f}ms")

async def example_workflow_integration():
    """Example: How this tool fits into larger workflows"""

    print("=== Workflow Integration Example ===")

    tool = BMFFilterTool()

    # Step 1: BMF Filter finds organizations
    filter_intent = BMFFilterIntent(
        criteria=BMFFilterCriteria(
            states=["VA"],
            revenue_min=1000000,
            limit=3
        ),
        what_youre_looking_for="Large Virginia nonprofits for partnership analysis"
    )

    bmf_results = await tool.execute(filter_intent)
    print(f"Step 1 - BMF Filter: Found {bmf_results.summary.total_found} organizations")

    # Step 2: Results would flow to next tool in workflow
    for org in bmf_results.organizations:
        # This would be input to next tool (AI Analysis, Network Analysis, etc.)
        next_tool_input = {
            "ein": org.ein,
            "name": org.name,
            "revenue": org.revenue,
            "basic_data": True,
            "analysis_type": "partnership_potential"
        }
        print(f"  → Queuing {org.name} for next analysis tool")

    print("Results prepared for next tool in workflow")

async def main():
    """Run all examples"""

    # Check environment
    if not os.getenv("BMF_DATABASE_PATH"):
        print("Warning: BMF_DATABASE_PATH not set, using default")

    await example_direct_tool_usage()
    print("\n" + "="*60 + "\n")

    await example_agent_usage()
    print("\n" + "="*60 + "\n")

    await example_workflow_integration()

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Learning Points

### 1. 12-Factor Structure
- **Configuration**: All settings from environment (.env)
- **BAML Schemas**: Structured input/output definitions
- **Tool Logic**: Deterministic code that executes intents
- **Agent Layer**: Handles LLM interaction and orchestration

### 2. Factor 4 Implementation
- **Structured Input**: `BMFFilterIntent` with clear criteria
- **Deterministic Code**: Database filtering logic
- **Structured Output**: `BMFFilterResult` with organizations and metadata

### 3. Clear Separation
- **BAML**: Defines the interface
- **Tool**: Implements the filtering logic
- **Agent**: Handles LLM interaction
- **Server**: Provides HTTP endpoints

### 4. Workflow Ready
- Tool produces structured output that flows cleanly to next tools
- Clear input/output contracts make chaining predictable
- Execution metadata helps with debugging and optimization

## Running the Tool

```bash
# Install dependencies
pip install -e .

# Set environment
export BMF_DATABASE_PATH=data/nonprofit_intelligence.db
export BMF_FILTER_PORT=8001

# Run examples
python app/main.py

# Run as service
python app/server.py

# Test HTTP endpoint
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Find education nonprofits in Virginia"}'
```

This structure follows the official 12-factor agents conventions while being beginner-friendly. The clear separation between BAML schemas, tool logic, and agent orchestration makes it easy to understand how the pieces fit together!