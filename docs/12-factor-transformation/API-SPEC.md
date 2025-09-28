# 12-Factor API Specification
*Complete interface documentation for 12-factor agent systems*

## API Architecture Overview

This specification defines RESTful and WebSocket APIs for 12-factor agent systems, including agent registration, workflow orchestration, configuration management, and monitoring interfaces. All APIs are designed for horizontal scaling, stateless operation, and environment parity.

## Core Principles

### 12-Factor Alignment
- **Factor VII (Port Binding)**: Self-contained HTTP services
- **Factor VI (Processes)**: Stateless request processing
- **Factor IV (Backing Services)**: External dependencies as resources
- **Factor III (Config)**: Environment-driven configuration
- **Factor XI (Logs)**: Request/response event logging

### API Standards
- **Protocol**: HTTP/1.1, HTTP/2, WebSocket
- **Format**: JSON request/response bodies
- **Authentication**: JWT Bearer tokens
- **Versioning**: URL path versioning (`/api/v1/`)
- **Documentation**: OpenAPI 3.0 specification

## Authentication & Authorization

### JWT Token Structure
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_12345",
    "iss": "catalynx-auth",
    "aud": "catalynx-api",
    "exp": 1640995200,
    "iat": 1640908800,
    "roles": ["user", "admin"],
    "permissions": ["read:profiles", "write:profiles", "execute:agents"]
  }
}
```

### Authorization Levels
- **Public**: No authentication required
- **User**: Valid JWT token required
- **Admin**: Admin role required
- **System**: Internal service-to-service communication

## Agent Registry API

### Base URL: `/api/v1/agents`

#### List Agents
```http
GET /api/v1/agents
Authorization: Bearer {jwt_token}
```

**Query Parameters:**
- `capability` (string, optional): Filter by capability
- `status` (string, optional): Filter by health status [healthy, degraded, unhealthy]
- `limit` (integer, default=50): Maximum results
- `offset` (integer, default=0): Pagination offset

**Response:**
```json
{
  "agents": [
    {
      "id": "bmf_filter_agent",
      "name": "BMF Filter Agent",
      "capabilities": ["bmf_filtering", "nonprofit_discovery"],
      "endpoint": "http://bmf-service:8001",
      "version": "1.2.0",
      "status": "healthy",
      "last_health_check": "2024-01-15T10:30:00Z",
      "metadata": {
        "process_type": "worker",
        "max_concurrent_tasks": 10,
        "average_response_time_ms": 150
      }
    }
  ],
  "total_count": 25,
  "healthy_count": 23,
  "pagination": {
    "limit": 50,
    "offset": 0,
    "has_more": false
  }
}
```

#### Register Agent
```http
POST /api/v1/agents
Authorization: Bearer {system_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "id": "new_agent_001",
  "name": "New Analysis Agent",
  "capabilities": ["analysis", "processing"],
  "endpoint": "http://new-agent:8002",
  "version": "1.0.0",
  "health_check_url": "http://new-agent:8002/health",
  "metadata": {
    "process_type": "worker",
    "max_concurrent_tasks": 5,
    "timeout_seconds": 300
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "new_agent_001",
  "status": "registered",
  "registered_at": "2024-01-15T10:30:00Z"
}
```

#### Get Agent Details
```http
GET /api/v1/agents/{agent_id}
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "id": "bmf_filter_agent",
  "name": "BMF Filter Agent",
  "capabilities": ["bmf_filtering", "nonprofit_discovery"],
  "endpoint": "http://bmf-service:8001",
  "version": "1.2.0",
  "status": "healthy",
  "registered_at": "2024-01-10T08:00:00Z",
  "last_health_check": "2024-01-15T10:30:00Z",
  "health_details": {
    "response_time_ms": 145,
    "memory_usage_mb": 256,
    "cpu_usage_percent": 12.5,
    "active_tasks": 3
  },
  "metadata": {
    "process_type": "worker",
    "max_concurrent_tasks": 10
  }
}
```

#### Execute Agent
```http
POST /api/v1/agents/{agent_id}/execute
Authorization: Bearer {jwt_token}
Content-Type: application/json
X-Correlation-ID: {correlation_id}
```

**Request Body:**
```json
{
  "action": "bmf_filter",
  "input": {
    "state": "VA",
    "ntee_codes": ["P20", "B25"],
    "revenue_range": [100000, 5000000]
  },
  "timeout_seconds": 300,
  "priority": "normal"
}
```

**Response:** `202 Accepted`
```json
{
  "execution_id": "exec_12345",
  "agent_id": "bmf_filter_agent",
  "status": "queued",
  "estimated_completion": "2024-01-15T10:35:00Z",
  "queue_position": 2
}
```

#### Get Execution Status
```http
GET /api/v1/agents/{agent_id}/executions/{execution_id}
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "execution_id": "exec_12345",
  "agent_id": "bmf_filter_agent",
  "status": "completed",
  "started_at": "2024-01-15T10:30:15Z",
  "completed_at": "2024-01-15T10:32:30Z",
  "duration_seconds": 135,
  "result": {
    "organizations_found": 47,
    "data": [
      {
        "ein": "541234567",
        "name": "Virginia Community Foundation",
        "ntee_code": "P20",
        "revenue": 2500000
      }
    ]
  }
}
```

## Workflow Orchestration API

### Base URL: `/api/v1/workflows`

#### Start Workflow
```http
POST /api/v1/workflows
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "workflow_type": "intelligence_tier",
  "tier": "enhanced",
  "profile_id": "profile_12345",
  "input": {
    "organization_name": "Virginia Community Foundation",
    "focus_areas": ["education", "health"],
    "geographic_scope": ["Virginia", "Washington DC"]
  },
  "options": {
    "async": true,
    "notification_webhook": "https://client.example.com/webhooks/workflow"
  }
}
```

**Response:** `202 Accepted`
```json
{
  "workflow_id": "wf_67890",
  "status": "initiated",
  "estimated_duration_minutes": 35,
  "steps": [
    {
      "step_id": "step_001",
      "agent_id": "bmf_filter_agent",
      "action": "bmf_filter",
      "status": "pending"
    },
    {
      "step_id": "step_002",
      "agent_id": "ai_heavy_agent",
      "action": "comprehensive_analysis",
      "status": "pending",
      "depends_on": ["step_001"]
    }
  ]
}
```

#### Get Workflow Status
```http
GET /api/v1/workflows/{workflow_id}
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "workflow_id": "wf_67890",
  "workflow_type": "intelligence_tier",
  "status": "running",
  "progress_percentage": 65,
  "started_at": "2024-01-15T10:30:00Z",
  "estimated_completion": "2024-01-15T11:05:00Z",
  "current_step": "step_002",
  "steps": [
    {
      "step_id": "step_001",
      "agent_id": "bmf_filter_agent",
      "action": "bmf_filter",
      "status": "completed",
      "started_at": "2024-01-15T10:30:15Z",
      "completed_at": "2024-01-15T10:32:30Z",
      "result_summary": "47 organizations found"
    },
    {
      "step_id": "step_002",
      "agent_id": "ai_heavy_agent",
      "action": "comprehensive_analysis",
      "status": "running",
      "started_at": "2024-01-15T10:32:45Z",
      "progress_percentage": 40
    }
  ],
  "metadata": {
    "total_cost_dollars": 12.50,
    "estimated_final_cost": 18.75
  }
}
```

#### Cancel Workflow
```http
DELETE /api/v1/workflows/{workflow_id}
Authorization: Bearer {jwt_token}
```

**Response:** `200 OK`
```json
{
  "workflow_id": "wf_67890",
  "status": "cancelled",
  "cancelled_at": "2024-01-15T10:45:00Z",
  "compensation_status": "in_progress",
  "partial_results_available": true
}
```

## Configuration Management API

### Base URL: `/api/v1/config`

#### Get System Configuration
```http
GET /api/v1/config
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
  "environment": "production",
  "version": "2.1.0",
  "feature_flags": {
    "gpt5_analysis": {
      "enabled": true,
      "rollout_percentage": 100
    },
    "enhanced_bmf_discovery": {
      "enabled": true,
      "rollout_percentage": 100
    },
    "real_time_notifications": {
      "enabled": false,
      "rollout_percentage": 0
    }
  },
  "agent_configs": {
    "bmf_filter_agent": {
      "max_concurrent_tasks": 10,
      "timeout_seconds": 300,
      "cache_ttl_minutes": 60
    },
    "ai_heavy_agent": {
      "max_concurrent_tasks": 2,
      "timeout_seconds": 600,
      "model": "gpt-5-turbo"
    }
  },
  "system_limits": {
    "max_concurrent_workflows": 50,
    "max_workflow_duration_minutes": 120,
    "rate_limit_requests_per_minute": 1000
  }
}
```

#### Update Feature Flag
```http
PATCH /api/v1/config/feature-flags/{flag_name}
Authorization: Bearer {admin_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "enabled": true,
  "rollout_percentage": 25,
  "conditions": {
    "user_tier": ["premium", "enterprise"]
  }
}
```

**Response:**
```json
{
  "flag_name": "real_time_notifications",
  "enabled": true,
  "rollout_percentage": 25,
  "updated_at": "2024-01-15T10:30:00Z",
  "effective_immediately": true
}
```

## Health & Monitoring API

### Base URL: `/api/v1/health`

#### System Health Check
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "2.1.0",
  "uptime_seconds": 86400,
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5,
      "connection_pool": {
        "active": 8,
        "idle": 12,
        "max": 20
      }
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2,
      "memory_usage_mb": 128
    },
    "agent_registry": {
      "status": "healthy",
      "total_agents": 25,
      "healthy_agents": 23,
      "degraded_agents": 2
    }
  },
  "metrics": {
    "requests_per_minute": 450,
    "average_response_time_ms": 250,
    "error_rate_percentage": 0.1,
    "active_workflows": 12
  }
}
```

