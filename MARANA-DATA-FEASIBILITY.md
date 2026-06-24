# Marana Structured-Data Feasibility Scan

**Researched 2026-06-24.** Goal: match (or exceed) the Oro Valley structured-data layer (`OV-DATA-FEASIBILITY.md`) for the **Town of Marana** (fast-growing NW Tucson suburb, Pima County, ~60.5k pop.). Anything an average Southern AZ reader finds interesting: new business/development filings, zoning, crime, budget/spending, water.

> **Provenance note:** This document was reconstructed from four parallel research subagents that ran 2026-06-24 and were interrupted by a PC crash mid-run. The **Crime** stream completed a full report; the **Development/GIS**, **Business & Council**, and **Budget/Finance/Water** streams were verified deep into their work but did not write final synthesized reports — their findings below come from their verified fetches (HTTP 200 confirmed, real records pulled). Items marked **UNVERIFIED** still need a live check.

---

## Cross-cutting WAF gotcha (READ FIRST — differs from OV)

Marana's main site WAF behaves **opposite** to Oro Valley's Akamai:

| Host | Protection | What gets through |
|---|---|---|
| `www.maranaaz.gov` | Akamai (OpenCities/OnBase CMS) | ⚠️ **No-UA or minimal-UA = 200; a full Chrome UA = 403.** The WAF flags browser-*spoofing* fingerprints. (Inverse of OV.) Some pages need the full Chrome header set instead — behavior is path-dependent; test both per path. |
| `www.maranaaz.gov/files/assets/...` (CDN) | same | **Direct PDF URLs download fine with no/minimal UA** (verified: 11 MB ACFR, 10 MB budget). This is the clean path for budget/finance/water PDFs. |
| `portal.maranaaz.gov` (ArcGIS Server) | **none** | ✅ Fully open, no auth, no WAF. The GIS gold mine. |
| `services1.arcgis.com/IZmVB517nWCTFBQy` (Marana AGOL org) | none | ✅ Open hosted feature services. |
| `gisdata.pima.gov` (Pima County GIS) | none | ✅ Open — hosts Marana zoning + authoritative parcels. |
| `openbooks.az.gov` | **Cloudflare** | Needs a *real* UA (Safari/Chrome); no-UA = 403. Opposite of maranaaz.gov. |
| `azcrimestatistics.azdps.gov` (DPS TOPS) | TLS chain broken | `curl -k` / `verify=False` required (plain fetch = HTTP 000). |
| `api.usa.gov/crime/fbi/cde` (FBI CDE) | none | ✅ Clean JSON API. |

**Prefer the WAF-free paths:** `portal.maranaaz.gov` (GIS), `services1.arcgis.com/IZmVB...` (econ-dev), `gisdata.pima.gov` (zoning/parcels), FBI CDE API, and direct `files/assets` PDF URLs.

---

## Priority build order (synthesized across all four streams)

| Rank | Feed | Verdict | Source | Why |
|---|---|---|---|---|
| ⭐ **1** | **Marana Development Watch** | **EASY — build first** | `DS_Current_Projects_Live` (Marana GIS) | Live, rich, queryable dev-cases feed — direct analog to the OV `Development_Cases` pipeline (`dev_watch_orovalley.py`). Name/date/number/location/applicant/description/type/status/link/photo. |
| **2** | **Marana Crime + the TPD-contrast story** | **EASY** | FBI CDE JSON API (ORI `AZ0100900`) | Confirmed clean-reporting ORI, continuous 2018–2024, no auth. Built-in "Marana reported, Tucson didn't (2021–23)" angle. |
| **3** | **Commercial building permits / new business** | **EASY–MODERATE** | `COMMERCIAL_BLDG_PERMITS` + `Business_License_2023` (Marana GIS) | Queryable permit + business-license point layers. "What's opening" feed. (Live business-license *registry* via CityView is summer-2026, not yet pollable.) |
| **4** | **Crime cross-check + rate callouts** | **MODERATE** | AZ DPS TOPS `/pdf` | Real parseable PDF (`-k` for cert) → `pdftotext`; corroborates FBI + adds DPS crime rate & clearance rate. |
| **5** | **Budget / spending** | **MODERATE** | maranaaz.gov `files/assets` PDFs | 228-pg budget + ACFR + AG Schedules A–G — clean `pdftotext`, dept-level. Vendor/check-register **NOT published** (records-request only). |
| **6** | **Water utility** | **MODERATE** | Rate study + CCR + annual reports (PDFs) | On-brand desert/water; PDF extraction, annual cadence. |
| **7** | **Liquor licenses** | **MODERATE** | AZ DLLC ABC Online / pending-apps | Statewide tool; Marana clerk page is process-only (no registry). See caveats. |

