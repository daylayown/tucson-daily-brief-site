# Roadmap — queued and gated work

Every not-yet-building track in one place: Responsiveness Index, Coverage Expansion, Structured-Data Layers, Data Center Watch, Tucson en Breve, AI-forward tools, moving off the laptop, short-form video, Spotify, and the completed OpenClaw/repo-consolidation work.

Reference doc split out of CLAUDE.md on 2026-07-17 to keep the always-loaded context lean. Prose is preserved verbatim from CLAUDE.md; CLAUDE.md now carries a short pointer to this file.

---

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

## Roadmap: Structured-Data Layers (Oro Valley / Marana / Tucson / Schools)

Shared thesis: RAG/Ask made TDB's *text* queryable; the next leap is turning the messy civic record into *structured data* and monitoring it (extraction → structured store → monitor/Ask), unlocking the AI-forward tools below. Each municipality gets its own layer, all reusing the `dev_watch_*.py` poll-and-diff pattern. **Gate per [[feedback_resist_feature_creep]]: the next big project is short-form video — capture only, don't start building these mid-stream without a user go-ahead.** Each has a full feasibility doc + memory entry with exact endpoints/fields/verdicts; the essentials:

- **Oro Valley** (scanned 2026-06-23, `OV-DATA-FEASIBILITY.md`). Wedge municipality. **Gotcha: `orovalleyaz.gov` is behind an Akamai WAF** (403 without a full Chrome header set); WAF-free paths: `gismap.orovalleyaz.gov` (GIS), Swagit→Granicus minutes redirect, FBI CDE API, Laserfiche `edoc`. Build-first = **OV Development Watch** (`gismap.orovalleyaz.gov/gismap/rest/services` `CED-Planning/Development_Cases`, poll/diff on `CaseNumber`). Then vote tracker (minutes PDFs → member-level votes), crime (FBI CDE), water, budget (vendor register = records-request only).

- **Marana** (scanned 2026-06-24, `MARANA-DATA-FEASIBILITY.md` + `project_marana_data_layer` memory). **Gotcha (INVERSE of OV): `www.maranaaz.gov` 403s a full Chrome UA but 200s with no/minimal UA.** WAF-free: `portal.maranaaz.gov` (ArcGIS), `services1.arcgis.com/IZmVB517nWCTFBQy` (AGOL), `gisdata.pima.gov`, FBI CDE. ✅ **Development Watch SHIPPED 2026-06-24 (`9120a30`, `dev_watch_marana.py`)** — content-hash diff (no edit-timestamp), undated projects skipped not dated-today; state `around-town/.dev_state_marana.json`. **Build next = Marana Crime** (FBI CDE, **Marana PD ORI `AZ0100900`**, clean NIBRS 2018–2024, `api.usa.gov/crime/fbi/cde/summarized/agency/AZ0100900/{violent-crime|property-crime|homicide}?from=MM-YYYY&to=MM-YYYY&API_KEY=…`) — ships a feed + the "Marana reported every year, TPD didn't" story. Then permits/business-licenses, DPS TOPS, budget, water. Open Qs: is `Business_License_2023` live or a frozen snapshot; DLLC pending-apps endpoint; Financial Transparency Dashboard vendor.

- **City of Tucson** (scanned 2026-06-26, `TUCSON-DATA-FEASIBILITY.md` + `project_tucson_data_layer` memory). **Headline: Tucson is the *most* data-open municipality** — two authless no-WAF ArcGIS REST hosts (`mapdata.tucsonaz.gov` + `gis.tucsonaz.gov` `/arcgis/rest/services`). **Gotcha: `www.tucsonaz.gov` CMS 403s a Chrome UA but serves a blank UA** (incl. `/files/` PDFs); bare `TPD`/`PublicSafety`/`HCD` folders token-secured → public data under `PublicMaps/OpenData_*`; budget = OpenGov (no API). Build-first = Development Watch + "What's Opening" (permits/COs `PermitsCode/MapServer` /81,/99 + licenses /3). High-value = **Crime + FBI-gap story** (`Tucson_Police_Reported_Crimes/FeatureServer/8`, TPD ORI `AZ0100300` 2021 NIBRS all-null; `clearance_verbose` makes the 97.56%/57.45% gap computable). Also 311/Responsiveness M1 (`seeclickfix.com/api/v2/issues?place_url=tucson`), code enforcement (`/103`). Story-only: TFD fire-data GAP.

