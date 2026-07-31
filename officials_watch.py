#!/usr/bin/env python3
"""officials_watch.py — press releases from the officials who represent Tucson,
plus the candidates in races Tucson votes on.

Feeds the daily brief's "What Your Officials Are Saying" section, which sits
just above the weather.

WHY SCRAPE RATHER THAN READ FEEDS
Every one of these offices either has no feed or has an abandoned one, and the
abandoned ones are the dangerous case because they still return HTTP 200:

    ciscomani.house.gov/rss.xml   last item 2026-05-28  (page: 2026-07-24)
    grijalva.house.gov/rss.xml    last item 2026-01-29  (page: 2026-07-22)
    kelly.senate.gov/feed/        last item 2026-06-02  (page: 2026-07-28)
    gallego.senate.gov/feed/      HTTP 503
    azgovernor.gov                no feed
    all three campaign sites      no feed

Reading those feeds would silently inject months-old content into a daily
brief. Scrape the pages. Never add an rss.xml here without re-checking it.

FAIRNESS RULE
Incumbents appear in two capacities and both are labeled:

  role="official"   official government channel (house.gov, senate.gov,
                    azgovernor.gov). What the office is doing.
  role="candidate"  campaign channel. What the campaign is saying.

Races are paired only where an independent rater calls them competitive, so we
are never deciding who deserves coverage — Cook Political Report is. As of
2026-07-29: Arizona governor is a toss-up (Hobbs 44 / Biggs 43) and AZ-06 is a
toss-up (Mendoza 47 / Ciscomani 45). AZ-07 is Solid D at D+13, so Grijalva runs
unpaired. Neither Senate seat is on a 2026 ballot (Kelly 2028, Gallego 2030).

If a rating moves, change `race` here — that is the only knob.

A paired race where only one side posted must SAY so. Silence from one campaign
is not the same as parity, and the synthesis prompt is instructed accordingly.

NOT INCLUDED, deliberately:
  * biggs.house.gov — Biggs is a sitting AZ-05 congressman (East Valley). That
    is neither a Tucson official nor governor-race material, and including it
    would hand him a channel Hobbs has no equivalent of.
  * A Ciscomani campaign channel — none found 2026-07-29. His official releases
    appear under Officials; the CD6 race block will note when his campaign is
    silent rather than quietly running Mendoza alone.

Standing caution: in an election year an incumbent's *official* releases often
carry campaign messaging on the public dime. No rule here catches that. It is a
per-item judgment at review time, and it matters most Aug-Nov.
"""

import re
import sys
from datetime import datetime, timedelta, timezone

import requests
import urllib3

requests.packages.urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    # azgovernor.gov answers 403 to a bare client and 200 with a referer.
    "Referer": "https://www.google.com/",
}
TIMEOUT = 25
DEFAULT_WINDOW_HOURS = 48
MAX_PER_SOURCE = 5

_MONTHS = ("January February March April May June July August September "
           "October November December").split()
_DATE_RE = r"(?:" + "|".join(_MONTHS) + r")\s+\d{1,2},?\s+20\d\d"


