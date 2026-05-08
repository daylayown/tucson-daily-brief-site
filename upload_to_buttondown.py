#!/usr/bin/env python3
"""Upload a TDB Weekly newsletter draft to Buttondown.

Reads a markdown draft from newsletter/drafts/, strips the metadata header
that generate_newsletter.py adds, derives a subject line from the filename,
and creates a draft email in Buttondown via API. Prints the edit URL.

Usage:
    python3 upload_to_buttondown.py newsletter/drafts/tdb-weekly-2026-05-10.md
    python3 upload_to_buttondown.py <file> --subject "Custom subject"
    python3 upload_to_buttondown.py <file> --dry-run

Requires BUTTONDOWN_API_KEY environment variable.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

API_BASE = "https://api.buttondown.email/v1"
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def strip_metadata_header(md: str) -> str:
    """Drop the *Draft generated...* preamble that generate_newsletter.py adds.

    The generator emits 4 italic metadata lines, then a `---` separator, then
    the actual newsletter body. We split on the first `---` and keep the
    second half. If no separator is found, return the file unchanged.
    """
    parts = md.split("\n---\n", 1)
    return parts[1].lstrip() if len(parts) == 2 else md


def parse_date_from_name(name: str) -> datetime | None:
    m = DATE_RE.search(name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d")
    except ValueError:
        return None


def default_subject(send_date: datetime | None) -> str:
    if send_date is None:
        return "TDB Weekly"
    return f"TDB Weekly — {send_date.strftime('%B')} {send_date.day}, {send_date.year}"


def create_draft(api_key: str, subject: str, body: str) -> dict:
    payload = {
        "subject": subject,
        "body": body,
        "status": "draft",
        "email_type": "public",
    }
    req = urllib.request.Request(
        f"{API_BASE}/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Buttondown API returned HTTP {e.code}: {err_body}")


def main():
    parser = argparse.ArgumentParser(description="Upload a newsletter draft to Buttondown.")
    parser.add_argument("file", type=str, help="Markdown draft file (e.g., newsletter/drafts/tdb-weekly-2026-05-10.md)")
    parser.add_argument("--subject", type=str, help="Override the subject line")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded; skip API call")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    raw = path.read_text()
    body = strip_metadata_header(raw)
    if not body.strip():
        print("ERROR: draft body is empty after stripping metadata header.", file=sys.stderr)
        sys.exit(1)

    send_date = parse_date_from_name(path.name)
    subject = args.subject or default_subject(send_date)

    print(f"File:        {path}")
    print(f"Subject:     {subject}")
    print(f"Body length: {len(body):,} chars")

    if args.dry_run:
        print("\n--- DRY RUN: body preview (first 600 chars) ---\n")
        print(body[:600])
        if len(body) > 600:
            print(f"\n[... {len(body) - 600:,} more chars truncated ...]")
        return

    api_key = os.environ.get("BUTTONDOWN_API_KEY")
    if not api_key:
        print("ERROR: BUTTONDOWN_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print("\nUploading to Buttondown...")
    result = create_draft(api_key, subject, body)
    email_id = result.get("id", "(no id)")
    edit_url = result.get("absolute_url") or f"https://buttondown.com/emails/{email_id}"
    print(f"\n  Draft created: {email_id}")
    print(f"  Edit at:       {edit_url}")


if __name__ == "__main__":
    main()
