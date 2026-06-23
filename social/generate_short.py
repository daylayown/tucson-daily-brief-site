#!/usr/bin/env python3
"""
Automated "Only in Tucson" short generator.

Pulls candidate stories from the last N days of published daily briefs
(posts/*.html), asks Claude Haiku to pick the single most light/feel-good one
and write a short beat script (no overclaiming — facts only), assembles the
clip with the standard eyebrow + CTA, and renders it via render_short.

Feel-good content isn't time-sensitive, so the default window is 14 days.

Usage:
    python3 generate_short.py                 # last 14 days -> render
    python3 generate_short.py --days 21
    python3 generate_short.py --dry-run       # pick + script, no render

Requires ANTHROPIC_API_KEY (sourced from ~/.config/environment.d/anthropic.conf
by the cron wrappers; export it for ad-hoc runs).
"""
import os, re, sys, json, html, argparse
from datetime import datetime, timedelta
from urllib.request import Request, urlopen

import render_short

HERE = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(HERE, "..", "posts")
CARDS_DIR = render_short.CARDS_DIR
USED_FILE = os.path.join(CARDS_DIR, ".used-stories.json")
MODEL = "claude-haiku-4-5-20251001"


def load_used():
    try:
        return set(json.load(open(USED_FILE)))
    except Exception:
        return set()


def save_used(used):
    os.makedirs(CARDS_DIR, exist_ok=True)
    json.dump(sorted(used), open(USED_FILE, "w"), indent=2)

SYSTEM = (
    "You produce 'Only in Tucson' — Tucson Daily Brief's warm, feel-good "
    "short-form video series: wildlife, desert wonder, community joy, charming "
    "local happenings, heartwarming human-interest. NOT hard news, politics, "
    "crime, tragedy, business/development, or anything controversial or sad."
)

PROMPT = """Today is {today}. From these candidate Tucson stories (last {days} days), pick the
SINGLE best light/feel-good one for an "Only in Tucson" vertical short, then write the
on-screen beat script.

CANDIDATES:
{candidates}

SELECTION PRIORITY:
- STRONGLY PREFER timeless / evergreen feel-good — wildlife, desert nature, charming
  local quirks, heartwarming human-interest — content that's still delightful weeks later.
- AVOID event promotions, calendars, sales, or anything tied to a specific day/week/season
  UNLESS its date is within 2 days of today (these go stale fast and may be auto-posted later).

HARD RULES:
- Use ONLY facts present in the chosen story. Never invent, exaggerate, or overclaim.
  No specific number/date/name unless it's in the story text. If unsure, stay vague.
- NO un-sourced hype words ("nobody expected", "impossible", "shocking", "unbelievable",
  "changed everything"). Describe what actually happened; let the facts carry it.
- Don't drop important caveats that change the meaning (cost, "proposed/planned", limits).
- Do NOT imply a timeframe ("this week", "today", "right now", "is here", "this weekend")
  unless the chosen story's date is within 2 days of today; otherwise keep it timeless.
- Each beat is LARGE on-screen text: ~4-12 words, max ~70 characters. Short.
- Beat 1 = the HOOK (a delightful curiosity-gap opener).
- Middle beats deliver the story simply and warmly. 3-4 beats total.
- Plain, friendly voice. No jargon. At most ONE tasteful emoji across all beats.
- Do NOT write a closing line/CTA — it is appended automatically.
- If NO candidate is genuinely light/feel-good, return {{"id": -1, "beats": []}}.

Also write: a YouTube "title" (<=80 chars, may include one emoji; do not add #Shorts,
it's added automatically), a warm 1-2 sentence "caption" ending by pointing readers to
tucsondailybrief.com, and 6-8 "hashtags" (each starting with #).

Return ONLY raw JSON, no markdown fences:
{{"id": <candidate number>, "reason": "<one line>", "beats": ["...", "..."],
  "title": "...", "caption": "...", "hashtags": ["#..."]}}"""


