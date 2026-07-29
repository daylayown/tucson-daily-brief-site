#!/usr/bin/env python3
"""scrape_azpm.py — AZPM (Arizona Public Media) story index.

WHY THIS EXISTS
AZPM is one of Tucson's major newsrooms and it was invisible to the brief for a
month. It appeared in 12 of 27 June briefs and 0 of 29 in July. Nothing broke
loudly: we read AZPM through their Bluesky account, that account went dormant on
2026-06-27, and a dormant feed returns success with no items forever.

They publish no RSS at all — news.azpm.org declares no feed and every
conventional path 404s — so scraping the index is the only channel.

SHAPE
fetch() matches generate_brief.fetch_rss's contract exactly: returns
(items, err) where each item is {title, summary, link, published}. That way
AZPM flows into the normal items block and the general brief, rather than
becoming a special case.

MARKUP (inspected 2026-07-29)
Story links are /p/{section}/{YYYY}/{M}/{D}/{id}-{slug}/ and the headline anchor
carries class="pollink". The date is in the URL, which is more reliable than any
rendered date — there is no <time> element or datetime attribute on the page.

SECTIONS
Local: azpmnews, newsfeature, news-topical-* (biz, politics, border, edu,
health, nature, sci, arts). Excluded: news-npr, which is national NPR wire and
made up 18 of the ~58 story links on the index when this was written. Ingesting
it would push national content into a Tucson brief. Anything unrecognised is
kept — a new local section should not be silently dropped, which is the failure
mode that cost us the institutional feeds for 34 days.

DATE PRECISION
The URL gives a calendar day, not a timestamp, so items are stamped at Arizona
midnight. That is honest about what we know but means a 36h window can clip a
same-day story; the source is configured with a wider window_hours to compensate.
"""

import html as _html
import re
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

import requests
import urllib3

requests.packages.urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TZ = ZoneInfo("America/Phoenix")
INDEX_URL = "https://news.azpm.org/"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Referer": "https://www.google.com/",
}
TIMEOUT = 25
MAX_ITEMS = 25
EXCLUDE_SECTIONS = {"news-npr"}

# href, section, Y, M, D, then the headline anchor's own text
_STORY = re.compile(
    r'<a\s+href="(/p/([a-z0-9-]+)/(\d{4})/(\d{1,2})/(\d{1,2})/\d+-[^"]*)"'
    r'[^>]*class="[^"]*pollink[^"]*"[^>]*>(.*?)</a>',
    re.S | re.I,
)


def _clean(s):
    # html.unescape rather than a hand-rolled entity table: the first version
    # listed &#039; but not &#39;, and AZPM emits the latter, so headlines
    # shipped as "&#39;Tell us where to look for her&#39;".
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def fetch(src, cutoff):
    """Same contract as generate_brief.fetch_rss: (items, err)."""
    url = (src or {}).get("url") or INDEX_URL
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
        r.raise_for_status()
    except Exception as e:
        return [], f"fetch error: {e}"

    html = re.sub(r"\s+", " ", r.text)
    items, seen = [], set()
    for m in _STORY.finditer(html):
        href, section, y, mo, d, title = m.groups()
        if section in EXCLUDE_SECTIONS:
            continue
        title = _clean(title)
        if not title or href in seen:
            continue
        try:
            pub = datetime.combine(datetime(int(y), int(mo), int(d)).date(),
                                   dtime(0, 0), tzinfo=TZ)
        except ValueError:
            continue
        if pub < cutoff:
            continue
        seen.add(href)
        items.append({
            "title": title,
            # The index carries no excerpt and inventing one ("AZPM azpmnews
            # story") would spend prompt tokens to say nothing. AZPM headlines
            # are descriptive enough to stand alone.
            "summary": "",
            "link": "https://news.azpm.org" + href,
            "published": pub,
        })
        if len(items) >= MAX_ITEMS:
            break

    if not items and not _STORY.search(html):
        # Distinguish "quiet day" from "they redesigned and we are parsing air".
        return [], "no story links matched — index markup may have changed"
    return items, None


if __name__ == "__main__":
    import sys
    from datetime import timedelta, timezone
    hrs = int(sys.argv[1]) if len(sys.argv) > 1 else 72
    got, err = fetch({}, datetime.now(timezone.utc) - timedelta(hours=hrs))
    print(f"error: {err}" if err else f"{len(got)} item(s) in last {hrs}h")
    for i in got:
        print(f"  {i['published']:%Y-%m-%d}  {i['title'][:74]}")
