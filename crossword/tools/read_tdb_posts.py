#!/usr/bin/env python3
"""Read recent Tucson Daily Brief posts as the news corpus for crossword cluing.

Replaces the Google News + Bluesky scrapers in the upstream Crosswording the
Situation pipeline. TDB posts live as static HTML in posts/YYYY-MM-DD.html
and follow a predictable template (see CLAUDE.md). Each story is a bold
headline inside a section like "Government" / "Public Safety" / etc.
"""

import re
import sys
from datetime import datetime, timedelta
from html import unescape
from pathlib import Path

POSTS_DIR = Path(__file__).parent.parent.parent / "posts"


def read_recent_posts(days_back: int = 7, today: datetime | None = None) -> list[dict]:
    """Read TDB posts from the past N days (skipping today if not yet posted).

    Returns a flat list of story dicts:
        {"date": "YYYY-MM-DD", "section": "Government", "title": "...",
         "summary": "...", "source": "...", "age_days": N}
    """
    if today is None:
        today = datetime.now()
    stories: list[dict] = []
    for i in range(days_back + 1):  # include today (0) through days_back
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        path = POSTS_DIR / f"{d}.html"
        if not path.exists():
            continue
        with open(path) as f:
            html = f.read()
        post_stories = _extract_stories(html)
        for s in post_stories:
            s["date"] = d
            s["age_days"] = i
        stories.extend(post_stories)
    return stories


_SECTION_RE = re.compile(r"<h2>([^<]+)</h2>")
_STORY_RE = re.compile(
    r"<p>\s*<strong>([^<]+?)</strong>(.*?)</p>"
    r"(?:\s*<p class=\"source\">(.*?)</p>)?",
    re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(s: str) -> str:
    return unescape(_TAG_RE.sub("", s)).strip()


def _extract_stories(html: str) -> list[dict]:
    """Extract bold-headline stories from a TDB post HTML, tagged by section."""
    out: list[dict] = []
    section_starts = list(_SECTION_RE.finditer(html))
    for idx, m in enumerate(section_starts):
        section_raw = _strip_tags(m.group(1))
        # Strip leading emoji / non-word chars
        section = re.sub(r"^[\W_]+", "", section_raw).strip()
        body_start = m.end()
        if idx + 1 < len(section_starts):
            body_end = section_starts[idx + 1].start()
        else:
            tail = html.find("</article>", body_start)
            body_end = tail if tail != -1 else len(html)
        body = html[body_start:body_end]
        for sm in _STORY_RE.finditer(body):
            title = _strip_tags(sm.group(1)).rstrip(".:")
            summary = _strip_tags(sm.group(2)).strip()
            source_block = sm.group(3) or ""
            source = _strip_tags(source_block).strip() if source_block else ""
            out.append({
                "section": section,
                "title": title,
                "summary": summary,
                "source": source,
            })
    return out


def format_posts_for_prompt(stories: list[dict], max_summary_chars: int = 280) -> str:
    """Format extracted stories for the Claude prompt — fresh first."""
    stories_sorted = sorted(stories, key=lambda s: s.get("age_days", 0))
    lines: list[str] = []
    for s in stories_sorted:
        age = s.get("age_days", 0)
        age_label = "today" if age == 0 else f"{age}d ago"
        section = s.get("section", "")
        src = f" — {s['source']}" if s.get("source") else ""
        lines.append(f"[{section} · {age_label}]{src}")
        lines.append(f"  {s['title']}")
        summary = s.get("summary", "")
        if summary:
            if len(summary) > max_summary_chars:
                summary = summary[:max_summary_chars].rsplit(" ", 1)[0] + "…"
            lines.append(f"  {summary}")
        lines.append("")
    return "\n".join(lines).strip()


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    stories = read_recent_posts(days)
    print(f"Found {len(stories)} stories across past {days} days\n", file=sys.stderr)
    print(format_posts_for_prompt(stories))
