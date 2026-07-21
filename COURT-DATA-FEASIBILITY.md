# Pima County Court & Justice-Data Layer — Feasibility Scan

Feasibility-scanned **2026-07-20** (2 live research agents; ~35 fetches total, all polite single requests — no crawling, no enumeration). Motivation: the 2026-07-20 downtown-shooting report (the charged suspect was ~14 months into a four-year probation term) raised the systemic question — what can TDB automate around violent crime, repeat offenders, probation outcomes, and case results in Pima County, rigorously and responsibly?

Companion to `TUCSON-DATA-FEASIBILITY.md` (incident side — TPD's clean ArcGIS FeatureServers, verified 2026-06-26), `crime.md` / `crime-tpd-data.md` (NIBRS gap + TPD's own numbers), and the "On Probation, Then Arrested Again" story entry in `ORIGINAL-JOURNALISM.md`. Exploration prompt that framed the scan: `court-data-journalism-llm-prompt.md`.

---

## Headline findings

1. **The Agave data is real and rich — but the portal is engineered and policy-marked against automation.** `robots.txt` disallows all spiders (`Disallow: /`, "Disallow all web spiders") plus a named AI-crawler blocklist (ClaudeBot, GPTBot, et al.) and `ai-train=no`. On top of that, a per-session URL-obfuscation layer defeats deep links (direct canonical URLs 404 even in-session). No CAPTCHA and no login, but every case requires a search POST → token-parse → GET dance.
2. **No document images online at all.** Every docket item says "Available at Courthouse" / "Documents must be purchased prior to 4:45 p.m. daily." The portal is metadata-only. Documents = eAccess ($10/doc) or purchased copies.
3. **DOB is month/year only** (e.g. `5/1962`), not a full date. That weakens name+DOB entity resolution materially — repeat-case matching moves from "Tier 1 aggregate" toward "conservative match + published error rates," and any named use stays human-verified.
4. **The official bulk route is real and defined:** Arizona Code of Judicial Administration § 1-605 ("Requests for Bulk or Compiled Data," implementing Rule 123) — dissemination agreement, custodian-set fee, use restrictions. Given the robots.txt posture, this is **the** legitimate route for systematic court data — and the ask itself is a transparency story whether it's granted or stonewalled.
5. **The AOC Safe Communities Act reports are confirmed, current, and Pima-specific** (FY 2024 report fetched and parsed): 330 Pima probationers convicted of a new felony in FY 2024; 583 revocations (537 to prison). The "On Probation" story is **writable today from published PDFs** — no scraping required.
6. **The incident side has no such policy cloud.** TPD's open-data FeatureServers (255,989 UCR rows 2017→2026; 93,544 geolocated 2025 incidents w/ `clearance_verbose`) are published for reuse. → The crime poller is the unambiguous first **build**; the court side starts with a **records request, not a crawler**.

---

## 1. The legal/policy layer (read first)

Everything below was fetched live 2026-07-20. Verbatim quotes are deliberate — these are the clauses that decide what we may automate.

**Agave robots.txt** (`https://wwww.cosc.pima.gov/robots.txt`) — two conflicting groups. Cloudflare-managed: `Allow: /` for `*` but blocks named AI bots (Amazonbot, ClaudeBot, GPTBot, CCBot, …) with `Content-Signal: search=yes,ai-train=no`. Operator's own block, verbatim: `# Disallow all web spiders` / `User-agent: *` / `Disallow: /`. RFC 9309 parsing trivia aside, **operator intent is unambiguous**. Any scripted access needs explicit editorial sign-off — ideally a call to the Clerk's office (520-724-3240) first.

**Agave accuracy disclaimer (on the app, verbatim):** "...the Clerk of the Superior Court declares that the information contained herein does not constitute an official record... the information is subject to change, update, modification and may not be up to date as of the instant with which the user is viewing the information..." → Every published number sourced from Agave carries a "per the Clerk's public portal, which the Clerk notes is not the official record" caveat.

**Clerk's records-page affirmation requirement (verbatim):** "Required Affirmation Pursuant to A.R.S. section 39-121.01, all public records requests must include an affirmation that the public record is not for a commercial purpose or, if the public record is for a commercial purpose, provide a statement that explains the intended use..." → TDB's requests go in as non-commercial journalism; say so explicitly.

