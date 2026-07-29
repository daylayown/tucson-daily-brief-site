#!/usr/bin/env python3
"""Fetch and extract Legistar agenda attachments as drafter context.

Why this exists: `ai_reporter.py` used to write post-meeting reports from the
transcript alone. Every fact that lived only in a document — contract amounts,
vendor names, program acronyms, appointee spellings — had to be reconstructed
from audio, and Deepgram is not a reliable source for any of those. The
2026-07-28 Pima County report needed five corrections that were all sitting in
agenda documents the model never saw.

This module pulls the attachment text so the drafter can read it.

Scope notes:
  - Discussion items only. Consent-calendar items already carry vendor, amount
    and program name in their agenda line (that line is what corrected the
    INVEST contract), so their attachments are not worth the tokens.
  - PDFs only, via `pdftotext -layout` (poppler-utils).
  - Hard caps per attachment and overall — agendas routinely carry hundreds of
    pages of exhibits.

Legistar attachments are mutable. A matter can gain a revised memo days after
the agenda first posts; on 2026-07-28 the operative membership slate arrived
~26 hours before the meeting and superseded the one mined five days earlier.
`build_manifest()` returns the modification stamps so callers can detect that.
"""

import json
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

LEGISTAR_BASE = "https://webapi.legistar.com/v1/pima"
SITE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SITE_DIR / "agenda-watch"

# Caps. A single exhibit can run hundreds of pages; the drafter needs the
# substance of the staff memo, not the appendices.
#
# The per-item cap matters as much as the total. Agendas are ordered by
# procedure, not importance — proclamations and liquor licenses come first and
# the consequential items come last. Without a per-item cap the budget is spent
# before the digest reaches them: the first run of this module burned all
# 60,000 characters on items 6-14 and never got to the item 25 IDA memos, which
# were the whole reason for building it.
# A 3-hour meeting transcript formats to roughly 110,000 characters, so a
# 120,000-character digest still lands the whole prompt near 60k tokens.
MAX_CHARS_PER_ATTACHMENT = 12_000
MAX_CHARS_PER_ITEM = 8_000
MAX_CHARS_PER_ITEM_FLOOR = 3_000
MAX_CHARS_TOTAL = 120_000
HTTP_TIMEOUT = 30

# Attachment-name prefixes worth skipping. These are Pima Legistar conventions
# for packets whose substance is already in the agenda line — liquor-license
# application forms and purchase orders carry vendor, amount and address in the
# item text, so the PDF adds pages without adding facts.
_SKIP_ATTACHMENT_RE = re.compile(r"^(FLP_|PO\d|G-LIB-)", re.I)


