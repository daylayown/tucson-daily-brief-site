#!/usr/bin/env bash
# run_bluesky_post.sh — catch-all cron wrapper for the Bluesky ledger-diff
# poster (social/bluesky_poster.py, SOCIAL-AUTOPOST.md Part 3).
#
# The poster also runs at the end of check_agendas.sh (8 AM). These catch-all
# runs pick up everything published outside that window: the 6:10 daily brief,
# human-approved news reports published ad hoc during the day, and anything a
# failed earlier run left behind. Idempotent by construction (ledger diff), so
# overlapping schedules are safe.
set -euo pipefail

REPO="$HOME/claude-code-projects/tucson-daily-brief-site"

# Load credentials the same way the other cron wrappers do.
for conf in "$HOME"/.config/environment.d/*.conf; do
  [ -f "$conf" ] && set -a && . "$conf" && set +a
done

cd "$REPO"
echo "$(date): Bluesky catch-all run"
python3 social/bluesky_poster.py
echo "$(date): Done."
