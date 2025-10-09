# End-to-End (E2E) Test Suite

Complete workflow tests validating full user journeys through the Catalynx Grant Intelligence Platform.

## E2E Test Workflows

### 1. Nonprofit Discovery Workflow
**File**: `test_nonprofit_discovery_e2e.py`

**Journey**:
```
Profile Creation → BMF Discovery → Financial Scoring →
Network Analysis → Risk Assessment → Report Generation
```

**Tests**:
- Complete discovery pipeline execution
- Data flow between components
- Multi-tool orchestration
- Final report accuracy

---

### 2. Grant Research Workflow
**File**: `test_grant_research_e2e.py`

**Journey**:
```
Opportunity Screening (200 opps) → Human Review Gateway →
Deep Intelligence (10 selected) → Package Generation
```

**Tests**:
- Two-tool AI pipeline
- Mass screening → detailed analysis
- Cost tracking accuracy
- Package assembly

---

### 3. Foundation Intelligence Workflow
**File**: `test_foundation_intelligence_e2e.py`

**Journey**:
```
990-PF XML Parsing → Schedule I Analysis →
Foundation Grant Intelligence → Grantee Bundling → Co-Funding Analysis
```

**Tests**:
- Multi-foundation analysis
- Network graph construction
- Grant-making pattern detection
- Recommendation generation

---

### 4. Complete Platform Workflow
**File**: `test_complete_platform_e2e.py`

**Journey**:
```
Profile Creation → Multi-Track Discovery →
Multi-Dimensional Scoring → Triage Queue →
Deep Analysis → Risk Assessment →
Historical Patterns → Final Reporting
```

**Tests**:
- Full platform capabilities
- All 24 tools integration
- Performance under load
- Data consistency

---

## Running E2E Tests

### Prerequisites
```bash
# Start web server (if testing API endpoints)
launch_catalynx_web.bat

# Ensure test data is available
python test_framework/test_all_profiles.py --setup
```

### Execute Tests
```bash
# All E2E tests
pytest tests/e2e/ -v --tb=short

# Specific workflow
pytest tests/e2e/test_nonprofit_discovery_e2e.py -v

# With detailed output
pytest tests/e2e/ -v -s
```

### Performance Testing
```bash
# Run with duration tracking
pytest tests/e2e/ --durations=10

# Run with timeout (max 5 minutes per test)
pytest tests/e2e/ --timeout=300
```

## Test Data

E2E tests use real test profiles:
- `profile_f3adef3b653c` - Heroes Bridge (Veteran Services)
- `profile_aefa1d788b1e` - Fauquier Free Clinic (Healthcare)
- `profile_b3db970a10ff` - Ford Foundation (Large Foundation)

## Expected Duration

| Workflow | Duration | Tools Used |
|----------|----------|------------|
| Nonprofit Discovery | 2-5 min | 8-10 tools |
| Grant Research | 3-7 min | 2-4 tools |
| Foundation Intelligence | 1-3 min | 5-6 tools |
| Complete Platform | 5-10 min | 15+ tools |

**Total E2E Suite**: ~15-25 minutes

## Success Criteria

- ✅ All workflow steps complete successfully
- ✅ Data flows correctly between components
- ✅ Final outputs match expected structure
- ✅ Performance within acceptable limits
- ✅ No data loss or corruption
- ✅ Error handling works correctly

## Troubleshooting

### Common Issues

1. **Timeout Errors**
   - Increase pytest timeout: `--timeout=600`
   - Check server is running
   - Verify API connectivity

2. **Data Not Found**
   - Run test data setup
   - Check database connectivity
   - Verify profile IDs exist

3. **Tool Execution Failures**
   - Check tool registry status
   - Verify 12factors.toml files
   - Review tool logs

## Notes

- E2E tests may make real API calls (depending on configuration)
- Tests should be idempotent (can run multiple times)
- Clean up test data after execution
- Monitor resource usage (memory, CPU)
