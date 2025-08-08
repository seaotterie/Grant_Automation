@echo off
echo Starting Enhanced Catalynx Web Interface with Processor Integration...
echo.
echo PHASE 1.3 COMPLETE: Profile-Processor Integration Ready!
echo - 20 processors registered and operational
echo - DISCOMBOBULATOR track endpoints: /api/discovery/nonprofit, /federal, /state, /commercial
echo - AMPLINATOR track endpoints: /api/analysis/scoring, /network, /export, /reports
echo - Profile-driven discovery with context-aware processors
echo - Enhanced Discover Opportunities button with automated sequences
echo - Full pipeline summary: /api/pipeline/full-summary
echo - Processor management: /api/processors
echo.
echo Server starting on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
"grant-research-env/Scripts/python.exe" src/web/main.py
pause