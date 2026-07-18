#!/usr/bin/env python3
"""Render an "In Depth" feature from a markdown draft into the site.

In Depth is TDB's standalone original-feature section: publish-once, human-
reviewed pieces on the biggest local issues, drawn from TDB's own corpus plus
web research. Mirrors the news-report renderer but its own section + nav slot.

Markdown draft layout (see in-depth/<slug>-draft.md):
    *metadata italics...*
    ---
    # Headline
    **Dek paragraph.**
    ...body, ## sections, [links](url)...
    *part-one kicker*
    ---
    ## Editorial review — status   <- stripped; everything after the 2nd --- is notes

Usage:
    python3 render_indepth.py in-depth/flock-southern-arizona-draft.md --date 2026-06-19
    python3 render_indepth.py --rebuild-index            # just rebuild in-depth.html
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from generate_post import (
    ANALYTICS_HTML,
    seo_head_html,
    derive_description,
    SCROLL_TRIGGER_JS,
    SUBSCRIBE_PANEL_HTML,
    footer_html,
    post_header_html,
    rebuild_homepage,
    section_nav_html,
    site_header_html,
    ARROW_LEFT_SVG,
)

SITE_DIR = Path(__file__).resolve().parent
INDEPTH_DIR = SITE_DIR / "in-depth"


def escape_html(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(text: str) -> str:
    """Inline markdown: links, bold, italic."""
    text = escape_html(text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text


def extract_article(md_text: str) -> str:
    """Return only the article body — the slice between the 1st and 2nd '---'."""
    parts = re.split(r"(?m)^-{3,}\s*$", md_text)
    # parts[0] = metadata header, parts[1] = article, parts[2:] = review notes
    if len(parts) >= 2:
        return parts[1].strip()
    return md_text.strip()


def md_to_html(md_text: str) -> str:
    lines = md_text.strip().split("\n")
    out, i = [], 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("## "):
            out.append(f"<h2>{_inline(s[3:])}</h2>"); i += 1; continue
        if s.startswith("# "):
            out.append(f"<h1>{_inline(s[2:])}</h1>"); i += 1; continue
        if s.startswith("> "):
            q = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                q.append(lines[i].strip()[2:]); i += 1
            out.append(f"<blockquote><p>{_inline(' '.join(q))}</p></blockquote>")
            continue
        # paragraph (gather until blank/heading)
        para = [s]; i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith("#") or nxt.startswith("> "):
                break
            para.append(nxt); i += 1
        out.append(f"<p>{_inline(' '.join(para))}</p>")
    return "\n".join(out)


def extract_title(article_md: str) -> str:
    for line in article_md.split("\n"):
        if line.strip().startswith("# ") and not line.strip().startswith("## "):
            return re.sub(r"\*\*|\*", "", line.strip()[2:]).strip()
    return "In Depth"


def extract_lede(article_md: str) -> str:
    for line in article_md.split("\n"):
        s = line.strip()
        if s.startswith("**") and s.endswith("**"):
            clean = s.strip("*").strip()
            return clean[:157] + "..." if len(clean) > 160 else clean
    return ""


# ---------------------------------------------------------------------------
# Page templates
# ---------------------------------------------------------------------------

def render_indepth_post(title: str, date: datetime, body_html: str, slug: str) -> str:
    from generate_post import news_article_jsonld
    path = f"in-depth/{slug}.html"
    description = derive_description(body_html) or title
    seo = seo_head_html(
        title=f"{title} — Tucson Daily Brief",
        description=description, path=path,
        og_type="article", published=date,
        jsonld=news_article_jsonld(headline=title, path=path,
                                   published=date, description=description))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="published" content="{date.strftime('%Y-%m-%d')}">
<title>{escape_html(title)} &mdash; Tucson Daily Brief</title>
{seo}
<link rel="stylesheet" href="../style.css">
{ANALYTICS_HTML}
</head>
<body>

{post_header_html()}

<div class="container">
{section_nav_html(active="indepth", path_prefix="../")}
</div>

<main>
<div class="container container--reading">
<a class="back-link" href="../in-depth.html">{ARROW_LEFT_SVG} In Depth</a>

<article id="indepth-{slug}" class="post-page">
<p class="post-meta">In Depth &middot; {date.strftime('%B %-d, %Y')}</p>
{body_html}
</article>
</div>
</main>

<div class="container">
<div style="margin-bottom:var(--gap-xl)">{SUBSCRIBE_PANEL_HTML}</div>
{footer_html(path_prefix="../")}
</div>

{SCROLL_TRIGGER_JS}
</body>
</html>
"""


