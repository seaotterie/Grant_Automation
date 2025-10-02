# API Migration Guide - V1 to V2/Tools

**Last Updated**: 2025-10-02
**Migration Timeline**: November 15, 2025
**Support**: https://github.com/catalynx/support

---

## Overview

This guide helps you migrate from deprecated V1 endpoints to modern V2/Tool-based APIs. All deprecated endpoints will return deprecation headers guiding you to replacements.

### Deprecation Headers

All deprecated endpoints include these headers:
```http
X-Deprecated: true
X-Replacement-Endpoint: /api/v2/profiles/build
X-Migration-Guide: https://docs.catalynx.com/api/migration
Sunset: Fri, 15 Nov 2025 00:00:00 GMT
X-Deprecation-Phase: 1
X-Migration-Notes: Additional migration guidance
```

---

## Phase 1: AI & Scoring Endpoints

### AI Analysis → Tool Execution API

#### Old: AI Lite Analysis
```javascript
// DEPRECATED
const response = await fetch('/api/ai/lite-analysis', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    opportunities: [...],
    profile: {...}
  })
});

const data = await response.json();
console.log(data.results);
```

#### New: Opportunity Screening Tool
```javascript
// MODERN
const response = await fetch('/api/v1/tools/opportunity-screening-tool/execute', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    inputs: {
      opportunities: [...],
      profile: {...},
      mode: 'fast'  // or 'thorough'
    },
    config: {
      threshold: 0.55,
      max_recommendations: 15
    }
  })
});

const data = await response.json();
if (data.success) {
  console.log(data.data.scores);
}
```

**Key Changes**:
- Inputs wrapped in `inputs` object
- Add `mode` parameter ('fast' or 'thorough')
- Optional `config` for thresholds
- Response includes `success`, `tool_name`, `execution_time_ms`, `cost`

---

#### Old: Deep Research
```javascript
// DEPRECATED
const response = await fetch('/api/ai/deep-research', {
  method: 'POST',
  body: JSON.stringify({
    opportunity: {...},
    profile: {...}
  })
});
```

#### New: Deep Intelligence Tool
```javascript
// MODERN
const response = await fetch('/api/v1/tools/deep-intelligence-tool/execute', {
  method: 'POST',
  body: JSON.stringify({
    inputs: {
      opportunity: {...},
      profile: {...},
      depth: 'complete'  // 'quick', 'standard', 'enhanced', or 'complete'
    }
  })
});

const data = await response.json();
if (data.success) {
  console.log(data.data);
  console.log(`Cost: $${data.cost}`);
}
```

**Key Changes**:
- Add `depth` parameter
- Cost tracking in response
- Structured response format

---

#### Old: Batch Analysis
```javascript
// DEPRECATED
const response = await fetch('/api/ai/batch-analysis', {
  method: 'POST',
  body: JSON.stringify({
    opportunities: [...]
  })
});
```

#### New: Workflow API
```javascript
// MODERN
const response = await fetch('/api/v1/workflows/screen-opportunities', {
  method: 'POST',
  body: JSON.stringify({
    opportunities: [...],
    profile_id: 'uuid',
    config: {
      fast_mode_threshold: 0.50,
      thorough_mode_threshold: 0.60
    }
  })
});

const data = await response.json();
const executionId = data.execution_id;

// Poll for status
const statusResponse = await fetch(`/api/v1/workflows/status/${executionId}`);
const status = await statusResponse.json();

// Get results when complete
if (status.status === 'completed') {
  const resultsResponse = await fetch(`/api/v1/workflows/results/${executionId}`);
  const results = await resultsResponse.json();
}
```

**Key Changes**:
- Async execution with status polling
- Execution ID tracking
- Separate status and results endpoints

---

### Scoring → Tool Execution API

#### Old: Government Scoring
```javascript
// DEPRECATED
const response = await fetch('/api/scoring/government', {
  method: 'POST',
  body: JSON.stringify({
    opportunity: {...},
    profile: {...}
  })
});
```

#### New: Multi-Dimensional Scorer
```javascript
// MODERN
const response = await fetch('/api/v1/tools/multi-dimensional-scorer-tool/execute', {
  method: 'POST',
  body: JSON.stringify({
    inputs: {
      opportunity: {...},
      profile: {...},
      stage: 'DISCOVER'  // Funnel stage for context
    }
  })
});

const data = await response.json();
if (data.success) {
  console.log(data.data.overall_score);
  console.log(data.data.dimensional_scores);
}
```

---

#### Old: Financial Scoring
```javascript
// DEPRECATED
const response = await fetch('/api/scoring/financial', {
  method: 'POST',
  body: JSON.stringify({
    organization: {...}
  })
});
```

#### New: Financial Intelligence Tool
```javascript
// MODERN
const response = await fetch('/api/v1/tools/financial-intelligence-tool/execute', {
  method: 'POST',
  body: JSON.stringify({
    inputs: {
      organization_ein: '81-2827604',
      form_990_data: {...}
    }
  })
});

const data = await response.json();
if (data.success) {
  console.log(data.data.financial_health_rating);
  console.log(data.data.grant_capacity);
}
```

