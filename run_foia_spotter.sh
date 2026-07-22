#!/usr/bin/env bash
#
# Weekly FOIA Lead Spotter run — trawl published news reports for
# public-records-request leads and draft the request emails.
# Drafts land in records-requests/drafts/ (local only); Telegram notifies.
#
# Cron (Mondays 9:30 AM MST):
#   30 9 * * 1 ~/claude-code-projects/tucson-daily-brief-site/run_foia_spotter.sh >> /tmp/foia-spotter.log 2>&1

set -uo pipefail

# --- Load environment variables (ANTHROPIC_API_KEY, Telegram creds) ---
set -a
for conf in "$HOME/.config/environment.d/"*.conf; do
    [ -f "$conf" ] && source "$conf"
done
set +a

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== FOIA Lead Spotter run: $(date) ==="
python3 "$SCRIPT_DIR/foia_lead_spotter.py"
echo "=== Done: $(date) ==="
