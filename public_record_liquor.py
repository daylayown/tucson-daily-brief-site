#!/usr/bin/env python3
"""
Public Record — Liquor License Pipeline

Scans the agenda-watch/*-full.md reference files produced by the four
agenda mining pipelines, identifies liquor license items, extracts
structured data via Claude, and auto-publishes individual filings to
the Public Record section of the site.

Coverage (v1): Pima County BOS, City of Tucson, Oro Valley Town Council.
Marana is not yet supported — Marana handles liquor licenses
administratively through the Town Clerk and does not agendize them
for council vote. Future expansion: scrape the Marana clerk page directly.

Idempotency: tracks processed source files in public-record/.processed.txt.
A given full agenda reference file is only processed once unless --force.

Usage:
    python public_record_liquor.py                    # Scan and publish new filings
    python public_record_liquor.py --dry-run          # Show what would happen
    python public_record_liquor.py --rebuild-index    # Rebuild index page only
    python public_record_liquor.py --force            # Reprocess all source files

Output:
    public-record/liquor-{slug}.html  # One file per filing
    public-record.html                # Section index
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# --- Config ---
SITE_DIR = Path(__file__).resolve().parent
AGENDA_WATCH_DIR = SITE_DIR / "agenda-watch"
PUBLIC_RECORD_DIR = SITE_DIR / "public-record"
INDEX_PATH = SITE_DIR / "public-record.html"
PROCESSED_LOG = PUBLIC_RECORD_DIR / ".processed.txt"
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Source files we know how to handle. Marana intentionally excluded.
SUPPORTED_PREFIXES = ("pima-county-", "tucson-", "orovalley-")

# Map filename prefix → human-readable body name + governing body URL
SOURCE_META = {
    "pima-county-": {
        "body": "Pima County Board of Supervisors",
        "short": "Pima County BOS",
        "agenda_url": "https://pima.legistar.com/Calendar.aspx",
    },
    "tucson-": {
        "body": "Tucson Mayor & Council",
        "short": "Tucson M&C",
        "agenda_url": "https://www.tucsonaz.gov/Departments/City-Clerk/Documents/Agendas-and-Minutes",
    },
    "orovalley-": {
        "body": "Oro Valley Town Council",
        "short": "Oro Valley Council",
        "agenda_url": "https://www.orovalleyaz.gov/Government/Departments/Town-Clerk",
    },
}


def get_source_meta(filename: str) -> dict | None:
    for prefix, meta in SOURCE_META.items():
        if filename.startswith(prefix):
            return meta
    return None


def load_processed() -> set[str]:
    if not PROCESSED_LOG.exists():
        return set()
    return {line.strip() for line in PROCESSED_LOG.read_text().splitlines() if line.strip()}


def mark_processed(filename: str) -> None:
    PUBLIC_RECORD_DIR.mkdir(exist_ok=True)
    with PROCESSED_LOG.open("a") as f:
        f.write(filename + "\n")


def find_liquor_blocks(full_md_text: str) -> list[str]:
    """Find text windows around 'liquor license' mentions in a full agenda reference.

    Strategy:
    1. Find every line containing "liquor license" (case-insensitive), skipping
       lines that are clearly about one-off special event permits.
    2. Cluster nearby hits — hits within 35 lines of each other are part of the
       same agenda section and become one block.
    3. For each cluster, take a generous window: 5 lines before the first hit
       to 35 lines after the last hit. Tucson is verbose (section header may be
       ~20 lines above the actual data fields), so a wide tail is essential.

    Each block may contain multiple distinct filings (Pima often has 2-3
    consecutive items). Claude handles splitting them in extract_liquor_filings.
    """
    lines = full_md_text.split("\n")
    n = len(lines)

    hits = []
    for i, line in enumerate(lines):
        lower = line.lower()
        if "liquor license" not in lower:
            continue
        # Skip one-off special event permits (Pima format: "Special Event Liquor License")
        if "special event" in lower:
            continue
        hits.append(i)

    if not hits:
        return []

    # Cluster hits into groups where consecutive hits are within 35 lines
    clusters = [[hits[0]]]
    for h in hits[1:]:
        if h - clusters[-1][-1] <= 35:
            clusters[-1].append(h)
        else:
            clusters.append([h])

    blocks = []
    for cluster in clusters:
        start = max(0, cluster[0] - 5)
        end = min(n, cluster[-1] + 35)
        block = "\n".join(lines[start:end]).strip()
        blocks.append(block)

    return blocks


def extract_liquor_filings(block: str, source_label: str, meeting_date: str) -> list[dict]:
    """Send a candidate text block to Claude for structured extraction.

    Returns a list of filings (zero, one, or many — a single block from Pima
    BOS often contains multiple consecutive items). Returns an empty list if
    Claude determines the block has no real filings or if the API call fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return []

    prompt = f"""You are extracting structured data from a {source_label} agenda for {meeting_date}. Below is a text block that mentions liquor licenses. The block may contain ZERO, ONE, or MULTIPLE distinct liquor license filings.

Return a JSON object with this shape:
{{
  "filings": [
    {{
      "is_new_business": true|false,
      "business_name": "string (DBA, e.g. 'Happy Joe's Pizza & Ice Cream')",
      "applicant": "string (person filing, or null)",
      "address": "string (street address — REQUIRED, look carefully through the entire block)",
      "city": "string (city, e.g. 'Tucson', 'Oro Valley')",
      "series": "string (license series number, e.g. '12')",
      "license_type": "string (e.g. 'Restaurant', 'Beer and Wine Bar', 'Beer and Wine Store', 'Hotel/Motel', 'Remote Tasting Room')",
      "action_type": "string (one of: 'New License', 'Person Transfer', 'Location Transfer', 'Person and Location Transfer', 'Renewal', 'Other')",
      "ward": "string or null (e.g. 'Ward 5')",
      "hearing_date": "string or null (date the governing body considers the application, if specified)",
      "summary": "string — write 2 plain sentences in newspaper style. First sentence: who/what/where. Second sentence: what happens next. Be specific. Do not editorialize."
    }}
  ]
}}

Rules:
- Return ONE entry per distinct application. If the same business has TWO different license series filed in parallel, that's TWO filings.
- is_new_business is true ONLY for action_type 'New License'. Transfers and renewals are false.
- SKIP any items that are special event one-off permits, procedural boilerplate, or notes about past liquor decisions.
- The address field is critical — search the entire block for "Address:", street numbers, or cross-streets. Do not return null for address unless it is genuinely absent.
- If the block contains no real filings (e.g., procedural mention only, or "no new applications scheduled"), return {{"filings": []}}.

TEXT BLOCK:

{block}

Return only the JSON object, no other text."""

    request_body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 1500,
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
            if not content or content[0].get("type") != "text":
                return []
            text = content[0]["text"].strip()
            # Strip markdown code fences if Claude added them
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\n?", "", text)
                text = re.sub(r"\n?```$", "", text)
            data = json.loads(text)
            return data.get("filings") or []
    except json.JSONDecodeError as e:
        print(f"  WARNING: Claude returned invalid JSON: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  WARNING: Claude API call failed: {e}", file=sys.stderr)
        return []