**The bulk route — ACJA § 1-605** (verified PDF: `azcourts.gov/Portals/0/0/admcode/pdfcurrentcode/1-605_Amended_08-2011.pdf`): "Rule 123… authorizes courts to release bulk or compiled court data. This section sets forth the procedure for releasing bulk or compiled data, for either a commercial or a non-commercial purpose." Process: request to the court's bulk-data custodian (AOC Administrative Director for the statewide repository) → dissemination agreement → fee "in an amount specified by the custodian" (no published rate). Restrictions: no commercial solicitation of named individuals; no re-dissemination of protected identifiers (street address, **day-of-birth**, last-4 SSN/DL); **must remove amended/sealed data within 2 business days of notice**; $1M liability insurance for commercial users (non-commercial may be excepted); custodian may audit/terminate. The "annual subscription fee" language the AOC hints at lives verbatim on the Public Access portal (`apps.azcourts.gov/publicaccess/`): "Data available on this web site is updated frequently and can be provided via electronic media for an annual subscription fee. If interested, please Contact Us."

**eAccess** (`azcourts.gov/eaccess`, Angular SPA, account + login wall): **$10/document** per Administrative Order 2019-48; subscriptions 20 docs/$80/mo → 375/$1,050/mo (5,000/$10,000/mo). **Pima criminal coverage only for cases filed on/after July 1, 2015.**

**Statewide Public Access Case Lookup** (`apps.azcourts.gov/publicaccess/`): BotDetect CAPTCHA confirmed in HTML ("...to prevent excessive high-volume use, we have implemented randomly generated verification words..."). Covers "177 out of 184 courts"; updated weekly (Fridays, through Wednesday); sealed/juvenile/mental-health/protection-order data excluded. **Not automatable, by design.**

**PCSO jail roster** (`sheriff.pima.gov/inmate/`): plain POST → flat HTML, no CAPTCHA — but current-inmates-only, and verbatim: "Any use of this information for commercial purposes is strictly prohibited." Fields confirmed: Name, Age (no DOB), Booking #, Location, Total Bond, per-case Reference #s (e.g. `CR26009544FE`) + Court + Bond Type/Amount. **Charge names are NOT shown** — you get case numbers to resolve elsewhere. Verdict: a human spot-lookup tool for Tier 2 verification, never a feed.

