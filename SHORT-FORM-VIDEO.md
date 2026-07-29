# Short-Form Vertical Video — Platform Map, Automation & Build Plan

Researched 2026-06-23 (parallel platform-automation scans + audience landscape). Goal: auto-generate ~30s vertical (1080×1920) news clips from existing TDB content and publish across the major short-form surfaces, with a Telegram one-tap review gate. Companion to the "Roadmap: Short-Form Video" section in `CLAUDE.md` and `project_social_promo_strategy` memory.

## Content strategy — LOCKED 2026-06-23

**Do NOT mirror the podcast.** A 5-story roundup fails on short-form for three reasons: (1) the platform rewards *one* sharp idea, not a roundup; (2) short-form is a *discovery* surface (reaching people who've never heard of TDB), not retention; (3) it should lead with TDB's *moat* (original civic finds), not commodity wire headlines. This also aligns with the long-term pivot away from the aggregation layer — short-form showcases the original journalism, not the brief.

**Model: a funnel of named recurring series.** Named segments build habit/recognition and make production a fill-in-the-template job. Three tiers, rotated (you don't pick one tier — you rotate):
- **TOP — reach/discovery** (new audience): feel-good, identity, desert wonder.
- **MIDDLE — utility** (reason to follow): explainers, what's opening, heat/safety.
- **BOTTOM — moat/trust** (what makes TDB different): the civic finds only the pipeline catches.

**LAUNCH LINEUP (locked): a two-series rotation bracketing the funnel —**
1. **🌵 "Only in Tucson"** (TOP / discovery engine) — feel-good, wildlife, identity, desert wonder. The most *shareable* content; grows the audience. *Example (real):* "Two orphaned mountain lion cubs. Tucson kids got to name them." → Moonbead & Pretzel, chosen by Beads of Courage kids → "Only in Tucson. Follow for the good stuff."
2. **🏛️ "Buried in the Agenda"** (BOTTOM / signature) — the stuff only the agenda-mining/Spotted pipeline catches; built-in curiosity gap, impossible to copy. *Example (real):* "Your town just made police bodycam footage 5× more expensive to see." → animate **$25/video → $46/hour** → "We read every agenda so you don't have to."

**LAUNCH SEQUENCING (decided 2026-06-23):** front-load the **first several videos with "Only in Tucson"** (feel-good) to build an audience before introducing the harder civic content — accountability content lands better *to* a following than into the void. "Buried in the Agenda" is **built and ready** (`buried-ov-bodycam` clip + dark theme + tense track) but **held/unpublished** until there's a following. (First published Short: the Moonbead & Pretzel "Only in Tucson" clip, YouTube `EE8-zlcCxjI`, 2026-06-23.)

**Bench series (add later, same templates):** "Desert 101" (evergreen, batchable explainers — e.g. "your tap water traveled 300 miles to get here"; the dry-day insurance), "Opening Soon" (food/business from Spotted + brief, map-zoom), "What They Decided" (council accountability recaps from meeting coverage; flagship once vote-tracker data exists).

**Third series family, framework locked 2026-07-28: the geographic editions ("What to Watch: Marana / Oro Valley")** — weekly town-specific clips run as a personalization-by-portfolio experiment against Meta's video-first feed pivot. Full spec in its own section below.

**Craft decisions (locked):**
- **Text-only motion first** (animated card system; no TTS) — works muted, cheapest, fastest, sidesteps "AI voice reads the news" weirdness. Add VO later, mainly for "Desert 101."
- **Music = own AI-generated tracks** (ElevenLabs Music, `POST /v1/music`, `model_v2`, `force_instrumental`). Commercial-licensed on the paid plan, **no attribution, no Content-ID claims** — the whole point (not about owning copyright, which AI output can't have). Trained on licensed data, so no Suno/Udio-style training-data lawsuit cloud. Strategy: a **small reusable per-series library** (one warm theme for "Only in Tucson", one tense theme for "Buried in the Agenda") = sonic brand identity, not per-video gen. Tracks in `social/assets/music/` (gitignored). NOTE: the ElevenLabs API key needs the `music_generation` scope (the TTS key didn't have it by default).
- **Cadence: NOT chained to daily news** — ~1 reactive clip (a feel-good or agenda find when one lands) + a **bank of batched evergreen "Desert 101"**. Removes the daily-pressure failure mode.
- Visual toolkit: motion typography + owned/stock desert b-roll + **maps** (great for "Opening Soon"/location items) + `people-photos/` portraits + data-viz. **No AI-generated imagery** (fabrication risk).
- **Bilingual:** lead Spanish cuts with "Only in Tucson" + "Opening Soon" + "Desert 101" (broad, not time-locked — travel furthest with the Spanish audience).

**First prototype:** an **"Only in Tucson"** clip — highest odds of landing, lowest risk, teaches what the muted-caption format needs before spending differentiation capital on the agenda series. Then establish "Buried in the Agenda" as the recurring signature.

## Geographic editions — "What to Watch: {Town}" (framework locked 2026-07-28)

The third series family, and the one with a thesis attached. Talked out 2026-07-28 against Meta's announcement (7/24) that Facebook will test **opening directly into a full-screen video feed**, Classic Feed demoted to a second tab — i.e., the feed becomes a pure recommendation surface where volume-of-relevant-video is the currency.

**The thesis: personalization by portfolio.** You can't address individual viewers on Facebook (no organic targeting exists), but you can hand the recommendation algorithm a portfolio of genuinely different town-specific videos and let *it* do the per-viewer matching. This is the zoned edition of the print era — killed decades ago by print economics — reborn as AI-rendered video at one-person cost. No Tucson-market competitor can cut a different video for every suburb every week; a cron job can. Run it as a **public experiment**: does town-level video earn differentiated distribution in Meta's video-first feed? Either answer is a finding, and the write-up (LinkedIn / industry track, per the two-brand rule) is a portfolio artifact with numbers attached — which is what distinguishes this from a demo.

**Editions: Marana + Oro Valley first — chosen by data-layer depth, not audience size.** Both have agenda miners + dev watch + Spotted (OV via agendas; Marana via the DLLC database diff, added 2026-07-28 — see `MEETING-WATCH-PIPELINE.md`), so every clip is derivable end-to-end from structured sources. "The editions follow the data layer" is itself the editorial-AI principle. Tucson wards/Pima can join later as their data layers justify it.

**Cadence: weekly, Monday morning, both towns** — after the 8 AM `check_agendas.sh` run so previews are fresh; render ~8:30, Telegram one-tap review, post to FB that morning. Forward-looking framing ("here's what your town decides this week") keeps every clip preview-grade — the auto-publish-safe tier of the editorial model — so review is a glance. This respects the locked not-chained-to-daily-news cadence decision: weekly, not daily. Skip rules for quiet weeks: no council meeting → lead with dev watch ("No council this week — but three new cases hit the map"); genuinely nothing → skip honestly and log it (a skipped week is experiment data, not a failure; the canceled-meeting guard says when this applies).

**Format: lead-plus-ticker, NOT a roundup** (respects the one-sharp-idea rule — the lead carries the clip; the ticker says "we see everything in your town," which is the moat message). ~30–40s; lean 30 — completion rate is the kingmaker signal in 2026 ranking. Storyboard:

```
Beat 1 (0–3s)   Boundary cold-open: town's actual boundary draws in as a
                hand-drawn-style SVG stroke (terracotta on dusk), pin drops.
                Kicker: WHAT TO WATCH. Boundary polygon from the same town
                ArcGIS portals the dev-watch pollers hit — no map tiles, no
                attribution, matches the site's hand-drawn SVG language.
Beat 2 (3–6s)   Title card: MARANA (Fraunces, huge) · Week of {date}
Beats 3–5       LEAD STORY, 2–3 scenes: headline → key number/detail (the
(6–~22s)        $25→$46 animated-stat treatment) → the stakes
Beat 6 (~22–30s) ALSO ON THE RADAR: 2–3 one-liners, icon + text
Beat 7 (last)   CTA card, inside the Reels safe zone: "Council meets Tuesday,
                6 PM" · "We read every Marana agenda so you don't have to" ·
                tucsondailybrief.com
```

**Visual identity:** the editions should look like tucsondailybrief.com in motion — light/bone theme, Fraunces, terracotta accents (utility register; the dark/tense treatment stays reserved for Buried in the Agenda). **Per-town identity is one accent variable, not a separate design:** Marana = adobe, Oro Valley = sage. Adding an edition is a config line, not a design project — that's the scalability story. One new "editions" music theme (ElevenLabs Music, per-series-library approach), steady and civic. Text-only motion per the locked craft decision. Implementation: a new `SERIES` preset + per-town accents in `render_short.py`, plus a beat-script generator that reads miner output.

**Content rules (derive, don't ask):** lead chosen by a deterministic priority ladder — topic-flagged items (data-center etc.) → public-hearing/rezoning items → the preview's top item → biggest dev-watch diff; ticker takes the next 2–3 off the same ranked list. The model's only job is phrasing; every proper noun and number must appear in miner output; hard on-screen word caps enforced in code (lead ≤ ~40 words, ticker items ≤ ~12). Candidate later hardening: run scripts through `provenance_gate.py`. **Never mix towns in one clip** — a hybrid clip muddies both engagement clusters.

**Distribution + the algorithm-legibility playbook.** Meta learns what a clip is from platform-level signals (caption, hashtags, location tag) plus content extraction (OCR of on-screen text, visual/audio embeddings); embedded MP4 file metadata is NOT a signal. Per-viewer serving is engagement clustering — watch time/completion above all, plus likes and the 2026 in-feed interest surveys (UTIS). So make the town machine-legible in every clip:
1. Town name in the first caption line, plain words, keyword-rich.
2. Town hashtag set per the locked 2026-07-19 system: `#Marana`/`#OroValley` + `#Tucson` + `#TucsonNews`, ≤5.
3. Location-tag every Reel with the town's actual Place.
4. Identical series title-card wording every week ("WHAT TO WATCH: ORO VALLEY") — it's OCR'd, so it's a machine topic signal, not just branding.
5. Hold the weekly cadence; clusters form on consistency.
6. **Standing caption line (audience education — decided 2026-07-28):** "Like the videos about your part of town and you'll see more of them. Every video: tucsondailybrief.com." Honest, feeds exactly the signals the ranking model uses, and doubles as the owned-surface CTA.

**One Page, no per-town Pages (decided 2026-07-28).** Within one Page you can't *guarantee* a viewer an OV-only diet — Meta decides per-user, per-post. Separate per-town Pages would make the guarantee real but fragment brand, followers, and workflow. Not for a two-edition test. Revisit only if eight weeks of data shows the clusters never diverge — and that outcome would itself be the finding.

**Posting: manual first.** FB/IG Reels adapters are build-order step 3 and unbuilt; two uploads a week is trivially manual, mirrors the TikTok learn-by-hand logic, and manual posting *is* the human-review gate for Meta surfaces. Cross-post the same MP4 to YouTube Shorts (full-auto there is already sanctioned). Facebook is the experiment's measurement surface. Build the Meta adapter only when the format stops changing.

**Measurement (decide-before-first-post):** per-post log — edition, date, reach, avg watch time / completion, follows, shares, notable geo-revealing comments ("that's my HOA's case" is the best geo evidence FB gives; per-Reel viewer geography isn't exposed). Eight-week window aligned with the MARKETING.md distribution loop, where the editions ARE the weekly moat package (reach slot stays Only in Tucson, preserving the front-load-feel-good decision). Success signal: divergence between the editions' reach/retention/comment patterns vs each other and vs generic clips. Conversion signal: edition viewers crossing to an owned channel (newsletter, site).

**Phase 2, earned sequel only: the personal video brief.** If editions demonstrate demand, the addressable version reuses the Matchday Inference stack wholesale: signup form (town/topics/length) → FastAPI+SQLite on Fly.io → weekly per-subscriber render → Cloudflare R2 at unguessable token URLs (custom subdomain — Gmail bounces r2.dev links) → transactional email teaser via Resend (NOT Buttondown — every recipient gets a different link). Do not build ahead of the data.

**BUILT 2026-07-28 (same day the framework locked)** — first scheduled run Monday 2026-08-03 via `check_agendas.sh`:
- `render_short.py`: `edition-marana` / `edition-orovalley` SERIES presets (light theme, adobe/sage accents, `safe_zone` footer at 380px), three new scene kinds (`boundary` cold-open on dusk, `title` card, `ticker`), optional per-scene `dur` (editions run ~22–26s), small `meta` line on CTA scenes (meeting day/time, only when derivable from the preview).
- Boundary polygons: `social/assets/boundaries/{marana,orovalley}.json` — Census TIGERweb incorporated-place geometry (BASENAME + STATE='04'), cached, rendered as stroke-only SVG + centroid pin. No map tiles, no attribution burden.
- Music: `social/assets/music/tdb-editions.mp3` — ElevenLabs Music (music_v2, force_instrumental, 35s, steady/civic), generated 2026-07-28.
- `generate_edition_short.py`: the ladder (topic-flag → hearing/rezoning → top item → dev-led "no council this week" → EDITION-SKIPPED), radar pool from published Around Town + Spotted pages (mtime window **guarded by filename date ≤90 days** — site-wide HTML sweeps touch every mtime and would otherwise resurface old cases), grounded Sonnet script + verify pass (BIA pattern), hard caps in code (lead ≤90 chars fatal / >70 warns; ticker truncated at 60), standing education line baked into every caption, meeting meta line derived from filename date + time regex over the preview (never invented).
- `check_agendas.sh` Monday block: renders both towns after the miners, `--publish` to YouTube Shorts, Telegram per edition with the MP4 path + paste-ready caption for the **manual FB/IG post** (the review gate), reminder to fill `social/editions-log.md` (the measurement log) after ~48h.
- First test renders (2026-07-28, dev-led week): Marana led with the Avra Valley ATC tower, OV with a 56-lot Rancho Vistoso subdivision — both from real pipeline data, ~22s, h264+aac.

## Decision: build our own thin publish layer; skip paid schedulers

Hosted schedulers (Ayrshare/Blotato/Upload-Post) sell **convenience** — they're pre-approved platform apps, so you skip every app review. But the value is the *approvals*, not the code (which is just OAuth + an HTTP POST per platform). **For a single set of self-owned accounts, most platforms require no review at all**, so a homegrown adapter layer covers nearly everything for $0. We build our own "Blotato." (Self-hosted OSS schedulers like Postiz/Mixpost do NOT help — you'd still register your own dev apps and face every review.)

## Per-platform automation reality (mid-2026)

| Platform | Auto-publish (own account)? | Gate / requirement | Account status |
|---|---|---|---|
| **YouTube Shorts** | ✅ **Yes — confirmed ship-now** | Existing project is audited (public uploads verified via oEmbed 2026-06-23); `videos.insert` + vertical + ≤3min auto-detects a Short. Same call as the podcast upload. | ✅ `@tucsondailybrief` (podcast channel) |
| **Bluesky** | ✅ **Yes — zero gate** | App password; `app.bsky.video.uploadVideo` → embed. ≤100MB/3min. No review, no business acct. | ❌ not created (offered) |
| **Instagram Reels** | ✅ **Yes — no app review for own account** | IG Business + Standard Access on your own Meta app; needs public MP4 URL (R2). 9:16, 5–90s, ≤100MB. Permissions renamed Jan 2025 → `instagram_business_content_publish`/`_basic`. ⚠️ verify the no-review path on the live App Dashboard. | ✅ `@tucsondailybrief` |
| **Facebook Reels** | ✅ **Yes — no app review for own Page** | Same Meta app; `POST /{page-id}/video_reels` 3-phase flow with `file_url` from R2; `pages_manage_posts`. | ✅ TDB FB Page |
| **TikTok** | ⚠️ **Not directly when unaudited** | Unaudited apps forced to PRIVATE. Public needs TikTok's **Content Posting audit** (~1–4 wks, attainable) OR draft-and-tap (push to inbox via `video.upload`, human taps publish). | ❌ **no account; user has never used the app** |
| Threads / LinkedIn / Snapchat / Pinterest | Mixed / second-tier | Defer. Threads = cross-post only; LinkedIn is a separate written track; Snapchat/Pinterest weak for local news. | Threads ✅, others n/a |

**Tokens for unattended cron:** Meta **system-user token = permanent**; YouTube refresh token (project in production) = permanent (already working); TikTok refresh = 365 days; Bluesky app password = static. All cron-friendly.

## Audience reality (why this order)

US adult usage (Pew 2025): YouTube 84% · Facebook 71% · Instagram 50% · TikTok 37%. Only **YouTube Shorts, Instagram Reels, TikTok** combine mass reach + a real short-form discovery engine (Facebook Reels a strong 4th for older/local). **Hispanic adults over-index on exactly the platforms that matter:** Instagram 62%, TikTok 57% (74% of Hispanic teens), YouTube = top daily platform; **WhatsApp over-indexes ~2.5×** (a distinct Spanish-distribution channel via broadcast lists — note for later). This validates social-first Spanish (see the Spanish-Language TDB roadmap). Caveat (Nieman Lab): short-form drives *reach* not comprehension — link every clip back to a tucsondailybrief.com story, and consider a Shorts→long-form funnel.

## TikTok is a future project, not the starting line

User has no TikTok account and has never used the app. So TikTok = (1) create account, (2) learn the platform's native style by posting manually, (3) only then decide whether the developer audit is worth it. The manual phase isn't a limitation — it's how you'd learn TikTok regardless. **Starting lineup = YouTube + Instagram + Facebook** (all owned, all free-to-automate, all the reach that matters), + Bluesky as an easy bonus if the account gets made.

## The reusable core: generation pipeline (~80% the podcast pipeline)

Publishing is just adapters on the end; the real work is platform-agnostic generation:
1. **Pick one story** from the day's brief (Sonnet/Haiku — extend `condense_script()` in `generate_podcast.py` to a single-story ~30s / ~450-char vertical script).
2. **TTS** (ElevenLabs/Voxtral) — same as podcast, shorter clip.
3. **Word timestamps** — run the TTS audio back through Deepgram (~$0.0002/30s) for karaoke caption timing (short-form is watched muted → burned-in captions drive retention). ElevenLabs can also return char-level timestamps.
4. **Render 1080×1920** — desert-palette template + headline + burned-in ASS captions via ffmpeg (low-dependency v1; moviepy/Remotion only if fancier motion is wanted). Reuse the `social/` render approach.
5. **Telegram one-tap approve** (per the human-review bar — a wrong 30s clip spreads worse than a buried paragraph).
6. **Publish** via the DIY adapters.

**Bilingual from day one:** design the script + caption step to emit Spanish (transcreated, not raw MT) alongside English — that's how Spanish TDB ships, per the social-first decision.

## Build order

1. **Generation pipeline** (the hard, valuable, platform-independent part) → one finished 1080×1920 MP4 + caption, Telegram-gated.
2. **Prove publish on no-gate channels:** YouTube Shorts (ship-now) + Bluesky (trivial, if account made).
3. **Add IG Reels + FB Reels** DIY adapters (Meta app, Standard Access, R2-hosted file — verify no-review path live).
4. **TikTok later:** create account → post manually to learn it → audit if it performs.
5. **Spanish cuts** + treat WhatsApp as a distinct distribution channel.

## Open items / caveats to resolve before/at build
- **Reels/Stories UI safe zone.** Reels and Stories are both full-screen 9:16 (1080×1920 — what `render_short.py` already outputs; feed posts/carousels are the shorter 4:5 1080×1350). BUT Instagram overlays its own UI on Reels: the caption, handle, like/comment/share buttons, and audio info cover roughly the **bottom ~20% and the right edge**. `render_short.py` currently places the footer ("Tucson Daily Brief") at the very bottom (≈150px up) and key text vertically centered — the footer would likely sit under IG's UI on a Reel. Fix when wiring the IG Reels adapter: lift the footer/CTA into the safe zone (keep critical text/logos out of the bottom ~340px and ~120px off the right edge), or render a Reels-specific variant. YouTube Shorts has a similar but smaller bottom overlay. Not an issue for the YouTube-only Short today; matters the moment we publish to IG.
- **YouTube channel is NOT phone-verified** → custom thumbnails 403 (the podcast thumbnail asset isn't being applied; videos use an auto-frame). Verify the channel in YouTube Studio. Low stakes for Shorts (custom thumbnails historically don't show on the Shorts feed) but needed for the podcast videos + branding.
- **Verify the IG/FB "no app review for own account" path** against the live Meta App Dashboard when building (Meta tightens this periodically).
- **Branding refresh** (separate but related, see below) — the podcast/video visual identity predates the 2026-05-11 site redesign; refreshing it produces the thumbnail + a vertical 1080×1920 template that carries straight into Shorts.
- Confirm exact Threads publishing scope string if Threads is ever added (`threads_content_publish` unconfirmed).

## Related: brand asset refresh (YouTube + Apple Podcasts → match IG)
The IG/Threads avatar is `~/tdb-fb-profile.png` (1080×1080 terracotta sun + "TDB" + wordmark). To unify:
- **YouTube channel avatar:** reuse `tdb-fb-profile.png` (set in YouTube Studio — manual; not API).
- **YouTube banner (2048×1152, safe area 1235×338):** generate desert-palette (see `social/render_brand.py`).
- **Apple Podcasts cover (1400–3000px square):** Apple pulls the `<itunes:image>` from the RSS feed → regenerate the square cover, upload to R2, update the image URL in `generate_feed.py`, re-push the feed; Apple refreshes on its next crawl.
- **Podcast/video thumbnail (1280×720) + vertical 1080×1920 variant:** do the design pass once, export both aspect ratios (the vertical becomes the Shorts template).
