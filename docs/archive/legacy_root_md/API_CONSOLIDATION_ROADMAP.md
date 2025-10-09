# API Consolidation Roadmap

**Date**: 2025-10-02
**Goal**: Reduce 162 legacy endpoints to 35 modern endpoints (78% reduction)
**Timeline**: 3 phases over 3 weeks
**Status**: Planning Phase

---

## Executive Summary

### Current State
- **162 legacy endpoints** using processor-based architecture
- **11 modern endpoints** using tool-based architecture (V2 + Tool API)
- **High duplication**: 80-90% of functionality duplicated across endpoints
- **High complexity**: 40+ processor imports, difficult to maintain

### Target State
- **35 core endpoints** using tool/workflow-based architecture
- **Clean separation**: Profiles, Tools, Workflows, Intelligence, System
- **Standardized patterns**: RESTful design, consistent responses
- **Reduced complexity**: 5 processor imports (minimum required)

### Benefits
- **78% endpoint reduction** (127 endpoints removed)
- **Simplified maintenance** (90% less code to maintain)
- **Better performance** (optimized tool execution)
- **Clearer documentation** (RESTful, predictable)
- **Easier frontend development** (consistent patterns)

---

## Phase 1: AI & Analysis Consolidation (Week 1)

### Priority: HIGH - Low Risk, High Impact
**Target**: Remove 55 endpoints (34% of total)

### 1.1 AI Analysis Endpoint Migration

#### Endpoints to Deprecate (30 endpoints)
```
# AI Analysis Endpoints
/api/ai/lite-analysis → /api/v1/tools/opportunity-screening-tool/execute
/api/ai/heavy-light/analyze → /api/v1/tools/opportunity-screening-tool/execute
/api/ai/heavy-1/research-bridge → /api/v1/tools/deep-intelligence-tool/execute
/api/ai/deep-research → /api/v1/tools/deep-intelligence-tool/execute
/api/ai/lite-1/validate → /api/v1/tools/opportunity-screening-tool/execute
/api/ai/lite-2/strategic-score → /api/v1/tools/opportunity-screening-tool/execute
/api/ai/batch-analysis → /api/v1/workflows/screen-opportunities
/api/ai/orchestrated-pipeline → /api/v1/workflows/deep-intelligence
/api/ai/analysis-status/{request_id} → /api/v1/workflows/status/{execution_id}
/api/ai/cost-estimates → (Add to tool metadata)
/api/ai/session-summary → (Add to workflow results)

# Research Endpoints
/api/research/ai-lite/analyze → /api/v1/tools/opportunity-screening-tool/execute
/api/research/capabilities → /api/v1/tools (GET)
/api/research/status/{profile_id} → /api/v1/workflows/status/{execution_id}
/api/research/integration-status/{opp_id} → /api/v1/workflows/status/{execution_id}
/api/research/split-capabilities → /api/v1/tools (GET)
/api/research/performance-summary → /api/v1/workflows/executions (GET)
/api/research/export-results → /api/v1/tools/data-export-tool/execute
/api/research/website-intelligence → /api/v1/tools/web-intelligence-tool/execute

# Profile-scoped AI Endpoints
/api/profiles/{id}/analyze/ai-lite → /api/v1/tools/opportunity-screening-tool/execute
/api/profiles/{id}/research/analyze-integrated → /api/v1/tools/deep-intelligence-tool/execute
/api/profiles/{id}/research/batch-analyze → /api/v1/workflows/screen-opportunities
/api/profiles/{id}/research/decision-package/{opp_id} → /api/v1/workflows/deep-intelligence

# Classification Endpoints
/api/classification/start → /api/v1/workflows/execute
/api/classification/{workflow_id}/results → /api/v1/workflows/results/{execution_id}
```

#### Migration Steps
1. **Add deprecation warnings** to all AI endpoints (response headers)
2. **Create migration guide** for frontend developers
3. **Update frontend code** to use tool execution API
4. **Add redirect layer** (optional) for graceful transition
5. **Monitor usage** for 1 week
6. **Remove endpoints** after usage drops to 0%

