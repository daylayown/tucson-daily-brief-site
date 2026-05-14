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
from datetime import datetime, timedelta
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent
POSTS_DIR = SITE_DIR / "posts"
MEETINGS_DIR = SITE_DIR / "meeting-watch"
REPORTS_DIR = SITE_DIR / "news-reports"
PUBLIC_RECORD_DIR = SITE_DIR / "public-record"

# Feature flag: surface the Tools (Ask, Responsiveness Index) on the site.
# Flip to True once at least one tool ships. When False:
#   - The homepage Tools card row is hidden
#   - The Tools nav row (under streams nav) is hidden on every page
# Stub pages at /ask.html and /responsiveness.html still exist and work; they
# just aren't linked from the main nav until this flag flips.
SHOW_TOOLS = False

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

ANALYTICS_HTML = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK@9..144,300..900,0..100,0..1&family=Newsreader:ital,opsz,wght@0,6..72,300..700;1,6..72,300..700&display=swap">
<noscript><style>.section-head__rule path { stroke-dashoffset: 0 !important; }</style></noscript>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MEYSB9GYF2"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-MEYSB9GYF2');
</script>"""

# Inline SVGs reused across the site
SUNRAY_SVG = """<svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
<circle cx="7" cy="7" r="2.2" fill="currentColor"/>
<g stroke="currentColor" stroke-width="1.2" stroke-linecap="round">
<line x1="7" y1="0.5" x2="7" y2="2.5"/><line x1="7" y1="11.5" x2="7" y2="13.5"/>
<line x1="0.5" y1="7" x2="2.5" y2="7"/><line x1="11.5" y1="7" x2="13.5" y2="7"/>
<line x1="2.4" y1="2.4" x2="3.6" y2="3.6"/><line x1="10.4" y1="10.4" x2="11.6" y2="11.6"/>
<line x1="2.4" y1="11.6" x2="3.6" y2="10.4"/><line x1="10.4" y1="3.6" x2="11.6" y2="2.4"/>
</g></svg>"""

# Larger sun motif for the homepage featured area — same geometry as SUNRAY_SVG
# but scaled up with 12 rays of varied length so it reads as an editorial mark
# rather than a tiny dingbat. Uses currentColor so the CSS sets the tint.
FEATURED_SUN_SVG = """<svg class="featured__sun" viewBox="0 0 160 160" aria-hidden="true">
<circle cx="80" cy="80" r="30" fill="currentColor" fill-opacity="0.85"/>
<g stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-opacity="0.75">
<line x1="80" y1="8" x2="80" y2="30"/>
<line x1="80" y1="130" x2="80" y2="152"/>
<line x1="8" y1="80" x2="30" y2="80"/>
<line x1="130" y1="80" x2="152" y2="80"/>
<line x1="29" y1="29" x2="44" y2="44"/>
<line x1="116" y1="116" x2="131" y2="131"/>
<line x1="29" y1="131" x2="44" y2="116"/>
<line x1="116" y1="44" x2="131" y2="29"/>
<line x1="50" y1="14" x2="56" y2="32"/>
<line x1="110" y1="14" x2="104" y2="32"/>
<line x1="50" y1="146" x2="56" y2="128"/>
<line x1="110" y1="146" x2="104" y2="128"/>
</g></svg>"""

ARROW_SVG = """<svg width="18" height="14" viewBox="0 0 18 14" aria-hidden="true"><path d="M1 7h15M11 2l5 5-5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>"""

ARROW_LEFT_SVG = """<svg width="18" height="14" viewBox="0 0 18 14" aria-hidden="true"><path d="M17 7H2M7 2L2 7l5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>"""

HAND_RULE_SVG = """<svg class="section-head__rule" width="280" height="14" viewBox="0 0 280 14" fill="none" aria-hidden="true">
<path d="M2 8 C 30 4, 80 12, 130 7 S 230 4, 278 9" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" fill="none"/>
</svg>"""

