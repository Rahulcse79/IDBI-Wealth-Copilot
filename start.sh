#!/usr/bin/env bash
#
# IDBI Wealth Copilot — one-command launcher.
#
# Usage:
#   ./start.sh           # set up (if needed) and run the app on http://127.0.0.1:8000
#   ./start.sh test      # set up and run the test suite
#   ./start.sh setup     # only create the venv + install dependencies
#
# Provide an Anthropic credential to enable the conversational copilot:
#   export ANTHROPIC_API_KEY=sk-ant-...    (or run `ant auth login`)
# The quick-action demos work without a key.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"
PORT="${PORT:-8000}"
HOST="${HOST:-localhost}"

cd "$BACKEND_DIR"

# Pick a Python 3 interpreter.
PYTHON_BIN="$(command -v python3 || command -v python)"
if [ -z "$PYTHON_BIN" ]; then
  echo "✗ Python 3 not found. Install Python 3.9+ and retry." >&2
  exit 1
fi

setup() {
  if [ ! -d "$VENV_DIR" ]; then
    echo "→ Creating virtual environment…"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  echo "→ Installing dependencies…"
  python -m pip install --quiet --upgrade pip
  python -m pip install --quiet -r requirements.txt
  echo "→ Generating synthetic dataset…"
  python -m data.generate >/dev/null
  echo "✓ Setup complete."
}

ensure_active() {
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
}

case "${1:-run}" in
  setup)
    setup
    ;;
  test)
    [ -d "$VENV_DIR" ] || setup
    ensure_active
    echo "→ Running tests…"
    pytest
    ;;
  run)
    [ -d "$VENV_DIR" ] || setup
    ensure_active
    if python -c "import os,sys; sys.exit(0 if (os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_AUTH_TOKEN')) else 1)"; then
      echo "✓ Anthropic credential detected — conversational copilot enabled."
    else
      echo "ℹ No Anthropic key — running in demo mode (quick actions work; free-text chat is disabled)."
    fi
    echo "→ Starting IDBI Wealth Copilot at http://$HOST:$PORT  (Ctrl+C to stop)"
    exec uvicorn app.main:app --host "$HOST" --port "$PORT"
    ;;
  *)
    echo "Usage: ./start.sh [run|test|setup]" >&2
    exit 1
    ;;
esac
