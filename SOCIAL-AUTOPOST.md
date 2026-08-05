# Facebook Strategy + Social Auto-Posting

Discussion + feasibility, **2026-06-26**. Two halves: (1) why Facebook is its own game for TDB's audience and how to post to it, and (2) what it takes to *automate* posting across all of TDB's social surfaces. Companion to the `project_social_promo_strategy` memory and `SHORT-FORM-VIDEO.md` (the auto-post layer described here IS that project's "thin publish layer"). Tooling lives in `social/` (`render_card.py`, `render_story.py`, etc.).

---

## Part 1 — Facebook vs. Instagram playbook

**Why FB matters most for TDB:** Southern Arizona skews **old** (Green Valley, SaddleBrooke, Oro Valley are retiree-dense), and older Americans live on Facebook. FB is likely TDB's **#1 organic channel for actual Tucsonans** — and almost nobody optimizes for it because it's not the "cool" platform.

**The catch — Meta buried the news feed.** Meta has spent years deprioritizing news/political/link content in the main feed. So you can't pipe links and expect reach. Winners are **native, engagement-driving** posts: image cards, questions, nostalgia, "did you know," photos. Lead with those; treat links as secondary.

**Three things FB does that IG can't:**
1. **Links work** (clickable, with previews) → real traffic to tucsondailybrief.com. But Meta throttles the reach of posts with a link in the body → use the **first-comment link trick** (post the image natively, drop the link as the first comment).
2. **Groups are the unlock** — Tucson has huge active groups (nostalgia "You know you grew up in Tucson if…", neighborhood, local-news). Distribution channel IG has no equivalent for. ⚠️ Etiquette: most ban overt self-promo and auto-posting gets you flagged — be a genuine member who shares **where it's truly on-topic**, build reputation, don't blast.
3. **Share culture + longer text** → nostalgia/community posts *travel* via shares (IG has no native re-share).

**Content mapping (same card, different captions):**

| Content | IG | Facebook |
|---|---|---|
| Nostalgia / local history (e.g. Old Tucson) | good | **peak FB** (shares + Groups) |
| Weather/safety alerts | Story | **great** (older audience shares to family) |
| "What's opening / closing" | good | **great** |
| Civic/government news | meh | **good** (older = more civically engaged) |
| Aesthetic carousels / Reels / Stories | **IG-leaning** | secondary |

Rule of thumb: **same card on both, write the caption twice** — IG tight + hashtags; FB longer + nostalgic + link-in-first-comment, no markdown asterisks (FB renders them literally).

**Worked example — FB-tailored Old Tucson post** (2026-06-26, the card was `social/cards/news-old-tucson-2026-06-26.png`):
> Well, here's one we didn't expect to see this week. 🤠
>
> Old Tucson — the historic Western movie set and theme park out west of the city — has been listed for sale, with an asking price of $1.5 million.
>
> If you grew up around here (or raised your kids here), there's a good chance Old Tucson is tied up in a memory or two: the staged gunfights on Main Street, the little train, a school field trip, maybe even a movie or show you know was filmed out there over the years.
>
> So we want to hear from you — what's your favorite Old Tucson memory? Tell us in the comments, we'll be reading. 👇

First comment: `🔗 Details via KVOA News 4: [link] — and we round up Tucson news like this every morning at tucsondailybrief.com 🌵`

**Cadence:** one well-chosen post a day (the most human/nostalgic/civic item), cross-posted from the IG card with an FB caption, plus genuine Group participation when something fits. Quality + Groups beats frequency.

---

## Part 2 — Auto-posting feasibility

**The dream (user, 2026-06-26):** "wake up and see all my socials populated with relevant content without doing anything." Verdict: **very possible, ~70% of the pieces already exist, and it's on-lane with the short-form-video project (not feature creep).** The posting is the easy part; the value/risk is in the editorial brain + Meta's app gates.

### What's auto-postable (own accounts, real APIs)

| Surface | Auto-post? | How |
|---|---|---|
| **Instagram** (feed + Stories) | ✅ | Content Publishing API: `POST /{ig-user-id}/media` (image_url from R2) → `POST /{ig-user-id}/media_publish`; Stories via `media_type=STORIES`. Needs a Meta app + `instagram_content_publish` (Standard Access). |
| **Facebook Page** | ✅ | Graph API `POST /{page-id}/photos` (url + caption). **First-comment link trick is also automatable:** `POST /{post-id}/comments`. Needs `pages_manage_posts`. |
| **Threads** | ✅ | Threads API (Meta shipped it 2024), own account. |
| **Bluesky** | ✅ trivially | AT Protocol + app password, `com.atproto.repo.createRecord` + blob upload. **Zero gatekeeper.** (No TDB account yet.) |
| **X (Twitter)** | ⚠️ pay-per-use | Verified 2026-08-04 (this doc originally skipped X — no account, personal-social rule). **The free API tier is gone**: closed to new developers, and the legacy Basic ($200/mo) / Pro ($5,000/mo) tiers are closed too, with remaining subscribers migrated off. Since **Feb 2026** new developers get **pay-per-use credits: ~$0.015 per post created, but ~$0.20 per post containing a link** — a 13× link tax aimed squarely at publishers. At TDB volume that's ~$6/mo for a daily linked post, pennies for card-only posts. **Posture: manual first.** A brand account posting the existing 2 packages/week via the app costs $0 and minutes; only buy API credits if X shows a pulse worth automating. (A reader emailed 2026-08-04 asking TDB to post on X — first organic channel request from any platform. Brand-account precedent: FB/IG were added as brand accounts under the personal-social rule, so `@tucsondailybrief` on X is consistent if the user wants it.) Sources: wearefounders.uk, postproxy.dev, api.sorsa.io, opentweet.io pricing trackers — re-verify before building, X pricing churns. |
| **FB & IG _Groups_** | ❌ **No** | **Meta sunset the Groups API in 2024** — group posting via API is dead. Groups stay a **manual** move (which suits Group etiquette anyway). |
| **LinkedIn** | (separate) | Technically automatable, but **keep it its own track** — different voice, journalism-industry audience; user wants those wires uncrossed. |

### You already own ~70%
- `social/render_card.py` / `render_story.py` → the cards (format proven this session: Old Tucson, weather).
- **R2 bucket** → public image hosting (what IG/FB publishing require).
- `upload_to_youtube.py` → OAuth auto-publish precedent (same shape).
- `social/generate_short.py` → already **picks a story with Haiku and posts fully unattended** to YouTube → working zero-touch precedent.
- Telegram approve flow → already used for news reports + newsletter.

### Architecture to build
1. **Editorial brain** (`generate_social.py` or similar): Sonnet reads the morning brief → picks the day's best social story(ies) → emits card config + **per-platform captions** (IG/FB/Threads/Bluesky variants) → renders the card → uploads to R2. (Half-exists conceptually as the Short's Haiku story-picker.)
2. **Publish adapters** — one thin OAuth-per-platform module each (FB Page, IG, Threads, Bluesky).
3. **Approve gate** — Telegram message with card preview + captions + ✅/✏️/❌ → on ✅, fan out to all surfaces. (Reuse existing Telegram pattern.)
4. **Cron** — runs after the 6:10 brief; posts to Telegram for approval; user taps from bed.

