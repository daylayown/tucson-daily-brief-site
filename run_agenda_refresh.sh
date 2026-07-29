#!/usr/bin/env bash
#
# Day-of agenda refresh — re-mine reference material for meetings happening
# today and alert on any document added or revised since the preview ran.
#
# Why this exists: the 8 AM check_agendas.sh run writes a preview once and then
# skips the meeting forever. Agenda documents keep moving after that. On
# 2026-07-28 the county administrator filed a revised IDA membership slate at
# ~3:29 PM on 7/27 — five days after the preview was generated and about 26
# hours before the vote. Nothing in the pipeline saw it, so the post-meeting
# drafter wrote the report without it and the appointee names had to be
# reconstructed from audio.
#
# This run refreshes agenda-watch/<base>-full.md and <base>-attachments.md,
# which ai_reporter.py reads as source context, and Telegrams what changed.
# It deliberately does NOT touch the published preview — a revised memo is a
# heads-up for the human, not a trigger to silently rewrite a live page.
#
# Pima County only. Marana, Oro Valley and Tucson are scraped rather than
# served by a Legistar API, so they have no attachment feed to diff.
#
# Cron (daily 9:15 AM MST, after the 8:00 agenda check and 8:45 index refresh):
#   15 9 * * * ~/claude-code-projects/tucson-daily-brief-site/run_agenda_refresh.sh >> /tmp/agenda-refresh.log 2>&1

set -uo pipefail

# --- Load environment variables (Telegram creds; no LLM call in this path) ---
set -a
for conf in "$HOME/.config/environment.d/"*.conf; do
    [ -f "$conf" ] && source "$conf"
done
set +a

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Agenda day-of refresh: $(date) ==="
python3 "$SCRIPT_DIR/agenda_mining.py" --refresh
echo "=== Done: $(date) ==="
