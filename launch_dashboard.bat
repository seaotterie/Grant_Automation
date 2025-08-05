@echo off
echo 🎯 Starting Grant Research Automation Dashboard...
echo.
echo Dashboard will be available at:
echo   Local:   http://localhost:8501
echo   Network: http://192.168.1.163:8501
echo.
echo Press Ctrl+C to stop the dashboard
echo.

grant-research-env\Scripts\streamlit.exe run src\dashboard\app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

pause