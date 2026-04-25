#!/usr/bin/env python3
"""
Auto-schedule live AI reporter recordings from agenda previews.

Given a preview + its full-reference agenda file, extract the public session
start time via Claude, look up the stream URL for the municipality, schedule
an `at` job to invoke run_live_reporter.sh a few minutes before the meeting,
and track the scheduled job in .scheduled.json. On reschedules, the previous
`at` job is removed and a new one created.

Usage:
    python3 schedule_recording.py <preview_path> <full_ref_path> <municipality>
    python3 schedule_recording.py --dry-run <preview> <full_ref> <municipality>
    python3 schedule_recording.py --list
    python3 schedule_recording.py --all-dry-run

Municipalities: pima-county, marana, orovalley, tucson
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

SITE_DIR = Path(__file__).resolve().parent
AGENDA_WATCH_DIR = SITE_DIR / "agenda-watch"
STATE_FILE = AGENDA_WATCH_DIR / ".scheduled.json"
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
AZ = ZoneInfo("America/Phoenix")
SCHEDULE_LEAD_MINUTES = 5

SEND_TELEGRAM = Path.home() / ".openclaw" / "skills" / "tucson-daily-brief" / "scripts" / "send_telegram.py"

STREAM_SOURCES = {
    "pima-county": {
        "url": "https://www.youtube.com/@PimaCountyArizona/live",
        "mode": "streamlink",
        "body_name": "Pima County BOS",
    },
    "tucson": {
        "url": "https://www.youtube.com/user/CityofTucson/live",
        "mode": "streamlink",
        "body_name": "Tucson Mayor & Council",
    },
    "orovalley": {
        "url": "https://stream.swagit.com/live-edge/orovalleyaz/smil:hd-16x9-1-a/playlist.m3u8",
        "mode": "direct",
        "body_name": "Oro Valley Town Council",
    },
    "marana": {
        # Pattern inferred from Oro Valley; verify with devtools on a live Marana broadcast
        # before relying on this in production.
        "url": "https://stream.swagit.com/live-edge/maranaaz/smil:hd-16x9-1-a/playlist.m3u8",
        "mode": "direct",
        "body_name": "Marana Town Council",
        "unverified": True,
    },
}


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            print(f"WARNING: could not parse {STATE_FILE}, starting fresh", file=sys.stderr)
    return {}


def save_state(state: dict) -> None:
    AGENDA_WATCH_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


def slug_from_preview(preview_path: Path) -> str:
    """pima-county-2026-04-29-preview.md → pima-county-2026-04-29"""
    stem = preview_path.stem
    if stem.endswith("-preview"):
        stem = stem[: -len("-preview")]
    return stem


def municipality_from_basename(basename: str) -> str | None:
    """Derive municipality key from a preview filename (basename only —
    the repo dir name contains 'tucson' and would falsely match full paths)."""
    if basename.startswith("marana"):
        return "marana"
    if basename.startswith("orovalley"):
        return "orovalley"
    if basename.startswith("tucson"):
        return "tucson"
    if basename.startswith("pima-county"):
        return "pima-county"
    return None


def meeting_date_from_slug(slug: str) -> datetime | None:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", slug)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%Y-%m-%d")


def extract_schedule_info(agenda_text: str, meeting_date: datetime, body_name: str) -> dict | None:
    """Ask Claude for structured scheduling info. Returns parsed dict or None."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return None

    date_str = meeting_date.strftime("%A, %B %d, %Y")
    snippet = agenda_text[:15000]

    prompt = f"""You are extracting scheduling information from a government meeting agenda.

The meeting is for the {body_name} on {date_str}. Read the agenda below and determine when the public/regular session begins. This is distinct from any executive session, which typically happens immediately before and is closed to the public. We want to record the public session, NOT the executive session.

Respond with ONLY a single JSON object. No markdown fences, no prose. Schema:

{{
  "public_session_start": "ISO 8601 with timezone offset, e.g. 2026-04-29T18:00:00-07:00. All Arizona times are UTC-7 (no DST).",
  "has_executive_session": true or false,
  "executive_session_start": "ISO 8601 or null",
  "confidence": "high | medium | low",
  "notes": "One short sentence explaining your reasoning — especially what distinguished public vs executive session. If ambiguous or a best-guess, say so."
}}

Guidance:
- "Regular Session: 6:00 PM" + "Executive Session: 5:00 PM" → public_session_start = 6 PM, confidence=high.
- One time with no exec session mentioned → use it, confidence=high.
- "Board will meet in executive session at 9 AM followed by regular session" → public session typically 30-60 min later; best guess, confidence=medium.
- No time found → still return JSON; set confidence=low and explain.

AGENDA:

{snippet}"""

    request_body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        CLAUDE_API_URL,
        data=request_body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
    except Exception as e:
        print(f"ERROR: Claude API call failed: {e}", file=sys.stderr)
        return None

    content = result.get("content", [])
    if not content or content[0].get("type") != "text":
        print(f"ERROR: unexpected Claude response: {result}", file=sys.stderr)
        return None

    text = content[0]["text"].strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"ERROR: could not parse Claude JSON: {e}\nResponse was: {text}", file=sys.stderr)
        return None


