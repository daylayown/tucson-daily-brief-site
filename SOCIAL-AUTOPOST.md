# Facebook Strategy + Social Auto-Posting

Discussion + feasibility, **2026-06-26**. Two halves: (1) why Facebook is its own game for TDB's audience and how to post to it, and (2) what it takes to *automate* posting across all of TDB's social surfaces. Companion to the `project_social_promo_strategy` memory and `SHORT-FORM-VIDEO.md` (the auto-post layer described here IS that project's "thin publish layer"). Tooling lives in `social/` (`render_card.py`, `render_story.py`, etc.).

---

## Part 1 — Facebook vs. Instagram playbook

**Why FB matters most for TDB:** Southern Arizona skews **old** (Green Valley, SaddleBrooke, Oro Valley are retiree-dense), and older Americans live on Facebook. FB is likely TDB's **#1 organic channel for actual Tucsonans** — and almost nobody optimizes for it because it's not the "cool" platform.

**The catch — Meta buried the news feed.** Meta has spent years deprioritizing news/political/link content in the main feed. So you can't pipe links and expect reach. Winners are **native, engagement-driving** posts: image cards, questions, nostalgia, "did you know," photos. Lead with those; treat links as secondary.

**Three things FB does that IG can't:**
1. **Links work** (clickable, with previews) → real traffic to tucsondailybrief.com. But Meta throttles the reach of posts with a link in the body → use the **first-comment link trick** (post the image natively, drop the link as the first comment).
2. **Groups are the unlock** — Tucson has huge active groups (nostalgia "You know you grew up in Tucson if…", neighborhood, local-news). Distribution channel IG has no equivalent for. ⚠️ Etiquette: most ban overt self-promo and auto-posting gets you flagged — be a genuine member who shares **where it's truly on-topic**, build reputation, don't blast.
3. **Share culture + longer text** → nostalgia/community posts *travel* via shares (IG has no native re-share).

**Content mapping (same card, different captions):**

| Content | IG | Facebook |
|---|---|---|
| Nostalgia / local history (e.g. Old Tucson) | good | **peak FB** (shares + Groups) |
| Weather/safety alerts | Story | **great** (older audience shares to family) |
| "What's opening / closing" | good | **great** |
| Civic/government news | meh | **good** (older = more civically engaged) |
| Aesthetic carousels / Reels / Stories | **IG-leaning** | secondary |

Rule of thumb: **same card on both, write the caption twice** — IG tight + hashtags; FB longer + nostalgic + link-in-first-comment, no markdown asterisks (FB renders them literally).

**Worked example — FB-tailored Old Tucson post** (2026-06-26, the card was `social/cards/news-old-tucson-2026-06-26.png`):
> Well, here's one we didn't expect to see this week. 🤠
>
> Old Tucson — the historic Western movie set and theme park out west of the city — has been listed for sale, with an asking price of $1.5 million.
>
> If you grew up around here (or raised your kids here), there's a good chance Old Tucson is tied up in a memory or two: the staged gunfights on Main Street, the little train, a school field trip, maybe even a movie or show you know was filmed out there over the years.
>
> So we want to hear from you — what's your favorite Old Tucson memory? Tell us in the comments, we'll be reading. 👇

First comment: `🔗 Details via KVOA News 4: [link] — and we round up Tucson news like this every morning at tucsondailybrief.com 🌵`

**Cadence:** one well-chosen post a day (the most human/nostalgic/civic item), cross-posted from the IG card with an FB caption, plus genuine Group participation when something fits. Quality + Groups beats frequency.

---

## Part 2 — Auto-posting feasibility

**The dream (user, 2026-06-26):** "wake up and see all my socials populated with relevant content without doing anything." Verdict: **very possible, ~70% of the pieces already exist, and it's on-lane with the short-form-video project (not feature creep).** The posting is the easy part; the value/risk is in the editorial brain + Meta's app gates.

### What's auto-postable (own accounts, real APIs)

| Surface | Auto-post? | How |
|---|---|---|
| **Instagram** (feed + Stories) | ✅ | Content Publishing API: `POST /{ig-user-id}/media` (image_url from R2) → `POST /{ig-user-id}/media_publish`; Stories via `media_type=STORIES`. Needs a Meta app + `instagram_content_publish` (Standard Access). |
| **Facebook Page** | ✅ | Graph API `POST /{page-id}/photos` (url + caption). **First-comment link trick is also automatable:** `POST /{post-id}/comments`. Needs `pages_manage_posts`. |
| **Threads** | ✅ | Threads API (Meta shipped it 2024), own account. |
| **Bluesky** | ✅ trivially | AT Protocol + app password, `com.atproto.repo.createRecord` + blob upload. **Zero gatekeeper.** (No TDB account yet.) |
| **FB & IG _Groups_** | ❌ **No** | **Meta sunset the Groups API in 2024** — group posting via API is dead. Groups stay a **manual** move (which suits Group etiquette anyway). |
| **LinkedIn** | (separate) | Technically automatable, but **keep it its own track** — different voice, journalism-industry audience; user wants those wires uncrossed. |

### You already own ~70%
- `social/render_card.py` / `render_story.py` → the cards (format proven this session: Old Tucson, weather).
- **R2 bucket** → public image hosting (what IG/FB publishing require).
- `upload_to_youtube.py` → OAuth auto-publish precedent (same shape).
- `social/generate_short.py` → already **picks a story with Haiku and posts fully unattended** to YouTube → working zero-touch precedent.
- Telegram approve flow → already used for news reports + newsletter.

### Architecture to build
1. **Editorial brain** (`generate_social.py` or similar): Sonnet reads the morning brief → picks the day's best social story(ies) → emits card config + **per-platform captions** (IG/FB/Threads/Bluesky variants) → renders the card → uploads to R2. (Half-exists conceptually as the Short's Haiku story-picker.)
2. **Publish adapters** — one thin OAuth-per-platform module each (FB Page, IG, Threads, Bluesky).
3. **Approve gate** — Telegram message with card preview + captions + ✅/✏️/❌ → on ✅, fan out to all surfaces. (Reuse existing Telegram pattern.)
4. **Cron** — runs after the 6:10 brief; posts to Telegram for approval; user taps from bed.

