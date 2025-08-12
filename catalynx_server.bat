@echo off
REM Catalynx Server Management Script
REM Usage: catalynx_server.bat [start|stop|restart|status]

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if "%1"=="" (
    set "COMMAND=start"
) else (
    set "COMMAND=%1"
)

if /i "%COMMAND%"=="start" (
    echo Starting Catalynx Server Service...
    "grant-research-env\Scripts\python.exe" start_catalynx_service.py start
    pause
) else if /i "%COMMAND%"=="stop" (
    echo Stopping Catalynx Server...
    "grant-research-env\Scripts\python.exe" start_catalynx_service.py stop
    pause
) else if /i "%COMMAND%"=="restart" (
    echo Restarting Catalynx Server...
    "grant-research-env\Scripts\python.exe" start_catalynx_service.py restart
    pause
) else if /i "%COMMAND%"=="status" (
    echo Checking Catalynx Server Status...
    "grant-research-env\Scripts\python.exe" start_catalynx_service.py status
    pause
) else if /i "%COMMAND%"=="auto" (
    echo Auto-launching Catalynx...
    "grant-research-env\Scripts\python.exe" launch_catalynx_auto.py
) else (
    echo Usage: catalynx_server.bat [start^|stop^|restart^|status^|auto]
    echo.
    echo Commands:
    echo   start   - Start server in background
    echo   stop    - Stop running server
    echo   restart - Restart server
    echo   status  - Check server status
    echo   auto    - Auto-start and open browser
    pause
)