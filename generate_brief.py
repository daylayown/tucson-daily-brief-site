#!/usr/bin/env python3
"""generate_brief.py — deterministic Tucson Daily Brief generator.

Replaces the OpenClaw 6 AM briefing agent. The agent was an agent runtime whose
agency we had already designed away (sources.json is the sole source of truth,
TUCSON-BRIEF.md pins the format and save path), and the agent loop introduced
three recurring failure modes, all from using an agent for deterministic work:

  1. mid-run context compaction silently dropped heavy feeds before synthesis,
     so the brief collapsed onto whichever 2 sources happened to survive;
  2. the agent occasionally saved the brief to the wrong path, stalling the
     whole 6:10 podcast/blog pipeline;
  3. holding every raw feed in one long context bloated the run.

Here the model does exactly ONE thing — read the day's already-fetched items and
write the brief (rank / select / dedupe / prose). Everything else is Python:

  * fetch every source in sources.json (RSS / Bluesky / NWS) — nothing can be
    silently dropped, because Python guarantees every feed reaches the prompt;
  * filter to a recent time window, dedupe;
  * read EDITOR-TIPS.md and include in-window tips;
  * one bounded Sonnet call for synthesis (no agent loop -> no compaction);
  * write to the canonical path with open(path, "w") — the mis-save bug is
    structurally impossible;
  * append a DETERMINISTIC provenance footer (Python knows exactly which feeds
    returned data and which failed — more honest than the model claiming).

Usage:
    python generate_brief.py                  # full run, write canonical brief
    python generate_brief.py --dry-run        # fetch + filter, print item digest, NO API call
    python generate_brief.py --print          # full run, print to stdout instead of writing
    python generate_brief.py --date 2026-06-25
    python generate_brief.py --hours 48       # widen the recency window (default 36h)
    python generate_brief.py --out /tmp/x.md  # write somewhere else (side-by-side testing)
"""

import argparse
import calendar
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser
import requests

# A handful of gov feeds use "insecure_tls" (broken cert chain); silence the
# per-request InsecureRequestWarning those verify=False fetches would emit.
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

HOME = Path.home()
# sources.json is version-controlled in this repo (pipeline/sources.json). The
# legacy ~/.openclaw/.../references/sources.json path is now a symlink to it, so
# any remaining OpenClaw reference still resolves, but this script reads the repo
# copy directly (script-relative) and no longer depends on ~/.openclaw existing.
SOURCES_JSON = Path(__file__).resolve().parent / "pipeline" / "sources.json"
# EDITOR-TIPS.md is likewise version-controlled here (pipeline/EDITOR-TIPS.md); the
# legacy ~/.openclaw/workspace/EDITOR-TIPS.md path is now a symlink to it. The original
# TUCSON-BRIEF.md editorial rules (retired with the OpenClaw agent) are preserved for
# reference at pipeline/TUCSON-BRIEF.md — the live rules are in SYNTHESIS_PROMPT below.
EDITOR_TIPS = Path(__file__).resolve().parent / "pipeline" / "EDITOR-TIPS.md"
# Output dir consumed downstream by run_podcast.sh (resolve_brief). Left under
# ~/.openclaw/workspace by design: a pipeline contract, not version-controlled config.
BRIEFINGS_DIR = HOME / ".openclaw/workspace/briefings"

CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

TZ = ZoneInfo("America/Phoenix")  # Arizona: no DST
DEFAULT_WINDOW_HOURS = 36         # catch late prior-day items at a 6 AM run

# Browser-ish UA so Lee Enterprises / WAF feeds don't 403 a bare urllib client.
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}
FETCH_TIMEOUT = 25
MAX_ITEMS_PER_FEED = 25  # mirror the l=25 the feeds already cap at


# ---------------------------------------------------------------------------
# Source loading
# ---------------------------------------------------------------------------

def load_sources():
    """Flatten sources.json tiers into an ordered list, preserving tier order."""
    data = json.loads(SOURCES_JSON.read_text())
    tier_order = [
        "tier_1_primary",
        "tier_2_broadcast",
        "tier_2_officials",
        "tier_3_supplemental",
        "tier_4_weather_safety",
    ]
    out = []
    for tier in tier_order:
        for src in data["sources"].get(tier, []):
            src = dict(src)
            src["_tier"] = tier
            out.append(src)
    return out


