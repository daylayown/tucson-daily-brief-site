# Tucson Daily Brief — Visual Redesign Plan (v2)

**Date:** 2026-05-11
**Scope:** Visual language. The information architecture shipped in commit `b927b4a` (Direction B — zoned homepage) stays. We are *not* relitigating IA; we are dressing the rooms.
**Direction:** Warm organic / Southwest. Editorial publication that grew up in the Sonoran Desert.

---

## 1. Aesthetic POV

TDB looks like an editorial magazine published from a thick-walled adobe building in Barrio Viejo — warm, slow, place-aware. The dominant atmospheric move is **Sonoran late-afternoon light**: a soft diagonal gradient that lives behind the content and slowly drifts as you scroll, making every page feel like 6 PM in Tucson. Pair that with a confident editorial serif (set with subtle imperfection, so letters feel hand-set), deep terracotta blocks used like Barragán color planes, hand-drawn SVG underlines that animate into view, and paper-grain texture across the whole surface. Restrained, never busy. The site reads like a publication, but the publication clearly grew up in this specific desert.

The current site says "this is a personal blog with extras." The new site says **"this is a place."**

---

## 2. Typography system

Two web fonts, both free on Google Fonts, both variable. Total weight: ~85KB woff2 subsetted.

### Display: Fraunces

`https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT,WONK@9..144,300..900,0..100,0..1`

- High-contrast warm serif designed by Undercase Type
- Variable axes used: `opsz` (optical size), `wght` (weight), `SOFT` (softness), **`WONK` (wonkiness — 1 gives idiosyncratic letterforms like a tail-down `g`, slanted `e`)**
- At display sizes (32px+), use `font-variation-settings: "opsz" 96, "SOFT" 60, "WONK" 1`. This is the one critical move — Fraunces with WONK on looks hand-set; Fraunces with WONK off looks like every other display serif.
- Weights used: 700 (display), 600 (subheads)

### Body & UI: Newsreader

`https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,200..800;1,6..72,200..800`

- Designed for long-form reading by Production Type
- Has true italic. Generous x-height. Optical sizes mean it reads warmly at body size and confidently at lede size.
- Weights used: 400 (body), 500 (emphasis), 600 (small labels in caps)

### Type scale (1.250 — major third, slightly tighter than golden ratio)

| Role | Size (rem) | Px @ 16px | Family | Weight | Tracking |
|---|---|---|---|---|---|
| Display 1 — featured headline | 3.815 | 61 | Fraunces | 700 + WONK | -0.02em |
| Display 2 — section heads | 2.441 | 39 | Fraunces | 700 | -0.015em |
| Display 3 — card titles | 1.563 | 25 | Fraunces | 600 | -0.01em |
| Lede | 1.25 | 20 | Newsreader | 400 italic | -0.005em |
| Body | 1.063 | 17 | Newsreader | 400 | 0 |
| Small | 0.875 | 14 | Newsreader | 400 | 0 |
| Eyebrow / kicker | 0.75 | 12 | Newsreader | 600 | 0.12em uppercase |

Line-heights: display 1.05; body 1.55; eyebrows 1.1.

---

## 3. Color system

Four locked, extended to nine.

```css
:root {
  /* Locked (must remain core) */
  --sand: #f5f0e6;          /* paper bg */
  --tan: #e8dfd1;           /* surface, panels */
  --terracotta: #c75b39;    /* primary accent */
  --terracotta-dark: #a84a2e; /* hover/active */
  --sage: #7a8b6f;          /* muted accent, dates */
  --brown: #3d3029;         /* ink */
  --brown-light: #5c4a3f;   /* secondary ink */

  /* Extensions (warm-only — no blues/teals/purples) */
  --bone: #faf4e8;          /* paper highlight, surfaces above sand */
  --adobe: #d97048;         /* brighter terracotta for CTA hover */
  --clay: #8c3a1f;          /* deeper rust for emphasis blocks, tool eyebrows */
  --dusk: #4a382c;          /* slightly cooler brown for high-contrast type */
  --shadow: #251c17;        /* deepest brown, only for true contrast moments */
  --dust: #c7b9a4;          /* warm hairline / rule color */

  /* Semantic roles */
  --bg: var(--sand);
  --bg-elevated: var(--bone);
  --bg-emphasis: var(--terracotta);
  --bg-tool: var(--clay);
  --ink: var(--brown);
  --ink-muted: var(--brown-light);
  --ink-quiet: var(--sage);
  --accent: var(--terracotta);
  --accent-hover: var(--adobe);
  --rule: var(--dust);
}
```

