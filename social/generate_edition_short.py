#!/usr/bin/env python3
"""
Geographic edition generator — "What to Watch: {Town}" (weekly).

Builds one town's weekly ~30s vertical edition from structured pipeline
output (agenda previews + Around Town dev-watch pages + Spotted filings),
renders it with the town's edition preset in render_short.py, and prints a
machine-readable EDITION-RENDERED line for check_agendas.sh. Posting to
FB/IG is MANUAL (that is the human-review gate for Meta surfaces); the same
MP4 may be auto-published to YouTube Shorts with --publish.

Spec: SHORT-FORM-VIDEO.md § Geographic editions. Format is lead-plus-ticker,
storyboard: boundary cold-open → town title card → 2-3 lead beats → radar
ticker → safe-zone CTA.

Lead selection is a DETERMINISTIC priority ladder (the model only phrases):
  1. upcoming preview exists → lead = agenda item, constrained in order:
     topic-flagged item (detect_topics) → public hearing / rezoning → the
     preview's most consequential item;
  2. no upcoming meeting → lead = newest Around Town / Spotted item this week
     ("No council this week" framing);
  3. neither → EDITION-SKIPPED (honest skip; a quiet week is data).

Grounding rules match generate_agenda_short.py: every fact must appear in
the supplied source text, pre-meeting hedging enforced, plus a second-pass
verification call. Hard word caps enforced in code.

Usage:
    python3 generate_edition_short.py marana
    python3 generate_edition_short.py orovalley --dry-run
    python3 generate_edition_short.py marana --publish        # + YouTube
    python3 generate_edition_short.py marana --days-back 30   # widen radar
"""
import os, re, sys, json, glob, argparse
from datetime import date, datetime, timedelta
from urllib.request import Request, urlopen

import render_short

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..")
AGENDA_DIR = os.path.join(SITE, "agenda-watch")
AROUND_DIR = os.path.join(SITE, "around-town")
RECORD_DIR = os.path.join(SITE, "public-record")
MEETING_WATCH_DIR = os.path.join(SITE, "meeting-watch")
CARDS_DIR = render_short.CARDS_DIR
MODEL = "claude-sonnet-4-6"
MAX_SOURCE_CHARS = 7000

TOWNS = {
    "marana": {
        "name": "Marana", "series": "edition-marana",
        "preview_prefix": "marana-", "mw": "marana-council",
        "body": "Marana Town Council",
        "dev_ok": lambda fn: fn.startswith("dev-marana-"),
        "hashtags": ["#Marana", "#Tucson", "#TucsonNews"],
    },
    "orovalley": {
        "name": "Oro Valley", "series": "edition-orovalley",
        "preview_prefix": "orovalley-", "mw": "orovalley-council",
        "body": "Oro Valley Town Council",
        # OV dev-watch slugs carry no town token; they are the dev-* pages
        # that are not Marana's.
        "dev_ok": lambda fn: fn.startswith("dev-") and not fn.startswith("dev-marana-"),
        "hashtags": ["#OroValley", "#Tucson", "#TucsonNews"],
    },
}

# The standing audience-education line (decided 2026-07-28) — feeds the exact
# signals Meta's ranking model uses and doubles as the owned-surface CTA.
EDUCATION_LINE = ("Like the videos about your part of town and you'll see "
                  "more of them. Every video: tucsondailybrief.com")

SYSTEM = (
    "You write 'What to Watch: {town}' — Tucson Daily Brief's weekly town-"
    "specific short-form video edition. Each edition previews what {town}'s "
    "local government decides this week, plus what's changing around town. "
    "Tone: neutral, factual, watchful — a public-records reporter, not an "
    "activist. You never editorialize about motives and never assert outcomes "
    "that haven't happened."
)

PROMPT = """Today is {today}. Build this week's "What to Watch: {town}" edition script.

LEAD SOURCE ({lead_kind}):
{lead_source}

{lead_instruction}

RADAR POOL (candidate ticker items — published Around Town / Spotted pages from the
last {days_back} days; each entry is "TITLE — detail"):
{radar_pool}

HARD RULES:
- Use ONLY facts present in the text above. Every number, dollar figure, date, and
  name must appear in the source. Never invent, round, or extrapolate. If unsure, omit.
- {hedge_rule}
- No hype words, no emoji in beats, no clickbait.
- LEAD: exactly {lead_n} beats. Each beat is LARGE on-screen text, MUST be under 70
  characters — count them. Punchy fragments, not sentences.
  Beat 1 = the hook (the concrete thing at stake). Beat 2 = the key number/detail.
  {beat3_rule}
- TICKER: pick the {ticker_n} most reader-relevant radar items. Rephrase each as ONE
  line under 55 characters, plain and concrete (e.g. "New Chipotle planned at Gladden
  Farms"). Skip items that duplicate the lead. If the pool is empty return [].
- Do NOT write a closing/CTA line — it is appended automatically.

Also write: a "title" for YouTube (<=80 chars, must start with "{town}: ", factual,
no emoji, NO dates), and a 1-2 sentence "caption" whose FIRST WORDS are "{town}:"
followed by the lead story in plain words (links and hashtags are appended
automatically).

Return ONLY raw JSON, no markdown fences:
{{"lead_beats": ["...", ...], "ticker": ["...", ...],
  "title": "...", "caption": "..."}}"""

