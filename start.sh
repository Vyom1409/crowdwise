#!/bin/bash
# CrowdWise Linux Launcher (start.sh)
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "======================================================================"
echo "          CrowdWise - One-Click Application Launcher (Linux)"
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
    echo " Please install Python via your package manager:"
    echo "   Ubuntu/Debian: sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    echo "   Fedora:        sudo dnf install -y python3 python3-pip"
    echo "   Arch Linux:    sudo pacman -S python python-pip"
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
if command -v curl >/dev/null 2>&1 && curl -s -f "http://127.0.0.1:8765/health" >/dev/null 2>&1; then
    echo "CrowdWise is already running at http://127.0.0.1:8765/"
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "http://127.0.0.1:8765/"
    fi
    exit 0
fi

# Find free port starting from 8765
PORT=8765
while command -v ss >/dev/null 2>&1 && ss -lnt "( sport = :$PORT )" | grep -q ":$PORT"; do
    PORT=$((PORT + 1))
done

export PORT=$PORT

# 5. Background watcher to open browser when /health is ready
(
    for i in {1..80}; do
        sleep 0.25
        if command -v curl >/dev/null 2>&1 && curl -s -f "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
            if command -v xdg-open >/dev/null 2>&1; then
                xdg-open "http://127.0.0.1:$PORT/"
            fi
            break
        fi
    done
) &

echo ""
echo "======================================================================"
echo "  CrowdWise is running at http://127.0.0.1:$PORT/"
echo "  Close this terminal window to stop the application."
echo "======================================================================"
echo ""

"$PY_CMD" app.py
