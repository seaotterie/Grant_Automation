@echo off
REM Quick Test Runner for Catalynx Playwright Tests
REM Run basic smoke tests for rapid development feedback

echo.
echo 🎭 Catalynx Playwright Quick Test Runner
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "package.json" (
    echo ❌ Error: Run this from the tests/playwright directory
    echo Current directory: %CD%
    echo Expected: ...\tests\playwright
    pause
    exit /b 1
)

REM Check if Catalynx server is running
echo 🔍 Checking if Catalynx server is running...
curl -s http://localhost:8000/api/system/status > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Catalynx server is not running on http://localhost:8000
    echo Please start the server first with: python src/web/main.py
    pause
    exit /b 1
)

echo ✅ Server is running
echo.

echo 🚀 Running basic smoke tests...
npx playwright test tests/smoke/00-basic-functionality.spec.js --project=chromium --reporter=line

echo.
echo 📊 Test Results Summary:
echo ========================

REM Check if tests passed
if %errorlevel% equ 0 (
    echo ✅ ALL TESTS PASSED!
    echo.
    echo 💡 Next steps:
    echo   - Run full smoke tests: npm run test:smoke
    echo   - Run with UI mode: npm run test:ui
    echo   - View test report: npm run test:report
) else (
    echo ❌ Some tests failed
    echo.
    echo 🔧 Debugging options:
    echo   - Run with headed browser: npx playwright test --headed
    echo   - Run in debug mode: npx playwright test --debug
    echo   - View HTML report: npx playwright show-report
)

echo.
pause