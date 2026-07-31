#!/usr/bin/env python3
"""
agenda_mining_schools.py — BoardBook adapter for Pima County school districts.

Fifth agenda miner, same shape as the four municipal ones (see
MEETING-WATCH-PIPELINE.md): scrape upcoming meetings → pull the agenda →
one Claude call for a "What to Watch" preview → publish + full reference.

WHY BOARDBOOK FIRST (revised from SCHOOL-DATA-FEASIBILITY.md's Vail-first plan):
BoardBook is the lowest-lift adapter of the two platforms (server-rendered HTML,
no SPA), and two of its four districts — Marana USD and Amphitheater — sit inside
TDB's existing municipal footprint (Amphitheater *is* the Oro Valley school
district). Same readers, no new geography, and it feeds the Marana/OV geographic
video editions. Diligent (TUSD, Vail, Sahuarita, Tanque Verde) comes second.

PLATFORM NOTES (verified live 2026-07-30):
  org page : https://meetings.boardbook.org/Public/Organization/{org_id}
  agenda   : https://meetings.boardbook.org/Public/Agenda/{slug}?meeting={id}
  The slug is NOT derivable from the org id — Marana is 'marana', Catalina
  Foothills 'catalina', Flowing Wells 'flowingwells', but Amphitheater's slug is
  literally its org id '2065'. Hardcode per district; verify before adding one.
  Meeting rows are <tr> blocks carrying "{Month} {D}, {YYYY} at {time} - {title}
  Meeting Type: {type}".

MEETING-TYPE FILTER — editorial, deliberate:
  BoardBook lists more than board meetings. Marana's July entries are all
  "Notice of Quorum" (type "Working") — notices that board members will be
  present at an event, where nothing is decided. Publishing "What to Watch" for
  one would promise readers a decision meeting that isn't. Only SKIP_TITLES-free
  meetings of a covered type are previewed; everything else is archived to the
  full reference only. Seasonality is normal: boards recess over summer, so
  July runs are legitimately empty. An empty run is not a failure.

Usage:
    python3 agenda_mining_schools.py --dry-run     # scrape + list, no AI, no writes
    python3 agenda_mining_schools.py               # full run, all districts
    python3 agenda_mining_schools.py --district marana
    python3 agenda_mining_schools.py --days 21     # lookahead window
"""
import argparse
import html
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

SITE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SITE_DIR / "agenda-watch"
PUBLISHED_DIR = SITE_DIR / "meeting-watch"

BASE = "https://meetings.boardbook.org"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120 Safari/537.36")
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_DAYS = 14

# slug verified per district — do not guess, see PLATFORM NOTES
DISTRICTS = {
    "marana": dict(org="1780", slug="marana", name="Marana Unified School District",
                   board="Governing Board", file_prefix="marana-usd"),
    "amphitheater": dict(org="2065", slug="2065", name="Amphitheater Public Schools",
                         board="Governing Board", file_prefix="amphitheater-usd"),
    "catalina-foothills": dict(org="1202", slug="catalina",
                               name="Catalina Foothills School District",
                               board="Governing Board", file_prefix="catalina-foothills-usd"),
    "flowing-wells": dict(org="1607", slug="flowingwells", name="Flowing Wells Schools",
                          board="Governing Board", file_prefix="flowing-wells-usd"),
}

# Types worth a preview. "Working" is BoardBook's catch-all for quorum notices.
# Longest-first so "work session" wins over a bare "work" prefix.
PREVIEW_TYPES = ("work session", "study session", "regular", "special", "study",
                 "budget")
# A BoardBook org hosts more than the governing board — parent groups, site
# councils, boosters, committees. Publishing a "What to Watch" for a
# family-faculty organization as school-board coverage is worse than missing a
# meeting: it's confidently wrong. So filter on title too, and asymmetrically —
# we accept a false negative (a skipped board meeting) over a false positive.
# Every skip is printed, so a miss is visible in the run output rather than
# silent. Add patterns here as new committee names appear.
SKIP_TITLE_RE = re.compile(
    r"notice of quorum|quorum notice|family faculty|faculty organization|"
    r"\bPTO\b|\bPTA\b|booster|site council|parent (advisory|group)|"
    r"foundation board|athletic council|wellness committee",
    re.I)