def slugify(text: str) -> str:
    """Make a URL-safe slug from arbitrary text."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:60]


def make_filing_slug(data: dict, meeting_date: str) -> str:
    """Generate a deterministic slug for the filing.

    Includes the series number to disambiguate cases where the same business
    files multiple parallel applications (e.g., Turquoise Wine Bar Series 7
    and Series 10 at the same Pima BOS meeting).
    """
    business = slugify(data.get("business_name") or "unknown")
    series = slugify(data.get("series") or "")
    if series:
        return f"liquor-{business}-series-{series}-{meeting_date}"
    return f"liquor-{business}-{meeting_date}"


def escape_html(text: str) -> str:
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def render_filing_html(data: dict, source_meta: dict, meeting_date: str) -> str:
    """Render a single liquor license filing as an HTML page."""
    business = data.get("business_name") or "Liquor License Filing"
    address = data.get("address") or ""
    city = data.get("city") or ""
    series = data.get("series") or ""
    license_type = data.get("license_type") or ""
    action_type = data.get("action_type") or ""
    applicant = data.get("applicant") or ""
    ward = data.get("ward") or ""
    hearing_date = data.get("hearing_date") or meeting_date
    summary = data.get("summary") or ""

    body_name = source_meta["body"]
    agenda_url = source_meta["agenda_url"]

    # Pretty meeting date
    try:
        pretty_date = datetime.strptime(meeting_date, "%Y-%m-%d").strftime("%B %-d, %Y")
    except ValueError:
        pretty_date = meeting_date

    title = f"{business} — Series {series} {license_type} ({action_type})"

    # Build the facts list
    facts = []
    if business:
        facts.append(f"<dt>Business</dt><dd>{escape_html(business)}</dd>")
    if address:
        addr_full = f"{address}, {city}".rstrip(", ")
        facts.append(f"<dt>Address</dt><dd>{escape_html(addr_full)}</dd>")
    if series or license_type:
        type_str = f"Series {series} — {license_type}".strip(" —")
        facts.append(f"<dt>License</dt><dd>{escape_html(type_str)}</dd>")
    if action_type:
        facts.append(f"<dt>Action</dt><dd>{escape_html(action_type)}</dd>")
    if applicant:
        facts.append(f"<dt>Applicant</dt><dd>{escape_html(applicant)}</dd>")
    if ward:
        facts.append(f"<dt>Ward</dt><dd>{escape_html(ward)}</dd>")
    facts.append(f"<dt>Before</dt><dd>{escape_html(body_name)}, {escape_html(pretty_date)}</dd>")

    facts_html = "\n".join(facts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape_html(title)}</title>
<link rel="stylesheet" href="../style.css">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MEYSB9GYF2"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-MEYSB9GYF2');
</script>
</head>
<body>
<div class="container">

<header>
<h1><a href="../">Tucson Daily Brief</a></h1>
<p class="tagline">An AI-powered local news pipeline by Nicholas De Leon</p>
</header>

<a class="back-link" href="../public-record.html">&larr; All public record filings</a>

<article class="public-record-filing">
<p class="post-meta">Public Record &middot; Liquor License Filing</p>
<h1>{escape_html(business)}</h1>
<p class="filing-subtitle">Series {escape_html(series)} {escape_html(license_type)} &middot; {escape_html(action_type)}</p>

<dl class="filing-facts">
{facts_html}
</dl>

<p>{escape_html(summary)}</p>

<p><a href="{escape_html(agenda_url)}">View {escape_html(source_meta['short'])} agenda</a></p>

<hr>

<p class="filing-disclosure"><em>This is a public record filing surfaced automatically from the {escape_html(body_name)} agenda. Tucson Daily Brief is interested in talking to the people behind new businesses opening in our community — if you're affiliated with this filing and would like to share more about your plans, <a href="mailto:nicholas@daylayown.org">get in touch</a>.</em></p>

<p class="filing-meta"><em>Generated {datetime.now().strftime('%Y-%m-%d')} by Tucson Daily Brief Public Record pipeline using {CLAUDE_MODEL}. AI-extracted from a public meeting agenda. Source: {escape_html(body_name)}.</em></p>
</article>

<footer>
<p>By Nicholas De Leon</p>
<p class="footer-links">
<a href="https://podcasts.apple.com/us/podcast/tucson-daily-brief/id1878173070">Apple Podcasts</a> &middot;
<a href="https://www.youtube.com/@tucsondailybrief">YouTube</a> &middot;
<a href="https://www.linkedin.com/in/nicholas-de-leon-3b5b6a9">LinkedIn</a> &middot;
<a href="https://www.instagram.com/daylayownphoto">Instagram</a> &middot;
<a href="mailto:nicholas@daylayown.org">Email</a>
</p>
</footer>

</div>
</body>
</html>
"""


