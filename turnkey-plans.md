# Turnkey Report: Carfax for NYC Apartments

## The Idea

A per-building report product for NYC apartments — like Carfax for vehicles. Prospective renters (and buyers) get a comprehensive history of a building before signing: landlord sanctions, repair history, violations, ownership changes, rent stabilization status. Solves the information asymmetry problem in a market where decisions are made in hours.

## Why NYC Is Ideal

NYC publishes an extraordinary amount of building-level data through open APIs and datasets:

| Data Source | What It Covers | Access Method |
|---|---|---|
| **HPD Violations & Complaints** | Full housing code violation history per building (heat, lead, pests, structural) | NYC Open Data / Socrata API |
| **DOB (Dept of Buildings)** | Permits, complaints, violations, elevator inspections, construction history | NYC Open Data / Socrata API |
| **ACRIS** | Property transfer records, mortgages, liens, ownership history | NYC Open Data |
| **HPD Registrations** | Current owner/managing agent on file | NYC Open Data |
| **311 Complaints** | Noise, rodents, heat/hot water, illegal conversion — geocoded and timestamped | NYC Open Data / Socrata API |
| **FDNY** | Fire inspection results, violations | NYC Open Data |
| **DHCR Rent Stabilization** | Which units are rent-stabilized (gold for renters) | Published lists |

Most of this is available through the NYC Open Data portal (Socrata API) with no authentication required. Far ahead of Tucson's mix of Legistar APIs, Destiny Hosted HTML scraping, and OnBase PDF extraction — NYC is almost entirely structured JSON via REST APIs.

## What Transfers From TDB

| TDB Skill | Turnkey Report Equivalent |
|---|---|
| Multiple data source ingestion (Legistar, Destiny, OnBase, Swagit) | Multiple NYC APIs (HPD, DOB, ACRIS, 311, FDNY) |
| Claude editorial analysis of raw government data | Claude synthesis of building history into a readable report |
| Idempotent pipeline design | Cache reports per building, refresh on demand |
| Public Record extraction (liquor licenses from agendas) | Extract meaningful signals from bulk violation/complaint data |
| Auto-publishing to static site | Report delivery (web, PDF, email) |

The architecture is essentially the same: ingest structured public data -> LLM pass for editorial synthesis -> deliver a human-readable product.

## What's Different (Harder)

### Entity resolution

TDB deals with ~4 municipalities and a handful of meetings per week. An NYC building report needs to join records across 6+ databases using BIN (Building Identification Number), BBL (Borough-Block-Lot), or address — and NYC addresses are messy (apartment numbers, alternate addresses, pre/post-merge buildings). This is the real engineering problem, not the scraping.

### Scale

TDB processes a few documents per day. A building report product needs to handle ~1M+ residential buildings. Pre-ingest and index rather than query APIs on-demand per report.

### LLM cost equation

TDB spends ~$3-4/month because volume is tiny. Thousands of reports means even Haiku adds up. The LLM layer should be a synthesis/narrative step on top of structured data already extracted and scored deterministically — not the primary analysis engine. Use traditional code for scoring and flagging, LLM only for the human-readable narrative.

## Business Model Options

1. **Freemium per-report** — Show the violation count and a letter grade for free, charge for the full narrative with history and context. Probably the right move.
2. **B2B to brokerages** — Real estate agents offer reports as a value-add. Higher ACV, fewer customers.
3. **Media-first** — Launch as a journalism product (worst landlords, neighborhood trends) and convert the audience to a tool. This is the path where existing TDB + Consumer Reports skills give the biggest unfair advantage.

## Existing Players

- **JustFix.nyc** — Tenants' rights tool, does some of this for advocacy purposes
- **Who Owns What (by JustFix)** — Ownership mapping, connects buildings to landlord portfolios
- Neither is positioned as a consumer report product for prospective renters/buyers

## The Hard Part

