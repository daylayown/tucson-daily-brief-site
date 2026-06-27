#!/usr/bin/env python3
"""
Around Town — Marana Development Watch

Polls the Town of Marana's public ArcGIS REST server for current and proposed
development projects (commercial, residential, land-use), diffs against prior
state, and publishes new/updated projects as individual pages under the Around
Town section of the site. Marana sibling of dev_watch_orovalley.py.

Source (no auth, no WAF — verified 2026-06-24):
    https://portal.maranaaz.gov/server/rest/services/Hosted/DS_Current_Projects_Live/FeatureServer/0/query

This is the "DS_Projects" layer that backs the town's public Current & Proposed
Projects dashboard. Fields: name, date, number, location, applicant,
description, link, type, status, img, objectid.

Differences from the Oro Valley source (handled below):
  * No edit-timestamp field exists on the layer, so change detection diffs a
    content hash of the display fields rather than a last_edited_date.
  * `date` (Project Date) is populated for only ~45% of rows. Because the feed
    shows each item's date on its card, we never invent one: the feed date comes
    from `date`, else the year+month encoded in the case number (e.g. PRV2112 =>
    2021-12), else the Cloudinary upload timestamp on the project image. Projects
    with none of those signals (mostly long-running subdivisions with no date,
    number, or image) are SKIPPED rather than dated "today" — that both avoids a
    wall of same-dated cards and avoids displaying a fabricated date.
  * `number` (Project Number) is also sparse, but Marana embeds the real project
    number in the Cloudinary `img` path (e.g. .../DPP2305-002_Catalina_Towing.png)
    so we recover it from there when the field is blank.
  * `type` is a coarse development *category* (Commercial / Residential /
    Land Use), not OV's specific case-action type.
  * Marana publishes a project rendering / site-plan image per case (`img`),
    which we show on the page.

The combined Around Town feed (around-town.html) is assembled centrally by
generate_post.rebuild_homepage, which merges these development cases with the
Spotted liquor/new-business filings and the OV cases, newest first.

Idempotency: state in around-town/.dev_state_marana.json (gitignored), keyed by
OBJECTID -> {hash, slug, feed_date}. Unchanged cases are skipped; a changed
content hash re-renders the page in place (same slug).

Usage:
    python dev_watch_marana.py                 # poll + publish new/changed
    python dev_watch_marana.py --dry-run       # show what would happen
    python dev_watch_marana.py --force         # re-render every case
    python dev_watch_marana.py --limit N       # process at most N cases
    python dev_watch_marana.py --no-llm        # skip the Claude summary pass
    python dev_watch_marana.py --rebuild-feed  # just rebuild around-town.html
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from generate_post import (
    ANALYTICS_HTML,
    ARROW_LEFT_SVG,
    SCROLL_TRIGGER_JS,
    detect_topics,
    footer_html,
    post_header_html,
    rebuild_homepage,
    section_nav_html,
    topic_badge_html,
)

# Public base URL for an Around Town page, used in topic alerts.
PUBLIC_BASE = "https://tucsondailybrief.com/around-town"

# --- Config ---
SITE_DIR = Path(__file__).resolve().parent
AROUND_TOWN_DIR = SITE_DIR / "around-town"
STATE_FILE = AROUND_TOWN_DIR / ".dev_state_marana.json"
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

ARCGIS_URL = (
    "https://portal.maranaaz.gov/server/rest/services/"
    "Hosted/DS_Current_Projects_Live/FeatureServer/0/query"
)
# portal.maranaaz.gov is a clean ArcGIS server (no WAF, unlike www.maranaaz.gov),
# but send a normal browser UA to be safe.
BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

MUNICIPALITY = "Marana"
BODY_NAME = "Town of Marana"

# Marana's `type` is a coarse development category. Plain-English gloss shown to
# readers + fed to the summary prompt so the model never has to guess.
CASE_TYPE_GLOSS = {
    "Commercial": "a commercial development project",
    "Residential": "a residential development project",
    "Land Use": "a land-use or zoning change",
}

# Recovers the project number Marana embeds in the Cloudinary image filename,
# e.g. .../Current%20Projects/DPP2305-002_Catalina_Towing.png -> DPP2305-002
IMG_PROJNUM_RE = re.compile(r"/([A-Z]{2,4}\d{4}-\d{3})_")

# Marana case numbers encode the filing year+month: PRV[21][12]-004 -> 2021-12.
PROJNUM_DATE_RE = re.compile(r"^[A-Z]{2,4}(\d{2})(\d{2})-\d{3}$")

# Cloudinary upload timestamp baked into the project image URL:
# .../image/upload/v1659384093/... -> a Unix seconds timestamp.
CLOUD_V_RE = re.compile(r"/upload/v(\d{9,10})/")


# ---------------------------------------------------------------------------
# Fetch + state
# ---------------------------------------------------------------------------

def fetch_cases() -> list[dict]:
    """Query the ArcGIS layer for all projects. Returns a list of attribute dicts."""
    params = urllib.parse.urlencode({
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "false",
        "f": "json",
    })
    req = urllib.request.Request(
        f"{ARCGIS_URL}?{params}",
        headers={"User-Agent": BROWSER_UA, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read())
    if "error" in data:
        raise RuntimeError(f"ArcGIS error: {data['error']}")
    return [f["attributes"] for f in data.get("features", [])]


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(state: dict) -> None:
    AROUND_TOWN_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(v) -> str:
    """ArcGIS string fields are often a single space or None; normalize to ''."""
    return str(v).strip() if v is not None else ""


def slugify(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:50]


def epoch_ms_to_date(ms) -> datetime:
    return datetime.fromtimestamp((ms or 0) / 1000, tz=timezone.utc)


def case_number(a: dict) -> str:
    """Project number — the `number` field, else recovered from the img path."""
    num = _clean(a.get("number"))
    if num:
        return num
    m = IMG_PROJNUM_RE.search(a.get("img") or "")
    return m.group(1) if m else ""


def case_title(a: dict) -> str:
    """Reader-facing title: the project name if present, else type + location."""
    name = _clean(a.get("name"))
    if name:
        return name
    ctype = _clean(a.get("type")) or "Development project"
    loc = _clean(a.get("location"))
    return f"{ctype} — {loc}" if loc else ctype


def case_key(a: dict) -> str:
    """Stable per-row identity. OBJECTID is unique on this layer."""
    return str(a.get("objectid"))


def content_hash(a: dict) -> str:
    """Hash the display-relevant fields so a content change re-renders the page.
    (The layer has no edit-timestamp to diff, so we diff the content itself.)"""
    payload = json.dumps({
        k: _clean(a.get(k)) for k in
        ("name", "type", "status", "location", "applicant",
         "description", "link", "img", "number")
    }, sort_keys=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def grounded_date(a: dict) -> datetime | None:
    """Date that drives the dated slug + the date shown on each Around Town card.
    Only ever derived from real data — never fabricated. Order of preference:
      1. the `date` (Project Date) field
      2. the year+month encoded in the case number (PRV2112-004 -> 2021-12)
      3. the Cloudinary upload timestamp on the project image
    Returns None when none of those exist, in which case the project is skipped.
    All three sources are deterministic, so the slug is stable across runs."""
    floor = datetime(2015, 1, 1, tzinfo=timezone.utc)
    ceil = datetime.now(tz=timezone.utc)

    ms = a.get("date")
    if ms:
        return epoch_ms_to_date(ms)

    m = PROJNUM_DATE_RE.match(case_number(a))
    if m:
        yy, mm = int(m.group(1)), int(m.group(2))
        if 1 <= mm <= 12:
            d = datetime(2000 + yy, mm, 1, tzinfo=timezone.utc)
            if floor <= d <= ceil:
                return d

    cm = CLOUD_V_RE.search(a.get("img") or "")
    if cm:
        d = datetime.fromtimestamp(int(cm.group(1)), tz=timezone.utc)
        if floor <= d <= ceil:
            return d

    return None


def make_slug(a: dict, date: datetime) -> str:
    base = slugify(a.get("name") or a.get("type") or "project")
    oid = a.get("objectid")
    return f"dev-marana-{base}-{date.strftime('%Y-%m-%d')}-{oid}"


def escape_html(text) -> str:
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def case_topics(a: dict) -> list[str]:
    """High-interest topic flags (e.g. data-center) for this case, matched over
    its name, type, and description. See generate_post.TOPIC_DEFS."""
    return detect_topics(_clean(a.get("name")),
                         _clean(a.get("type")),
                         _clean(a.get("description")))


# ---------------------------------------------------------------------------
# Summary (LLM with grounded fallback)
# ---------------------------------------------------------------------------

def fallback_summary(a: dict) -> str:
    """A plain, hedged summary built only from the case fields — no invention."""
    ctype = _clean(a.get("type")) or "development"
    gloss = CASE_TYPE_GLOSS.get(ctype, "a development project")
    desc = _clean(a.get("description")).rstrip(".")
    loc = _clean(a.get("location"))
    where = f" at {loc}" if loc else ""
    first = f"The {BODY_NAME} lists an active {ctype.lower()} project{where} — {gloss}."
    if desc:
        second = f"The project proposes {desc[0].lower()}{desc[1:]}."
    else:
        second = "Details are listed in the town's project record."
    return f"{first} {second}"


def summarize_case(a: dict, use_llm: bool) -> str:
    """Two-sentence, soft-hedged, plain-English summary grounded in the fields."""
    if not use_llm:
        return fallback_summary(a)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return fallback_summary(a)

    ctype = _clean(a.get("type"))
    fields = {k: _clean(a.get(k)) for k in (
        "name", "type", "status", "location", "applicant", "description",
    ) if _clean(a.get(k))}
    num = case_number(a)
    if num:
        fields["project_number"] = num
    prompt = f"""You are writing a 2-sentence, plain-English summary of an active {MUNICIPALITY} development project for a local-news "what's changing around town" feed.