#### Implementation Tasks
- [ ] Add `X-Deprecated: true` header to all AI endpoints
- [ ] Add `X-Replacement-Endpoint` header with new endpoint
- [ ] Create frontend migration PR with updated API calls
- [ ] Update API documentation
- [ ] Add usage monitoring for deprecated endpoints

### 1.2 Scoring & Analysis Endpoint Migration

#### Endpoints to Deprecate (15 endpoints)
```
# Scoring Endpoints
/api/analysis/scoring → /api/v1/tools/multi-dimensional-scorer-tool/execute
/api/analysis/enhanced-scoring → /api/v1/tools/multi-dimensional-scorer-tool/execute
/api/scoring/government → /api/v1/tools/multi-dimensional-scorer-tool/execute
/api/scoring/financial → /api/v1/tools/financial-intelligence-tool/execute
/api/scoring/network → /api/v1/tools/network-intelligence-tool/execute
/api/scoring/ai-lite → /api/v1/tools/opportunity-screening-tool/execute
/api/scoring/comprehensive → /api/v1/tools/multi-dimensional-scorer-tool/execute
/api/scoring/success-patterns → /api/v1/tools/multi-dimensional-scorer-tool/execute
/api/scoring/configuration → (Add to tool metadata)

# Analysis Endpoints
/api/analysis/network → /api/v1/tools/network-intelligence-tool/execute
/api/analysis/strategic-plan → /api/v1/workflows/deep-intelligence
/api/analyze/network-data/{profile_id} → /api/v1/tools/network-intelligence-tool/execute

# Profile-scoped Scoring
/api/profiles/{id}/opportunity-scores → /api/v2/profiles/{id}/opportunities/score
/api/profiles/{id}/opportunities/{opp_id}/score → /api/v2/profiles/{id}/opportunities/score
/api/profiles/{id}/opportunities/{opp_id}/scoring-rationale → /api/v2/profiles/{id}/opportunities/score
```

#### Implementation Tasks
- [ ] Deprecate scoring endpoints with migration headers
- [ ] Update frontend scoring components
- [ ] Test tool execution API performance
- [ ] Update scoring documentation

### 1.3 Export & Reporting Endpoint Migration

#### Endpoints to Deprecate (10 endpoints)
```
# Export Endpoints
/api/export/opportunities → /api/v1/tools/data-export-tool/execute
/api/analysis/export → /api/v1/tools/data-export-tool/execute
/api/exports/{export_filename} → (Keep for file downloads)
/api/exports/charts/{export_filename} → (Keep for file downloads)
/api/exports/classification/{workflow_id} → /api/v1/workflows/results/{execution_id}
/api/exports/workflow/{workflow_id} → /api/v1/workflows/results/{execution_id}

# Reporting Endpoints
/api/analysis/reports → /api/v1/tools/report-generator-tool/execute
/api/dossier/{dossier_id}/generate-document → /api/v1/tools/report-generator-tool/execute
/api/dossier/templates → /api/v1/tools/report-generator-tool (GET metadata)
/api/dossier/performance-summary → /api/v1/workflows/executions
```

#### Implementation Tasks
- [ ] Deprecate export/report endpoints
- [ ] Update report generation frontend
- [ ] Keep file download endpoints (non-redundant)
- [ ] Update export documentation

### Phase 1 Success Metrics
- ✅ 55 endpoints deprecated (34% of total)
- ✅ Frontend migration complete
- ✅ Zero production errors
- ✅ API usage shifted to tool execution

---

## Phase 2: Profile & Discovery Consolidation (Week 2)

### Priority: MEDIUM - Moderate Risk, High Impact
**Target**: Remove 60 endpoints (37% of total)

### 2.1 Profile Management Consolidation

#### Current State (40 endpoints)
**Problem**: Highly fragmented profile operations across many endpoints