def parse_date(s):
    s = re.sub(r"\s+", " ", (s or "").strip()).rstrip(",")
    # %m/%d/%y is juanciscomani.com's Squarespace blog ("7/28/26"); the rest of
    # the sites spell the month out.
    for fmt in ("%B %d, %Y", "%B %d %Y", "%m/%d/%y"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    # ISO-8601 (Bluesky `createdAt`). Sub-second precision runs to nanoseconds,
    # which fromisoformat rejects, so truncate the fraction to microseconds.
    iso = re.sub(r"(\.\d{6})\d+", r"\1", s.replace("Z", "+00:00"))
    try:
        dt = datetime.fromisoformat(iso)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _clean(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = (s.replace("&#039;", "'").replace("&amp;", "&").replace("&quot;", '"')
          .replace("&nbsp;", " ").replace("&#8217;", "’")
          .replace("&#8220;", "“").replace("&#8221;", "”"))
    return re.sub(r"\s+", " ", s).strip()


def _abs(href, base):
    if not href:
        return ""
    if href.startswith("http"):
        return href
    return base.rstrip("/") + "/" + href.lstrip("/")


# --- per-site extractors -----------------------------------------------------
# Each returns [(title, url, date_str)]. Written against markup inspected
# 2026-07-29; if a site redesigns, its extractor returns [] and fetch_all()
# reports the source as empty rather than failing the run.

def _x_house(html, base):
    """house.gov 'evo' CMS — Ciscomani, Grijalva."""
    out = []
    for m in re.finditer(
        r'<div class="h3[^"]*font-weight-bold[^"]*">\s*<a href="([^"]+)"[^>]*>(.*?)</a>\s*</div>'
        r'(.{0,600}?)<div class="col-auto">\s*(' + _DATE_RE + r')', html, re.S):
        out.append((_clean(m.group(2)), _abs(m.group(1), base), m.group(4)))
    return out


def _x_senate(html, base):
    """senate.gov Elementor layout — Kelly, Gallego.

    The date leads: <time> sits in its own post-info section and the headline
    follows in a later heading widget. Kelly's gap runs ~900 chars, Gallego's
    ~200, so the window is generous. Matching title-then-date (the house.gov
    order) silently returns nothing here.
    """
    out = []
    for m in re.finditer(
        r'<time>\s*(' + _DATE_RE + r')\s*</time>(.{0,2000}?)'
        r'<h\d[^>]*>\s*<a href="([^"]+)"[^>]*>(.*?)</a>\s*</h\d>', html, re.S):
        out.append((_clean(m.group(4)), _abs(m.group(3), base), m.group(1)))
    return out


def _x_azgov(html, base):
    """azgovernor.gov news list."""
    out = []
    for m in re.finditer(
        r'<a[^>]+href="([^"]+)"[^>]*class="styleColor">(.*?)</a>(.{0,400}?)'
        r'<div class="date[^"]*">\s*(' + _DATE_RE + r')', html, re.S):
        out.append((_clean(m.group(2)), _abs(m.group(1), base), m.group(4)))
    return out


def _x_mendoza(html, base):
    """joannamendoza.com — <time> then title in a following <p>."""
    out = []
    for m in re.finditer(
        r'href="([^"]+)"[^>]*>\s*<div class="interior">(.{0,300}?)<time>\s*('
        + _DATE_RE + r')\s*</time>(.{0,600}?)</p>\s*<p[^>]*>(.*?)</p>', html, re.S):
        out.append((_clean(m.group(5)), _abs(m.group(1), base), m.group(3)))
    return out


def _x_ciscomani(html, base):
    """juanciscomani.com/news/ — Squarespace blog (added 2026-07-31).

    Each item prints its date TWICE (blog-meta-primary + blog-meta-secondary),
    so this matches forward from the first <time> to that item's
    <h1 class="blog-title"> and lets the duplicate fall inside the gap. The
    bounded {0,1500} span keeps a title-less item from swallowing the next one.
    Dates are M/D/YY here, not the spelled-out month the other sites use.
    """
    out = []
    for m in re.finditer(
        r'<time class="blog-date"[^>]*>\s*(\d{1,2}/\d{1,2}/\d{2})\s*</time>'
        r'.{0,1500}?<h1 class="blog-title">\s*<a href="([^"]+)"[^>]*>(.*?)</a>',
            html, re.S):
        out.append((_clean(m.group(3)), _abs(m.group(2), base), m.group(1)))
    return out


def _x_hobbs(html, base):
    """katiehobbs.org — <h2 class="long-title"> then <p class="byline">."""
    out = []
    for m in re.finditer(
        r'<h2 class="long-title">\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>\s*</h2>'
        r'(.{0,400}?)<p class="byline">\s*(' + _DATE_RE + r')', html, re.S):
        out.append((_clean(m.group(2)), _abs(m.group(1), base), m.group(4)))
    return out


def _x_biggs(html, base):
    """biggsforarizona.com — Bricks builder; title then date, link on a wrapper."""
    out = []
    for m in re.finditer(
        r'href="([^"]+)"[^>]*class="[^"]*home-news-card[^"]*"[^>]*>'
        r'<h\d[^>]*class="[^"]*home-news-title[^"]*"[^>]*>(.*?)</h\d>'
        r'(.{0,400}?)home-news-date[^>]*>\s*(' + _DATE_RE + r')', html, re.S):
        out.append((_clean(m.group(2)), _abs(m.group(1), base), m.group(4)))
    return out


def _bluesky(payload, base):
    """Bluesky author feed (JSON, not HTML) -> the same (title, url, date) rows
    the scrapers return, so fetch_source stays one code path.

    Two exclusions, both deliberate:
      * reposts (`reason` on the feed item) — amplifying someone else is not
        the official's own statement, and attributing it to them would be wrong.
      * replies (`reply` on the record) — conversational fragments that read as
        non-sequiturs out of thread. Their own posts are the statement.
    A post has no title; the text IS the content, so it becomes the title.
    """
    rows = []
    for item in (payload.get("feed") or []):
        if "reason" in item:                       # repost
            continue
        post = item.get("post") or {}
        rec = post.get("record") or {}
        if "reply" in rec:                         # reply in a thread
            continue
        text = _clean(rec.get("text") or "")
        handle = (post.get("author") or {}).get("handle")
        rkey = (post.get("uri") or "").rsplit("/", 1)[-1]
        if not (text and handle and rkey):
            continue
        rows.append((text, f"https://bsky.app/profile/{handle}/post/{rkey}",
                     rec.get("createdAt")))
    return rows


# --- who we watch ------------------------------------------------------------
# role:  "official" = government channel | "candidate" = campaign channel
# race:  None = not on a competitive ballot | else the pairing key
# kind:  "scrape" (default, HTML + x=extractor) | "bluesky" (JSON author feed)
#
# An officeholder's own social feed is an official channel and belongs here, not
# in pipeline/sources.json's news items. Kelly's and Gallego's Bluesky moved out
# of tier_2_officials on 2026-07-30: routed as news they fed the story sections,
# where the model could only treat them as reporting; here they feed 📢, which is
# what "what your officials are saying" means. Their press-release pages remain
# separate entries — same person, two channels, both official.

SOURCES = [
    # ---- Officials (government channels) ----
    dict(name="Sen. Mark Kelly", role="official", race=None, x=_x_senate,
         url="https://www.kelly.senate.gov/newsroom/press-releases/",
         base="https://www.kelly.senate.gov"),
    dict(name="Sen. Ruben Gallego", role="official", race=None, x=_x_senate,
         url="https://www.gallego.senate.gov/newsroom/press-releases/",
         base="https://www.gallego.senate.gov"),
    dict(name="Rep. Juan Ciscomani (R-CD6)", role="official", race=None, x=_x_house,
         url="https://ciscomani.house.gov/media/press-releases",
         base="https://ciscomani.house.gov"),
    dict(name="Rep. Adelita Grijalva (D-CD7)", role="official", race=None, x=_x_house,
         url="https://grijalva.house.gov/media/press-releases",
         base="https://grijalva.house.gov"),
    dict(name="Gov. Katie Hobbs", role="official", race=None, x=_x_azgov,
         url="https://azgovernor.gov/newsroom", base="https://azgovernor.gov"),

    # ---- Officials (their own social channels) ----
    dict(name="Sen. Mark Kelly (Bluesky)", role="official", race=None,
         kind="bluesky", x=_bluesky, base="https://bsky.app",
         url="https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed"
             "?actor=captmarkkelly.bsky.social&limit=10"),
    dict(name="Sen. Ruben Gallego (Bluesky)", role="official", race=None,
         kind="bluesky", x=_bluesky, base="https://bsky.app",
         url="https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed"
             "?actor=gallego.senate.gov&limit=10"),

    # ---- Candidates in Cook-rated competitive races (campaign channels) ----
    dict(name="Katie Hobbs (D)", role="candidate", race="governor", x=_x_hobbs,
         url="https://katiehobbs.org/news/", base="https://katiehobbs.org"),
    dict(name="Andy Biggs (R)", role="candidate", race="governor", x=_x_biggs,
         url="https://biggsforarizona.com/", base="https://biggsforarizona.com"),
    dict(name="JoAnna Mendoza (D)", role="candidate", race="cd6", x=_x_mendoza,
         url="https://joannamendoza.com/news/", base="https://joannamendoza.com"),
    # Added 2026-07-31. A prior note here claimed no Ciscomani campaign channel
    # existed (checked 2026-07-29) — WRONG; juanciscomani.com has an active news
    # section (ciscomaniforcongress.com redirects to it). That miss was worse
    # than a gap: RACE_FIELDS names him, so with no source he was never in
    # `posting` and never in `errors`, which dropped him into `silent` every
    # single day. The brief was being told daily that a candidate who posts
    # several times a week had said nothing. Nothing false reached print (only
    # the 7/31 brief carried a CD6 line, and his latest item predated its 48h
    # window), but it would have within days.
    # LESSON: a missing source and a failed source are not the same thing. The
    # unchecked/silent split only protects sides we actually try to fetch — so
    # every name in RACE_FIELDS needs a source here, or the silence note lies.
    dict(name="Juan Ciscomani (R)", role="candidate", race="cd6", x=_x_ciscomani,
         url="https://juanciscomani.com/news/", base="https://juanciscomani.com"),
]

RACE_LABELS = {"governor": "the governor's race", "cd6": "the CD6 race"}
# Every side of a paired race, whether or not it has a working channel. Used to
# report silence honestly instead of implying parity.
RACE_FIELDS = {"governor": ["Katie Hobbs (D)", "Andy Biggs (R)"],
               "cd6": ["JoAnna Mendoza (D)", "Juan Ciscomani (R)"]}


def fetch_source(src, cutoff):
    try:
        r = requests.get(src["url"], headers=HEADERS, timeout=TIMEOUT, verify=False)
        r.raise_for_status()
    except Exception as e:
        return [], f"{type(e).__name__}: {e}"
    try:
        if src.get("kind") == "bluesky":
            rows = src["x"](r.json(), src["base"])
        else:
            rows = src["x"](re.sub(r"\s+", " ", r.text), src["base"])
    except Exception as e:
        return [], f"parse failed: {type(e).__name__}: {e}"

    items, seen = [], set()
    # SILENT-ZERO GUARD. A live press page or author feed always carries *some*
    # entries, whatever their date. Zero extractor rows therefore means we lost
    # the source — a redesign the regex no longer matches, or an error body
    # served with HTTP 200 — not that the office was quiet. Those two are
    # indistinguishable downstream: both yield an empty block, both make
    # build_block() omit the section, and the brief then reads as normal while
    # the source is silently gone. Same failure shape as the stale-feed problem
    # in this file's header, and the same fix as the Marana DLLC poller's
    # under-100-licenses check: treat an implausible emptiness as breakage.
    #
    # Note this tests rows BEFORE the date filter. Zero *in-window* rows is
    # normal and stays normal; zero rows at all is the alarm.
    if not rows:
        return [], "no entries found on page (layout change or error body?)"

    dated = 0
    for title, url, ds in rows:
        dt = parse_date(ds)
        if dt:
            dated += 1
        if not dt or not title or dt < cutoff or url in seen:
            continue
        seen.add(url)
        items.append(dict(name=src["name"], role=src["role"], race=src["race"],
                          title=title, url=url, date=dt))
        if len(items) >= MAX_PER_SOURCE:
            break

    # Rows found but not one date parsed = the date format moved. Every item
    # would be dropped and the source would read as quiet. This is exactly the
    # Bluesky nanosecond-timestamp bug, caught generically.
    if not dated:
        return [], f"{len(rows)} entries found but no parseable dates (format change?)"
    return items, None


def fetch_all(window_hours=DEFAULT_WINDOW_HOURS, verbose=True):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    items, errors = [], []
    for src in SOURCES:
        got, err = fetch_source(src, cutoff)
        if err:
            errors.append((src["name"], err))
            if verbose:
                print(f"  FAIL  {src['name']}: {err}", file=sys.stderr)
        elif verbose:
            print(f"  ok    {src['name']}: {len(got)} release(s) in window",
                  file=sys.stderr)
        items.extend(got)
    return items, errors


def build_block(items, window_hours=DEFAULT_WINDOW_HOURS, errors=None):
    """Prompt block. Empty string when nothing is in window — the section is
    skipped entirely rather than padded.

    `errors` is the list fetch_all() returns. It matters for fairness, not just
    diagnostics: the CONTESTED note asserts that a named candidate posted
    nothing. If that candidate's scraper FAILED we do not know whether they
    posted, and saying they were silent would be a factual claim about a real
    person manufactured by our own bug. So a failed side suppresses the silence
    note and is reported as unchecked instead.
    """
    if not items:
        return ""
    failed = {name for name, _ in (errors or [])}
    lines = [f"OFFICIAL AND CAMPAIGN RELEASES (last {window_hours}h):", ""]

    officials = [i for i in items if i["role"] == "official"]
    if officials:
        lines.append("OFFICIALS — official government channels:")
        for i in sorted(officials, key=lambda x: x["date"], reverse=True):
            lines.append(f"- {i['name']} | {i['date']:%b %-d} | {i['title']}\n  {i['url']}")
        lines.append("")

    for race, label in RACE_LABELS.items():
        got = [i for i in items if i["race"] == race]
        posting = {i["name"] for i in got}
        lines.append(f"CONTESTED — {label} (campaign channels; rated competitive):")
        if got:
            for i in sorted(got, key=lambda x: x["date"], reverse=True):
                lines.append(f"- {i['name']} | {i['date']:%b %-d} | {i['title']}\n  {i['url']}")
        quiet = [n for n in RACE_FIELDS[race]
                 if not any(n.split(" (")[0] in p for p in posting)]
        # A side whose scraper failed is unknown, not silent — never both.
        unchecked = [n for n in quiet
                     if any(n.split(" (")[0] in f for f in failed)]
        silent = [n for n in quiet if n not in unchecked]
        if silent:
            lines.append(f"- NOTE: nothing in window from {', '.join(silent)}. "
                         f"If you report one side of this race, say the other "
                         f"posted nothing — do not imply parity by omission.")
        if unchecked:
            lines.append(f"- NOTE: could not check {', '.join(unchecked)} today "
                         f"(source fetch failed). Do NOT say they posted nothing — "
                         f"we do not know. If you report the other side, either "
                         f"omit this race or say their channel could not be checked.")
        lines.append("")
    return "\n".join(lines).strip()


if __name__ == "__main__":
    hrs = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_WINDOW_HOURS
    got, errs = fetch_all(window_hours=hrs)
    print(f"\n{len(got)} item(s), {len(errs)} error(s)\n", file=sys.stderr)
    print(build_block(got, hrs, errors=errs) or "(nothing in window — section would be skipped)")
