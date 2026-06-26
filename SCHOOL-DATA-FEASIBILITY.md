# Southern Arizona School-District Data — Feasibility Scan

Feasibility-scanned **2026-06-26** (4 parallel research agents, all endpoints fetched live). Companion to `TUCSON-DATA-FEASIBILITY.md`, `OV-DATA-FEASIBILITY.md`, `MARANA-DATA-FEASIBILITY.md`, and `COVERAGE-EXPANSION.md` Part 1C (the meeting-coverage plan this extends with the **data** dimension). Covers the 9 major Tucson-metro K-12 districts.

**Why this beat:** School boards are the most under-covered governance beat in American local news (night meetings, procedural agendas, consequential decisions). U of A soaks up local higher-ed attention; K-12 governance goes dark. AI can attend every board meeting no reporter does AND re-present a deep, structured state/federal data trail nobody re-presents for families. **Editorial note:** schools are emotionally charged / culture-war-adjacent — keep the human-review gate on all meeting reports, never surface individual-student data (FERPA).

---

## TL;DR — what's collectible

| Layer | Best source | Verdict | Pattern |
|---|---|---|---|
| **A-F letter grades** (scored, per school/district) | `azsbe.az.gov` XLSX | **EASY** | direct .xlsx (UA + Referer) |
| **Assessment / grad / enrollment / EL / absenteeism / per-pupil trends** | **azreportcards.azed.gov undocumented JSON API** | **EASY** | JSON GET, no key |
| **Dropout rate** | walled ADE Excel only | **HARD** | headless browser / FOIA |
| **District finance** — classroom %, per-category $, **teacher salary** | **Auditor General statewide XLSX** | **EASY** | direct .xlsx, all districts |
| **Per-pupil revenue/expenditure, revenue mix, enrollment-decline** | **Urban Institute Education Data API** | **EASY** | REST/JSON, no key |
| **Discipline / suspensions / expulsions by race & disability** | Urban API (CRDC) | **EASY** | REST/JSON |
| **Override / bond + board-race results** | Pima County CSV (CivicPlus) | **MODERATE** | scrape + 302-follow CSV |
| **Board meeting agendas** (8 of 9 districts) | Diligent + BoardBook | **EASY–MOD** | 2 scrapers |
| **Board meeting video** (6 districts) | YouTube | **EASY** | existing `run_live_reporter.sh` |
| **AFRs / detailed budgets** | per-district PDF behind ADE wall | **HARD** | headless + pdftotext |

**Three big cross-cutting gotchas:**
1. **`www.azed.gov` is a Cloudflare *managed JS challenge* wall** (403 to curl AND header-spoofed Chrome — the interstitial is `Just a moment…`). Unlike the Marana/OV UA-only WAFs, header spoofing does **not** work; the walled Excel files need a real headless browser. **The workaround is to avoid it** — the Report Cards JSON API and azsbe XLSX give ~90% of the academic data with zero headless dependency.
2. **`azsbe.az.gov`** (A-F files) needs a browser UA **and** a `Referer: https://azsbe.az.gov/schools/a-f-school-letter-grades` header or you hit intermittent 403s.
3. **Federal data lags 1–3 years** and varies by survey — stamp every figure with its survey year.

---

## District ID crosswalk (verified) — the keys for every dataset

Three different ID systems key the three data worlds. This table is the join spine.

| District | ~Enroll | ADE entity ID¹ | CTDS² | NCES LEAID³ | Agenda platform | Board video |
|---|---|---|---|---|---|---|
| **Tucson Unified (TUSD)** | ~40K | 4403 | 100201000 | 0408800 | Diligent `tusd1-schooldesk.community.highbond.com` | **Livestream.com** (HLS), YT secondary |
| **Sunnyside USD** | ~14.5K | 4407 | 100212000 | 0408170 | **BoardDocs** `go.boarddocs.com/az/susd12` (hard) | YouTube `SunnysideUSD12` ✅ |
| **Vail USD** | ~14.3K | 4413 | 100220000 | 0408850 | Diligent `vailschooldistrict.community.highbond.com` | YouTube ✅ (pilot) |
| **Marana USD** | ~12.3K | 4404 | 100206000 | 0404630 | BoardBook org **1780** | YouTube `@maranaschools/streams` ✅ |
| **Amphitheater USD**⁴ | ~12.4K | 4406 | 100210000 | 0400680 | BoardBook org **2065** | YouTube `@amphitheaterpublicschools4779` ✅ |
| **Sahuarita USD** | ~6.4K | 4411 | 100230000 | 0407300 | Diligent `susd-30.community.diligentoneplatform.com` | YouTube ✅ |
| **Flowing Wells USD** | ~5.4K | 4405 | 100208000 | 0403010 | BoardBook org **1607** | YouTube `@flowingwellsstream5127/streams` ✅ |
| **Catalina Foothills USD** | ~5.2K | 4410 | 100216000 | 0401760 | BoardBook org **1202** | YouTube — **unclear, verify** |
| **Tanque Verde USD** | ~2.2K | 4408 | 100213000 | 0408280 | Diligent `tanqueverdeschools.community.highbond.com` | **none** (in-person only) |

