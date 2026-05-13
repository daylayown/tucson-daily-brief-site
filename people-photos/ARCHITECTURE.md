# Official Portraits — Architecture Note

Status: **research only as of 2026-05-12.** Photos and metadata are being collected; no website code paths consume them yet. Tomorrow's decision: ship the integration or not.

## What was collected (2026-05-12 research pass)

**Coverage: 24 of 25 officials.** Only missing: Constance L. Hargrove (Pima County Elections Director) — no CC or `.gov`-hosted portrait exists; news-outlet photos do exist but all copyrighted. Recommended next step: email the elections department directly for an editorial-use portrait.

Two background agents searched Wikimedia Commons, official `.gov` staff pages, and Flickr CC, in that priority order. Photos saved to:

```
people-photos/
├── pima-county/<slug>.jpg     # Supervisors + senior admin + dept heads
├── tucson/<slug>.jpg           # Mayor + council + city manager
├── marana/<slug>.jpg           # Mayor + vice mayor + town manager
├── orovalley/<slug>.jpg        # Mayor + vice mayor + town manager
├── regional/<slug>.jpg         # Countywide elected (sheriff, attorney, recorder)
└── _manifest.json              # Per-image source/license/attribution metadata
```

Slug format: kebab-case canonical name (e.g., `andres-cano.jpg`, `gabriella-cazares-kelly.jpg`).

## Manifest schema

```json
{
  "/people-photos/pima-county/andres-cano.jpg": {
    "subject": "Andrés Cano",
    "source_url": "https://commons.wikimedia.org/wiki/File:...",
    "image_url": "https://upload.wikimedia.org/wikipedia/commons/...",
    "license": "CC BY-SA 4.0",
    "attribution_required": "Photo by X via Wikimedia Commons, CC BY-SA 4.0",
    "date_captured": "2026-05-12",
    "notes": ""
  }
}
```

Entries for officials with no findable photo have `"missing": true` and a one-line note about what was tried, so future passes don't redo dead-end searches.

## Proposed deploy architecture

### 1. Single source of truth: extend `local_names.json`

Add a `photo` object to each person entry in the bible:

```json
{
  "canonical": "Andrés Cano",
  "title": "Supervisor, District 5",
  "deepgram_misreads": ["Conner", "Connor", ...],
  "photo": {
    "src": "/assets/people/andres-cano.jpg",
    "srcset_2x": "/assets/people/andres-cano@2x.jpg",
    "alt": "Andrés Cano",
    "credit": "Photo: AZ State Senate, public domain"
  }
}
```

The current `_manifest.json` is a build-time artifact; at deploy time its data folds into the bible entries.

### 2. Build pipeline: resize + optimize once, commit the outputs

A new `pipeline/process_photos.py` script:
- Reads `people-photos/_manifest.json`
- For each photo: resize to 400px wide (`<slug>.jpg`) and 800px wide (`<slug>@2x.jpg`), optimize with `jpegoptim` / `cwebp`
- Writes to `assets/people/` (gets committed and served by GitHub Pages)
- Updates the `photo` field in `local_names.json`

Run once when photos are added or updated. Source `people-photos/` directory can be gitignored if storage is a concern, but small enough (~25 originals at ~500KB each = ~12MB) that committing is fine.

### 3. Render-time integration: minimal change to `ai_reporter.py`

In `render_post()` (or a post-process step), after the report markdown is generated:
- Scan for canonical-name matches against the bible's people entries
- At each name's **first occurrence in the body**, wrap the name in a `<figure>` block:
  ```html
  <figure class="report-portrait">
    <img src="/assets/people/andres-cano.jpg" srcset="/assets/people/andres-cano@2x.jpg 2x" alt="Andrés Cano">
    <figcaption>Andrés Cano<br><small>Supervisor, District 5</small></figcaption>
    <small class="photo-credit">Photo: AZ State Senate, public domain</small>
  </figure>
  ```
- Subsequent mentions: plain text, no photo flood
- Missing-photo people: skipped silently (text-only is the fallback)

### 4. CSS: warm-organic styling

