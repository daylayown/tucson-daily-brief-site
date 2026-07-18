# Information-Architecture Reorg + Naming Overhaul

Planning doc — **2026-06-24**. Status: **approved, building locally (not yet pushed to prod).**

> **⚠️ Labels superseded 2026-07-18.** The hub *structure* below is current, but three reader-facing labels were renamed again in a second wave (from `sol/sol-new-names.md`): **Local Meeting Previews → What to Watch**, **Local Meeting Reports → What They Decided**, **Deep Dives → In Depth**. URLs, dirs, and `_NAV` keys (`meetings`/`reports`/`indepth`) were preserved both times. Where this doc says "Local Meeting Previews / Local Meeting Reports / Deep Dives," read the current label. See the rename note in CLAUDE.md.

Motivation: the streams nav had grown to 6–7 flat, mixed-register items ("Briefings · Meeting Watch · News Reports · Spotted · In Depth · Ask") and was about to gain a 7th (OV development tracking). The list conflated *content type* with *reader intent* and was headed for 10–12 flat items as roadmap sections land. This reorg collapses it into **five clear, durable hubs**, renames every section in a single plain-spoken register (clarity for a first-time reader over cleverness), and folds the new Oro Valley development coverage in cleanly.

This is the IA + naming step. It pairs with — and sets up — the OV structured-data buildout (`OV-DATA-FEASIBILITY.md`) and the public "we're ramping up suburban coverage" announcement.

---

## 1. Final structure (source of truth)

Top-level nav (5 items):

> **Daily Briefs · Local Government ▾ · Around Town ▾ · Deep Dives · ChatTDB**

| Top-level | Was | Kind | Contains |
|---|---|---|---|
| **Daily Briefs** | Briefings | section | the daily news synthesis |
| **Local Government** | *(new hub)* | hub | **Local Meeting Previews** (was Meeting Watch) · **Local Meeting Reports** (was News Reports) · *future: Vote Tracker, Budget* |
| **Around Town** | *(new hub)* | hub / combined feed | new businesses & filings (was Spotted) + development & rezonings (the OV/Marana work) |
| **Deep Dives** | In Depth | section | standalone feature stories |
| **ChatTDB** | Ask | tool | the AI Q&A surface |

### Naming decisions + rationale (one line each)
- **Daily Briefs** — say exactly what it is; reinforces the eponymous product. (User: "people need to know exactly what they're looking at.")
- **Local Government** (hub) — groups the deliberative/process beat; carries the "government" context so its children can stay short-ish.
- **Local Meeting Previews / Local Meeting Reports** — matched, parallel pair; the shared "Local Meeting" prefix signals same beat, "Previews/Reports" signals before/after. Killed the vague "News Reports."
- **Around Town** (hub) — consumer-framed "what's opening & changing near me." Merges filings + development because to a reader they're one question. Replaces the unclear "Spotted."
- **Deep Dives** — plain "big thorough story"; avoids the "Reports" collision that "In Depth Reports" would create.
- **ChatTDB** — piggybacks on "ChatGPT" familiarity to instantly signal "AI chat." The one bit of product sparkle, and it's *clear*, unlike the old "Ask."

---

## 2. Nav architecture (NO JavaScript — hub landing pages, not dropdowns)

The site ships zero JS by design, so the ▾ hubs are **landing pages + a contextual second nav row**, not hover/click dropdowns.

- **Row 1 (always):** the five top-level items. The current hub/section is marked active (plain text, no link).
- **Row 2 (contextual):** appears only when you're inside a hub or on one of its child pages, listing that hub's children. Reuses the existing two-row nav infrastructure (the old `tools-nav` second-row slot, repurposed). On mobile both rows stack (existing `.section-nav { flex-direction: column }`).

`section_nav_html()` gains a hub-aware signature:
```
section_nav_html(active_top="", active_sub="", path_prefix="")
```
Driven by a single `_NAV` registry: `(key, label, href, children)` where `children` is `None` for a direct section or a list of `(key, label, href)` for a hub. Old per-renderer calls (`active="record"`, `active="indepth"`, etc.) get mapped to the new keys.

### Hub pages
- **`local-government.html`** (new) — landing page: intro sentence + the latest Preview and latest Report surfaced inline (reuse `collect_latest_meeting`/`collect_latest_report`) + links to the two full archives. Contextual row shows on it and on the two child pages.
- **`around-town.html`** (new) — IS the combined feed (filings + development merged, newest first, each item tagged **New business** or **Development**). Canonical Around Town page; the nav points here.

---

## 3. URL / file plan (preserve existing URLs — same trick as the Spotted rename)

Display names change; **URLs, directories, file prefixes, and internal code terms stay** to avoid breaking links/bookmarks (exact precedent: Public Record → Spotted kept `public-record.html` + `public-record/`).

| Section (new label) | Page URL (unchanged) | Item dir (unchanged) |
|---|---|---|
| Daily Briefs | `briefings.html` | `posts/` |
| Local Meeting Previews | `meeting-watch.html` | `meeting-watch/` |
| Local Meeting Reports | `news-reports.html` | `news-reports/` |
| Around Town — filings | (feed at `around-town.html`) | `public-record/` |
| Around Town — development | (feed at `around-town.html`) | `around-town/` (NEW) |
| Deep Dives | `in-depth.html` | `in-depth/` |
| ChatTDB | `ask.html` | — |

