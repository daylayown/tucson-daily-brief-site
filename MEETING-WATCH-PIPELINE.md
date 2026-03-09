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
