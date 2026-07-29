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
    for fmt in ("%B %d, %Y", "%B %d %Y"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
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


# --- who we watch ------------------------------------------------------------
# role:  "official" = government channel | "candidate" = campaign channel
# race:  None = not on a competitive ballot | else the pairing key

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

    # ---- Candidates in Cook-rated competitive races (campaign channels) ----
    dict(name="Katie Hobbs (D)", role="candidate", race="governor", x=_x_hobbs,
         url="https://katiehobbs.org/news/", base="https://katiehobbs.org"),
    dict(name="Andy Biggs (R)", role="candidate", race="governor", x=_x_biggs,
         url="https://biggsforarizona.com/", base="https://biggsforarizona.com"),
    dict(name="JoAnna Mendoza (D)", role="candidate", race="cd6", x=_x_mendoza,
         url="https://joannamendoza.com/news/", base="https://joannamendoza.com"),
    # No Ciscomani campaign channel exists (checked 2026-07-29). The cd6 pair is
    # therefore one-sided; build_block() labels that rather than hiding it.
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
        rows = src["x"](re.sub(r"\s+", " ", r.text), src["base"])
    except Exception as e:
        return [], f"parse failed: {type(e).__name__}: {e}"

    items, seen = [], set()
    for title, url, ds in rows:
        dt = parse_date(ds)
        if not dt or not title or dt < cutoff or url in seen:
            continue
        seen.add(url)
        items.append(dict(name=src["name"], role=src["role"], race=src["race"],
                          title=title, url=url, date=dt))
        if len(items) >= MAX_PER_SOURCE:
            break
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


def build_block(items, window_hours=DEFAULT_WINDOW_HOURS):
    """Prompt block. Empty string when nothing is in window — the section is
    skipped entirely rather than padded."""
    if not items:
        return ""
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
        silent = [n for n in RACE_FIELDS[race]
                  if not any(n.split(" (")[0] in p for p in posting)]
        if silent:
            lines.append(f"- NOTE: nothing in window from {', '.join(silent)}. "
                         f"If you report one side of this race, say the other "
                         f"posted nothing — do not imply parity by omission.")
        lines.append("")
    return "\n".join(lines).strip()


if __name__ == "__main__":
    hrs = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_WINDOW_HOURS
    got, errs = fetch_all(window_hours=hrs)
    print(f"\n{len(got)} item(s), {len(errs)} error(s)\n", file=sys.stderr)
    print(build_block(got, hrs) or "(nothing in window — section would be skipped)")