---

#### Old: Network Scoring
```javascript
// DEPRECATED
const response = await fetch('/api/scoring/network', {
  method: 'POST',
  body: JSON.stringify({
    organization: {...}
  })
});
```

#### New: Network Intelligence Tool
```javascript
// MODERN
const response = await fetch('/api/v1/tools/network-intelligence-tool/execute', {
  method: 'POST',
  body: JSON.stringify({
    inputs: {
      organization_ein: '81-2827604',
      board_members: [...],
      target_funder_ein: '12-3456789'
    }
  })
});
```

---

### Profile-Scoped Endpoints → V2 API

#### Old: Profile Scoring
```javascript
// DEPRECATED
const response = await fetch(`/api/profiles/${profileId}/opportunity-scores`, {
  method: 'POST',
  body: JSON.stringify({
    opportunities: [...]
  })
});
```

#### New: V2 Profile Opportunity Scoring
```javascript
// MODERN
const response = await fetch(`/api/v2/profiles/${profileId}/opportunities/score`, {
  method: 'POST',
  body: JSON.stringify({
    opportunities: [...]
  })
});
```

---

### Export & Reporting → Tool Execution API

#### Old: Export Opportunities
```javascript
// DEPRECATED
const response = await fetch('/api/export/opportunities', {
  method: 'POST',
  body: JSON.stringify({
    opportunities: [...],
    format: 'excel'
  })
});
```

#### New: Data Export Tool
```javascript
// MODERN
const response = await fetch('/api/v1/tools/data-export-tool/execute', {
  method: 'POST',
  body: JSON.stringify({
    inputs: {
      data: [...],
      data_type: 'opportunities',
      format: 'excel',
      fields: ['name', 'deadline', 'amount']
    }
  })
});

const data = await response.json();
if (data.success) {
  // Download file from data.data.file_path
  window.location.href = data.data.download_url;
}
```

---

#### Old: Generate Reports
```javascript
// DEPRECATED
const response = await fetch('/api/analysis/reports', {
  method: 'POST',
  body: JSON.stringify({
    opportunity: {...},
    template: 'comprehensive'
  })
});
```

#### New: Report Generator Tool
```javascript
// MODERN
const response = await fetch('/api/v1/tools/report-generator-tool/execute', {
  method: 'POST',
  body: JSON.stringify({
    inputs: {
      opportunity: {...},
      profile: {...},
      template: 'comprehensive',  // 'comprehensive', 'executive', 'risk', 'implementation'
      format: 'html'
    }
  })
});

const data = await response.json();
if (data.success) {
  // Display HTML report
  document.getElementById('report').innerHTML = data.data.html_content;
}
```

---

## Response Format Standards

### Tool Execution Response
All tool executions return this format:

```typescript
interface ToolExecutionResponse {
  success: boolean;
  tool_name: string;
  tool_version: string;
  execution_time_ms: number;
  cost: number;
  data?: any;  // Tool-specific output
  error?: string;  // Only if success=false
}
```

### Workflow Execution Response

```typescript
interface WorkflowExecutionResponse {
  execution_id: string;
  workflow_name: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  started_at: string;
  estimated_completion?: string;
}

interface WorkflowStatusResponse {
  execution_id: string;
  status: string;
  progress: number;  // 0-100
  current_step?: string;
  completed_steps: string[];
  errors: string[];
}

interface WorkflowResultResponse {
  execution_id: string;
  workflow_name: string;
  status: 'completed' | 'failed';
  result: any;
  execution_time_ms: number;
  cost: number;
}
```

---

## Error Handling

### Old Error Handling
```javascript
// DEPRECATED - varied error formats
try {
  const response = await fetch('/api/ai/lite-analysis', {...});
  const data = await response.json();

  if (!response.ok) {
    // Error format varied by endpoint
    console.error(data.error || data.message || 'Unknown error');
  }
} catch (e) {
  console.error(e);
}
```

### New Error Handling
```javascript
// MODERN - consistent error format
try {
  const response = await fetch('/api/v1/tools/opportunity-screening-tool/execute', {...});
  const data = await response.json();

  if (!data.success) {
    // Consistent error in data.error
    console.error(`Tool execution failed: ${data.error}`);
    return;
  }

  // Success - data in data.data
  console.log(data.data);

} catch (e) {
  console.error('Network error:', e);
}
```

---

## Common Migration Patterns

### Pattern 1: Single Tool Call

**Before**:
```javascript
const result = await callDeprecatedEndpoint();
```

**After**:
```javascript
const response = await fetch('/api/v1/tools/{tool-name}/execute', {
  method: 'POST',
  body: JSON.stringify({inputs: {...}})
});
const result = await response.json();
```

### Pattern 2: Batch Processing

**Before**:
```javascript
const results = await callBatchEndpoint({items: [...]});
```

