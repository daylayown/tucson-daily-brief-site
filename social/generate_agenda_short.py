#!/usr/bin/env python3
"""
Automated "Buried in the Agenda" short generator (weekly).

Scans agenda-watch/*-preview.md for UPCOMING meetings (next N days), asks
Claude Sonnet to pick the single most consequential under-the-radar item and
write a hedged 5-beat vertical script (Sol formula: surprising fact -> where
it appeared -> why it matters -> when it's decided), renders it with the
dark "buried-in-the-agenda" series preset, and optionally publishes to
YouTube Shorts.

Unlike the daily "Only in Tucson" short (evergreen, feel-good), this is civic
news published BEFORE the meeting happens — the script prompt enforces the
soft-hedging rules (nothing is decided yet; "will consider / proposed /
headed to a vote") and claims nothing not present in the preview text.

Runs Mondays via check_agendas.sh (after the agenda miners, so the freshest
previews are included). Skips cleanly — exit 0, no render — on weeks with no
upcoming meetings or no genuinely consequential item; the model is allowed to
say "nothing this week."

Usage:
    python3 generate_agenda_short.py                # pick + script + render
    python3 generate_agenda_short.py --dry-run      # pick + script only
    python3 generate_agenda_short.py --publish      # ... + upload to YouTube
    python3 generate_agenda_short.py --days-ahead 10

Requires ANTHROPIC_API_KEY (sourced from ~/.config/environment.d/anthropic.conf
by the cron wrappers; export it for ad-hoc runs).
"""
import os, re, sys, json, argparse
from datetime import date, timedelta
from urllib.request import Request, urlopen

import render_short

HERE = os.path.dirname(os.path.abspath(__file__))
AGENDA_DIR = os.path.join(HERE, "..", "agenda-watch")
MEETING_WATCH_DIR = os.path.join(HERE, "..", "meeting-watch")
CARDS_DIR = render_short.CARDS_DIR
USED_FILE = os.path.join(CARDS_DIR, ".used-agenda-items.json")
MODEL = "claude-sonnet-4-6"
MAX_PREVIEW_CHARS = 6000  # per preview, keeps multi-meeting weeks in budget

MUNI = {
    "pima-county": {"name": "Pima County Board of Supervisors", "mw": "pima-county-bos"},
    "tucson": {"name": "Tucson Mayor & Council", "mw": "tucson-council"},
    "marana": {"name": "Marana Town Council", "mw": "marana-council"},
    "orovalley": {"name": "Oro Valley Town Council", "mw": "orovalley-council"},
}

SYSTEM = (
    "You produce 'Buried in the Agenda' — Tucson Daily Brief's civic short-form "
    "video series. Each short surfaces ONE consequential item from an upcoming "
    "Southern Arizona government meeting agenda that residents would otherwise "
    "never hear about. Tone: neutral, factual, watchful — a public-records "
    "reporter, not an activist. You never editorialize about motives and never "
    "assert outcomes that haven't happened."
)

PROMPT = """Today is {today}. Below are Tucson Daily Brief's "What to Watch" previews for
upcoming government meetings. Pick the SINGLE most consequential item that ordinary
residents are least likely to hear about elsewhere, then write the on-screen beat
script for a ~20-second vertical video.

PREVIEWS:
{previews}

SELECTION PRIORITY:
- Prefer genuinely buried items: consent-calendar items, procedural-sounding items with
  big real-world stakes (money, land use, service changes, fees, public access).
- Prefer concrete resident impact over political theater. A boundary map that green-lights
  hundreds of homes beats a symbolic resolution that will get TV coverage anyway.
- Big dollar figures, service cuts, and "could pass without discussion" flags are strong signals.

HARD RULES — THIS IS PRE-MEETING CIVIC NEWS:
- Use ONLY facts present in the preview text. Every number, dollar figure, date, and name
  must appear in the source. Never invent, round up, or extrapolate. If unsure, omit.
- NOTHING IS DECIDED YET. Use "will consider", "could", "proposed", "headed to a vote",
  "on the agenda". NEVER "approved", "passed", "decided", or any past-tense outcome.
- Keep caveats that change the meaning (e.g. "recommended", "to be identified", "extension").
- Do NOT speculate about consequences beyond what the preview itself states. The "why it
  matters" beat must restate the preview's own stakes, not invent new outcomes or scenarios.
- Name public officials by title only if needed; never name private individuals.
- No hype words ("shocking", "unbelievable", "they don't want you to know"). No emoji in beats.
- Exactly 4 beats. Each beat is LARGE on-screen text and MUST be under 70 characters —
  count them. A beat is a punchy fragment, not a full sentence. Split or cut; never cram.
  - Beat 1 = the HOOK: the surprising concrete fact.
  - Beat 2 = where it's buried (which body's agenda; say "consent calendar" if it is).
  - Beat 3 = why it matters to residents.
  - Beat 4 = when: the meeting day and date (e.g. "The vote: Tuesday, July 14.").
- Never repeat a fact across beats. The meeting date appears in beat 4 ONLY.
- Do NOT write a closing line/CTA — it is appended automatically.
- If NO item is genuinely consequential and under-covered, return {{"meeting": -1, "beats": []}}.
  A skipped week is better than a weak or overclaimed one.

Also write: a YouTube "title" (<=80 chars, factual, no clickbait, no emoji; do not add
#Shorts, it's added automatically), a neutral 1-2 sentence "caption" (the preview link is
appended automatically), and 6-8 "hashtags" (each starting with #, include #Tucson).

Return ONLY raw JSON, no markdown fences:
{{"meeting": <preview number>, "item": "<short name of the chosen agenda item>",
  "reason": "<one line>", "beats": ["...", "...", "...", "..."],
  "title": "...", "caption": "...", "hashtags": ["#..."]}}"""


