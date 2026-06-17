#!/usr/bin/env python3
"""Render the live Heat/Water/Power panel into responsiveness.html from the
archived utility data in data/outages.sqlite.

The page is a static GitHub Pages file, so this bakes a snapshot of the current
numbers between the <!-- WATER:START --> / <!-- WATER:END --> markers. Re-run
(and commit) to refresh. For now: run manually or on a daily cadence — NOT on
every 30-min poll (that would churn the git history).

Usage:
  python3 render_responsiveness.py
  python3 render_responsiveness.py --db data/outages.sqlite
"""

import argparse
import html
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SITE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = SITE_DIR / "data" / "outages.sqlite"
PAGE = SITE_DIR / "responsiveness.html"
TZ = ZoneInfo("America/Phoenix")  # MST, no DST

START = "<!-- WATER:START -->"
END = "<!-- WATER:END -->"

RULE_SVG = (
    '<svg class="section-head__rule" width="280" height="14" viewBox="0 0 280 14" '
    'fill="none" aria-hidden="true">'
    '<path d="M2 8 C 30 4, 80 12, 130 7 S 230 4, 278 9" stroke="currentColor" '
    'stroke-width="2.5" stroke-linecap="round" fill="none"/></svg>'
)


def fmt_date(iso, fmt="%b %-d, %Y"):
    if not iso:
        return ""
    try:
        return datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").strftime(fmt)
    except ValueError:
        return ""


def stats(conn):
    q = lambda s, *a: conn.execute(s, a).fetchone()
    total = q("SELECT COUNT(*) FROM water_advisory")[0]
    open_n = q("SELECT COUNT(*) FROM water_advisory WHERE lifted_at IS NULL")[0]
    unplanned = q("SELECT COUNT(*) FROM water_advisory WHERE advise_type='Unplanned Outage'")[0]
    # earliest *real* advisory (skip the 1970 epoch artifact)
    since_iso = q("SELECT MIN(advise_start_iso) FROM water_advisory "
                  "WHERE advise_start_ms > 1000000000000")[0]
    open_rows = conn.execute(
        """SELECT advise_type, description, advise_start_iso, centroid_lat, centroid_lon
           FROM water_advisory WHERE lifted_at IS NULL
           ORDER BY advise_start_iso DESC""").fetchall()
    return {
        "total": total,
        "open": open_n,
        "unplanned_pct": round(unplanned / total * 100) if total else 0,
        "since": fmt_date(since_iso, "%B %Y"),
        "open_rows": open_rows,
    }


def active_list(rows):
    if not rows:
        return ('<p style="font-family:\'Newsreader\',serif;color:#5c4a3f;'
                'margin-top:var(--gap-l)">No active advisories at last check &mdash; '
                'the archive below holds the full history.</p>')
    items = []
    for r in rows:
        atype = html.escape(r["advise_type"] or "Advisory")
        desc = html.escape((r["description"] or "").strip())
        if len(desc) > 180:
            desc = desc[:177] + "…"
        since = fmt_date(r["advise_start_iso"])
        since_html = (f'<span style="font-family:\'Newsreader\',serif;color:#8c6a52;'
                      f'font-size:.9rem"> &middot; since {since}</span>') if since else ""
        items.append(
            '<li style="padding:14px 0;border-top:1px solid #e8dfd1">'
            f'<span style="font-family:\'Fraunces\',serif;font-variation-settings:\'WONK\' 1;'
            f'font-weight:600;color:#c75b39">{atype}</span>'
            f'<span style="font-family:\'Newsreader\',serif;color:#3d3029"> &mdash; {desc}</span>'
            f'{since_html}</li>'
        )
    return (
        '<div style="margin-top:var(--gap-l)">'
        '<h3 style="font-family:\'Fraunces\',serif;font-variation-settings:\'WONK\' 1;'
        'text-transform:uppercase;letter-spacing:.12em;font-size:.8rem;color:#8c6a52;'
        'margin:0 0 4px">Active right now</h3>'
        '<ul style="list-style:none;margin:0;padding:0">' + "".join(items) + "</ul></div>"
    )


def render_section(s, updated):
    return f"""{START}
<section style="padding:var(--gap-l) 0 var(--gap-xl)">
<h2 class="section-head">Heat &middot; Water &middot; Power
{RULE_SVG}
</h2>
<p class="coming-soon-body" style="margin-top:0">In the desert, a water advisory or a power outage isn&rsquo;t an inconvenience &mdash; in a 108&deg; July it is a safety event. These utilities publish what is happening <em>now</em> but keep no public history. So TDB keeps it. <strong>Water is live; power and 311 follow.</strong></p>
<div class="dash-grid">
<div class="dash-card"><p class="dash-card__eyebrow">Tucson Water &mdash; advisories active now</p><p class="dash-card__value">{s['open']}</p><p class="dash-card__caption">Service disruptions Tucson Water is reporting across its system right now.</p></div>
<div class="dash-card"><p class="dash-card__eyebrow">In the archive since {s['since']}</p><p class="dash-card__value">{s['total']:,}</p><p class="dash-card__caption">Advisories TDB has recorded &mdash; a history Tucson Water itself does not publish.</p></div>
<div class="dash-card"><p class="dash-card__eyebrow">Unplanned outages</p><p class="dash-card__value">{s['unplanned_pct']}%</p><p class="dash-card__caption">Of the archive; the rest is planned work, pressure events, and discolored-water reports.</p></div>
</div>
{active_list(s['open_rows'])}
<p style="font-family:'Newsreader',serif;font-size:.88rem;color:#8c6a52;margin-top:var(--gap-l)">Updated {updated}. Source: City of Tucson Water public advisory feed, archived by TDB.</p>
</section>
{END}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args()

    if not args.db.exists():
        print(f"ERROR: {args.db} not found. Run poll_tucson_water.py first.", file=sys.stderr)
        return 1
    conn = sqlite3.connect(str(args.db))
    conn.row_factory = sqlite3.Row
    s = stats(conn)
    conn.close()

    updated = datetime.now(TZ).strftime("%b %-d, %Y, %-I:%M %p %Z")
    section = render_section(s, updated)

    page = PAGE.read_text()
    if START not in page or END not in page:
        print(f"ERROR: markers {START} / {END} not found in {PAGE.name}", file=sys.stderr)
        return 1
    new_page = re.sub(re.escape(START) + r".*?" + re.escape(END), section, page, flags=re.DOTALL)
    PAGE.write_text(new_page)
    print(f"Rendered Heat/Water/Power panel: {s['open']} active, "
          f"{s['total']:,} archived. Updated {updated}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