The reason nobody has nailed this yet isn't data access — it's distribution and willingness to pay. Renters making split-second decisions in a competitive market are the exact people least likely to pause and buy a report. Higher-leverage customers:

- **Buyers** (co-ops/condos) — bigger financial decision, more time to research
- **Landlords** doing due diligence on acquisitions
- **Real estate professionals** — agents, property managers, investors

## NYC as the Next City (Instead of Phoenix)

Considerations for expanding the TDB model to NYC rather than Phoenix:

**For NYC:**
- Born and raised there — deep neighborhood knowledge and cultural fluency
- Wealth of structured, API-accessible municipal data (far better than most cities)
- Massive market with higher willingness to pay for local information
- Natural synergy with the Turnkey Report product — same data pipelines feed both
- NYC's municipal data infrastructure (Open Data portal, Socrata APIs) is a known quantity
- Could cover NYC City Council, community boards, MTA, etc.

**For Phoenix:**
- Geographic proximity to Tucson — same state politics, overlapping stories
- Natural editorial expansion (Tucson -> Arizona)
- Smaller, less competitive local media market

**The case for NYC:** If the goal is to demonstrate the "AI + public data" thesis as a portfolio piece and potential business, NYC is a bigger stage with better data. Phoenix is the obvious geographic expansion, but NYC is the bigger opportunity — especially if Turnkey Report and a NYC daily brief share the same data pipelines.

## Prototype Scope

A working prototype could be built in a weekend given existing TDB skills:

1. Pick 3-4 NYC Open Data endpoints (HPD violations, DOB complaints, 311, ACRIS)
2. Build ingestion scripts (simpler than TDB — just Socrata API calls, no scraping)
3. Entity resolution layer: normalize addresses -> BIN/BBL lookup
4. Scoring layer: deterministic flags (violation count, recency, severity, ownership churn)
5. LLM narrative layer: Claude Haiku generates the 1-page "Turnkey Report" from structured scores
6. Static site output: one HTML page per building, same pattern as TDB posts

## NYC Brief: A Data Digest, Not a News Brief

### Why not replicate TDB's format

TDB exists because Tucson is under-covered by traditional media — it fills a gap. NYC doesn't have that problem. The Times, Gothamist, THE CITY, Patch, and dozens of others cover breaking news and events. Competing on news coverage means competing on ground with no structural advantage.

But NYC has a different gap: **nobody is making the city's own data legible to regular people.** NYC publishes more structured municipal data than probably any city in the world, and almost none of it gets surfaced to residents in a useful way unless a journalist decides to write a specific story about it.

### The product: a personalized daily city data digest

An automated intelligence layer on top of NYC Open Data, personalized by neighborhood / community district / zip code. Instead of "here's what happened in the news today," it's **"here's what the city filed about your neighborhood today."**

**Sample daily digest:**

> **Your neighborhood today** (Community District 7, Upper West Side)
>
> - 3 new DOB permits filed — including a full-building demolition permit at 215 W 84th St (rent-stabilized building, 24 units)
> - 5 new HPD violations issued on your block (2 heat/hot water, 1 lead paint, 2 pest)
> - ACRIS recorded 2 property transfers over $2M in your zip code
> - 311 complaints: noise complaints up 35% week-over-week in your CD
> - City Council Committee on Housing meets Thursday — 2 bills on agenda affecting rent stabilization
> - MTA: planned weekend service changes on the 1/2/3

### Why this works

- **Personalization by geography.** NYC residents have intense neighborhood identity but near-zero visibility into public record activity around them. "Here's what the city filed about your neighborhood" is something no newsroom is doing because it doesn't scale with reporters. It scales trivially with APIs and an LLM.
- **No competition.** Not trying to out-report THE CITY or Gothamist. Building something they structurally can't — an automated, personalized, data-first product that treats the city's own filings as a primary source.
- **Feeds Turnkey Report.** The same HPD/DOB/ACRIS/311 ingestion pipeline that generates the daily digest also populates per-building reports. Two products, one data layer.
- **Natural alert triggers.** Demolition permits on rent-stabilized buildings, sudden spikes in violations for a single landlord, large property transfers in gentrifying neighborhoods — these are stories hiding in data that nobody is monitoring systematically.

