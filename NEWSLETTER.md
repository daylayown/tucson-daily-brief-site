# TDB Weekly Newsletter

Strategic logic, format, editorial voice, recency guardrail, the three-component pipeline, Buttondown platform decision, sender architecture, and the site signup form.

Reference doc split out of CLAUDE.md on 2026-07-17 to keep the always-loaded context lean. Prose is preserved verbatim from CLAUDE.md; CLAUDE.md now carries a short pointer to this file.

---

## TDB Weekly Newsletter

Weekly editorial newsletter delivered via Buttondown. Reader-facing promise: "Feel more caught up on Tucson every Sunday." Generated from the past 7 days of TDB content (daily briefs + news reports + public-record filings + upcoming meeting previews) by Claude Sonnet 4.6, written as a markdown draft, **human-reviewed before sending**.

**Status:** Full pipeline live as of 2026-05-08. **Generation is a manual step of the Saturday ritual, not cron'd (changed 2026-07-04).** The old Friday-6pm cron generated + auto-uploaded a draft a full day *before* Saturday's crossword existed, so every draft shipped with a "no puzzle available" placeholder. Now: lock this week's Tucson Mini first (generate + review together), then run `run_newsletter.sh` by hand — and `generate_newsletter.py` **hard-stops if no puzzle is locked for the send date** (escape hatch: `--allow-missing-puzzle`), so a puzzle-less draft structurally can't ship. The user does an editorial pass and manually clicks "Schedule send" in Buttondown for Sunday 5am MST. First real issue sent 2026-05-10.

**Name:** TDB Weekly. Boring on purpose — initialism-forward, instantly legible, doesn't lock the day. (Working name "Sunday in Tucson" was rejected 2026-05-07; the user's gut was that boring + initialism-forward branding fits the product better.)

### Strategic logic

A daily site is great for the people who already know about TDB, but it's a terrible discovery surface — daily readers are a tiny minority of any audience. Layering a weekly curation on top of the daily firehose is how regional outlets actually grow (Axios Local, most successful local newsletters). Cost is essentially zero: a Sonnet pass over the previous seven days is ~$0.07/run, and the existing ElevenLabs TTS pipeline handles the audio version when we get there with no new infrastructure.

### Format (encoded in the prompt)

~800–1200 words, structured warm-not-civic. No H1 title — the email subject line is the title. The body opens directly with the warm paragraph.

- **Warm opening** (no heading) — 2-4 sentences setting the mood, often referencing weather/season
- **## What's worth knowing** — 3-4 most important Tucson-area stories of the week, narrative paragraphs, not a list
- **## What changed around town** — local government decisions, neighborhood changes, development items
- **## What's opening** — new businesses across food/drink/retail/fitness; liquor filings are ONE input among several
- **## One thing to watch** — specific upcoming meeting or event in the next ~2 weeks
- **## The Tucson Mini** — single short paragraph + crossword link
- **Closing note** (no heading) — ~2 sentences, warm beat

### Editorial voice

Warm, friendly, kitchen-table-Sunday-morning. NOT civic-tech or insider — the reader doesn't see the AI pipelines, the agenda mining, the public-records work behind it. Different voice from the daily brief: the daily is fast and headline-y; the weekly is slower, more opinionated, more story-shaped.

The same Sonnet pass that picks the week's best stories also rewrites them in newsletter voice. Not a digest of headlines.

The prompt explicitly bans civic-tech phrasings ("public records," "agenda mining," "local intelligence," "monitoring the situation," "our review," "flagged by," "surfaced from," "according to filings") because the model leaks them by default in v1. Concrete banned-phrase examples in the prompt land better than abstract rules.

### Recency-claim guardrail

Encoded in the prompt: a business is only "newly opened" if the source content has an explicit recent date ("opened April 24," "grand opening Saturday"). News *coverage* of a business this week is not the same as the business *opening* this week — many places get their first press long after they open. Default to attribution-style hedging: "Bloom Tea Wellness was profiled in Inside Tucson Business this week." Reserve "newly opened" / "just opened" for items with an explicit date.

