# Oro Valley Data Layer — Feasibility Scan

Research date: **2026-06-23** (parallel web-research agents). Purpose: determine what structured civic data about the **Town of Oro Valley** is collectible in a machine-readable, automatable way, to seed a "structured data" layer for TDB (the next evolution past the RAG/Ask text layer). Companion to `COVERAGE-EXPANSION.md` (which covers *meeting* coverage expansion) and `responsiveness/PLANNING.md`.

**Why Oro Valley:** under-covered by the Star/KGUN, but affluent, civically engaged, growing fast (Oracle Rd corridor), and **small enough that an AI pipeline can plausibly become the system of record** — much harder in the City of Tucson. Collecting OV structured data is also what unlocks the next-gen AI tools (vote tracker, anomaly detection, Responsiveness Index) — those tools are only as good as the structured corpus beneath them.

---

## ⚠️ Cross-cutting gotcha: the Akamai WAF on `orovalleyaz.gov`

The **entire `orovalleyaz.gov` host sits behind an Akamai WAF.** Bare/default-UA requests (WebFetch, plain `curl`) get **HTTP 403 "Access Denied" (errors.edgesuite.net)**. Confirmed fix: requests succeed (200) **only with a full browser header set** — real Chrome `User-Agent` + `Accept` / `Accept-Language` + same-origin `Referer` + `Sec-Fetch-*` headers (or a headless browser). Any pipeline touching `orovalleyaz.gov` (budget PDFs, water reports, town pages, the Elected Officials roster) must spoof a complete browser header set or the fetch silently fails. Same class of barrier as the Tucson Sentinel Cloudflare wall.

**The clean paths that AVOID the WAF** (use these preferentially): the GIS server `gismap.orovalleyaz.gov`, the Swagit→Granicus minutes redirect, the FBI Crime Data Explorer API, and the Laserfiche `edoc` download path. These are the load-bearing sources below.

---

## Source-by-source findings

### 1. ⭐ Development cases (rezonings / GPAs / variances) — **EASY. The standout unlock.**

OV runs its **own public, anonymous ArcGIS REST server**: `https://gismap.orovalleyaz.gov/gismap/rest/services` (ArcGIS Enterprise 11.4; folders `CED-Planning`, `Landbase`, `Planning-ReadOnly`). **No auth, no key, no WAF.**

- **Primary layer:** `CED-Planning/Development_Cases/MapServer/0` — verified live, ~30 active cases, `Query` enabled. Fields: `CaseNumber, Common_Name, Case_Description, Applicant_Name, Location, Case_Type` (Rezoning / General Plan Amendment / Zoning Variance / …), `Case_Status`, `Property_Address, Subdivision_Name, Property_Area_Affected, Town_Contact_Name/Email/Phone, Outreach_Link, created_date, last_edited_date` + polygon geometry. Real records seen: "Linda Vista Plaza" (Rezoning, Active), a GPA by "Paradigm Land Designs, LLC."
  - Query: `…/Development_Cases/MapServer/0/query?where=1=1&outFields=*&orderByFields=last_edited_date DESC&f=json`
  - **Poll daily, diff on `CaseNumber`/`last_edited_date`** → a "Development Watch" feed in the exact shape of the existing Spotted / agenda miners.
- **Parcels:** `Landbase/Parcel_Viewer/MapServer/0` + `Landbase/SmartGOV_Parcels/MapServer/0` — `PARCEL, Situs_Address, Owner_Name, Zone_Code, PARCEL_USE, GISACRES, Year_Constructed, Subdivision, Floodplain_Type`, and a `LINK` to the Pima Assessor (`gis.pima.gov/d.htm?P={parcel}`) for valuation. No dollar value in-layer.
- **Other queryable `CED-Planning` layers:** Zoning, 2026 Land Use, 2016 General Plan, 2026 Growth Areas, PAD_Zoning, Annexation_History, Environmentally_Sensitive_Lands.
- **Note:** WebFetch got 403 on the GIS server due to *its* UA; plain `requests`/`curl` with a normal UA returns 200. Not the Akamai WAF — just a UA quirk.
- **Verdict: EASY.** Textbook ArcGIS REST polling, JSON, no auth. Highest value-to-effort of the whole scan. **Build this first.**
- Document depth (staff reports, applications) comes free from the existing OV agenda mining (Destiny Hosted) + each case's `Outreach_Link`.

### 2. Council voting record (member-level) — **EASY–MODERATE. Accountability gold.**

