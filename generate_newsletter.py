#!/usr/bin/env python3
"""TDB Weekly — Newsletter Draft Generator

Scans the past 7 days of TDB content (daily briefs, news reports, public
record filings, and upcoming meeting watch previews) and asks Claude Sonnet
to draft a warm weekly newsletter ("TDB Weekly") in the voice spec'd in
CLAUDE.md.

Output is a markdown draft at newsletter/drafts/tdb-weekly-YYYY-MM-DD.md.
Human review is required before sending via Buttondown.

Usage:
    python3 generate_newsletter.py
    python3 generate_newsletter.py --send-date 2026-05-10
    python3 generate_newsletter.py --force
    python3 generate_newsletter.py --dry-run     # print prompt, skip API call

Requires:
    ANTHROPIC_API_KEY environment variable.
"""

import argparse
import html
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent
POSTS_DIR = SITE_DIR / "posts"
NEWS_REPORTS_DIR = SITE_DIR / "news-reports"
PUBLIC_RECORD_DIR = SITE_DIR / "public-record"
MEETING_WATCH_DIR = SITE_DIR / "meeting-watch"
CROSSWORD_PUZZLES_DIR = SITE_DIR / "crossword" / "puzzles"
NEWSLETTER_DRAFTS_DIR = SITE_DIR / "newsletter" / "drafts"

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-6"

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def parse_date_from_name(name: str) -> date | None:
    m = DATE_RE.search(name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None


def html_to_text(s: str) -> str:
    """Strip HTML chrome and tags, collapse whitespace.

    Drops <head>, <script>, <style>, and the site's <header>/<footer> blocks
    so the model doesn't see GA boilerplate or the footer CTA every time.
    """
    for block in ("head", "script", "style", "header", "footer", "nav"):
        s = re.sub(rf"<{block}\b[^>]*>.*?</{block}>", "", s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def collect_daily_briefs(start: date, end: date) -> list[tuple[date, str]]:
    out = []
    for f in sorted(POSTS_DIR.glob("*.html")):
        d = parse_date_from_name(f.name)
        if not d or d < start or d > end:
            continue
        out.append((d, html_to_text(f.read_text())))
    return out


def collect_news_reports(start: date, end: date) -> list[tuple[date, str, str]]:
    out = []
    for f in sorted(NEWS_REPORTS_DIR.glob("*.html")):
        d = parse_date_from_name(f.name)
        if not d or d < start or d > end:
            continue
        out.append((d, f.stem, html_to_text(f.read_text())))
    return out


def collect_public_record(start: date, end: date) -> list[tuple[date, str, str]]:
    """Public record filings published (file mtime) within the window.

    The filename embeds the agenda date, not the publish date, so we use
    mtime — close enough for "what was newly surfaced this week."
    """
    out = []
    for f in sorted(PUBLIC_RECORD_DIR.glob("*.html")):
        publish_date = date.fromtimestamp(f.stat().st_mtime)
        if publish_date < start or publish_date > end:
            continue
        out.append((publish_date, f.stem, html_to_text(f.read_text())))
    return out


def collect_upcoming_meetings(reference: date, lookahead_days: int = 14) -> list[tuple[date, str, str]]:
    horizon = reference + timedelta(days=lookahead_days)
    out = []
    for f in sorted(MEETING_WATCH_DIR.glob("*.html")):
        meeting_date = parse_date_from_name(f.name)
        if not meeting_date or meeting_date < reference or meeting_date > horizon:
            continue
        out.append((meeting_date, f.stem, html_to_text(f.read_text())))
    return out


def get_crossword_link(send_date: date) -> str | None:
    """Pick the puzzle for send_date, or the earliest puzzle dated after."""
    candidates = []
    for f in sorted(CROSSWORD_PUZZLES_DIR.glob("*.json")):
        d = parse_date_from_name(f.name)
        if not d:
            continue
        if d == send_date:
            return f"https://tucsondailybrief.com/crossword/play.html?p={f.stem}"
        if d > send_date:
            candidates.append((d, f.stem))
    if candidates:
        candidates.sort()
        return f"https://tucsondailybrief.com/crossword/play.html?p={candidates[0][1]}"
    return None


PROMPT_TEMPLATE = """You are drafting "TDB Weekly," a Sunday newsletter from the Tucson Daily Brief.

EDITORIAL VOICE
- Warm, friendly, lightly conversational — like a Tucson neighbor writing to you on a Sunday morning.
- NOT civic-tech or insider. The reader does not see the AI pipelines, the agenda mining, the public-records work. They just want to feel caught up on the week.
- Different voice from the daily brief. The daily is fast and headline-y; the weekly is slower, more opinionated, more story-shaped.

NEVER use any of this backstage / civic-tech phrasing — it breaks the voice:
- "public records," "agenda mining," "local intelligence," "monitoring the situation"
- "our review," "our pipeline," "flagged by," "surfaced from," "came through our review"
- "according to filings," "per the data," "based on the agenda materials"
Write as if you're a person who reads the news closely, not a system that processes it.

LENGTH
- 800-1200 words total, in markdown.

FORMAT — DO NOT include an H1 title. The newsletter's title will live in the email subject line. Start directly with the warm opening paragraph.

Use these section headings as H2 (`## `), in this order:
1. (no heading) — a 2-4 sentence warm opening. Set the week's mood; reference Tucson weather/season if it fits naturally.
2. ## What's worth knowing — the 3-4 most important Tucson-area stories of the week. Short narrative paragraphs, NOT a bulleted list. Pick what mattered, not what was loudest.
3. ## What changed around town — local government decisions, neighborhood changes, development items. 2-3 paragraphs.
4. ## What's opening — businesses in the local food/drink/retail/fitness scene worth knowing about. Pull from any source in the supplied content (daily briefs, news reports, filings).
   CRITICAL: a business "opening this week" or being "newly opened" REQUIRES the source content to contain an explicit recent date ("opened April 24," "grand opening Saturday," "launched last month"). A place getting news COVERAGE this week — a profile piece, a review, a feature — does NOT mean it opened this week. Many places get their first press long after they open. Default to attribution-based hedging that's faithful to what actually happened:
   - PREFERRED: "Bloom Tea Wellness was profiled in Inside Tucson Business this week" — name the outlet, describe the kind of coverage.
   - ALSO FINE: "got a writeup," "is in the news this week," "is worth a visit," "is one to know about."
   - RESERVED for explicit-date items: "newly opened," "just opened," "opened [date]."
   When you have the outlet name in the source content, prefer the attribution-style hedge — it's more honest and more useful to the reader.
   The liquor-license filings are ONE input among several — if the week has filings, weave them in with hedged language ("applied for," "planned"); if it doesn't, do not call attention to their absence. Lead with whatever's most interesting, not with how it was sourced. 2-3 short paragraphs.
5. ## One thing to watch — a specific upcoming meeting or event in the next ~2 weeks. ~1 paragraph. Specific time/place if known.
6. ## The Tucson Mini — a single short paragraph teasing this week's mini crossword with a clean link.
7. (no heading) — brief closing, ~2 sentences. End on a warm beat.

If a section has no real material from the supplied content, write a SHORT honest paragraph and move on. Do not pad. Do not invent.

HARD RULES
- DO NOT FABRICATE FACTS. Every name, date, dollar amount, address, vote count, business detail must come from the supplied content. If you can't verify something, write more generally rather than inventing.
- For liquor-license filings, use hedged language: "applied for," "planned," "proposed," "listed." Do not assert that a place is open.
- NO outbound links to source articles in the body. The newsletter is its own product, not a link round-up.
- NO emoji.
- NO H1 title at the top of the document.
- The Tucson Mini section MUST embed this exact link: {crossword_link}
  Use natural anchor text ("this week's mini," "play it here," etc.). Do not paste the raw URL as the link text.

CONTENT FROM THE PAST WEEK (and upcoming meetings):

{content_block}

Now write the newsletter draft. Output ONLY the markdown — no preamble, no metadata, no notes about your process.
"""


def build_content_block(daily_briefs, news_reports, public_record, upcoming_meetings) -> str:
    parts = ["=== DAILY BRIEFS (past 7 days) ===\n"]
    for d, text in daily_briefs:
        parts.append(f"--- {d.isoformat()} ---\n{text}\n")
    parts.append("\n=== NEWS REPORTS (human-reviewed, past 7 days) ===\n")
    for d, slug, text in news_reports:
        parts.append(f"--- {slug} ({d.isoformat()}) ---\n{text}\n")
    parts.append("\n=== PUBLIC RECORD FILINGS (past 7 days) ===\n")
    for d, slug, text in public_record:
        parts.append(f"--- {slug} ---\n{text}\n")
    parts.append("\n=== UPCOMING MEETINGS (next 2 weeks) ===\n")
    for d, slug, text in upcoming_meetings:
        parts.append(f"--- {slug} (meeting date: {d.isoformat()}) ---\n{text}\n")
    return "\n".join(parts)


def call_claude(prompt: str, api_key: str) -> str | None:
    body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        CLAUDE_API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
            content = result.get("content", [])
            if content and content[0].get("type") == "text":
                return content[0]["text"]
            return None
    except Exception as e:
        print(f"  ERROR: Claude API call failed: {e}", file=sys.stderr)
        return None


def next_sunday(today: date) -> date:
    days_ahead = (6 - today.weekday()) % 7
    return today if days_ahead == 0 else today + timedelta(days=days_ahead)


def main():
    parser = argparse.ArgumentParser(description="Generate a TDB Weekly newsletter draft.")
    parser.add_argument("--send-date", type=str, help="Send date YYYY-MM-DD (default: next Sunday)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing draft")
    parser.add_argument("--dry-run", action="store_true", help="Print the prompt and exit; no API call")
    args = parser.parse_args()

    today = date.today()
    send_date = (
        datetime.strptime(args.send_date, "%Y-%m-%d").date() if args.send_date else next_sunday(today)
    )

    end = today
    start = end - timedelta(days=7)

    NEWSLETTER_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = NEWSLETTER_DRAFTS_DIR / f"tdb-weekly-{send_date.isoformat()}.md"
    if out_path.exists() and not args.force and not args.dry_run:
        print(f"Draft already exists at {out_path}. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    print(f"Send date: {send_date.isoformat()}")
    print(f"Scanning content from {start.isoformat()} to {end.isoformat()}...")

    daily_briefs = collect_daily_briefs(start, end)
    news_reports = collect_news_reports(start, end)
    public_record = collect_public_record(start, end)
    upcoming_meetings = collect_upcoming_meetings(today, lookahead_days=14)

    print(f"  Daily briefs:          {len(daily_briefs)}")
    print(f"  News reports:          {len(news_reports)}")
    print(f"  Public record filings: {len(public_record)}")
    print(f"  Upcoming meetings:     {len(upcoming_meetings)}")

    crossword_link = get_crossword_link(send_date)
    if not crossword_link:
        print("WARNING: no crossword puzzle found for send date. Placeholder used.", file=sys.stderr)
        crossword_link = "(no puzzle available — pick one before sending)"
    else:
        print(f"  Crossword:             {crossword_link}")

    content_block = build_content_block(daily_briefs, news_reports, public_record, upcoming_meetings)
    prompt = PROMPT_TEMPLATE.format(crossword_link=crossword_link, content_block=content_block)

    print(f"\nPrompt size: ~{len(prompt):,} chars (~{len(prompt) // 4:,} tokens)")

    if args.dry_run:
        print("\n--- DRY RUN: prompt below ---\n")
        print(prompt)
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print("Calling Claude...")
    draft = call_claude(prompt, api_key)
    if not draft:
        print("ERROR: failed to generate draft", file=sys.stderr)
        sys.exit(1)

    header = (
        f"*Draft generated {datetime.now().strftime('%Y-%m-%d %H:%M')} by the TDB Weekly newsletter generator using {CLAUDE_MODEL}.*\n"
        f"*Send date: {send_date.isoformat()}.*\n"
        f"*Crossword link embedded: {crossword_link}*\n"
        f"*Human review required before sending via Buttondown.*\n\n---\n\n"
    )
    out_path.write_text(header + draft)
    print(f"\nDraft saved: {out_path}")


if __name__ == "__main__":
    main()