#### Component Health Check
```http
GET /api/v1/health/{component_name}
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "component": "database",
  "status": "healthy",
  "last_check": "2024-01-15T10:30:00Z",
  "details": {
    "connection_test": "passed",
    "query_test": "passed",
    "response_time_ms": 5,
    "disk_usage_percentage": 45
  },
  "history": [
    {
      "timestamp": "2024-01-15T10:25:00Z",
      "status": "healthy",
      "response_time_ms": 6
    }
  ]
}
```

## Data Management API

### Base URL: `/api/v1/data`

#### Get Entity Data
```http
GET /api/v1/data/entities/{entity_type}/{entity_id}
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "entity_type": "nonprofit",
  "entity_id": "541234567",
  "data": {
    "basic_info": {
      "ein": "541234567",
      "name": "Virginia Community Foundation",
      "city": "Richmond",
      "state": "VA"
    },
    "financial_data": {
      "revenue": 2500000,
      "assets": 15000000,
      "year": 2023
    },
    "metadata": {
      "last_updated": "2024-01-15T08:00:00Z",
      "data_sources": ["bmf", "form_990"],
      "confidence_score": 0.95
    }
  }
}
```

#### Query Entities
```http
POST /api/v1/data/entities/query
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "entity_type": "nonprofit",
  "filters": {
    "state": ["VA", "MD", "DC"],
    "ntee_codes": ["P20", "B25"],
    "revenue_range": [100000, 5000000]
  },
  "fields": ["ein", "name", "revenue", "city"],
  "limit": 100,
  "offset": 0,
  "sort": [
    {"field": "revenue", "direction": "desc"}
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "ein": "541234567",
      "name": "Virginia Community Foundation",
      "revenue": 2500000,
      "city": "Richmond"
    }
  ],
  "total_count": 247,
  "pagination": {
    "limit": 100,
    "offset": 0,
    "has_more": true
  },
  "query_metadata": {
    "execution_time_ms": 45,
    "cache_hit": false,
    "data_freshness": "2024-01-15T08:00:00Z"
  }
}
```