**Usage rules:**
- `--terracotta` is the primary accent, used sparingly (links, the lede color-block, hand-drawn underlines)
- `--clay` is reserved for **tools** (Ask, Responsiveness) — they get a deeper, more present treatment so they don't read as "another stream item"
- `--sage` stays as the date/eyebrow color where streams need to recede
- Color blocks (Barragán moves) only appear at high-importance moments: the featured Today's Brief, the tools row, and the subscribe panel. Don't sprinkle them.

---

## 4. Spatial / layout system

Break the single column. Use three container widths intentionally.

### Containers

| Name | Max width | Used for |
|---|---|---|
| `.reading` | 640px | Body prose, lists of articles, the subscribe panel |
| `.editorial` | 1040px | Cross-stream cards (3-up grid), tools row, recent briefings |
| `.full` | 1280px | The masthead, the featured Today's Brief, section dividers, footer |

Mobile (<768px): everything collapses to a single 100% column with 20px side padding.

### Grid

CSS grid for the cross-stream cards: `grid-template-columns: 1.4fr 1fr 1fr` at desktop — the meeting-watch card gets visual priority, news-reports and public-record balance it. **Deliberate asymmetry**, not three equal cards.

For the tools row: a single emphatic 2-up grid with both cards getting large display type. Tools are not stream items — they get their own visual hierarchy.

### Vertical rhythm

Base unit 8px. Section spacing in multiples of 24px:
- Within a card: 8/16/24px
- Between elements in a section: 24/40/64px
- Between major sections: 96px desktop, 64px mobile

### Masthead is large

The wordmark gets ~88px at desktop. This is a publication; it should *announce* itself. Currently the wordmark is 28px — about a quarter of what it should be.

---

## 5. Visual depth treatments

Five layered atmospheric moves, applied in this order from back to front:

### 5a. The Sun-Cast (signature move)

A diagonal warm gradient covering the entire viewport, fixed, slowly animating its position.

```css
body::before {
  content: "";
  position: fixed;
  inset: 0;
  background:
    radial-gradient(
      ellipse 1400px 900px at 12% 8%,
      rgba(217, 112, 72, 0.18) 0%,
      rgba(217, 112, 72, 0.10) 25%,
      rgba(122, 139, 111, 0.06) 60%,
      transparent 85%
    );
  background-size: 140% 140%;
  background-position: 0% 0%;
  animation: sun-drift 180s ease-in-out infinite alternate;
  pointer-events: none;
  z-index: 0;
}

@keyframes sun-drift {
  0%   { background-position: 0% 0%; }
  100% { background-position: 30% 20%; }
}
```

This is the one thing readers remember. Subtle, never distracting, but felt.

### 5b. Paper grain

Fine noise via inline SVG, fixed, low opacity. Gives the entire site a tooth.

```css
body::after {
  content: "";
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.6  0 0 0 0 0.4  0 0 0 0 0.2  0 0 0 0.12 0'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
  opacity: 0.6;
  mix-blend-mode: multiply;
  pointer-events: none;
  z-index: 1;
}
```

Body content sits at `z-index: 2`.

### 5c. Adobe color blocks (Barragán)

The featured Today's Brief sits half-on a confident terracotta block. The tools section gets a clay block. No borders, no gradients on the blocks themselves — just flat saturated color. The contrast between the block and the cream paper is the move.

