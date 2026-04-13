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
├── ai_reporter_live.py          # Live input: streamlink/direct HLS → Deepgram WebSocket → transcript JSON
├── run_live_reporter.sh         # Shell wrapper for live reporter (env loading, dep validation)
├── transcripts/                 # Working directory: transcript JSON + drafts (gitignored)
├── agenda-watch/                # Working directory: markdown previews + full references (not published)
├── agenda_mining.py             # Pima County BOS pipeline (Legistar API)
├── agenda_mining_marana.py      # Marana Town Council pipeline (Destiny Hosted scraping)
├── agenda_mining_orovalley.py   # Oro Valley Town Council pipeline (Destiny Hosted scraping)
├── agenda_mining_tucson.py      # City of Tucson pipeline (Hyland OnBase PDF + pdftotext)
├── check_agendas.sh             # Daily cron wrapper: runs all 4 pipelines + public record, auto-publishes, pushes
├── public_record_liquor.py      # Public Record pipeline: extracts liquor license filings from agenda-watch reference files
├── public-record.html           # Auto-generated Public Record section index
├── public-record/               # Published HTML files for individual filings
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

### OpenClaw and Anthropic API billing

**All AI calls in this pipeline use the Anthropic API via API key** (`"mode": "api_key"` in `openclaw.json`), not a Claude Pro/Max subscription. This was a deliberate architectural decision from day one (February 2026). The Claude Max subscription is used only for interactive sessions (Claude Code, claude.ai).

**Why this matters:** On April 4, 2026, Anthropic officially cut off Claude subscribers from using Pro/Max subscription OAuth tokens with third-party tools like OpenClaw, citing unsustainable infrastructure strain. Users running agents through flat-rate subscriptions were burning $1,000–5,000/day in equivalent API costs. This crackdown does not affect API key users — only subscription-based auth.

**This pipeline is unaffected.** OpenClaw's role here is as a cron scheduler and skills platform (see below), authenticated via API key. All downstream scripts (`agenda_mining*.py`, `ai_reporter.py`, `generate_podcast.py`) also make direct API calls with the API key from `~/.config/environment.d/anthropic.conf`.

**Monthly API cost:** ~$3–4/month total. Daily briefing (Sonnet) ~$0.09/day, podcast condensation (Haiku) ~$0.01/day, agenda mining (Sonnet) ~$0.50–0.80/month across all four municipalities.

This site is part of a daily pipeline with two stages:

1. **6:00 AM MST** — OpenClaw cron job (`~/.openclaw/cron/jobs.json`) runs the briefing agent (Sonnet 4.6) in an isolated session. The agent reads `TUCSON-BRIEF.md`, fetches sources from `sources.json`, and saves the briefing to `~/.openclaw/workspace/briefings/tucson-brief-YYYY-MM-DD.md`. OpenClaw delivery is set to `"none"` — the agent does not send to Telegram directly.

2. **6:10 AM MST** — System cron triggers `~/.openclaw/skills/tucson-daily-brief/scripts/run_podcast.sh`, which waits for the `.md` file, then runs in this order: sends to Telegram (via `send_telegram.py`) → generates blog post + git push → generates condensed podcast script (via Claude Haiku) → generates podcast audio (ElevenLabs TTS) → uploads RSS/R2 → generates YouTube video → uploads to YouTube. The blog post runs **before** and **independently of** the podcast, so a podcast failure (e.g. ElevenLabs quota exceeded) never blocks the blog. Each distribution step is non-fatal.

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

- **Post-Meeting News Reports** — 🚧 **FIRST REAL RECORDINGS SCHEDULED (April 7-8, 2026).** AI reporter that transcribes government meetings (live or from VOD) and generates AP-style news reports. Requires human editorial review before publishing. Live pipeline tested on YouTube livestreams (`ai_reporter.py` + `ai_reporter_live.py`). Pima County BOS (9 AM) and Tucson Mayor & Council (5:30 PM) scheduled via `at` for April 7. Oro Valley Town Council (5 PM) scheduled for April 8 — first Swagit live capture using `--direct` mode. `run_live_reporter.sh` includes a wait-for-stream retry loop (polls every 60s for up to 30 min).

