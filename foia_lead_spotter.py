#!/usr/bin/env python3
"""
FOIA Lead Spotter — public-records-request lead pipeline

Trawls published news reports (news-reports/*.html) for loose ends worth an
Arizona Public Records Law request (A.R.S. § 39-121) — decisions whose
implementation was never reported, canceled contracts with no disposition of
the assets, studies referenced but never released — and for each lead drafts
a send-ready request email.

The model's job is editorial judgment only: spotting the lead and naming the
specific records. Everything legal/mechanical — the statute citation, the
non-commercial declaration, the custodian address — is assembled
deterministically from a template plus pipeline/records_custodians.json.
Custodian contact info in that file must be verified against an official
government page before it is added; a lead pointing at a government we have
no verified channel for gets flagged "research needed", never a guessed email.

Nothing sends automatically. Drafts land in records-requests/drafts/
(gitignored — the repo is public, and an unsent request shouldn't be), and a
consolidated Telegram notification lists what was found. The human reviews,
edits, and sends from nicholas@daylayown.org.

Usage:
    python foia_lead_spotter.py                  # Scan new reports, draft leads
    python foia_lead_spotter.py --dry-run        # Show leads, write nothing
    python foia_lead_spotter.py --force          # Reprocess all reports
    python foia_lead_spotter.py --limit N        # At most N reports (testing)
    python foia_lead_spotter.py --report FILE    # One specific report

Output:
    records-requests/drafts/YYYY-MM-DD-{slug}.md   # One draft per lead
    records-requests/.processed.txt                # Idempotency log
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime
from html import unescape
from pathlib import Path

# --- Config ---
SITE_DIR = Path(__file__).resolve().parent
NEWS_REPORTS_DIR = SITE_DIR / "news-reports"
OUTPUT_DIR = SITE_DIR / "records-requests"
DRAFTS_DIR = OUTPUT_DIR / "drafts"
PROCESSED_LOG = OUTPUT_DIR / ".processed.txt"
CUSTODIANS_PATH = SITE_DIR / "pipeline" / "records_custodians.json"
SEND_TELEGRAM = Path.home() / ".openclaw/skills/tucson-daily-brief/scripts/send_telegram.py"
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

REQUESTER_NAME = "Nicholas De Leon"
REQUESTER_EMAIL = "nicholas@daylayown.org"
REQUESTER_OUTLET = "Tucson Daily Brief (tucsondailybrief.com)"


def load_custodians() -> dict:
    if not CUSTODIANS_PATH.exists():
        print(f"ERROR: custodian table not found: {CUSTODIANS_PATH}", file=sys.stderr)
        sys.exit(1)
    return json.loads(CUSTODIANS_PATH.read_text())


def load_processed() -> set[str]:
    if not PROCESSED_LOG.exists():
        return set()
    return {line.strip() for line in PROCESSED_LOG.read_text().splitlines() if line.strip()}


def mark_processed(filename: str) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    with PROCESSED_LOG.open("a") as f:
        f.write(filename + "\n")


def extract_article_text(html: str) -> str:
    """Pull readable article text out of a published news-report page.

    Grabs the <article> block (falls back to <main>), drops script/style,
    strips tags, and unescapes entities. Good enough for a prompt — this is
    input to editorial judgment, not something re-published.
    """
    m = re.search(r"<article\b.*?>(.*?)</article>", html, re.DOTALL)
    if not m:
        m = re.search(r"<main\b.*?>(.*?)</main>", html, re.DOTALL)
    body = m.group(1) if m else html
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", body, flags=re.DOTALL)
    body = re.sub(r"<br\s*/?>|</p>|</h[1-6]>|</li>", "\n", body)
    body = re.sub(r"<[^>]+>", " ", body)
    body = unescape(body)
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n\s*\n\s*\n+", "\n\n", body)
    return body.strip()


def find_leads(report_text: str, report_name: str, governments: list[str]) -> list[dict]:
    """One Claude call: editorial judgment on what's worth a records request.

    Returns a list of leads (zero is a normal, expected answer). The model
    picks the responsible government from a fixed list derived from the
    custodian table — it never supplies contact info, and the records list
    must be anchored in facts quoted from the report.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return []

    gov_list = "\n".join(f"- {g}" for g in governments)

    prompt = f"""You are an investigative editor at a small Tucson news outlet reviewing one of our own published meeting reports for FOLLOW-UP opportunities via the Arizona Public Records Law (A.R.S. § 39-121).

A good lead is a specific, answerable loose end where a public record would advance the story. Classic signals:
- A decision was made but implementation was never reported (contract canceled — what happened to the equipment? program approved — was it stood up?)
- A document is referenced but not public (an audit, study, assessment, legal memo described but not released)
- A number or claim by an official that a record could verify (costs, counts, timelines)
- A sole-source or unusual procurement
- Follow-through with a deadline that has now passed

Rules:
- ZERO leads is a perfectly good answer. Most routine reports have none worth an editor's time. Only flag leads where the record would likely yield a publishable follow-up.
- Every lead MUST quote the sentence(s) from the report that anchor it, verbatim, in source_facts. Do not invent or embellish facts.
- records_sought must name concrete, identifiable records a clerk could locate (e.g. "the termination notice and any correspondence with Vendor X between March and June 2026"), not vague topics ("all documents about X").
- Include a date range in each record description whenever the report supports one — unbounded requests get slow-walked.
- responsible_government MUST be exactly one of:
{gov_list}
If the records would be held by a government not on that list, use "OTHER: <name>".
- Maximum 3 leads per report. Rank by news value.

Report file: {report_name}

REPORT TEXT:

{report_text}

Return a JSON object only, no other text:
{{
  "leads": [
    {{
      "headline": "short working title for the follow-up story",
      "responsible_government": "one of the listed governments, or OTHER: <name>",
      "records_sought": ["specific record description with date range", "..."],
      "source_facts": "verbatim quote(s) from the report that anchor this lead",
      "why_newsworthy": "1-2 sentences: what the record would tell readers",
      "urgency": "high|normal"
    }}
  ]
}}"""

    request_body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 2000,
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read())
            content = result.get("content", [])
            if not content or content[0].get("type") != "text":
                return []
            text = content[0]["text"].strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\n?", "", text)
                text = re.sub(r"\n?```$", "", text)
            data = json.loads(text)
            return data.get("leads") or []
    except json.JSONDecodeError as e:
        print(f"  WARNING: Claude returned invalid JSON: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  WARNING: Claude API call failed: {e}", file=sys.stderr)
        return []


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60]