OV minutes use a **fixed, consistent template** that names every mover, seconder, and — on split votes — **every dissenter and abstainer by name**, plus a named `Present:` roll-call block. Because the body has 7 fixed seats and the Present list is named, **each member's vote on every motion is fully derivable** (present − opposed − abstained = voted-with-majority). This is true member-level attribution, not just tallies. Attendance falls out for free.

- **Cleanest fetch path (no auth, no WAF):** Swagit → Granicus redirect. `https://orovalleyaz.new.swagit.com/videos/{id}/minutes` 302-redirects to the official PDF at `https://swagit-attachments.granicus.com/uploads/video/minutes_file/{id}/{date}_Minutes.pdf`. Verified: real text-extractable PDF (`pdftotext` works), same named-OPPOSED/ABSTAINING format.
- **Backup/archival:** Laserfiche `edoc` download path `https://srvvlfweb01.orovalley.net/WebLink/0/edoc/{DOCID}/{file}.pdf` (verified 200, no login). The Laserfiche *search* UI (CustomSearch/BrowseData) 302s to a CookieCheck — so doc-ID *discovery* is the only wrinkle; the Swagit redirect sidesteps it entirely (ID = the meeting video ID, which the existing OV recording pipeline already has).
- **Build:** enumerate Swagit Town Council video IDs → GET `/videos/{id}/minutes` → download PDF → `pdftotext` → regex the template (`Present:`, per motion `mover/seconder`, `Vote: X - Y Carried/Failed`, `OPPOSED:`, `Other: … (ABSTAINING)`).
- **Verdict: EASY–MODERATE.** One-time parser tuning + a **5–10 meeting spot-check** to confirm "all dissenters always named" holds (verified on one 3-4 vote). No FOIA, no OCR. Directly feeds the **Council Vote & Promise Tracker** AI-tool idea, and reuses the existing transcription/agenda pipeline.
- **Bonus:** the scan returned a current **names roster** (Mayor Joseph C. Winfield, Vice-Mayor Melanie Barrett, CMs Joyce Jones-Ivey, Josh Nicolson, Harry Greene, Mary Murphy, Elizabeth Robb; Clerk Mike Standish; Town Mgr Jeff Wilkins; Town Atty Steven Zraick). **Flag:** several seats are up in the **Aug 4 2026 primary** — confirm post-election before hardcoding. Update `pipeline/local_names.json` once confirmed (Elected Officials page 403s non-browser clients — needs a browser confirm).

### 3. Crime / policing — **EASY (FBI API) + the TPD-contrast story is confirmed.**

- **Backbone — FBI Crime Data Explorer API:** `https://api.usa.gov/crime/fbi/sapi/` (free key from `api.data.gov/signup`). Clean JSON, **ORI-addressable**, queryable by agency/year/offense. The only true REST API in the whole landscape. **Verdict: EASY.** Use for OV crime trends.
- **State supplement — AZ DPS "Crime Insight" (TOPS):** predictable per-agency URLs `https://azcrimestatistics.azdps.gov/tops/report/{type}/oro-valley-pd/{year}` (+ append `/pdf` for a downloadable PDF). Confirmed types: `crime-overview`, `violent-crimes`. CSV/XML export exists but only inside the JS table app (needs headless browser). **TLS wrinkle:** the host threw a cert-chain error to the fetcher — test with real `curl` first. **Verdict: MODERATE** (PDFs easy via predictable URLs; CSV needs a browser).
- **The story (confirmed):** TPD was the **only US agency over 250K population that failed to report to the FBI in 2022** (matches existing `crime.md`), while **OV PD reported cleanly through the SRS→NIBRS transition** (continuous 2019–2023 in CDE). "Small suburb reports its crime cleanly; the big metro had a multi-year hole" is a real, supportable contrast. **Verify before publishing:** OV PD's exact ORI (candidates `AZ0100400`/`AZ01004`, unverified) and per-year completeness directly in FBI CDE (not aggregators).
- **OV's own police pages** (`orovalleyaz.gov/police/crime-statistics`): WAF-403'd, and appear to be a promotional referral page ("safest city in AZ", 4 beats), not a data feed. Treat as editorial context only. Beat-level data likely records-request only.

### 4. Water utility — **MODERATE. On-brand desert/water angle, but annual cadence.**

