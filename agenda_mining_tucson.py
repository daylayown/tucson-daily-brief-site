#!/usr/bin/env python3
"""
City of Tucson Mayor & Council — Agenda Mining Pipeline

Fetches upcoming meeting agendas from the Hyland OnBase system (PDF),
extracts text, and generates a "What to Watch" markdown summary.
Previews are auto-published by check_agendas.sh.

Usage:
    python agenda_mining_tucson.py                     # Check for new meetings
    python agenda_mining_tucson.py --meeting-id 1917   # Analyze a specific meeting
    python agenda_mining_tucson.py --publish <file>     # Publish preview to site

Output saved to: agenda-watch/tucson-YYYY-MM-DD-{preview,full}.md
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# --- Config ---
ONBASE_BASE = "https://tucsonaz.hylandcloud.com/221agendaonline"
SITE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = str(SITE_DIR / "agenda-watch")
PUBLISHED_DIR = SITE_DIR / "meeting-watch"
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Meeting types we care about (from the download filename patterns)
COUNCIL_MEETING_TYPES = [
    "Mayor___Council_-_Regular",
    "Mayor___Council_-_Special",
]


def fetch_url(url: str, binary: bool = False):
    """Fetch content from a URL."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "TucsonDailyBrief/1.0 (agenda mining)",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        if binary:
            return resp.read()
        return resp.read().decode("utf-8", errors="replace")


def get_meetings() -> list[dict]:
    """Fetch the meeting search page and extract meeting info from download links."""
    url = f"{ONBASE_BASE}/Meetings/Search?term=&CIession=&dateRange=thismonth&startDate=&endDate=&meetingType="
    html = fetch_url(url)

    meetings = []
    seen_ids = set()

    # Parse meeting info from PDF download filenames
    # Pattern: Downloadfile/Mayor___Council_-_Regular_1917_Agenda_3_3_2026_5_30_00_PM.pdf?documentType=1&meetingId=1917
    pattern = re.compile(
        r'Downloadfile/(.+?)_(\d+)_Agenda_(\d{1,2})_(\d{1,2})_(\d{4})_(\d{1,2})_(\d{2})_\d{2}_(AM|PM)\.pdf\?documentType=1(?:&amp;|&)meetingId=(\d+)',
        re.IGNORECASE,
    )

    for m in pattern.finditer(html):
        meeting_name = m.group(1).replace('___', ' & ').replace('_-_', ' - ').replace('_', ' ')
        meeting_id = m.group(9)
        month = int(m.group(3))
        day = int(m.group(4))
        year = int(m.group(5))
        hour = int(m.group(6))
        minute = int(m.group(7))
        ampm = m.group(8)

        if meeting_id in seen_ids:
            continue
        seen_ids.add(meeting_id)

        if ampm == "PM" and hour != 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0

        try:
            date = datetime(year, month, day, hour, minute)
        except ValueError:
            continue

        raw_type = m.group(1)
        is_council = any(t in raw_type for t in COUNCIL_MEETING_TYPES)

        meetings.append({
            "id": meeting_id,
            "name": meeting_name,
            "raw_type": raw_type,
            "date": date,
            "date_str": date.strftime("%B %d, %Y"),
            "time_str": date.strftime("%I:%M %p"),
            "is_council": is_council,
        })

    # Sort by date
    meetings.sort(key=lambda x: x["date"])
    return meetings


def strip_boilerplate(text: str) -> str:
    """Remove the standard boilerplate pages (English/Spanish notices, council roster, etc.)."""
    # Try to find the start of the actual agenda content
    # Tucson agendas have 2 pages of boilerplate before "REGULAR AGENDA" or "MAYOR & COUNCIL"
    # on the third page
    markers = [
        "REGULAR AGENDA",
        "STUDY SESSION AGENDA",
        "SPECIAL MEETING AGENDA",
        "1.    ROLL CALL",
        "1.\tROLL CALL",
    ]
    for marker in markers:
        idx = text.find(marker)
        if idx != -1:
            return text[idx:]

    # Fallback: skip past the Spanish translation section
    spanish_end = text.find("AVISO & AGENDA")
    if spanish_end != -1:
        # Find the next page break or major section after the Spanish text
        after_spanish = text[spanish_end:]
        # Look for numbered items
        item_match = re.search(r'\n1\.\s+', after_spanish)
        if item_match:
            return after_spanish[item_match.start():]

    return text


