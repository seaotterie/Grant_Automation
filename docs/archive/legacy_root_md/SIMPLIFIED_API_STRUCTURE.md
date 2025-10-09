# Simplified API Structure - Target Architecture

**Date**: 2025-10-02
**Version**: 2.0
**Status**: Target Design
**Total Endpoints**: 35 (down from 162)

---

## Overview

This document defines the simplified, modern API structure for the Catalynx platform. The design follows RESTful principles, eliminates duplication, and provides a clean, predictable interface.

### Design Principles
1. **RESTful Design** - Standard HTTP methods, resource-oriented URLs
2. **Tool-Based Execution** - All AI/analysis via unified tool API
3. **Workflow Orchestration** - Multi-step processes via workflow API
4. **Minimal Duplication** - One canonical endpoint per function
5. **Version Control** - V2 APIs for breaking changes

---

## API Structure

### 1. Profile API - `/api/v2/profiles`
**Purpose**: Manage nonprofit profiles (YOUR organization)

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| POST | `/api/v2/profiles` | Create new profile | `{name, ein, ...}` | Profile object |
| GET | `/api/v2/profiles` | List all profiles | Query params | Profile array |
| GET | `/api/v2/profiles/{id}` | Get profile details | - | Full profile |
| PUT | `/api/v2/profiles/{id}` | Update profile | Updated fields | Profile object |
| DELETE | `/api/v2/profiles/{id}` | Delete profile | - | Success status |
| POST | `/api/v2/profiles/build` | Build comprehensive profile | `{ein, options}` | Workflow result |
| GET | `/api/v2/profiles/{id}/analytics` | Get profile analytics | - | Analytics data |
| POST | `/api/v2/profiles/{id}/export` | Export profile data | `{format, fields}` | Export result |
| GET | `/api/v2/profiles/{id}/quality` | Quality assessment | - | Quality score |
| GET | `/api/v2/profiles/health` | API health check | - | Health status |

#### Key Features
- **Orchestrated Building**: `/build` endpoint uses ProfileEnhancementOrchestrator
- **Quality Scoring**: Built-in quality assessment via ProfileQualityScorer
- **Data Export**: Multi-format export (JSON, CSV, Excel, PDF)
- **Analytics**: Consolidated analytics instead of multiple metrics endpoints

#### Example: Build Profile
```http
POST /api/v2/profiles/build
Content-Type: application/json

{
  "ein": "812827604",
  "enable_tool25": true,   # Web intelligence
  "enable_tool2": false,   # Deep AI analysis ($0.75)
  "quality_threshold": 0.70
}
```

Response:
```json
{
  "profile": {
    "id": "uuid",
    "name": "Heroes Bridge",
    "ein": "812827604",
    ...
  },
  "workflow_result": {
    "success": true,
    "steps_completed": ["bmf", "990", "tool25"],
    "cost": 0.10,
    "duration_ms": 15000
  },
  "quality_score": {
    "overall": 0.82,
    "rating": "GOOD",
    "components": {...}
  }
}
```

---

### 2. Tool Execution API - `/api/v1/tools`
**Purpose**: Execute any of the 23 operational tools

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| GET | `/api/v1/tools` | List all tools | `?category=&status=` | Tool list |
| GET | `/api/v1/tools/{tool_name}` | Get tool metadata | - | Tool metadata |
| POST | `/api/v1/tools/{tool_name}/execute` | Execute tool | Tool-specific inputs | Execution result |
| GET | `/api/v1/tools/categories/list` | List tool categories | - | Category list |
| GET | `/api/v1/tools/health` | API health check | - | Health status |

#### Available Tools (23)
**Data Collection (9)**: xml-990-parser, xml-990pf-parser, xml-990ez-parser, bmf-filter-tool, form990-analysis, form990-propublica, foundation-grant-intelligence, propublica-api-enrichment, xml-schedule-parser

**AI Intelligence (2)**: opportunity-screening-tool, deep-intelligence-tool

**Analysis (4)**: financial-intelligence-tool, risk-intelligence-tool, network-intelligence-tool, schedule-i-grant-analyzer

**Quality (3)**: data-validator-tool, ein-validator-tool, data-export-tool

**Output (3)**: grant-package-generator-tool, multi-dimensional-scorer-tool, report-generator-tool

