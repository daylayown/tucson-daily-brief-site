#!/usr/bin/env python3
"""
Praise Tracker — officials praising named private entities, joined against
pending business before the same government.

The CNN Trump/Truth Social pattern localized: extract every instance of an
official or staff member praising/endorsing a named business, developer,
nonprofit, or vendor in a meeting (verbatim-validated, like promise_tracker),
then deterministically join the praised entity against what we know is
pending: agenda references, Spotted filings, Around Town development cases,
and the Rio Nuevo investigation. A join hit is a LEAD for human verification,
never a finding — innocent explanations are the norm.

Shares promise-ledger/promises.sqlite (table `praise`) and the validation
helpers in promise_tracker.py.

Usage:
    python3 praise_tracker.py extract transcripts/foo.json | --all
    python3 praise_tracker.py list [--status ...] [--slug ...]
    python3 praise_tracker.py report        # join praise vs pending business → review sheet
    python3 praise_tracker.py confirm ID [--name "Real Name"] [--notes TEXT]
    python3 praise_tracker.py reject ID [--notes TEXT]
"""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

from ai_reporter import load_transcript, format_transcript_for_prompt
from promise_tracker import (
    DB_PATH, LEDGER_DIR, TRANSCRIPTS_DIR, TZ_LOCAL,
    body_from_slug, build_locator, call_claude, hms, load_api_key,
    locate_quote, parse_json_array, _norm,
)

SITE_DIR = Path(__file__).resolve().parent

SCHEMA = """
CREATE TABLE IF NOT EXISTS praise (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL,
    body TEXT NOT NULL,
    meeting_date TEXT NOT NULL,
    speaker_label TEXT,
    speaker_role_hint TEXT,
    speaker_name TEXT,
    entity TEXT NOT NULL,
    quote TEXT NOT NULL,
    t_start REAL NOT NULL,
    timestamp_hms TEXT NOT NULL,
    summary TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'machine-extracted',
    notes TEXT,
    extracted_at TEXT NOT NULL,
    UNIQUE(slug, quote)
);
"""


def open_db() -> sqlite3.Connection:
    LEDGER_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.row_factory = sqlite3.Row
    return conn


EXTRACT_PROMPT = """You are an evidence extractor for a local-news accountability tracker covering {body} ({meeting_date}).

Below is a meeting transcript. Find every instance where an OFFICIAL or GOVERNMENT STAFF MEMBER praises, endorses, promotes, or speaks favorably about a NAMED private entity — a specific business, developer, property owner, nonprofit, contractor, or vendor.

Rules:
- ONLY statements by officials or government staff. Never public commenters, never entity representatives talking about themselves.
- The entity must be NAMED (a company, organization, or identifiable proper noun). Generic praise ("our local businesses are great") does not count.
- Exclude praise of other government agencies, government employees, first responders acting officially, or public institutions (schools, libraries). The tracker is about PRIVATE interests before public bodies.
- Exclude routine proclamations/awards ceremonies ONLY if purely ceremonial with no business pending; when unsure, include it.
- ZERO instances is a normal result. Do not pad.
- The "quote" field must be copied VERBATIM, character-for-character, from the transcript — the exact contiguous span containing the praise (1–3 sentences). It is programmatically checked and the entry discarded if it does not match exactly. No paraphrasing, no stitching.
- Speaker names in the transcript are unverified; give a role guess in speaker_role_hint or null.

Respond with ONLY a JSON array (no prose, no code fences). Each element:
{{"quote": "...", "entity": "canonical entity name", "summary": "one sentence: who praised whom and in what context", "speaker_role_hint": "..." or null}}

If there are none, respond with [].

TRANSCRIPT:

{transcript}"""


