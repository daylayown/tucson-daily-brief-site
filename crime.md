# Tucson Police Department, the FBI Crime Data Explorer, and the "0 violent crimes" problem

*Research compiled 2026-05-19. Source: research agent run against FBI Crime Data Explorer, FBI agency API, Tucson Police Department's own dashboard, Arizona DPS, and local + national news coverage.*

## Bottom line

The screenshot is real, the source link is real, and the underlying federal data is real — but the headline statistic ("0 violent crimes, 65,632 property crimes, 2019–2024") is the product of a third-party aggregator (**Crime Explorer / crimeexplorer.com**) doing arithmetic on top of a known TPD federal reporting hole. The hole exists because **TPD did not have its data flowing through to the FBI's NIBRS submission for most of 2021, 2022, and 2023**, and the aggregator does not appear to flag or compensate for that gap. The federal pipeline is the primary culprit; the aggregator is a secondary one that lacks the data hygiene to notice.

The story is reportable, with caveats noted below.

---

## 1. The aggregator: Crime Explorer (crimeexplorer.com)

**URL of the page in the screenshot:** https://www.crimeexplorer.com/arizona/tucson/

**About page:** https://crimeexplorer.com/about/

What I verified about Crime Explorer:

- It is a private, third-party site — **not** affiliated with the FBI, despite its branding strongly evoking the FBI's own "Crime Data Explorer." The FBI's official site is at https://cde.ucr.cjis.gov/ (note the `.cjis.gov`, a federal domain). Crime Explorer's About page does not name an owner; only a generic `contact@crimeexplorer.com` email is given. WHOIS / corporate ownership is not disclosed on the page.
- Its stated methodology: "Crime Explorer pulls from the FBI Uniform Crime Reporting Program, the National Incident-Based Reporting System, and state/local law enforcement agencies reporting to the FBI." It says it "exclude[s] agencies with missing or unusable data" and analyzes "over a 5-year window to smooth out gaps or reporting issues." That smoothing logic is exactly what produces the "0 violent crimes" headline for Tucson — the violent-crime stream was almost entirely missing, the system appears to have read those missing months as zeros (or excluded them entirely from the aggregation but kept the divisor) rather than flagging the city as non-comparable.
- The page provides **no year-by-year breakdown** of the 65,632 property-crime total, no data-completeness footnote, no NIBRS gap disclaimer.
- The rate math on the page is internally inconsistent. "4.9 per 100k, 97.0% below the national average" cannot be derived from 65,632 property crimes over Tucson's ~542K population in any standard calculation. (A correct 5-year average would be ~13,126/year, or ~2,420 per 100k/year — above the national property-crime average, not 97% below it.) The "4.9 per 100k" figure is itself a bug in their pipeline, likely arising from dividing one month's worth of data, or one slice, by the wrong denominator.

**Why this matters editorially:** Crime Explorer is exactly the kind of site that gets pulled into Google snippets, Realtor/Zillow-style "is this a safe neighborhood" overlays, and casual "how dangerous is Tucson" searches. Its visual styling is clean enough to look authoritative. The site's name and language deliberately mirror the FBI's. So a reader trying to do basic civic homework on Tucson safety lands on a page that says, in effect, "Tucson is a near-zero-violent-crime city and is 97% safer than average on property crime" — both statements roughly the inverse of reality.

---

## 2. The FBI Crime Data Explorer record for TPD

**TPD's ORI:** AZ0100300 (verified via the FBI CDE API — `https://api.usa.gov/crime/fbi/cde/agency/byOri/AZ0100300?API_KEY=DEMO_KEY`).

**Key agency metadata from the FBI's own API:**
- `is_nibrs: true`
- `nibrs_start_date: 2024-01-01`