### 5d. Hand-drawn underlines

Under section heads ("Latest from across TDB", "Tools", "Recent briefings"), inline SVG paths drawn with a slight wobble, animated to draw themselves on first viewport entry.

```svg
<svg width="280" height="14" viewBox="0 0 280 14" fill="none" aria-hidden="true">
  <path d="M2 8 C 30 4, 80 12, 130 7 S 230 4, 278 9" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" fill="none" pathLength="100" style="stroke-dasharray: 100; stroke-dashoffset: 100;" class="hand-rule"/>
</svg>
```

JS toggles `.in-view` which removes the dashoffset over 800ms with `cubic-bezier(0.25, 0.46, 0.45, 0.94)`.

### 5e. Dingbat — the sunray

A small SVG glyph used as section markers and to separate eyebrow text from the date. Stylized desert sun, 12px square, color picks up parent.

```svg
<svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
  <circle cx="7" cy="7" r="2.2" fill="currentColor"/>
  <g stroke="currentColor" stroke-width="1.2" stroke-linecap="round">
    <line x1="7" y1="0.5" x2="7" y2="2.5"/>
    <line x1="7" y1="11.5" x2="7" y2="13.5"/>
    <line x1="0.5" y1="7" x2="2.5" y2="7"/>
    <line x1="11.5" y1="7" x2="13.5" y2="7"/>
    <line x1="2.4" y1="2.4" x2="3.6" y2="3.6"/>
    <line x1="10.4" y1="10.4" x2="11.6" y2="11.6"/>
    <line x1="2.4" y1="11.6" x2="3.6" y2="10.4"/>
    <line x1="10.4" y1="3.6" x2="11.6" y2="2.4"/>
  </g>
</svg>
```

Used: as the favicon, as the bullet between section name and date in card eyebrows, as the dingbat between recent-briefing items.

---

## 6. Motion

Restrained. Three moments.

### 6a. Page load — masthead cascade

When the page first paints, the masthead reveals in three quick stages:
1. Kicker (`A Tucson publication`) fades up — 0ms
2. Wordmark fades up — 80ms
3. Tagline fades up — 160ms

Total: ~400ms. Quiet enough not to feel like a splash; present enough to feel intentional.

```css
@keyframes fade-up {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.masthead .kicker     { animation: fade-up 0.6s ease-out 0.00s both; }
.masthead .wordmark   { animation: fade-up 0.6s ease-out 0.08s both; }
.masthead .tagline    { animation: fade-up 0.6s ease-out 0.16s both; }
```

### 6b. Scroll-triggered hand-drawn underlines

Section heads carry an SVG underline that draws itself on first viewport entry. ~800ms, cubic-bezier ease. Vanilla IntersectionObserver toggles a class — no library.

### 6c. Card hover

Cross-stream cards lift 2px and shift their shadow when hovered. Sub-pixel — should feel "responsive," not "wow." 180ms transition.

```css
.card { transition: transform 180ms ease, box-shadow 180ms ease; }
.card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px -10px rgba(60, 40, 30, 0.18); }
```

### 6d. Sun-cast drift

The background gradient slowly travels (180s loop, alternates back). Never explicitly noticeable; cumulatively makes every reload feel "slightly different." `prefers-reduced-motion: reduce` disables all motion globally.

---

## 7. The one memorable element

**The sun-cast.** A subtle, animated diagonal warmth that lives behind every page and drifts as you read. Combined with hand-drawn underlines that draw themselves into view, those two together make the site feel alive without being flashy. Readers will describe TDB as "that Tucson site with the warm light moving across it." Nobody else in local news has that.

Backup memorable thing if the sun-cast feels too subtle in user testing: **drop caps on featured ledes** — large Fraunces capitals (with WONK on) pulled into the paragraph in the same way Harper's does. That alone instantly signals "publication," not "blog."