#### Target State (8 endpoints)
```
# Core Profile Endpoints (V2 API)
POST   /api/v2/profiles                    # Create profile
GET    /api/v2/profiles                    # List profiles
GET    /api/v2/profiles/{id}               # Get profile details
PUT    /api/v2/profiles/{id}               # Update profile
DELETE /api/v2/profiles/{id}               # Delete profile
POST   /api/v2/profiles/build              # Orchestrated profile building
GET    /api/v2/profiles/{id}/analytics     # Profile analytics
POST   /api/v2/profiles/{id}/export        # Export profile data
```

#### Endpoints to Deprecate (32 endpoints)
```
# Profile CRUD (consolidate to 5 endpoints)
/api/profiles (GET, POST) → /api/v2/profiles
/api/profiles/{id} (GET, PUT, DELETE) → /api/v2/profiles/{id}
/api/profiles/simple/{id} (DELETE) → /api/v2/profiles/{id}
/api/profiles-new (GET) → /api/v2/profiles
/api/profiles/database (GET) → /api/v2/profiles
/api/profiles/templates (POST) → (Remove - use frontend templates)

# Profile Building (consolidate to 1 endpoint)
/api/profiles/fetch-ein → /api/v2/profiles/build
/api/profiles/{id}/enhanced-intelligence → /api/v2/profiles/build
/api/profiles/{id}/verified-intelligence → /api/v2/profiles/build
/api/profiles/{ein}/web-intelligence → /api/v2/profiles/build

# Profile Analytics (consolidate to 1 endpoint)
/api/profiles/{id}/analytics → /api/v2/profiles/{id}/analytics
/api/profiles/{id}/analytics/real-time → /api/v2/profiles/{id}/analytics
/api/profiles/{id}/metrics → /api/v2/profiles/{id}/analytics
/api/profiles/{id}/metrics/funnel → /api/v2/profiles/{id}/analytics
/api/profiles/{id}/metrics/session → /api/v2/profiles/{id}/analytics
/api/profiles/metrics/summary → /api/v2/profiles (aggregated)

# Profile Discovery (move to discovery section)
/api/profiles/{id}/discover → /api/v2/discovery/execute
/api/profiles/{id}/discover/bmf → /api/v2/discovery/bmf
/api/profiles/{id}/discover/entity-analytics → /api/v2/discovery/execute
/api/profiles/{id}/discover/entity-preview → /api/v2/discovery/preview
/api/profiles/{id}/discover/unified → /api/v2/discovery/execute
/api/profiles/{id}/discovery/sessions → /api/v2/discovery/sessions
/api/profiles/{id}/entity-analysis → /api/v2/discovery/analyze
/api/profiles/{id}/entity-discovery → /api/v2/discovery/execute

# Profile Dossier (consolidate to tool)
/api/profiles/{id}/dossier/generate → /api/v1/tools/report-generator-tool/execute
/api/profiles/{id}/dossier/batch-generate → /api/v1/workflows/execute

# Profile Results (consolidate)
/api/profiles/{id}/plan-results → /api/v2/profiles/{id}/analytics
/api/profiles/{id}/pipeline → /api/v2/profiles/{id}/analytics
```

#### Implementation Tasks
- [ ] Implement V2 profile CRUD endpoints
- [ ] Migrate profile building to orchestrated workflow
- [ ] Consolidate analytics into single endpoint with query params
- [ ] Update frontend profile components
- [ ] Create profile migration guide

### 2.2 Discovery & Search Consolidation

#### Current State (20 endpoints)
**Problem**: Multiple discovery tracks with overlapping functionality

#### Target State (6 endpoints)
```
# Unified Discovery Endpoints
POST   /api/v2/discovery/execute           # Execute discovery workflow
GET    /api/v2/discovery/bmf               # BMF-specific discovery
POST   /api/v2/discovery/search            # Search across all sources
GET    /api/v2/discovery/sessions          # List discovery sessions
GET    /api/v2/discovery/sessions/{id}     # Get session details
POST   /api/v2/discovery/analyze           # Analyze discovery results
```

