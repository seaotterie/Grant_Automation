# Catalynx API Documentation

## Table of Contents
- [API Overview](#api-overview)
- [Authentication](#authentication)
- [Core Endpoints](#core-endpoints)
- [Profile Management](#profile-management)
- [Discovery System](#discovery-system)
- [Analysis and Scoring](#analysis-and-scoring)
- [AI Processing](#ai-processing)
- [Export and Reporting](#export-and-reporting)
- [WebSocket Integration](#websocket-integration)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Code Examples](#code-examples)

## API Overview

The Catalynx API provides programmatic access to the comprehensive grant research intelligence platform. Built on FastAPI, it offers high-performance async endpoints with automatic OpenAPI documentation, real-time WebSocket integration, and enterprise-grade security features.

### Base URL
```
http://localhost:8000
```

### API Documentation
Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### Content Types
- **Request**: `application/json`
- **Response**: `application/json`
- **File Uploads**: `multipart/form-data`
- **Downloads**: `application/octet-stream`, `text/csv`, `application/pdf`

## Authentication

### JWT Token Authentication
The API uses JWT (JSON Web Tokens) for authentication with configurable expiration and refresh capabilities.

#### Authentication Endpoints

**POST /auth/login**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "string"
}
```

**POST /auth/refresh**
```json
{
  "refresh_token": "string"
}
```

### API Key Management
**GET /auth/api-keys**
```http
Authorization: Bearer <token>
```

**Response**:
```json
{
  "api_keys": {
    "openai": "configured",
    "grants_gov": "configured", 
    "propublica": "configured",
    "usaspending": "configured"
  },
  "status": "active"
}
```

## Core Endpoints

### System Health and Status

**GET /health**
```json
{
  "status": "healthy",
  "version": "6.0.0",
  "uptime": 3600,
  "processors": {
    "total": 18,
    "active": 18,
    "failed": 0
  },
  "cache_stats": {
    "hit_rate": 0.85,
    "entries": 1247,
    "size_mb": 15.2
  }
}
```

**GET /api/system/status**
```json
{
  "system_status": "operational",
  "processors": [
    {
      "name": "BMF Filter",
      "status": "active",
      "last_run": "2025-08-26T10:30:00Z",
      "success_rate": 1.0
    }
  ],
  "api_services": {
    "grants_gov": "connected",
    "propublica": "connected",
    "usaspending": "connected",
    "openai": "connected"
  }
}
```

### Dashboard Statistics

**GET /api/dashboard/stats**
```json
{
  "profiles": {
    "total": 67,
    "active": 42,
    "recent": 3
  },
  "opportunities": {
    "total": 1547,
    "high_score": 89,
    "recent": 23
  },
  "analysis": {
    "ai_lite_processed": 1547,
    "ai_heavy_promoted": 89,
    "success_rate": 0.94
  },
  "performance": {
    "avg_processing_time": 0.17,
    "cache_hit_rate": 0.85,
    "uptime": "99.8%"
  }
}
```

## Profile Management

### Profile CRUD Operations

**GET /api/profiles**
```http
Authorization: Bearer <token>
```

**Query Parameters**:
- `limit` (int): Number of results (default: 50, max: 100)
- `offset` (int): Pagination offset (default: 0)
- `search` (string): Search term for filtering
- `ntee_code` (string): Filter by NTEE classification

**Response**:
```json
{
  "profiles": [
    {
      "id": "profile_f3adef3b653c",
      "organization_name": "Example Nonprofit",
      "ein": "12-3456789",
      "ntee_codes": ["P20", "P30"],
      "created_at": "2025-08-25T14:30:00Z",
      "last_discovery": "2025-08-26T09:15:00Z",
      "opportunities_count": 23,
      "avg_score": 0.67
    }
  ],
  "total": 67,
  "limit": 50,
  "offset": 0
}
```

**POST /api/profiles**
```json
{
  "organization_name": "Example Nonprofit",
  "ein": "12-3456789",
  "address": {
    "street": "123 Main St",
    "city": "Richmond",
    "state": "VA",
    "zip": "23220"
  },
  "ntee_codes": ["P20", "P30"],
  "focus_areas": ["Education", "Youth Development"],
  "funding_preferences": {
    "min_amount": 10000,
    "max_amount": 500000,
    "types": ["grant", "contract"]
  },
  "geographic_scope": ["Virginia", "Mid-Atlantic"]
}
```

**GET /api/profiles/{profile_id}**
```json
{
  "id": "profile_f3adef3b653c",
  "organization_name": "Example Nonprofit",
  "ein": "12-3456789",
  "entity_data": {
    "financial_health": 0.78,
    "board_size": 12,
    "revenue_trend": "stable",
    "program_expense_ratio": 0.82
  },
  "opportunities": {
    "total": 23,
    "high_score": 12,
    "medium_score": 8,
    "low_score": 3
  },
  "last_analysis": "2025-08-26T09:15:00Z"
}
```

**PUT /api/profiles/{profile_id}**
```json
{
  "organization_name": "Updated Organization Name",
  "ntee_codes": ["P20", "P30", "P40"],
  "focus_areas": ["Education", "Youth Development", "Community Health"]
}
```

**DELETE /api/profiles/{profile_id}**
```http
HTTP 204 No Content
```

## Discovery System

### Entity-Based Discovery

**POST /api/profiles/{profile_id}/discover/entity-analytics**
```json
{
  "tracks": ["government", "state", "foundation", "commercial"],
  "parameters": {
    "max_results": 50,
    "geographic_filter": ["VA", "MD", "DC"],
    "min_funding": 10000,
    "max_funding": 500000,
    "deadline_days": 90
  },
  "use_shared_analytics": true,
  "priority": "normal"
}
```

**Response**:
```json
{
  "discovery_id": "disc_abc123def456",
  "status": "processing",
  "progress": {
    "total_processors": 18,
    "completed": 0,
    "current": "BMF Filter",
    "eta_seconds": 45
  },
  "websocket_url": "/ws/discovery/disc_abc123def456"
}
```

### Discovery Status and Results

**GET /api/discovery/{discovery_id}/status**
```json
{
  "discovery_id": "disc_abc123def456", 
  "status": "completed",
  "progress": {
    "total_processors": 18,
    "completed": 18,
    "success_rate": 1.0,
    "total_time": 12.34
  },
  "results": {
    "opportunities_found": 23,
    "high_score": 8,
    "medium_score": 12,
    "low_score": 3
  }
}
```

**GET /api/profiles/{profile_id}/opportunities**
```http
Authorization: Bearer <token>
```

**Query Parameters**:
- `score_min` (float): Minimum score threshold
- `track` (string): Filter by funding track
- `status` (string): Filter by opportunity status
- `limit` (int): Number of results

**Response**:
```json
{
  "opportunities": [
    {
      "id": "opportunity_abc123",
      "title": "STEM Education Innovation Grant",
      "agency": "Department of Education",
      "track": "government",
      "scores": {
        "government": 0.87,
        "ai_lite": 0.82,
        "overall": 0.85
      },
      "funding": {
        "min_amount": 50000,
        "max_amount": 250000,
        "total_available": 5000000
      },
      "deadlines": {
        "application": "2025-12-15T17:00:00Z",
        "award": "2025-02-15T00:00:00Z"
      },
      "compatibility": {
        "eligibility": 0.95,
        "geographic": 0.80,
        "timing": 0.85,
        "financial": 0.78
      }
    }
  ]
}
```

### Entity Cache Management

**GET /api/discovery/entity-cache-stats**
```json
{
  "cache_stats": {
    "total_entities": 42,
    "hit_rate": 0.85,
    "miss_rate": 0.15,
    "cache_size_mb": 15.2,
    "avg_lookup_time": 0.003
  },
  "entity_types": {
    "nonprofits": 42,
    "foundations": 15,
    "government": 127
  },
  "recent_activity": [
    {
      "entity_id": "ein_123456789",
      "type": "nonprofit",
      "last_accessed": "2025-08-26T10:30:00Z",
      "access_count": 23
    }
  ]
}
```

## Analysis and Scoring

### Government Opportunity Scoring

**POST /api/scoring/government**
```json
{
  "opportunity_id": "opportunity_abc123",
  "profile_id": "profile_f3adef3b653c",
  "parameters": {
    "eligibility_weight": 0.30,
    "geographic_weight": 0.20,
    "timing_weight": 0.20,
    "financial_weight": 0.15,
    "historical_weight": 0.15
  }
}
```

**Response**:
```json
{
  "overall_score": 0.87,
  "components": {
    "eligibility": {
      "score": 0.95,
      "weight": 0.30,
      "details": "Strong alignment with NTEE codes and focus areas"
    },
    "geographic": {
      "score": 0.80,
      "weight": 0.20,
      "details": "Virginia preference matches organization location"
    },
    "timing": {
      "score": 0.85,
      "weight": 0.20,
      "details": "90-day application window allows adequate preparation"
    },
    "financial": {
      "score": 0.78,
      "weight": 0.15,
      "details": "Award size compatible with organizational capacity"
    },
    "historical": {
      "score": 0.82,
      "weight": 0.15,
      "details": "Similar organizations have 82% success rate"
    }
  },
  "recommendation": "high",
  "confidence": 0.91
}
```

### Network Analysis

**GET /api/profiles/{profile_id}/network-analysis**
```json
{
  "network_metrics": {
    "board_connections": 47,
    "influence_score": 0.73,
    "centrality_rank": 12,
    "strategic_connections": [
      {
        "name": "Board Member Name",
        "connections": 23,
        "organizations": ["Org A", "Org B"],
        "influence": 0.82
      }
    ]
  },
  "partnership_opportunities": [
    {
      "organization": "Strategic Partner Org",
      "connection_strength": 0.76,
      "shared_board_members": 2,
      "collaboration_potential": "high"
    }
  ]
}
```

### Financial Analysis

**GET /api/entities/{entity_id}/financial-metrics**
```json
{
  "financial_health": 0.78,
  "metrics": {
    "revenue_trend": {
      "direction": "stable",
      "growth_rate": 0.03,
      "volatility": 0.12
    },
    "efficiency_ratios": {
      "program_expense": 0.82,
      "admin_expense": 0.12,
      "fundraising_expense": 0.06
    },
    "capacity_indicators": {
      "net_assets": 2500000,
      "liquid_assets": 450000,
      "debt_ratio": 0.15
    }
  },
  "funding_capacity": {
    "recommended_min": 25000,
    "recommended_max": 400000,
    "risk_tolerance": "moderate"
  }
}
```

## AI Processing

### AI Service Management

**GET /api/ai/status**
```json
{
  "services": {
    "ai_lite": {
      "status": "active",
      "processed_today": 147,
      "success_rate": 0.98,
      "avg_response_time": 0.85
    },
    "ai_heavy": {
      "status": "active",
      "processed_today": 23,
      "success_rate": 0.96,
      "avg_response_time": 12.34
    }
  },
  "cost_tracking": {
    "daily_spend": 15.67,
    "monthly_budget": 500.00,
    "utilization": 0.31
  }
}
```

### AI-Lite Scoring

**POST /api/ai/lite/score**
```json
{
  "opportunity_id": "opportunity_abc123",
  "profile_id": "profile_f3adef3b653c",
  "priority": "normal"
}
```

**Response**:
```json
{
  "ai_lite_score": 0.82,
  "processing_time": 0.85,
  "components": {
    "compatibility": 0.85,
    "strategic_fit": 0.78,
    "feasibility": 0.83
  },
  "promotion_eligible": true,
  "promotion_reason": "High compatibility and strategic alignment",
  "cost": 0.012
}
```

### AI-Heavy Promotion

**POST /api/ai/heavy/promote**
```json
{
  "opportunity_ids": ["opportunity_abc123", "opportunity_def456"],
  "profile_id": "profile_f3adef3b653c",
  "priority": "high"
}
```

**Response**:
```json
{
  "promotion_id": "promo_xyz789",
  "status": "processing",
  "opportunities": 2,
  "estimated_time": 45,
  "estimated_cost": 0.85,
  "websocket_url": "/ws/ai-heavy/promo_xyz789"
}
```

**GET /api/ai/heavy/results/{promotion_id}**
```json
{
  "promotion_id": "promo_xyz789",
  "status": "completed",
  "results": [
    {
      "opportunity_id": "opportunity_abc123",
      "ai_heavy_score": 0.89,
      "analysis": {
        "executive_summary": "Highly compatible opportunity...",
        "strategic_assessment": "Strong alignment with mission...",
        "application_strategy": "Recommended approach includes...",
        "risk_assessment": "Low risk with strong success probability"
      },
      "recommendation": "apply",
      "confidence": 0.92
    }
  ]
}
```

## Export and Reporting

### Multi-Format Export System

**POST /api/export/opportunities**
```json
{
  "profile_id": "profile_f3adef3b653c",
  "opportunity_ids": ["opportunity_abc123", "opportunity_def456"],
  "format": "pdf",
  "template": "executive",
  "options": {
    "include_charts": true,
    "include_analysis": true,
    "branding": "default"
  }
}
```

**Response**:
```json
{
  "export_id": "export_abc123",
  "status": "processing",
  "format": "pdf",
  "estimated_time": 15,
  "websocket_url": "/ws/export/export_abc123"
}
```

**GET /api/export/{export_id}/download**
```http
Content-Type: application/pdf
Content-Disposition: attachment; filename="catalynx_report_2025-08-26.pdf"
```

### Report Generation

**POST /api/reports/generate**
```json
{
  "template": "executive_summary",
  "profile_id": "profile_f3adef3b653c",
  "date_range": {
    "start": "2025-08-01",
    "end": "2025-08-26"
  },
  "sections": [
    "overview",
    "opportunities",
    "analysis",
    "recommendations"
  ],
  "format": "pdf"
}
```

## WebSocket Integration

### Real-Time Progress Monitoring

**Connection**: `ws://localhost:8000/ws/discovery/{discovery_id}`

**Message Types**:
```json
{
  "type": "progress",
  "data": {
    "processor": "Government Opportunity Scorer",
    "progress": 0.65,
    "status": "processing",
    "results_found": 12,
    "eta_seconds": 15
  }
}
```

```json
{
  "type": "result",
  "data": {
    "opportunity_id": "opportunity_abc123",
    "title": "New Opportunity Found",
    "score": 0.87,
    "track": "government"
  }
}
```

```json
{
  "type": "complete",
  "data": {
    "total_time": 23.45,
    "opportunities_found": 18,
    "success_rate": 1.0,
    "cache_hits": 15
  }
}
```

### AI Processing WebSocket

**Connection**: `ws://localhost:8000/ws/ai-heavy/{promotion_id}`

**Message Types**:
```json
{
  "type": "analysis_start",
  "data": {
    "opportunity_id": "opportunity_abc123",
    "estimated_time": 15
  }
}
```

```json
{
  "type": "analysis_complete", 
  "data": {
    "opportunity_id": "opportunity_abc123",
    "ai_heavy_score": 0.89,
    "processing_time": 12.34,
    "cost": 0.45
  }
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid profile ID format",
    "details": {
      "field": "profile_id",
      "expected": "profile_{12_char_id}",
      "received": "invalid_id"
    },
    "timestamp": "2025-08-26T10:30:00Z",
    "request_id": "req_abc123def456"
  }
}
```

### HTTP Status Codes
- **200 OK**: Successful request
- **201 Created**: Resource created successfully
- **204 No Content**: Successful deletion
- **400 Bad Request**: Invalid request format or parameters
- **401 Unauthorized**: Authentication required or invalid
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict or duplicate
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server processing error
- **503 Service Unavailable**: Service temporarily unavailable

### Error Types
- **VALIDATION_ERROR**: Request validation failure
- **AUTHENTICATION_ERROR**: Authentication failure
- **AUTHORIZATION_ERROR**: Insufficient permissions
- **RESOURCE_NOT_FOUND**: Requested resource not found
- **PROCESSING_ERROR**: Backend processing failure
- **RATE_LIMIT_EXCEEDED**: API rate limit exceeded
- **SERVICE_UNAVAILABLE**: External service unavailable

## Rate Limiting

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 3600
```

### Default Limits
- **General API**: 1000 requests/hour
- **AI Processing**: 100 requests/hour
- **Export Operations**: 50 requests/hour
- **Discovery Operations**: 20 requests/hour

### Rate Limit Response
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit exceeded",
    "details": {
      "limit": 1000,
      "window": 3600,
      "reset_time": "2025-08-26T11:00:00Z"
    }
  }
}
```

## Code Examples

### Python Client Example
```python
import requests
import json

class CatalynxClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
    
    def login(self, username, password):
        response = requests.post(f"{self.base_url}/auth/login", json={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            return True
        return False
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    def create_profile(self, profile_data):
        response = requests.post(
            f"{self.base_url}/api/profiles",
            json=profile_data,
            headers=self.get_headers()
        )
        return response.json()
    
    def start_discovery(self, profile_id, tracks=None):
        tracks = tracks or ["government", "state", "foundation"]
        response = requests.post(
            f"{self.base_url}/api/profiles/{profile_id}/discover/entity-analytics",
            json={"tracks": tracks},
            headers=self.get_headers()
        )
        return response.json()
    
    def get_opportunities(self, profile_id, score_min=0.7):
        response = requests.get(
            f"{self.base_url}/api/profiles/{profile_id}/opportunities",
            params={"score_min": score_min},
            headers=self.get_headers()
        )
        return response.json()

# Usage example
client = CatalynxClient()
client.login("username", "password")

# Create a profile
profile = client.create_profile({
    "organization_name": "Example Nonprofit",
    "ein": "12-3456789",
    "ntee_codes": ["P20"],
    "focus_areas": ["Education"]
})

# Start discovery
discovery = client.start_discovery(profile["id"])

# Get high-scoring opportunities
opportunities = client.get_opportunities(profile["id"], score_min=0.8)
```

### JavaScript Client Example
```javascript
class CatalynxAPI {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.token = null;
    }
    
    async login(username, password) {
        const response = await fetch(`${this.baseURL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            this.token = data.access_token;
            return true;
        }
        return false;
    }
    
    getHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
        };
    }
    
    async getDashboardStats() {
        const response = await fetch(`${this.baseURL}/api/dashboard/stats`, {
            headers: this.getHeaders()
        });
        return response.json();
    }
    
    async startDiscovery(profileId, tracks = ['government']) {
        const response = await fetch(
            `${this.baseURL}/api/profiles/${profileId}/discover/entity-analytics`,
            {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify({ tracks })
            }
        );
        return response.json();
    }
    
    // WebSocket for real-time updates
    connectWebSocket(discoveryId, onMessage) {
        const ws = new WebSocket(`ws://localhost:8000/ws/discovery/${discoveryId}`);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage(data);
        };
        return ws;
    }
}

// Usage example
const api = new CatalynxAPI();
await api.login('username', 'password');

const stats = await api.getDashboardStats();
console.log('Dashboard stats:', stats);

const discovery = await api.startDiscovery('profile_abc123');
const ws = api.connectWebSocket(discovery.discovery_id, (data) => {
    console.log('Progress update:', data);
});
```

---

**API Version**: 6.0.0  
**Last Updated**: 2025-08-26  
**Documentation Status**: Complete - All 18 processors and Phase 6 features documented