VERIFY_PROMPT = """You are the fact-check pass for a "Buried in the Agenda" short that publishes
WITHOUT human review. Below are the SOURCE preview text and a draft script. Check every factual
claim in the beats, title, and caption against the SOURCE:
- Every number, dollar figure, date, and name must appear in the SOURCE.
- No outcome or consequence may be asserted or implied that the SOURCE does not itself state.
  Watch for invented scenarios ("could stall", "could face gaps", "may be cut") — strike them
  unless the SOURCE says so.
- Pre-meeting hedging required ("will consider", "proposed", "up for a vote"); nothing is
  decided yet — no past-tense outcomes.
- Beats must each stay under 70 characters; exactly {n} beats; the meeting date appears only
  in the last beat.

Rewrite ONLY what fails; keep everything that passes verbatim.

SOURCE:
{source}

DRAFT:
{draft}

Return ONLY raw JSON, no markdown fences:
{{"changed": true|false, "notes": "<one line: what was fixed, or 'clean'>",
  "beats": [...], "title": "...", "caption": "..."}}"""


def load_used():
    try:
        return set(json.load(open(USED_FILE)))
    except Exception:
        return set()


def save_used(used):
    os.makedirs(CARDS_DIR, exist_ok=True)
    json.dump(sorted(used), open(USED_FILE, "w"), indent=2)


def collect_previews(days_ahead):
    """Upcoming-meeting preview files: [{muni, date, slug, text}, ...]."""
    today = date.today()
    horizon = today + timedelta(days=days_ahead)
    out = []
    for fn in sorted(os.listdir(AGENDA_DIR)):
        m = re.match(
            r"(marana|orovalley|tucson|pima-county)-(\d{4}-\d{2}-\d{2})((?:-[a-z-]+)?)-preview\.md$",
            fn)
        if not m:
            continue
        muni, d, suffix = m.groups()
        try:
            dt = date.fromisoformat(d)
        except ValueError:
            continue
        if not (today <= dt <= horizon):
            continue
        text = open(os.path.join(AGENDA_DIR, fn)).read()[:MAX_PREVIEW_CHARS]
        out.append({"muni": muni, "date": d, "slug": fn[:-len("-preview.md")],
                    "suffix": suffix, "text": text})
    return out


def preview_url(meeting):
    """Public URL of the published meeting-watch page for a preview (with UTM)."""
    prefix = MUNI[meeting["muni"]]["mw"]
    page = None
    try:
        candidates = [fn for fn in os.listdir(MEETING_WATCH_DIR)
                      if fn.startswith(prefix) and meeting["date"] in fn
                      and fn.endswith(".html")]
        if candidates:
            page = f"meeting-watch/{sorted(candidates)[0]}"
    except OSError:
        pass
    page = page or "meeting-watch.html"
    return (f"https://tucsondailybrief.com/{page}"
            "?utm_source=youtube&utm_medium=short&utm_campaign=buried-in-the-agenda")


def call_claude(prompt):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set.")
    payload = json.dumps({"model": MODEL, "max_tokens": 1024,
                          "system": SYSTEM,
                          "messages": [{"role": "user", "content": prompt}]}).encode()
    req = Request("https://api.anthropic.com/v1/messages", data=payload,
                  headers={"Content-Type": "application/json", "x-api-key": key,
                           "anthropic-version": "2023-06-01"}, method="POST")
    with urlopen(req, timeout=120) as r:
        result = json.loads(r.read())
    raw = result["content"][0]["text"].strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw).strip()
    u = result.get("usage", {})
    print(f"  Sonnet: {u.get('input_tokens',0)} in + {u.get('output_tokens',0)} out tokens")
    return json.loads(raw)


