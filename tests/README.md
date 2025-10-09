# Catalynx Test Suite

**Comprehensive test coverage for the Catalynx Grant Intelligence Platform**

**Last Updated**: October 9, 2025 (Phase 4 - Comprehensive Testing)
**Total Tests**: 250+ test functions
**Test Files**: 89 active test files
**Coverage Goal**: 70%+

---

## Test Organization

### 📊 Test Statistics

| Category | Files | Test Functions | Duration | Status |
|----------|-------|----------------|----------|--------|
| Unit | 8 | 119 | < 2 min | ✅ Active |
| Integration | 8 | 97 | 3-5 min | ✅ Active |
| E2E | 4 | 12 | 15-25 min | ✅ Active |
| Profiles | 5 | 36 | 2-3 min | ✅ Active |
| API | 1 | 8 | 1-2 min | ✅ Active |
| Performance | 4 | 15 | 5-10 min | ⚠️  Requires setup |
| Security | 1 | 8 | 1-2 min | ⚠️  Requires setup |
| **Total Active** | **31** | **295+** | **30-50 min** | - |
| Archived | 40 | ~120 | - | 📦 Pre-transformation |

---

## Test Directory Structure

```
tests/
├── unit/                    # Component tests (119 tests) ✅
│   ├── test_api_endpoints.py
│   ├── test_data_models.py
│   ├── test_discovery_scorer.py
│   ├── test_entity_cache.py
│   └── ... (8 files)
│
├── integration/            # Multi-component tests (97 tests) ✅
│   ├── test_api_clients.py
│   ├── test_database_integration.py
│   ├── test_processor_workflow_integration.py
│   ├── test_web_api_integration.py
│   └── ... (8 files)
│
├── e2e/                   # End-to-end workflows (12 tests) ✅
│   ├── test_nonprofit_discovery_e2e.py
│   ├── test_grant_research_e2e.py
│   ├── test_foundation_intelligence_e2e.py
│   └── test_complete_platform_e2e.py
│
├── profiles/              # Profile workflows (36 tests) ✅
│   ├── test_discovery_workflow.py
│   ├── test_orchestration.py
│   ├── test_unified_service.py
│   └── ... (5 files)
│
├── api/                   # REST API tests (8 tests) ✅
│   └── test_profiles_v2_api.py
│
├── functional/            # Feature tests ⚠️
│   └── test_discovery_engine.py
│
├── intelligence/          # Data pipeline tests ⚠️
│   └── test_990_pipeline.py
│
├── performance/           # Load & stress tests ⚠️
│   ├── locustfile.py
│   ├── test_load_performance.py
│   └── ... (4 files)
│
├── security/             # Security validation ⚠️
│   └── security_test_suite.py
│
├── integrated/           # Cross-system tests ⚠️
│   └── ... (7 files)
│
├── archive/              # Historical tests 📦
│   ├── pre_transformation/
│   │   ├── legacy_tests/          (40 files)
│   │   └── deprecated_processor_tests/
│   └── README.md
│
├── fixtures/             # Shared test data
│   └── database_fixtures.py
│
├── conftest.py           # Pytest configuration
├── test_tools_api.py     # Comprehensive tool API tests (8 tests)
├── test_foundation_network_graph.py
└── README.md             # This file
```

---

## Core Test Categories

### 1. Unit Tests (`tests/unit/`) ✅

**Purpose**: Test individual components in complete isolation

**Coverage**: ~119 test functions across 8 files

**Key Test Files**:
- `test_http_client.py` - HTTP client abstraction layer
- `test_data_models.py` - Data models and Pydantic validation
- `test_api_endpoints.py` - Individual API endpoint handlers
- `test_discovery_scorer.py` - Scoring algorithm logic
- `test_entity_cache.py` - Entity caching mechanisms
- `test_entity_cache_manager.py` - Cache management
- `test_processor_registry.py` - Tool/processor registration
- `test_dashboard_router.py` - Dashboard routing logic

**Run Commands**:
```bash
# All unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=src --cov-report=term

# Specific test file
pytest tests/unit/test_data_models.py -v
```

**Expected Duration**: < 2 minutes
**Dependencies**: None (all mocked)

---

### 2. Integration Tests (`tests/integration/`) ✅

**Purpose**: Test interaction between multiple components

**Coverage**: ~97 test functions across 8 files

**Key Test Files**:
- `test_api_clients.py` - API client integration with HTTP layer
- `test_database_integration.py` - Database operations and queries
- `test_processor_workflow_integration.py` - Multi-tool workflows
- `test_web_api_integration.py` - Web API endpoint integration
- `test_websocket_integration.py` - Real-time WebSocket functionality
- `test_workflow_integration.py` - Workflow orchestration
- `test_api_gui_binding.py` - Frontend-backend integration
- `test_api_performance.py` - API response time validation

**Run Commands**:
```bash
# All integration tests
pytest tests/integration/ -v

# Exclude slow tests
pytest tests/integration/ -m "not slow" -v

# With database
pytest tests/integration/ --db-test -v
```

**Expected Duration**: 3-5 minutes
**Dependencies**: Database, some API mocking

---

### 3. End-to-End (E2E) Tests (`tests/e2e/`) ✅

**Purpose**: Validate complete user journeys through the system

**Coverage**: ~12 test functions across 4 workflow files

**Key Test Files**:
- `test_nonprofit_discovery_e2e.py` - Complete discovery pipeline (8 tools)
- `test_grant_research_e2e.py` - Two-tool AI pipeline workflow
- `test_foundation_intelligence_e2e.py` - Multi-foundation analysis
- `test_complete_platform_e2e.py` - Full platform integration (15+ tools)

