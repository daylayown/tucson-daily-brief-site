#!/usr/bin/env bash
#
# Daily A/B: run the challenger model on the same prompt the published brief was
# built from. Publishes nothing — output lands in model-ab/ for side-by-side
# reading. See brief_model_ab.py for why this is paired rather than alternating.
#
# Cron (daily 6:05 AM MST, after run_brief.sh writes the canonical brief):
#   5 6 * * * ~/claude-code-projects/tucson-daily-brief-site/run_brief_ab.sh >> /tmp/brief-ab.log 2>&1

set -uo pipefail
set -a
for conf in "$HOME/.config/environment.d/"*.conf; do
    [ -f "$conf" ] && source "$conf"
done
set +a

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== Model A/B run: $(date) ==="
"$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/brief_model_ab.py"
echo "=== Done: $(date) ==="
