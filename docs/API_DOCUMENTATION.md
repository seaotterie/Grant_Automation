# Catalynx API Documentation

**Version**: 2.0.0
**Base URL**: `http://localhost:8000`
**Date**: 2025-09-30

---

## Overview

The Catalynx API provides unified access to 22 12-factor compliant grant intelligence tools. All tools follow consistent patterns for execution, error handling, and structured outputs.

### Key Features
- **Unified Interface**: Single API for all tools
- **Structured Outputs**: Type-safe responses via BAML validation
- **Cost Transparency**: Every response includes execution cost
- **12-Factor Compliance**: Stateless, autonomous tool execution

---

## Authentication

Currently no authentication required (development mode).

Production will use:
- API Keys via `Authorization: Bearer <token>` header
- Rate limiting: 60 requests/minute per IP

---

## Tool Execution API

### List All Tools

```http
GET /api/v1/tools
```

**Query Parameters**:
- `category` (optional): Filter by category (e.g., `parsing`, `scoring`, `analysis`)
- `status` (optional): Filter by status (e.g., `operational`, `deprecated`)

**Response**:
```json
{
  "tools": [
    {
      "name": "Multi-Dimensional Scorer Tool",
      "version": "1.0.0",
      "status": "operational",
      "category": "scoring"
    }
  ],
  "total_count": 22,
  "operational_count": 22
}
```

---

### Get Tool Metadata

```http
GET /api/v1/tools/{tool_name}
```

**Path Parameters**:
- `tool_name`: Tool identifier (e.g., `multi-dimensional-scorer-tool`)

**Response**:
```json
{
  "name": "Multi-Dimensional Scorer Tool",
  "version": "1.0.0",
  "status": "operational",
  "category": "scoring",
  "description": "Multi-dimensional opportunity scoring with confidence calculation",
  "single_responsibility": "Scoring only - no data fetching, no reporting",
  "cost_per_operation": 0.00,
  "inputs": {
    "type": "ScoringInput",
    "required_fields": ["opportunity_data", "organization_profile", "workflow_stage"]
  },
  "outputs": {
    "type": "MultiDimensionalScore",
    "fields": ["overall_score", "confidence", "dimensional_scores"]
  }
}
```

---

### Execute Tool

```http
POST /api/v1/tools/{tool_name}/execute
```

**Path Parameters**:
- `tool_name`: Tool identifier

**Request Body**:
```json
{
  "inputs": {
    // Tool-specific input parameters (see tool metadata)
  },
  "config": {
    // Optional configuration overrides
  }
}
```

**Response**:
```json
{
  "success": true,
  "tool_name": "Multi-Dimensional Scorer Tool",
  "tool_version": "1.0.0",
  "execution_time_ms": 0.52,
  "cost": 0.00,
  "data": {
    // Tool-specific structured output
  },
  "error": null
}
```

**Error Response** (400/404/500):
```json
{
  "success": false,
  "tool_name": "...",
  "tool_version": "...",
  "execution_time_ms": 0.10,
  "cost": 0.00,
  "data": null,
  "error": "Error description"
}
```

---

## Tool Categories

### Data Acquisition (9 tools)
- `xml-990-parser-tool` - Parse regular nonprofit 990 filings
- `xml-990pf-parser-tool` - Parse private foundation 990-PF filings
- `xml-990ez-parser-tool` - Parse small nonprofit 990-EZ filings
- `bmf-filter-tool` - IRS Business Master File filtering
- `form990-analysis-tool` - Financial metrics extraction
- `form990-propublica-tool` - ProPublica API enrichment
- `foundation-grant-intelligence-tool` - Grant-making analysis
- `propublica-api-enrichment-tool` - Additional data enrichment
- `xml-schedule-parser-tool` - Schedule extraction and parsing

### Intelligence & Scoring (5 tools)
- `financial-intelligence-tool` - Comprehensive financial analysis
- `risk-intelligence-tool` - Multi-dimensional risk assessment
- `network-intelligence-tool` - Board network and relationships
- `schedule-i-grant-analyzer-tool` - Foundation grant patterns
- `multi-dimensional-scorer-tool` - 5-stage dimensional scoring

### Data Quality (2 tools)
- `data-validator-tool` - Quality and completeness validation
- `ein-validator-tool` - EIN format validation and lookup

### Discovery (1 tool)
- `bmf-discovery-tool` - Multi-criteria nonprofit discovery

### Output & Reporting (3 tools)
- `data-export-tool` - Multi-format export (JSON, CSV, Excel, PDF)
- `grant-package-generator-tool` - Application package assembly
- `report-generator-tool` - Professional report templates

### Analysis (2 tools)
- `historical-funding-analyzer-tool` - USASpending.gov pattern analysis
- `opportunity-screening-tool` - Mass screening (fast/thorough modes)
- `deep-intelligence-tool` - 4-depth comprehensive analysis

---

## Example: Multi-Dimensional Scorer

### Request
```http
POST /api/v1/tools/multi-dimensional-scorer-tool/execute
Content-Type: application/json

{
  "inputs": {
    "scoring_input": {
      "opportunity_data": {
        "opportunity_id": "OPP-2025-001",
        "title": "Community Health Initiative Grant",
        "award_amount": 50000,
        "location": "Virginia"
      },
      "organization_profile": {
        "ein": "81-2827604",
        "name": "Heroes Bridge",
        "revenue": 504030
      },
      "workflow_stage": "discover",
      "track_type": "nonprofit"
    }
  }
}
```

