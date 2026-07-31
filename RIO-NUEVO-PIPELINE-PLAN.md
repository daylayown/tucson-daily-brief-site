# Rio Nuevo data pipeline — build plan

**Status: GREENLIT 2026-07-21** (user's call). Build **next session**. Emerged from the Empire/Rio Nuevo
investigation (`rio-nuevo-investigation/`); feeds the civic-transparency apparatus
(`k3-data-plan.md`). Don't let it balloon past these three tiers.

## Why Rio Nuevo is an unusually good automation target

It's a state-chartered downtown TIF district (9-member board appointed by state politicians) —
the **5th body** alongside the 4 municipal councils, but structurally different: its records
live on **rionuevo.org**, not Legistar/Destiny/OnBase. The killer enabler: **Rio Nuevo posts
verbatim court-reporter transcripts of every board meeting** ("4PP" PDFs, Min-U-Script / Fink &
Associates). So for post-meeting reports we **skip Deepgram/streamlink entirely** — feed the
official transcript straight to Claude. Cheaper and more accurate than our own STT.

## Technical groundwork (discovered + verified 2026-07-21 — reuse this, don't re-derive)

- **Agendas index (the crawl seed):** `https://rionuevo.org/board/agendas/` lists every meeting
  (Board Meetings + Study Sessions) with agenda-PDF URLs. Agenda URLs encode the date
  (`YYYY-MM-DD`). This is how you enumerate meetings.
- **Transcript URL pattern:**
  `https://rionuevo.org/wp-content/uploads/{YYYY}/{MM}/{MMDDYY}-Rio-Nuevo_4PP.pdf`
  - filename = **meeting date** as `MMDDYY` (e.g. `062425` = June 24, 2025)
  - folder `{YYYY}/{MM}` = **upload month**, usually **meeting month + 1** (transcript lags the
    meeting ~1 month). When harvesting, try offsets **+1, then +0, then +2** and check for a
    valid `%PDF` header. (Working harvest loop was in scratch `rn_transcripts/` this session —
    ephemeral, but the logic: bash loop over meetings, curl -sfL with browser UA, verify magic
    bytes, `pdftotext -layout`, grep.)
  - The **most recent ~4–6 weeks of meetings won't have a transcript posted yet** — expected.
- **Extraction:** these are **text PDFs, not scans** — `pdftotext -layout` gives clean,
  greppable output. (`chromium`/`convert` present on this box; `pdftotext` from poppler already
  a pipeline dep.)
- **Cadence:** board meets ~2×/month — a **Board Meeting** (substantive, votes) + a **Study
  Session**. The Board Meetings are the ones worth reporting.
- **Sanity-check corpus already read this session:** Jan 28 2025 (Empire approval), June 24
  2025 (budget), Feb 24 2026 — all parsed fine.

## The three tiers

1. **What to Watch (agenda previews)** — `agenda_mining_rionuevo.py`, cloned from the pattern of
   the 4 municipal miners: poll the agendas page → new agenda PDF → `pdftotext` → one Claude
   "what to watch" summary → auto-publish under the Local Government hub. **Auto-publish is fine**
   here (forward-looking agenda summary, per the editorial model). Easiest; do first.
2. **What They Decided (post-meeting reports)** — the transcript-fed path. Fetch the published
   4PP transcript → `pdftotext` → Claude drafts a report → **human review** → publish. Reuse
   `ai_reporter.py` but add a **"published-transcript" mode** that bypasses Deepgram/streamlink
   (`ai_reporter_live.py` / `ai_reporter_vod.py` not needed for Rio Nuevo). Human-reviewed, per
   the editorial model (post-meeting reporting is never full-auto).
3. **Grants-accountability ledger (the differentiated layer)** — mine transcripts + the AZ
   Auditor General project ledger (in `rio-nuevo-investigation/`) into a structured "Rio Nuevo
   money" dataset: recipient · amount **approved** · amount **actually disbursed** ·
   promised-vs-delivered · the new **80%-sales-tax-rule** compliance. Approved ≠ paid is the
   core editorial distinction — track both columns from day one, never conflate them. This is
   the accountability spine no other outlet has. Do last; highest value.

## Evidence discipline (adopted 2026-07-23, from next-gen-tdb.md)

The failure mode to design against is the compounding-source chain: transcript → AI report →
AI extractor → output, where each model pass reinterprets the previous one's prose. Rules:

- **Every ledger row carries an exact primary-source pointer:** source document (transcript
  PDF, agenda packet, Auditor General ledger), page number — the 4PP court transcripts have
  real page/line numbers, use them — and the **verbatim quoted span** the fact came from.
- **Extraction targets the primary document, never our own published prose.** A Tier-3 fact
  is mined from the transcript/ledger PDF directly, not from a What They Decided report.
- **Rows have a status:** machine-extracted → human-confirmed (or contradicted/superseded).
  Only human-confirmed rows feed published prose. Prose is generated *from* the ledger;
  the ledger is never back-filled *from* prose.
- **Deterministic validation before anything publishes:** quoted spans must appear verbatim
  in the cited source (programmatic string check), amounts must sum, dates must parse.

## Fit with existing infra

- Import shared chrome from `generate_post.py` (nav, footer, SEO helpers, topic flags) like
  every other renderer; nested-page footer prefix + `page_slug` kwarg.
- Routing/slugs mirror `meeting-watch` (What to Watch) and `news-reports` (What They Decided).
- Add the miner to `check_agendas.sh` (8 AM cron) once Tier 1 is proven.
- Ties to `MEETING-WATCH-PIPELINE.md` (the 4-miner architecture) and `AI-REPORTER.md`
  (transcript→report flow) — read both before building.

## Suggested build order

Tier 1 (agenda miner — matches an existing, proven pattern) → a **one-off Tier-2 report** on a
recent Board Meeting as a transcript-fed proof-of-concept (human-reviewed) → Tier 3 ledger.
Start next session with Tier 1 or the Tier-2 one-off, whichever the user prefers.
