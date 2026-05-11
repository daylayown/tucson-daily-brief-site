# Tucson Responsiveness Index — Planning Doc

> **Status:** Researched 2026-05-10. Not yet building. Pick up here when ready.
>
> **Companion memory:** `project_responsiveness_index.md` (key decisions, M1 scope).
>
> This doc is the canonical reference for everything decided about this project so far. It exists so a future session — yours or mine — can resume cold without re-doing the research and the strategic conversations.

---

## The pitch (one paragraph)

A living website at `tucsondailybrief.com/responsiveness/` (working title — name TBD, see "Open decisions" below) that reframes Tucson's civic infrastructure through three lenses no one else combines: **how the city responds** to resident-reported problems, **what the city publishes** versus what it doesn't, and **how the desert** makes both of those questions structurally different than they'd be in any other US metro. Inaugural framing: *"Before we measure how fast Tucson responds, we have to measure what Tucson tells us."* The transparency story leads; the responsiveness numbers follow; the desert lens (TEP outages, Tucson Water advisories, heat-connected 311) makes the project distinctly local.

This is TDB's evolution from aggregation to **original reporting**. The daily brief was the MVP. This is the bigger product.

---

## What's new about this (vs. existing TDB pillars)

- **Daily Brief** — repackages existing journalism. Aggregation.
- **Meeting Watch** — AI-assisted previews of agendas. Automated, not original-source.
- **News Reports** — AI-drafted, human-reviewed coverage of meetings. Original but episodic.
- **Public Record** — surfaces filings already buried in agendas. Reporting layer over existing data.
- **Responsiveness Index** — *original journalism using data nobody else publishes or surfaces.* The first TDB product whose value comes from accumulating its own time-series archive over months and years.

That accumulation is the moat. Six months from now, TDB will own the only comprehensive historical archive of TEP outages, the only systematic record of Tucson Water advisories, and the only ward-tagged closure-time history of Tucson 311. None of that exists in any usable form today.

---

## The umbrella deliverable

A **living website** — not a weekly PDF — built around four publishable surfaces:

### 1. Live dashboard (the daily entry point)

A static page that updates whenever the cron runs (likely weekly for v0; eventually daily). Right-now numbers: open 311 cases by category, active TEP outages, current water advisories, median pothole closure this month, top reported intersections, week-over-week delta. Mobile-first, no JS frameworks, fast.

A permanent **"Heat / Water / Power"** banner at the top makes the desert lens unmissable: TEP outages happening right now, current Tucson Water advisories, heat-connected 311 categories filtered out from the noise. This isn't a separate product — it's a permanent fixture on the main view that signals *this is local, this is desert, this isn't a generic civic-data project.*

### 2. Weekly explainer post

What the original spec called the "weekly report" — but reframed as **editorial commentary**, not a metrics dump. Voice is TDB's voice. ~600 words. Picks 2-3 things worth pulling out of that week's data, links back to the dashboard for everything else. Distributed via the newsletter and feeds the RAG corpus.

### 3. Transparency Tracker (the strongest opening play)

A standalone, periodically-updated page that audits **what Tucson publishes vs. what it doesn't** across every relevant agency, with direct comparisons to peer cities (especially NYC, given the editor's lived experience there). The research already produced the spine of it:

- Tucson does not publish 311 on its open-data portal — the data only exists via SeeClickFix's vendor API.
- Tucson does not publish code enforcement at all.
- Tucson does not publish permits in bulk (Property Research Online is per-parcel only).
- Tucson Water publishes no operational KPI report.
- Pima County Sheriff publishes only PDF aggregates of calls-for-service.

Compare to NYC, where 311, DOB permits, water main breaks, and DSNY service requests are all published as machine-readable open datasets with daily refresh.

This page can stand alone *before any responsiveness numbers exist*. It's also the cheapest to ship — mostly editorial work plus a small machine-checkable component (does dataset X exist? was it updated this week?). It's the strongest editorial play because:

