#!/usr/bin/env python3
"""
Around Town — Oro Valley Development Watch

Polls the Town of Oro Valley's public ArcGIS REST server for active
development cases (rezonings, General Plan amendments, variances,
conditional use permits, development plans, design review), diffs against
prior state, and publishes new/updated cases as individual pages under the
Around Town section of the site.

Source (no auth, no WAF — verified 2026-06-24):
    https://gismap.orovalleyaz.gov/gismap/rest/services/CED-Planning/Development_Cases/MapServer/0/query

Each case becomes around-town/{slug}.html. The combined Around Town feed
(around-town.html) is assembled centrally by generate_post.rebuild_homepage,
which merges these development cases with the Spotted liquor/new-business
filings, newest first.

Idempotency: state in around-town/.dev_state.json (gitignored), keyed by
CaseNumber → last_edited epoch + current slug. Unchanged cases are skipped;
a changed last_edited_date re-renders (and renames) the page.

This is the OV-first instance of the pattern; a Marana sibling can follow the
same shape once a Marana development source is identified.

Usage:
    python dev_watch_orovalley.py                 # poll + publish new/changed
    python dev_watch_orovalley.py --dry-run       # show what would happen
    python dev_watch_orovalley.py --force         # re-render every case
    python dev_watch_orovalley.py --limit N       # process at most N cases
    python dev_watch_orovalley.py --no-llm        # skip the Claude summary pass
    python dev_watch_orovalley.py --rebuild-feed  # just rebuild around-town.html
"""

import argparse
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
    SUBSCRIBE_PANEL_HTML,
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
STATE_FILE = AROUND_TOWN_DIR / ".dev_state.json"
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

ARCGIS_URL = (
    "https://gismap.orovalleyaz.gov/gismap/rest/services/"
    "CED-Planning/Development_Cases/MapServer/0/query"
)
# orovalleyaz.gov sits behind an Akamai WAF, but the GIS host only needs a
# normal browser UA (not the full header set). Send one to be safe.
BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

MUNICIPALITY = "Oro Valley"
BODY_NAME = "Town of Oro Valley"

# Plain-English gloss per case type — shown to readers + fed to the summary
# prompt so the model never has to guess what a case type means.
CASE_TYPE_GLOSS = {
    "Rezoning": "a request to change how a piece of land is zoned",
    "General Plan Amendment": "a proposed change to the town's long-range land-use plan",
    "Zoning Variance": "a request for an exception to the zoning rules",
    "Conditional Use Permit": "a request to allow a specific use that needs special approval",
    "Development Plan": "a plan for how a site would be built out",
    "Architecture": "design review of a project's buildings and appearance",
    "Site Design": "design review of a project's site layout",
}


# ---------------------------------------------------------------------------
# Fetch + state
# ---------------------------------------------------------------------------