# Vanilla JS for scroll-triggered hand-drawn underlines
SCROLL_TRIGGER_JS = """<script>
(function(){if(!('IntersectionObserver' in window)){document.querySelectorAll('.section-head__rule').forEach(el=>el.classList.add('in-view'));return;}
const io=new IntersectionObserver((entries)=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in-view');io.unobserve(e.target);}});},{rootMargin:'0px 0px -8% 0px',threshold:0.1});
document.querySelectorAll('.section-head__rule').forEach(el=>io.observe(el));})();
</script>"""

FOOTER_HTML = """<div class="footer-row">
<p class="footer-row__byline">By Nicholas De Leon, in Tucson.</p>
<p class="footer-row__links">
<a href="https://podcasts.apple.com/us/podcast/tucson-daily-brief/id1878173070">Apple Podcasts</a>
<a href="https://www.youtube.com/@tucsondailybrief">YouTube</a>
<a href="https://www.linkedin.com/in/nicholas-de-leon-3b5b6a9">LinkedIn</a>
<a href="https://x.com/nicholasadeleon">X</a>
<a href="https://bsky.app/profile/nicholasadeleon.bsky.social">Bluesky</a>
<a href="mailto:nicholas@daylayown.org">Email</a>
</p>
</div>"""

# Decorative SVG for the subscribe panel: sun, mountains, saguaro silhouette
SUBSCRIBE_ART_SVG = """<svg viewBox="0 0 240 240" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
<stop offset="0%" stop-color="#d97048" stop-opacity="0"/>
<stop offset="100%" stop-color="#8c3a1f" stop-opacity="0.5"/>
</linearGradient></defs>
<circle cx="190" cy="60" r="36" fill="#f5f0e6" opacity="0.92"/>
<g stroke="#faf4e8" stroke-width="1.5" stroke-linecap="round" opacity="0.55">
<line x1="190" y1="6" x2="190" y2="20"/><line x1="190" y1="100" x2="190" y2="114"/>
<line x1="136" y1="60" x2="150" y2="60"/><line x1="230" y1="60" x2="244" y2="60"/>
<line x1="152" y1="22" x2="162" y2="32"/><line x1="218" y1="98" x2="228" y2="108"/>
<line x1="152" y1="98" x2="162" y2="88"/><line x1="218" y1="22" x2="228" y2="12"/>
</g>
<path d="M -10 200 L 30 150 L 60 175 L 90 130 L 130 165 L 170 110 L 210 145 L 250 175 L 250 240 L -10 240 Z" fill="#3d3029" opacity="0.6"/>
<path d="M -10 230 L 50 195 L 100 215 L 150 185 L 200 205 L 250 190 L 250 240 L -10 240 Z" fill="#251c17" opacity="0.55"/>
<g transform="translate(60 130)" fill="#3d3029" opacity="0.85">
<rect x="-4" y="0" width="8" height="80" rx="3"/>
<rect x="-4" y="20" width="3" height="22" rx="1.5"/>
<rect x="1" y="36" width="3" height="16" rx="1.5"/>
<rect x="-12" y="22" width="8" height="3" rx="1.5"/>
<rect x="-9" y="20" width="3" height="14" rx="1.5"/>
<rect x="4" y="32" width="8" height="3" rx="1.5"/>
<rect x="9" y="22" width="3" height="14" rx="1.5"/>
</g>
<rect x="0" y="0" width="240" height="240" fill="url(#sky)"/>
</svg>"""

SUBSCRIBE_PANEL_HTML = f"""<div class="subscribe__panel">
<div class="subscribe__art">{SUBSCRIBE_ART_SVG}</div>
<div class="subscribe__body">
<p class="subscribe__eyebrow">TDB Weekly</p>
<h2 class="subscribe__title">A warm Sunday-morning roundup of Tucson, in your inbox.</h2>
<p>Five sections, ~900 words. Subscribers also get The Tucson Mini &mdash; a 5&times;5 crossword built just for them.</p>
<form action="https://buttondown.email/api/emails/embed-subscribe/tucsondailybrief" method="post" target="_blank" class="subscribe__form">
<input class="subscribe__input" type="email" name="email" placeholder="you@somewhere.com" aria-label="Email address" required>
<button class="subscribe__button" type="submit">Subscribe</button>
</form>
<p class="subscribe__fine">Free. Sunday mornings. Unsubscribe anytime.</p>
</div>
</div>"""

