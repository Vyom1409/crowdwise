@echo off
setlocal enabledelayedexpansion
title CrowdWise Delhi Bus Planner - One-Click Launcher

:: ============================================================================
:: 1. Navigate to Project Directory (Portability Guarantee)
:: ============================================================================
cd /d "%~dp0"

echo ======================================================================
echo           CrowdWise - One-Click Application Launcher
echo ======================================================================
echo Starting application...
echo Project directory: %CD%
echo.

:: ============================================================================
:: 2. Locate Google Chrome
:: ============================================================================
set "CHROME_BIN="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_BIN=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
)
if not defined CHROME_BIN if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_BIN=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
)
if not defined CHROME_BIN if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_BIN=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

:: ============================================================================
:: 3. Check & Configure Python Environment
:: ============================================================================
echo Checking dependencies...

set "PY_CMD="

:: Check virtual environment inside project
if exist "%~dp0.venv\Scripts\python.exe" set "PY_CMD=%~dp0.venv\Scripts\python.exe"
if not defined PY_CMD if exist "%~dp0venv\Scripts\python.exe" set "PY_CMD=%~dp0venv\Scripts\python.exe"

:: Check known real Python installation paths first
if not defined PY_CMD (
    if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
        set "PY_CMD=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    )
)

if not defined PY_CMD (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
        if not defined PY_CMD if exist "%%D\python.exe" set "PY_CMD=%%D\python.exe"
    )
)

if not defined PY_CMD (
    for /d %%D in ("C:\Python3*") do (
        if not defined PY_CMD if exist "%%D\python.exe" set "PY_CMD=%%D\python.exe"
    )
)

:: Check py launcher and python in PATH
if not defined PY_CMD (
    where py >nul 2>&1
    if !errorlevel! equ 0 set "PY_CMD=py"
)

if not defined PY_CMD (
    where python >nul 2>&1
    if !errorlevel! equ 0 set "PY_CMD=python"
)

if not defined PY_CMD (
    echo.
    echo ======================================================================
    echo  [ERROR] Python interpreter was not found on this system!
    echo ======================================================================
    echo  Please install Python 3.10 or higher from https://www.python.org/
    echo  Ensure Add Python to PATH is checked during installation.
    echo.
    pause
    exit /b 1
)

:: ============================================================================
:: 4. Node.js Project Check (If package.json exists)
:: ============================================================================
if exist "package.json" (
    if not exist "app.py" (
        where node >nul 2>&1
        if !errorlevel! neq 0 (
            echo [ERROR] Node.js is required for this project but was not found.
            pause
            exit /b 1
        )
        if not exist "node_modules" (
            echo Installing Node.js dependencies...
            call npm install
        )
        echo Starting Node.js server...
        start cmd /c "npm start"
    )
)

:: ============================================================================
:: 5. Verify & Install Python Dependencies
:: ============================================================================
"%PY_CMD%" -c "import fastapi, uvicorn" >nul 2>&1
if !errorlevel! neq 0 (
    echo Required Python libraries missing. Installing fastapi and uvicorn...
    "%PY_CMD%" -m pip install fastapi uvicorn
    if !errorlevel! neq 0 (
        echo.
        echo ======================================================================
        echo  [ERROR] Failed to install required packages via pip.
        echo  Please verify your internet connection and retry.
        echo ======================================================================
        pause
        exit /b 1
    )
    echo Required dependencies installed successfully.
)

:: ============================================================================
:: 6. Detect Port Configured in app.py (Do not assume port number)
:: ============================================================================
set "PORT=8765"
if exist "app.py" (
    for /f "tokens=*" %%P in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "$c = Get-Content 'app.py' -Raw; if ($c -match 'port\s*=\s*(\d+)') { $Matches[1] } else { '8765' }" 2^>nul') do (
        if not "%%P"=="" set "PORT=%%P"
    )
)

:: ============================================================================
:: 7. Prevent Duplicate Server Instances (Requirement 9)
:: ============================================================================
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue) { exit 10 } else { exit 0 }"
if !errorlevel! equ 10 (
    echo Backend started successfully. [Reusing existing server on port %PORT%]
    
    :: Open in Google Chrome
    if defined CHROME_BIN (
        start "" "!CHROME_BIN!" "http://127.0.0.1:%PORT%/"
    ) else (
        start "" "http://127.0.0.1:%PORT%/"
    )
    
    echo Website opened successfully.
    echo.
    echo ======================================================================
    echo   CrowdWise is open in Chrome at http://127.0.0.1:%PORT%/
    echo ======================================================================
    ping 127.0.0.1 -n 4 >nul
    exit /b 0
)

:: ============================================================================
:: 8. Start Background Opener Watcher & Launch Server
:: ============================================================================
start /b "" powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$port = '%PORT%';" ^
    "for ($i = 0; $i -lt 50; $i++) {" ^
    "    Start-Sleep -Milliseconds 300;" ^
    "    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {" ^
    "        Write-Host 'Backend started successfully.';" ^
    "        if ($env:CHROME_BIN) { Start-Process $env:CHROME_BIN \"http://127.0.0.1:$port/\" } else { Start-Process \"http://127.0.0.1:$port/\" };" ^
    "        Write-Host 'Website opened successfully.';" ^
    "        break;" ^
    "    }" ^
    "}"

:: Start Backend Server
"%PY_CMD%" app.py

pause
