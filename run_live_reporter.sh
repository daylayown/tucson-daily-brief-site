#!/usr/bin/env bash
#
# Shell wrapper for the live AI reporter pipeline.
# Loads environment variables, validates dependencies, and passes args through.
#
# Usage:
#   ./run_live_reporter.sh "https://youtube.com/watch?v=XXX" --slug pentagon-2026-03-26
#   ./run_live_reporter.sh "https://stream.swagit.com/.../playlist.m3u8" --slug ov-2026-04-08 --direct
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

# --- Check for --direct flag ---
DIRECT_MODE=0
for arg in "$@"; do
    if [[ "$arg" == "--direct" ]]; then
        DIRECT_MODE=1
        break
    fi
done

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

if [ "$DIRECT_MODE" -eq 0 ] && ! command -v streamlink &>/dev/null; then
    echo "ERROR: streamlink not found. Run: pip install streamlink" >&2
    missing=1
fi

if ! command -v ffmpeg &>/dev/null; then
    echo "ERROR: ffmpeg not found. Install ffmpeg." >&2
    missing=1
fi

PYTHON="${SCRIPT_DIR}/.venv/bin/python3"
if [ ! -x "$PYTHON" ]; then
    echo "ERROR: venv not found at ${SCRIPT_DIR}/.venv" >&2
    echo "  Run: python -m venv .venv && .venv/bin/pip install deepgram-sdk" >&2
    missing=1
elif ! "$PYTHON" -c "import deepgram" 2>/dev/null; then
    echo "ERROR: deepgram-sdk not installed. Run: .venv/bin/pip install deepgram-sdk" >&2
    missing=1
fi

if [ "$missing" -eq 1 ]; then
    exit 1
fi

# --- Wait for stream to go live (if not already) ---
# In direct mode, skip yt-dlp polling — ffmpeg will connect to the URL directly
# and block/retry on its own. For streamlink mode, poll with yt-dlp.
if [ "$DIRECT_MODE" -eq 0 ]; then
    WAIT_INTERVAL=60
    WAIT_MAX=1800  # 30 minutes

    url=""
    for arg in "$@"; do
        if [[ "$arg" == http* ]]; then
            url="$arg"
            break
        fi
    done

    if [ -n "$url" ]; then
        elapsed=0
        while ! yt-dlp --simulate "$url" &>/dev/null; do
            if [ "$elapsed" -ge "$WAIT_MAX" ]; then
                echo "ERROR: Stream not live after ${WAIT_MAX}s, giving up: $url" >&2
                exit 1
            fi
            echo "$(date): Stream not live yet, retrying in ${WAIT_INTERVAL}s... ($url)"
            sleep "$WAIT_INTERVAL"
            elapsed=$((elapsed + WAIT_INTERVAL))
        done
        echo "$(date): Stream is live, starting reporter: $url"
    fi
else
    echo "$(date): Direct mode — skipping stream polling, ffmpeg will connect directly"
fi

# --- Run ---
cd "$SCRIPT_DIR"
exec "$PYTHON" ai_reporter_live.py "$@"