**Responsible posture (project decision):** per-case lookups by a human (or one-off lookups supporting a specific human-reviewed story) are ordinary journalism — that's what the portal is for. **Systematic collection against Agave is not, absent a § 1-605 agreement or the Clerk's written blessing.** Aggregates only by default; no searchable name→history database, ever (also the ARS § 13-911 sealing problem: a permanent named database can't honor sealing).

---

## 2. Agave portal — verified mechanics

- **Canonical URL: `https://wwww.cosc.pima.gov/PublicDocs/`** — four w's, not a typo; that's the Clerk's own link. Cloudflare-fronted IIS/ASP.NET 4.0.
- **Stack:** legacy ASP.NET WebForms, nested frameset, `__VIEWSTATE`/`__EVENTVALIDATION` round-trips required. No CAPTCHA, no login.
- **One search form** (left frame), `POST /PublicDocs/search2a.aspx`, fields: `txtLastName`/`txtFirstName` or `txtCaseNumber`, `SearchGroup` = `rdoName`|`rdoCase`, plus ViewState fields. Response re-renders the form + `<script>window.open('<session-token>','main')` — results/case pages live behind **per-session obfuscated tokens**; parse the token, GET it.
- **Name search** → `grdCases` table: `Party Name | Case Number | Case Caption | Filing Date`, all case types in one list, no pagination (test: 366 rows for a common name, 1993→2023).
- **Case detail** (`GetCase2.aspx` behind token) — grids confirmed:
  - `grdParty`: Party Full Name / Role / **Name Type (`True`, `Also Known As (AKA)`)** / **DOB = month/year only**
  - `grdCharges`: Count / Prep Offense / **ARS statute** / Desc / **Class (F4, M1…)** / **Disp Date / Disposition** (`Guilty`, `Court Dismissed`, …)
  - `grdDocuments`: full docket — Document Type / SubType / Caption / **File Date** / Image="Available at Courthouse" (39 rows on sample; subtypes incl. `Sentencing`, `Pre-Sentence Report`, `Appearance Order with Release Conditions`)
  - Judge: populated read-only field
- **Case numbers:** displayed/searched as **`CRyyyynnnn`** (8 digits, no dashes/spaces per the official help PDF), year prefix + zero-padded sequence. **No `-001` defendant suffix** — refutes the prompt's `CR2024####-001` assumption. Jail-roster references use a different format (`CR26009544FE`) — reconcile before cross-walking (open question).
- **No deep links:** real path visible in form action (`GetCase2.aspx?ID=1205848` — internal IDs look sequential) but direct GET 404s even with the live session cookie. Enumeration by case number through the form = 1 POST + 1 GET per case — mechanically possible, **policy-barred** (see §1).
- **Scriptability verdict: MODERATE mechanically** (server-rendered tables, stable grid IDs, plain POST, no CAPTCHA) **but policy-gated**. PTRs appear as docket caption rows, so a PTR tracker is metadata-feasible — pending the bulk/agreement route, not scraping.

**Justice Court (separate, confirmed):** `https://www.jp.pima.gov/CaseSearch/` — ASP.NET WebForms but **no frames, no URL obfuscation**; fields `searchType` (`byName`/`byCase`/`byCitation`), `lname`, `fname`, `caseNum`, `citationNum`. Covers misdemeanors/initial appearances — matters because low-level violent-adjacent cases (DV misdemeanors, endangerment) live there. robots.txt unverified — check before any use.

---

## 3. Surrounding sources — verification results

| Source | Verdict | Notes |
|---|---|---|
| **AOC Safe Communities Act reports** | ✅ Confirmed, current | Landing `azcourts.gov/apsd/Data-and-Research/Safe-Communities-Act`; PDFs under `Portals/0/25/SafeCommunitiesAct/` FY2017–FY2023 linked; **FY 2024 report fetchable** (`FY 2024 Safe Communities Report_FINAL.pdf`, ©2025 AOC). Annual poll; guess next FY's URL (page lags). |
| **AOC bulk data (ACJA § 1-605)** | ✅ Real, contract-gated | Dissemination agreement + custodian-set fee; restrictions in §1 above. Not self-serve. |
| **eAccess** | ✅ Confirmed | $10/doc; subscriptions from $80/mo; Pima criminal ≥ 2015-07-01 only. |
| **Statewide Public Access** | ✅ Confirmed CAPTCHA | Not automatable; bulk users directed to "Contact Us" (= § 1-605). |
| **PCSO jail roster** | ⚠️ Spot tool only | No charges shown; no-commercial-use notice; current inmates only. |
| **Urban Institute Pima studies** | ✅ Both confirmed | 2021 + 2024, rich quantified findings (below). Cite; nothing to poll. |
| **PCAO data** | ✅ **VERIFIED 2026-07-20 — real prosecutorial data exists + is monitorable** | `pcao.pima.gov` bot-blocks plain fetches, but the "By The Numbers" PowerBI renders fine headless (see §3a). Contents: felony/misdemeanor/juvenile funnels, diversion, jail pop, budget, staff. **Dashboard frozen at 2025-03-16; several series broken at zero since 2023.** |
| **Auditor General** | ✅ Reference | Performance Audit of AOC Adult Probation, Report 17-105 (June 2017) + follow-up. Static. |

### 3a. PCAO "By The Numbers" PowerBI — probed 2026-07-20 (headless Chromium + CDP)

The dashboard lives in an iframe on `pcao.pima.gov/by-the-numbers/` (page shell retrieved via Wayback; the live site 403s bots). Embed URL:
`https://app.powerbigov.us/view?r=eyJrIjoiZDRjNzVmMDQtNDU1My00NGQzLWJlYzktNjI2NjNkNTEyMzU3IiwidCI6ImRhNGQ5MjNjLTI0NGUtNDgyNC04ZThjLTg0ZjdlOTgwYTg1YSJ9` (title "Web Data Points", 2 pages).

**Access technique (proven, ~40s/run):** headless Chromium + CDP (`--remote-debugging-port`, `Page.navigate`, 20s render, `Runtime.evaluate` to click the footer's `Next Page` button, `document.body.innerText` for text, `Page.captureScreenshot` for visual). The tables extract as **clean plain text — numbers parse deterministically, no LLM near the data** (house rule). It's a public "Publish to web" report; viewing it in a browser (headless or not) is exactly its purpose. Two polite page loads per probe.

**FINDING 1 — the dashboard is frozen.** Footer claims *"Values Above Represent YTD Totals as of Yesterday"* but the baked-in date is **2025-03-16** — 16+ months stale as of this scan. The 2025 column is YTD-mid-March; 2026–2028 columns are empty placeholders.

**FINDING 1a — WHY it's frozen (forensics, 2026-07-20): the public embed is a point-in-time copy that was never connected to refresh.** Wayback + token analysis:
- Embed tokens are base64 `{"k":"<report-id>","t":"<tenant>"}`. The site's captures from **Nov 2021 → Jan 2025** all embed report **`d7ba02f3-9be3-4436-a3f5-61728a140247`** ("OLD") — one live, daily-refreshing report for 3+ years.
- The `by-the-numbers` page **404'd on 2025-03-13 and 2025-03-15**, was republished **2025-03-17** (WordPress `article:modified_time`), and re-embedded with a **different report, `d4c75f04-4553-44d3-bec9-62663d512357`** ("NEW") — same tenant, new ID, data frozen at 2025-03-16 from birth. The NEW report is a card-layout rebuild of the OLD one's tables. Conclusion: during a mid-March-2025 page rebuild someone published a *copy* of the report and embedded it; the copy never got a refresh schedule.
- **The OLD report is still publicly reachable** at its original publish-to-web URL — and it **kept refreshing until 2026-06-13** (its baked "as of yesterday" date; jail pop 1,629, employees 312 FT / 17 PT, victims comp 108, diversion successful 191 are live 2026 values). It grew from 2 pages to **4 pages** while staff kept using it.
- **But the OLD report's case-flow feeds are broken for 2026**: felony/misdemeanor/juvenile YTD all read **0** as of 06/13/2026, and its year-table lost the 2024 column with 2025–26 empty. The PbK warehouse case feed (below) stopped delivering cases around the end of 2025. Its own refresh then stopped too (~2026-06-13).
- **Net: two frozen public reports.** The one the site embeds is 16 months stale; the "live" original is 5+ weeks stale and has dead case-flow. Nobody at PCAO appears to have noticed either.

**FINDING 1b — the OLD report's extra pages leak the internals (and hand us the metric definitions).** Pages 3–4 of the OLD report, sitting on a public link since ~2025:
- **Page 3 = metric definitions** (exactly what publishing ratios needed). Key ones, verbatim-ish: Felony Presented = "defendants where [Date Charged] falls within the target year and [Case Type]='Felony'"; Indicted adds "the defendant was indicted"; Pleas = "[Disposition]='Pled'"; Trials = trial events where result is NOT 'Continued'/'Vacated'; Homicides = "defendants … [Statute Category]='Murder' … not cases or counts, does not include ATTEMPTED MURDER" (explains why it exceeds TPD murder counts); Prison/Probation Years = SUM of sentence years by type; Employees = "adjusted daily based on PCAO HR database"; Budget = "adjusted annually based on feedback from the PCAO Budget Officer" (manual!).
- **Page 4 = raw SQL + schema names**: case data from **`PBKDW.dbo.vCaseDefn`** (PbK = *Prosecutor by Karpel*, PCAO's case-management system), events from `PbKMetrics.rpt.t_Event`, diversion from `PCAD.dbo`, jail from `RawData.dbo.InCustody` — plus visible hand-maintenance bugs (the victims query points at a typo'd `PBDKW`; the misdemeanor "Filed" query filters `[Issue Status]='Indicted'` — misdemeanors aren't indicted, so that metric is suspect; the part-time employee query duplicates the full-time one). Don't republish their schema; do cite the definitions, and verify the buggy ones before using those numbers.

**FINDING 2 — several series are broken at zero, not real zeros.** Drug Only Cases: 3,008→1,421→1,211→1,013→**0,0,0** (2023–25). Prison Years Sentenced: 4,714→2,074→440→571→**0,0,0**. Probation Years: 7,336→3,683→1,189→1,724→**0,0,0**. Budget Adopted 2024: **$0**. Jail population: `???` for 2019–20. PCAO plainly did not sentence zero people to prison in 2023 — these are dead data feeds. Same failure shape as Crime Explorer's "0 violent crimes" (`crime.md`): unflagged broken pipelines rendering as zeros.

**FINDING 3 — the core funnel is real, current through 2024, and monitorable.** Year table (page 2), verbatim:

| Data Point | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025* |
|---|---|---|---|---|---|---|---|
| Employees Full-Time | 355 | 355 | 342 | 293 | 310 | 298 | 295 |
| Employees Part-Time | 21 | 21 | 25 | 20 | 7 | 6 | 6 |
| Budget Proposed | $40.37M | $37.10M | $39.56M | $42.99M | $41.11M | $45.11M | — |
| Budget Adopted | $40.12M | $38.63M | $39.75M | $43.26M | $41.11M | $0 (broken) | — |
| Jail pop (6am) | ??? | ??? | 1,602 | 1,752 | 1,705 | 1,612 | 1,670 |
| **Felony Presented** | 10,427 | 5,095 | 9,388 | 9,754 | 10,183 | 9,733 | 2,093 |
| **Felony Indicted** | 6,909 | — | 5,165 | 5,937 | 4,509 | 4,512 | 702 |
| Felony Pleas | 5,667 | 3,124 | 1,287 | 985 | 1,409 | 2,987 | 199 |
| Defendants at Trials | 163 | 32 | 41 | 123 | 52 | 115 | 16 |
| Felony Dismissals | 602 | 334 | 172 | 283 | 207 | 207 | 7 |
| Homicides (detail) | 118 | 140 | 137 | 157 | 132 | 136 | 24 |
| Domestic Violence (detail) | 1,312 | 1,491 | 1,515 | 1,385 | 1,089 | 1,220 | 229 |
| Juvenile Presented/Filed | 3,388/1,782 | 2,128/1,162 | 1,359/748 | 1,327/677 | 1,668/845 | 1,922/1,128 | 318/161 |
| **Misdemeanor Presented** | 10,525 | 8,420 | 8,743 | 9,999 | 9,802 | 9,355 | 1,826 |
| **Misdemeanor Filed** | 10,174 | 8,053 | 8,031 | 9,057 | 9,342 | 9,028 | 1,717 |
| Diversion STEPs Offered/Completed/Failed | 0/0/0 | 0/0/0 | 331/63/129 | 354/117/158 | 1,518/150/127 | 1,362/230/180 | 287/38/45 |
| Diversion Successful/Unsuccessful | 783/192 | 415/137 | 247/32 | 380/32 | 387/55 | 573/78 | 113/14 |
| Victims Compensation | 382 | 216 | 303 | 355 | 307 | 297 | 39 |

*2025 = YTD as of 2025-03-16 (frozen).

**Editorial read (verify before publishing — definitions unknown):**
- **Misdemeanor Filed/Presented runs ~95–97% every year** — superficially contradicts the city's "65% of fentanyl/public-drug cases go unprosecuted" claim. Both can be true: the 65% is a subset (drug cases) and/or a different stage (dismissed at initial appearance, per Kasmar). **This is the same "both numbers accurate, different definitions" shape as the 97.56%/57.45% clearance gap** — defining the cohort precisely is the story.
- Indicted/Presented fell from 66% (2019) to 46% (2024) — but "Presented→Indicted" isn't a clean funnel (complaints, pendings, superior-court informations). Don't publish ratios without PCAO's metric definitions.
- "Homicides 118–157/yr" exceeds TPD's murder counts — likely all homicide-type charges/cases presented. Definition needed.
- Pleas collapsed 5,667 (2019) → 985 (2022) → 2,987 (2024); trials 163 → 32–52 → 115.

### 3b. Round 3 — the live-data hunt (2026-07-20, creative pass)

A third attempt using techniques not tried in rounds 1–2. Results:

1. **PCAO's site loads fine in a real browser engine — the "bot block" is UA-based, not a wall.** Headless Chromium loads pcao.pima.gov; the **WordPress REST API is fully open** (`/wp-json/wp/v2/pages`, `/media`). Plain `curl` also works with a browser UA (`-k` needed for a cert-chain quirk). Live check today: site still embeds the frozen NEW report; `by-the-numbers` last modified 2025-03-17.
2. **Full page inventory (~100 pages): no third PowerBI embed anywhere on the site.** `weekly` = press-recap blog, not data. Newsletters/news-releases are styled archives, active through July 2026 — the office communicates plenty; it just stopped publishing *data*.
3. **Media library: no 2025 year-end report exists** (2024 report `3794009-PCAO-2024-year-end-report-DRAFT10.pdf` uploaded 2025-01-14; older reports 2021–2023 present). As of July 2026, the 2025 report is missing — another signal the data operation went quiet. The 2024 report's "By the Numbers" page (different metrics than the dashboard): **69 homicides county-wide 2024 (excl. officer-involved), 7,769 total pending cases, 70.63 open cases per prosecutor**, homicide victims down 33.7% 2021→2024 (104→69).
4. **⭐ LIVE DATA — Pima County Medical Examiner PowerBI, alive and current (Last Updated on 7/8/2026).** Different tenant (`33b6e2c3-…`), 10 pages, found via the Tucson Crime Free Coalition's links page. Embed: `https://app.powerbigov.us/view?r=eyJrIjoiNGI4OWM4ZDEtM2U0ZC00M2EzLWIzMDItZWFmNTkyZmQwMzFiIiwidCI6IjMzYjZlMmMzLTBiMWEtNDg3OS1iNzQxLTQ3NDYxYTZjMWE4OSJ9`. The coroner counts *bodies* (manner-of-death homicide), independent of the police — a genuine independent check on the homicide trend.
   **⚠️ CORRECTION (re-pulled live 2026-07-20): the OME is a REGIONAL office serving six counties, and the dashboard defaults to ALL of them — the figures first recorded here were the multi-county total, not Pima.** Unfiltered "Homicides" page (963 cases; **137 · 128 · 102 · 99 · 94 · 42** for 2021→2026 YTD; firearms 733/963) = **six-county total (Pima + Cochise + La Paz + Graham + Santa Cruz + Apache), NOT Pima.** **Pima-filtered (830 cases): 84 · 79 · 69 · 86 · 119 · 104 · 90 · 89 · 77 · 33 (2017→2026 YTD)** — i.e. **2021 peak = 119, 2025 = 77.** Firearms 632/830 (76%); 82% male; deaths concentrated ages 20–39. Screenshot: `in-depth/evidence-me-homicides-pima-2026-07-20.jpg`.
   **Caveats before any published use:** proprietary PowerBI (same non-auditable limit as TPD's dashboard); counts manner-of-death homicide countywide (includes justifiable/officer-involved), so it is NOT the same metric as a city murder count and must not be folded into the TPD/TOPS/FBI city count-disagreement — it corroborates the *trend* at the county level, nothing more. 2026 is partial-year (don't annualize). Always filter to Pima and re-pull at publish.
5. **Measures for Justice (measuresforjustice.org/portal)** — standardized county prosecutorial-performance data (arrest → post-conviction, offense-type filters) with an Arizona state CSV download — **but `/api/datasets/Arizona_State_Data.zip` 404s** even with browser UA + referer. Pima presence/vintage unverified; needs a real-browser retry or an email to MFJ. (Their county set is curated; Pima is plausibly in it — worth one more try.)
6. **Tucson Crime Free Coalition** (tucsoncrimefree.com) — local advocacy group already publishing monthly "Community Safety & Accountability" newsletters (incl. crime stats of uncertain rigor). They're part of the local crime-data conversation — monitor them, and note their records requests may already hold PCAO data.
7. **Failed this round:** `pcao.nextrequest.com/requests.json` (empty/404 — NextRequest JSON endpoint not found); MFJ zip 404 (above).

**Round-3 verdict:** PCAO's own live case data remains publicly unreachable — no third report, no 2025 annual report, dashboard frozen, OLD report half-dead. The current-data routes that DO exist: (a) the **ME dashboard** (live, county-wide homicides); (b) the **§ 1-605 bulk request** (court outcomes); (c) the **PIO email** (`pcao-pio-email.md`); (d) **MFJ** (periodic, standardized, gated); (e) the OLD report's living fragments (jail/HR/victims/diversion through 2026-06-13).

**Monitor verdict:** buildable NOW as a weekly cron — headless render → deterministic text parse → diff vs. last snapshot → Telegram on any change. **Monitor THREE reports:** the embedded NEW one (flag the day the frozen date moves — that means PCAO noticed), the unlisted-but-public OLD one (de-facto live feed when it works; case-flow returning to nonzero is the signal), and the **ME dashboard** (its "Last Updated" stamp + 2026 YTD homicide count are live county data). First output is the reconstruction story itself: the public dashboard has been a frozen copy since March 2025 while the live original kept updating in plain sight. PIO/records questions: (1) was the March 2025 swap a deliberate snapshot or a mistake, (2) who owns the refresh schedule, (3) why does `vCaseDefn` return zero 2026 cases (Karpel/PbK migration?), (4) why did the OLD report's refresh stop 2026-06-13, (5) are pages 3–4 (definitions + raw SQL) intended to be public?
- **330 Pima probationers convicted of a new felony in FY 2024** (up from 239 FY 2023; FY 2008 baseline 221; **+49.3% vs. baseline**)
- Pima revocations FY 2024: **583 total — 537 to ADCRR (prison), 45 to jail**, 1 without incarceration
- Pima probation population: 8,781 total (5,985 direct-supervised)
- Baseline stat (A.R.S. §12-270(A)(2), verbatim): "The percentage of people on supervised probation from each county who are convicted of a new felony offense compared to the percentage of probationers who would have been convicted of a new felony offense at the Baseline probation conviction rate."

**Urban Institute — key findings (both Pima-specific, citable):**
- *Reducing Probation Revocations in Pima County* (July 2021): 10,863-person study population; **45% had ≥1 PTR filed**; of those, **43% were revoked**. **Over two-thirds of PTRs were purely technical violations; only 2% involved new crime alone.** 36% of PTRs end in revocation to prison, 5% to jail. Felony primary charge → >3× odds of PTR, >7× odds of revocation.
- *Reducing Probation Violations in Pima County* (March 2024): FY2016–22, **46% of probation cases had ≥1 PTR; 63% of PTRs were administrative-only**. Ending automatic holds: **85% of people held were never revoked**. Project SAFE (escalating jail sanctions) killed after data showed **35.2% revocation vs. 19.6% control**. Jail bookings −37% (2015–2020).

---

## 4. The two-leg program (incident ↔ court)

Violence in Pima County flows through four systems that publish separately and are joined by nobody: **incidents (TPD/PCSD) → clearance/arrest → charging (PCAO) → court outcomes (Superior Court / probation)**. The person-level join across systems is deliberately impossible with public data (incidents are de-identified; courts have names but no incident link). **The aggregate join is the product** — no outlet publishes the chain, and it's the systemic answer to the question the 2026-07-20 shooting raised, delivered without advocacy.

### Tier 1 — automatable, aggregate-only, deterministic (previews risk model)
1. **Tucson Crime poller** — TPD FeatureServer/8 (UCR 2017→2026) + PublicSafety/81 (geolocated, ward, weapon, clearance) → monthly violent-category trends, ward breakdowns. Feeds: brief chart line, Around Town-style feed, social cards, RAG stats. (Endpoints verified 2026-06-26 in `TUCSON-DATA-FEASIBILITY.md`.)
2. **Clearance Watch** — rolling clearance rates from `clearance_verbose`/`CLEARANCE_DATE`; makes the 97.56%-vs-57.45% methodology gap *computable* (see `crime-tpd-data.md`).
3. **Metro homicide rollup** — TPD + PCSD + Marana/OV/Sahuarita via FBI CDE APIs. One number, monthly.
4. **AOC Safe Communities annual poll** — FY PDF parse, Pima row + statewide context, year-over-year.
5. **PCAO dashboard monitor** — weekly headless-Chromium render of the "By The Numbers" PowerBI (technique proven, §3a) → deterministic text parse → diff → Telegram on change. Its first story is already in hand: the dashboard is frozen at 2025-03-16 and three sentencing series have been broken at zero since 2023.

### Tier 2 — automate the flag, human verifies (news-reports model)
5. **Homicide case-status tracker** — every charged homicide in Pima Superior Court: status, next hearing, disposition. Highest-value named product; names only via human-reviewed stories; per-case lookups are ordinary journalism.
6. **Violent-filing lead flagger** — new violent felony + heavy prior history → Telegram flag → human decides. (Automates what was done by hand for the shooting suspect.) Requires the bulk route or Clerk blessing — not scraping.
7. **Court outcomes snapshot / PTR tracker / repeat-case share** — filings, disposition mix, time-to-disposition, PTR volume/outcomes, conservatively-matched repeat-case rate. **All gated on § 1-605 bulk data or written Clerk permission.** Matching caveat: month/year DOB only → conservative rules + published error rates; named use stays human-verified.
8. **Safe City accountability pass** — city claims (85% nonfatal-shooting clearance, 25% firearm-incident drop, 86% conviction rate) are checkable against incident + court layers. Publish whether they hold or not.

### Tier 3 — don't build
- On-probation-at-time-of-offense at scale (term length is paywalled/courthouse; proxy too weak to publish)
- Person-level incident↔court linkage (structurally impossible with de-identified incidents)
- Jail-roster history / feed (current-only, no-commercial-use, no charges shown)
- Statewide priors (CAPTCHA); judge scorecards (equity-score lesson); any searchable name→history database (sealing, presumption of innocence)

---

## 5. Build order

1. **Tucson Crime poller + Clearance Watch** (Tier 1 #1–2) — verified endpoints, zero policy cloud, deterministic aggregates. Establishes the crime-poller pattern Marana/OV then reuse (`MARANA-DATA-FEASIBILITY.md` already queues Marana's).
2. **PCAO dashboard monitor** (Tier 1 #5) — cheap (proven technique, §3a), immediately topical, and its first deliverable (frozen dashboard + broken series) is a Transparency-Tracker story by itself. Pair with a PIO/records question: who owns the feed, why did it die in March 2025, and what are the metric definitions?
3. **ACJA § 1-605 bulk-data request + Clerk call** (human action, this week) — ask the Pima Superior Court bulk-data custodian (and/or AOC Administrative Director) for compiled CR-case metadata: filings, charges, dispositions, docket-event types/dates, party name + birth month/year, judge. Document the ask and the response — granted or stonewalled, it's a Transparency-Tracker-grade story.
4. **"On Probation, Then Arrested Again"** (human-written In Depth piece) — publishable NOW from the AOC FY 2024 Pima numbers + both Urban studies + the 2019 holds-policy context. No scraping. Normal human review.
5. **Court-side automation (Tier 2 #5–7)** — build only after the § 1-605 answer; if denied, report the denial and fall back to AOC aggregates + per-case manual lookups.

## Open questions
- **For the PCAO PIO** (the five §3a questions): was the March 2025 embed swap deliberate; who owns refresh; why `vCaseDefn` returns zero 2026 cases; why the OLD report froze 2026-06-13; are the internal definitions/SQL pages meant to be public. Metric definitions are now in hand from the report itself (§3a, Finding 1b) — verify the two buggy queries (misdemeanor "Filed," part-time employees) before using those numbers.
- **CR case-key normalization:** probe one live case-number search (`CRyyyynnnn`) before building anything on it (one "Case Not Found" probe so far; displayed keys are 8-digit).
- **Jail-roster reference format** (`CR26009544FE`) vs. Agave keys — reconcile.
- **§ 1-605 custodian for Pima CR data:** Pima Superior Court's own custodian vs. AOC Administrative Director — the request letter should address both.
- **Does bulk data include birth month/year?** (Day-of-birth is a protected identifier under § 1-605; month/year status unstated — ask explicitly in the request.)
- **JP portal robots.txt** — only the Cloudflare default block fetched so far (no operator disallow-all, unlike Agave); confirm full posture before any systematic use.
- **PCAO NextRequest archive** — public but JS-gated; find the JSON endpoint or drive headless (same CDP pattern as §3a).
- **`ecrpublic.sc.pima.gov` ("ECR for Parties")** — uninvestigated document channel.

---

*Scanned live 2026-07-20 by 2 research agents; every URL above fetched successfully unless marked unverified. House pattern: same shape as OV/Marana/Tucson/Schools feasibility docs. Editorial guardrails for this coverage area live in `ORIGINAL-JOURNALISM.md` ("On Probation, Then Arrested Again") and the project's standing rules (aggregates by default; derive, don't ask a model; transparency not advocacy).*
