# Modernized Testing Harness - 12-Factor Tools

**Created**: 2025-10-09
**Status**: Phase 3 Complete - Testing Infrastructure Modernized

---

## Overview

Comprehensive testing framework for 30 12-factor compliant components:
- **24 Tools** in `tools/` directory
- **6 Scoring Modules** in `src/scoring/`

---

## Directory Structure

```
test_framework/
├── 12factor_tools/          # Tool-level tests (24 tools)
│   ├── test_tool_template.py                    # Template for new tool tests
│   ├── test_bmf_filter_tool.py                  # Example: BMF Filter Tool
│   ├── test_opportunity_screening_tool.py       # Example: Opportunity Screening
│   └── ...                                       # 22 more tool tests
│
├── scoring_systems/         # Scoring module tests (6 modules)
│   ├── test_scoring_template.py                 # Template for new scorer tests
│   ├── test_ntee_scorer.py                      # NTEE Two-Part Scoring
│   ├── test_schedule_i_voting.py                # Schedule I Voting
│   ├── test_grant_size_scoring.py               # Grant Size Realism Bands
│   ├── test_composite_scorer_v2.py              # Composite Scorer V2
│   ├── test_triage_queue.py                     # Triage Queue
│   └── test_reliability_safeguards.py           # Reliability Safeguards
│
├── network_intelligence/    # Network analysis tests
│   ├── test_network_template.py                 # Template for network tests
│   ├── test_network_intelligence_tool.py        # Board network analysis
│   ├── test_foundation_grantee_bundling.py      # Multi-foundation bundling
│   ├── test_cofunding_analyzer.py               # Co-funding analysis
│   └── test_schedule_i_analyzer.py              # Schedule I patterns
│
├── api_integration/         # REST API endpoint tests
│   ├── test_api_template.py                     # Template for API tests
│   ├── test_tools_api.py                        # /api/v1/tools/* endpoints
│   ├── test_profiles_api.py                     # /api/profiles/* endpoints
│   ├── test_workflows_api.py                    # /api/workflows/* endpoints
│   └── test_foundation_network_api.py           # /api/foundation-network/* endpoints
│
├── deprecated_tests/        # Legacy tests (moved from essential_tests/)
│   ├── test_processor_suite.py
│   ├── test_ai_processors.py
│   ├── test_intelligence_tiers.py
│   └── ...
│
├── fixtures/                # Shared test fixtures
├── README_MODERNIZED_TESTING.md  # This file
└── ...                      # Legacy files (to be cleaned up in Phase 5)
```

---

## Test Templates

### 1. Tool Test Template (`12factor_tools/test_tool_template.py`)

**Purpose**: Template for testing 12-factor compliant tools

**Test Categories**:
- **TestToolCompliance**: 12-factor compliance checks
  - Factor 4: Structured outputs (BAML validation)
  - Factor 6: Stateless execution
  - Factor 10: Single responsibility
  - Configuration file existence (`12factors.toml`)

- **TestToolFunctionality**: Core functionality tests
  - Basic execution
  - Output structure validation
  - Invalid input handling
  - Performance benchmarks

- **TestToolIntegration**: System integration tests
  - Import validation
  - Tool registry registration
  - API availability (if applicable)

- **TestToolBAMLValidation**: BAML schema validation
  - Schema existence verification
  - Output validation against BAML schemas

**Usage**:
```bash
# Copy template
cp test_tool_template.py test_my_tool.py

# Update configuration
TOOL_NAME = "my-tool"
TOOL_MODULE_PATH = "tools.my_tool.app.my_tool"
TOOL_CLASS_NAME = "MyTool"

# Run tests
pytest test_framework/12factor_tools/test_my_tool.py -v
```

---

### 2. Scoring System Template (`scoring_systems/test_scoring_template.py`)

**Purpose**: Template for testing foundation scoring modules

