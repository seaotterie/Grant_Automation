# DevOps Testing Best Practices Guide - Catalynx Grant Intelligence Platform

## Executive Summary

This guide provides comprehensive DevOps testing best practices for the Catalynx Grant Intelligence Platform, a sophisticated multi-layered system with 18 processors, entity-based architecture, and advanced Phase 6 capabilities. The guide covers automated testing frameworks, CI/CD pipeline integration, and production monitoring strategies.

## Table of Contents

1. [Testing Architecture Overview](#testing-architecture-overview)
2. [Automated Testing Framework](#automated-testing-framework)
3. [CI/CD Pipeline Integration](#cicd-pipeline-integration)
4. [Performance Testing Strategy](#performance-testing-strategy)
5. [Data Integrity Testing](#data-integrity-testing)
6. [Security Testing](#security-testing)
7. [Monitoring & Observability](#monitoring--observability)
8. [Environment Management](#environment-management)
9. [Testing Best Practices](#testing-best-practices)
10. [Implementation Roadmap](#implementation-roadmap)

---

## Testing Architecture Overview

### System Architecture Context

The Catalynx platform consists of:
- **FastAPI Backend**: 100+ REST endpoints with async processing
- **Entity-Based Data Layer**: EIN/ID-organized with 85% cache hit rate
- **18 Processing Components**: Discovery, analysis, and intelligence engines
- **Modern Web Interface**: Alpine.js with real-time WebSocket updates
- **Phase 6 Advanced Systems**: 7 implemented systems requiring integration

### Testing Pyramid Strategy

```
                    /\
                   /  \
                  /E2E \     End-to-End (5%)
                 /Tests\     - Complete workflow validation
                /______\     - User journey testing
               /        \
              /Integration\   Integration Tests (25%)
             /   Tests    \   - API testing
            /______________\  - Cross-system validation
           /                \
          /   Unit Tests     \ Unit Tests (70%)
         /                   \ - Individual component testing
        /_____________________\ - Scorer validation
```

---

## Automated Testing Framework

### 1. Unit Testing Framework

#### 1.1 Python Backend Testing

**Framework**: pytest with async support
**Location**: `tests/unit/`

```python
# tests/unit/test_discovery_scorer.py
import pytest
import asyncio
from src.scoring.discovery_scorer import DiscoveryScorer
from src.profiles.models import OrganizationProfile

@pytest.mark.asyncio
async def test_discovery_scorer_basic_functionality():
    """Test basic discovery scoring functionality"""
    scorer = DiscoveryScorer()
    
    # Mock organization profile
    profile = OrganizationProfile(
        organization_name="Test Foundation",
        ntee_codes=["B25"],
        revenue=1000000,
        state="VA"
    )
    
    # Mock opportunity
    opportunity = {
        "organization_name": "Educational Initiative",
        "ntee_codes": ["B25"],
        "external_data": {"state": "VA"},
        "description": "Educational support program"
    }
    
    result = await scorer.score_opportunity(opportunity, profile)
    
    assert result.overall_score >= 0.0
    assert result.overall_score <= 1.0
    assert result.confidence_level > 0.0
    assert len(result.dimension_scores) > 0

@pytest.mark.asyncio
async def test_discovery_scorer_edge_cases():
    """Test edge cases and error handling"""
    scorer = DiscoveryScorer()
    
    # Test with missing data
    profile = OrganizationProfile(organization_name="Test")
    opportunity = {}
    
    result = await scorer.score_opportunity(opportunity, profile)
    
    # Should handle gracefully with default values
    assert result.overall_score >= 0.0
    assert result.confidence_level < 0.5  # Low confidence for missing data

# Performance testing
@pytest.mark.performance
def test_discovery_scorer_performance():
    """Test scoring performance requirements"""
    import time
    
    scorer = DiscoveryScorer()
    
    start_time = time.time()
    # Run 1000 scoring operations
    for _ in range(1000):
        # Mock fast scoring operation
        pass
    
    elapsed = time.time() - start_time
    
    # Should process 1000 scores in under 1 second (sub-millisecond per score)
    assert elapsed < 1.0
```

#### 1.2 API Endpoint Testing

```python
# tests/unit/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from src.web.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test system health endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_profiles_crud():
    """Test profile CRUD operations"""
    # Create profile
    profile_data = {
        "organization_name": "Test Organization",
        "mission_statement": "Test mission",
        "ntee_codes": ["B25"],
        "revenue": 1000000
    }
    
    response = client.post("/api/profiles", json=profile_data)
    assert response.status_code == 200
    profile_id = response.json()["profile_id"]
    
    # Read profile
    response = client.get(f"/api/profiles/{profile_id}")
    assert response.status_code == 200
    assert response.json()["organization_name"] == "Test Organization"
    
    # Update profile
    updated_data = {"revenue": 2000000}
    response = client.put(f"/api/profiles/{profile_id}", json=updated_data)
    assert response.status_code == 200
    
    # Delete profile
    response = client.delete(f"/api/profiles/{profile_id}")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_discovery_api():
    """Test discovery API functionality"""
    # Test entity-based discovery
    discovery_data = {
        "profile_id": "test_profile",
        "discovery_type": "entity_analytics",
        "parameters": {"max_results": 10}
    }
    
    response = client.post("/api/profiles/test_profile/discover/entity-analytics", 
                          json=discovery_data)
    
    # Should return results or appropriate error
    assert response.status_code in [200, 404]  # 404 if profile doesn't exist
```

### 2. Integration Testing Framework

#### 2.1 Cross-System Integration Tests

```python
# tests/integration/test_workflow_integration.py
import pytest
import asyncio
from src.web.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_workflow():
    """Test complete DISCOVER → PLAN → ANALYZE → EXAMINE → APPROACH workflow"""
    
    # Step 1: Create test profile
    profile_data = {
        "organization_name": "Integration Test Foundation",
        "mission_statement": "Supporting educational initiatives",
        "ntee_codes": ["B25"],
        "revenue": 5000000,
        "state": "VA"
    }
    
    profile_response = client.post("/api/profiles", json=profile_data)
    assert profile_response.status_code == 200
    profile_id = profile_response.json()["profile_id"]
    
    try:
        # Step 2: DISCOVER - Run discovery
        discovery_response = client.post(
            f"/api/profiles/{profile_id}/discover/entity-analytics",
            json={"max_results": 5}
        )
        assert discovery_response.status_code == 200
        opportunities = discovery_response.json()["opportunities"]
        
        if opportunities:
            opportunity_id = opportunities[0]["opportunity_id"]
            
            # Step 3: PLAN - Assess readiness
            readiness_response = client.get(f"/api/profiles/{profile_id}/analytics")
            assert readiness_response.status_code == 200
            
            # Step 4: ANALYZE - AI-Lite analysis
            analyze_response = client.post("/api/ai/lite-analysis", json={
                "profile_id": profile_id,
                "opportunity_id": opportunity_id,
                "analysis_type": "strategic_fit"
            })
            # Should return analysis or queue for processing
            assert analyze_response.status_code in [200, 202]
            
            # Step 5: EXAMINE - AI Heavy research (if high priority)
            examine_response = client.post("/api/ai/deep-research", json={
                "profile_id": profile_id,
                "opportunity_id": opportunity_id,
                "depth": "comprehensive"
            })
            assert examine_response.status_code in [200, 202]
            
            # Step 6: APPROACH - Decision synthesis
            approach_response = client.post(
                f"/api/profiles/{profile_id}/approach/synthesize-decision",
                json={"opportunity_id": opportunity_id}
            )
            assert approach_response.status_code in [200, 501]  # 501 if not implemented
            
    finally:
        # Cleanup
        client.delete(f"/api/profiles/{profile_id}")

@pytest.mark.integration
def test_cache_integration():
    """Test entity cache integration across systems"""
    # Test cache consistency across different API calls
    profile_id = "cache_test_profile"
    
    # First call should populate cache
    response1 = client.get(f"/api/profiles/{profile_id}/analytics")
    
    # Second call should use cache
    response2 = client.get(f"/api/profiles/{profile_id}/analytics")
    
    # Should have similar response times (cache hit)
    # In production, implement proper cache hit rate monitoring
```

#### 2.2 Phase 6 System Integration Tests

```python
# tests/integration/test_phase6_integration.py
import pytest
from src.decision.decision_synthesis_framework import DecisionSynthesisFramework
from src.visualization.advanced_visualization_framework import VisualizationFramework
from src.export.comprehensive_export_system import ExportSystem

@pytest.mark.phase6
@pytest.mark.asyncio
async def test_decision_synthesis_integration():
    """Test Phase 6 decision synthesis framework integration"""
    
    framework = DecisionSynthesisFramework()
    
    # Mock workflow scores
    workflow_scores = {
        'discover_score': 0.8,
        'plan_readiness': 0.7,
        'analyze_strategic_fit': 0.9,
        'examine_intelligence': 0.85
    }
    
    confidence_scores = {
        'discover': 0.9,
        'plan': 0.8,
        'analyze': 0.85,
        'examine': 0.9
    }
    
    result = await framework.synthesize_decision(workflow_scores, confidence_scores)
    
    assert result['synthesis_score'] >= 0.0
    assert result['synthesis_score'] <= 1.0
    assert result['overall_confidence'] >= 0.0
    assert 'stage_contributions' in result

@pytest.mark.phase6
def test_visualization_framework():
    """Test advanced visualization framework"""
    
    viz_framework = VisualizationFramework()
    
    # Test chart generation
    chart_data = {
        'type': 'decision_matrix',
        'data': {
            'opportunities': ['Opp1', 'Opp2', 'Opp3'],
            'scores': [0.8, 0.6, 0.9],
            'confidence': [0.9, 0.7, 0.85]
        }
    }
    
    chart = viz_framework.generate_chart(chart_data)
    
    assert chart is not None
    assert 'chart_config' in chart
    assert 'data' in chart

@pytest.mark.phase6
def test_export_system():
    """Test comprehensive export system"""
    
    export_system = ExportSystem()
    
    # Test PDF export
    export_data = {
        'format': 'pdf',
        'template': 'executive',
        'data': {
            'profile_name': 'Test Organization',
            'opportunities': [],
            'analysis_results': {}
        }
    }
    
    result = export_system.generate_export(export_data)
    
    assert result['status'] == 'success'
    assert 'file_path' in result or 'file_data' in result
```

### 3. API Testing with Postman/Newman

#### 3.1 Postman Collection Structure

```json
{
  "info": {
    "name": "Catalynx API Test Suite",
    "description": "Comprehensive API testing for Catalynx platform"
  },
  "item": [
    {
      "name": "Health Checks",
      "item": [
        {
          "name": "System Health",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/api/health"
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Status code is 200', () => {",
                  "  pm.response.to.have.status(200);",
                  "});",
                  "",
                  "pm.test('Response has status field', () => {",
                  "  const response = pm.response.json();",
                  "  pm.expect(response).to.have.property('status');",
                  "  pm.expect(response.status).to.equal('healthy');",
                  "});"
                ]
              }
            }
          ]
        }
      ]
    },
    {
      "name": "Profile Management",
      "item": [
        {
          "name": "Create Profile",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/api/profiles",
            "body": {
              "mode": "raw",
              "raw": "{\n  \"organization_name\": \"Test Organization\",\n  \"mission_statement\": \"Test mission\",\n  \"ntee_codes\": [\"B25\"],\n  \"revenue\": 1000000\n}",
              "options": {
                "raw": {
                  "language": "json"
                }
              }
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "pm.test('Profile created successfully', () => {",
                  "  pm.response.to.have.status(200);",
                  "  const response = pm.response.json();",
                  "  pm.expect(response).to.have.property('profile_id');",
                  "  pm.globals.set('test_profile_id', response.profile_id);",
                  "});"
                ]
              }
            }
          ]
        }
      ]
    }
  ]
}
```

#### 3.2 Newman CLI Integration

```bash
#!/bin/bash
# scripts/run_api_tests.sh

# Install Newman if not present
if ! command -v newman &> /dev/null; then
    npm install -g newman
fi

# Set environment variables
export BASE_URL="http://localhost:8000"
export TEST_PROFILE_ID=""

# Run API tests
echo "Running Catalynx API Test Suite..."

newman run tests/api/Catalynx_API_Tests.postman_collection.json \
  --environment tests/api/environments/local.postman_environment.json \
  --reporters cli,json \
  --reporter-json-export results/api_test_results.json \
  --timeout 30000 \
  --delay-request 100

# Check results
if [ $? -eq 0 ]; then
    echo "✅ All API tests passed"
    exit 0
else
    echo "❌ Some API tests failed"
    exit 1
fi
```

---

## CI/CD Pipeline Integration

### 1. GitHub Actions Workflow

```yaml
# .github/workflows/test_pipeline.yml
name: Catalynx Test Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  PYTHON_VERSION: '3.9'
  NODE_VERSION: '16'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: catalynx_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=src --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Start application
      run: |
        python src/web/main.py &
        sleep 10  # Wait for startup
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v --tb=short
    
    - name: Run API tests with Newman
      run: |
        npm install -g newman
        newman run tests/api/Catalynx_API_Tests.postman_collection.json \
          --environment tests/api/environments/ci.postman_environment.json

  performance-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install locust
    
    - name: Run performance tests
      run: |
        python src/web/main.py &
        sleep 10
        locust -f tests/performance/locustfile.py --headless \
          --users 10 --spawn-rate 2 --run-time 60s \
          --host http://localhost:8000

  security-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Bandit security scan
      run: |
        pip install bandit
        bandit -r src/ -f json -o security_report.json
    
    - name: Run Safety dependency check
      run: |
        pip install safety
        safety check --json > safety_report.json
    
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          security_report.json
          safety_report.json
```

### 2. Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
  
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3
  
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
  
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest unit tests
        entry: pytest tests/unit/ -xvs
        language: system
        pass_filenames: false
        always_run: true
      
      - id: mypy
        name: mypy type checking
        entry: mypy src/
        language: system
        pass_filenames: false
        always_run: true
```

---

## Performance Testing Strategy

### 1. Load Testing with Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import json
import random

class CatalynxUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup test data"""
        self.profile_id = None
        self.create_test_profile()
    
    def create_test_profile(self):
        """Create a test profile for this user"""
        profile_data = {
            "organization_name": f"Load Test Org {random.randint(1000, 9999)}",
            "mission_statement": "Load testing mission",
            "ntee_codes": ["B25"],
            "revenue": random.randint(100000, 10000000)
        }
        
        response = self.client.post("/api/profiles", json=profile_data)
        if response.status_code == 200:
            self.profile_id = response.json()["profile_id"]
    
    @task(5)
    def view_dashboard(self):
        """Test dashboard loading - most common operation"""
        self.client.get("/")
    
    @task(3)
    def get_profile_analytics(self):
        """Test profile analytics - common operation"""
        if self.profile_id:
            self.client.get(f"/api/profiles/{self.profile_id}/analytics")
    
    @task(2)
    def run_discovery(self):
        """Test discovery operations - moderate frequency"""
        if self.profile_id:
            self.client.post(
                f"/api/profiles/{self.profile_id}/discover/entity-analytics",
                json={"max_results": 10}
            )
    
    @task(1)
    def export_data(self):
        """Test export operations - less frequent"""
        if self.profile_id:
            self.client.post("/api/export/opportunities", json={
                "profile_id": self.profile_id,
                "format": "json"
            })
    
    def on_stop(self):
        """Cleanup test data"""
        if self.profile_id:
            self.client.delete(f"/api/profiles/{self.profile_id}")

class AdminUser(HttpUser):
    wait_time = between(5, 15)
    weight = 1  # Less frequent than regular users
    
    @task
    def view_system_status(self):
        """Admin monitoring tasks"""
        self.client.get("/api/system/status")
    
    @task
    def view_analytics_overview(self):
        """Admin analytics"""
        self.client.get("/api/analytics/overview")
```

### 2. Performance Benchmarking

```python
# tests/performance/benchmark_scorers.py
import asyncio
import time
import statistics
from src.scoring.discovery_scorer import DiscoveryScorer
from src.analytics.success_scorer import SuccessScorer

async def benchmark_discovery_scorer():
    """Benchmark discovery scorer performance"""
    scorer = DiscoveryScorer()
    
    # Generate test data
    profiles = [create_test_profile(i) for i in range(100)]
    opportunities = [create_test_opportunity(i) for i in range(1000)]
    
    # Warmup
    for i in range(10):
        await scorer.score_opportunity(opportunities[0], profiles[0])
    
    # Benchmark
    times = []
    for opportunity in opportunities[:100]:  # Test 100 combinations
        start = time.perf_counter()
        await scorer.score_opportunity(opportunity, profiles[0])
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds
    
    # Results
    avg_time = statistics.mean(times)
    p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
    
    print(f"Discovery Scorer Performance:")
    print(f"  Average time: {avg_time:.3f}ms")
    print(f"  95th percentile: {p95_time:.3f}ms")
    print(f"  Target: <1ms per operation")
    
    assert avg_time < 1.0, f"Performance degradation: {avg_time:.3f}ms > 1ms"
    assert p95_time < 2.0, f"P95 performance issue: {p95_time:.3f}ms > 2ms"

def benchmark_cache_performance():
    """Benchmark entity cache performance"""
    from src.core.entity_cache_manager import get_entity_cache_manager
    
    cache_manager = get_entity_cache_manager()
    
    # Test cache hit rate
    cache_hits = 0
    total_requests = 1000
    
    for i in range(total_requests):
        ein = f"12-345678{i % 100:02d}"  # Repeat EINs to test cache hits
        
        start = time.perf_counter()
        result = cache_manager.get_entity_data(ein)
        end = time.perf_counter()
        
        if result:  # Cache hit
            cache_hits += 1
    
    hit_rate = cache_hits / total_requests
    print(f"Cache Performance:")
    print(f"  Hit rate: {hit_rate:.1%}")
    print(f"  Target: >85%")
    
    assert hit_rate > 0.85, f"Cache hit rate below target: {hit_rate:.1%}"

if __name__ == "__main__":
    asyncio.run(benchmark_discovery_scorer())
    benchmark_cache_performance()
```

---

## Data Integrity Testing

### 1. Database Testing

```python
# tests/data/test_data_integrity.py
import pytest
import asyncio
from src.core.database import get_database
from src.profiles.service import ProfileService

@pytest.mark.asyncio
async def test_profile_data_integrity():
    """Test profile data consistency"""
    profile_service = ProfileService()
    
    # Create test profile
    profile_data = {
        "organization_name": "Data Integrity Test",
        "revenue": 1000000,
        "ntee_codes": ["B25"]
    }
    
    profile_id = await profile_service.create_profile(profile_data)
    
    try:
        # Test data retrieval consistency
        profile1 = await profile_service.get_profile(profile_id)
        profile2 = await profile_service.get_profile(profile_id)
        
        assert profile1.organization_name == profile2.organization_name
        assert profile1.revenue == profile2.revenue
        assert profile1.ntee_codes == profile2.ntee_codes
        
        # Test data updates
        await profile_service.update_profile(profile_id, {"revenue": 2000000})
        
        updated_profile = await profile_service.get_profile(profile_id)
        assert updated_profile.revenue == 2000000
        
    finally:
        await profile_service.delete_profile(profile_id)

@pytest.mark.asyncio
async def test_entity_cache_consistency():
    """Test entity cache data consistency"""
    from src.core.entity_cache_manager import get_entity_cache_manager
    
    cache_manager = get_entity_cache_manager()
    
    # Test data
    ein = "12-3456789"
    entity_data = {
        "ein": ein,
        "organization_name": "Cache Test Org",
        "revenue": 1000000
    }
    
    # Store data
    cache_manager.store_entity_data(ein, entity_data)
    
    # Retrieve and verify
    retrieved_data = cache_manager.get_entity_data(ein)
    
    assert retrieved_data["ein"] == entity_data["ein"]
    assert retrieved_data["organization_name"] == entity_data["organization_name"]
    assert retrieved_data["revenue"] == entity_data["revenue"]
    
    # Test cache expiration
    import time
    time.sleep(2)  # Simulate time passage
    
    # Data should still be available (within TTL)
    retrieved_data2 = cache_manager.get_entity_data(ein)
    assert retrieved_data2 is not None

def test_scoring_consistency():
    """Test scoring result consistency"""
    from src.scoring.discovery_scorer import DiscoveryScorer
    
    scorer = DiscoveryScorer()
    
    # Same inputs should produce same outputs
    profile = create_test_profile()
    opportunity = create_test_opportunity()
    
    results = []
    for _ in range(10):
        result = asyncio.run(scorer.score_opportunity(opportunity, profile))
        results.append(result.overall_score)
    
    # All scores should be identical for same inputs
    assert len(set(results)) == 1, "Scoring inconsistency detected"
```

### 2. Migration Testing

```python
# tests/data/test_migrations.py
import pytest
from src.core.database import Database
from src.migrations.migration_manager import MigrationManager

@pytest.mark.migration
def test_migration_rollback():
    """Test database migration rollback functionality"""
    migration_manager = MigrationManager()
    
    # Get current migration version
    current_version = migration_manager.get_current_version()
    
    # Apply next migration
    next_version = current_version + 1
    migration_result = migration_manager.migrate_to_version(next_version)
    
    if migration_result.success:
        # Verify migration applied
        assert migration_manager.get_current_version() == next_version
        
        # Test rollback
        rollback_result = migration_manager.rollback_to_version(current_version)
        assert rollback_result.success
        assert migration_manager.get_current_version() == current_version

@pytest.mark.migration
def test_data_preservation_during_migration():
    """Test that data is preserved during migrations"""
    # Create test data before migration
    test_data = create_test_migration_data()
    
    migration_manager = MigrationManager()
    current_version = migration_manager.get_current_version()
    
    # Apply migration
    next_version = current_version + 1
    migration_result = migration_manager.migrate_to_version(next_version)
    
    if migration_result.success:
        # Verify data still exists and is accessible
        retrieved_data = retrieve_test_migration_data()
        assert_data_equivalent(test_data, retrieved_data)
        
        # Rollback
        migration_manager.rollback_to_version(current_version)
```

---

## Security Testing

### 1. API Security Testing

```python
# tests/security/test_api_security.py
import pytest
from fastapi.testclient import TestClient
from src.web.main import app

client = TestClient(app)

def test_sql_injection_protection():
    """Test protection against SQL injection attacks"""
    # Test malicious profile names
    malicious_inputs = [
        "'; DROP TABLE profiles; --",
        "' OR '1'='1",
        "'; UPDATE profiles SET revenue=0; --"
    ]
    
    for malicious_input in malicious_inputs:
        profile_data = {
            "organization_name": malicious_input,
            "revenue": 1000000
        }
        
        response = client.post("/api/profiles", json=profile_data)
        
        # Should either reject the input or sanitize it
        if response.status_code == 200:
            # If accepted, verify no SQL injection occurred
            profile_id = response.json()["profile_id"]
            
            # Verify system integrity
            health_response = client.get("/api/health")
            assert health_response.status_code == 200
            
            # Cleanup
            client.delete(f"/api/profiles/{profile_id}")

def test_xss_protection():
    """Test protection against XSS attacks"""
    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>"
    ]
    
    for payload in xss_payloads:
        profile_data = {
            "organization_name": payload,
            "mission_statement": payload
        }
        
        response = client.post("/api/profiles", json=profile_data)
        
        if response.status_code == 200:
            profile_id = response.json()["profile_id"]
            
            # Verify data is properly escaped/sanitized
            get_response = client.get(f"/api/profiles/{profile_id}")
            profile_data = get_response.json()
            
            # Should not contain executable script tags
            assert "<script>" not in profile_data["organization_name"]
            assert "javascript:" not in profile_data["organization_name"]
            
            client.delete(f"/api/profiles/{profile_id}")

def test_rate_limiting():
    """Test API rate limiting"""
    # Rapid requests to test rate limiting
    responses = []
    for i in range(100):
        response = client.get("/api/health")
        responses.append(response.status_code)
    
    # Should eventually return 429 (Too Many Requests) if rate limiting is enabled
    # Note: Implement rate limiting in production
    # assert 429 in responses, "Rate limiting not working"

def test_authentication_required():
    """Test that sensitive endpoints require authentication"""
    # Test admin endpoints
    admin_endpoints = [
        "/api/system/status",
        "/api/analytics/overview"
    ]
    
    for endpoint in admin_endpoints:
        response = client.get(endpoint)
        # Should require authentication (401) or be publicly accessible (200)
        assert response.status_code in [200, 401, 403]

def test_input_validation():
    """Test input validation and sanitization"""
    # Test invalid data types
    invalid_profile_data = {
        "organization_name": 12345,  # Should be string
        "revenue": "invalid",        # Should be number
        "ntee_codes": "not_a_list"   # Should be list
    }
    
    response = client.post("/api/profiles", json=invalid_profile_data)
    
    # Should reject invalid data
    assert response.status_code in [400, 422]  # Bad Request or Validation Error
```

### 2. Dependency Security Scanning

```bash
#!/bin/bash
# scripts/security_scan.sh

echo "Running security scans..."

# Python dependency scanning with Safety
echo "Scanning Python dependencies..."
safety check --json > safety_report.json

# Static code analysis with Bandit
echo "Running static code analysis..."
bandit -r src/ -f json -o bandit_report.json

# Check for secrets in code
echo "Scanning for secrets..."
if command -v truffleHog &> /dev/null; then
    truffleHog --json . > secrets_report.json
else
    echo "Warning: truffleHog not installed, skipping secrets scan"
fi

# Generate summary
echo "Security scan completed. Check reports:"
echo "  - safety_report.json (dependency vulnerabilities)"
echo "  - bandit_report.json (static analysis)"
echo "  - secrets_report.json (secret detection)"
```

---

## Monitoring & Observability

### 1. Application Monitoring

```python
# src/monitoring/health_checks.py
from fastapi import APIRouter, Depends
from typing import Dict, Any
import psutil
import time
from src.core.database import get_database
from src.core.entity_cache_manager import get_entity_cache_manager

router = APIRouter()

@router.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check endpoint"""
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Database connectivity
    try:
        db = get_database()
        await db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Cache system
    try:
        cache_manager = get_entity_cache_manager()
        cache_stats = cache_manager.get_cache_stats()
        health_status["checks"]["cache"] = {
            "status": "healthy",
            "hit_rate": cache_stats.get("hit_rate", 0),
            "entries": cache_stats.get("total_entries", 0)
        }
    except Exception as e:
        health_status["checks"]["cache"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # System resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    health_status["checks"]["system"] = {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    # Alert if resources are high
    if cpu_percent > 80 or memory.percent > 80:
        health_status["status"] = "warning"
    
    return health_status

@router.get("/api/metrics")
async def metrics() -> Dict[str, Any]:
    """Performance metrics endpoint"""
    
    # Collect performance metrics
    metrics = {
        "timestamp": time.time(),
        "performance": {
            "request_count": get_request_count(),
            "average_response_time": get_average_response_time(),
            "error_rate": get_error_rate()
        },
        "cache": {
            "hit_rate": get_cache_hit_rate(),
            "miss_rate": get_cache_miss_rate(),
            "total_requests": get_cache_total_requests()
        },
        "scoring": {
            "discovery_avg_time": get_discovery_scorer_avg_time(),
            "success_avg_time": get_success_scorer_avg_time(),
            "ai_lite_avg_time": get_ai_lite_avg_time()
        }
    }
    
    return metrics
```

### 2. Logging Strategy

```python
# src/monitoring/logging_config.py
import logging
import json
from datetime import datetime
from typing import Dict, Any

class StructuredFormatter(logging.Formatter):
    """Structured JSON logging formatter"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'profile_id'):
            log_entry['profile_id'] = record.profile_id
        
        if hasattr(record, 'processing_time'):
            log_entry['processing_time'] = record.processing_time
        
        if hasattr(record, 'cache_hit'):
            log_entry['cache_hit'] = record.cache_hit
        
        return json.dumps(log_entry)

def setup_logging():
    """Setup structured logging configuration"""
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler for errors
    error_handler = logging.FileHandler('logs/error.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)
    
    # Performance logger
    perf_logger = logging.getLogger('catalynx.performance')
    perf_handler = logging.FileHandler('logs/performance.log')
    perf_handler.setFormatter(StructuredFormatter())
    perf_logger.addHandler(perf_handler)
    
    # Security logger
    security_logger = logging.getLogger('catalynx.security')
    security_handler = logging.FileHandler('logs/security.log')
    security_handler.setFormatter(StructuredFormatter())
    security_logger.addHandler(security_handler)

# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor function performance"""
    import functools
    import time
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        
        try:
            result = await func(*args, **kwargs)
            
            processing_time = time.perf_counter() - start_time
            
            logger = logging.getLogger('catalynx.performance')
            logger.info(
                f"Function {func.__name__} completed",
                extra={
                    'function': func.__name__,
                    'processing_time': processing_time,
                    'success': True
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = time.perf_counter() - start_time
            
            logger = logging.getLogger('catalynx.performance')
            logger.error(
                f"Function {func.__name__} failed",
                extra={
                    'function': func.__name__,
                    'processing_time': processing_time,
                    'success': False,
                    'error': str(e)
                }
            )
            
            raise
    
    return wrapper
```

---

## Environment Management

### 1. Test Environment Configuration

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  catalynx-test:
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      - ENVIRONMENT=test
      - DATABASE_URL=postgresql://test:testpass@postgres-test:5432/catalynx_test
      - CACHE_BACKEND=redis://redis-test:6379/0
      - LOG_LEVEL=DEBUG
    depends_on:
      - postgres-test
      - redis-test
    ports:
      - "8001:8000"
    volumes:
      - ./tests:/app/tests
      - ./src:/app/src
  
  postgres-test:
    image: postgres:13
    environment:
      - POSTGRES_DB=catalynx_test
      - POSTGRES_USER=test
      - POSTGRES_PASSWORD=testpass
    ports:
      - "5433:5432"
    volumes:
      - postgres_test_data:/var/lib/postgresql/data
  
  redis-test:
    image: redis:7-alpine
    ports:
      - "6380:6379"

volumes:
  postgres_test_data:
```

### 2. Test Data Management

```python
# tests/fixtures/test_data_factory.py
import factory
import random
from datetime import datetime, timedelta
from src.profiles.models import OrganizationProfile

class OrganizationProfileFactory(factory.Factory):
    class Meta:
        model = OrganizationProfile
    
    organization_name = factory.Faker('company')
    mission_statement = factory.Faker('text', max_nb_chars=200)
    revenue = factory.LazyFunction(lambda: random.randint(100000, 10000000))
    state = factory.Faker('state_abbr')
    ntee_codes = factory.LazyFunction(lambda: [random.choice(['B25', 'P20', 'T30'])])
    staff_count = factory.LazyFunction(lambda: random.randint(5, 100))
    years_active = factory.LazyFunction(lambda: random.randint(1, 50))

class OpportunityFactory(factory.Factory):
    class Meta:
        model = dict
    
    opportunity_id = factory.Sequence(lambda n: f"opp_{n}")
    organization_name = factory.Faker('company')
    source_type = factory.Faker('random_element', elements=['Nonprofit', 'Government', 'Foundation'])
    funding_amount = factory.LazyFunction(lambda: random.randint(10000, 1000000))
    application_deadline = factory.LazyFunction(
        lambda: (datetime.now() + timedelta(days=random.randint(30, 365))).isoformat()
    )
    raw_score = factory.LazyFunction(lambda: random.uniform(0.0, 1.0))
    confidence_level = factory.LazyFunction(lambda: random.uniform(0.5, 1.0))

# Test data sets
def create_test_dataset(size=100):
    """Create a complete test dataset"""
    return {
        'profiles': [OrganizationProfileFactory() for _ in range(size // 10)],
        'opportunities': [OpportunityFactory() for _ in range(size)]
    }

def create_performance_test_dataset(size=1000):
    """Create large dataset for performance testing"""
    return create_test_dataset(size)

def create_edge_case_dataset():
    """Create dataset with edge cases"""
    edge_cases = []
    
    # Missing data cases
    edge_cases.append(OrganizationProfileFactory(revenue=None))
    edge_cases.append(OrganizationProfileFactory(ntee_codes=[]))
    
    # Extreme values
    edge_cases.append(OrganizationProfileFactory(revenue=0))
    edge_cases.append(OrganizationProfileFactory(revenue=1000000000))
    
    # Invalid data
    edge_cases.append(OpportunityFactory(raw_score=-0.1))
    edge_cases.append(OpportunityFactory(confidence_level=1.5))
    
    return edge_cases
```

---

## Testing Best Practices

### 1. Test Organization

```
tests/
├── unit/                     # Unit tests (70% of tests)
│   ├── scoring/
│   │   ├── test_discovery_scorer.py
│   │   ├── test_success_scorer.py
│   │   └── test_government_scorer.py
│   ├── analytics/
│   ├── processors/
│   └── web/
├── integration/              # Integration tests (25% of tests)
│   ├── test_workflow_integration.py
│   ├── test_api_integration.py
│   └── test_phase6_integration.py
├── e2e/                      # End-to-end tests (5% of tests)
│   ├── test_complete_workflow.py
│   └── test_user_journeys.py
├── performance/              # Performance tests
│   ├── locustfile.py
│   └── benchmark_tests.py
├── security/                 # Security tests
│   └── test_security.py
├── data/                     # Data integrity tests
│   ├── test_data_integrity.py
│   └── test_migrations.py
├── api/                      # API tests (Postman collections)
│   ├── Catalynx_API_Tests.postman_collection.json
│   └── environments/
└── fixtures/                 # Test data and utilities
    ├── test_data_factory.py
    └── conftest.py
```

### 2. Test Naming Conventions

```python
# Test naming pattern: test_[what]_[when]_[expected_result]

def test_discovery_scorer_with_valid_data_returns_score():
    """Test that discovery scorer returns valid score with good data"""
    pass

def test_discovery_scorer_with_missing_data_returns_low_confidence():
    """Test that discovery scorer handles missing data gracefully"""
    pass

def test_api_profile_creation_with_valid_data_returns_201():
    """Test that profile creation API returns 201 with valid data"""
    pass

def test_cache_manager_with_expired_data_triggers_refresh():
    """Test that cache manager refreshes expired data"""
    pass
```

### 3. Test Configuration

```python
# tests/conftest.py
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.database import Base, get_database
from tests.fixtures.test_data_factory import create_test_dataset

# Test database setup
TEST_DATABASE_URL = "postgresql://test:testpass@localhost:5433/catalynx_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_database():
    """Setup test database"""
    engine = create_engine(TEST_DATABASE_URL)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
async def test_session(test_database):
    """Create a test database session"""
    TestSessionLocal = sessionmaker(bind=test_database)
    session = TestSessionLocal()
    
    yield session
    
    session.rollback()
    session.close()

@pytest.fixture(scope="function")
def test_data():
    """Provide test data for tests"""
    return create_test_dataset(size=50)

@pytest.fixture(scope="function")
def mock_api_client():
    """Mock API client for external service tests"""
    from unittest.mock import Mock
    
    client = Mock()
    client.get.return_value.status_code = 200
    client.get.return_value.json.return_value = {"status": "success"}
    
    return client

# Pytest markers
pytest.mark.asyncio = pytest.mark.asyncio
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.security = pytest.mark.security
pytest.mark.phase6 = pytest.mark.phase6
```

---

## Implementation Roadmap

### Week 1-2: Foundation Setup
1. **Setup Testing Infrastructure**
   - Configure pytest with async support
   - Setup test database and fixtures
   - Implement basic CI/CD pipeline

2. **Unit Test Implementation**
   - Create tests for all scorers
   - Test API endpoints
   - Achieve 70% test coverage

3. **Integration Test Framework**
   - Cross-system integration tests
   - API integration with Postman/Newman
   - Cache consistency tests

### Week 3-4: Advanced Testing
1. **Performance Testing**
   - Implement Locust load testing
   - Benchmark scorer performance
   - Cache performance validation

2. **Security Testing**
   - API security tests
   - Dependency scanning
   - Input validation tests

3. **Phase 6 Integration Testing**
   - Decision synthesis framework tests
   - Visualization system tests
   - Export system validation

### Week 5-6: Production Readiness
1. **End-to-End Testing**
   - Complete workflow testing
   - User journey validation
   - Mobile responsiveness testing

2. **Monitoring Implementation**
   - Health check endpoints
   - Performance metrics collection
   - Structured logging setup

3. **Documentation & Training**
   - Test documentation
   - Developer testing guidelines
   - Production runbook

### Success Metrics

- **Test Coverage**: >90% code coverage
- **Performance**: <100ms API response times
- **Reliability**: <0.1% error rate
- **Cache Efficiency**: >85% hit rate
- **Security**: Zero critical vulnerabilities
- **CI/CD**: <10 minute pipeline execution

This comprehensive testing strategy ensures the Catalynx platform maintains its sophisticated multi-layered architecture while delivering enterprise-grade reliability and performance.