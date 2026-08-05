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

# --- Non-fatal stage failures -----------------------------------------------
# Every pipeline below is invoked with `|| record_failure ...` so one broken
# stage never blocks the others. But "non-fatal" used to also mean "invisible":
# every Telegram notification in this script fires on *success* only, so a dead
# poller left no trace except a traceback in /tmp/agenda-check.log that nobody
# reads. Marana's dev-watch ArcGIS layer was unpublished and went unnoticed
# until 2026-08-01 for exactly that reason.
#
# record_failure remembers what broke and keeps going; the EXIT trap reports it
# once at the end. The trap fires on *every* exit path, so it also catches an
# unexpected `set -e` abort — the failure mode that stranded the 8 AM output on
# 2026-08-01, where publishing had already happened but the git push never ran.
FAILURES=""

record_failure() {
    local stage="$1"
    local out="${2:-}"
    local detail
    detail=$(printf '%s\n' "$out" | sed '/^[[:space:]]*$/d' | tail -3)
    echo "ERROR: $stage FAILED (non-fatal — continuing)"
    FAILURES="${FAILURES}• ${stage}
${detail}

"
    return 0
}

report_failures() {
    local rc=$?
    if [ -z "$FAILURES" ] && [ "$rc" -eq 0 ]; then
        return 0
    fi

    local MSG="⚠️ AGENDA PIPELINE — stage failure

check_agendas.sh reported problems on $(date '+%Y-%m-%d %H:%M %Z')."

    if [ -n "$FAILURES" ]; then
        MSG="${MSG}

Failed stage(s):
${FAILURES}"
    fi

    if [ "$rc" -ne 0 ]; then
        MSG="${MSG}
The script exited abnormally (code ${rc}). Anything after the failing stage did
not run — including the git push, so published output may still be sitting
uncommitted in the working tree."
    fi

    MSG="${MSG}
Full log: /tmp/agenda-check.log"

    local TMPFILE
    TMPFILE=$(mktemp /tmp/agenda-fail-XXXXX.md)
    printf '%s\n' "$MSG" > "$TMPFILE"
    if [ -f "$SEND_TELEGRAM" ]; then
        python3 "$SEND_TELEGRAM" "$TMPFILE" || echo "WARNING: failure-alert Telegram failed"
    fi
    rm -f "$TMPFILE"
    return 0
}
trap report_failures EXIT

# Fire a distinct, louder Telegram for high-interest topic flags (data centers,
# etc.) that the dev-watch pollers emit as `TOPIC-ALERT` lines. This is on top
# of the routine development-count notice — these items get human eyes fast.
# Arg: the captured stdout of a dev_watch_*.py run.
send_topic_alerts() {
    local out="$1"
    local alerts
    alerts=$(printf '%s\n' "$out" | grep '^TOPIC-ALERT' || true)
    [ -z "$alerts" ] && return 0

    local body=""
    while IFS=$'\t' read -r _tag _topic muni title url; do
        [ -z "$title" ] && continue
        body="${body}• ${muni}: ${title}
  ${url}
"
    done <<< "$alerts"

    local MSG="🛰️ DATA CENTER WATCH — high-interest application surfaced

A data-center-related land-use application was just auto-published to Around Town. Data centers are a live Southern AZ flashpoint (power · water · growth) — consider fast-tracking human coverage.

${body}
Discovery: town ArcGIS land-use feed. Documents: town permit portal (eTRAKiT)."

    local TMPFILE
    TMPFILE=$(mktemp /tmp/topic-alert-XXXXX.md)
    printf '%s\n' "$MSG" > "$TMPFILE"
    if [ -f "$SEND_TELEGRAM" ]; then
        python3 "$SEND_TELEGRAM" "$TMPFILE" || echo "WARNING: Topic-alert Telegram notification failed (non-fatal)"
    fi
    rm -f "$TMPFILE"
}

cd "$SCRIPT_DIR"

echo "$(date): Checking for new agendas..."

PREVIEWS=""

