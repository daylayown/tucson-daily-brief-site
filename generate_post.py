#!/usr/bin/env python3
"""
Generate an HTML blog post from a Tucson Daily Brief markdown briefing file,
and regenerate the index page with all posts listed newest-first.

Usage:
    python generate_post.py path/to/tucson-brief-2026-02-18.md
"""

import sys
import os
import re
from datetime import datetime
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent
POSTS_DIR = SITE_DIR / "posts"


def parse_date_from_filename(filepath: str) -> datetime:
    """Extract date from a filename like tucson-brief-2026-02-18.md."""
    basename = Path(filepath).stem
    match = re.search(r"(\d{4}-\d{2}-\d{2})", basename)
    if not match:
        print(f"Error: could not extract date from filename '{basename}'", file=sys.stderr)
        sys.exit(1)
    return datetime.strptime(match.group(1), "%Y-%m-%d")


def md_to_html(text: str) -> str:
    """Convert briefing markdown to HTML. Handles the specific format of
    Tucson Daily Brief files without any external dependencies."""
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

        # Empty line
        if not line:
            i += 1
            continue

        # Horizontal rule (─── or similar)
        if re.match(r"^[─\-]{3,}$", line):
            html_parts.append("<hr>")
            i += 1
            continue

        # Source citation line (starts with 📰 or 📄)
        if line.startswith("\U0001f4f0") or line.startswith("\U0001f4c4"):
            source_text = line.replace("\U0001f4f0", "").replace("\U0001f4c4", "").strip()
            html_parts.append(f'<p class="source">{escape(source_text)}</p>')
            i += 1
            continue

        # Section header (emoji followed by text, like "🏛️ Government")
        if re.match(r"^[\U0001f300-\U0001faff\u2600-\u27bf\ufe0f]", line) and not line.startswith("**"):
            html_parts.append(f"<h2>{escape(line)}</h2>")
            i += 1
            continue

        # Regular paragraph — collect continuation lines
        para_lines = [line]
        i += 1
        while i < end:
            next_line = lines[i].strip()
            if (not next_line or
                    next_line.startswith("\U0001f4f0") or
                    next_line.startswith("\U0001f4c4") or
                    re.match(r"^[─\-]{3,}$", next_line) or
                    re.match(r"^[\U0001f300-\U0001faff\u2600-\u27bf\ufe0f]", next_line)):
                break
            para_lines.append(next_line)
            i += 1

        para_text = " ".join(para_lines)
        para_html = inline_format(para_text)
        html_parts.append(f"<p>{para_html}</p>")

    return "\n".join(html_parts)


def escape(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def inline_format(text: str) -> str:
    """Handle bold (**text**) within already-safe-ish content."""
    # Escape first, then apply bold
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return text


def extract_lede(text: str) -> str:
    """Pull the first story headline for the index listing."""
    for line in text.strip().split("\n"):
        match = re.search(r"\*\*(.+?)\*\*", line)
        if match:
            headline = match.group(1)
            # Trim trailing period if present
            if headline.endswith("."):
                headline = headline[:-1]
            # Truncate if very long
            if len(headline) > 120:
                headline = headline[:117] + "..."
            return headline
    return ""


def format_date_long(dt: datetime) -> str:
    """February 18, 2026"""
    return dt.strftime("%B %-d, %Y")


def format_date_short(dt: datetime) -> str:
    """Feb 18, 2026"""
    return dt.strftime("%b %-d, %Y")


def post_slug(dt: datetime) -> str:
    """2026-02-18"""
    return dt.strftime("%Y-%m-%d")


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
</head>
<body>
<div class="container">

<header>
<h1><a href="../">Tucson Daily Brief</a></h1>
<p class="tagline">An AI-powered local news pipeline by Nicholas De Leon</p>
</header>

<a class="back-link" href="../">&larr; All briefings</a>

<article id="{slug}">
<p class="post-meta">{format_date_long(date)}</p>
{body_html}
</article>

<footer>
<p>By Nicholas De Leon</p>
<p class="footer-links">
<a href="https://podcasts.apple.com/us/podcast/tucson-daily-brief/id1795533938">Apple Podcasts</a> &middot;
<a href="https://www.youtube.com/@TucsonDailyBrief">YouTube</a>
</p>
</footer>

</div>
</body>
</html>
"""


def render_index(posts: list[dict]) -> str:
    """Render the index page. posts is a list of dicts with keys:
    date, slug, lede — sorted newest-first."""
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
<title>Tucson Daily Brief</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">

<header>
<h1><a href="./">Tucson Daily Brief</a></h1>
<p class="tagline">An AI-powered local news pipeline by Nicholas De Leon</p>
</header>

<ul class="post-list">
{post_list}
</ul>

<footer>
<p>By Nicholas De Leon</p>
<p class="footer-links">
<a href="https://podcasts.apple.com/us/podcast/tucson-daily-brief/id1795533938">Apple Podcasts</a> &middot;
<a href="https://www.youtube.com/@TucsonDailyBrief">YouTube</a>
</p>
</footer>

</div>
</body>
</html>
"""


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
        # Extract lede from the file
        content = f.read_text()
        lede_match = re.search(r'<p class="post-lede"[^>]*>(.+?)</p>', content)
        if not lede_match:
            # Try to get the first <strong> text from the post itself
            strong_match = re.search(r"<strong>(.+?)</strong>", content)
            lede = strong_match.group(1).rstrip(".") if strong_match else ""
        else:
            lede = lede_match.group(1)
        posts.append({"date": dt, "slug": post_slug(dt), "lede": lede})
    return posts


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/tucson-brief-YYYY-MM-DD.md>", file=sys.stderr)
        sys.exit(1)

    md_path = sys.argv[1]
    if not os.path.isfile(md_path):
        print(f"Error: file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    # Parse
    date = parse_date_from_filename(md_path)
    slug = post_slug(date)
    md_text = Path(md_path).read_text()
    body_html = md_to_html(md_text)
    lede = extract_lede(md_text)

    # Write post
    POSTS_DIR.mkdir(exist_ok=True)
    post_file = POSTS_DIR / f"{slug}.html"
    post_file.write_text(render_post(date, body_html))
    print(f"Wrote {post_file}")

    # Rebuild index
    posts = collect_existing_posts()
    # Ensure current post is represented (idempotent — replace if exists)
    posts = [p for p in posts if p["slug"] != slug]
    posts.append({"date": date, "slug": slug, "lede": lede})
    posts.sort(key=lambda p: p["date"], reverse=True)

    index_file = SITE_DIR / "index.html"
    index_file.write_text(render_index(posts))
    print(f"Wrote {index_file}")
    print(f"Index now lists {len(posts)} post(s).")


if __name__ == "__main__":
    main()