**Discovery (2)**: historical-funding-analyzer-tool, web-intelligence-tool

#### Example: Execute Screening Tool
```http
POST /api/v1/tools/opportunity-screening-tool/execute
Content-Type: application/json

{
  "inputs": {
    "opportunities": [...],
    "profile": {...},
    "mode": "thorough"
  },
  "config": {
    "threshold": 0.55,
    "max_recommendations": 15
  }
}
```

Response:
```json
{
  "success": true,
  "tool_name": "opportunity-screening-tool",
  "tool_version": "1.0.0",
  "execution_time_ms": 5234,
  "cost": 0.02,
  "data": {
    "screened": 200,
    "passed_threshold": 47,
    "recommended": 15,
    "scores": [...]
  }
}
```

---

### 3. Workflow API - `/api/v1/workflows`
**Purpose**: Orchestrate multi-tool workflows

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| POST | `/api/v1/workflows/execute` | Execute workflow | `{workflow, context}` | Execution ID |
| GET | `/api/v1/workflows/status/{execution_id}` | Get workflow status | - | Status object |
| GET | `/api/v1/workflows/results/{execution_id}` | Get workflow results | - | Results object |
| GET | `/api/v1/workflows/list` | List available workflows | - | Workflow list |
| GET | `/api/v1/workflows/executions` | List workflow executions | Query params | Execution list |
| POST | `/api/v1/workflows/screen-opportunities` | Convenience: screening | Screening params | Execution ID |
| POST | `/api/v1/workflows/deep-intelligence` | Convenience: deep analysis | Analysis params | Execution ID |

#### Available Workflows
1. **opportunity_screening.yaml** - Two-stage screening funnel
2. **deep_intelligence.yaml** - Comprehensive analysis workflow
3. **profile_enhancement.yaml** - Multi-step profile building

#### Example: Execute Workflow
```http
POST /api/v1/workflows/execute
Content-Type: application/json

{
  "workflow_name": "opportunity_screening",
  "context": {
    "profile_id": "uuid",
    "opportunities": [...],
    "config": {
      "fast_mode_threshold": 0.50,
      "thorough_mode_threshold": 0.60
    }
  }
}
```

Response:
```json
{
  "execution_id": "exec-uuid",
  "workflow_name": "opportunity_screening",
  "status": "running",
  "started_at": "2025-10-02T10:00:00Z",
  "estimated_completion": "2025-10-02T10:15:00Z"
}
```

---

### 4. Discovery API - `/api/v2/discovery`
**Purpose**: Discover funding opportunities and potential matches

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| POST | `/api/v2/discovery/execute` | Execute discovery workflow | `{track, criteria}` | Discovery results |
| GET | `/api/v2/discovery/bmf` | BMF-specific discovery | Query params | BMF results |
| POST | `/api/v2/discovery/search` | Search across sources | Search query | Search results |
| GET | `/api/v2/discovery/sessions` | List discovery sessions | Query params | Session list |
| GET | `/api/v2/discovery/sessions/{id}` | Get session details | - | Session object |
| POST | `/api/v2/discovery/analyze` | Analyze discovery results | Results data | Analysis |

#### Discovery Tracks
- **nonprofit**: 990-PF foundations (funding opportunities)
- **federal**: Grants.gov and USASpending (government opportunities)
- **state**: State-level grant programs
- **commercial**: Corporate foundations and CSR programs
- **bmf**: IRS Business Master File (nonprofit discovery)

#### Example: Execute Discovery
```http
POST /api/v2/discovery/execute
Content-Type: application/json

{
  "track": "nonprofit",
  "criteria": {
    "ntee_codes": ["P20", "B25"],
    "states": ["VA", "MD", "DC"],
    "min_assets": 1000000,
    "grant_capacity": "Major"
  },
  "profile_id": "uuid"
}
```

Response:
```json
{
  "session_id": "disc-uuid",
  "track": "nonprofit",
  "results": {
    "total_found": 472,
    "filtered": 187,
    "high_quality": 45,
    "opportunities": [...]
  },
  "execution_time_ms": 850
}
```

---