def is_skipped(src):
    """sources.json: status 'broken' or 'disabled' -> never fetch."""
    return src.get("status") in ("broken", "disabled")


# ---------------------------------------------------------------------------
# Recency
# ---------------------------------------------------------------------------

def struct_to_dt(parsed):
    """feedparser's *_parsed time.struct_time is UTC -> aware datetime."""
    if not parsed:
        return None
    try:
        return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)
    except Exception:
        return None


def within_window(dt, cutoff):
    return dt is not None and dt >= cutoff


def clean_text(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)          # strip HTML tags from summaries
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ---------------------------------------------------------------------------
# Fetchers — one per source type. Each returns (items, error_or_None).
# An item is a dict: {title, summary, link, published (aware dt or None)}.
# ---------------------------------------------------------------------------

def fetch_rss(src, cutoff):
    # A few government feeds (e.g. Pima County Attorney) serve a valid feed over
    # an incomplete TLS chain; "insecure_tls": true skips verification for them.
    verify = not src.get("insecure_tls", False)
    try:
        resp = requests.get(src["url"], headers=HTTP_HEADERS,
                            timeout=FETCH_TIMEOUT, verify=verify)
        resp.raise_for_status()
    except Exception as e:
        return [], f"fetch error: {e}"

    feed = feedparser.parse(resp.content)
    if feed.bozo and not feed.entries:
        return [], f"parse error: {getattr(feed, 'bozo_exception', 'malformed feed')}"

    items, undated = [], []
    for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
        pub = struct_to_dt(entry.get("published_parsed") or entry.get("updated_parsed"))
        item = {
            "title": clean_text(entry.get("title", "")),
            "summary": clean_text(entry.get("summary", "") or entry.get("description", "")),
            "link": entry.get("link", ""),
            "published": pub,
        }
        if not item["title"]:
            continue
        if pub is None:
            undated.append(item)        # keep a few; feed order ~ newest first
        elif within_window(pub, cutoff):
            items.append(item)
    # Include up to a few undated items only if the feed gave us almost nothing
    # dated (some feeds omit dates entirely) — flagged so the model can hedge.
    if undated and len(items) < 3:
        for it in undated[:3]:
            it["undated"] = True
            items.append(it)
    return items, None