Project data (the ONLY facts you may use):
{json.dumps(fields, indent=2)}

Development category: "{ctype}" = {CASE_TYPE_GLOSS.get(ctype, "a development project")}.

Rules:
- Exactly two sentences. First: what is being built/proposed and where. Second: what stage it's at / what it would do.
- These are projects in the town's development pipeline (proposed or under review), not done deals. Use "proposes," "would," "is planned" — never assert anything is open, finished, or approved.
- Use ONLY the facts above. Do NOT invent applicants, dates, addresses, unit counts, square footage, tenants, or outcomes. If a fact isn't given, leave it out.
- Plain, neutral, non-promotional. No editorializing.

Return only the two sentences, no preamble."""

    body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        CLAUDE_API_URL, data=body,
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
            return content[0]["text"].strip()
    except Exception as e:
        print(f"    WARNING: summary LLM call failed ({e}); using fallback", file=sys.stderr)
    return fallback_summary(a)


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render_case_html(a: dict, summary: str, date: datetime) -> str:
    title = case_title(a)
    ctype = _clean(a.get("type")) or "Development project"
    status = _clean(a.get("status")) or "Active"
    topic_badge = topic_badge_html(case_topics(a))

    facts = []
    if _clean(a.get("name")):
        facts.append(f"<dt>Project</dt><dd>{escape_html(a['name'].strip())}</dd>")
    facts.append(f"<dt>Type</dt><dd>{escape_html(ctype)}</dd>")
    loc = _clean(a.get("location"))
    if loc:
        facts.append(f"<dt>Location</dt><dd>{escape_html(loc)}</dd>")
    appl = _clean(a.get("applicant"))
    if appl:
        facts.append(f"<dt>Applicant</dt><dd>{escape_html(appl)}</dd>")
    num = case_number(a)
    if num:
        facts.append(f"<dt>Project no.</dt><dd>{escape_html(num)}</dd>")
    facts.append(f"<dt>Status</dt><dd>{escape_html(status)}</dd>")
    facts.append(f"<dt>Before</dt><dd>{escape_html(BODY_NAME)}</dd>")
    facts_html = "\n".join(facts)

    desc = _clean(a.get("description"))
    desc_block = f"<p><strong>From the project record:</strong> {escape_html(desc)}</p>" if desc else ""

    # Marana publishes a project rendering / site-plan image per case.
    img = _clean(a.get("img"))
    img_block = ""
    if img.startswith("http"):
        img_block = (
            f'<figure class="filing-image">'
            f'<img src="{escape_html(img)}" alt="{escape_html(title)} — site plan or rendering" loading="lazy">'
            f'<figcaption>Site plan or rendering from the {escape_html(BODY_NAME)} project record.</figcaption>'
            f'</figure>'
        )

    link = _clean(a.get("link"))
    links_html = ""
    if link.startswith("http"):
        links_html = f'<p><a href="{escape_html(link)}">View the town&rsquo;s project record</a></p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape_html(title)} &mdash; Around Town &mdash; Tucson Daily Brief</title>
<link rel="stylesheet" href="../style.css">
{ANALYTICS_HTML}
</head>
<body>

{post_header_html()}

<div class="container">
{section_nav_html(active="around-town", path_prefix="../")}
</div>

<main>
<div class="container container--reading">
<a class="back-link" href="../around-town.html">{ARROW_LEFT_SVG} All of Around Town</a>

<article class="post-page public-record-filing">
<p class="post-meta">Around Town &middot; Development &middot; {escape_html(MUNICIPALITY)}</p>
{topic_badge}
<h1>{escape_html(title)}</h1>
<p class="filing-subtitle">{escape_html(ctype)} &middot; {escape_html(status)}</p>

<dl class="filing-facts">
{facts_html}
</dl>

<p>{escape_html(summary)}</p>

{desc_block}

{img_block}

{links_html}

<hr>

<p class="filing-disclosure"><em>This development project was surfaced automatically from the {escape_html(BODY_NAME)}&rsquo;s public Current &amp; Proposed Projects records. It is in the town&rsquo;s development pipeline &mdash; nothing here is final or approved. Affiliated with this project and want to share more? <a href="mailto:nicholas@daylayown.org">Get in touch</a>.</em></p>

<p class="filing-meta"><em>Generated {datetime.now().strftime('%Y-%m-%d')} by Tucson Daily Brief&rsquo;s Around Town pipeline. AI-assisted summary, grounded in the town&rsquo;s public project record. Source: {escape_html(BODY_NAME)} Development Services{f" (project {escape_html(num)})" if num else ""}.</em></p>
</article>
</div>
</main>

<div class="container">
{footer_html(path_prefix="../")}
</div>

{SCROLL_TRIGGER_JS}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def process(dry_run=False, force=False, limit=None, use_llm=True) -> int:
    AROUND_TOWN_DIR.mkdir(exist_ok=True)
    state = {} if force else load_state()
    new_state = dict(state)

    print("Fetching Marana development projects...")
    cases = fetch_cases()
    print(f"  {len(cases)} project(s) returned")
    if limit:
        cases = cases[:limit]

    published = 0
    skipped_undated = 0
    for a in cases:
        # Skip projects we can't honestly date (no date field, no case-number
        # year/month, no image timestamp) — don't publish a fabricated date.
        date = grounded_date(a)
        if date is None:
            skipped_undated += 1
            continue

        key = case_key(a)
        chash = content_hash(a)
        prior = state.get(key)
        if prior and prior.get("hash") == chash and not force:
            continue  # unchanged

        slug = make_slug(a, date)
        out_path = AROUND_TOWN_DIR / f"{slug}.html"
        title = case_title(a)
        topics = case_topics(a)

        if dry_run:
            action = "update" if prior else "new"
            flag = f"  [TOPIC: {', '.join(topics)}]" if topics else ""
            print(f"  [DRY RUN] {action}: {slug}.html  ({_clean(a.get('type')) or '?'}: {title}){flag}")
            published += 1
            continue

        # If a prior render used a different slug (e.g. a real `date` appeared),
        # remove the stale file.
        if prior and prior.get("slug") and prior["slug"] != slug:
            old = AROUND_TOWN_DIR / f"{prior['slug']}.html"
            if old.exists():
                old.unlink()

        print(f"  Publishing: {slug}.html  ({_clean(a.get('type')) or '?'}: {title})")
        summary = summarize_case(a, use_llm=use_llm)
        out_path.write_text(render_case_html(a, summary, date))
        new_state[key] = {"hash": chash, "slug": slug}
        published += 1

        # Machine-readable alert line for high-interest topics (data centers,
        # etc.). check_agendas.sh greps for these and fires a distinct, louder
        # Telegram than the routine development-count notice. Tab-separated:
        # TOPIC-ALERT <topic-key> <municipality> <title> <url>
        for t in topics:
            print(f"TOPIC-ALERT\t{t}\t{MUNICIPALITY}\t{title}\t{PUBLIC_BASE}/{slug}.html")

    if not dry_run:
        save_state(new_state)
        if published:
            rebuild_homepage()  # reassemble the combined Around Town feed

    if skipped_undated:
        print(f"  (skipped {skipped_undated} undated project(s) — no groundable date)")
    print(f"\nPublished/updated {published} development project(s).")
    return published


def main():
    ap = argparse.ArgumentParser(description="Marana Development Watch (Around Town)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="Re-render every case")
    ap.add_argument("--limit", type=int, help="Process at most N cases")
    ap.add_argument("--no-llm", action="store_true", help="Skip the Claude summary pass")
    ap.add_argument("--rebuild-feed", action="store_true", help="Just rebuild around-town.html")
    args = ap.parse_args()

    if args.rebuild_feed:
        rebuild_homepage()
        return

    process(dry_run=args.dry_run, force=args.force, limit=args.limit,
            use_llm=not args.no_llm)


if __name__ == "__main__":
    main()
