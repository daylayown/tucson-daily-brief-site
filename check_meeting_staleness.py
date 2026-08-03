#!/usr/bin/env python3
"""
Meeting-coverage staleness check.

The failure this exists to catch: a scraper that quietly stops finding meetings
looks exactly like a governing body that has stopped meeting. Both are silence.
Oro Valley went seven weeks with no preview in mid-2026 and nothing flagged it —
that gap turned out to be a genuine July recess, but only a hand check proved it.

So this splits the two cases apart. For each municipality it asks:

  1. How long since we last PUBLISHED a preview?  (meeting-watch/*.html)
  2. If that's stale, is the SOURCE still alive?   (does the listing still
     return rows of any kind for recent months?)

A live source with no council meetings is a recess — informational. A source
returning nothing at all is a probable break — alert. Nothing here publishes;
it only reports.

Usage:
    python3 check_meeting_staleness.py            # human-readable report
    python3 check_meeting_staleness.py --telegram # also alert if warranted
    python3 check_meeting_staleness.py --force-telegram   # alert regardless (test)
"""

import argparse
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent
PUBLISHED_DIR = SITE_DIR / "meeting-watch"
SEND_TELEGRAM = Path.home() / ".openclaw/skills/tucson-daily-brief/scripts/send_telegram.py"

# `stale_days` is "long enough that a working pipeline would have found
# something." Oro Valley's is the widest because it takes a real July recess —
# in 2025 the June 18 → August 13 gap alone ran 56 days.
MUNICIPALITIES = [
    {"key": "pima-county", "name": "Pima County BOS",     "stale_days": 40, "prober": None},
    {"key": "tucson",      "name": "City of Tucson",      "stale_days": 40, "prober": None},
    {"key": "marana",      "name": "Marana Town Council", "stale_days": 45,
     "prober": "agenda_mining_marana"},
    {"key": "orovalley",   "name": "Oro Valley Town Council", "stale_days": 70,
     "prober": "agenda_mining_orovalley"},
]

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def last_published(key: str) -> datetime | None:
    """Newest meeting date among published previews for this municipality."""
    if not PUBLISHED_DIR.exists():
        return None
    dates = []
    for f in PUBLISHED_DIR.glob(f"{key}-*.html"):
        m = DATE_RE.search(f.stem)
        if m:
            try:
                dates.append(datetime.strptime(m.group(1), "%Y-%m-%d"))
            except ValueError:
                continue
    return max(dates) if dates else None


def probe_source(module_name: str, today: datetime) -> dict:
    """Ask the miner's own month listing whether the source still returns rows.

    Returns {'ok': bool, 'rows': int, 'council': int, 'detail': str}. `ok` False
    means the source errored or returned nothing across the probed window — the
    signal that separates "broken" from "in recess".
    """
    try:
        mod = __import__(module_name)
    except Exception as e:  # noqa: BLE001 - report, never raise, this is a monitor
        return {"ok": False, "rows": 0, "council": 0, "detail": f"import failed: {e}"}

    rows = council = 0
    errors = []
    # Current month plus the two behind it — enough to span a normal meeting cadence.
    for back in (0, 1, 2):
        y, m = today.year, today.month - back
        while m <= 0:
            m += 12
            y -= 1
        try:
            found = mod.get_meetings_for_month(y, m)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{y}-{m:02d}: {e}")
            continue
        rows += len(found)
        council += sum(1 for x in found if x.get("is_council"))

    if errors and rows == 0:
        return {"ok": False, "rows": 0, "council": 0, "detail": "; ".join(errors[:2])}
    if rows == 0:
        return {"ok": False, "rows": 0, "council": 0,
                "detail": "listing returned zero rows of any type for the last 3 months"}
    return {"ok": True, "rows": rows, "council": council,
            "detail": f"{rows} rows / {council} council in last 3 months"}


