# Meeting Watch Pipeline

AI-assisted agenda previews for local government meetings in the Tucson metro area.

## Covered Bodies

| Body | Data Source | Script | Status |
|------|------------|--------|--------|
| Pima County BOS | Legistar API (free, no auth) | `agenda_mining.py` | Live |
| Marana Town Council | Destiny Hosted (HTML scraping) | `agenda_mining_marana.py` | Live |
| Oro Valley Town Council | Destiny Hosted (HTML scraping, via Granicus) | `agenda_mining_orovalley.py` | Live |
| City of Tucson Mayor & Council | Hyland OnBase (PDF download + pdftotext) | `agenda_mining_tucson.py` | Live |

## How It Works

### Fully Automated (runs daily via cron — zero human intervention)

```
8:00 AM MST — check_agendas.sh
  │
  ├─ Pima County BOS (agenda_mining.py)
  │    ├─ Queries Legistar API for upcoming meetings (next 30 days)
  │    ├─ No new agenda? → skips
  │    └─ New agenda found? →
  │         ├─ Fetches all agenda items via Legistar API
  │         ├─ Filters out ~70 procedural items, keeps substantive ones
  │         ├─ Sends substantive items to Claude Sonnet 4.6 for editorial analysis
  │         └─ Saves preview + full reference markdown
  │
  ├─ Marana Town Council (agenda_mining_marana.py)
  │    ├─ Scrapes Destiny Hosted for upcoming council meetings
  │    ├─ No new agenda? → skips
  │    └─ New agenda found? →
  │         ├─ Fetches agenda content from Destiny Hosted
  │         ├─ Sends agenda content to Claude Sonnet 4.6 for editorial analysis
  │         └─ Saves preview + full reference markdown
  │
  ├─ Oro Valley Town Council (agenda_mining_orovalley.py)
  │    ├─ Scrapes Destiny Hosted (id=67682) for upcoming council meetings
  │    ├─ No new agenda? → skips
  │    └─ New agenda found? → same flow as Marana
  │
  ├─ City of Tucson Mayor & Council (agenda_mining_tucson.py)
  │    ├─ Queries Hyland OnBase for meetings with posted agendas
  │    ├─ No new agenda? → skips
  │    └─ New agenda found? →
  │         ├─ Downloads agenda PDF via OnBase ViewDocument endpoint
  │         ├─ Extracts text with pdftotext, strips boilerplate
  │         ├─ Sends to Claude Sonnet 4.6 for editorial analysis
  │         └─ Saves preview + full reference markdown
  │
  ├─ Auto-publish: converts each new preview to HTML (--publish)
  ├─ Git commit & push to GitHub Pages
  └─ Telegram notification: "Preview published for [date]"
```

Agenda previews are forward-looking summaries of what's on the agenda — they publish automatically. Post-meeting news reports (future feature) will require human editorial review.

## Commands Reference

### Pima County BOS

```bash
# List upcoming meetings
python3 agenda_mining.py --list

# Generate preview + full reference for all upcoming meetings
python3 agenda_mining.py

# Generate for a specific meeting (by Legistar event ID)
python3 agenda_mining.py --event-id 1797

# Generate without Claude analysis (no API cost)
python3 agenda_mining.py --event-id 1797 --no-llm

# Publish a reviewed preview to the site as HTML
python3 agenda_mining.py --publish agenda-watch/pima-county-YYYY-MM-DD-preview.md
```

### Marana Town Council

```bash
# List upcoming council meetings
python3 agenda_mining_marana.py --list

# Generate preview for all upcoming council meetings
python3 agenda_mining_marana.py

# Generate for a specific meeting (by Destiny seq number)
python3 agenda_mining_marana.py --seq 3162

# List all meeting types (not just council)
python3 agenda_mining_marana.py --list --all-types

# Filter by month/year
python3 agenda_mining_marana.py --list --month 3 --year 2026

# Generate without Claude analysis (no API cost)
python3 agenda_mining_marana.py --seq 3162 --no-llm

# Publish a reviewed preview to the site as HTML
python3 agenda_mining_marana.py --publish agenda-watch/marana-YYYY-MM-DD-preview.md
```