def request_email_body(lead: dict, custodian: dict | None) -> str:
    """Assemble the request email deterministically. The statute language,
    declarations, and formatting are fixed; only the records list and the
    story-agnostic subject come from the lead."""
    records_lines = "\n".join(f"  {i}. {r}" for i, r in enumerate(lead["records_sought"], 1))
    office = custodian.get("office", "Public Records Custodian") if custodian else "Public Records Custodian"

    return f"""Dear {office}:

Pursuant to the Arizona Public Records Law, A.R.S. § 39-121 et seq., I request copies of the following public records:

{records_lines}

I am a journalist and request these records for news gathering and dissemination; this request is made for a non-commercial purpose as defined by A.R.S. § 39-121.03(D).

I request electronic copies (PDF or native format) delivered by email where practicable. If any portion of a requested record is exempt from disclosure, please release the remainder and identify the specific exemption claimed for each redaction or withholding.

If fees for copies will exceed $25, please notify me of the estimated cost before fulfilling the request. If you are not the custodian of any of these records, I would appreciate being directed to the correct office.

A.R.S. § 39-121.01(E) requires that public records be promptly furnished; please let me know when I can expect a response.

Thank you for your time.

{REQUESTER_NAME}
{REQUESTER_OUTLET}
{REQUESTER_EMAIL}"""


def render_draft(lead: dict, custodian: dict | None, report_name: str, today: str) -> str:
    """A draft file: structured header the human scans, then the email body."""
    gov = lead["responsible_government"]
    if custodian is None:
        to_line = "RESEARCH NEEDED — no verified records channel for this government"
        channel_note = "Verify the custodian on the government's official site before sending, then add it to pipeline/records_custodians.json."
    elif custodian.get("channel_type") in ("portal", "form"):
        kind = custodian["channel_type"]
        to_line = f"(submit via {kind}) {custodian.get('portal_url', '')}"
        channel_note = f"This government takes requests through a {kind}, not email — use {custodian.get('portal_url', 'the linked page')} and adapt the body below. Verified: {custodian.get('source_url', 'n/a')}"
    else:
        to_line = custodian.get("email", "")
        channel_note = f"Verified custodian channel: {custodian.get('source_url', 'n/a')}"
    if custodian and custodian.get("notes"):
        channel_note += f" Note: {custodian['notes']}"

    subject = f"Public Records Request — {lead['headline']}"
    urgency = lead.get("urgency", "normal")

    return f"""---
status: DRAFT — review and send manually
date: {today}
to: {to_line}
from: {REQUESTER_EMAIL}
subject: {subject}
government: {gov}
urgency: {urgency}
source_report: news-reports/{report_name}
---

## Why this request

{lead.get('why_newsworthy', '')}

**Anchored in the report:**

> {lead.get('source_facts', '')}

**Channel:** {channel_note}

## Email body (copy below the line)

---

{request_email_body(lead, custodian)}
"""


