#!/usr/bin/env bash
#
# Generate the weekly TDB Weekly newsletter draft and upload it to Buttondown.
#
# NOT cron'd. This is the final step of the manual Saturday ritual: generate and
# review this week's Tucson Mini crossword together FIRST (it's the newsletter's
# subscriber perk), lock it in, then run this. generate_newsletter.py hard-stops
# if no puzzle is locked for the send date, so a puzzle-less draft can't ship.
# The uploaded draft sits in Buttondown for review and is manually scheduled for
# the Sunday 5am send.
#
# Usage:
#   ./run_newsletter.sh              # full run: generate + upload
#   ./run_newsletter.sh --dry-run    # generator runs in dry-run mode, no upload

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
