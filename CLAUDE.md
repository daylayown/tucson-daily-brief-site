# Tucson Daily Brief Site

Static blog for GitHub Pages — minimal, text-first, Daring Fireball style. No JavaScript, no frameworks, no build tools.

## Project Structure

```
├── style.css                    # Warm-organic Southwest editorial CSS (see REDESIGN-V2.md)
├── generate_post.py             # Daily brief renderer + shared chrome (masthead, footer, section nav, subscribe panel, SVG primitives); also rebuilds homepage and briefings archive
├── index.html                   # Auto-generated homepage — zoned entry-hall layout (NOT the daily archive)
├── briefings.html               # Auto-generated full daily-brief archive page (formerly the role of index.html)
├── posts/                       # Individual daily brief HTML files (named YYYY-MM-DD.html)
├── meeting-watch.html           # Auto-generated Meeting Watch index page
├── meeting-watch/               # Published meeting preview HTML files
├── news-reports.html            # Auto-generated News Reports index page
├── news-reports/                # Published news report HTML files (human-approved)
├── public-record.html           # Auto-generated section index (display name: "Spotted"; URL kept for backwards-compat)
├── public-record/               # Published HTML files for individual filings
├── ask.html                     # Live RAG-powered Q&A interface (Phase 2); POSTs to Fly app tdb-ask; linked in main streams nav as of 2026-06-23
├── responsiveness.html          # Coming-soon stub for the Tucson Responsiveness Index dashboard
├── about.html                   # Hand-authored About page — TAS-metaphor framing, linked from the footer site-wide
├── ai_reporter.py               # Downstream pipeline: transcript JSON → Claude report → Telegram → publish
├── ai_reporter_live.py          # Live input: streamlink/direct HLS → Deepgram WebSocket → transcript JSON
├── ai_reporter_vod.py           # VOD input: ffmpeg → opus → Deepgram batch API → transcript JSON (fallback when live capture fails)
├── run_live_reporter.sh         # Shell wrapper for live reporter (env loading, dep validation)
├── pipeline/                    # Shared reference data injected into pipeline prompts
│   └── local_names.json         # Canonical names + titles + Deepgram misreads for Southern AZ officials and places; loaded by ai_reporter.py at draft time
├── people-photos/               # Research only as of 2026-05-12 — official portraits + _manifest.json + ARCHITECTURE.md; not yet wired into the renderer
├── transcripts/                 # Working directory: transcript JSON + drafts (gitignored)
├── agenda-watch/                # Working directory: markdown previews + full references (not published)
├── agenda_mining.py             # Pima County BOS pipeline (Legistar API)
├── agenda_mining_marana.py      # Marana Town Council pipeline (Destiny Hosted scraping)
├── agenda_mining_orovalley.py   # Oro Valley Town Council pipeline (Destiny Hosted scraping)
├── agenda_mining_tucson.py      # City of Tucson pipeline (Hyland OnBase PDF + pdftotext)
├── check_agendas.sh             # Daily cron wrapper: runs all 4 pipelines + public record, auto-publishes, pushes
├── schedule_recording.py        # Auto-schedules live AI reporter `at` jobs for discovered meetings
├── public_record_liquor.py      # Spotted pipeline: extracts liquor license filings from agenda-watch reference files
├── rag/                         # RAG knowledge agent — Phase 1 (CLI) + Phase 2 (web service) both live
│   ├── build_index.py           # Walks corpus, document-type-aware chunking, embeds via Voyage, writes to sqlite-vec
│   ├── ask.py                   # Core: question → retrieval → Sonnet synthesis with citation discipline + date awareness (CLI + imported by server)
│   ├── server.py                # FastAPI wrapper around ask() — POST /ask, /health, per-IP rate limit, CORS (deployed to Fly app tdb-ask)
│   ├── requirements-server.txt  # Lean runtime deps for the Fly image
│   └── index.sqlite             # Vector store (gitignored; baked into the Fly image at deploy)
├── refresh_ask_index.sh         # Daily 8:45am cron: rebuild index + fly deploy so the live Ask agent stays current
├── Dockerfile                   # Builds the Ask service image (rag/ + baked index.sqlite) for Fly
├── fly.toml                     # Fly.io config for the Ask service (app: tdb-ask)
├── crossword/                   # The Tucson Mini — weekly subscriber crossword (see section below)
│   ├── play.html                # Playable shell, reads ?p=slug query param, has noindex meta
│   ├── crossword.js, style.css  # Vendored game engine (from CtS) + desert-palette restyle
│   ├── tools/                   # generate_puzzle.py, generate_grid.py, read_tdb_posts.py, filter_wordlist.py + wordlists
│   └── puzzles/                 # Generated YYYY-MM-DD-XXXXXX.json (unguessable slugs)
├── generate_newsletter.py       # TDB Weekly newsletter draft generator (Sonnet 4.6, see section below)
├── upload_to_buttondown.py      # Push a markdown draft to Buttondown via API as an editable draft
├── run_newsletter.sh            # Friday 6pm cron wrapper: env loading + generate + upload
├── newsletter/                  # TDB Weekly working directory
│   └── drafts/                  # Generated markdown drafts (gitignored, human-reviewed before send)
├── responsiveness/              # Tucson Responsiveness Index — planning only, not yet building
│   └── PLANNING.md              # Canonical thesis, M1 scope (SeeClickFix 311 + TPD CFS), build sequence
├── social/                      # Instagram/Threads promo image-card renderers (see "Social Media Cards" section)
│   ├── render_card.py           # Core: build_card() -> headless Chromium 2x screenshot -> 1080x1350 PNG; terracotta + light themes; built-in card configs
│   ├── render_feature_carousel.py # Multi-slide swipeable "what sets us apart" carousel (cover -> feature slides -> CTA)
│   ├── render_crossword_card.py # Numbered 5x5 Tucson Mini grid + clues, promoting the Sunday newsletter perk
│   ├── render_story.py          # 1080x1920 IG Story asset (sticker-safe open bottom third)
│   └── cards/                   # Generated PNG output (gitignored; tooling is committed, renders are working state)
├── REDESIGN.md                  # Information architecture redesign — Direction B (zoned homepage), shipped 2026-05-11
├── REDESIGN-V2.md               # Visual language redesign — warm-organic Southwest editorial, shipped 2026-05-11
├── redesign-preview.html        # Self-contained reference demo of the v2 visual language (single file, embedded CSS)
├── MEETING-WATCH-PIPELINE.md    # Full reference docs for the meeting watch system
├── crime.md                     # Research notes (2026-05-19) — FBI NIBRS reporting gap for TPD; downstream aggregators showing "0 violent crimes" for Tucson
├── crime-tpd-data.md            # Research notes (2026-05-19) — TPD's own published crime data 2019–2025, clearance-rate methodology gap, peer-city comparison
├── OV-DATA-FEASIBILITY.md       # Feasibility scan (2026-06-23) — what Oro Valley structured data is machine-collectible (GIS dev cases, vote minutes, FBI crime API, water/budget PDFs)
├── SHORT-FORM-VIDEO.md          # Platform automation map + DIY-adapter plan (2026-06-23) — YouTube/IG/FB auto-publishable for $0, TikTok = future; generation pipeline reuses ~80% of podcast flow
├── CNAME                        # Custom domain: tucsondailybrief.com
├── .nojekyll                    # Tells GitHub Pages to skip Jekyll
├── .gitignore                   # Excludes __pycache__/, .venv/, transcripts/, etc.
└── CLAUDE.md
```

## How It Works

`generate_post.py` takes a briefing markdown file as input and:
1. Extracts the date from the filename (e.g., `tucson-brief-2026-02-18.md` → `2026-02-18`)
2. Converts the markdown to HTML (handles bold, emoji section headers, source citations with links, separators)
3. Writes an editorial-style HTML post (Fraunces display date, drop cap, magazine-style section heads) to `posts/YYYY-MM-DD.html`
4. Calls `rebuild_homepage()` which scans all posts in `posts/` AND the newest entry in `meeting-watch/`, `news-reports/`, `public-record/`, then rebuilds **both** `index.html` (zoned homepage) and `briefings.html` (full daily archive). The homepage's cross-stream cards surface the latest items from every section so a new daily brief, new meeting preview, new news report, or new Spotted filing all refresh the homepage.
5. Is idempotent — running it twice with the same input overwrites cleanly, no duplicates

