# Add the TDB Podcast to Spotify — Do-It-Later Checklist

**Status (2026-06-30):** Feed is validated and 100% ready to submit. The *only*
blocker is a Spotify-side login bug — Spotify support confirmed a known **login
redirect loop** in the Spotify for Creators portal that day. Nothing is wrong
with our account or feed. Just retry the portal login later (next day usually
clears it) and run the steps below.

No code change is needed, ever. Spotify just re-polls the same `feed.xml` that
`run_podcast.sh` already updates every morning, so new episodes appear
automatically after the one-time submission.

---

## Your feed URL (paste this into Spotify)

```
https://pub-9552aa4d76834cea9f9e35f908b604e4.r2.dev/feed.xml
```

## Feed validation — already passed (2026-06-30)

| Requirement | Status |
|---|---|
| Feed reachable | ✅ HTTP 200, `application/rss+xml` |
| Episodes | ✅ 128 `<item>`s, all with reachable `audio/mpeg` `<enclosure>`s |
| Owner email | ✅ `nicholas@daylayown.org` (Spotify sends the verification code here) |
| Cover art | ✅ 3000×3000 PNG (Spotify wants 1400–3000 square — at max) |
| Category / language / explicit | ✅ News / `en-us` / present |

To re-validate later if you want to double-check, see "Re-validate the feed" below.

---

## Submission steps

1. Go to **https://creators.spotify.com** (the rebranded Spotify for Podcasters /
   Anchor) and log in with any Spotify account (a free account is fine).
2. Click **Add your podcast** (a.k.a. "Get started" / "Add or claim").
3. Paste the feed URL above.
4. **Verify ownership:** Spotify emails an **8-digit code** to the address in the
   feed — **`nicholas@daylayown.org`**. Confirm that inbox/forwarding is reachable
   *before* you start so you're not stuck waiting. Enter the code.
5. Confirm the auto-pulled details (title = Tucson Daily Brief, category = News,
   country, language), then **Submit**.
6. Spotify reviews + publishes — usually a few hours, sometimes minutes,
   occasionally up to ~5 days.

---

## If the login loop is still happening

It's a cross-site auth-cookie problem. In order of likelihood:

1. **Allow third-party cookies + clear Spotify cookies.** Clear all cookies for
   `spotify.com`, then allow third-party cookies (or add an exception for
   `spotify.com` / `creators.spotify.com`). #1 cause.
2. **Use plain Chrome.** Safari "Prevent cross-site tracking" and Firefox/Brave
   tracking protection break this exact redirect. A clean Chrome profile with no
   extensions is the most reliable.
3. **Disable privacy extensions / VPN** for the session (uBlock, Privacy Badger,
   Ghostery, AdGuard, etc.).
4. **"Sign out everywhere" first** (main Spotify site → Account), then log into
   the creators portal fresh — multiple active Spotify sessions confuse the
   redirect.
5. **Match your login method** — if the account was created with "Continue with
   Google/Apple/Facebook," use that same button (don't use email/password on a
   social-auth account).
6. Quick isolation test: try once in an **incognito window** with third-party
   cookies allowed. If it works there, it's a cookie/extension issue in your
   normal profile.

---

## After it's live

- Grab your **Spotify show URL** and add it to:
  - the site footer (alongside Apple Podcasts + YouTube),
  - the social "link in comments" / link-in-bio for podcast promo posts.
- Optional: the podcast **cover art predates the 2026-05-11 site redesign** — a
  natural moment to refresh it to the warm-Southwest visual language, but not
  required to submit.

---

## Re-validate the feed (optional, if revisiting much later)

```bash
FEED="https://pub-9552aa4d76834cea9f9e35f908b604e4.r2.dev/feed.xml"
curl -sS -o /tmp/feed.xml -w "HTTP %{http_code} type=%{content_type}\n" "$FEED"
grep -c "<item>" /tmp/feed.xml                       # episode count
grep -o '<itunes:email>[^<]*</itunes:email>' /tmp/feed.xml | head -1
COVER=$(grep -o '<itunes:image href="[^"]*"' /tmp/feed.xml | head -1 | sed 's/.*href="//;s/"//')
curl -sS -o /tmp/cover.img "$COVER"; identify /tmp/cover.img   # must be 1400–3000 square
```
