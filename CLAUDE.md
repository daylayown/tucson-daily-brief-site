# Tucson Daily Brief Site

Static blog for GitHub Pages — minimal, text-first, Daring Fireball style. No JavaScript, no frameworks, no build tools.

## Project Structure

```
├── style.css                    # Desert/Southwest themed CSS (sand, terracotta, sage)
├── generate_post.py             # Daily brief: Markdown → HTML generator + index rebuilder
├── index.html                   # Auto-generated daily brief index page (newest-first)
├── posts/                       # Individual daily brief HTML files (named YYYY-MM-DD.html)
├── meeting-watch.html           # Auto-generated Meeting Watch index page
├── meeting-watch/               # Published meeting preview HTML files
├── news-reports.html            # Auto-generated News Reports index page
├── news-reports/                # Published news report HTML files (human-approved)
├── ai_reporter.py               # Downstream pipeline: transcript JSON → Claude report → Telegram → publish
├── ai_reporter_live.py          # Live input: streamlink → Deepgram WebSocket → transcript JSON
├── run_live_reporter.sh         # Shell wrapper for live reporter (env loading, dep validation)
├── transcripts/                 # Working directory: transcript JSON + drafts (gitignored)
├── agenda-watch/                # Working directory: markdown previews + full references (not published)
├── agenda_mining.py             # Pima County BOS pipeline (Legistar API)
├── agenda_mining_marana.py      # Marana Town Council pipeline (Destiny Hosted scraping)
├── agenda_mining_orovalley.py   # Oro Valley Town Council pipeline (Destiny Hosted scraping)
├── agenda_mining_tucson.py      # City of Tucson pipeline (Hyland OnBase PDF + pdftotext)
├── check_agendas.sh             # Daily cron wrapper: runs all 4 pipelines, auto-publishes, pushes
├── MEETING-WATCH-PIPELINE.md    # Full reference docs for the meeting watch system
├── CNAME                        # Custom domain: tucsondailybrief.com
├── .nojekyll                    # Tells GitHub Pages to skip Jekyll
├── .gitignore                   # Excludes __pycache__/, transcripts/
└── CLAUDE.md
```

## How It Works

`generate_post.py` takes a briefing markdown file as input and:
1. Extracts the date from the filename (e.g., `tucson-brief-2026-02-18.md` → `2026-02-18`)
2. Converts the markdown to HTML (handles bold, emoji section headers, source citations with links, separators)
3. Writes an HTML post to `posts/YYYY-MM-DD.html`
4. Rebuilds `index.html` by scanning all posts in `posts/` and listing them newest-first
5. Is idempotent — running it twice with the same input overwrites cleanly, no duplicates

Usage:
```
python generate_post.py ~/.openclaw/workspace/briefings/tucson-brief-2026-02-18.md
```

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

- Desert palette: sand bg `#f5f0e6`, terracotta links `#c75b39`, sage dates `#7a8b6f`, brown text `#3d3029`
- Single-column, max-width 600px, centered
- System font stack, line-height 1.7
- Mobile-friendly via viewport meta + fluid layout
- Footer links to Apple Podcasts, YouTube, LinkedIn, and Email
- Google Analytics (GA4) tracking via gtag.js, measurement ID `G-MEYSB9GYF2`

## Source Links

`generate_post.py` includes a `SOURCE_URLS` dictionary mapping outlet names to their homepages, and a `linkify_sources()` function that handles two citation formats:

1. **Markdown links** `[Source Name](url)` — links directly to the original article (preferred)
2. **Plain text** `Source Name` — falls back to the outlet's homepage via `SOURCE_URLS` lookup

The upstream briefing agent (`~/.openclaw/workspace/TUCSON-BRIEF.md`) is instructed to include direct article URLs in markdown link format. If it can't determine the URL for a story, plain text is acceptable and the homepage fallback kicks in.

## Automation

This site is part of a daily pipeline with two stages:

1. **6:00 AM MST** — OpenClaw cron job (`~/.openclaw/cron/jobs.json`) runs the briefing agent (Sonnet 4.6) in an isolated session. The agent reads `TUCSON-BRIEF.md`, fetches sources from `sources.json`, and saves the briefing to `~/.openclaw/workspace/briefings/tucson-brief-YYYY-MM-DD.md`. OpenClaw delivery is set to `"none"` — the agent does not send to Telegram directly.