def normalize_type(raw: str) -> str:
    """BoardBook's row text runs the meeting type straight into the location, so
    a greedy capture yields 'Special Tucson' instead of 'Special'. Matching that
    against PREVIEW_TYPES silently skips a real board meeting — a false negative
    that loses coverage with no error. Resolve by longest known-type prefix."""
    s = " ".join(raw.split()).lower()
    for t in PREVIEW_TYPES:
        if s == t or s.startswith(t + " "):
            return t
    return s.split(" ")[0] if s else ""

ROW_RE = re.compile(r"<tr[^>]*>.*?</tr>", re.S | re.I)
MEET_RE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(\d{1,2}),\s+(20\d\d)\s+at\s+([\d:]+\s*[AP]M)\s*-\s*"
    r"(.+?)\s*Meeting Type:\s*(\w[\w ]*)", re.I)
ID_RE = re.compile(r"/Public/Agenda/[a-z0-9_-]+\?meeting=(\d+)", re.I)


def fetch(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=45)
    r.raise_for_status()
    return r.text


def strip_tags(fragment: str) -> str:
    txt = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S | re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", html.unescape(txt)).strip()


def get_meetings(district: dict, days: int) -> list[dict]:
    """Upcoming meetings for one district, from the public org page."""
    page = fetch(f"{BASE}/Public/Organization/{district['org']}")
    today = datetime.now().date()
    horizon = today + timedelta(days=days)
    out = []
    for row in ROW_RE.findall(page):
        if "Public/Agenda" not in row:
            continue
        mid = ID_RE.search(row)
        m = MEET_RE.search(strip_tags(row))
        if not (mid and m):
            continue
        try:
            when = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}",
                                     "%B %d %Y").date()
        except ValueError:
            continue
        if not (today <= when <= horizon):
            continue
        title = m.group(5).strip()
        mtype = normalize_type(m.group(6))
        out.append(dict(
            date=when, meeting_id=mid.group(1), time=m.group(4).strip(),
            title=title, mtype=mtype,
            previewable=(mtype in PREVIEW_TYPES
                         and not SKIP_TITLE_RE.search(title)),
            url=f"{BASE}/Public/Agenda/{district['slug']}?meeting={mid.group(1)}",
        ))
    out.sort(key=lambda x: (x["date"], x["meeting_id"]))
    return out


def get_agenda_text(meeting: dict) -> str:
    """Agenda body as text. BoardBook renders server-side, so no headless needed."""
    page = fetch(meeting["url"])
    m = re.search(r"<main\b.*?</main>", page, re.S | re.I)
    body = m.group(0) if m else page
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", body, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>|</p>|</h[1-6]>|</li>|</tr>|</div>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    # drop BoardBook chrome that precedes the agenda proper
    for marker in ("Agenda Help", "View Options:", "Hide Everything"):
        idx = text.find(marker)
        if idx != -1 and idx < len(text) // 2:
            text = text[idx + len(marker):]
    return text.strip()