We're using both. Sun-cast is atmospheric; drop caps are the editorial signature.

---

## 8. Per-surface treatment

Each surface gets a treatment that signals its content shape *before* you read.

### Stream surfaces (Briefings / Meeting Watch / News Reports / Public Record)

The familiar editorial reading experience.
- Background: `--sand` with sun-cast and paper grain
- Card eyebrows: small caps Newsreader, `--terracotta`, sunray dingbat between section and date
- Card titles: Fraunces 600
- Hand-drawn underline under each section head
- Layout: 1.4fr-1fr-1fr asymmetric grid for the homepage cross-stream cards; single 640px column for individual posts

### Living/data surfaces (Tucson Responsiveness Index)

A *structurally different* page that signals "this is a tool, not an article."
- Background still `--sand` (continuity), but the data zone sits on `--bone` panels
- Eyebrows in `--clay` (deeper red), no dates (it's a living surface — date stamps would lie)
- Large display numerals (Fraunces 700, optical size 144, 56-80px) for key statistics — these become the dominant visual
- Sparkline mini-charts in `--sage` against the bone surface
- Methodology section (smaller, restrained, 640px column) follows the dashboard
- Hairline grid using `--dust` to organize data blocks

### Interactive tools (Ask)

Visually the most open surface.
- Larger negative space; the input affordance is the protagonist
- Input shaped like a real card — adobe color block under it, drop shadow
- Tone: invitation, not interface. "Ask Tucson anything." in Fraunces display.
- Recent questions (when the agent is live) shown as small chips below — `--tan` surface, Newsreader
- Eyebrows: `--clay`, matching Responsiveness — both tools share a color family so readers learn "clay = tool"

### Subscriber perks (Tucson Mini)

Kept distinct from the rest of the site. The crossword play page (when subscribed) gets:
- Hand-drawn frame around the grid (SVG, slightly imperfect)
- Numbers in Fraunces small caps
- Across/Down clue panels in Newsreader italic
- This is already partially in place; the redesign refines the type pairing and adds the frame

### Subscribe panel

Currently a tan rectangle with form. In the redesign:
- A wider container with **two columns at desktop**: left = warm illustrative element (cactus silhouette OR an abstract sun/shadow shape), right = the form and copy
- Mobile: stacks, illustration on top
- Surface: `--bone` against the `--sand` page — slight elevation, hairline border in `--dust`
- The button is `--clay` (matching tools — subscribing is the highest-conversion CTA, deserves its own visual register)

---

## 9. Per-page changes summary

| Page | Biggest visual shift |
|---|---|
| `index.html` (homepage) | Hero featured card with adobe block + drop cap; asymmetric 1.4-1-1 cross-stream grid; tools row in clay; subscribe panel rebuilt 2-col |
| `briefings.html` | Reading-column layout with handsome card list; hand-drawn underline under "Daily briefings" head |
| `meeting-watch.html` / `news-reports.html` / `public-record.html` | Same shape as briefings but each gets a section-specific kicker color (terracotta / terracotta / clay-light) |
| `posts/*.html` | Drop cap on first paragraph (Fraunces, ~64px, pulled-in float); hand-drawn underline under section H2s; warm body type |
| `meeting-watch/*.html` | Editorial layout: lede block emphasized, "Why it matters" blockquotes get a Barragán-style left border block in clay |
| `news-reports/*.html` | Stronger lede paragraph treatment; bylines and meta in caps |
| `public-record/*.html` | Filing facts get a card-within-card treatment using `--bone` and hairlines |
| `ask.html` | Complete rebuild — input as hero, palette + drop shadow centered |
| `responsiveness.html` | Complete rebuild — dashboard-shaped, big numbers, sparklines |
| `crossword/play.html` | Frame, type, otherwise unchanged (existing engine stays) |

---

## 10. Implementation roadmap

The plan ships in three passes so the site is never broken.

### Pass 1: Foundation (~4 hours)

1. Add Google Fonts `<link>` for Fraunces + Newsreader to the shared `ANALYTICS_HTML` block (rename → `HEAD_TAGS`) in `generate_post.py`
2. Replace the entire body of `style.css` with new tokens, sun-cast, paper grain, type system, base elements
3. Verify every existing page still loads and is readable (the new CSS is a full replacement; layout will reflow)

### Pass 2: Homepage and section indexes (~6 hours)

1. Rewrite `render_homepage()` to emit the new zoned markup with the hero featured card, asymmetric grid, tools row, subscribe panel rebuild, recent list
2. Update the three section-index renderers (`agenda_mining.py`, `ai_reporter.py`, `public_record_liquor.py`) to use the new card markup
3. Add the dingbat SVG and hand-drawn-underline SVG as Python string constants in `generate_post.py`
4. Add the vanilla JS for scroll-trigger underlines as a small `<script>` block

### Pass 3: Individual posts + new stubs (~4 hours)

1. Add drop-cap CSS class; apply to first-paragraph in `render_post()`
2. Rebuild `ask.html` from scratch (input-as-hero)
3. Rebuild `responsiveness.html` from scratch (dashboard layout, placeholder data with realistic numbers)
4. Update `meeting-watch/`, `news-reports/`, `public-record/` individual-post renderers with new editorial treatments
5. Mobile QA pass: 375px, 414px, 768px breakpoints

### Pass 4 (optional, later): Subscribe panel illustration

Commission or build a hand-drawn SVG illustration for the subscribe panel. Defer to a separate pass — the redesign ships with a typographic-only subscribe panel that still feels right; illustration is upside.

**Total focused work:** ~14 hours over 2–3 sessions. Each pass is independently shippable.

---

## 11. Anti-patterns we're avoiding

- Generic Inter / system fonts (TDB used these before — that was the problem)
- Purple gradients on white (the SaaS default)
- Three-equal-cards grid (predictable; we use asymmetric 1.4-1-1)
- Centered hero with stock photo (we use editorial color blocks instead)
- "Modern" cookie-cutter card components with rounded corners and pastel backgrounds (we use Barragán-style blocks)
- Motion for motion's sake (we have three motion moments, each with a specific job)
- Cosplaying as something we're not (we're not pretending to be Apache or O'odham — we're using a Sonoran modernist palette that *happens* to share warmth with indigenous Southwest design vocabulary, executed with restraint)