# --- Pima County BOS (Legistar API) ---
echo "Checking Pima County BOS..."
OUTPUT=$(python3 agenda_mining.py 2>&1) || record_failure "Pima County BOS agenda miner" "$OUTPUT"
echo "$OUTPUT"
PREVIEWS="$PREVIEWS
$(echo "$OUTPUT" | grep "Saved publishable preview:" | sed 's/.*Saved publishable preview: //' || true)"

# --- Marana Town Council (Destiny Hosted) ---
echo "Checking Marana Town Council..."
OUTPUT=$(python3 agenda_mining_marana.py 2>&1) || record_failure "Marana agenda miner" "$OUTPUT"
echo "$OUTPUT"
PREVIEWS="$PREVIEWS
$(echo "$OUTPUT" | grep "Saved publishable preview:" | sed 's/.*Saved publishable preview: //' || true)"

# --- Oro Valley Town Council (Destiny Hosted / Granicus) ---
echo "Checking Oro Valley Town Council..."
OUTPUT=$(python3 agenda_mining_orovalley.py 2>&1) || record_failure "Oro Valley agenda miner" "$OUTPUT"
echo "$OUTPUT"
PREVIEWS="$PREVIEWS
$(echo "$OUTPUT" | grep "Saved publishable preview:" | sed 's/.*Saved publishable preview: //' || true)"

# --- City of Tucson Mayor & Council (Hyland OnBase / PDF) ---
echo "Checking City of Tucson..."
OUTPUT=$(python3 agenda_mining_tucson.py 2>&1) || record_failure "City of Tucson agenda miner" "$OUTPUT"
echo "$OUTPUT"
PREVIEWS="$PREVIEWS
$(echo "$OUTPUT" | grep "Saved publishable preview:" | sed 's/.*Saved publishable preview: //' || true)"

# --- Sahuarita Unified Governing Board (Diligent + published board calendar) ---
# TDB's first school district. Runs as its own self-contained stage rather than
# feeding $PREVIEWS, because it differs from the municipal miners in two ways:
# it publishes its own preview inline, and it schedules the live reporter from
# the board's PUBLISHED annual calendar (schedule_recording.py --start) instead
# of having a model read a start time out of the agenda.
#
# Placed above the "no new previews" branch below, which was an `exit 0` when
# this stage was written (fixed 2026-08-04). The placement no longer matters for
# correctness, but it still reflects the requirement: this stage must run every
# day, because its whole advantage is scheduling a capture for a meeting weeks
# out, on days when no municipal agenda has dropped at all.
# Idempotent — re-running no-ops on both the `at` job and the preview.
echo "Checking Sahuarita Unified Governing Board..."
SAH_OUTPUT=$(python3 agenda_mining_sahuarita.py 2>&1) \
    || record_failure "Sahuarita governing board miner" "$SAH_OUTPUT"
echo "$SAH_OUTPUT"

# Clean up empty lines
PREVIEWS=$(echo "$PREVIEWS" | sed '/^$/d')

# No new previews is NOT a reason to stop. This used to be `exit 0`, which
# skipped all eight independent stages below — Spotted, the Marana DLLC poll,
# both dev-watch pollers, the Monday short, the geographic editions and the
# staleness check — none of which have anything to do with whether a council
# posted an agenda. They were added to this script after the guard existed and
# silently inherited it.
#
# It fired on most days, because the common case triggers it: the miners run
# fine, find the meetings, and report "Preview already exists." Three of the
# four runs in /tmp/agenda-check.log (Aug 1-4 2026) exited here. Aug 3 was a
# MONDAY, so that week's "Buried in the Agenda" Short and the geographic
# editions never published — and unlike the diff-based pollers, a Monday-gated
# job has no catch-up path; it waits a week.
#
# NOTE ON STYLE: the publish loop below is deliberately NOT indented into this
# else branch. Its body contains a multi-line NOTIFY_MSG string, and indenting
# those continuation lines would inject leading whitespace into the Telegram
# message. Bash does not care about the indentation; the message does.
if [ -z "$PREVIEWS" ]; then
    echo "No new previews to publish (continuing to the remaining stages)."