def render_index_html(filings: list[dict]) -> str:
    """Render the public-record.html section index page."""
    items = []
    for f in filings:
        date_str = f["date"].strftime("%b %-d, %Y")
        items.append(f"""<li>
<span class="post-date">{date_str}</span>
<a href="public-record/{f["slug"]}.html">{escape_html(f["title"])}</a>
<p class="post-lede">{escape_html(f["lede"])}</p>
</li>""")

    post_list = "\n".join(items) if items else '<li class="empty">No filings yet.</li>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Public Record &mdash; Tucson Daily Brief</title>
<link rel="stylesheet" href="style.css">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MEYSB9GYF2"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-MEYSB9GYF2');
</script>
</head>
<body>
<div class="container">

<header>
<h1><a href="./">Tucson Daily Brief</a></h1>
<p class="tagline">Public Record &mdash; new businesses, permits, and filings surfaced from public meetings</p>
</header>

<nav class="section-nav">
<a href="./">&larr; Daily briefings</a>
<a href="meeting-watch.html">Meeting Watch &rarr;</a>
<a href="news-reports.html">News Reports &rarr;</a>
</nav>

<p class="section-intro">New restaurants, bars, and businesses go through public meetings before they open. Most never get reported on. Tucson Daily Brief surfaces them automatically from the agendas of the Pima County Board of Supervisors, Tucson Mayor &amp; Council, and Oro Valley Town Council. If you spot a place opening near you, <a href="mailto:nicholas@daylayown.org">tell us about it</a>.</p>