- **Southern AZ Schools** (scanned 2026-06-26, `SCHOOL-DATA-FEASIBILITY.md` + `project_school_data_layer` memory + `COVERAGE-EXPANSION.md` Part 1C). 9 metro K-12 districts — most under-covered governance beat. **EASY data (no WAF): Auditor General "School District Spending" XLSX** (classroom-% + teacher salary, all districts), **ADE Report Cards JSON API** (`azreportcards.azed.gov/api/DataApi/…`, no key) + A-F grades XLSX on `azsbe.az.gov`, **Urban Institute Education Data API** (`educationdata.urban.org`, no key). **Gotcha: `www.azed.gov` is a Cloudflare JS-challenge wall (spoofing FAILS)** — use the APIs instead. **Meetings: 8/9 districts via two scrapers — Diligent** (TUSD `tusd1-schooldesk.community.highbond.com`, Vail, Sahuarita, Tanque Verde) + **BoardBook** (Amphi 2065, Marana 1780, Catalina Foothills 1202, Flowing Wells 1607); **Sunnyside = BoardDocs `susd12`** (hardest). 6 YouTube live feeds + TUSD Livestream.com HLS (`--direct`). **Pilot = Vail USD.** Higher editorial sensitivity (culture-war-adjacent) → human-review all reports, never surface student-level data (FERPA).

**Side task across all four:** add council members / PD command staff / board members + superintendents to `pipeline/local_names.json`.

## Topic flags + Roadmap: Southern AZ Data Center Watch

**Shipped 2026-06-27 (`49e7487`): a high-interest topic-flag layer on the Around Town dev-watch pollers.** Data centers are a live Southern AZ flashpoint (power/water/growth) — Marana approved a 600-acre hyperscale Beale rezoning 6–0 in Jan 2026 over packed-chamber opposition, and a *second* application ("Ranch House SP Major Amendment," `PCZ2511-001`, The Planning Center, 13100 W Marana Rd — record reads "Technology Campus, Data Center and Medium Density Residential") was filed Nov 2025. **TDB's `dev_watch_marana.py` auto-surfaced that second filing on 2026-06-24, two days before KOLD reported it on 2026-06-26.** The applications live in the town's public ArcGIS land-use feed (the layer we already poll); the actual case documents live in Marana's **eTRAKiT** portal (`maranaegov.com/eTRAKiT/`, case `PCZ2511-001`), which 403s non-browser clients (discovery is automatable; document-pull is not).

How the topic layer works (one source of truth, reused by Marana, Oro Valley, and any future Tucson poller):
- `generate_post.py`: `TOPIC_DEFS` / `detect_topics()` / `topic_badge_html()`. High-precision keywords (`data center`, `hyperscale`, `server farm`, `technology/computing/compute campus`) — precision over recall, since a match elevates a card AND pings a human. Around Town feed cards (`_collect_at_dir` → `_render_at_item`) carry the flag.
- `dev_watch_marana.py` + `dev_watch_orovalley.py`: flag matching cases, render a **"Data Center Watch"** badge on the page + card, and print a machine-readable `TOPIC-ALERT\t<topic>\t<muni>\t<title>\t<url>` line on publish.
- `check_agendas.sh`: `send_topic_alerts()` greps those lines and fires a **distinct, louder Telegram** ("🛰️ DATA CENTER WATCH") on top of the routine development-count notice. Fires only on NEW/changed flagged cases (no spam for known ones).
- `style.css`: `.topic-flag(s)` terracotta pill on the desert palette. To add a future topic (e.g. an ICE-detention flag), add one entry to `TOPIC_DEFS` — everything else inherits it.

**Queued (NOT building — gated): a standing "Southern AZ Data Center Watch" tracking page.** A canonical page aggregating every metro data-center application + approval (Beale/Project Blue, Ranch House, future Marana/OV/Tucson) with status, the power/water asks, hearing dates, and links to TDB's own coverage. This is a **Tracking-section instance** (see the Tracking roadmap above) and the topic-flag layer is its feeder — the detector already finds the cases; the page would aggregate them. **Gate per [[feedback_resist_feature_creep]]:** the next big project is short-form video; this is captured here, not started. It also inherits Tracking's hard gate (ship after RAG Phase 2 is fully deployed — it is) and Tracking's human-review-every-update editorial bar. Parked at the user's direction 2026-06-27; revisit after short-form video.

