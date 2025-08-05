@echo off
echo Launching Catalynx Main Dashboard...
echo.
echo Dashboard will be available at: http://localhost:8502
echo Press Ctrl+C to stop the dashboard
echo.

cd /d "%~dp0"
"grant-research-env/Scripts/streamlit.exe" run src/dashboard/app.py --server.address 127.0.0.1 --server.port 8502 --server.headless false

pause