Everything in ranks 1–3 reuses the existing OV/Spotted/FBI poller patterns almost verbatim.

---

## Stream 1 — Development / GIS ⭐ (the gold mine)

**Marana runs its own fully-open ArcGIS Server** at `https://portal.maranaaz.gov/server/rest/services/` — no auth, no WAF. This is the Oro Valley equivalent (and then some). Two service families matter:

### 1a. `Hosted/` feature services — the LIVE feeds (build these)

Base: `https://portal.maranaaz.gov/server/rest/services/Hosted/`

**⭐ `DS_Current_Projects_Live/FeatureServer/0` ("DS_Projects")** — THE dev-watch feed. Point geometry, `capabilities: Query`, maxRecord 1000. Fields:
```
objectid (OID) · name (Project Name) · date (Project Date) · number (Project Number)
· location (Project Location) · applicant (Applicant Name) · description (Project Description)
· link (Submittal Link) · type (Development Type) · status (Project Status) · img (Photo Link)
```
This is richer than OV's layer — it already carries applicant, description, submittal link, and a photo. Poll + diff on `number` / `objectid` (and `date`), same shape as `dev_watch_orovalley.py`.

**`COMMERCIAL_BLDG_PERMITS/FeatureServer/0`** — point layer, Query-capable, maxRecord 2000. Fields: `objectid · name · type · issue_date`. → "new commercial construction" feed.