VERIFY_PROMPT = """You are the fact-check pass for a town-edition video script. Check every claim
in the draft against the SOURCE text:
- Every number, dollar figure, date, and name must appear in the SOURCE.
- No outcome or consequence asserted that the SOURCE does not itself state.
- {hedge_rule}
- Lead beats under 70 chars each; ticker lines under 55 chars each.
Rewrite ONLY what fails; keep everything that passes verbatim.

SOURCE:
{source}

DRAFT:
{draft}

Return ONLY raw JSON, no markdown fences:
{{"changed": true|false, "notes": "<one line>",
  "lead_beats": [...], "ticker": [...], "title": "...", "caption": "..."}}"""


def call_claude(prompt, town):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set.")
    payload = json.dumps({"model": MODEL, "max_tokens": 1024,
                          "system": SYSTEM.format(town=town),
                          "messages": [{"role": "user", "content": prompt}]}).encode()
    req = Request("https://api.anthropic.com/v1/messages", data=payload,
                  headers={"Content-Type": "application/json", "x-api-key": key,
                           "anthropic-version": "2023-06-01"}, method="POST")
    with urlopen(req, timeout=120) as r:
        result = json.loads(r.read())
    raw = result["content"][0]["text"].strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw).strip()
    u = result.get("usage", {})
    print(f"  Sonnet: {u.get('input_tokens', 0)} in + {u.get('output_tokens', 0)} out tokens")
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def find_preview(town_cfg, days_ahead):
    """Newest preview for an upcoming meeting of this town, or None."""
    today = date.today()
    horizon = today + timedelta(days=days_ahead)
    best = None
    for fn in sorted(os.listdir(AGENDA_DIR)):
        m = re.match(
            rf"{town_cfg['preview_prefix']}(\d{{4}}-\d{{2}}-\d{{2}})((?:-[a-z-]+)?)-preview\.md$", fn)
        if not m:
            continue
        try:
            dt = date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if today <= dt <= horizon:
            best = {"file": fn, "date": dt,
                    "text": open(os.path.join(AGENDA_DIR, fn)).read()[:MAX_SOURCE_CHARS]}
    return best


def _page_title_lede(path):
    html = open(path).read()
    tm = re.search(r"<article.*?<h1>(.+?)</h1>", html, re.DOTALL)
    lm = re.search(r'<p class="filing-subtitle">(.+?)</p>', html)
    sm = re.search(r"</dl>\s*<p>(.+?)</p>", html, re.DOTALL)
    def clean(s):
        s = re.sub(r"<[^>]+>", " ", s or "")
        s = (s.replace("&amp;", "&").replace("&middot;", "·")
              .replace("&mdash;", "—").replace("&rsquo;", "'"))
        return re.sub(r"\s+", " ", s).strip()
    return clean(tm.group(1) if tm else os.path.basename(path)), \
        clean(lm.group(1) if lm else ""), clean(sm.group(1) if sm else "")[:300]


def radar_items(town_cfg, days_back):
    """Recently published Around Town + Spotted pages for this town, newest
    first. Recency = file mtime (discovery-time proxy), BUT guarded by the
    date embedded in the filename: site-wide HTML sweeps touch every page's
    mtime, and without the guard a 2023 case would resurface as "news" after
    one. Sorted by the filename date (the case's own grounded date), newest
    first."""
    cutoff = datetime.now().timestamp() - days_back * 86400
    date_floor = date.today() - timedelta(days=90)

    def fn_date(fn):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", fn)
        try:
            return date.fromisoformat(m.group(1)) if m else None
        except ValueError:
            return None

    items = []
    for path in glob.glob(os.path.join(AROUND_DIR, "dev-*.html")):
        fn = os.path.basename(path)
        d = fn_date(fn)
        if (not town_cfg["dev_ok"](fn) or os.path.getmtime(path) < cutoff
                or d is None or d < date_floor):
            continue
        title, lede, summary = _page_title_lede(path)
        items.append({"title": title, "detail": lede, "summary": summary,
                      "date": d.isoformat()})
    town_l = town_cfg["name"].lower()
    for path in glob.glob(os.path.join(RECORD_DIR, "liquor-*.html")):
        fn = os.path.basename(path)
        d = fn_date(fn)
        if os.path.getmtime(path) < cutoff or d is None or d < date_floor:
            continue
        html = open(path).read().lower()
        if town_l not in html:
            continue
        title, lede, summary = _page_title_lede(path)
        items.append({"title": title, "detail": f"Liquor license filing · {lede}",
                      "summary": summary, "date": d.isoformat()})
    items.sort(key=lambda i: i["date"], reverse=True)
    return items


