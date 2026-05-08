#!/usr/bin/env bash
#
# Generate the weekly TDB Weekly newsletter draft and upload it to Buttondown.
# Runs Friday at 6pm via cron; the draft sits in Buttondown for editorial
# review over the weekend and is manually scheduled for Sunday 5am send.
#
# Usage:
#   ./run_newsletter.sh              # full run: generate + upload
#   ./run_newsletter.sh --dry-run    # generator runs in dry-run mode, no upload
#
# Cron (Fridays at 6 PM MST):
#   0 18 * * 5 ~/claude-code-projects/tucson-daily-brief-site/run_newsletter.sh >> /tmp/newsletter-gen.log 2>&1

set -euo pipefail

# --- Load environment variables (ANTHROPIC_API_KEY, BUTTONDOWN_API_KEY) ---
set -a
for conf in "$HOME/.config/environment.d/"*.conf; do
    [ -f "$conf" ] && source "$conf"
done
set +a

# --- Config ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/.venv/bin/python3"
DRAFTS_DIR="$SCRIPT_DIR/newsletter/drafts"
DRY_RUN=0

if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=1
fi

cd "$SCRIPT_DIR"

echo "================================================"
echo "$(date): TDB Weekly newsletter generation start"
echo "================================================"

# --- Step 1: Generate the markdown draft ---
echo
echo "Step 1/2: generate_newsletter.py"
if [ "$DRY_RUN" = 1 ]; then
    "$PYTHON" generate_newsletter.py --dry-run
    echo
    echo "DRY RUN — skipping upload step."
    exit 0
fi

"$PYTHON" generate_newsletter.py --force

# --- Step 2: Upload to Buttondown ---
LATEST_DRAFT=$(ls -t "$DRAFTS_DIR"/tdb-weekly-*.md 2>/dev/null | head -1)
if [ -z "$LATEST_DRAFT" ]; then
    echo "ERROR: no draft file found in $DRAFTS_DIR after generation" >&2
    exit 1
fi

echo
echo "Step 2/2: upload_to_buttondown.py"
echo "Draft file: $LATEST_DRAFT"
"$PYTHON" upload_to_buttondown.py "$LATEST_DRAFT"

echo
echo "$(date): Done"
