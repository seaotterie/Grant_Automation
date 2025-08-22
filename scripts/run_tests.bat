@echo off
REM Catalynx Test Execution Script - Windows
REM Runs comprehensive test suite with reporting

echo ===============================================
echo Catalynx Test Suite Execution
echo ===============================================
echo.

REM Set environment variables
set CATALYNX_ENV=test
set PYTHONPATH=%cd%\src
set TEST_DATABASE_URL=sqlite:///./test_catalynx.db

REM Check if virtual environment exists
if not exist "grant-research-env\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run setup first.
    exit /b 1
)

REM Activate virtual environment
call grant-research-env\Scripts\activate.bat

REM Install test dependencies if needed
echo Installing test dependencies...
pip install -r requirements-test.txt >nul 2>&1

REM Create test results directory
if not exist "test-results" mkdir test-results

echo.
echo ===============================================
echo Running Unit Tests
echo ===============================================
pytest tests/unit/ -v --cov=src --cov-report=html:test-results/coverage-html --cov-report=xml:test-results/coverage.xml --junitxml=test-results/junit-unit.xml

if %ERRORLEVEL% neq 0 (
    echo Unit tests failed!
    set TEST_FAILED=1
) else (
    echo Unit tests passed!
)

echo.
echo ===============================================
echo Running Integration Tests
echo ===============================================
pytest tests/integration/ -v --junitxml=test-results/junit-integration.xml -m "integration and not slow"

if %ERRORLEVEL% neq 0 (
    echo Integration tests failed!
    set TEST_FAILED=1
) else (
    echo Integration tests passed!
)

echo.
echo ===============================================
echo Running Performance Tests (Quick)
echo ===============================================
pytest tests/performance/ -v --junitxml=test-results/junit-performance.xml -m "performance and not slow" --timeout=300

if %ERRORLEVEL% neq 0 (
    echo Performance tests failed!
    set TEST_FAILED=1
) else (
    echo Performance tests passed!
)

echo.
echo ===============================================
echo Running API Tests with Newman
echo ===============================================

REM Check if Newman is installed
newman --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Newman not found, installing...
    npm install -g newman
)

REM Start application in background for API testing
echo Starting application for API testing...
start /b python src/web/main.py

REM Wait for application to start
timeout /t 15 /nobreak >nul

REM Run API tests
newman run tests/api/Catalynx_API_Tests.postman_collection.json ^
    --environment tests/api/environments/local.postman_environment.json ^
    --reporters cli,json ^
    --reporter-json-export test-results/newman-results.json ^
    --timeout 30000 ^
    --delay-request 500

if %ERRORLEVEL% neq 0 (
    echo API tests failed!
    set TEST_FAILED=1
) else (
    echo API tests passed!
)

REM Stop application
taskkill /f /im python.exe /fi "WindowTitle eq *main.py*" >nul 2>&1

echo.
echo ===============================================
echo Generating Test Report
echo ===============================================

python -c "
import json
import os
from datetime import datetime

# Generate test summary
summary = {
    'timestamp': datetime.now().isoformat(),
    'test_results': {
        'unit_tests': os.path.exists('test-results/junit-unit.xml'),
        'integration_tests': os.path.exists('test-results/junit-integration.xml'),
        'performance_tests': os.path.exists('test-results/junit-performance.xml'),
        'api_tests': os.path.exists('test-results/newman-results.json')
    },
    'coverage_report': 'test-results/coverage-html/index.html'
}

with open('test-results/test-summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print('Test summary generated: test-results/test-summary.json')
print('Coverage report: test-results/coverage-html/index.html')
"

echo.
echo ===============================================
echo Test Execution Complete
echo ===============================================

if defined TEST_FAILED (
    echo.
    echo ❌ Some tests failed! Check test-results/ directory for details.
    exit /b 1
) else (
    echo.
    echo ✅ All tests passed successfully!
    echo.
    echo Test Results Available:
    echo   - Coverage Report: test-results\coverage-html\index.html
    echo   - Test Summary: test-results\test-summary.json
    echo   - Individual Results: test-results\
    exit /b 0
)