def meeting_meta_line(preview):
    """CTA meta line from real data only: weekday + date from the filename,
    time only if it appears in the preview text."""
    dt = preview["date"]
    line = f"Council meets {dt.strftime('%A, %b. %-d')}"
    tm = re.search(r"\b(\d{1,2}:\d{2})\s*([ap])\.?m\.?", preview["text"], re.IGNORECASE)
    if tm:
        line += f" · {tm.group(1)} {tm.group(2).upper()}M"
    return line


def preview_url(town_cfg, preview):
    page = "meeting-watch.html"
    d = preview["date"].isoformat()
    cands = [fn for fn in os.listdir(MEETING_WATCH_DIR)
             if fn.startswith(town_cfg["mw"]) and d in fn and fn.endswith(".html")]
    if cands:
        page = f"meeting-watch/{sorted(cands)[0]}"
    return (f"https://tucsondailybrief.com/{page}"
            f"?utm_source=social&utm_medium=short&utm_campaign=edition-{town_cfg['name'].lower().replace(' ', '')}")


# ---------------------------------------------------------------------------
# Lead-selection ladder (deterministic; the model only phrases)
# ---------------------------------------------------------------------------

def lead_constraint(preview_text):
    """Returns (constraint instruction, label) per the priority ladder."""
    try:
        sys.path.insert(0, SITE)
        from generate_post import detect_topics
        topics = detect_topics(preview_text)
    except Exception:
        topics = []
    if topics:
        return (f"THE LEAD MUST BE the agenda item flagged for high-interest "
                f"topic(s): {', '.join(topics)}. Do not choose another item.",
                f"topic-flag:{','.join(topics)}")
    if re.search(r"public hearing|rezon", preview_text, re.IGNORECASE):
        return ("THE LEAD MUST BE a public-hearing or rezoning item from the "
                "preview (the first one if several). Do not choose another item.",
                "hearing/rezoning")
    return ("Choose the single most consequential item for ordinary residents "
            "(money, land use, services, fees, public access).", "top-item")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("town", choices=sorted(TOWNS))
    ap.add_argument("--days-ahead", type=int, default=7)
    ap.add_argument("--days-back", type=int, default=7,
                    help="radar window for Around Town / Spotted items")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true",
                    help="also upload to YouTube Shorts (FB/IG stay manual)")
    ap.add_argument("--privacy", default="public",
                    choices=["public", "unlisted", "private"])
    args = ap.parse_args()

    cfg = TOWNS[args.town]
    town = cfg["name"]
    preview = find_preview(cfg, args.days_ahead)
    radar = radar_items(cfg, args.days_back)

    if not preview and not radar:
        print(f"EDITION-SKIPPED\t{town}\tno upcoming meeting and no radar items "
              f"in the last {args.days_back} days")
        return

    # --- Assemble the model's inputs per the ladder ---
    if preview:
        instruction, ladder = lead_constraint(preview["text"])
        lead_kind = f"upcoming {cfg['body']} meeting preview, {preview['date']}"
        lead_source = preview["text"]
        hedge = ("NOTHING IS DECIDED YET — pre-meeting language only: \"will "
                 "consider\", \"proposed\", \"up for a vote\". Never past tense.")
        lead_n, beat3 = 3, ("Beat 3 = the stakes, restating the preview's own "
                            "stakes — do not invent consequences.")
        radar_pool = radar[1:] if False else radar  # full pool; dedup is in-prompt
    else:
        lead = radar[0]
        instruction = ("THE LEAD IS the first radar item below (the newest). "
                       "Open with the fact that the council does not meet this "
                       "week, then the item.")
        ladder = "dev-led (no meeting)"
        lead_kind = "no council meeting this week — newest Around Town/Spotted item"
        lead_source = json.dumps(lead, indent=2)
        hedge = ("These are pipeline/permit records — nothing is approved or "
                 "final. Use \"proposes\", \"planned\", \"filed\".")
        lead_n, beat3 = 2, ""
        radar_pool = radar[1:]

    pool_text = "\n".join(f"- {i['title']} — {i['detail']}" +
                          (f" — {i['summary']}" if i["summary"] else "")
                          for i in radar_pool) or "(empty)"
    ticker_n = min(3, max(2, len(radar_pool))) if radar_pool else 0

    print(f"[{town}] lead: {ladder}; radar pool: {len(radar_pool)} item(s)")
    out = call_claude(PROMPT.format(
        today=date.today().strftime("%A, %B %d, %Y"), town=town,
        lead_kind=lead_kind, lead_source=lead_source,
        lead_instruction=instruction, radar_pool=pool_text,
        days_back=args.days_back, hedge_rule=hedge,
        lead_n=lead_n, beat3_rule=beat3, ticker_n=ticker_n), town)

    # --- Verify pass (grounding insurance, same posture as BIA) ---
    source_all = lead_source + "\n\nRADAR POOL:\n" + pool_text
    draft = json.dumps({k: out.get(k) for k in
                        ("lead_beats", "ticker", "title", "caption")}, indent=2)
    check = call_claude(VERIFY_PROMPT.format(
        source=source_all[:MAX_SOURCE_CHARS + 3000], draft=draft,
        hedge_rule=hedge), town)
    print(f"Fact-check: {check.get('notes', '')}")
    if check.get("changed"):
        for k in ("lead_beats", "ticker", "title", "caption"):
            if check.get(k):
                out[k] = check[k]

    # --- Hard caps enforced in code (derive, don't trust) ---
    beats = [b.strip() for b in out.get("lead_beats", []) if b.strip()][:3]
    ticker = [t.strip() for t in out.get("ticker", []) if t.strip()][:3]
    for b in beats:
        if len(b) > 90:
            sys.exit(f"ERROR: lead beat over 90 chars, refusing to render: {b!r}")
        if len(b) > 70:
            print(f"  WARNING: lead beat over 70 chars ({len(b)}): {b!r}")
    ticker = [t if len(t) <= 60 else t[:57].rsplit(" ", 1)[0] + "…" for t in ticker]
    if not beats:
        print(f"EDITION-SKIPPED\t{town}\tmodel returned no usable lead beats")
        return

    # --- Assemble the storyboard ---
    week_of = f"Week of {date.today().strftime('%B %-d')}"
    script = [
        {"kind": "boundary", "kicker": "What to Watch", "dur": 2.8},
        {"kind": "title", "sub": week_of, "dur": 2.8},
    ]
    script += [{"text": b, "dur": 4.5} for b in beats]
    if ticker:
        script.append({"kind": "ticker", "items": ticker, "dur": 6.0})
    cta = {"text": f"We read every {town} agenda\nso you don’t have to.",
           "cta": True, "dur": 4.0}
    if preview:
        cta["meta"] = meeting_meta_line(preview)
    script.append(cta)

    url = (preview_url(cfg, preview) if preview
           else "https://tucsondailybrief.com/around-town.html"
                f"?utm_source=social&utm_medium=short&utm_campaign=edition-{args.town}")
    caption = f"{out.get('caption', '').strip()}\n\n{EDUCATION_LINE}\n\nMore: {url}"

    print("\n--- script ---")
    for s in script:
        print(f"  • {s.get('kind', 'text')}: "
              f"{s.get('text') or s.get('items') or s.get('sub') or s.get('kicker')!r}")
    print(f"\nTitle:   {out.get('title', '')}")
    print(f"Caption:\n{caption}")
    print(f"Tags:    {' '.join(cfg['hashtags'])}")

    if args.dry_run:
        print("\n(dry run — not rendered)")
        return

    slug = f"edition-{args.town}-{date.today().isoformat()}"
    mp4 = render_short.render_from_config(slug, cfg["series"], script)
    meta = {"slug": slug, "series": cfg["series"], "lead_ladder": ladder,
            "source": {"preview": preview["file"] if preview else None,
                       "radar_count": len(radar)},
            "title": out.get("title", ""), "caption": caption,
            "hashtags": cfg["hashtags"], "script": script}
    with open(os.path.join(CARDS_DIR, f"short-{slug}.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Metadata -> short-{slug}.json")

    if args.publish:
        import publish_youtube_short as pub
        desc = pub.build_description(caption, cfg["hashtags"])
        tags = [h.lstrip("#") for h in cfg["hashtags"]]
        vid = pub.upload(mp4, out.get("title", f"What to Watch: {town}"),
                         desc, tags, args.privacy)
        print(f"SHORT-PUBLISHED\t{out.get('title', '')}\t"
              f"https://www.youtube.com/shorts/{vid}")

    # Machine-readable line for check_agendas.sh → Telegram (manual FB/IG post).
    print(f"EDITION-RENDERED\t{town}\t{mp4}\t{out.get('title', '')}")


if __name__ == "__main__":
    main()
