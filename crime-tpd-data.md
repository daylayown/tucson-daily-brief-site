# What we actually know about Tucson crime in 2024–2025

*Research compiled May 19, 2026. Primary sources: Tucson Police Department's data submission to Arizona DPS (the TOPS portal), TPD's published "Year at a Glance" 2024 figures, AZPM year-end reporting drawn from TPD's PowerBI dashboard, Pima County Sheriff's Department's 2024 and 2025 Annual Reports (raw PDFs), and contemporaneous local coverage of TPD's homicide and shooting data. Flags below for what could not be verified without a human browser session.*

*Companion to `crime.md` (federal NIBRS reporting gap research). This file focuses on what TPD actually publishes itself.*

---

## What would unlock the most additional reporting in one afternoon

Three concrete things will close most of the verification gaps below:

1. **A browser session capturing the live PowerBI dashboard** at `policeanalysis.tucsonaz.gov` with screenshots of each filter view (categories × years × geographic). The dashboard renders client-side and no automated tool can scrape it.
2. **A direct human download of the 2024 TPD Annual Report PDF** at `https://www.tucsonaz.gov/files/sharedassets/public/v/5/police/documents/annual-reports/tucson-police-department-2024-annual-report.pdf`. The URL is correct; the city's asset server returns 403 to any non-browser client.
3. **A public-records request for the methodology footnote behind the "97.56% homicide resolution rate" figure.** That single clarification answers the cleanest single methodology question I encountered — it's the gap between TPD's 97.56% self-reported figure and TOPS' FBI-format 57.45% clearance rate for the same year.

---

## 1. What is TPD's most recent published crime data?

