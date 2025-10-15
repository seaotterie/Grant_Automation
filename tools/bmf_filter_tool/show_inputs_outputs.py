#!/usr/bin/env python3
"""
BMF Filter Tool - Input/Output Examples
======================================

Demonstrates the structured input/output patterns for the 12-factor BMF Filter Tool.
Shows exactly what data goes in and what comes out.
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Set up test environment
os.environ['BMF_INPUT_PATH'] = 'test_data/sample_bmf.csv'
os.environ['BMF_FILTER_CONFIG_PATH'] = 'test_data/sample_config.json'
os.environ['BMF_CACHE_ENABLED'] = 'false'

from app.bmf_filter import BMFFilterTool
from app.generated import (
    BMFFilterIntent, BMFFilterCriteria, BMFSearchPriority,
    BMFSortOption, BMFFoundationType
)

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def print_json(obj, title):
    """Print an object as formatted JSON"""
    print(f"\n{title}:")
    print("-" * 40)
    if hasattr(obj, 'model_dump'):
        # Pydantic model
        data = obj.model_dump()
    elif hasattr(obj, '__dict__'):
        # Regular object
        data = obj.__dict__
    else:
        # Already a dict
        data = obj

    print(json.dumps(data, indent=2, default=str))

async def example_1_basic_filtering():
    """Example 1: Basic filtering by state and NTEE code"""
    print_section("EXAMPLE 1: Basic Filtering (State + NTEE Code)")

    # INPUT: Structured Intent
    input_intent = BMFFilterIntent(
        criteria=BMFFilterCriteria(
            states=["VA"],
            ntee_codes=["P20"],  # Education
            limit=3
        ),
        what_youre_looking_for="Education nonprofits in Virginia",
        priority=BMFSearchPriority.standard
    )

    print_json(input_intent, "INPUT (BMFFilterIntent)")

    # EXECUTE TOOL
    tool = BMFFilterTool()
    result = await tool.execute(input_intent)

    # OUTPUT: Structured Result
    print_json(result, "OUTPUT (BMFFilterResult)")

    # Show key output components
    print(f"\nKEY OUTPUT COMPONENTS:")
    print(f"Organizations Found: {len(result.organizations)}")
    print(f"Execution Time: {result.execution_metadata.execution_time_ms:.1f}ms")
    print(f"Total Records Processed: {result.summary.total_in_database}")
    print(f"Cache Hit: {result.execution_metadata.cache_hit}")

async def example_2_complex_filtering():
    """Example 2: Complex multi-criteria filtering"""
    print_section("EXAMPLE 2: Complex Multi-Criteria Filtering")

    # INPUT: Complex criteria
    input_intent = BMFFilterIntent(
        criteria=BMFFilterCriteria(
            states=["VA", "MD", "DC"],
            ntee_codes=["P20", "B25"],  # Education and Health
            revenue_min=500000,
            revenue_max=2000000,
            organization_name="center",
            sort_by=BMFSortOption.revenue_desc,
            limit=5
        ),
        what_youre_looking_for="Medium-sized education and health centers in DC metro area",
        priority=BMFSearchPriority.thorough
    )

    print_json(input_intent, "INPUT (Complex Criteria)")

    # EXECUTE
    tool = BMFFilterTool()
    result = await tool.execute(input_intent)

    # Show simplified output focusing on key data
    output_summary = {
        "organizations_found": len(result.organizations),
        "sample_organizations": [
            {
                "name": org.name,
                "state": org.state,
                "ntee_code": org.ntee_code,
                "revenue": org.revenue,
                "match_reasons": org.match_reasons
            }
            for org in result.organizations[:2]  # Show first 2
        ],
        "execution_metadata": {
            "execution_time_ms": result.execution_metadata.execution_time_ms,
            "query_complexity": result.execution_metadata.query_complexity,
            "rows_processed": result.execution_metadata.database_rows_scanned,
            "cache_hit": result.execution_metadata.cache_hit
        },
        "summary": {
            "criteria_summary": result.summary.criteria_summary,
            "geographic_distribution": result.summary.geographic_distribution,
            "financial_summary": result.summary.financial_summary
        }
    }

    print_json(output_summary, "OUTPUT (Key Components)")

async def example_3_http_api_format():
    """Example 3: HTTP API request/response format"""
    print_section("EXAMPLE 3: HTTP API Request/Response Format")

    # Show what the HTTP API expects and returns
    http_request = {
        "intent": "bmf_filter",
        "criteria": {
            "states": ["VA"],
            "ntee_codes": ["B25"],  # Health
            "revenue_min": 750000,
            "limit": 2,
            "sort_by": "revenue_desc"
        },
        "what_youre_looking_for": "Large health organizations in Virginia",
        "priority": "standard"
    }

    print_json(http_request, "HTTP POST /filter Request Body")

    # Execute to get response
    tool = BMFFilterTool()
    intent = BMFFilterIntent(**http_request)
    result = await tool.execute(intent)

    # Format as HTTP response
    http_response = {
        "intent": result.intent,
        "organizations": [
            {
                "ein": org.ein,
                "name": org.name,
                "state": org.state,
                "city": org.city,
                "ntee_code": org.ntee_code,
                "revenue": org.revenue,
                "assets": org.assets,
                "match_reasons": org.match_reasons,
                "match_score": org.match_score
            }
            for org in result.organizations
        ],
        "summary": {
            "total_found": result.summary.total_found,
            "criteria_summary": result.summary.criteria_summary,
            "top_matches_description": result.summary.top_matches_description
        },
        "execution_metadata": {
            "execution_time_ms": result.execution_metadata.execution_time_ms,
            "cache_hit": result.execution_metadata.cache_hit,
            "query_complexity": result.execution_metadata.query_complexity
        }
    }

    print_json(http_response, "HTTP Response Body")

async def example_4_workflow_integration():
    """Example 4: How output flows to next tool in workflow"""
    print_section("EXAMPLE 4: Workflow Integration Pattern")

    # Step 1: BMF Filter Tool Output
    tool = BMFFilterTool()
    bmf_intent = BMFFilterIntent(
        criteria=BMFFilterCriteria(
            states=["VA"],
            revenue_min=1000000,
            limit=3
        ),
        what_youre_looking_for="Large Virginia nonprofits for partnership analysis"
    )

    bmf_result = await tool.execute(bmf_intent)

    print_json(bmf_intent, "STEP 1 INPUT (BMF Filter)")

    # Step 2: Transform output for next tool
    next_tool_inputs = []
    for org in bmf_result.organizations:
        next_input = {
            "tool": "ai-analysis-tool",
            "intent": "analyze_partnership_potential",
            "data": {
                "ein": org.ein,
                "name": org.name,
                "state": org.state,
                "revenue": org.revenue,
                "ntee_code": org.ntee_code,
                "source_tool": "bmf-filter",
                "match_score": org.match_score,
                "analysis_priority": "high" if org.revenue and org.revenue > 1500000 else "medium"
            },
            "context": {
                "workflow_id": "partnership-analysis-001",
                "previous_step": "bmf-filter",
                "criteria_used": bmf_result.summary.criteria_summary
            }
        }
        next_tool_inputs.append(next_input)

    print_json(next_tool_inputs, "STEP 2 OUTPUT (Prepared for AI Analysis Tool)")

    # Show workflow metadata
    workflow_metadata = {
        "workflow": "Partnership Analysis Pipeline",
        "step_1": {
            "tool": "bmf-filter",
            "results": len(bmf_result.organizations),
            "execution_time_ms": bmf_result.execution_metadata.execution_time_ms
        },
        "step_2": {
            "tool": "ai-analysis-tool",
            "inputs_prepared": len(next_tool_inputs),
            "ready_for_processing": True
        },
        "data_flow": "BMFFilterResult → AIAnalysisInput[]"
    }

    print_json(workflow_metadata, "WORKFLOW METADATA")

def show_csv_input_format():
    """Show the CSV input format the tool expects"""
    print_section("CSV INPUT DATA FORMAT")

    print("CSV Expected CSV Structure (sample_bmf.csv):")
    print("-" * 40)

    # Read and show sample CSV
    csv_path = 'test_data/sample_bmf.csv'
    if Path(csv_path).exists():
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:6]):  # Show header + 5 rows
                print(f"{i+1:2}: {line.strip()}")
            if len(lines) > 6:
                print(f"... ({len(lines)-6} more rows)")

    print("\nCONFIG Configuration File Format (sample_config.json):")
    print("-" * 40)

    config_path = 'test_data/sample_config.json'
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            print(f.read())

def show_environment_config():
    """Show environment configuration format"""
    print_section("ENVIRONMENT CONFIGURATION")

    env_config = {
        "BMF_INPUT_PATH": "data/input/eo_va.csv",
        "BMF_FILTER_CONFIG_PATH": "data/input/filter_config.json",
        "BMF_CACHE_ENABLED": "true",
        "BMF_MAX_RESULTS": "1000",
        "BMF_FILTER_PORT": "8001",
        "BMF_LOG_LEVEL": "INFO"
    }

    print_json(env_config, "Environment Variables (.env.tool)")

async def main():
    """Run all input/output examples"""
    print("BMF Filter Tool - Input/Output Demonstration")
    print("Shows structured data flow for 12-factor agents")

    try:
        # Show configuration formats
        show_csv_input_format()
        show_environment_config()

        # Show execution examples
        await example_1_basic_filtering()
        await example_2_complex_filtering()
        await example_3_http_api_format()
        await example_4_workflow_integration()

        print_section("SUMMARY")
        print("KEY PATTERNS DEMONSTRATED:")
        print("  • Structured Input: BMFFilterIntent with typed criteria")
        print("  • Deterministic Processing: Pure CSV filtering logic")
        print("  • Structured Output: BMFFilterResult with metadata")
        print("  • HTTP API Ready: JSON request/response format")
        print("  • Workflow Integration: Output flows to next tools")
        print("  • Performance Tracking: Execution metadata included")

        print("\nFactor 4 Compliance: 'Tools are structured outputs that trigger deterministic code'")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())