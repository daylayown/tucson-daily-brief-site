#!/usr/bin/env python3
"""
Promise Tracker — the "What They Promised" evidence ledger.

Extracts commitments made by officials/staff in meeting transcripts into a
private SQLite ledger, with the evidence discipline from
RIO-NUEVO-PIPELINE-PLAN.md: every row carries a verbatim quoted span that is
programmatically validated against the transcript before it is accepted, plus
a code-derived timestamp. The model proposes; deterministic code validates;
a human confirms. Only human-confirmed rows may feed published prose.

Speaker identity follows NAMES-BIBLE.md: the diarization label and the
model's role guess are hypotheses. `speaker_name` stays NULL until a human
confirms it during review (cross-reference the approved meeting report).

Usage:
    python3 promise_tracker.py extract transcripts/tucson-2026-07-21.json
    python3 promise_tracker.py extract --all          # every non-partial transcript
    python3 promise_tracker.py list [--status machine-extracted] [--slug SLUG]
    python3 promise_tracker.py show ID
    python3 promise_tracker.py confirm ID [--name "Real Name"] [--follow-up YYYY-MM-DD] [--notes TEXT]
    python3 promise_tracker.py reject ID [--notes TEXT]
    python3 promise_tracker.py export-review [--slug SLUG]   # markdown for human review
    python3 promise_tracker.py due [--within DAYS]           # passed/upcoming deadlines

Requires ANTHROPIC_API_KEY (read from ~/.config/environment.d/anthropic.conf
if not already in the environment).
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

TZ_LOCAL = ZoneInfo("America/Phoenix")

from ai_reporter import CLAUDE_API_URL, CLAUDE_MODEL, load_transcript, format_transcript_for_prompt

SITE_DIR = Path(__file__).resolve().parent
LEDGER_DIR = SITE_DIR / "promise-ledger"
DB_PATH = LEDGER_DIR / "promises.sqlite"
TRANSCRIPTS_DIR = SITE_DIR / "transcripts"

BODY_NAMES = {
    "pima-county": "Pima County Board of Supervisors",
    "tucson": "Tucson City Council",
    "marana": "Marana Town Council",
    "orovalley": "Oro Valley Town Council",
}

TOPICS = [
    "downtown-shooting", "public-safety", "housing", "transportation",
    "budget", "development", "water", "elections", "other",
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS promises (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL,
    body TEXT NOT NULL,
    meeting_date TEXT NOT NULL,
    speaker_label TEXT,
    speaker_role_hint TEXT,
    speaker_name TEXT,
    quote TEXT NOT NULL,
    t_start REAL NOT NULL,
    timestamp_hms TEXT NOT NULL,
    summary TEXT NOT NULL,
    topic TEXT,
    deadline_kind TEXT NOT NULL DEFAULT 'none',
    deadline_text TEXT,
    deadline_date TEXT,
    status TEXT NOT NULL DEFAULT 'machine-extracted',
    follow_up_date TEXT,
    notes TEXT,
    extracted_at TEXT NOT NULL,
    UNIQUE(slug, quote)
);
"""

VALID_STATUSES = (
    "machine-extracted", "human-confirmed", "rejected",
    "contradicted", "superseded", "fulfilled",
)


def open_db() -> sqlite3.Connection:
    LEDGER_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.row_factory = sqlite3.Row
    return conn