### Content sources mapped to digest sections

| Digest Section | Data Source | Signal |
|---|---|---|
| Building activity | DOB permits, NOW applications | New construction, demolitions, major alterations — especially on rent-stabilized buildings |
| Housing violations | HPD violations & complaints | New violations by block/CD, severity, repeat offenders |
| Property transfers | ACRIS deeds & mortgages | Sales over threshold, ownership changes, portfolio acquisitions |
| Quality of life | 311 complaints | Noise, pests, heat, illegal conversion — trends and spikes by neighborhood |
| City Council | Legistar (NYC Council uses it) | Bills, hearings, votes — filtered to topics affecting the subscriber's area |
| Community boards | Board meeting agendas/minutes | Land use applications, liquor licenses, street permits — hyperlocal |
| Transit | MTA feeds | Planned service changes, elevator/escalator outages for subscriber's stations |

### How it differs from TDB

| | TDB (Tucson) | NYC Brief |
|---|---|---|
| **Core function** | Local news synthesis + original journalism | Municipal data digest + anomaly detection |
| **Voice** | Editorial, narrative, human-curated feel | Data-forward, personalized, automated |
| **Personalization** | One edition for all readers | Personalized by neighborhood/CD/zip |
| **Competition** | Fills a coverage gap (under-covered market) | Fills a data legibility gap (well-covered market, illegible data) |
| **LLM role** | Editorial analysis and narrative writing | Summarization, anomaly flagging, plain-language translation of filings |
| **Publishing cadence** | Daily, same content for everyone | Daily, different content per subscriber geography |
| **Revenue path** | Substack newsletter / podcast | Freemium digest (free) + Turnkey Reports (paid) + B2B |

### Distribution and growth

The digest is the top of funnel for Turnkey Reports. Free daily digest builds the audience and demonstrates data quality. When a subscriber sees a violation spike on their block or a demolition permit on a neighboring building, the natural next action is "tell me everything about this building" — that's the paid Turnkey Report.

Growth loop: subscriber gets digest -> sees something alarming about a building -> pulls a Turnkey Report -> shares it with neighbors / on neighborhood Facebook group -> new subscribers. The shareability is in the specificity — "did you know our building has 47 open violations?" spreads in a way that generic news doesn't.

### Technical architecture

```
NYC Open Data (Socrata API)          MTA feeds         City Council (Legistar)
        |                                |                      |
        v                                v                      v
    Ingestion layer (daily cron, same pattern as TDB check_agendas.sh)
        |
        v
    Normalized data store (SQLite or Postgres — needed for geographic queries)
        |
        v
    Per-subscriber geographic filter (CD, zip, custom polygon)
        |
        v
    Anomaly detection (deterministic: thresholds, week-over-week changes, known flags)
        |
        v
    LLM narrative pass (Haiku — summarize, translate jargon, write the digest)
        |
        v
    Delivery (email via Substack or Buttondown, web archive, push notifications later)
```

Key difference from TDB: requires a **data store** (not just flat files) because geographic filtering and trend detection need queryable historical data. SQLite is fine for prototype; Postgres if it grows.

## Open Questions

- Pricing: per-report vs. subscription vs. freemium?
- Liability: does publishing building "grades" create legal exposure?
- Data freshness: how often to re-ingest? NYC Open Data update frequency varies by dataset
- Scope: start with one borough or all five?
- Identity: is this a TDB sub-brand, a separate product, or both?
- Digest personalization: how granular? Community district? Zip code? Custom address radius?
- Email platform: Substack (network effects, but limited personalization) vs. Buttondown/Resend (full control over per-subscriber content)?
- Data store: SQLite for prototype, but when does Postgres become necessary?
- Community board coverage: are agendas/minutes available via API or does this require scraping?
