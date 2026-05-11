#!/usr/bin/env python3
"""
Generate an HTML blog post from a Tucson Daily Brief markdown briefing file,
and rebuild both the homepage (index.html) and the full daily-brief archive
(briefings.html).

Usage:
    python generate_post.py path/to/tucson-brief-2026-02-18.md
    python generate_post.py --rebuild-homepage     # refresh only (no new post)
"""

import sys
import os
import re
import argparse
from datetime import datetime
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent
POSTS_DIR = SITE_DIR / "posts"
MEETINGS_DIR = SITE_DIR / "meeting-watch"
REPORTS_DIR = SITE_DIR / "news-reports"
PUBLIC_RECORD_DIR = SITE_DIR / "public-record"

# Map source outlet names to their homepages (longest names first to match greedily)
SOURCE_URLS = {
    "Arizona Luminaria": "https://azluminaria.org",
    "AZ Luminaria": "https://azluminaria.org",
    "Arizona Daily Star": "https://tucson.com",
    "Arizona Mirror": "https://azmirror.com",
    "AZPM": "https://www.azpm.org",
    "Cronkite News": "https://cronkitenews.azpbs.org",
    "Inside Tucson Business": "https://www.insidetucsonbusiness.com",
    "KGUN 9": "https://www.kgun9.com",
    "NWS Tucson": "https://forecast.weather.gov/MapClick.php?CityName=Tucson&state=AZ",
    "SaddleBrooke Progress": "https://www.saddlebrookeprogress.com",
    "This Is Tucson": "https://thisistucson.com",
    "Tucson Agenda": "https://tucsonagenda.substack.com",
    "Tucson Foodie": "https://www.tucsonfoodie.com",
    "Tucson Local Media": "https://www.tucsonlocalmedia.com",
    "Explorer News": "https://www.tucsonlocalmedia.com",
    "CALÓ News": "https://calonews.org",
}


# ---------------------------------------------------------------------------
# Date and slug helpers
# ---------------------------------------------------------------------------

def parse_date_from_filename(filepath: str) -> datetime:
    """Extract date from a filename like tucson-brief-2026-02-18.md."""
    basename = Path(filepath).stem
    match = re.search(r"(\d{4}-\d{2}-\d{2})", basename)
    if not match:
        print(f"Error: could not extract date from filename '{basename}'", file=sys.stderr)
        sys.exit(1)
    return datetime.strptime(match.group(1), "%Y-%m-%d")


def format_date_long(dt: datetime) -> str:
    """February 18, 2026"""
    return dt.strftime("%B %-d, %Y")


def format_date_short(dt: datetime) -> str:
    """Feb 18, 2026"""
    return dt.strftime("%b %-d, %Y")


def format_date_eyebrow(dt: datetime) -> str:
    """TUESDAY, MAY 11 — used for the featured Today's Brief card."""
    return dt.strftime("%A, %B %-d").upper()