### 5. Funnel API - `/api/v2/funnel`
**Purpose**: Manage opportunity funnel and stage transitions

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| POST | `/api/v2/funnel/{profile_id}/transition` | Transition opportunity stage | `{opp_ids, action}` | Result |
| GET | `/api/v2/funnel/{profile_id}/opportunities` | List by stage | `?stage=` | Opportunity list |
| GET | `/api/v2/funnel/{profile_id}/metrics` | Funnel metrics | - | Metrics object |
| GET | `/api/v2/funnel/{profile_id}/recommendations` | Smart suggestions | - | Recommendations |
| GET | `/api/v2/funnel/stages` | Get stage definitions | - | Stage list |

#### Funnel Stages
1. **DISCOVER** - Initial discovery
2. **PLAN** - Planning and preparation
3. **ANALYZE** - Detailed analysis
4. **EXAMINE** - Due diligence
5. **APPROACH** - Decision and approach strategy

#### Transition Actions
- `promote` - Move to next stage
- `demote` - Move to previous stage
- `skip_to` - Jump to specific stage
- `archive` - Remove from active funnel
- `restore` - Restore archived opportunity

#### Example: Bulk Transition
```http
POST /api/v2/funnel/{profile_id}/transition
Content-Type: application/json

{
  "opportunity_ids": ["opp1", "opp2", "opp3"],
  "action": "promote",
  "target_stage": "ANALYZE",  # Optional for skip_to
  "reason": "Passed initial screening"
}
```

Response:
```json
{
  "success": true,
  "transitioned": 3,
  "failed": 0,
  "results": [
    {
      "opportunity_id": "opp1",
      "from_stage": "PLAN",
      "to_stage": "ANALYZE",
      "timestamp": "2025-10-02T10:00:00Z"
    },
    ...
  ]
}
```

---

### 6. System API - `/api/system`
**Purpose**: System health and monitoring

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| GET | `/api/system/health` | Health check | - | Health status |
| GET | `/api/system/status` | System status | - | Status object |

#### Example: Health Check
```http
GET /api/system/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-02T10:00:00Z",
  "components": {
    "database": "healthy",
    "tools": {
      "total": 23,
      "operational": 23,
      "deprecated": 0
    },
    "workflows": "healthy",
    "apis": {
      "v2_profiles": "healthy",
      "v1_tools": "healthy",
      "v1_workflows": "healthy"
    }
  },
  "uptime_seconds": 86400,
  "version": "2.0.0"
}
```

---

## API Comparison

### Before (162 endpoints)
**Fragmented, duplicated, processor-based**

```
# AI Analysis (30+ endpoints - all doing similar things)
/api/ai/lite-analysis
/api/ai/heavy-light/analyze
/api/ai/deep-research
/api/research/ai-lite/analyze
/api/profiles/{id}/analyze/ai-lite
...

# Profile Management (40+ endpoints - scattered)
/api/profiles
/api/profiles/fetch-ein
/api/profiles/{id}/analytics
/api/profiles/{id}/metrics
/api/profiles/{id}/enhanced-intelligence
...

# Scoring (15+ endpoints - duplicated)
/api/analysis/scoring
/api/scoring/government
/api/scoring/financial
/api/scoring/network
...
```

### After (35 endpoints)
**Clean, RESTful, tool-based**

```
# AI Analysis (2 tool execution calls)
POST /api/v1/tools/opportunity-screening-tool/execute
POST /api/v1/tools/deep-intelligence-tool/execute

# Profile Management (10 well-defined endpoints)
POST   /api/v2/profiles
GET    /api/v2/profiles
GET    /api/v2/profiles/{id}
PUT    /api/v2/profiles/{id}
DELETE /api/v2/profiles/{id}
POST   /api/v2/profiles/build
...

# Scoring (4 tool execution calls)
POST /api/v1/tools/financial-intelligence-tool/execute
POST /api/v1/tools/risk-intelligence-tool/execute
POST /api/v1/tools/network-intelligence-tool/execute
POST /api/v1/tools/multi-dimensional-scorer-tool/execute
```

---

## Request/Response Patterns

### Standard Response Format
All endpoints return consistent response structure:

```json
{
  "success": true,
  "data": {...},  # Main response data
  "meta": {
    "timestamp": "2025-10-02T10:00:00Z",
    "execution_time_ms": 123,
    "version": "2.0.0"
  },
  "errors": []  # Empty if success=true
}
```