### Response
```json
{
  "success": true,
  "tool_name": "Multi-Dimensional Scorer Tool",
  "tool_version": "1.0.0",
  "execution_time_ms": 0.45,
  "cost": 0.00,
  "data": {
    "overall_score": 0.840,
    "confidence": 0.753,
    "dimensional_scores": [
      {
        "dimension_name": "mission_alignment",
        "raw_score": 0.583,
        "weight": 0.30,
        "weighted_score": 0.175
      },
      {
        "dimension_name": "geographic_fit",
        "raw_score": 1.000,
        "weight": 0.25,
        "weighted_score": 0.250
      }
    ],
    "stage": "discover",
    "track_type": "nonprofit",
    "proceed_recommendation": true,
    "key_strengths": [
      "Geographic Fit: 100%",
      "Financial Match: 100%"
    ]
  }
}
```

---

## Example: Historical Funding Analyzer

### Request
```http
POST /api/v1/tools/historical-funding-analyzer-tool/execute
Content-Type: application/json

{
  "inputs": {
    "analysis_input": {
      "organization_ein": "81-2827604",
      "historical_data": [
        {
          "amount": 150000,
          "date": "2024-03-15",
          "state": "VA",
          "agency": "HHS"
        }
      ],
      "analysis_years": 5
    }
  }
}
```

### Response
```json
{
  "success": true,
  "tool_name": "Historical Funding Analyzer Tool",
  "tool_version": "1.0.0",
  "execution_time_ms": 4.57,
  "cost": 0.00,
  "data": {
    "organization_ein": "81-2827604",
    "total_awards": 12,
    "total_funding": 1220000.00,
    "average_award_size": 101666.67,
    "funding_patterns": [...],
    "geographic_distribution": [...],
    "temporal_trends": [...],
    "key_insights": [
      "Received 12 awards totaling $1,220,000.00",
      "VA is top funding state with $850,000.00 (69.7%)",
      "Funding trend is increasing (+21.4% year-over-year)"
    ]
  }
}
```

---

## Example: Report Generator

### Request
```http
POST /api/v1/tools/report-generator-tool/execute
Content-Type: application/json

{
  "inputs": {
    "report_input": {
      "template_type": "comprehensive",
      "opportunity_data": {
        "title": "Community Health Grant",
        "award_amount": 50000
      },
      "organization_data": {
        "name": "Heroes Bridge",
        "ein": "81-2827604"
      },
      "scoring_results": [...],
      "output_format": "html"
    }
  }
}
```

### Response
```json
{
  "success": true,
  "tool_name": "Report Generator Tool",
  "tool_version": "1.0.0",
  "execution_time_ms": 1520.34,
  "cost": 0.00,
  "data": {
    "report_id": "10fad307",
    "file_path": "data/reports/report_comprehensive_20250930_204519_10fad307.html",
    "format": "html",
    "sections_generated": 20,
    "file_size_bytes": 16004,
    "metadata": {
      "completeness_score": 1.0,
      "data_quality_score": 0.8
    }
  }
}
```

---

## Health & Status Endpoints

### Tool API Health Check
```http
GET /api/v1/tools/health
```

**Response**:
```json
{
  "status": "healthy",
  "total_tools": 22,
  "operational_tools": 22,
  "deprecated_tools": 0,
  "registry_initialized": true
}
```

### List Categories
```http
GET /api/v1/tools/categories/list
```

**Response**:
```json
{
  "categories": [
    "analysis",
    "discovery",
    "output",
    "parsing",
    "reporting",
    "scoring",
    "validation"
  ],
  "count": 7
}
```

---

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error description",
  "status_code": 400/404/500
}
```

### Common Error Codes
- **400 Bad Request**: Invalid input parameters or tool not operational
- **404 Not Found**: Tool does not exist
- **500 Internal Server Error**: Tool execution failed

---

## Rate Limiting

- **Development**: 60 requests/minute per IP
- **Production**: TBD based on usage patterns

Headers returned:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1696089600
```

---

## Performance Expectations

| Tool Category | Typical Duration | Cost |
|--------------|------------------|------|
| Parsers (XML 990) | 100-500ms | $0.00 |
| Intelligence Tools | 500-1000ms | $0.02-$0.04 |
| Scorers | <1ms | $0.00 |
| Reports | 1-2s | $0.00 |
| Historical Analysis | 4-5ms | $0.00 |

---

## Best Practices

1. **Check tool metadata first**: Understand required inputs before execution
2. **Handle errors gracefully**: All tools return structured error responses
3. **Monitor costs**: Sum `cost` field across requests
4. **Batch operations**: Use workflow API for multi-tool pipelines
5. **Cache results**: Tools are stateless, results can be cached

---

## OpenAPI Specification

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

---

## Support

For issues or questions:
- GitHub Issues: `https://github.com/anthropics/catalynx/issues`
- Documentation: `docs/TWO_TOOL_ARCHITECTURE.md`
- Migration Guide: `docs/MIGRATION_HISTORY.md`

---

**Last Updated**: 2025-09-30
**API Version**: 2.0.0 (12-Factor Compliant)
