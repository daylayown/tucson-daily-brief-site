#!/usr/bin/env python3
"""
Marana Town Council — Agenda Mining Pipeline

Fetches upcoming meeting agendas from the Destiny Hosted system,
extracts substantive items, and generates a "What to Watch" markdown
summary for human review.

Usage:
    python agenda_mining_marana.py                  # Check current month for meetings
    python agenda_mining_marana.py --seq 3162       # Analyze a specific meeting
    python agenda_mining_marana.py --publish <file>  # Publish preview to site

Output saved to: agenda-watch/marana-YYYY-MM-DD-{preview,full}.md
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# --- Config ---
DESTINY_BASE = "https://destinyhosted.com/agenda_publish.cfm"
DESTINY_ID = "62726"  # Marana's Destiny system ID
SITE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = str(SITE_DIR / "agenda-watch")
PUBLISHED_DIR = SITE_DIR / "meeting-watch"
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Meeting types we care about (skip boards like Public Safety Retirement, CORP, etc.)
COUNCIL_MEETING_TYPES = [
    "council-regular meeting",
    "council-special meeting",
    "council regular meeting",
    "council special meeting",
    "regular meeting",
    "special meeting",
]


def fetch_html(url: str) -> str:
    """Fetch HTML content from a URL."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "TucsonDailyBrief/1.0 (agenda mining)",
        "Accept": "text/html",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def get_meetings_for_month(year: int, month: int) -> list[dict]:
    """Fetch the meeting listing page and extract council meetings."""
    url = (
        f"{DESTINY_BASE}?id={DESTINY_ID}&mt=ALL&vl=true"
        f"&get_month={month}&get_year={year}"
    )
    html = fetch_html(url)

    meetings = []

    # The Destiny system HTML structure:
    # <a href="...&amp;dsp=ag&amp;seq=NNNN" ...>March 3, 2026</a>
    # followed by a <td> with the meeting type like "Council-Regular Meeting"

    # Find agenda links — note &amp; encoding in href
    link_pattern = re.compile(
        r'<a\s+href="[^"]*?(?:&amp;|&)seq=(\d+)[^"]*?"[^>]*>\s*(\w+ \d{1,2}, \d{4})\s*</a>',
        re.IGNORECASE,
    )

    # For each link, find the meeting type in the next <td>
    for link_match in link_pattern.finditer(html):
        seq = link_match.group(1)
        date_text = link_match.group(2)

        # Look for the meeting type in the <td> following this link
        after_link = html[link_match.end():link_match.end() + 500]
        type_match = re.search(
            r'<td[^>]*>\s*([A-Za-z][A-Za-z &\-]+(?:Meeting|Board|Session|Commission|District)[^<]*)',
            after_link,
            re.IGNORECASE,
        )
        meeting_type = type_match.group(1).strip() if type_match else "Unknown"

        try:
            date = datetime.strptime(date_text, "%B %d, %Y")
        except ValueError:
            continue

        type_lower = meeting_type.lower()
        is_council = any(t in type_lower for t in COUNCIL_MEETING_TYPES)

        meetings.append({
            "seq": seq,
            "date": date,
            "date_str": date_text,
            "type": meeting_type,
            "is_council": is_council,
        })

    return meetings


def get_agenda_content(seq: str) -> str:
    """Fetch and extract the text content of a specific agenda."""
    url = f"{DESTINY_BASE}?id={DESTINY_ID}&mt=ALL&vl=true&dsp=ag&seq={seq}"
    html = fetch_html(url)

    # Strip HTML tags but preserve some structure
    # Replace headers and breaks with newlines
    text = html

    # Remove script and style blocks
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Preserve structure with newlines
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(p|div|tr|li|h[1-6])>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<(p|div|tr|li|h[1-6])[^>]*>', '\n', text, flags=re.IGNORECASE)

    # Remove remaining tags
    text = re.sub(r'<[^>]+>', ' ', text)

    # Decode HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")

    # Clean up whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()

    return text


def analyze_with_claude(meeting_date: datetime, meeting_type: str, agenda_text: str) -> str | None:
    """Send agenda to Claude for editorial analysis."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  WARNING: ANTHROPIC_API_KEY not set, skipping LLM analysis")
        return None

    date_str = meeting_date.strftime("%A, %B %d, %Y")

    # Truncate if very long
    if len(agenda_text) > 15000:
        agenda_text = agenda_text[:15000] + "\n\n[TRUNCATED]"

    prompt = f"""You are a local government reporter covering the Town of Marana, Arizona for the Tucson Daily Brief. Analyze the following Marana Town Council meeting agenda for {date_str}.

