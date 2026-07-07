# AI Reporter Pipeline — full reference

Deep reference for the live + VOD meeting-transcription → news-report pipeline. Summary + the load-bearing bits (stream URLs, `at` scheduling, enable flag) live in `CLAUDE.md` under "AI Reporter Pipeline"; everything else is here.

Live pipeline built March 2026. VOD pipeline built May 2026 (`ai_reporter_vod.py`).

## Architecture

```
Live input (YouTube):  streamlink → ffmpeg (PCM 16kHz mono) → Deepgram WebSocket → transcript JSON
Live input (Swagit):   ffmpeg reads HLS .m3u8 directly (--direct mode) → Deepgram WebSocket → transcript JSON
VOD input:             ffmpeg extracts → opus file → Deepgram batch (pre-recorded) API → transcript JSON
                                                                                    │
Downstream:            transcript JSON → Claude Sonnet 4.6 news report → Telegram review → approve → publish HTML
```

**Why a separate VOD pipeline?** Deepgram's live WebSocket API expects ~1× real-time audio. ffmpeg reading an HLS VOD pulls audio much faster than real-time, which floods the live WebSocket and triggers a 1011 keepalive-timeout error after a minute or two. Verified on the Marana May 5 VOD (2026-05-10): live pipeline died after capturing 95 seconds; batch API processed the same 72-minute meeting cleanly in one shot. The batch API is the right tool whenever the source is a complete recording rather than a real-time stream.

## Scripts

| Script | Purpose |
|---|---|
| `ai_reporter.py` | Downstream pipeline: transcript JSON → Claude report → Telegram → approve/publish |
| `ai_reporter_live.py` | Live input: streamlink or direct HLS → Deepgram WebSocket → real-time terminal display → transcript JSON |
| `ai_reporter_vod.py` | VOD input: any audio/video URL or local file → ffmpeg extracts opus → Deepgram batch API → transcript JSON, then hands off to `ai_reporter.py` for the draft |
| `run_live_reporter.sh` | Shell wrapper: loads env vars, validates deps, waits for stream to go live, passes args through. Skips streamlink/yt-dlp checks in `--direct` mode |

## Usage

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

## File layout

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

## Transcript JSON schema

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

## Wait-for-stream — two modes

- **Streamlink mode** (default): `run_live_reporter.sh` polls with `yt-dlp --simulate` every 60 seconds for up to 30 minutes. YouTube's `/live` URL for a channel always redirects to the current livestream if one exists, but returns nothing if the channel isn't streaming yet.
- **Direct mode** (`--direct`): The shell wrapper skips yt-dlp polling. Instead, `ai_reporter_live.py` probes the URL with a quick `ffmpeg` read attempt, retrying every 60 seconds for up to 30 minutes. This is needed for HLS URLs (Swagit, etc.) that yt-dlp doesn't understand.

## Scheduling live recordings with `at`

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

## Live stream URLs by municipality

| Municipality | Platform | Live URL | Mode |
|---|---|---|---|
| Pima County BOS | YouTube | `https://www.youtube.com/@PimaCountyArizona/live` | streamlink (default) |
| City of Tucson | YouTube | `https://www.youtube.com/user/CityofTucson/live` | streamlink (default) |
| Oro Valley | Swagit (HLS) | `https://stream.swagit.com/live-edge/orovalleyaz/smil:hd-16x9-1-a/playlist.m3u8` | `--direct` |
| Marana | Swagit (HLS) | `https://edge-f.swagit.com/live/maranaaz/live-1-a/playlist.m3u8` | `--direct` |

Pima County and Tucson stream on YouTube (use default streamlink mode). Oro Valley and Marana stream on Swagit, which serves HLS `.m3u8` streams — use `--direct` mode to have ffmpeg read the URL directly, bypassing streamlink. Swagit's streaming infrastructure uses Video.js + HLS.js on the frontend, backed by `stream.swagit.com` CDN.