def check_atd_running() -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "atd"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


def at_schedule(when: datetime, command: str) -> int | None:
    """Schedule via `at`. Returns job id or None."""
    # Pass the time in system-local tz so `at` interprets it correctly.
    when_local = when.astimezone()
    at_time = when_local.strftime("%H:%M %Y-%m-%d")

    proc = subprocess.run(
        ["at", at_time],
        input=command,
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print(f"ERROR: `at` failed: {proc.stderr}", file=sys.stderr)
        return None

    m = re.search(r"job\s+(\d+)\s+at", proc.stderr)
    if not m:
        print(f"WARNING: could not parse at job id from: {proc.stderr}", file=sys.stderr)
        return None
    return int(m.group(1))


def at_remove(job_id: int) -> bool:
    proc = subprocess.run(["atrm", str(job_id)], capture_output=True, text=True)
    return proc.returncode == 0


def send_telegram(message: str) -> None:
    if not SEND_TELEGRAM.exists():
        print(f"WARNING: {SEND_TELEGRAM} not found, skipping notification", file=sys.stderr)
        return
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(message)
        tmp_path = f.name
    try:
        subprocess.run(
            ["python3", str(SEND_TELEGRAM), tmp_path],
            capture_output=True, text=True, timeout=30,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def build_at_command(slug: str, stream_url: str, mode: str) -> str:
    repo = str(SITE_DIR)
    extra = " --direct" if mode == "direct" else ""
    log = f"/tmp/live-reporter-{slug}.log"
    return (
        f"cd {repo} && ./run_live_reporter.sh '{stream_url}' "
        f"--slug {slug}{extra} >> {log} 2>&1"
    )


def schedule_one(
    preview_path: Path,
    full_ref_path: Path,
    municipality: str,
    dry_run: bool = False,
    force: bool = False,
) -> int:
    source = STREAM_SOURCES.get(municipality)
    if not source:
        print(f"ERROR: unknown municipality '{municipality}'", file=sys.stderr)
        return 2
    if not full_ref_path.exists():
        print(f"ERROR: full reference not found: {full_ref_path}", file=sys.stderr)
        return 2

    slug = slug_from_preview(preview_path)
    meeting_date = meeting_date_from_slug(slug)
    if not meeting_date:
        print(f"ERROR: could not parse date from slug {slug}", file=sys.stderr)
        return 2

    body_name = source["body_name"]
    agenda_text = full_ref_path.read_text()

    info = extract_schedule_info(agenda_text, meeting_date, body_name)
    if not info:
        if not dry_run:
            send_telegram(
                f"WARN: Could not extract schedule info for {body_name} "
                f"on {meeting_date.strftime('%Y-%m-%d')} — no `at` job created."
            )
        return 1

    try:
        public_start = datetime.fromisoformat(info["public_session_start"])
    except (KeyError, ValueError, TypeError) as e:
        print(f"ERROR: bad public_session_start: {e}\ninfo={info}", file=sys.stderr)
        if not dry_run:
            send_telegram(
                f"WARN: Schedule extraction returned invalid time for {body_name} "
                f"on {meeting_date.strftime('%Y-%m-%d')}. Notes: {info.get('notes', '(none)')}"
            )
        return 1

    confidence = info.get("confidence", "unknown")
    notes = info.get("notes", "")

    now = datetime.now(AZ)
    lead = timedelta(minutes=SCHEDULE_LEAD_MINUTES)
    start_at = max(now + timedelta(minutes=2), public_start - lead)
    is_past = public_start < now

    state = load_state()
    prior = state.get(slug)

    if dry_run:
        print(f"[DRY-RUN] {slug} ({municipality})")
        print(f"  public_session_start: {public_start.astimezone(AZ).isoformat()}")
        print(f"  at start time:        {start_at.astimezone(AZ).isoformat()}")
        print(f"  confidence:           {confidence}")
        print(f"  notes:                {notes}")
        print(f"  stream:               {source['url']} ({source['mode']})")
        if is_past:
            print(f"  (would skip — meeting is in the past)")
        if source.get("unverified"):
            print(f"  (!) stream URL is unverified")
        if prior:
            print(f"  prior state:          {json.dumps(prior)}")
        return 0

    if is_past:
        print(f"SKIP {slug}: meeting is in the past ({public_start.isoformat()})")
        return 0

    if prior and not force:
        try:
            prior_public = datetime.fromisoformat(prior["public_session_start"])
        except (KeyError, ValueError, TypeError):
            prior_public = None

        if prior_public and abs((prior_public - public_start).total_seconds()) < 60:
            print(f"NO-OP: {slug} already scheduled at {public_start.isoformat()}")
            return 0

    if prior and "at_job_id" in prior:
        removed = at_remove(prior["at_job_id"])
        print(f"Removed prior at job {prior['at_job_id']} (success={removed})")

    command = build_at_command(slug, source["url"], source["mode"])
    job_id = at_schedule(start_at, command)
    if job_id is None:
        send_telegram(
            f"WARN: Failed to create `at` job for {body_name} "
            f"on {meeting_date.strftime('%Y-%m-%d')}"
        )
        return 1

    state[slug] = {
        "at_job_id": job_id,
        "scheduled_for": start_at.astimezone(AZ).isoformat(),
        "public_session_start": public_start.astimezone(AZ).isoformat(),
        "stream_url": source["url"],
        "mode": source["mode"],
        "municipality": municipality,
        "body_name": body_name,
        "preview_path": str(preview_path),
        "confidence": confidence,
        "notes": notes,
        "scheduled_at": now.isoformat(),
        "status": "rescheduled" if prior else "scheduled",
    }
    save_state(state)

    verb = "rescheduled" if prior else "scheduled"
    tags = ""
    if confidence == "low":
        tags += " [please verify — low confidence]"
    if source.get("unverified"):
        tags += " [stream URL unverified]"
    msg = (
        f"Live recording {verb}{tags}\n\n"
        f"{body_name} — {public_start.astimezone(AZ).strftime('%a %b %d, %-I:%M %p %Z')}\n"
        f"Recording starts {SCHEDULE_LEAD_MINUTES} min early at "
        f"{start_at.astimezone(AZ).strftime('%-I:%M %p %Z')}\n"
        f"at job: {job_id} | confidence: {confidence}\n\n"
        f"Extraction notes: {notes}"
    )
    send_telegram(msg)
    print(msg)
    return 0


def list_scheduled() -> None:
    state = load_state()
    if not state:
        print("No scheduled recordings.")
        return
    for slug, entry in sorted(state.items(), key=lambda kv: kv[1].get("public_session_start", "")):
        print(slug)
        print(f"  at job:     {entry.get('at_job_id')}")
        print(f"  meeting:    {entry.get('public_session_start')}")
        print(f"  recording:  {entry.get('scheduled_for')}")
        print(f"  confidence: {entry.get('confidence')}")
        print(f"  status:     {entry.get('status')}")
        print()


def all_dry_run() -> None:
    """Backtest: dry-run every *-preview.md paired with its *-full.md."""
    for preview in sorted(AGENDA_WATCH_DIR.glob("*-preview.md")):
        basename = preview.name
        muni = municipality_from_basename(basename)
        if not muni:
            print(f"SKIP {basename}: unknown municipality\n")
            continue
        full_ref = AGENDA_WATCH_DIR / basename.replace("-preview.md", "-full.md")
        if not full_ref.exists():
            print(f"SKIP {basename}: no full reference\n")
            continue
        print(f"--- {basename} ---")
        schedule_one(preview, full_ref, muni, dry_run=True)
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-schedule live AI reporter recordings")
    parser.add_argument("preview", nargs="?", help="Preview markdown path")
    parser.add_argument("full_ref", nargs="?", help="Full-reference markdown path")
    parser.add_argument("municipality", nargs="?", choices=list(STREAM_SOURCES.keys()))
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be scheduled; no `at`, no state write, no Telegram")
    parser.add_argument("--force", action="store_true",
                        help="Re-schedule even if state matches current extraction")
    parser.add_argument("--list", action="store_true", help="List currently scheduled recordings")
    parser.add_argument("--all-dry-run", action="store_true",
                        help="Backtest: dry-run every preview in agenda-watch/")
    args = parser.parse_args()

    if args.list:
        list_scheduled()
        return 0
    if args.all_dry_run:
        all_dry_run()
        return 0

    if not (args.preview and args.full_ref and args.municipality):
        parser.error("preview, full_ref, and municipality required (or use --list / --all-dry-run)")

    if not args.dry_run and not check_atd_running():
        msg = "atd daemon is not running — cannot schedule live recordings. Run: sudo systemctl enable --now atd"
        print(msg, file=sys.stderr)
        send_telegram(msg)
        return 3

    return schedule_one(
        Path(args.preview), Path(args.full_ref), args.municipality,
        dry_run=args.dry_run, force=args.force,
    )


if __name__ == "__main__":
    sys.exit(main() or 0)
