#!/usr/bin/env python3
"""school_news.py — news from the Tucson-metro school districts' own channels.

Feeds the daily brief's 🎓 Schools section, which sits between Development &
Business and What Your Officials Are Saying.

WHY THIS IS A MODULE AND NOT ENTRIES IN pipeline/sources.json
Same reason Kelly's and Gallego's Bluesky feeds moved out of tier_2_officials
on 2026-07-30: a district's own news page is an OFFICIAL CHANNEL, not
reporting. Routed through the news-items block, the model can only read it as
though a newsroom had checked it, and a district press release becomes "TUSD
did X" instead of "the district said X". Routed here it feeds a labeled
section whose prompt rules say what it actually is. Do not move these into
sources.json.

WHY SCRAPE
Of the nine metro districts, exactly one publishes a usable feed:

    Marana USD          Finalsite Atom, /fs/post-manager/boards/3/posts/feed  ✅
    Sunnyside USD       ParentSquare SmartSites — HTML only
    Catalina Foothills   "         "            — HTML only
    Sahuarita USD        "         "            — HTML only
    Amphitheater USD     "         "            — HTML only, list is UNDATED
    TUSD                custom CMS — HTML only, date lives in the URL slug
    Vail USD            Finalsite behind a JS "Client Challenge"  ⛔
    Flowing Wells USD    "         "                             ⛔
    Tanque Verde USD     "         "                             ⛔

Probed 2026-08-04. No RSS autodiscovery link on any of the nine; the four
ParentSquare sites 404 every conventional feed path (/rss, /feed, /rss.xml,
/news-room/rss, /apps/news/rss.jsp). The Finalsite board-feed route was found
by reading their application JS, not by guessing.

THE THREE BLOCKED DISTRICTS
Vail, Flowing Wells and Tanque Verde sit behind Finalsite's Client Challenge —
a JS interstitial served from the CDN edge, identical asset hash on all three,
applied to EVERY path including /robots.txt-adjacent ones and the board-feed
route. Header spoofing does not work (full Chrome header set incl. sec-ch-ua
over HTTP/2 still gets the challenge), and no origin hostname is exposed. This
is the ADE Cloudflare situation from SCHOOL-DATA-FEASIBILITY.md, not the
Marana/OV UA-only WAFs: it needs a real headless browser. They are listed in
SOURCES with status="blocked" ON PURPOSE — build_block() names them in the
prompt so the brief can say the coverage is partial instead of implying nine
districts were checked. Remove the flag if a route opens up; do not delete the
entries.

REPEAT SUPPRESSION
Districts post a few times a week, so a window sized to the brief's daily
cadence would miss anything posted over a weekend. The window is therefore
wide (96h) and repeats are suppressed by a ledger keyed on brief DATE, not on
fetch time: an item is skipped only if it was already offered to an EARLIER
brief. A same-day re-run (run_brief.sh retries five times) still sees its own
items, so a failed brief never loses a story. State lives in
pipeline/.school_news_seen.json (gitignored).

FERPA / EDITORIAL
Never surface anything about an individual student. Districts do publish
student names and photos with parental release on file; that is their consent
to obtain, not ours to reuse, and a brief is a different context than a
district newsletter. The prompt rules in build_block() enforce it, and the
per-item cap keeps a single district from taking over the section.
"""

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 25
DEFAULT_WINDOW_HOURS = 96      # districts post a few times/week; see REPEAT SUPPRESSION
MAX_PER_SOURCE = 4             # no one district takes over the section
MAX_DETAIL_FETCHES = 4         # cap on the Amphitheater per-item date lookups

SEEN_FILE = Path(__file__).resolve().parent / "pipeline" / ".school_news_seen.json"
SEEN_KEEP_DAYS = 45            # prune the ledger so it cannot grow forever

_MONTHS = ("January February March April May June July August September "
           "October November December").split()
_DATE_RE = r"(?:" + "|".join(_MONTHS) + r")\s+\d{1,2},?\s+20\d\d"


# --- helpers -----------------------------------------------------------------

