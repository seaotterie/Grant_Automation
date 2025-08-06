@echo off
echo Starting Catalynx Modern Web Interface...
echo.
echo The interface will be available at:
echo   http://localhost:8000
echo   http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server.
echo.

cd "%~dp0src\web"
"..\..\grant-research-env\Scripts\python.exe" main.py

pause