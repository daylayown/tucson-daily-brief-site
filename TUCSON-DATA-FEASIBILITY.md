# City of Tucson Structured-Data Layer — Feasibility Scan

Feasibility-scanned **2026-06-26** (4 parallel research agents; reconstructed after a PC crash wiped the original session's unsaved search). Same thesis and shape as `OV-DATA-FEASIBILITY.md` and `MARANA-DATA-FEASIBILITY.md` — Tucson is the third (and largest, most data-rich) municipality to get a structured-data layer.

**Guiding principle (user, 2026-06-26):** TDB uses AI to collect, analyze, and re-present the civic data that Tucson-area governments already publish — turning scattered portals, PDFs, and dashboards into content that makes Southern Arizona legible to readers. **Output is not limited to articles, charts, and podcasts** — any form that makes the information easy to find and understand is on the table (maps, live dashboards, short-form video, social cards, alerts, searchable trackers, RAG answers, etc.).

**Headline finding:** Tucson is *unusually generous* with machine-collectible data — the opposite of its reputation (its agendas are locked in OnBase PDFs, which colored our earlier assumptions). Almost everything below is reachable as raw ArcGIS REST JSON with **no auth and no WAF**. The PowerBI dashboards everyone links to are just skins over scrapable FeatureServers.

---

## Cross-cutting infrastructure (read first)

**Two clean, authless ArcGIS REST hosts** — the workhorses, both drop straight into the existing `dev_watch_*.py` poll-and-diff pattern:
- `https://mapdata.tucsonaz.gov/arcgis/rest/services` — City ArcGIS Server, v11.3, JSON + GeoJSON, pageable (`resultOffset`). No WAF, no token, plain UA fine.
- `https://gis.tucsonaz.gov/arcgis/rest/services` — also returns the `PublicMaps/OpenData_*` services authlessly; the police agent pulled live counts from here.
- **⚠️ Reconcile at build time (5-min check):** `mapdata.` and `gis.` both serve `PublicMaps/OpenData_*` and `PermitsCode` — they're likely the same server under two hostnames (or a mirror). Layer IDs lined up across agents (e.g. CFS-2023 = layer 76 on both). Pick one canonical host, confirm the layer-ID map, before coding a poller.
- The curated open-data layers live under the **`PublicMaps/OpenData_*`** MapServers (PublicSafety, Transportation, PropertyPlanning, Parks, EconomicDevelopment, Boundaries) plus `PermitsCode`, `Zoning`, `PropertyHousing`.
- **GOTCHA — secured folders return empty:** the bare `TPD`, `PublicSafety`, `HCD`, `CityManager` folders list `"services":[]` to anonymous callers (token-secured). The public versions are re-exposed under `PublicMaps/OpenData_*`. So police data IS open — via `OpenData_PublicSafety`, not the `TPD` folder.

**WAF inversion (mirror image of Oro Valley's Akamai):** `www.tucsonaz.gov` (the CMS) returns **403 to a full Chrome UA** but **200 to a blank/minimal UA** — including `/files/sharedassets/...` PDF URLs. So any City PDF (budget, water CCR, dept report) needs a blank-UA fetch (or headless browser). The GIS REST hosts have **no WAF at all**. Prefer REST; treat `www.tucsonaz.gov` PDFs as gated.

**Catalog discovery:** `https://gisdata.tucsonaz.gov` is the human-facing ArcGIS Hub — a **JS-only SPA, don't scrape the HTML.** But its DCAT catalog is machine-readable: `https://gisdata.tucsonaz.gov/api/feed/dcat-us/1.1.json` (HTTP 200) — use it to enumerate published datasets, then hit the REST layer directly. AGOL org slug = `cotgis` / `9coHY2fvuFjG9HQX`.

**NOT Socrata.** There is no `data.tucsonaz.gov` SODA catalog (that vanity domain is a flaky Hub alias). Geospatial/operational data = Esri ArcGIS; budget/finance = **OpenGov** (no public API → export/PDF). `maps2.tucsonaz.gov` is **dead (404)** — ignore stale search hits pointing there.

---

## Priority order (verdicts + verified endpoints)

### 1. ⭐ Crime / police data — EASY. Build first. (The flagship.)
The single richest find. Two complementary surfaces, both live and current to **this month**:

- **Summarized master table (UCR trends, no geometry):**
  `https://services3.arcgis.com/9coHY2fvuFjG9HQX/arcgis/rest/services/Tucson_Police_Reported_Crimes/FeatureServer/8`
  — **255,989 records**, Jan 2017 → May 2026. Fields: `IncidentID, DateOccurred, Year, Month, Division, Ward, UCR, UCRDescription, Offense, OffenseDescription, CallSource`. This is the **exact table behind the policeanalysis.tucsonaz.gov PowerBI dashboard** (item description says so). Citywide/ward/category trend charts straight off this.
- **Geolocated MapServer (incidents/CFS/arrests/OIS/traffic, lat+long):**
  `https://gis.tucsonaz.gov/arcgis/rest/services/PublicMaps/OpenData_PublicSafety/MapServer` — append `/{id}/query?where=1=1&outFields=*&f=json`:
  - `/81` Incidents 2025 — **93,544 rows**, rich schema (`LAT, LONG, DATE_OCCU, OFFENSE, WEAPON1DESC, CLEARANCE_DATE, clearance_verbose, WARD, DIVISION, NEIGHBORHD, CENSUSTRACT`). Addresses rounded to hundred-block for privacy. Per-year back to 2009.
  - `/42` Incidents last 45 days (9,668) · `/76` Calls for Service 2023 (**266,718**; annual series stops at 2023, recent CFS only in the 45-day rolling `/41`) · arrests per-year 2009–2023 · `/34` Officer-Involved Shootings (55 geolocated — verify freshness, may stop ~2018) · `/0` TPD_AAPO (902, offender age/race/sex) · `/62` traffic accidents (53,547) + bike/distracted/ped variants · `/50` division polygons.
- **FBI Crime Data Explorer (the accountability story):** TPD ORI `AZ0100300`.
  `https://api.usa.gov/crime/fbi/cde/summarized/agency/AZ0100300/{violent-crime|property-crime|homicide}?from=MM-YYYY&to=MM-YYYY&API_KEY=KEY` (free key at api.data.gov; date format **MM-YYYY**).
  **Reproduced the NIBRS gap:** every month of **2021 returns null** (0/12). 2017–20 and 2022–25 report. Directly confirms the `crime.md` / `crime-tpd-data.md` thesis and the "Marana (AZ0100900) reported every year, TPD didn't" contrast.
- **`clearance_verbose` / `CLEARANCE_DATE`** on the incidents layers = raw material for **original clearance-rate reporting** — the 97.56%-vs-57.45% methodology gap in `crime-tpd-data.md` becomes computable, not just citable.
- **Don't scrape** the `app.powerbigov.us/view?r=...` embeds (client-side, non-scrapable) — you never need to; recompute any dashboard metric from the FeatureServers.
- **Blocked/partial:** Use-of-force data temporarily offline ("changing data display software" — recheck for a new UoF layer). Clean traffic-*stops* table not confirmed (arrests-with-demographics is the proxy). Pima County jail/booking = HARD (Sheriff inmate search form `https://www.sheriff.pima.gov/inmate/`, browser-scrape only, county turf).

### 2. ⭐ 311 service requests (SeeClickFix) — EASY. The Responsiveness Index spine.
`https://seeclickfix.com/api/v2/issues?place_url=tucson` — authless, live, paginated. **5,947 issues**, newest created **today**. Fields: `id, status (Open/Acknowledged/Closed), summary, created_at, address, lat/lng, request_type{title, organization}` (org distinguishes City vs Dept of Transportation & Mobility — Potholes, Graffiti, Illegal Dumping, Street Lights…). Poll `&after=<ts>`, diff on `id`, track status transitions for open→closed latency. **Use the native `api/v2` path** — the Open311 `/open311/v2/.../services.json` returns 404 for Tucson. This is M1 of `responsiveness/PLANNING.md`, now confirmed trivially collectible.

### 3. Building permits + Certificates of Occupancy — EASY. Development watch + "what's opening."
`https://mapdata.tucsonaz.gov/arcgis/rest/services/PublicMaps/PermitsCode/MapServer` (52 layers):
- `/81` Commercial building — 4,716 rows, newest ISSUEDATE 2026-06-23. Fields incl. `NUMBER, ADDRESS, STATUS, WORKCLASS, VALUE, SQUAREFEET, PROJECTNAME, WARD, CSS_URL, LAT, LON`.
- `/85` Residential (19,108) · `/84` Multi-family · `/86` Subdivision · `/87` Lot splits.
- **`/99` Certificates of Occupancy — 3,480 rows, newest yesterday; `FinalCofO/TCO/Max_Occ` → the cleanest "what just opened" signal in the catalog.**
Poll `where=ISSUEDATE > <last>`, dedup on `NUMBER`/`OBJECTID`. Same shape as `dev_watch_marana.py`. Feeds a **Tucson Development Watch** in Around Town + a "what's opening" feed.

### 4. Business licenses — EASY. "What's opening," round two.
`https://gis.tucsonaz.gov/arcgis/rest/services/PublicMaps/OpenData_EconomicDevelopment/MapServer/3` (Business Licenses Open Data) — **93,483 rows**; also `PermitsCode/MapServer/9` (BUSLIC). Fields: `ACC_NAME, NAIC_CODE, NAIC_DESC, LIC_TYPE, DT_START, FULLADDRESS, LIC_STATUS, OWN_TYPE, LAT, LON`. ⚠️ `DT_START` includes future dates — filter on a window, don't assume max = today. Also a **weekly CSV** of new businesses: `https://www.tucsonaz.gov/Departments/Business-Services-Department/Taxpayer-Assistance-Division/Business-License-and-Tax-Information/Business-License-Downloads` (blank-UA fetch). Pair NAIC + CofO for opening confirmation. Active liquor licenses also here (`LL_ACTIVE`, 1,877) — extends **Spotted** beyond agenda-sourced filings.

### 5. Code enforcement — EASY. Accountability feed nobody else runs.
Notable: **Tucson publishes code-enforcement cases openly** (a gap in most metros). `PublicMaps/PermitsCode/MapServer/102` (ENGOV_CodeCases, 23,900 rows, current) and **`/103` last-60-days (3,017 rows — ready-made rolling feed)**. Fields incl. `CASENUMBER, status, OPENEDDATE, CLOSEDDATE, DESCRIPTION, type, MainAddress, District, CSS_URL`. open→closed durations computable → also feeds Responsiveness. Reader output: neighborhood code-complaint feed, "slumlord"/housing-accountability angle (pair with `PropertyHousing/HCD_VIOLATIONS_PUBLIC`).

### 6. Transit — Sun Tran / Sun Link — EASY. Live + a DIY original-reporting angle.
Full GTFS static + all three GTFS-Realtime feeds, authless:
- Static: `https://GTFS-RT.suntran.com/TMGTFSRealTimeWebService/Static/SunTranGTFS.zip`
- RT VehiclePositions: `.../Vehicle/VehiclePositions.pb` (protobuf, current) · TripUpdates `.../TripUpdate/TripUpdates.pb` · ServiceAlerts `.../Alert/Alerts.pb`
- Static GIS route/stop layers in `PublicMaps/OpenData_Transportation/MapServer` (`TDOT_BUSSTOPS` /22 = 2,257 stops, `MODERN_STREETCAR_VIEW` /10, etc.).
- **Ridership = PDF only** (FY24 report `https://www.suntran.com/wp-content/uploads/2026/01/Annual-Report-FY24-REV-8-12-25.pdf` — note `suntran.com/wp-content/` is reachable, unlike `tucsonaz.gov`). **On-time performance is not published** but is **derivable by archiving GTFS-RT TripUpdates over time** — original local reporting no one else does. Reader output: live "where's my streetcar" map, service-alert relay, OTP data story.

### 7. Air quality — EASY (via AirNow). County data, attribute correctly.
Tucson air monitoring is **Pima County DEQ**, not a City dept; `envista.pima.gov` 403s bots. Clean path = **AirNow API** (EPA, free key, 500 req/hr, JSON by lat/long or zip): `https://docs.airnowapi.org/webservices`. Reader output: daily AQI line in the brief, monsoon-dust / wildfire-smoke alerts, summer ozone — strong fit for the desert-lens thesis.

### 8. Rezoning cases — MODERATE, **stale post-2019.**
`https://gis.tucsonaz.gov/arcgis/rest/services/PublicMaps/Zoning/MapServer/6` (AREA_ZONE_VIEW, 2,363 rows, case-tracking schema: `zone_case_no, status, status_dt, init_dt, authrztn_dt, authrztn_vote_desc, conditions`). **But newest record is Dec 2019** — excellent for a *historical* rezoning analysis, NOT a live new-cases feed. Live rezoning/planning cases would need the `pro.tucsonaz.gov` per-parcel portal or a CSS planning portal — neither a clean bulk feed. (Note: City *agendas* still come via the existing OnBase pipeline; that's where current rezoning *votes* surface.)

### 9. Budget & spending — MIXED. Docs MODERATE; vendor check register HARD.
- OpenGov budget viz `https://tucsonaz.opengov.com/transparency` (200, JS SPA, no public API → UI export only). Procurement `https://procurement.opengov.com/portal/tucson-az` (403, Cloudflare). 
- ACFR / adopted budget = **PDFs** on the Budget Division pages (blank-UA fetch → `pdftotext`, same muscle as OV/Marana budgets) → dept-level budget-vs-actual.
- **No published vendor-level check register / "open checkbook"** — records-request-only. (ClearGov is used by other AZ towns, not Tucson.)

### 10. Water / environment — EASY (washes/flood) / MODERATE (CCR, WAF).
Already have the Tucson Water ArcGIS *advisory* feed (Responsiveness water dashboard). Additional clean layers on `mapdata`: `WASHES`, `COTFLOODHAZARDS`, `WASH_ERZ_REGULATORY` (flood/monsoon-drainage geometry — EASY poll). Annual **CCR water-quality PDFs** (PWSID `AZ0410112`) are WAF-gated on `tucsonaz.gov/files/` → blank-UA/browser fetch (MODERATE). No operational Tucson Water KPI dataset (consistent with the Responsiveness "Tucson Water publishes no ops KPI" finding — itself a Transparency-Tracker line).

### 11. Parks / pavement / infrastructure — EASY reference layers.
`PublicMaps/OpenData_Parks` (`TPRD_PARKS`, Prop 407 bond projects/connectivity). DCAT also lists **Pavement Conditions — Major/Minor Streets** + sidewalk ramps (TDOT) → a "state of Tucson's roads, ward by ward" data story. Plus streetlights, traffic signals, crosswalks, CIP project locations. Mostly reference/static; good for maps and bond-project trackers.

### 12. Tucson Fire — HARD / **genuine GAP** (and a story in itself).
**No operational TFD data published anywhere machine-readable.** Only GIS layer is `PS_FIRE_ESZ` (dispatch-zone boundary polygons — no incidents, no response times). Annual reports are **third-party PDFs (Tucson Fire Foundation), 1950s–2021 only**; City fire pages are WAF-403; records = request-only. Response-time-vs-NFPA-1710 story would require a FOIA. **This is exactly the "what the City doesn't publish" angle the Transparency Tracker is built on** — frame the absence as the finding.

### 13. Adoptable pets (PACC) — MODERATE, county data.
`https://24petconnect.com/PimaAdoptablePets` (updates ~15 min, per-animal records, scrapeable). No intake/outcome stats API (request-only). Run by **Pima County**, attribute accordingly. Reader output: a recurring "adoptable pets" feel-good card / Short (pairs with the existing daily-Short pipeline).

**County, not City (collectible but attribute correctly):** air quality, libraries (Pima County Public Library), animal care (PACC), elections (Pima County Recorder / AZ SOS). City Clerk holds campaign-finance filings (PDF/portal, not a feed — not deeply scanned).

---

## What this unlocks — content forms (not just articles/charts/podcasts)

The user is explicitly open to any format. Mapping the data to delivery surfaces TDB already has or could add:

- **Around Town feeds** (existing): a **Tucson Development Watch** (permits + CofO) and a **"What's Opening" feed** (business licenses + CofO + liquor) — direct clones of the shipped OV/Marana dev-watch pollers.
- **Spotted** (existing): extend beyond agenda-sourced liquor filings using `LL_ACTIVE` + code-enforcement cases.
- **Responsiveness Index** (planned, `responsiveness/PLANNING.md`): 311 (SeeClickFix) + code-enforcement open→closed latency + the Transparency-Tracker framing (Fire gap, no check register, no Water KPI). The data for M1 is now confirmed trivial.
- **ChatTDB / RAG** (existing): index the structured rows so readers can *ask* ("how many burglaries in Ward 3 this year?", "what's the status of my 311 pothole report's neighborhood?").
- **Live maps / dashboards**: crime map, 311 map, "what's being built," pavement-quality map, live bus/streetcar tracker (GTFS-RT).
- **Charts in the daily brief**: monthly crime trend, AQI line, ridership.
- **Short-form video / social cards** (existing pipeline): "Tucson crime is down X% — here's the data," map flyovers, "5 things opening near you."
- **Semantic alerts** ("watch this for me," from the AI-tools roadmap): a reader subscribes to crime in their ward, a permit on their block, or a 311 category, and gets pushed matches.
- **Original journalism**: clearance-rate analysis (the 97.56%/57.45% gap, now computable), the TPD-vs-FBI 2021 reporting-gap piece, DIY transit on-time-performance, the Fire-data transparency story.

---

## Build order recommendation

1. **Tucson Development Watch + "What's Opening"** (permits/CofO/business licenses) — clone the existing dev-watch poller; fastest path to visible new content in Around Town.
2. **Tucson Crime poller + the FBI-gap story** — highest editorial value; establishes the crime-poller pattern OV/Marana also want.
3. **311 / Responsiveness M1** — unblocks the long-planned Responsiveness Index.
4. **Code enforcement** — easy add, unique accountability feed.
5. Transit live map, AQI, water/flood maps, pavement story — opportunistic.
6. Fire gap + budget PDFs — story-driven, not feeds.

## Open questions to resolve before building
- **Host canonicalization:** confirm `mapdata.` vs `gis.tucsonaz.gov` (same server? mirror?) and lock the layer-ID map per service.
- **OIS layer freshness** (layer 34 may stop ~2018) before any OIS tracker.
- **CFS continuity:** annual layers stop at 2023; decide whether a continuous post-2023 CFS series matters (only the 45-day rolling layer covers recent).
- **`DT_START` / `ISSUEDATE` future-dating:** always filter on a window; never treat `max(date)` as "today."
- Add City of Tucson / Pima County officials already missing from `pipeline/local_names.json` as crime/permit reporting surfaces names.

---

*Reconstructed from 4 parallel research agents, all endpoints fetched live 2026-06-26. Companion to OV-DATA-FEASIBILITY.md and MARANA-DATA-FEASIBILITY.md. Pairs with crime.md / crime-tpd-data.md (TPD reporting-gap research) and responsiveness/PLANNING.md (311 + Transparency Tracker).*
