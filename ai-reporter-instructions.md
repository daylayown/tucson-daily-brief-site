# AI Reporter — Quick Reference

## Record a live meeting or briefing

```bash
./run_live_reporter.sh "YOUTUBE_LIVE_URL" --slug tucson-council-2026-04-01
```

This transcribes the stream and automatically generates a news report draft when it stops.

## Transcribe only (no report)

```bash
./run_live_reporter.sh "YOUTUBE_LIVE_URL" --slug tucson-council-2026-04-01 --transcribe-only
```

## It stops automatically when:

- No one speaks for 5 minutes (meeting adjourned)
- The livestream ends
- 6 hours elapse (safety cap)
- You hit Ctrl+C

Override defaults with `--dead-air-timeout 600` (seconds) or `--max-duration 3600` (seconds).

## After it finishes

```bash
# Generate a report from a transcript
.venv/bin/python3 ai_reporter.py transcripts/tucson-council-2026-04-01.json

# Re-generate (if draft already exists)
.venv/bin/python3 ai_reporter.py transcripts/tucson-council-2026-04-01.json --force

# Approve a draft
.venv/bin/python3 ai_reporter.py --approve transcripts/tucson-council-2026-04-01-draft.md

# Publish an approved report
.venv/bin/python3 ai_reporter.py --publish transcripts/tucson-council-2026-04-01-approved.md
```

## File locations

| File | Location |
|---|---|
| Raw transcript | `transcripts/{slug}.json` |
| Partial (during recording) | `transcripts/{slug}-partial.json` |
| Draft report | `transcripts/{slug}-draft.md` |
| Approved report | `transcripts/{slug}-approved.md` |
| Published HTML | `news-reports/{slug}.html` |

## Slug naming convention

`{source}-{date}` — e.g., `tucson-council-2026-04-01`, `pima-bos-2026-04-08`, `wh-briefing-2026-03-28`