---

## 12. What this redesign does *not* do

- Doesn't add hero photography or photo-led articles (out of scope; needs editorial photo workflow)
- Doesn't introduce a CMS or build step (TDB stays pure-static + Python)
- Doesn't restructure URLs (everything stays where it is — `briefings.html`, `meeting-watch.html`, etc.)
- Doesn't change the IA — Direction B (REDESIGN.md) is the structure; this redesign is the visual language inside that structure

---

## 13. Demo

`redesign-preview.html` at the repo root is a self-contained proof. Open it directly in a browser (`file://` works). It demonstrates the homepage with real current content. The CSS is embedded so the demo doesn't disturb the live `style.css`. The vanilla JS for scroll-trigger underlines is in the same file. Mobile-responsive.

Once approved, implementation follows the three passes above. Final code will live in `style.css` and the Python renderers — not in this demo file.


---

# As-shipped summary (moved from CLAUDE.md 2026-07-17)

The condensed token list now lives in CLAUDE.md; this is the fuller description of the signature moves, including the 2026-05-13 tuning decisions.

## Design

The current visual language is **warm-organic Southwest editorial**, shipped 2026-05-11. The original Daring Fireball-inspired restraint (system fonts, single 600px column, no decoration) is gone. See `REDESIGN-V2.md` for the full plan and `REDESIGN.md` for the IA-only step that preceded it. `redesign-preview.html` at the repo root is a self-contained single-file reference of the visual language.

