@echo off
echo Launching Catalynx Analytics Dashboard...
echo.
echo Dashboard will be available at: http://localhost:8501
echo Press Ctrl+C to stop the dashboard
echo.

cd /d "%~dp0"
"grant-research-env/Scripts/streamlit.exe" run src/dashboard/analytics_dashboard.py --server.address 127.0.0.1 --server.port 8501 --server.headless false

pause