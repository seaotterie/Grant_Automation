# Catalynx Code Review & Improvement Plan

**Date**: 2026-03-18
**Scope**: Full codebase review — architecture, code quality, security, testing, technical debt
**Codebase Stats**: ~226,800 lines of Python across 463 files (232 src/, 103 tools/, 128 tests/)

---

## Table of Contents

1. [Critical Findings](#1-critical-findings)
2. [Architecture Review](#2-architecture-review)
3. [Code Quality Issues](#3-code-quality-issues)
4. [Security Audit](#4-security-audit)
5. [Testing & Quality Assurance](#5-testing--quality-assurance)
6. [Technical Debt Inventory](#6-technical-debt-inventory)
7. [Improvement Plan](#7-improvement-plan-prioritized)

---

## 1. Critical Findings

### 1.1 `src/web/main.py` is 10,703 lines (God File)

**Severity**: Critical
**Impact**: Maintainability, testability, onboarding difficulty

This single file contains **164 route handlers**, utility functions, WebSocket handlers, business logic, and data access code. It is the largest file in the project by 4.7x. Despite having 20 router modules in `src/web/routers/`, the majority of endpoints are still defined directly on the `app` object in `main.py`.

**Key problems**:
- Business logic mixed with HTTP handling (e.g., `similar_organization_names()` at line 106, `secure_profile_deletion()` at line 157)
- Inline data dictionaries (chart type definitions at lines 10614-10671)
- 164 route decorators = ~65 lines per endpoint average, with many being 50-100+ lines of inline logic
- WebSocket handlers with complex business logic (lines 1428-1615+)
- Duplicate endpoint patterns (profiles CRUD both in main.py and in routers/profiles.py, routers/profiles_v2.py)

### 1.2 Secrets in `.env.example`

**Severity**: Critical (Security)
**File**: `.env.example` lines 5-15

The `.env.example` file contains what appear to be **actual generated secrets** — not placeholder values:
```
JWT_SECRET_KEY=xcOE2n-vgOtOxc7zC5qwOcNjqbPQPVEQ-vkolC3YpQUhxucAw2ajYyXHFbdyrGqI6VsxM_BFwX2NbAoxD0bAlg
ADMIN_PASSWORD=jEzFH9BIraPlBqFOHChI4-BL-MOXDhoOo3KvLNuqgRQ
USER_PASSWORD=7YOBtqbVsD_bb3lk2iOH6zS_xuLpA6tdW5sZlIRCaGM
```

If these were ever used in production, they are now compromised since `.env.example` is committed to git. Even if they were generated just for the example, this pattern encourages copying real secrets into examples.

### 1.3 No Production `requirements.txt`

**Severity**: Critical (Deployability)

Only `requirements-test.txt` exists. There is no `requirements.txt`, `pyproject.toml`, or `setup.py` defining production dependencies. This means:
- No reproducible builds
- No dependency pinning for production
- No way to install the project as a package
- No clear boundary between production and dev dependencies

### 1.4 No `.gitignore` or Incomplete Git Hygiene

**Severity**: High

No `pyproject.toml` or proper Python project packaging. `sys.path.append()` is used in `main.py` (line 32) to make imports work, which is a fragile anti-pattern.

---

## 2. Architecture Review

### 2.1 Overall Structure Assessment

```
Grant_Automation/
├── tools/          (103 files, ~32,800 lines) — 12-factor tools ✓ Good
├── src/            (232 files, ~113,100 lines) — Mixed quality
│   ├── web/        — FastAPI app (needs major refactoring)
│   ├── core/       — Framework infrastructure (solid)
│   ├── profiles/   — Service layer (acceptable)
│   ├── discovery/  — Service layer (acceptable)
│   ├── database/   — Data access (needs review)
│   └── [17 more]   — Many unused/legacy modules
└── tests/          (128 files) — Needs organization
```

### 2.2 Dead Modules (Zero Imports Anywhere in Project)

| Module | Files | Lines | Status |
|--------|-------|-------|--------|
| `src/accessibility/` | 1 | 1,825 | **Dead code** — never imported |
| `src/data_migration/` | 4 | 1,450 | **Dead code** — never imported |
| `src/evaluation/` | 4 | 2,753 | **Dead code** — never imported |
| `src/monitoring/` | 1 | 282 | **Dead code** — never imported |
| **Total** | **10** | **6,310** | Can be safely removed |

### 2.3 Legacy Processor System (Partially Deprecated)

`src/processors/` still contains **10 active Python files** (5,644 lines) despite the 12-factor tool migration being "complete." The `processors/registry.py` is still imported in `main.py` (line 53). This creates confusion about which system is authoritative.

Additional legacy presence:
- `src/profiles/_deprecated/service_legacy.py` (686 lines)
- `src/web/routers/discovery_legacy.py` (303 lines) — still imported in main.py (line 83)
- `src/web/routers/_deprecated/` directory exists
- `src/web/routers/ai_processing.py` — commented out in main.py but file still exists

### 2.4 Module Sprawl in `src/`

27 subdirectories under `src/` is excessive. Many contain only 1-2 files. The actual "active core" appears to be:
- `core/`, `web/`, `profiles/`, `discovery/`, `database/`, `workflows/`, `auth/`, `middleware/`

Modules with limited/unclear usage: `scoring/`, `analysis/`, `export/`, `visualization/`, `intelligence/`, `learning/`, `network/`, `pipeline/`, `clients/`, `config/`, `utils/`

### 2.5 Dual Architecture Confusion

The codebase maintains two parallel systems:
1. **12-factor tools** in `tools/` (24 tools, modern architecture)
2. **Legacy processors** in `src/processors/` and various `src/` modules

The CLAUDE.md describes both as operational, and the web layer references both systems. There's no clear migration path that removes the old system entirely.

### 2.6 Router Duplication

Multiple router versions exist for the same domain:
- `profiles.py` + `profiles_v2.py` + `profiles_intelligence.py` + endpoints in `main.py`
- `discovery.py` + `discovery_v2.py` + `discovery_legacy.py`
- Routes in `main.py` that overlap with routes in router modules

This creates ambiguity about which endpoint is canonical and risks route conflicts.

---

## 3. Code Quality Issues

### 3.1 God File Decomposition Needed

`src/web/main.py` at 10,703 lines should be decomposed into focused routers. Approximate breakdown of what's currently inline:

| Category | Estimated Lines | Target Router |
|----------|----------------|---------------|
| Profile CRUD | ~1,500 | `routers/profiles_v2.py` (merge) |
| Research/AI endpoints | ~2,000 | `routers/research.py` (new) |
| Dossier generation | ~800 | `routers/dossier.py` (new) |
| Visualization/Charts | ~600 | `routers/visualizations.py` (new) |
| Scoring/Promotion | ~1,200 | `routers/scoring.py` (exists, merge) |
| Discovery endpoints | ~800 | `routers/discovery_v2.py` (merge) |
| System/Dashboard | ~400 | `routers/dashboard.py` (exists, merge) |
| WebSocket handlers | ~500 | `routers/websocket.py` (exists, merge) |
| Static files/docs | ~400 | `routers/docs.py` (new) |
| Testing/Export | ~400 | `routers/export.py` (exists, merge) |
| App setup + middleware | ~500 | Keep in `main.py` |
| Utility functions | ~300 | Move to `src/utils/` |

**Target**: `main.py` should be ~200-300 lines (app factory, middleware setup, router registration).

### 3.2 `sys.path.append()` Anti-Pattern

`main.py:32` uses `sys.path.append()` for imports. This is fragile and breaks in many deployment scenarios. The project should be installable as a package.

### 3.3 Heavy `__init__.py` Files

- `src/scoring/__init__.py` — 268 lines (contains actual logic, not just exports)
- `src/data_transformation/__init__.py` — 104 lines
- `src/evaluation/__init__.py` — 92 lines
- `src/processors/__init__.py` — 79 lines

`__init__.py` files should primarily handle exports, not contain business logic.

### 3.4 TODO/FIXME Markers

39 unresolved TODO/FIXME/HACK markers across the codebase (17 in src/, 22 in tools/). These should be triaged — either converted to tracked issues or resolved.

### 3.5 Tool-Level Consistency Issues

**Duplicate `RiskLevel` enum with incompatible values**:
- `deep_intelligence_tool/app/intelligence_models.py`: 4 values (LOW, MEDIUM, HIGH, CRITICAL)
- `risk_intelligence_tool/app/risk_models.py`: 5 values (MINIMAL, LOW, MEDIUM, HIGH, CRITICAL)
- These tools produce incompatible risk assessments. Needs consolidation into `tools/shared_schemas/`.

**Inconsistent path setup across tools**:
- 10 tools use `setup_tool_paths(__file__)` (correct pattern)
- 4 tools manually compute `project_root = Path(__file__).parent.parent.parent.parent` and `sys.path.insert()`
- Should standardize on `setup_tool_paths()` everywhere.

**Inconsistent enum inheritance**: Some enums use `str, Enum` (JSON-serializable), others use plain `Enum`. Should standardize to `str, Enum` for API compatibility.

**12factors.toml detail variation**: AI tools have 120-185 lines of detailed compliance docs; utility tools (EIN Validator, Data Export) have only 24-28 lines. Should use a common template.

**Missing tool tests**: `web_intelligence_tool` and `report_generator_tool` have no test files. `ein_validator_tool` has only 3 test cases.

**Underutilized shared_schemas/**: `tools/shared_schemas/` exists with `grant_funder_intelligence.py` but common types like `RiskLevel`, `HealthRating`, financial metrics, and assessment base classes aren't shared.

### 3.6 Inline Configuration Data

Chart type definitions, static metadata, and configuration dictionaries are hardcoded inline throughout `main.py` instead of being externalized to configuration files or constants modules.

### 3.6 Core Service Layer Issues (Per-File Analysis)

**`src/database/database_manager.py` (1,474 lines)**:
- 15+ catch-all `except Exception as e` handlers that return `False` with no diagnostic info
- Database connection pattern (`sqlite3.connect()` + `row_factory` + `cursor`) duplicated 6+ times
- Lazy `import sqlite3` inside methods instead of module-level import
- Schema initialization spread across 4+ methods making it hard to track what gets created
- Unused member variables (`_connection`, `_data_transformer`)
- Mixes `os.path` and `pathlib.Path` inconsistently
- Does not use existing `path_helper.py` for path management

**`src/profiles/unified_service.py` (1,022 lines)**:
- 3 separate `import sqlite3` at different locations in the file
- Debug code left in production (lines 324-334: lists all profiles on delete failure)
- Hardcoded DB paths in 2 formats: `os.path.join(root, "data", "catalynx.db")` vs `"data/catalynx.db"`
- Database-to-dict conversion logic duplicated between `get_profile()` and `list_profiles()`
- Potential circular import: `UnifiedProfileService` ↔ `DatabaseManager`

**`src/core/openai_service.py` (531 lines)**:
- ~55 lines of unreachable `_simulate_completion()` code (exception raised before it could be called)
- Test-specific logic ("STOP THE TEST") in production code (line 116)
- 5 fallback text extraction strategies in a brittle chain with no tracking of which succeeds
- Silent model fallback to `gpt-5-nano` on unknown models (line 456) — masks configuration errors
- Unused `import openai` (only `AsyncOpenAI` is actually used)

**`src/core/tool_registry.py` (436 lines)**:
- Uses `print()` instead of `logger.warning()` for tool loading failures (line 104)
- Fragile heuristic-based tool class detection: scans `dir(module)` for names ending in "Tool"
- Category extraction based on directory naming conventions — breaks silently on renames

**`src/workflows/tool_loader.py` (276 lines)**:
- Re-raises exceptions as generic `Exception`, losing original type information
- Redundant `from src.core.tool_framework import ToolResult` inside method (already imported at top)
- Module path resolution is fragile — assumes last part of dotted path is the module name

**`src/profiles/service.py` (60 lines)**:
- Deprecated compatibility shim using `type()` to create a fake class with lambdas
- Will break `isinstance()` checks — should be proper class inheritance or removed entirely

---

## 4. Security Audit

### 4.1 Critical: Authentication Disabled on All 164 Endpoints

JWT auth system exists (`src/auth/jwt_auth.py`) and is imported, but **commented out on every endpoint**. Comments throughout `main.py` say "Removed authentication: single-user desktop application." This means:
- Any network client can create/delete profiles, run expensive AI analyses, export all data
- Profile deletion (`DELETE /api/profiles/{profile_id}`) triggers permanent cascade deletion with no confirmation
- WebSocket endpoints (`/api/live/*`) accept any connection with no auth or subscription validation
- Batch endpoints can trigger mass operations (e.g., `/batch-web-research` with no size limit)

This is acceptable only for strictly local desktop use. Any networked deployment is completely unprotected.

### 4.2 Critical: Secrets in Version Control

**File**: `.env.example`
**Issue**: Generated JWT secrets and passwords committed to git
**Fix**: Replace with obvious placeholders like `your-jwt-secret-here`, `change-me-admin-password`

### 4.3 High: Path Traversal in Static File Serving

`main.py:952` serves static files via a custom handler instead of FastAPI's built-in `StaticFiles` middleware:
```python
@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    # NO path validation!
```
A request to `/static/../../../.env` could read sensitive files. Fix: Use the already-imported `StaticFiles` middleware.

### 4.4 High: CORS Overly Permissive

`main.py:395-401` — `allow_methods=["*"]` and `allow_headers=["*"]` allow unrestricted cross-origin requests. CORS origins are hardcoded rather than read from environment variables.

### 4.5 High: CSP Allows `unsafe-inline` and `unsafe-eval`

**File**: `src/middleware/security.py:31-32`
`unsafe-eval` effectively negates XSS protections from CSP. Required for Alpine.js/Tailwind CDN but should be replaced with nonce-based approach.

### 4.6 High: SSRF in PDF Analysis Endpoint

`opportunities.py:1498` — `POST /{opportunity_id}/analyze-990-pdf` accepts an arbitrary URL, downloads a PDF, and parses it. No URL validation, no file size limits, no content-type checking. Could be used for internal network scanning.

### 4.7 High: SQL Injection via String Interpolation

**File**: `src/analytics/soi_financial_analytics.py:125`
The `tax_year` parameter is interpolated directly into SQL via f-string:
```python
year_filter = f"AND tax_year = {tax_year}" if tax_year else ""
```
While `ein` is parameterized, `tax_year` is injected raw. If it comes from API input, arbitrary SQL can be injected.

Additional SQL risk in `profiles_v2.py:93-150` — NTEE code queries use regex validation but construct queries with string patterns rather than fully parameterized queries.

### 4.8 High: Path Traversal in Workflow Name Resolution

**File**: `src/web/routers/workflows.py:95`
```python
workflow_file = Path("src/workflows/definitions") / f"{workflow_name}.yaml"
```
User-supplied `workflow_name` is used directly in path construction. The `.yaml` suffix limits exploitability but defense in depth requires validation at point of use (e.g., `^[a-zA-Z0-9_-]+$`).

### 4.9 Medium: XSS Middleware Skips All `/api/` Paths

**File**: `src/middleware/security.py:152`
The `XSSProtectionMiddleware` skips all paths starting with `/api/` — the primary attack surface. API responses with user-provided data get no XSS sanitization from this middleware.

### 4.10 Medium: Rate Limiter Skips Localhost + X-Forwarded-For Spoofable

**File**: `src/middleware/security.py:397-399`
Rate limiting skipped entirely for `127.0.0.1`, `localhost`, `::1`. If deployed behind a reverse proxy that sets client IP to localhost, all rate limiting is bypassed. Both `jwt_auth.py:327` and `security.py:358` trust `X-Forwarded-For` without verification.

### 4.11 Medium: Error Messages Leak Internal Details

Throughout `main.py`, exception handlers pass `str(e)` directly to HTTP responses:
```python
raise HTTPException(status_code=500, detail=f"Chart export failed: {str(e)}")
```

### 4.9 Medium: Rate Limiting Too Simplistic

Global 60 req/min limit with no per-user/per-IP differentiation, no burst allowance, no exemption for async background tasks. May cause false positives during batch screening (200 opportunities) while providing no protection against distributed attacks.

### 4.10 Medium: Test/Debug Endpoints in Production

- `GET /api/test-fix` (main.py:489)
- `POST /api/testing/export-results` (main.py:1615)
- These should not exist in production code.

### 4.14 Medium: No CSRF Protection

CORS allows credentials (`allow_credentials=True`) but no CSRF token mechanism exists. If cookie-based auth is ever added, CSRF attacks become possible.

### 4.15 Medium: In-Memory User Store

**File**: `src/auth/jwt_auth.py:66`
Users stored in an in-memory dictionary. Password changes, account lockouts lost on restart. Rate limiter also in-memory — no distributed rate limiting possible.

### 4.16 Medium: Monolithic Frontend (`app.js` — 19,622 lines)

Single JavaScript file at ~900KB. CDN dependencies (Tailwind, D3.js) create external failure points. `innerHTML` usage with user data (line 9946) is an XSS risk. Modular `js/modules/` directory exists but `app.js` remains monolithic.

### 4.17 Low: Duplicate Router Prefixes

Two routers share `/api/v2/profiles` prefix:
- `profiles_v2.py` (line 36)
- `profiles_intelligence.py` (line 39)

Endpoint definitions could be overwritten depending on router inclusion order.

---

## 5. Testing & Quality Assurance

### 5.1 Test Overview

| Metric | Value | Assessment |
|--------|-------|------------|
| Active test files | 89 | Good |
| Archived test files | 40 | Legacy, properly tracked |
| Test functions | 295+ | Comprehensive |
| Total assertions | 1,678 | Good density |
| Async tests | 102 | Well-covered |
| Mock/patch usages | 483 | Thorough mocking |
| Fixtures defined | 97 | Excellent reusability |
| Parametrized tests | **0** | Critical gap |
| `pytest.raises()` calls | **2** | Error paths under-tested |

**Test Distribution**: Unit (40%), Integration (33%), E2E (4%), Other (23%) — proper pyramid structure.

### 5.2 Test Strengths

- **Central `conftest.py`** (450 lines): 97 fixtures including data factories, mock factories, assertion utilities (`assert_valid_score()`, `assert_valid_profile()`), and edge case generators
- **Async support**: 102 async tests with proper `AsyncMock` usage
- **Graceful degradation**: 19 `pytest.skip()` calls when services unavailable (appropriate pattern)
- **Quality of individual tests**: `test_screening_tool.py` is well-organized with 5 test classes covering success/failure paths, edge cases, and cost estimation

### 5.3 Test Gaps

**No parametrized tests**: Zero `@pytest.mark.parametrize` usage across the entire test suite. This means boundary conditions, multiple input combinations, and data-driven test variations are all tested through single-value fixtures rather than systematic parametrization.

**Minimal error/exception testing**: Only 2 `pytest.raises()` calls in 89 test files. Missing exception coverage for:
- Network failures and timeouts
- Database connection loss
- Invalid JSON/XML responses
- AI service rate limiting

**Manual test patterns**: `test_profile_suite.py` (747 lines) uses custom `print_result()` instead of standard pytest assertions — harder to integrate with CI/CD.

### 5.4 No CI/CD Pipeline

No `.github/workflows/` directory exists. Tests must be run manually. This is a critical gap — no automated regression detection on push or PR.

### 5.5 Coverage Gaps

- `pytest.ini` coverage targets `src/` only — the 24 tools in `tools/` have no coverage tracking
- Only 6 of 24 tools have `conftest.py` files; tool test structure varies significantly
- No production `requirements.txt` means test deps can't be verified against production deps
- Test database URL hardcoded: `sqlite:///./test_catalynx.db`

### 5.6 Missing Test Types

- Contract tests between tools and the web API layer
- End-to-end workflow tests (screening → gateway → deep intelligence)
- Load/performance tests for the API (locust configured but not automated)
- Database migration tests

---

## 6. Technical Debt Inventory

### 6.1 Quantified Debt

| Category | Lines/Files | Priority |
|----------|-------------|----------|
| Dead modules (4 unused) | 6,310 lines / 10 files | High — free cleanup |
| `main.py` god file | 10,703 lines / 1 file | Critical — blocks all web work |
| `app.js` god file | 19,622 lines / 1 file | High — frontend equivalent |
| Legacy `src/analysis/` | ~368 KB / 10 files | Medium — replaced by tools |
| Legacy `src/scoring/` | ~328 KB / 15 files | Medium — replaced by Tool 20 |
| Legacy `src/processors/` | ~56 KB / 18 files | Medium — migration planned |
| Deprecated files still imported | ~989 lines / 2 files | Medium |
| Router duplication | ~3 sets of v1/v2/legacy | High — API confusion |
| Unreachable code in `main.py` | Lines 9569, 10198 | Low — quick fix |
| Unused imports (Vulture, 90%+ confidence) | 18 items | Low — auto-fixable |
| Unused variables (100% confidence) | 11 items | Low — auto-fixable |
| Heavy `__init__.py` files | ~543 lines / 4 files | Low |
| Legacy JS in `_deprecated/` | 22 KB / 2 files | Low — safe to remove |
| Legacy test archive | 388 KB / 30+ files | Low |
| **Total recoverable** | **~1.3 MB of legacy code** | |

### 6.2 Critical: Tool Placeholder Implementations

Several "operational" tools contain **placeholder logic** with TODOs instead of actual AI integration:

| File | Line | TODO |
|------|------|------|
| `deep_intelligence_tool/app/depth_handlers.py` | 62 | "Replace with actual BAML AI calls" |
| `deep_intelligence_tool/app/depth_handlers.py` | 263 | "Replace with actual data analysis" |
| `deep_intelligence_tool/app/depth_handlers.py` | 316 | "Replace with actual network analysis" |
| `deep_intelligence_tool/app/depth_handlers.py` | 517 | "Replace with actual network analysis using Tool 12" |
| `deep_intelligence_tool/app/depth_handlers.py` | 603 | "Replace with actual Historical Funding Analyzer Tool (Tool 22)" |
| `financial_intelligence_tool/app/financial_tool.py` | 105 | "Placeholder - TODO: implement actual BAML call" |
| `risk_intelligence_tool/app/risk_tool.py` | 597 | "TODO: Implement actual BAML call" |

These tools are listed as "100% operational" in CLAUDE.md but contain stub implementations for core AI functionality. This is the most significant discrepancy between documented status and actual code state.

### 6.3 Deprecated Endpoints Past Sunset Date

20+ endpoints in `src/web/middleware/deprecation.py` have a sunset date of **2025-11-15** — over 4 months ago. These deprecated routes are still active and being served with deprecation headers. Examples:
- `/api/ai/lite-analysis` → should redirect to Tool 1
- `/api/ai/deep-research` → should redirect to Tool 2
- `/api/profiles/{id}/analyze/ai-lite` → should redirect to Tool 1

### 6.4 Missing Infrastructure

| Item | Impact | Priority |
|------|--------|----------|
| `requirements.txt` (production) | Cannot deploy reproducibly | Critical |
| `pyproject.toml` / proper packaging | Fragile imports, no installability | High |
| CI/CD pipeline | No automated quality gates | High |
| API versioning strategy | Breaking changes risk | Medium |
| Database migration tooling | Schema changes are manual | Medium |
| Logging standardization | Inconsistent log formats | Low |

### 6.5 CLAUDE.md Drift

The `CLAUDE.md` file is **extremely long** and contains contradictory information:
- States both "2-Tier Intelligence System" and "4-TIER INTELLIGENCE SYSTEM"
- Phase statuses conflict (Phase 1 "IN PROGRESS" at the bottom vs Phase 8 "COMPLETE" at top)
- Tools described as "100% operational" but contain placeholder implementations
- Contains detailed implementation notes that belong in separate docs
- Mixes user-facing documentation with developer notes

---

## 7. Improvement Plan (Prioritized)

### Phase A: Critical Fixes (Week 1)

**Goal**: Address security issues and deployment blockers

| # | Task | Effort | Impact |
|---|------|--------|--------|
| A1 | Replace secrets in `.env.example` with placeholder values | 15 min | Critical security |
| A2 | Create `requirements.txt` from actual imports + pinned versions | 2 hrs | Deployment blocker |
| A3 | Create `pyproject.toml` for proper Python packaging | 2 hrs | Import stability |
| A4 | Sanitize all `HTTPException` details — remove `str(e)` patterns | 2 hrs | Information leakage |
| A5 | Remove `sys.path.append()` from `main.py`, fix imports via packaging | 1 hr | Import stability |

### Phase B: God File Decomposition (Weeks 2-3)

**Goal**: Reduce `main.py` from 10,703 lines to ~300 lines

| # | Task | Effort | Impact |
|---|------|--------|--------|
| B1 | Extract research/AI endpoints → `routers/research.py` | 4 hrs | ~2,000 lines moved |
| B2 | Extract scoring/promotion endpoints → merge into `routers/scoring.py` | 3 hrs | ~1,200 lines moved |
| B3 | Extract profile CRUD → merge into `routers/profiles_v2.py` | 3 hrs | ~1,500 lines moved |
| B4 | Extract dossier endpoints → `routers/dossier.py` | 2 hrs | ~800 lines moved |
| B5 | Extract visualization/chart endpoints → `routers/visualizations.py` | 2 hrs | ~600 lines moved |
| B6 | Extract documentation endpoints → `routers/docs.py` | 1 hr | ~400 lines moved |
| B7 | Move utility functions to `src/utils/` | 1 hr | ~300 lines moved |
| B8 | Consolidate WebSocket handlers into `routers/websocket.py` | 2 hrs | ~500 lines moved |
| B9 | Move inline config data to constants/config files | 1 hr | Cleaner separation |
| B10 | Final `main.py` cleanup — app factory pattern | 2 hrs | ~300 line target |

**Approach**: Extract one router at a time, test after each extraction, ensure no route conflicts.

### Phase C: Dead Code Removal (Week 3)

**Goal**: Remove ~24,000 lines of dead/legacy code

| # | Task | Effort | Impact |
|---|------|--------|--------|
| C1 | Remove `src/accessibility/` (0 imports, 1,825 lines) | 15 min | Dead code |
| C2 | Remove `src/data_migration/` (0 imports, 1,450 lines) | 15 min | Dead code |
| C3 | Remove `src/evaluation/` (0 imports, 2,753 lines) | 15 min | Dead code |
| C4 | Remove `src/monitoring/` (0 imports, 282 lines) | 15 min | Dead code |
| C5 | Remove `src/profiles/_deprecated/` | 15 min | Legacy cleanup |
| C6 | Consolidate router versions (remove v1 if v2 exists) | 4 hrs | API clarity |
| C7 | Remove or archive `src/processors/` if tools are authoritative | 4 hrs | Architecture clarity |
| C8 | Clean up `src/web/routers/ai_processing.py` (commented out) | 15 min | Cleanup |

### Phase D: Security Hardening (Week 4)

**Goal**: Production-grade security posture

| # | Task | Effort | Impact |
|---|------|--------|--------|
| D1 | Re-enable JWT auth on all endpoints (use `Depends(get_current_user_dependency)`) | 4 hrs | All endpoints unprotected |
| D2 | Fix static file serving — use `StaticFiles` middleware, remove custom handler | 1 hr | Path traversal fix |
| D3 | Add auth to WebSocket connections + subscription validation | 3 hrs | Info disclosure fix |
| D4 | Fix CORS — specify exact methods/headers, externalize to env vars | 1 hr | CORS hardening |
| D5 | Replace `unsafe-eval`/`unsafe-inline` with nonce-based CSP | 4 hrs | XSS protection |
| D6 | Add URL validation + size limits to PDF analysis endpoint | 2 hrs | SSRF prevention |
| D7 | Add batch size limits to all `/batch-*` endpoints | 2 hrs | DoS protection |
| D8 | Implement per-user/per-IP rate limiting with burst allowance | 3 hrs | Rate limit improvement |
| D9 | Remove test/debug endpoints from production code | 30 min | Attack surface reduction |
| D10 | Add structured logging (remove f-string logging patterns) | 4 hrs | Log injection prevention |

### Phase E: Testing & CI/CD (Weeks 5-6)

**Goal**: Automated quality gates and comprehensive coverage

| # | Task | Effort | Impact |
|---|------|--------|--------|
| E1 | Add tool-level test infrastructure for all 24 tools | 8 hrs | Coverage gap |
| E2 | Extend pytest coverage config to include `tools/` | 1 hr | Visibility |
| E3 | Create CI pipeline (GitHub Actions) with lint/test/security | 4 hrs | Automation |
| E4 | Add integration tests for key workflows | 8 hrs | Reliability |
| E5 | Triage and resolve 39 TODO/FIXME markers | 4 hrs | Debt cleanup |

### Phase F: Documentation & Developer Experience (Week 6)

**Goal**: Accurate, maintainable documentation

| # | Task | Effort | Impact |
|---|------|--------|--------|
| F1 | Rewrite `CLAUDE.md` — remove contradictions, reduce to essentials | 4 hrs | Developer clarity |
| F2 | Create `CONTRIBUTING.md` with setup instructions | 2 hrs | Onboarding |
| F3 | Add API documentation via OpenAPI/Swagger annotations | 4 hrs | API consumers |
| F4 | Document the tool ↔ processor migration status clearly | 2 hrs | Architecture clarity |

---

## Summary

### Top 5 Actions by Impact

1. **Decompose `main.py`** — This single change will improve maintainability, testability, code review efficiency, and developer onboarding more than anything else.

2. **Create `requirements.txt` + `pyproject.toml`** — Without these, the project cannot be reliably deployed or installed.

3. **Remove dead modules** — 6,310 lines of code that are never imported. Free reduction in cognitive load and repo size.

4. **Fix `.env.example` secrets** — If these are real or derived from real values, this is an active security vulnerability.

5. **Establish CI/CD** — No automated quality gates means every merge is a gamble. Even a basic lint + test pipeline would catch regressions.

### Metrics After Full Plan Execution

### Security Findings Summary

| Severity | Count | Key Themes |
|----------|-------|------------|
| Critical | 3 | Secrets in git, auth disabled on 164 endpoints, path traversal in static files |
| High | 5 | SQL injection, workflow path traversal, SSRF, exception leakage (212 occurrences), CORS |
| Medium | 8 | XSS middleware bypass, rate limiter gaps, CSP weak, no CSRF, in-memory auth, monolithic frontend |
| Low | 4 | SQLite durability, test endpoint, password policy, no requirements.txt |

### Metrics After Full Plan Execution

| Metric | Current | Target |
|--------|---------|--------|
| `main.py` lines | 10,703 | ~300 |
| `app.js` lines | 19,622 | Modular (<500 per file) |
| Dead/legacy code | ~1.3 MB | <100 KB |
| Total codebase lines | ~226,800 | ~180,000 |
| Production deps file | Missing | `pyproject.toml` |
| CI/CD pipeline | None | GitHub Actions |
| Test coverage (tools/) | Unmeasured | 60%+ |
| Security findings (Critical) | 3 | 0 |
| Security findings (High) | 5 | 0 |
| Router files with duplicates | 3 sets | 1 each |
| Tool placeholder TODOs | 7 | 0 |
| Deprecated endpoints past sunset | 20+ | 0 |