- **Agenda Mining** — ✅ **LIVE.** Before meetings happen, read every agenda and supporting document. Surface buried items that reporters would miss and publish "what to watch" previews. Auto-publishes for all four municipalities.

- **Public Record** — ✅ **LIVE (April 11, 2026).** Surfaces public filings buried in government meeting agendas — starting with liquor license applications. Most never get reported on. The pipeline (`public_record_liquor.py`) is a post-process that runs after the four agenda miners finish: it scans the `agenda-watch/*-full.md` reference files, identifies liquor license items via keyword + line clustering, and uses Claude Sonnet to extract structured data (business name, address, series, license type, action type, applicant, ward) plus a 2-sentence newspaper-style summary. Each filing publishes as its own HTML page under `public-record/` with the existing site styling. Coverage: Pima County BOS, City of Tucson, Oro Valley Town Council. **Marana intentionally not supported** — Marana handles liquor licenses administratively through the Town Clerk and does not agendize them for council vote. Future expansion: scrape the Marana clerk page directly. Each cron run sends one consolidated Telegram notification if any new filings were published. Idempotent via `public-record/.processed.txt` (gitignored) plus per-filing output-file existence check. Cost: ~$0.005 per source file processed (one Sonnet call per liquor block, typically 1-3 filings extracted per call). The "Roadmap: Original Journalism" thesis in action — these filings are the basis for both automated coverage and optional human follow-up (the user can chase a filing for a quote/photo, promoting it from a Tier 1 filing to a Tier 2 feature; Tier 2 workflow is not yet built but is the natural next iteration).

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
Live input (YouTube):  streamlink → ffmpeg (PCM 16kHz mono) → Deepgram WebSocket → transcript JSON
Live input (Swagit):   ffmpeg reads HLS .m3u8 directly (--direct mode) → Deepgram WebSocket → transcript JSON
                                                                                    │
Downstream:            transcript JSON → Claude Sonnet 4.6 news report → Telegram review → approve → publish HTML
```

**Scripts:**

| Script | Purpose |
|---|---|
| `ai_reporter.py` | Downstream pipeline: transcript JSON → Claude report → Telegram → approve/publish |
| `ai_reporter_live.py` | Live input: streamlink or direct HLS → Deepgram WebSocket → real-time terminal display → transcript JSON |
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
| Marana | Swagit (HLS) | TBD — likely `https://stream.swagit.com/live-edge/maranaaz/smil:hd-16x9-1-a/playlist.m3u8` | `--direct` |

Pima County and Tucson stream on YouTube (use default streamlink mode). Oro Valley and Marana stream on Swagit, which serves HLS `.m3u8` streams — use `--direct` mode to have ffmpeg read the URL directly, bypassing streamlink. Swagit's streaming infrastructure uses Video.js + HLS.js on the frontend, backed by `stream.swagit.com` CDN.

**Future automation:** The agenda mining pipeline already knows meeting dates and times. A natural next step is to have `check_agendas.sh` auto-schedule `at` jobs when it discovers new meetings — for all four municipalities now that `--direct` mode supports Swagit.

**Live pipeline details:**
- Audio pipeline (default): `streamlink --stdout URL audio_only` → `ffmpeg` (convert to PCM s16le, 16kHz, mono) → Python reads 4096-byte chunks (~128ms) → Deepgram WebSocket
- Audio pipeline (direct): `ffmpeg -i URL` reads HLS/RTMP directly → same PCM conversion → same Deepgram path
- Deepgram config: nova-2 model, smart_format, diarize, interim_results, 300ms endpointing
- Terminal display: interim results shown in-place, final results with timestamps and speaker labels
- Periodic save every 60 seconds to `{slug}-partial.json` (crash protection)
- Graceful shutdown: Ctrl+C, dead air timeout (15 min default, only after first speech), max duration (6 hr default), or stream end → flushes Deepgram finals, saves transcript, auto-runs downstream pipeline
- Cost: ~$0.0077/min (~$1.38 for a 3-hour meeting)
- Idempotency: skips if transcript JSON already exists; skips draft generation if `-draft.md` exists (use `--force` to override)
- Runs unattended: designed for automated recording of town halls/briefings with no human monitoring

**Deepgram setup:** ✅ Done (March 27, 2026). API key in `~/.config/environment.d/deepgram.conf`. $200 free credit claimed.

