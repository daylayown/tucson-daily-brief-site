# TDB Social Media Setup & Strategy

Reference doc for standing up Tucson Daily Brief's social presence. Captured 2026-06-17.

## Strategy at a glance

Three channels, three different jobs — **don't cross the wires:**

| Channel | Job | Content |
|---|---|---|
| **Instagram** | Discovery | Faceless motion-typography video shorts **+** static image cards / carousels |
| **YouTube** | Discovery | Video shorts (same renders as IG Reels) |
| **LinkedIn** | Credibility (Nicholas's pro/journalism network) | **Written** build-in-public posts — NOT motion shorts |
| **Facebook** | Means-to-an-end | See below — mostly a substrate, not a real feed channel |
| **Threads** (future) | Text-first discovery | Automated "On this day in Tucson" corpus posts — *after* FB/IG core work |

**Hard preferences:**
- **No on-camera.** Faceless only.
- **As automated as possible**, BUT keep a one-tap review gate on anything shareable (a viral 30s clip that's wrong is worse than a buried blog paragraph). Automate *generation* 100%; keep a human approve before *posting* until the format is calibrated.

### What Facebook is actually for

It's **80% a means to an end, 20% a real channel.** Reasons to create it, in priority order:
1. **Required substrate for Instagram auto-publishing.** The IG Business account must be linked to a FB Page for the Graph API to publish. No Page → no IG automation.
2. **Legitimacy / search anchor.** People expect a local outlet to have a FB presence; its absence reads as "not real."
3. **A handle for sharing into local Facebook Groups** — where Tucson news actually circulates.

What it is **not:** a meaningful traffic source via the Page feed (Meta gutted organic Page reach and throttles news *links*). So: create it, make it look legit, **don't pour manual effort into it.** Content-automation energy goes to IG + YouTube.

## Meta account model (the thing that confuses everyone)

Meta separates the **human** from the **brand**. You never make a second personal account.

- **Personal Facebook profile** = one real human, the administrative root. Stays backstage; followers never see it.
- **Facebook Page** = TDB's public presence. Not a separate login — your personal account *administers* it.
- **Instagram account** = its own login. Created fresh for TDB, switched to **Business** mode.
- **"Meta account"** = just Meta's universal *login keyring* that can hold one or more profiles. Not a new network. For TDB, prefer its **own keyring (own email)** for clean separation.
- **Meta Business Portfolio** (Business Suite) = optional umbrella holding the Page + IG + later the developer app.

The link that matters for automation (**IG Business ↔ FB Page**) is independent of the keyring choice, so you can't break the API path by picking the Meta-account option "wrong."

## Brand assets (already generated)

Generated from the real site palette/fonts (HTML template → headless Chromium → PNG). Stored in `~/`:

| File | Size | Use |
|---|---|---|
| `~/tdb-fb-profile.png` | 1080×1080 | FB **and** IG profile picture (terracotta, sun motif, "TDB" + name; survives circle crop) |
| `~/tdb-fb-cover.png` | 3280×1248 | FB cover banner (text in top half so the profile circle doesn't collide) |
| `~/ask-tool-linkedin.png` | 2560×2880 | LinkedIn launch image for the Ask/RAG tool |

> Regeneration tooling: `chromium --headless=new --screenshot` against a small HTML file using the locked palette (sand `#f5f0e6`, terracotta `#c75b39`, brown `#3d3029`) + Fraunces/Newsreader from Google Fonts + the site sun SVG. Same approach will drive the automated image-card generator.

## Facebook Page — creation steps

> Meta moves these buttons around; labels may differ, the flow is stable.

1. **Log into the existing personal FB account** (secure it first: 2FA + current email/phone — a dormant account suddenly creating a Page + dev app can trip security review).
2. Go to **facebook.com/pages/create** (or **+ → Page**).
3. **Name:** `Tucson Daily Brief`. **Category:** "News & Media Website" (or "Media/News Company"). **Bio:** *"AI-assisted local journalism for Tucson & Pima County. A daily brief from the Old Pueblo."*
4. **Create.**
5. **Profile picture** → upload `~/tdb-fb-profile.png`. **Cover photo** → upload `~/tdb-fb-cover.png`.
6. **Edit details:** website `https://tucsondailybrief.com`, email, location *Tucson, AZ*, longer About blurb.
7. **Username/handle:** grab `@tucsondailybrief` → `facebook.com/tucsondailybrief`.
8. Don't worry about posting content yet — the Page's job is to exist and be ready to link to IG.

## Instagram account — creation steps (iOS app)

**Prereqs:** TDB FB Page exists ✅ · a dedicated TDB email you can receive mail at (`tdb@tucsondailybrief.com` routes to your inbox via Cloudflare).

1. **Fresh signup:** if a personal IG is logged in → Profile → ☰ → **Settings → Add account → Create new account**. If no IG at all → open app → **Create new account**.
2. **Sign up with email — NOT "Continue with Facebook"** (that would chain the login to your personal profile). Use `tdb@tucsondailybrief.com`.
3. **Username:** `tucsondailybrief` if free. Strong unique password, saved.
4. **Verify** the email code. **Decline** contact sync.
5. **At the Meta account / Accounts Center prompt → keep it separate** (its own Meta account). Adding it to your personal Accounts Center is survivable but less clean.
6. **Profile:** upload `~/tdb-fb-profile.png`, name **Tucson Daily Brief**, bio + `tucsondailybrief.com`.
7. **Switch to Business:** Settings → **For professionals / Account type and tools** → **Switch to professional account** → category "News & Media Company" → choose **Business** (not Creator).
8. **Link to the FB Page:** during pro setup, **Connect to Facebook** → log into the FB account that admins the TDB Page → select the **Tucson Daily Brief** Page. (Later path: Settings → Business tools → linked Page.) **This link unlocks the IG publishing API.**

## Warm-up rule (both platforms)

Don't create an account and immediately hammer it with automation — new accounts that convert to business + link + API-post on day one trip spam/verification holds. **Post the profile pic + a couple of intro posts by hand, let it age a few days, then wire up publishing.**

## Build order (content pipeline)

1. **Stand up accounts** (FB Page ✅ done · IG Business — in progress).
2. **Image-card generator** — generalize the proven HTML→Chromium→PNG trick into branded templates (Spotted filing card, "what to watch this week" agenda card, quote/stat card). Outputs PNGs to a folder; post from phone. *Lowest lift, lowest risk — start here.*
3. **Motion-typography video shorts** — reuses ~80% of the podcast pipeline (script → TTS → Deepgram word timestamps → ASS captions → ffmpeg 1080×1920). Post to YT Shorts + IG Reels.
4. **Auto-publishing** — YouTube Shorts first (existing OAuth/Data API), then Meta app review for `instagram_content_publish`.
5. **Threads** (later) — text-first, reuses the IG identity; "On this day in Tucson" automated corpus posts. Bias to recent items; frame older ones explicitly so stale stories aren't posted as news.

See `CLAUDE.md` → "Roadmap: Short-Form Video" and the `project_social_promo_strategy` memory for the durable version.