¹ keys the Report Cards JSON API **and** the A-F XLSX `DistrictCode`. ² state CTDS (county code 10 = Pima). ³ federal, keys NCES CCD + Urban API (`?leaid=`). ⁴ "Oro Valley schools" = Amphitheater (no standalone OV district); Catalina = Amphitheater too.

CTDS master list (open PDF): `https://azdor.gov/sites/default/files/document/PUBLICATION_2025_ADESchoolListing.pdf`. Drill to school-level IDs under a district: Report Cards API `GetEntityListByDistrict?districtId={id}&fiscalYear=2025`, or Urban `schools/ccd/directory/{year}/?fips=4`.

---

## A. Academic / accountability data (ADE)

### A1 ⭐ Report Cards JSON API — `azreportcards.azed.gov` — EASY, the spine
The site is a Vue SPA (browser-only as HTML) **backed by an open, unauthenticated JSON API with no WAF.** Plain GET, no key. ~9 districts × ~6 endpoints ≈ 54 cheap calls for a full metro refresh. Base `https://azreportcards.azed.gov`:

- `/api/DataApi/GetFiscalYears` → years **2018–2025** (2025 active; 2020 absent = COVID)
- `/api/Search/GetByName?nameToSearch=x` → full entity→ID lookup table (name→`educationOrganizationId`)
- `/api/DataApi/GetAssessmentTrendData?educationOrganizationId={id}&fiscalYear={yr}` → ELA/Math/Science % proficient by subgroup × year (TUSD = 1,982 rows). ⚠️ `assessmentType` is hard-labeled `"AzMerit"` even for AASA-era years — ignore as a label.
- `/api/DataApi/GetGradRateTrendData` → cohort grad rate by subgroup, 2018–2025
- `/api/DataApi/GetEnrollmentTrendData` → enrollment by grade × subgroup × year
- `/api/DataApi/GetELProficiencyTrendData` (AZELLA), `/GetChronicAbsenteeismTrendData`, `/GetGrowthRate`, `/GetDistrictPerPupilExpenditure`, `/GetTeachersTrendData`, `/CCRI`, `/Post-Secondary`, `/NAEP`, `/CRDC`
- Redacted small-n cells = `-1`/`redacted:1`. **Undocumented → pin fiscal year, validate schema per run.**

### A2 ⭐ A-F letter grades — `azsbe.az.gov` XLSX — EASY
Official scored A-F file, mirrored on the State Board site (not Cloudflare-walled; needs UA + Referer). Newest = **FY25**:
`https://azsbe.az.gov/sites/default/files/2026-06/FY%2025%20Combined%20A-F%20Public%20File%202026-06-16_v20.xlsx` (252 KB, verified). Prior years FY24/23/22/19/16-17 all live at `https://azsbe.az.gov/schools/a-f-school-letter-grades`. Schema: `FiscalYear, SchoolName, SchoolCode, DistrictName, DistrictCode, County, Charter, LetterGrade, Model` + scored components; 3 sheets (K-8 / 9-12 / Alternative). **`DistrictCode` = the Report Cards API entity ID** → joins directly to A1.