else

# Auto-publish each new preview and notify via Telegram
PUBLISHED=0

while IFS= read -r preview_path; do
    if [ -f "$preview_path" ]; then
        # Extract the meeting date from the filename
        meeting_date=$(echo "$preview_path" | grep -oP '\d{4}-\d{2}-\d{2}')

        # Determine which municipality from the filename (basename only,
        # not full path — full path contains "tucson-daily-brief-site" which
        # would falsely match every preview against the tucson check)
        preview_basename="$(basename "$preview_path")"
        if echo "$preview_basename" | grep -q "marana"; then
            body_name="Marana Town Council"
            municipality="marana"
            publish_cmd="python3 agenda_mining_marana.py --publish $preview_path"
        elif echo "$preview_basename" | grep -q "orovalley"; then
            body_name="Oro Valley Town Council"
            municipality="orovalley"
            publish_cmd="python3 agenda_mining_orovalley.py --publish $preview_path"
        elif echo "$preview_basename" | grep -q "tucson"; then
            body_name="Tucson Mayor & Council"
            municipality="tucson"
            publish_cmd="python3 agenda_mining_tucson.py --publish $preview_path"
        else
            body_name="Pima County BOS"
            municipality="pima-county"
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

View it at: https://tucsondailybrief.com/meeting-watch.html"

            TMPFILE=$(mktemp /tmp/agenda-notify-XXXXX.md)
            echo "$NOTIFY_MSG" > "$TMPFILE"

            if [ -f "$SEND_TELEGRAM" ]; then
                python3 "$SEND_TELEGRAM" "$TMPFILE" || echo "WARNING: Telegram notification failed (non-fatal)"
            else
                echo "WARNING: send_telegram.py not found, skipping notification"
            fi

            rm -f "$TMPFILE"

            # --- Auto-schedule live AI reporter recording ---
            # Gated by ENABLE_AUTO_SCHEDULE=1 while soak-testing. When enabled,
            # extracts public_session_start via Claude, queues an `at` job to
            # run run_live_reporter.sh shortly before the meeting, and sends a
            # Telegram notification. Non-fatal on failure.
            if [ "${ENABLE_AUTO_SCHEDULE:-0}" = "1" ]; then
                full_ref_path="${preview_path/-preview.md/-full.md}"
                if [ -f "$full_ref_path" ]; then
                    echo "Auto-scheduling live recording for $body_name ($municipality)..."
                    python3 schedule_recording.py "$preview_path" "$full_ref_path" "$municipality" \
                        || echo "WARNING: auto-scheduling failed for $preview_path (non-fatal)"
                else
                    echo "WARNING: full reference not found at $full_ref_path; skipping auto-schedule"
                fi
            fi
        else
            record_failure "Preview publish: $preview_path" ""
        fi
    fi
done <<< "$PREVIEWS"

fi   # end of the "new previews to publish" branch

# --- Public Record liquor license filings (post-process) ---
# Scans agenda-watch/*-full.md files produced by the four pipelines above,
# extracts liquor license items via Claude, and publishes them as filings
# under public-record/. Idempotent: each source file is processed once.
echo "Scanning for liquor license filings..."
PR_OUTPUT=$(python3 public_record_liquor.py 2>&1) || record_failure "Spotted: liquor filings (agenda scan)" "$PR_OUTPUT"
echo "$PR_OUTPUT"
PR_COUNT=$(echo "$PR_OUTPUT" | grep -oP 'published \K\d+(?= new filing)' | tail -1) || true
PR_COUNT=${PR_COUNT:-0}

if [ "$PR_COUNT" -gt 0 ]; then
    NOTIFY_MSG="🥂 $PR_COUNT new public record filing(s) published

New liquor license filings have been surfaced from this week's government meeting agendas and auto-published to Tucson Daily Brief.

