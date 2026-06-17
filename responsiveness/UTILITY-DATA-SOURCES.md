# Utility Data Sources — Responsiveness Index

Build-ready profiles of Tucson-metro utility data for the "Heat / Water / Power" archive. All endpoints/IDs **verified live 2026-06-17** via research agents unless flagged. Companion to `PLANNING.md` (strategy) — this doc is the tactical data layer.

**The through-line (and the story):** transparency tracks regulatory structure. A municipal utility answerable to its own residents publishes live operational data; an ACC-regulated private utility discloses only the annual minimum, in PDFs, after the fact. Same metro, same desert, wildly different accessibility — this is the spine of the *"Accessibility of Public Data in Southern Arizona"* story idea.

## Transparency spectrum

| Utility | Type | Regulator | Real-time outage/advisory feed | Archivable | Monitoring approach |
|---|---|---|---|---|---|
| **City of Tucson Water** | Municipal | City | ✅ ArcGIS GeoJSON (5 open / ~3,900 archived, daily) | Yes, real-time | **Poll** (~30 min) |
| **Tucson Electric Power** | Investor-owned | AZ Corp Commission | ✅ first-party JSON, but "no 3rd-party use" notice | Yes (ToS gray area) | **Poll** (2 min) — *decision tabled* |
| **Lago Del Oro Water Co.** | Private (PE-owned) | AZ Corp Commission | ❌ none of any kind | Annual PDFs only | **Manual / annual** |

**Recommended build order:** Tucson Water first (cleanest, highest signal-per-effort) → TEP (pending the ToS decision) → Lago Del Oro stays manual/annual.

---

## 1. City of Tucson Water (municipal) — POLLABLE, SHIP FIRST

Clean, authless ArcGIS GeoJSON advisory feed. Live signal daily; deep history queryable. The easiest high-value source in the project.

- **Advisory layer (poll this):**
  `https://utility.arcgis.com/usrsvcs/servers/83923d49e2954c1588a032784fe3d4bf/rest/services/Water/DrinkingWaterAdvisory/MapServer/0`
- **Current open advisories (GeoJSON):**
  `…/0/query?where=STATUS='OPEN'&outFields=*&returnGeometry=true&outSR=4326&f=geojson`
- **Full archive count:** `…/0/query?where=1=1&returnCountOnly=true&f=json` → ~3,922 rows
- **Auth:** none. **Geometry:** polygon. **Cadence:** human-entered, changes a few times/day → poll `*/30`.
- **Key fields:** `OBJECTID` (stable PK — key on this, NOT the free-text `ADVISEID`), `ADVISETYPE` (Unplanned Outage / Planned Outage / Discolored Water / Pressure / Purging-Flushing / Informational / …; **no Boil Water records ever** — frame as "service disruptions," not boil-water tracker), `STATUS` (OPEN/CLOSED/CANCELED), `ADVISESTART`/`ADVISEEND` (epoch ms), bilingual `DESCRIPTION`/`DESCRIPTION_ES`.
- **Companion layers (Tucson AGO org, no token):** `https://services5.arcgis.com/8tbZGzFP4ylTC7QO/ArcGIS/rest/services` → `Water_Main_Breaks_with_Time` (point history), service-area, pressure zones (pull once as static reference GeoJSON for spatial joins).
- **Quality:** ADEQ Drinking Water Watch PWSID `AZ0410112` (DWW JSP **403s bots**, no API → browser-scrape or use annual CCR PDFs: `…/water-quality/report-archive/ccr_mainsystem_YYYY.pdf`).
- **Schema + poller design:** see the snapshot-and-store / lifecycle model in the research notes (one row per advisory keyed on OBJECTID, append-only observation table on field-change only, poll-audit table; a failed fetch must NEVER false-resolve advisories).
- **Effort:** MVP ~2 days.

## 2. Tucson Electric Power (TEP) — TABLED (ToS decision pending)

> ⚠️ **Correction:** the old `PLANNING.md` Kubra `VIEW_ID 1b43510f-…` is **Baltimore Gas & Electric, not TEP** (decoded via customer count + Maryland geometry). Do not use it.