def extract_file(path: Path, conn: sqlite3.Connection, api_key: str) -> tuple[int, int, int]:
    data = load_transcript(str(path))
    meta = data["meta"]
    slug = meta.get("slug", path.stem)
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
        body=body, meeting_date=meeting_date,
        transcript=format_transcript_for_prompt(data),
    )
    raw = call_claude(prompt, api_key)
    items = parse_json_array(raw) if raw else None
    if items is None:
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
        entity = (it.get("entity") or "").strip()
        summary = (it.get("summary") or "").strip()
        if not quote or not entity or not summary:
            rejected += 1
            continue
        loc = locate_quote(quote, full_text, offsets, segments)
        if loc is None:
            rejected += 1
            print(f"  REJECTED (quote not verbatim): {entity} — {summary[:60]}")
            continue
        t_start, speaker_label = loc
        try:
            conn.execute(
                """INSERT INTO praise(slug, body, meeting_date, speaker_label, speaker_role_hint,
                       entity, quote, t_start, timestamp_hms, summary, extracted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (slug, body, meeting_date, speaker_label, it.get("speaker_role_hint"),
                 entity, quote, t_start, hms(t_start), summary, now),
            )
            accepted += 1
            print(f"  [{hms(t_start)}] {entity}: {summary[:80]}")
        except sqlite3.IntegrityError:
            dupes += 1

    conn.commit()
    print(f"  accepted {accepted}, rejected-by-validation {rejected}, duplicate {dupes}")
    return accepted, rejected, dupes


# ---------------------------------------------------------------------------
# The join: praised entities vs pending business (deterministic, no model)
# ---------------------------------------------------------------------------

STOPWORDS = {
    "the", "of", "and", "inc", "llc", "co", "company", "corp", "corporation",
    "az", "arizona", "tucson", "marana", "oro", "valley", "pima", "county",
    "group", "and", "at", "on",
}


def entity_tokens(name: str) -> set[str]:
    toks = {t for t in re.split(r"[^a-z0-9]+", _norm(name)) if len(t) > 2}
    return toks - STOPWORDS


def scan_corpus_for_entity(entity: str) -> list[tuple[str, str]]:
    """Return (source_file, matched_line) hits for an entity across pending-business
    surfaces. Requires ALL distinctive tokens of the entity name to appear on the
    same line (order-independent), which keeps false positives low for humans to
    then verify. Entities whose name reduces to no distinctive tokens are skipped."""
    toks = entity_tokens(entity)
    # An entity whose name reduces to fewer than 2 distinctive tokens ("KB
    # Home" → {"home"}) would match far too broadly on tokens alone — fall
    # back to exact-phrase matching on the full normalized name instead.
    phrase = _norm(re.sub(r"\(.*?\)", " ", entity))
    phrase = re.sub(r"[^a-z0-9 ]+", " ", phrase)
    phrase = re.sub(r"\s+", " ", phrase).strip()
    use_phrase = len(toks) < 2
    if use_phrase and len(phrase) < 5:
        return []
    hits: list[tuple[str, str]] = []
    surfaces = (
        list((SITE_DIR / "agenda-watch").glob("*-full.md"))
        + list((SITE_DIR / "public-record").glob("liquor-*.html"))
        + list((SITE_DIR / "around-town").glob("*.html"))
        + list((SITE_DIR / "rio-nuevo-investigation").glob("*.md"))
    )
    for f in surfaces:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            nl = re.sub(r"[^a-z0-9 ]+", " ", _norm(re.sub(r"<[^>]+>", " ", line)))
            nl = re.sub(r"\s+", " ", nl)
            if not nl:
                continue
            matched = (phrase in nl) if use_phrase else all(t in nl for t in toks)
            if matched:
                hits.append((str(f.relative_to(SITE_DIR)), line.strip()[:200]))
                break  # one hit per file is enough for the lead
    return hits


def cmd_report(args):
    conn = open_db()
    rows = conn.execute(
        "SELECT * FROM praise WHERE status != 'rejected' ORDER BY meeting_date, t_start"
    ).fetchall()
    out = LEDGER_DIR / "review" / f"praise-report-{date.today().isoformat()}.md"
    out.parent.mkdir(exist_ok=True)
    flagged, unflagged = [], []
    for r in rows:
        hits = scan_corpus_for_entity(r["entity"])
        (flagged if hits else unflagged).append((r, hits))

    lines = [f"# Praise × pending business — {date.today().isoformat()}",
             "",
             f"{len(rows)} praise mention(s); {len(flagged)} with a pending-business join hit.",
             "A join hit is a LEAD, not a finding — verify the item, the timing, and the",
             "innocent explanation before treating it as a story. Speakers are unverified",
             "hypotheses until confirmed against approved reports.",
             ""]
    if flagged:
        lines.append("## ⚑ Praise with pending business (verify each)")
        lines.append("")
        for r, hits in flagged:
            lines += [
                f"### [{r['id']}] {r['entity']} — {r['body']}, {r['meeting_date']} at {r['timestamp_hms']}",
                "",
                f"- **Speaker:** {r['speaker_label'] or '?'} (role guess: {r['speaker_role_hint'] or '?'}) — UNVERIFIED",
                f"- **Summary:** {r['summary']}",
                "",
                f"> {r['quote']}",
                "",
                "**Pending-business hits:**",
            ]
            lines += [f"- `{f}`: {line}" for f, line in hits]
            lines.append("")
    if unflagged:
        lines.append("## Praise with no join hit (context only)")
        lines.append("")
        for r, _ in unflagged:
            lines.append(f"- [{r['id']}] {r['meeting_date']} {r['body']} {r['timestamp_hms']} — "
                         f"{r['entity']}: {r['summary']}")
    out.write_text("\n".join(lines))
    print(f"Wrote {out} ({len(flagged)} flagged / {len(rows)} total)")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_extract(args):
    api_key = load_api_key()
    conn = open_db()
    if args.all:
        paths = sorted(p for p in TRANSCRIPTS_DIR.glob("*.json")
                       if not p.name.endswith("-partial.json"))
    else:
        paths = [Path(p) for p in args.files]
    if not paths:
        print("No transcript files to process."); return 1
    totals = [0, 0, 0]
    for p in paths:
        a, r, d = extract_file(p, conn, api_key)
        totals[0] += a; totals[1] += r; totals[2] += d
    print(f"\nTOTAL: accepted {totals[0]}, rejected-by-validation {totals[1]}, duplicate {totals[2]}")
    return 0


def cmd_list(args):
    conn = open_db()
    where, params = "1=1", []
    if args.status:
        where += " AND status = ?"; params.append(args.status)
    if args.slug:
        where += " AND slug = ?"; params.append(args.slug)
    rows = conn.execute(f"SELECT * FROM praise WHERE {where} ORDER BY meeting_date, t_start",
                        params).fetchall()
    for r in rows:
        who = r["speaker_name"] or r["speaker_role_hint"] or r["speaker_label"] or "?"
        print(f"[{r['id']:3d}] {r['meeting_date']} {r['slug']} {r['timestamp_hms']} "
              f"({r['status']}) {r['entity']} | {who}: {r['summary']}")
    print(f"\n{len(rows)} mention(s)")
    return 0


def _set_status(args, status):
    conn = open_db()
    if not conn.execute("SELECT id FROM praise WHERE id = ?", (args.id,)).fetchone():
        print(f"No praise row with id {args.id}"); return 1
    sets, params = ["status = ?"], [status]
    if getattr(args, "name", None):
        sets.append("speaker_name = ?"); params.append(args.name)
    if getattr(args, "notes", None):
        sets.append("notes = ?"); params.append(args.notes)
    params.append(args.id)
    conn.execute(f"UPDATE praise SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()
    print(f"Praise {args.id} → {status}")
    return 0


def main():
    p = argparse.ArgumentParser(description="Praise × pending business tracker")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("extract"); e.add_argument("files", nargs="*")
    e.add_argument("--all", action="store_true"); e.set_defaults(func=cmd_extract)

    l = sub.add_parser("list"); l.add_argument("--status"); l.add_argument("--slug")
    l.set_defaults(func=cmd_list)

    r = sub.add_parser("report"); r.set_defaults(func=cmd_report)

    c = sub.add_parser("confirm"); c.add_argument("id", type=int)
    c.add_argument("--name"); c.add_argument("--notes")
    c.set_defaults(func=lambda a: _set_status(a, "human-confirmed"))

    j = sub.add_parser("reject"); j.add_argument("id", type=int)
    j.add_argument("--notes")
    j.set_defaults(func=lambda a: _set_status(a, "rejected"))

    args = p.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
