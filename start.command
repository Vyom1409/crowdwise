#!/bin/bash
# CrowdWise macOS Double-Clickable Launcher (start.command)
set -e

# Change directory to the repository folder
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "======================================================================"
echo "          CrowdWise - One-Click Application Launcher (macOS)"
echo "======================================================================"
echo "Project directory: $DIR"
echo ""

# 1. Detect Python 3.10+
PY_CMD=""
if [ -f "$DIR/.venv/bin/python" ]; then
    PY_CMD="$DIR/.venv/bin/python"
fi

if [ -z "$PY_CMD" ]; then
    for cmd in python3 python python3.12 python3.11 python3.10; do
        if command -v "$cmd" >/dev/null 2>&1; then
            if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
                PY_CMD="$cmd"
                break
            fi
        fi
    done
fi

if [ -z "$PY_CMD" ]; then
    echo "======================================================================"
    echo " [ERROR] Python 3.10 or higher is required but was not found!"
    echo "======================================================================"
    echo " Please install Python from https://www.python.org/downloads/"
    echo " or via Homebrew: brew install python"
    echo "======================================================================"
    echo ""
    read -p "Press [Enter] to exit..."
    exit 1
fi

# 2. Setup virtual environment (.venv) if missing
if [ ! -f "$DIR/.venv/bin/python" ]; then
    echo "Creating Python virtual environment in .venv ..."
    "$PY_CMD" -m venv "$DIR/.venv" || true
    if [ -f "$DIR/.venv/bin/python" ]; then
        PY_CMD="$DIR/.venv/bin/python"
    fi
else
    PY_CMD="$DIR/.venv/bin/python"
fi

# 3. Check & install dependencies
if ! "$PY_CMD" -c "import fastapi, uvicorn, pydantic, httpx, numpy, pandas, sklearn" >/dev/null 2>&1; then
    echo "Installing required Python packages (first run only) ..."
    "$PY_CMD" -m pip install -r requirements.txt
fi

# 4. Check if server already running & healthy
if curl -s -f "http://127.0.0.1:8765/health" >/dev/null 2>&1; then
    echo "CrowdWise is already running at http://127.0.0.1:8765/"
    open "http://127.0.0.1:8765/"
    exit 0
fi

# Find free port starting from 8765
PORT=8765
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
    PORT=$((PORT + 1))
done

export PORT=$PORT

# 5. Background watcher to open browser when /health is ready
(
    for i in {1..80}; do
        sleep 0.25
        if curl -s -f "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
            open "http://127.0.0.1:$PORT/"
            break
        fi
    done
) &

echo ""
echo "======================================================================"
echo "  CrowdWise is running at http://127.0.0.1:$PORT/"
echo "  Close this Terminal window to stop the application."
echo "======================================================================"
echo ""

"$PY_CMD" app.py