- Cheapest to build.
- Most defensible (nobody can argue with "this dataset doesn't exist").
- **Depoliticizes everything that comes after.** Once Tucson is established as a transparency laggard relative to peers, every subsequent measurement is contextualized as "this is what we can see — we'd like to see more."
- Cleanest pitch for interviews and LinkedIn (CTPO portfolio play).
- Naturally invites city engagement: "Publish the data and we'll measure it."

### 4. Original journalism using the accumulated data

Once the archive piles up — six months of polled TEP outages, a year of 311 closure rates, the full SeeClickFix backfill — there's material no one else has. *"The five intersections in Tucson with the most pothole reports of 2026."* *"How TEP outages clustered around heat-advisory days last summer."* *"What happens to a 311 request after you submit it: a 16-year history of the city's evolving response."* These pieces live in the existing `news-reports/` stream and pull people in who don't read TDB yet.

---

## The "distinctly Tucson / distinctly desert" thread

Three structural truths that make this project different from anything a NYC-style civic-data project would look like:

- **Power in Tucson is life-or-death in summer.** A ConEd outage in NYC in May is an inconvenience. A TEP outage in Tucson in July at 108°F, in an apartment where the elderly tenant has nowhere else to go, is a heat death waiting to happen. TEP restoration time isn't just an operational metric — it's a survival statistic.
- **Water in Tucson is precarious in a way New Yorkers cannot intuit.** NYC has watershed protected by 1842 legislation and infinite-feeling supply. Tucson is groundwater-dependent metro on borrowed Colorado River water with a state-mandated safe-yield deadline that just hit. A boil-water advisory or main break carries a different psychological weight here.
- **Heat is a layer that connects to 311.** Cooling-center failures, broken AC at city facilities, downed shade trees, abandoned buildings being used as shelter — these are 311 categories that can be isolated and tracked as the **heat dimension** of city responsiveness.

The product treats this as a permanent fixture, not a feature: every dashboard view shows the heat/water/power banner first, every weekly explainer can pull a thread from it.

---

## The four AI functions

AI is at the heart of the project not as a gimmick but because civic data is structured, footprint-small, factually grounded, and read by a public that mostly doesn't have time to learn how it works. AI removes friction at every step. Four functions, each with one or two strong applications:

### Function 1 — Discovery: what's worth telling residents about?

- **Anomaly detection / story angle suggester.** Each cycle, an LLM reads the structured metric outputs and flags 3-5 story-worthy patterns (a sudden graffiti spike in one ward, an intersection that's been on the 311 board for 47 straight days, a TEP outage cluster that didn't match any storm). Same architecture as the FOIA Lead Spotter on the existing TDB roadmap. AI surfaces leads, **the editor decides what to chase**. Force-multiplying, not editorially substitutive.
- **Cross-source correlation engine.** This is where the desert lens becomes algorithmic. *Did TEP outages cluster on heat advisory days? Did Tucson Water main breaks correlate with a 311 cooling-call spike? Did graffiti reports drop during periods when the city ran active cleanup contracts?* AI doesn't invent the correlations — it computes them deterministically and writes the explanations. **This is what makes the project more than the sum of its sources.**

### Function 2 — Synthesis: how do we explain it?

- **Original journalism drafted from data plus context.** Given the week's metrics + relevant chunks of TDB's editorial corpus + relevant agenda references, draft an 800-word explainer in TDB's voice. Same prompt discipline as existing pipelines: no fabrication, cite metric IDs and source rows, refuse to make claims the data doesn't support.
- **Civic concept explainers / contextual glossary.** Hover over "CDBG" or "lost-and-unaccounted-for water" or "safe-yield" → AI-generated plain-language explanation, cited to authoritative sources, embedded in the dashboard. Many residents don't know what these terms mean and won't read footnotes. Removing that friction is a literacy play.

### Function 3 — Access: how do residents find what's relevant to them?

