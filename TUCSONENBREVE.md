# Tucson en Breve — Spanish-Language Fork (planning)

Captured 2026-06-24. **Status: planning only — not building yet.** A parallel Spanish-language version of TDB at **tucsonenbreve.com**, mirroring TDB's content via LLM auto-translation. Developed alongside TDB as a fork, not a rebuild. This supersedes the earlier "Spanish = social-only" framing (see "Roadmap: Spanish-Language TDB" in CLAUDE.md): the end-state is a **full sister site**, with Spanish short-form video as one early component, not the whole thing.

## Why

- Large, under-served Spanish-speaking population in the Tucson metro; **no outlet does Spanish-language *civic* coverage** (meetings, agendas, public record) here.
- The marginal cost is tiny: TDB already produces all the canonical content; translation is one cheap LLM step per artifact, and the renderers/CSS are reusable.
- Audience data (from `SHORT-FORM-VIDEO.md` research): Hispanic adults over-index on IG/TikTok/YouTube and **WhatsApp** — strong distribution surfaces for a Spanish product.
- It's civic mission + differentiation + portfolio value, all at once.

## Name & brand

- **Tucson en Breve** ("Tucson in Brief") — clean, instantly legible, parallels "Tucson Daily Brief."
- Domain **tucsonenbreve.com**; social handles **@tucsonenbreve** (IG / YouTube / Threads / TikTok / Bluesky).
- **Same visual identity** as TDB — identical desert-palette CSS, Fraunces+Newsreader, sun motif. Only the language (and UI strings) change. One brand family, two languages.

## Core architecture (recommended)

**Translate at the canonical-markdown/source level, then run language-parameterized renderers.** The English pipeline stays the source of truth; a translation layer converts each canonical artifact to Spanish; the *same* generator code (parameterized by language) builds the Spanish site.

1. **Translation layer** — after each EN artifact is produced (daily brief `.md`, news-report `.md`, meeting preview `.md`, Spotted filing data, In Depth feature), an LLM step (**Sonnet**, transcreate not literal) emits the Spanish `.md`, preserving: markdown structure, source-citation links, and proper nouns (names/places do NOT translate — reuse `pipeline/local_names.json`). Output to a parallel content tree.
2. **Language-aware generators** — parameterize `generate_post.py` + the section renderers with a `LANG`: a small i18n strings table for chrome (nav labels, "Read today's brief" → "Leer el resumen de hoy", section names, footer, date formatting in Spanish via `locale`/manual month names, drop-cap logic unchanged). The atmospheric CSS is identical.
3. **Separate deploy** — **DECIDED 2026-06-24: a dedicated domain, `tucsonenbreve.com`** (user is buying it), served from its **own GitHub Pages repo** (`tucson-en-breve-site`) with that domain in its `CNAME`. Setup: register the domain → new repo → Pages on → `CNAME` file = `tucsonenbreve.com` → DNS apex A records to GitHub Pages IPs (185.199.108–111.153) + a `www` CNAME → free Let's Encrypt SSL. Cross-link EN↔ES with `hreflang` tags. **Why the domain over a free subdir/subdomain:** the brand IS the point for an under-served Spanish audience (more trusted/shareable/memorable than `tucsondailybrief.com/en-breve`); ~$12/yr is negligible; the usual SEO-from-zero knock is weak for hyperlocal Spanish civic news (growth comes via social + WhatsApp + a prominent link from the EN site, not Google rankings); and a separate domain gives clean, separate analytics on the Spanish audience. The translation pipeline is URL-agnostic, so this was a deploy/DNS choice, not an architecture constraint.
4. **Civic-terminology glossary** — a companion to the names bible: a curated EN→ES map for civic terms so translations stay consistent and correct (e.g., Board of Supervisors → Junta de Supervisores; City Council → Concejo Municipal; license-plate readers → lectores de matrículas; liquor license → licencia de licores; agenda → orden del día; levy → gravamen). Inject into the translation prompt.

## Scope — what to fork

