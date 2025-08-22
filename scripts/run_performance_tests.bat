@echo off
REM Catalynx Performance Testing Script
REM Comprehensive performance validation and benchmarking

echo ===============================================
echo Catalynx Performance Test Suite
echo ===============================================
echo.

REM Set environment variables
set CATALYNX_ENV=performance
set PYTHONPATH=%cd%\src
set PERFORMANCE_TEST_DURATION=300

REM Activate virtual environment
if not exist "grant-research-env\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    exit /b 1
)

call grant-research-env\Scripts\activate.bat

REM Create performance results directory
if not exist "performance-results" mkdir performance-results

echo Starting Catalynx application for performance testing...
start /b python src/web/main.py

REM Wait for application startup
echo Waiting for application startup...
timeout /t 20 /nobreak >nul

REM Check if application is running
curl -f http://localhost:8000/api/health >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Application failed to start!
    exit /b 1
)

echo Application started successfully!
echo.

echo ===============================================
echo 1. Running Unit Performance Tests
echo ===============================================
pytest tests/performance/test_system_performance.py -v --timeout=600 --junitxml=performance-results/junit-unit-performance.xml

echo.
echo ===============================================
echo 2. Running Locust Load Tests
echo ===============================================
echo Load testing with Locust (5 minute test)...

locust -f tests/performance/locustfile.py ^
    --headless ^
    --users 20 ^
    --spawn-rate 2 ^
    --run-time 300s ^
    --host http://localhost:8000 ^
    --html performance-results/locust-report.html ^
    --csv performance-results/locust-stats

if %ERRORLEVEL% neq 0 (
    echo Load testing completed with warnings
) else (
    echo Load testing completed successfully
)

echo.
echo ===============================================
echo 3. Running Cache Performance Tests
echo ===============================================
pytest tests/unit/test_entity_cache.py::TestEntityCacheManager::test_cache_performance_with_large_dataset -v

echo.
echo ===============================================
echo 4. Running API Response Time Tests
echo ===============================================
newman run tests/api/Catalynx_API_Tests.postman_collection.json ^
    --environment tests/api/environments/local.postman_environment.json ^
    --reporters json ^
    --reporter-json-export performance-results/api-performance.json ^
    --timeout 60000 ^
    --delay-request 100

echo.
echo ===============================================
echo 5. Generating Performance Report
echo ===============================================

python -c "
import json
import os
import subprocess
import psutil
from datetime import datetime

def get_system_info():
    return {
        'cpu_count': psutil.cpu_count(),
        'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'python_version': subprocess.check_output(['python', '--version']).decode().strip()
    }

def analyze_locust_results():
    try:
        with open('performance-results/locust-stats_stats.csv', 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:
                # Parse summary line (usually the last line with aggregated stats)
                for line in reversed(lines):
                    if 'Aggregated' in line or 'Total' in line:
                        parts = line.split(',')
                        return {
                            'avg_response_time': float(parts[5]) if len(parts) > 5 else 0,
                            'requests_per_second': float(parts[9]) if len(parts) > 9 else 0,
                            'failure_rate': float(parts[10]) if len(parts) > 10 else 0
                        }
        return {'avg_response_time': 0, 'requests_per_second': 0, 'failure_rate': 0}
    except:
        return {'avg_response_time': 0, 'requests_per_second': 0, 'failure_rate': 0}

# Generate comprehensive performance report
report = {
    'timestamp': datetime.now().isoformat(),
    'test_duration_seconds': 300,
    'system_info': get_system_info(),
    'locust_results': analyze_locust_results(),
    'files_generated': {
        'locust_html_report': 'performance-results/locust-report.html',
        'locust_csv_stats': 'performance-results/locust-stats_stats.csv',
        'api_performance': 'performance-results/api-performance.json',
        'unit_performance': 'performance-results/junit-unit-performance.xml'
    },
    'baseline_comparison': {
        'target_avg_response_time_ms': 250,
        'target_requests_per_second': 50,
        'target_failure_rate_percent': 1.0
    }
}

# Load baselines for comparison
try:
    with open('tests/performance/baselines.json', 'r') as f:
        baselines = json.load(f)
        report['baseline_targets'] = baselines['performance_baselines']['api_performance']
except:
    pass

with open('performance-results/performance-report.json', 'w') as f:
    json.dump(report, f, indent=2)

# Print summary
locust = report['locust_results']
print(f'Performance Test Summary:')
print(f'  Average Response Time: {locust[\"avg_response_time\"]:.1f}ms')
print(f'  Requests per Second: {locust[\"requests_per_second\"]:.1f}')
print(f'  Failure Rate: {locust[\"failure_rate\"]:.1f}%')
print(f'  System: {report[\"system_info\"][\"cpu_count\"]} CPU, {report[\"system_info\"][\"memory_total_gb\"]}GB RAM')
print(f'Report saved to: performance-results/performance-report.json')
"

REM Stop application
echo.
echo Stopping application...
taskkill /f /im python.exe /fi "WindowTitle eq *main.py*" >nul 2>&1

echo.
echo ===============================================
echo Performance Testing Complete
echo ===============================================
echo.
echo 📊 Performance Reports Generated:
echo   - HTML Report: performance-results\locust-report.html
echo   - CSV Stats: performance-results\locust-stats_stats.csv
echo   - JSON Summary: performance-results\performance-report.json
echo   - API Performance: performance-results\api-performance.json
echo.
echo Open performance-results\locust-report.html to view detailed results.

pause