- **Operational RAG — the chatbot extended to live data.** The existing RAG agent (`rag/ask.py`) answers from published articles. Extend it to query the SQLite store: *"Has anyone reported a pothole on my block?"* *"When was the last time my address had a water advisory?"* *"Is there a TEP outage near me right now?"* **Single highest-leverage user-facing AI move in the project.** Turns the dashboard from a thing-readers-look-at into a thing-readers-converse-with. Technical lift is small (same retrieval architecture, plus structured-data sources alongside text chunks, plus a few new tools the model can call: geographic lookup, time-range queries). User-facing impact is large.
- **Natural-language data exploration.** "Show me all 311 calls about abandoned vehicles within a half-mile of Speedway and Campbell from the last six months." Translate user prose into a parameterized SQL query against the store. Lowers the technical bar to zero.

### Function 4 — Translation: how do we reach more readers?

- **Spanish-language version of everything.** ~25% of Pima County speaks Spanish at home. Most local outlets either don't translate or run it through Google Translate. Sonnet translates editorial prose at high quality with the same author voice. Dashboard, explainer, chatbot, alerts — all available in Spanish at near-zero marginal cost. **Cheapest distinct-from-competitors play in the project,** distinctively local in a way NYC peers don't typically need.
- **Audio version using the existing podcast pipeline.** Weekly responsiveness audio brief, ~3 minutes, via the same TTS plumbing the daily podcast uses. Different audience, same source material.

### Adjacent AI applications worth flagging

- **Public records request drafting.** When the Transparency Tracker shows a missing dataset, AI drafts the records request — proper agency, legal basis, specific scope. Connects the Tracker from descriptive to actionable.
- **City feedback parsing.** If the project adopts a "give the city 24-hour notice" model, AI extracts factual claims from freeform email responses, integrates corrections into the next report. Closes the editorial loop.

### What we are NOT building (AI guardrails)

- **No "predict crime" anything** with TPD CFS. Off-thesis, ethically fraught, and CFS isn't a clean crime proxy.
- **No AI-generated composite "city score."** The whole project is disciplined about not creating master scores; AI shouldn't sneak them back in via composite metrics.
- **No AI that pretends to be an authority it isn't.** Same RAG discipline applies: cite, refuse, no fabrication.

---

## Editorial discipline (carried over from TDB)

- No fabrication. Ever. AI passes only structured metrics; LLM rewrites them.
- Cite source files, metric IDs, or row-level identifiers in every claim.
- Calls-for-service ≠ crime. Always label as "police demand" or "public safety call volume."
- Workload ≠ effectiveness. Distinguish them.
- Responsiveness ≠ outcomes. Distinguish them.
- Missing/stale data is itself a finding, not a gap.
- "Needs caution" is a real status label, not a hedge.
- No partisan or "gotcha" framing.
- Use status labels (Improving / Flat / Worsening / Data missing / Needs caution), not numeric 0-100 scores. Numeric scores invite false precision and gaming.

---

## Build sequence

### M0 — Research ✅ DONE 2026-05-10

Three rounds of research agents covered: 311 + permits + code enforcement + police calls + open-data landscape + Census ACS + TEP outages + Tucson Water. Findings consolidated above and in `project_responsiveness_index.md` memory.

### M1 — v0 launch (target: 1-2 weekends of focused work)

**Three deliverables, all live at the same time:**

1. **Transparency Tracker page.** Mostly editorial. ~1 weekend.
2. **311 dashboard with citywide numbers.** Backlog, medians, week-over-week, top categories, top reported locations. No equity, no per-ward, no judgment. Pure operational reporting. ~1 weekend given how clean the SeeClickFix data is.
3. **"How this works" methodology page.** Documents data sources, what the project does NOT measure, contact info for residents.

**Sources:** SeeClickFix 311 + TPD CFS only.

**No Equity Score** (dropped per 2026-05-10 decision — politically charged, low marginal value at v1, would derail trust-building).

### M1.5 — Editorial layer

- Weekly explainer post wired into the existing publish flow.
- Anomaly detection feeding the editor with weekly story leads.

### M2 — TEP outages (greenfield civic data)

- Kubra GeoJSON polling on a 2-min cadence, snapshot-and-store. **TDB becomes the historical archive** since TEP doesn't publish history.
- Outage section added to dashboard.
- Operational RAG extension begins — the chatbot starts answering questions about TEP outages using the new structured store.

