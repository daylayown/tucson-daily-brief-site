#!/usr/bin/env python3
"""
Sahuarita Unified School District governing-board agenda miner.

TDB's first school district (2026-08-04). Produces "What to Watch" previews the
same way the four municipal miners do, and — unlike them — schedules the live
AI reporter from the board's own published calendar rather than from the agenda.

WHY SAHUARITA IS THE PILOT
Of the nine metro districts it is the only one that clears every bar at once
(see SCHOOL-DATA-FEASIBILITY.md § E for the full scan):
  * posts EVERY board meeting to YouTube, next-day, with regular titles
  * publishes a machine-readable agenda (Diligent) months of dates ahead
  * meets twice monthly and does not go dark in summer (it met July 8)
It replaces the doc's original "Pilot = Vail USD" recommendation, which was
wrong: Vail's main channel carries no board meetings and its "Vail Streaming"
channel lists none.

TWO SOURCES, ON PURPOSE
  1. SCHEDULE — the district's annual board calendar at
     susd30.us/governing-board/. Lists every 2026 meeting date with location,
     plus the standing "Meetings begin at 6 p.m." This is where the live
     reporter's start time comes from.
  2. AGENDA — the Diligent portal. Agendas appear only ~24-48h ahead (ARS
     §38-431.02 notice, and the portal says so in as many words: "subject to
     change, up to 24 hours prior").

Splitting them is the whole trick. The municipal miners can only schedule a
recording once an agenda exists, which leaves a day or two of lead time. Here
the capture for a meeting five weeks out can be scheduled today, and the
preview fills in when the agenda lands. It is also strictly more accurate:
`schedule_recording.py --start` takes the published 6 p.m. verbatim instead of
asking a model to find a time in a PDF, per feedback_verify_dont_delegate.

TWO PARSING TRAPS, BOTH LIVE
  * The calendar page carries TWO tables. The second is board members' school
    visit schedule — rows marked `┼┼` with times like "11:00 a.m. – 11:30 a.m."
    Those are not board meetings and must never be captured. `parse_calendar()`
    requires the row to be in the meetings table and rejects any row carrying
    its own time range.
  * Agenda documents are served from URLs ending `.docx`, but the response is
    rendered HTML, not a Word file. Do not reach for python-docx or pdftotext;
    read the HTML.

FERPA
Board agendas name students (awards, discipline appeals, scholarship lists).
Previews must never carry a student's name. The prompt says so, and it is the
one instruction here that is not about news judgment.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta
from html import unescape
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SITE_DIR / "agenda-watch"
PUBLISHED_DIR = SITE_DIR / "meeting-watch"

CALENDAR_URL = "https://susd30.us/governing-board/"
PORTAL_BASE = "https://susd-30.community.diligentoneplatform.com"
PORTAL_MEETINGS = f"{PORTAL_BASE}/Portal/MeetingTypeList.aspx"
# The district's own livestream shortlink, printed on every agenda and in the
# portal. Kept here as documentation; the capture URL lives in
# schedule_recording.py STREAM_SOURCES["sahuarita"].
LIVESTREAM_SHORTLINK = "http://bit.ly/SUSD30youtube"

CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

BODY_NAME = "Sahuarita Unified Governing Board"
MUNICIPALITY = "sahuarita"          # schedule_recording.py STREAM_SOURCES key
SLUG_PREFIX = "sahuarita"           # municipality_from_basename() matches this
DEFAULT_START_LOCAL = "18:00:00"    # "Meetings begin at 6 p.m." — published
AZ_OFFSET = "-07:00"                # Arizona: no DST, ever

HTTP_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 40

_MONTHS = ("January February March April May June July August September "
           "October November December").split()
_DATE_RE = (r"(?:" + "|".join(_MONTHS) + r")\s+\d{1,2},\s+20\d\d")
# A time RANGE marks a school-visit row, never a board meeting.
_TIME_RANGE_RE = re.compile(r"\d{1,2}:\d{2}\s*[ap]\.?m\.?\s*(?:–|-|&ndash;|to)\s*\d{1,2}:\d{2}", re.I)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HTTP_HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _text_lines(html: str) -> list[str]:
    """HTML -> visible lines, scripts and styles removed."""
    html = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<[^>]+>", "\n", html)
    out = []
    for raw in html.split("\n"):
        line = unescape(raw).replace("\xa0", " ")
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            out.append(line)
    return out


# ---------------------------------------------------------------------------
# 1. The schedule (annual calendar)
# ---------------------------------------------------------------------------

def parse_calendar(html: str | None = None) -> list[dict]:
    """Board meeting dates from the district's published annual calendar.

    Returns [{date: datetime, location: str}] in date order.

    Rejects the school-visit table. Those rows sit after the board-meeting rows
    and each carries its own time range ("11:00 a.m. – 11:45 a.m."), so a row
    with a time range is excluded no matter where it appears. The board rows
    carry no time at all — the time is prose elsewhere on the page ("Meetings
    begin at 6 p.m."), which is why DEFAULT_START_LOCAL is a constant and not
    scraped per row.
    """
    html = html if html is not None else fetch(CALENDAR_URL)
    lines = _text_lines(html)
    date_only = re.compile(r"^[^A-Za-z0-9]*(" + _DATE_RE + r")\s*(.*)$")

    meetings, seen = [], set()
    for i, line in enumerate(lines):
        m = date_only.match(line)
        if not m:
            continue
        trailing = m.group(2)
        # Look-ahead window is where a school visit prints its time range.
        window = " ".join(lines[i:i + 3])
        if _TIME_RANGE_RE.search(window) or "┼" in line or "┼" in trailing:
            continue
        try:
            when = datetime.strptime(m.group(1), "%B %d, %Y")
        except ValueError:
            continue
        if when.isoformat() in seen:
            continue
        # Board meetings are Wednesdays (published policy: "second and fourth
        # Wednesdays"). A non-Wednesday date in this table is either a special
        # meeting the calendar rarely lists or a stray parse — skip it rather
        # than schedule a capture against a guess.
        if when.weekday() != 2:
            continue
        seen.add(when.isoformat())
        location = lines[i + 1] if i + 1 < len(lines) else ""
        if date_only.match(location) or _TIME_RANGE_RE.search(location):
            location = ""
        meetings.append({"date": when, "location": location[:160]})
    meetings.sort(key=lambda x: x["date"])
    return meetings


def upcoming_meetings(days_ahead: int = 60, today: datetime | None = None) -> list[dict]:
    today = today or datetime.now()
    horizon = today + timedelta(days=days_ahead)
    return [m for m in parse_calendar()
            if today.date() <= m["date"].date() <= horizon.date()]


# ---------------------------------------------------------------------------
# 2. The agenda (Diligent portal)
# ---------------------------------------------------------------------------

def _normalise_doc_url(href: str) -> str:
    url = href if href.startswith("http") else PORTAL_BASE + "/" + href.lstrip("/")
    # Their own markup emits "http://https://…" in places; also force https so
    # the document fetch is not a plaintext hop.
    url = re.sub(r"^http://(?=https://)", "", url)
    return re.sub(r"^http://", "https://", url)


def agenda_header_date(agenda_html: str) -> datetime | None:
    """The meeting date as the AGENDA ITSELF states it.

    Every Sahuarita agenda opens with "Wednesday, July 8, 2026 at 6:00 PM".
    That header is the only trustworthy key: the document's *filename* is
    truncated by Diligent ("…Agenda, July 8,.docx" — no year) and the link text
    is an empty icon anchor, so neither can be matched on.
    """
    for line in _text_lines(agenda_html)[:60]:
        m = re.search(r"(" + _DATE_RE + r")\s+at\s+(\d{1,2}:\d{2}\s*[AP]M)", line, re.I)
        if m:
            try:
                return datetime.strptime(m.group(1), "%B %d, %Y")
            except ValueError:
                continue
    return None


def find_agenda_url(meeting_date: datetime, portal_html: str | None = None) -> str | None:
    """Locate the agenda document for a given meeting date.

    Walks MeetingTypeList -> each MeetingInformation.aspx?Id=N -> its single
    document link, then reads each document's own header date and keeps the one
    that matches. A handful of fetches (the portal lists only currently-active
    meetings, ~6), which is why brute-force is fine here.

    A "Revised" agenda supersedes the plain one for the same date — the portal
    says agendas change up to 24 hours out — so a revision wins on a tie.
    """
    html = portal_html if portal_html is not None else fetch(PORTAL_MEETINGS)
    ids = sorted({int(x) for x in re.findall(r"MeetingInformation\.aspx\?Id=(\d+)", html)},
                 reverse=True)   # newest first: the upcoming meeting is the high id
    if not ids:
        print("  WARNING: no MeetingInformation ids on the portal — layout change?")
        return None

    best = None
    for mid in ids:
        try:
            page = fetch(f"{PORTAL_BASE}/Portal/MeetingInformation.aspx?Id={mid}")
        except Exception as e:
            print(f"  WARNING: Id={mid} fetch failed: {e}")
            continue
        for href in re.findall(r'href="([^"]*/document/[^"]+)"', page, re.I):
            url = _normalise_doc_url(href)
            if not re.search(r"agenda", url, re.I):
                continue        # File.html attachments etc. are not the agenda
            try:
                doc = fetch(url)
            except Exception as e:
                print(f"  WARNING: document fetch failed ({url[:70]}…): {e}")
                continue
            got = agenda_header_date(doc)
            if got is None or got.date() != meeting_date.date():
                continue
            revised = bool(re.search(r"revis", url, re.I))
            if best is None or (revised and not best[1]):
                best = (url, revised, doc)
            if revised:
                break
        if best and best[1]:
            break
    if best:
        print(f"  Agenda found (revised={best[1]}): {best[0][:88]}…")
        return best[0]
    return None


def get_agenda_text(agenda_url: str) -> str:
    """Agenda text from Diligent.

    The URL ends in `.docx` but Diligent renders it as HTML, so this is an HTML
    parse. Reaching for python-docx or pdftotext here fails on a document that
    was never a binary in the first place.
    """
    lines = _text_lines(fetch(agenda_url))
    # Drop the boilerplate that precedes every agenda's item list; keep it out
    # of the model's context so the picks come from actual business.
    skip = re.compile(r"^(?:Skip Navigation|Jump to SideBar|Quick Menu|Public site|"
                      r"Policy|Sign in|Your Javascript|Home|Calendar|Meetings|Search|Share)$")
    return "\n".join(l for l in lines if not skip.match(l))


def is_canceled(agenda_text: str) -> bool:
    from agenda_mining import is_canceled_meeting
    return is_canceled_meeting("", agenda_text)


# ---------------------------------------------------------------------------
# 3. Analysis
# ---------------------------------------------------------------------------

def analyze_with_claude(meeting_date: datetime, agenda_text: str) -> str | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  WARNING: ANTHROPIC_API_KEY not set, skipping LLM analysis")
        return None
    date_str = meeting_date.strftime("%A, %B %d, %Y")
    if len(agenda_text) > 15000:
        agenda_text = agenda_text[:15000] + "\n\n[TRUNCATED]"

    from agenda_mining import meeting_context_block

    prompt = f"""You are a local education reporter covering the Sahuarita Unified School District (SUSD #30) for the Tucson Daily Brief. Analyze the following Governing Board meeting agenda for {date_str}.

{meeting_context_block("Governing Board Meeting")}

Your job: identify up to the 3-6 most newsworthy items and explain WHY they matter to Sahuarita-area families and Pima County residents. Think like a beat reporter — what affects students, taxpayers, staff, or how the district is run?

Sahuarita context: SUSD #30 serves ~6,400 students in Sahuarita and Green Valley, south of Tucson in Pima County. Recurring stories:
- Enrollment and the statewide ESA voucher shift pulling students from district schools
- Budget, override and bond measures — what the district asks of voters and what it funds
- Teacher and staff pay, vacancies, and retention
- Growth along the I-19 corridor and new-school or boundary decisions
- Facilities, transportation, and school-safety spending
- Academic outcomes: state letter grades, proficiency, graduation rates

Prioritize:
1. Money — budgets, overrides, bonds, big contracts, purchasing over ~$100k
2. Policy changes that affect students and families (calendar, boundaries, discipline, curriculum adoption)
3. Personnel decisions at the leadership level (superintendent, principals, reorganizations)
4. Public hearings and anything where the board is taking community input
5. Facilities and construction

De-prioritize:
- Routine minutes approval, ceremonial recognitions, field-trip approvals
- Individual personnel actions for non-leadership staff
- Consent-agenda housekeeping — unless a consent item is unusually large or contentious

ABSOLUTE RULE — FERPA: never name, or make identifiable, an individual student. Agendas do name students (award recipients, scholarship lists, appeals). Write "a student" or describe the category. This overrides newsworthiness.

Also: an item's presence on an agenda means it is PROPOSED, not decided. Write "the board will consider," never "the board approved."

For each item you highlight, write:
- A clear, specific headline (not the bureaucratic agenda title)
- 2-3 sentences explaining what it is and why it matters
- Note if it's on the consent agenda

Format as markdown. Start with a 2-sentence overview: the first sentence must lead with the single most newsworthy item, named concretely ("a $12M bond request for a new elementary school," not "a significant facilities item"); the second sentence rounds up the rest of the meeting. Then list your picks. NOWHERE in the piece — not the overview, not an item, not a closing line — comment on the meeting's size, thinness, routineness, or on what is absent from the agenda ("a light agenda," "the agenda is thin on major votes," "notably missing is..."). Describe the news, not the meeting. The piece is a published web page: it opens with the overview and ENDS with the last item. There is no closing note, editor's note, coverage plan, logistics paragraph, or sign-off. Never write about the Tucson Daily Brief itself — do not say it will attend, cover, or follow anything.

AGENDA TEXT:

{agenda_text}"""

    body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        CLAUDE_API_URL, data=body,
        headers={"Content-Type": "application/json", "x-api-key": api_key,
                 "anthropic-version": "2023-06-01"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read())
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            return content[0]["text"]
    except Exception as e:
        print(f"  WARNING: Claude API call failed: {e}")
    return None


# ---------------------------------------------------------------------------
# 4. Render + publish
# ---------------------------------------------------------------------------

def generate_preview(meeting_date: datetime, analysis: str, location: str = "",
                     canceled: bool = False) -> str:
    date_str = meeting_date.strftime("%B %d, %Y")
    day = meeting_date.strftime("%A")
    lines = [
        f"# Sahuarita Unified Governing Board — {'Meeting Canceled' if canceled else 'What to Watch'}",
        f"## {day}, {date_str}",
        "",
        "Governing Board Meeting" + (f" — {location}" if location else ""),
        "",
        "---",
        "",
        analysis,
        "",
        "---",
    ]
    # No per-article AI disclosure — see the note in agenda_mining.py.
    if canceled:
        lines.append("*No agenda was posted for this meeting.*")
    lines.append(f"*Source: [Sahuarita Unified Governing Board portal]({PORTAL_MEETINGS})*")
    return "\n".join(lines)


def generate_full_report(meeting_date: datetime, agenda_text: str) -> str:
    date_str = meeting_date.strftime("%B %d, %Y")
    day = meeting_date.strftime("%A")
    return "\n".join([
        "# Sahuarita Unified Governing Board — Full Agenda Reference",
        f"## {day}, {date_str}",
        "",
        "Governing Board Meeting",
        "",
        "---",
        "",
        agenda_text,
        "",
        "---",
        f"*Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by Tucson Daily Brief agenda mining pipeline*",
        f"*Source: [Sahuarita Unified Governing Board portal]({PORTAL_MEETINGS})*",
    ])


def publish_preview(preview_path: Path) -> None:
    """Render the preview to HTML and refresh the What to Watch index.

    Same shape as the municipal miners' publish_preview so the section keeps one
    set of chrome; slug prefix is `sahuarita-board-` to sit alongside
    `orovalley-council-` etc.
    """
    from agenda_mining import preview_md_to_html, render_meeting_post, render_meeting_index
    from generate_post import rebuild_homepage

    md_text = preview_path.read_text()
    m = re.search(r"(\d{4}-\d{2}-\d{2})", preview_path.stem)
    if not m:
        print(f"  ERROR: could not extract date from {preview_path}")
        return
    date = datetime.strptime(m.group(1), "%Y-%m-%d")
    slug = f"sahuarita-board-{date:%Y-%m-%d}"

    title = "Sahuarita Unified Governing Board — What to Watch"
    for line in md_text.split("\n"):
        if line.startswith("## "):
            title = line[3:].strip()
            break

    PUBLISHED_DIR.mkdir(exist_ok=True)
    html_path = PUBLISHED_DIR / f"{slug}.html"
    html_path.write_text(render_meeting_post(title, date, preview_md_to_html(md_text),
                                             page_slug=html_path.stem))
    print(f"  Published: {html_path}")

    posts = []
    for f in PUBLISHED_DIR.glob("*.html"):
        mm = re.search(r"(\d{4}-\d{2}-\d{2})", f.stem)
        if not mm:
            continue
        content = f.read_text()
        tm = re.search(r'<p class="post-meta">(.+?)</p>', content)
        lm = re.search(r'</p>\s*<(?:p|h[12])>(.+?)</(?:p|h[12])>', content)
        lede = ""
        if lm:
            lede = re.sub(r"<[^>]+>", "", lm.group(1))
            lede = (lede.replace("&amp;", "&").replace("&lt;", "<")
                        .replace("&gt;", ">").replace("&quot;", '"'))
            if len(lede) > 120:
                lede = lede[:117] + "..."
        posts.append({"date": datetime.strptime(mm.group(1), "%Y-%m-%d"),
                      "slug": f.stem, "title": tm.group(1) if tm else f.stem,
                      "lede": lede})
    posts.sort(key=lambda p: p["date"], reverse=True)
    (SITE_DIR / "meeting-watch.html").write_text(render_meeting_index(posts))
    print(f"  Updated index: meeting-watch.html ({len(posts)} preview(s))")
    rebuild_homepage()


# ---------------------------------------------------------------------------
# 5. Scheduling the live reporter
# ---------------------------------------------------------------------------

def schedule_capture(meeting_date: datetime, dry_run: bool = False) -> None:
    """Hand the live reporter a start time from the published calendar.

    Uses `schedule_recording.py --start`, so no model is asked what time the
    meeting begins — the board publishes it. Safe to call repeatedly: the
    scheduler no-ops when the stored time already matches.
    """
    import subprocess
    slug = f"{SLUG_PREFIX}-{meeting_date:%Y-%m-%d}"
    preview = OUTPUT_DIR / f"{slug}-preview.md"
    start = f"{meeting_date:%Y-%m-%d}T{DEFAULT_START_LOCAL}{AZ_OFFSET}"
    cmd = [sys.executable, str(SITE_DIR / "schedule_recording.py"),
           "--start", start, str(preview), MUNICIPALITY]
    if dry_run:
        cmd.insert(2, "--dry-run")
    print(f"  Scheduling capture: {' '.join(cmd[2:])}")
    subprocess.run(cmd, cwd=str(SITE_DIR))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process(meeting: dict, dry_run: bool = False, no_schedule: bool = False,
            force: bool = False) -> bool:
    """One meeting: agenda -> preview -> publish -> schedule. True if published."""
    date = meeting["date"]
    slug = f"{SLUG_PREFIX}-{date:%Y-%m-%d}"
    preview_path = OUTPUT_DIR / f"{slug}-preview.md"
    full_path = OUTPUT_DIR / f"{slug}-full.md"
    print(f"\n=== {BODY_NAME} — {date:%A, %B %d, %Y} ===")

    # Schedule first and unconditionally. The capture must not depend on the
    # agenda existing: agendas post ~24h ahead, the calendar is months ahead,
    # and a meeting with no agenda yet is still a meeting that will be streamed.
    if not no_schedule:
        schedule_capture(date, dry_run=dry_run)

    if preview_path.exists() and not force:
        print("  Preview already exists — skipping (use --force to regenerate)")
        return False

    agenda_url = find_agenda_url(date)
    if not agenda_url:
        print("  No agenda posted yet — capture is scheduled; preview will be "
              "written on a later run once the agenda appears.")
        return False

    agenda_text = get_agenda_text(agenda_url)
    print(f"  Agenda text: {len(agenda_text):,} chars")

    canceled = is_canceled(agenda_text)
    if canceled:
        from agenda_mining import canceled_analysis_md
        analysis = canceled_analysis_md(BODY_NAME, date)
        print("  Meeting appears CANCELED — writing cancellation notice")
    else:
        analysis = analyze_with_claude(date, agenda_text)
        if not analysis:
            print("  ERROR: no analysis produced — not publishing")
            return False

    if dry_run:
        print("  [DRY-RUN] would write preview + full reference and publish")
        print("  --- preview ---")
        print(generate_preview(date, analysis, meeting.get("location", ""), canceled)[:1500])
        return False

    OUTPUT_DIR.mkdir(exist_ok=True)
    preview_path.write_text(generate_preview(date, analysis,
                                             meeting.get("location", ""), canceled))
    full_path.write_text(generate_full_report(date, agenda_text))
    print(f"  Wrote {preview_path.name} + {full_path.name}")
    publish_preview(preview_path)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--days-ahead", type=int, default=60,
                    help="How far out to look on the board calendar (default 60)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would happen; no files, no at job, no publish")
    ap.add_argument("--no-schedule", action="store_true",
                    help="Skip live-reporter scheduling (preview work only)")
    ap.add_argument("--force", action="store_true",
                    help="Regenerate a preview that already exists")
    ap.add_argument("--calendar", action="store_true",
                    help="Print the parsed board calendar and exit")
    ap.add_argument("--date", help="Process only this meeting date (YYYY-MM-DD)")
    args = ap.parse_args()

    if args.calendar:
        cal = parse_calendar()
        print(f"{len(cal)} board meeting(s) on the published calendar:")
        today = datetime.now().date()
        for m in cal:
            when = "past  " if m["date"].date() < today else "future"
            print(f"  {when} {m['date']:%Y-%m-%d %a}  {DEFAULT_START_LOCAL[:5]}  {m['location'][:70]}")
        return 0

    meetings = upcoming_meetings(days_ahead=args.days_ahead)
    if args.date:
        meetings = [m for m in meetings if f"{m['date']:%Y-%m-%d}" == args.date]
        if not meetings:
            # Allow acting on a date outside the horizon if it is on the calendar.
            meetings = [m for m in parse_calendar()
                        if f"{m['date']:%Y-%m-%d}" == args.date]
        if not meetings:
            print(f"ERROR: {args.date} is not a board meeting on the published calendar",
                  file=sys.stderr)
            return 2

    if not meetings:
        print(f"No board meetings on the calendar in the next {args.days_ahead} days.")
        return 0

    print(f"{len(meetings)} upcoming board meeting(s) within {args.days_ahead} days")
    published = 0
    for m in meetings:
        try:
            if process(m, dry_run=args.dry_run, no_schedule=args.no_schedule,
                       force=args.force):
                published += 1
        except Exception as e:
            print(f"  ERROR processing {m['date']:%Y-%m-%d}: "
                  f"{type(e).__name__}: {e}", file=sys.stderr)
    print(f"\nDone. {published} preview(s) published.")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