This was identified during the first draft review on 2026-05-07. Bloom Tea actually opened in January, but the May 3 daily brief said "Bloom Tea Wellness has opened in Oro Valley" because of an Inside Tucson Business profile, and the model dutifully repeated it. The newsletter-layer fix is defensive; the long-term fix is upstream — tighten `TUCSON-BRIEF.md` to require explicit dates for any "X has opened" claim. Deferred until we have more weeks of data on how often this recurs.

### Pipeline

Three components chain together via `run_newsletter.sh`:

**1. `generate_newsletter.py` — markdown draft from past-week content**

1. Calculates send date (next Sunday by default; overridable via `--send-date`).
2. Scans the past 7 days of `posts/`, `news-reports/`, `public-record/` (mtime-based for the last) and the next 14 days of `meeting-watch/`.
3. Strips HTML chrome (head/script/header/footer/nav) and tags from each file before passing to the model.
4. Picks the puzzle for the send date from `crossword/puzzles/` (exact-date match, else earliest puzzle dated after) and embeds `https://tucsondailybrief.com/crossword/play.html?p={slug}` in the prompt.
5. Sends ~17K tokens of context to Sonnet 4.6 with the editorial prompt (voice rules, format spec, recency guardrail, hard rules).
6. Writes the draft to `newsletter/drafts/tdb-weekly-YYYY-MM-DD.md` (gitignored — drafts are working state).

Cost: ~$0.07/run. Output: ~950 words drafted directly in markdown.

**2. `upload_to_buttondown.py` — push draft to Buttondown via API**

1. Strips the `*Draft generated...*` metadata header that the generator prepends.
2. Derives a subject line from the filename (e.g., `TDB Weekly — May 10, 2026`); overridable via `--subject`.
3. POSTs to `https://api.buttondown.email/v1/emails` with `status: "draft"`, `email_type: "public"`. Buttondown stores the markdown natively; no HTML conversion needed.
4. Prints the edit URL (`https://buttondown.com/tucsondailybrief/archive/<slug>/`) so the user can open and edit.

Auth: `BUTTONDOWN_API_KEY` from `~/.config/environment.d/buttondown.conf`.