def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:40]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days-ahead", type=int, default=7,
                    help="how far ahead to look for meetings (default 7)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-dedup", action="store_true",
                    help="don't exclude previously-used agenda items")
    ap.add_argument("--publish", action="store_true",
                    help="upload the rendered clip to YouTube Shorts")
    ap.add_argument("--privacy", default="public",
                    choices=["public", "unlisted", "private"])
    args = ap.parse_args()

    meetings = collect_previews(args.days_ahead)
    if not meetings:
        print(f"No upcoming meeting previews in the next {args.days_ahead} days — skipping.")
        return
    used = set() if args.no_dedup else load_used()
    print(f"Found {len(meetings)} upcoming meeting preview(s): "
          + ", ".join(m["slug"] for m in meetings))

    used_note = ""
    if used:
        used_note = ("\nALREADY COVERED in previous shorts (do NOT pick these again):\n"
                     + "\n".join(f"- {u}" for u in sorted(used)))
    listing = "\n\n".join(
        f"=== PREVIEW [{i}] — {MUNI[m['muni']]['name']}, meeting date {m['date']} ===\n{m['text']}"
        for i, m in enumerate(meetings)) + used_note

    today = date.today().strftime("%A, %B %d, %Y")
    out = call_claude(PROMPT.format(today=today, previews=listing))

    if out.get("meeting", -1) < 0 or not out.get("beats"):
        print("Sonnet found no genuinely consequential buried item this week — skipping.")
        return
    chosen = meetings[out["meeting"]]
    item_key = f"{chosen['slug']}#{slugify(out.get('item', 'item'))}"
    if item_key in used:
        sys.exit(f"Chosen item already used ({item_key}) — refusing to repeat.")
    print(f"\nPicked: {MUNI[chosen['muni']]['name']} {chosen['date']} — {out.get('item','')}")
    print(f"Reason: {out.get('reason','')}")

    # Second-pass fact check: nobody reviews this before publish, so every
    # claim gets verified against the source preview by a separate call.
    draft = json.dumps({"beats": out["beats"], "title": out.get("title", ""),
                        "caption": out.get("caption", "")}, indent=2)
    check = call_claude(VERIFY_PROMPT.format(n=len(out["beats"]),
                                             source=chosen["text"], draft=draft))
    print(f"Fact-check: {check.get('notes', '')}")
    if check.get("changed") and check.get("beats"):
        out["beats"] = check["beats"]
        out["title"] = check.get("title", out.get("title", ""))
        out["caption"] = check.get("caption", out.get("caption", ""))

    # Assemble the clip: eyebrow on beat 0 + the series' fixed CTA sign-off.
    beats = out["beats"]
    for b in beats:
        if len(b) > 80:
            print(f"  WARNING: beat over 80 chars ({len(b)}), will render small: {b!r}")
    script = [{"eyebrow": "Buried in the Agenda", "text": beats[0]}]
    script += [{"text": b} for b in beats[1:]]
    script.append({"text": "We read every agenda\nso you don’t have to.", "cta": True})

    url = preview_url(chosen)
    print("\n--- script ---")
    for s in script:
        print(f"  • {s['text']!r}")
    print(f"\nTitle:   {out.get('title','')}")
    print(f"Caption: {out.get('caption','')}")
    print(f"Link:    {url}")
    print(f"Tags:    {' '.join(out.get('hashtags', []))}")

    if args.dry_run:
        print("\n(dry run — not rendered)")
        return

    slug = f"buried-{chosen['date']}-{slugify(out.get('item', chosen['slug']))}"
    mp4 = render_short.render_from_config(slug, "buried-in-the-agenda", script)
    caption = f"{out.get('caption', '')}\n\nFull meeting preview: {url}"
    meta = {"slug": slug, "series": "buried-in-the-agenda",
            "source": {"preview": chosen["slug"], "item": out.get("item", "")},
            "title": out.get("title", ""), "caption": caption,
            "hashtags": out.get("hashtags", []), "script": script}
    with open(os.path.join(CARDS_DIR, f"short-{slug}.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\nMetadata -> short-{slug}.json")

    if not args.no_dedup:
        used.add(item_key)
        save_used(used)

    if args.publish:
        import publish_youtube_short as pub
        desc = pub.build_description(caption, out.get("hashtags", []))
        tags = [h.lstrip("#") for h in out.get("hashtags", [])] or ["Tucson"]
        vid = pub.upload(mp4, out.get("title", "Buried in the Agenda"), desc,
                         tags, args.privacy)
        # Machine-readable line for check_agendas.sh to grep for the Telegram note.
        print(f"SHORT-PUBLISHED\t{out.get('title','')}\thttps://www.youtube.com/shorts/{vid}")


if __name__ == "__main__":
    main()
