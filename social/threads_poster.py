#!/usr/bin/env python3
"""Threads ledger-diff poster (SOCIAL-AUTOPOST.md — Threads port of Part 3 v1).

Same architecture as bluesky_poster.py, whose derivation helpers this imports:
discover published pages from sitemap.xml, diff against a gitignored ledger,
post anything new as derived text + a link attachment (Threads fetches the
page's own og: meta for the preview card server-side — no blob upload needed).
Fully derived, zero model calls, so full-auto under the Part 2 tiered rule.

Threads-specific plumbing:
  * Auth is a long-lived user token (60 days). refresh_token_if_due() refreshes
    it via th_refresh_token once it's REFRESH_EVERY_DAYS old and rewrites
    ~/.config/environment.d/threads.conf in place (mode 0600 preserved).
    State (last refresh time) lives in social/threads-state.json (gitignored).
  * Publishing is the two-step container flow: POST /{uid}/threads (creation)
    then POST /{uid}/threads_publish.

Usage:
    python3 threads_poster.py --seed       # mark back catalog as posted (first run)
    python3 threads_poster.py --dry-run    # show what would post, post nothing
    python3 threads_poster.py              # post new pages (oldest first)

Auth: THREADS_ACCESS_TOKEN / THREADS_USER_ID / THREADS_APP_ID / THREADS_APP_SECRET
from the environment (~/.config/environment.d/threads.conf).
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from bluesky_poster import (  # same directory; pure derivation helpers
    DEFAULT_MAX_PER_RUN,
    MAX_AGE_DAYS,
    compose,
    page_meta,
    sitemap_entries,
)

SOCIAL_DIR = Path(__file__).resolve().parent
LEDGER = SOCIAL_DIR / "threads-ledger.json"        # gitignored
STATE = SOCIAL_DIR / "threads-state.json"          # gitignored — token refresh clock
CONF = Path.home() / ".config/environment.d/threads.conf"

GRAPH = "https://graph.threads.net/v1.0"
REFRESH_EVERY_DAYS = 7        # refresh well inside the 60-day expiry
MIN_TOKEN_AGE_HOURS = 24      # Threads refuses to refresh tokens younger than this


def log(msg: str) -> None:
    print(f"[threads] {msg}")


def api(method: str, path: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode()
    if method == "GET":
        req = urllib.request.Request(f"{path}?{urllib.parse.urlencode(params)}")
    else:
        req = urllib.request.Request(path, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")[:300]
        raise RuntimeError(f"{exc.code} on {path}: {body}") from exc


def load_json(path: Path, default: dict) -> dict:
    return json.loads(path.read_text()) if path.exists() else default


def save_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")


def refresh_token_if_due(token: str) -> str:
    """Refresh the long-lived token once it's REFRESH_EVERY_DAYS old and write
    it back to threads.conf. Non-fatal: on any failure the current token is
    kept (it stays valid ~60 days from its own issue)."""
    state = load_json(STATE, {})
    now = datetime.now()
    last = state.get("refreshed_at")
    if last is None:
        # First sighting of this token — start the clock, don't refresh yet
        # (tokens under 24h old are refused anyway).
        save_json(STATE, {"refreshed_at": now.isoformat(timespec="seconds")})
        return token
    age_days = (now - datetime.fromisoformat(last)).days
    if age_days < REFRESH_EVERY_DAYS:
        return token
    try:
        res = api("GET", "https://graph.threads.net/refresh_access_token",
                  {"grant_type": "th_refresh_token", "access_token": token})
        new_token = res["access_token"]
    except Exception as exc:
        log(f"WARNING: token refresh failed (non-fatal, current token kept): {exc}")
        return token
    lines = CONF.read_text().splitlines()
    lines = [f"THREADS_ACCESS_TOKEN={new_token}"
             if ln.startswith("THREADS_ACCESS_TOKEN=") else ln for ln in lines]
    tmp = CONF.with_suffix(".conf.tmp")
    tmp.write_text("\n".join(lines) + "\n")
    tmp.chmod(0o600)
    os.replace(tmp, CONF)
    save_json(STATE, {"refreshed_at": now.isoformat(timespec="seconds")})
    log(f"token refreshed (was {age_days}d since last) and written to {CONF.name}")
    return new_token


def post_page(uid: str, token: str, url: str, text: str) -> dict:
    creation = api("POST", f"{GRAPH}/{uid}/threads", {
        "media_type": "TEXT", "text": text,
        "link_attachment": url, "access_token": token,
    })
    published = api("POST", f"{GRAPH}/{uid}/threads_publish", {
        "creation_id": creation["id"], "access_token": token,
    })
    post_id = published["id"]
    permalink = ""
    try:
        permalink = api("GET", f"{GRAPH}/{post_id}",
                        {"fields": "permalink", "access_token": token})["permalink"]
    except Exception:
        pass  # cosmetic only
    return {"id": post_id, "permalink": permalink}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", action="store_true",
                    help="mark every current sitemap URL as posted, post nothing")
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would post without posting")
    ap.add_argument("--max-per-run", type=int, default=DEFAULT_MAX_PER_RUN)
    args = ap.parse_args()

    token = os.environ.get("THREADS_ACCESS_TOKEN")
    uid = os.environ.get("THREADS_USER_ID")
    if not token or not uid:
        sys.exit("[threads] ERROR: THREADS_ACCESS_TOKEN / THREADS_USER_ID not set")

    entries = sitemap_entries()
    ledger = load_json(LEDGER, {"posted": {}})
    posted = ledger["posted"]
    now = datetime.now()

    if args.seed:
        fresh = 0
        for e in entries:
            if e["url"] not in posted:
                posted[e["url"]] = {"at": now.isoformat(timespec="seconds"), "seeded": True}
                fresh += 1
        save_json(LEDGER, ledger)
        log(f"seeded {fresh} URLs ({len(posted)} total in ledger)")
        return

    token = refresh_token_if_due(token)

    new = [e for e in entries if e["url"] not in posted]
    stale, queue = [], []
    for e in new:
        try:
            age = (now - datetime.strptime(e["lastmod"], "%Y-%m-%d")).days
        except ValueError:
            age = MAX_AGE_DAYS + 1
        (queue if age <= MAX_AGE_DAYS else stale).append(e)

    for e in stale:
        posted[e["url"]] = {"at": now.isoformat(timespec="seconds"), "skipped": "stale"}
        log(f"stale ({e['lastmod']}), ledgered without posting: {e['rel']}")

    if len(queue) > args.max_per_run:
        log(f"NOTE: {len(queue)} new pages, capping at {args.max_per_run} this run")
        queue = queue[: args.max_per_run]

    if not queue:
        if stale and not args.dry_run:
            save_json(LEDGER, ledger)
        log("nothing new to post")
        return

    failures = 0
    for e in queue:
        meta = page_meta(e["rel"])
        if meta is None:
            continue
        composed = compose(e["rel"], meta)
        if args.dry_run:
            log(f"DRY RUN would post: {e['rel']}")
            log(f"  text: {composed['text']}")
            continue
        try:
            ref = post_page(uid, token, e["url"], composed["text"])
            posted[e["url"]] = {"at": now.isoformat(timespec="seconds"),
                                "id": ref["id"], "permalink": ref["permalink"]}
            log(f"posted: {e['rel']} → {ref['permalink'] or ref['id']}")
        except Exception as exc:
            failures += 1
            log(f"ERROR posting {e['rel']}: {exc}")  # not ledgered — retries next run

    if not args.dry_run:
        save_json(LEDGER, ledger)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