def check(today: datetime) -> list[dict]:
    results = []
    for muni in MUNICIPALITIES:
        last = last_published(muni["key"])
        days = (today - last).days if last else None
        stale = days is None or days > muni["stale_days"]

        probe = None
        if stale and muni["prober"]:
            probe = probe_source(muni["prober"], today)

        # Severity: a dead source is an alert; a live source with no council
        # meetings is a recess we just want noted.
        if not stale:
            level = "ok"
        elif probe is None:
            level = "warn"          # stale, and we have no way to probe the source
        elif not probe["ok"]:
            level = "alert"         # source returns nothing — probable break
        elif probe["council"] == 0:
            level = "info"          # source alive, genuinely no council meetings
        else:
            level = "alert"         # source HAS council meetings we never published

        results.append({**muni, "last": last, "days": days,
                        "stale": stale, "probe": probe, "level": level})
    return results


def format_report(results: list[dict], today: datetime) -> str:
    icons = {"ok": "✅", "info": "🟡", "warn": "⚠️", "alert": "🚨"}
    lines = [f"Meeting-coverage staleness — {today:%Y-%m-%d}", ""]
    for r in results:
        last = f"{r['last']:%Y-%m-%d}" if r["last"] else "never"
        if r["days"] is None:
            age = "no previews found"
        elif r["days"] < 0:
            # Previews are forward-looking, so a future meeting date means we're
            # already covering something that hasn't happened yet.
            age = f"upcoming, in {-r['days']}d"
        else:
            age = f"{r['days']}d ago"
        lines.append(f"{icons[r['level']]} {r['name']}: newest {last} ({age}, "
                     f"threshold {r['stale_days']}d)")
        if r["probe"]:
            state = "source alive" if r["probe"]["ok"] else "SOURCE NOT RETURNING DATA"
            lines.append(f"     └ {state} — {r['probe']['detail']}")
    return "\n".join(lines)


def format_telegram(results: list[dict], today: datetime) -> str | None:
    bad = [r for r in results if r["level"] in ("alert", "warn")]
    noted = [r for r in results if r["level"] == "info"]
    if not bad and not noted:
        return None

    parts = []
    if bad:
        parts.append("🚨 Meeting monitor needs a look\n")
        for r in bad:
            last = f"{r['last']:%Y-%m-%d}" if r["last"] else "never"
            parts.append(f"• {r['name']} — nothing published since {last} "
                         f"({r['days'] if r['days'] is not None else '?'}d).")
            if r["probe"] and not r["probe"]["ok"]:
                parts.append(f"  Source returned no data: {r['probe']['detail']}")
                parts.append("  → Likely a scraper break, not a recess. Verify the agenda site.")
            elif r["probe"] and r["probe"]["council"]:
                parts.append(f"  Source lists {r['probe']['council']} council meeting(s) "
                             f"we never published. → Check the type filter.")
            else:
                parts.append("  No source probe available — check the agenda site by hand.")
    if noted:
        parts.append("\n🟡 Quiet, but the source is alive (probably a recess):")
        for r in noted:
            last = f"{r['last']:%Y-%m-%d}" if r["last"] else "never"
            parts.append(f"• {r['name']} — last {last} ({r['days']}d); "
                         f"{r['probe']['detail']}")
    parts.append(f"\nChecked {today:%Y-%m-%d}. Nothing was published by this check.")
    return "\n".join(parts)


def send_telegram(message: str) -> None:
    if not SEND_TELEGRAM.exists():
        print(f"WARNING: {SEND_TELEGRAM} not found, skipping notification", file=sys.stderr)
        return
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
        fh.write(message)
        path = fh.name
    try:
        subprocess.run(["python3", str(SEND_TELEGRAM), path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Telegram notification failed (non-fatal): {e}", file=sys.stderr)
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--telegram", action="store_true", help="alert if anything is stale")
    ap.add_argument("--force-telegram", action="store_true", help="always send (testing)")
    ap.add_argument("--date", help="override today's date, YYYY-MM-DD (testing)")
    args = ap.parse_args()

    today = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)

    results = check(today)
    print(format_report(results, today))

    msg = format_telegram(results, today)
    if args.force_telegram and msg is None:
        msg = f"✅ Meeting monitor: all four municipalities current as of {today:%Y-%m-%d}."
    if msg:
        # Echo into the cron log so the log shows exactly what was alerted.
        print("\n--- alert text ---\n" + msg)
    if (args.telegram or args.force_telegram) and msg:
        send_telegram(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