### The one real decision: full-auto vs. one-tap — tiered, per the quality bar
TDB's strict no-fabrication bar ([[feedback_ai_content_quality_bar]]) was hit **twice on 2026-06-26 alone** (a "since we were kids" brand-backstory claim; the weather "broadcasters reported it" hedge). A wrong fact on a public card spreads faster than a buried blog line. So:
- **Fully unattended** for evergreen/safe content (what the daily Short already does).
- **5-second Telegram one-tap approve** for news/civic cards — delivers ~95% of the "mental unlock" (no writing, no story-picking, no rendering, no posting) while keeping a human eye between the AI and a permanent public post. **Recommended default for news.**

### Build order (each de-risks the next)
1. **Bluesky** — zero gate; proves the whole render→caption→publish→approve loop. (Make an account first.)
2. **Threads** — own account, straightforward.
3. **Facebook Page** — needs a Meta app; for your *own* page there's likely a no-review path via dev-mode/business assets — **verify live**.
4. **Instagram** — same Meta app, `instagram_content_publish`; the app-review queue is the **only real calendar-time variable** (the code is trivial).
5. **X** — *if at all*, and manual before API. Pay-per-use credits (see table) mean automation is ~$6/mo, not free; earn it with evidence first. Reality check that motivates the ordering: as of 2026-08-04 the measured audiences are **IG 250 · newsletter 31 · FB 3** (see the `project_channel_baselines` memory) — the FB "#1 organic channel" thesis from Part 1 is untested at current effort level, and channel decisions should start from those numbers.