### Oro Valley Town Council

```bash
# List upcoming council meetings
python3 agenda_mining_orovalley.py --list

# Generate preview for all upcoming council meetings
python3 agenda_mining_orovalley.py

# Generate for a specific meeting (by Destiny seq number)
python3 agenda_mining_orovalley.py --seq 1124

# List all meeting types (not just council)
python3 agenda_mining_orovalley.py --list --all-types

# Generate without Claude analysis (no API cost)
python3 agenda_mining_orovalley.py --seq 1124 --no-llm

# Publish a reviewed preview to the site as HTML
python3 agenda_mining_orovalley.py --publish agenda-watch/orovalley-YYYY-MM-DD-preview.md
```

### City of Tucson Mayor & Council

```bash
# List meetings (all types from OnBase)
python3 agenda_mining_tucson.py --list

# Generate preview for upcoming council meetings
python3 agenda_mining_tucson.py

# Generate for a specific meeting (by OnBase meeting ID)
python3 agenda_mining_tucson.py --meeting-id 1917

# List all meeting types (not just regular/special council)
python3 agenda_mining_tucson.py --list --all-types

# Generate without Claude analysis (no API cost)
python3 agenda_mining_tucson.py --meeting-id 1917 --no-llm

# Publish a reviewed preview to the site as HTML
python3 agenda_mining_tucson.py --publish agenda-watch/tucson-YYYY-MM-DD-preview.md
```

### General

```bash
# Manually run the daily check (all four municipalities)
~/claude-code-projects/tucson-daily-brief-site/check_agendas.sh

# Check the log
cat /tmp/agenda-check.log
```

## Cron Schedule

```
0 8 * * * ~/claude-code-projects/tucson-daily-brief-site/check_agendas.sh >> /tmp/agenda-check.log 2>&1
```

## File Layout

```
agenda-watch/                          # Working directory (not published)
  pima-county-YYYY-MM-DD-preview.md    # Publishable editorial preview
  pima-county-YYYY-MM-DD-full.md       # Full itemized agenda (your reference)
  marana-YYYY-MM-DD-preview.md
  marana-YYYY-MM-DD-full.md
  orovalley-YYYY-MM-DD-preview.md
  orovalley-YYYY-MM-DD-full.md
  tucson-YYYY-MM-DD-preview.md
  tucson-YYYY-MM-DD-full.md

meeting-watch/                         # Published HTML (on GitHub Pages)
  pima-county-bos-YYYY-MM-DD.html
  marana-council-YYYY-MM-DD.html
  orovalley-council-YYYY-MM-DD.html
  tucson-council-YYYY-MM-DD.html

meeting-watch.html                     # Meeting Watch index page
```

## Meeting Schedules

- **Pima County BOS**: 1st and 3rd Tuesdays of each month. Agendas posted ~1 week before.
- **Marana Town Council**: 1st and 3rd Tuesdays of each month (regular meetings).
- **Oro Valley Town Council**: 1st and 3rd Wednesdays of each month (regular sessions).
- **City of Tucson Mayor & Council**: 1st and 3rd Tuesdays of each month (regular meetings). Study sessions same days, earlier.

## Dependencies

- **Legistar API**: `webapi.legistar.com/v1/pima` — no auth required
- **Destiny Hosted (Marana)**: `destinyhosted.com/agenda_publish.cfm?id=62726` — HTML scraping, no auth
- **Destiny Hosted (Oro Valley)**: `destinyhosted.com/agenda_publish.cfm?id=67682` — HTML scraping, no auth
- **Hyland OnBase (Tucson)**: `tucsonaz.hylandcloud.com/221agendaonline` — PDF download, no auth
- **pdftotext**: System dependency (poppler-utils) for extracting text from Tucson PDFs
- **Claude API**: `ANTHROPIC_API_KEY` in `~/.config/environment.d/anthropic.conf`
- **Telegram**: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `~/.config/environment.d/telegram.conf`
- **send_telegram.py**: `~/.openclaw/skills/tucson-daily-brief/scripts/send_telegram.py`


