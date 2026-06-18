# Coverage Expansion & Original-Story Research

Verified research from three feasibility scans run **2026-06-18**. Two parts: (1) expanding the government-coverage stack to new jurisdictions/bodies, and (2) a write-ready brief for the first original-journalism feature (Flock cameras). Companion to `responsiveness/UTILITY-DATA-SOURCES.md`.

**Gate:** none of this starts until the in-flight work (TEP poller, dashboard auto-refresh, Instagram build) is settled. Priority order: **Flock article → Sahuarita → school districts.**

---

# Part 1 — Coverage-area expansion

### Correction up front
**Vail is NOT an incorporated town.** Voters rejected incorporation in 2023; it's an unincorporated CDP governed by Pima County — no Vail Town Council exists. Same for **Green Valley** and **Corona de Tucson** (all unincorporated). **Sahuarita is the only incorporated municipality in the SE corridor.**

## A. Sahuarita — clean municipal add (the "fifth municipality")

- Incorporated 1994; **7-member council** (mayor + vice-mayor chosen from members), council-manager form.
- Regular meetings **select Mondays 6 p.m.**; also runs P&Z + Board of Adjustment (extra agenda streams if wanted).
- **Agenda platform: eScribe** (OnX/Granicus). Current portal: `https://pub-sahuarita.escribemeetings.com/meetingscalendarview.aspx`. HTML + PDF, **no public API**. (Legacy IQM2 portal still linked but superseded — confirm eScribe is canonical before coding.)
- **Video: YouTube** — `https://www.youtube.com/user/TownofSahuarita/live`. Reuses the existing streamlink/yt-dlp path (Pima/Tucson pattern); **no Swagit HLS hunting.**
- **Lift: MODERATE.** One new eScribe agenda scraper (≈ Marana/Oro Valley miner effort) + a YouTube `STREAM_SOURCES` entry. No new transcription primitive. The textbook "fifth municipality."

## B. Vail — not a municipal add

No town government. The realistic civic surface:
- **Pima County BOS, District 4 (Supervisor Steve Christy)** — *already in the TDB pipeline.* Vail county-level items (zoning, community facilities districts) are already ingested; the move is editorial **tagging** with a Vail lens (zero new ingestion).
- **Vail School District** — the real genuinely-Vail elected body (see Part 1C). On Diligent Community + YouTube.
- **Fire districts** (Rincon Valley FD, Corona de Tucson FD) — elected boards, plain HTML/PDF agendas, **no meeting video** → previews/minutes only. Lowest priority.

## C. School-district coverage — the sleeper expansion