**Run Commands**:
```bash
# All E2E tests
pytest tests/e2e/ -v --tb=short

# Specific workflow
pytest tests/e2e/test_nonprofit_discovery_e2e.py -v

# With timeout (5 min per test)
pytest tests/e2e/ --timeout=300 -v
```

**Expected Duration**: 15-25 minutes
**Dependencies**: Web server, database, real test data

**See**: `tests/e2e/README.md` for detailed workflow documentation

---

### 4. Profile Tests (`tests/profiles/`) ✅

**Purpose**: Test nonprofit profile management and discovery workflows

**Coverage**: ~36 test functions across 5 files

**Key Test Files**:
- `test_unified_service.py` - UnifiedProfileService without locking
- `test_discovery_workflow.py` - Complete discovery session lifecycle
- `test_orchestration.py` - Multi-tool orchestration
- `test_quality_scoring.py` - Profile data quality assessment
- `test_profile_suite.py` - Comprehensive profile operations

**Run Commands**:
```bash
# All profile tests
pytest tests/profiles/ -v

# Unified service tests only
pytest tests/profiles/test_unified_service.py -v
```

**Expected Duration**: 2-3 minutes
**Dependencies**: Database, profile test data

---

### 5. API Tests (`tests/api/`, `tests/test_tools_api.py`) ✅

**Purpose**: Validate REST API endpoints for tools and profiles

**Coverage**: ~16 test functions across 2 files

**Key Test Files**:
- `test_tools_api.py` - Comprehensive tool execution API (22+ tools)
- `api/test_profiles_v2_api.py` - Profile v2 API endpoints

**Run Commands**:
```bash
# Tool API tests
pytest tests/test_tools_api.py -v

# Profile API tests
pytest tests/api/test_profiles_v2_api.py -v
```

**Expected Duration**: 1-2 minutes
**Dependencies**: Web server running

---

### 6. Performance Tests (`tests/performance/`) ⚠️

**Purpose**: Load testing, stress testing, and performance benchmarks

**Coverage**: ~15 test functions across 4 files

**Key Test Files**:
- `locustfile.py` - Locust load testing configuration
- `test_load_performance.py` - Concurrent user simulation
- `test_performance_regression.py` - Performance baseline tracking
- `test_system_performance.py` - System-wide performance metrics

**Run Commands**:
```bash
# Performance benchmarks
pytest tests/performance/ -v

# Locust load test (requires Locust installed)
locust -f tests/performance/locustfile.py
```

**Expected Duration**: 5-10 minutes
**Dependencies**: Locust, production-like environment

---

### 7. Archived Tests (`tests/archive/`) 📦

**Purpose**: Historical tests from pre-transformation architecture

**Contents**:
- `pre_transformation/legacy_tests/` - 40 pre-12-factor tests
- `pre_transformation/deprecated_processor_tests/` - Old processor tests

**Status**: ❌ **NOT MAINTAINED** - Preserved for reference only

**See**: `tests/archive/README.md` for archival information

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Ensure all environment variables are set for testing
export CATALYNX_ENV=test
```

### Run All Tests
```bash
# From project root
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Functional tests only
pytest tests/functional/
```

### Run Individual Test Files
```bash
pytest tests/unit/test_http_client.py -v
pytest tests/functional/test_discovery_engine.py::TestUnifiedDiscoveryEngine -v
```

## Test Configuration

### Fixtures
Common test fixtures are defined in `conftest.py`:
- `sample_organization_profile` - Standard test organization
- `sample_government_opportunity` - Test opportunity data
- `mock_api_response` - Generic API response structure
- `http_client` - Configured HTTP client for testing

### Environment Variables
Test environment variables are automatically mocked:
- `CATALYNX_ENV=test`
- `API_KEY_*` - Mocked API keys for all services

### Mocking Strategy
- External API calls are mocked at the HTTP client level
- Database operations use in-memory or temporary storage
- File system operations use temporary directories

## Test Data

### Sample Data
Test data is generated dynamically using fixtures to ensure:
- Consistent test scenarios
- Realistic data structures
- Edge case coverage

### Mock Responses
API response mocks are based on actual API documentation and real responses, ensuring:
- Accurate field mapping
- Proper error condition testing
- Schema validation

## Coverage Goals

Target test coverage by component:
- Core modules (data models, HTTP client): 95%+
- API clients: 85%+
- Discovery engine: 90%+
- Web interface: 80%+
- Processors: 85%+

## Test Performance

### Async Testing
All async functionality is properly tested using:
- `pytest-asyncio` for async test execution
- Proper event loop management
- Async context manager testing

### Parallel Execution
Tests can be run in parallel using `pytest-xdist`:
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

## Continuous Integration

### GitHub Actions
Tests run automatically on:
- Pull requests
- Main branch commits
- Release tags

### Test Matrix
Tests run against:
- Python 3.8, 3.9, 3.10, 3.11
- Multiple operating systems (Ubuntu, Windows, macOS)

## Contributing Tests

### Writing New Tests
1. Follow the existing naming convention (`test_*.py`)
2. Use descriptive test method names
3. Include docstrings for complex test scenarios
4. Mock external dependencies appropriately
5. Test both success and failure scenarios

### Test Organization Guidelines
- Unit tests: Single component, no external dependencies
- Integration tests: Multiple components, mocked external services
- Functional tests: Complete workflows, may include real service calls in development

### Best Practices
- Use fixtures for common test data
- Keep tests independent and idempotent
- Test edge cases and error conditions
- Maintain test performance (avoid unnecessary delays)
- Update tests when refactoring code