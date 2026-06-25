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
echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') daily brief run ==="
.venv/bin/python3 generate_brief.py --date "$TODAY"