View at: https://tucsondailybrief.com/public-record.html"

    TMPFILE=$(mktemp /tmp/pr-notify-XXXXX.md)
    echo "$NOTIFY_MSG" > "$TMPFILE"
    if [ -f "$SEND_TELEGRAM" ]; then
        python3 "$SEND_TELEGRAM" "$TMPFILE" || echo "WARNING: Public Record Telegram notification failed (non-fatal)"
    fi
    rm -f "$TMPFILE"
    PUBLISHED=$((PUBLISHED + PR_COUNT))
fi

# --- Spotted: Marana liquor licenses (state DLLC database poll) ---
# Marana never agendizes liquor licenses (handled administratively), so the
# agenda scan above can't see them. This poller enumerates Pima County
# licenses in the Arizona DLLC public database by license-number prefix,
# filters to Marana premises addresses, and diffs against
# public-record/.dllc_state_marana.json. First run seeds silently; after
# that, newly appearing Active licenses publish as Spotted filings. No AI
# calls — all fields are structured state records. Non-fatal on failure.
echo "Checking Marana liquor licenses (DLLC)..."
DLLC_OUTPUT=$(python3 public_record_liquor_dllc.py 2>&1) || record_failure "Spotted: Marana liquor licenses (DLLC)" "$DLLC_OUTPUT"
echo "$DLLC_OUTPUT"
DLLC_COUNT=$(echo "$DLLC_OUTPUT" | grep -oP 'DLLC Marana: published \K\d+' | tail -1) || true
DLLC_COUNT=${DLLC_COUNT:-0}

if [ "$DLLC_COUNT" -gt 0 ]; then
    NOTIFY_MSG="🥂 $DLLC_COUNT new Marana liquor license(s) published

Newly issued liquor license(s) at Marana addresses were surfaced from the Arizona DLLC license database and auto-published to Tucson Daily Brief. Marana handles these administratively, so they never appear on a council agenda.

View at: https://tucsondailybrief.com/public-record.html"

    TMPFILE=$(mktemp /tmp/dllc-notify-XXXXX.md)
    echo "$NOTIFY_MSG" > "$TMPFILE"
    if [ -f "$SEND_TELEGRAM" ]; then
        python3 "$SEND_TELEGRAM" "$TMPFILE" || echo "WARNING: DLLC Telegram notification failed (non-fatal)"
    fi
    rm -f "$TMPFILE"
    PUBLISHED=$((PUBLISHED + DLLC_COUNT))
fi

# --- Around Town: Oro Valley development cases (ArcGIS poll) ---
# Polls Oro Valley's public ArcGIS Development_Cases layer, diffs against prior
# state (around-town/.dev_state.json), and publishes new/changed cases under
# around-town/. Idempotent; non-fatal on failure. Feeds the combined Around
# Town feed (rebuilt internally via rebuild_homepage).
echo "Checking Oro Valley development cases..."
DEV_OUTPUT=$(python3 dev_watch_orovalley.py 2>&1) || record_failure "Around Town: Oro Valley development watch" "$DEV_OUTPUT"
echo "$DEV_OUTPUT"
send_topic_alerts "$DEV_OUTPUT"
DEV_COUNT=$(echo "$DEV_OUTPUT" | grep -oP 'Published/updated \K\d+' | tail -1) || true
DEV_COUNT=${DEV_COUNT:-0}

if [ "$DEV_COUNT" -gt 0 ]; then
    NOTIFY_MSG="🏗️ $DEV_COUNT new/updated Oro Valley development case(s)

New rezonings, variances, or development plans have been surfaced from Oro Valley's planning records and auto-published to Around Town.

View at: https://tucsondailybrief.com/around-town.html"

    TMPFILE=$(mktemp /tmp/dev-notify-XXXXX.md)
    echo "$NOTIFY_MSG" > "$TMPFILE"
    if [ -f "$SEND_TELEGRAM" ]; then
        python3 "$SEND_TELEGRAM" "$TMPFILE" || echo "WARNING: Around Town Telegram notification failed (non-fatal)"
    fi
    rm -f "$TMPFILE"
    PUBLISHED=$((PUBLISHED + DEV_COUNT))
