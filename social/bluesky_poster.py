#!/usr/bin/env python3
"""Bluesky ledger-diff poster (SOCIAL-AUTOPOST.md Part 3, v1).

Fully derived, zero model calls. Discovers published pages from sitemap.xml
(the canonical "actually published" list — every publishing pipeline rebuilds
it), diffs against a gitignored ledger, and posts anything new as a link card
composed from each page's own baked-in SEO meta (og:title / og:description /
og:image). Safe to full-auto because every page already passed its own
editorial gate before it reached the sitemap.

Usage:
    python3 bluesky_poster.py --seed       # mark back catalog as posted (first run)
    python3 bluesky_poster.py --dry-run    # show what would post, post nothing
    python3 bluesky_poster.py              # post new pages (oldest first)

Auth: BLUESKY_HANDLE + BLUESKY_APP_PASSWORD from the environment
(~/.config/environment.d/bluesky.conf — cron wrappers source every *.conf).
"""

import argparse
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

SOCIAL_DIR = Path(__file__).resolve().parent
ROOT = SOCIAL_DIR.parent
SITEMAP = ROOT / "sitemap.xml"
LEDGER = SOCIAL_DIR / "bluesky-ledger.json"          # gitignored
SESSION_FILE = SOCIAL_DIR / "bluesky-session.txt"    # gitignored

PUBLIC_MAP = ROOT / "assets" / "bluesky-posts.json"        # published — feeds bsky-comments.js

SITE = "https://tucsondailybrief.com/"
# Content sections only — hub pages, ask, about, crossword never post.
SECTIONS = ("posts/", "meeting-watch/", "news-reports/",
            "around-town/", "public-record/", "in-depth/")

MAX_GRAPHEMES = 300          # Bluesky post limit
MAX_THUMB_BYTES = 950_000    # blob upload ceiling, with headroom
MAX_AGE_DAYS = 7             # never post pages older than this (ledger-gap safety)
DEFAULT_MAX_PER_RUN = 8      # firehose guard

_TITLE_SUFFIX = re.compile(r"\s*(—|&mdash;)\s*Tucson Daily Brief.*$")
_META_RE = {
    "title": re.compile(r'<meta property="og:title" content="([^"]*)"'),
    "description": re.compile(r'<meta property="og:description" content="([^"]*)"'),
    "image": re.compile(r'<meta property="og:image" content="([^"]*)"'),
}
_H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
_P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_DATE_TITLE = re.compile(r"^\w+day, \w+ \d{1,2}, \d{4}( at \d{1,2}:\d{2} [AP]M)?$")
_STATS_DEK = re.compile(r"^\d+ substantive items? on the agenda")


def log(msg: str) -> None:
    print(f"[bluesky] {msg}")


def sitemap_entries() -> list[dict]:
    """Content-section URLs from sitemap.xml with lastmod, oldest first."""
    tree = ET.parse(SITEMAP)
    out = []
    for url_el in tree.getroot().findall("{*}url"):
        loc = url_el.findtext("{*}loc", "").strip()
        lastmod = url_el.findtext("{*}lastmod", "").strip()
        rel = loc.removeprefix(SITE)
        if rel != loc and rel.startswith(SECTIONS):
            out.append({"url": loc, "rel": rel, "lastmod": lastmod})
    out.sort(key=lambda e: (e["lastmod"], e["rel"]))
    return out


def load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {"posted": {}}


def save_ledger(ledger: dict) -> None:
    LEDGER.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n")


def export_public_map(ledger: dict) -> bool:
    """Write the page-URL → post-URI map that /assets/bsky-comments.js reads.

    Only real posts (entries with a "uri") are exported — seeded and stale
    entries have no thread to show. Returns True when the file changed.
    """
    mapping = {url: rec["uri"] for url, rec in ledger["posted"].items() if rec.get("uri")}
    text = json.dumps(mapping, indent=1, sort_keys=True) + "\n"
    if PUBLIC_MAP.exists() and PUBLIC_MAP.read_text() == text:
        return False
    PUBLIC_MAP.write_text(text)
    return True