In `style.css`:
```css
.report-portrait {
  float: right;
  width: 200px;
  margin: 0 0 1rem 1.5rem;
  border: 1px solid var(--dust);
  background: var(--bone);
}
.report-portrait img { width: 100%; display: block; }
.report-portrait figcaption {
  padding: .5rem .75rem;
  font: 14px/1.3 'Newsreader', serif;
  color: var(--brown);
}
.report-portrait .photo-credit {
  display: block;
  padding: 0 .75rem .5rem;
  font-size: 11px;
  color: var(--brown-light);
}
@media (max-width: 880px) {
  .report-portrait { float: none; width: 100%; margin: 1.5rem 0; }
}
```

## Editorial rules (load-bearing)

These need to be agreed before deploy:

1. **One photo per person, always the same.** No per-story selection. Choosing between a smiling portrait and a stern podium shot is implicit editorializing; we don't want to defend that call story by story.
2. **Photo appears at first mention, period.** Even if the story is critical of the subject (e.g., the Nanos perjury referral). Suppressing the photo for negative coverage would itself be a bias.
3. **Captions are strictly informational.** `<Name>, <Title>`. No description of role in the story, no editorial framing.
4. **Attribution is non-negotiable.** Every photo carries visible credit. CC-BY and CC-BY-SA both legally require attribution; .gov photos don't but we should still credit for transparency.
5. **No photo, no problem.** When someone doesn't have a photo, the report text reads the same as it does today. No placeholder ghost outline.

## Open questions for tomorrow

- **Coverage is strong (24/25).** Hargrove is the only gap and she rarely leads a story. Visual consistency across stories isn't a concern.
- **Two photos are tiny.** Melanie Barrett (Oro Valley Vice Mayor, 190×280) and Timothy Thomure (Tucson City Manager, 150×225) are usable as small avatars only. If the rendered portrait is ~200px wide they'll look soft. Worth a manual re-fetch when those `.gov` sites become reachable, or accepting the soft look in v1.
- **Selina Barajas (Tucson Ward 5)** — the only photo found is a UCLA Luskin alumni feature from Nov 2025: she's in a cowboy hat, outdoors. Identifiable but not a sterile headshot. Out of step with the rest of the council portraits. Decision: live with it, or skip her photo until a city-issued portrait exists.
- **Timothy Thomure (Tucson City Manager)** — the EXIF on his portrait names **Martha Lochert** as copyright holder with a "non-exclusive use granted to client" note. Crediting "Photo: Martha Lochert" is the safe move; alternatively drop and wait for a clearer-license replacement.
- **Regina Romero photo** is CC BY-SA 2.0 (from Wikimedia). Attribution required, and the SA clause means any derivative we publish stays under the same license. No infection of unrelated site content — only the image is governed.
- **Nanos photo** is the official PCSO portrait (250×300). Low res but canonical. We'll be using it in every Nanos story going forward, including the perjury referral one we just published. Acceptable per the "always the same photo, even when story is critical" editorial rule above — but worth your gut-check.
- **Provenance variance.** Some photos came from campaign sites (kevindahl4tucson.com, mirandaforward6.com) or alumni features rather than `.gov` sources. Editorially fine for portraiture — these are public figures and the photos are unambiguous likenesses — but flag if you want a stricter "city-issued only" standard.
- **Wayback fallback worked but is brittle.** All three city sites (tucsonaz.gov, maranaaz.gov, orovalleyaz.gov) hard-block bots via Akamai 403. The agent worked around it via `web.archive.org` snapshots, but Wayback often archives just the HTML wrapper without the JPEG bytes. Future re-fetches will hit this. If we want a maintenance pipeline that auto-refreshes portraits, we'd need direct contact with the city web teams.
- **Front-matter override.** Add a per-draft flag like `no_portraits: true` for edge cases? Skip in v1; flag if a real need emerges.

## Effort to deploy

- Image processing script (resize + optimize + manifest merge into bible): ~1.5 hr
- Renderer integration in `ai_reporter.py`: ~2-3 hr (first-mention detection is the only tricky part)
- CSS + visual review on real reports: ~1 hr
- Editorial rules doc on the public site: 30 min
- **Total: ~5-6 focused hours**

A natural sequence: ship one report with portraits to a private branch, see how it reads, iterate on CSS, then enable on the master pipeline.