#### Endpoints to Deprecate (14 endpoints)
```
# Discovery Track Endpoints (consolidate to execute)
/api/discovery/nonprofit → /api/v2/discovery/execute (track: nonprofit)
/api/discovery/federal → /api/v2/discovery/execute (track: federal)
/api/discovery/state → /api/v2/discovery/execute (track: state)
/api/discovery/commercial → /api/v2/discovery/execute (track: commercial)
/api/states/discover → /api/v2/discovery/execute (track: state)
/api/commercial/discover → /api/v2/discovery/execute (track: commercial)
/api/commercial/industries → /api/v2/discovery/execute (track: commercial)

# BMF Discovery (keep specialized)
/api/discovery/bmf/{profile_id} → /api/v2/discovery/bmf
/api/profiles/{id}/run-bmf-filter → /api/v2/discovery/bmf

# Search Endpoints (consolidate)
/api/search/opportunities → /api/v2/discovery/search
/api/search/fields → /api/v2/discovery/search (metadata)
/api/search/stats → /api/v2/discovery/sessions (stats)

# Discovery Sessions
/api/discovery/sessions → /api/v2/discovery/sessions
/api/discovery/sessions/recent → /api/v2/discovery/sessions?recent=true

# Discovery Stats
/api/discovery/stats/global → /api/v2/discovery/sessions (aggregate stats)
/api/discovery/entity-cache-stats → /api/v2/discovery/sessions (cache stats)
```

#### Implementation Tasks
- [ ] Implement unified discovery execute endpoint
- [ ] Add track/type parameter for different discovery modes
- [ ] Consolidate search functionality
- [ ] Migrate session management
- [ ] Update discovery frontend

### 2.3 Opportunity Management Consolidation

#### Current State (20 endpoints)
**Problem**: Opportunity CRUD scattered across profile and standalone endpoints

#### Target State (6 endpoints)
```
# Opportunity Endpoints (V2)
GET    /api/v2/profiles/{id}/opportunities                # List opportunities
POST   /api/v2/profiles/{id}/opportunities/discover       # Discover new
GET    /api/v2/profiles/{id}/opportunities/{opp_id}      # Get details
PUT    /api/v2/profiles/{id}/opportunities/{opp_id}      # Update
DELETE /api/v2/profiles/{id}/opportunities/{opp_id}      # Delete
POST   /api/v2/profiles/{id}/opportunities/{opp_id}/evaluate  # Evaluate
```

#### Endpoints to Deprecate (14 endpoints)
```
# Opportunity CRUD
/api/opportunities → /api/v2/profiles/{id}/opportunities
/api/profiles/{id}/opportunities (GET) → /api/v2/profiles/{id}/opportunities
/api/profiles/{id}/opportunities/{opp_id} (GET, PUT, DELETE) → /api/v2/profiles/{id}/opportunities/{opp_id}
/api/profiles/{id}/opportunities/{opp_id}/details → /api/v2/profiles/{id}/opportunities/{opp_id}

# Opportunity Enhancement
/api/profiles/{id}/opportunities/{opp_id}/enhanced-data → /api/v2/profiles/{id}/opportunities/{opp_id}
/api/profiles/{id}/opportunities/enhanced-data/batch → /api/v2/profiles/{id}/opportunities (batch param)

# Opportunity Evaluation
/api/profiles/{id}/opportunities/{opp_id}/evaluate → /api/v2/profiles/{id}/opportunities/{opp_id}/evaluate
/api/intelligence/classify → /api/v2/profiles/{id}/opportunities/{opp_id}/evaluate

# Leads Management
/api/profiles/{id}/leads → /api/v2/profiles/{id}/opportunities?type=lead
/api/profiles/{id}/add-entity-lead → /api/v2/profiles/{id}/opportunities/discover
/api/profiles/leads/{lead_id}/entity-analysis → /api/v2/profiles/{id}/opportunities/{opp_id}
```

#### Implementation Tasks
- [ ] Implement V2 opportunity CRUD
- [ ] Add discovery integration
- [ ] Consolidate enhancement logic
- [ ] Update opportunity frontend

### Phase 2 Success Metrics
- ✅ 60 endpoints deprecated (37% of total)
- ✅ V2 profile/discovery APIs operational
- ✅ Frontend fully migrated to V2
- ✅ <5% error rate during migration