def download_agenda_pdf(meeting_id: str) -> str | None:
    """Download the agenda PDF and extract text using pdftotext."""
    url = f"{ONBASE_BASE}/Documents/ViewDocument?meetingId={meeting_id}&documentType=1"

    try:
        pdf_data = fetch_url(url, binary=True)
    except Exception as e:
        print(f"  ERROR: Failed to download PDF: {e}")
        return None

    if not pdf_data or len(pdf_data) < 100:
        print("  ERROR: PDF download returned empty or too small")
        return None

    # Check it's actually a PDF
    if not pdf_data[:5] == b'%PDF-':
        print("  ERROR: Downloaded file is not a PDF")
        return None

    # Write to temp file and extract text
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_data)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["pdftotext", "-layout", tmp_path, "-"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            print(f"  ERROR: pdftotext failed: {result.stderr}")
            return None
        text = result.stdout
        # Strip boilerplate to focus on actual agenda items
        text = strip_boilerplate(text)
        return text
    except Exception as e:
        print(f"  ERROR: pdftotext failed: {e}")
        return None
    finally:
        os.unlink(tmp_path)


def analyze_with_claude(meeting_date: datetime, meeting_name: str, agenda_text: str) -> str | None:
    """Send agenda to Claude for editorial analysis."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  WARNING: ANTHROPIC_API_KEY not set, skipping LLM analysis")
        return None

    date_str = meeting_date.strftime("%A, %B %d, %Y")

    # Truncate if very long (boilerplate already stripped, so 30k should capture full agendas)
    if len(agenda_text) > 30000:
        agenda_text = agenda_text[:30000] + "\n\n[TRUNCATED]"

    prompt = f"""You are a local government reporter covering the City of Tucson, Arizona for the Tucson Daily Brief. Analyze the following Tucson Mayor & Council meeting agenda for {date_str}.

Your job: identify the 3-8 most newsworthy items and explain WHY they matter to Tucson residents. Think like a beat reporter — what would your editor want you to cover? What affects people's lives, money, safety, or rights?

Tucson context: Tucson is a city of ~550,000 in southern Arizona, the urban core of Pima County. Key ongoing stories include:
- Affordable housing crisis and homelessness response
- Water sustainability (Colorado River, CAP allocations, reclaimed water)
- Public safety staffing and police reform
- Regional transportation (RTA/transit expansion, Broadway corridor, streetcar)
- Immigration policy and sanctuary city status
- Economic development and downtown revitalization
- Climate adaptation and urban heat mitigation
- City budget pressures and infrastructure backlog

Prioritize:
1. Policy changes that affect residents (ordinances, zoning, regulations)
2. Large spending decisions or contracts (especially >$1M)
3. Public hearings where community input is sought
4. Development and land use decisions
5. Items that connect to ongoing regional stories
6. Intergovernmental agreements (with Pima County, RTA, state, federal)

De-prioritize:
- Proclamations and ceremonial items
- Routine meeting minutes approval
- Individual liquor license applications (mention as a group if many)
- Board/committee appointments (unless controversial)

For each item you highlight, write:
- A clear, specific headline (not the bureaucratic title)
- The item number and any resolution/ordinance number
- 2-3 sentences explaining what it is and why it matters
- Note if it's on the consent agenda (could pass without discussion)

Format as markdown. Start with a brief 2-sentence overview of the meeting, then list your picks under "## Top Items to Watch" with ### for each item.

AGENDA TEXT:

{agenda_text}"""

    request_body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 2500,
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
            if content and content[0].get("type") == "text":
                return content[0]["text"]
            return None
    except Exception as e:
        print(f"  WARNING: Claude API call failed: {e}")
        return None


def generate_preview(meeting_date: datetime, meeting_name: str, analysis: str) -> str:
    """Generate the publishable preview."""
    date_str = meeting_date.strftime("%B %d, %Y")
    day_of_week = meeting_date.strftime("%A")

    lines = []
    lines.append(f"# Tucson Mayor & Council — What to Watch")
    lines.append(f"## {day_of_week}, {date_str}")
    lines.append(f"\n{meeting_name}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(analysis)
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by Tucson Daily Brief agenda mining pipeline using {CLAUDE_MODEL}.*")
    lines.append(f"*AI-assisted journalism — auto-published.*")
    lines.append(f"*Source: [City of Tucson Agendas]({ONBASE_BASE})*")

    return "\n".join(lines)


def generate_full_report(meeting_date: datetime, meeting_name: str, agenda_text: str) -> str:
    """Generate the full agenda reference."""
    date_str = meeting_date.strftime("%B %d, %Y")
    day_of_week = meeting_date.strftime("%A")

    lines = []
    lines.append(f"# Tucson Mayor & Council — Full Agenda Reference")
    lines.append(f"## {day_of_week}, {date_str}")
    lines.append(f"\n{meeting_name}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(agenda_text)
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by Tucson Daily Brief agenda mining pipeline*")
    lines.append(f"*Source: [City of Tucson Agendas]({ONBASE_BASE})*")

    return "\n".join(lines)


def publish_preview(preview_path: str) -> None:
    """Convert a preview markdown file to HTML and publish to the site."""
    from agenda_mining import preview_md_to_html, render_meeting_post, escape_html

    md_text = Path(preview_path).read_text()

    match = re.search(r"(\d{4}-\d{2}-\d{2})", Path(preview_path).stem)
    if not match:
        print(f"  ERROR: Could not extract date from {preview_path}")
        return
    date = datetime.strptime(match.group(1), "%Y-%m-%d")
    slug = f"tucson-council-{date.strftime('%Y-%m-%d')}"

    title = "Tucson Mayor & Council — What to Watch"
    for line in md_text.split("\n"):
        if line.startswith("## "):
            title = line[3:].strip()
            break

    PUBLISHED_DIR.mkdir(exist_ok=True)
    body_html = preview_md_to_html(md_text)
    html_path = PUBLISHED_DIR / f"{slug}.html"
    html_path.write_text(render_meeting_post(title, date, body_html))
    print(f"  Published: {html_path}")

    # Rebuild meeting watch index
    from agenda_mining import render_meeting_index
    posts = []
    for f in PUBLISHED_DIR.glob("*.html"):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f.stem)
        if not m:
            continue
        dt = datetime.strptime(m.group(1), "%Y-%m-%d")
        content = f.read_text()
        title_match = re.search(r'<p class="post-meta">(.+?)</p>', content)
        post_title = title_match.group(1) if title_match else f.stem
        lede_match = re.search(r'</p>\s*<(?:p|h[12])>(.+?)</(?:p|h[12])>', content)
        lede = ""
        if lede_match:
            lede = re.sub(r"<[^>]+>", "", lede_match.group(1))
            # Unescape HTML entities so escape_html() doesn't double-encode
            lede = lede.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
            if len(lede) > 120:
                lede = lede[:117] + "..."
        posts.append({"date": dt, "slug": f.stem, "title": post_title, "lede": lede})

    posts.sort(key=lambda p: p["date"], reverse=True)
    index_path = SITE_DIR / "meeting-watch.html"
    index_path.write_text(render_meeting_index(posts))
    print(f"  Updated index: {index_path} ({len(posts)} preview(s))")


def process_meeting(meeting_id: str, meeting_name: str, meeting_date: datetime,
                    no_llm: bool = False) -> str | None:
    """Process a single meeting: download PDF, extract text, analyze, save."""
    date_slug = meeting_date.strftime("%Y-%m-%d")
    base = f"tucson-{date_slug}"

    # Check if preview already exists
    preview_path = os.path.join(OUTPUT_DIR, f"{base}-preview.md")
    if os.path.exists(preview_path):
        print(f"  Preview already exists: {preview_path}")
        return None

    # Download and extract PDF text
    print(f"  Downloading agenda PDF...")
    agenda_text = download_agenda_pdf(meeting_id)
    if not agenda_text:
        print("  No agenda text could be extracted.")
        return None

    # Save full reference
    full_report = generate_full_report(meeting_date, meeting_name, agenda_text)
    full_path = os.path.join(OUTPUT_DIR, f"{base}-full.md")
    with open(full_path, "w") as f:
        f.write(full_report)
    print(f"  Saved full reference: {full_path}")

    # LLM analysis
    if not no_llm:
        print("  Running editorial analysis with Claude...")
        analysis = analyze_with_claude(meeting_date, meeting_name, agenda_text)
        if analysis:
            print("  Editorial analysis complete")
            preview = generate_preview(meeting_date, meeting_name, analysis)
            with open(preview_path, "w") as f:
                f.write(preview)
            print(f"  Saved publishable preview: {preview_path}")
            return preview_path

    return None


def main():
    parser = argparse.ArgumentParser(description="City of Tucson agenda mining pipeline")
    parser.add_argument("--meeting-id", type=str, help="Analyze a specific OnBase meeting ID")
    parser.add_argument("--list", action="store_true", help="List meetings without generating reports")
    parser.add_argument("--all-types", action="store_true", help="Include non-council meetings")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM editorial analysis")
    parser.add_argument("--publish", type=str, metavar="PREVIEW_FILE", help="Publish a preview to the site")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.publish:
        if not os.path.isfile(args.publish):
            print(f"Error: file not found: {args.publish}", file=sys.stderr)
            sys.exit(1)
        print(f"Publishing: {args.publish}")
        publish_preview(args.publish)
        return

    print("Fetching Tucson meeting listings...")
    meetings = get_meetings()

    if not meetings:
        print("  No meetings found.")
        return

    # Filter to council meetings unless --all-types
    if not args.all_types:
        council_meetings = [m for m in meetings if m["is_council"]]
    else:
        council_meetings = meetings

    if args.meeting_id:
        # Find the specific meeting
        target = [m for m in meetings if m["id"] == args.meeting_id]
        if not target:
            print(f"  Meeting ID {args.meeting_id} not found in listing. Processing anyway...")
            # Process it anyway with minimal info
            process_meeting(args.meeting_id, "Mayor & Council", datetime.now(), args.no_llm)
            return
        m = target[0]
        print(f"\nProcessing: {m['date_str']} — {m['name']} (id={m['id']})")
        process_meeting(m["id"], m["name"], m["date"], args.no_llm)
        return

    if args.list:
        for m in meetings:
            marker = " *" if m["is_council"] else ""
            print(f"  {m['date_str']} {m['time_str']} — {m['name']} — id={m['id']}{marker}")
        council_count = len([m for m in meetings if m["is_council"]])
        print(f"\nFound {len(meetings)} meeting(s), {council_count} regular/special council meeting(s).")
        print("(* = council meeting)")
        return

    if not council_meetings:
        print("  No council meetings found. Use --all-types to see all meetings.")
        return

    # Only process upcoming meetings (today or future), or most recent if none upcoming
    now = datetime.now()
    upcoming = [m for m in council_meetings if m["date"].date() >= now.date()]

    if not upcoming:
        # Process the most recent meeting if no upcoming ones
        upcoming = council_meetings[-1:]

    for m in upcoming:
        print(f"\nProcessing: {m['date_str']} — {m['name']} (id={m['id']})")
        process_meeting(m["id"], m["name"], m["date"], args.no_llm)


if __name__ == "__main__":
    main()
