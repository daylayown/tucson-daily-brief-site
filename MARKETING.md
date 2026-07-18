# Marketing & Distribution Strategy

The two-brand split, the distribution loop, content-mix targets, instrumentation TODOs, the impact ledger, and sequencing decisions.

Reference doc split out of CLAUDE.md on 2026-07-17 to keep the always-loaded context lean. Prose is preserved verbatim from CLAUDE.md; CLAUDE.md now carries a short pointer to this file.

---

## Marketing & Distribution Strategy (distilled 2026-07-11)

Distilled from an external strategy review (full docs live **outside the repo** in `~/claude-code-projects/tucson-daily-brief-notes/` — `sol-advice.md` + `sol-advice-2.md`; deliberately kept out of this public repo). The review's core diagnosis matched our own: **TDB has more product than audience — the constraint is distribution, not reporting capacity.**

**Shipped 2026-07-11 (`a8bbd6a` + follow-up):**
- **Consumer promise:** site-wide masthead tagline is now **"The Tucson news you'd otherwise miss, by Nicholas De Leon."** (replaced the AI-experiment line). About page reordered benefit-first; the tool-assisted-speedrun essay moved intact under "How this is made." Subscribe-panel copy now states concretely what arrives ("the week's most important Tucson developments, what local government decided, what's coming next — plus The Tucson Mini").
- **Two-brand split (the rule for all future copy):** reader-facing surfaces lead with the *outcome* (news you'd otherwise miss); the AI/TAS story is for About, LinkedIn, and industry conversations. Don't lead consumer marketing with "AI-assisted journalism."

**The distribution loop (= the working definition of the short-form video project):**
- Two strong social packages per week for **eight consecutive weeks**: one *moat* package (Buried in the Agenda / What They Decided) + one *reach* package (Only in Tucson), published natively to IG/FB/YouTube Shorts, each converting toward the weekly newsletter. Success = the sustained baseline, not any single viral post; review in 4-week blocks.
- **Do NOT launch all six proposed franchises at once.** Backlog franchises (post-traction): Opening Soon / What's Going There, Tucson by the Numbers, Before the Meeting / Civic Week Ahead.
- Content-mix target on social: **60% original civic/data/development, 25% identity/utility/weather, 15% curated outside reporting** — don't let feel-good content overwhelm the moat.
- The review's full weekly cadence (doc 1) is a *ceiling*, not a plan — unsustainable solo. Doc 2's two-packages/week is the plan.

**Instrumentation TODOs (build before/alongside the loop):**
- **✅ UTM convention — the outbound automated links now carry it (Phase 0, shipped 2026-07-18).** Scheme: `utm_source={platform}&utm_medium={channel}&utm_campaign={franchise}`. Wired: the weekly "Buried in the Agenda" short (`buried-in-the-agenda`, already live), the **daily "Only in Tucson" short** (`social/publish_youtube_short.py` → `DAILY_SHORT_LINK`, `only-in-tucson`), and the **podcast feed** (`generate_feed.py` in the OpenClaw skills dir — per-episode `<link>` + description line back to that day's brief, `daily-brief`). **Still manual:** any link you paste by hand on FB/IG/Nextdoor/Reddit/LinkedIn — tag those from the appendix table in `kimi-operational-advice.md`. Read in GA4 → Acquisition → Traffic acquisition → Session campaign; cross-ref Buttondown signup source.
- **✅ Subscribe panel on every content page (Phase 0, shipped 2026-07-18).** `SUBSCRIBE_PANEL_HTML` now renders above the footer on all individual pages — daily briefs, news reports, Spotted filings, meeting-watch previews, deep dives, Around Town dev cases — not just section indexes. Added to each renderer + one-time in-place retrofit of the archives (338 pages). Closes the conversion leak on the highest-intent surfaces.
- **✅ Prev/next edition nav on daily briefs (Phase 0, shipped 2026-07-18).** Self-healing: `render_post` emits an empty `<!--PREVNEXT-START-->…<!--PREVNEXT-END-->` marker; `restamp_edition_nav()` (called from `rebuild_homepage`) fills prev/next for every brief on each rebuild, so the previous newest brief gains its "next" link the moment a newer one publishes. Styled via `.edition-nav` in `style.css`.
- **"How we know" provenance box** on human-reviewed pieces (news reports, deep dives): source type, where found, review status, date. Makes the trust story visible on the work itself.

**Impact ledger:** `~/claude-code-projects/tucson-daily-brief-notes/IMPACT-LEDGER.md` (private). Dated entries of concrete impact (found-it-first, resident action, leads supplied, agency responses, records made usable). Entry #1: Ranch House data-center filing surfaced 2026-06-24, two days before KOLD. **Add entries as they happen** — this is the raw material for grants/partnerships/LinkedIn.

**Sequencing decisions recorded:**
- **Schools beat = post-traction backlog.** The review's detailed schools playbook (franchises, safeguards, advisory group, Vail pilot marketed around family questions) is good — execute it *after* the distribution loop exists, not before. Matches the existing COVERAGE-EXPANSION gate.
- **Responsiveness:** market as concrete questions first ("How long does Tucson take to close 311 reports?"), brand the "Index" only after the constituent measurements have earned trust. Amend `responsiveness/PLANNING.md` framing when building.
- **OPEN — Spanish sequencing:** the review argues for 2 Spanish social posts/week *before* the full tucsonenbreve.com fork (contradicts the current full-fork plan in `TUCSONENBREVE.md`). Needs a deliberate decision, not drift.
- **✅ "Buried in the Agenda" UN-SHELVED — weekly auto-short SHIPPED 2026-07-11.** `social/generate_agenda_short.py`, run by `check_agendas.sh` every **Monday** after the agenda miners (so fresh previews are included). Flow: scan `agenda-watch/*-preview.md` for meetings in the next 7 days → Sonnet picks the most consequential under-covered item (consent-calendar/big-dollar/low-visibility signals) and writes a 4-beat hedged script (Sol formula: fact → where buried → why it matters → vote date) → **a second Sonnet fact-check pass verifies every claim against the preview text** (added because single-pass runs intermittently speculated consequences not in the source; the verifier catches + rewrites them) → render with the dark `buried-in-the-agenda` series preset → **publish public to YouTube Shorts unattended** (user call 2026-07-11: full-auto, same posture as the daily Short while YouTube-only) → Telegram notification with the URL so a bad one can be pulled fast. Skips cleanly on weeks with no upcoming meetings or no genuinely strong item (the model may return "nothing this week"). Dedup state: `social/cards/.used-agenda-items.json`. Caption carries the meeting-preview URL with the UTM convention (`utm_source=youtube&utm_medium=short&utm_campaign=buried-in-the-agenda`). Cost ~2.5¢/week (two Sonnet calls).