**`Business_License_2023/FeatureServer/0`** — business licenses (note the `2023` suffix — confirm it's current vs. a frozen snapshot before relying on it).

Other Hosted layers present: `AllPemits_2023`, `MultiFamily_DS_Projects`, `Single_Family_Residential`, `CIP_Projects_Public` / `CIP_Projects`, `DS_Inspections`, plus Survey123/Map service noise to ignore.

Query pattern (standard ArcGIS REST, verified working):
```
https://portal.maranaaz.gov/server/rest/services/Hosted/DS_Current_Projects_Live/FeatureServer/0/query?where=1%3D1&outFields=*&returnGeometry=false&f=json
```

### 1b. `LandRecords/Development/FeatureServer` — reference/historical polygons

Base: `https://portal.maranaaz.gov/server/rest/services/LandRecords/Development/FeatureServer` (37 layers). Useful ones with dates for diffing:
- **(13) Conditional Use Permit** — `ORD_DATE` (epoch-ms, populated), `PROJECT_NO`, `USE_`. 33 records.
- **(9) Significant Landuse Change** — has `ORD_DATE`.
- **(15) Development Plans** — `DP_NAME`, `APPR_DATE`, `UNITS`, `ACRES`, `Proj_Num`. 270 records. (⚠️ APPR_DATE query came back empty — dates may be null/non-queryable; verify.)
- **(2) Proposed Subdivisions** — 93 records.
- **(4) Annexations**, (10) Specific Plans, (12) Minor Land Division, (22) Vacant Properties.

⚠️ **(14) "Current Development Activity" is misleadingly named** — it holds **historical** data (project numbers like `PRV-06xxx`/`DPR-05xxx` = 2005–2008 era) with `last_edited_date` **null**. 95 records. Do NOT use it as the live feed — use `Hosted/DS_Current_Projects_Live` instead. If you ever must diff layer 14, fall back to OBJECTID set-comparison (no usable date).

### 1c. Parcels — `LandRecords/Parcels/FeatureServer`

- **Layer 4 "Pima Parcels"** — full schema (`APN`, `SITUS_ADD`, `Zoning`/`CURZONE`, `SUBDIV_NM`, `TOTALFCV`/`LANDFCV`/`IMPFCV` assessor values, `PARCEL_USE`, `MAIL1-5`, `JURIS_OL`). BUT: it's the **full Pima County set (83,843 parcels)**, and the owner/value fields look **largely unpopulated on this copy** — authoritative owner/value data lives at the Pima County Assessor. `JURIS_OL LIKE '%arana%'` returns 32,632. Treat as geometry/zoning reference, not assessor truth.

### 1d. Zoning — lives on Pima County's server (clean)

```
https://gisdata.pima.gov/arcgis1/rest/services/GISOpenData/Boundaries2/MapServer/8
```
(Owned by "PimaMaps"; also surfaced via the AZGeo hub `azgeo-open-data-agic.hub.arcgis.com/datasets/PimaMaps::zoning-town-of-marana`.)

### 1e. Economic Development Pipeline — Marana AGOL org (`services1.arcgis.com/IZmVB517nWCTFBQy`)

Hosted feature services worth a look for "what's coming to Marana":
- `Economic_Development_Pipeline_Projects_WFL1/FeatureServer/0`
- `Marana_Top_25_Employer_Locations` / `Marana_Top_25_Employers_WFL1`
- `Marana_Vacant_Properties_Occupation_WFL1`, `Occupation_Data_Marana`

### 1f. Permits portal — eTRAKiT (search-only, NOT bulk-queryable)

`https://maranaegov.com/etrakit/search/permit.aspx` — ASP.NET/IIS, ViewState, search-only UI. No JSON/bulk path. Detail URL pattern `?ActivityNo=B2205-163` exists but driving it needs a headless browser. **Skip for automation** — the GIS permit layers (1a) are the clean substitute. Note: **CityView (Harris) licensing/permitting portal goes live summer 2026** — re-check then for a live business-license registry.

---

## Stream 2 — Crime & Policing (✅ COMPLETE report)

**Marana PD ORI = `AZ0100900`** — CONFIRMED via FBI CDE agency-list (not inferred). `is_nibrs: true`, `nibrs_start_date: 2021-01-01`, **continuous monthly data 2018–2024, NO reporting gap** — the direct contrast to Tucson PD's 2021–2023 hole.

### Source 1 — FBI Crime Data Explorer JSON API ⭐ (EASY, build first)

Confirm ORI / NIBRS status (all AZ agencies by county):
```
https://api.usa.gov/crime/fbi/cde/agency/byStateAbbr/AZ?API_KEY=DEMO_KEY
```
Offense + clearance counts by year (workhorse — swap the category; **date format `MM-YYYY`**, bare year = HTTP 400):
```
https://api.usa.gov/crime/fbi/cde/summarized/agency/AZ0100900/violent-crime?from=01-2020&to=12-2024&API_KEY=DEMO_KEY
```
Categories verified: `violent-crime`, `property-crime`, `homicide`. JSON keys: `offenses` → `actuals` (monthly "...Offenses" + "...Clearances" series → annualize by summing months) + `rates` (AZ + US per-100k benchmarks for free chart context). Get a free api.data.gov key for daily cron (`DEMO_KEY` is rate-limited). `arrest` endpoint exists but uses a different offense-ID vocabulary (Phase-2).

**Verified Marana actuals (annualized):**

| Year | Violent off. | Violent clear. | Property off. | Homicides |
|---|---|---|---|---|
| 2020 | 39 | 30 | 1,172 | 0 |
| 2021 | 59 | 39 | 1,206 | 2 |
| 2022 | 49 | 25 | 1,279 | 1 |
| 2023 | 49 | 25 | 1,038 | 1 |
| 2024 | 68 | 43 | 818 | 2 |

Story angles: (a) the Tucson-contrast transparency piece; (b) Marana property crime **−36% 2022→2024** (1,279 → 818) even as the town grew.

### Source 2 — AZ DPS TOPS (Crime Insight) ✅ (MODERATE, cross-check)

PDF (the automatable variant): `https://azcrimestatistics.azdps.gov/tops/report/crime-overview/marana-pd/2024/pdf`
(slug pattern `{agency-slug}/{year}`; `/image`, `/print` variants exist). The **HTML page is JS-rendered Highcharts — not scrapable**; the **PDF is a real 3-page application/pdf (215 KB), extracts cleanly with `pdftotext -layout`**. Verified content: Number of Crimes 1,160; Clearance Rate 42.41%; Population 60,507; Crime Rate/100k 1,917.13; −13.24% vs 2023; 5-yr trend; Crimes Against Person/Property/Society. ⚠️ **TLS chain broken — cron must use `curl -k` / `verify=False`** (plain fetch = HTTP 000).

### Negative findings
- **maranaaz.gov PD pages** (`/Departments/Police`, Police-Records, the 2024 Annual Report PDF): **WAF 403 even with full Chrome headers**; only a promotional Annual Report PDF, no CFS log, no dashboard, no portal. Manual-only. Public-records contact `mpdrecords@maranaaz.gov`.
- **ADOT/AZCARE crash data**: statewide-only, Marana doesn't publish its own slice — **UNVERIFIED**, needs a separate ADOT check.
- No calls-for-service / use-of-force / body-cam dataset found.

---

## Stream 3 — Business activity & Liquor (verified, no final report)

- **Marana DOES require a business license** (Finance dept): types incl. Standard, Mobile Food Vendor, Massage, Short-Term Rental, Peddler, Sexually-Oriented Business. Page `/Departments/Finance/Business-Licenses` — **no public registry on the page**; the data path is the GIS `Business_License_2023` layer (Stream 1a) and, from summer 2026, the **CityView** portal.
- **Town Clerk liquor page is process-only** (`/Departments/Town-Clerk/Firework-Permits-Liquor-Licenses`) — describes how to apply, links to DLLC, **publishes NO list of pending/issued applications.** (So unlike the Spotted liquor pipeline for Pima/Tucson/OV, Marana liquor must come from the *state*, confirming the long-standing "Marana handles liquor administratively, not via council vote" note.)
- **AZ liquor (state) — DLLC:** old `azliquor.gov` endpoints now 302-redirect; new domain `liquor.az.gov` returns 200 but the rich `license-search` (city/county/series/status filters) is **JS-rendered — UNVERIFIED, needs a headless browser.** The confirmed scriptable path is the legacy **ABC Online grid** `https://dllc.azliquor.gov/azdlprod/pub/Default.aspx?PossePresentation=LicenseSearch` (HTTP 200, no auth, ASP.NET POSSE with `__VIEWSTATE`): fields Premise / Licensee / LicenseNumber / License Type / EffectiveDate range — but **no City field** in basic search (filter Marana by Premise/address text), and the search button is a JS postback (`PerformSearch_fn()`) → fragile from curl, likely a headless-browser job. The more valuable **`azliquor.gov/query/pending_applications.cfm`** ("new filings by jurisdiction" — exactly what we'd want) is **403-walled** — re-probe. `query/search_lgb.cfm` lists license activity per governing body — worth checking.
- **Verdict:** Marana business-opening data is best sourced from the **GIS permit/business-license layers (Stream 1)**, not the liquor system. Liquor is a MODERATE/UNVERIFIED state-level add.

---

## Stream 4 — Budget / Finance / Water (verified, no final report)

All clean via **direct `files/assets` PDF URLs** (no/minimal UA; Chrome UA may 403):

**Budget / ACFR (parseable, dept-level):**
- FY25 budget: `…/finance/documents/townofmaranafy25annualbudgetfinancialplan.pdf` (228 pp, text-extractable, dept-by-fund-type tables **with FTE counts**, clean columnar w/ `pdftotext -layout`).
- FY24 budget: `…/townofmaranafy24annualbudgetfinancialplan.pdf`
- 2024 ACFR: `…/finance/documents/2024-town-of-marana-acfr-final.pdf` (11 MB; full statistical section).
- **AG (Auditor General) Schedules A–G:** `…/fy2025townofmaranatentativebudgetauditorgeneralschedules.pdf` — **standardized state forms, identical structure across AZ municipalities → extremely parseable and cross-comparable** (high value: same extractor works for OV, Sahuarita, etc.).
- Impact-fee report: `…/finance/documents/impact-fees/2025-impact-fee-report.pdf`. Business-license update: `…/v/2/finance/documents/business-license-update-june-2025.pdf`.

**Financial Transparency Dashboard** (`/Departments/Finance/Financial-Transparency-Dashboard`) — an interactive "Marana Financial System" database + Quarterly Financial Briefs. **The single most important UNVERIFIED item** (the crash hit right as this was being opened): determine the vendor (OpenGov/ClearGov/Socrata?) and whether it exposes a queryable API or vendor-level expenditure data.

**Vendor / check-register data is NOT published** — `openbooks.az.gov/town-marana` is a **stub** (just an "ACFR URL" pointer back to Marana's own page; the "vendor payments by Vendor/Customer" blurb was generic portal boilerplate, not Marana's actual hosted data — matches the OV finding). **Records-request only** unless the Transparency Dashboard above proves otherwise.

**Water (on-brand desert/water beat):**
- Raftelis rate study: `…/water/raftelis-water-and-water-reclamation-rate-study-report_final.pdf`
- Pages: `/Departments/Water-Water-Reclamation/` → Rate-Study, Water-Rates-and-Fees, Consumer-Confidence-Reports, Water-Quality. PDF extraction, annual cadence, image-table LLM pass likely needed.

---

## Immediate next steps (when picking this up)

1. **Build `dev_watch_marana.py`** off `Hosted/DS_Current_Projects_Live` — clone `dev_watch_orovalley.py`, swap the endpoint + field map (`name/number/applicant/description/type/status/date/link`), diff on `number`/`objectid`. Highest value, lowest lift.
2. **Wire FBI CDE `AZ0100900`** into whatever the OV crime poller uses; ship the "Marana reported, Tucson didn't" contrast chart.
3. **VERIFY the 3 open items:** (a) Financial Transparency Dashboard vendor/API; (b) DLLC pending-applications path for a real liquor feed; (c) `Business_License_2023` currency (snapshot vs. live) + ADOT crash data.
4. Add Marana council members + Marana PD to `pipeline/local_names.json` if not already (cross-check against the existing Marana meeting-watch coverage).
5. Fold the strongest feeds into the **Around Town** section + RAG index, same as the OV dev-watch wiring (commit `c264aea`).
