#!/usr/bin/env bash
# run_brief_compare.sh — SHADOW run of the deterministic generate_brief.py.
#
# Purpose: during the OpenClaw -> deterministic cutover, run generate_brief.py
# every morning alongside the live 6 AM OpenClaw agent and write its output to a
# SHADOW directory so we can diff the two briefs before trusting the new path.
#
# SAFETY: writes ONLY to $SHADOW_DIR, which is deliberately NOT the canonical
# ~/.openclaw/workspace/briefings/ dir nor the ~/.openclaw/workspace/briefs/
# mis-save dir that run_podcast.sh's resolve_brief() globs. So this can never be
# mistaken for the real brief by the 6:10 podcast/blog pipeline.
#
# Remove the crontab line that calls this once the cutover is done.
set -euo pipefail

REPO="$HOME/claude-code-projects/tucson-daily-brief-site"
SHADOW_DIR="$HOME/tdb-brief-shadow"
TODAY="$(date +%Y-%m-%d)"

# Load API keys the same way the other cron wrappers do.
for conf in "$HOME"/.config/environment.d/*.conf; do
  [ -f "$conf" ] && set -a && . "$conf" && set +a
done

mkdir -p "$SHADOW_DIR"
cd "$REPO"

echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') shadow brief run ==="
.venv/bin/python3 generate_brief.py --date "$TODAY" --out "$SHADOW_DIR/tucson-brief-${TODAY}.md"
echo "Shadow brief written to $SHADOW_DIR/tucson-brief-${TODAY}.md"
echo "Compare against canonical: ~/.openclaw/workspace/briefings/tucson-brief-${TODAY}.md"