OV runs its own water utility and publishes a rich **recurring** document set — all **PDF, no dashboard, no API/CSV** (the "operational KPI report" = the annual report PDF, not a live dashboard; flagged so we don't misrepresent one as existing). All behind the Akamai WAF (header-spoof required).

- **Water Utility Annual Report ⭐** (recurring ~April; 2021–2024 eds. confirmed online). Production by source in acre-feet (2023: groundwater 4,925 / CAP 2,573 / reclaimed 1,880 / total 9,378), CAP entitlement, **per-well static groundwater-level time series** (Appendix A), 3-year utility statistics (Appendix C), ops + financial highlights. Body text extracts via `pdftotext -layout`; **key tables/charts are images** → needs an LLM extraction pass, not pure regex.
- **Water Rates Analysis Report** (recurring ~March): tiered rate changes over time, 5-year plan. Rate tables extract reasonably. Best "rate over time" tracker input.
- **Consumer Confidence Report** (water quality, recurring by June): contaminant tables extract **cleanly** via `pdftotext -layout` (consistent EPA template). Slow-moving (3–6 yr sample cycles).
- **Water Utility Commission** agendas/minutes: monthly (2nd Monday), same agenda-mining shape — could fold into the existing pipeline.
- **Verdict: MODERATE**, gated by WAF headers + chart-as-image extraction. Two best recurring time-series (both annual): **production-by-source + groundwater levels** (annual report) and **rates by tier** (rates report). Annual cadence = low update frequency.

### 5. Budget / spending — **MODERATE for summaries; vendor-level data is BLOCKED.**

- **OV Finance docs** (`/Government/Departments/Finance/Annual-Reports-and-Financial-Documents`, WAF-403'd page but stable CDN PDF URLs): **ACFR** (FY18/21/22/23/24), **Adopted Budgets** (FY23/24–25/26, 300+pp), AG Final Budget Schedules, "Know Your Town's Budget" (2pp summary), PAFR, and monthly financial reports. **All PDF**, department/line-item granularity. Parse with existing `pdftotext` muscle (same as Tucson OnBase). **Verdict: MODERATE** (easy to locate, WAF + PDF-parse is the work).
- **Vendor payments / check register / contract awards — NOT published anywhere public.** Only a vendor *registration* portal + a procurement guide. The single highest-value accountability dataset (sole-source awards, large payments) requires an **Arizona public-records request** to the Clerk/Finance — a human, non-automatable step. Lower-value proxy: harvest contract-award votes from OV council agendas already mined. **Verdict: HARD / records request.**
- **openbooks.az.gov/town-oro-valley:** a **stub** that only links back to OV's ACFR; the portal hosts *state-agency* data, not OV transactional data. **Dead end for OV.**
- **AZ Auditor General** (AELR / financial audits, per-entity PDFs): **MODERATE but low marginal value** — duplicates ACFR aggregates; useful only as a corroboration/anomaly signal.

---

## Priority recommendation

| # | Build | Source | Verdict | Why |
|---|---|---|---|---|
| 1 | **OV Development Watch** | `gismap.orovalleyaz.gov` Development_Cases REST | **EASY** | JSON, no auth, no WAF; same shape as Spotted/agenda miners; rezonings/GPAs before anyone reports them |
| 2 | **OV Council Vote Tracker** | Swagit→Granicus minutes PDFs | **EASY–MOD** | Member-level attribution; reuses existing pipeline; feeds the Vote/Promise Tracker AI tool |
| 3 | **OV Crime + TPD-contrast story** | FBI CDE API (+ AZ DPS TOPS PDFs) | **EASY** | Real JSON API; confirmed, publishable reporting-gap story |
| 4 | **Water tracker** | Annual Report + Rates PDFs | **MODERATE** | On-brand desert/water; but annual cadence, image-table extraction |
| 5 | Budget summaries | OV ACFR/budget PDFs | **MODERATE** | Dept-level budget-vs-actual; vendor data needs a records request |

**The unifying insight:** #1 and #2 are the wedge — both are EASY-ish, both produce recurring reader-facing content immediately, and both prove the **extraction → structured store → monitor/Ask** loop on a small, tractable town before scaling to Pima County + Tucson. Crime (#3) adds a strong one-off story. Water/budget are slower-burn.

## Items flagged "needs manual/browser check" (do NOT treat as confirmed)
1. OV PD exact ORI (`AZ0100400`/`AZ01004` unverified) + per-year FBI reporting completeness in CDE directly.
2. The `azcrimestatistics.azdps.gov` TLS cert error — real misconfig vs. fetch-tool quirk (test with curl).
3. Whether a headless browser clears the `orovalleyaz.gov` Akamai 403 reliably (needed for budget + water).
4. "All dissenters always named" in OV minutes — spot-check ~5–10 split votes before trusting attribution.
5. Live OV elected-officials roster (page 403s bots) before updating `pipeline/local_names.json`; several seats up in the Aug 4 2026 primary.
6. Whether SmartGov's authenticated public permit search returns result tables — there's no bulk path either way, so building permits / business licenses are effectively **not automatable** (paid Granicus API or records request only).