---

## Phase 3: Workflow & System Finalization (Week 3)

### Priority: LOW to MEDIUM - Variable Risk
**Target**: Remove 12 endpoints (7% of total), finalize architecture

### 3.1 Workflow & Funnel Consolidation

#### Current State (15 endpoints)
**Problem**: Workflow and funnel management fragmented

#### Target State (7 endpoints - already exist)
```
# Workflow Endpoints (already implemented)
POST   /api/v1/workflows/execute                          # Execute workflow
GET    /api/v1/workflows/status/{execution_id}            # Get status
GET    /api/v1/workflows/results/{execution_id}           # Get results
GET    /api/v1/workflows/list                             # List workflows
GET    /api/v1/workflows/executions                       # List executions
POST   /api/v1/workflows/screen-opportunities             # Convenience
POST   /api/v1/workflows/deep-intelligence                # Convenience
```

#### Endpoints to Deprecate (8 endpoints)
```
# Legacy Workflow Endpoints
/api/workflows/start → /api/v1/workflows/execute
/api/workflows → /api/v1/workflows/list
/api/workflows/{workflow_id}/status → /api/v1/workflows/status/{execution_id}
/api/testing/export-results → /api/v1/workflows/results/{execution_id}

# Live Progress Endpoints
/api/live/progress/{workflow_id} → /api/v1/workflows/status/{execution_id}
/api/live/discovery/{session_id} → /api/v2/discovery/sessions/{id}
```

#### Funnel Endpoints (Keep but enhance - 7 endpoints)
**Note**: Funnel is unique functionality, consolidate but don't remove
```
# Funnel Endpoints (enhance with V2)
POST   /api/v2/funnel/{profile_id}/transition             # Generic transition
GET    /api/v2/funnel/{profile_id}/opportunities          # List by stage
GET    /api/v2/funnel/{profile_id}/metrics                # Funnel metrics
GET    /api/v2/funnel/{profile_id}/recommendations        # Smart suggestions
GET    /api/v2/funnel/stages                              # Stage definitions

# Deprecate specific transition endpoints (consolidate to generic)
/api/funnel/{id}/opportunities/{opp_id}/promote → /api/v2/funnel/{id}/transition
/api/funnel/{id}/opportunities/{opp_id}/demote → /api/v2/funnel/{id}/transition
/api/funnel/{id}/opportunities/{opp_id}/stage → /api/v2/funnel/{id}/opportunities/{opp_id}
/api/funnel/{id}/bulk-transition → /api/v2/funnel/{id}/transition (batch)
/api/profiles/{id}/opportunities/bulk-promote → /api/v2/funnel/{id}/transition (batch)
/api/profiles/{id}/opportunities/{opp_id}/promote → /api/v2/funnel/{id}/transition
/api/profiles/{id}/promotion-candidates → /api/v2/funnel/{id}/recommendations
/api/profiles/{id}/promotion-history → /api/v2/funnel/{id}/metrics
/api/profiles/{id}/automated-promotion/process → /api/v2/funnel/{id}/auto-promote
/api/profiles/{id}/automated-promotion/candidates → /api/v2/funnel/{id}/recommendations
/api/profiles/{id}/automated-promotion/bulk-promote → /api/v2/funnel/{id}/transition (batch)
/api/automated-promotion/config → /api/v2/funnel/config
/api/automated-promotion/stats → /api/v2/funnel/{id}/metrics
```

#### Implementation Tasks
- [ ] Deprecate legacy workflow endpoints
- [ ] Implement V2 funnel API with generic transitions
- [ ] Consolidate promotion/demotion logic
- [ ] Update funnel frontend

### 3.2 System & Monitoring Consolidation

#### Keep Core System Endpoints (10 endpoints)
```
# Health & Status (essential)
GET    /api/system/health
GET    /api/system/status
GET    /api/health
GET    /api/v1/tools/health
GET    /api/v2/profiles/health

# Dashboard & Analytics (essential)
GET    /api/dashboard/overview
GET    /api/analytics/overview
GET    /api/analytics/trends

# Documentation (essential)
GET    /api/docs
GET    /api/redoc
```

