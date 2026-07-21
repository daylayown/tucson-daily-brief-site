# k3 Data Plan — the TDB civic-transparency pipeline

*Drafted 2026-07-20, from the court/crime/PCAO research arc: `COURT-DATA-FEASIBILITY.md`, `powerbi.md`, `crime.md`, `crime-tpd-data.md`, `TUCSON-DATA-FEASIBILITY.md`. This is the program plan; per-source verification detail lives in those docs.*

## Core insight

Accountability doesn't come from any single story. It comes from **measuring the same thing, the same way, forever, in public.** Officials can spin a number; they can't spin a trend they know is being tracked. The PCAO saga proves the corollary: **a feed that stops working is itself the news.** A frozen dashboard, a zeroed series, a missing annual report — not absences of news, but findings. The pipeline must treat "what government publishes vs. what it doesn't" as a first-class metric.

## Architecture: pollers → snapshots → surfaces

No platform. The atomic unit is the existing `dev_watch_*.py` poll-and-diff pattern, cloned per source.

**Layer 1 — Collectors (deterministic, one per source).** Each poller: fetch → normalize → snapshot → diff. Headless-Chromium renderers for PowerBI (technique proven 2026-07-20, `powerbi.md` §4), ArcGIS REST for TPD, `pdftotext` for AOC/PCSD PDFs. **No LLM near the numbers** — LLMs draft prose and classify documents; deterministic code owns every count and rate (house rule: derive, don't ask).

**Layer 2 — Snapshot archive (the moat).** Every run stores dated, immutable snapshots (raw + parsed JSON). Twelve months in, TDB can say "when we started watching, X — today, Y" about jail population, clearance rates, PCAO funnel, feed health. Nobody else in Tucson keeps that archive. It compounds.

**Layer 3 — Surfaces, matched to risk:**
- **Telegram flags** (private, instant) — every change, every dead feed, every parse failure
- **Daily-brief chart lines + Around Town-style feeds** (aggregates; previews risk model — auto-publish)
- **One dashboard page** (aggregates only; only after 3+ feeds are flowing)
- **Human-reviewed In Depth stories** (the spikes flags surface; news-reports editorial model)

## Build sequence

Each item ≈ a day of work, ships something visible, de-risks the next.

| # | Build | Source status |
|---|---|---|
| 1 | **PCAO Watch** — weekly headless render of three PowerBI reports (NEW/OLD/ME), deterministic text parse, diff, Telegram flag | Technique proven 2026-07-20; baseline captured in `powerbi.md` |
| 2 | **Tucson Crime poller + Clearance Watch** — TPD `Tucson_Police_Reported_Crimes/FeatureServer/8` + `OpenData_PublicSafety/81`: monthly violent-category trends, ward splits, computable clearance rates (the 97.56%/57.45% gap, made computable) | Verified 2026-06-26, zero policy cloud |
| 3 | **ME homicide monitor + metro rollup** — ME dashboard (live) + TPD + PCSD + FBI CDE → one canonical monthly metro number, coroner as tiebreaker | ME verified live 2026-07-20 (updated 7/8) |
| 4 | **AOC Safe Communities annual poll + Safe City claims check** — FY PDF parse (Pima row + statewide context); city's 85%/25%/86% claims checked against incident + court layers | FY2024 parsed 2026-07-20 |
| 5 | **§ 1-605 bulk-data request** → court outcomes snapshot / PTR tracker / repeat-case share | Letter per `COURT-DATA-FEASIBILITY.md` §5; send now — long-lead, and the correspondence itself is content (granted or stonewalled, publish it) |

> **ME collector caveat (learned 2026-07-20, load-bearing):** the OME dashboard serves **six counties and defaults to all of them.** The collector must apply the **Pima filter every run**, read each value off the *rendered chart* (not the flattened `innerText`, which misaligns label↔value), and treat the coroner's series as a countywide **manner-of-death trend corroborator** — **never** a "tiebreaker" for city murder counts (it includes justifiable/officer-involved deaths; different metric, different geography). Skipping the filter reproduces the `137`-instead-of-`119` error. See `powerbi.md` §3 + §4.4.

**Parallel human actions this week:** send the § 1-605 request (addressed to both the Pima Superior Court custodian and the AOC Administrative Director; ask explicitly for birth month/year); send the PCAO PIO email (`pcao-pio-email.md`).

## The dashboard (earns its page after 3+ feeds flow)

Three zones:

1. **The numbers** — few, defined, sourced, dated. Crime trend, clearance rate, metro homicides, PCAO funnel, PTR volume. **Every metric carries its denominator next to it** (the 97.56%/57.45% lesson: no naked ratios).
2. **The Transparency Tracker** — a live feed-health table: "PCAO By the Numbers: frozen, day N. TPD NIBRS gap: 2021–2023. TFD: publishes nothing. Tucson Water: no KPI report. Check register: doesn't exist." Scores government's *disclosure*, never people (equity-score lesson).
3. **Methodology + freshness** — every number shows source, pull date, parser version. The PCAO lesson applied inward: TDB's dashboard must be honest about its own staleness. A feed that stops changing flags *our* infrastructure too.

## Accountability mechanics

1. **Consistency beats volume.** Same metric, same cadence, public history — that's what can't be spun.
2. **Flag-to-story pipeline.** Telegram spike → human verifies → In Depth piece. The downtown-shooting probation check (done by hand, 2026-07-20) is the prototype; pollers automate the flag, never the judgment.
3. **Documented asks.** Every records request and its response (or stonewall) is published. Asking on the record forces an answer or a visible non-answer.
4. **Publish boring.** Most monthly updates say "roughly unchanged." That credibility is what makes the one real spike land. Outrage machines get dismissed; measured ones get cited.

## Guardrails (load-bearing, not decorative)

- Aggregates by default; names only in human-reviewed stories tied to current charges of public concern.
- **No searchable name→history database, ever** (ARS § 13-911 sealing can't be honored by a permanent named DB; presumption of innocence).
- Official/legal data routes before scraping (Agave robots.txt disallows all spiders → § 1-605, not a crawler).
- Denominators labeled beside every rate; "repeat-case share" ≠ "recidivism rate"; charged ≠ convicted; AOC aggregate published beside ours for calibration.
- Blame assignment is a reporting question, not a data-feed question (probation non-revocation runs through Adult Probation + the court, not only PCAO).

## Failure modes to design against

- **Derive, don't ask** — every Spotted bug came from asking the model for something code should compute.
- **Silent schema changes kill feeds** → snapshot + alert on parse failure; silence is a flag, not a pass.
- **One person, ~$4/month** → no feed that needs ongoing heroics survives. If a source fights back twice, drop it and publish *why* (that's content too).
- **Don't build the dashboard before the pollers.** Page ships after 3+ feeds flow, not before.

## Where each thread lives

- PCAO PowerBI forensics + monitor design → `powerbi.md`
- Court/probation data, § 1-605, tiers, Agave mechanics → `COURT-DATA-FEASIBILITY.md`
- TPD incident/clearance data → `TUCSON-DATA-FEASIBILITY.md`
- NIBRS gap + TPD's own numbers → `crime.md`, `crime-tpd-data.md`
- "On Probation" story entry (active track) → `ORIGINAL-JOURNALISM.md`
- PIO outreach draft → `pcao-pio-email.md`; LLM cross-check prompt → `k3-pima-county.md`; original exploration prompt → `court-data-journalism-llm-prompt.md`