def push_public_map() -> None:
    """Commit + push the public map so the live site's comment sections light
    up. Non-fatal: every pipeline pushes from this machine, so failures here
    just mean the map rides along with the next pipeline push."""
    import subprocess
    for cmd in (["git", "add", "assets/bluesky-posts.json"],
                ["git", "commit", "-m", "Update Bluesky comments map"],
                ["git", "push"]):
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            log(f"WARNING: {' '.join(cmd[:2])} failed (non-fatal): "
                f"{(r.stderr or r.stdout).strip()[:200]}")
            return
    log("comments map committed and pushed")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def page_meta(rel: str) -> dict | None:
    """Pull og meta + h1 from the local published HTML."""
    path = ROOT / rel
    if not path.exists():
        log(f"WARNING: {rel} in sitemap but missing on disk — skipped")
        return None
    src = path.read_text(errors="replace")
    meta = {}
    for key, rx in _META_RE.items():
        m = rx.search(src)
        meta[key] = clean(m.group(1)) if m else ""
    m = _H1_RE.search(src)
    meta["h1"] = clean(_TAG_RE.sub("", m.group(1))) if m else ""
    meta["paragraphs"] = [clean(_TAG_RE.sub("", p.group(1)))
                          for p in _P_RE.finditer(src)][:40]
    # Agenda-item headings (meeting previews' "Top Items to Watch" h3s, ranked
    # by the miners) — leading emoji is on-page structure, stripped here.
    meta["items"] = [re.sub(r"^[\W_]+", "", clean(_TAG_RE.sub("", m.group(1))))
                     for m in re.finditer(r"<h3[^>]*>(.*?)</h3>", src, re.S)][:12]
    return meta


def expand_dek(dek: str, paragraphs: list[str]) -> str:
    """A dek ending in '…' is derive_description()'s 160-char meta cut. Find the
    lede paragraph it was cut from and refit it as complete sentences within the
    300-grapheme post limit instead — still fully derived, never mid-sentence."""
    stub = dek.rstrip("… .").strip()
    key = stub[:50].lower()
    if not key:
        return dek
    for p in paragraphs:
        if not p.lower().startswith(key):
            continue
        fitted = ""
        for sent in _SENT_SPLIT.split(p):
            cand = (fitted + " " + sent).strip()
            if len(cand) > MAX_GRAPHEMES:
                break
            fitted = cand
        return fitted or dek  # first sentence alone >300 → keep dek, truncate later
    return dek  # constructed deks (daily briefs) match no paragraph — keep as-is


def compose(rel: str, meta: dict) -> dict:
    """Derive post text + card copy. No model, no new facts.

    Card title carries the headline; post text carries the dek — the
    card-vs-caption rule (BRAND-BIBLE.md): never say the same thing twice.
    """
    headline = _TITLE_SUFFIX.sub("", meta["title"]).strip()
    # Meeting previews bake the date into og:title; the h1 has the real subject
    # ("{Body} — What to Watch" across all four miners).
    if rel.startswith("meeting-watch/") or not headline or _DATE_TITLE.match(headline):
        headline = meta["h1"] or headline
    if headline.endswith("— What to Watch"):
        headline = "What to Watch: " + headline.removesuffix("— What to Watch").strip(" —")
    dek = meta["description"]
    if dek.endswith("…"):
        dek = expand_dek(dek, meta["paragraphs"])
    # Pima BOS previews have no lede paragraph, so the derived description is a
    # bare stats line with no date. Assemble one from the page's own parts —
    # glue words only, no new facts.
    date_title = _TITLE_SUFFIX.sub("", meta["title"]).strip()
    if _STATS_DEK.match(dek) and _DATE_TITLE.match(date_title):
        body = meta["h1"].removesuffix("— What to Watch").strip(" —")
        dek = f"The {body} meets {date_title} — {dek}."
    text = dek if dek and dek.lower() != headline.lower() else headline
    # Meeting previews: lead with the page's own top-ranked agenda item when it
    # fits — the lede alone can undersell the meeting (a "land use item" that is
    # actually the data-center rules hearing).
    if rel.startswith("meeting-watch/") and meta.get("items"):
        cand = f"{text}\n\nTop of the agenda: {meta['items'][0]}"
        if len(cand) <= MAX_GRAPHEMES:
            text = cand
    if len(text) > MAX_GRAPHEMES:
        text = text[: MAX_GRAPHEMES - 1].rsplit(" ", 1)[0].rstrip(",;:—- ") + "…"
    # Text carries the dek, card carries the headline — leave the card description
    # empty so the same sentence never renders twice in one post.
    return {"text": text, "card_title": headline or "Tucson Daily Brief",
            "card_desc": "", "image": meta["image"]}