**After**:
```javascript
// Initiate workflow
const {execution_id} = await fetch('/api/v1/workflows/execute', {
  method: 'POST',
  body: JSON.stringify({workflow_name: '...', context: {...}})
}).then(r => r.json());

// Poll for completion
const results = await pollWorkflowResults(execution_id);
```

### Pattern 3: Sequential Dependent Calls

**Before**:
```javascript
const scored = await score(opps);
const analyzed = await analyze(scored);
const report = await generateReport(analyzed);
```

**After**:
```javascript
// Use workflow for orchestration
const {execution_id} = await fetch('/api/v1/workflows/deep-intelligence', {
  method: 'POST',
  body: JSON.stringify({
    opportunities: opps,
    profile_id: profileId,
    depth: 'complete'
  })
}).then(r => r.json());

const results = await pollWorkflowResults(execution_id);
```

---

## Testing Your Migration

### 1. Check Deprecation Headers
```javascript
const response = await fetch('/api/ai/lite-analysis', {...});

if (response.headers.get('X-Deprecated') === 'true') {
  const replacement = response.headers.get('X-Replacement-Endpoint');
  console.warn(`Deprecated! Use: ${replacement}`);
}
```

### 2. Compare Responses
```javascript
// Call both old and new endpoints
const oldResponse = await fetch('/api/scoring/financial', {...});
const newResponse = await fetch('/api/v1/tools/financial-intelligence-tool/execute', {...});

// Compare results
console.log('Old:', await oldResponse.json());
console.log('New:', await newResponse.json());
```

### 3. Performance Testing
```javascript
const start = Date.now();
const response = await fetch('/api/v1/tools/...', {...});
const duration = Date.now() - start;

const data = await response.json();
console.log(`Client time: ${duration}ms`);
console.log(`Server time: ${data.execution_time_ms}ms`);
console.log(`Cost: $${data.cost}`);
```

---

## Utilities & Helpers

### Helper Function: Tool Execution
```javascript
async function executeTool(toolName, inputs, config = {}) {
  const response = await fetch(`/api/v1/tools/${toolName}/execute`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({inputs, config})
  });

  const data = await response.json();

  if (!data.success) {
    throw new Error(`Tool execution failed: ${data.error}`);
  }

  return data;
}

// Usage
const result = await executeTool('opportunity-screening-tool', {
  opportunities: [...],
  mode: 'fast'
});
```

### Helper Function: Workflow Execution
```javascript
async function executeWorkflow(workflowName, context) {
  // Start workflow
  const initResponse = await fetch('/api/v1/workflows/execute', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({workflow_name: workflowName, context})
  });

  const {execution_id} = await initResponse.json();

  // Poll for completion
  while (true) {
    const statusResponse = await fetch(`/api/v1/workflows/status/${execution_id}`);
    const status = await statusResponse.json();

    if (status.status === 'completed') {
      const resultsResponse = await fetch(`/api/v1/workflows/results/${execution_id}`);
      return await resultsResponse.json();
    }

    if (status.status === 'failed') {
      throw new Error(`Workflow failed: ${status.errors.join(', ')}`);
    }

    // Wait before polling again
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}

// Usage
const results = await executeWorkflow('screen-opportunities', {
  opportunities: [...],
  profile_id: 'uuid'
});
```

---

## Timeline

| Date | Milestone |
|------|-----------|
| Oct 2, 2025 | Deprecation headers added |
| Oct 9, 2025 | Week 1 - AI/Scoring migration complete |
| Oct 16, 2025 | Week 2 - Profile/Discovery migration complete |
| Oct 23, 2025 | Week 3 - Final migration complete |
| Nov 15, 2025 | **Sunset Date - Legacy endpoints removed** |

---

## Support & Resources

### Documentation
- **OpenAPI Spec**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Tool List**: `GET /api/v1/tools`
- **Workflow List**: `GET /api/v1/workflows/list`

### Monitoring
- **Deprecation Stats**: `GET /api/admin/deprecated-usage`
- **System Health**: `GET /api/system/health`

### Get Help
- **GitHub Issues**: https://github.com/catalynx/support/issues
- **Migration Questions**: migration@catalynx.com
- **Slack Channel**: #api-migration

---

## FAQ

**Q: What if I can't migrate by November 15?**
A: Contact us at migration@catalynx.com. We can provide extension support for critical integrations.

**Q: Will the response format change?**
A: Yes - see "Response Format Standards" above. All tool responses follow the same structure.

**Q: How do I know which tool to use?**
A: Check the deprecation header `X-Replacement-Endpoint` or see the mapping tables above.

**Q: Are there breaking changes?**
A: Request/response formats are different, but all functionality is preserved. Use the helper functions above for easier migration.

**Q: Can I test the new endpoints now?**
A: Yes! All V2/tool endpoints are operational. You can run them in parallel with legacy endpoints.

---

**Version**: 1.0
**Last Updated**: 2025-10-02
**Feedback**: Please report issues or suggestions to api-feedback@catalynx.com