def fetch_cases() -> list[dict]:
    """Query the ArcGIS layer for all cases. Returns a list of attribute dicts."""
    params = urllib.parse.urlencode({
        "where": "1=1",
        "outFields": "*",
        "orderByFields": "last_edited_date DESC",
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

def slugify(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:50]


def epoch_ms_to_date(ms) -> datetime:
    return datetime.fromtimestamp((ms or 0) / 1000, tz=timezone.utc)


def case_title(a: dict) -> str:
    """Reader-facing title: the project name if present, else type + location."""
    name = (a.get("Common_Name") or "").strip()
    if name:
        return name
    ctype = (a.get("Case_Type") or "Development case").strip()
    loc = (a.get("Location") or a.get("Property_Address") or "").strip()
    return f"{ctype} — {loc}" if loc else ctype


def case_key(a: dict) -> str:
    """Stable per-row identity. CaseNumber is NOT unique (e.g. two GPA cases
    share 2201373), so key off the ArcGIS GlobalID, falling back to OBJECTID."""
    return str(a.get("GlobalID") or a.get("OBJECTID"))


def make_slug(a: dict, date: datetime) -> str:
    base = slugify(a.get("Common_Name") or a.get("Case_Type") or "case")
    oid = a.get("OBJECTID")
    return f"dev-{base}-{date.strftime('%Y-%m-%d')}-{oid}"


def escape_html(text) -> str:
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def case_topics(a: dict) -> list[str]:
    """High-interest topic flags (e.g. data-center) for this case, matched over
    its name, type, and description. See generate_post.TOPIC_DEFS."""
    return detect_topics(a.get("Common_Name") or a.get("Subdivision_Name") or "",
                         a.get("Case_Type") or "",
                         a.get("Case_Description") or "")


# ---------------------------------------------------------------------------
# Summary (LLM with grounded fallback)
# ---------------------------------------------------------------------------

def fallback_summary(a: dict) -> str:
    """A plain, hedged summary built only from the case fields — no invention."""
    ctype = (a.get("Case_Type") or "development case").strip()
    gloss = CASE_TYPE_GLOSS.get(ctype, "a development case")
    desc = (a.get("Case_Description") or "").strip().rstrip(".")
    loc = (a.get("Location") or a.get("Property_Address") or "").strip()
    where = f" at {loc}" if loc else ""
    first = f"The {BODY_NAME} has an active {ctype.lower()} case on file{where} — {gloss}."
    second = f"The application proposes {desc[0].lower()}{desc[1:]}." if desc else \
        "Details are listed in the town's case record."
    return f"{first} {second}"


def summarize_case(a: dict, use_llm: bool) -> str:
    """Two-sentence, soft-hedged, plain-English summary grounded in the fields."""
    if not use_llm:
        return fallback_summary(a)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return fallback_summary(a)

    ctype = a.get("Case_Type") or ""
    fields = {k: a.get(k) for k in (
        "CaseNumber", "Common_Name", "Case_Description", "Case_Type",
        "Case_Status", "Location", "Property_Address", "Applicant_Name",
    ) if a.get(k)}
    prompt = f"""You are writing a 2-sentence, plain-English summary of an active {MUNICIPALITY} development case for a local-news "what's changing around town" feed.

Case data (the ONLY facts you may use):
{json.dumps(fields, indent=2)}

Case-type meaning: "{ctype}" = {CASE_TYPE_GLOSS.get(ctype, "a development case")}.

Rules:
- Exactly two sentences. First: what is being proposed and where. Second: what stage it's at / what it would do.
- These are PROPOSALS under review, not done deals. Use "proposes," "would," "is seeking" — never assert anything is approved or happening.
- Use ONLY the facts above. Do NOT invent applicants, dates, addresses, project details, or outcomes. If a fact isn't given, leave it out.
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
    ctype = (a.get("Case_Type") or "Development case").strip()
    status = (a.get("Case_Status") or "Active").strip()
    pretty_date = date.strftime("%B %-d, %Y")
    topic_badge = topic_badge_html(case_topics(a))

    facts = []
    if a.get("Common_Name"):
        facts.append(f"<dt>Project</dt><dd>{escape_html(a['Common_Name'])}</dd>")
    facts.append(f"<dt>Type</dt><dd>{escape_html(ctype)}</dd>")
    loc = a.get("Location") or a.get("Property_Address")
    if loc:
        facts.append(f"<dt>Location</dt><dd>{escape_html(loc)}</dd>")
    if a.get("Subdivision_Name"):
        facts.append(f"<dt>Subdivision</dt><dd>{escape_html(a['Subdivision_Name'])}</dd>")
    if a.get("Applicant_Name"):
        facts.append(f"<dt>Applicant</dt><dd>{escape_html(a['Applicant_Name'])}</dd>")
    if a.get("CaseNumber"):
        facts.append(f"<dt>Case no.</dt><dd>{escape_html(a['CaseNumber'])}</dd>")
    facts.append(f"<dt>Status</dt><dd>{escape_html(status)}</dd>")
    facts.append(f"<dt>Before</dt><dd>{escape_html(BODY_NAME)}</dd>")
    facts_html = "\n".join(facts)

    desc = (a.get("Case_Description") or "").strip()
    desc_block = f"<p><strong>From the case record:</strong> {escape_html(desc)}</p>" if desc else ""

    outreach = (a.get("Outreach_Link") or "").strip()
    links = []
    if outreach:
        links.append(f'<a href="{escape_html(outreach)}">View the town&rsquo;s case story map</a>')
    if links:
        links_html = "<p>" + " &middot; ".join(links) + "</p>"
    else:
        links_html = ""

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

{links_html}

<hr>

<p class="filing-disclosure"><em>This development case was surfaced automatically from the {escape_html(BODY_NAME)}&rsquo;s public planning records. It is a proposal under review &mdash; nothing here is final or approved. Affiliated with this project and want to share more? <a href="mailto:nicholas@daylayown.org">Get in touch</a>.</em></p>

<p class="filing-meta"><em>Generated {datetime.now().strftime('%Y-%m-%d')} by Tucson Daily Brief&rsquo;s Around Town pipeline. AI-assisted summary, grounded in the town&rsquo;s public case record. Source: {escape_html(BODY_NAME)} planning (case {escape_html(a.get('CaseNumber') or 'n/a')}).</em></p>
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

    print("Fetching Oro Valley development cases...")
    cases = fetch_cases()
    print(f"  {len(cases)} case(s) returned")
    if limit:
        cases = cases[:limit]

    published = 0
    for a in cases:
        key = case_key(a)
        last_edited = a.get("last_edited_date") or a.get("created_date") or 0
        prior = state.get(key)
        if prior and prior.get("last_edited") == last_edited and not force:
            continue  # unchanged

        date = epoch_ms_to_date(last_edited)
        slug = make_slug(a, date)
        out_path = AROUND_TOWN_DIR / f"{slug}.html"
        title = case_title(a)
        topics = case_topics(a)

        if dry_run:
            action = "update" if prior else "new"
            flag = f"  [TOPIC: {', '.join(topics)}]" if topics else ""
            print(f"  [DRY RUN] {action}: {slug}.html  ({a.get('Case_Type')}: {title}){flag}")
            published += 1
            continue

        # A changed last_edited_date means a new dated slug — remove the stale file.
        if prior and prior.get("slug") and prior["slug"] != slug:
            old = AROUND_TOWN_DIR / f"{prior['slug']}.html"
            if old.exists():
                old.unlink()

        print(f"  Publishing: {slug}.html  ({a.get('Case_Type')}: {title})")
        summary = summarize_case(a, use_llm=use_llm)
        out_path.write_text(render_case_html(a, summary, date))
        new_state[key] = {"last_edited": last_edited, "slug": slug}
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

    print(f"\nPublished/updated {published} development case(s).")
    return published


def main():
    ap = argparse.ArgumentParser(description="Oro Valley Development Watch (Around Town)")
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