---

# Operational detail (moved from CLAUDE.md 2026-07-17)

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

**Slug routing in `check_agendas.sh`:** The cron wrapper determines which publish script to use by matching the preview filename against municipality keywords (`marana`, `orovalley`, `tucson`, else Pima County). **Critical:** this matching is done on `basename` only, not the full path — the repo directory name (`tucson-daily-brief-site`) contains "tucson" and would falsely match every preview against the Tucson check. This was a bug fixed April 2026 that caused Pima County previews to be published with `tucson-council-` slugs. **Two artifacts of that bug are still live and are staying that way** (user's call 2026-07-15): `meeting-watch/tucson-council-2026-03-24.html` and `tucson-council-2026-03-27.html` are Pima County BOS previews sitting at Tucson URLs. Content is correct, only the slug is wrong. Don't "fix" them by republishing the matching `pima-county-*-preview.md` — that mints a correctly-slugged twin and leaves *both* in the sitemap as duplicate content (nearly happened 2026-07-15). Fixing properly means deleting live URLs or leaving meta-refresh stubs; not worth it for two old pages.

**Canceled-meeting guard (added 2026-07-15, commit `9f03cc3`).** Before the guard, a canceled meeting got the full editorial treatment: the 2026-07-21 Marana meeting was canceled and the pipeline published a complete preview about it — headline, "Reporter's Note", follow-up questions to pursue — which then sat on the homepage as the latest meeting preview. Ask a model to preview a meeting with no agenda and it will manufacture significance. Three meetings got this treatment (`marana-2026-07-07`, `marana-2026-07-21`, `tucson-2026-07-07`).

- `is_canceled_meeting(meeting_label, agenda_text)` in `agenda_mining.py`, imported by all four miners and called immediately before `analyze_with_claude`. **It must check both the label and the body, because the portals disagree on where they say it:** Marana and Oro Valley put it in the meeting label ("Council Regular Meeting - CANCELED"), but **Tucson's label still reads "Mayor & Council - Regular"** and buries the notice in the PDF body ("Due to an anticipated lack of quorum, the ... meetings of JULY 7, 2026, are CANCELLED"). A label-only check misses every Tucson cancellation. The body check requires the cancel word *near* "meeting"/"session" and only within the first 40 lines, so an agenda that cancels a contract 200 lines down doesn't trip it. Fires on exactly 3 of 44 agendas, zero false positives.
- Canceled meetings skip the Claude call entirely and get `canceled_analysis_md()` — a flat statement of fact. Published rather than skipped, because "is there a meeting Tuesday?" is a real reader question.
- `generate_preview(..., canceled=False)` in all four miners takes the flag and swaps **both** the title ("Meeting Canceled", not "What to Watch") **and the disclosure**. The default footer credits `CLAUDE_MODEL`, which would be a false disclosure on text no model wrote.

**Two renderer bugs in `preview_md_to_html` (fixed 2026-07-15, commit `0ce0b2c`).** Both were live site-wide:
- **Markdown links were never converted.** Every preview published its own source attribution as dead text — `Source: [Town of Marana Agendas](https://destinyhosted.com/...)` rendered literally on all 39 pages, so the provenance link never worked. `_inline_format` now converts links, and the standalone-italic branch (which the footer takes) routes through it instead of bare-escaping. Scheme pinned to `http(s)`; the substitution runs *after* `escape_html`, so `&` and `"` in the URL are already entity-safe.
- **`### **Headline**` published its asterisks.** Headings were escaped but not inline-formatted. `_heading_text()` unwraps a fully-bolded heading (headings render bold already) and formats the rest.

Republishing every preview from its existing markdown is safe and free — it's deterministic md→HTML with no API calls, and the 2026-07-11 SEO retrofit survives regeneration (verified). That's the way to push a renderer fix to already-published pages.

### Key dependencies

- `pdftotext` (poppler-utils) — required for Tucson PDF extraction
- `at` + `atd` daemon — required for scheduled live recordings
- `ANTHROPIC_API_KEY` in `~/.config/environment.d/anthropic.conf`
- Telegram credentials for notifications