### M3 — Tucson Water + cross-source correlations

- ArcGIS Experience FeatureServer URL discovery (need browser devtools network inspection) → polling for water advisories + main breaks.
- Water section on dashboard.
- Cross-source correlation engine goes live: the desert-specific signature feature kicks in (heat days × TEP outages × water advisories × 311 cooling calls).

### Beyond M3

- Spanish-language translation across all surfaces.
- Audio version of weekly explainer via existing podcast pipeline.
- Public records request drafting (turning Transparency Tracker from descriptive to actionable).
- City feedback parsing (if "24-hour notice" engagement model adopted).
- Permits via PRO scrape (if the marginal value justifies the engineering work).
- Code enforcement and Pima County Sheriff CFS via FOIA queue.
- Possible re-introduction of Equity Score with mature methodology + heavy caveats.

---

## Data sources summary

### SeeClickFix 311 (M1, primary)

- **Endpoint:** `https://seeclickfix.com/api/v2/issues?place_url=tucson` (place_id 894)
- **Auth:** None. No documented rate limits. Verified anonymous read works.
- **Coverage:** 88,172 records back to November 2009. ~16 years of history.
- **Update cadence:** Real-time (records appear within minutes of submission).
- **Backfill cost:** ~880 paginated calls for full archive.
- **Citation URL pattern:** Each issue has `html_url` for a public per-issue page on `seeclickfix.com/tucson/issues/{id}`.

**Three known gotchas (must handle in ingestion):**

1. **Timestamps are Eastern Time** (`-04:00` / `-05:00` offsets), not MST. Normalize at ingest or every weekly bucketing breaks.
2. **"Closed" and "Archived"** both have `closed_at`. Treat them together for response-time stats.
3. **`acknowledged_at` is auto-set ~2 seconds after `created_at`** for nearly every record — DO NOT use it for response time. Use `closed_at - created_at`.

**Other quirks:** No ward field (derive from lat/lng against city ward shapefile from `gisdata.tucsonaz.gov`); call-taker entries dominate volume; lat/lng precision varies; no resolution-reason field on closed records.

### TPD calls-for-service (M1, secondary)

- **45-day rolling layer:** `https://policeanalysis.tucsonaz.gov/datasets/tucson-police-calls-for-service-last-45-days-open-data`
- **Annual archives 2017-2025:** Same hub (e.g., `cotgis::tucson-police-calls-for-service-2022-open-data`).
- **Platform:** ArcGIS Hub. Every dataset has a queryable REST FeatureServer endpoint.
- **Schema:** call type/code, received/dispatched/cleared timestamps, disposition, priority, division/beat, geographic point (block-level redacted, hundred-block).
- **Auth:** None. Free.
- **Caveat:** "Calls for service" ≠ "crime." Frame as police *demand*, not crime stats.

### TEP outages via Kubra (M2)

- **Live map:** `https://www.tep.com/outages/`
- **Underlying API (no auth):** `https://kubra.io/stormcenter/api/v1/stormcenters/{INSTANCE_ID}/views/{VIEW_ID}/currentState?preview=false`
- **TEP `VIEW_ID`:** `1b43510f-b947-437b-9879-c0bd8f6d7816`
- **`INSTANCE_ID`:** discoverable via browser devtools Network panel.
- **Format:** GeoJSON, polygon-precise (red-box circuit polygons, NOT addresses — privacy feature).
- **Refresh:** ~2 minutes.
- **No public historical archive.** Polling and storing is the only path to history. **TDB becomes the canonical historical record.**
- **Open-source scrapers exist:** `fgregg/kubra`, `open-austin/energy-outage`. Adapt, don't build from scratch.
- **Annual SAIDI/SAIFI metrics** via EIA Form 861 (CSV, federal — cleaner) or ACC docket E-01933A (PDF — more detail).
- **Trico Electric** (Tucson edges — Marana, Corona de Tucson, Sahuarita, Avra Valley) also uses Kubra: `https://trico.outagemap.coop/`. Add when ready.

