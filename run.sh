#!/usr/bin/env bash
set -e

# ─── BEU Result Intelligence Assistant ───
# Quick-start script: sets up venv, installs deps, and launches the server.

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

VENV_DIR=".venv"
PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

# ── 1. Create virtual environment if missing ──
if [ ! -d "$VENV_DIR" ]; then
  echo "🔧  Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

# ── 2. Activate virtual environment ──
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# ── 3. Install / update dependencies ──
echo "📦  Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# ── 4. Ensure .env exists ──
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo "⚠️   Created .env from .env.example — please fill in your API keys before first use."
  else
    echo "⚠️   No .env file found. The app may fail without required environment variables."
  fi
fi

# ── 5. Launch the server ──
echo ""
echo "🚀  Starting BEU Result Intelligence Assistant on http://$HOST:$PORT"
echo "    Press Ctrl+C to stop."
echo ""
uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