**Gate per [[feedback_resist_feature_creep]]:** this is the publish layer of the short-form-video project (the user's chosen next big build) — build it *alongside* that, don't start mid-stream without a green light. The format is now arguably proven (multiple cards shipped this session), which was the original deferral condition.

---

## Part 3 — Bluesky/ATProto build plan (locked 2026-08-04; **v1 BUILT + LIVE same day**)

**Status:** account live as `@tucsondailybrief.com` (domain handle verified via Cloudflare TXT, DID `did:plc:mo77ybho6xbkzjbzfdaxmhrn`), app password in `~/.config/environment.d/bluesky.conf`, `atproto` SDK installed `--user`. v1 shipped as `social/bluesky_poster.py`; ledger seeded with the 366-page back catalog; first three posts (2026-08-04 brief + Marana/Tucson council previews) published 2026-08-04. Wired: end of `check_agendas.sh` (8 AM) + `run_bluesky_post.sh` catch-all crons at 6:45 AM/4:45 PM (`/tmp/bluesky-post.log`). Build refinements vs the plan below: discovery reads **`sitemap.xml`** (the canonical published list every pipeline rebuilds) instead of re-scanning section dirs; compose reads each page's **baked og: meta** instead of calling the SEO helpers; post text carries the dek and the link card carries the headline (card description left empty — never say the same thing twice); Pima BOS previews get a date sentence assembled from the page's own strings (their pages have no lede, only a stats strip); a dek ending in "…" (derive_description's 160-char meta cut) is re-fit from the page's lede paragraph as complete sentences within the 300-grapheme limit — never post mid-sentence text; meeting previews append "Top of the agenda: {first Top-Items h3}" when it fits, because the lede alone can undersell the meeting (the 8/5 Tucson lede said "two significant land use items" without naming the data-center rules hearing — the miners' own item ranking supplies the emphasis, no model call); >7-day-old pages are ledgered without posting (ledger-gap safety); 8 posts/run cap. Session string cached in `social/bluesky-session.txt` (gitignored, like the ledger).

**Account posture: brand account** (`@tucsondailybrief`), decided 2026-08-04 — same personal-social-rule carve-out as FB/IG. Purpose: extend TDB's reach / new audiences. Context: AZPM's Bluesky went dormant (PIPELINE.md) — Tucson presence on the network is thin, which is both the opportunity and the audience caveat. Baselines say Bluesky = 0 today; the justification is zero marginal cost once automated + this being the proving ground for the whole publish-adapter stack (build order, Part 2).

**Day-one move, before any code: domain handle.** Set the handle to `@tucsondailybrief.com` via DNS TXT `_atproto.tucsondailybrief.com` — free, instant, ATProto's built-in anti-impersonation verification.

### v1 — ledger-diff poster (`social/bluesky_poster.py`), fully derived, full-auto

Do **not** bolt posting into each pipeline. One decoupled script, the published site as source of truth:

1. **Discover** published URLs by scanning the section dirs the way `rebuild_homepage()` does (`posts/`, `meeting-watch/`, `news-reports/`, `around-town/`, `public-record/`, `in-depth/`).
2. **Diff** against a posted-ledger (gitignored SQLite/JSON, like `promise-ledger/`). **Seed the ledger with the live back catalog on first run** or it firehoses ~400 old pages.
3. **Compose** from the SEO layer — `extract_headline()` + `derive_description()` + link card. Zero model calls, zero fabrication risk; safe to full-auto because every page already passed its own editorial gate. Register: neutral/watchful for briefs/previews/decided; warmer allowed for Around Town/Spotted (BRAND-BIBLE.md).
4. **Post** via the official `atproto` Python SDK (app password in `~/.config/environment.d/`, same pattern as anthropic.conf).

Idempotent by construction, so wire it cheaply: end of `run_podcast.sh`, end of `check_agendas.sh`, plus a late-morning catch-all cron. `ai_reporter.py` needs no changes — human-approved reports get picked up on the next run, so the review gate stays upstream.

**Mechanics gotchas:** 300-grapheme limit; link facets use **UTF-8 byte offsets** (off-by-emoji bug); the link-card thumbnail must be uploaded as a blob ≤~1MB per post (Bluesky won't fetch OG images — reuse each page's OG image, compress if needed). Rate limits are a non-issue at TDB volume.

### Manual announcements — `--announce` (added 2026-08-04)

`bluesky_poster.py --announce "TEXT|@file" [--announce-url URL]` posts
hand-written copy with a link card to one of our own pages. The **only**
non-derived path in that file, and deliberately narrow: it never touches the
ledger (nothing came from the sitemap, and a stray entry could suppress a real
page later), it is never cron-wired (it requires the flag, so an unattended run
cannot reach it), and over-length copy is a **hard error rather than a
truncation** — `compose()` may trim machine-written text, but silently cutting
hand-written copy mid-word is worse than a failed command. Card title comes
from the target page's own `og:title`, description stays empty (same "never say
the same thing twice" rule). Use `--dry-run` first; it prints the copy and the
character count.

**First use, 2026-08-04:** the school-districts announcement
(`3msc62t55fy2q`), linking the homepage. Copy workshopped rather than
generated. What shaped it, for the next one:
- **Led with the gap, not the feature** — "School boards decide a lot and
  almost nobody covers them" before "the brief now carries school district
  news." The thesis is the hook; the feature is the payload.
- **"I'm teaching my software to sit in on the board meetings"** for the
  forward tease. Honest that it does not exist yet, keeps the accountable human
  in frame, and holds the account's no-"AI" line (below) without being coy.
- **Named the six districts we actually read**, and used "more districts to
  come" for the three behind the Finalsite wall — true, and it doesn't hand
  readers a technical excuse.
- **"reading what they tell families"**, not "covering the districts" — we read
  announcements; we do not yet report on the districts. Precision here is the
  same discipline as the 🎓 section's attribution rules (`PIPELINE.md`).

### Two operational gotchas (both hit 2026-08-04)

1. **`atproto` is installed `--user` for system Python, not the project
   `.venv`.** So this script runs under `python3`, never `.venv/bin/python3` —
   which is what `run_bluesky_post.sh` and `check_agendas.sh` already do. Easy
   to trip on, because everything else in the repo is venv-run.
2. **The cached session string gets revoked** (`ExpiredToken`) — seen within
   hours of creation. `get_client()` catches it, logs in fresh and rewrites
   `bluesky-session.txt`, so it self-heals; the log line is noise, not a
   failure. Do not "fix" it by deleting the session cache.

### The pinned post — rewrite DEFERRED (2026-08-04)

Current pinned intro is `3msbtcoo5ba22` (299/300 chars, link card → homepage),
with the UTM-tagged TDB Weekly card as a pinned self-reply beneath it
(`3msbtcouu7e23`). **Deliberately not rewritten to add schools** — user's call:
replace it once the live AI reporter actually covers school boards, so the copy
can state it plainly instead of teasing it. Drafts explored and the reasoning
worth keeping:

- **Bluesky posts are not editable.** A "rewrite" is delete + repost + re-pin,
  and deleting the parent **orphans the pinned newsletter reply** (renders under
  a "deleted post" placeholder), so the reply has to be reposted too. Re-pinning
  means writing the `pinnedPost` strongRef back onto the `app.bsky.actor.profile`
  self record. Budget for four steps, not one.
- The window is cheap while engagement is zero — check
  `app.bsky.feed.getPosts` for likes/reposts/quotes before deleting anything.
- The draft that overclaimed, caught before posting: "watch the meetings across
  Tucson, Pima County, Marana, Oro Valley **and now the school districts**"
  reads as though we attend school board meetings. We don't yet. Keep the school
  clause grammatically separate from the meetings clause until the reporter
  ships — at which point this whole problem goes away.
- At 299/300 the post has no room, so adding schools costs the closing question
  ("What part of town are you reading from?"). On an evergreen pinned post that
  question is what converts a profile visit into a reply — don't drop it
  casually. Reading the profile: `app.bsky.actor.getProfile` returns
  `pinnedPost`, and the whole thread is readable unauthenticated via
  `app.bsky.feed.getPostThread`.

### v2 framework (discussed 2026-08-04, post-launch)

Account is fully dressed as of launch day: hand-written bio, pinned intro post (the "software I whipped together" nod — deliberate wording; the word "AI" avoided because Bluesky's early-adopter crowd skews AI-skeptical), UTM-tagged newsletter reply pinned beneath it (`utm_source=bluesky&utm_medium=social&utm_campaign=tdb-weekly`), first follows done manually.

Remaining, in priority order:
1. **Starter pack** of Southern-AZ civic accounts — manual, ~10 min, once the account has ~a week of content.
2. **Metrics logger** — daily snapshot of followers + per-post engagement to a gitignored jsonl (public API, no auth); feeds the 8-week distribution-loop evaluation. Pair with UTM-tagging the auto-poster's links (Bluesky mobile apps often send no referrer, so GA4 undercounts without it).
3. **Preview→outcome quote-posts** (user-approved 2026-08-04, next build session alongside the metrics logger) — when a What They Decided report publishes, quote-post the matching What to Watch post instead of posting a standalone link: "here's what happened" quoting "here's what to watch." Fully derived — the ledger has every post's URI and report slugs pair with preview slugs, so it's a slug join, no model call. Makes TDB's defining preview→outcome rhythm visible in a native Bluesky format; ~20 lines.
4. **Monday "This week in local government" thread** (user-approved 2026-08-04, future session) — one thread, one post per body meeting that week, derived from published previews via the v1 compose machinery. A recurring anchor product in a predictable slot. Build it *together with* the rollup decision below — the weekly thread is the natural home for Spotted/Around Town digests if batching wins.
5. **Rollup policy decision** — watch a week of the firehose first: possibly keep briefs/previews/reports/In Depth as individual posts but batch Spotted + Around Town into derived digest posts to keep the feed high-signal.
6. **Custom feed generator** — ROADMAP-gated, see "Other ATProto plays" below.

**Wait-and-see: Bluesky as a newsgathering input.** Flip the pipe: a daily poll of Bluesky search for Tucson keywords (street names, "Pima County," agency names) appending interesting hits to `pipeline/EDITOR-TIPS.md`, which the brief generator already reads every run. User likes the concept (2026-08-04) but is unconvinced there's enough Tucson content on the network yet — the same thinness that makes the account an easy land-grab makes it a weak source. Revisit when the metrics logger (or just time in-app) shows a real Tucson conversation forming; a one-week trial is cheap whenever curiosity strikes.

**Declined:** notifications→Telegram forwarding (2026-08-04) — user is at the PC all day and will handle replies directly in-app; don't re-propose. **Deferred:** the Flash caption writer below — the launch-day compose improvements (sentence-fit + top-of-agenda) ate most of its value; revisit only if metrics show Bluesky earning real attention.

### v2 — DeepSeek V4 Flash caption writer (later, optional)

Flash writes the post text as a **compression-only** task: input is the page's own extracted text, no outside facts, derived v1 text as automatic fallback when output fails checks (too long / names not present in source — the provenance-gate trick, reused). Cost is fractions of a cent per day. Bake-off lessons that apply (PIPELINE.md): Flash **thinks by default and overthinks** (cap/disable thinking for captions); OpenAI-compatible endpoint → reuse the `run_chat()` shape from `brief_model_ab.py`, not `call_claude()`; PRC hosting settled 2026-07-31, don't re-raise. Governance: model-written captions are reader-facing news text → per Part 2's tiered rule, either Telegram one-tap or the compression-only + fallback guard. Decide when v2 starts; v1 doesn't need it.

### Portability of the Bluesky builds to X / Threads (researched 2026-08-05)

Verdict per feature — the differences are structural, not effort:

- **Ledger-diff auto-poster → Threads: SHIPPED 2026-08-05** (`social/threads_poster.py`).
  Imports the derivation helpers straight from `bluesky_poster.py` (sitemap diff,
  `page_meta()`, `compose()`); own gitignored ledger (`threads-ledger.json`); posts via
  the two-step container flow with `link_attachment` (Threads fetches our og: meta
  server-side — no blob upload). Runs alongside the Bluesky poster in
  `run_bluesky_post.sh` (6:45 AM / 4:45 PM) and at the end of `check_agendas.sh`.
  **No App Review / Tech Provider Verification was needed for own-account posting**:
  dev-mode Meta app ("tdb-publisher") + "Threads Tester" invite to @tucsondailybrief
  grants threads_basic + threads_content_publish immediately; review is only for
  serving third parties. Setup gotchas hit live: the token-generator popup authorizes
  whatever threads.net session the browser holds (log in as the brand account first),
  and the tester invite must be accepted from the brand account's Settings → Website
  permissions. **Token lifecycle:** long-lived (60 days); the poster self-refreshes
  via th_refresh_token once the token is 7 days old and rewrites
  `~/.config/environment.d/threads.conf` in place (clock in gitignored
  `threads-state.json`; tokens <24h old can't be refreshed). Credentials:
  THREADS_ACCESS_TOKEN / THREADS_USER_ID (27808088595552441) / THREADS_APP_ID /
  THREADS_APP_SECRET — the *Threads* app ID/secret, not the Facebook pair.
  Back catalog seeded; first post (2026-08-05 brief) live at launch.
- **Auto-poster → X: ports at ~$12–18/mo.** Pay-per-use is $0.015/post but **$0.20
  per post containing a link** — our poster is ~2–3 link posts/day. Credits are
  prepaid (a natural hard budget cap). Manual-first posture from the 2026-08-04 note
  stands; also NO brand account exists on X yet — creating one is a user action.
- **Comments embed → NEITHER.** The embed exists because Bluesky's AppView is
  unauthenticated + CORS-open, so readers' browsers fetch threads directly. X reads
  cost $0.005 each (client-side impossible, and a proxy would pay per pageview —
  costs scale with traffic). Threads reads are free but token-gated → would need a
  caching proxy service on Fly, for a second comment section of dubious UX value.
  **Comments stay Bluesky-only, by design — it's the differentiator, not a gap.**
- **Starter pack → no analog.** X Lists are the nearest cousin (manual, no
  follow-all); Threads has nothing.

Sources (all 2026): docs.x.com pricing, postproxy.dev, opentweet.io, api.sorsa.io
(X); blotato.com, postproxy.dev, replia.net (Threads). X pricing churns — re-verify
before buying credits.

### Bluesky-powered article comments (SHIPPED 2026-08-05)

Every article page carries a hidden `<section id="bsky-comments">` (chrome constant
`BLUESKY_COMMENTS_HTML` in `generate_post.py`, interpolated before `</article>` in the
brief template and all seven section renderers; a one-time sweep patched 369 published
pages). `/assets/bsky-comments.js` (vanilla, no deps) looks up the page's canonical URL
in `/assets/bluesky-posts.json`, fetches the post's reply thread from the **public
AppView** (`public.api.bsky.app`, unauthenticated, CORS-open), and renders replies —
chronological, nesting capped at 3, labeled replies skipped, everything inserted via
`textContent` (no HTML injection path). Pages with no Bluesky post keep the section
hidden; zero-reply pages show a "Be the first to comment" CTA. **No backend.**

The map is exported by `bluesky_poster.py::export_public_map()` from its ledger (real
posts only — seeded/stale entries have no thread) after every posting run, and
committed/pushed by `push_public_map()` (non-fatal; all pushes originate from this
laptop so races don't bite). So a new page's comment section lights up when the 6:45 AM
/ 4:45 PM poster run posts it — same latency as the Bluesky post itself.

Dev preview on any article page: `?bsky-uri=<at://…/app.bsky.feed.post/…>` overrides
the map lookup. Verified live 2026-08-05 in-browser: zero-reply CTA path on a real
article + full thread render via the override.

### Starter pack (SHIPPED 2026-08-05) + other ATProto plays, ranked

0. ~~Starter pack~~ — **"Tucson News & Community"**, 34 accounts, created entirely via
   the protocol (list + listitems + starterpack records):
   https://bsky.app/starter-pack/tucsondailybrief.com/3msdxceiw672s
   Roster + skip reasons (kept private): `../tucson-daily-brief-notes/bluesky-starter-pack-roster.md`.
   Announced as a reply under the pinned post. Add/remove = listitem records or the app.
1. ~~Domain handle~~ — day one, see above.
2. **Tucson custom feed generator** — a subscribable "Tucson News" feed (TDB + Star + Sentinel + AZPM + local reporters) via Jetstream + feed-skeleton service on Fly next to `tdb-ask`. TDB owns a *distribution surface*, not just an account. Real multi-session project — ROADMAP it, gated. The starter-pack roster doubles as its seed list.
3. **Standard Site publishing** (surfaced by the Decoder interview with CEO Toni
   Schneider, 2026-08-03) — an emergent long-form-publishing lexicon defined by
   Leaflet/Pckt/Offprint that Bluesky now surfaces natively in-app, with WordPress
   adopting. If TDB published articles as Standard Site records, they'd render as
   first-class long-form content across the ATmosphere instead of link cards.
   NOT YET INVESTIGATED: spec maturity, whether records embed or link canonical
   content, SEO/canonical implications. Feasibility scan before any build.
4. **Custom lexicons for civic records** (k3-adjacent) — no consumer exists today,
   but Schneider explicitly invites custom record types ("you can define your own
   records on the protocol"); parked as a note.
5. **Self-hosted PDS** — skip, buys nothing at this scale.

**Effort:** v1 ≈ one session; v2 ≈ +1 hour; feed generator = its own project.

---

*Captured 2026-06-26. Strategy + feasibility only — not building. Part 3 added 2026-08-04 (architecture locked, awaiting build go-ahead). Pairs with SHORT-FORM-VIDEO.md and the project_social_promo_strategy / project_social_autopost memories.*