2. **6:10 AM MST** — System cron triggers `~/.openclaw/skills/tucson-daily-brief/scripts/run_podcast.sh`, which waits for the `.md` file, then runs in this order: sends to Telegram (via `send_telegram.py`) → generates blog post + git push → generates condensed podcast script (via Claude Haiku) → generates podcast audio (ElevenLabs TTS) → uploads RSS/R2 → generates YouTube video → uploads to YouTube. The blog post runs **before** and **independently of** the podcast, so a podcast failure (e.g. ElevenLabs quota exceeded) never blocks the blog. Each distribution step is non-fatal.

Telegram delivery happens **only** through `run_podcast.sh` → `send_telegram.py`, which reads the saved `.md` file. OpenClaw's cron delivery was disabled to prevent duplicate sends of raw agent output.

### Podcast script condensing

The podcast script is condensed from a full ~7,500-char read (~8 minutes) to a tight ~1,400-char read (~90 seconds) using Claude Haiku. This was implemented to stay within the ElevenLabs Creator tier (100K chars/month, $22/mo). The `condense_script()` function in `generate_podcast.py` sends the full script to Haiku with instructions to pick the top 5 most newsworthy stories, drop weather/source attributions/section transitions, and write in broadcast style. Cost: ~$0.01/day. Falls back to the full script if the API call fails.

