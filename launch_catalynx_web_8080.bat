@echo off
echo Starting Catalynx Modern Web Interface on port 8080...
echo.
echo The interface will be available at:
echo   http://localhost:8080
echo   http://127.0.0.1:8080
echo.
echo Press Ctrl+C to stop the server.
echo.

cd "%~dp0src\web"
"..\..\grant-research-env\Scripts\python.exe" -c "
import uvicorn
import main
uvicorn.run(main.app, host='127.0.0.1', port=8080, reload=False)
"

pause