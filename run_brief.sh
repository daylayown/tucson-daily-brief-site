#!/usr/bin/env bash
# run_brief.sh — PRODUCTION daily-brief generator.
#
# Replaces the OpenClaw 6 AM briefing agent (disabled 2026-06-25 in
# ~/.openclaw/cron/jobs.json). Deterministic: generate_brief.py reads
# sources.json + EDITOR-TIPS.md, fetches every feed, runs ONE Sonnet synthesis
# call, and writes the CANONICAL brief that run_podcast.sh (6:10) consumes:
#   ~/.openclaw/workspace/briefings/tucson-brief-YYYY-MM-DD.md
#
# generate_brief.py writes that canonical path by default (no --out), via
# open().write() — so the OpenClaw save-to-wrong-path bug is structurally gone.
set -euo pipefail

REPO="$HOME/claude-code-projects/tucson-daily-brief-site"
TODAY="$(date +%Y-%m-%d)"

# Load API keys the same way the other cron wrappers do.
for conf in "$HOME"/.config/environment.d/*.conf; do
  [ -f "$conf" ] && set -a && . "$conf" && set +a
done

cd "$REPO"

# Retry on failure. The 6 AM run shares the laptop's network; a transient DNS
# blip at 6:00 makes every source fetch fail, generate_brief.py sees 0 items and
# aborts with exit 1 (correctly — it refuses to publish an empty brief), and the
# whole day's chain stalls (run_podcast at 6:10 waits 10 min for a brief that
# never lands). Retrying a few times lets a short outage self-heal before the
# 6:20 podcast deadline. Safe to retry: the brief is only written AFTER a
# successful synthesis call, so a failed attempt wrote nothing.
MAX_ATTEMPTS="${BRIEF_MAX_ATTEMPTS:-5}"
RETRY_DELAY="${BRIEF_RETRY_DELAY:-60}"

attempt=1
while true; do
  echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') daily brief run (attempt $attempt/$MAX_ATTEMPTS) ==="
  rc=0
  .venv/bin/python3 generate_brief.py --date "$TODAY" || rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "=== brief generated on attempt $attempt ==="
    break
  fi
  if [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
    echo "=== brief FAILED after $MAX_ATTEMPTS attempts (last exit $rc) — giving up ===" >&2
    exit "$rc"
  fi
  echo "--- attempt $attempt failed (exit $rc); retrying in ${RETRY_DELAY}s (likely transient network/DNS) ---" >&2
  sleep "$RETRY_DELAY"
  attempt=$((attempt + 1))
done