def post_slug(dt: datetime) -> str:
    """2026-02-18"""
    return dt.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def escape(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def inline_format(text: str) -> str:
    """Handle bold (**text**) within already-safe-ish content."""
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return text


# ---------------------------------------------------------------------------
# Briefing markdown → HTML
# ---------------------------------------------------------------------------

def md_to_html(text: str) -> str:
    """Convert briefing markdown to HTML."""
    lines = text.strip().split("\n")
    html_parts = []
    i = 0

    # Skip first line (title — we use the date from filename instead)
    if lines and lines[0].startswith("Tucson Daily Brief"):
        i = 1

    # Skip trailing metadata lines
    end = len(lines)
    for j in range(len(lines) - 1, -1, -1):
        line = lines[j].strip()
        if (line.startswith("Briefing saved:") or
                line.startswith("Sources fetched:") or
                line.startswith("Failed sources:") or
                line.startswith("Next update:")):
            end = j
        else:
            break

    while i < end:
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        if re.match(r"^[─\-]{3,}$", line):
            html_parts.append("<hr>")
            i += 1
            continue

        if line.startswith("\U0001f4f0") or line.startswith("\U0001f4c4"):
            source_text = line.replace("\U0001f4f0", "").replace("\U0001f4c4", "").strip()
            html_parts.append(f'<p class="source">{linkify_sources(source_text)}</p>')
            i += 1
            continue

        if re.match(r"^[\U0001f300-\U0001faff☀-➿️]", line) and not line.startswith("**"):
            html_parts.append(f"<h2>{escape(line)}</h2>")
            i += 1
            continue

        para_lines = [line]
        i += 1
        while i < end:
            next_line = lines[i].strip()
            if (not next_line or
                    next_line.startswith("\U0001f4f0") or
                    next_line.startswith("\U0001f4c4") or
                    re.match(r"^[─\-]{3,}$", next_line) or
                    re.match(r"^[\U0001f300-\U0001faff☀-➿️]", next_line)):
                break
            para_lines.append(next_line)
            i += 1

        para_text = " ".join(para_lines)
        para_html = inline_format(para_text)
        html_parts.append(f"<p>{para_html}</p>")

    return "\n".join(html_parts)


def linkify_sources(text: str) -> str:
    """Convert source citation text to HTML with hyperlinks."""
    def md_link_to_html(m):
        name = m.group(1)
        url = m.group(2)
        return f'<a href="{escape(url)}">{escape(name)}</a>'

    result = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', md_link_to_html, text)

    for name in sorted(SOURCE_URLS, key=len, reverse=True):
        url = SOURCE_URLS[name]
        result = re.sub(
            r'(?<![">])' + re.escape(name) + r'(?![^<]*</a>)',
            f'<a href="{url}">{escape(name)}</a>',
            result,
        )
    return result


def extract_lede(text: str) -> str:
    """Pull the first story headline for the index listing."""
    for line in text.strip().split("\n"):
        match = re.search(r"\*\*(.+?)\*\*", line)
        if match:
            headline = match.group(1)
            if headline.endswith("."):
                headline = headline[:-1]
            if len(headline) > 120:
                headline = headline[:117] + "..."
            return headline
    return ""


# ---------------------------------------------------------------------------
# Shared page chrome — used by every index page on the site
# ---------------------------------------------------------------------------

ANALYTICS_HTML = """<script async src="https://www.googletagmanager.com/gtag/js?id=G-MEYSB9GYF2"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-MEYSB9GYF2');
</script>"""

FOOTER_HTML = """<footer>
<p>By Nicholas De Leon</p>
<p class="footer-links">
<a href="https://podcasts.apple.com/us/podcast/tucson-daily-brief/id1878173070">Apple Podcasts</a> &middot;
<a href="https://www.youtube.com/@tucsondailybrief">YouTube</a> &middot;
<a href="https://www.linkedin.com/in/nicholas-de-leon-3b5b6a9">LinkedIn</a> &middot;
<a href="https://www.instagram.com/daylayownphoto">Instagram</a> &middot;
<a href="mailto:nicholas@daylayown.org">Email</a>
</p>
</footer>"""

SUBSCRIBE_PANEL_HTML = """<section class="subscribe-cta">
<h2>TDB Weekly</h2>
<p>A warm Sunday-morning roundup of what mattered in Tucson this week. Subscribers also get The Tucson Mini &mdash; a 5&times;5 crossword built just for them.</p>
<form action="https://buttondown.email/api/emails/embed-subscribe/tucsondailybrief" method="post" target="_blank">
<input type="email" name="email" placeholder="your@email.com" aria-label="Email address" required>
<button type="submit">Subscribe</button>
</form>
<p class="subscribe-fineprint">Free. Sunday mornings. Unsubscribe anytime.</p>
</section>"""


# Section nav slots — used to mark the current page (no link) and adjust paths
# `active` values: "" (homepage), "briefings", "meetings", "reports", "record",
# "ask", "responsiveness"
_STREAMS = [
    ("briefings", "Briefings", "briefings.html"),
    ("meetings", "Meeting Watch", "meeting-watch.html"),
    ("reports", "News Reports", "news-reports.html"),
    ("record", "Public Record", "public-record.html"),
]

_TOOLS = [
    ("ask", "Ask", "ask.html"),
    ("responsiveness", "Responsiveness", "responsiveness.html"),
]


def section_nav_html(active: str = "", path_prefix: str = "") -> str:
    """Render the two-row section nav. `active` marks the current page (rendered
    as plain text). `path_prefix` is "" for site root or "../" for nested pages."""
    def link_or_text(key, label, href):
        if key == active:
            return f'<span class="active">{label}</span>'
        return f'<a href="{path_prefix}{href}">{label}</a>'

    streams = " &middot; ".join(link_or_text(*s) for s in _STREAMS)
    tools = " &middot; ".join(link_or_text(*t) for t in _TOOLS)

    return f"""<nav class="section-nav">
<div class="streams-nav">{streams}</div>
<div class="tools-nav">{tools}</div>
</nav>"""


# ---------------------------------------------------------------------------
# Post rendering (individual daily-brief page)
# ---------------------------------------------------------------------------

def render_post(date: datetime, body_html: str) -> str:
    """Render a full post HTML page."""
    title = f"Tucson Daily Brief &mdash; {format_date_long(date)}"
    slug = post_slug(date)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="../style.css">
{ANALYTICS_HTML}
</head>
<body>
<div class="container">

<header>
<h1><a href="../">Tucson Daily Brief</a></h1>
<p class="tagline">An ongoing experiment at the intersection of artificial intelligence and local journalism, by Nicholas De Leon</p>
</header>

<a class="back-link" href="../briefings.html">&larr; All briefings</a>

<article id="{slug}">
<p class="post-meta">{format_date_long(date)}</p>
{body_html}
</article>

{FOOTER_HTML}

</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Cross-section data collection (for the homepage cross-stream cards)
# ---------------------------------------------------------------------------

def collect_existing_posts() -> list[dict]:
    """Scan posts/ directory for existing HTML files and extract metadata."""
    posts = []
    if not POSTS_DIR.exists():
        return posts
    for f in POSTS_DIR.glob("*.html"):
        match = re.search(r"(\d{4}-\d{2}-\d{2})", f.stem)
        if not match:
            continue
        dt = datetime.strptime(match.group(1), "%Y-%m-%d")
        content = f.read_text()
        lede_match = re.search(r'<p class="post-lede"[^>]*>(.+?)</p>', content)
        if not lede_match:
            strong_match = re.search(r"<strong>(.+?)</strong>", content)
            lede = strong_match.group(1).rstrip(".") if strong_match else ""
        else:
            lede = lede_match.group(1)
        posts.append({"date": dt, "slug": post_slug(dt), "lede": lede})
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def _newest_html_in(directory: Path) -> Path | None:
    """Return the newest dated HTML file in a section directory, or None."""
    if not directory.exists():
        return None
    candidates = []
    for f in directory.glob("*.html"):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f.stem)
        if not m:
            continue
        dt = datetime.strptime(m.group(1), "%Y-%m-%d")
        candidates.append((dt, f))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def _unescape_and_truncate(html_snippet: str, max_len: int = 110) -> str:
    """Strip tags, decode HTML entities, optionally truncate. Returns plain text."""
    text = re.sub(r"<[^>]+>", "", html_snippet).strip()
    text = (text.replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", '"')
                .replace("&mdash;", "—")
                .replace("&middot;", "·")
                .replace("&rsquo;", "’")
                .replace("&lsquo;", "‘")
                .replace("&times;", "×"))
    text = re.sub(r"\s+", " ", text)
    if max_len and len(text) > max_len:
        text = text[: max_len - 3] + "..."
    return text