# Header used by every page on the site
def site_header_html() -> str:
    return """<header class="masthead">
<div class="container">
<p class="masthead__kicker">From the Old Pueblo</p>
<h1 class="masthead__wordmark"><a href="./">Tucson Daily Brief</a></h1>
<p class="masthead__tagline">An ongoing experiment at the intersection of artificial intelligence and local journalism, by Nicholas De Leon.</p>
</div>
</header>"""

# Subpage header (for individual posts) — relative paths back to root
def post_header_html() -> str:
    return """<header class="masthead">
<div class="container">
<p class="masthead__kicker">From the Old Pueblo</p>
<h1 class="masthead__wordmark"><a href="../">Tucson Daily Brief</a></h1>
<p class="masthead__tagline">An ongoing experiment at the intersection of artificial intelligence and local journalism, by Nicholas De Leon.</p>
</div>
</header>"""


# Section nav slots — used to mark the current page (no link) and adjust paths
# `active` values: "" (homepage), "briefings", "meetings", "reports", "record",
# "ask", "responsiveness"
_STREAMS = [
    ("briefings", "Briefings", "briefings.html"),
    ("meetings", "Meeting Watch", "meeting-watch.html"),
    ("reports", "News Reports", "news-reports.html"),
    ("record", "Spotted", "public-record.html"),
]

_TOOLS = [
    ("ask", "Ask", "ask.html"),
    ("responsiveness", "Responsiveness", "responsiveness.html"),
]


def section_nav_html(active: str = "", path_prefix: str = "") -> str:
    """Render the section nav. `active` marks the current page (rendered as
    plain text). `path_prefix` is "" for site root or "../" for nested pages.
    The Tools row is gated by the SHOW_TOOLS flag."""
    def link_or_text(key, label, href):
        if key == active:
            return f'<span class="active">{label}</span>'
        return f'<a href="{path_prefix}{href}">{label}</a>'

    streams = " &middot; ".join(link_or_text(*s) for s in _STREAMS)

    if SHOW_TOOLS:
        tools = " &middot; ".join(link_or_text(*t) for t in _TOOLS)
        tools_row = f'<div class="tools-nav">{tools}</div>'
    else:
        tools_row = ""

    return f"""<nav class="section-nav">
<div class="streams-nav">{streams}</div>
{tools_row}
</nav>"""


# ---------------------------------------------------------------------------
# Post rendering (individual daily-brief page)
# ---------------------------------------------------------------------------

def render_post(date: datetime, body_html: str) -> str:
    """Render a daily-brief individual post page in the new editorial language."""
    title = f"{format_date_long(date)} &mdash; Tucson Daily Brief"
    slug = post_slug(date)
    weekday = date.strftime("%A")
    css_path = "../style.css"
    home_href = "../"
    back_href = "../briefings.html"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{css_path}">
{ANALYTICS_HTML}
</head>
<body>

<header class="masthead">
<div class="container">
<p class="masthead__kicker">From the Old Pueblo</p>
<h1 class="masthead__wordmark"><a href="{home_href}">Tucson Daily Brief</a></h1>
<p class="masthead__tagline">An ongoing experiment at the intersection of artificial intelligence and local journalism, by Nicholas De Leon.</p>
</div>
</header>

<div class="container">
{section_nav_html(active="briefings", path_prefix=home_href)}
</div>

<main>
<div class="container container--reading">
<a class="back-link" href="{back_href}">{ARROW_LEFT_SVG} All briefings</a>

