@echo off
echo Starting Catalynx Modern Web Interface...
echo.
echo The interface will be available at:
echo   http://localhost:8000
echo   http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop the server.
echo.

REM Stay in root directory to access main data/profiles folder
cd "%~dp0"
"grant-research-env\Scripts\python.exe" src\web\main.py

pause