def _fetch_json(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_attachment_list(matter_id: int) -> list[dict]:
    """Return attachment records for a Legistar matter, newest last.

    Sorted by MatterAttachmentSort so a revised memo reads after the original,
    which matches how the board received them.
    """
    if not matter_id:
        return []
    try:
        rows = _fetch_json(f"{LEGISTAR_BASE}/matters/{matter_id}/attachments")
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as exc:
        print(f"    WARNING: attachment list failed for matter {matter_id}: {exc}",
              file=sys.stderr)
        return []
    if not isinstance(rows, list):
        return []
    return sorted(rows, key=lambda r: r.get("MatterAttachmentSort") or 0)


def extract_pdf_text(url: str) -> str:
    """Download a PDF and return its text, or '' if it can't be read."""
    if not url or not url.lower().endswith(".pdf"):
        return ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TucsonDailyBrief/1.0"})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            blob = resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        print(f"    WARNING: download failed {url}: {exc}", file=sys.stderr)
        return ""

    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(blob)
        tmp.flush()
        try:
            out = subprocess.run(
                ["pdftotext", "-layout", tmp.name, "-"],
                capture_output=True, timeout=60,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            print(f"    WARNING: pdftotext failed: {exc}", file=sys.stderr)
            return ""
    text = out.stdout.decode("utf-8", errors="replace")
    # Collapse the whitespace -layout produces without losing line structure.
    text = re.sub(r"[ \t]{3,}", "  ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_manifest(items: list[dict]) -> dict:
    """Map matter id -> {attachment name: last-modified stamp}.

    Compared across runs to spot documents added or revised after the agenda
    first posted. Cheap: one API call per discussion item, no downloads.
    """
    manifest = {}
    for item in items:
        matter_id = item.get("EventItemMatterId")
        if not matter_id:
            continue
        rows = fetch_attachment_list(matter_id)
        if rows:
            manifest[str(matter_id)] = {
                r.get("MatterAttachmentName", "?"): r.get("MatterAttachmentLastModifiedUtc", "")
                for r in rows
            }
    return manifest


def diff_manifests(old: dict, new: dict) -> list[str]:
    """Human-readable list of attachments added or revised since `old`."""
    changes = []
    for matter_id, attachments in new.items():
        previous = old.get(matter_id, {})
        for name, modified in attachments.items():
            if name not in previous:
                changes.append(f"NEW: {name} (matter {matter_id})")
            elif previous[name] != modified:
                changes.append(f"REVISED: {name} (matter {matter_id})")
    return changes


def build_digest(items: list[dict], base: str, write: bool = True) -> tuple[str, dict]:
    """Build the attachment-text digest for a meeting's discussion items.

    Returns (digest_markdown, manifest). Writes `<base>-attachments.md` and
    `<base>-attachments.json` unless `write` is False.
    """
    discussion = [i for i in items if not i.get("EventItemConsent")]

    # Every discussion item gets a guaranteed share rather than first-come.
    # Agendas run proclamations and zoning hearings before the consequential
    # business, so a purely sequential spend never reaches the end of the list.
    per_item_cap = MAX_CHARS_TOTAL // max(1, len(discussion))
    per_item_cap = max(MAX_CHARS_PER_ITEM_FLOOR, min(MAX_CHARS_PER_ITEM, per_item_cap))

    lines = [
        f"# Agenda attachment text — {base}",
        "",
        "Extracted from Legistar for discussion items. Reporter reference and "
        "drafter context; not for publication.",
        "",
    ]
    manifest = {}
    total = 0
    fetched = 0

    for item in discussion:
        matter_id = item.get("EventItemMatterId")
        if not matter_id:
            continue
        rows = fetch_attachment_list(matter_id)
        if not rows:
            continue
        manifest[str(matter_id)] = {
            r.get("MatterAttachmentName", "?"): r.get("MatterAttachmentLastModifiedUtc", "")
            for r in rows
        }
        if total >= MAX_CHARS_TOTAL:
            continue

        title = (item.get("EventItemTitle") or "").strip().split("\n")[0]
        agenda_no = item.get("EventItemAgendaNumber") or "?"
        header_written = False
        item_total = 0

        # Newest first: when staff files a revision, the later document governs
        # and the earlier one is superseded. On 2026-07-28 the operative
        # membership slate was a 3,574-character revision filed the day before,
        # while the superseded version it replaced ran 18,440 characters — read
        # in filing order, the stale one would have crowded out the real one.
        for row in sorted(rows, key=lambda r: r.get("MatterAttachmentLastModifiedUtc") or "",
                          reverse=True):
            if total >= MAX_CHARS_TOTAL or item_total >= per_item_cap:
                break
            name = row.get("MatterAttachmentName", "attachment")
            if _SKIP_ATTACHMENT_RE.match(name):
                continue
            text = extract_pdf_text(row.get("MatterAttachmentHyperlink", ""))
            if not text:
                continue
            budget = min(MAX_CHARS_PER_ATTACHMENT, per_item_cap - item_total)
            truncated = len(text) > budget
            if truncated:
                text = text[:budget]
            if not header_written:
                lines += ["---", f"## Item {agenda_no}: {title}", ""]
                header_written = True
            stamp = row.get("MatterAttachmentLastModifiedUtc", "")
            lines.append(f"### {name}" + (f"  _(last modified {stamp})_" if stamp else ""))
            lines.append("")
            lines.append("```")
            lines.append(text)
            if truncated:
                lines.append(f"[... truncated at {MAX_CHARS_PER_ATTACHMENT} characters ...]")
            lines.append("```")
            lines.append("")
            total += len(text)
            item_total += len(text)
            fetched += 1

    if total >= MAX_CHARS_TOTAL:
        lines.append(f"*Digest capped at {MAX_CHARS_TOTAL} characters; "
                     f"later attachments omitted.*")

    digest = "\n".join(lines)

    if write:
        OUTPUT_DIR.mkdir(exist_ok=True)
        (OUTPUT_DIR / f"{base}-attachments.md").write_text(digest)
        (OUTPUT_DIR / f"{base}-attachments.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(f"  Attachments: {fetched} extracted, {total:,} chars "
              f"-> agenda-watch/{base}-attachments.md")

    return digest, manifest


def load_manifest(base: str) -> dict:
    path = OUTPUT_DIR / f"{base}-attachments.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError):
        return {}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: agenda_attachments.py <event_id> <base-slug>", file=sys.stderr)
        sys.exit(1)
    event_id, base = sys.argv[1], sys.argv[2]
    event_items = _fetch_json(f"{LEGISTAR_BASE}/events/{event_id}/eventitems?AgendaNote=1")
    build_digest(event_items, base)