**3. `run_newsletter.sh` — manual Saturday-ritual wrapper (NOT cron'd)**

Loads env vars from `~/.config/environment.d/`, runs the generator with `--force`, finds the latest draft, and uploads it. Logs to `/tmp/newsletter-gen.log`. Single `--dry-run` flag for manual testing.

**No cron entry (removed 2026-07-04).** This is the last step of the manual Saturday ritual: generate + review this week's Tucson Mini together and lock it in, then run `./run_newsletter.sh`. Because the newsletter now runs *after* the puzzle is locked, the crossword link is always present. The draft then sits in Buttondown for editorial review; the user manually schedules the send for Sunday 5am MST. (Pre-2026-07-04 backup of the crontab with the old `0 18 * * 5` line: `~/.cache/crontab/crontab.pre-newsletter-removal.bak`.)

Usage:

```bash
.venv/bin/python3 generate_newsletter.py                  # generate draft only
.venv/bin/python3 generate_newsletter.py --dry-run        # print prompt, no API call
.venv/bin/python3 upload_to_buttondown.py <draft.md>      # upload existing draft
./run_newsletter.sh                                        # full chain (cron uses this)
./run_newsletter.sh --dry-run                              # full chain dry run
```

### Critical principle: do not duplicate the website

The newsletter must not be a copy of the daily site. If both surfaces show the same content, neither has a reason to exist.

- **Website** = daily archive, canonical source, searchable, linkable, comprehensive.
- **Newsletter** = weekly editorial product. Opinionated, curated, written *to* a specific person reading at the kitchen table on Sunday morning. Different voice, different selection logic, different value proposition.

### Platform: Buttondown (decided 2026-05-06, wired 2026-05-08)

Originally planned around Substack for the recommendation flywheel. Pivoted to **Buttondown**:

- **Real REST API.** Buttondown supports creating drafts, scheduling sends, and managing subscribers via API. Substack has no posting API (read-only stats; unofficial reverse-engineered libraries are fragile and unsafe for cron).
- **Markdown-native.** Buttondown stores posts as markdown, which fits the rest of the TDB pipeline naturally. No "render to HTML and paste manually" workflow.
- **No revenue cut.** Substack takes 10% on paid subscriptions; Buttondown is flat-fee SaaS.
- **Single-developer-friendly.** Buttondown is tooling, not a media platform.

**The trade-off:** Substack's recommendation engine is a real distribution channel for independent writers. Buttondown gives that up — TDB would build distribution itself through word-of-mouth, the Tucson Mini referral hook, and partnerships with existing Tucson outlets. Acceptable for build velocity and editorial control on a single-developer side project.

### Sender architecture

- **From:** `Nicholas De Leon <tdb@mail.tucsondailybrief.com>` (subdomain).
- **Reply-To:** Buttondown-managed (`replies+UUID@replies.buttondown.email`). Replies land as wrapped notifications in user's Gmail; user replies back as themselves. The "view replies in Buttondown dashboard" feature is preserved.
- **DNS for `mail.tucsondailybrief.com`:** delegated to Buttondown's nameservers (`ns1.onbuttondown.com`, `ns2.onbuttondown.com`) via 2 NS records on the apex. Buttondown manages all DKIM/SPF/MX/DMARC at the subdomain in perpetuity — no manual record management.
- **DNS for apex (`tucsondailybrief.com`):** still owned by user. Cloudflare Email Routing forwards `tdb@tucsondailybrief.com` → `nicholas@daylayown.org`. Used for direct emails to the apex address (website inquiries, business contacts) — not load-bearing for newsletter replies anymore but keeps the apex address functional.

**Why the subdomain split:** Cloudflare Email Routing takes exclusive ownership of MX records at the apex by design. Postmark (Buttondown's underlying ESP) wanted an MX too. Couldn't coexist. Subdomain delegation cleanly avoids the conflict.

**Account:** username `tucsondailybrief`, login `nicholas@daylayown.org`. API key in `~/.config/environment.d/buttondown.conf`.

### Tucson Mini as the subscriber perk + funnel

The Mini (see `CROSSWORD.md`) is the subscriber-exclusive perk and the growth hook. Architecture:

- Each weekly newsletter contains a fresh Tucson Mini link.
- The play page is unlisted (noindex, no public links) — subscribers get the URL only via the newsletter.
- Static play page on the TDB site, JSON puzzle data behind unguessable slugs.
- The newsletter generator reads from `crossword/puzzles/` and auto-embeds the play URL for the send date.

NYT Mini is the dominant retention pattern for newsletters with games. The Tucson Mini is the local version: 5×5, charming, takes 1-3 minutes, has a forwardable share grid.

### Site signup form

Subscribe form lives on `tucsondailybrief.com` between the section nav and the daily-brief post list. Rendered by `render_index()` in `generate_post.py` (so it survives every nightly homepage rebuild) and styled in `style.css` under `.subscribe-cta` (tan panel, terracotta CTA button, brown text — matches the desert palette).

Form posts directly to Buttondown's embed endpoint:

```
POST https://buttondown.email/api/emails/embed-subscribe/tucsondailybrief
```

`target="_blank"` opens Buttondown's confirmation flow in a new tab so the user stays on tucsondailybrief.com. Buttondown handles double opt-in, the success page, and the welcome email.

For now the form is homepage-only. Adding to other index pages (`meeting-watch.html`, `news-reports.html`, `public-record.html`) and individual posts is straightforward but deferred until conversion data warrants it.

### Audio version (deferred)

Reuse the existing TTS pipeline (`generate_podcast.py` flow). Weekly episode is just a different input text — clean for TTS, send to ElevenLabs, upload to R2 or Buttondown's native podcast hosting. Add this once the written newsletter is stable.

### Build order (updated 2026-05-08)

1. Public Record liquor license pipeline ✅ live (2026-04-11)
2. Tucson Mini crossword ✅ live (2026-05-06, v0.4)
3. **TDB Weekly newsletter ✅ LIVE (2026-05-08)**
   - Draft generator ✅ built 2026-05-07 (v4 prompt)
   - Buttondown API integration ✅ built 2026-05-08
   - Wrapper ✅ built 2026-05-08; **de-cron'd 2026-07-04** — now a manual step of the Saturday ritual, gated on the locked crossword
   - Site signup form ✅ shipped 2026-05-08 (homepage, posts to Buttondown embed endpoint)
   - First real send: Sunday 2026-05-10 (manually scheduled in Buttondown)
4. Marana coverage in Public Record — pending
5. Audio version of newsletter — after written newsletter is stable