**Test Categories**:
- **TestScorerCompliance**: 12-factor compliance for scorers
- **TestScorerFunctionality**: Core scoring functionality
- **TestScorerBAMLIntegration**: BAML schema integration
- **TestScorerEdgeCases**: Edge cases and boundary conditions
- **TestScorerAccuracy**: Accuracy validation with known cases

**BAML Types Covered**:
- **NTEE Scoring**: `NTEEScoreResult`, `NTEECode`, `NTEEDataSource`, `NTEEMatchLevel`
- **Schedule I Voting**: `ScheduleIAnalysis`, `RecipientVote`, `NTEEVoteResult`
- **Grant Size**: `GrantSizeAnalysis`, `GrantSizeBand`, `CapacityLevel`, `GrantSizeFit`
- **Composite**: `CompositeScoreResult`, `FoundationOpportunityData`
- **Triage**: `TriageItem`, `TriageQueueStats`, `TriageStatus`, `TriagePriority`
- **Reliability**: `ReliabilitySafeguardsResult`, `FilingRecencyAnalysis`, etc.

**Usage**:
```bash
# Run all scoring tests
pytest test_framework/scoring_systems/ -v

# Run specific scorer
pytest test_framework/scoring_systems/test_ntee_scorer.py -v
```

---

### 3. Network Intelligence Template (`network_intelligence/test_network_template.py`)

**Purpose**: Template for testing network analysis and foundation intelligence

**Test Categories**:
- **TestNetworkToolCompliance**: NetworkX dependency, structured graph outputs
- **TestNetworkToolFunctionality**: Network construction, metrics, pathways
- **TestFoundationNetworkSpecific**: Foundation-specific analysis
- **TestCoFundingAnalysis**: Co-funding similarity and recommendations
- **TestNetworkPerformance**: Large network performance
- **TestNetworkOutputStructure**: BAML output validation

**BAML Types Covered**:
- **Bundling**: `GranteeBundlingOutput`, `BundledGrantee`, `FoundationOverlap`, `ThematicCluster`
- **Co-funding**: `CoFundingAnalysisOutput`, `FunderSimilarity`, `PeerFunderGroup`, `FunderRecommendation`
- **Enums**: `FundingStability`, `RecommendationType`

**Usage**:
```bash
# Run all network tests
pytest test_framework/network_intelligence/ -v

# Run specific network tool
pytest test_framework/network_intelligence/test_foundation_grantee_bundling.py -v
```

---

### 4. API Integration Template (`api_integration/test_api_template.py`)

**Purpose**: Template for testing REST API endpoints

**Test Categories**:
- **TestAPIAvailability**: Server health and OpenAPI spec
- **TestAPIEndpoints**: CRUD endpoints (list, get, create, execute)
- **TestAPIValidation**: Input validation and error handling
- **TestAPIPerformance**: Response time and concurrent requests
- **TestAPIErrorHandling**: 404, 405, 500 error responses
- **TestAPIResponseStructure**: Consistent response formats

**API Categories**:
- **Tool Execution**: `/api/v1/tools/*` (24 tools)
- **Profiles**: `/api/profiles/*` (nonprofit profiles)
- **Workflows**: `/api/workflows/*` (orchestration)
- **Foundation Network**: `/api/foundation-network/*` (16 endpoints)

**Usage**:
```bash
# Start server first
launch_catalynx_web.bat

# Run API tests (in separate terminal)
pytest test_framework/api_integration/ -v

# Run specific API category
pytest test_framework/api_integration/test_tools_api.py -v
```

---

## Test Execution

### Run All Tests
```bash
pytest test_framework/ -v
```

### Run by Category
```bash
# Tool tests only
pytest test_framework/12factor_tools/ -v

# Scoring tests only
pytest test_framework/scoring_systems/ -v

# Network tests only
pytest test_framework/network_intelligence/ -v

# API tests only (requires running server)
pytest test_framework/api_integration/ -v
```

