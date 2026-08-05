#!/usr/bin/env python3
"""
Spotted — Marana liquor licenses via the Arizona DLLC database

Marana handles liquor licenses administratively (no council vote), so they
never appear in the agendas that public_record_liquor.py mines. This poller
goes around the agendas entirely: it queries the state Department of Liquor
Licenses and Control's public "Search for issued Licenses" app (POSSE /
Computronix, no auth), enumerates Pima County licenses by license-number
prefix, filters to Marana premises addresses, and diffs against prior state.
Newly appearing licenses publish as Spotted filings.

No AI call anywhere in this pipeline — every field is structured source data
from the DLLC database (derive, don't ask a model).

How the enumeration works (probed + verified 2026-07-28):
  * The search form is driven by POSSE's `datachanges` tuple protocol: POST
    the possedocumentchangeform fields back with functiondef=5,
    paneid=1535035, and a "('C','S0',<columnDefId>,'<value>')" tuple appended
    to the page's datachanges blob. A fresh GET is required before each POST
    (the blob is per-page-load).
  * The Premises field matches the business NAME only (ZIP/city return
    nothing), but the License Number field is a PREFIX match, and AZ license
    numbers encode series + county: legacy 8-digit "SS10NNNN" and modern
    12-digit "0SS10NNNNNNN", where "10" = Pima County. So per series we run
    two prefix queries ("0610" + "00610") and get every Pima license of that
    series. Statuses, dates, licensee, and premises address come back as
    structured spans (LicenseNumber/LicenseType/Licensee/Premise/State/
    EffectiveDate/InactiveDate/ExpirationDate/OriginalIssueDate).
  * Rows are filtered to premises addresses containing "MARANA, AZ". Caveat:
    DLLC premises city is the mailing city, and some businesses inside town
    limits carry TUCSON mailing addresses (e.g. Casa Marana Craft Beer) — v1
    accepts that under-match rather than over-matching into territory the
    agenda pipelines already cover.

First run seeds public-record/.dllc_state_marana.json WITHOUT publishing
(Marana has decades-old licenses — e.g. a 1961 liquor store — that would all
otherwise flood the feed as "new"). After seeding, a license number not in
state = newly issued (or newly licensed premises) → published, if Active.

Usage:
    python public_record_liquor_dllc.py              # poll, diff, publish new
    python public_record_liquor_dllc.py --dry-run    # show what would happen
    python public_record_liquor_dllc.py --seed       # (re)seed state, publish nothing
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

from generate_post import (
    BLUESKY_COMMENTS_HTML,
    ANALYTICS_HTML,
    ARROW_LEFT_SVG,
    SCROLL_TRIGGER_JS,
    SUBSCRIBE_PANEL_HTML,
    footer_html,
    post_header_html,
    seo_head_html,
    section_nav_html,
)
from public_record_liquor import rebuild_index, slugify, escape_html

# --- Config ---
SITE_DIR = Path(__file__).resolve().parent
PUBLIC_RECORD_DIR = SITE_DIR / "public-record"
STATE_FILE = PUBLIC_RECORD_DIR / ".dllc_state_marana.json"

SEARCH_URL = ("https://dllc.azliquor.gov/azdlprod/pub/Default.aspx"
              "?PossePresentation=LicenseSearch")
BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# POSSE column-definition id for the License Number search field (from the
# form's onchange handler; the Premises field is 1535037).
COL_LICENSE_NUMBER = 1535039

# Consumer-facing license series worth a Spotted item when one appears at a
# Marana address. Producers/wholesalers/special-event one-offs excluded.
# Series -> what a new one means, in plain English (used in the page lede).
TARGET_SERIES = {
    "03": "a new microbrewery",
    "06": "a new bar",
    "07": "a new beer and wine bar",
    "09": "a new liquor store",
    "10": "a new beer and wine store",
    "11": "a new hotel/motel bar",
    "12": "a new restaurant serving alcohol",
    "13": "a new farm winery outlet",
    "14": "a new private club",
    "18": "a new craft distillery",
    "19": "a new tasting room",
}

# Pima County's code inside AZ liquor license numbers.
COUNTY_CODE = "10"

# Premises address filter. DLLC city is the mailing city; see module docstring.
CITY_MATCH = "MARANA, AZ"

# Fields POSSE renders per result row as <span id="{Field}_..._sp"> elements.
ROW_FIELDS = ("LicenseNumber", "LicenseType", "Licensee", "Premise", "State",
              "EffectiveDate", "InactiveDate", "ExpirationDate",
              "OriginalIssueDate")


# ---------------------------------------------------------------------------
# DLLC query layer
# ---------------------------------------------------------------------------

def _get_form(session: requests.Session) -> dict:
    """GET the search page; return the possedocumentchangeform fields
    (including the per-page-load datachanges blob the POST must carry)."""
    r = session.get(SEARCH_URL, headers={"User-Agent": BROWSER_UA}, timeout=30)
    r.raise_for_status()
    m = re.search(r"<form id=possedocumentchangeform.*?</form>", r.text, re.DOTALL)
    if not m:
        raise RuntimeError("DLLC search page missing possedocumentchangeform "
                           "(layout change?)")
    fields = {}
    for im in re.finditer(r"<input[^>]*name=\"?([a-zA-Z]+)\"?[^>]*?value=\"?(.*?)\"?\s*/?>",
                          m.group(0), re.DOTALL):
        fields[im.group(1)] = im.group(2).strip()
    return fields


def _search_license_prefix(session: requests.Session, prefix: str) -> str:
    """Run one license-number prefix search; return the result HTML."""
    fields = _get_form(session)
    data = dict(fields)
    tup = f"('C','S0',{COL_LICENSE_NUMBER},'{prefix}')"
    dc = data.get("datachanges", "")
    data["datachanges"] = dc + "," + tup if dc else tup
    data["paneid"] = "1535035"
    data["functiondef"] = "5"
    for k in ("sortcolumns", "changesxml", "changespending", "changesonobject"):
        data.setdefault(k, "")
    data.setdefault("comesfrom", "posse")
    r = session.post(SEARCH_URL, data=data,
                     headers={"User-Agent": BROWSER_UA}, timeout=60)
    r.raise_for_status()
    return r.text


def _parse_rows(html: str) -> list[dict]:
    """Parse result rows via their POSSE field spans.

    Row spans look like <span id="LicenseNumber_1535035_<pane>_<objid>_sp">.
    Group by the trailing object id so each license's fields stay together.
    """
    rows: dict[str, dict] = {}
    for m in re.finditer(
            r'id="([A-Za-z]+)_1535035_\d+_(\d+)_sp"[^>]*>(.*?)</span>',
            html, re.DOTALL):
        field, objid, raw = m.group(1), m.group(2), m.group(3)
        if field not in ROW_FIELDS:
            continue
        val = re.sub(r"<script.*?</script>", "", raw, flags=re.DOTALL)
        val = re.sub(r"<[^>]+>", " ", val)
        val = (val.replace("&amp;", "&").replace("&#39;", "'")
                  .replace("&quot;", '"').replace("&nbsp;", " "))
        val = re.sub(r"\s+", " ", val).strip()
        rows.setdefault(objid, {})[field] = val
    return [r for r in rows.values() if r.get("LicenseNumber")]


def fetch_pima_licenses(series_keys: list[str], pause: float = 1.0) -> list[dict]:
    """Enumerate all Pima County licenses for the target series.

    Two prefix queries per series (legacy 8-digit + modern 12-digit number
    formats), deduped by license number.
    """
    session = requests.Session()
    seen: dict[str, dict] = {}
    for s in series_keys:
        for prefix in (f"{s}{COUNTY_CODE}", f"0{s}{COUNTY_CODE}"):
            html = _search_license_prefix(session, prefix)
            rows = _parse_rows(html)
            fresh = 0
            for row in rows:
                num = row["LicenseNumber"]
                if num not in seen:
                    seen[num] = row
                    fresh += 1
            print(f"  prefix {prefix}: {len(rows)} row(s), {fresh} new")
            time.sleep(pause)
    return list(seen.values())


# ---------------------------------------------------------------------------
# Filtering + state
# ---------------------------------------------------------------------------

def is_marana(row: dict) -> bool:
    return CITY_MATCH in (row.get("Premise") or "").upper()


def premise_name_address(row: dict) -> tuple[str, str]:
    """Split the Premise blob into (business name, address).

    DLLC renders it as NAME then address lines; the address starts at the
    first token that begins with a street number.
    """
    blob = (row.get("Premise") or "").strip()
    m = re.search(r"\s(\d+ .+)$", blob)
    if m:
        return blob[: m.start()].strip(), m.group(1).strip()
    return blob, ""


def series_of(row: dict) -> str:
    """Series key from the LicenseType text, e.g. '009 Liquor Store' -> '09'."""
    m = re.match(r"(\d{2,3})", row.get("LicenseType") or "")
    if not m:
        return ""
    return m.group(1)[-2:]


def type_name(row: dict) -> str:
    """Human license type from the DLLC row, e.g. 'Liquor Store'."""
    return re.sub(r"^\d{2,3}[A-Z]?\s*", "", row.get("LicenseType") or "").strip()


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(state: dict) -> None:
    PUBLIC_RECORD_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render_dllc_filing_html(row: dict, discovered: datetime, page_slug: str) -> str:
    name, address = premise_name_address(row)
    series = series_of(row)
    ltype = type_name(row)
    licensee = row.get("Licensee") or ""
    status = row.get("State") or ""
    effective = row.get("EffectiveDate") or ""
    original = row.get("OriginalIssueDate") or ""
    number = row.get("LicenseNumber") or ""
    meaning = TARGET_SERIES.get(series, "a new liquor license")

    title = f"{name} — Series {series.lstrip('0')} {ltype} (New License)"

    facts = [
        f"<dt>Business</dt><dd>{escape_html(name)}</dd>",
    ]
    if address:
        facts.append(f"<dt>Address</dt><dd>{escape_html(address)}</dd>")
    facts.append(f"<dt>License</dt><dd>Series {escape_html(series.lstrip('0'))} — "
                 f"{escape_html(ltype)} (no. {escape_html(number)})</dd>")
    if licensee:
        facts.append(f"<dt>Licensee</dt><dd>{escape_html(licensee)}</dd>")
    if status:
        facts.append(f"<dt>Status</dt><dd>{escape_html(status)}</dd>")
    if effective:
        facts.append(f"<dt>Effective</dt><dd>{escape_html(effective)}</dd>")
    if original:
        facts.append(f"<dt>Originally issued</dt><dd>{escape_html(original)}</dd>")
    facts.append("<dt>Issued by</dt><dd>Arizona Department of Liquor "
                 "Licenses and Control</dd>")
    facts_html = "\n".join(facts)

    summary = (f"{name} holds a newly listed Series {series.lstrip('0')} "
               f"({ltype}) liquor license at {address or 'a Marana address'} — "
               f"typically {meaning}. The license was surfaced from the state "
               f"liquor database on {discovered.strftime('%B %-d, %Y')}; Marana "
               f"processes liquor applications administratively, so unlike our "
               f"other coverage areas these never appear on a council agenda.")

    description = summary
    if len(description) > 300:
        description = description[:297].rsplit(" ", 1)[0] + "…"
    seo = seo_head_html(
        title=f"{title} — Tucson Daily Brief",
        description=description,
        path=f"public-record/{page_slug}.html",
        og_type="article", published=discovered) + "\n"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape_html(title)} &mdash; Tucson Daily Brief</title>
{seo}<link rel="stylesheet" href="../style.css">
{ANALYTICS_HTML}
</head>
<body>

{post_header_html()}

<div class="container">
{section_nav_html(active="record", path_prefix="../")}
</div>

<main>
<div class="container container--reading">
<a class="back-link" href="../around-town.html">{ARROW_LEFT_SVG} All of Around Town</a>

<article class="post-page public-record-filing">
<p class="post-meta">Around Town &middot; New business &middot; Liquor License &middot; Marana</p>
<h1>{escape_html(name)}</h1>
<p class="filing-subtitle">Series {escape_html(series.lstrip('0'))} {escape_html(ltype)} &middot; New License</p>

<dl class="filing-facts">
{facts_html}
</dl>

<p>{escape_html(summary)}</p>

<p><a href="{escape_html(SEARCH_URL)}">Search the Arizona DLLC license database</a></p>

<hr>

<p class="filing-disclosure"><em>This liquor license was surfaced automatically from the Arizona Department of Liquor Licenses and Control&rsquo;s public license database. Tucson Daily Brief is interested in talking to the people behind new businesses opening in our community &mdash; if you&rsquo;re affiliated with this license and would like to share more about your plans, <a href="mailto:editor@tucsondailybrief.com">get in touch</a>.</em></p>
{BLUESKY_COMMENTS_HTML}
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


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def process(dry_run=False, seed=False) -> int:
    print("Querying Arizona DLLC license database (Pima County enumeration)...")
    licenses = fetch_pima_licenses(list(TARGET_SERIES))
    marana = [r for r in licenses if is_marana(r)]
    print(f"  {len(licenses)} Pima County license(s) across "
          f"{len(TARGET_SERIES)} series; {len(marana)} at {CITY_MATCH} addresses")

    # Refuse to trust an implausibly thin result — a DLLC layout change would
    # otherwise read as "everything disappeared" and, worse, a later recovery
    # run would republish the entire town as "new".
    if len(licenses) < 100:
        print(f"ERROR: only {len(licenses)} license(s) returned — expected "
              f"several hundred. Treating as a source failure; state untouched.",
              file=sys.stderr)
        return 0

    state = load_state()
    first_run = not state

    if seed or first_run:
        if first_run and not seed:
            print("  No prior state — seeding without publishing "
                  "(first run). Future runs will diff against this.")
        for row in marana:
            state[row["LicenseNumber"]] = {
                "status": row.get("State", ""),
                "premise": row.get("Premise", ""),
                "seen": datetime.now().strftime("%Y-%m-%d"),
            }
        if not dry_run:
            save_state(state)
            print(f"  Seeded state with {len(marana)} Marana license(s).")
        else:
            print(f"  [DRY RUN] Would seed state with {len(marana)} license(s).")
        return 0

    discovered = datetime.now()
    published = 0
    for row in marana:
        num = row["LicenseNumber"]
        if num in state:
            # Track status changes silently (a future surface could report
            # closures via Active -> Inactive transitions).
            state[num]["status"] = row.get("State", "")
            continue

        name, _addr = premise_name_address(row)
        status = row.get("State", "")
        state[num] = {
            "status": status,
            "premise": row.get("Premise", ""),
            "seen": discovered.strftime("%Y-%m-%d"),
        }
        if status.lower() != "active":
            print(f"  New but not Active ({status}): {name} ({num}) — "
                  f"recorded, not published")
            continue

        series = series_of(row)
        slug = f"liquor-{slugify(name)}-series-{series.lstrip('0')}-{discovered.strftime('%Y-%m-%d')}"
        out_path = PUBLIC_RECORD_DIR / f"{slug}.html"
        if out_path.exists():
            print(f"  Already published: {slug}.html")
            continue

        if dry_run:
            print(f"  [DRY RUN] Would publish: {slug}.html  ({name}, "
                  f"Series {series.lstrip('0')} {type_name(row)})")
            published += 1
            continue

        PUBLIC_RECORD_DIR.mkdir(exist_ok=True)
        out_path.write_text(render_dllc_filing_html(row, discovered, slug))
        print(f"  Published: {slug}.html")
        published += 1

    if not dry_run:
        save_state(state)
        if published:
            rebuild_index()

    print(f"\nDLLC Marana: published {published} new filing(s)")
    return published


def main():
    ap = argparse.ArgumentParser(
        description="Spotted: Marana liquor licenses via the AZ DLLC database")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--seed", action="store_true",
                    help="(Re)seed state from current data; publish nothing")
    args = ap.parse_args()
    process(dry_run=args.dry_run, seed=args.seed)


if __name__ == "__main__":
    main()