def fetch_bluesky(src, cutoff):
    try:
        resp = requests.get(src["url"], headers={"User-Agent": HTTP_HEADERS["User-Agent"]},
                            timeout=FETCH_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [], f"fetch error: {e}"

    items = []
    for fi in data.get("feed", []):
        post = fi.get("post", {})
        record = post.get("record", {})
        # Skip reposts (a 'reason' on the feed item marks a repost).
        if fi.get("reason"):
            continue
        created = record.get("createdAt")
        pub = None
        if created:
            try:
                pub = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except Exception:
                pub = None
        if not within_window(pub, cutoff):
            continue
        text = clean_text(record.get("text", ""))
        external = (post.get("embed") or {}).get("external") or {}
        # record.embed is the canonical place for the external link too.
        if not external:
            external = (record.get("embed") or {}).get("external") or {}
        link = external.get("uri", "")
        title = clean_text(external.get("title", ""))
        desc = clean_text(external.get("description", ""))
        summary_parts = [p for p in (text, title, desc) if p]
        items.append({
            "title": title or (text[:120] if text else "(post)"),
            "summary": " — ".join(summary_parts),
            "link": link,                 # may be empty for plain posts
            "published": pub,
        })
    return items, None


def fetch_weather(sources):
    """Fetch NWS active alerts + the multi-day point forecast.

    Returns (weather_context_str, errors_list). The forecast is passed to the
    model as structured text; the model writes the ⛈️ section per the format.
    """
    errors = []
    alerts_src = next((s for s in sources if "Active Alerts" in s["name"]), None)
    point_src = next((s for s in sources if "Point Forecast" in s["name"]), None)

    alert_lines = []
    if alerts_src:
        try:
            r = requests.get(alerts_src["url"], headers={"User-Agent": HTTP_HEADERS["User-Agent"],
                                                         "Accept": "application/geo+json"},
                            timeout=FETCH_TIMEOUT)
            r.raise_for_status()
            for feat in r.json().get("features", []):
                p = feat.get("properties", {})
                alert_lines.append(
                    f"- {p.get('event','Alert')}: {p.get('headline','')} "
                    f"(severity {p.get('severity','?')}, ends {p.get('expires','?')})\n"
                    f"  {clean_text(p.get('description',''))[:600]}"
                )
        except Exception as e:
            errors.append(("NWS Active Alerts", str(e)))

    forecast_lines = []
    if point_src:
        try:
            r = requests.get(point_src["url"], headers={"User-Agent": HTTP_HEADERS["User-Agent"]},
                            timeout=FETCH_TIMEOUT)
            r.raise_for_status()
            forecast_url = r.json().get("properties", {}).get("forecast")
            if forecast_url:
                fr = requests.get(forecast_url, headers={"User-Agent": HTTP_HEADERS["User-Agent"]},
                                 timeout=FETCH_TIMEOUT)
                fr.raise_for_status()
                for period in fr.json().get("properties", {}).get("periods", [])[:8]:
                    forecast_lines.append(
                        f"- {period.get('name','')}: {period.get('detailedForecast','')}"
                    )
        except Exception as e:
            errors.append(("NWS Point Forecast", str(e)))

    parts = []
    if alert_lines:
        parts.append("ACTIVE NWS ALERTS:\n" + "\n".join(alert_lines))
    else:
        parts.append("ACTIVE NWS ALERTS: none.")
    if forecast_lines:
        parts.append("FORECAST PERIODS (NWS Tucson, downtown point):\n" + "\n".join(forecast_lines))
    else:
        parts.append("FORECAST: unavailable.")
    return "\n\n".join(parts), errors


# ---------------------------------------------------------------------------
# Editor tips
# ---------------------------------------------------------------------------

def load_editor_tips(today):
    """Return the raw markdown of tips whose include-through date >= today."""
    if not EDITOR_TIPS.exists():
        return []
    text = EDITOR_TIPS.read_text()
    # Split on '## ' headings; keep blocks whose include-through date is current.
    blocks = re.split(r"\n(?=## )", text)
    live = []
    for block in blocks:
        if not block.lstrip().startswith("## "):
            continue
        m = re.search(r"\[include-through:\s*(\d{4}-\d{2}-\d{2})\]", block)
        if not m:
            continue
        try:
            through = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            continue
        if through >= today:
            live.append(block.strip())
    return live


# ---------------------------------------------------------------------------
# Dedupe + prompt assembly
# ---------------------------------------------------------------------------

def dedupe(items):
    seen, out = set(), []
    for it in items:
        key = (it.get("link") or "").strip().lower() or it["title"].strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def build_items_block(by_source):
    """Render the fetched items, grouped by source, for the synthesis prompt."""
    parts = []
    for name, items in by_source:
        if not items:
            continue
        parts.append(f"### SOURCE: {name}  ({len(items)} item(s) in window)")
        for it in items:
            when = it["published"].astimezone(TZ).strftime("%Y-%m-%d %H:%M MST") if it.get("published") else "undated"
            flag = " [UNDATED — hedge or skip]" if it.get("undated") else ""
            parts.append(f"- TITLE: {it['title']}")
            if it["summary"]:
                parts.append(f"  SUMMARY: {it['summary'][:700]}")
            parts.append(f"  LINK: {it['link'] or '(none)'}")
            parts.append(f"  PUBLISHED: {when}{flag}")
        parts.append("")
    return "\n".join(parts)


SYNTHESIS_PROMPT = """\
You are the editor of the Tucson Daily Brief, a daily hyper-local news briefing \
for the Tucson / Pima County area. Today is {today_human} (America/Phoenix).

You are given the day's news items, ALREADY FETCHED from the brief's vetted \
sources (you do not fetch anything — work only from what is below). Your job is \
editorial judgment: select, rank, deduplicate, and write the brief.

EDITORIAL PRIORITIES (rank stories in this order; lead with the highest available):
1. Government actions — city council votes, county decisions, AZ legislation affecting Tucson, ballot measures
2. Public safety — major incidents, emergency alerts, law enforcement news (not routine blotter)
3. Education — TUSD, Amphitheater, Catalina Foothills, U of A
4. Development & business — construction, business openings/closings, economic news
5. Community & events — major events, cultural happenings (only if genuinely significant)
6. Weather — always include; lead with it ONLY if an active alert exists

SELECTION RULES:
- Target 7-12 stories. Quality over quantity. Omit empty sections rather than padding.
- DEDUPLICATE: if the same story appears in multiple sources, merge and cite all of them.
- SOURCE DIVERSITY: draw across the available sources; do not lean on one or two \
outlets if others carry relevant local stories. (Some sources may simply have nothing \
local today — that is fine; never invent stories to balance them.)
- Exclude national/state news UNLESS it directly impacts Tucson/Pima County.
- Exclude sports unless it's a major U of A item and significant (not routine results).
- Exclude sponsored/affiliate/advertorial content.
- Items flagged [UNDATED] may be stale — only use one if clearly still relevant, and hedge.
- Soft-hedge single-source or unconfirmed items ("according to [outlet]," "is scheduled to").
- NEVER fabricate facts, names, dates, quotes, or sources. If unsure, leave it out.
- Write neutral, factual AP-style prose. No opinion, no framing — even on political items.

EDITOR TIPS: The blocks under "=== EDITOR TIPS ===" are hand-submitted leads. Treat \
each as a candidate story ranked normally. Follow each tip's own editor note (attribution, \
hedging, what to withhold). Do not invent details beyond the tip and its links.

WEATHER: Write the ⛈️ section from the NWS data under "=== WEATHER ===". If an active \
alert exists, lead that section with a ⚠️ callout in bold. Include today's \
conditions/high/low/wind, tonight, tomorrow, and a 2-3 sentence outlook.

OUTPUT FORMAT — output ONLY the briefing, starting with the title line. No preamble, \
no "Good morning," no sign-off, no footer (the system appends provenance). Use this \
structure, with ─── dividers between sections, omitting any section with no stories:

Tucson Daily Brief — {today_human}

🚨 Public Safety
**[Headline.]** [2-3 sentence neutral summary.]
📰 [Source Name](https://direct-article-url)

───

🏛️ Government
[same per story]

───

🏗️ Development & Business
[same per story]

───

🎉 Community & Events
[same per story]

───

⛈️ Weather — Tucson
[alert callout if any, then forecast as described]

📄 NWS Tucson Forecast API

ATTRIBUTION: every story ends with 📰 and a markdown link to the DIRECT article URL \
from its LINK field: `📰 [Source Name](url)`. Multi-source: `📰 [A](url1), [B](url2)`. \
If an item's LINK is "(none)", cite the source name without a link. Never link to a homepage.

=== WEATHER ===
{weather_block}

=== EDITOR TIPS ===
{tips_block}

=== NEWS ITEMS (grouped by source) ===
{items_block}
"""


# ---------------------------------------------------------------------------
# Claude call (raw HTTP + retry/backoff — matches generate_newsletter.py)
# ---------------------------------------------------------------------------

MAX_RETRIES = 4


def call_claude(prompt, api_key, max_tokens=4000):
    body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        CLAUDE_API_URL, data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read())
                content = result.get("content", [])
                if content and content[0].get("type") == "text":
                    return content[0]["text"]
                return None
        except urllib.error.HTTPError as e:
            if e.code != 429 and 400 <= e.code < 500:
                detail = e.read().decode("utf-8", "replace")[:400]
                print(f"  ERROR: Claude API HTTP {e.code} (not retrying): {detail}", file=sys.stderr)
                return None
            last_err = f"HTTP {e.code}"
        except Exception as e:
            last_err = str(e)
        if attempt < MAX_RETRIES:
            backoff = 2 ** (attempt - 1) + 0.1 * attempt
            print(f"  WARN: Claude call failed ({last_err}); retry {attempt}/{MAX_RETRIES-1} in {backoff:.1f}s",
                  file=sys.stderr)
            time.sleep(backoff)
        else:
            print(f"  ERROR: Claude call failed after {MAX_RETRIES} attempts: {last_err}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Provenance footer — deterministic, Python owns the ground truth
# ---------------------------------------------------------------------------

def build_footer(date_str, fetched, failed, skipped):
    succeeded = [n for n, c in fetched if c > 0]
    empty = [n for n, c in fetched if c == 0]
    lines = ["───", "", f"Briefing saved: tucson-brief-{date_str}.md"]
    lines.append(f"Sources with content: {len(succeeded)} of {len(fetched)} fetched "
                 f"({', '.join(succeeded) if succeeded else 'none'})")
    if empty:
        lines.append(f"Fetched, no items in window: {', '.join(empty)}")
    if failed:
        lines.append("Fetch failures: " + "; ".join(f"{n} ({e})" for n, e in failed))
    if skipped:
        lines.append(f"Skipped (broken/disabled in sources.json): {', '.join(skipped)}")
    lines.append("Generated deterministically by generate_brief.py — Next update: 6:00 AM MST")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Generate the Tucson Daily Brief deterministically.")
    ap.add_argument("--date", help="Brief date YYYY-MM-DD (default: today, America/Phoenix)")
    ap.add_argument("--hours", type=int, default=DEFAULT_WINDOW_HOURS,
                    help=f"Recency window in hours (default {DEFAULT_WINDOW_HOURS})")
    ap.add_argument("--out", help="Write to this path instead of the canonical briefings dir")
    ap.add_argument("--print", dest="to_stdout", action="store_true",
                    help="Print the brief to stdout instead of writing a file")
    ap.add_argument("--dry-run", action="store_true",
                    help="Fetch + filter only; print the item digest and exit (no API call)")
    args = ap.parse_args()

    now = datetime.now(TZ)
    brief_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else now.date()
    now_utc = datetime.now(timezone.utc)
    today_human = brief_date.strftime("%B %-d, %Y")

    print(f"Generating Tucson Daily Brief for {brief_date} "
          f"(default window: last {args.hours}h; per-source 'window_hours' honored)", file=sys.stderr)
    sources = load_sources()

    by_source = []          # [(name, [items])] in tier order
    fetched = []            # [(name, count)] for the footer
    failed = []             # [(name, error)]
    skipped = []            # [name]

    for src in sources:
        name, stype = src["name"], src["type"]
        if is_skipped(src):
            skipped.append(name)
            continue
        if stype == "api_json":
            continue        # weather handled separately
        # Per-source recency window: low-cadence, high-value sources (e.g. AZPM)
        # can set "window_hours" in sources.json to a longer lookback than the
        # default so their bursty posts still get caught.
        src_hours = src.get("window_hours", args.hours)
        src_cutoff = now_utc - timedelta(hours=src_hours)
        if stype == "rss":
            items, err = fetch_rss(src, src_cutoff)
        elif stype == "bluesky":
            items, err = fetch_bluesky(src, src_cutoff)
        else:
            continue
        if err:
            failed.append((name, err))
            print(f"  FAIL  {name}: {err}", file=sys.stderr)
            continue
        items = dedupe(items)
        by_source.append((name, items))
        fetched.append((name, len(items)))
        win = f" [window {src_hours}h]" if src_hours != args.hours else ""
        print(f"  ok    {name}: {len(items)} item(s) in window{win}", file=sys.stderr)

    weather_block, weather_errs = fetch_weather(sources)
    failed.extend(weather_errs)
    for n, e in weather_errs:
        print(f"  FAIL  {n}: {e}", file=sys.stderr)

    tips = load_editor_tips(brief_date)
    if tips:
        print(f"  ok    Editor tips: {len(tips)} live", file=sys.stderr)

    items_block = build_items_block(by_source)
    tips_block = "\n\n".join(tips) if tips else "(none)"
    total_items = sum(c for _, c in fetched)
    print(f"Total items in window: {total_items} across "
          f"{sum(1 for _, c in fetched if c)} source(s) with content", file=sys.stderr)

    if args.dry_run:
        print("\n=== WEATHER ===\n" + weather_block)
        print("\n=== EDITOR TIPS ===\n" + tips_block)
        print("\n=== ITEMS ===\n" + items_block)
        return

    if total_items == 0:
        print("ERROR: no items in window from any source — aborting (would produce an empty brief).",
              file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    prompt = SYNTHESIS_PROMPT.format(
        today_human=today_human,
        weather_block=weather_block,
        tips_block=tips_block,
        items_block=items_block,
    )
    print(f"Prompt: ~{len(prompt):,} chars (~{len(prompt)//4:,} tokens). Calling Claude...", file=sys.stderr)

    body = call_claude(prompt, api_key)
    if not body:
        print("ERROR: synthesis failed", file=sys.stderr)
        sys.exit(1)

    footer = build_footer(brief_date.isoformat(), fetched, failed, skipped)
    brief = body.strip() + "\n\n" + footer + "\n"

    if args.to_stdout:
        print(brief)
        return

    out_path = Path(args.out) if args.out else (BRIEFINGS_DIR / f"tucson-brief-{brief_date.isoformat()}.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(brief)        # <-- deterministic path: the mis-save bug cannot happen
    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