def _article_h1(content: str) -> str | None:
    """Pull the first <h1> inside the <article> tag."""
    m = re.search(r'<article[^>]*>.*?<h1>(.+?)</h1>', content, re.DOTALL)
    return _unescape_and_truncate(m.group(1), max_len=0) if m else None


def collect_latest_meeting() -> dict | None:
    """Scan meeting-watch/ for the newest preview. Returns a card dict or None."""
    f = _newest_html_in(MEETINGS_DIR)
    if not f:
        return None
    m = re.search(r"(\d{4}-\d{2}-\d{2})", f.stem)
    dt = datetime.strptime(m.group(1), "%Y-%m-%d")
    content = f.read_text()
    title = _article_h1(content) or f.stem
    # Lede: paragraph right after the "Meeting Preview" h2 (editorial overview)
    lede = ""
    lede_match = re.search(
        r'<h2>\s*Meeting Preview\s*</h2>\s*<p>(.+?)</p>',
        content, re.DOTALL)
    if lede_match:
        lede = _unescape_and_truncate(lede_match.group(1))
    return {
        "date": dt,
        "title": title,
        "lede": lede,
        "href": f"meeting-watch/{f.stem}.html",
    }


def collect_latest_report() -> dict | None:
    """Scan news-reports/ for the newest report."""
    f = _newest_html_in(REPORTS_DIR)
    if not f:
        return None
    m = re.search(r"(\d{4}-\d{2}-\d{2})", f.stem)
    dt = datetime.strptime(m.group(1), "%Y-%m-%d")
    content = f.read_text()
    title = _article_h1(content) or f.stem
    # Lede: first <p><strong>...</strong></p> after the h1 (the bold lede paragraph)
    lede = ""
    lede_match = re.search(
        r'<article[^>]*>.*?<h1>.+?</h1>\s*<p><strong>(.+?)</strong></p>',
        content, re.DOTALL)
    if lede_match:
        lede = _unescape_and_truncate(lede_match.group(1))
    return {
        "date": dt,
        "title": title,
        "lede": lede,
        "href": f"news-reports/{f.stem}.html",
    }