**Tokens (in `style.css :root`):**
- Locked palette: sand `#f5f0e6`, tan `#e8dfd1`, terracotta `#c75b39` / dark `#a84a2e`, sage `#7a8b6f`, brown `#3d3029` / light `#5c4a3f`
- Extensions (warm-only): bone `#faf4e8`, adobe `#d97048`, clay `#8c3a1f`, dusk `#4a382c`, shadow `#251c17`, dust (hairlines) `#c7b9a4`
- Type: Fraunces (display, with `WONK` axis on for hand-set feel) + Newsreader (body), both variable, both Google Fonts
- Three container widths: reading 640px, editorial 1040px, full 1280px
- Mobile breakpoint: `max-width: 880px` (single-column collapse, site-wide)
- Vertical rhythm: 8px base, sections in multiples of 24px

**Atmospheric signature moves (none of these are required to understand the layout, but they're the brand):**
- **Sun-cast** — fixed warm radial gradient on `body::before`, slowly drifts via 180s alternating animation
- **Paper-grain** — SVG turbulence noise overlay on `body::after`, multiply blend, every page
- **Paper-grain bleed** — denser local noise on `.featured::before`, masked to fade out on the right, concentrating "ink" under the headline
- **Featured sun motif** (`FEATURED_SUN_SVG`) — desert sun with 12 rays of varied length in the upper-right of the homepage feature; echoes the small sunray dingbat used in kickers. Desktop only (hidden under the 880px breakpoint). Sized down 2026-05-13 (max width 240→180px, top -28px) so the bottom of the sun clears the right-column aside even when the daily-brief headline is short (3 lines)
- **Hand-drawn SVG underlines** (`HAND_RULE_SVG`) under section heads on daily-brief posts only — animated draw on first viewport entry via IntersectionObserver. Removed 2026-05-13 from the four section index heads (Daily briefings, Meeting Watch, News Reports, Spotted) where they read as awkward decoration on the big titles
- **Drop caps** on the lede of daily-brief posts (large Fraunces capital, pulled into the column)

**Section nav, footer, masthead** are centralized in `generate_post.py` constants. The masthead kicker reads "From the Old Pueblo" — ties to the "The Old Pueblo Speaks" outreach section under the Roadmap. The masthead tagline reads **"The Tucson news you'd otherwise miss, by Nicholas De Leon."** — changed 2026-07-11 from the old AI-experiment line per the two-brand split (see Marketing & Distribution Strategy); it's baked into every published page, so changing it again means editing `generate_post.py` AND string-replacing across all published HTML (use Python, not sed — `&` entities in replacement text break sed). Footer links (in order): About (`about.html`), Apple Podcasts, YouTube, LinkedIn, Email. X and Bluesky were removed 2026-05-15 — user prefers personal social media (besides LinkedIn) not be connected to the site.

**Feature flag: `SHOW_TOOLS`** in `generate_post.py`. Currently `False`. **Note (2026-06-23): `Ask` has been promoted into the main streams nav (`_STREAMS`) and is now linked site-wide UNCONDITIONALLY — it is no longer gated.** `SHOW_TOOLS` now only gates (a) the secondary Tools nav row, which contains just **Responsiveness**, and (b) the homepage Tools *card* row (where Ask still shows a "Coming soon" card). So the live nav is: Briefings · Meeting Watch · News Reports · Spotted · In Depth · Ask. Flip `SHOW_TOOLS=True` once the Responsiveness dashboard ships.

**Public Record → "Spotted" display rename.** The section's user-facing name is **Spotted** (in the nav, page titles, eyebrows, post-meta). The URL stayed `public-record.html` and the directory stayed `public-record/` so existing links and bookmarks don't break. Internal references in code (file names, Python module names, CSS class `public-record-filing`, etc.) all keep the original `public-record` terminology — only display text changed.

**Analytics:** Google Analytics (GA4) via `gtag.js`, measurement ID `G-MEYSB9GYF2`. Loaded site-wide via `ANALYTICS_HTML` in `generate_post.py`.
