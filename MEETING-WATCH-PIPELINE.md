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

## Silence is ambiguous — the staleness check (added 2026-08-03)

**The failure mode:** a scraper that stops finding meetings looks exactly like a governing body that has stopped meeting. Both are silence, and nothing in the pipeline distinguished them. Oro Valley went seven weeks with no preview and nothing flagged it; it turned out to be a genuine recess, but only a hand check proved that.

`check_meeting_staleness.py` runs at the end of `check_agendas.sh` and splits the two cases:

1. **How long since we published?** — newest dated file in `meeting-watch/<key>-*.html`. Previews are forward-looking, so a *future* date means we're ahead, not behind.
2. **If stale, is the source alive?** — re-query the miner's own `get_meetings_for_month()` for the last three months and count rows of *any* type.

| result | level | meaning |
|---|---|---|
| not stale | ✅ | fine |
| stale, source returns rows, 0 council | 🟡 | recess — noted, not alarming |
| stale, source returns **nothing** | 🚨 | probable scraper break |
| stale, source lists council meetings we never published | 🚨 | type-filter bug |
| stale, no prober available (Pima, Tucson) | ⚠️ | check by hand |

Thresholds live in `MUNICIPALITIES`. **Oro Valley's is the widest (70d) because it takes a real July recess every year** — in 2025 the June 18 → August 13 gap alone ran 56 days. Pima/Tucson have no prober because their sources aren't month-listing scrapes (Legistar API, OnBase PDFs); they degrade to ⚠️.

The check never publishes. `--date YYYY-MM-DD` simulates another day, `--force-telegram` sends regardless — both for testing.

## Meeting-type filters: prefix, don't enumerate (fixed 2026-08-03)

`agenda_mining_orovalley.py` gated `is_council` on a fixed list of type strings. Destiny's actual strings vary more than the list anticipated, so **9 real Town Council meetings were silently dropped between 2024 and 2026**:

| date | Destiny type |
|---|---|
| 2024-05-08, 2024-05-09 | Town Council Budget Study Session |
| 2025-04-30 | Town Council Study and Special  Session |
| 2025-05-05 | Town Council Budget Study Session |
| 2025-05-07 | Town Council Regular and Study  Session |
| 2026-01-21, 2026-03-02 | Town Council Retreat |
| 2026-04-22 | Town Council Regular and Study  Session |
| 2026-05-04 | Town Council Budget Study Session |

Note the **double space** in "Regular and Study  Session" — the strings aren't normalized upstream, which is exactly why enumerating them fails. Budget study sessions are where the town's spending is actually set, so this was real lost coverage.

**Fix:** `is_council` is now a prefix test (`type.startswith("town council")`) minus a small `NON_COUNCIL_MARKERS` exclusion list, rather than an allowlist of full type strings.

Two bugs compounded it, both in the same row parse:
- The type regex required the cell text to end in `Meeting|Board|Session|Commission|…` matched over a character class that **excluded `;`**, so any entity-bearing type (`Planning &amp; Zoning Commission`) failed and fell through to `"Unknown"` — and `Unknown` is silently non-council. It now takes the next `<td>` whole and `html.unescape()`s it. This alone took the `Unknown` count from as high as 12 rows in a month to **zero across all 36 months** of 2024–2026.
- Import `from html import unescape`, **not** `import html` — `get_meetings_for_month` has a local variable named `html` that shadows the module.

**Marana and Tucson still use the old enumerate-the-types pattern** (`COUNCIL_MEETING_TYPES` in `agenda_mining_marana.py:37` and `agenda_mining_tucson.py:38`).

### Routine study sessions are deliberately NOT covered (editorial call, 2026-08-03)

Auditing the filters turned up that Marana drops `Council-Study Session` (4 meetings) and **Tucson drops every single study session** — each Tucson meeting day is a study session in the afternoon and a regular meeting that evening, and only the regular one was ever previewed:

```
DROPPED  2026-08-05 13:30  Mayor & Council - Study Session
COVERED  2026-08-05 17:30  Mayor & Council - Regular
```