<ul class="post-list">
{post_list}
</ul>

<footer>
<p>By Nicholas De Leon</p>
<p class="footer-links">
<a href="https://podcasts.apple.com/us/podcast/tucson-daily-brief/id1878173070">Apple Podcasts</a> &middot;
<a href="https://www.youtube.com/@tucsondailybrief">YouTube</a> &middot;
<a href="https://www.linkedin.com/in/nicholas-de-leon-3b5b6a9">LinkedIn</a> &middot;
<a href="https://www.instagram.com/daylayownphoto">Instagram</a> &middot;
<a href="mailto:nicholas@daylayown.org">Email</a>
</p>
</footer>

</div>
</body>
</html>
"""


def rebuild_index() -> int:
    """Rebuild public-record.html by scanning all published filings."""
    PUBLIC_RECORD_DIR.mkdir(exist_ok=True)
    filings = []

    for f in PUBLIC_RECORD_DIR.glob("liquor-*.html"):
        # Filename: liquor-{business-slug}-YYYY-MM-DD.html
        m = re.search(r"(\d{4}-\d{2}-\d{2})", f.stem)
        if not m:
            continue
        date = datetime.strptime(m.group(1), "%Y-%m-%d")

        content = f.read_text()
        # Extract business name from <h1> in the article. Unescape HTML entities
        # so render_index_html (which escapes again) doesn't double-encode them.
        title_match = re.search(r'<article[^>]*>.*?<h1>(.+?)</h1>', content, re.DOTALL)
        title = title_match.group(1) if title_match else f.stem
        title = title.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')

        # Extract subtitle/lede from filing-subtitle paragraph
        lede_match = re.search(r'<p class="filing-subtitle">(.+?)</p>', content)
        lede = ""
        if lede_match:
            lede = re.sub(r"<[^>]+>", "", lede_match.group(1))
            lede = lede.replace("&amp;", "&").replace("&middot;", "·").replace("&mdash;", "—").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')

        filings.append({
            "date": date,
            "slug": f.stem,
            "title": title,
            "lede": lede,
        })

    filings.sort(key=lambda p: p["date"], reverse=True)
    INDEX_PATH.write_text(render_index_html(filings))
    print(f"  Rebuilt index: {INDEX_PATH} ({len(filings)} filing(s))")
    return len(filings)


def process_source_file(
    source_file: Path,
    dry_run: bool = False,
) -> int:
    """Extract and publish liquor filings from a single -full.md file.

    Returns the number of new filings published.
    """
    filename = source_file.name
    source_meta = get_source_meta(filename)
    if not source_meta:
        return 0

    # Extract meeting date from filename
    m = re.search(r"(\d{4}-\d{2}-\d{2})", source_file.stem)
    if not m:
        print(f"  WARN: no date in filename: {filename}")
        return 0
    meeting_date = m.group(1)

    text = source_file.read_text()
    blocks = find_liquor_blocks(text)
    if not blocks:
        return 0

    print(f"  {filename}: found {len(blocks)} candidate block(s)")
    published = 0

    for i, block in enumerate(blocks, 1):
        print(f"    Block {i}/{len(blocks)}: extracting via Claude...")
        filings = extract_liquor_filings(block, source_meta["body"], meeting_date)
        if not filings:
            print(f"    Block {i}: no real filings extracted, skipping")
            continue

        print(f"    Block {i}: extracted {len(filings)} filing(s)")
        for data in filings:
            slug = make_filing_slug(data, meeting_date)
            out_path = PUBLIC_RECORD_DIR / f"{slug}.html"

            if out_path.exists():
                print(f"      Already published as {slug}.html, skipping")
                continue

            if dry_run:
                print(f"      [DRY RUN] Would publish: {slug}.html")
                print(f"               Business: {data.get('business_name')}")
                print(f"               Series {data.get('series')} {data.get('license_type')} ({data.get('action_type')})")
                print(f"               Address: {data.get('address')}, {data.get('city')}")
                published += 1
                continue

            PUBLIC_RECORD_DIR.mkdir(exist_ok=True)
            out_path.write_text(render_filing_html(data, source_meta, meeting_date))
            print(f"      Published: {out_path.name}")
            published += 1

    return published


def scan_and_publish(dry_run: bool = False, force: bool = False, limit: int | None = None) -> int:
    """Scan all -full.md files in agenda-watch/, publish new liquor filings."""
    if not AGENDA_WATCH_DIR.exists():
        print(f"agenda-watch directory not found: {AGENDA_WATCH_DIR}")
        return 0

    processed = set() if force else load_processed()
    files = sorted(AGENDA_WATCH_DIR.glob("*-full.md"))

    # Filter to supported municipalities
    files = [f for f in files if any(f.name.startswith(p) for p in SUPPORTED_PREFIXES)]

    if limit:
        files = files[:limit]

    print(f"Scanning {len(files)} agenda reference file(s)...")

    total_published = 0
    files_processed = 0

    for source_file in files:
        if source_file.name in processed:
            continue
        files_processed += 1
        published = process_source_file(source_file, dry_run=dry_run)
        total_published += published

        if not dry_run:
            mark_processed(source_file.name)

    print(f"\nProcessed {files_processed} new file(s), published {total_published} new filing(s)")

    if total_published > 0 and not dry_run:
        rebuild_index()

    return total_published


def main():
    parser = argparse.ArgumentParser(description="Public Record liquor license pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be published, don't write files")
    parser.add_argument("--rebuild-index", action="store_true", help="Rebuild public-record.html index from existing filings")
    parser.add_argument("--force", action="store_true", help="Reprocess all source files, ignoring .processed.txt")
    parser.add_argument("--limit", type=int, help="Process at most N source files (for testing)")
    args = parser.parse_args()

    if args.rebuild_index:
        rebuild_index()
        return

    count = scan_and_publish(dry_run=args.dry_run, force=args.force, limit=args.limit)
    sys.exit(0 if count >= 0 else 1)


if __name__ == "__main__":
    main()
