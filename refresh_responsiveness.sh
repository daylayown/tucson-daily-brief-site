#!/usr/bin/env bash
#
# Re-render the live Heat/Water/Power panel in responsiveness.html from the
# archived utility data (data/outages.sqlite) and commit/push if it changed.
#
# Runs once daily so the PUBLIC dashboard stays current without churning git on
# every 30-min poll. The poller (run_water_poll.sh, */30) keeps the DB fresh;
# this just bakes a daily snapshot into the static page and keeps the
# "Updated ..." stamp honest.
#
# Cron (daily, 9:05 AM MST — after the 8:00 agenda check + 8:45 Ask refresh):
#   5 9 * * * ~/claude-code-projects/tucson-daily-brief-site/refresh_responsiveness.sh >> /tmp/responsiveness-refresh.log 2>&1

set -euo pipefail

# --- Load environment variables (parity with the other cron wrappers) ---
set -a
for conf in "$HOME/.config/environment.d/"*.conf; do
    [ -f "$conf" ] && source "$conf"
done
set +a

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== responsiveness refresh $(date '+%Y-%m-%d %H:%M:%S %Z') ==="

.venv/bin/python3 render_responsiveness.py

# Commit ONLY responsiveness.html, even if other files are dirty, so this never
# sweeps up unrelated working changes.
if git diff --quiet -- responsiveness.html; then
    echo "No change to responsiveness.html — nothing to commit."
else
    git add responsiveness.html
    git commit -q -m "Refresh Responsiveness water dashboard ($(date '+%Y-%m-%d'))"
    git push
    echo "Dashboard updated — committed and pushed."
fi