### Tucson Water advisories (M3)

- **Outage map:** `https://experience.arcgis.com/experience/213a937e939745daa394e074367e0083` (ArcGIS Experience app).
- **Underlying data:** ArcGIS FeatureServer, exact URL TBD via browser devtools Network panel inspection.
- **Categories:** "Planned Infrastructure Upgrades" and "Emergency Repairs."
- **Service area shapefile:** `https://gisdata.tucsonaz.gov/datasets/tucson-water-obligated-service-area`
- **Annual Consumer Confidence Reports (CCR):** Published in June. PWSID `AZ0410112`. Structured data via ADEQ Drinking Water Watch: `https://azsdwis.azdeq.gov/DWW_EXT/JSP/WaterSystemDetail.jsp?tinwsys_is_number=2047&tinwsys_st_code=AZ&wsnumber=AZ0410112`.
- **No published operational KPI report.** This is itself a Transparency Tracker finding. Oro Valley Water Utility, a peer, publishes a real KPI annual report.
- **Surfaced public KPI:** 11.43% lost-and-unaccounted-for water in 2024 (exceeded ADWR's 10% statutory limit). Reported via Tucson.com investigation.

### Census ACS (deferred with Equity Score)

- **API:** `https://api.census.gov/data/2024/acs/acs5` (free key required for production).
- **Recommended variables:** `B01003_001E` (population), `B19013_001E` (median household income), `B17001_002E/B17001_001E` (poverty), `B03002` group (race/ethnicity), `B16001` group (language), `B25003` (housing tenure).
- **Crosswalk needed:** wards aren't a Census geography. Population-weighted areal apportionment using 2020 Census blocks is the accepted method (1-3% error vs. 5-15% for pure-areal).
- **Re-introduction trigger:** if/when Equity Score returns with mature methodology.

### Defer entirely

- **Permits:** Tucson PRO + Pima Accela are search-only, no API, no bulk export. Scrape engineering work — defer until justified.
- **Code enforcement:** Not published anywhere by either jurisdiction. FOIA queue. Third-party site `neighborhood.w6iwi.org` partially mirrors Tucson code data — worth a contact email when this becomes priority.
- **Pima County Sheriff CFS:** Only PDF aggregates published. FOIA queue.
- **State-level data with Tucson/Pima rows:** ADEQ environmental complaints, ADOT highway maintenance, Auditor General audits, ACC utility complaints — interesting eventually but defer until M3+.

---

## Codebase reuse plan

~60-70% of the infrastructure already exists in the TDB monorepo. Direct lifts:

| TDB component | Responsiveness use |
|---|---|
| Desert-palette CSS, footer, GA, mobile layout | Index pages live at `tucsondailybrief.com/responsiveness/` and inherit the brand |
| `preview_md_to_html()` and `render_meeting_index()` from `agenda_mining.py` | Render weekly markdown reports → HTML in the same shape |
| Telegram notification pipeline (`send_telegram.py`) | "Weekly Index published" ping |
| Anthropic SDK + Sonnet 4.6 prompt pattern | Constrained "write prose from these metrics only" calls |
| `~/.config/environment.d/*.conf` env pattern | Add `census.conf` etc. when needed |
| Friday/Sunday cron pattern (`run_newsletter.sh`) | Weekly cron for Index report generation |
| Idempotency-via-output-file pattern | "Skip if `reports/2026-W19.md` already exists" |
| RAG agent (`rag/ask.py`) | Operational extension — same architecture, plus structured-data sources |
| Editorial bar discipline (no fabrication, no obscure references, evidence-based) | Already documented in memory; transfers directly |

**Genuinely new:**

- **SQLite as a *time-series store*.** TDB is largely stateless. Responsiveness needs persistent time-series for week-over-week deltas, 4-week moving averages, etc. RAG agent introduced sqlite-vec but used it as a one-shot index.
- **`pandas` for time-series math.** New dep.
- **Geographic point-in-polygon for ward derivation** (operational only, not for equity).
- **Data-quality monitoring as first-class output.** New discipline.
- **Polling and persisting third-party APIs (Kubra)** to become the historical archive.

---

## Open decisions / deferred calls

1. **Name.** "Tucson Responsiveness Index" works for the analytical core but might want a friendlier umbrella. Strong candidate: **"How Tucson Works."** Decide once a draft home-page layout exists.
2. **URL.** Currently a coming-soon stub at `tucsondailybrief.com/responsiveness.html` (root level, mirrors the pattern of every other section index after the 2026-05-11 IA redesign). When the real dashboard ships, options: keep it at `responsiveness.html` as a single-page dashboard; or use `responsiveness/dashboard.html`, `responsiveness/methodology.html`, `responsiveness/transparency-tracker.html` for multi-page navigation, with `responsiveness.html` as the landing page that links into them. **Avoid `responsiveness/index.html`** — GitHub Pages does not serve directory index files on this site (verified during the 2026-05-11 redesign; site has `.nojekyll`).
3. **City engagement protocol.** Publish cold, or give the city 24-hour notice with a chance to provide context that lands in the report? Leaning toward notice (models the responsiveness being measured; non-response itself becomes a finding).
4. **Equity Score re-introduction.** Dropped from v1 (2026-05-10). Methodology (population-weighted block-to-ward crosswalk + MOE handling) is documented above. May return with mature methodology and heavy caveats.
5. **Geographic granularity in dashboard.** Per-ward maps are off-table for v1, but neighborhood-level hot-spot maps are still on (operational, not equity-comparison). Exact granularity (intersection / block face / census tract) is a v0 design call.
6. **Dashboard freshness.** v0 likely weekly cron-driven. Eventually daily, then real-time as polling pipelines mature.
7. **Charts vs. tables.** The spec called for matplotlib/plotly. Static SVG charts generated at build time fits the existing static-site model better. Decide during v0 design.

---

## When to resume

This work is paused as of **2026-05-10**. Status update **2026-05-11**: full IA + visual redesign of the site shipped (commits `b927b4a` through `35fd6fb`). A coming-soon stub for this section is live at `responsiveness.html`. Active TDB priorities now:

1. **RAG agent Phase 2** — web UI + Cloudflare Worker + public launch as the marketing event. This and the Responsiveness Index are the two queued next-builds; pick one to attack on the next session. Phase 2 has an unresolved architectural question (where the sqlite-vec DB lives in deploy) — see CLAUDE.md "Phase 2 — public web UI" section.
2. **The Responsiveness Index itself** (this doc). M1 scope is locked.
3. **Marana Spotted coverage** — pending tier-1 work. Smaller scope than either of the above; could fit between them.
4. **The Old Pueblo Speaks** — outreach-based reporting; roadmap stub in CLAUDE.md. Not blocking anything.
5. **60-day marketing push** — kicks off after RAG Phase 2 ships publicly.

Pick this up when:
- The RAG agent ships publicly and demonstrated the chat-over-corpus pattern works.
- Or when an editorial trigger appears (a major Tucson Water or TEP story makes the project's framing irresistible).
- Or when the user is between bigger items and wants a focused weekend project.

The research is durable. The data sources, gotchas, and architecture decisions in this doc don't expire fast.

---

## Quick-start checklist for resuming

When picking this up cold:

1. Re-read this doc and `project_responsiveness_index.md` memory.
2. Verify SeeClickFix endpoint still works: `curl 'https://seeclickfix.com/api/v2/issues?place_url=tucson&per_page=1'`.
3. Verify TPD CFS layer still publishes: visit `policeanalysis.tucsonaz.gov`.
4. Check whether Tucson has started publishing 311 on `gisdata.tucsonaz.gov` directly (would change the Transparency Tracker lead).
5. Decide v0 scope (Transparency Tracker page + 311 dashboard, or start smaller).
6. Begin: `responsiveness/build_index.py` (ingest), `responsiveness/db.py` (schema), `responsiveness/render.py` (HTML).

That's enough to get from cold start to first commit in an afternoon.