fi

# --- Around Town: Marana development projects (ArcGIS poll) ---
# Polls Marana's public ArcGIS DS_Current_Projects_Live layer, diffs against
# prior state (around-town/.dev_state_marana.json), and publishes new/changed
# projects under around-town/. Idempotent; non-fatal on failure. Feeds the same
# combined Around Town feed.
echo "Checking Marana development projects..."
DEV_OUTPUT_MA=$(python3 dev_watch_marana.py 2>&1) || record_failure "Around Town: Marana development watch" "$DEV_OUTPUT_MA"
echo "$DEV_OUTPUT_MA"
send_topic_alerts "$DEV_OUTPUT_MA"
DEV_COUNT_MA=$(echo "$DEV_OUTPUT_MA" | grep -oP 'Published/updated \K\d+' | tail -1) || true
DEV_COUNT_MA=${DEV_COUNT_MA:-0}

if [ "$DEV_COUNT_MA" -gt 0 ]; then
    NOTIFY_MSG="🏗️ $DEV_COUNT_MA new/updated Marana development project(s)

New commercial, residential, or land-use projects have been surfaced from Marana's development records and auto-published to Around Town.

View at: https://tucsondailybrief.com/around-town.html"

    TMPFILE=$(mktemp /tmp/dev-notify-ma-XXXXX.md)
    echo "$NOTIFY_MSG" > "$TMPFILE"
    if [ -f "$SEND_TELEGRAM" ]; then
        python3 "$SEND_TELEGRAM" "$TMPFILE" || echo "WARNING: Around Town (Marana) Telegram notification failed (non-fatal)"
    fi
    rm -f "$TMPFILE"
    PUBLISHED=$((PUBLISHED + DEV_COUNT_MA))
fi

# Git commit and push if anything was published
if [ "$PUBLISHED" -gt 0 ]; then
    echo "Committing and pushing $PUBLISHED new item(s)..."
    # Stage only what the agenda + public-record pipelines produce — not
    # whatever else is in the working tree — so in-progress/manual edits aren't
    # swept into this auto-commit. agenda-watch/ holds the tracked reference
    # markdown; the rest are published HTML + rebuilt indexes. Update this list
    # if a pipeline starts writing new output paths.
    git add agenda-watch/ meeting-watch/ meeting-watch.html \
            public-record/ public-record.html \
            around-town/ around-town.html local-government.html \
            index.html briefings.html
    git commit -m "Auto-publish meeting preview(s) and public record filing(s) for $(date +%Y-%m-%d)" || true
    git push
    echo "Pushed to GitHub Pages."
fi

# --- Weekly "Buried in the Agenda" short (Mondays) ---
# Picks the most consequential under-the-radar item from this week's upcoming
# meeting previews, renders a vertical short, and publishes it to YouTube
# Shorts unattended (user call 2026-07-11: full-auto while YouTube-only, same
# posture as the daily Only in Tucson short). Runs AFTER the miners so
# freshly-generated previews are included. Skips cleanly on weeks with no
# upcoming meetings or no genuinely strong item. Non-fatal on failure.
if [ "$(date +%u)" = "1" ]; then
    echo "Monday: generating weekly 'Buried in the Agenda' short..."
    BIA_OUTPUT=$(python3 social/generate_agenda_short.py --publish 2>&1) || true
    echo "$BIA_OUTPUT"
    BIA_LINE=$(printf '%s\n' "$BIA_OUTPUT" | grep '^SHORT-PUBLISHED' | tail -1 || true)
    if [ -n "$BIA_LINE" ]; then
        IFS=$'\t' read -r _tag BIA_TITLE BIA_URL <<< "$BIA_LINE"
        NOTIFY_MSG="🎬 Buried in the Agenda short published (unreviewed)

This week's agenda short was auto-published to YouTube Shorts. Watch it and pull it if anything is off:

$BIA_TITLE
$BIA_URL"
        TMPFILE=$(mktemp /tmp/bia-notify-XXXXX.md)
        printf '%s\n' "$NOTIFY_MSG" > "$TMPFILE"
        if [ -f "$SEND_TELEGRAM" ]; then
            python3 "$SEND_TELEGRAM" "$TMPFILE" || echo "WARNING: BIA Telegram notification failed (non-fatal)"
        fi
        rm -f "$TMPFILE"
    fi
fi

# --- Weekly geographic editions: "What to Watch: Marana / Oro Valley" (Mondays) ---
# Personalization-by-portfolio experiment (SHORT-FORM-VIDEO.md § Geographic
# editions). Renders each town's weekly ~25s edition from miner output
# (deterministic lead ladder + grounded phrasing + verify pass), auto-publishes
# to YouTube Shorts (sanctioned full-auto surface), and Telegrams the MP4 path
# + ready-to-paste caption for the MANUAL Facebook/Instagram post — manual
# posting is the human-review gate for Meta surfaces. A skipped town (no
# meeting, no radar items) is normal and logged. Non-fatal on failure.
if [ "$(date +%u)" = "1" ]; then
    for TOWN in marana orovalley; do
        echo "Monday: generating '$TOWN' edition..."
        ED_OUTPUT=$(python3 social/generate_edition_short.py "$TOWN" --publish 2>&1) || true
        echo "$ED_OUTPUT"
        ED_LINE=$(printf '%s\n' "$ED_OUTPUT" | grep '^EDITION-RENDERED' | tail -1 || true)
        ED_SKIP=$(printf '%s\n' "$ED_OUTPUT" | grep '^EDITION-SKIPPED' | tail -1 || true)
        YT_LINE=$(printf '%s\n' "$ED_OUTPUT" | grep '^SHORT-PUBLISHED' | tail -1 || true)
        if [ -n "$ED_LINE" ]; then
            IFS=$'\t' read -r _tag ED_TOWN ED_MP4 ED_TITLE <<< "$ED_LINE"
            ED_CAPTION=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1].replace('.mp4','.json')))['caption'])" "$ED_MP4" 2>/dev/null || true)
            YT_NOTE=""
            if [ -n "$YT_LINE" ]; then
                IFS=$'\t' read -r _t _title YT_URL <<< "$YT_LINE"
                YT_NOTE="Published to YouTube Shorts: $YT_URL
"
            fi
            NOTIFY_MSG="🗺️ $ED_TOWN edition rendered — post it to Facebook + Instagram

$ED_TITLE

Video file: $ED_MP4
${YT_NOTE}
Caption to paste (add the town's location tag when posting):

$ED_CAPTION

Reminder: log reach/watch-time/follows in social/editions-log.md after ~48h."
            TMPFILE=$(mktemp /tmp/edition-notify-XXXXX.md)
            printf '%s\n' "$NOTIFY_MSG" > "$TMPFILE"
            if [ -f "$SEND_TELEGRAM" ]; then
                python3 "$SEND_TELEGRAM" "$TMPFILE" || echo "WARNING: edition Telegram notification failed (non-fatal)"
            fi
            rm -f "$TMPFILE"
        elif [ -n "$ED_SKIP" ]; then
            echo "Edition skipped: $ED_SKIP"
        fi
    done
fi

# --- Meeting-coverage staleness check ---
# A scraper that stops finding meetings is indistinguishable from a body that
# stops meeting — both are silence. This separates the two (see
# check_meeting_staleness.py) and alerts only when the source itself looks dead
# or is listing council meetings we never published. Non-fatal.
echo "Checking meeting-coverage staleness..."
python3 "$SCRIPT_DIR/check_meeting_staleness.py" --telegram \
    || echo "WARNING: staleness check failed (non-fatal)"

# --- Bluesky ledger-diff poster (SOCIAL-AUTOPOST.md Part 3) ---
# Posts anything newly published since the last run; idempotent, non-fatal.
echo "Posting new pages to Bluesky..."
python3 "$SCRIPT_DIR/social/bluesky_poster.py" \
    || echo "WARNING: Bluesky poster failed (non-fatal)"

echo "$(date): Done."