**The user's call is to leave these dropped: a recurring procedural sub-meeting is too granular for a news publication.** Don't "fix" this later mistaking it for the same bug as the Oro Valley one — it's a deliberate scope boundary. Volume is the distinction:

| | per year | covered? |
|---|---:|---|
| Tucson study sessions | ~24 | ❌ too granular |
| Marana `Council-Study Session` | ~2 | ❌ same rationale |
| OV Budget Study Session | ~1 | ✅ sets the town budget |
| OV Retreat | ~1–2 | ✅ sets council priorities |
| OV "Regular **and** Study Session" | ~1 | ✅ it *is* a regular meeting |

Pima County has no allowlist at all (it processes every BOS event from Legistar), which is why `news-reports/pima-county-*-study-session.html` exist — those predate this boundary.

**Still open:** Marana carries a large `Unknown` type bucket (38 rows across 2024–2026). Study sessions aside, the open question is whether any *regular or special* council meeting is hiding in there — an unparsed type is silently non-council. Unresolved as of 2026-08-03 because destinyhosted.com rate-limited us mid-audit (see below).

### Don't sweep destinyhosted.com

Auditing three years × 12 months across two municipalities is ~70+ requests and **will get you rate-limited** — the host starts refusing connections outright (`Errno 111`), for *all* Destiny municipalities at once, not just the one you were querying. It recovers in minutes but re-blocks immediately on a fresh burst, so it's adaptive rather than a fixed window. If you need a historical sweep: throttle hard (several seconds between requests), cache the HTML to disk on first fetch, and never run it close to the 8:00 AM `check_agendas.sh` window. Both Destiny miners are wrapped in `|| record_failure`, so a block degrades to a Telegram failure report rather than aborting the run — but that's a safety net, not a licence.

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

**Short-agenda guard — `meeting_context_block()` (added 2026-07-31).** The sibling of the canceled-meeting bug, and the same root cause: an editorial judgment handed to a model that the code already had the facts to make.

The 2026-08-03 Pima meeting was a **special meeting lawfully carrying one item** — the A.R.S. §16-642(A) canvass certifying the July 21 primary. The miner mined it correctly. The model then read one item as evidence of a *failed fetch* and wrote:

> ⚠️ **Reporter's Note:** Only one agenda item was provided for this analysis… if you have the complete agenda, paste the remaining items for full coverage.

plus a closing "*To generate a complete meeting preview with 5–8 newsworthy items, please paste the full agenda*", and a lede calling the agenda "notably slim" and "largely procedural" — about the meeting that makes an election official. **Previews auto-publish with no human review, so operator-addressed text goes straight to readers.** It only missed the live site because the machine crashed before the push.

**Why it happened: every miner already knew the meeting type and never told the model.** Legistar's `EventComment` (`"Special Meeting"`) and the scraped labels in the other three were passed to `generate_preview()`/`generate_full_report()` — i.e. into the *rendered page* — but never into the *prompt*. The model was left to infer from item count alone why an agenda was short. All four miners had this; **Marana, Oro Valley and Tucson accepted a `meeting_type`/`meeting_name` argument and used it only for output**, which is exactly the kind of near-miss that reads as wired-up on a skim.

`meeting_context_block(meeting_type, counts=None)` in `agenda_mining.py` now prepends derived facts to all five prompts (`counts` is `(substantive, discussion, consent)` for Pima, which has structured items; the scrape-based miners pass the type only). It states the meeting type as fact, states that the agenda is complete rather than an excerpt, and forbids the specific inferences — no "appears incomplete", no "slim"/"procedural" on item count alone, **no addressing the operator**, and no padding to reach a target count. Each miner's "identify the N most newsworthy items" also became "identify **up to** the N most", since a fixed target on a one-item agenda is itself an invitation to pad.

Verified end-to-end against the real 8/3 agenda: the model now opens "a special meeting called for a single, legally required purpose" and notes that the lone item "is among the most consequential actions the Board takes all year." Its factual claims checked out too (it cited two posted attachments, one dated 7/30 — both real).