That single date is the most important fact in this story. The FBI's own metadata says TPD is a NIBRS submitter only as of **January 1, 2024**. The FBI's transition deadline was **January 1, 2021** (Source: https://www.fbi.gov/how-we-can-help-you/more-fbi-services-and-information/ucr/nibrs ; the post-deadline state of play is covered by https://www.themarshallproject.org/2022/06/14/what-did-fbi-data-say-about-crime-in-2021-it-s-too-unreliable-to-tell). That means TPD has **three years (2021, 2022, 2023) where its data was not flowing through the FBI's NIBRS pipeline.**

**Monthly-totals data pulled from `api.usa.gov/crime/fbi/cde/summarized/agency/AZ0100300/all`** (raw monthly offense counts; not broken into violent vs. property in the simple endpoint, but the participation pattern is the load-bearing detail):

| Year | Pattern |
|---|---|
| 2019 | All 12 months populated (263–368/month) |
| 2020 | All 12 months populated (284–361/month) |
| **2021** | **All 12 months null — zero reporting** |
| **2022** | **Months Jan–Aug = 0; Sep–Dec partial (291–332/month)** |
| **2023** | **Multiple months with 0; only 8 of 12 months meaningful** |
| 2024 | All 12 months populated (136–405/month — TPD's NIBRS submission begins) |

Property-crime-specific monthly data showed the same pattern (2021 entirely null, 2022 mostly 0–27/month — anomalously low, consistent with partial late-year submission only, then recovery in 2024).

**Implication for the "0 violent crimes" figure:** The aggregator's 5-year window is 2019–2023. Of those five years, **only 2019 and 2020 had complete TPD reporting to the FBI**. 2021 has zero data. 2022 and 2023 have severely partial data. Violent crime is a low-frequency category to begin with (relative to property), so the months that did get reported in 2022–2023 may not have included violent offenses, or those offenses were not classified into the categories Crime Explorer rolled up. The 65,632 property total looks plausible for the months that *did* report — it's the violent total that collapsed because of the specific months TPD's data did and did not arrive.

The FBI's CDE warns in its 2024 release that NIBRS and SRS submissions together cover 95.6% of the US population — but agency-level pages render whatever was submitted, including months of zeros. The CDE has no agency-level "data not available" footnote that aggregators are obligated to honor. (Sources: https://www.fbi.gov/news/press-releases/fbi-releases-2024-reported-crimes-in-the-nation-statistics ; https://cde.ucr.cjis.gov/LATEST/resources/reports/Reported%20Crimes%20in%20the%20Nation%202024%20FAQs.pdf — both confirm the FBI accepted both NIBRS and SRS for 2024 to maximize coverage.)

---

## 3. TPD's NIBRS compliance timeline

Reconstructed from the FBI metadata, statewide reporting, and local news:

- **Pre-2021:** TPD reported under SRS (Summary Reporting System). The FBI's metadata for AZ0100300 has full month-by-month coverage for 2019 and 2020.
- **Jan 1, 2021:** FBI's hard switch to NIBRS-only data collection takes effect. TPD does not have a NIBRS-compatible records management system ready. **Reporting to the FBI effectively stops for all of 2021.**
- **2022:** TPD's data starts trickling in to AZ DPS and ultimately the FBI only in the back half of the year. The Tucson Sentinel (Oct 25, 2023) and AZ Mirror reported that TPD "did not send reports on hate crimes for multiple quarters in 2022." A statistician-run analysis at jasher.substack.com found that **Tucson was the only US agency serving 250,000+ people that failed to report data to the FBI in 2022** — out of 90 such agencies nationally.
- **2023:** Reporting is still partial. The Arizona Daily Star editorial (May 2024) reported that initial AZ DPS numbers were "very far from reality" and that **even after corrections, only 40% of the 2023 crime numbers had been sent by TPD to DPS** as of mid-2024. (Source: https://tucson.com/opinion/column/article_85fa193c-1498-11ef-b733-d7a1df0c4c45.html — pulled successfully; not paywalled.)
- **January 1, 2024:** Per the FBI's own metadata, TPD officially begins NIBRS submission. The CDE has full 12-month coverage for 2024 (with characteristic month-to-month variance — no zeros).

The FBI's 2024 national release (published Aug 5, 2025) accepted both NIBRS and SRS submissions through April 1, 2025. The fact that the FBI shows TPD with full 2024 data means the catch-up worked — but it doesn't retroactively repair 2021–2023.

**Historical pattern worth noting (this is *not* the first time):** Tucson.com archive has an article titled **"Data glitches leave Tucson out of FBI report"** (https://tucson.com/news/data-glitches-leave-tucson-out-of-fbi-report/article_94a318b1-0a04-5c17-a8bb-d8d5c8ec4f95.html). It documents that:
- TPD's 2014 data was missing from the FBI's UCR publication due to a data-transfer error between TPD, AZ DPS, and the FBI. TPD said it met its submission requirements; the error was at the state-to-federal handoff.
- **From 2006 to 2012, the FBI report left categories for larceny and property crime blank for Tucson.**

So the TPD → AZ DPS → FBI handoff has a documented multi-decade history of breaking. The NIBRS transition just made the breakage much larger and longer.

---

## 4. Why property shows but violent shows zero

This was the user's sharpest analytical question and the most important thing to answer carefully. Three contributing factors, in descending order of confidence:

**(a) Time-shifted partial reporting that happened to capture property but not violent.** Violent crime is much rarer than property crime in any given month. If TPD's late-2022 / 2023 batches included months where property thefts were reported but violent incidents either (i) were not yet in a NIBRS-compatible format or (ii) fell into the months that didn't make the cut, you'd see exactly this asymmetry. This is consistent with the AZ Mirror / Tucson Sentinel reporting that **hate crimes specifically went unreported "for multiple quarters in 2022"** — meaning TPD's pipeline was selectively flushing some categories and not others during the transition.

**(b) The aggregator's classification logic.** NIBRS classifies offenses with much finer granularity than SRS (52+ Group A offenses across 23 categories vs. SRS's 8 Part I crimes). When a city submits NIBRS data, building a "violent crime" rollup requires mapping NIBRS offense codes (e.g., 09A homicide, 11A rape, 120 robbery, 13A aggravated assault) to the legacy violent-crime bucket. If Crime Explorer's pipeline mapping is broken for one of those codes — or if it's looking for SRS columns that no longer exist in NIBRS submissions — it would silently count zero violent crimes even when the FBI has the underlying data. This is a known failure mode of aggregators that haven't fully retooled for the NIBRS-only world.

**(c) Pure aggregator bug, unrelated to NIBRS.** The "4.9 per 100k, 97% below national average" math is internally broken in a way that can't be explained by missing data alone — that rate is too small by roughly a factor of 500. Some piece of Crime Explorer's pipeline is dividing or summing wrong. So even if the underlying FBI data were perfect, this page would be wrong. The NIBRS gap created an opportunity; the aggregator's own logic made it catastrophic.

**Reportable framing:** I'd describe (a) and (b) as the federal pipeline's responsibility, and (c) as the aggregator's. A fair story doesn't blame TPD or the FBI for what Crime Explorer is rendering — but it does blame both for creating the conditions that let Crime Explorer render it without consequence.

---

## 5. TPD's own data (the reality check)

What TPD itself reports, via its own dashboard (https://policeanalysis.tucsonaz.gov/pages/reported-crimes) and the Arizona Daily Star editorial citing TPD's 2023 annual crime trend report:

| Year | Homicides (TPD) | Sexual assaults | Robberies |
|---|---|---|---|
| 2019 | 49 | — | — |
| 2020 | 68 | — | — |
| 2021 | **86–93** (sources disagree slightly; record-high year) | 483 | 1,130 |
| 2022 | **75 victims / 67 cases** | 401 | 1,088 |
| 2023 | **59** | 379 | 746 |
| 2024 (through mid-May) | 18 | 121 | — |

(Sources: https://tucson.com/opinion/column/article_85fa193c-1498-11ef-b733-d7a1df0c4c45.html ; https://www.kgun9.com/news/local-news/crime-stats-drop-in-tucson-police-annual-report ; AZPM's coverage at https://www.azpm.org/s/88479-tucson-homicide-rate-soars/ ; AZCIR fact brief at https://azcir.org/news/2024/08/30/fact-brief-has-tucson-crime-increased-significantly-no/.)

These are real numbers from a real city's police department. Crime Explorer's claim that there were **0 violent crimes** over a five-year window during which TPD itself recorded roughly **300+ homicides, ~1,500+ sexual assaults, and ~4,000+ robberies** is — depending on how charitable you want to be — a 100% data-quality failure, not a 0.001% one.

---

## 6. Has this been reported locally?

Yes, partially, in pieces. There is no single article that ties the whole thread together — TPD's NIBRS gap + FBI consequence + downstream aggregator pollution + reputational impact on the city. Pieces of it:

1. **Arizona Daily Star editorial (May 2024)** — "Violent-crime trend encouraging, not cataclysmic." Documents the 40% submission gap and pushes back on a Goldwater Institute op-ed that cited the partial data. https://tucson.com/opinion/column/article_85fa193c-1498-11ef-b733-d7a1df0c4c45.html
2. **Tucson Sentinel / AZ Mirror (Oct 25, 2023)** — "Hate crimes in Arizona dip slightly in 2022, though data is incomplete." Calls out TPD specifically for missing multiple quarters of 2022. https://www.tucsonsentinel.com/local/report/102523_hate_crimes/hate-crimes-arizona-dip-slightly-2022-though-data-incomplete/ and https://azmirror.com/briefs/hate-crimes-in-arizona-dip-slightly-in-2022-though-data-is-incomplete/
3. **AZCIR fact brief (Aug 30, 2024)** — "Has crime in Tucson increased significantly? No." References TPD's annual report but notably does not address the federal reporting gap. https://azcir.org/news/2024/08/30/fact-brief-has-tucson-crime-increased-significantly-no/
4. **Axios Phoenix (Jun 14, 2022)** — "Inconsistencies in Arizona reporting could complicate crime data comparisons." Names Phoenix, Maricopa, Glendale, Tempe, AZ DPS as non-reporters for 2021. Notably **does not name Tucson** — Tucson's gap became visible only when 2022 numbers came in. https://www.axios.com/local/phoenix/2022/06/14/reporting-inconsistencies-arizona-complicate-comparing-crime-data
5. **jasher.substack.com (Apr 2024)** — Statistical analysis. Names Tucson as **the only US agency over 250K population that failed to report to the FBI in 2022**. https://jasher.substack.com/p/did-6000-agencies-fail-to-report
6. **The Marshall Project (Jun 14, 2022; Jul 13, 2023)** — National coverage of the FBI/NIBRS gap, but does not name Tucson. https://www.themarshallproject.org/2022/06/14/what-did-fbi-data-say-about-crime-in-2021-it-s-too-unreliable-to-tell ; https://www.themarshallproject.org/2023/07/13/fbi-crime-rates-data-gap-nibrs

**The unreported angle** — and the strongest editorial hook for a TDB story — is that nobody has actually closed the loop on what the federal data hole *did to Tucson's public reputation* via downstream aggregators. The Daily Star editorial pushed back on one political op-ed; nobody has shown that the gap is also producing the inverse error — making Tucson look *implausibly safe* to anyone searching for crime stats — across the dozens of real-estate and city-comparison sites that pull from the FBI's data feed.

The historical precedent (https://tucson.com/news/data-glitches-leave-tucson-out-of-fbi-report/article_94a318b1-0a04-5c17-a8bb-d8d5c8ec4f95.html — TPD missing from 2014 report; property categories blank 2006–2012) adds depth: this isn't one bad transition, it's a pattern.

---

## 7. Reportability assessment

**Story is publishable**, with the right framing and a few additional reporting steps. The headline should not be "TPD hides crime" — that's wrong, the numbers are public on TPD's own dashboard. The headline should be something like:

> *"The federal crime database has a Tucson-shaped hole — and the websites that fill it are making the city look implausibly safe."*

Or:

> *"For three years, Tucson stopped showing up in the FBI's crime data. The websites that quote that data didn't notice — and now they're telling readers the city has had zero violent crimes since 2019."*

**Things I'd want before publishing, in priority order:**

1. **A direct screenshot of the FBI Crime Data Explorer's agency page for TPD** (https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/explorer/crime/crime-trend, then drill to Tucson, AZ). The page renders client-side so WebFetch couldn't capture it — a human browser session needs to grab the visual. This becomes the central exhibit: "Here's what the FBI itself shows for 2021, 2022, 2023." If the FBI's own line chart has a gap there, the story is bulletproof.
2. **A statement from TPD's records / data unit** about: (a) when their NIBRS implementation actually went live, (b) what records management system they migrated to, (c) what they think about Crime Explorer's "0 violent crimes" claim. Send a public records request for emails between TPD and AZ DPS about the NIBRS transition between 2020 and 2024.
3. **A statement from Arizona DPS** about the state's role in the handoff. The 2014 "data glitches" story specifically pinned the failure on the DPS-FBI transfer, not on TPD. The current gap may have a similar structural cause that should be documented for accountability.
4. **Find 3–5 other downstream aggregators** that consume FBI data and check what they show for Tucson. NeighborhoodScout, AreaVibes, City-Data, BestPlaces, HomeSnacks all surfaced in the searches. If multiple of them have nonsense numbers for Tucson 2021–2023, the story is "a federal pipeline failure is corrupting the consumer-facing safety data for an entire major US city," which is a national story. If only Crime Explorer has it wrong and the others handled it gracefully, the story is narrower — a single bad aggregator.
5. **Identify Crime Explorer's owner.** Their About page reveals nothing. A WHOIS lookup and a polite email to `contact@crimeexplorer.com` asking who runs it and how they handle non-reporting agencies would either get a response (good — quote it) or get silence (also good — "Crime Explorer's anonymous operator did not respond to requests for comment").

**What I'd flag as a risk before publishing:**

- The Crime Explorer page says "2019–2024" in the overview but the property total appears to be a 5-year sum covering 2019–2023 (per their methodology language about "most recent five-year period"). The exact window matters because 2024 is now back in the FBI's data; if their pipeline updated and the page still says zero, the bug is more severe and more easily provable. Pin the exact rendering on the day of publication with an archive.org snapshot.
- The "TPD-DPS-FBI handoff broke" narrative is well-sourced for hate crimes (multiple outlets) and well-sourced for 2014. The bridging claim — that the *same* handoff process broke for the *same* TPD-DPS-FBI link during the NIBRS transition — is logically supported but should be confirmed by either AZ DPS or TPD directly before publication, not just inferred from the FBI's own NIBRS start date metadata.
- The math on "4.9 per 100k, 97% below national average" might be Crime Explorer doing something specific (perhaps using just one year's partial data divided by full population, perhaps a unit-conversion error). I described it as a bug but I haven't reverse-engineered the specific formula. A confident write-up should either explain the bug precisely or characterize it as "we could not reproduce their math from any combination of FBI data we could find" — both are acceptable.

**Strength of the story as it stands:** Strong enough to publish with the FBI's CDE screenshot and one phone call to TPD's public-information unit. The federal-pipeline / aggregator-bug angle is the public-interest hook; the historical "Tucson keeps falling out of the FBI report" pattern (2006–2012, 2014, 2021–2023) is the depth that lifts it from "one bad website" to "an ongoing structural problem in how Tucson is represented in national data."

---

## Source URLs cited above (all primary or near-primary)

**FBI / federal data:**
- FBI Crime Data Explorer: https://cde.ucr.cjis.gov/
- FBI 2024 release: https://www.fbi.gov/news/press-releases/fbi-releases-2024-reported-crimes-in-the-nation-statistics
- FBI Reported Crimes in the Nation 2024 FAQ: https://cde.ucr.cjis.gov/LATEST/resources/reports/Reported%20Crimes%20in%20the%20Nation%202024%20FAQs.pdf
- FBI NIBRS page: https://www.fbi.gov/how-we-can-help-you/more-fbi-services-and-information/ucr/nibrs
- FBI 2024 NIBRS portal: https://nibrs.fbi.gov/2024/
- CDE agency API for TPD (ORI AZ0100300): https://api.usa.gov/crime/fbi/cde/agency/byOri/AZ0100300?API_KEY=DEMO_KEY (works) and `summarized/agency/AZ0100300/all?from=01-2019&to=12-2024` for monthly counts
- Congressional Research Service report on NIBRS: https://www.congress.gov/crs-product/R46668

**The aggregator:**
- https://www.crimeexplorer.com/arizona/tucson/
- https://crimeexplorer.com/about/

**TPD / Tucson / Arizona official:**
- TPD data portal: https://policeanalysis.tucsonaz.gov/
- TPD reported crimes: https://policeanalysis.tucsonaz.gov/pages/reported-crimes
- TPD hate-crimes open data: https://policeanalysis.tucsonaz.gov/datasets/cotgis::tucson-police-hate-and-bias-crimes-open-data/about
- TPD annual reports: https://www.tucsonaz.gov/Departments/Police/About-TPD/TPD-Annual-Reports
- AZ DPS TOPS (Tucson PD 2023 overview): https://azcrimestatistics.azdps.gov/tops/report/crime-overview/tucson-pd/2023 (SSL cert chain didn't verify in WebFetch; confirm in browser)
- Arizona Criminal Justice Commission trends one-pager: https://www.azcjc.gov/Portals/0/Documents/pubs/2023_AZCrimeTrends_OnePager.pdf

**Local / regional coverage:**
- Arizona Daily Star editorial on the 40% gap: https://tucson.com/opinion/column/article_85fa193c-1498-11ef-b733-d7a1df0c4c45.html
- "Data glitches leave Tucson out of FBI report" (the 2014 and 2006–2012 precedent): https://tucson.com/news/data-glitches-leave-tucson-out-of-fbi-report/article_94a318b1-0a04-5c17-a8bb-d8d5c8ec4f95.html
- Tucson Sentinel hate-crimes article: https://www.tucsonsentinel.com/local/report/102523_hate_crimes/hate-crimes-arizona-dip-slightly-2022-though-data-incomplete/
- AZ Mirror hate-crimes article: https://azmirror.com/briefs/hate-crimes-in-arizona-dip-slightly-in-2022-though-data-is-incomplete/
- AZ Mirror on antisemitism 2022: https://azmirror.com/2023/03/24/antisemitism-continued-to-rise-in-2022-including-a-homicide-in-arizona/
- AZPM on homicide spike: https://www.azpm.org/s/88479-tucson-homicide-rate-soars/
- AZCIR fact brief: https://azcir.org/news/2024/08/30/fact-brief-has-tucson-crime-increased-significantly-no/
- Axios Phoenix on Arizona NIBRS gap (Jun 2022): https://www.axios.com/local/phoenix/2022/06/14/reporting-inconsistencies-arizona-complicate-comparing-crime-data
- KGUN on TPD annual report: https://www.kgun9.com/news/local-news/crime-stats-drop-in-tucson-police-annual-report

**National coverage / methodology:**
- The Marshall Project (2022): https://www.themarshallproject.org/2022/06/14/what-did-fbi-data-say-about-crime-in-2021-it-s-too-unreliable-to-tell
- The Marshall Project (2023): https://www.themarshallproject.org/2023/07/13/fbi-crime-rates-data-gap-nibrs
- jasher.substack.com on Tucson as the only 250K+ non-reporter: https://jasher.substack.com/p/did-6000-agencies-fail-to-report
- jasher.substack.com on FBI estimation methodology: https://jasher.substack.com/p/how-the-fbi-estimates-missing-data

---

## Bonus: one-paragraph distillation if you want to test it on the reader

> A reader sent us a screenshot from a site called Crime Explorer (crimeexplorer.com), which claims that Tucson recorded zero violent crimes between 2019 and 2024 and that the city's property-crime rate is 97% below the national average. Both claims are nonsense — Tucson Police Department's own data records 86 homicides in 2021 alone, and TPD's actual property-crime numbers run roughly twice the national average. But the site isn't fabricating: it's pulling from a real federal data hole. According to the FBI's own metadata, Tucson PD's NIBRS reporting start date is January 1, 2024 — meaning the department's data was not flowing into the federal crime database for all of 2021, most of 2022, and most of 2023 while the FBI transitioned away from its century-old crime-reporting system. A 2024 Arizona Daily Star editorial reported that even by mid-2024 only 40% of TPD's 2023 crime data had been submitted to Arizona DPS, which is what feeds the FBI. The data hole isn't new — tucson.com's archive shows the FBI left Tucson's property-crime categories blank from 2006 to 2012, and the 2014 report had similar transfer-glitch problems. What's new is the NIBRS transition turned a quiet data-quality issue into a public-facing one: third-party sites like Crime Explorer scrape the federal numbers, fail to flag the gaps, and end up telling readers a major US city has had no violent crime for half a decade.
