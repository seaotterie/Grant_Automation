# Catalynx Test Suite

Comprehensive test coverage for the Catalynx Grant Research Automation platform.

## Test Organization

### Unit Tests (`tests/unit/`)
Tests individual components in isolation:
- `test_http_client.py` - HTTP client abstraction layer
- `test_data_models.py` - Data models and validation
- `test_base_processor.py` - Base processor functionality
- `test_api_clients.py` - Individual API client classes

### Integration Tests (`tests/integration/`)
Tests interaction between components:
- `test_api_clients.py` - API client integration with HTTP layer
- `test_processor_integration.py` - Processor workflow integration
- `test_discovery_integration.py` - Discovery engine component interaction

### Functional Tests (`tests/functional/`)
Tests complete workflows and user scenarios:
- `test_discovery_engine.py` - End-to-end discovery workflows
- `test_web_interface.py` - Web API functionality
- `test_full_pipeline.py` - Complete grant research pipeline

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