#!/usr/bin/env bash
#
# Check for new government meeting agendas across four municipalities,
# generate AI previews, and auto-publish them to the site. Runs daily via cron.
#
# Municipalities: Pima County BOS, Marana, Oro Valley, City of Tucson
# Flow: check APIs/sites → Claude analysis → markdown preview → HTML → git push
# Sends a Telegram notification after each preview is published.
#
# Usage: ./check_agendas.sh
#
# Cron example (daily at 8 AM MST):
#   0 8 * * * ~/claude-code-projects/tucson-daily-brief-site/check_agendas.sh >> /tmp/agenda-check.log 2>&1

set -euo pipefail

# --- Load environment variables ---
set -a
for conf in "$HOME/.config/environment.d/"*.conf; do
    [ -f "$conf" ] && source "$conf"
done
set +a

# --- Config ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENDA_WATCH_DIR="$SCRIPT_DIR/agenda-watch"
SEND_TELEGRAM="$HOME/.openclaw/skills/tucson-daily-brief/scripts/send_telegram.py"

cd "$SCRIPT_DIR"

echo "$(date): Checking for new agendas..."

PREVIEWS=""

# --- Pima County BOS (Legistar API) ---
echo "Checking Pima County BOS..."
OUTPUT=$(python3 agenda_mining.py 2>&1) || true
echo "$OUTPUT"
PREVIEWS="$PREVIEWS
$(echo "$OUTPUT" | grep "Saved publishable preview:" | sed 's/.*Saved publishable preview: //' || true)"

# --- Marana Town Council (Destiny Hosted) ---
echo "Checking Marana Town Council..."
OUTPUT=$(python3 agenda_mining_marana.py 2>&1) || true
echo "$OUTPUT"
PREVIEWS="$PREVIEWS
$(echo "$OUTPUT" | grep "Saved publishable preview:" | sed 's/.*Saved publishable preview: //' || true)"

# --- Oro Valley Town Council (Destiny Hosted / Granicus) ---
echo "Checking Oro Valley Town Council..."
OUTPUT=$(python3 agenda_mining_orovalley.py 2>&1) || true
echo "$OUTPUT"
PREVIEWS="$PREVIEWS
$(echo "$OUTPUT" | grep "Saved publishable preview:" | sed 's/.*Saved publishable preview: //' || true)"

# --- City of Tucson Mayor & Council (Hyland OnBase / PDF) ---
echo "Checking City of Tucson..."
OUTPUT=$(python3 agenda_mining_tucson.py 2>&1) || true
echo "$OUTPUT"
PREVIEWS="$PREVIEWS
$(echo "$OUTPUT" | grep "Saved publishable preview:" | sed 's/.*Saved publishable preview: //' || true)"

# Clean up empty lines
PREVIEWS=$(echo "$PREVIEWS" | sed '/^$/d')

if [ -z "$PREVIEWS" ]; then
    echo "No new previews generated."
    exit 0
fi

# Auto-publish each new preview and notify via Telegram
PUBLISHED=0

while IFS= read -r preview_path; do
    if [ -f "$preview_path" ]; then
        # Extract the meeting date from the filename
        meeting_date=$(echo "$preview_path" | grep -oP '\d{4}-\d{2}-\d{2}')

        # Determine which municipality from the filename
        if echo "$preview_path" | grep -q "marana"; then
            body_name="Marana Town Council"
            publish_cmd="python3 agenda_mining_marana.py --publish $preview_path"
        elif echo "$preview_path" | grep -q "orovalley"; then
            body_name="Oro Valley Town Council"
            publish_cmd="python3 agenda_mining_orovalley.py --publish $preview_path"
        elif echo "$preview_path" | grep -q "tucson"; then
            body_name="Tucson Mayor & Council"
            publish_cmd="python3 agenda_mining_tucson.py --publish $preview_path"
        else
            body_name="Pima County BOS"
            publish_cmd="python3 agenda_mining.py --publish $preview_path"
        fi

        # Publish the preview to HTML
        echo "Publishing $body_name preview for $meeting_date..."
        if eval "$publish_cmd"; then
            echo "Published: $preview_path"
            PUBLISHED=$((PUBLISHED + 1))

            # Send Telegram notification (informational — already published)
            NOTIFY_MSG="📋 $body_name meeting preview published for $meeting_date

A new \"What to Watch\" preview has been auto-published to Tucson Daily Brief.

View it at: https://tucsondailybrief.com/meeting-watch/"

            TMPFILE=$(mktemp /tmp/agenda-notify-XXXXX.md)
            echo "$NOTIFY_MSG" > "$TMPFILE"

            if [ -f "$SEND_TELEGRAM" ]; then
                python3 "$SEND_TELEGRAM" "$TMPFILE" || echo "WARNING: Telegram notification failed (non-fatal)"
            else
                echo "WARNING: send_telegram.py not found, skipping notification"
            fi

            rm -f "$TMPFILE"
        else
            echo "ERROR: Failed to publish $preview_path"
        fi
    fi
done <<< "$PREVIEWS"

# Git commit and push if anything was published
if [ "$PUBLISHED" -gt 0 ]; then
    echo "Committing and pushing $PUBLISHED new preview(s)..."
    git add -A
    git commit -m "Auto-publish meeting preview(s) for $(date +%Y-%m-%d)"
    git push
    echo "Pushed to GitHub Pages."
fi

echo "$(date): Done."
