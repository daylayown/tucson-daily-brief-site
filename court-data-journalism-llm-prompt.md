# Exploration prompt: automated court-data civic-transparency journalism for Tucson

> **How to use:** Paste everything below the line into different LLMs (Claude, GPT, Gemini, etc.) and compare their answers. It's self-contained — no outside context needed. Optionally end with: *"Be rigorous and skeptical; if the premise is flawed, say so."*

---

## Role
You are a senior advisor blending three skill sets: **data journalism**, **legal/ethical review of public-records work**, and **pragmatic data engineering**. I want rigorous, specific, skeptical analysis — not cheerleading. Challenge my framing where it's weak.

## Who I am
I run **Tucson Daily Brief (TDB)**, a one-person, **AI-assisted** local news operation covering the Tucson / Pima County, Arizona metro. It's a static website plus a daily brief, original meeting coverage, and social distribution. Tooling budget is tiny (~$3–4/month in LLM API calls); the "staff" is me plus AI agents. My editorial model: **AI drafts and flags, a human reviews and approves before anything with a factual claim publishes.** My north star is **depth and civic transparency in an under-covered city — not advocacy.** (I once dropped a planned "equity score" feature specifically because it was too politically loaded. Keep that instinct.)

## The problem I want to explore
A man was recently charged in a mass shooting here; I confirmed from primary court records that he was already on supervised probation for a prior aggravated assault. That raised a systemic question I think Tucson is "crying out" for someone to answer, in the name of civic transparency:

> **What can I actually automate to report on repeat offenders, probation outcomes, and case results in Pima County — rigorously and responsibly — as an AI-assisted newsroom?**

I do NOT want a hand-wavy "you could build a dashboard!" answer. I want a clear-eyed map of what's genuinely automatable vs. human-in-the-loop vs. impossible, given the *actual* data-access facts below.

## Ground truth: the data landscape I've already verified
- **Pima County Superior Court "Agave" public portal** (the county clerk's own site): **free, no login, no CAPTCHA.** Search by name or case number. Returns, per case: defendant **name + date of birth + aliases**, charges (with Arizona statute + felony class), **dispositions** (guilty/dismissed/etc.), full **docket** of filings with dates (including probation-conditions docs and Petitions to Revoke), and judge. A name search returns **all** of a person's cases. Criminal case numbers look sequential (e.g., `CR2024####-001`). It's frame-based/legacy but scriptable.
- **Pima County Sheriff jail roster**: current inmates only (no history). Shows **name + age (NOT DOB)** + booking number + charges-as-booked + bond. Simple to query. Carries a "no commercial use" notice.
- **Tucson Police open crime data** (public ArcGIS/REST): rich incident data (type, date, location) but **de-identified — no names**, so you cannot look a person up from it.
- **Arizona statewide court "Public Access"**: name+DOB search, but **CAPTCHA-gated** (not automatable) and **poorly indexed for Pima felonies.**
- **Arizona "eAccess"**: can buy actual court PDFs, but **requires an account and ~$10 per document.**
- **Arizona AOC "Safer Communities Act" reports**: published annual PDFs giving, **per county**, the share of supervised probationers **convicted of a new felony** (a recidivism rate). Aggregate, not individual.
- **Urban Institute** has two **Pima-specific** studies on probation violations/revocations (2021, 2024).
- The AZ courts note that bulk data "can be provided via electronic media for an **annual subscription fee**" — i.e., an official bulk-data route may exist.
- Local context: Pima County **eliminated automatic probation holds in 2019** (arrest of a probationer no longer triggers an automatic jail hold; it's now officer discretion).

## Reframes I'm already considering (critique these too)
1. Pivot the denominator from **"arrests"** (de-identified, unusable) to **"charged defendants"** (named, DOB'd in court data).
2. Replace the un-automatable **"on probation at the time of the offense"** (needs the probation term length, which is paywalled/courthouse-only) with the automatable **"has a prior felony case"** (repeat-offender signal, computable by matching name+DOB across court cases).

## What I want from you
1. **Feasibility map.** Sort the plausible stories/metrics into three tiers, and justify each placement against the data facts above:
   - **Tier 1 — fully automatable & publishable** (a defensible number/dataset with no per-case human verification).
   - **Tier 2 — automate the *flag*, human verifies before publishing** (leads pipeline).
   - **Tier 3 — not automatable** (and why).
2. **The single best first product.** Name the one automatable civic-transparency metric or dataset I should build first, and exactly why it's the strongest risk-adjusted starting point.
3. **Technical approach** for that first product: data acquisition (**legit routes first** — bulk-data agreement / records request / official subscription — before any scraping), the ETL, the entity-resolution/matching method (and its error modes), the metrics, and refresh cadence. Note where an LLM adds value vs. where deterministic code must own the numbers.
4. **Legal & ethical review.** Bulk automated access to court systems, "commercial use" restrictions, terms-of-service, defendant privacy/harm (naming people, presumption of innocence), and expungement/sealing. What's the responsible posture? What would you refuse to do?
5. **Methodology traps** that would make a published statistic misleading, and how to defuse each — especially the difference between *"% of arrests who were probationers"* and *"% of probationers who reoffend,"* base rates, "charged ≠ convicted," and name/DOB false matches.
6. **MVP pilot.** A concrete, bounded proof-of-concept I could ship in a week or two to test the whole idea before committing.
7. **What am I missing?** Better angles, better data sources, a smarter reframe, or a reason this whole line is a bad idea.

## Constraints to respect
- Solo operator, minimal budget, AI-assisted, human-in-the-loop for anything published.
- Transparency framing, **not** advocacy or a "soft-on-crime" narrative.
- No fabrication; every published number must be traceable to a primary source and reproducible.
- Prefer official/legal data routes over scraping; if you recommend scraping, spell out the risks and a more defensible alternative.

## Output format (so I can compare models cleanly)
1. **Verdict** (3–4 sentences): is this worth doing, and what's the single highest-value automatable play?
2. **Feasibility table**: Story/metric | Tier (1/2/3) | Why | Key risk.
3. **First product**: pick + reasoning + the MVP pilot.
4. **Top 5 risks** (legal, ethical, methodological) each with a one-line mitigation.
5. **What I'm missing / would push back on.**

End by stating your confidence level and the two assumptions in my framing most likely to be wrong.