def thumb_bytes(image_url: str, cache: dict) -> bytes | None:
    """Local bytes for an og:image on our own domain (Bluesky won't fetch OG)."""
    if not image_url.startswith(SITE):
        return None
    if image_url in cache:
        return cache[image_url]
    path = ROOT / image_url.removeprefix(SITE)
    data = path.read_bytes() if path.exists() else None
    if data and len(data) > MAX_THUMB_BYTES:
        try:  # soft dependency — a page with an oversized image just posts without a thumb
            import io
            from PIL import Image
            im = Image.open(io.BytesIO(data)).convert("RGB")
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=80)
            data = buf.getvalue() if len(buf.getvalue()) <= MAX_THUMB_BYTES else None
        except Exception:
            data = None
    cache[image_url] = data
    return data


def get_client():
    from atproto import Client
    client = Client()
    if SESSION_FILE.exists():
        try:
            client.login(session_string=SESSION_FILE.read_text().strip())
            return client
        except Exception as exc:
            log(f"saved session invalid ({exc}); logging in fresh")
    handle = os.environ.get("BLUESKY_HANDLE")
    password = os.environ.get("BLUESKY_APP_PASSWORD")
    if not handle or not password:
        sys.exit("[bluesky] ERROR: BLUESKY_HANDLE / BLUESKY_APP_PASSWORD not set")
    client.login(handle, password)
    SESSION_FILE.write_text(client.export_session_string())
    return client


def post_page(client, entry: dict, composed: dict, blob_cache: dict):
    from atproto import models
    thumb = None
    data = thumb_bytes(composed["image"], blob_cache.setdefault("bytes", {}))
    if data is not None:
        blobs = blob_cache.setdefault("blobs", {})
        if composed["image"] not in blobs:
            blobs[composed["image"]] = client.upload_blob(data).blob
        thumb = blobs[composed["image"]]
    embed = models.AppBskyEmbedExternal.Main(
        external=models.AppBskyEmbedExternal.External(
            uri=entry["url"],
            title=composed["card_title"],
            description=composed["card_desc"],
            thumb=thumb,
        ))
    return client.send_post(text=composed["text"], embed=embed, langs=["en"])


