# Tucson Daily Brief Site

Static blog for GitHub Pages — no JavaScript, no frameworks, no build tools. Live at `https://tucsondailybrief.com`.

The project is a one-person local news operation for the Tucson metro: a daily aggregated brief, plus an original-journalism layer (meeting previews, AI-drafted post-meeting news reports, surfaced public filings, development watch), plus distribution surfaces (podcast, newsletter, crossword, social, RAG-powered Ask).

## Reference docs — read these before working in an area

CLAUDE.md is the index. Detail lives in these; **when you learn something durable, add it to the relevant doc, not here.**

| Doc | Covers |
|---|---|
| `PIPELINE.md` | Daily brief renderer internals, the 6:00/6:10 AM cron chain, Anthropic billing posture, recurring failure modes (mis-save, no-network, weather-alert briefs, NWS fire-zone fix, editor's desk, self-citation gap) |
| `MEETING-WATCH-PIPELINE.md` | The four agenda miners, publishing flow, slug routing, canceled-meeting guard, renderer bugs |
| `AI-REPORTER.md` | Live + VOD transcription → news report: architecture, usage, schema, scheduler, stream URLs, STT research |
| `NAMES-BIBLE.md` | `pipeline/local_names.json` — canonical names, Deepgram misreads, the pronouns rule, the queued audit |
| `ORIGINAL-JOURNALISM.md` | Planned content types (Old Pueblo Speaks, Tracking, FOIA Lead Spotter, Deep Read…), post-meeting data-source matrix, story ideas |
| `RAG.md` | Ask / `tdb-ask` — architecture, gotchas, Fly.io hosting, Phase 3 backlog |
| `NEWSLETTER.md` | TDB Weekly — voice, format, pipeline, Buttondown, sender architecture |
| `CROSSWORD.md` | The Tucson Mini — editorial posture, generation, wordbank, Saturday ritual |
| `SOCIAL-CARDS.md` | `social/` renderers, themes, aspect ratios, render-sharpness lessons |
| `SHORT-FORM-VIDEO.md` | Platform automation map + DIY publish-adapter plan |
| `SOCIAL-AUTOPOST.md` | Auto-posting feasibility per platform; Facebook strategy |
| `MARKETING.md` | Two-brand split, the distribution loop, content mix, instrumentation TODOs |
| `IG-BTS-STRATEGY.md` | IG behind-the-scenes content: the "outcome + accountable human, never the tooling" principle, format buckets, founder-post signal, variable-isolation test |
| `ROADMAP.md` | **Everything queued and gated** — Responsiveness, coverage expansion, structured-data layers, Data Center Watch, Tucson en Breve, off-the-laptop migration, Spotify |
| `REDESIGN-V2.md` / `REDESIGN.md` | Visual language / information architecture (both shipped 2026-05-11) |
| `*-DATA-FEASIBILITY.md`, `COVERAGE-EXPANSION.md` | Per-municipality and school-district data scans (OV, Marana, Tucson, schools, courts/probation) |
| `crime.md`, `crime-tpd-data.md` | The FBI-reporting-gap story research |
| `powerbi.md` | The PCAO PowerBI forensics — frozen dashboard swap, both reports' contents, ME live dashboard, reusable probing techniques |
| `k3-data-plan.md` | The civic-transparency pipeline plan — pollers→snapshots→surfaces, build order (PCAO Watch → crime poller → ME rollup → AOC → §1-605), guardrails |

Strategy/impact notes live **outside this repo** in `~/claude-code-projects/tucson-daily-brief-notes/` (deliberately private).

**History:** CLAUDE.md was a single 159k file until 2026-07-17, when it hit the 150k context limit and was split into the docs above. The prose moved verbatim — nothing was dropped — but if something seems missing, the pre-split original is `git show 30d8853:CLAUDE.md`.

## Standing rules

These are the ones that cost something when forgotten:

- **No fabrication in reader-facing output, ever.** Verify every factual claim before it ships. Highest-scrutiny category is pop-culture/celebrity clues and any card or short. See the `feedback_ai_content_quality_bar` memory.
- **Derive, don't ask a model.** Every data-integrity bug found so far was the pipeline asking a model for something it should have computed — a list length, a lookup-table value, an editorial judgment about a meeting with no agenda. The model answers plausibly each time. See `feedback_verify_dont_delegate`.
- **A name that entered via transcript is a hypothesis, not a fact,** until an external source confirms it. See `NAMES-BIBLE.md`.
- **Cite our own reporting first.** On any morning after we publish a news report, check `news-reports/` before crediting an outside outlet for a story we broke. See the self-citation gap in `PIPELINE.md`.
- **Don't start new section-scale features mid-build.** Capture in `ROADMAP.md` with a gate, then drop it. See `feedback_resist_feature_creep`.
- **Two-brand split:** reader-facing surfaces lead with the outcome ("The Tucson news you'd otherwise miss"); the AI/tooling story belongs on About, LinkedIn, and industry conversations.

## Editorial model

- **Agenda previews** (forward-looking "What to Watch") publish automatically, no human review — they summarize what's on the agenda. Low risk, high value in timeliness.
- **Post-meeting reporting and all other original journalism** is human-reviewed before publishing — no exceptions. AI drafts and flags; a human reviews, edits, approves.
- **Daily Shorts + the weekly "Buried in the Agenda" Short** are the deliberate exception: full-auto to YouTube, user's call, while they stay YouTube-only.
- Each piece carries a clear disclosure about AI involvement.

**Coverage area:** the Tucson metro broadly — City of Tucson, Pima County, Marana, Oro Valley, and their governing bodies, commissions, and public records. Not limited to city limits. TDB's north star is depth in an under-covered metro, not statewide expansion (see the `project_editorial_thesis` memory).

## Project Structure

```
├── style.css                    # Warm-organic Southwest editorial CSS (REDESIGN-V2.md)
├── generate_post.py             # Daily brief renderer + ALL shared chrome; rebuilds homepage, archive, sitemap, RSS
├── generate_brief.py            # Deterministic 6 AM brief generator (replaced the OpenClaw agent)
├── index.html                   # Auto-generated zoned homepage (NOT the daily archive)
├── briefings.html               # Auto-generated full daily-brief archive
├── posts/                       # Daily brief HTML (YYYY-MM-DD.html)
├── meeting-watch.html + meeting-watch/     # Agenda previews (auto-published)
├── news-reports.html + news-reports/       # AI-drafted, human-reviewed reports
├── public-record.html + public-record/     # "Spotted" — display name only; URL kept for back-comat
├── around-town/                 # Development-watch feed items
├── in-depth/                    # Deep dives
├── ask.html                     # Live RAG Q&A; POSTs to Fly app tdb-ask
├── responsiveness.html          # Coming-soon stub (dashboard not built)
├── about.html                   # Hand-authored — NOT generated by any pipeline
├── ai_reporter.py               # transcript JSON → Claude report → Telegram → publish
├── ai_reporter_live.py          # streamlink/HLS → Deepgram WebSocket → transcript JSON
├── ai_reporter_vod.py           # ffmpeg → Deepgram batch → transcript JSON (VOD fallback)
├── run_live_reporter.sh         # Live reporter wrapper (env, dep validation)
├── schedule_recording.py        # Auto-schedules live-capture `at` jobs from previews
├── pipeline/                    # Version-controlled brief config
│   ├── sources.json             # News source config (status: broken|disabled = skip)
│   ├── local_names.json         # Names bible — see NAMES-BIBLE.md
│   ├── records_custodians.json  # Verified public-records channels per government — never guess an entry
│   ├── EDITOR-TIPS.md           # Hand-submitted leads, read each run
│   └── TUCSON-BRIEF.md          # Original agent rules — REFERENCE ONLY (rules now in generate_brief.py)
├── agenda_mining.py             # Pima County BOS (Legistar API) + shared render/publish helpers
├── agenda_mining_marana.py      # Marana (Destiny Hosted scrape)
├── agenda_mining_orovalley.py   # Oro Valley (Destiny Hosted scrape)
├── agenda_mining_tucson.py      # City of Tucson (Hyland OnBase PDF + pdftotext)
├── check_agendas.sh             # 8 AM cron: 4 miners + Spotted + dev watch + auto-publish + push
├── public_record_liquor.py      # Spotted pipeline: liquor filings out of agenda references
├── foia_lead_spotter.py         # Weekly: trawl news-reports/ for records-request leads → web-search verify facts/prior-disclosure → draft §39-121 emails → Telegram
├── run_foia_spotter.sh          # Cron wrapper (Mondays 9:30 AM)
├── records-requests/            # Working dir (gitignored — repo is public, unsent requests stay local)
├── dev_watch_marana.py          # Marana development watch (ArcGIS poll/diff)
├── dev_watch_orovalley.py       # Oro Valley development watch (ArcGIS poll/diff)
├── rag/                         # Ask — build_index.py, ask.py, server.py, index.sqlite (gitignored)
├── refresh_ask_index.sh         # 8:45 AM cron: rebuild index + fly deploy
├── Dockerfile + fly.toml        # Ask service image (app: tdb-ask)
├── crossword/                   # The Tucson Mini — play.html, tools/, puzzles/
├── generate_newsletter.py       # TDB Weekly draft generator
├── upload_to_buttondown.py      # Push draft to Buttondown as editable draft
├── run_newsletter.sh            # Manual Saturday wrapper (NOT cron'd)
├── social/                      # Card + short-form renderers; cards/ output gitignored
├── responsiveness/PLANNING.md   # Responsiveness Index — planning only
├── people-photos/               # Official portraits + manifest — research only, not wired in
├── transcripts/                 # Working dir (gitignored)
├── agenda-watch/                # Working dir: previews + full references (not published)
├── newsletter/drafts/           # Working dir (gitignored)
├── CNAME, .nojekyll, robots.txt, 404.html, sitemap.xml, rss.xml
└── CLAUDE.md
```

## How It Works

`generate_post.py` takes a briefing markdown file, extracts the date from the filename, converts markdown → HTML, writes `posts/YYYY-MM-DD.html`, then calls `rebuild_homepage()` — which scans all posts plus the newest entry in each section directory and rebuilds `index.html`, `briefings.html`, `sitemap.xml`, and `rss.xml`. Idempotent; running twice overwrites cleanly.

```bash
python generate_post.py ~/.openclaw/workspace/briefings/tucson-brief-2026-02-18.md  # normal
python generate_post.py --rebuild-homepage                                           # refresh only
python generate_post.py --rebuild-all ~/.openclaw/workspace/briefings/               # bulk re-render
```

**`generate_post.py` is the single source of truth for shared chrome.** Every section renderer (`agenda_mining.py`, `ai_reporter.py`, `public_record_liquor.py`, `dev_watch_*.py`, `render_indepth.py`) imports from it: `ANALYTICS_HTML`, `SUBSCRIBE_PANEL_HTML`, `SCROLL_TRIGGER_JS`, the SVG primitives (`HAND_RULE_SVG`, `SUNRAY_SVG`, `ARROW_SVG`, `FEATURED_SUN_SVG`…), `site_header_html()`, `section_nav_html()`, `footer_html()`, `rebuild_homepage()`, plus the SEO helpers (`seo_head_html()`, `news_article_jsonld()`, `derive_description()`, `extract_headline()`) and the topic-flag layer (`TOPIC_DEFS`, `detect_topics()`, `topic_badge_html()`).

**Footer is path-aware:** `footer_html(path_prefix="")` for root pages, `"../"` for nested ones. Renderers producing nested pages must pass the prefix. Nested renderers also take a `page_slug` kwarg so canonical/OG URLs match the real file.

**Feature flag `SHOW_TOOLS`** (currently `False`) gates only the secondary Tools nav row (just Responsiveness) and the homepage Tools card row. Ask is **not** gated — it's linked site-wide as ChatTDB. Flip when the Responsiveness dashboard ships.

**Live nav (top level): Daily Briefs · Local Government · Around Town · In Depth · ChatTDB.** The Local Government hub has two children, surfaced as a second nav row on hub-child pages: **What to Watch** (meeting previews) and **What They Decided** (post-meeting reports).

**Display-name renames are display-only** (same trick as Spotted): the reader-facing labels changed but URLs, directories, `_NAV` active-keys, module names, and CSS classes kept the original terminology. Two rename waves:
- **2026-06-24 IA reorg** → the topic-hub structure above (see `IA-REORG.md`).
- **2026-07-18 reader-facing labels** (from `sol/sol-new-names.md`): Meeting Watch/Local Meeting Previews → **What to Watch**; News Reports/Local Meeting Reports → **What They Decided**; Deep Dives → **In Depth**. URLs stayed `meeting-watch.html`, `news-reports.html`, `in-depth.html`; nav keys stayed `meetings`/`reports`/`indepth`. Renderers plus a one-time HTML sweep over published pages carried the change; "Spotted" and "Daily Briefs" were already good and kept.

**"Spotted" is a display rename only.** URL stayed `public-record.html`, directory stayed `public-record/`, and all code (module names, CSS class `public-record-filing`) keeps the original terminology. Only user-facing text changed.

Detail on renderer internals and the recurring failure modes → `PIPELINE.md`.

## Input Format

Briefing files land in `~/.openclaw/workspace/briefings/tucson-brief-YYYY-MM-DD.md` (a pipeline contract with `run_podcast.sh` — don't relocate). They have a title line, emoji section headers (🏛️ Government, 🚨 Public Safety…), bold story headlines with descriptions, source citations prefixed 📰/📄, ─── separators, a weather section, and trailing metadata (stripped during conversion).

**Source citations** come in two forms, both handled by `linkify_sources()` in `generate_post.py`: markdown links `📰 [Source Name](https://direct-url)` (preferred — links to the article) or plain text `📰 Source Name` (falls back to the outlet homepage via the `SOURCE_URLS` dict).

## Design

Visual language is **warm-organic Southwest editorial**, shipped 2026-05-11. The original Daring Fireball restraint is gone and should never be reverted to (see `feedback_tdb_visual_direction`). Full plan in `REDESIGN-V2.md`; `redesign-preview.html` is a self-contained reference.

**Tokens (`style.css :root`):**
- Locked palette: sand `#f5f0e6`, tan `#e8dfd1`, terracotta `#c75b39` / dark `#a84a2e`, sage `#7a8b6f`, brown `#3d3029` / light `#5c4a3f`
- Warm-only extensions: bone `#faf4e8`, adobe `#d97048`, clay `#8c3a1f`, dusk `#4a382c`, shadow `#251c17`, dust (hairlines) `#c7b9a4`
- Type: Fraunces (display, `WONK` axis on) + Newsreader (body) — both variable, both Google Fonts
- Containers: reading 640px, editorial 1040px, full 1280px. Mobile breakpoint `max-width: 880px`. 8px vertical rhythm, sections in multiples of 24px.

**Signature moves:** fixed drifting sun-cast gradient (`body::before`), SVG paper-grain overlay (`body::after`), grain bleed under the featured headline, the desert-sun motif on the homepage feature (desktop only), hand-drawn animated SVG underlines under section heads on daily briefs only, drop caps on brief ledes.

**Masthead tagline: "The Tucson news you'd otherwise miss, by Nicholas De Leon."** Baked into every published page — changing it means editing `generate_post.py` **and** string-replacing across all published HTML (use Python, not sed — `&` entities break sed). Kicker reads "From the Old Pueblo".

**Footer links:** About, Apple Podcasts, YouTube, Facebook, Instagram, LinkedIn, Email. Facebook (`facebook.com/tucsondailybrief`) + Instagram (`instagram.com/tucsondailybrief`) added 2026-07-19 — these are **brand accounts**, so linking them is consistent with the standing preference that *personal* social not be connected to the site. X and Bluesky were removed 2026-05-15 for that personal-social reason and stay off. Adding/removing a footer link means editing `footer_html()` in `generate_post.py` **and** sweeping it into already-published HTML (Python, not sed — match the adjacent-anchor pair so only the footer is touched; `redesign-preview.html` has no live footer and is skipped).

**Analytics:** GA4 via `gtag.js`, ID `G-MEYSB9GYF2`, site-wide via `ANALYTICS_HTML`.

## SEO layer

Every page carries a meta description, canonical URL, OG + Twitter Card tags, and RSS discovery. Article pages add `article:published_time`; briefs/reports/deep dives add schema.org `NewsArticle` JSON-LD; the homepage carries `WebSite` + `NewsMediaOrganization`. One source of truth: the SEO helpers in `generate_post.py`.

- **Share image:** `assets/og-default.png` (1200×630, terracotta wordmark card) — regenerate with the same chromium-screenshot approach as `social/render_card.py` if the brand changes.
- **`sitemap.xml` + `rss.xml`** are regenerated by `rebuild_homepage()` (`build_sitemap()` / `build_rss()`), so every publishing pipeline refreshes them. RSS = last 30 briefs. Crossword excluded (noindex, subscriber-only).
- **`robots.txt`** (allow all + sitemap pointer) and **`404.html`** (noindex, absolute paths so it works at any URL depth) are static, hand-maintained files.
- **Daily-brief `<title>`/description lead with the day's first real headline** via `extract_headline()` — which skips weather day-labels the same way `collect_existing_posts` does — instead of a bare date.
- **One `<h1>` per page:** the wordmark is an `<h1>` only on the homepage (`site_header_html(h1=True)`); elsewhere the page's own title is the h1.
- Already-published pages were retrofitted in place 2026-07-11; anything new gets meta from its renderer.
- Google Search Console is registered and the sitemap is fetching successfully. Google only — user isn't interested in other engines.

## Site structure

The homepage is a **zoned entry hall** (featured brief + cross-stream cards + Tools row [gated] + subscribe panel + last 7 briefs). The full daily archive is `/briefings.html`.

- **Daily Brief** (`/`, `/briefings.html`, `posts/`) — live
- **What to Watch** (`meeting-watch.html`) — agenda previews, 4 municipalities, auto-published (under the Local Government hub)
- **What They Decided** (`news-reports.html`) — post-meeting reports, AI-drafted, human-reviewed (under the Local Government hub)
- **Spotted** (`public-record.html`) — filings surfaced from agendas; v1 = liquor licenses (Pima, Tucson, Oro Valley). Marana not supported — it handles them administratively, not by council vote
- **Around Town** — development-watch items (Marana + Oro Valley pollers)
- **Ask** (`ask.html`) — RAG Q&A, live, linked site-wide
- **Responsiveness** (`responsiveness.html`) — stub only
- **The Tucson Mini** (`crossword/`) — unlisted subscriber perk
- **About** (`about.html`) — hand-edit only; leads with the reader promise, "How this is made" essay below it
- Planned: The Old Pueblo Speaks, Deep Read, Tracking → `ORIGINAL-JOURNALISM.md`

## Automation

**All AI calls use the Anthropic API via API key**, not a Pro/Max subscription — a deliberate decision from day one, and why the April 2026 subscription-OAuth crackdown didn't affect this pipeline. ~$3–4/month total.

| Time (MST) | Job | Log |
|---|---|---|
| 6:00 AM daily | `generate_brief.py` via `run_brief.sh` — fetch sources → one Sonnet synthesis call → save to canonical path (retry loop, 5 attempts/60s) | — |
| 6:10 AM daily | `run_podcast.sh` — Telegram → blog post + push → daily YouTube Short → podcast script (Haiku) → ElevenLabs TTS → RSS/R2 → YouTube | `/tmp/podcast-gen.log` |
| 8:00 AM daily | `check_agendas.sh` — 4 agenda miners + Spotted + dev watch + auto-schedule live recordings (`ENABLE_AUTO_SCHEDULE=1`); **Mondays** also publish the weekly "Buried in the Agenda" Short | `/tmp/agenda-check.log` |
| 8:45 AM daily | `refresh_ask_index.sh` — rebuild RAG index + `fly deploy` (baked index would otherwise freeze answers) | `/tmp/ask-index-refresh.log` |
| 9:30 AM Mon | `run_foia_spotter.sh` — FOIA Lead Spotter: scan new published news reports for records-request leads, **web-search-verify each lead** (facts accurate? already public? — catches AI-paraphrased program names from our own reports), draft A.R.S. § 39-121 request emails to `records-requests/drafts/`, Telegram alert. **Nothing sends automatically** — human reviews and sends from `nicholas@daylayown.org` | `/tmp/foia-spotter.log` |
| Manual, Sat | `run_newsletter.sh` — **not cron'd.** Run by hand after the Tucson Mini is locked; the generator hard-stops if no puzzle exists for the send date | `/tmp/newsletter-gen.log` |
| Scheduled | `at` jobs — live reporter for YouTube + Swagit meetings | `/tmp/live-reporter*.log` |

The blog post runs **before and independently of** the podcast, so a podcast failure never blocks the blog. Each distribution step is non-fatal. `atd` must be enabled (`systemctl enable --now atd`) for live recordings.

**Key dependencies:** `pdftotext` (poppler-utils) for Tucson PDFs; `at` + `atd`; `ANTHROPIC_API_KEY` in `~/.config/environment.d/anthropic.conf`; Telegram credentials. Telegram delivery happens **only** through `run_podcast.sh` → `send_telegram.py`.

Failure modes, billing detail, and the editor's-desk hook → `PIPELINE.md`.

## Deployment

- **Live:** `https://tucsondailybrief.com` (CNAME), GitHub Pages from `master` root, repo `daylayown/tucson-daily-brief-site`, `.nojekyll` for static serving.
- **Deploy runs via a custom GitHub Actions workflow** (`.github/workflows/deploy.yml`), **not** GitHub's managed "Deploy from a branch" flow. Switched 2026-07-04 because the managed flow has no retry and the Pages backend intermittently failed the hand-off (twice in three days — the build succeeded both times). The workflow uploads the repo root and deploys with **3 attempts + backoff** (60s, 120s), so transient hiccups self-heal. Triggers on push to `master` + manual `workflow_dispatch`.
- Revert if ever needed: `gh api repos/daylayown/tucson-daily-brief-site/pages -X PUT -f build_type=legacy`

## What's next

**The next big project is short-form video** (`SHORT-FORM-VIDEO.md` + `MARKETING.md`) — specifically the distribution loop: two social packages per week for eight consecutive weeks, one moat package + one reach package, each converting toward the newsletter. Everything else in `ROADMAP.md` is captured and gated behind it. Don't start those mid-stream without a user go-ahead.
