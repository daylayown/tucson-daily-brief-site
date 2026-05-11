# Tucson Daily Brief — Site Redesign Plan

**Date:** 2026-05-11
**Scope:** Information architecture and homepage redesign — *not* a full visual rebrand. Desert palette and DF-inspired typography stay. Pure-static, JS-free, Python-rendered constraints honored throughout.
**Why now:** Before launching the RAG-powered Ask page and the Tucson Responsiveness Index, the homepage needs to graduate from "reverse-chron daily-brief stream" to "entry hall for a multi-surface publication." Doing it after those launches would be the wrong order.

---

## Why the current site doesn't scale

The site is currently four reverse-chronological streams (Daily, Meeting Watch, News Reports, Public Record) plus one unlisted tool (Crossword). Every section index renders the *exact same template*: `<header>` → three-link section nav → identical Buttondown subscribe box → `<ul class="post-list">`. The homepage is the most extreme case — the only thing that distinguishes Daily Brief from Meeting Watch is the tagline and the items. There is no concept of "home is special." This worked when there was only one product. With seven surfaces of three different shapes coming, it stops working — the homepage cannot keep being a single-content stream that happens to be named "Tucson Daily Brief," because that stream is going to become *one of seven things you can do here*, not *the thing this site is*.

## Three shapes, not one

The IA now has to gracefully hold three different content shapes:

- **Streams** (Briefings, Meeting Watch, News Reports, Public Record) — dated, chronological, reverse-chron index pages
- **Living/evergreen data products** (Responsiveness Index, future: Budget Analysis, FOIA Lead Spotter) — dashboards that update in place, not append
- **Interactive tools** (Ask) — user-driven, no chronology

Every news+tools reference site (ProPublica, The Markup, Texas Tribune) treats these as **peer sections** with explicit visual separation. TDB is currently doing the wrong thing — pretending all five existing surfaces are the same shape — and that breaks the moment Ask and Responsiveness ship.

## Reference points consulted

- **ProPublica.** Hero + topical streams + an explicit *"Explore Our Data — Maps, Visualizations, and Databases"* section. Data tools are visually peer with investigations, not buried under "About." Takeaway: the dashboard category gets its own labeled rail, not a nav item.
- **The Markup.** Five horizontal sections on the homepage: *This Just In, Impact, Investigations, Blueprints, Tools*. Each is a distinct content type with its own treatment. Closest existing analog to TDB's "streams + dashboards + tool" mix.
- **Texas Tribune.** Top nav: *Investigations, Guides, About, Events, Data, Newsletters, Donate.* "Data" is a top-level nav item, *peer* with "Investigations." Newsletter CTA appears multiple times (top, mid, footer).
- **Block Club Chicago.** Newsletter signup mid-page, not above the fold. Trust-building copy ("Get Our Free Newsletter") rather than perks pitch.
- **Daring Fireball.** TDB's inheritance. Worth noting: Gruber doesn't have seven products. The DF model breaks once you have data tools.
- **Stratechery.** Single-author + paid product. Useful for "this is a subscriber-only thing" signaling.

## Direction chosen: B — Zoned homepage

Two other directions were considered and rejected (see "Rejected directions" below).

### Homepage structure

```
Tucson Daily Brief
An ongoing experiment...
Briefings · Meetings · Reports · Record       ← streams nav (terracotta)
Ask · Responsiveness                          ← tools nav (sage)
────────────────────────────────────────────
TUESDAY, MAY 11
Today's Brief
Trump admin proposes canceling NASA
funding for U of A's OSIRIS-APEX...
Read today's brief →
────────────────────────────────────────────
Latest from across TDB

MEETING WATCH · May 12
Pima County BOS — What to Watch

NEWS REPORTS · May 6
Oro Valley Council Approves...

PUBLIC RECORD · May 12
Quick Mart · Series 10 Beer & Wine
────────────────────────────────────────────
Tools

ASK TDB
Ask any question about Tucson. Answers
come from TDB's own reporting, with citations. →

RESPONSIVENESS INDEX
How fast does Tucson respond to its
residents? A living dashboard. →
────────────────────────────────────────────
[ TDB Weekly subscribe box ]
Subscribers also get The Tucson Mini —
a weekly 5×5 crossword.
────────────────────────────────────────────
Recent briefings (7 items)
  May 10 · Southside community vigil
  May 9  · Cooling centers open early
  May 8  · TUSD school closure process
  ...
  See all daily briefings →
────────────────────────────────────────────
Footer
```

### Nav model

Two rows in `.section-nav`. Streams on top in terracotta, tools below in sage. Visually distinguishes the two shapes without adding new structure. The Mini link is *not* in the nav — it lives inside the subscribe panel as the perk, preserving the unlisted/noindex constraint.

### Stream vs. tool vs. dashboard distinction