def analyze_with_claude(district: dict, meeting: dict, agenda_text: str) -> str | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return None
    import json
    import urllib.request

    prompt = f"""You are a local news editor writing a short "What to Watch" preview of an upcoming school district governing board meeting for readers in Tucson, Arizona.

District: {district['name']}
Board: {district['board']}
Meeting: {meeting['title']} ({meeting['mtype']})
Date: {meeting['date'].strftime('%A, %B %d, %Y')} at {meeting['time']}

Write 3-6 short bullet points covering only what a parent or taxpayer would actually want to know: money being spent, policy changes, personnel actions at the leadership level, boundary/calendar/program changes, contracts, and anything likely to draw public comment.

Rules:
- Ground every point in the agenda text below. Do not speculate about outcomes or motives.
- Skip pure routine (approving minutes, consent items with no substance, recurring reports) unless the dollar figure or subject is notable.
- Name dollar amounts and vendor/program names exactly as the agenda gives them.
- NEVER name or describe an individual student, and skip any item involving student discipline, records, or identifiable student information (FERPA).
- If the agenda is thin or purely procedural, say so plainly in one line rather than padding.
- Plain prose. No headline, no preamble, no sign-off.

AGENDA TEXT:

{agenda_text[:60000]}"""

    body = json.dumps({"model": CLAUDE_MODEL, "max_tokens": 1200,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        CLAUDE_API_URL, data=body, method="POST",
        headers={"Content-Type": "application/json", "x-api-key": api_key,
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        content = data.get("content", [])
        return content[0]["text"].strip() if content else None
    except Exception as e:
        print(f"  WARNING: Claude call failed: {e}", file=sys.stderr)
        return None


def generate_preview(district: dict, meeting: dict, analysis: str) -> str:
    d = meeting["date"]
    return "\n".join([
        f"# {district['name']} {district['board']} — What to Watch",
        f"## {d.strftime('%A')}, {d.strftime('%B %d, %Y')}",
        "", f"{meeting['title']} ({meeting['mtype']}) — {meeting['time']}",
        "", "---", "", analysis, "", "---",
        f"*Generated {datetime.now():%Y-%m-%d %H:%M} by Tucson Daily Brief agenda "
        f"mining pipeline using {CLAUDE_MODEL}.*",
        "*AI-assisted journalism — reviewed by a human editor before publication.*",
        f"*Source: [{district['name']} BoardBook]({meeting['url']})*",
    ])


def generate_full_report(district: dict, meeting: dict, agenda_text: str) -> str:
    d = meeting["date"]
    return "\n".join([
        f"# {district['name']} {district['board']} — Full Agenda Reference",
        f"## {d.strftime('%A')}, {d.strftime('%B %d, %Y')}",
        "", f"{meeting['title']} ({meeting['mtype']}) — {meeting['time']}",
        "", "---", "", agenda_text, "", "---",
        f"*Generated {datetime.now():%Y-%m-%d %H:%M} by Tucson Daily Brief agenda "
        f"mining pipeline*",
        f"*Source: [{district['name']} BoardBook]({meeting['url']})*",
    ])


def publish_preview(preview_path: Path, district: dict) -> None:
    from agenda_mining import preview_md_to_html, render_meeting_post

    md_text = preview_path.read_text()
    m = re.search(r"(\d{4}-\d{2}-\d{2})", preview_path.stem)
    if not m:
        print(f"  ERROR: no date in {preview_path}")
        return
    date = datetime.strptime(m.group(1), "%Y-%m-%d")
    slug = f"{district['file_prefix']}-{date:%Y-%m-%d}"

    title = f"{district['name']} {district['board']} — What to Watch"
    for line in md_text.split("\n"):
        if line.startswith("## "):
            title = line[3:].strip()
            break

    PUBLISHED_DIR.mkdir(exist_ok=True)
    html_path = PUBLISHED_DIR / f"{slug}.html"
    html_path.write_text(render_meeting_post(title, date, preview_md_to_html(md_text),
                                             page_slug=html_path.stem))
    print(f"  Published: {html_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="scrape + list only")
    ap.add_argument("--district", choices=sorted(DISTRICTS), help="just one")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS)
    a = ap.parse_args()

    keys = [a.district] if a.district else sorted(DISTRICTS)
    OUTPUT_DIR.mkdir(exist_ok=True)
    published = 0

    for key in keys:
        district = DISTRICTS[key]
        print(f"\n=== {district['name']} (org {district['org']}) ===")
        try:
            meetings = get_meetings(district, a.days)
        except Exception as e:
            print(f"  ERROR fetching org page: {e}", file=sys.stderr)
            continue
        if not meetings:
            print(f"  No meetings in the next {a.days} days "
                  "(normal — boards recess over summer)")
            continue

        for mt in meetings:
            tag = "PREVIEW" if mt["previewable"] else "skip   "
            print(f"  [{tag}] {mt['date']} {mt['time']:>8s} [{mt['mtype']}] "
                  f"{mt['title'][:52]}")
            if a.dry_run or not mt["previewable"]:
                continue

            base = f"{district['file_prefix']}-{mt['date']:%Y-%m-%d}"
            preview_path = OUTPUT_DIR / f"{base}-preview.md"
            full_path = OUTPUT_DIR / f"{base}-full.md"
            if preview_path.exists():
                print("     already processed")
                continue

            try:
                agenda_text = get_agenda_text(mt)
            except Exception as e:
                print(f"     ERROR fetching agenda: {e}", file=sys.stderr)
                continue
            if len(agenda_text) < 400:
                print(f"     agenda too short ({len(agenda_text)}b) — skipping")
                continue

            full_path.write_text(generate_full_report(district, mt, agenda_text))
            analysis = analyze_with_claude(district, mt, agenda_text)
            if not analysis:
                continue
            preview_path.write_text(generate_preview(district, mt, analysis))
            print(f"     Wrote {preview_path.name}")
            publish_preview(preview_path, district)
            published += 1

    print(f"\n{published} preview(s) published")


if __name__ == "__main__":
    main()
