# The Pima County Attorney's PowerBI dashboards: what we found, how, and what we know now

*Research compiled 2026-07-20. Everything below was fetched/probed live that day unless noted. Companion to `COURT-DATA-FEASIBILITY.md` (§§3a–3b) and the court-data program generally.*

## Bottom line

PCAO's public "By the Numbers" dashboard has been **frozen since 2025-03-16** — not because the data died, but because in mid-March 2025 the office **swapped its live report for a point-in-time copy that was never connected to a refresh schedule**. The original report kept updating in plain sight (at a still-public URL) until **2026-06-13**, though its felony/misdemeanor case-flow metrics have returned zeros for 2026. No 2025 year-end report exists. The one genuinely live county dashboard we found is the **Medical Examiner's** (updated 2026-07-08) — county-wide homicide counts, 2017–present.

---

## 1. The cast

| Report | Report ID (`k`) | Status as of 2026-07-20 |
|---|---|---|
| PCAO **"OLD"** report (site embed Nov 2021 → Jan 2025; still public at original URL) | `d7ba02f3-9be3-4436-a3f5-61728a140247` | Publicly reachable; last refresh **2026-06-13**; 4 pages; case-flow feeds dead for 2026; jail/HR/victims/diversion live through 6/13 |
| PCAO **"NEW"** report (current site embed) | `d4c75f04-4553-44d3-bec9-62663d512357` | **Frozen at 2025-03-16**; 2 pages; card-layout rebuild of the OLD tables |
| Pima County **Medical Examiner** dashboard | tenant `33b6e2c3-…` (not PCAO's) | **Live — "Last Updated on 7/8/2026"**; 10 pages incl. Homicides |

Embed URLs (publish-to-web, no auth):
- OLD: `https://app.powerbigov.us/view?r=eyJrIjoiZDdiYTAyZjMtOWJlMy00NDM2LWEzZjUtNjE3MjhhMTQwMjQ3IiwidCI6ImRhNGQ5MjNjLTI0NGUtNDgyNC04ZThjLTg0ZjdlOTgwYTg1YSJ9`
- NEW: `https://app.powerbigov.us/view?r=eyJrIjoiZDRjNzVmMDQtNDU1My00NGQzLWJlYzktNjI2NjNkNTEyMzU3IiwidCI6ImRhNGQ5MjNjLTI0NGUtNDgyNC04ZThjLTg0ZjdlOTgwYTg1YSJ9`
- ME: `https://app.powerbigov.us/view?r=eyJrIjoiNGI4OWM4ZDEtM2U0ZC00M2EzLWIzMDItZWFmNTkyZmQwMzFiIiwidCI6IjMzYjZlMmMzLTBiMWEtNDg3OS1iNzQxLTQ3NDYxYTZjMWE4OSJ9`

Embed tokens are base64 of `{"k":"<report-id>","t":"<tenant-id>"}` — decode to compare reports. PCAO tenant: `da4d923c-244e-4824-8e8c-84f7e980a85a`.

## 2. The forensic timeline (how the staleness happened)

1. **Nov 2021 → Jan 2025:** every Wayback capture of `pcao.pima.gov/by-the-numbers/` embeds the OLD report. One live, daily-refreshing report for 3+ years.
2. **2025-03-13 and 2025-03-15:** the page returns **404** (Wayback CDX).
3. **2025-03-17:** page republished (WordPress `article:modified_time`) — embedding the NEW report, a card-layout rebuild whose data was **frozen at 2025-03-16 from birth**. Conclusion: during a page rebuild someone published a *copy* and never gave it a refresh schedule.
4. **Meanwhile the OLD report stayed alive** — staff kept using it (it grew from 2 → 4 pages), refreshing daily through **2026-06-13** (jail population 1,629, employees 312 FT / 17 PT, victim comp 108, diversion successful 191 — all 2026 values).
5. **But its case-flow feeds broke around end of 2025:** felony/misdemeanor/juvenile YTD read **0** for 2026, and its year-table lost the 2024 column. The case data comes from PCAO's Karpel case-management warehouse (`PBKDW.dbo.vCaseDefn`) — a CMS migration/change is the likely culprit (unconfirmed).
6. **2026-06-13:** the OLD report's refresh stops too.

**Net: two frozen public reports.** The one the site shows is 16+ months stale; the live original is 5+ weeks stale with dead case-flow. Nobody at PCAO appears to have noticed either.

## 3. What the dashboards contain

### PCAO NEW report (frozen 2025-03-16) — YTD tiles + year table, 2019–2025*

| Data Point | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025* |
|---|---|---|---|---|---|---|---|
| Employees FT / PT | 355/21 | 355/21 | 342/25 | 293/20 | 310/7 | 298/6 | 295/6 |
| Budget Proposed | $40.37M | $37.10M | $39.56M | $42.99M | $41.11M | $45.11M | — |
| Budget Adopted | $40.12M | $38.63M | $39.75M | $43.26M | $41.11M | **$0 (broken)** | — |
| Jail pop (6am) | ??? | ??? | 1,602 | 1,752 | 1,705 | 1,612 | 1,670 |
| **Felony Presented** | 10,427 | 5,095 | 9,388 | 9,754 | 10,183 | 9,733 | 2,093 |
| **Felony Indicted** | 6,909 | — | 5,165 | 5,937 | 4,509 | 4,512 | 702 |
| Felony Pleas | 5,667 | 3,124 | 1,287 | 985 | 1,409 | 2,987 | 199 |
| Defendants at Trials | 163 | 32 | 41 | 123 | 52 | 115 | 16 |
| Felony Dismissals | 602 | 334 | 172 | 283 | 207 | 207 | 7 |
| Homicides (detail) | 118 | 140 | 137 | 157 | 132 | 136 | 24 |
| Domestic Violence (detail) | 1,312 | 1,491 | 1,515 | 1,385 | 1,089 | 1,220 | 229 |
| Juvenile Presented / Filed | 3,388/1,782 | 2,128/1,162 | 1,359/748 | 1,327/677 | 1,668/845 | 1,922/1,128 | 318/161 |
| **Misdemeanor Presented / Filed** | 10,525/10,174 | 8,420/8,053 | 8,743/8,031 | 9,999/9,057 | 9,802/9,342 | 9,355/9,028 | 1,826/1,717 |
| Diversion STEPs Offered/Completed/Failed | 0/0/0 | 0/0/0 | 331/63/129 | 354/117/158 | 1,518/150/127 | 1,362/230/180 | 287/38/45 |
| Diversion Successful/Unsuccessful | 783/192 | 415/137 | 247/32 | 380/32 | 387/55 | 573/78 | 113/14 |
| Victims Compensation | 382 | 216 | 303 | 355 | 307 | 297 | 39 |

*2025 = YTD as of 2025-03-16. Broken series: Drug Only Cases, Prison Years, Probation Years all read 0 from 2023 (dead feeds, not real zeros).

### OLD report — pages 3–4 (internal, publicly reachable since ~2025)

- **Page 3 = metric definitions.** E.g.: Felony Presented = defendants with [Date Charged] in year, [Case Type]='Felony'; Homicides = defendants, [Statute Category]='Murder', excludes attempts (explains why it exceeds TPD murder counts); Prison/Probation Years = SUM of sentence years by type; budgets "adjusted annually based on feedback from the PCAO Budget Officer" (manual).
- **Page 4 = raw SQL + schema**: case data from `PBKDW.dbo.vCaseDefn` (PbK = *Prosecutor by Karpel*), events `PbKMetrics.rpt.t_Event`, diversion `PCAD.dbo`, jail `RawData.dbo.InCustody`. Hand-maintenance bugs visible: misdemeanor "Filed" filters `[Issue Status]='Indicted'` (misdemeanors aren't indicted — **that metric is suspect**); part-time employee query duplicates the full-time one. Don't republish their schema; do verify before using those two numbers.

### PCAO 2024 year-end report (PDF, uploaded 2025-01-14)

`https://www.pcao.pima.gov/wp-content/uploads/2024/01/3794009-PCAO-2024-year-end-report-DRAFT10.pdf` — PR-style "Year 4 Review." Its "By the Numbers" page: **69 homicides county-wide 2024 (excl. officer-involved), 7,769 total pending cases, 70.63 open cases per prosecutor**, homicide victims down 33.7% 2021→2024 (104→69). **No 2025 year-end report exists** in the media library as of 2026-07-20.

### Medical Examiner dashboard (LIVE, updated 2026-07-08)

Homicide deaths. **⚠️ CORRECTION (re-verified live 2026-07-20): the OME serves SIX counties and the dashboard defaults to all of them — the series first recorded here was the multi-county total, not Pima.** Unfiltered = six-county total (963 cases, 2017→2026 YTD: 95 · 89 · 77 · 100 · **137** · 128 · 102 · 99 · 94 · 42; firearms 733/963). **Pima-filtered (830 cases): 84 · 79 · 69 · 86 · 119 · 104 · 90 · 89 · 77 · 33** — **2021 peak = 119, 2025 = 77**; firearms 632/830 (76%); 82% male; ages 20–39. The mislabel traces to the §4.4 caveat: the CDP `innerText` pull read the county-unfiltered default (and flattened text is misalignment-prone) — so **read the rendered chart with the Pima filter applied**, don't trust the text dump. Screenshot: `in-depth/evidence-me-homicides-pima-2026-07-20.jpg`. Still valuable: an independent, live county homicide *trend* — but it counts manner-of-death homicide (incl. justifiable/OIS), NOT a substitute for city murder counts, so don't fold it into the TPD/TOPS/AZPM 47-vs-54-vs-69 city split. Also: deaths-reported, manner-of-death, exam-type, accidents, suicides, natural/undetermined, demographics pages. Found via the Tucson Crime Free Coalition's links page.

## 4. How we found it (techniques, all reusable)

1. **Wayback CDX + raw captures** — `web.archive.org/cdx/search/cdx?url=pcao.pima.gov/by-the-numbers/` for the capture list (incl. the two 404s); `web.archive.org/web/<ts>id_/<url>` for raw HTML; grep for `app.powerbigov.us/view?r=` to compare embed tokens across years.
2. **Token decoding** — base64 of `{"k","t"}` reveals report/tenant IDs; that's how the OLD-vs-NEW swap was proven.
3. **Headless Chromium screenshots** — `chromium --headless=new --no-sandbox --screenshot=… --virtual-time-budget=25000 "<powerbi url>"` renders publish-to-web reports (JS apps) in ~30s.
4. **CDP driving (Chrome DevTools Protocol via websocket)** — navigate, wait, click the footer "Next Page" button or in-report nav buttons via `Runtime.evaluate`, dump `document.body.innerText`, `Page.captureScreenshot`. Extracts clean, deterministically-parseable text — **no LLM near the numbers**. (Caveat: flattened innerText can misalign chart label↔value pairing — verify against the screenshot before publishing chart values. We caught exactly one such misalignment on the ME page.)
5. **The live site loads in a real browser engine** — the "bot block" is UA-based: `curl` works with a browser UA (`-k` for a cert-chain quirk), and the **WordPress REST API is fully open** (`/wp-json/wp/v2/pages`, `/media?search=…`). That's how the full page inventory (~100 pages, one PowerBI embed) and the year-end-report PDFs were found.
6. **Search engines** — DuckDuckGo HTML endpoint found the ME dashboard via the Tucson Crime Free Coalition's links page.

## 5. What we know now

1. **The public dashboard isn't dying; it was replaced.** A frozen copy has stood in for it since March 2025 — most likely an accident of a page rebuild, not a policy choice. Either way, PCAO's public transparency surface has been dead for 16 months.
2. **PCAO's internal live pipeline existed until ~6 weeks ago** (refresh through 2026-06-13) but its case-flow feeds (Karpel `vCaseDefn`) have been broken for 2026 — consistent with a case-management-system change nobody has explained.
3. **No third PCAO report exists anywhere on their site**, and no 2025 year-end report — the office's data publishing has gone quiet across every surface.
4. **Live county violent-crime data does exist — at the Medical Examiner.** Updated 2026-07-08. It gives the county-wide homicide baseline PCAO's dashboard can't currently provide.
5. **The remaining routes to current PCAO data:** the PIO email (`pcao-pio-email.md`), the ACJA § 1-605 bulk-data request (court-side), Measures for Justice (Arizona county dataset exists but the download 404'd — retry via browser or email), and the OLD report's living fragments (jail/HR/victims/diversion through 6/13).
6. **Monitoring plan (buildable):** weekly headless render → deterministic text parse → diff → Telegram on change, watching THREE reports — NEW (flag when the frozen date moves = PCAO noticed), OLD (case-flow returning to nonzero = feed fixed), ME (fresh homicide counts).

## 6. Questions for the PCAO PIO (also in `pcao-pio-email.md`)

1. Was the March 2025 embed swap a deliberate snapshot or a rebuild mistake — and does PCAO know the public dashboard has been frozen 16 months?
2. Who owns the refresh schedule, and is it coming back?
3. Why does `vCaseDefn` return zero 2026 cases (Karpel/PbK migration)?
4. Why did the OLD report stop refreshing on 2026-06-13?
5. Are the OLD report's pages 3–4 (metric definitions + raw SQL) intended to be public?

## Source URLs

- PCAO By the Numbers: `https://www.pcao.pima.gov/by-the-numbers/`
- Wayback CDX: `http://web.archive.org/cdx/search/cdx?url=pcao.pima.gov/by-the-numbers/&output=json`
- OLD / NEW / ME embed URLs: see §1
- PCAO 2024 year-end report: `https://www.pcao.pima.gov/wp-content/uploads/2024/01/3794009-PCAO-2024-year-end-report-DRAFT10.pdf`
- WP REST inventory: `https://www.pcao.pima.gov/wp-json/wp/v2/pages`, `…/media?search=report`
- ME dashboard discovered via: `https://www.tucsoncrimefree.com/pages/links`
- Measures for Justice portal: `https://measuresforjustice.org/portal/datasets` (Arizona zip 404 as of 2026-07-20)
