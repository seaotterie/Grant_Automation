@echo off
echo Launching Modern Catalynx Analytics...
echo.
echo The legacy analytics dashboard has been integrated into our modern web interface.
echo.
echo Starting Catalynx Modern Web Interface with Analytics...
echo Interface will be available at:
echo   http://localhost:8000
echo.
echo Navigate to the Analytics tab for enhanced Chart.js visualizations.
echo Press Ctrl+C to stop the server.
echo.

cd "%~dp0src\web"
"..\..\grant-research-env\Scripts\python.exe" main.py

pause