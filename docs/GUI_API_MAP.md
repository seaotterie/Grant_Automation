# GUI → API Call Map

Last updated: 2026-03-05

Maps every significant GUI element to the JavaScript function it calls and the backend API endpoint that handles the request.

---

## Application Structure

| File | Role |
|---|---|
| `src/web/static/index.html` | Main SPA (3 stages: Profiler, Screening, Intelligence) |
| `src/web/static/app.js` | Alpine.js root app data and legacy functions |
| `src/web/static/api-helpers.js` | Reusable fetch wrappers for tool/workflow APIs |
| `src/web/static/modules/screening-module.js` | All screening-stage logic |
| `src/web/static/modules/intelligence-module.js` | All intelligence-stage logic |
| `src/web/static/gateway.html` | Standalone Human Gateway page (`/gateway`) |

---

## `index.html` — Main Application

### Stage: Profiler

| GUI Element | JS Function | API Endpoint |
|---|---|---|
| EIN field + lookup button | `fetchEINData()` | `POST /api/profiles/fetch-ein` |
| "Build Profile" button | inline `fetch()` in app.js | `POST /api/v2/profiles/build` |
| Profile list (auto-load on tab) | `loadProfiles()` | `GET /api/profiles` |
| Edit/save profile form | `saveProfile()` | `PUT /api/profiles/{id}` or `POST /api/profiles` |
| Delete profile (confirm dialog) | inline | `DELETE /api/profiles/{id}` |
| Metrics tab | `fetchMetrics()` | `GET /api/profiles/{id}/metrics` |

### Stage: Screening (`screening-module.js`)

| GUI Element | JS Function | API Endpoint |
|---|---|---|
| Discovery modal → "Start Discovery" | `executeNonprofitDiscovery(profileId, opts)` | `POST /api/v2/profiles/{id}/discover` |
| Discovery modal → BMF track | inline | `GET /api/v2/discovery/bmf?...` |
| "Discover All URLs" button | `discoverAllUrls(forceRefresh)` | `GET /api/v2/profiles/{id}/url-statistics` |
| "Screen Selected (Fast)" button | `screenOpportunities(opps, 'fast')` | `POST /api/v1/tools/Opportunity Screening Tool/execute` (via `api-helpers.js`) |
| "Promote Selected" button | `promoteSelectedOpportunities()` | `POST /api/v2/opportunities/{id}/promote` |
| "Proceed to Intelligence" button | `proceedToIntelligence()` | *(switches stage, no API call)* |
| "Run Web Research" button (opportunity modal) | `runWebResearch()` | `POST /api/v2/opportunities/{id}/research` |
| Opportunity detail → Promote | `promoteOpportunity()` | `POST /api/v2/opportunities/{id}/promote-with-notes` |
| Opportunity detail → Demote | `demoteOpportunity()` | `POST /api/v2/opportunities/{id}/demote` |
| Opportunity notes save | `saveNotes()` | `POST /api/v2/opportunities/{id}/notes` |

### Stage: Intelligence (`intelligence-module.js`)

| GUI Element | JS Function | API Endpoint |
|---|---|---|
| Opportunities list (auto-load) | `loadIntelligenceOpps()` | `GET /api/v2/profiles/{id}/opportunities?stage=intelligence` |
| Depth selector (Essentials / Premium) | `selectDepth(id)` | *(local state only)* |
| "Analyze All" button | `analyzeAll()` | `POST /api/intelligence/profiles/{id}/analysis` (one call per opp, polled via `GET /api/intelligence/analysis/{taskId}`) |
| "Run Analysis Now" per opportunity | `analyzeOpportunity(opp)` | `POST /api/intelligence/profiles/{id}/analysis` |
| "Generate Report" button | `generateReport(oppId)` | `POST /api/v1/tools/Report Generator Tool/execute` |
| "Export" button | `exportData(oppId, format)` | *(tool API — format-dependent)* |
| "Generate Package" button | `generatePackage(oppId)` | `POST /api/v1/tools/Grant Package Generator Tool/execute` |
| Scoring rationale panel (auto) | auto on opp select | `GET /api/profiles/{id}/opportunities/{id}/scoring-rationale` |

---

## `gateway.html` — Human Gateway (`/gateway`)

Standalone page. Paste screening JSON output, review opportunities, make pass/reject/investigate decisions, then launch deep analysis.