**Fork (in rough priority):**
1. **Daily Brief** (`/`, posts) — the core; translate each day's brief.
2. **News Reports** — translate each approved report (content already human-reviewed in EN; ES translation gets a lighter Spanish spot-check — user speaks Spanish).
3. **Meeting Watch** (agenda previews) and **Spotted** (filings) — translate.
4. **In Depth** features — translate.
5. **Podcast** — Spanish audio: translate script → Spanish TTS (ElevenLabs/Voxtral Spanish voice) → separate RSS feed / R2 path → Spanish podcast.
6. **Short-form video** — Spanish cuts (the bilingual-Shorts idea): transcreate beats → render same template → publish to @tucsonenbreve socials. *Likely the first visible deliverable* since the short-form pipeline already exists.
7. **Newsletter** — Spanish "Tucson en Breve" weekly via a separate Buttondown list.

**Defer / maybe-never (v1 skips these):**
- **Ask / RAG** — corpus is English; a bilingual Ask (accept Spanish Q, retrieve over EN chunks, answer in Spanish) is doable later but not v1.
- **The Tucson Mini crossword** — needs a Spanish wordbank + clue generation; separate effort, skip initially.
- **Responsiveness Index** — skip; it's English-data-dashboard work.

## Translation quality

- **Transcreate, don't literal-translate** — natural Sonoran/Mexican-Spanish register for a Tucson audience, not stiff MT.
- **Names/places never translate** — reuse `pipeline/local_names.json`; inject the civic glossary.
- **Preserve source links + structure**; keep AP-equivalent number/date conventions in Spanish.
- **Review model mirrors EN:** the daily brief can auto-translate + auto-publish (like the EN auto-pipeline); human-reviewed EN content (news reports) → translation auto-runs but gets a Spanish spot-check before publish, at least until calibrated. Per [[feedback_ai_content_quality_bar]].

## Build phases

- **Phase 0:** register tucsonenbreve.com; decide repo structure (separate repo recommended); stand up the language-aware renderer + i18n strings + civic glossary.
- **Phase 1:** daily brief → Spanish brief page; deploy tucsonenbreve.com with daily briefs auto-translating off the EN pipeline.
- **Phase 2:** extend translation to News Reports, Meeting Watch, Spotted, In Depth.
- **Phase 3:** Spanish short-form (@tucsonenbreve socials) + Spanish podcast.
- **Phase 4:** Spanish newsletter; consider WhatsApp broadcast as a distribution channel (over-indexes with the audience).
- **Later:** bilingual Ask, Spanish crossword.

## Open decisions (resolve before building)

1. ✅ **DECIDED (2026-06-24): dedicated domain `tucsonenbreve.com` + its own GitHub Pages repo** (`tucson-en-breve-site`). See Core architecture #3 for setup + rationale. (Subdirectory-first was the cheap-validation alternative; rejected — the standalone Spanish brand is worth the $12/yr.)
2. **Auto-publish vs. review for the ES daily brief** — likely auto (mirrors EN); confirm.
3. **Where the translation step lives** — in each EN generator (emit ES alongside EN) vs. a standalone `translate_to_es.py` post-process that watches the EN outputs. Lean standalone post-process (decouples the fork from the EN pipeline; a translation failure never touches the EN site).
4. **Hosting/migration** — this multiplies the laptop-cron surface; ties to "Move TDB off the laptop." A clean translation post-process is easy to migrate.
5. **Whether to consolidate** the EN config first (Repo Consolidation roadmap) so the fork inherits a clean, version-controlled source.

## Cost

Negligible: translation ~pennies/artifact (Sonnet), Spanish TTS comparable to EN podcast, domain ~$12/yr. The real cost is build time, not runtime.

## Ties to existing roadmaps

- **Spanish-Language TDB** (CLAUDE.md) — this is its evolved, full-fork form.
- **Short-form video** — Spanish cuts are an early deliverable here.
- **Move TDB off the laptop** / **Repo Consolidation** — both make the fork cleaner; ideally consolidate + migrate the EN pipeline first so the fork forks something tidy.
- **Eliminate OpenClaw** — a deterministic EN brief pipeline (`generate_brief.py`) makes a clean, translatable source artifact, which helps the fork.