Your job: identify the 3-6 most newsworthy items and explain WHY they matter to Marana and greater Tucson-area residents. Think like a beat reporter — what would your editor want you to cover? What affects people's lives, money, safety, or rights?

Marana context: Marana is a fast-growing town northwest of Tucson in Pima County. Key ongoing stories include:
- Data center rezoning controversy (lawsuits filed over rejected referendum petitions)
- Proposed ICE immigration detention facility at former state prison
- Rapid residential and commercial development along I-10 corridor
- Water infrastructure for new growth areas
- Relationship with Tucson metro on regional transportation (RTA)

Prioritize:
1. Policy changes that affect residents (ordinances, zoning, regulations)
2. Large spending decisions or contracts
3. Public hearings where community input is sought
4. Development and land use decisions
5. Items that connect to ongoing regional stories

De-prioritize:
- Proclamations and ceremonial items
- Routine meeting minutes approval
- Small contract renewals

For each item you highlight, write:
- A clear, specific headline (not the bureaucratic title)
- 2-3 sentences explaining what it is and why it matters
- Note if it's on the consent agenda

Format as markdown. Start with a brief 2-sentence overview of the meeting, then list your picks.

AGENDA TEXT:

{agenda_text}"""

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
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            content = result.get("content", [])
            if content and content[0].get("type") == "text":
                return content[0]["text"]
            return None
    except Exception as e:
        print(f"  WARNING: Claude API call failed: {e}")
        return None


def generate_preview(meeting_date: datetime, meeting_type: str, analysis: str) -> str:
    """Generate the publishable preview."""
    date_str = meeting_date.strftime("%B %d, %Y")
    day_of_week = meeting_date.strftime("%A")

    lines = []
    lines.append(f"# Marana Town Council — What to Watch")
    lines.append(f"## {day_of_week}, {date_str}")
    lines.append(f"\n{meeting_type}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(analysis)
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by Tucson Daily Brief agenda mining pipeline using {CLAUDE_MODEL}.*")
    lines.append(f"*AI-assisted journalism — reviewed by a human editor before publication.*")
    lines.append(f"*Source: [Town of Marana Agendas](https://destinyhosted.com/agenda_publish.cfm?id={DESTINY_ID})*")

    return "\n".join(lines)


def generate_full_report(meeting_date: datetime, meeting_type: str, agenda_text: str) -> str:
    """Generate the full agenda reference."""
    date_str = meeting_date.strftime("%B %d, %Y")
    day_of_week = meeting_date.strftime("%A")

    lines = []
    lines.append(f"# Marana Town Council — Full Agenda Reference")
    lines.append(f"## {day_of_week}, {date_str}")
    lines.append(f"\n{meeting_type}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(agenda_text)
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by Tucson Daily Brief agenda mining pipeline*")
    lines.append(f"*Source: [Town of Marana Agendas](https://destinyhosted.com/agenda_publish.cfm?id={DESTINY_ID})*")

    return "\n".join(lines)


def publish_preview(preview_path: str) -> None:
    """Convert a preview markdown file to HTML and publish to the site."""
    # Import the publishing functions from the Pima County script
    from agenda_mining import preview_md_to_html, render_meeting_post, escape_html

    md_text = Path(preview_path).read_text()

    match = re.search(r"(\d{4}-\d{2}-\d{2})", Path(preview_path).stem)
    if not match:
        print(f"  ERROR: Could not extract date from {preview_path}")
        return
    date = datetime.strptime(match.group(1), "%Y-%m-%d")
    slug = f"marana-council-{date.strftime('%Y-%m-%d')}"

    title = "Marana Town Council — What to Watch"
    for line in md_text.split("\n"):
        if line.startswith("## "):
            title = line[3:].strip()
            break

    PUBLISHED_DIR.mkdir(exist_ok=True)
    body_html = preview_md_to_html(md_text)
    html_path = PUBLISHED_DIR / f"{slug}.html"
    html_path.write_text(render_meeting_post(title, date, body_html))
    print(f"  Published: {html_path}")

    # Rebuild meeting watch index (import and call from pima county script)
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
            lede = lede.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
            if len(lede) > 120:
                lede = lede[:117] + "..."
        posts.append({"date": dt, "slug": f.stem, "title": post_title, "lede": lede})

    posts.sort(key=lambda p: p["date"], reverse=True)
    index_path = SITE_DIR / "meeting-watch.html"
    index_path.write_text(render_meeting_index(posts))
    print(f"  Updated index: {index_path} ({len(posts)} preview(s))")


def main():
    parser = argparse.ArgumentParser(description="Marana Town Council agenda mining pipeline")
    parser.add_argument("--seq", type=str, help="Analyze a specific Destiny agenda sequence number")
    parser.add_argument("--month", type=int, default=None, help="Month to check (default: current)")
    parser.add_argument("--year", type=int, default=None, help="Year to check (default: current)")
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

    now = datetime.now()
    year = args.year or now.year
    month = args.month or now.month

    if args.seq:
        # Analyze a specific meeting
        print(f"Fetching agenda seq={args.seq}...")
        agenda_text = get_agenda_content(args.seq)
        if not agenda_text:
            print("  No content found.")
            return

        # Try to extract date from the agenda text
        date_match = re.search(r'(\w+ \d{1,2}, \d{4})', agenda_text[:500])
        if date_match:
            try:
                meeting_date = datetime.strptime(date_match.group(1), "%B %d, %Y")
            except ValueError:
                meeting_date = now
        else:
            meeting_date = now

        meeting_type = "Council Meeting"
        date_slug = meeting_date.strftime("%Y-%m-%d")
        base = f"marana-{date_slug}"

        # Save full reference
        full_report = generate_full_report(meeting_date, meeting_type, agenda_text)
        full_path = os.path.join(OUTPUT_DIR, f"{base}-full.md")
        with open(full_path, "w") as f:
            f.write(full_report)
        print(f"  Saved full reference: {full_path}")

        # LLM analysis
        if not args.no_llm:
            print("  Running editorial analysis with Claude...")
            analysis = analyze_with_claude(meeting_date, meeting_type, agenda_text)
            if analysis:
                print("  Editorial analysis complete")
                preview = generate_preview(meeting_date, meeting_type, analysis)
                preview_path = os.path.join(OUTPUT_DIR, f"{base}-preview.md")
                with open(preview_path, "w") as f:
                    f.write(preview)
                print(f"  Saved publishable preview: {preview_path}")
        return

    # Scan for meetings in the given month
    print(f"Checking for Marana meetings in {month}/{year}...")
    meetings = get_meetings_for_month(year, month)

    if not meetings:
        print("  No meetings found.")
        return

    # Filter to council meetings unless --all-types
    if not args.all_types:
        council_meetings = [m for m in meetings if m["is_council"]]
    else:
        council_meetings = meetings

    if args.list:
        for m in meetings:
            marker = " *" if m["is_council"] else ""
            print(f"  {m['date_str']} — {m['type']} — seq={m['seq']}{marker}")
        print(f"\nFound {len(meetings)} meeting(s), {len([m for m in meetings if m['is_council']])} council meeting(s).")
        print("(* = council meeting)")
        return

    if not council_meetings:
        print("  No council meetings found this month. Use --all-types to see all meetings.")
        return

    for m in council_meetings:
        date_slug = m["date"].strftime("%Y-%m-%d")
        base = f"marana-{date_slug}"

        # Check if preview already exists
        preview_path = os.path.join(OUTPUT_DIR, f"{base}-preview.md")
        if os.path.exists(preview_path):
            print(f"  Preview already exists for {m['date_str']}, skipping.")
            continue

        print(f"\nProcessing: {m['date_str']} — {m['type']} (seq={m['seq']})")

        agenda_text = get_agenda_content(m["seq"])
        if not agenda_text:
            print("  No agenda content found.")
            continue

        # Save full reference
        full_report = generate_full_report(m["date"], m["type"], agenda_text)
        full_path = os.path.join(OUTPUT_DIR, f"{base}-full.md")
        with open(full_path, "w") as f:
            f.write(full_report)
        print(f"  Saved full reference: {full_path}")

        # LLM analysis
        if not args.no_llm:
            print("  Running editorial analysis with Claude...")
            analysis = analyze_with_claude(m["date"], m["type"], agenda_text)
            if analysis:
                print("  Editorial analysis complete")
                preview = generate_preview(m["date"], m["type"], analysis)
                preview_path = os.path.join(OUTPUT_DIR, f"{base}-preview.md")
                with open(preview_path, "w") as f:
                    f.write(preview)
                print(f"  Saved publishable preview: {preview_path}")


if __name__ == "__main__":
    main()