| GUI Element | JS Function | API Endpoint |
|---|---|---|
| JSON paste → "Load Results" button | `createSession()` | `POST /api/gateway/sessions` |
| Filter buttons (All / Pending / Pass / Reject / Investigate) | *(local filter)* | — |
| Sort by Score/Title toggle | *(local sort)* | — |
| "Pass" button per opportunity | `decide(id, 'pass')` | `PUT /api/gateway/sessions/{sid}/opportunities/{id}/decision` |
| "Reject" button | `decide(id, 'reject')` | `PUT /api/gateway/sessions/{sid}/opportunities/{id}/decision` |
| "Investigate" button | `decide(id, 'investigate')` | `PUT /api/gateway/sessions/{sid}/opportunities/{id}/decision` |
| Investigate question → submit | `investigate(oppId)` | `POST /api/gateway/sessions/{sid}/investigate/{id}` |
| Depth selector per passed opp | `updateDepth(opp)` | `PUT /api/gateway/sessions/{sid}/opportunities/{id}/decision` (includes `selected_depth`) |
| "Launch Deep Analysis" button | `launchDeepAnalysis()` | `GET /api/gateway/sessions/{sid}/passed` — **shows cost estimate alert only, not yet wired to deep intelligence** |

---

## Backend Routers (registered in `src/web/main.py`)

| Router File | Prefix | Key Endpoints |
|---|---|---|
| `profiles.py` | `/api/profiles` | CRUD profiles, fetch-ein, metrics, plan-results |
| `profiles_v2.py` | `/api/v2/profiles` | build, enhance, orchestrate, discover, quality-score |
| `discovery_v2.py` | `/api/v2/discovery` | execute, bmf, search |
| `intelligence.py` | `/api/intelligence` | `POST /profiles/{id}/analysis`, `GET /analysis/{taskId}` |
| `workflows.py` | `/api/workflows` | execute, status, results, list, screen-opportunities, deep-intelligence |
| `tools.py` | `/api/v1/tools` | list, `GET /{name}`, `POST /{name}/execute`, health |
| `gateway.py` | `/api/gateway` | sessions CRUD, decisions, batch-decision, investigate, passed list |
| `learning.py` | `/api/learning` | outcomes CRUD, summary, calibration, missed-opportunities, dashboard |
| `opportunities.py` | `/api/v2/opportunities` | promote, demote, notes, research, promote-with-notes |
| `intelligence.py` | `/api/intelligence` | profiles analysis, task polling |
| `foundation_network.py` | `/api/...` | foundation network analysis |

---

## Tool Execution Path

All 12-factor tools are executed through one of two paths:

**Path 1: Direct tool API** (used by intelligence-module.js and api-helpers.js)
```
GUI button
  → api-helpers.js: executeToolAPI(toolName, inputs)
  → POST /api/v1/tools/{toolName}/execute
  → src/web/routers/tools.py
  → tools/{tool_dir}/app/main.py
```

**Path 2: Intelligence analysis** (used for deep intelligence)
```
GUI button
  → api-helpers.js: analyzeOpportunityDeep(opp, profile, depth)
  → POST /api/intelligence/profiles/{id}/analysis
  → src/web/routers/intelligence.py
  → tools/deep_intelligence_tool/app/depth_handlers.py
  → src/core/anthropic_service.py → Claude API
  (async: poll GET /api/intelligence/analysis/{taskId})
```

**Path 3: Screening tool** (used by screening-module.js)
```
GUI "Screen" button
  → screening-module.js: screenOpportunities()
  → api-helpers.js: screenOpportunities() → executeToolAPI()
  → POST /api/v1/tools/Opportunity Screening Tool/execute
  → tools/opportunity_screening_tool/app/screening_tool.py
  → src/core/anthropic_service.py → Claude API (haiku for fast, sonnet for thorough)
```

---

## Known Gaps

| Gap | Location | Status |
|---|---|---|
| "Launch Deep Analysis" in gateway.html shows cost estimate but does not call deep intelligence | `gateway.html: launchDeepAnalysis()` | Not wired — alerts placeholder text |
| Learning/outcome dashboard has no GUI entry point | `src/web/routers/learning.py` | API exists, no frontend page |
| Foundation Preprocessing Tool not wired into any pipeline | `tools/foundation_preprocessing_tool/` | Built but unused |
| WebSocket `wsConnectionStatus` undefined on load | `src/web/static/app.js` | Initialization bug |