## WebSocket Real-Time API

### Connection: `wss://api.catalynx.com/ws/v1`

#### Authentication
```javascript
// Connect with JWT token
const ws = new WebSocket('wss://api.catalynx.com/ws/v1?token=' + jwt_token);
```

#### Subscribe to Workflow Updates
```json
{
  "action": "subscribe",
  "channel": "workflow_updates",
  "filters": {
    "workflow_id": "wf_67890"
  }
}
```

#### Workflow Progress Event
```json
{
  "event_type": "workflow_progress",
  "timestamp": "2024-01-15T10:35:00Z",
  "data": {
    "workflow_id": "wf_67890",
    "progress_percentage": 75,
    "current_step": "step_003",
    "estimated_completion": "2024-01-15T10:50:00Z"
  }
}
```

#### Agent Status Event
```json
{
  "event_type": "agent_status_change",
  "timestamp": "2024-01-15T10:35:00Z",
  "data": {
    "agent_id": "bmf_filter_agent",
    "old_status": "healthy",
    "new_status": "degraded",
    "reason": "High response time detected"
  }
}
```

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": [
      {
        "field": "revenue_range",
        "issue": "Maximum value cannot exceed 50000000"
      }
    ],
    "correlation_id": "req_12345",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `AUTHENTICATION_ERROR` | 401 | Invalid or missing authentication |
| `AUTHORIZATION_ERROR` | 403 | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource doesn't exist |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `AGENT_UNAVAILABLE` | 503 | Agent temporarily unavailable |
| `WORKFLOW_TIMEOUT` | 504 | Workflow execution timeout |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## Rate Limiting

### Standard Limits
- **Free Tier**: 100 requests/hour
- **Standard Tier**: 1000 requests/hour
- **Premium Tier**: 10000 requests/hour
- **Enterprise Tier**: Unlimited

### Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1640995200
```

## API Versioning

### URL Versioning
- Current: `/api/v1/`
- Future: `/api/v2/` (backward compatible)

### Deprecation Headers
```http
Deprecation: true
Sunset: Sat, 31 Dec 2024 23:59:59 GMT
Link: </api/v2/agents>; rel="successor-version"
```

## OpenAPI Specification

### Complete OpenAPI 3.0 Schema
```yaml
openapi: 3.0.3
info:
  title: Catalynx 12-Factor Agent API
  description: RESTful API for 12-factor agent orchestration system
  version: 1.0.0
  contact:
    name: API Support
    email: api-support@catalynx.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.catalynx.com/api/v1
    description: Production server
  - url: https://staging-api.catalynx.com/api/v1
    description: Staging server

security:
  - bearerAuth: []

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    Agent:
      type: object
      required:
        - id
        - name
        - capabilities
        - endpoint
        - version
      properties:
        id:
          type: string
          pattern: '^[a-z0-9_]+$'
          example: "bmf_filter_agent"
        name:
          type: string
          example: "BMF Filter Agent"
        capabilities:
          type: array
          items:
            type: string
          example: ["bmf_filtering", "nonprofit_discovery"]
        endpoint:
          type: string
          format: uri
          example: "http://bmf-service:8001"
        version:
          type: string
          pattern: '^\d+\.\d+\.\d+$'
          example: "1.2.0"
        status:
          type: string
          enum: [healthy, degraded, unhealthy]
        metadata:
          type: object
          additionalProperties: true

    Workflow:
      type: object
      required:
        - workflow_type
        - input
      properties:
        workflow_type:
          type: string
          enum: [intelligence_tier, custom_analysis]
        tier:
          type: string
          enum: [current, standard, enhanced, complete]
        profile_id:
          type: string
        input:
          type: object
          additionalProperties: true
        options:
          type: object
          properties:
            async:
              type: boolean
              default: true
            notification_webhook:
              type: string
              format: uri

    Error:
      type: object
      required:
        - error
      properties:
        error:
          type: object
          required:
            - code
            - message
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: array
              items:
                type: object
            correlation_id:
              type: string
            timestamp:
              type: string
              format: date-time

paths:
  /agents:
    get:
      summary: List all agents
      parameters:
        - name: capability
          in: query
          schema:
            type: string
        - name: status
          in: query
          schema:
            type: string
            enum: [healthy, degraded, unhealthy]
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 50
        - name: offset
          in: query
          schema:
            type: integer
            minimum: 0
            default: 0
      responses:
        '200':
          description: List of agents
          content:
            application/json:
              schema:
                type: object
                properties:
                  agents:
                    type: array
                    items:
                      $ref: '#/components/schemas/Agent'
                  total_count:
                    type: integer
                  healthy_count:
                    type: integer

    post:
      summary: Register new agent
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Agent'
      responses:
        '201':
          description: Agent registered successfully
        '400':
          description: Invalid agent configuration
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /workflows:
    post:
      summary: Start new workflow
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Workflow'
      responses:
        '202':
          description: Workflow initiated
        '400':
          description: Invalid workflow configuration
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
```

## SDK Examples

### Python SDK
```python
from catalynx_sdk import CatalynxClient, WorkflowRequest

# Initialize client
client = CatalynxClient(
    api_key="your_api_key",
    base_url="https://api.catalynx.com/api/v1"
)

# Start intelligence workflow
workflow = WorkflowRequest(
    workflow_type="intelligence_tier",
    tier="enhanced",
    profile_id="profile_12345",
    input={
        "organization_name": "Virginia Community Foundation",
        "focus_areas": ["education", "health"]
    }
)

result = await client.workflows.create(workflow)
print(f"Workflow started: {result.workflow_id}")

# Monitor progress
async for update in client.workflows.stream_progress(result.workflow_id):
    print(f"Progress: {update.progress_percentage}%")
```

### JavaScript SDK
```javascript
import { CatalynxClient } from '@catalynx/sdk';

const client = new CatalynxClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.catalynx.com/api/v1'
});

// Start workflow
const workflow = await client.workflows.create({
  workflowType: 'intelligence_tier',
  tier: 'enhanced',
  profileId: 'profile_12345',
  input: {
    organizationName: 'Virginia Community Foundation',
    focusAreas: ['education', 'health']
  }
});

// Real-time updates via WebSocket
const ws = client.websocket.connect();
ws.subscribe('workflow_updates', { workflowId: workflow.workflowId }, (update) => {
  console.log(`Progress: ${update.progressPercentage}%`);
});
```

---

This API specification provides comprehensive interface documentation for building, integrating with, and maintaining 12-factor agent systems. All endpoints support horizontal scaling, stateless operation, and environment-based configuration following 12-factor principles.