def parse_date(s):
    """Every date shape these platforms emit -> aware datetime, or None."""
    s = re.sub(r"\s+", " ", (s or "").strip()).rstrip(",")
    for fmt in ("%B %d, %Y", "%B %d %Y",
                "%m/%d/%y",      # Amphitheater detail page "Posted Date: 06/15/26"
                "%m%d%y",        # TUSD press-release filename "...-TUSD-080625.pdf"
                "%Y%m%d"):       # TUSD story slug "story-20260722-tusd-solar"
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    iso = re.sub(r"(\.\d{6})\d+", r"\1", s.replace("Z", "+00:00"))
    try:
        dt = datetime.fromisoformat(iso)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _clean(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    for a, b in (("&#039;", "'"), ("&rsquo;", "’"), ("&amp;", "&"), ("&quot;", '"'),
                 ("&nbsp;", " "), ("&#8217;", "’"), ("&ldquo;", "“"), ("&rdquo;", "”"),
                 ("&#8220;", "“"), ("&#8221;", "”"), ("&ndash;", "–"), ("&mdash;", "—"),
                 ("&#8211;", "–"), ("&hellip;", "…")):
        s = s.replace(a, b)
    # ParentSquare pads e-mail-derived post bodies with zero-width joiners.
    s = s.replace("‌", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def _abs(href, base):
    if not href:
        return ""
    if href.startswith("http"):
        return href
    return base.rstrip("/") + "/" + href.lstrip("/")


# --- per-platform extractors --------------------------------------------------
# Each returns [(title, url, date_str, summary)]. date_str may be "" only for a
# source flagged detail_date=True, which fetch_source then resolves per item.
# Written against markup inspected 2026-08-04; a redesign makes an extractor
# return [] and the silent-zero guard in fetch_source reports it as breakage.

def _x_finalsite(payload, base):
    """Finalsite Composer post-board Atom feed (Marana).

    A real feed, so feedparser does the work. Entry summaries lead with an
    <img> and a <br />; _clean strips the markup and the leading whitespace.
    """
    out = []
    for e in feedparser.parse(payload).entries:
        title = _clean(e.get("title", ""))
        link = e.get("link", "")
        when = e.get("published") or e.get("updated") or ""
        if title and link:
            out.append((title, link, when, _clean(e.get("summary", ""))))
    return out


def _x_psq_newsroom(html, base):
    """ParentSquare SmartSites dedicated news page (Sunnyside /news-room).

    <a class="ss-row ss-post-page-row" href="/426106_2?articleID=71374">
      ... <h2 class="ss-post-title">TITLE</h2>
      <div class="ss-post-description">SUMMARY</div>
      ... <div class="ss-post-date">July 28, 2026</div>
    """
    out = []
    for m in re.finditer(
        r'class="ss-row ss-post-page-row"\s+href="([^"]+)"'
        r'.{0,2000}?ss-post-title">(.*?)</h2>'
        r'(.{0,1200}?)ss-post-date">\s*([^<]+?)\s*</div>', html, re.S):
        desc = re.search(r'ss-post-description">(.*?)</div>', m.group(3), re.S)
        out.append((_clean(m.group(2)), _abs(m.group(1), base), m.group(4),
                    _clean(desc.group(1)) if desc else ""))
    return out


def _x_psq_stack(html, base):
    """ParentSquare SmartSites "stack news grid" homepage block
    (Catalina Foothills, Sahuarita).

    Parsed per <article> block rather than with one long regex, because the
    title class differs by theme variant (stack-news-grid-title on CFSD,
    stack-three-two-title on Sahuarita) and the blocks are NOT in date order —
    a pinned item can sit first. Date filtering sorts that out downstream.
    """
    out = []
    for block in re.findall(r'<article id="article\d+".*?</article>', html, re.S):
        href = re.search(r'href="([^"]+)"', block)
        date = re.search(r'news-grid-date[^>]*>\s*([^<]+?)\s*</', block)
        title = re.search(r'-title stack-news-text"[^>]*>\s*(.*?)\s*</', block, re.S)
        desc = re.search(r'news-article-description[^>]*>\s*(.*?)\s*</p>', block, re.S)
        if href and date and title:
            out.append((_clean(title.group(1)), _abs(href.group(1), base),
                        date.group(1), _clean(desc.group(1)) if desc else ""))
    return out


def _x_psq_feed(html, base):
    """ParentSquare SmartSites "psq feed" homepage block (Amphitheater).

    This theme variant prints NO date in the list — the only date is
    "Posted Date: MM/DD/YY" on the article page. So date_str comes back empty
    and the source carries detail_date=True; fetch_source resolves each one.
    Returning items with no date and no resolver would silently drop them all,
    which is why the flag and this docstring exist.
    """
    out = []
    for block in re.findall(r'<article id="article\d+".*?</article>', html, re.S):
        href = re.search(r'href="([^"]+)"', block)
        title = re.search(r'psq_feed_content_title"[^>]*>\s*(.*?)\s*</h\d>', block, re.S)
        desc = re.search(r'psq_feed_content_description"[^>]*>\s*(.*?)\s*</div>',
                         block, re.S)
        if href and title:
            out.append((_clean(title.group(1)), _abs(href.group(1), base), "",
                        _clean(desc.group(1)) if desc else ""))
    return out


def _psq_detail_date(html):
    """"Posted Date: 06/15/26 (01:14 PM)" on a ParentSquare article page."""
    m = re.search(r"Posted Date:\s*(\d{1,2}/\d{1,2}/\d{2})", html)
    return m.group(1) if m else ""


def _x_tusd_stories(html, base):
    """TUSD /stories — a hand-maintained tabbed archive.

    The date is IN THE URL (story-YYYYMMDD-slug), so it is derived, not parsed
    out of prose. Link text is "Headline – July 22, 2026 (Article & Photos)";
    the trailing date and format note are cut so the headline stands alone.
    Some anchors on this page are image links with empty text — deduped by URL,
    non-empty title wins.
    """
    best = {}
    for m in re.finditer(r'<a[^>]+href="([^"]*story-(\d{8})-[^"]*)"[^>]*>(.{0,300}?)</a>',
                         html, re.S):
        url, ymd = m.group(1), m.group(2)
        title = _clean(m.group(3))
        title = re.split(r"\s+[–—-]\s+" + _DATE_RE, title)[0].strip()
        title = re.sub(r"\s*\((?:Article|Video|Photo)[^)]*\)\s*$", "", title).strip()
        if title and len(title) > len(best.get(url, ("",))[0]):
            best[url] = (title, ymd)
    return [(t, _abs(u, base), ymd, "") for u, (t, ymd) in best.items()]


def _x_tusd_press(html, base):
    """TUSD press releases — PDFs on the Communications page.

    Date derived from the filename (NAME-TUSD-MMDDYY.pdf). Very low cadence:
    as of 2026-08-04 the newest was 091225, i.e. eleven months stale. Kept
    anyway so a resumption is caught automatically — it costs one fetch and
    normally contributes zero in-window items.
    """
    out = []
    for m in re.finditer(
        r'<a[^>]+href="([^"]*communications[^"]*?-TUSD-(\d{6})\.pdf)"[^>]*>(.{0,300}?)</a>',
            html, re.S | re.I):
        title = _clean(m.group(3))
        title = re.split(r"\s+-\s+" + _DATE_RE, title)[0].strip()
        title = re.sub(r"\s*\(PDF\)\s*$", "", title).strip()
        if title:
            out.append((title, _abs(m.group(1), base), m.group(2), ""))
    return out


# --- who we watch -------------------------------------------------------------
# name        reader-facing district name; the brief attributes to this
# enroll      approximate enrollment, so the prompt can weigh reach
# url/base    list page and host for relative links
# x           extractor above
# kind        "feed" (bytes -> feedparser) | "scrape" (HTML text)
# detail_date fetch each item's page to resolve its date (Amphitheater only)
# status      "blocked" = known-unreachable, reported as a gap, never fetched
#
# Enrollment figures and the platform map come from SCHOOL-DATA-FEASIBILITY.md.

SOURCES = [
    dict(name="Tucson Unified (TUSD)", enroll="~40,000", kind="scrape",
         x=_x_tusd_stories, base="https://www.tusd1.org",
         url="https://www.tusd1.org/stories"),
    dict(name="Tucson Unified (TUSD) press releases", enroll="~40,000",
         kind="scrape", x=_x_tusd_press, base="https://www.tusd1.org",
         url="https://www.tusd1.org/communications-and-media-relations-dept"),
    dict(name="Sunnyside Unified", enroll="~14,500", kind="scrape",
         x=_x_psq_newsroom, base="https://www.susd12.org",
         url="https://www.susd12.org/news-room"),
    dict(name="Marana Unified", enroll="~12,300", kind="feed",
         x=_x_finalsite, base="https://www.maranausd.org",
         url="https://www.maranausd.org/fs/post-manager/boards/3/posts/feed"),
    dict(name="Amphitheater Public Schools", enroll="~12,400", kind="scrape",
         x=_x_psq_feed, base="https://www.amphi.com",
         url="https://www.amphi.com/", detail_date=True),
    dict(name="Sahuarita Unified", enroll="~6,400", kind="scrape",
         x=_x_psq_stack, base="https://www.susd30.us",
         url="https://www.susd30.us/"),
    dict(name="Catalina Foothills Unified", enroll="~5,200", kind="scrape",
         x=_x_psq_stack, base="https://www.cfsd16.org",
         url="https://www.cfsd16.org/"),

    # ---- known-unreachable; see THE THREE BLOCKED DISTRICTS in the header ----
    dict(name="Vail Unified", enroll="~14,300", status="blocked",
         url="https://www.vailschooldistrict.org/",
         note="Finalsite Client Challenge (JS wall) on every path"),
    dict(name="Flowing Wells Unified", enroll="~5,400", status="blocked",
         url="https://www.flowingwellsschools.org/",
         note="Finalsite Client Challenge (JS wall) on every path"),
    dict(name="Tanque Verde Unified", enroll="~2,200", status="blocked",
         url="https://www.tanqueverdeschools.org/",
         note="Finalsite Client Challenge (JS wall) on every path"),
]


# --- repeat-suppression ledger ------------------------------------------------

def load_seen():
    if not SEEN_FILE.exists():
        return {}
    try:
        return json.loads(SEEN_FILE.read_text())
    except Exception:
        return {}                      # a corrupt ledger costs repeats, not the run


def save_seen(seen, today):
    """Write the ledger, dropping entries older than SEEN_KEEP_DAYS."""
    cutoff = (today - timedelta(days=SEEN_KEEP_DAYS)).isoformat()
    pruned = {u: d for u, d in seen.items() if d >= cutoff}
    try:
        SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        SEEN_FILE.write_text(json.dumps(pruned, indent=2, sort_keys=True))
    except Exception as e:
        print(f"  WARN  could not write {SEEN_FILE.name}: {e}", file=sys.stderr)


# --- fetch --------------------------------------------------------------------

def fetch_source(src, cutoff):
    try:
        r = requests.get(src["url"], headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        return [], f"{type(e).__name__}: {e}"
    try:
        payload = r.content if src.get("kind") == "feed" else re.sub(r"\s+", " ", r.text)
        rows = src["x"](payload, src["base"])
    except Exception as e:
        return [], f"parse failed: {type(e).__name__}: {e}"

    # SILENT-ZERO GUARD (same reasoning as officials_watch.fetch_source): a live
    # district news page always carries some posts, whatever their dates. Zero
    # extractor rows means we lost the source — a redesign, or an error body
    # served as HTTP 200 — not that the district was quiet. Both look identical
    # downstream, so treat implausible emptiness as breakage. Tested BEFORE the
    # date filter: zero in-window rows is normal, zero rows at all is the alarm.
    if not rows:
        return [], "no posts found on page (layout change or error body?)"

    # Amphitheater's list carries no dates; resolve them from the article pages.
    if src.get("detail_date"):
        resolved, budget = [], MAX_DETAIL_FETCHES
        for title, url, ds, summary in rows:
            if ds or budget <= 0:
                resolved.append((title, url, ds, summary))
                continue
            budget -= 1
            try:
                dr = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
                dr.raise_for_status()
                ds = _psq_detail_date(dr.text)
            except Exception:
                ds = ""
            resolved.append((title, url, ds, summary))
        rows = resolved

    items, seen_urls, dated = [], set(), 0
    for title, url, ds, summary in rows:
        dt = parse_date(ds)
        if dt:
            dated += 1
        if not dt or not title or dt < cutoff or url in seen_urls:
            continue
        seen_urls.add(url)
        items.append(dict(district=src["name"], enroll=src.get("enroll", ""),
                          title=title, url=url, date=dt, summary=summary))

    # Rows found but not one date parsed = the date format moved, every item
    # would be dropped, and the district would read as quiet. Caught generically
    # rather than per-platform.
    if not dated:
        return [], f"{len(rows)} posts found but no parseable dates (format change?)"

    items.sort(key=lambda i: i["date"], reverse=True)
    return items[:MAX_PER_SOURCE], None


def fetch_all(window_hours=DEFAULT_WINDOW_HOURS, brief_date=None, verbose=True,
              mark_seen=True):
    """Fetch every reachable district. Returns (items, errors, blocked).

    `brief_date` (a date) drives repeat suppression: an item already offered to
    an EARLIER brief is dropped, an item first seen today is kept even on a
    re-run. Pass mark_seen=False for a dry run so it does not consume items.
    """
    brief_date = brief_date or datetime.now(timezone.utc).date()
    today_str = brief_date.isoformat()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    seen = load_seen()
    items, errors, blocked = [], [], []
    for src in SOURCES:
        if src.get("status") == "blocked":
            blocked.append((src["name"], src.get("note", "unreachable")))
            if verbose:
                print(f"  skip  {src['name']}: {src.get('note','blocked')}",
                      file=sys.stderr)
            continue
        got, err = fetch_source(src, cutoff)
        if err:
            errors.append((src["name"], err))
            if verbose:
                print(f"  FAIL  {src['name']}: {err}", file=sys.stderr)
            continue
        fresh = [i for i in got if seen.get(i["url"], today_str) >= today_str]
        repeats = len(got) - len(fresh)
        if verbose:
            extra = f" ({repeats} already used in an earlier brief)" if repeats else ""
            print(f"  ok    {src['name']}: {len(fresh)} post(s) in window{extra}",
                  file=sys.stderr)
        for i in fresh:
            seen.setdefault(i["url"], today_str)
        items.extend(fresh)

    if mark_seen:
        save_seen(seen, brief_date)
    return items, errors, blocked


# --- prompt block -------------------------------------------------------------

def build_block(items, window_hours=DEFAULT_WINDOW_HOURS, errors=None, blocked=None):
    """Prompt block for the 🎓 Schools section. Empty string when nothing is in
    window, so the section is skipped rather than padded.

    `blocked` is not diagnostics. Three of the nine districts cannot be read at
    all, and a section built from six that reads as "the schools news" would
    quietly assert coverage we do not have. Naming them keeps the brief honest
    the same way officials_watch distinguishes a silent campaign from an
    unchecked one.
    """
    if not items:
        return ""
    lines = [f"SCHOOL DISTRICT ANNOUNCEMENTS (districts' own channels, last "
             f"{window_hours}h):", ""]
    for i in sorted(items, key=lambda x: x["date"], reverse=True):
        lines.append(f"- {i['district']} ({i['enroll']} students) | "
                     f"{i['date']:%b %-d} | {i['title']}")
        if i["summary"]:
            lines.append(f"  SUMMARY: {i['summary'][:400]}")
        lines.append(f"  {i['url']}")
    lines.append("")

    if blocked:
        names = ", ".join(n for n, _ in blocked)
        lines.append(f"NOT CHECKED TODAY (their sites block automated reading): "
                     f"{names}. If you write this section, do NOT imply it covers "
                     f"every district, and never say these districts announced "
                     f"nothing — we did not look.")
    if errors:
        names = ", ".join(n for n, _ in errors)
        lines.append(f"FETCH FAILED TODAY: {names}. Same rule — unchecked, not quiet.")
    return "\n".join(lines).strip()


if __name__ == "__main__":
    hrs = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_WINDOW_HOURS
    got, errs, blk = fetch_all(window_hours=hrs, mark_seen=False)
    print(f"\n{len(got)} item(s), {len(errs)} error(s), {len(blk)} blocked\n",
          file=sys.stderr)
    print(build_block(got, hrs, errors=errs, blocked=blk)
          or "(nothing in window — section would be skipped)")