School boards are badly under-covered and high-stakes. The metro consolidates onto **two agenda platforms**, so **two scrapers cover 8 of 9 major districts** — *lower* lift than the four-municipality pipeline (clean HTML/PDF, easier than Tucson's OnBase).

| District | ~Enroll | Community | Agenda platform | Board video |
|---|---|---|---|---|
| **TUSD** | ~40,000 | City of Tucson core | **Diligent** (`govboard.tusd1.org`) | Diligent / YouTube |
| **Sunnyside** | ~14,100 | South Tucson / south side | **NovusAGENDA** (outlier) | self-hosted / YouTube |
| **Vail USD** | ~14,800 | Vail, SE metro | **Diligent** (`vailschooldistrict.community.highbond.com`) | **YouTube** |
| **Amphitheater** | ~13,500 | **Oro Valley** + N Tucson + Catalina | **BoardBook** (Org 2065) | unconfirmed |
| **Marana USD** | ~12,300 | Marana, NW | **BoardBook** (Org 1780) | **YouTube** @maranaschools |
| **Sahuarita USD** | ~6,400 | Sahuarita / Green Valley | **Diligent** (`susd-30.community.diligentoneplatform.com`) | unconfirmed |
| **Flowing Wells** | ~5,400 | NW Tucson | **BoardBook** (Org 1607) | unconfirmed |
| **Catalina Foothills** | ~5,200 | Foothills + S. Oro Valley | **BoardBook** (Org 1202) | YouTube |
| **Tanque Verde** | ~2,200 | E Tucson | **Diligent** (`tanqueverdeschools.community.highbond.com`) | unconfirmed |

**The headline — platform consolidation:**
- One **Diligent Community** scraper → TUSD + Vail + Sahuarita + Tanque Verde (~63K students, incl. the two biggest).
- One **BoardBook** scraper → Amphitheater + Marana + Catalina Foothills + Flowing Wells (~31K). BoardBook exposes structured HTML + direct PDF (`meetings.boardbook.org/Documents/DownloadPDF/{guid}?org={ID}`) — the cleanest target.
- +1 **NovusAGENDA** scraper → Sunnyside.
- **No Legistar/Granicus** for school boards — your municipal Legistar work doesn't transfer here.

**Notes:** "Oro Valley schools" = **Amphitheater** (no standalone OV district); Catalina = Amphitheater. All boards = 5 elected at-large, 4-yr terms.

**Video for AI reports:** **Vail + Marana** school boards livestream to **YouTube** = direct fit with existing `run_live_reporter.sh`; best early transcription pilots.

**Recommended pilot: Vail USD** — 2nd-largest, fastest-growing, on Diligent + YouTube (can ship a preview AND a post-meeting report day one), and the **Vail Chamber of Commerce** relationship = warm launch. One Diligent scraper then yields TUSD/Sahuarita/Tanque Verde nearly free.

**Build order:** Diligent scraper (Vail pilot) → BoardBook scraper (4 districts) → NovusAGENDA (Sunnyside). Plus extend `pipeline/local_names.json` with board members + superintendents.

**⚠️ Stale-link caution:** several districts have dangling legacy `go.boarddocs.com` pages still ranking in search — **abandoned**. TUSD moved BoardDocs→Diligent Jan 2026; Vail/Sahuarita are on Diligent now. Confirm against each district's live "Governing Board" page before coding.

---

# Part 2 — Original story brief: "Southern Arizona Debated Flock Cameras"

First **original-journalism feature** pilot. Non-advocacy / descriptive. Human-reviewed (news-report bar). Plays to TDB's moat — anchor in TDB's own meeting transcripts, layer external reporting underneath.

### ⚠️ Critical framing correction
**Tucson / TPD does NOT use Flock** — they use **Verkada + Fūsus**. The "Tucson Flock" debate in the corpus is the **City of South Tucson** (separate ~1.2-sq-mi incorporated city), which **cancelled** its Flock contract **Feb 17, 2026**. Conflating the two is the easiest way to be wrong — make the distinction explicit early.

### The regional spine
A **pull-back wave** (South Tucson cancels; Sedona & Flagstaff already dropped Flock) running against an **expansion countercurrent** (Oro Valley adds Flock drones; U of A runs 62 cameras) — against **no Arizona ALPR law**, a contested 2026 bill (SB 1111), and **SB 1070's non-sanctuary posture** sharpening the ICE-access question here more than almost anywhere.

### Jurisdiction status (verify starred items before print)
| Jurisdiction | Vendor | Status | Cameras / Cost | Vote / date |
|---|---|---|---|---|
| Tucson / TPD | **Verkada + Fūsus** (NOT Flock) | In use | undisclosed (records req) | — |
| South Tucson | Flock | **CANCELLED** | 10-cam, ~$20K/yr | **5-1-1\*, Feb 17 2026** |
| Oro Valley PD | Flock | In use + **expanding** | ~20 ALPR + 4 drones; $146K yr1 / ~$850K 3yr | drone grant 1/28/26; IGA 7-0 4/22/26 |
| U of A PD | Flock | In use | **62 cams, $870K/5yr** | no public vote (procurement, Feb 2025) |
| Marana | Vigilant/Motorola (NOT Flock) | In use | 4 units + trailer (2019 Stonegarden) | — |
| Pima County Sheriff | ambiguous | "5 units" vs "none"\* | — | 2019 expansion rejected |
| Sahuarita / PCC / school districts | — | no evidence (records req to confirm) | — | — |

### Best accountability angle
**U of A PD** publicly said it doesn't share with feds, but **EFF records show UAPD ran nationwide Flock searches for the U.S. Marshals Service (Feb–Mar 2025)** — documented federal partner is the Marshals Service, not ICE directly. Plus a Clery Act complaint (Deflock Tucson, Oct 2025) over the undisclosed cameras.
**Oro Valley:** capability-vs-policy nuance — Flock's network *can* run federal/ICE queries (default-off); OVPD says it doesn't. Frame precisely; **call OVPD.**

### Outline (~1,200–1,800 words, neutral)
1. **Lede:** South Tucson rips cameras out as Oro Valley + UA add more.
2. **What Flock/ALPR is** (1 para): plate capture, hotlist alerts, 30-day retention, the national-network search mechanic.
3. **The Southern AZ map** (comparison table) — lead with the Tucson = Verkada-not-Flock correction.
4. **Data-sharing flashpoint:** South Tucson's stated reason; national reporting (404 Media, Illinois audit); Flock's rebuttal; capability-vs-policy (OV); the UA/Marshals contradiction.
5. **Legal backdrop:** no AZ ALPR law; SB 1111 (+ its public-records exemption) vs. the supermajority bill; SB 1520; SB 1070 non-sanctuary.
6. **Where each body stands / what to watch.**

### Records requests that would strengthen it
South Tucson (contract, **2/17 minutes** to settle the vote count, audit logs); UA PD ($870K contract, sharing-settings history, the Marshals search logs); Oro Valley (drone contract + AZ DPS grant, sharing settings, audit logs); TPD (Verkada contract/count/policy + any Flock-pilot plan); PCSD (ALPR inventory/status); Marana (2019 Motorola/Stonegarden terms).

### Confirm-before-publishing checklist
- South Tucson vote count: **5-1-1** (Star/Spotlight) vs **5-2** (KGUN) — minutes settle it.
- Oro Valley ICE-sharing: capability vs. stated policy (call OVPD).
- PCSD operational ALPR status (call PCSD).
- "TPD planning a Flock pilot" lead — **UNVERIFIED, do not print** without confirmation.
- SB 1111 / SB 1520 final disposition (mid-session at last check).
- DeFlock counts — crowdsourced/advocacy; attribute, read live map in a browser.
- Sahuarita / PCC / TUSD "does not use" = absence-of-evidence; records requests harden these.

### Key sources
**Tucson Spotlight** (deepest local well), **AZPM** (UA accountability thread), Arizona Daily Star, KGUN9, **KOLD** (best overview; confirms TPD=Verkada), Arizona Luminaria, **Arizona Mirror** (legislative), **EFF** (Atlas of Surveillance, ALPR resource), **404 Media** (ICE access), DeFlock Tucson (crowdsourced — attribute as such).

### TDB's unique contribution
Mine TDB's **own meeting transcripts** for the actual debate moments (e.g., the two public commenters in the Oro Valley 2026-06-17 news report) so the piece is **primary-sourced TDB reporting**, not a synthesis of others' coverage. That's the moat — lead with what TDB uniquely has, layer external reporting underneath.

---

*Generated from research-agent scans, 2026-06-18. Nothing here is started yet — gated behind in-flight work.*