**ElevenLabs budget:** Creator tier, 100K chars/month. Condensed podcast uses ~45K chars/month (with Turbo v2.5 at 0.5 credits/char, that's ~22.5K credits/month). Usage-based billing enabled at 25,000 credit threshold as safety net.

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

### Key dependencies

- `pdftotext` (poppler-utils) — required for Tucson PDF extraction
- `ANTHROPIC_API_KEY` in `~/.config/environment.d/anthropic.conf`
- Telegram credentials for notifications

## Roadmap: Original Journalism

The daily brief repackages existing journalism. The agenda mining pipeline (above) is the first **original journalism** feature — AI-generated previews of government meetings. The next stage expands this with more content types.

### Planned content types

- **Post-Meeting News Reports** — 🚧 **LIVE PIPELINE BUILT, AWAITING DEEPGRAM SETUP (March 2026).** AI reporter that transcribes government meetings (live or from VOD) and generates AP-style news reports. Requires human editorial review before publishing. Live pipeline code complete (`ai_reporter.py` + `ai_reporter_live.py`), needs Deepgram API key to activate — see "AI Reporter Pipeline" section below.

- **Agenda Mining** — ✅ **LIVE.** Before meetings happen, read every agenda and supporting document. Surface buried items that reporters would miss and publish "what to watch" previews. Auto-publishes for all four municipalities.

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

Live pipeline built March 2026. VOD pipeline planned but not yet implemented.

**Architecture:**
```
Live input:  streamlink → ffmpeg (PCM 16kHz mono) → Deepgram WebSocket → transcript JSON
                                                                              │
Downstream:  transcript JSON → Claude Sonnet 4.6 news report → Telegram review → approve → publish HTML
```

**Scripts:**

| Script | Purpose |
|---|---|
| `ai_reporter.py` | Downstream pipeline: transcript JSON → Claude report → Telegram → approve/publish |
| `ai_reporter_live.py` | Live input: streamlink → Deepgram WebSocket → real-time terminal display → transcript JSON |
| `run_live_reporter.sh` | Shell wrapper: loads env vars, validates deps, passes args through |

**Usage:**
```bash
# Capture a live stream and generate a news report
./run_live_reporter.sh "https://youtube.com/watch?v=XXX" --slug pentagon-2026-03-26

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

**Live pipeline details:**
- Audio pipeline: `streamlink --stdout URL audio_only` → `ffmpeg` (convert to PCM s16le, 16kHz, mono) → Python reads 4096-byte chunks (~128ms) → Deepgram WebSocket
- Deepgram config: nova-2 model, smart_format, diarize, utterances, interim_results, 300ms endpointing
- Terminal display: interim results shown in-place, final results with timestamps and speaker labels
- Periodic save every 60 seconds to `{slug}-partial.json` (crash protection)
- Graceful Ctrl+C: closes Deepgram (flushes finals), saves transcript, auto-runs downstream pipeline
- Cost: ~$0.0077/min (~$1.38 for a 3-hour meeting)
- Idempotency: skips if transcript JSON already exists; skips draft generation if `-draft.md` exists (use `--force` to override)

**Deepgram setup required (not yet done):**
1. Sign up at https://deepgram.com and claim the $200 free credit (~430 hours of transcription)
2. Create an API key
3. Save it: `echo "DEEPGRAM_API_KEY=your_key_here" > ~/.config/environment.d/deepgram.conf`

**Python dependencies required (not yet installed):**
```bash
pip install deepgram-sdk    # WebSocket API client
pip install streamlink      # Live YouTube audio capture
pip install yt-dlp          # Streamlink dependency for YouTube
```

**Dry run plan:** Test on Pentagon press briefings (Hegseth/Caine Iran war briefings, several per week, 30-60 min, well-mic'd). DOW publishes official transcripts at war.gov/News/Transcripts/ for accuracy comparison. Schedule not fixed — check [DOW Live Events](https://www.war.gov/News/Live-events/) or [DVIDS](https://www.dvidshub.net/feature/PentagonPressBriefings) for upcoming streams.

**VOD pipeline (planned, not yet built):**
- `ai_reporter_vod.py` — yt-dlp downloads audio → Deepgram batch API transcribes → same downstream pipeline
- Cost: ~$0.0043/min (~$0.78 for a 3-hour meeting)
- Can also use Marana/OV Swagit transcripts directly where available
- Production workhorse once live pipeline is validated

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

- **Public Record** — Monitor building permits, business license applications, court filings, and campaign finance disclosures. Flag anomalies: large developments before they're announced, unusual donations, lawsuits involving the city.

- **Budget & Spending Analysis** — Track city/county budgets, check registers, and contract awards. Flag unusually large contracts, sole-source awards, and spending trends. Compare budget projections vs. actuals over time.

- **Deep Read** — AI-assisted analysis of large documents when they drop: environmental impact statements, audit reports, proposed legislation, police use-of-force statistics, school performance data.

- **Cross-referencing** — Connect dots across public datasets: developers who get rezonings and also donate to council members, LLCs buying properties along future transit corridors, contractors who win multiple bids and employ registered lobbyists.

- **Community Input Analysis** — Analyze public comment submissions on controversial projects (hundreds of written comments that get one-sentence summaries in staff reports). Track 311 complaints by neighborhood.

### Coverage area

The Tucson metro area broadly: City of Tucson, Pima County, Town of Marana, Town of Oro Valley, and their respective governing bodies, commissions, and public records. Not limited to Tucson city limits.

### Editorial model

- **Agenda previews** (forward-looking "What to Watch") publish automatically with no human review. They summarize what's on the agenda — low risk, high value in timeliness.
- **Post-meeting reporting and all other original journalism** is human-reviewed before publishing — no exceptions. AI drafts and flags; a human reviews, edits, and approves.
- Each piece carries a clear disclosure about AI involvement.

### Site structure

- **Daily Brief** (`index.html`, `posts/`) — daily news synthesis from local sources (live)
- **Meeting Watch** (`meeting-watch.html`, `meeting-watch/`) — AI-generated agenda previews for 4 municipalities (live, auto-published)
- **News Reports** (`news-reports.html`, `news-reports/`) — AI-drafted, human-reviewed post-meeting news reports (pipeline built, awaiting Deepgram setup)
- **Public Record** — flagged permits, filings, contracts (planned)
- **Deep Read** — AI-assisted analysis of large documents (planned)

### Story ideas

- **"The Accessibility of Public Data in Southern Arizona"** — An investigative deep dive comparing how four municipalities in the same metro area handle public access to government meeting data. Pima County offers a free, unauthenticated REST API (Legistar); Marana has scrapeable HTML pages (Destiny Hosted); Oro Valley pays for proprietary Granicus software with no public API; Tucson (the largest city) locks agendas in PDFs via Hyland OnBase. All of this is taxpayer-funded public record, yet accessibility varies wildly based on vendor choices most residents don't know were made. Could include public records requests for contract amounts to show what each municipality pays for its system.

### Constraints

The hardest part is sourcing data, not the AI pipeline. Start with what Tucson/Pima County already publishes in machine-readable formats. Some data requires FOIA/public records requests or lives in terrible PDFs and legacy systems.

## Deployment

- **Live URL:** `https://tucsondailybrief.com` (custom domain via CNAME)
- GitHub Pages from the main branch root, repo `daylayown/tucson-daily-brief-site`
- `.nojekyll` ensures static serving

### Cron schedule (system crontab)

| Time (MST) | Job | Log |
|---|---|---|
| 6:00 AM | OpenClaw briefing agent | (OpenClaw internal) |
| 6:10 AM | `run_podcast.sh` — Telegram, blog, podcast, YouTube | `/tmp/podcast-gen.log` |
| 8:00 AM | `check_agendas.sh` — all 4 agenda pipelines | `/tmp/agenda-check.log` |