#### Endpoints to Deprecate (4 endpoints)
```
# Processor-specific endpoints
/api/processors → /api/v1/tools (GET)
/api/processors/{name}/execute → /api/v1/tools/{name}/execute
/api/processors/{name}/status → /api/v1/tools/{name} (metadata)
/api/processors/architecture/overview → (Remove - use docs)
/api/processors/migration/status → (Remove - use PROCESSOR_DEPRECATION_PLAN.md)

# Pipeline Endpoints (no longer needed)
/api/pipeline/status → /api/system/status
/api/pipeline/full-summary → /api/system/status

# Testing Endpoints (move to separate test API)
/api/test → (Remove)
/api/test-fix → (Remove)
/api/testing/processors/{name}/test → (Remove)
/api/testing/processors/{name}/logs → (Remove)
/api/testing/processors/status → (Remove)
/api/testing/system/logs → (Remove)

# Miscellaneous (remove or consolidate)
/api/debug/funnel-status → /api/v2/funnel/{id}/metrics
/api/enhanced-data/cache → /api/system/status
/api/enhanced-data/config → (Remove)
/api/enhanced-data/stats → /api/system/status
```

#### Implementation Tasks
- [ ] Keep core health/status endpoints
- [ ] Remove processor-specific endpoints
- [ ] Remove test endpoints (use separate test suite)
- [ ] Update system monitoring

### Phase 3 Success Metrics
- ✅ 12 endpoints deprecated (7% of total)
- ✅ Funnel API V2 operational
- ✅ System monitoring streamlined
- ✅ All deprecated endpoints removed

---

## Final Target Architecture

### Core API Structure (35 endpoints total)

#### 1. Profile API (10 endpoints)
```
POST   /api/v2/profiles
GET    /api/v2/profiles
GET    /api/v2/profiles/{id}
PUT    /api/v2/profiles/{id}
DELETE /api/v2/profiles/{id}
POST   /api/v2/profiles/build
GET    /api/v2/profiles/{id}/analytics
POST   /api/v2/profiles/{id}/export
GET    /api/v2/profiles/{id}/quality
GET    /api/v2/profiles/health
```

#### 2. Tool Execution API (5 endpoints)
```
GET    /api/v1/tools                     # List all tools
GET    /api/v1/tools/{tool_name}         # Get tool metadata
POST   /api/v1/tools/{tool_name}/execute # Execute tool
GET    /api/v1/tools/categories/list     # List categories
GET    /api/v1/tools/health              # Health check
```

#### 3. Workflow API (7 endpoints)
```
POST   /api/v1/workflows/execute
GET    /api/v1/workflows/status/{execution_id}
GET    /api/v1/workflows/results/{execution_id}
GET    /api/v1/workflows/list
GET    /api/v1/workflows/executions
POST   /api/v1/workflows/screen-opportunities
POST   /api/v1/workflows/deep-intelligence
```

#### 4. Discovery API (6 endpoints)
```
POST   /api/v2/discovery/execute
GET    /api/v2/discovery/bmf
POST   /api/v2/discovery/search
GET    /api/v2/discovery/sessions
GET    /api/v2/discovery/sessions/{id}
POST   /api/v2/discovery/analyze
```

#### 5. Funnel API (5 endpoints)
```
POST   /api/v2/funnel/{profile_id}/transition
GET    /api/v2/funnel/{profile_id}/opportunities
GET    /api/v2/funnel/{profile_id}/metrics
GET    /api/v2/funnel/{profile_id}/recommendations
GET    /api/v2/funnel/stages
```

#### 6. System API (2 endpoints)
```
GET    /api/system/health
GET    /api/system/status
```

**Total: 35 endpoints**

---

## Migration Support Infrastructure

### 1. Deprecation Headers
Add to all deprecated endpoints:
```http
X-Deprecated: true
X-Deprecation-Date: 2025-10-15
X-Replacement-Endpoint: /api/v2/...
X-Migration-Guide: https://docs.catalynx.com/api/migration
Sunset: Fri, 15 Nov 2025 00:00:00 GMT
```