<article id="{slug}" class="brief">
<header class="brief-header">
<p class="brief-kicker">{SUNRAY_SVG} Daily Brief</p>
<h1 class="brief-date">{format_date_long(date)}</h1>
<p class="brief-weekday">{weekday}</p>
</header>
<div class="brief-body">
{body_html}
</div>
</article>
</div>
</main>

<div class="container">
{FOOTER_HTML}
</div>

{SCROLL_TRIGGER_JS}
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

def _render_featured(featured: dict) -> str:
    """The Today's Brief feature: kicker, headline, aside w/ drop cap.
    A terracotta sun motif sits in the upper-right negative space of the
    featured area (see .featured__sun in style.css)."""
    return f"""<section class="featured">
<div class="container">
{FEATURED_SUN_SVG}
<div class="featured__grid">
<div>
<div class="featured__kicker">
{SUNRAY_SVG}
<span class="featured__kicker-text">{format_date_eyebrow(featured["date"])}</span>
</div>
<h2 class="featured__headline">{escape(featured["lede"])}</h2>
</div>
<aside class="featured__aside">
<p class="featured__aside-kicker">Today&rsquo;s Brief</p>
<p class="featured__aside-lede">Plus the rest of the day&rsquo;s news from Tucson, Pima County, and beyond.</p>
<a href="posts/{featured["slug"]}.html" class="featured__cta">
Read today&rsquo;s brief {ARROW_SVG}
</a>
</aside>
</div>
</div>
</section>"""


def _render_stream_card(label: str, when: str, item: dict) -> str:
    """A cross-stream card: eyebrow with section + date, big title, optional lede."""
    lede_html = f'<p class="card__lede">{escape(item["lede"])}</p>' if item.get("lede") else ""
    return f"""<article class="card">
<p class="card__eyebrow">
{SUNRAY_SVG}
<span>{label}</span>
<span class="dot"></span>
<span>{when}</span>
</p>
<h3 class="card__title"><a href="{item["href"]}">{escape(item["title"])}</a></h3>
{lede_html}
</article>"""


def _render_tool_card(label: str, title: str, body: str, cta: str, href: str) -> str:
    """A clay tool card on the homepage (Ask, Responsiveness)."""
    return f"""<a href="{href}" class="tool-card">
<p class="tool-card__eyebrow">{label}</p>
<h3 class="tool-card__title">{title}</h3>
<p class="tool-card__body">{body}</p>
<span class="tool-card__cta">{cta} {ARROW_SVG}</span>
</a>"""


def _render_recent_item(p: dict) -> str:
    weekday_abbr = p["date"].strftime("%a")
    date_str = p["date"].strftime("%b %-d") + f" &middot; {weekday_abbr}"
    return f"""<li class="recent__item">
<span class="recent__date">{date_str}</span>
<h3 class="recent__title"><a href="posts/{p["slug"]}.html">{escape(p["lede"])}</a></h3>
</li>"""