**Dependencies:** ✅ Installed. `streamlink` and `yt-dlp` via pacman, `deepgram-sdk` (v6.1.1) via pip in project venv (`.venv/`). The shell wrapper `run_live_reporter.sh` uses `.venv/bin/python3` automatically.

**Deepgram SDK v6 notes:** The script was updated from the v3/v4 API to v6.1.1. Key differences: context manager pattern (`with client.listen.v1.connect(...) as connection`), `EventType.MESSAGE` replaces `LiveTranscriptionEvents.Transcript`, `send_media()` replaces `send()`, `send_close_stream()` replaces `finish()`, boolean params must be passed as strings (`"true"` not `True`) due to SDK query string encoding bug.

**Auto-stop behavior:** The live pipeline runs unattended with three auto-stop triggers:
- **Dead air timeout** (default 15 min) — no speech detected → graceful stop. Configurable via `--dead-air-timeout N` (seconds). **Only activates after first speech is detected** — pre-meeting silence is ignored so the recorder can wait through late starts and always-on streams (e.g., Tucson's 24/7 YouTube stream). This was added April 7, 2026 after both Pima County BOS and Tucson Mayor & Council recordings failed due to meetings starting late.
- **Max duration** (default 6 hours) — safety cap to prevent runaway costs. Configurable via `--max-duration N` (seconds).
- **Stream end** — streamlink/ffmpeg exit when the broadcast ends.

**Tested:** March 27, 2026. Verified on live YouTube streams (WWE, Al Jazeera). Broadcast-quality audio produces near-perfect transcripts (confidence 0.999-1.0). Speaker diarization working.

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

- **FOIA Lead Spotter** — A downstream post-processing layer that runs a Sonnet pass over ingested public documents (agenda-watch full references, news report drafts, public record filings) to flag items worth a public records request. Target signals: sole-source contracts above a threshold, agenda items referencing documents not included in the packet (audits, assessments, studies), rezoning decisions with thin supporting documentation, budget amendments with no attached justification. Output is a Telegram notification with the specific item, which document it came from, and what record to request — a lead, not an automated filing. The human decides whether to pursue. Fits the same architecture as `public_record_liquor.py`: scan existing reference files, apply editorial judgment via LLM, notify. Natural to build after the existing pipelines are producing steady volume, since more data flowing through means more signal to catch.

### Coverage area

The Tucson metro area broadly: City of Tucson, Pima County, Town of Marana, Town of Oro Valley, and their respective governing bodies, commissions, and public records. Not limited to Tucson city limits.

### Editorial model

- **Agenda previews** (forward-looking "What to Watch") publish automatically with no human review. They summarize what's on the agenda — low risk, high value in timeliness.
- **Post-meeting reporting and all other original journalism** is human-reviewed before publishing — no exceptions. AI drafts and flags; a human reviews, edits, and approves.
- Each piece carries a clear disclosure about AI involvement.

### Site structure

- **Daily Brief** (`index.html`, `posts/`) — daily news synthesis from local sources (live)
- **Meeting Watch** (`meeting-watch.html`, `meeting-watch/`) — AI-generated agenda previews for 4 municipalities (live, auto-published)
- **News Reports** (`news-reports.html`, `news-reports/`) — AI-drafted, human-reviewed post-meeting news reports (pipeline built, first real recordings scheduled April 7, 2026)
- **Public Record** (`public-record.html`, `public-record/`) — flagged filings surfaced from agendas; v1 covers liquor license applications across Pima County BOS, City of Tucson, Oro Valley (live as of April 11, 2026)
- **Deep Read** — AI-assisted analysis of large documents (planned)

### Story ideas

- **"The Accessibility of Public Data in Southern Arizona"** — An investigative deep dive comparing how four municipalities in the same metro area handle public access to government meeting data. Pima County offers a free, unauthenticated REST API (Legistar); Marana has scrapeable HTML pages (Destiny Hosted); Oro Valley pays for proprietary Granicus software with no public API; Tucson (the largest city) locks agendas in PDFs via Hyland OnBase. All of this is taxpayer-funded public record, yet accessibility varies wildly based on vendor choices most residents don't know were made. Could include public records requests for contract amounts to show what each municipality pays for its system.

### Constraints

The hardest part is sourcing data, not the AI pipeline. Start with what Tucson/Pima County already publishes in machine-readable formats. Some data requires FOIA/public records requests or lives in terrible PDFs and legacy systems.

## Roadmap: Distribution (Weekly Newsletter + Podcast)

Planned distribution channel for after the Public Record pipeline is live and humming. The strategic logic: a daily site is great for the people who already know about TDB, but it's a terrible discovery surface — daily readers are a tiny minority of any audience. Layering a weekly curation on top of the daily firehose is how regional outlets actually grow (Axios Local, most successful Substack locals). Cost is essentially zero: a Sonnet pass over the previous seven days of content is ~$0.05/week, and the existing TTS pipeline (ElevenLabs or Voxtral) handles the audio version with no new infrastructure.

### Format

Roughly 800-1200 words / 6-8 minutes of audio, structured as:

- **One lead story** — the most consequential thing of the week
- **4-5 short hits** — each with a one-sentence "why this matters" explainer
- **One Public Record callout** — "Coming soon to your neighborhood" (new restaurants, businesses, permits, etc. — this is the unique hook other regional newsletters can't match)
- **One Meeting Watch lookahead** — "Here's what's on the agenda next week"
- **A closing note** — voice, personality, neighborhood color

Generated by Claude Sonnet from the past 7 days of site content. The same pass picks the lead and adjusts prose register for the kitchen-table-on-Sunday-morning reader (warmer, more opinionated than the daily brief).

### Platform: Substack

Default to Substack rather than self-hosted, despite the 10% revenue cut. Reasons:
- **Built-in network effects.** Substack's recommendation engine has become a real distribution channel for regional/independent journalism — other Substacks recommending each other is how new audiences are found.
- **Zero infrastructure.** Native email, native podcast hosting, decent analytics, no SMTP/RSS plumbing to maintain.
- **Brand association.** Substack is where independent journalism lives in the public mind right now.
- **Portability.** Export the subscriber list periodically. The audience comes with you if you ever migrate.

The 10% rev share is acceptable as the cost of the discovery flywheel. Self-hosted has better unit economics but no growth engine — for a side project trying to grow, network effects beat margins.

### Audio version

Reuse the existing TTS pipeline (`generate_podcast.py` flow). Weekly episode is just a different input text — clean for TTS, send to ElevenLabs or Voxtral, upload to R2 / Substack's native podcast hosting. Substack's app plays inline audio for paid posts, and the episode also distributes via RSS to Apple/Spotify if desired. Probably fits inside the existing podcast feed as a separate weekly long-form episode rather than a second feed.

### Critical principle: do not duplicate the website

The Substack must not be a copy of the daily site. If both surfaces show the same content, neither has a reason to exist.

- **Website** = daily archive, canonical source, searchable, linkable, comprehensive.
- **Substack** = weekly editorial product. Opinionated, curated, written *to* a specific person reading at the kitchen table on Sunday morning. Different voice, different selection logic, different value proposition.

Same Sonnet pass that picks the week's best stories also rewrites them in newsletter voice — not just a digest of headlines.

### Sequence and timing

**Do not launch the newsletter until the Public Record pipeline has been live and producing content for 2-3 weeks.** Reason: without Public Record, the weekly newsletter is "7 daily briefs + 4-8 meeting previews" — competent but not differentiated. With Public Record running, the weekly has a unique recurring story type ("here's what's opening, closing, and changing in your neighborhood") that nobody else produces for Tucson. That's the forwarding hook — the thing that makes a reader send it to a friend, which is the only marketing channel that actually compounds.

Build order:
1. Public Record liquor license pipeline (in progress)
2. Watch it run for 2-3 weeks, learn what volume and editorial gotchas look like
3. Launch Substack with weekly written newsletter
4. Add audio version once written newsletter is stable

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
| (scheduled) | `at` jobs — live reporter for YouTube + Swagit meetings | `/tmp/live-reporter*.log` |

**`atd` daemon** must be enabled (`systemctl enable --now atd`) for scheduled live recordings. Jobs are one-off — each meeting needs its own `at` job (see "Scheduling live recordings with `at`" under AI Reporter Pipeline).