**The generalizable rule:** when the pipeline knows something, tell the model rather than letting it infer. A short agenda, a canceled meeting, a source that failed to fetch — each is a fact the code holds and the model will otherwise guess at, plausibly and wrongly. Same lesson as the officials-watch silent/unchecked split. See `feedback_verify_dont_delegate`.

**Two renderer bugs in `preview_md_to_html` (fixed 2026-07-15, commit `0ce0b2c`).** Both were live site-wide:
- **Markdown links were never converted.** Every preview published its own source attribution as dead text — `Source: [Town of Marana Agendas](https://destinyhosted.com/...)` rendered literally on all 39 pages, so the provenance link never worked. `_inline_format` now converts links, and the standalone-italic branch (which the footer takes) routes through it instead of bare-escaping. Scheme pinned to `http(s)`; the substitution runs *after* `escape_html`, so `&` and `"` in the URL are already entity-safe.
- **`### **Headline**` published its asterisks.** Headings were escaped but not inline-formatted. `_heading_text()` unwraps a fully-bolded heading (headings render bold already) and formats the rest.

Republishing every preview from its existing markdown is safe and free — it's deterministic md→HTML with no API calls, and the 2026-07-11 SEO retrofit survives regeneration (verified). That's the way to push a renderer fix to already-published pages.

### Spotted: the Marana DLLC route (added 2026-07-28)

Spotted's agenda route (`public_record_liquor.py`) can never see Marana — the town approves liquor licenses administratively, nothing reaches a council agenda, and the clerk's site publishes no application list (checked 2026-07-28; the clerk pages are process-info only, and maranaaz.gov 403s non-browser fetchers anyway). Marana coverage instead comes from `public_record_liquor_dllc.py`, which polls the **state DLLC public license database** (`dllc.azliquor.gov`, POSSE/Computronix, no auth) daily from `check_agendas.sh`:

- **Enumeration trick:** the search's Premises field matches business *names* only, but License Number is a *prefix* match and AZ license numbers encode series + county (`10` = Pima). Two prefix queries per consumer-facing series (legacy `0610` + modern `00610` formats) enumerate every Pima license of that series (~1,700 rows across 11 series). Rows come back as clean structured spans; filter to premises addresses containing `MARANA, AZ`, diff license numbers against `public-record/.dllc_state_marana.json` (gitignored), publish newly appearing **Active** licenses. **Zero AI calls** — every published field is a state database record. Protocol details (the POSSE `datachanges` tuple POST) are in the module docstring.
- **First run seeds silently** (53 Marana licenses at seed time, including a liquor store licensed in 1961) — republishing history as "news" is the failure mode. `--seed` re-seeds deliberately; a result set under 100 licenses is treated as a source failure and leaves state untouched, so a DLLC outage or layout change can't wipe the baseline and cause a republish flood.
- **Known limitations:** DLLC's premises city is the *mailing* city, so Marana-limits businesses with Tucson mailing addresses (e.g. Casa Marana Craft Beer, `TUCSON, AZ 85741`) are missed — deliberate under-match. This route also surfaces licenses at *issuance*, not application; the forward-looking version (pending applications) died with DLLC's 2025-ish site migration and now requires a clerk relationship (records request / standing weekly list — in progress).

### `check_agendas.sh` failure modes (all three found 2026-08-01)

**1. A `499 Token Required` from ArcGIS usually means the layer is *gone*, not secured.** Marana unpublished `DS_Current_Projects_Live`; ArcGIS returns 499 for an absent service exactly as it does for a protected one, so the error reads like an auth change and sends you hunting for credentials. Diagnose by requesting the parent `/services/Hosted?f=json` directory — if that still answers unauthenticated (it did), access didn't change and the layer simply isn't listed anymore. The successor is `Hosted/DS_Current_Projects` (layer name `DS_Projects`), public, identical 11-field schema, **OBJECTID preserved** — which is what made the repoint safe, since `case_key()` is the bare objectid and renumbering would have re-published all 62 projects as new. Always diff the new layer's objectids against the saved state before repointing any of these pollers.

**2. `|| true` on the poller did not make the poller non-fatal.** Every stage is invoked as `OUT=$(python3 …) || true`, but the *next* line extracted a count:

```bash
DEV_COUNT_MA=$(echo "$DEV_OUTPUT_MA" | grep -oP 'Published/updated \K\d+' | tail -1)
```

Under `set -euo pipefail`, a failed poller's output has no match → `grep` exits 1 → `pipefail` propagates it out of the command substitution → `set -e` kills the run. So a *development-watch* failure silently killed *agenda publishing*: the previews had already been written and indexed, and the script died before `git push`, leaving published HTML uncommitted in the working tree. All four count extractions now carry `|| true` (the `:-0` fallbacks below them already handled the empty case). **The general trap: guarding a command does nothing if the line that parses its output is itself unguarded.**

**3. Failures were invisible by construction.** Every Telegram in the script fires inside an `if COUNT > 0` branch, so notifications only ever went out on *success* — a dead poller produced no signal at all, just a traceback in a log nobody reads. `record_failure()` now records each stage failure (same non-fatal contract) and an **EXIT trap** sends one consolidated alert naming every broken stage. The trap fires on all exit paths, so it also reports an unexpected `set -e` abort and warns that the push may not have run. Verified: clean run stays silent, single/multiple failures listed, hard abort reports its code.

**Structural quirk, not yet changed:** the script `exit 0`s early when no *new agenda preview* was generated — **before** Spotted, DLLC, and both dev-watch pollers run. So those four pollers only execute on days a new preview appears, not daily. Worth revisiting if development-watch latency ever matters.

### Key dependencies

- `pdftotext` (poppler-utils) — required for Tucson PDF extraction
- `at` + `atd` daemon — required for scheduled live recordings
- `ANTHROPIC_API_KEY` in `~/.config/environment.d/anthropic.conf`
- Telegram credentials for notifications

## Agenda documents move after the preview runs

**The 8 AM pass mines a meeting once and then never looks again.** `main()` used
to `continue` past any meeting whose `-preview.md` already existed, skipping the
full reference too. Agenda attachments are not static, so that guard quietly
froze our picture of a meeting at whatever staff had filed by the first run.

The case that exposed it: Pima's 2026-07-28 IDA item (Legistar matter 21643)
drew three documents — 7/15, 7/23 and **7/27**. The 7/27 memo revised the
proposed board slate, replacing two named appointees with two others, and landed
about 26 hours before the vote. Our preview went out on 7/23 describing the
superseded slate, and the post-meeting drafter never saw the revision, so the
appointee names had to be reconstructed from Deepgram audio. One came out wrong
("Kavanaugh" for Cavanaugh).

### Day-of refresh

`run_agenda_refresh.sh` (cron, 9:15 AM daily) runs `agenda_mining.py --refresh`:

- refreshes `<base>-full.md` and `<base>-attachments.md` for meetings **today**
- diffs the attachment manifest and Telegrams anything added or revised
- **never republishes the preview** — a revised memo is a heads-up for the
  human, not a trigger to silently rewrite a live page

The first refresh on a given meeting records a baseline and stays silent; alerts
begin on the second run.

Pima only. Marana, Oro Valley and Tucson are scraped rather than served by a
Legistar API, so they have no attachment feed to diff.

### `agenda_attachments.py` — two non-obvious rules

**Newest attachment first.** When staff files a revision, the later document
governs. Sorting by filing order buries it: on 7/28 the operative revision was
3,574 characters and the superseded version it replaced ran 18,440, so reading
in order would have spent the item's budget on the stale one.

**Every discussion item gets a guaranteed share of the character budget.**
Agendas are ordered by procedure, not importance — proclamations and zoning
hearings come first, the consequential business comes last. The first build
spent all 60,000 characters on items 6–14 and never reached the item 25 memos
that motivated the whole thing. Per-item allocation fixed it; the total budget
is now 120,000 characters, which still leaves the full drafter prompt near
60k tokens against a ~110,000-character transcript.

Digests and manifests are gitignored — regenerable, bulky, and
`check_agendas.sh` does a wholesale `git add agenda-watch/` that would otherwise
commit them into the public repo daily.