def render_homepage(posts: list[dict],
                    latest_meeting: dict | None,
                    latest_report: dict | None,
                    latest_filing: dict | None) -> str:
    """Render the new zoned homepage in the warm-organic design language."""
    today = datetime.now()

    if not posts:
        featured_block = '<section class="featured"><div class="container"><p style="color:var(--ink-muted);font-style:italic">No briefings yet.</p></div></section>'
        recent_block = ""
    else:
        featured_block = _render_featured(posts[0])
        recent = posts[1:8]
        if recent:
            recent_items = "\n".join(_render_recent_item(p) for p in recent)
            recent_block = f"""<section class="recent">
<div class="container container--editorial">
<div class="recent__head">
<h2 class="section-head">Recent briefings</h2>
</div>
<ul class="recent__list">
{recent_items}
</ul>
<p class="recent__see-all">
<a href="briefings.html">See all daily briefings {ARROW_SVG}</a>
</p>
</div>
</section>"""
        else:
            recent_block = ""

    cards = []
    if latest_meeting:
        when = "Tomorrow" if latest_meeting["date"].date() == (today.date() + timedelta(days=1)) else format_date_short(latest_meeting["date"])
        cards.append(_render_stream_card("Meeting Watch", when, latest_meeting))
    if latest_report:
        cards.append(_render_stream_card("News Reports", format_date_short(latest_report["date"]), latest_report))
    if latest_filing:
        cards.append(_render_stream_card("Spotted", format_date_short(latest_filing["date"]), latest_filing))

    if cards:
        cross_block = f"""<section class="cross-section">
<div class="container container--editorial">
<div class="cross-section__head">
<h2 class="section-head">Latest from across TDB</h2>
</div>
<div class="cross-grid">
{"".join(cards)}
</div>
</div>
</section>"""
    else:
        cross_block = ""

    if SHOW_TOOLS:
        tools_block = f"""<section class="tools-section">
<div class="container container--editorial">
<div class="tools-section__head">
<h2 class="section-head">Tools
{HAND_RULE_SVG}
</h2>
</div>
<div class="tools-grid">
{_render_tool_card("Coming soon", "Ask Tucson anything.", "Answers from three months &mdash; soon, three years &mdash; of original TDB reporting. Citations included.", "Try it", "ask.html")}
{_render_tool_card("Coming soon", "How fast does Tucson respond to its residents?", "A living dashboard measuring the city&rsquo;s 311 service requests, code enforcement, and public records.", "See the index", "responsiveness.html")}
</div>
</div>
</section>"""
    else:
        tools_block = ""

    subscribe_block = f"""<section class="subscribe">
<div class="container container--editorial">
{SUBSCRIBE_PANEL_HTML}
</div>
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

{site_header_html()}

<div class="container">
{section_nav_html(active="")}
</div>

<main>
{featured_block}
{cross_block}
{tools_block}
{subscribe_block}
{recent_block}
</main>

<div class="container">
{FOOTER_HTML}
</div>

{SCROLL_TRIGGER_JS}
</body>
</html>
"""


def render_briefings_index(posts: list[dict]) -> str:
    """Render the full daily-brief archive page."""
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

{site_header_html()}

<div class="container">
{section_nav_html(active="briefings")}
</div>

<main>
<div class="container container--editorial">
<div style="padding-top:var(--gap-xl);margin-bottom:var(--gap-l)">
<h2 class="section-head">Daily briefings</h2>
<p class="section-intro">Every day&rsquo;s synthesis of Tucson, Pima County, and Arizona news, newest first.</p>
</div>

<div style="margin-bottom:var(--gap-xl)">{SUBSCRIBE_PANEL_HTML}</div>

<ul class="post-list">
{post_list}
</ul>
</div>
</main>

<div class="container">
{FOOTER_HTML}
</div>

{SCROLL_TRIGGER_JS}
</body>
</html>
"""


def rebuild_all_briefs(source_dir: str | Path) -> None:
    """Regenerate every individual post HTML by re-running each markdown source
    through render_post(). Called once after a render_post() template change."""
    source = Path(source_dir).expanduser()
    if not source.exists():
        print(f"  Source dir not found: {source}")
        return
    count = 0
    POSTS_DIR.mkdir(exist_ok=True)
    for md_path in sorted(source.glob("tucson-brief-*.md")):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", md_path.stem)
        if not m:
            continue
        date = datetime.strptime(m.group(1), "%Y-%m-%d")
        slug = post_slug(date)
        md_text = md_path.read_text()
        body_html = md_to_html(md_text)
        (POSTS_DIR / f"{slug}.html").write_text(render_post(date, body_html))
        count += 1
    print(f"  Regenerated {count} daily-brief HTML page(s)")


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
    parser.add_argument("--rebuild-all", metavar="DIR",
                        help="Regenerate all individual post HTML from .md files in DIR, then rebuild homepage.")
    args = parser.parse_args()

    if args.rebuild_all:
        rebuild_all_briefs(args.rebuild_all)
        rebuild_homepage()
        return

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