**Marana stream URL verified 2026-05-19.** The live URL is `https://edge-f.swagit.com/live/maranaaz/live-1-a/playlist.m3u8` — captured via devtools (Network → `.m3u8` filter) on `www.maranaaz.gov/Council/Public-Meeting-Videos` during the May 19 Town Council broadcast. The previous inferred URL (`stream.swagit.com/live-edge/maranaaz/smil:hd-16x9-1-a/playlist.m3u8`, copied from the Oro Valley pattern) was wrong on three dimensions: different host (`edge-f` vs `stream`), different path segment (`/live/` vs `/live-edge/`), and different stream slug (`live-1-a` vs `smil:hd-16x9-1-a`). The inferred URL had failed live capture twice (most recently 2026-05-05, ffmpeg retried for 30 min and got nothing). Lesson: Swagit's URL conventions vary per municipality — do not infer; always verify via devtools during a real broadcast before scheduling.

## Auto-scheduling from agenda mining (built April 2026)

`check_agendas.sh` calls `schedule_recording.py` after each new preview is published. The scheduler:

1. Reads the `{slug}-full.md` reference file produced by the miner.
2. Asks Claude Sonnet for a structured JSON extraction of `public_session_start` — deliberately distinguishing it from any executive session that might precede it (e.g., Oro Valley's "Regular Session at or after 5:00 PM" [executive] vs "Resume Regular Session at or after 6:00 PM" [public]). Returns `confidence: high|medium|low` with one-sentence reasoning.
3. Looks up the stream URL + mode from a hardcoded `STREAM_SOURCES` dict (YouTube/streamlink for Pima + Tucson, Swagit/`--direct` for Oro Valley + Marana).
4. Schedules an `at` job for `max(now+2min, public_session_start - 5min)` — 5-min lead absorbs minor meeting slop, the `now+2min` floor handles same-day discovery (e.g., agenda posted at 8 AM for a 9 AM BOS meeting).
5. Persists state to `agenda-watch/.scheduled.json` (gitignored) keyed by slug. On the next run, matching public-session times are no-ops; different times trigger `atrm` + re-schedule.
6. Sends a Telegram notification with the meeting time, `at` job id, confidence level, and the LLM's reasoning notes. Low-confidence extractions are tagged "please verify".

**Enable flag:** The scheduling call in `check_agendas.sh` is gated by `ENABLE_AUTO_SCHEDULE=1`. **This is enabled in the 8 AM cron line as of April 24, 2026** — the crontab prefixes the command with `ENABLE_AUTO_SCHEDULE=1`. To temporarily disable, either `crontab -e` and remove the prefix, or unset the env var in an ad-hoc run. Backup of the pre-change crontab lives at `~/.cache/crontab/crontab.bak`.

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

## Live pipeline details

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

## VOD pipeline (built 2026-05-10)

- `ai_reporter_vod.py` — ffmpeg extracts audio from any URL or local file → opus at 24 kbps mono 16 kHz → Deepgram pre-recorded API (`POST /v1/listen`) with `model=nova-2&diarize=true&utterances=true&smart_format=true&punctuate=true&language=en-US` → utterances mapped into the standard transcript JSON schema → exec `ai_reporter.py` for the Sonnet draft.
- Why batch vs. live for VOD: Deepgram's live WebSocket expects ~1× real-time audio; ffmpeg pulls HLS VODs much faster and triggers a 1011 keepalive timeout. Batch API ingests at its own pace.
- Cost: ~$0.0043/min (~$0.31 for a 72-minute meeting via the pre-recorded endpoint, well under the live pipeline's $1.38 for a 3-hour meeting because there's no streaming overhead).
- Wall clock: ~5–10 minutes total for a 72-min meeting (ffmpeg HLS pull is the bottleneck; Deepgram batch returns much faster than real-time).
- First production use: Marana May 5 Town Council Regular Meeting, transcribed via VOD on 2026-05-10 after live capture failed. 1,095 utterances, 16 diarized speakers, clean draft.
- Marana/OV Swagit auto-transcripts (available 1–3 business days after a meeting at `maranaaz.new.swagit.com/videos/{id}/transcript`) remain a viable alternative when human-quality captions are preferable to Deepgram's batch output — but our pipeline doesn't ingest them yet.

## STT provider research (March 2026)

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
