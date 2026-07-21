#!/usr/bin/env bash
#
# One-command launcher for the Personal Study Agent.
#
# Builds the React frontend, installs the Python backend, and starts a single
# server that serves BOTH the UI and the API on one port. Open the printed URL
# in any browser - including your phone's, if it's on the same network (use the
# machine's LAN IP instead of localhost).
#
#   ./run.sh              # builds if needed, serves on http://0.0.0.0:8000
#   PORT=9000 ./run.sh    # pick a different port
#   SKIP_BUILD=1 ./run.sh # reuse an existing frontend build (faster restarts)
#
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${PORT:-8000}"

# --- frontend build ---------------------------------------------------------
if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  echo "==> Building frontend..."
  cd "$HERE/frontend"
  if [[ ! -d node_modules ]]; then
    npm install
  fi
  npm run build
fi

# --- backend setup ----------------------------------------------------------
echo "==> Setting up backend..."
cd "$HERE/backend"
if [[ ! -d venv ]]; then
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Best-effort: pull the real NLP models for stronger de-identification and
# concept extraction. If the network blocks these (some sandboxes do), the app
# still runs on its built-in fallbacks - so we never fail the launch on this.
if [[ "${SKIP_MODELS:-0}" != "1" ]]; then
  echo "==> Fetching NLP models (best-effort)..."
  python -m spacy download en_core_web_sm || echo "   (spaCy model unavailable - using fallback)"
  pip install --quiet \
    "https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_md-0.5.4.tar.gz" \
    || echo "   (scispaCy model unavailable - using fallback)"
fi

# --- launch -----------------------------------------------------------------
echo ""
echo "==> Study Agent is starting on http://0.0.0.0:${PORT}"
echo "    Open http://localhost:${PORT} on this machine,"
echo "    or http://<this-machine-LAN-IP>:${PORT} from your phone on the same network."
echo ""
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