**Weather-alert-led briefs (fixed 2026-06-23, commit `2c6827d`):** On days with an active NWS alert, the 6 AM agent leads the brief with the Weather section + a `⚠️ **Alert headline.**` callout. This surfaced two bugs, both fixed in `generate_post.py`: (1) `md_to_html` treated *any* emoji-prefixed line as a section header (`<h2>`), so the alert line became a heading with literal `**` asterisks — now an emoji line containing `**` falls through to the paragraph branch and renders the bold properly (real section headers like `🏛️ Government` never contain bold markdown, so they're unaffected); (2) `collect_existing_posts` picked the first `<strong>` as the homepage featured headline, which on weather-led days was a forecast day-label ("Today (Monday, June 22):") — it now skips weather labels (via `_is_weather_label()`: text ending in `:` or containing `°`) and uses the first real headline (e.g. the heat-warning text). Sanity-check the homepage featured card on any weather-alert day.

Usage:
```
# Normal mode — process a single new briefing and refresh derived pages
python generate_post.py ~/.openclaw/workspace/briefings/tucson-brief-2026-02-18.md

# Refresh-only mode — rebuild homepage + briefings.html with no new post
python generate_post.py --rebuild-homepage

# Bulk regen — re-render every individual post HTML from .md sources, then refresh.
# Useful after template changes; not used by cron.
python generate_post.py --rebuild-all ~/.openclaw/workspace/briefings/
```

`generate_post.py` is also the home of the shared chrome — every section index renderer (`agenda_mining.py`, `ai_reporter.py`, `public_record_liquor.py`) imports `ANALYTICS_HTML`, `SUBSCRIBE_PANEL_HTML`, `SCROLL_TRIGGER_JS`, `HAND_RULE_SVG`, `SUNRAY_SVG`, `ARROW_SVG`, `ARROW_LEFT_SVG`, `FEATURED_SUN_SVG`, `site_header_html()`, `section_nav_html()`, `footer_html()`, and `rebuild_homepage()`. One source of truth for masthead, footer, nav, subscribe panel, and SVG primitives.

**Footer is path-aware.** `footer_html(path_prefix="")` takes `""` for root pages and `"../"` for nested pages (so the About link resolves correctly from both `/index.html` and `/posts/YYYY-MM-DD.html`). Every renderer that produces a nested page (`render_meeting_post`, `render_report_post`, the Spotted filing renderer, `render_post`) passes the prefix; root-level renderers call `footer_html()` bare.

## Input Format

Briefing files come from the Tucson Daily Brief podcast project at `~/.openclaw/workspace/briefings/`. They have:
- Title line: "Tucson Daily Brief — February 18, 2026"
- Emoji section headers (🏛️ Government, 🚨 Public Safety, etc.)
- Bold story headlines with descriptions
- Source citations prefixed with 📰 or 📄, in two possible formats:
  - Markdown links (preferred): `📰 [Source Name](https://direct-article-url)`
  - Plain text (legacy/fallback): `📰 Source Name`
- ─── separators between sections
- Weather section
- Trailing metadata lines (stripped during conversion)

## Design

The current visual language is **warm-organic Southwest editorial**, shipped 2026-05-11. The original Daring Fireball-inspired restraint (system fonts, single 600px column, no decoration) is gone. See `REDESIGN-V2.md` for the full plan and `REDESIGN.md` for the IA-only step that preceded it. `redesign-preview.html` at the repo root is a self-contained single-file reference of the visual language.

**Tokens (in `style.css :root`):**
- Locked palette: sand `#f5f0e6`, tan `#e8dfd1`, terracotta `#c75b39` / dark `#a84a2e`, sage `#7a8b6f`, brown `#3d3029` / light `#5c4a3f`
- Extensions (warm-only): bone `#faf4e8`, adobe `#d97048`, clay `#8c3a1f`, dusk `#4a382c`, shadow `#251c17`, dust (hairlines) `#c7b9a4`
- Type: Fraunces (display, with `WONK` axis on for hand-set feel) + Newsreader (body), both variable, both Google Fonts
- Three container widths: reading 640px, editorial 1040px, full 1280px
- Mobile breakpoint: `max-width: 880px` (single-column collapse, site-wide)
- Vertical rhythm: 8px base, sections in multiples of 24px

**Atmospheric signature moves (none of these are required to understand the layout, but they're the brand):**
- **Sun-cast** — fixed warm radial gradient on `body::before`, slowly drifts via 180s alternating animation
- **Paper-grain** — SVG turbulence noise overlay on `body::after`, multiply blend, every page
- **Paper-grain bleed** — denser local noise on `.featured::before`, masked to fade out on the right, concentrating "ink" under the headline
- **Featured sun motif** (`FEATURED_SUN_SVG`) — desert sun with 12 rays of varied length in the upper-right of the homepage feature; echoes the small sunray dingbat used in kickers. Desktop only (hidden under the 880px breakpoint). Sized down 2026-05-13 (max width 240→180px, top -28px) so the bottom of the sun clears the right-column aside even when the daily-brief headline is short (3 lines)
- **Hand-drawn SVG underlines** (`HAND_RULE_SVG`) under section heads on daily-brief posts only — animated draw on first viewport entry via IntersectionObserver. Removed 2026-05-13 from the four section index heads (Daily briefings, Meeting Watch, News Reports, Spotted) where they read as awkward decoration on the big titles
- **Drop caps** on the lede of daily-brief posts (large Fraunces capital, pulled into the column)

**Section nav, footer, masthead** are centralized in `generate_post.py` constants. The masthead kicker reads "From the Old Pueblo" — ties to the "The Old Pueblo Speaks" outreach section under the Roadmap. Footer links (in order): About (`about.html`), Apple Podcasts, YouTube, LinkedIn, Email. X and Bluesky were removed 2026-05-15 — user prefers personal social media (besides LinkedIn) not be connected to the site.

**Feature flag: `SHOW_TOOLS`** in `generate_post.py`. Currently `False`. **Note (2026-06-23): `Ask` has been promoted into the main streams nav (`_STREAMS`) and is now linked site-wide UNCONDITIONALLY — it is no longer gated.** `SHOW_TOOLS` now only gates (a) the secondary Tools nav row, which contains just **Responsiveness**, and (b) the homepage Tools *card* row (where Ask still shows a "Coming soon" card). So the live nav is: Briefings · Meeting Watch · News Reports · Spotted · In Depth · Ask. Flip `SHOW_TOOLS=True` once the Responsiveness dashboard ships.

**Public Record → "Spotted" display rename.** The section's user-facing name is **Spotted** (in the nav, page titles, eyebrows, post-meta). The URL stayed `public-record.html` and the directory stayed `public-record/` so existing links and bookmarks don't break. Internal references in code (file names, Python module names, CSS class `public-record-filing`, etc.) all keep the original `public-record` terminology — only display text changed.

**Analytics:** Google Analytics (GA4) via `gtag.js`, measurement ID `G-MEYSB9GYF2`. Loaded site-wide via `ANALYTICS_HTML` in `generate_post.py`.

## Source Links

`generate_post.py` includes a `SOURCE_URLS` dictionary mapping outlet names to their homepages, and a `linkify_sources()` function that handles two citation formats:

1. **Markdown links** `[Source Name](url)` — links directly to the original article (preferred)
2. **Plain text** `Source Name` — falls back to the outlet's homepage via `SOURCE_URLS` lookup

The upstream briefing agent (`~/.openclaw/workspace/TUCSON-BRIEF.md`) is instructed to include direct article URLs in markdown link format. If it can't determine the URL for a story, plain text is acceptable and the homepage fallback kicks in.

## Automation

### OpenClaw and Anthropic API billing

**All AI calls in this pipeline use the Anthropic API via API key** (`"mode": "api_key"` in `openclaw.json`), not a Claude Pro/Max subscription. This was a deliberate architectural decision from day one (February 2026). The Claude Max subscription is used only for interactive sessions (Claude Code, claude.ai).

**Why this matters:** On April 4, 2026, Anthropic officially cut off Claude subscribers from using Pro/Max subscription OAuth tokens with third-party tools like OpenClaw, citing unsustainable infrastructure strain. Users running agents through flat-rate subscriptions were burning $1,000–5,000/day in equivalent API costs. This crackdown does not affect API key users — only subscription-based auth.

**This pipeline is unaffected.** OpenClaw's role here is as a cron scheduler and skills platform (see below), authenticated via API key. All downstream scripts (`agenda_mining*.py`, `ai_reporter.py`, `generate_podcast.py`) also make direct API calls with the API key from `~/.config/environment.d/anthropic.conf`.

**Monthly API cost:** ~$3–4/month total. Daily briefing (Sonnet) ~$0.09/day, podcast condensation (Haiku) ~$0.01/day, agenda mining (Sonnet) ~$0.50–0.80/month across all four municipalities.

This site is part of a daily pipeline with two stages:

1. **6:00 AM MST** — OpenClaw cron job (`~/.openclaw/cron/jobs.json`) runs the briefing agent (Sonnet 4.6) in an isolated session. The agent reads `TUCSON-BRIEF.md`, fetches sources from `sources.json`, and saves the briefing to `~/.openclaw/workspace/briefings/tucson-brief-YYYY-MM-DD.md`. OpenClaw delivery is set to `"none"` — the agent does not send to Telegram directly.

   **Source-skip mechanism + context-compaction note (2026-06-14):** A source in `sources.json` with `"status": "broken"` OR `"status": "disabled"` is skipped entirely by the agent (rule lives in `TUCSON-BRIEF.md`). `broken` = the feed can't be reached (e.g. Tucson Sentinel, Cloudflare-walled); `disabled` = intentionally paused, still fetchable. Several June briefs ended with a footer note like *"Arizona Daily Star feeds fetched but content unavailable due to context compaction"* — this is the agent honestly reporting that OpenClaw's mid-run context compaction summarized away a heavy feed's raw content before stories could be extracted, so that source contributed ~zero stories those days. The **Arizona Daily Star main feed** (`tucson.com/search/?f=rss&t=article&l=25`) was the main offender: two heavy 25-item Daily Star feeds, and the main one is mostly national/wire/sports with only ~2 of 25 items overlapping the local feed. **Trial fix (2026-06-14):** main feed set `"status": "disabled"`, keeping only **Arizona Daily Star - Local News** (`&c=news/local`) — nearly all hyper-local Tucson coverage. Revert by removing the `status` field. If compaction still drops feeds, the durable fix is an extract-as-you-go instruction in `TUCSON-BRIEF.md` (distill each feed to notes right after fetching, before synthesis).

   **Editor's desk — manual story injection (2026-06-19):** A hook for hand-feeding the daily brief stories that aren't in any `sources.json` feed yet (tips, Chamber/PR emails, scoops you catch early). The file `~/.openclaw/workspace/EDITOR-TIPS.md` holds editor-submitted tips; the "Editor Tips" section of `TUCSON-BRIEF.md` instructs the 6 AM agent to read it every run, include any tip whose `[include-through: YYYY-MM-DD]` date is today or later (ranked by the normal Editorial Priorities), and — as the **one explicit exception to the sources.json-only rule** — fetch the vetted link(s) in a tip to confirm details and build attribution. Tips auto-expire (skipped once their include-through date passes), so they never linger. Each tip carries an editor note steering attribution + tone (e.g. soft-hedge single-source items, report political events neutrally) and may instruct withholding specifics (e.g. report a venue as "Oro Valley" without naming the building). To queue one: add an entry to `EDITOR-TIPS.md` in the documented format (what / when / where / details / sources / editor note + include-through date). First use: the June 22 2026 VP JD Vance Oro Valley event, queued 2026-06-19.

2. **6:10 AM MST** — System cron triggers `~/.openclaw/skills/tucson-daily-brief/scripts/run_podcast.sh`, which waits for the `.md` file, then runs in this order: sends to Telegram (via `send_telegram.py`) → generates blog post + git push → **generates + auto-publishes the daily short-form video to YouTube Shorts** (`social/generate_short.py --publish`) → generates condensed podcast script (via Claude Haiku) → generates podcast audio (ElevenLabs TTS) → uploads RSS/R2 → generates YouTube video → uploads to YouTube. The blog post runs **before** and **independently of** the podcast, so a podcast failure (e.g. ElevenLabs quota exceeded) never blocks the blog. Each distribution step is non-fatal.

   **Daily Short (auto, added 2026-06-23):** after the blog post, `social/generate_short.py --publish` has Haiku pick an *evergreen feel-good* story from the last 14 days of `posts/`, write a facts-only beat script (anti-hype + dedup against already-used stories), render a 1080×1920 "Only in Tucson" clip with its own AI music, and **publish it public to YouTube Shorts unattended** (no review gate — user's call, full auto while it's YouTube-only). Exits non-zero (non-fatal) on days with no fresh feel-good story. See the "Social Media Cards" / `SHORT-FORM-VIDEO.md` for the full design. "Buried in the Agenda" (the moat series) is built but held until there's an audience.

Telegram delivery happens **only** through `run_podcast.sh` → `send_telegram.py`, which reads the saved `.md` file. OpenClaw's cron delivery was disabled to prevent duplicate sends of raw agent output.

### Podcast script condensing

The podcast script is condensed from a full ~7,500-char read (~8 minutes) to a tight ~1,400-char read (~90 seconds) using Claude Haiku. This was implemented to stay within the ElevenLabs Creator tier (100K chars/month, $22/mo). The `condense_script()` function in `generate_podcast.py` sends the full script to Haiku with instructions to pick the top 5 most newsworthy stories, drop weather/source attributions/section transitions, and write in broadcast style. Cost: ~$0.01/day. Falls back to the full script if the API call fails.

**ElevenLabs budget:** Creator tier, 100K chars/month. Condensed podcast uses ~45K chars/month (with Turbo v2.5 at 0.5 credits/char, that's ~22.5K credits/month). Usage-based billing enabled at 25,000 credit threshold as safety net.

### Voxtral TTS as ElevenLabs replacement (researched March 2026)

Mistral released **Voxtral TTS** (4B params) on March 26, 2026 — an open-weights TTS model with a hosted API. It's a strong candidate to replace ElevenLabs for podcast generation.

**Cost comparison:**

| Provider | Cost per 1K chars | Monthly cost (45K chars) | Monthly cost (100K chars) |
|---|---|---|---|
| ElevenLabs Creator | $22/mo flat (overage $0.30/1K) | $22/mo | $22/mo |
| Voxtral TTS API | $0.016/1K chars | **$0.72/mo** | **$1.60/mo** |

**API details:**
- Endpoint: `POST https://api.mistral.ai/v1/audio/speech`
- Model ID: `voxtral-mini-tts-2603`
- Auth: `Authorization: Bearer $MISTRAL_API_KEY`
- Output formats: MP3, WAV, PCM, FLAC, Opus, AAC (MP3 supported directly — no conversion needed)
- Response: JSON with `audio_data` field (base64-encoded), requires `base64.b64decode()`
- Python SDK: `pip install mistralai` → `client.audio.speech.complete()`
- Output sample rate: 24 kHz
- Latency: ~70-90ms model processing, ~3s time-to-first-audio (MP3 streaming)

**Voice cloning:** Adapts from as little as 3 seconds of reference audio. Two approaches:
1. **One-off:** Pass base64-encoded audio clip as `ref_audio` in each request
2. **Saved voice:** Create once via `POST /v1/audio/voices` with `sample_audio` (base64), then use returned `voice_id`

**Quality:** Mistral claims 62.8% listener preference over ElevenLabs Flash v2.5 on naturalness, parity with ElevenLabs v3 on expressiveness. Current pipeline uses Turbo v2.5 (comparable to Flash), so Voxtral could be an upgrade. Not independently benchmarked for news podcast voices yet.

**Limit to watch:** Max 2 minutes of audio per request. Condensed script (~1,400 chars / ~90 seconds) fits. Full script fallback (~7,500 chars / ~8 minutes) would NOT fit — would need chunking or truncation if condensation fails.

**License:** Open weights on HuggingFace are CC BY-NC 4.0 (non-commercial for self-hosting). Hosted API has standard commercial terms — no restriction.

**What the swap looks like:** ~15-line change in `generate_podcast.py`. Replace the ElevenLabs HTTP POST with Voxtral endpoint, swap auth header, change voice parameter, add base64 decode. `clean_for_tts()`, condensation, RSS, R2 upload, and YouTube pipeline are all untouched.

**Status:** Research complete. Next step is a side-by-side audio quality test — generate a sample episode via Voxtral API and compare against current ElevenLabs output. Requires Mistral API key from `console.mistral.ai`.

## Meeting Watch (Agenda Mining Pipeline)

Automated "What to Watch" previews for government meetings across four municipalities. Runs daily via cron, auto-publishes to the site with zero human intervention. See `MEETING-WATCH-PIPELINE.md` for full reference.

### How it works

**8:00 AM MST** — `check_agendas.sh` runs all four pipelines:

| Municipality | Script | Data Source | Method |
|---|---|---|---|
| Pima County BOS | `agenda_mining.py` | Legistar REST API | JSON API, filter procedural items |
| Marana Town Council | `agenda_mining_marana.py` | Destiny Hosted (id=62726) | HTML scraping |
| Oro Valley Town Council | `agenda_mining_orovalley.py` | Destiny Hosted (id=67682) | HTML scraping |
| City of Tucson | `agenda_mining_tucson.py` | Hyland OnBase | PDF download → pdftotext → strip boilerplate |

Each pipeline: checks for new agendas → sends to Claude Sonnet 4.6 for editorial analysis → saves preview + full reference markdown → auto-publishes to HTML → git commit & push → Telegram notification.

Previews are only generated once per meeting (idempotent). Each script checks for an existing `{slug}-preview.md` in `agenda-watch/` before processing a meeting — if the file exists, it skips. This is critical: without the check, the cron wrapper re-publishes and re-sends Telegram notifications for old meetings every day. Any new pipeline script **must** include this guard.

### Publishing flow

Each script has a `--publish` flag that converts a markdown preview to HTML using shared functions from `agenda_mining.py` (`preview_md_to_html`, `render_meeting_post`, `render_meeting_index`). Publishing also rebuilds the `meeting-watch.html` index page. The cron wrapper calls `--publish` automatically and then does a single `git add -A && git commit && git push` at the end. After publishing, a Telegram notification is sent linking to `https://tucsondailybrief.com/meeting-watch.html` (note: `.html`, not `/meeting-watch/` — GitHub Pages does not serve directory index files).

**Slug routing in `check_agendas.sh`:** The cron wrapper determines which publish script to use by matching the preview filename against municipality keywords (`marana`, `orovalley`, `tucson`, else Pima County). **Critical:** this matching is done on `basename` only, not the full path — the repo directory name (`tucson-daily-brief-site`) contains "tucson" and would falsely match every preview against the Tucson check. This was a bug fixed April 2026 that caused Pima County previews to be published with `tucson-council-` slugs.

### Key dependencies

- `pdftotext` (poppler-utils) — required for Tucson PDF extraction
- `at` + `atd` daemon — required for scheduled live recordings
- `ANTHROPIC_API_KEY` in `~/.config/environment.d/anthropic.conf`
- Telegram credentials for notifications

## Roadmap: Original Journalism

The daily brief repackages existing journalism. The agenda mining pipeline (above) is the first **original journalism** feature — AI-generated previews of government meetings. The next stage expands this with more content types.

### Planned content types

- **Post-Meeting News Reports** — ✅ **LIVE.** AI reporter transcribes government meetings (live or from VOD) and generates AP-style news reports; human editorial review required before publishing. First real recordings April 7-8, 2026; steady cadence since. As of 2026-05-21, ten reports published covering Pima County BOS (study sessions, regular meetings, special meetings), Tucson Mayor & Council, Marana Town Council, and Oro Valley Town Council. **First successful live capture of a Marana Town Council meeting completed 2026-05-19** using the newly verified Swagit HLS URL (see "Live stream URLs by municipality" below). The Oro Valley May 20 report (Sun City Lion's Head Fountain amendment, Leisure Travel Plan adoption, formal in-house town attorney transition) added a tenth name to the bible: **Steven Zraick**, the new Town Attorney who replaced the Clark & Rothschild contract arrangement — Deepgram heard "Drake" (phonetically /zraɪk/ → "Drake" with mis-segmented leading Z), confirmed via signed Resolution R26-16 (April 22, 2026) on Destiny Hosted; the misreads `["Drake", "Strake", "Zrake"]` are now in the bible so future drafts catch it automatically. Recording is auto-scheduled by `schedule_recording.py` from agenda-watch previews (gated by `ENABLE_AUTO_SCHEDULE=1`). Names bible (`pipeline/local_names.json`, see below) injected into the report-generation prompt as of 2026-05-12 dramatically reduced editorial review time by correcting Deepgram name mistranscriptions before drafts land.

- **Agenda Mining** — ✅ **LIVE.** Before meetings happen, read every agenda and supporting document. Surface buried items that reporters would miss and publish "what to watch" previews. Auto-publishes for all four municipalities.

- **Spotted** (formerly "Public Record") — ✅ **LIVE (April 11, 2026; renamed 2026-05-11).** Surfaces public filings buried in government meeting agendas — starting with liquor license applications. Most never get reported on. The pipeline (`public_record_liquor.py`) is a post-process that runs after the four agenda miners finish: it scans the `agenda-watch/*-full.md` reference files, identifies liquor license items via keyword + line clustering, and uses Claude Sonnet to extract structured data (business name, address, series, license type, action type, applicant, ward) plus a 2-sentence newspaper-style summary. Each filing publishes as its own HTML page under `public-record/` (URL kept; only display name changed). Coverage: Pima County BOS, City of Tucson, Oro Valley Town Council. **Marana intentionally not supported** — Marana handles liquor licenses administratively through the Town Clerk and does not agendize them for council vote. Future expansion: scrape the Marana clerk page directly. Each cron run sends one consolidated Telegram notification if any new filings were published. Idempotent via `public-record/.processed.txt` (gitignored) plus per-filing output-file existence check. Cost: ~$0.005 per source file processed (one Sonnet call per liquor block, typically 1-3 filings extracted per call). The "Roadmap: Original Journalism" thesis in action — these filings are the basis for both automated coverage and the planned **The Old Pueblo Speaks** outreach pipeline (see above), which takes each Spotted filing and produces a draft request-for-comment email to the business owner for human review and send.

### Post-meeting data sources (researched March 2026)

| Municipality | Minutes | Video/Audio | Transcripts | Livestream |
|---|---|---|---|---|
| **Pima County** | Summary PDFs via Legistar API (`EventMinutesFile`) | Granicus player (`pima.granicus.com/player/clip/{EventMedia}`) | None published | Granicus + YouTube |
| **Marana** | Summary PDFs on Destiny Hosted | Swagit (`maranaaz.new.swagit.com/videos/{id}`), MP4/MP3 | **Auto-generated from closed captions** at `/videos/{id}/transcript` | Swagit + Zoom |
| **Oro Valley** | Summary PDFs on Laserfiche + Destiny | Swagit (`orovalleyaz.new.swagit.com/videos/{id}`), MP4/MP3 | Closed captions via Swagit (possibly human-generated) | Swagit |
| **Tucson** | Summary PDFs on OnBase (`documentType=2`) | YouTube (`@cityoftucson`) + Internet Archive (`archive.org`) | None published | YouTube Live |

**Key URLs for future pipeline:**
- Marana transcripts: `https://maranaaz.new.swagit.com/videos/{id}/transcript`
- Oro Valley videos: `https://orovalleyaz.new.swagit.com/videos/{id}` (MP4/MP3 download links)
- Oro Valley minutes (Laserfiche): `https://srvvlfweb01.orovalley.net/WebLink/CustomSearch.aspx?SearchName=Minutes&dbid=0&repo=OroValley`
- Tucson YouTube: `https://www.youtube.com/@cityoftucson/streams`
- Tucson Internet Archive: `https://archive.org/details/cotaz-Tucson_Mayor_and_City_Council_Meeting_{date}`
- Pima County Granicus: `https://pima.granicus.com/player/clip/{clip_id}`
- Pima County minutes via API: `EventMinutesFile` field on `/v1/pima/events/{id}`

**Recommended build order for post-meeting pipeline:**
1. **Marana** (easiest) — Swagit transcripts already available as text, just fetch and send to Claude
2. **Oro Valley** — Same Swagit platform, captions may be higher quality (human-generated)
3. **Tucson** — Download audio from YouTube via `yt-dlp`, transcribe with Deepgram
4. **Pima County** (hardest) — Need to figure out Granicus video/audio download, then transcribe

### AI Reporter Pipeline

Live pipeline built March 2026. VOD pipeline built May 2026 (`ai_reporter_vod.py`).

**Architecture:**
```
Live input (YouTube):  streamlink → ffmpeg (PCM 16kHz mono) → Deepgram WebSocket → transcript JSON
Live input (Swagit):   ffmpeg reads HLS .m3u8 directly (--direct mode) → Deepgram WebSocket → transcript JSON
VOD input:             ffmpeg extracts → opus file → Deepgram batch (pre-recorded) API → transcript JSON
                                                                                    │
Downstream:            transcript JSON → Claude Sonnet 4.6 news report → Telegram review → approve → publish HTML
```

**Why a separate VOD pipeline?** Deepgram's live WebSocket API expects ~1× real-time audio. ffmpeg reading an HLS VOD pulls audio much faster than real-time, which floods the live WebSocket and triggers a 1011 keepalive-timeout error after a minute or two. Verified on the Marana May 5 VOD (2026-05-10): live pipeline died after capturing 95 seconds; batch API processed the same 72-minute meeting cleanly in one shot. The batch API is the right tool whenever the source is a complete recording rather than a real-time stream.

**Scripts:**

| Script | Purpose |
|---|---|
| `ai_reporter.py` | Downstream pipeline: transcript JSON → Claude report → Telegram → approve/publish |
| `ai_reporter_live.py` | Live input: streamlink or direct HLS → Deepgram WebSocket → real-time terminal display → transcript JSON |
| `ai_reporter_vod.py` | VOD input: any audio/video URL or local file → ffmpeg extracts opus → Deepgram batch API → transcript JSON, then hands off to `ai_reporter.py` for the draft |
| `run_live_reporter.sh` | Shell wrapper: loads env vars, validates deps, waits for stream to go live, passes args through. Skips streamlink/yt-dlp checks in `--direct` mode |

**Usage:**
```bash
# Capture a YouTube live stream and generate a news report
./run_live_reporter.sh "https://youtube.com/watch?v=XXX" --slug pentagon-2026-03-26

# Capture a Swagit/HLS live stream (direct mode — no streamlink needed)
./run_live_reporter.sh "https://stream.swagit.com/live-edge/orovalleyaz/smil:hd-16x9-1-a/playlist.m3u8" --slug orovalley-council-2026-04-08 --direct

# Transcribe only (no news report)
./run_live_reporter.sh "https://youtube.com/watch?v=XXX" --slug test-1 --transcribe-only

# Generate a report from an existing transcript
python3 ai_reporter.py transcripts/pentagon-2026-03-26.json

# Re-generate with --force if draft already exists
python3 ai_reporter.py transcripts/pentagon-2026-03-26.json --force

# Approve and publish a draft
python3 ai_reporter.py --approve transcripts/pentagon-2026-03-26-draft.md

# Publish an already-approved file
python3 ai_reporter.py --publish transcripts/pentagon-2026-03-26-approved.md

# VOD transcription — when live capture failed or the source is a recording
# (HLS playlist URL works; MP4 / local file works; ffmpeg handles any input format)
.venv/bin/python3 ai_reporter_vod.py \
    "https://archive-stream.granicus.com/.../playlist.m3u8" \
    --slug marana-2026-05-05 \
    --title "Marana Town Council Regular Meeting" \
    --started-at 2026-05-05
```

**File layout:**
```
transcripts/                              # Working directory (gitignored)
  pentagon-2026-03-26.json                # Raw Deepgram transcript
  pentagon-2026-03-26-partial.json        # Auto-saved during live capture (every 60s)
  pentagon-2026-03-26-draft.md            # Claude news report draft
  pentagon-2026-03-26-approved.md         # Human-approved version

news-reports/                             # Published HTML (on GitHub Pages)
  pentagon-2026-03-26.html

news-reports.html                         # News Reports index page
```

**Transcript JSON schema:**
```json
{
  "meta": {
    "source_url": "https://youtube.com/...",
    "slug": "pentagon-2026-03-26",
    "title": "Pentagon Press Briefing",
    "started_at": "2026-03-26T14:00:00Z",
    "ended_at": "2026-03-26T14:45:00Z",
    "duration_seconds": 2700,
    "provider": "deepgram",
    "model": "nova-2",
    "diarization": true
  },
  "segments": [
    {"start": 0.0, "end": 3.5, "speaker": 0, "text": "Good afternoon.", "confidence": 0.98}
  ]
}
```

**Wait-for-stream:** Two modes depending on input type:
- **Streamlink mode** (default): `run_live_reporter.sh` polls with `yt-dlp --simulate` every 60 seconds for up to 30 minutes. YouTube's `/live` URL for a channel always redirects to the current livestream if one exists, but returns nothing if the channel isn't streaming yet.
- **Direct mode** (`--direct`): The shell wrapper skips yt-dlp polling. Instead, `ai_reporter_live.py` probes the URL with a quick `ffmpeg` read attempt, retrying every 60 seconds for up to 30 minutes. This is needed for HLS URLs (Swagit, etc.) that yt-dlp doesn't understand.

**Scheduling live recordings with `at`:**

Recordings can be pre-scheduled using the `at` command (package: `at`, daemon: `atd`). `at` captures the current working directory and environment at scheduling time.

```bash
# Schedule a YouTube recording — start 5 min before meeting, retry loop handles the gap
echo "./run_live_reporter.sh 'https://www.youtube.com/@PimaCountyArizona/live' --slug pima-bos-2026-04-07 >> /tmp/live-reporter.log 2>&1" | at 8:55 AM 2026-04-07

# Schedule a Swagit/HLS recording (direct mode)
echo "./run_live_reporter.sh 'https://stream.swagit.com/live-edge/orovalleyaz/smil:hd-16x9-1-a/playlist.m3u8' --slug orovalley-council-2026-04-08 --direct >> /tmp/live-reporter-ov.log 2>&1" | at 4:55 PM 2026-04-08

# List scheduled jobs
atq

# Inspect a job
at -c <job_number>

# Remove a job
atrm <job_number>
```

**Live stream URLs by municipality:**

| Municipality | Platform | Live URL | Mode |
|---|---|---|---|
| Pima County BOS | YouTube | `https://www.youtube.com/@PimaCountyArizona/live` | streamlink (default) |
| City of Tucson | YouTube | `https://www.youtube.com/user/CityofTucson/live` | streamlink (default) |
| Oro Valley | Swagit (HLS) | `https://stream.swagit.com/live-edge/orovalleyaz/smil:hd-16x9-1-a/playlist.m3u8` | `--direct` |
| Marana | Swagit (HLS) | `https://edge-f.swagit.com/live/maranaaz/live-1-a/playlist.m3u8` | `--direct` |

Pima County and Tucson stream on YouTube (use default streamlink mode). Oro Valley and Marana stream on Swagit, which serves HLS `.m3u8` streams — use `--direct` mode to have ffmpeg read the URL directly, bypassing streamlink. Swagit's streaming infrastructure uses Video.js + HLS.js on the frontend, backed by `stream.swagit.com` CDN.

**Auto-scheduling from agenda mining (built April 2026):** `check_agendas.sh` calls `schedule_recording.py` after each new preview is published. The scheduler:

1. Reads the `{slug}-full.md` reference file produced by the miner.
2. Asks Claude Sonnet for a structured JSON extraction of `public_session_start` — deliberately distinguishing it from any executive session that might precede it (e.g., Oro Valley's "Regular Session at or after 5:00 PM" [executive] vs "Resume Regular Session at or after 6:00 PM" [public]). Returns `confidence: high|medium|low` with one-sentence reasoning.
3. Looks up the stream URL + mode from a hardcoded `STREAM_SOURCES` dict (YouTube/streamlink for Pima + Tucson, Swagit/`--direct` for Oro Valley + Marana).
4. Schedules an `at` job for `max(now+2min, public_session_start - 5min)` — 5-min lead absorbs minor meeting slop, the `now+2min` floor handles same-day discovery (e.g., agenda posted at 8 AM for a 9 AM BOS meeting).
5. Persists state to `agenda-watch/.scheduled.json` (gitignored) keyed by slug. On the next run, matching public-session times are no-ops; different times trigger `atrm` + re-schedule.
6. Sends a Telegram notification with the meeting time, `at` job id, confidence level, and the LLM's reasoning notes. Low-confidence extractions are tagged "please verify".

**Enable flag:** The scheduling call in `check_agendas.sh` is gated by `ENABLE_AUTO_SCHEDULE=1`. **This is enabled in the 8 AM cron line as of April 24, 2026** — the crontab prefixes the command with `ENABLE_AUTO_SCHEDULE=1`. To temporarily disable, either `crontab -e` and remove the prefix, or unset the env var in an ad-hoc run. Backup of the pre-change crontab lives at `~/.cache/crontab/crontab.bak`.

**Marana stream URL verified 2026-05-19.** The live URL is `https://edge-f.swagit.com/live/maranaaz/live-1-a/playlist.m3u8` — captured via devtools (Network → `.m3u8` filter) on `www.maranaaz.gov/Council/Public-Meeting-Videos` during the May 19 Town Council broadcast. The previous inferred URL (`stream.swagit.com/live-edge/maranaaz/smil:hd-16x9-1-a/playlist.m3u8`, copied from the Oro Valley pattern) was wrong on three dimensions: different host (`edge-f` vs `stream`), different path segment (`/live/` vs `/live-edge/`), and different stream slug (`live-1-a` vs `smil:hd-16x9-1-a`). The inferred URL had failed live capture twice (most recently 2026-05-05, ffmpeg retried for 30 min and got nothing). Lesson: Swagit's URL conventions vary per municipality — do not infer; always verify via devtools during a real broadcast before scheduling.

**Backtest and audit commands:**
```bash
# Dry-run extraction against every existing preview (no `at`, no state write, no Telegram)
python3 schedule_recording.py --all-dry-run

# List currently-scheduled recordings
python3 schedule_recording.py --list

# Manual schedule for a single preview
python3 schedule_recording.py agenda-watch/pima-county-2026-04-29-preview.md \
    agenda-watch/pima-county-2026-04-29-full.md pima-county

# Force re-schedule even if state matches
python3 schedule_recording.py --force <preview> <full_ref> <municipality>
```

**Reschedule/cancellation limits:** The scheduler handles same-slug rescheduling (e.g., the same meeting gets a new time in a re-posted agenda). It does **not** handle date-level moves or cancellations — if a meeting is moved to a different day, the old `at` job remains scheduled and must be manually removed via `atrm`. Future improvement: nightly cleanup pass that prunes stale entries from `.scheduled.json`.

**Live pipeline details:**
- Audio pipeline (default): `streamlink --stdout URL audio_only` → `ffmpeg` (convert to PCM s16le, 16kHz, mono) → Python reads 4096-byte chunks (~128ms) → Deepgram WebSocket
- Audio pipeline (direct): `ffmpeg -i URL` reads HLS/RTMP directly → same PCM conversion → same Deepgram path
- Deepgram config: nova-2 model, smart_format, diarize, interim_results, 300ms endpointing
- Terminal display: interim results shown in-place, final results with timestamps and speaker labels
- Periodic save every 60 seconds to `{slug}-partial.json` (crash protection)
- Graceful shutdown: Ctrl+C, dead air timeout (15 min default, only after first speech AND after the 4 hr `min-recording-time` floor), max duration (6 hr default), or stream end → flushes Deepgram finals, saves transcript, auto-runs downstream pipeline
- Cost: ~$0.0077/min (~$1.38 for a 3-hour meeting)
- Idempotency: skips if transcript JSON already exists; skips draft generation if `-draft.md` exists (use `--force` to override)
- Runs unattended: designed for automated recording of town halls/briefings with no human monitoring

**Deepgram setup:** ✅ Done (March 27, 2026). API key in `~/.config/environment.d/deepgram.conf`. $200 free credit claimed.

**Dependencies:** ✅ Installed. `streamlink` and `yt-dlp` via pacman, `deepgram-sdk` (v6.1.1) via pip in project venv (`.venv/`). The shell wrapper `run_live_reporter.sh` uses `.venv/bin/python3` automatically.

**Deepgram SDK v6 notes:** The script was updated from the v3/v4 API to v6.1.1. Key differences: context manager pattern (`with client.listen.v1.connect(...) as connection`), `EventType.MESSAGE` replaces `LiveTranscriptionEvents.Transcript`, `send_media()` replaces `send()`, `send_close_stream()` replaces `finish()`, boolean params must be passed as strings (`"true"` not `True`) due to SDK query string encoding bug.

**Auto-stop behavior:** The live pipeline runs unattended with three auto-stop triggers:
- **Dead air timeout** (default 15 min) — no speech detected → graceful stop. Configurable via `--dead-air-timeout N` (seconds). **It only fires after TWO gates clear: (1) first speech has been detected, and (2) the `--min-recording-time` floor has elapsed — which defaults to 4 hours** (`MIN_RECORDING_TIME` in `ai_reporter_live.py`, measured from recording start, configurable via `--min-recording-time N`). The first-speech gate ignores pre-meeting silence so the recorder can wait through late starts and always-on streams (e.g., Tucson's 24/7 YouTube stream); the 4-hour floor means mid-meeting silence (recesses, closed/executive sessions) in the first 4 hours will **not** stop the recording. Practical consequence: for a meeting that opens with a closed executive session before the public portion (e.g., the June 1 2026 Pima County BOS ACA-lawsuit special meeting), the recorder sits through the silent closed session and still captures the public vote when it resumes — no flag tuning needed. The first-speech gate was added April 7, 2026 after both Pima County BOS and Tucson Mayor & Council recordings failed due to late meeting starts.
- **Max duration** (default 6 hours) — safety cap to prevent runaway costs. Configurable via `--max-duration N` (seconds).
- **Stream end** — streamlink/ffmpeg exit when the broadcast ends.

**Tested:** March 27, 2026. Verified on live YouTube streams (WWE, Al Jazeera). Broadcast-quality audio produces near-perfect transcripts (confidence 0.999-1.0). Speaker diarization working.

**VOD pipeline (built 2026-05-10):**
- `ai_reporter_vod.py` — ffmpeg extracts audio from any URL or local file → opus at 24 kbps mono 16 kHz → Deepgram pre-recorded API (`POST /v1/listen`) with `model=nova-2&diarize=true&utterances=true&smart_format=true&punctuate=true&language=en-US` → utterances mapped into the standard transcript JSON schema → exec `ai_reporter.py` for the Sonnet draft.
- Why batch vs. live for VOD: Deepgram's live WebSocket expects ~1× real-time audio; ffmpeg pulls HLS VODs much faster and triggers a 1011 keepalive timeout. Batch API ingests at its own pace.
- Cost: ~$0.0043/min (~$0.31 for a 72-minute meeting via the pre-recorded endpoint, well under the live pipeline's $1.38 for a 3-hour meeting because there's no streaming overhead).
- Wall clock: ~5–10 minutes total for a 72-min meeting (ffmpeg HLS pull is the bottleneck; Deepgram batch returns much faster than real-time).
- First production use: Marana May 5 Town Council Regular Meeting, transcribed via VOD on 2026-05-10 after live capture failed. 1,095 utterances, 16 diarized speakers, clean draft.
- Marana/OV Swagit auto-transcripts (available 1–3 business days after a meeting at `maranaaz.new.swagit.com/videos/{id}/transcript`) remain a viable alternative when human-quality captions are preferable to Deepgram's batch output — but our pipeline doesn't ingest them yet.

**STT provider research (March 2026):**

OpenAI's Realtime API was evaluated as an alternative to Deepgram for live transcription. **Decision: stick with Deepgram.** Key findings:

| | OpenAI Realtime | Deepgram WebSocket |
|---|---|---|
| 3-hr meeting cost | $0.54 (mini) / $1.08 (4o) | $1.39 |
| Session limit | **60 min** (dealbreaker) | **None** |
| Latency | 300-800ms | Sub-300ms |
| Audio formats | PCM16 only (24kHz mono) | PCM, Opus, MP3, WAV, FLAC... |
| Speaker diarization | No | Yes |
| Free credits | None | $200 (~430 hrs) |

OpenAI's 60-minute session cap requires 3-4 reconnections per meeting with potential audio gaps — unacceptable for production. Also: no speaker diarization (needed to attribute statements to council members), PCM16-only input (YouTube streams AAC/Opus, would need ffmpeg conversion), and the API is designed for interactive voice agents, not passive long-form monitoring. The ~$0.85/meeting savings doesn't justify the complexity. OpenAI's batch `gpt-4o-mini-transcribe` ($0.003/min) remains a viable VOD alternative if Deepgram batch pricing is unfavorable.

Google's Gemini 3.1 Flash Live (launched March 2026) was also evaluated. **Decision: rejected, same fundamental problem as OpenAI.**

| | Gemini 3.1 Flash Live | Deepgram WebSocket |
|---|---|---|
| 3-hr meeting cost | ~$0.90 (audio input) | $1.39 |
| Session limit | **10-15 min** (dealbreaker) | **None** |
| Latency | "Optimized for real-time" (no exact number) | Sub-300ms |
| Audio formats | PCM, AAC, FLAC, MP3, OGG, WAV, WebM | PCM, Opus, MP3, WAV, FLAC... |
| Speaker diarization | No | Yes |
| Free credits | Free tier available | $200 (~430 hrs) |

The 10-15 minute session cap is even worse than OpenAI's 60 minutes — would need 12-18 reconnections per 3-hour meeting, with no session resumption support. No speaker diarization either. Gemini Live API is designed for conversational voice agents, not passive long-form monitoring. Gemini's non-Live batch API could be worth evaluating for the VOD pipeline separately.

**No municipality publishes verbatim transcripts as official records** — all four produce summary/action minutes only. For full meeting content, video/audio recordings + transcription is the only path.

**Transcript availability timing (Marana, tested March 2026):** Marana's policy is recordings within 3 working days. In practice, the March 3 (Tuesday evening) meeting had a full Swagit transcript available by March 8 (Sunday). Transcripts are auto-generated from closed captions, so they're likely available as soon as the video is posted — estimated **1-3 business days** after the meeting. Pipeline approach: morning-after cron check, retry daily until transcript appears, then draft and send to Telegram for human review.

### Local names and places bible

Built 2026-05-12 during an editorial review of a Pima County BOS draft that surfaced systematic Deepgram errors (Cano → Conner, Cullen → Cohen, Cuaron → Quaron, Acuña → Cunno, Heinz → Hines, Winfield → Rainfield/Wynne/Ranfeld). The bible is a single JSON file holding canonical names, titles, and known mistranscriptions for every regularly-cited official across the four municipalities plus regional/state players. Loaded by `ai_reporter.py` and injected into the report-generation system prompt so Sonnet writes the correct name on first reference and fixes pronouns to match.

**File:** `pipeline/local_names.json`. Top-level keys: `pima-county`, `tucson`, `marana`, `orovalley` (per-jurisdiction rosters) and `regional` (countywide elected officials, state-level players like the AZ Auditor General, regional landmarks). Each bucket has `people[]` and `places[]` arrays with `canonical`, `title`, optional `pronouns`, and `deepgram_misreads` arrays. A `_meta.verification_needed` array flags entries the original roster pass couldn't fully confirm (currently Suzanne Droubie, Dan Hunt) so they get re-checked before they appear in a real transcript.

**Integration in `ai_reporter.py`:** `municipality_from_slug()` matches the transcript slug prefix to a municipality, and `load_local_names_reference()` formats the relevant municipality plus the shared `regional` bucket into a "REFERENCE — CANONICAL NAMES AND PLACES" block injected after the speaker note. Unknown slugs return empty cleanly. Per-call overhead: ~500-700 tokens (fractions of a cent).

**How to grow the bible:** every editorial review yields new misreads — add them to the relevant entry's `deepgram_misreads` array as you encounter them. New officials surfacing in a meeting (e.g., the Pima County Elections Director, AZ Auditor General team) should be added to the appropriate bucket. Bible is the single source of truth; no separate post-pass regex layer is needed at this scale.

**First production proof:** the 2026-05-12 Pima County BOS regular meeting draft (Nanos perjury referral). Every Pima County name came through correctly on first reference — Cano with accent, Heinz not Hines, Cázares-Kelly with accent, DeBonis spelled right — and editorial review focused entirely on substantive issues (vote tally, attribution, framing) rather than name corrections.

- **Spotted, expanded scope** — Currently covers liquor license filings (live as of 2026-04-11). Roadmap: monitor building permits, business license applications, court filings, and campaign finance disclosures. Flag anomalies — large developments before they're announced, unusual donations, lawsuits involving the city.

- **Budget & Spending Analysis** — Track city/county budgets, check registers, and contract awards. Flag unusually large contracts, sole-source awards, and spending trends. Compare budget projections vs. actuals over time.

- **Deep Read** — AI-assisted analysis of large documents when they drop: environmental impact statements, audit reports, proposed legislation, police use-of-force statistics, school performance data.

- **Cross-referencing** — Connect dots across public datasets: developers who get rezonings and also donate to council members, LLCs buying properties along future transit corridors, contractors who win multiple bids and employ registered lobbyists.

- **Community Input Analysis** — Analyze public comment submissions on controversial projects (hundreds of written comments that get one-sentence summaries in staff reports). Track 311 complaints by neighborhood.

- **FOIA Lead Spotter** — A downstream post-processing layer that runs a Sonnet pass over ingested public documents (agenda-watch full references, news report drafts, public record filings) to flag items worth a public records request. Target signals: sole-source contracts above a threshold, agenda items referencing documents not included in the packet (audits, assessments, studies), rezoning decisions with thin supporting documentation, budget amendments with no attached justification. Output is a Telegram notification with the specific item, which document it came from, and what record to request — a lead, not an automated filing. The human decides whether to pursue. Fits the same architecture as `public_record_liquor.py`: scan existing reference files, apply editorial judgment via LLM, notify. Natural to build after the existing pipelines are producing steady volume, since more data flowing through means more signal to catch.

- **The Old Pueblo Speaks** — Outreach pipeline that turns Spotted filings into actual journalism by hearing from the people behind them. When Spotted publishes a new filing, a follow-up script drafts a polite request-for-comment email to the business owner / applicant / responsible party, asking for a short statement or interview. Draft saved as markdown in `outreach/drafts/{slug}.md` with a structured header (to/from/subject/body/source-filing-link/date). User edits and sends manually from `nicholas@daylayown.org` via Gmail. When a response comes in, it gets paired with the original filing and published as a short interview/statement post under a new "The Old Pueblo Speaks" section on the site (homepage link, section index, individual pages). Name ties to the masthead kicker ("From the Old Pueblo") — the section is literally Old Pueblo voices speaking.

  **Build sequence (each gate de-risks the next):**
  1. Drafter only, no contact discovery. Input: a Spotted filing's structured data. Output: a markdown email draft in the outreach folder. Use existing 18 filings as test cases. If drafts read at human-quality, proceed.
  2. Add contact discovery — Google + Sonnet web-search to find owner contact info (~50-70% accurate on small businesses; chains are easier). Pre-fill the "to" address; if no contact found, flag `research_needed: true` so user knows to look it up.
  3. Wire to Spotted's publish step (already extends `public_record_liquor.py` via Telegram on new filings — add the drafter call there).
  4. Build the section publisher — takes a manually-paired (filing, response) markdown and produces an HTML page under `the-old-pueblo-speaks/{slug}.html`, plus rebuilds the section index. Same shape as the existing news-reports renderer.

  **Send mode:** manual is the default and current intent — drafts sit in the folder, user edits and sends from Gmail by copy-paste. Architectural support for `SEND_MODE=auto` (smtplib + Gmail app password) can ship alongside but stays off; flip the flag once the prompt is calibrated against 4-8 weeks of real responses. Manual review also catches edge cases: some "applicants" on filings are corporate attorneys acting on behalf of the actual owner, and an auto-email to a Phoenix law firm asking about a Tucson bar would land badly.

  **The hard engineering problem is contact discovery, not drafting.** Liquor license filings give an applicant's legal name but rarely an email. The web-search step is where accuracy and reputational risk both concentrate. Start with the drafter; add discovery only when drafts are proven.

  **Volume sizing:** Spotted is currently 1-3 filings/week. Manageable manually. If Spotted expands to building permits, court filings, or campaign finance disclosures (as planned above), volume could go 10× — at which point the section needs a real triage/review tool, not just folders. Size the data model for that eventual scale now.

- **Tracking** — Standing topic pages that aggregate everything TDB knows about a developing story (e.g., the Karla Toledo ICE detention from 2026-05-19), backed by research-agent pulls of external coverage and primary documents. Solves the local-news SEO problem: fragmented daily-brief paragraphs don't rank for "Karla Toledo ICE Tucson," but a canonical `/tracking/karla-toledo` page would. Also a real reader-value problem — no other Tucson outlet does the running-file format.

  **Name:** "Tracking" picked because it's two-syllable, fits the sectional pattern (Meeting Watch / News Reports / Spotted / Tracking), reads honestly as "developing story" rather than overpromising investigative reporting, and matches a query users actually google.

  **Page structure (v1):** TLDR + "Updated: [date]" badge; timeline of dated events; key people; what TDB has covered (links to daily briefs, news reports, meeting-watch entries); external coverage cited and dated; primary documents when research agents find them; open questions / what to watch next.

  **Editorial model:** Human review required on every publish AND every update — this is not the agenda-mining model. A standing canonical page that's wrong stays wrong, so the bar is the news-reports bar, not the previews bar.

  **Source model:** TDB RAG corpus is the spine ("everything TDB has said about Topic X across daily briefs + meeting transcripts + news reports + agenda full references"). Research agents add external coverage (KGUN, AZ Daily Star, KOLD, federal court records, agency press releases) and primary documents (council statements, detention records, FOIA returns) so the page is more than an aggregation of secondhand reporting. For the Toledo example: lead with what TDB uniquely knows about Tucson sanctuary-city policy and TPD's ICE-cooperation posture from meeting coverage, then layer KGUN's reporting and external primary docs underneath.

  **Hard gate: ship after RAG Phase 2 is fully deployed.** Tracking depends on the same retrieval infrastructure as Ask, and there's no point standing up a second consumer of the RAG index before the first one is in production. Don't start building until `ask.html` is live, the Worker is stable, and the incremental cron rebuild is wired.

  **Biggest unresolved design question (decide before building):** maintenance cadence. First-publish is easy; the hard part is week 3 when there are 5 active Tracking pages and 2 of them have new developments. Two options: (a) manual trigger — user decides "refresh the Toledo page today" and runs a regenerator; (b) weekly cron pass that runs "what's new since last update?" against the RAG corpus + a fresh research-agent sweep on each active topic, then surfaces a draft diff via Telegram for human review. (b) is what makes the section feel alive rather than 5 abandoned pages, but it's a bigger build. Pick before writing the generator.

  **Pilot topic:** Karla Toledo's ICE detention (2026-05-19), if it's still developing when Tracking is ready to build. Small enough to be tractable, big enough to test the multi-source / research-agent assembly. Alternative candidate: the Pima County Sheriff Nanos investigation report saga (perjury referral + the May 26 release-the-report vote), which spans multiple meetings already in the corpus.

### Coverage area

The Tucson metro area broadly: City of Tucson, Pima County, Town of Marana, Town of Oro Valley, and their respective governing bodies, commissions, and public records. Not limited to Tucson city limits.

### Editorial model

- **Agenda previews** (forward-looking "What to Watch") publish automatically with no human review. They summarize what's on the agenda — low risk, high value in timeliness.
- **Post-meeting reporting and all other original journalism** is human-reviewed before publishing — no exceptions. AI drafts and flags; a human reviews, edits, and approves.
- Each piece carries a clear disclosure about AI involvement.

### Site structure

The homepage at `/` is now a **zoned entry hall** (featured Today's Brief + cross-stream cards + Tools row [gated] + subscribe panel + last 7 daily briefs). Direction B from `REDESIGN.md`. The full daily-brief archive lives at `/briefings.html`. Every section page uses a shared two-row nav: streams on top (terracotta), tools below (sage, hidden behind `SHOW_TOOLS` flag).

- **Daily Brief** (`/`, `/briefings.html`, `posts/`) — daily news synthesis from local sources (live). Homepage features today's brief prominently; full archive at `/briefings.html`
- **Meeting Watch** (`meeting-watch.html`, `meeting-watch/`) — AI-generated agenda previews for 4 municipalities (live, auto-published)
- **News Reports** (`news-reports.html`, `news-reports/`) — AI-drafted, human-reviewed post-meeting news reports (pipeline built, first real recordings scheduled April 7, 2026)
- **Spotted** (`public-record.html`, `public-record/`) — flagged filings surfaced from agendas; v1 covers liquor license applications across Pima County BOS, City of Tucson, Oro Valley (live as of April 11, 2026). Display name changed from "Public Record" to "Spotted" on 2026-05-11; URL preserved
- **Ask** (`ask.html`) — RAG-powered Q&A surface. Phase 1 (CLI) + Phase 2 (web UI on Fly.io, app `tdb-ask`) both live as of 2026-06-14. **Now publicly linked in the main streams nav site-wide as of 2026-06-23** (promoted out of the `SHOW_TOOLS`-gated Tools row into `_STREAMS`); the shakedown period is effectively over for the nav link
- **Tucson Responsiveness Index** (`responsiveness.html`) — stub page for the upcoming dashboard. Planning in `responsiveness/PLANNING.md`; no code yet
- **The Tucson Mini** (`crossword/`) — weekly Tucson-themed 5×5 mini crossword; subscriber perk for the TDB Weekly newsletter; unlisted (noindex, no public links) (v0.4 live as of May 6, 2026; see "The Tucson Mini" section below)
- **The Old Pueblo Speaks** — future outreach-based reporting section (see Roadmap above); not yet building
- **Deep Read** — AI-assisted analysis of large documents (planned)
- **About** (`about.html`) — hand-authored editorial page explaining the project (live as of 2026-05-15). Framed around the "tool-assisted speedrun" metaphor: software handles the scale, a working journalist handles the judgment. Linked from the footer on every page. Hand-edit only — NOT generated by any pipeline. Layout note: uses the standard `article.post-page` treatment (terracotta-underlined h1, auto-upgraded bold lede paragraph) but inside a plain `.container` (full width, 1280px) with an inline `max-width: 680px` on the article itself, so the reading column sits flush-left with the masthead's left edge instead of jumping inward to a centered island like `container--reading` would.

### Story ideas

- **"The Accessibility of Public Data in Southern Arizona"** — An investigative deep dive comparing how four municipalities in the same metro area handle public access to government meeting data. Pima County offers a free, unauthenticated REST API (Legistar); Marana has scrapeable HTML pages (Destiny Hosted); Oro Valley pays for proprietary Granicus software with no public API; Tucson (the largest city) locks agendas in PDFs via Hyland OnBase. All of this is taxpayer-funded public record, yet accessibility varies wildly based on vendor choices most residents don't know were made. Could include public records requests for contract amounts to show what each municipality pays for its system.

- **"Tucson's Crime, in the FBI's Database vs. Tucson's Own"** — Two-part story arc developed from research on 2026-05-19. Full notes in `crime.md` and `crime-tpd-data.md`.
  - **Part one (the federal hole):** Per the FBI's own agency metadata for TPD (ORI AZ0100300), TPD's NIBRS reporting start date is January 1, 2024 — three years after the FBI's hard cutover. TPD's data didn't flow to the FBI for all of 2021, most of 2022, and most of 2023. Downstream aggregators like Crime Explorer (crimeexplorer.com) present that as "0 violent crimes 2019–2024" with internally broken rate math ("97% below national average" — actual Tucson property crime is *above* the national average). A statistician's analysis named Tucson as the only US agency over 250K population that failed to report to the FBI in 2022. Historical precedent: TPD also fell out of the FBI report in 2014 (TPD→AZ DPS→FBI handoff failure) and the FBI left Tucson's property categories blank from 2006–2012 — this is a pattern, not a one-time NIBRS transition.
  - **Part two (TPD's own numbers):** TPD's PowerBI dashboard shows 54 homicides in 2025, down 22% from 69 in 2024 and below the 2021 peak of 78. Metro-wide (TPD + PCSD + Marana + Oro Valley + Sahuarita) = 62 homicides in 2025, lowest in seven years. 2024 FBI peer comparison: Tucson sits at 589 violent / 3,313 property per 100K, higher than Mesa and El Paso, lower than Fresno/Sacramento/Albuquerque. **The reportable methodology bombshell:** TPD's 2024 city report claims a 97.56% homicide "resolution rate" while the FBI-format clearance it submits to AZ DPS shows 57.45% for the same year — both numbers are accurate but measure different things, and no source explains the gap.
  - **Three unlocks needed before publishing** (documented at the top of `crime-tpd-data.md`): a browser session capturing the live PowerBI dashboard at policeanalysis.tucsonaz.gov (renders client-side, can't be scraped), a human download of the 2024 TPD Annual Report PDF (city asset server 403s non-browser clients), and a public-records request for the methodology behind the 97.56% figure.

### Constraints

The hardest part is sourcing data, not the AI pipeline. Start with what Tucson/Pima County already publishes in machine-readable formats. Some data requires FOIA/public records requests or lives in terrible PDFs and legacy systems.

## The Tucson Mini (Weekly Subscriber Crossword)

Weekly Tucson-themed 5×5 mini crossword. Subscriber perk for the forthcoming TDB Weekly newsletter (see "TDB Weekly Newsletter" section below). Adapted from the upstream "Crosswording the Situation" project at `~/claude-code-projects/crossword-puzzle` — same scaffolding (grid generator, Claude API plumbing, validation, JS engine, mobile UX), retuned for a weekly local audience.

### Differentiator from CtS

CtS is **news-first**: every clue must tie to a real news story. The Tucson Mini is **Tucson-vocabulary-first**: the puzzle's identity is local flavor (saguaros, monsoons, U of A, Sonoran food, Tucson place names), with past-week TDB stories as a small accent rather than the spine. This was a deliberate editorial decision the user articulated explicitly during the May 6 build: "Tucson is a small city; not much news happens. Don't twist ourselves into knots trying to match news events to the puzzle."

### Editorial posture (encoded in the LLM prompt)

- **NORTH STAR**: Tucson vocabulary leads. Wordbank entries surface first; news is reached for only when natural (typically 1-3 of 10 clues).
- **HARD RULE — DO NOT INVENT TUCSON REFERENCES**: prompt enforced, with concrete examples of past failures ("a common Tucson dog-park name" — invented). Every Tucson reference must come from the wordbank `context`, the thematic_lexicon, or the past-week TDB stories.
- **HARD RULE — DO NOT INVENT FACTS, EVER**: applies to all clues. Real fabrications caught and prompt-fixed: "the Colorado River was named for a biblical patriarch" (false — Spanish for 'colored red'), "EDEMA, a concern in Tucson's dry summer heat" (medically wrong). When in doubt, write a simple definition or wordplay clue.
- **Soft-hedging on uncertain news items**: filings/agendas/proposed openings must use "planned," "proposed," "listed" — never assert as fact.
- **Tucson and southern Arizona only — no Phoenix-area landmarks.** This is an explicit user constraint.

### Pipeline

```
Past 7 days of TDB posts (read_tdb_posts.py)
    ↓
Tucson wordbank + thematic lexicon (wordbank-tucson.json)
    ↓
Filtered wordlist (STWL → Zipf ≥ 2.5 → filter_wordlist.py → wordlist.json)
    ↓
Grid generation (generate_grid.py: backtracking with wordbank preference)
    ↓
Clue generation (generate_puzzle.py: Sonnet 4.6, prompt with wordbank context first)
    ↓
Validate + cross-clue dedup pass
    ↓
Output: puzzles/YYYY-MM-DD-XXXXXX.json with unguessable hex slug
```

### Word filtering: frequency floor + blocklist + wordbank whitelist

The grid solver pulls from STWL (12.7K words, 3-5 letters, score 50+). Three filters layered on top:

1. **Frequency floor (Zipf ≥ 2.5)** — built once via `filter_wordlist.py`, output committed as `wordlist.json`. Auto-excludes obscure fill (UGALI 1.43, BOPIT 0, AROAR 0, RAGAS 1.86, SAGET 2.24, SESH 2.45) without hand-tagging. Tunable.
2. **Editorial blocklist** (`wordlist-blocklist.json`) — small hand-maintained list for words that pass the frequency filter but still feel wrong (currently includes BRET, ESSO, AAMCO).
3. **Wordbank whitelist** (`wordbank-tucson.json`) — Tucson-specific words always pass through, even if their Zipf is low (NOPAL 1.67, ELOTE 1.40, MARANA 1.97). Without the whitelist, half the local vocabulary would be filtered.

`wordfreq` is a Python library used at *build time* only, not at runtime. Install in `.venv` if regenerating:
```
.venv/bin/pip install wordfreq
.venv/bin/python3 crossword/tools/filter_wordlist.py
```

Re-run after editing the wordbank or blocklist, then commit the new `wordlist.json`.

### Wordbank as the editorial north star

`wordbank-tucson.json` holds 163 curated 3-5 letter Tucson/southern Arizona answers plus a 45-term thematic lexicon (longer words like SAGUARO, MONSOON, JAVELINA biased into clue *text* rather than answers). Each entry has:

- `tucson_strength` (high/medium/low) — how unmistakably Tucson it is
- `clue_styles` — sample warm clue angles
- `context` — the *why* (used by the LLM for evidenced clues)

The grid generator biases toward wordbank entries via `preferred_words` in `solve_grid()`. Currently only ACROSS slots are biased; DOWN slots emerge from intersections. Typical run: 3-5 of 10 answers come from the wordbank.

### URLs and unlisted publishing

Each puzzle gets an unguessable hex slug: `puzzles/YYYY-MM-DD-XXXXXX.json`. The play page reads `?p={slug}` from the URL:

- `tucsondailybrief.com/crossword/play.html?p=2026-05-10-49c6f1` — solvable puzzle
- `tucsondailybrief.com/crossword/play.html` — empty state ("no puzzle, you'll find the link in the newsletter")

`play.html` has `<meta name="robots" content="noindex,nofollow">`. No public link to the crossword from anywhere on the site. Subscribers get URLs only via the newsletter.

### Running it

```
.venv/bin/python3 crossword/tools/generate_puzzle.py [YYYY-MM-DD]
.venv/bin/python3 crossword/tools/generate_puzzle.py --force  # re-run for the same date
```

Outputs to `crossword/puzzles/{date}-{6char}.json` plus updates `.latest.txt` (gitignored, build-state pointer for the newsletter generator).

### Cost

~$0.02-0.03 per puzzle (Sonnet 4.6, two API calls: clue generation + dedup-references check). Negligible at weekly cadence.

### Deferred work (as of 2026-05-06)

- **Cron wiring** — currently manual. Once the newsletter generator exists, both should run Saturday afternoon so Sunday's email has a fresh puzzle.
- **DOWN-slot bias** — only ACROSS is preferred toward the wordbank; DOWN words emerge from intersections.
- **Newsletter integration** — the newsletter draft generator should read `crossword/puzzles/.latest.txt` and embed the play URL.
- **More wordbank growth** — 163 entries is enough for years of weekly puzzles, but additions are welcome. Phoenix-area references explicitly excluded.

## TDB Weekly Newsletter

Weekly editorial newsletter delivered via Buttondown. Reader-facing promise: "Feel more caught up on Tucson every Sunday." Generated from the past 7 days of TDB content (daily briefs + news reports + public-record filings + upcoming meeting previews) by Claude Sonnet 4.6, written as a markdown draft, **human-reviewed before sending**.

**Status:** Full pipeline live as of 2026-05-08. Cron generates a draft every Friday at 6pm MST and uploads it to Buttondown. The user does an editorial pass over the weekend and manually clicks "Schedule send" in Buttondown for Sunday 5am MST. First real issue scheduled to send 2026-05-10.

**Name:** TDB Weekly. Boring on purpose — initialism-forward, instantly legible, doesn't lock the day. (Working name "Sunday in Tucson" was rejected 2026-05-07; the user's gut was that boring + initialism-forward branding fits the product better.)

### Strategic logic

A daily site is great for the people who already know about TDB, but it's a terrible discovery surface — daily readers are a tiny minority of any audience. Layering a weekly curation on top of the daily firehose is how regional outlets actually grow (Axios Local, most successful local newsletters). Cost is essentially zero: a Sonnet pass over the previous seven days is ~$0.07/run, and the existing TTS pipeline (ElevenLabs or Voxtral) handles the audio version when we get there with no new infrastructure.

### Format (encoded in the prompt)

~800–1200 words, structured warm-not-civic. No H1 title — the email subject line is the title. The body opens directly with the warm paragraph.

- **Warm opening** (no heading) — 2-4 sentences setting the mood, often referencing weather/season
- **## What's worth knowing** — 3-4 most important Tucson-area stories of the week, narrative paragraphs, not a list
- **## What changed around town** — local government decisions, neighborhood changes, development items
- **## What's opening** — new businesses across food/drink/retail/fitness; liquor filings are ONE input among several
- **## One thing to watch** — specific upcoming meeting or event in the next ~2 weeks
- **## The Tucson Mini** — single short paragraph + crossword link
- **Closing note** (no heading) — ~2 sentences, warm beat

### Editorial voice

Warm, friendly, kitchen-table-Sunday-morning. NOT civic-tech or insider — the reader doesn't see the AI pipelines, the agenda mining, the public-records work behind it. Different voice from the daily brief: the daily is fast and headline-y; the weekly is slower, more opinionated, more story-shaped.

The same Sonnet pass that picks the week's best stories also rewrites them in newsletter voice. Not a digest of headlines.

The prompt explicitly bans civic-tech phrasings ("public records," "agenda mining," "local intelligence," "monitoring the situation," "our review," "flagged by," "surfaced from," "according to filings") because the model leaks them by default in v1. Concrete banned-phrase examples in the prompt land better than abstract rules.

### Recency-claim guardrail

Encoded in the prompt: a business is only "newly opened" if the source content has an explicit recent date ("opened April 24," "grand opening Saturday"). News *coverage* of a business this week is not the same as the business *opening* this week — many places get their first press long after they open. Default to attribution-style hedging: "Bloom Tea Wellness was profiled in Inside Tucson Business this week." Reserve "newly opened" / "just opened" for items with an explicit date.

This was identified during the first draft review on 2026-05-07. Bloom Tea actually opened in January, but the May 3 daily brief said "Bloom Tea Wellness has opened in Oro Valley" because of an Inside Tucson Business profile, and the model dutifully repeated it. The newsletter-layer fix is defensive; the long-term fix is upstream — tighten `TUCSON-BRIEF.md` to require explicit dates for any "X has opened" claim. Deferred until we have more weeks of data on how often this recurs.

### Pipeline

Three components chain together via `run_newsletter.sh`:

**1. `generate_newsletter.py` — markdown draft from past-week content**

1. Calculates send date (next Sunday by default; overridable via `--send-date`).
2. Scans the past 7 days of `posts/`, `news-reports/`, `public-record/` (mtime-based for the last) and the next 14 days of `meeting-watch/`.
3. Strips HTML chrome (head/script/header/footer/nav) and tags from each file before passing to the model.
4. Picks the puzzle for the send date from `crossword/puzzles/` (exact-date match, else earliest puzzle dated after) and embeds `https://tucsondailybrief.com/crossword/play.html?p={slug}` in the prompt.
5. Sends ~17K tokens of context to Sonnet 4.6 with the editorial prompt (voice rules, format spec, recency guardrail, hard rules).
6. Writes the draft to `newsletter/drafts/tdb-weekly-YYYY-MM-DD.md` (gitignored — drafts are working state).

Cost: ~$0.07/run. Output: ~950 words drafted directly in markdown.

**2. `upload_to_buttondown.py` — push draft to Buttondown via API**

1. Strips the `*Draft generated...*` metadata header that the generator prepends.
2. Derives a subject line from the filename (e.g., `TDB Weekly — May 10, 2026`); overridable via `--subject`.
3. POSTs to `https://api.buttondown.email/v1/emails` with `status: "draft"`, `email_type: "public"`. Buttondown stores the markdown natively; no HTML conversion needed.
4. Prints the edit URL (`https://buttondown.com/tucsondailybrief/archive/<slug>/`) so the user can open and edit.

Auth: `BUTTONDOWN_API_KEY` from `~/.config/environment.d/buttondown.conf`.

**3. `run_newsletter.sh` — cron wrapper**

Loads env vars from `~/.config/environment.d/`, runs the generator with `--force`, finds the latest draft, and uploads it. Logs to `/tmp/newsletter-gen.log`. Single `--dry-run` flag for manual testing.

**Cron entry:**
```
0 18 * * 5 ~/claude-code-projects/tucson-daily-brief-site/run_newsletter.sh >> /tmp/newsletter-gen.log 2>&1
```

(Friday 6pm MST. The draft sits in Buttondown for ~36 hours of human editorial review; user manually schedules the send for Sunday 5am MST after editing.)

Usage:

```bash
.venv/bin/python3 generate_newsletter.py                  # generate draft only
.venv/bin/python3 generate_newsletter.py --dry-run        # print prompt, no API call
.venv/bin/python3 upload_to_buttondown.py <draft.md>      # upload existing draft
./run_newsletter.sh                                        # full chain (cron uses this)
./run_newsletter.sh --dry-run                              # full chain dry run
```

### Critical principle: do not duplicate the website

The newsletter must not be a copy of the daily site. If both surfaces show the same content, neither has a reason to exist.

- **Website** = daily archive, canonical source, searchable, linkable, comprehensive.
- **Newsletter** = weekly editorial product. Opinionated, curated, written *to* a specific person reading at the kitchen table on Sunday morning. Different voice, different selection logic, different value proposition.

### Platform: Buttondown (decided 2026-05-06, wired 2026-05-08)

Originally planned around Substack for the recommendation flywheel. Pivoted to **Buttondown**:

- **Real REST API.** Buttondown supports creating drafts, scheduling sends, and managing subscribers via API. Substack has no posting API (read-only stats; unofficial reverse-engineered libraries are fragile and unsafe for cron).
- **Markdown-native.** Buttondown stores posts as markdown, which fits the rest of the TDB pipeline naturally. No "render to HTML and paste manually" workflow.
- **No revenue cut.** Substack takes 10% on paid subscriptions; Buttondown is flat-fee SaaS.
- **Single-developer-friendly.** Buttondown is tooling, not a media platform.

**The trade-off:** Substack's recommendation engine is a real distribution channel for independent writers. Buttondown gives that up — TDB would build distribution itself through word-of-mouth, the Tucson Mini referral hook, and partnerships with existing Tucson outlets. Acceptable for build velocity and editorial control on a single-developer side project.

### Sender architecture

- **From:** `Nicholas De Leon <tdb@mail.tucsondailybrief.com>` (subdomain).
- **Reply-To:** Buttondown-managed (`replies+UUID@replies.buttondown.email`). Replies land as wrapped notifications in user's Gmail; user replies back as themselves. The "view replies in Buttondown dashboard" feature is preserved.
- **DNS for `mail.tucsondailybrief.com`:** delegated to Buttondown's nameservers (`ns1.onbuttondown.com`, `ns2.onbuttondown.com`) via 2 NS records on the apex. Buttondown manages all DKIM/SPF/MX/DMARC at the subdomain in perpetuity — no manual record management.
- **DNS for apex (`tucsondailybrief.com`):** still owned by user. Cloudflare Email Routing forwards `tdb@tucsondailybrief.com` → `nicholas@daylayown.org`. Used for direct emails to the apex address (website inquiries, business contacts) — not load-bearing for newsletter replies anymore but keeps the apex address functional.

**Why the subdomain split:** Cloudflare Email Routing takes exclusive ownership of MX records at the apex by design. Postmark (Buttondown's underlying ESP) wanted an MX too. Couldn't coexist. Subdomain delegation cleanly avoids the conflict.

**Account:** username `tucsondailybrief`, login `nicholas@daylayown.org`. API key in `~/.config/environment.d/buttondown.conf`.

### Tucson Mini as the subscriber perk + funnel

The Mini (see section above) is the subscriber-exclusive perk and the growth hook. Architecture:

- Each weekly newsletter contains a fresh Tucson Mini link.
- The play page is unlisted (noindex, no public links) — subscribers get the URL only via the newsletter.
- Static play page on the TDB site, JSON puzzle data behind unguessable slugs.
- The newsletter generator reads from `crossword/puzzles/` and auto-embeds the play URL for the send date.

NYT Mini is the dominant retention pattern for newsletters with games. The Tucson Mini is the local version: 5×5, charming, takes 1-3 minutes, has a forwardable share grid.

### Site signup form

Subscribe form lives on `tucsondailybrief.com` between the section nav and the daily-brief post list. Rendered by `render_index()` in `generate_post.py` (so it survives every nightly homepage rebuild) and styled in `style.css` under `.subscribe-cta` (tan panel, terracotta CTA button, brown text — matches the desert palette).

Form posts directly to Buttondown's embed endpoint:

```
POST https://buttondown.email/api/emails/embed-subscribe/tucsondailybrief
```

`target="_blank"` opens Buttondown's confirmation flow in a new tab so the user stays on tucsondailybrief.com. Buttondown handles double opt-in, the success page, and the welcome email.

For now the form is homepage-only. Adding to other index pages (`meeting-watch.html`, `news-reports.html`, `public-record.html`) and individual posts is straightforward but deferred until conversion data warrants it.

### Audio version (deferred)

Reuse the existing TTS pipeline (`generate_podcast.py` flow). Weekly episode is just a different input text — clean for TTS, send to ElevenLabs or Voxtral, upload to R2 or Buttondown's native podcast hosting. Add this once the written newsletter is stable.

### Build order (updated 2026-05-08)

1. Public Record liquor license pipeline ✅ live (2026-04-11)
2. Tucson Mini crossword ✅ live (2026-05-06, v0.4)
3. **TDB Weekly newsletter ✅ LIVE (2026-05-08)**
   - Draft generator ✅ built 2026-05-07 (v4 prompt)
   - Buttondown API integration ✅ built 2026-05-08
   - Cron + wrapper ✅ built 2026-05-08 (Friday 6pm MST)
   - Site signup form ✅ shipped 2026-05-08 (homepage, posts to Buttondown embed endpoint)
   - First real send: Sunday 2026-05-10 (manually scheduled in Buttondown)
4. Marana coverage in Public Record — pending
5. Audio version of newsletter — after written newsletter is stable

## RAG Knowledge Agent

A retrieval-augmented chat agent that answers questions about Tucson using only the TDB corpus, with inline citations to source URLs. Differentiates TDB from every other local outlet — most of which can't have a meaningful conversation about their own archive. The corpus IS the moat; making it queryable is what turns it into a product.

**Status:** Phase 1 (CLI) live since 2026-05-09 (`a1d0149`). **Phase 2 backend + Ask UI shipped 2026-06-14** (`8387bd7`) — the RAG agent is deployed to Fly.io at `https://tdb-ask.fly.dev` and `ask.html` is a working Q&A interface, currently gated behind `SHOW_TOOLS=False` for an unlisted shakedown. See "Phase 2 — public web UI" below for what shipped; the daily index-refresh cron is now wired too, so what's left before launch is the shakedown pass, then flip `SHOW_TOOLS`.

### Files

- `rag/build_index.py` — walks corpus, document-type-aware chunking, embeds via Voyage, writes to sqlite-vec.
- `rag/ask.py` — CLI: question → top-K retrieval → Claude Sonnet 4.6 synthesis with citation discipline → printed answer + numbered source list.
- `rag/index.sqlite` — vector store (gitignored).
- `requirements.txt` — adds `voyageai`, `sqlite-vec`, `anthropic`.

### Architecture

- **Embeddings:** Voyage `voyage-3-lite` (512-dim, $0.02/1M tokens, Anthropic-acquired Voyage AI is the recommended pairing for Claude RAG). API key in `~/.config/environment.d/voyage.conf`.
- **Vector store:** SQLite + `sqlite-vec` v0.1.9 extension. Single file at `rag/index.sqlite`. No server, no hosted service.
- **Generation:** Claude Sonnet 4.6 with strict "answer only from these sources" system prompt; refuses to fabricate, suggests where to look when corpus doesn't cover the question.
- **Chunking:** document-type-aware. Daily brief → one chunk per story. News report → title+lede + per-`<h2>` sections. Meeting preview → per top-item. Public-record filing → whole filing. Agenda full reference → 1500-char windows with 200-char overlap.
- **Idempotency:** content hash per file in `file_state` table — re-running re-embeds only changed/new files (verified — incremental rebuild after a new daily brief takes ~0.5s).
- **Citation URLs:** every chunk carries the public TDB URL it came from; `agenda-watch/*-full.md` references map to the corresponding `meeting-watch/{slug}.html` published preview when one exists, else fall back to the meeting-watch index page.

### Index stats (as of 2026-05-10)

147 files, 1,464 chunks. Distribution: 1,105 daily-brief chunks, 207 agenda-full, 121 meeting-watch, 18 public-record, 13 news-report. Initial embed: ~262K tokens, well under Voyage's 200M-token free tier.

### Cost

- Embedding: ~$0.005 to embed entire corpus once. Daily incremental: pennies/day.
- **Per query at runtime:** ~$0.015 (Sonnet 4.6 with retrieved chunks). Hand-tests range $0.011–$0.020 depending on output length.
- 100 queries/day ≈ $1.50/day, $45/month. Realistic shakedown volume is pennies/month.

### Known gotchas (caught during build, must remember)

1. **sqlite-vec KNN syntax:** use `WHERE embedding MATCH ? AND k = ?` inside the WHERE clause, NOT a regular SQL `LIMIT`. Plain `LIMIT` raises `OperationalError: A LIMIT or 'k = ?' constraint is required on vec0 knn queries`.
2. **Voyage `input_type`:** use `"document"` when embedding for the index, `"query"` when embedding the user's question. They're tuned differently.
3. **Vector serialization:** sqlite-vec accepts `sqlite_vec.serialize_float32(vec)` for storage. Do not pass Python lists directly.
4. **Boolean params on SDKs:** Voyage 0.2.x is fine, but the Deepgram pattern of "pass booleans as strings" is a precedent worth remembering when integrating other vector/SDK libraries.

### Usage

```bash
.venv/bin/python3 rag/build_index.py              # incremental — only re-embeds changed files
.venv/bin/python3 rag/build_index.py --rebuild    # drop everything and re-embed all
.venv/bin/python3 rag/build_index.py --dry-run    # walk + chunk only, no API calls

.venv/bin/python3 rag/ask.py "your question here"
.venv/bin/python3 rag/ask.py --k 15 "..."         # retrieve more chunks
.venv/bin/python3 rag/ask.py --json "..."         # machine-readable output
```

### Phase 2 — public web UI (next, ~2-3 days of focused work)

The chat agent ships publicly as the **launch event** of the project's marketing push. Status of the plan (✅ = shipped 2026-06-14, `8387bd7`):

1. ✅ **`ask.html` rebuilt** — was a coming-soon stub; now a working Q&A interface (vanilla JS, scoped `<style>` on the locked desert palette): question box + example-question chips + answer card + citation list. The answer's `[N]` markers render as links that jump to the numbered source list; each source links out to its TDB page. Carries a beta disclaimer. POSTs to the Fly service (no Cloudflare Worker — that plan was dropped, see hosting decision below). **Still gated behind `SHOW_TOOLS=False`** — do NOT flip until shakedown is clean.
2. ✅ **Fly.io service** (`rag/server.py`) — FastAPI wrapper around the existing `ask()` function. Holds Voyage + Anthropic keys as Fly secrets (`fly secrets set`, reused from `environment.d`). `POST /ask` → `{question, k?}` → `{answer, sources}`; `GET /health` for the Fly health check. App name **`tdb-ask`**, deployed via `fly deploy --remote-only`; the prebuilt `index.sqlite` is **baked into the image** (`Dockerfile` copies it in — service is read-only at runtime, no volume). `fly.toml`: `shared-cpu-1x`/512mb, scale-to-zero (`min_machines_running = 0`), HTTPS forced. Image ~107MB.
3. ✅ **Per-IP rate limiting** in the FastAPI app — in-process sliding window, 20 req/hour (env-tunable via `RATE_LIMIT_*`). CORS locked to `tucsondailybrief.com` (+ localhost for dev); other origins blocked. Input validation: question 1–500 chars, `k` clamped 1–20.
4. ⏳ **Unlisted shakedown (~1 week)** — in progress. `ask.html` is pushed but unlinked (`SHOW_TOOLS=False`, not in any nav/sitemap), so it's effectively unlisted. After clean shakedown: flip `SHOW_TOOLS=True` in `generate_post.py` (surfaces Ask + Responsiveness in the homepage Tools row and Tools nav site-wide), then public launch (r/Tucson + LinkedIn + local press).
5. ✅ **Cron the index refresh — DONE 2026-06-14.** `refresh_ask_index.sh` rebuilds the index (`build_index.py`) then `fly deploy --remote-only --app tdb-ask` to reship it, since the baked `index.sqlite` otherwise freezes live answers at deploy-time. Runs daily at **8:45 AM MST** (cron, after `check_agendas.sh` at 8:00 so both the morning brief and freshly mined agendas/filings are indexed) → `/tmp/ask-index-refresh.log`. Non-interactive deploy auth uses a **scoped Fly deploy token** in `~/.config/environment.d/fly.conf` (`FLY_API_TOKEN`, created via `fly tokens create deploy -a tdb-ask`, 1-yr expiry — regenerate before it lapses). The script sources `environment.d/*.conf` (Voyage key + Fly token) like the other cron wrappers. Skips the deploy if the rebuild fails. Future optimization: a Fly volume + pushing just the `.sqlite` instead of a full image rebuild each day; current daily redeploy is cheap (~107MB image) and fine at this scale.

**Local dev / redeploy quickref:**
```bash
# Test the server locally against the real index (from rag/):
../.venv/bin/uvicorn server:app --reload --port 8080
# Refresh the deployed index after new content lands:
.venv/bin/python3 rag/build_index.py && fly deploy --remote-only --app tdb-ask
# Logs / status:
fly logs --app tdb-ask ; fly status --app tdb-ask
```
Note: `fastapi` + `uvicorn[standard]` are in both the repo-root `requirements.txt` (laptop `.venv`) and `rag/requirements-server.txt` (the lean Fly image).

**Shakedown + date-awareness fix (2026-06-14):** A 13-question adversarial pass found grounding strong — clean refusals on out-of-corpus questions (Phoenix mayor, Wildcats football) and false premises (a fictional streetcar derailment, a made-up Romero car-ban plan), a corrected loaded premise on the Nanos "corruption charges" question, and a gracefully-declined prompt injection. The one real failure: no sense of "now" — it served a months-old weather brief as "tomorrow's forecast." **Fixed** by injecting the current Tucson date (`America/Phoenix`, no DST) plus a real-time/staleness instruction into the system prompt at request time (`current_date_note()` in `ask.py`, appended to `SYSTEM_PROMPT`). Verified: the weather question now flags its newest source as stale and points to NWS, "this week" questions lead with the most recent source and admit gaps, and well-covered topics still answer confidently. **Two structural follow-ups deliberately deferred** (discuss before building): (a) exclude ephemeral weather sections from the index — they only generate stale-data traps; (b) recency weighting in retrieval (Phase 3) — retrieval still surfaces mostly older chunks for "latest/this week" questions, so the prompt fix makes the model degrade honestly but doesn't fix ranking. **Also flagged for pre-launch:** the in-process per-IP rate limit resets on every deploy and is per-machine (2 machines) — soft against real abuse; revisit before flipping `SHOW_TOOLS`.

**Phase 2 hosting decision (2026-05-25): Fly.io with local SQLite (option C from the original evaluation).** One small Python service wraps `ask.py`; the `index.sqlite` file ships with the deploy. Reasons: zero rewrite of existing `build_index.py` / `ask.py` code; one system to maintain (vs. Worker + VPS); avoids re-implementing the chunk store in Cloudflare Vectorize for a problem (scale, edge latency) TDB doesn't have at expected traffic. Rate limiting lives in the FastAPI app (per-IP bucket, ~20 lines) instead of at the Worker edge. Replaces the earlier Cloudflare Worker plan throughout this section — `ask.html` will POST to the Fly.io app directly, no Worker hop. This is also **Stage 1 of the broader "Move TDB off the laptop" roadmap** (see section below) — chosen as the low-stakes first migration to prove out the cloud-deploy workflow before tackling the heavier cron + live-recording migration.

### Phase 3+ (eval-driven, defer until Phase 2 has run for a few weeks)

- **Eval set** — 30–50 hand-graded real Tucson questions, automated regression-tested on every change. Build before any of the items below; without it, "improvements" are guesses.
- **Hybrid search** — BM25 + vector, then rerank top-30 → top-10 via Voyage Rerank or Cohere Rerank. Highest-leverage quality lever in most RAG systems.
- **Recency weighting** — explicit time-decay scoring if Sonnet isn't picking up "what's happening lately" framing from prompt instructions alone.
- **Agentic multi-hop retrieval** — for cross-document questions ("Who funded the council member who voted yes on Bloom Tea's liquor license?"). Let the model issue multiple retrieval queries iteratively.
- **Operational RAG extension** — once the Responsiveness Index ships, extend the agent to query its live SQLite store alongside the text corpus (covered in detail in `responsiveness/PLANNING.md` under "Function 3 — Access").

## Tucson Responsiveness Index (planned, researched 2026-05-10)

Side project that evolves TDB from aggregation toward original reporting. A living dashboard at `tucsondailybrief.com/responsiveness.html` (currently a coming-soon stub with a sample 3-card preview) that reframes Tucson's civic infrastructure through three lenses no one else combines: how the city responds to resident-reported problems, what the city publishes vs. what it doesn't, and how the desert (heat / water / power) makes both questions structurally different than they'd be in any other US metro.

**Status:** Research complete (M0). Coming-soon stub live at `responsiveness.html` (not yet linked from main nav — gated behind `SHOW_TOOLS=False`). Not yet building the real dashboard. With RAG agent Phase 2 now shipped (2026-06-14), this is the main remaining queued next-build candidate.

**Canonical planning doc:** `responsiveness/PLANNING.md` — covers the full thesis, four publishable surfaces (live dashboard, weekly explainer, Transparency Tracker, original journalism using accumulated data), the four AI functions (Discovery, Synthesis, Access, Translation) with specific applications under each, build sequence (M1 → M3 → beyond), data source URLs and gotchas, codebase reuse plan, and open decisions.

**M1 scope (locked):** SeeClickFix 311 + TPD CFS only. No Equity Score in v1 (politically charged, dropped 2026-05-10). Three deliverables ship together: Transparency Tracker page, 311 dashboard with citywide numbers, "How this works" methodology page.

**The editorial thesis from research:** *"Before we measure how fast Tucson responds, we have to measure what Tucson tells us."* Tucson does not publish 311 on its own open-data portal, does not publish code enforcement at all, does not publish permits in bulk, and Tucson Water publishes no operational KPI report (a peer utility — Oro Valley Water — does). The Transparency Tracker leads; responsiveness numbers follow; the desert lens is permanent.

When picking this up cold: read `responsiveness/PLANNING.md` and the `project_responsiveness_index.md` memory entry. Both are durable — the data sources, gotchas, and architecture decisions don't expire fast.

## Roadmap: Coverage Expansion (Sahuarita, school districts, Vail) + first original feature

Researched and verified 2026-06-18 (feasibility scans). **Full reference: `COVERAGE-EXPANSION.md`.** **Gate:** nothing starts until the in-flight work (TEP poller, dashboard auto-refresh, Instagram build) is settled. Priority order: **Flock article → Sahuarita → school districts.**

- **Sahuarita Town Council — the clean "fifth municipality."** Only incorporated town in the SE corridor (Vail, Green Valley, Corona de Tucson are all unincorporated → no councils; Vail rejected incorporation in 2023). Agendas on **eScribe** (`pub-sahuarita.escribemeetings.com`, new portal vendor but Marana/OV-shaped scrape) + **YouTube** livestream (reuses existing transcription path). Lift: moderate, one new scraper + a `STREAM_SOURCES` entry.

- **School-district board coverage — the sleeper expansion (new content line).** Under-covered, high-stakes. The whole metro consolidates onto **two agenda platforms**: one **Diligent Community** scraper covers TUSD + Vail + Sahuarita + Tanque Verde (~63K students, incl. the two biggest); one **BoardBook** scraper covers Amphitheater + Marana + Catalina Foothills + Flowing Wells (~31K); +NovusAGENDA for Sunnyside. Two scrapers ≈ 8 of 9 major districts — *lower* lift than the municipal pipeline. **Pilot: Vail USD** (Diligent + YouTube, ties to the Vail Chamber relationship). Note: "Oro Valley schools" = Amphitheater district; there is no standalone OV district. Extend `pipeline/local_names.json` with board members + superintendents.

- **Vail itself is not a municipal add** — no town government. Its civic surface is (a) Pima County BOS District 4, *already* in the pipeline (editorial tagging only), and (b) the Vail School District (above). Fire districts (no video) are lowest priority.

- **First original-journalism feature: "Southern Arizona Debated Flock Cameras"** (write-ready brief in `COVERAGE-EXPANSION.md` Part 2). Non-advocacy, human-reviewed, anchored in TDB's own meeting transcripts with external reporting layered underneath. **Framing landmine:** Tucson/TPD uses Verkada, NOT Flock — the "Tucson Flock" debate is the separate City of South Tucson, which cancelled its contract Feb 17 2026. The regional spine: South Tucson pulls back while Oro Valley (drones) and U of A (62 cams, $870K) expand, against no AZ ALPR law + SB 1070 non-sanctuary posture. Best accountability thread: UA PD said it doesn't share with feds but ran searches for the U.S. Marshals Service (EFF records). Brief includes outline, records-request list, and a confirm-before-publish checklist.

## Roadmap: Oro Valley Structured-Data Layer

Feasibility-scanned 2026-06-23. **Full reference: `OV-DATA-FEASIBILITY.md`.** Thesis: RAG/Ask made TDB's *text* queryable; the next leap is turning the messy civic record into *structured data* and monitoring it (extraction → structured store → monitor/Ask). Oro Valley is the wedge — under-covered but small/tractable enough that an AI pipeline can become the system of record, and the structured data unlocks the next-gen AI tools below. **Gate:** don't start until the in-flight social/short-form-video work settles (per [[feedback_resist_feature_creep]]); the next big project is short-form video, not this.

**Cross-cutting gotcha:** `orovalleyaz.gov` is behind an **Akamai WAF** — bots get 403 unless they spoof a full Chrome header set (UA + Accept + Referer + Sec-Fetch-*) or use a headless browser. The clean WAF-free paths (prefer these): `gismap.orovalleyaz.gov` (GIS), Swagit→Granicus minutes redirect, FBI Crime Data Explorer API, Laserfiche `edoc` download.

Priority order (verdicts + sources in the doc):
1. ⭐ **OV Development Watch — EASY, build first.** OV's own public anonymous **ArcGIS REST** server exposes a `CED-Planning/Development_Cases` layer (rezonings/GPAs/variances) as queryable JSON — `gismap.orovalleyaz.gov/gismap/rest/services`. Poll + diff on `CaseNumber`/`last_edited_date`; same shape as the Spotted/agenda miners. No auth, no WAF.
2. **OV Council Vote Tracker — EASY–MODERATE.** Official minutes PDFs (member-level: named OPPOSED/ABSTAINING + roll call → each member's vote derivable, not just tallies) via the Swagit→Granicus redirect `orovalleyaz.new.swagit.com/videos/{id}/minutes` → `pdftotext` → regex the fixed template. Reuses the existing OV transcription pipeline; feeds the **Vote & Promise Tracker** tool. Spot-check ~5–10 split votes first. Scan returned a current names roster to add to `pipeline/local_names.json` (confirm post-Aug-4-2026 primary).
3. **OV Crime + the TPD-contrast story — EASY (FBI CDE API).** `api.usa.gov/crime/fbi/sapi` (free key, ORI-keyed JSON) for OV trends; AZ DPS TOPS PDFs supplement. Confirmed story: TPD was the only US agency >250K pop that failed to report to the FBI in 2022 while OV PD reported cleanly — verify OV's ORI + per-year completeness in CDE before publishing.
4. **Water tracker — MODERATE.** Annual Report (production by source, per-well groundwater levels) + Rates Analysis PDFs; on-brand desert/water but annual cadence, image-table extraction needs an LLM pass. WAF headers required.
5. **Budget summaries — MODERATE; vendor data BLOCKED.** ACFR/adopted-budget PDFs parse with existing `pdftotext` muscle (dept-level budget-vs-actual). The high-value vendor check register is **not published** — records request only. `openbooks.az.gov` is a dead end for OV (stub).

## Roadmap: Spanish-Language TDB (bilingual, social-first)

Discussed 2026-06-23. **The single strongest "set us further apart" move on the table.** The Tucson metro has a large, under-served Spanish-speaking population; AI translation makes a bilingual product near-free at the margin; no other local outlet does real bilingual *civic* coverage. It's differentiation + civic mission + reuses everything already built.

- **Focus = social / short-form, NOT a parallel website (user's call, 2026-06-23).** Local Spanish speakers over-index on TikTok / IG / YouTube Shorts, so the highest-leverage play is **Spanish-language short-form video + image cards**, not a full es-mirror of the site. This dovetails directly with the **next big project (short-form video automation)** and the `social/` card pipeline — generate Spanish captions/cards/scripts alongside the English ones in the same pipeline.
- **Build shape:** add a translation/transcreation step (Claude — translate *and* localize tone, not literal MT) to the caption + short-form-script generators. Same Telegram one-tap review gate. A bilingual **Ask** (accept Spanish questions, answer in Spanish from the same corpus) is a natural later extension since the RAG infra is already live.
- **Quality bar:** translation must be reviewed, not raw MT — civic terms, official names, and place names need care (per [[feedback_ai_content_quality_bar]]). User has working Spanish (and Portuguese) to spot-check.
- **Gate:** ride on the short-form-video build; don't stand up a separate Spanish track before the English short-form pipeline exists.

## Roadmap: AI-forward tools beyond RAG (net-new ideas, 2026-06-23)

Captured from a strategy discussion. These extend the "structured data + AI" thesis; several depend on the OV data layer above. (Distinct from already-documented roadmap items: Tracking pages, FOIA Lead Spotter, Budget Analysis, Community Input Analysis, Cross-referencing, Deep Read.)

- **Semantic alerts ("watch this for me").** Reader saves a standing question (a neighborhood, a council member, a topic); the system re-runs it against new content on a cron and pushes matches. Literally saved RAG queries — direct extension of the Ask infra; the retention/subscription hook that turns Ask into a habit.
- **Council Vote & Promise Tracker.** From transcripts/minutes already captured: AI extracts (a) every vote → "how did Member X vote, what's the pattern," and (b) **commitments** officials make ("we'll revisit in 90 days") and surfaces when they come due or quietly die. Almost impossible manually; trivial for an agent watching transcripts. Depends on the OV vote-data work (#2 above).
- **Anomaly detection on structured data.** Once OV crime/permit/budget data flows, an AI pass flags outliers (a crime-category spike, an unusual sole-source contract, a permit anomaly). Where the data-collection and AI-tooling threads converge.

## Roadmap: Move TDB off the laptop

TDB has graduated past "laptop project" status — real readers, paid services (ElevenLabs, Buttondown, API costs), automated pipelines, a subscriber newsletter. A closed lid or a coffee-shop trip shouldn't be able to break it. Plan is to migrate everything off the laptop in **two stages**, not one, so a single failure doesn't cascade across all the moving parts at once.

**Stage 1 — RAG Phase 2 on Fly.io (small, single-purpose). ✅ DEPLOYED 2026-06-14** (`8387bd7`). Ask runs as its own Fly.io app (`tdb-ask`) with `ask.py` + the baked `index.sqlite` packaged together; FastAPI wrapper (`rag/server.py`), per-IP rate limiting, CORS-locked. The deploy workflow is now proven (remote builder, secrets, health checks, scale-to-zero). Laptop pipelines keep running unchanged. Costs ~$2–5/mo (near $0 idle). The daily index-refresh cron (`refresh_ask_index.sh`, 8:45 AM) is now wired (Phase 2 item 5), so the deployed agent stays current automatically. Per the Stage-2 gate, let this run stable for a couple of weeks before migrating the cron pipelines + live recordings.

**Stage 2 — Migrate the cron pipelines + live recordings to a separate, larger host.** Multi-day project. What's currently on the laptop:

| What | Move difficulty | Notes |
|---|---|---|
| 6 AM OpenClaw briefing | Medium | Python under the hood; need OpenClaw running on Linux + API key from `environment.d` |
| 6:10 AM `run_podcast.sh` | Medium | ElevenLabs/YouTube creds on the server, git push from prod (deploy key) |
| 8 AM `check_agendas.sh` | Medium | Needs `pdftotext` (poppler-utils), git push from prod |
| Friday 6 PM `run_newsletter.sh` | Easy | Python + Buttondown API; trivially portable |
| `at` jobs for live recordings | **Hard** | Long-running (2–6 hr), CPU-heavy (ffmpeg + Deepgram WebSocket); Fly.io has no `at` daemon — needs a different scheduling primitive (probably a small persistent worker process that reads the `.scheduled.json` state and wakes itself at the right times) |

The live-recording piece dictates VM sizing — likely $15–25/mo instead of $5 because long ffmpeg/Deepgram sessions need real CPU. Plan: run both laptop and new host in parallel for several days to verify nothing silently breaks before retiring the laptop cron.

**Gate:** Don't start Stage 2 until Stage 1 has been live and stable for at least a couple weeks. Reasons: (a) Stage 1 teaches the Fly.io workflow on something low-stakes, (b) splitting reduces blast radius if a deploy goes wrong, (c) it forces a clear distinction between "the public Ask service" and "the daily content pipelines" — different shapes of system, probably different ops models.

## Roadmap: Repo Consolidation

Pipeline config files (`sources.json`, `TUCSON-BRIEF.md`, openclaw skill references) currently live under `~/.openclaw/` and are not version controlled. Plan is to consolidate them into this repo so everything is in one git history.

**Preferred approach:** Single repo. The site and pipeline are tightly coupled — `sources.json` feeds the agent that produces the markdown that `generate_post.py` turns into HTML. One repo means one `git log` tells the full story.

**Work involved:**
- Move/symlink relevant files from `~/.openclaw/skills/tucson-daily-brief/` and `~/.openclaw/workspace/TUCSON-BRIEF.md` into this repo (e.g. under `config/` or `pipeline/`)
- Update hardcoded `~/.openclaw/` paths in: `TUCSON-BRIEF.md`, `check_agendas.sh`, `run_podcast.sh`, openclaw cron config (`~/.openclaw/cron/jobs.json`), and the skill's `references/` pointer
- Verify `.gitignore` covers sensitive files (API keys are already in `environment.d`, not in the repo)
- Test that the 6:00 AM and 8:00 AM cron pipelines still run end-to-end

**Key files to bring in:**
- `~/.openclaw/skills/tucson-daily-brief/references/sources.json` — news source config
- `~/.openclaw/workspace/TUCSON-BRIEF.md` — editorial instructions for the briefing agent
- Any other skill references that have accumulated

Estimated effort: ~30-60 minutes. The path updates across scripts are the fiddliest part.

## Social Media Cards (Instagram + Threads)

Image-card promo pipeline for the bespoke **`@tucsondailybrief`** Instagram (Business account, avatar `~/tdb-fb-profile.png` reused from the FB Page) + the linked **Threads** account (logs in via IG; same handle). Built starting 2026-06-20. The "video and image" promo track is IG + Threads; **LinkedIn is a separate track** (written, journalism-industry audience — don't cross the wires). Strategy + history live in the `project_social_promo_strategy` memory.

**Tooling (`social/`, committed; `social/cards/` output is gitignored):**
- `render_card.py` — core renderer. `build_card(theme, kicker, headline, dek, source, meta_text)` returns HTML; `render(slug, html)` shells out to `chromium --headless=new` at 2× device scale, screenshots, then ImageMagick `convert` downscales to a crisp **1080×1350** (IG portrait 4:5). Two themes on the locked desert palette: `terracotta` (identity/statement/alert cards, matches the avatar) and `light` (bone bg, for news headlines + explainers). A `DEMO` list at the bottom holds the dated card configs that have shipped.
- `render_feature_carousel.py` — multi-slide swipeable carousel (`SLIDES` config). Terracotta cover → light feature slides → terracotta CTA, with `N / total` counters and a "swipe →" affordance on the cover. Used for the "what sets us apart" week (Meeting Watch / Spotted / News Reports / **Ask** / **Podcast** → "Read it. Hear it. Ask it." closer).
- `render_crossword_card.py` — renders a numbered 5×5 **Tucson Mini** grid (real puzzle structure, blocks + clue numbers) + a few unmistakably-Tucson clues, to promote the Sunday newsletter's free-crossword perk. `SHOW_LETTERS=False` shows the classic empty "solve me" grid.
- `render_story.py` — **1080×1920** IG Story asset (9:16). Bottom third left intentionally open so a poll / question / link sticker can be dropped on it in-app without covering text.

**Conventions / lessons:**
- **No fabrication on public cards** (per the `feedback_ai_content_quality_bar` memory): verify any factual claim before it goes on a card. Example — the 2026-06-23 "where our weather comes from" card cited the NWS point `api.weather.gov/points/32.2217,-110.9694` (downtown Tucson / Hotel Congress) only after confirming it in `~/.openclaw/skills/tucson-daily-brief/references/sources.json`.
- **Source attribution lives in the caption, not on the card** — user found the outlet name on the card too busy (2026-06-21); news cards show just the date.
- **Stories vs. posts are different cultures**: posts = polished/permanent (carousels, statements); Stories = casual/24h, driven by interactive stickers (polls highest-completion) + the link sticker (the route to drive traffic to tucsondailybrief.com).
- **Getting cards to the phone**: user sets up IG/Threads from iPhone; email the PNG to `yesdeleon@gmail.com` or drop in iCloud/Drive, then save to Photos.
- **Auto-posting is deferred** until the format is proven; when built, start with the **Bluesky** adapter (only gatekeeper-free channel — open AT Protocol + app password). Threads/IG need a Meta app + app review. See `project_social_promo_strategy` for the full platform-difficulty map (Threads≠Bluesky protocol; Mastodon=ActivityPub). The generation pipeline (card render + a future Sonnet caption step → Telegram one-tap approve) is the reusable part across all platforms.

## Roadmap: Short-Form Video (Shorts / Reels / TikTok)

Auto-generate ~30-second vertical (1080×1920) news videos from existing TDB content and publish to YouTube Shorts, Instagram Reels, and TikTok. Discussed 2026-06-04 as a growth/discovery surface (same strategic logic as the newsletter — a daily site is a poor discovery surface; short-form video is where local audiences actually find you). **This is the user's next big project** (decided 2026-06-23). **Full platform-automation map + build plan: `SHORT-FORM-VIDEO.md`.**

**Key conclusions (2026-06-23 platform-automation research):**
- **Build our own thin publish layer — skip paid schedulers** (Ayrshare/Blotato/etc. are a convenience tax; their value is pre-approved app status, not code, and a single self-owned account needs almost no approvals). The reusable work is the platform-agnostic *generation* pipeline; publishing is just OAuth-per-platform adapters.
- **Auto-publishable for $0, no app review, own accounts:** **YouTube Shorts** (confirmed ship-now — existing project is audited, public uploads verified via oEmbed; `videos.insert` is the same call), **Instagram Reels** + **Facebook Reels** (Standard Access on own Meta app; needs R2-hosted public MP4 — verify the no-review path live), **Bluesky** (app password, zero gate; no account yet).
- **TikTok = future project, not the starting line.** User has no TikTok account / has never used the app. Unaudited apps are forced to private; public posting needs TikTok's Content Posting audit (~1–4 wks) OR draft-and-tap. Plan: make an account → post manually to learn the platform → audit only if it performs.
- **Audience:** YouTube/IG/TikTok are the three that matter; Hispanic adults over-index on IG (62%) + TikTok (57%) + YouTube, validating social-first Spanish; WhatsApp is a distinct Spanish channel (~2.5× over-index) for later.
- **Bilingual from day one:** the script + caption step should emit transcreated Spanish alongside English — that's how the social-first Spanish TDB ships.
- **Caveat found:** the YouTube channel `@tucsondailybrief` is **not phone-verified** → custom thumbnails 403 (podcast videos use an auto-frame; the thumbnail asset isn't applied). Verify the channel in Studio; low stakes for Shorts.

### Feasibility: high. The generation half reuses ~80% of the existing podcast pipeline.

The current podcast video path is minimal: `~/.openclaw/skills/tucson-daily-brief/scripts/generate_video.sh` does *static 1280×720 thumbnail + MP3 → MP4 via ffmpeg*, and `upload_to_youtube.py` already does OAuth + YouTube Data API v3 uploads (category 25, News & Politics). A vertical short is the **same recipe** with three deltas:

1. **Script** — extend `condense_script()` in `generate_podcast.py` to pick *one* story and write a ~30s (~450-char) vertical script (vs. the existing 90s / 5-story condense). One extra Haiku call, pennies.
2. **Audio** — same ElevenLabs/Voxtral TTS, shorter clip.
3. **Video** — the only genuinely new work: render at **1080×1920** (branded vertical template + headline text + **burned-in captions**). Captions are the key upgrade — short-form is watched **muted**, so karaoke-style captions drive retention. Timing path we already own: run the generated TTS audio back through **Deepgram** (~$0.0002 for 30s) for word timestamps → build an ASS/SRT file → ffmpeg burns it in. (ElevenLabs can also return character-level timestamps directly.) Stay on raw ffmpeg + ASS for the low-dependency v1; `moviepy`/Remotion only if fancier motion graphics are wanted later.

### Publishing is a gradient — build in this order (each gate de-risks the next):

1. **YouTube Shorts — trivial, already solved.** A Short is just a vertical video ≤3 min via the *same* Data API call already in use; YouTube auto-detects "Short" from aspect ratio + duration (#Shorts in description helps). ~1 day of work reusing existing auth. **Start here.**
2. **Instagram Reels — feasible, moderate setup.** Needs an IG Business/Creator account + a Meta app with `instagram_content_publish` (requires Meta **app review**) + a publicly-hosted MP4 (the existing **R2 bucket** already solves hosting). Flow: create media container → publish. Rate-limited (~50/day, far above need). The gate is the review, not the code.
3. **TikTok — feasible, most gated.** TikTok Content Posting API only lets *unaudited* apps push to **drafts**; fully-automated public posting needs passing TikTok's app audit. Pragmatic v1: auto-generate → drop into TikTok drafts → tap "publish" from the phone. Pursue the audit once it's performing.

### Constraints / decisions

- **Editorial review required, not full-auto.** A shareable 30s video that gets a fact wrong is worse than a buried blog paragraph — it's the format optimized for spread. Keep a human-in-the-loop (Telegram-approve, like news reports and the newsletter) at least until calibrated. Consistent with the existing "produced/original content is reviewed" model.
- **The hard part isn't the tech** — it's (a) the IG/TikTok API onboarding (Meta/TikTok review queues) and (b) visual quality: a static card + captions is a fine v1, but performing on these platforms eventually wants motion or b-roll (a design problem, not engineering). **Avoid AI-generated imagery for news (fabrication risk)** — lean on the official portraits in `people-photos/` (rights already held) or motion typography.
- **Cost:** negligible compute (ffmpeg free + pennies of TTS/Deepgram per short). Real cost = build time + platform onboarding + the per-short review tap.

### Related near-term task: refresh the podcast/video visual identity

The current YouTube thumbnail (`~/.openclaw/skills/tucson-daily-brief/assets/youtube-thumbnail-1280x720.png`) predates the 2026-05-11 site redesign and no longer matches the **warm-organic Southwest / desert aesthetic** (see `REDESIGN-V2.md` — Fraunces + Newsreader, sand/terracotta/sage palette, sun motif). User wants to redesign it to align with the site. When doing so, **also produce a vertical 1080×1920 variant** so the same visual language carries straight into Shorts/Reels/TikTok — do this design pass once, use both aspect ratios. This is the natural first concrete step toward the short-form pipeline above.

## Roadmap: Podcast on Spotify

**To-do:** Get the Tucson Daily Brief podcast onto Spotify. The podcast already publishes an RSS feed (generated + uploaded to R2 in the `run_podcast.sh` flow) and is live on Apple Podcasts and YouTube. Spotify ingests standard podcast RSS — the work is submitting the existing feed URL through Spotify for Podcasters (formerly Anchor), validating it, and confirming episodes flow automatically thereafter. No pipeline code change expected; it's a one-time submission of the RSS feed already being produced. Verify the feed meets Spotify's requirements (valid `<enclosure>` MP3 URLs, cover art ≥1400×1400, required iTunes tags) before submitting.

## Deployment

- **Live URL:** `https://tucsondailybrief.com` (custom domain via CNAME)
- GitHub Pages from the main branch root, repo `daylayown/tucson-daily-brief-site`
- `.nojekyll` ensures static serving

### Cron schedule (system crontab)

| Time (MST) | Job | Log |
|---|---|---|
| 6:00 AM (daily) | OpenClaw briefing agent | (OpenClaw internal) |
| 6:10 AM (daily) | `run_podcast.sh` — Telegram, blog, podcast, YouTube | `/tmp/podcast-gen.log` |
| 8:00 AM (daily) | `check_agendas.sh` — all 4 agenda pipelines + auto-schedule live recordings (`ENABLE_AUTO_SCHEDULE=1`) | `/tmp/agenda-check.log` |
| 8:45 AM (daily) | `refresh_ask_index.sh` — rebuild RAG vector index + redeploy Fly Ask app (`tdb-ask`) | `/tmp/ask-index-refresh.log` |
| 6:00 PM (Fri) | `run_newsletter.sh` — TDB Weekly draft generation + upload to Buttondown | `/tmp/newsletter-gen.log` |
| (scheduled) | `at` jobs — live reporter for YouTube + Swagit meetings | `/tmp/live-reporter*.log` |

**`atd` daemon** must be enabled (`systemctl enable --now atd`) for scheduled live recordings. Jobs are one-off — each meeting needs its own `at` job (see "Scheduling live recordings with `at`" under AI Reporter Pipeline).