### Error Response Format
```json
{
  "success": false,
  "data": null,
  "meta": {
    "timestamp": "2025-10-02T10:00:00Z",
    "execution_time_ms": 12,
    "version": "2.0.0"
  },
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "EIN format is invalid",
      "field": "ein",
      "details": "Expected 9-digit format: XX-XXXXXXX"
    }
  ]
}
```

### Pagination Pattern
For list endpoints:

```http
GET /api/v2/profiles?page=2&limit=50&sort=name&order=asc
```

Response:
```json
{
  "success": true,
  "data": [...],
  "meta": {
    "pagination": {
      "page": 2,
      "limit": 50,
      "total_pages": 10,
      "total_items": 472,
      "has_next": true,
      "has_prev": true
    }
  }
}
```

---

## Authentication & Security

### API Key Authentication
```http
GET /api/v2/profiles
Authorization: Bearer {api_key}
```

### Rate Limiting
```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1633024800
```

### CORS Headers
```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
```

---

## Versioning Strategy

### URL-Based Versioning
- `/api/v1/*` - Tool & Workflow APIs (stable)
- `/api/v2/*` - Profile, Discovery, Funnel APIs (current)
- `/api/v3/*` - Future breaking changes

### Deprecation Policy
1. **Announce deprecation** - 30 days notice
2. **Add deprecation headers** - Sunset header with date
3. **Maintain for transition** - 60 days minimum
4. **Remove deprecated** - After usage drops to 0%

---

## OpenAPI Specification

### Complete API Documentation
Available at:
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/openapi.json`

### Example OpenAPI Path
```yaml
/api/v2/profiles/build:
  post:
    summary: Build comprehensive profile
    description: Execute orchestrated profile building workflow
    tags: [profiles_v2]
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [ein]
            properties:
              ein:
                type: string
                pattern: '^[0-9]{2}-[0-9]{7}$'
              enable_tool25:
                type: boolean
                default: true
              enable_tool2:
                type: boolean
                default: false
              quality_threshold:
                type: number
                minimum: 0
                maximum: 1
                default: 0.70
    responses:
      200:
        description: Profile built successfully
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProfileBuildResponse'
      400:
        description: Invalid request
      500:
        description: Internal server error
```

---

## Migration Path

### From Legacy to V2

**Old (deprecated)**:
```http
POST /api/profiles/fetch-ein
{
  "ein": "812827604",
  "enable_web_scraping": true
}
```

**New (V2)**:
```http
POST /api/v2/profiles/build
{
  "ein": "812827604",
  "enable_tool25": true,
  "enable_tool2": false
}
```

### Tool Execution Migration

**Old (deprecated)**:
```http
POST /api/ai/heavy-light/analyze
{
  "opportunities": [...],
  "profile": {...}
}
```

**New (tool API)**:
```http
POST /api/v1/tools/opportunity-screening-tool/execute
{
  "inputs": {
    "opportunities": [...],
    "profile": {...},
    "mode": "thorough"
  }
}
```

---

## Performance Targets

### Response Time SLAs
- **Health checks**: <50ms
- **Profile CRUD**: <200ms
- **Discovery queries**: <1s
- **Tool execution**: Varies by tool (see tool metadata)
- **Workflow execution**: Async with status polling

### Throughput Targets
- **Concurrent requests**: 100+
- **Tool executions**: 50/minute (rate limited)
- **Database queries**: <100ms p95
- **Workflow orchestration**: 20 concurrent workflows

---

## Summary

### Key Improvements
1. **78% reduction** in endpoints (162 → 35)
2. **RESTful design** - Standard HTTP methods and patterns
3. **Tool-based execution** - Unified interface for all AI/analysis
4. **Workflow orchestration** - Multi-step processes simplified
5. **Clear versioning** - V1 vs V2 separation
6. **Comprehensive docs** - OpenAPI specification

### Benefits
- **Easier to learn** - Predictable patterns
- **Easier to maintain** - Less code duplication
- **Better performance** - Optimized tool execution
- **Clearer semantics** - One endpoint per function
- **Future-proof** - Versioning strategy in place

---

**Document Version**: 1.0
**Last Updated**: 2025-10-02
**Related Documents**:
- TOOLS_AND_ENDPOINTS_ANALYSIS.md
- API_CONSOLIDATION_ROADMAP.md
- PROCESSOR_DEPRECATION_PLAN.md