TPD's open-data portal at **https://policeanalysis.tucsonaz.gov/** is the city's primary surface. Its three section pages — **Reported Crimes**, **Police Activity**, and **Datasets** — are ArcGIS Hub instances embedding a Microsoft PowerBI dashboard hosted at `app.powerbigov.us` (the "Reported Crimes" embed token is in the URL set at https://app.powerbigov.us/view?r=eyJrIjoiY2ViZmNiYzAtMDQ5ZC00OTMwLTliMTgtYjM1ZjAwYjJlMTkzIiwidCI6ImQyMWU1OWVjLWMyMDgtNDNlYi1hYWYxLWNmMDZkOWExOTZlMCJ9&pageName=ReportSectionccd6be2a1a0db780dadd ). Both the ArcGIS Hub frame and the PowerBI report render fully client-side; neither WebFetch nor curl pulls anything beyond the loading shell. **Capturing the most recent month visible on the dashboard requires a human browser session.**

The static data sources I could verify:

| Source | URL | Most recent data |
|---|---|---|
| TPD 2024 Annual Report | `https://www.tucsonaz.gov/files/sharedassets/public/v/5/police/documents/annual-reports/tucson-police-department-2024-annual-report.pdf` | Calendar 2024 (year-ending Dec 31). City of Tucson asset server returns 403 to any non-browser client; the PDF was located via web search but could not be downloaded. |
| AZ DPS TOPS — Tucson PD Crime Overview 2024 | `https://azcrimestatistics.azdps.gov/tops/report/crime-overview/tucson-pd/2024/pdf/` | Full calendar 2024 |
| AZ DPS TOPS — Tucson PD Crime Overview 2025 | `https://azcrimestatistics.azdps.gov/tops/report/crime-overview/tucson-pd/2025/pdf/` | **Partial — YTD only.** The PDF carries the standard "current year does not reflect a full 12 months" disclaimer, and the homicide case count (38) is well below the AZPM full-year figure (54), suggesting roughly the first three quarters as of the May 19, 2026 pull. |
| AZ DPS TOPS — Violent Crimes Tucson PD 2024 | `https://azcrimestatistics.azdps.gov/tops/report/violent-crimes/tucson-pd/2024/pdf/` | Full 2024 |
| AZ DPS TOPS — Violent Crimes Tucson PD 2025 | `https://azcrimestatistics.azdps.gov/tops/report/violent-crimes/tucson-pd/2025/pdf/` | Partial 2025 (same caveat) |
| City of Tucson "Tucson 2024 By the Numbers" | summary covered at https://www.signalsaz.com/articles/see-tucson-2024-by-the-numbers/ (published Jan 17, 2025) | Calendar 2024 — internal city-wide accomplishments report; has the only published TPD operational metrics I could find for 2024 (calls-for-service total, homicide clearance, drug arrests, naloxone administrations, community-satisfaction score). |
| Tucson Open Data — Police Incidents 2025 | `https://gisdata.tucsonaz.gov/datasets/tucson-police-incidents-2025-open-data` | Continuous (Jan 1, 2025 forward; record-level) |
| Tucson Open Data — Reported Crimes (rolling) | `https://gisdata.tucsonaz.gov/datasets/tucson-police-reported-crimes` | 2018 to date, record-level |

**Freshest single data point** publicly verified: TPD's PowerBI year-end dashboard for 2025 (reported by AZPM January 26, 2026; https://news.azpm.org/p/azpmnews/2026/1/26/228130-homicides-dropped-in-tucson-in-2025/) showing **54 homicides in calendar 2025**. AZ DPS TOPS lags by several months — its 2025 violent-crime PDF shows 38 homicide cases YTD as of this pull.

**Categories tracked by TPD's dashboard** (per AZPM, January 6, 2025; https://news.azpm.org/p/newsc/2025/1/6/223129-tucson-homicides-go-up-in-2024-but-stay-below-recent-high/): "homicide, sexual assault, robbery, aggravated assault, burglary, larceny, grand theft auto, and arson" — the standard FBI Part I rollup. The TOPS PDFs confirm the same eight categories, with NIBRS-style detail for victim demographics, weapon type, and victim-offender relationship layered on top from 2024 forward.

**Note for a future round of reporting:** Five named TPD products are referenced in this research without being readable by automated tools — the live PowerBI dashboard, the 2024 TPD Annual Report PDF, the ArcGIS Hub "Reported Crimes" interactive frame, the "Police Activity" page (response times, traffic stops, use of force), and the Datasets page. A human at a browser, with screenshots and CSV downloads, would close all five gaps in an afternoon.

---

## 2. The actual numbers — year-by-year totals

**Caveat on which dataset to trust.** TPD's own PowerBI dashboard and the AZ DPS TOPS portal (which is fed by TPD's submissions to AZ DPS) produce slightly different counts for the same category and year. The most prominent example: TOPS shows **47 homicide cases** for TPD calendar 2024, while AZPM (citing TPD's PowerBI) shows **69 homicides** for the same year. The most likely reasons: (a) NIBRS counts each victim as one case but historically each homicide *incident* is counted in city/police narratives, so multi-victim incidents inflate the PowerBI number relative to TOPS' offense count; (b) TOPS classifies only "Murder and Nonnegligent Manslaughter" (NIBRS 09A); the city's "homicide" public-facing number includes negligent manslaughter, justifiable homicides, and likely some attempted/other categorizations; (c) reporting lag — the TOPS pull may not yet reflect all 2024 reclassifications. None of those gaps were ever closed in published coverage; this is itself worth pointing out in a story.

For year-by-year continuity I've used **the AZPM / contemporaneous reporting counts**, which trace back to TPD's own dashboard, supplemented by TOPS where it adds NIBRS-style category detail.

### Homicide — TPD jurisdiction, by year

| Year | Homicides (TPD count, via dashboard / annual report) | Source |
|---|---|---|
| 2019 | 43 (AZPM Jan 2026); 49 (KOLD/Kasmar March 2025) | AZPM https://news.azpm.org/s/102556 ; KOLD https://www.kold.com/2025/03/04/how-police-chief-chad-kasmar-plans-tackle-uptick-violent-crime-tucson/ |
| 2020 | 68 | KOLD March 2025 |
| 2021 | **78** (AZPM Jan 2026) / **93** (KOLD March 2025; KGUN 9 cites "record") | AZPM ; KOLD ; KGUN9 https://www.kgun9.com/news/local-news/tucson-police-chief-compares-crime-numbers-from-previous-years |
| 2022 | 75 | KOLD March 2025 |
| 2023 | 53 (AZPM Jan 2025) / 54 (AZPM Jan 2026) / 59 (KOLD March 2025) | AZPM Jan 2025 https://news.azpm.org/p/newsc/2025/1/6/223129-tucson-homicides-go-up-in-2024-but-stay-below-recent-high/ |
| 2024 | **69** (AZPM Jan 2026) / 65–66 (Jan 2025 / KOLD March 2025) | AZPM Jan 2026 |
| 2025 | **54 — lowest since 2019; tied with 2023** | AZPM Jan 2026 https://news.azpm.org/p/azpmnews/2026/1/26/228130-homicides-dropped-in-tucson-in-2025/ |

The drift between sources (e.g., 2024 reported as 65, 66, or 69) is real and reflects late reclassifications between when each story was published. For a TDB write-up, the safest formulation is "TPD's year-end dashboard shows 54 homicides in 2025, down from 69 in 2024 and well below the 2021 peak of 78." That's all from a single source (AZPM citing the dashboard) at a single moment in time.

### Full Part I table — TPD jurisdiction, FY 2023 vs. 2024, from AZ DPS TOPS

These are TPD's NIBRS submissions to AZ DPS, rolled up to the legacy Part I "violent" and "property" buckets.

| Category | 2023 cases | 2023 clearance | 2024 cases | 2024 clearance | 2024 YoY |
|---|---|---|---|---|---|
| **Violent crime (rollup)** | 3,506 | 31.75% | **3,544** | 38.23% | **+1.08%** |
| Homicide (Murder & Nonnegligent Manslaughter, NIBRS 09A) | 56 | 55.36% | **47** | 57.45% | **−16.07%** |
| Aggravated Assault | 2,292 | 38.57% | **2,543** | 42.59% | **+10.95%** |
| Robbery | 747 | 20.62% | **657** | 30.59% | **−12.05%** |
| Sexual Assault | 411 | 10.71% | **297** | 14.81% | **−27.74%** |

Source: TOPS PDF, https://azcrimestatistics.azdps.gov/tops/report/violent-crimes/tucson-pd/2024/pdf/ (downloaded May 19, 2026 — verified locally).

### Crime Overview — 2023 vs 2024 (TOPS, all Part I + Part II combined)

| Year | Total crimes reported | Clearance rate | Population | Crime rate per 100K | YoY |
|---|---|---|---|---|---|
| 2023 | 31,383 | 17.31% | 548,544 | 5,721.15 | −10.79% (from 2022) |
| **2024** | **31,176** | **18.32%** | **548,789** | **5,680.87** | **−0.66%** |
| 2025 (partial YTD) | 17,494 | 36.13% | 556,898 | 3,141.33 | — |

Source: TOPS PDFs, https://azcrimestatistics.azdps.gov/tops/report/crime-overview/tucson-pd/2024/pdf/ and `.../tucson-pd/2025/pdf/` .

The jump in 2025 clearance (36.13% YTD vs 18.32% in 2024) is striking but **almost certainly a partial-data artifact** — partial-year clearance rates inflate as recent offenses (still unsolved) haven't yet been reported, while older offenses (more likely solved) dominate the denominator. Do not lead with this number.

### Property categories — TPD 2024, from external reporting against the FBI/UCR feed for TPD

The TOPS "Property Crimes / Tucson PD 2024" PDF returned HTTP 500 on the AZ DPS server (a consistent error, not transient), so I do not have a primary-source verification for these. The numbers below are widely repeated in real-estate aggregators citing FBI 2024 data released in September 2025:

| Property category | 2024 count | Per 100K | Source |
|---|---|---|---|
| Burglary | 1,629 | (not given, ~297) | AreaVibes Tucson, citing FBI 2024 UCR release ( https://www.areavibes.com/tucson-az/crime/ ) |
| Larceny-theft | 13,723 | (not given, ~2,500) | Same |
| Motor vehicle theft | 2,830 | 516 | Same |
| Arson | 110 | — | Same |
| **All property crimes** | **18,182** | **3,313** | Same |
| **All violent crimes** | **3,231** | **589** | Same |

These are derived from the same TPD submission that produced the TOPS violent-crime figures, but they pass through a different pipeline (FBI → CDE → consumer aggregators). The violent-crime count of 3,231 here is lower than TOPS' 3,544, again likely a victim-counted-vs-incident-counted distinction. **For a TDB story I would not publish the 18,182 number without a TPD-direct confirmation; cite it as "according to FBI 2024 data released September 2025" with that hedge.**

### Population-adjusted rate — peer comparison, 2024 calendar year (FBI 2024 UCR)

| City | Population | Violent crime rate per 100K | Property crime rate per 100K | Total |
|---|---|---|---|---|
| **Albuquerque, NM** | 558,745 | 1,181.76 | 4,628.77 | 5,810.53 |
| Sacramento, CA | 526,670 | 754.93 | 2,547.33 | 3,302.26 |
| Fresno, CA | 546,722 | 735.47 | 3,271.32 | 4,006.79 |
| **Tucson, AZ** | 548,789 | **588.75** | **3,313.11** | **3,901.86** |
| Mesa, AZ | 513,585 | 482.69 | 1,464.61 | 1,947.30 |
| El Paso, TX | 678,860 | 278.41 | 1,493.98 | 1,772.39 |

Source: Wikipedia's "List of US cities by crime rate" 2024 table ( https://en.wikipedia.org/wiki/List_of_United_States_cities_by_crime_rate ); ultimate source is FBI Crime Data Explorer 2024.

**The key reading:** Tucson is *not* an Albuquerque-style outlier. It's higher than its in-state Phoenix-metro peer (Mesa) and lower than every California city of comparable size — but higher than the national average (~359 violent / ~1,760 property per 100K in 2024 per AreaVibes). Tucson's profile is property-crime-heavy and violent-crime-moderate, which matches every long-running observation of the city.

### What TPD itself says about the trend

The 2024 TPD Annual Report (per a search-result excerpt I could not verify against the PDF directly): "In 2024, homicides and aggravated assaults trended above 2023 levels and the 5-year average, with homicides up 12% and aggravated assaults up 12.8% from the 5-year average."

Then-Chief Kasmar to KOLD on March 3, 2025 (https://www.kold.com/2025/03/04/how-police-chief-chad-kasmar-plans-tackle-uptick-violent-crime-tucson/):

> "It's not unusual for us to collect 50 to 100 spent shell casings at a shooting scene… It's a gun culture issue that we all have to address here in Tucson."

> "Identifying the trigger puller. So if you pull a trigger on a firearm illegally within city limits, we will investigate and find you this year."

> "We're seeing automatic handguns, extended magazines, and bullet catchers."

The trend through 2025 reversed: AZPM, citing TPD's PowerBI dashboard on January 26, 2026 (https://news.azpm.org/p/azpmnews/2026/1/26/228130-homicides-dropped-in-tucson-in-2025/):

> "Several other categories of violent crime decreased in Tucson, too. Robberies declined the most, reaching almost half of pandemic-era levels. Aggravated assaults in Tucson stayed constant in 2025 and are still above pre-pandemic levels."

That last sentence is the load-bearing one: **homicide and robbery improved through 2025; aggravated assault did not.**

---

## 3. Geographic / neighborhood breakdown

What's published vs. what's accessible:

- **Tucson Open Data** publishes record-level incident data (one row per incident, with lat/long, incident type, and date) at `gisdata.tucsonaz.gov/datasets/tucson-police-incidents-2025-open-data` and similar URLs by year. This is the only way TPD makes ward- or neighborhood-level patterns available — there is **no canned ward-by-ward dashboard**. A user can aggregate incidents to wards or council districts by spatial join, but it's not the default view. (Source: search-result metadata; the page itself doesn't render under WebFetch.)

- **Police Scorecard's Tucson page** (https://policescorecard.org/az/police-department/tucson, data through 2022–2023) is the closest thing to a published ward/district comparison, but it's a national civilian-rights project, not TPD's own product.

- **AZPM's 2025 year-end story** (Jan 26, 2026) gives the only published geographic call-out at the city level for the most recent year: "Homicides in 2025 were concentrated on Tucson's south side, west side, and north of downtown." No counts by ward, no map.

- **TPD's PowerBI dashboard** likely contains map filters by district or ward — but capturing that requires a browser session. I cannot verify from automated tools.

**The honest line for a TDB story:** TPD publishes record-level location data that lets anyone *build* a geographic analysis. It does not publish ward-by-ward tallies in its dashboards, and the city's stated geographic breakdown for 2025 is the loose three-region "south, west, and north of downtown" line above.

---

## 4. Clearance rates and case outcomes

This is where TPD's own numbers and the external scorecards diverge most sharply, and it deserves direct attention.

### TPD's own published clearance rates (2024, from TOPS submission to AZ DPS)

| Category | Cases | Clearance % |
|---|---|---|
| Homicide (NIBRS 09A) | 47 | **57.45%** |
| Aggravated Assault | 2,543 | **42.59%** |
| Robbery | 657 | **30.59%** |
| Sexual Assault | 297 | **14.81%** |
| All violent crime | 3,544 | **38.23%** |
| All offenses (Part I + II) | 31,176 | **18.32%** |

Source: TOPS PDF https://azcrimestatistics.azdps.gov/tops/report/violent-crimes/tucson-pd/2024/pdf/ and `.../crime-overview/.../2024/pdf/`.

### City of Tucson "Year at a Glance" 2024 figure (from "Tucson 2024 By the Numbers")

> "97.56% homicide case resolution rate."

Source: Signals AZ summarizing the city report, January 17, 2025 (https://www.signalsaz.com/articles/see-tucson-2024-by-the-numbers/). This figure — explicitly framed as the city's headline accomplishment in the public safety section — is a fundamentally different metric than the TOPS / FBI clearance rate. **TPD's 97.56% likely refers to cases active in 2024 that received an arrest *or* an exceptional clearance *over a multi-year window* (cleared-by-arrest plus cleared-by-other-means), not the percentage of incidents that occurred in 2024 that were cleared by year-end.** The two metrics are commonly conflated in city-published self-reporting; the FBI's standard reports clearance rate on a year-of-occurrence basis (cases cleared by Dec 31 of the year they occurred), which is always lower and is what TOPS reflects.

Reportable framing: "TPD reports a 97.56% homicide case resolution rate in its 2024 annual self-summary, while the standard FBI-format clearance rate that TPD submits to Arizona DPS shows 57.45% for the same year. Both numbers are accurate — they measure different things — but the gap matters."

### Earlier, then-Chief Kasmar gave KGUN 9 an even higher number

Date unspecified in the article, but consistent with the 2022/2023 annual reporting cycle (https://www.kgun9.com/news/local-news/tucson-police-chief-compares-crime-numbers-from-previous-years):

> "We did see a slight reduction in homicides last year, which we were happy about, we have about an 84% clearance rate."

The 84% number in the same lineage as the 97.56% — both are TPD's own self-reporting that resists comparison to FBI-format data.

### Non-fatal shooting clearance

Tucson Spotlight, February 12, 2026 (https://www.tucsonspotlight.org/tucson-reports-drop-in-shootings-under-safe-city-plan/), on the Safe City Initiative one-year update:

- **85% nonfatal shooting clearance rate in 2025**
- **86% conviction rate in state and federal courts**
- **25% decrease in firearm-related incidents from 2024 to 2025**
- **15% reduction in nonfatal shootings (2024 → 2025)**
- The "Grant/Dodge VIVA site" saw an 80% decrease in violent crime over two years.

These are TPD-supplied numbers, not independently verified.

### Independent third-party clearance assessment — Police Scorecard

https://policescorecard.org/az/police-department/tucson (data through 2022–2023):

- "Homicide Clearance: 370 homicides, 148 unsolved (40% solved)"
- Overall TPD scorecard rating: **42% (12th of 15 major AZ departments)**
- Accountability sub-category: **11%** — characterized as "significantly low"
- 3,163 misconduct complaints 2016-2022; 5% ruled in favor of civilians
- 67% of arrests 2013–2023 for "low-level, non-violent offenses"
- Arrest rate higher than 97% of comparable departments

These figures are a multi-year window (typically 2013–2023 or 2016–2022) and capture a substantially different — and lower — long-run clearance rate than TPD reports for any single recent year.

### Response time data

There is no publicly verifiable TPD response-time figure for 2024 or 2025. KGUN 9's most-cited reference numbers (Priority 1 calls: 4 min 47 sec average; Priority 4 calls: 1 hr 37 min) are from **fiscal year 2017–18** (https://www.kgun9.com/longform/what-s-expected-tucson-police-response-times). The 2018 Priority 1 goal-met rate was 72%.

Jeff Asher's national response-time analysis (July 14, 2025; https://jasher.substack.com/p/police-response-times-may-be-improving) explicitly notes that **"Mesa and Tucson were included when I did the exercise in 2023 but don't have comparable data anymore"** — meaning the data feed Asher used pulled Tucson out of his national comparison. This is itself worth a sentence in a TDB story: TPD's response-time data is no longer surfacing through the standard national tracking infrastructure.

Tim Steller, March 2025 (paraphrased; not behind paywall): "It is widely recognized that Tucson police often do not respond in a timely way to reports of minor crimes, and even some more serious incidents go without prompt response if officers are too busy."

---

## 5. National and peer comparisons — what's fair to say

**Honest position:** The 2024 FBI Crime Data Explorer numbers for TPD are valid (TPD's NIBRS submission resumed January 1, 2024 per the FBI's own agency metadata for ORI AZ0100300; see the earlier `crime.md` research). Anything earlier than 2024 in the FBI's feed is partial or missing, so any "Tucson vs peer cities" comparison that uses FBI data from 2021, 2022, or 2023 is unreliable for Tucson.

For 2024-only comparisons, the table above (Section 2) is fair to cite. Tucson is roughly:
- **Higher than its in-state peer Mesa** on every metric.
- **Higher than El Paso** (often cited as the "safest big city in the US").
- **Lower than Fresno and Sacramento** in California on total crime rate.
- **Lower than Albuquerque, NM** — substantially lower on both violent and property.
- **Higher than the FBI national city average** of ~359 violent crime / ~1,760 property crime per 100K (per the AreaVibes write-up).

**Independent national comparisons:**

- **AH Datalytics' Real-Time Crime Index** (https://www.ahdatalytics.com/rtci/) tracks ~500–1,000 agencies monthly. Whether Tucson is currently in the RTCI panel could not be confirmed via WebFetch (the dashboard renders client-side). Asher's general 2025 finding via that index: murder is down ~19.8% nationally Jan-Oct 2025 vs. 2024 (https://www.newsweek.com/us-murder-rates-biggest-yearly-drop-11270098). Tucson's 22% homicide drop (69 → 54) fits the national pattern.
- **MAP Dashboard at the University of Arizona** (https://mapazdashboard.arizona.edu/quality-place/public-safety) gives the Tucson MSA (not city) a 2024 violent crime rate of 383.2/100K — below the state rate of 421.9/100K and above the national rate of 359.1/100K. (The MSA number is lower than the city number because the MSA includes Marana, Oro Valley, Sahuarita and unincorporated Pima County — all lower-crime jurisdictions.)
- **2022 firearm fatality rate** (UA MAP, citing CDC): Tucson MSA at 19.9/100K, third-highest among western peer MSAs. Albuquerque MSA was first at 25.5/100K.
- **Police Scorecard** ranks TPD 12th of 15 major Arizona departments overall (42% score), specifically due to a poor accountability sub-score (11%).

---

## 6. Local context — what's driving the trends

### Leadership transition (the single most important context item for any 2026 story)

**Chad Kasmar retired as TPD chief on February 13, 2026**, after serving since 2021 (https://content.govdelivery.com/accounts/AZTUCSON/bulletins/407f35a ; https://www.tucsonsentinel.com/local/report/020526_kasmar_tpd/). He was appointed deputy administrator for Pima County effective March 1, 2026 (https://www.kold.com/2026/02/05/tucson-police-chief-chad-kasmar-resigns-take-job-with-pima-county/).

**Monica Prieto** — 26-year TPD veteran, Tucson native, Desert View HS grad, second woman and first Latina to lead TPD — was appointed by City Manager Tim Thomure as the new chief, effective February 13, 2026. She prioritizes street racing and traffic safety (33 traffic fatalities YTD as of late April 2026; she's targeting a 20% reduction in six months), recruitment (applicant pool +50%; 50 new positions from a COPS grant), and continuing the violence-prevention work Kasmar started. From her April 29, 2026 KOLD interview (https://www.kold.com/2026/04/29/exclusive-new-tucson-police-chief-taking-command-tackling-citys-biggest-challenges/):

> "Next year at this time, I'm hoping to have about 911 officers."

> "The biggest piece of that is just having that responsibility now — that you are the one that's now responsible for 1,210 people in your organization, and it's a heavy lift. It's an absolute privilege, but it's a heavy lift."

> On street racing: "We're going to be taking cars, and we're going to be charging people with felonies, with endangerment and participating in a criminal syndicate."

### Safe City Initiative — the city's named policy response

Mayor Romero announced the **Safe City Initiative** in October 2025 (https://www.tucsonsentinel.com/local/report/101425_safe_city_initiative/; AZ Free News editorialization at https://azfreenews.com/2025/10/tucson-mayor-announces-she-will-now-allow-cops-to-address-crime/). The initiative bundles:

- A misdemeanor ordinance for public drug possession (under council discussion since September 2025; the AZ Luminaria April 13, 2026 update notes the ordinance is "on the backburner" while existing tools are strengthened).
- A 15-bed sobering center at the Mission Annex facility, funded with **$1.86 million in opioid settlement funds**.
- Expanded Community Court diversion.
- Increased police presence on Sun Tran transit and in high-crime areas.

Kasmar's October 2025 framing of the underlying drivers:

> "Felony arrests increased by 50 percent and misdemeanor arrests increased by 100 percent over the last five years."

> "80 percent of addicts on the streets will refuse treatment because they know there are no consequences."

> "It's the reality that they know, if they only get caught with a lower level of possession, that they're likely to have those charges dismissed during initial appearance, and they think, well, I'll just be out. I'll just be out in six or eight hours."

**Safe City Task Force** launched November 14, 2025 (https://news.azpm.org/p/news-articles/2025/11/17/227285-with-launch-of-task-force-tucson-officials-continue-policy-shift-on-public-safety/): includes Pima County Attorney's Office, Old Pueblo Community Services, Cactus Empire Little League, QuikTrip, and city officials. Romero, same article:

> "Crime is going down in our city, but yet, our neighbors, our residents in Tucson are still tangibly seeing the crisis of unsheltered homelessness and the public health crisis of fentanyl and opioid misuse."

City officials cite the figure that **65% of fentanyl-possession and public-drug-use cases TPD brings to the Pima County Attorney go unprosecuted**.

### Drug arrests (Q1 2026)

From the April 13, 2026 Safe City Initiative update at AZ Luminaria (https://azluminaria.org/2026/04/13/tucson-sees-sharp-rise-in-drug-arrests-as-officials-get-first-update-on-safe-city-initiative/):

- **806 drug-related arrests in Q1 2026** — a 67% increase vs. the same period over the last three years.
- 149 deflections (offered services instead of arrest).
- 53 referrals to the Sobering Alternative Recovery center.
- Transit deployments March 9–30, 2026: 69 arrests, 139 warnings, 9 service referrals.

Chief Monica Prieto:

> "It just tells us that the opioid crisis continues to be an issue."

Assistant City Manager Liz Morales:

> "Safe City is the umbrella of all the efforts that we're doing to really address the challenges we have around shelter, the fentanyl public health crisis, and the violent crimes."

### Staffing — the central operational constraint

| Source | Date | Figure |
|---|---|---|
| Kasmar to KOLD | March 3, 2025 | "750 deployable officers… too low for a city this size with the crime that we have." |
| KGUN 9 | January 2025 | "About 780 officers on duty." |
| Chief Prieto to KOLD | April 29, 2026 | "1,210 people in your organization." (Total department, not just sworn.) Goal "next year at this time" of about 911 officers. |
| City "By the Numbers" 2024 | Jan 2025 | TPD added 111 new employees in 2024 — a 9.4% staffing increase. |
| AZ DPS 2023 stats | 2023 | TPD had 1,143 full-time law enforcement employees, including 777 officers (649 male, 128 female). |

**The narrative line:** TPD has roughly **750–780 deployable officers** as of 2025–2026, against an internally-targeted ~911. The gap is roughly 15–18%. Three academies/year are running; 20–30 recruits per academy, which the recruitment team frames as the achievable rate. The department added 111 employees in 2024 (a record under Kasmar) but that was largely catching up — net deployable strength is barely above 2022 levels.

### City-wide accomplishments in TPD's 2024 self-report

From the City of Tucson "Tucson 2024 By the Numbers" annual report (via https://www.signalsaz.com/articles/see-tucson-2024-by-the-numbers/):

- **255,959 calls for service** (mid-December 2024)
- **97.56% homicide case resolution rate** (TPD's framing; see Section 4 caveat)
- **111 new employees** added (+9.4%)
- **6,534 drug-related arrests**
- **538 individuals diverted to treatment** instead of arrest
- **152 naloxone administrations** for opioid overdoses by TPD
- **80.8% community satisfaction rating**

These are city-published, not externally validated.

### Violence Interruption & Vitalization Action (VIVA) sites

Per Tucson Spotlight Feb 12, 2026:

- 2,527 community members engaged at four VIVA sites through 60 events.
- 638 referrals to Goodwill's Village program in 18 months (357 from TPD youth ages 12–24; 165 from Banner-UMC).
- Grant/Dodge VIVA site: 80% decrease in violent crime over two years.

---

## 7. Data quality caveats

1. **The FBI NIBRS reporting gap (2021–2023)** is documented in the prior `crime.md` research and remains the single biggest data-quality issue. Any peer-city or national-trend story drawing on FBI data for TPD prior to 2024 is structurally unreliable. The 2024 FBI numbers are clean. 2025 FBI data won't be fully published until ~September 2026.

2. **TPD's PowerBI dashboard does not render in any non-browser tool I could try** (curl, WebFetch, ArcGIS Hub data API). The dashboard reportedly has the freshest data — possibly with multi-month or weekly granularity — but verification requires a human at a browser. This is itself a transparency limitation: a journalist cannot scrape, archive, or trend-line TPD's published numbers without screenshots taken at specific moments.

3. **Multiple competing "homicide" counts.** Section 2 documents the 47 / 53 / 54 / 65 / 66 / 69 spread across TOPS, AZPM dates, KOLD, KGUN 9, and city reporting. None of the sources I found explained the methodology gap. This is reportable on its own: TPD publishes meaningful counts that vary depending on which file you pull and when, and there is no methodology footnote anywhere that addresses it.

4. **Clearance rate framing.** TPD's "97.56% homicide case resolution" (city report) vs TOPS' 57.45% (FBI format) is a methodology gap that is not disclosed anywhere I could find. Reporting either number without addressing the difference would mislead readers.

5. **The Tucson Open Data layer publishes record-level incidents** (https://gisdata.tucsonaz.gov/datasets/tucson-police-incidents-2025-open-data) — which is the gold-standard transparency mode — but does so without obvious dashboards, geographic rollups, or trend visualizations on the city's surfaces. A journalist (or anyone) needs to download the raw layer and do their own analysis to get any view beyond what TPD chooses to highlight.

6. **No published use-of-force, complaint, or discipline dashboard.** The most-cited statistics are from the Police Scorecard external project (covering 2013–2023). The Police Activity page at `policeanalysis.tucsonaz.gov/pages/police-activity` purports to publish operational data but renders client-side and could not be verified.

7. **No published response-time dashboard for 2024 or 2025.** The KGUN 9 reference (Priority 1: ~5 min, Priority 4: ~97 min) is from fiscal year 2017–18. Jeff Asher of AH Datalytics explicitly noted Tucson dropped out of his 2025 national response-time comparison because comparable data is no longer surfacing.

8. **2025 in TOPS is mid-year YTD only**, despite the URL `.../tucson-pd/2025`. Anyone reading that page without the "current year does not reflect a full 12 months" disclaimer would draw catastrophically wrong conclusions (e.g., comparing TOPS' 38 homicides to 2024's 47 and seeing a 19% drop, when the real full-year 2025 number from TPD's PowerBI was 54 vs. 69 — a 22% drop in the same direction but a different magnitude).

9. **Categorical inconsistency between TPD's narrative reports and TOPS / FBI rollups.** TPD's annual reports tend to lead with "non-fatal shootings" (the agency's chosen operational metric since the gun-violence reduction initiative), while the FBI rollup uses aggravated assault. These are overlapping but not identical universes; TPD's choice of metric framing is itself a story (what does the agency choose to measure and report?).

---

## 8. Pima County Sheriff's Department

PCSD covers approximately 9,186 square miles of unincorporated Pima County, serving over one million residents (PCSD 2025 Annual Report, pg. 4). Total employees as of Dec 31, 2025: 1,404 full-time (506 commissioned deputies, 498 corrections officers, 400 professional staff), plus 245 volunteers.

### PCSD FBI Part I Crime Statistics (from PCSD's own 2025 Annual Report)

| Reported crime | 2025 total | 5-year average |
|---|---|---|
| Homicide | **8** | 13 |
| Sexual assault | **49** | 67 |
| Robbery | **59** | 88 |
| Aggravated assault | **499** | 489 |
| Burglary | **787** | 973 |
| Larceny | **5,479** | 5,613 |
| Motor vehicle theft | **536** | 674 |
| Arson | **41** | 52 |

Source: PCSD 2025 Annual Report, pg. 5 — downloaded May 19, 2026 from `https://pimasheriff.org/download_file/2180/427` (verified locally; 32 MB PDF).

### PCSD 2024 comparison (from prior-year annual report)

| Reported crime | 2024 total | 5-year average |
|---|---|---|
| Homicide | 13 | 14 |
| Sexual assault | 104 | 73 |
| Robbery | 87 | 105 |
| Aggravated assault | 435 | 475 |
| Burglary | 949 | 995 |
| Larceny | 5,619 | 5,647 |
| Motor vehicle theft | 702 | 710 |
| Arson | 44 | 57 |

Source: PCSD 2024 Annual Report, downloaded from `https://pimasheriff.org/download_file/1970/427`.

### PCSD operational metrics (2025)

From the same PCSD report (pg. 5):

- **Overall customer rating: 4.56 / 5**
- **Public satisfaction with response time to calls for service: 4.73 / 5**
- New platform: Versaterm Technologies "CommunityConnect" — automated public-facing case-status updates

PCSD also pointedly notes (pg. 4):

> "The United States Department of Justice (DOJ) recommends the total average ratio of deputies per every 1,000 residents. In Pima County for the population we serve, we should have 2.6 deputies per every thousand residents. Currently, we have 1.1 deputies per 1,000, this is less than half the DOJ recommendation."

(Source citation in the PCSD report: FBI 2019 Police Employee Data table 71.)

### PCSD geographic breakdowns

PCSD publishes **calls-for-service PDFs by ZIP code** under each of eight patrol districts (Ajo, Catalina, Foothills, Green Valley, Rincon, San Xavier, Tucson Mountain, Vail). Index page: `https://pimasheriff.org/crime-map-stats/statistics`. Per-ZIP PDFs are hundreds of files under `pimasheriff.org/application/files/...`. This is more granular geographic publishing than TPD does at the city level — PCSD has a documented per-ZIP product, TPD has only record-level Open Data + the PowerBI dashboard.

### PCSD homicides — context for the Tucson metro story

PCSD's **8 homicides in 2025** (down from 13 in 2024) plus Tucson's **54** plus zero in Marana, Oro Valley, and Sahuarita (per AZPM) give a 2025 metro-wide total of **62 homicides** — the lowest metro figure in seven years. That's the macro figure I'd lead with in a "what we know about Tucson safety in 2025" piece if focused on the regional picture: TPD plus PCSD, two different jurisdictions, both reporting the most favorable trend in their five-year averages on most categories.

---

## Sources cited (every URL verified May 19, 2026 unless noted)

**TPD / City of Tucson primary sources**
- TPD data portal: https://policeanalysis.tucsonaz.gov/ (renders client-side; cannot be scraped)
- TPD Reported Crimes page: https://policeanalysis.tucsonaz.gov/pages/reported-crimes (renders client-side)
- TPD Police Activity page: https://policeanalysis.tucsonaz.gov/pages/police-activity (renders client-side)
- TPD PowerBI dashboard (Reported Crimes embed): https://app.powerbigov.us/view?r=eyJrIjoiY2ViZmNiYzAtMDQ5ZC00OTMwLTliMTgtYjM1ZjAwYjJlMTkzIiwidCI6ImQyMWU1OWVjLWMyMDgtNDNlYi1hYWYxLWNmMDZkOWExOTZlMCJ9&pageName=ReportSectionccd6be2a1a0db780dadd
- TPD Annual Reports landing: https://www.tucsonaz.gov/Departments/Police/About-TPD/TPD-Annual-Reports (403 from non-browser; visible in search)
- TPD 2024 Annual Report PDF: https://www.tucsonaz.gov/files/sharedassets/public/v/5/police/documents/annual-reports/tucson-police-department-2024-annual-report.pdf (403 to curl)
- TPD Open Data — Incidents 2025: https://gisdata.tucsonaz.gov/datasets/tucson-police-incidents-2025-open-data
- TPD Open Data — Reported Crimes (rolling): https://gisdata.tucsonaz.gov/datasets/tucson-police-reported-crimes
- TPD Real Time Event Tracker (PowerBI): https://app.powerbigov.us/view?r=eyJrIjoiZjI5Y2EyZjgtMzA1Ny00NGJhLTkxZWUtZTIwMWM0YmVlNTI2IiwidCI6ImQyMWU1OWVjLWMyMDgtNDNlYi1hYWYxLWNmMDZkOWExOTZlMCJ9
- "Tucson 2024 By the Numbers" via Signals AZ (Jan 17, 2025): https://www.signalsaz.com/articles/see-tucson-2024-by-the-numbers/
- TPD media release — Kasmar retirement / Prieto appointment (Feb 5, 2026): https://content.govdelivery.com/accounts/AZTUCSON/bulletins/407f35a
- Kasmar June 2025 statement on federal immigration ops: https://content.govdelivery.com/accounts/AZTUCSON/bulletins/3e4b1ea

**Arizona DPS / state primary sources (verified locally)**
- TOPS Tucson PD Crime Overview 2024: https://azcrimestatistics.azdps.gov/tops/report/crime-overview/tucson-pd/2024/pdf/
- TOPS Tucson PD Crime Overview 2025 (partial YTD): https://azcrimestatistics.azdps.gov/tops/report/crime-overview/tucson-pd/2025/pdf/
- TOPS Tucson PD Violent Crimes 2024: https://azcrimestatistics.azdps.gov/tops/report/violent-crimes/tucson-pd/2024/pdf/
- TOPS Tucson PD Violent Crimes 2025: https://azcrimestatistics.azdps.gov/tops/report/violent-crimes/tucson-pd/2025/pdf/
- TOPS Tucson PD Violent Crimes 2023: https://azcrimestatistics.azdps.gov/tops/report/violent-crimes/tucson-pd/2023/pdf/
- TOPS Tucson PD Crime Overview 2023: https://azcrimestatistics.azdps.gov/tops/report/crime-overview/tucson-pd/2023/pdf/
- TOPS Tucson PD Property Crimes 2024: HTTP 500 (server error, consistent — likely a data-not-yet-ingested issue)

**Pima County Sheriff's Department (verified locally)**
- PCSD 2025 Annual Report: https://pimasheriff.org/download_file/2180/427 (32 MB PDF)
- PCSD 2024 Annual Report: https://pimasheriff.org/download_file/1970/427 (7 MB PDF)
- PCSD 2023 Annual Report: https://pimasheriff.org/download_file/1800/427
- PCSD Annual Report landing: https://pimasheriff.org/police-reform/annual-report
- PCSD Calls for Service statistics index: https://pimasheriff.org/crime-map-stats/statistics

**Local news coverage**
- AZPM — Homicides dropped in Tucson in 2025 (Jan 26, 2026): https://news.azpm.org/p/azpmnews/2026/1/26/228130-homicides-dropped-in-tucson-in-2025/ (mirror: https://news.azpm.org/s/102556-homicides-dropped-in-tucson-in-2025/)
- AZPM — Tucson homicides go up in 2024 (Jan 6, 2025): https://news.azpm.org/p/newsc/2025/1/6/223129-tucson-homicides-go-up-in-2024-but-stay-below-recent-high/
- AZPM — Safe City task force launch (Nov 17, 2025): https://news.azpm.org/p/news-articles/2025/11/17/227285-with-launch-of-task-force-tucson-officials-continue-policy-shift-on-public-safety/
- AZPM — Public drug-use obstacles (Jan 29, 2026): https://news.azpm.org/p/news-topical-health/2026/1/29/228223-tucson-pushes-to-address-public-drug-use-but-obstacles-remain/
- KOLD — Kasmar uptick plan (Mar 4, 2025): https://www.kold.com/2025/03/04/how-police-chief-chad-kasmar-plans-tackle-uptick-violent-crime-tucson/
- KOLD — Prieto exclusive (Apr 29, 2026): https://www.kold.com/2026/04/29/exclusive-new-tucson-police-chief-taking-command-tackling-citys-biggest-challenges/
- KOLD — Kasmar retirement (Feb 5, 2026): https://www.kold.com/2026/02/05/tucson-police-chief-chad-kasmar-resigns-take-job-with-pima-county/
- KGUN 9 — Kasmar comparison: https://www.kgun9.com/news/local-news/tucson-police-chief-compares-crime-numbers-from-previous-years
- KGUN 9 — TPD annual report drop: https://www.kgun9.com/news/local-news/crime-stats-drop-in-tucson-police-annual-report
- KGUN 9 — TPD recruitment: https://www.kgun9.com/news/community-inspired-journalism/midtown-news/tucson-police-department-ramps-up-recruitment-efforts-to-keep-up-with-staffing-needs
- KGUN 9 — Response time longform (2018 data): https://www.kgun9.com/longform/what-s-expected-tucson-police-response-times
- Tucson Sentinel — Kasmar retirement (Feb 5, 2026): https://www.tucsonsentinel.com/local/report/020526_kasmar_tpd/
- Tucson Sentinel — Safe City unveil (Oct 14, 2025): https://www.tucsonsentinel.com/local/report/101425_safe_city_initiative/mayor-romero-tucson-officials-unveil-new-safe-city-program/
- Tucson Spotlight — Safe City shootings update (Feb 12, 2026): https://www.tucsonspotlight.org/tucson-reports-drop-in-shootings-under-safe-city-plan/
- AZ Luminaria — Drug arrests Q1 2026 (Apr 13, 2026): https://azluminaria.org/2026/04/13/tucson-sees-sharp-rise-in-drug-arrests-as-officials-get-first-update-on-safe-city-initiative/
- AZ Free News — Mayor announce Safe City (Oct 2025): https://azfreenews.com/2025/10/tucson-mayor-announces-she-will-now-allow-cops-to-address-crime/
- AZCIR fact brief — Has crime increased? (Aug 30, 2024): https://azcir.org/news/2024/08/30/fact-brief-has-tucson-crime-increased-significantly-no/

**Third-party / national context**
- AreaVibes Tucson 2024 FBI data: https://www.areavibes.com/tucson-az/crime/
- Wikipedia US cities crime rate 2024 (FBI source): https://en.wikipedia.org/wiki/List_of_United_States_cities_by_crime_rate
- UA MAP Dashboard — Public Safety: https://mapazdashboard.arizona.edu/quality-place/public-safety
- Police Scorecard — Tucson (2013–2023 multi-year data): https://policescorecard.org/az/police-department/tucson
- AH Datalytics Real-Time Crime Index: https://www.ahdatalytics.com/rtci/ and https://ah-datalytics.github.io/rtci/index.html
- Jeff Asher on response times (Jul 14, 2025): https://jasher.substack.com/p/police-response-times-may-be-improving
- Newsweek — US murder rates 2025 (Asher RTCI): https://www.newsweek.com/us-murder-rates-biggest-yearly-drop-11270098

---

## Short-form editorial assessment

The cleanest single-sentence summary I can write from this research:

> **TPD's own dashboard reports 54 homicides in 2025, down from 69 in 2024 and well below the 2021 peak of 78 — but every other crime category, every clearance rate, and every comparison to peer cities sits inside a thicket of methodology gaps, partial-year disclaimers, and dashboards that nobody outside a Tucson browser session has ever seen the same way twice.**

That's the story angle. The 54/69/78 line is the lede. The methodology thicket is the body. The leadership transition (Kasmar → Prieto), the Safe City Initiative, and PCSD's structurally low staffing (1.1 deputies/1K vs. DOJ-recommended 2.6) are the supporting paragraphs.