def collect_latest_filing() -> dict | None:
    """Scan public-record/ for the newest filing."""
    if not PUBLIC_RECORD_DIR.exists():
        return None
    candidates = []
    for f in PUBLIC_RECORD_DIR.glob("liquor-*.html"):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f.stem)
        if not m:
            continue
        dt = datetime.strptime(m.group(1), "%Y-%m-%d")
        candidates.append((dt, f))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    dt, f = candidates[0]
    content = f.read_text()
    title = _article_h1(content) or f.stem
    lede = ""
    lede_match = re.search(r'<p class="filing-subtitle">(.+?)</p>', content)
    if lede_match:
        lede = _unescape_and_truncate(lede_match.group(1))
    return {
        "date": dt,
        "title": title,
        "lede": lede,
        "href": f"public-record/{f.stem}.html",
    }


# ---------------------------------------------------------------------------
# Homepage and full-archive (briefings.html) rendering
# ---------------------------------------------------------------------------

def _render_featured_card(featured: dict) -> str:
    """The big 'Today's Brief' card at the top of the homepage."""
    return f"""<article class="home-feature">
<p class="eyebrow stream">{format_date_eyebrow(featured["date"])}</p>
<h2 class="home-feature-title">Today's Brief</h2>
<p class="home-feature-lede">{escape(featured["lede"])}</p>
<p class="home-feature-cta"><a href="posts/{featured["slug"]}.html">Read today's brief &rarr;</a></p>
</article>"""


def _render_stream_card(label: str, item: dict) -> str:
    """A cross-stream card (Meeting Watch, News Reports, or Public Record)."""
    eyebrow = f"{label} &middot; {format_date_short(item['date'])}"
    lede_html = f'<p class="home-card-lede">{escape(item["lede"])}</p>' if item.get("lede") else ""
    return f"""<article class="home-card">
<p class="eyebrow stream">{eyebrow}</p>
<h3 class="home-card-title"><a href="{item["href"]}">{escape(item["title"])}</a></h3>
{lede_html}
</article>"""


def _render_tool_card(label: str, blurb: str, href: str) -> str:
    """A card for an interactive tool (Ask, Responsiveness)."""
    return f"""<article class="home-card tool-card">
<p class="eyebrow tool">{label}</p>
<p class="tool-card-blurb"><a href="{href}">{blurb} &rarr;</a></p>
</article>"""


def _render_recent_list(posts: list[dict]) -> str:
    """Compressed list of the most recent daily briefs (after the featured one)."""
    items = []
    for p in posts:
        items.append(f"""<li>
<span class="recent-date">{format_date_short(p["date"])}</span>
<a href="posts/{p["slug"]}.html">{escape(p["lede"])}</a>
</li>""")
    return "\n".join(items)