### The one real decision: full-auto vs. one-tap — tiered, per the quality bar
TDB's strict no-fabrication bar ([[feedback_ai_content_quality_bar]]) was hit **twice on 2026-06-26 alone** (a "since we were kids" brand-backstory claim; the weather "broadcasters reported it" hedge). A wrong fact on a public card spreads faster than a buried blog line. So:
- **Fully unattended** for evergreen/safe content (what the daily Short already does).
- **5-second Telegram one-tap approve** for news/civic cards — delivers ~95% of the "mental unlock" (no writing, no story-picking, no rendering, no posting) while keeping a human eye between the AI and a permanent public post. **Recommended default for news.**

### Build order (each de-risks the next)
1. **Bluesky** — zero gate; proves the whole render→caption→publish→approve loop. (Make an account first.)
2. **Threads** — own account, straightforward.
3. **Facebook Page** — needs a Meta app; for your *own* page there's likely a no-review path via dev-mode/business assets — **verify live**.
4. **Instagram** — same Meta app, `instagram_content_publish`; the app-review queue is the **only real calendar-time variable** (the code is trivial).

**Gate per [[feedback_resist_feature_creep]]:** this is the publish layer of the short-form-video project (the user's chosen next big build) — build it *alongside* that, don't start mid-stream without a green light. The format is now arguably proven (multiple cards shipped this session), which was the original deferral condition.

---

*Captured 2026-06-26. Strategy + feasibility only — not building. Pairs with SHORT-FORM-VIDEO.md and the project_social_promo_strategy / project_social_autopost memories.*
