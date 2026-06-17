#!/usr/bin/env bash
#
# Poll the City of Tucson Water advisory feed and archive it to
# data/outages.sqlite. First feature of the Responsiveness Index
# "Heat/Water/Power" archive. See poll_tucson_water.py for details.
#
# Cron example (every 30 minutes):
#   */30 * * * * ~/claude-code-projects/tucson-daily-brief-site/run_water_poll.sh >> /tmp/water-poll.log 2>&1
#
# Note: this is an always-on poller — a closed laptop lid = a gap in the
# archive (recorded as downtime in the water_poll_run table). This is exactly
# the kind of process the "Move TDB off the laptop" Stage 2 roadmap absorbs.

set -euo pipefail

# --- Load environment variables (Telegram creds for notifications) ---
set -a
for conf in "$HOME/.config/environment.d/"*.conf; do
    [ -f "$conf" ] && source "$conf"
done
set +a

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== water poll $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
exec .venv/bin/python3 poll_tucson_water.py "$@"