def announce(client, text: str, url: str, blob_cache: dict):
    """Post hand-written copy with a link card for one of our own pages.

    The ONLY non-derived path in this file, for announcements that aren't a
    published page ("we now cover the school districts"). Deliberately narrow:

      * It never touches the ledger. Nothing here came from the sitemap, so
        there is nothing to mark as posted, and writing to the ledger could
        suppress a real page later.
      * No cron wiring, ever. It requires --announce, so an unattended run
        cannot reach it. Automation posts only what the site already published.
      * Over-length is an ERROR, not a truncation. compose() may trim derived
        text because a machine wrote it; hand-written copy that gets silently
        cut mid-word is worse than a failed command.

    The card title comes from the target page's own og:title and the
    description stays empty — same "never say the same thing twice" rule the
    derived path follows, since the post text is doing that work.
    """
    from atproto import models
    rel = url.removeprefix(SITE) or "index.html"
    meta = page_meta(rel) or {"title": "Tucson Daily Brief", "image": ""}
    thumb = None
    data = thumb_bytes(meta["image"], blob_cache.setdefault("bytes", {}))
    if data is not None:
        thumb = client.upload_blob(data).blob
    embed = models.AppBskyEmbedExternal.Main(
        external=models.AppBskyEmbedExternal.External(
            uri=url,
            title=meta["title"] or "Tucson Daily Brief",
            description="",
            thumb=thumb,
        ))
    return client.send_post(text=text, embed=embed, langs=["en"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", action="store_true",
                    help="mark every current sitemap URL as posted, post nothing")
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would post without posting")
    ap.add_argument("--max-per-run", type=int, default=DEFAULT_MAX_PER_RUN)
    ap.add_argument("--announce", metavar="TEXT|@FILE",
                    help="post hand-written copy with a link card (manual only; "
                         "'@path' reads the text from a file). Never ledgered.")
    ap.add_argument("--announce-url", default=SITE, metavar="URL",
                    help=f"page the announce link card points at (default {SITE})")
    args = ap.parse_args()

    if args.announce:
        text = args.announce
        if text.startswith("@"):
            text = Path(text[1:]).read_text().strip()
        if not text:
            sys.exit("[bluesky] ERROR: --announce text is empty")
        if len(text) > MAX_GRAPHEMES:
            sys.exit(f"[bluesky] ERROR: {len(text)} chars, limit {MAX_GRAPHEMES} "
                     f"— edit the copy, this path will not truncate it")
        if not args.announce_url.startswith(SITE):
            sys.exit(f"[bluesky] ERROR: --announce-url must be on {SITE}")
        log(f"announce ({len(text)}/{MAX_GRAPHEMES} chars) → {args.announce_url}")
        print("-" * 60 + f"\n{text}\n" + "-" * 60)
        if args.dry_run:
            log("dry run — nothing posted")
            return
        res = announce(get_client(), text, args.announce_url, {})
        log(f"posted: {res.uri}")
        return

    entries = sitemap_entries()
    ledger = load_ledger()
    posted = ledger["posted"]
    now = datetime.now()

    if args.seed:
        fresh = 0
        for e in entries:
            if e["url"] not in posted:
                posted[e["url"]] = {"at": now.isoformat(timespec="seconds"), "seeded": True}
                fresh += 1
        save_ledger(ledger)
        log(f"seeded {fresh} URLs ({len(posted)} total in ledger)")
        return

    new = [e for e in entries if e["url"] not in posted]
    stale, queue = [], []
    for e in new:
        try:
            age = (now - datetime.strptime(e["lastmod"], "%Y-%m-%d")).days
        except ValueError:
            age = MAX_AGE_DAYS + 1
        (queue if age <= MAX_AGE_DAYS else stale).append(e)

    for e in stale:  # too old to post — ledger them so they stop reappearing
        posted[e["url"]] = {"at": now.isoformat(timespec="seconds"), "skipped": "stale"}
        log(f"stale ({e['lastmod']}), ledgered without posting: {e['rel']}")

    if len(queue) > args.max_per_run:
        log(f"NOTE: {len(queue)} new pages, capping at {args.max_per_run} this run "
            f"({len(queue) - args.max_per_run} deferred to next run)")
        queue = queue[: args.max_per_run]

    if not queue:
        if stale and not args.dry_run:
            save_ledger(ledger)
        log("nothing new to post")
        return

    client = None
    blob_cache: dict = {}
    failures = 0
    for e in queue:
        meta = page_meta(e["rel"])
        if meta is None:
            continue
        composed = compose(e["rel"], meta)
        if args.dry_run:
            log(f"DRY RUN would post: {e['rel']}")
            log(f"  text: {composed['text']}")
            log(f"  card: {composed['card_title']} | {composed['card_desc']}")
            continue
        try:
            if client is None:
                client = get_client()
            ref = post_page(client, e, composed, blob_cache)
            posted[e["url"]] = {"at": now.isoformat(timespec="seconds"), "uri": ref.uri}
            log(f"posted: {e['rel']} → {ref.uri}")
        except Exception as exc:
            failures += 1
            log(f"ERROR posting {e['rel']}: {exc}")  # not ledgered — retries next run

    if not args.dry_run:
        save_ledger(ledger)
        if export_public_map(ledger):
            push_public_map()
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