def _text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def collect_candidates(days):
    """Scan recent posts for non-weather story paragraphs."""
    cutoff = datetime.now() - timedelta(days=days)
    cands = []
    for fn in sorted(os.listdir(POSTS_DIR), reverse=True):
        m = re.match(r"(\d{4}-\d{2}-\d{2})\.html$", fn)
        if not m:
            continue
        dt = datetime.strptime(m.group(1), "%Y-%m-%d")
        if dt < cutoff:
            continue
        content = open(os.path.join(POSTS_DIR, fn)).read()
        section = ""
        for h2, attrs, inner in re.findall(
                r"<h2>(.*?)</h2>|<p\b([^>]*)>(.*?)</p>", content, re.DOTALL):
            if h2:
                section = _text(h2)
                continue
            if "post-meta" in attrs or "source" in attrs or "<strong>" not in inner:
                continue
            if "weather" in section.lower():
                continue
            sm = re.search(r"<strong>(.*?)</strong>", inner, re.DOTALL)
            headline = _text(sm.group(1)) if sm else ""
            desc = _text(inner)
            if not headline:
                continue
            cands.append({"date": m.group(1), "section": re.sub(r"^[^\w]+", "", section),
                          "headline": headline, "text": desc[:260]})
    return cands


def call_haiku(prompt):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set.")
    payload = json.dumps({"model": MODEL, "max_tokens": 1024,
                          "system": SYSTEM,
                          "messages": [{"role": "user", "content": prompt}]}).encode()
    req = Request("https://api.anthropic.com/v1/messages", data=payload,
                  headers={"Content-Type": "application/json", "x-api-key": key,
                           "anthropic-version": "2023-06-01"}, method="POST")
    with urlopen(req, timeout=60) as r:
        result = json.loads(r.read())
    raw = result["content"][0]["text"].strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw).strip()
    u = result.get("usage", {})
    print(f"  Haiku: {u.get('input_tokens',0)} in + {u.get('output_tokens',0)} out tokens")
    return json.loads(raw)


def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:40]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-dedup", action="store_true",
                    help="don't exclude previously-used stories")
    ap.add_argument("--publish", action="store_true",
                    help="upload the rendered clip to YouTube Shorts")
    ap.add_argument("--privacy", default="public",
                    choices=["public", "unlisted", "private"])
    args = ap.parse_args()

    used = set() if args.no_dedup else load_used()
    cands = [c for c in collect_candidates(args.days)
             if slugify(c["headline"]) not in used]
    if not cands:
        sys.exit("No fresh candidate stories found in window (all used?).")
    print(f"Collected {len(cands)} fresh candidate stories "
          f"from the last {args.days} days ({len(used)} excluded as used).")
    listing = "\n".join(
        f"[{i}] ({c['date']}, {c['section']}) {c['headline']} — {c['text']}"
        for i, c in enumerate(cands))
    today = datetime.now().strftime("%Y-%m-%d")
    out = call_haiku(PROMPT.format(today=today, days=args.days, candidates=listing))

    if out.get("id", -1) < 0 or not out.get("beats"):
        sys.exit("Haiku found no genuinely light/feel-good story in this window.")
    chosen = cands[out["id"]]
    print(f"\nPicked: [{out['id']}] {chosen['headline']}  ({chosen['date']})")
    print(f"Reason: {out.get('reason','')}")

    # Assemble the clip: standard eyebrow on beat 0 + fixed CTA sign-off.
    beats = out["beats"]
    script = [{"eyebrow": "Only in Tucson", "text": beats[0]}]
    script += [{"text": b} for b in beats[1:]]
    script.append({"text": "Only in Tucson. 🌵", "cta": True, "nowrap": True})

    print("\n--- script ---")
    for s in script:
        print(f"  • {s['text']!r}")
    print(f"\nTitle:   {out.get('title','')}")
    print(f"Caption: {out.get('caption','')}")
    print(f"Tags:    {' '.join(out.get('hashtags', []))}")

    if args.dry_run:
        print("\n(dry run — not rendered)")
        return

    slug = f"only-in-tucson-{chosen['date']}-{slugify(chosen['headline'])}"
    mp4 = render_short.render_from_config(slug, "only-in-tucson", script)
    # sidecar metadata for the (future) publish step
    meta = {"slug": slug, "series": "only-in-tucson", "source": chosen,
            "title": out.get("title", ""), "caption": out.get("caption", ""),
            "hashtags": out.get("hashtags", []), "script": script}
    with open(os.path.join(CARDS_DIR, f"short-{slug}.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\nMetadata -> short-{slug}.json")

    if not args.no_dedup:
        used.add(slugify(chosen["headline"]))
        save_used(used)

    if args.publish:
        import publish_youtube_short as pub
        desc = pub.build_description(out.get("caption", ""), out.get("hashtags", []))
        tags = [h.lstrip("#") for h in out.get("hashtags", [])] or ["Tucson"]
        pub.upload(mp4, out.get("title", "Only in Tucson"), desc, tags, args.privacy)


if __name__ == "__main__":
    main()