def render_homepage(posts: list[dict],
                    latest_meeting: dict | None,
                    latest_report: dict | None,
                    latest_filing: dict | None) -> str:
    """Render the new zoned homepage."""
    if not posts:
        featured_html = '<p class="empty">No briefings yet.</p>'
        recent_html = ""
    else:
        featured = posts[0]
        featured_html = _render_featured_card(featured)
        recent = posts[1:8]
        if recent:
            recent_html = f"""<section class="home-recent">
<h2 class="home-section-title">Recent briefings</h2>
<ul class="home-recent-list">
{_render_recent_list(recent)}
</ul>
<p class="see-all"><a href="briefings.html">See all daily briefings &rarr;</a></p>
</section>"""
        else:
            recent_html = ""

    cards = []
    if latest_meeting:
        cards.append(_render_stream_card("MEETING WATCH", latest_meeting))
    if latest_report:
        cards.append(_render_stream_card("NEWS REPORTS", latest_report))
    if latest_filing:
        cards.append(_render_stream_card("PUBLIC RECORD", latest_filing))

    if cards:
        cross_section_html = f"""<section class="home-cross">
<h2 class="home-section-title">Latest from across TDB</h2>
{"".join(cards)}
</section>"""
    else:
        cross_section_html = ""

    tools_html = f"""<section class="home-tools">
<h2 class="home-section-title">Tools</h2>
{_render_tool_card("ASK TDB", "Ask any question about Tucson. Answers come from TDB&rsquo;s own reporting, with citations.", "ask.html")}
{_render_tool_card("RESPONSIVENESS INDEX", "How fast does Tucson respond to its residents? A living dashboard.", "responsiveness.html")}
</section>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tucson Daily Brief</title>
<link rel="stylesheet" href="style.css">
{ANALYTICS_HTML}
</head>
<body>
<div class="container">

<header>
<h1><a href="./">Tucson Daily Brief</a></h1>
<p class="tagline">An ongoing experiment at the intersection of artificial intelligence and local journalism, by Nicholas De Leon</p>
</header>

{section_nav_html(active="")}

{featured_html}

{cross_section_html}

{tools_html}

{SUBSCRIBE_PANEL_HTML}

{recent_html}

{FOOTER_HTML}

</div>
</body>
</html>
"""


def render_briefings_index(posts: list[dict]) -> str:
    """Render the full daily-brief archive page (formerly index.html's role)."""
    items = []
    for p in posts:
        items.append(f"""<li>
<span class="post-date">{format_date_short(p["date"])}</span>
<a href="posts/{p["slug"]}.html">{format_date_long(p["date"])}</a>
<p class="post-lede">{escape(p["lede"])}</p>
</li>""")

    post_list = "\n".join(items) if items else '<li class="empty">No briefings yet.</li>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Briefings &mdash; Tucson Daily Brief</title>
<link rel="stylesheet" href="style.css">
{ANALYTICS_HTML}
</head>
<body>
<div class="container">

<header>
<h1><a href="./">Tucson Daily Brief</a></h1>
<p class="tagline">Daily briefings &mdash; every day&rsquo;s local news synthesis, newest first</p>
</header>

{section_nav_html(active="briefings")}

{SUBSCRIBE_PANEL_HTML}

<ul class="post-list">
{post_list}
</ul>

{FOOTER_HTML}

</div>
</body>
</html>
"""


def rebuild_homepage() -> None:
    """Rebuild index.html (zoned homepage) and briefings.html (full archive).
    Callable from any pipeline that publishes new content."""
    posts = collect_existing_posts()
    latest_meeting = collect_latest_meeting()
    latest_report = collect_latest_report()
    latest_filing = collect_latest_filing()

    (SITE_DIR / "index.html").write_text(
        render_homepage(posts, latest_meeting, latest_report, latest_filing)
    )
    (SITE_DIR / "briefings.html").write_text(render_briefings_index(posts))
    print(f"  Rebuilt: index.html (homepage) + briefings.html ({len(posts)} briefing(s))")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate a TDB daily-brief post and rebuild the homepage.")
    parser.add_argument("briefing", nargs="?", help="Path to tucson-brief-YYYY-MM-DD.md")
    parser.add_argument("--rebuild-homepage", action="store_true",
                        help="Refresh index.html and briefings.html only; do not process a briefing.")
    args = parser.parse_args()

    if args.rebuild_homepage:
        rebuild_homepage()
        return

    if not args.briefing:
        parser.error("provide a briefing path, or use --rebuild-homepage")

    md_path = args.briefing
    if not os.path.isfile(md_path):
        print(f"Error: file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    date = parse_date_from_filename(md_path)
    slug = post_slug(date)
    md_text = Path(md_path).read_text()
    body_html = md_to_html(md_text)

    POSTS_DIR.mkdir(exist_ok=True)
    post_file = POSTS_DIR / f"{slug}.html"
    post_file.write_text(render_post(date, body_html))
    print(f"Wrote {post_file}")

    rebuild_homepage()


if __name__ == "__main__":
    main()