### A3 Gaps
- **Dropout rate** — no API endpoint; only in walled `azed.gov` Excel → HARD (headless or FOIA).
- Everything on `www.azed.gov` (bulk Accountability Excel, AASA district file, dropout) = Cloudflare-walled. Student-level AASA = Pearson-login-gated (correctly).
- No `data.azed.gov` open portal (doesn't resolve). The practical "master index" = **A1 API + A2 azsbe XLSX**.

**Reader output:** per-district report card (grade + 5-yr trend), metro A-F leaderboard/map, "which schools dropped a grade," subgroup achievement-gap tables, proficiency/grad/enrollment trend charts.

---

## B. Financial / spending data

### B1 ⭐ Auditor General "School District Spending" XLSX — EASY, best single file
One statewide `.xlsx` covering ALL ~236 districts, per-student spending by category, **classroom %**, peer comparisons, **AND average teacher salary** — satisfies finance + teacher-pay in one download. No WAF.
- Newest (FY25, published 2026-02-26): `https://www.azauditor.gov/sites/default/files/2026-02/AZ_School_District_Spending_FY25_Data_File.xlsx` (563 KB, verified). Prior years each have their own page (FY24/23/22/19/18/17).
- Columns: demographics (county, LD, # schools, special-ed %, EL %, 5-yr enrollment change), classroom (instruction + student/instruction support) vs nonclassroom (admin, plant, food, transport) per-student $, **Instructional Spending % (ISP)** + diff from peer/state avg, **avg teacher salary since FY2017**, assessment pass rates. All 9 metro districts present.
- Headline baked in: FY25 statewide ISP record-low **52.1%**, avg teacher salary **$65,613**.
- Interactive portal `sdspending.azauditor.gov` = 403/WAF — irrelevant, the Excel IS the data.
- ⚠️ Runs **~1 fiscal year behind** on final-actual columns.

### B2 Override / bond + board-race elections — MODERATE
- **Which districts ran measures (prop# → district):** Pima County School Superintendent — `https://www.schools.pima.gov/elections/bond-and-override-election-information` (403s bots; browser UA).
- **Results — structured CSV (the target):** Pima County is authoritative for BOTH board races and school measures (SOS never carries school results). Archive `https://www.pima.gov/2865/Election-Results` → grab "Summary Results (CSV/Excel)" → it's a CivicPlus asset: `https://www.pima.gov/asset/{uuid}` **302-redirects** to `https://content.civicplus.com/api/assets/{uuid}` (follow it). Verified Nov 2024 CSV has columns like `Governing Board - Tucson Unified School District No. 1`, `PROPOSITION 411 - Marana Unified…`. Nov 2025 CSV: Props 414 (TUSD M&O override), 415 (Flowing Wells $30M bond), 416 (Sunnyside $120M bond).
- New election-night SPA (`livevoterturnout.com`) = bot-blocked; ignore, parse the durable CSV.
- **No statewide structured list of currently-active overrides/bonds** — must be assembled from election history + budgets (Ballotpedia is stale, bonds-through-2018 only).

### B3 AFRs / detailed budgets — HARD (deep-dive only)
Standardized USFR-template per-district PDFs; index lives behind ADE's Cloudflare wall (or on each district's own site, ARS §15-904 requires Nov-15 posting). One parser works across districts once you have the files. Lower priority — B1 already gives clean category spending; AFRs only add fund-level detail (bond/capital, food service) for a specific story.

### B4 Skip
`openbooks.az.gov` (WAF + JS dashboard + partial K-12 coverage), `schoolspending.az.gov` (dead, doesn't resolve). AG Excel is strictly better.

**Reader output:** annual **"Where your district's money goes"** + classroom-dollar ranking of the 9 metro districts + teacher-pay comparison (all from B1); override/bond scorecard (B2).

---

## C. Federal data (the cleanest APIs)

### C1 ⭐ Urban Institute Education Data API — `educationdata.urban.org` — EASY, the federal backbone
Wraps NCES CCD + F-33 finance + CRDC + IPEDS in one consistent REST/JSON interface, **no API key**, paginated. Make this the backbone; drop to raw NCES bulk only for a year Urban hasn't ingested.
- Base: `https://educationdata.urban.org/api/v1/{level}/{source}/{topic}/{year}/[disaggregators]/?[filters]` (`?fips=4` = AZ, `?leaid=0408800` = one district)
- **CCD directory/enrollment** (FRPL, demographics) → newest **FY2023**. e.g. `…/school-districts/ccd/enrollment/2022/grade-12/race/sex/?leaid=0408800`
- **F-33 finance** (per-pupil revenue/expenditure, revenue mix) → via Urban newest **FY2020** (`count:0` for FY21); raw NCES F-33 has FY2023. e.g. TUSD FY2020: rev_total $518.1M, exp_total $457.7M → ~$11,143/pupil.
- **CRDC discipline** by race/disability/sex → newest **2020-21 SY** (2020-21 was COVID-depressed — flag). Equity cut: `…/schools/crdc/discipline/{year}/disability/race/sex/?leaid=0408800` → suspensions/expulsions/arrests/law-enforcement-referrals per school × subgroup. Also restraint-seclusion, harassment, AP/IB access, chronic absenteeism.
- Endpoint catalog is itself an API: `…/api/v1/api-endpoints/`. Docs: `educationdata.urban.org/documentation/`.

### C2 Raw NCES (newer-year fallback) — MODERATE
CCD flat files `https://nces.ed.gov/ccd/files.asp`; F-33 `https://nces.ed.gov/ccd/f33agency.asp` (newest SY2022-23). Flat CSV/fixed-width, no JSON API — why Urban is preferred.

### C3 NAEP / EDFacts / IPEDS — limited local value
NAEP API works (`nationsreportcard.gov/Dataservice/GetAdhocData.aspx?...jurisdiction=AZ...`) but is **state-level only — no AZ district in TUDA**, so no Tucson/TUSD NAEP. Use as statewide backdrop only. EDFacts → use Urban's `edfacts` source, but ADE (A1) is fresher for district proficiency/grad. IPEDS = higher-ed, skip (only K-12-adjacent angle = local-grad college outcomes).

**Reader output:** enrollment-decline tracker (TUSD ~42K and falling — pairs with the **ESA voucher** story), per-pupil spending + revenue-mix comparison across the metro, discipline-equity analysis by race/disability.

---

## D. Board meetings (from COVERAGE-EXPANSION.md, now verified + corrected)

**8 of 9 districts with two scrapers.** Corrections to the prior plan:
- **TUSD portal corrected** → `tusd1-schooldesk.community.highbond.com` (the guessed `govboard.tusd1.org` is a hub page; old `go.boarddocs.com/az/tucsonusd` is DEAD as of Jan 31 2026).
- **Sunnyside is NOT NovusAGENDA** — migrated to **BoardDocs** (`go.boarddocs.com/az/susd12`, DB key `susd12`); **403s bots, JS/AJAX — the hardest adapter of the nine** (needs headless or reverse-engineered AJAX). Novus still resolves but shows "No records."
- **Diligent (4):** TUSD, Vail, Sahuarita (on `diligentoneplatform.com` host), Tanque Verde. One adapter, two host variants. Portal calendars are JS-rendered, but `/Portal/MeetingInformation.aspx?Org=Cal&Id={n}` is server-rendered HTML and IDs are small sequential ints; agendas/minutes as direct PDF (`/document/{docId}/{slug}/?printPdf=true`).
- **BoardBook (4):** Amphitheater 2065, Marana 1780, Catalina Foothills 1202, Flowing Wells 1607. Server-rendered HTML (cleanly scrapable, no SPA), direct-PDF verified: `https://meetings.boardbook.org/Documents/DownloadPDF/{GUID}?org={ORG_ID}`. **Lowest-lift adapter.**

**Board video for AI reports (`run_live_reporter.sh`):** 6 clean YouTube YES — **Vail, Marana, Amphitheater, Sahuarita, Sunnyside, Flowing Wells**. Best `/streams` targets: Marana, Flowing Wells, Sahuarita. **TUSD = Livestream.com (HLS)** → use the Swagit-style `--direct` ffmpeg path, not YouTube/streamlink. Catalina Foothills unclear (verify), Tanque Verde none. Note: school streams are typically scheduled live *events* (per-meeting watch URLs), not a channel-level `/live` redirect like Pima County — may need to resolve the upcoming live-event URL per meeting.

---

## Build order (recommended)
1. **EASY data wins, ship first (no headless, no WAF):**
   - **Auditor General XLSX** → "Where your district's money goes" + classroom-$ ranking + teacher-pay comparison (one download, highest value/lowest lift in the whole catalog).
   - **Report Cards JSON API + azsbe A-F XLSX** → per-district academic report cards (grades, proficiency, grad, enrollment trends).
   - **Urban API** → enrollment-decline + per-pupil + discipline-equity.
   → one `school_data.py` poller (9 districts × the above APIs) feeds Around Town cards, charts, RAG, and originals.
2. **Meeting coverage pilot = Vail USD** (Diligent + YouTube → preview AND post-meeting report day one; Vail Chamber warm launch). One Diligent adapter then yields TUSD/Sahuarita/Tanque Verde nearly free; BoardBook adapter adds the other 4.
3. **Override/bond scorecard** (Pima County CSV) — election-cycle cadence.
4. **Deep-dive only:** AFR PDFs, dropout, full demographic cross-tabs (all behind the ADE Cloudflare wall → headless browser when a specific story needs them).

## Signature original-reporting threads this unlocks
- **ESA vouchers vs. district enrollment** — universal AZ ESA since 2022; track district enrollment decline (Urban/ADE) against the funding/student shift. Biggest AZ ed story, thinly covered locally.
- **"Dollars in the classroom"** — annual AG drop, auto-generate per-district (52.1% statewide and falling).
- **Discipline equity** — CRDC suspension/expulsion disparities by race/disability per district.
- **Override/bond accountability** — who's asking voters for money, who passed/failed, and what it funds.
- **A-F + achievement gaps** — make the wide outcome spread across Pima districts legible.

## Side task
Extend `pipeline/local_names.json` with the 9 districts' board members + superintendents (helps the AI meeting-reporter + RAG get names right — same pattern that fixed municipal transcriptions).

---

*Reconstructed from 4 parallel research agents, all endpoints fetched live 2026-06-26. Pairs with COVERAGE-EXPANSION.md Part 1C (meeting-coverage plan) and the municipal data feasibility docs.*
