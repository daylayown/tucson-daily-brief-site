#!/usr/bin/env bash
#
# Shell wrapper for the live AI reporter pipeline.
# Loads environment variables, validates dependencies, and passes args through.
#
# Usage:
#   ./run_live_reporter.sh "https://youtube.com/watch?v=XXX" --slug pentagon-2026-03-26
#   ./run_live_reporter.sh "https://youtube.com/watch?v=XXX" --slug test-1 --transcribe-only

set -euo pipefail

# --- Load environment variables ---
set -a
for conf in "$HOME/.config/environment.d/"*.conf; do
    [ -f "$conf" ] && source "$conf"
done
set +a

# --- Config ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Validate dependencies ---
missing=0

if [ -z "${DEEPGRAM_API_KEY:-}" ]; then
    echo "ERROR: DEEPGRAM_API_KEY not set" >&2
    echo "  Add it to ~/.config/environment.d/deepgram.conf" >&2
    missing=1
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "ERROR: ANTHROPIC_API_KEY not set" >&2
    missing=1
fi

if ! command -v streamlink &>/dev/null; then
    echo "ERROR: streamlink not found. Run: pip install streamlink" >&2
    missing=1
fi

if ! command -v ffmpeg &>/dev/null; then
    echo "ERROR: ffmpeg not found. Install ffmpeg." >&2
    missing=1
fi

if ! python3 -c "import deepgram" 2>/dev/null; then
    echo "ERROR: deepgram-sdk not installed. Run: pip install deepgram-sdk" >&2
    missing=1
fi

if [ "$missing" -eq 1 ]; then
    exit 1
fi

# --- Run ---
cd "$SCRIPT_DIR"
exec python3 ai_reporter_live.py "$@"
