@echo off
setlocal enabledelayedexpansion
title CrowdWise - Crowdedness-Aware Journey Planner

:: Navigate to script directory
cd /d "%~dp0"

echo ======================================================================
echo           CrowdWise - One-Click Application Launcher
echo ======================================================================
echo Project directory: %CD%
echo.

:: 1. Detect Python 3.10+
set "PY_CMD="
if exist "%~dp0.venv\Scripts\python.exe" set "PY_CMD=%~dp0.venv\Scripts\python.exe"

if not defined PY_CMD (
    for %%C in ("%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" py python python3) do (
        if not defined PY_CMD (
            %%~C -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
            if !errorlevel! equ 0 set "PY_CMD=%%~C"
        )
    )
)

if not defined PY_CMD (
    echo.
    echo ======================================================================
    echo  [ERROR] Python 3.10 or higher is required but was not found!
    echo ======================================================================
    echo  Please download and install Python from:
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: Check the box "Add Python to PATH" during installation.
    echo ======================================================================
    echo.
    pause
    exit /b 1
)

:: 2. Setup virtual environment (.venv) if missing
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Creating Python virtual environment in .venv ...
    "%PY_CMD%" -m venv "%~dp0.venv"
    if exist "%~dp0.venv\Scripts\python.exe" (
        set "PY_CMD=%~dp0.venv\Scripts\python.exe"
    ) else (
        echo [WARNING] Could not create .venv; proceeding with system Python.
    )
) else (
    set "PY_CMD=%~dp0.venv\Scripts\python.exe"
)

:: 3. Install dependencies from requirements.txt if not already installed
"%PY_CMD%" -c "import fastapi, uvicorn, pydantic, httpx, numpy, pandas, sklearn" >nul 2>&1
if !errorlevel! neq 0 (
    echo Installing requirements from requirements.txt (first run only)
    "%PY_CMD%" -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo.
        echo ======================================================================
        echo  [ERROR] Failed to install required packages.
        echo  Please verify your internet connection and retry.
        echo ======================================================================
        pause
        exit /b 1
    )
    echo Dependencies verified successfully.
)

:: 4. Port Auto-Discovery and Reuse Check
set "BASE_PORT=8765"
set "PORT="

:: Check if server is already running on default port and healthy
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 1; if ($r.status -eq 'healthy') { exit 10 } else { exit 0 } } catch { exit 0 }" >nul 2>&1
if !errorlevel! equ 10 (
    echo Server is already running and healthy at http://127.0.0.1:8765/
    start "" "http://127.0.0.1:8765/"
    echo CrowdWise opened in your default browser.
    timeout /t 3 >nul
    exit /b 0
)

:: Find an available port starting from 8765
for /f %%P in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$p = 8765; while ($p -lt 8800) { if (-not (Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue)) { $p; break }; $p++ }"') do (
    set "PORT=%%P"
)
if not defined PORT set "PORT=8765"

echo Target Port: %PORT%
set "PORT=%PORT%"

:: 5. Launch Background Browser Opener (waits for /health)
start /b "" powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$port = '%PORT%';" ^
    "$url = \"http://127.0.0.1:$port/\";" ^
    "$healthUrl = \"http://127.0.0.1:$port/health\";" ^
    "Write-Host 'Waiting for server to start...';" ^
    "for ($i = 0; $i -lt 100; $i++) {" ^
    "    Start-Sleep -Milliseconds 250;" ^
    "    try {" ^
    "        $res = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 1;" ^
    "        if ($res.status -eq 'healthy') {" ^
    "            Write-Host 'Backend ready. Opening CrowdWise in browser...';" ^
    "            Start-Process $url;" ^
    "            break;" ^
    "        }" ^
    "    } catch {}" ^
    "}"

:: 6. Start CrowdWise Server
echo.
echo ======================================================================
echo   CrowdWise is running at http://127.0.0.1:%PORT%/
echo   Close this window to stop the application.
echo ======================================================================
echo.

"%PY_CMD%" app.py

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] The server stopped with an error code: !errorlevel!
    pause
)