New files: `local-government.html`, `around-town.html`, `around-town/` (development item pages), the OV development pipeline script.

Backwards-compat: `public-record.html` keeps generating (so existing inbound links work) but is **dropped from the nav**; its content also flows into `around-town.html`. Filing detail pages' "back" link retargets to `around-town.html`. Decision: keep `public-record.html` as a still-working secondary view for now; revisit a meta-refresh redirect later if it's confusing.

---

## 4. Around Town combined feed

`around-town.html` is rebuilt centrally (in `generate_post.py`, alongside `rebuild_homepage`) by scanning **both** `public-record/*.html` (filings) and `around-town/*.html` (development), merging by date, newest first. Each card carries a type eyebrow:
- **New business** / **New filing** → from `public-record/`
- **Development** → from `around-town/`

So both the existing liquor pipeline and the new OV development pipeline just write their item pages; the feed assembles automatically (idempotent, same as the homepage).

Keep the two lanes visually distinguishable so Around Town's "filings" and "development" don't blur (noted earlier as a risk: Spotted's future building-permit scope vs. development cases).

---

## 5. Oro Valley Development pipeline (populates Around Town — "Development")

New script `dev_watch_orovalley.py`, shaped like `public_record_liquor.py`:
- **Source:** OV ArcGIS REST `https://gismap.orovalleyaz.gov/gismap/rest/services/CED-Planning/Development_Cases/MapServer/0/query` — verified live 2026-06-24 (no auth, no WAF). Fields per `OV-DATA-FEASIBILITY.md` §1.
- **Poll + diff** on `CaseNumber` + `last_edited_date`; state in `around-town/.dev_state.json` (gitignored). New or materially-changed case → render/refresh an item page.
- **Data is already structured** — no LLM needed for the facts (CaseNumber, Common_Name, Case_Type, Case_Status, Location, Applicant_Name, Outreach_Link…). One **small, tightly-grounded** Sonnet pass writes a 2-sentence plain-English "what this is" summary from the case fields ONLY (soft-hedged: "proposes," "would" — per the quality bar; no invention).
- **Item page:** `around-town/{slug}.html`, same chrome as a Spotted filing (facts `<dl>` + summary + link to the OV case/outreach page + AI disclosure).
- **Telegram** notification on new items; **idempotent**.
- **Marana next:** structured the script so a `dev_watch_marana.py` sibling can follow once a Marana source is identified (noted for the announcement's "Marana coming" promise).

> v1 may launch with Pima/Tucson development still TODO; Around Town's "Development" lane is OV-first. That's fine and on-thesis (OV is the wedge).

---

## 6. "How TDB works" section guide

Readers should be able to learn exactly what each section is. Three layers (no redundancy):
1. **One sharpened sentence atop each hub/section page** (most already have a `section-intro`).
2. **A detailed guide folded into a revamped About** (`about.html`, hand-authored) — a short paragraph per section + the AI-drafts / human-reviews model. Doubles as the backbone of the announcement post.
3. **A compact "What you'll find here" strip on the homepage** linking into each hub.

---

## 7. Mobile (treat the phone as the primary canvas)

Most traffic is mobile; this reorg must look intentional there, not merely "not broken." Checklist:
- Both nav rows stack cleanly and stay tappable (adequate target size, no cramped wrap). Verify 5 top items + the contextual row at 390px and 360px widths.
- Hub landing pages and the Around Town feed render single-column with comfortable spacing.
- Card eyebrows / type tags legible at small sizes.
- Test renders at desktop (1280), tablet (~800), and phone (390/360) before declaring done. Existing breakpoint is a single `@media (max-width: 880px)`; add finer rules only where the nav needs them.

---

## 8. Cross-cutting label updates (don't miss these)
- `generate_post.py`: `_STREAMS`→`_NAV`, `section_nav_html`, homepage cross-stream card labels ("Meeting Watch"→"Local Meeting Previews", "News Reports"→"Local Meeting Reports", "Spotted"→"Around Town"/type tag, "In Depth"→"Deep Dives"), "Latest from across TDB" stays.
- Per-renderer eyebrows/titles/back-links/`active=` keys: `render_indepth.py`, `public_record_liquor.py`, `agenda_mining*.py` (index titles + nav), `ai_reporter.py` (report pages + index).
- `social/render_feature_carousel.py` kickers (lower priority — promo assets, not the site).
- Page `<title>`s and `section-head`s.

## 9. Deferred to after local review / not blocking the visual review
- RAG index: add an `around-town/` chunking branch in `rag/build_index.py`.
- Cron: add `dev_watch_orovalley.py` to `check_agendas.sh`.
- Announcement post (capstone) + the "Marana coming" note — written once the OV build is in.
- Marana development source identification.

## 10. Build sequence
1. **Nav engine + renames** — `_NAV`, hub-aware `section_nav_html`, relabel everywhere. (Structure visible.)
2. **Hub pages** — `local-government.html`, `around-town.html` + central Around Town feed builder.
3. **OV development pipeline** — `dev_watch_orovalley.py`; run it to populate real Around Town items.
4. **About guide + homepage "What you'll find" strip.**
5. **Mobile pass** — render + eyeball desktop/tablet/phone; fix.
6. *(later)* RAG + cron wiring, then the announcement post.

Reviewed locally end-to-end before any `git push`.