def render_indepth_index(items: list[dict]) -> str:
    if items:
        lis = "\n".join(f"""<li>
<span class="post-date">{it['date'].strftime('%b %-d, %Y')}</span>
<a href="in-depth/{it['slug']}.html">{escape_html(it['title'])}</a>
<p class="post-lede">{escape_html(it['lede'])}</p>
</li>""" for it in items)
    else:
        lis = '<li class="empty">No features yet.</li>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>In Depth &mdash; Tucson Daily Brief</title>
{seo_head_html(
    title="In Depth — Tucson Daily Brief",
    description="Original reporting and in-depth features on Tucson and Southern Arizona civic life, built on public records, meeting transcripts, and government data.",
    path="in-depth.html")}
<link rel="stylesheet" href="style.css">
{ANALYTICS_HTML}
</head>
<body>

{site_header_html()}

<div class="container">
{section_nav_html(active="indepth")}
</div>

<main>
<div class="container container--editorial">
<div style="padding-top:var(--gap-xl);margin-bottom:var(--gap-l)">
<h1 class="section-head">In Depth</h1>
<p class="section-intro">Standalone features on the issues that matter most across Southern Arizona &mdash; reported from TDB&rsquo;s own archive of meetings, filings, and records, with the wider context layered in. Human-reviewed, every one.</p>
</div>

<div style="margin-bottom:var(--gap-xl)">{SUBSCRIBE_PANEL_HTML}</div>

<ul class="post-list">
{lis}
</ul>
</div>
</main>

<div class="container">
{footer_html()}
</div>

{SCROLL_TRIGGER_JS}
</body>
</html>
"""


def collect_features() -> list[dict]:
    """Scan in-depth/*.html for published features (skip drafts)."""
    items = []
    if not INDEPTH_DIR.exists():
        return items
    for f in sorted(INDEPTH_DIR.glob("*.html")):
        content = f.read_text()
        m = re.search(r'<meta name="published" content="(\d{4}-\d{2}-\d{2})">', content)
        date = datetime.strptime(m.group(1), "%Y-%m-%d") if m else datetime.fromtimestamp(f.stat().st_mtime)
        h1 = re.search(r"<h1>(.+?)</h1>", content, re.DOTALL)
        title = re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else f.stem
        lede_m = re.search(r"<p><strong>(.+?)</strong></p>", content, re.DOTALL)
        lede = re.sub(r"<[^>]+>", "", lede_m.group(1)).strip() if lede_m else ""
        if len(lede) > 160:
            lede = lede[:157] + "..."
        items.append({"slug": f.stem, "title": title, "lede": lede, "date": date})
    items.sort(key=lambda x: x["date"], reverse=True)
    return items


def rebuild_index() -> None:
    (SITE_DIR / "in-depth.html").write_text(render_indepth_index(collect_features()))
    print(f"  Rebuilt: in-depth.html ({len(collect_features())} feature(s))")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft", nargs="?", help="path to the -draft.md file")
    ap.add_argument("--date", help="publish date YYYY-MM-DD (default: today)")
    ap.add_argument("--rebuild-index", action="store_true")
    args = ap.parse_args()

    INDEPTH_DIR.mkdir(exist_ok=True)

    if args.rebuild_index and not args.draft:
        rebuild_index()
        rebuild_homepage()
        return 0

    if not args.draft:
        ap.error("provide a draft path or --rebuild-index")

    draft = Path(args.draft)
    md = draft.read_text()
    article_md = extract_article(md)
    title = extract_title(article_md)
    slug = draft.stem.replace("-draft", "")
    date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now()
    body_html = md_to_html(article_md)

    out = INDEPTH_DIR / f"{slug}.html"
    out.write_text(render_indepth_post(title, date, body_html, slug))
    print(f"  Published: {out}")

    rebuild_index()
    rebuild_homepage()
    print("  Rebuilt: index.html (homepage) + briefings.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
