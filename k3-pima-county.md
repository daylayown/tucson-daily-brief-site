# k3-pima-county — find where Pima County Attorney's *live* public data actually lives

> **How to use:** Paste everything below the line into an LLM with web access (Claude, GPT, Gemini, etc.). It's self-contained. The mission: we've mapped the obvious surfaces — find what we're overlooking. End your run by stating how confident you are that the live data is or isn't publicly reachable.

---

## Role

You are a web-forensics researcher embedded with a local newsroom. Your specialty is finding government data that has moved, been renamed, been quietly republished elsewhere, or was never as public/unpublic as assumed. You are rigorous: every URL you cite is one you actually fetched, and anything you couldn't load is labeled "unverified," never guessed.

## Who I am

I run **Tucson Daily Brief**, a one-person local news outlet covering the Tucson / Pima County, Arizona metro. I'm building automated civic-transparency monitoring around the **Pima County Attorney's Office (PCAO)** — the county prosecutor — and I'm trying to answer one deceptively simple question:

> **Where does PCAO's current public data actually live — if anywhere?**

## The situation so far (all verified live on 2026-07-20; treat as ground truth)

PCAO publishes a "By The Numbers" dashboard at `https://www.pcao.pima.gov/by-the-numbers/` — a PowerBI "publish to web" embed. Through token forensics and the Wayback Machine I established:

- **Embed tokens are base64** of `{"k":"<report-id>","t":"<tenant-id>"}`. PCAO's tenant: `da4d923c-244e-4824-8e8c-84f7e980a85a`.
- **Report OLD** (`k=d7ba02f3-9be3-4436-a3f5-61728a140247`) was the site's embed from **Nov 2021 → Jan 2025** (verified across Wayback captures). Embed URL: `https://app.powerbigov.us/view?r=eyJrIjoiZDdiYTAyZjMtOWJlMy00NDM2LWEzZjUtNjE3MjhhMTQwMjQ3IiwidCI6ImRhNGQ5MjNjLTI0NGUtNDgyNC04ZThjLTg0ZjdlOTgwYTg1YSJ9`
- The page **404'd 2025-03-13 and 2025-03-15** (Wayback), was republished **2025-03-17** (WordPress `article:modified_time`), and re-embedded **Report NEW** (`k=d4c75f04-4553-44d3-bec9-62663d512357`): `https://app.powerbigov.us/view?r=eyJrIjoiZDRjNzVmMDQtNDU1My00NGQzLWJlYzktNjI2NjNkNTEyMzU3IiwidCI6ImRhNGQ5MjNjLTI0NGUtNDgyNC04ZThjLTg0ZjdlOTgwYTg1YSJ9`
- **Report NEW is frozen at 2025-03-16** despite a footer claiming "Values Above Represent YTD Totals as of Yesterday." It appears to be a card-layout *copy* that was never given a refresh schedule.
- **Report OLD is still publicly reachable** at its original URL and **kept refreshing until 2026-06-13** (live 2026 values for jail population 1,629, employees 312 FT / 17 PT, victim compensation 108, diversion successful 191) — but its **felony/misdemeanor/juvenile case-flow metrics read 0 for 2026**, and its own refresh has now also stopped (~5 weeks stale as of today, 2026-07-20).
- Report OLD grew to **4 pages**; pages 3–4 expose internal metric definitions and raw SQL. The case data comes from **`PBKDW.dbo.vCaseDefn`** (PbK = *Prosecutor by Karpel*, PCAO's case-management system); jail from `RawData.dbo.InCustody`; diversion from `PCAD.dbo`; events from `PbKMetrics.rpt.t_Event`. Several series (drug-only cases, prison years, probation years) have read 0 since 2023 — dead feeds, not real zeros.
- **What the dashboard measures (2019–2024 real, per Report OLD):** felony presented (~9,400–10,400/yr), indicted, pleas, trials, dismissals; homicide-charge defendants (118–157/yr); domestic violence; misdemeanor presented/filed (~95–97% filed); juvenile presented/filed; STEPs diversion; victim compensation applications; jail population; PCAO headcount; budget.
- **Technique that works for reading these reports:** headless Chromium + Chrome DevTools Protocol — navigate, 20s render, click the footer's "Next Page" button via JS, dump `document.body.innerText`, screenshot. ~40s per report.
- **Wayback CDX pattern used:** `http://web.archive.org/cdx/search/cdx?url=pcao.pima.gov/by-the-numbers/&output=json&limit=-N` and raw captures via `http://web.archive.org/web/<timestamp>id_/<url>`.

## Surfaces already checked (don't redo these — extend beyond them)

- `pcao.pima.gov` — nginx bot-blocks plain non-browser fetches (403/timeout). WordPress + Elementor site.
- The `by-the-numbers` page itself (current + 2021–2026 Wayback captures) — token forensics above.
- `pcao.nextrequest.com` — public records portal; archive is public but JS-gated (shell only without a browser). JSON endpoint NOT yet found — worth one attempt.
- PCAO "year-end report" PDFs referenced under `www.pcao.pima.gov/wp-content/uploads/...` (exact URLs unknown; 2022 "Year Two Report" and a "PCAO 2024 year-end report" were seen in search results).
- Pima County Superior Court "Agave" (`wwww.cosc.pima.gov/PublicDocs/`), the Justice Court portal (`jp.pima.gov/CaseSearch/`), AZ eAccess, AZ AOC Safe Communities Act reports, TPD/PCSD crime data — these are COURT and POLICE systems, related but NOT PCAO's own numbers. Don't conflate.

## Your mission

**Find where PCAO's current (2025–2026) public numbers actually live — or assemble strong evidence they exist nowhere public.** Lines of inquiry to test, in whatever order your judgment says, plus at least two angles NOT on this list:

1. **Is there a THIRD (or newer) publish-to-web report?** Check: Wayback CDX wildcard for `pcao.pima.gov*` pages mentioning powerbi (try `url=pcao.pima.gov*&filter=original:.*powerbi.*` — and note CDX indexes HTML, so also fetch likely PCAO page captures and grep them); search engines for `app.powerbigov.us` + pima/pcao; other PCAO site pages that might embed PowerBI (department pages, budget pages, "data" pages); the PCAO site map (`wp-json/wp/v2/pages` may list all pages even where the site 403s browsers — try it, plus `wp-sitemap.xml`).
2. **PCAO annual / year-end reports** — find the actual PDF URLs (CDX wildcard on `pcao.pima.gov/wp-content/uploads/*` filtered to pdf; the site's media library API `wp-json/wp/v2/media?search=report`). Do they carry the same metrics, more currently? Is there a 2025 report?
3. **Pima County's own data/performance surfaces** — does the county run an open-data or performance portal (check `data.pima.gov`, `gisdata.pima.gov`, county budget/transparency dashboards, ClearGov/OpenGov instances) that carries attorney-office stats?
4. **Board of Supervisors records** — PCAO presents to the Pima County BOS; Legistar (`webapi.legistar.com/v1/pima`) matter attachments may contain current caseload/budget presentations. Search Legistar matters for County Attorney items in 2025–2026.
5. **The NextRequest released-documents archive** — has another requester already obtained PCAO caseload/charging stats? (Try `/requests.json`, the CivicPlus API patterns, or a headless render.)
6. **News/social quoting fresh PCAO numbers** — PCAO's own social accounts (@PimaCountyAtty), local outlets (tucson.com, KOLD, KGUN, AZPM, Tucson Sentinel) citing PCAO statistics in 2025–2026 — the numbers' existence proves a source; identify it.
7. **Karpel (PbK) public products** — do any Karpel customer counties publish public caseload portals, and does Pima have one?
8. **Wayback snapshots of the PowerBI view URLs themselves** — CDX for `app.powerbigov.us/view?r=eyJrIjoiZDdiYTAyZjMtOWJlMy00NDM2…` — if archived, older data states might be recoverable for comparison.

## Constraints

- Polite: a handful of requests per host, no hammering. No CAPTCHA bypass, no auth bypass, no robots.txt violations (note: `wwww.cosc.pima.gov` disallows all spiders — leave Agave alone).
- Every URL cited must be actually fetched by you. Label failures "unverified."
- If you propose a technique rather than execute it, mark it clearly as untested.
- No fabrication. A wrong "found it!" is far worse than an honest "it's not public."

## Output format

1. **Verdict** (3–5 sentences): where the live PCAO data is — or the case that it exists nowhere public right now.
2. **Surfaces table**: Surface | URL | Fetched & verified? | What it contains | How current | Automation potential (clean/headless/none).
3. **The two+ angles I didn't list**, and what each turned up.
4. **Refined PIO question list** — what should I ask PCAO's public information officer, sharpened by what you found?
5. **One thing you tried that failed** — so the next person doesn't retry it blindly.

End with your confidence level and the single most likely place the data turns out to be living.