## Roadmap: Spanish-Language TDB → "Tucson en Breve" full fork

**Evolved 2026-06-24 → the vision is now a full Spanish sister site at `tucsonenbreve.com`, not just social. Full plan: `TUCSONENBREVE.md`.** A parallel Spanish fork that mirrors TDB's content via LLM auto-translation (translate canonical markdown → language-aware renderers → separate GitHub Pages repo, same desert-palette CSS, Spanish UI strings + a civic-terminology glossary; names/places reuse `pipeline/local_names.json`). Forks the brief, news reports, meeting watch, Spotted, In Depth, podcast (Spanish TTS), short-form (Spanish cuts → @tucsonenbreve socials), and newsletter; **defers Ask/RAG, the crossword, and the Responsiveness Index.** Spanish short-form cuts are likely the first visible deliverable (the bilingual-Shorts idea — but as *separate cuts*, not both languages crammed on one card). Status: planning only. The notes below are the earlier social-first framing, now subsumed by the full-fork plan.

### Earlier social-first framing (2026-06-23, subsumed by the fork plan above)

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
| `run_newsletter.sh` (manual, Saturday ritual — no longer cron'd) | Easy | Python + Buttondown API; trivially portable |
| `at` jobs for live recordings | **Hard** | Long-running (2–6 hr), CPU-heavy (ffmpeg + Deepgram WebSocket); Fly.io has no `at` daemon — needs a different scheduling primitive (probably a small persistent worker process that reads the `.scheduled.json` state and wakes itself at the right times) |

The live-recording piece dictates VM sizing — likely $15–25/mo instead of $5 because long ffmpeg/Deepgram sessions need real CPU. Plan: run both laptop and new host in parallel for several days to verify nothing silently breaks before retiring the laptop cron.

**Gate:** Don't start Stage 2 until Stage 1 has been live and stable for at least a couple weeks. Reasons: (a) Stage 1 teaches the Fly.io workflow on something low-stakes, (b) splitting reduces blast radius if a deploy goes wrong, (c) it forces a clear distinction between "the public Ask service" and "the daily content pipelines" — different shapes of system, probably different ops models.

## Roadmap: Eliminate the OpenClaw dependency (research)

**Motivation (2026-06-24):** OpenClaw's *only* job in this stack is running the 6 AM briefing agent (everything else — `run_podcast.sh`, `check_agendas.sh`, the AI reporter, the newsletter, the daily Short — is plain system cron + Python calling the Anthropic API directly). And that one agent is unreliable in ways that hurt: (a) it **mis-saves the brief to the wrong path ~weekly** despite an explicit, unambiguous instruction (see the "Brief mis-save failure mode" note above), and (b) OpenClaw's **mid-run context compaction** silently drops heavy feeds before synthesis (the Daily Star issue). Both are symptoms of using a general agent for what is really **deterministic plumbing**: fetch a fixed list of URLs → hand the content to Claude for editorial synthesis → save to a fixed path. The LLM should do the *judgment* (rank/select/write stories), not the fetching or the file I/O.

**The thesis:** replace the OpenClaw agent with a self-contained **`generate_brief.py`** (system cron, like every other job), where:
- **Python** reads `sources.json`, fetches each feed/weather API, and reads `EDITOR-TIPS.md` — deterministic, no agent, no compaction, no "improvised" sources.
- **One Anthropic API call** (Sonnet) does the synthesis: pass the fetched content + the editorial rules (ported from `TUCSON-BRIEF.md` — editorial priorities, source-skip, soft-hedging, the editor-tips include-through logic) and get back the structured markdown brief.
- **Python writes** the file to the canonical path — a normal `open(...).write(...)`, so the save-path bug is *structurally impossible*.
- Downstream is unchanged: `run_podcast.sh` already does Telegram/blog/Short/podcast off the saved `.md`.

**Why it's attractive:** eliminates the two recurring failure modes, removes a whole runtime dependency, makes the stack uniformly Python-on-cron, and is **far easier to migrate off the laptop** (a Python script ports trivially; an OpenClaw runtime does not) — so this de-risks the "Move TDB off the laptop" roadmap too. It also pairs naturally with **Repo Consolidation** (the ported editorial rules + `sources.json` come into the repo and get version-controlled).

**Things to research / decide before building:** (1) context budget — can one Sonnet call hold ~11 fetched feeds, or do we distill each feed to notes first (cheap per-feed pass) then synthesize? (the extract-as-you-go idea, now forced by Python rather than hoped-for from an agent); (2) faithfully porting the `TUCSON-BRIEF.md` editorial logic into a prompt + the EDITOR-TIPS include-through date handling; (3) whether any OpenClaw skill features are actually used beyond cron+agent-turn (audit `~/.openclaw/` — believed to be nothing else); (4) feed-fetch robustness (Cloudflare-walled sources, the `status: broken/disabled` mechanism) reimplemented in Python with proper headers/timeouts. **Not yet building — research first.** Likely a ~1-day build given the synthesis prompt already exists in `TUCSON-BRIEF.md`.

## Repo Consolidation (brief-pipeline config — ✅ DONE 2026-06-26)

The brief pipeline's config files now live in the repo under `pipeline/` and are version-controlled, so one `git log` tells the full story. Pattern used throughout: **move the file into `pipeline/`, leave a symlink at the old `~/.openclaw/` path** so any stale reference still resolves, and point the script at the repo copy directly.

**Consolidated:**
- `pipeline/sources.json` — news source config (moved 2026-06-25, `095a20a`). Old `~/.openclaw/skills/tucson-daily-brief/references/sources.json` → symlink.
- `pipeline/EDITOR-TIPS.md` — hand-submitted editor leads read by `generate_brief.py` each run (moved 2026-06-26). Old `~/.openclaw/workspace/EDITOR-TIPS.md` → symlink. `generate_brief.py` reads the repo copy script-relative.
- `pipeline/TUCSON-BRIEF.md` — the original briefing-agent editorial rules, **now reference-only** (the OpenClaw agent is retired; the live rules are ported into `SYNTHESIS_PROMPT` in `generate_brief.py`). Kept for provenance. Old `~/.openclaw/workspace/TUCSON-BRIEF.md` → symlink.
- Editorial rules themselves: already embedded in `generate_brief.py`'s `SYNTHESIS_PROMPT` (no separate rules file needed).

**Deliberately left under `~/.openclaw/` (not consolidated, by design):**
- `BRIEFINGS_DIR` (`~/.openclaw/workspace/briefings/`) — the brief **output** dir, a pipeline *contract* with `run_podcast.sh` (`resolve_brief`), not version-controlled config. Relocating it would mean a coordinated change to `run_podcast.sh` for no consolidation benefit.
- `send_telegram.py` (`~/.openclaw/skills/tucson-daily-brief/scripts/`) — shared notify utility referenced by **four other pipelines** (`check_agendas.sh`, `ai_reporter.py`, `schedule_recording.py`, `poll_tucson_water.py`). Bringing it in is a broader, separate task touching those pipelines — a reasonable future follow-up, but out of scope for the brief consolidation.

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
2. **Audio** — same ElevenLabs TTS, shorter clip.
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

**To-do:** Get the Tucson Daily Brief podcast onto Spotify. The podcast already publishes an RSS feed (generated + uploaded to R2 in the `run_podcast.sh` flow) and is live on Apple Podcasts and YouTube. Spotify ingests standard podcast RSS — the work is submitting the existing feed URL through Spotify for Creators (the rebranded Spotify for Podcasters / Anchor, at `creators.spotify.com`), validating it, and confirming episodes flow automatically thereafter. No pipeline code change expected; it's a one-time submission of the RSS feed already being produced.

**Status (2026-06-30): feed validated + ready to submit; blocked only on a Spotify-side login bug.** Full do-it-later checklist (feed URL, validation results, submission steps, login-loop fixes, post-launch tasks) lives in **`SPOTIFY-SUBMISSION.md`**. Short version: feed `https://pub-9552aa4d76834cea9f9e35f908b604e4.r2.dev/feed.xml` passed every requirement (128 episodes, reachable MP3 enclosures, owner email `nicholas@daylayown.org`, 3000×3000 cover, News/en-us). Submission is blocked by a **known Spotify for Creators login redirect loop** (Spotify support confirmed 2026-06-30 it's a current issue on their side, not our account/feed). Pick-up: retry the portal login next day → paste feed URL → enter the verification code emailed to `nicholas@daylayown.org` → submit. Once live, add the Spotify show URL to the site footer + social link-in-comments.