- **Real source (TEP first-party):** `POST https://apps.tep.com/OutageApp/mapfeed` — no auth/token; GET→403, POST→200. JSON: aggregate counts + per-outage array (center point + bounding box, customers affected, cause, start time, ETR; **no stable outage ID** → synthesize a key from `point + start_time`). Filter `division == 'TEP'` (feed also carries USE/UEE).
- **Cadence:** exactly **2 minutes** (`"RefreshFrequency":"2"`).
- **⛔ ToS caveat — open decision:** payload contains `"Notice: 3rd party use of this API is not permitted."` Unauthenticated (policy line, not a technical wall). **TEP is an ACC-regulated monopoly** → strong public-interest footing + possible sanctioned feed. **Plan before building: send TEP a courtesy email** asking for a sanctioned way to access outage data. *Decision deliberately tabled by user 2026-06-17 — revisit before any TEP build.*
- **Trico Electric** (rural edges — Marana/Sahuarita/Avra Valley) genuinely uses **Kubra** → separate fetch adapting `open-austin/energy-outage`'s quadtree scraper; needs a live devtools capture of Trico's INSTANCE_ID/VIEW_ID (not in static HTML).
- **Effort:** TEP MVP ~½ day once the ToS question is resolved.

## 3. Lago Del Oro Water Company (private / ACC-regulated) — MANUAL / ANNUAL

The user's own water provider. **No real-time data surface of any kind** — no outage map, RSS, alerts page, or active social channel. Customers learn of main breaks by mail/phone/word-of-mouth; a monitor learns never. That absence is itself a publishable finding and the opaque end of the transparency spectrum.

**Identity / ownership:**
- AZ Class-C private water utility, founded 1963 (Robson Communities roots). ACC docket stem **`W-01944A`**.
- Parent: **JW Water Holdings, LLC** (Prescott). Ultimate owner: **CVC DIF** (infra arm of European PE firm CVC Capital Partners) — **acquired Nov 21, 2024**. Site/billing white-labeled under `jwwater.com/lagodelorowater/`.
- Local operator: **Ed MacMeans**, Tucson on-site manager (Grade 4 operator).

**Service area / size:** SaddleBrooke + Catalina, far-north metro (Pima/Pinal line — county ambiguous). **~6,700 connections**, 100% groundwater (17 wells, Upper Santa Cruz alluvial aquifer; no CAP/purchased water).

**Live story — first rate hike since ~2014 (consolidated case):**
- **Dockets:** rate `W-01944A-25-0194`, financing `W-01944A-25-0218` (consolidated with Quail Creek `W-02514A-25-019x` + Ridgeview `W-03861A-25-019x`).
- **Ask:** +28% standalone (typical bill $27.21 → $30.56) **or up to +46%** ($27.21 → ~$39.82) under the proposed 3-utility consolidation; + up to $2.5M affiliate debt. **The angle:** consolidation *lowers* Quail Creek/Ridgeview bills while *raising* Lago Del Oro's — LDO's larger base subsidizes the two smaller systems.
- **Status (2026-06-17):** evidentiary hearing was set for **June 15, 2026**; **no decision yet.** Realistic track: post-hearing briefs ~July → ALJ Recommended Opinion & Order ~late summer/fall → Commission vote ~fall 2026 → **new rates late 2026/early 2027.** The untold number = ACC Staff / RUCO's recommended (lower) figure — **in the docket only.**
- **eDocket is a JS SPA — not machine-readable.** To check status/testimony: open `edocket.azcc.gov` in a browser, search docket `W-01944A-25-0194`. **Watch item: re-check ~fall 2026 for the ROO / decision.**

**Water quality (PWSID `AZ0411117`, ADEQ DWW `tinwsys_is_number=2362`):** no contaminant exceedances; uranium closest to limit (10.4 of 30 µg/L); **arsenic non-detect** (cuts against the regional-groundwater-arsenic assumption); three 2025 *late-monitoring/reporting* violations (paperwork, not health).

**What's archivable (low effort, high patience):**
- **Annual CCR PDFs** — stable URL pattern, back to 2020: `https://jwwater.com/lagodelorowater/forms-and-reports/` (2025: `…/sites/6/2026/06/LDO-CCR-2025_ADEQ-Approved.pdf`). Grab the new one each ~June.
- **ACC filings** (annual reports, rate-case PDFs) — fetchable once located at `azcc.gov`; docket index itself not scrapable.
- **No real-time anything.** Monitoring = manual.

**Key IDs:** PWSID `AZ0411117` · DWW `tinwsys_is_number=2362` · ACC stem `W-01944A` · site `jwwater.com/lagodelorowater/`.

---

*Generated from research-agent findings, 2026-06-17. TEP ToS decision and the Lago Del Oro rate-case outcome are open items.*