- **Streams** (Briefings, Meetings, Reports, Record): card label in terracotta uppercase, dated, headline-first.
- **Tools** (Ask, Responsiveness): card label in sage uppercase, no date, prompt-shaped headline, trailing arrow. Distinct because they don't decay.
- **Mini**: lives inside the subscribe panel as "subscribers also get."

### Newsletter signup

Keeps the existing panel but moves below the tools row, with a one-line Mini callout instead of the current `<h2>` Mini header. Subscribe is what the user clicks *after* they've seen what TDB does — not before.

### Visual changes (small)

- Section-card label style: small uppercase eyebrow above each card with a colored bullet (terracotta for stream, sage for tool).
- Everything else reused: same type stack, same colors, same line-height, same column width.
- Cards are `<article>` elements separated by hairlines.

### What's gained

- A first-time visitor in seven seconds learns what TDB is. Right now they learn what yesterday's news was.
- Ask launches into a homepage that already has a slot for it — the marketing moment lands on a built-in shelf, not on a press-release page.
- Responsiveness Index has a permanent home next to Ask, framing "tools" as a real category before the third tool ships.
- The Mini's value gets communicated without being publicly linked.
- The compressed recent-briefings list keeps the DF feel for return visitors.

### What's given up

- The newest daily brief is no longer the *first* thing on the page — it's the *featured* thing. Fractional click cost for pure daily readers. Mitigated by the prominent "Today's Brief" card and the recent-briefings list at the bottom.
- More renderer logic. Homepage now reads from four content directories instead of one.

---

## Rejected directions

### Direction A — Newspaper sections (conservative)

Keep the homepage as the Daily Brief stream; just expand the section nav to all seven surfaces.

**Rejected because:** The homepage still teaches readers that TDB is "a daily brief that also happens to do these other things." A first-time visitor doesn't learn that there's a queryable archive and a transparency tracker until they read the nav carefully. Wastes the marketing-launch moment of Ask.

### Direction C — Ask-first (aggressive)

Lead with the Ask interface as the primary surface; demote daily streams below.

**Rejected because:**
- Daily readers (existing audience) get pushed one level down.
- If the RAG agent has a bad day (rate-limited, slow, hallucinating) the homepage is broken. High-blast-radius.
- Requires JS on the homepage, which violates the JS-free constraint everywhere except `ask.html`.
- Premature — Ask is *one* tool. Better to do this after Ask runs for a quarter and has metrics.

---

## Implementation plan

Roughly **6–10 hours** of focused work.

### Files that change

- `generate_post.py` — `render_index()` becomes `render_homepage()`, reads from four content directories, renders new sections. A new `render_briefings_index()` produces `briefings.html` (the moved daily archive). New helpers: `collect_latest_meeting()`, `collect_latest_report()`, `collect_latest_filing()`. About 150–200 lines, replacing the current ~70-line `render_index`.
- New `rebuild_homepage()` entry point exposed via CLI flag so the agenda, news-reports, and public-record pipelines can refresh the homepage when they publish.
- `style.css` — additions only, no changes to existing rules. New classes: `.home-feature`, `.home-card`, `.eyebrow.stream`, `.eyebrow.tool`, `.home-recent-list`, `.tool-card`, `.streams-nav`, `.tools-nav`. Roughly 80 new lines.
- `agenda_mining.py` — update `render_meeting_index` nav; call `rebuild_homepage` after publishing.
- `ai_reporter.py` — update `render_report_index` nav; call `rebuild_homepage` after publishing.
- `public_record_liquor.py` — update `render_index_html` nav; call `rebuild_homepage` after publishing.
- New stub `ask.html` and new stub `responsiveness/index.html` so the homepage tool cards link to *something* on day one.
- `briefings.html` — generated by `render_briefings_index()`, mirrors the current homepage's full archive list.

### What doesn't change

- Individual post HTML (`posts/*.html`, `meeting-watch/*.html`, `news-reports/*.html`, `public-record/*.html`).
- Buttondown form, Telegram pipeline, agenda mining, AI reporter, podcast generation, newsletter generator.
- Crossword pipeline. Stays unlisted.
- RAG agent itself. The redesign creates the slot it will land in; the agent ships separately.

### Phasing

1. **Hour 1–3:** New `render_homepage()` and `render_briefings_index()`. New CSS. Test by running `generate_post.py` against today's brief and inspecting locally.
2. **Hour 3–5:** Update the three section-nav renderers in the agenda/news-report/public-record pipelines. Add `rebuild_homepage` calls.
3. **Hour 5–7:** Build `ask.html` and `responsiveness/index.html` stub pages with the desert palette and "Coming soon" copy.
4. **Hour 7–8:** Cross-test all four pipelines end-to-end; verify each publishes its own thing *and* refreshes the homepage.
5. **Hour 8–10:** Buffer for the small things (mobile QA at 375px, OG tags, sitemap update).

The redesign can ship before the Ask launch — `ask.html` is a stub on day one — and the launch becomes "the Ask card on the homepage now works" rather than "we added a new section."