def load_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    conf = Path.home() / ".config" / "environment.d" / "anthropic.conf"
    if conf.exists():
        for line in conf.read_text().splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    print("ERROR: ANTHROPIC_API_KEY not set and not found in environment.d", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Deterministic validation: quote → transcript location
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def build_locator(segments: list[dict]):
    """Concatenate normalized segment text, tracking each segment's start
    offset, so a validated quote can be mapped back to a timestamp."""
    parts = []
    offsets = []  # (offset_in_full, segment_index)
    pos = 0
    for i, seg in enumerate(segments):
        t = _norm(seg.get("text", ""))
        if not t:
            continue
        offsets.append((pos, i))
        parts.append(t)
        pos += len(t) + 1  # the joining space
    return " ".join(parts), offsets


def locate_quote(quote: str, full_text: str, offsets: list, segments: list[dict]):
    """Return (t_start, speaker_label) if the normalized quote appears
    verbatim in the transcript, else None. This is the hard gate: a quote
    the model paraphrased does not enter the ledger."""
    q = _norm(quote)
    if len(q) < 15:  # too short to be meaningful evidence
        return None
    idx = full_text.find(q)
    if idx < 0:
        return None
    seg_i = 0
    for off, i in offsets:
        if off <= idx:
            seg_i = i
        else:
            break
    seg = segments[seg_i]
    speaker = seg.get("speaker")
    label = f"Speaker {int(speaker)}" if speaker is not None else None
    return seg.get("start", 0.0), label


def hms(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

EXTRACT_PROMPT = """You are an evidence extractor for a local-news promise tracker covering {body} ({meeting_date}).

Below is a meeting transcript. Find every clear COMMITMENT made by an official or staff member — a statement promising future action for which they can later be held accountable. Examples: "staff will report back", "we will revisit this in 90 days", "I'm directing staff to...", "we'll bring this back to council", "a study is underway and will be completed by...", "we will hire/implement/publish X by DATE".

Rules:
- ONLY commitments by officials or government staff. Never public commenters.
- A commitment is a specific future action, not a value statement ("we care deeply about safety" is NOT a commitment; "we will present a downtown security plan in August" IS).
- Routine procedural motions (continuing an item to the next agenda) are NOT commitments unless a substantive deliverable is promised.
- ZERO commitments is a normal and common result. Do not invent or pad. Most meetings contain only a handful, some contain none.
- The "quote" field must be copied VERBATIM, character-for-character, from the transcript — the exact contiguous span containing the commitment (1–3 sentences). It will be programmatically checked against the transcript and the entry discarded if it does not match exactly. Do not fix grammar, do not paraphrase, do not stitch separate sentences together.
- Speaker names in the transcript are unverified. In speaker_role_hint give your best guess at the speaker's role from context (e.g. "mayor", "police chief", "city manager", "council member", "county administrator") or null if unclear.

For deadlines:
- "explicit": a calendar date or month is spoken ("by September 1", "in August") — put the spoken words in deadline_text and your best ISO date (first of month if only a month) in deadline_date.
- "relative": a duration is spoken ("in 90 days", "within two weeks") — put the spoken words in deadline_text and the number of days in deadline_days.
- "vague": future action promised but no timeframe ("we'll come back to this") — deadline_text holds any timing language.
- "none": no timing language at all.

Topics (pick one): {topics}

Respond with ONLY a JSON array (no prose, no code fences). Each element:
{{"quote": "...", "summary": "one sentence: who committed to what", "speaker_role_hint": "..." or null, "topic": "...", "deadline_kind": "explicit|relative|vague|none", "deadline_text": "..." or null, "deadline_date": "YYYY-MM-DD" or null, "deadline_days": int or null}}

If there are no commitments, respond with [].

TRANSCRIPT:

{transcript}"""


def call_claude(prompt: str, api_key: str, max_tokens: int = 16000) -> str | None:
    request_body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": max_tokens,
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
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read())
            content = result.get("content", [])
            if content and content[0].get("type") == "text":
                return content[0]["text"]
    except Exception as e:
        print(f"  WARNING: Claude API call failed: {e}", file=sys.stderr)
    return None


def parse_json_array(text: str) -> list | None:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start = text.find("[")
    if start >= 0:
        try:
            # raw_decode: parse the first complete array, ignore anything the
            # model appended after it. strict=False: verbatim transcript quotes
            # sometimes carry literal control characters the model doesn't escape.
            out, _ = json.JSONDecoder(strict=False).raw_decode(text, start)
            return out if isinstance(out, list) else None
        except json.JSONDecodeError as e:
            print(f"  (json parse: {e})", file=sys.stderr)
    # Salvage a truncated array (response hit max_tokens mid-object): trim to
    # the last complete object and close the array. Complete rows are kept.
    if start < 0:
        return None
    last_obj_end = text.rfind("}")
    if last_obj_end <= start:
        return None
    try:
        out = json.loads(text[start:last_obj_end + 1] + "]", strict=False)
        return out if isinstance(out, list) else None
    except json.JSONDecodeError as e:
        print(f"  (json salvage parse: {e})", file=sys.stderr)
        return None


def body_from_slug(slug: str) -> str:
    for prefix, name in BODY_NAMES.items():
        if slug.startswith(prefix):
            return name
    return slug


def extract_file(path: Path, conn: sqlite3.Connection, api_key: str) -> tuple[int, int, int]:
    """Extract promises from one transcript. Returns (accepted, rejected_validation, duplicates)."""
    data = load_transcript(str(path))
    meta = data["meta"]
    slug = meta.get("slug", path.stem)
    # started_at is UTC; evening meetings roll past midnight UTC, so convert
    # to Phoenix time before taking the date.
    meeting_date = "unknown"
    if meta.get("started_at"):
        try:
            meeting_date = datetime.fromisoformat(meta["started_at"]).astimezone(TZ_LOCAL).date().isoformat()
        except ValueError:
            meeting_date = meta["started_at"][:10]
    body = body_from_slug(slug)
    segments = data["segments"]

    print(f"— {slug} ({body}, {meeting_date}, {len(segments)} segments)")

    prompt = EXTRACT_PROMPT.format(
        body=body,
        meeting_date=meeting_date,
        topics=", ".join(TOPICS),
        transcript=format_transcript_for_prompt(data),
    )
    raw = call_claude(prompt, api_key)
    items = parse_json_array(raw) if raw else None
    if items is None:
        # one retry for malformed output or a failed API call
        raw = call_claude(prompt, api_key)
        items = parse_json_array(raw) if raw else None
    if items is None:
        print("  ERROR: no parseable model output — skipping file")
        return 0, 0, 0

    full_text, offsets = build_locator(segments)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    accepted = rejected = dupes = 0

    for it in items:
        quote = (it.get("quote") or "").strip()
        summary = (it.get("summary") or "").strip()
        if not quote or not summary:
            rejected += 1
            continue

        loc = locate_quote(quote, full_text, offsets, segments)
        if loc is None:
            rejected += 1
            print(f"  REJECTED (quote not verbatim in transcript): {summary[:70]}")
            continue
        t_start, speaker_label = loc

        deadline_kind = it.get("deadline_kind") or "none"
        if deadline_kind not in ("explicit", "relative", "vague", "none"):
            deadline_kind = "vague"
        deadline_text = it.get("deadline_text")
        deadline_date = None
        if deadline_kind == "explicit":
            d = it.get("deadline_date")
            if d and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
                deadline_date = d
        elif deadline_kind == "relative":
            days = it.get("deadline_days")
            if isinstance(days, int) and 0 < days <= 730 and meeting_date != "unknown":
                deadline_date = (date.fromisoformat(meeting_date) + timedelta(days=days)).isoformat()

        topic = it.get("topic") if it.get("topic") in TOPICS else "other"

        try:
            conn.execute(
                """INSERT INTO promises(slug, body, meeting_date, speaker_label, speaker_role_hint,
                       quote, t_start, timestamp_hms, summary, topic,
                       deadline_kind, deadline_text, deadline_date, extracted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (slug, body, meeting_date, speaker_label, it.get("speaker_role_hint"),
                 quote, t_start, hms(t_start), summary, topic,
                 deadline_kind, deadline_text, deadline_date, now),
            )
            accepted += 1
            print(f"  [{hms(t_start)}] {summary[:90]}")
        except sqlite3.IntegrityError:
            dupes += 1

    conn.commit()
    print(f"  accepted {accepted}, rejected-by-validation {rejected}, duplicate {dupes}")
    return accepted, rejected, dupes


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def cmd_extract(args):
    api_key = load_api_key()
    conn = open_db()
    if args.all:
        paths = sorted(
            p for p in TRANSCRIPTS_DIR.glob("*.json")
            if not p.name.endswith("-partial.json")
        )
    else:
        paths = [Path(p) for p in args.files]
    if not paths:
        print("No transcript files to process.")
        return 1
    totals = [0, 0, 0]
    for p in paths:
        a, r, d = extract_file(p, conn, api_key)
        totals[0] += a; totals[1] += r; totals[2] += d
    print(f"\nTOTAL: accepted {totals[0]}, rejected-by-validation {totals[1]}, duplicate {totals[2]}")
    return 0


def _rows(conn, where="1=1", params=()):
    return conn.execute(
        f"SELECT * FROM promises WHERE {where} ORDER BY meeting_date, t_start", params
    ).fetchall()


def cmd_list(args):
    conn = open_db()
    where, params = "1=1", []
    if args.status:
        where += " AND status = ?"; params.append(args.status)
    if args.slug:
        where += " AND slug = ?"; params.append(args.slug)
    rows = _rows(conn, where, params)
    for r in rows:
        dl = r["deadline_date"] or r["deadline_text"] or "—"
        who = r["speaker_name"] or r["speaker_role_hint"] or r["speaker_label"] or "?"
        print(f"[{r['id']:3d}] {r['meeting_date']} {r['slug']} {r['timestamp_hms']} "
              f"({r['status']}) [{r['topic']}] due:{dl} | {who}: {r['summary']}")
    print(f"\n{len(rows)} promise(s)")
    return 0


def cmd_show(args):
    conn = open_db()
    r = conn.execute("SELECT * FROM promises WHERE id = ?", (args.id,)).fetchone()
    if not r:
        print(f"No promise with id {args.id}"); return 1
    for k in r.keys():
        print(f"{k}: {r[k]}")
    return 0


def _set_status(args, status: str):
    conn = open_db()
    r = conn.execute("SELECT id FROM promises WHERE id = ?", (args.id,)).fetchone()
    if not r:
        print(f"No promise with id {args.id}"); return 1
    sets, params = ["status = ?"], [status]
    if getattr(args, "name", None):
        sets.append("speaker_name = ?"); params.append(args.name)
    if getattr(args, "follow_up", None):
        sets.append("follow_up_date = ?"); params.append(args.follow_up)
    if getattr(args, "notes", None):
        sets.append("notes = ?"); params.append(args.notes)
    params.append(args.id)
    conn.execute(f"UPDATE promises SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()
    print(f"Promise {args.id} → {status}")
    return 0


def cmd_confirm(args):
    return _set_status(args, "human-confirmed")


def cmd_reject(args):
    return _set_status(args, "rejected")


def cmd_export_review(args):
    conn = open_db()
    where, params = "status = 'machine-extracted'", []
    if args.slug:
        where += " AND slug = ?"; params.append(args.slug)
    rows = _rows(conn, where, params)
    out = LEDGER_DIR / "review" / f"review-{date.today().isoformat()}.md"
    out.parent.mkdir(exist_ok=True)
    lines = [f"# Promise review — {date.today().isoformat()}",
             "",
             f"{len(rows)} machine-extracted promise(s) awaiting review. For each: confirm "
             f"(`promise_tracker.py confirm ID --name \"...\"`) or reject. Speaker identity "
             f"is a hypothesis until confirmed — cross-reference the approved meeting report.",
             ""]
    for r in rows:
        dl = r["deadline_date"] or r["deadline_text"] or "none stated"
        lines += [
            f"## [{r['id']}] {r['summary']}",
            "",
            f"- **Meeting:** {r['body']}, {r['meeting_date']} (`{r['slug']}`) at **{r['timestamp_hms']}**",
            f"- **Speaker:** {r['speaker_label'] or '?'} (role guess: {r['speaker_role_hint'] or '?'}) — UNVERIFIED",
            f"- **Topic:** {r['topic']} · **Deadline:** {dl} ({r['deadline_kind']})",
            "",
            f"> {r['quote']}",
            "",
        ]
    out.write_text("\n".join(lines))
    print(f"Wrote {out} ({len(rows)} promises)")
    return 0


def cmd_due(args):
    conn = open_db()
    horizon = (date.today() + timedelta(days=args.within)).isoformat()
    rows = _rows(conn,
                 "status IN ('human-confirmed', 'machine-extracted') AND "
                 "((deadline_date IS NOT NULL AND deadline_date <= ?) OR "
                 " (follow_up_date IS NOT NULL AND follow_up_date <= ?))",
                 (horizon, horizon))
    today = date.today().isoformat()
    for r in rows:
        d = r["deadline_date"] or r["follow_up_date"]
        flag = "OVERDUE" if d < today else "due soon"
        print(f"[{r['id']:3d}] {flag} {d} ({r['status']}) {r['body']} {r['meeting_date']}: {r['summary']}")
    print(f"\n{len(rows)} promise(s) at or past deadline within {args.within} days")
    return 0


def main():
    p = argparse.ArgumentParser(description="What They Promised — evidence ledger")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("extract", help="Extract promises from transcript JSON(s)")
    e.add_argument("files", nargs="*", help="Transcript JSON paths")
    e.add_argument("--all", action="store_true", help="All non-partial transcripts")
    e.set_defaults(func=cmd_extract)

    l = sub.add_parser("list", help="List promises")
    l.add_argument("--status", choices=VALID_STATUSES)
    l.add_argument("--slug")
    l.set_defaults(func=cmd_list)

    s = sub.add_parser("show", help="Show one promise in full")
    s.add_argument("id", type=int)
    s.set_defaults(func=cmd_show)

    c = sub.add_parser("confirm", help="Mark human-confirmed")
    c.add_argument("id", type=int)
    c.add_argument("--name", help="Confirmed real speaker name")
    c.add_argument("--follow-up", dest="follow_up", help="Follow-up date YYYY-MM-DD")
    c.add_argument("--notes")
    c.set_defaults(func=cmd_confirm)

    r = sub.add_parser("reject", help="Mark rejected")
    r.add_argument("id", type=int)
    r.add_argument("--notes")
    r.set_defaults(func=cmd_reject)

    x = sub.add_parser("export-review", help="Markdown review sheet of machine-extracted rows")
    x.add_argument("--slug")
    x.set_defaults(func=cmd_export_review)

    d = sub.add_parser("due", help="Promises at/past deadline")
    d.add_argument("--within", type=int, default=14)
    d.set_defaults(func=cmd_due)

    args = p.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
