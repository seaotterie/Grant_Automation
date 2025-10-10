@echo off
REM Catalynx Load Testing Script
REM Comprehensive load testing using Locust for desktop POC validation

echo ====================================
echo    Catalynx Load Testing Suite
echo ====================================
echo.

REM Activate virtual environment
call grant-research-env\Scripts\activate.bat

REM Check if Catalynx server is running
echo Checking if Catalynx server is running at localhost:8000...
timeout 3 curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Catalynx server does not appear to be running!
    echo Please start the server with: launch_catalynx_web.bat
    echo.
    pause
    exit /b 1
)

echo Server is running - proceeding with load tests...
echo.

REM Check if Locust is installed
python -c "import locust" >nul 2>&1
if errorlevel 1 (
    echo Installing Locust for load testing...
    python -m pip install locust websockets
)

echo Available Load Test Options:
echo.
echo 1. Light Load Test (10 users, 2 spawn rate, 2 minutes)
echo 2. Moderate Load Test (50 users, 5 spawn rate, 5 minutes) 
echo 3. Heavy Load Test (100 users, 10 spawn rate, 10 minutes)
echo 4. Stress Test (200 users, 20 spawn rate, 15 minutes)
echo 5. Interactive Web UI Mode (Recommended for analysis)
echo 6. Quick Discovery Stress Test (50 users, discovery focused)
echo 7. Cache Performance Test (25 users, cache focused)
echo 8. WebSocket Load Test (Python-based)
echo 9. Exit
echo.

set /p choice="Select test option (1-9): "

if "%choice%"=="1" (
    echo Running Light Load Test...
    locust -f tests\performance\locustfile.py --users 10 --spawn-rate 2 -t 2m --host http://localhost:8000 --headless
)

if "%choice%"=="2" (
    echo Running Moderate Load Test...
    locust -f tests\performance\locustfile.py --users 50 --spawn-rate 5 -t 5m --host http://localhost:8000 --headless
)

if "%choice%"=="3" (
    echo Running Heavy Load Test...
    locust -f tests\performance\locustfile.py --users 100 --spawn-rate 10 -t 10m --host http://localhost:8000 --headless
)

if "%choice%"=="4" (
    echo Running Stress Test...
    echo WARNING: This is an intensive test that may impact system performance
    timeout 5 >nul
    locust -f tests\performance\locustfile.py --users 200 --spawn-rate 20 -t 15m --host http://localhost:8000 --headless
)

if "%choice%"=="5" (
    echo Starting Interactive Web UI Mode...
    echo Open http://localhost:8089 in your browser to control the test
    echo Press Ctrl+C to stop the test server
    locust -f tests\performance\locustfile.py --host http://localhost:8000
)

if "%choice%"=="6" (
    echo Running Discovery Stress Test...
    locust -f tests\performance\locustfile.py --users 50 --spawn-rate 10 -t 5m --host http://localhost:8000 --headless CatalynxUser DiscoveryStressTest
)

if "%choice%"=="7" (
    echo Running Cache Performance Test...
    locust -f tests\performance\locustfile.py --users 25 --spawn-rate 5 -t 3m --host http://localhost:8000 --headless CachePerformanceTest
)

if "%choice%"=="8" (
    echo Running WebSocket Load Test...
    python tests\performance\test_load_performance.py
)

if "%choice%"=="9" (
    echo Exiting...
    exit /b 0
)

echo.
echo Load test completed!
echo.
echo Results Analysis:
echo - Check console output above for test summary
echo - Review any performance warnings or failures
echo - For detailed analysis, use option 5 (Interactive Web UI Mode)
echo.
echo Performance Targets:
echo - Failure rate: ^< 5%%
echo - Average response time: ^< 1000ms  
echo - Cache hit rate: ^> 70%% (when applicable)
echo - Requests per second: ^> 10 RPS minimum
echo.
pause