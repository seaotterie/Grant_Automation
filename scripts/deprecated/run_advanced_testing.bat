@echo off
echo ========================================================================
echo WEEK 3-4 ADVANCED TESTING SUITE
echo Comprehensive DevOps Testing Implementation
echo ========================================================================
echo.
echo Starting comprehensive testing suite...
echo - Manual testing checklist (100%% success rate target)
echo - Phase 6 systems validation (70%% implementation target)  
echo - Security testing framework (OWASP Top 10 coverage)
echo - Performance baseline validation (75%% score target)
echo.
echo Server must be running on localhost:8000
echo Press Ctrl+C to cancel, or any key to continue...
pause > nul
echo.

REM Execute the comprehensive testing suite
"grant-research-env\Scripts\python.exe" run_advanced_testing_suite.py

echo.
echo ========================================================================
echo Testing suite execution completed.
echo Check the generated reports for detailed results.
echo ========================================================================
pause