def send_telegram_summary(drafted: list[dict]) -> None:
    if not SEND_TELEGRAM.exists():
        print("  WARNING: send_telegram.py not found, skipping notification", file=sys.stderr)
        return
    lines = [f"🗄️ RECORDS-REQUEST LEADS — {len(drafted)} new draft(s)\n"]
    for d in drafted:
        flag = "🔴 " if d["lead"].get("urgency") == "high" else ""
        lines.append(f"{flag}• {d['lead']['headline']}")
        lines.append(f"  {d['lead']['responsible_government']}")
        lines.append(f"  {d['path']}\n")
    lines.append("Drafts are ready to review — nothing has been sent. Arizona Public Records Law (A.R.S. § 39-121), send from nicholas@daylayown.org.")
    msg = "\n".join(lines)
    with tempfile.NamedTemporaryFile("w", suffix=".md", prefix="records-leads-", delete=False) as f:
        f.write(msg)
        tmp = f.name
    try:
        sys.stdout.flush()  # keep parent/child output ordered in cron logs
        subprocess.run([sys.executable, str(SEND_TELEGRAM), tmp], check=False)
    finally:
        os.unlink(tmp)


def process_report(report_path: Path, custodians: dict, dry_run: bool, today: str) -> list[dict]:
    """Scan one published report; return list of {lead, path} drafted."""
    text = extract_article_text(report_path.read_text())
    if len(text) < 400:
        print(f"  {report_path.name}: too little article text, skipping")
        return []

    print(f"  {report_path.name}: scanning for leads...")
    leads = find_leads(text, report_path.name, list(custodians.keys()))
    if not leads:
        print("    no leads")
        return []

    drafted = []
    for lead in leads[:3]:
        gov = lead.get("responsible_government", "")
        custodian = custodians.get(gov)
        slug = slugify(lead.get("headline", "lead"))
        out_path = DRAFTS_DIR / f"{today}-{slug}.md"

        if not lead.get("records_sought"):
            continue

        if dry_run:
            print(f"    [DRY RUN] {lead['headline']}  ({gov}, {lead.get('urgency')})")
            for r in lead["records_sought"]:
                print(f"              - {r}")
            drafted.append({"lead": lead, "path": str(out_path)})
            continue

        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render_draft(lead, custodian, report_path.name, today))
        print(f"    Drafted: {out_path.relative_to(SITE_DIR)}")
        drafted.append({"lead": lead, "path": str(out_path.relative_to(SITE_DIR))})

    return drafted


def main():
    parser = argparse.ArgumentParser(description="FOIA Lead Spotter — records-request lead pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Show leads, write nothing, mark nothing processed")
    parser.add_argument("--force", action="store_true", help="Reprocess all reports, ignoring .processed.txt")
    parser.add_argument("--limit", type=int, help="Process at most N reports")
    parser.add_argument("--report", help="Process one specific report file (name or path)")
    args = parser.parse_args()

    custodians = load_custodians()
    today = datetime.now().strftime("%Y-%m-%d")

    if args.report:
        p = Path(args.report)
        if not p.exists():
            p = NEWS_REPORTS_DIR / args.report
        if not p.exists():
            print(f"ERROR: report not found: {args.report}", file=sys.stderr)
            sys.exit(1)
        files = [p]
    else:
        processed = set() if args.force else load_processed()
        files = [f for f in sorted(NEWS_REPORTS_DIR.glob("*.html")) if f.name not in processed]
        if args.limit:
            files = files[: args.limit]

    print(f"Scanning {len(files)} report(s)...")
    all_drafted = []
    for f in files:
        all_drafted.extend(process_report(f, custodians, args.dry_run, today))
        if not args.dry_run and not args.report:
            mark_processed(f.name)

    print(f"\n{len(all_drafted)} lead(s) drafted")
    if all_drafted and not args.dry_run:
        send_telegram_summary(all_drafted)


if __name__ == "__main__":
    main()