### 2. Response Wrappers
Add deprecation warning to response:
```json
{
  "data": {...},
  "meta": {
    "deprecated": true,
    "replacement": "/api/v2/profiles/build",
    "sunset_date": "2025-11-15",
    "migration_guide": "https://docs.catalynx.com/api/migration"
  }
}
```

### 3. Usage Monitoring
Track endpoint usage:
```python
# middleware/deprecation_tracker.py
async def track_deprecated_endpoint(request, endpoint):
    metrics.increment(f"deprecated.{endpoint}.usage")
    logger.warning(f"Deprecated endpoint accessed: {endpoint}")
```

### 4. Migration Guide Document
Create comprehensive migration guide:
- **Before/After** examples for each endpoint
- **Code snippets** for common use cases
- **Breaking changes** documentation
- **Support contacts** for assistance

### 5. Redirect Layer (Optional)
Automatic redirect for simple migrations:
```python
@app.get("/api/profiles/fetch-ein")
async def fetch_ein_redirect(request):
    # Redirect to V2 with deprecation warning
    return RedirectResponse(
        url="/api/v2/profiles/build",
        headers={"X-Deprecated-Redirect": "true"}
    )
```

---

## Risk Mitigation

### High-Risk Migrations
1. **Profile endpoints** - Heavy frontend usage
   - **Mitigation**: Phased rollout, feature flags, rollback plan

2. **Funnel transitions** - Complex state management
   - **Mitigation**: Extensive testing, staged deployment

3. **Discovery workflows** - Complex query patterns
   - **Mitigation**: Parallel testing, gradual migration

### Rollback Strategy
1. **Keep deprecated endpoints** for 2 weeks after migration
2. **Monitor error rates** - rollback if >5% errors
3. **Feature flags** for enabling V2 endpoints
4. **Database compatibility** maintained during transition

### Testing Strategy
1. **Unit tests** for all V2 endpoints
2. **Integration tests** for workflows
3. **Load tests** for performance validation
4. **Migration tests** comparing V1 vs V2 responses

---

## Success Criteria

### Phase 1 (Week 1)
- [ ] 55 AI/scoring endpoints deprecated
- [ ] Frontend migrated to tool execution API
- [ ] <2% error rate
- [ ] API usage monitoring active

### Phase 2 (Week 2)
- [ ] 60 profile/discovery endpoints deprecated
- [ ] V2 APIs fully operational
- [ ] Frontend 100% migrated
- [ ] <5% error rate during migration

### Phase 3 (Week 3)
- [ ] 12 system/workflow endpoints deprecated
- [ ] Funnel V2 operational
- [ ] All deprecated endpoints removed
- [ ] Final architecture documented

### Final Metrics
- ✅ **78% endpoint reduction** (162 → 35)
- ✅ **90% code reduction** in API layer
- ✅ **Zero breaking changes** (with migration period)
- ✅ **Improved performance** (tool-based execution)
- ✅ **Complete documentation** (RESTful, OpenAPI)

---

## Next Steps

### Immediate (This Week)
1. **Review this roadmap** with team
2. **Create migration guide** document
3. **Add deprecation headers** to Phase 1 endpoints
4. **Set up usage monitoring** for deprecated endpoints
5. **Plan frontend migration** Sprint 1

### Week 1 (Phase 1)
1. Start AI endpoint migration
2. Update frontend for tool execution API
3. Monitor usage and errors
4. Adjust rollout as needed

### Week 2 (Phase 2)
1. Start profile/discovery migration
2. Implement V2 APIs
3. Frontend migration Sprint 2
4. Testing and validation

### Week 3 (Phase 3)
1. Finalize workflow/system migration
2. Remove all deprecated endpoints
3. Final testing and documentation
4. Production deployment

---

**Document Version**: 1.0
**Author**: Phase 9 Planning Team
**Last Updated**: 2025-10-02
**Next Review**: After Phase 1 completion