### Run with Markers
```bash
# Skip slow tests
pytest test_framework/ -m "not slow" -v

# Run integration tests only
pytest test_framework/ -m "integration" -v

# Run accuracy tests only
pytest test_framework/scoring_systems/ -m "accuracy" -v
```

### Performance Testing
```bash
# Run performance benchmarks
pytest test_framework/ -m "performance" -v

# Run with duration reporting
pytest test_framework/ --durations=10
```

---

## BAML Integration

All test templates include BAML validation support:

### Import BAML Types
```python
from baml_client.types import (
    # Scoring types
    NTEEScoreResult,
    CompositeScoreResult,
    GrantSizeAnalysis,

    # Network types
    GranteeBundlingOutput,
    CoFundingAnalysisOutput,

    # Triage types
    TriageItem,
    TriageQueueStats,
)
```

### Validate Outputs
```python
def test_output_validates_against_baml(self):
    result = tool.execute(input_data)

    # Type checking
    assert isinstance(result, ExpectedBAMLType)

    # Field validation
    for field in ExpectedBAMLType.__annotations__:
        assert hasattr(result, field)
```

---

## 12-Factor Compliance Testing

Each test template validates 12-factor compliance:

### Core Factors (Enforced)
- **Factor 4**: Tools as Structured Outputs (BAML validation)
- **Factor 6**: Stateless execution (no state between runs)
- **Factor 10**: Single responsibility (focused purpose)

### Supporting Factors (Verified)
- **Factor 1**: Codebase tracked in Git
- **Factor 2**: Dependencies declared (`requirements.txt`)
- **Factor 3**: Configuration in environment (`.env`, `12factors.toml`)
- **Factor 12**: API-first design (REST endpoints)

---

## Migration from Legacy Tests

### Essential Tests → Deprecated
```bash
# Move legacy tests
test_framework/essential_tests/* → test_framework/deprecated_tests/
```

### Legacy Test Files
- `test_processor_suite.py` → Replaced by tool tests
- `test_ai_processors.py` → Replaced by AI tool tests
- `test_intelligence_tiers.py` → Replaced by depth tests
- `test_modal_system.py` → Deprecated

---

## Next Steps (Phase 4: Comprehensive Testing)

### Create Concrete Tests (30+ test files)
1. **Tool Tests** (24 files)
   - `test_bmf_filter_tool.py`
   - `test_opportunity_screening_tool.py`
   - `test_deep_intelligence_tool.py`
   - ... (21 more)

2. **Scoring Tests** (6 files)
   - `test_ntee_scorer.py`
   - `test_schedule_i_voting.py`
   - `test_grant_size_scoring.py`
   - `test_composite_scorer_v2.py`
   - `test_triage_queue.py`
   - `test_reliability_safeguards.py`

3. **Network Tests** (4 files)
   - `test_network_intelligence_tool.py`
   - `test_foundation_grantee_bundling.py`
   - `test_cofunding_analyzer.py`
   - `test_schedule_i_analyzer.py`

4. **API Tests** (4 files)
   - `test_tools_api.py`
   - `test_profiles_api.py`
   - `test_workflows_api.py`
   - `test_foundation_network_api.py`

### Run Comprehensive Testing
```bash
# Execute all 38+ test files
pytest test_framework/ -v --cov=src --cov=tools

# Generate coverage report
pytest test_framework/ --cov-report=html
```

---

## Documentation

- **Templates**: All templates include detailed docstrings and usage examples
- **Markers**: Pytest markers for test organization (`slow`, `integration`, `accuracy`, etc.)
- **Coverage**: Code coverage tracking with pytest-cov
- **CI/CD**: Ready for integration with GitHub Actions

---

## Summary

✅ **Phase 3 Complete**: Testing infrastructure modernized
- 4 comprehensive test templates created
- 4 test categories organized
- BAML validation integrated
- 12-factor compliance checks included
- Legacy tests segregated

**Ready for Phase 4**: Comprehensive testing with 38+ concrete test files

---

**Next**: Create concrete tests for all 30 12-factor components (Phase 4)
