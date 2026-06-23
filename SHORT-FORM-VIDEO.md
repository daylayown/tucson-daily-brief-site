# Short-Form Vertical Video — Platform Map, Automation & Build Plan

Researched 2026-06-23 (parallel platform-automation scans + audience landscape). Goal: auto-generate ~30s vertical (1080×1920) news clips from existing TDB content and publish across the major short-form surfaces, with a Telegram one-tap review gate. Companion to the "Roadmap: Short-Form Video" section in `CLAUDE.md` and `project_social_promo_strategy` memory.

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
