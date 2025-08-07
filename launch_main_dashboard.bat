@echo off
echo Launching Modern Catalynx Interface...
echo.
echo The legacy dashboard has been replaced with our modern web interface.
echo.
echo Starting Catalynx Modern Web Interface...
echo Interface will be available at:
echo   http://localhost:8000
echo   http://127.0.0.1:8000
echo.
echo Features: Commercial Track, State Discovery, Enhanced Analytics, Mobile Support
echo Press Ctrl+C to stop the server.
echo.

cd "%~dp0src\web"
"..\..\grant-research-env\Scripts\python.exe" main.py

pause