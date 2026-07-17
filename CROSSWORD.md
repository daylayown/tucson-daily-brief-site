# The Tucson Mini (Weekly Subscriber Crossword)

Editorial posture, pipeline, word filtering, wordbank, unlisted publishing, the Saturday review ritual, and deferred work.

Reference doc split out of CLAUDE.md on 2026-07-17 to keep the always-loaded context lean. Prose is preserved verbatim from CLAUDE.md; CLAUDE.md now carries a short pointer to this file.

---

## The Tucson Mini (Weekly Subscriber Crossword)

Weekly Tucson-themed 5×5 mini crossword. Subscriber perk for the forthcoming TDB Weekly newsletter (see `NEWSLETTER.md`). Adapted from the upstream "Crosswording the Situation" project at `~/claude-code-projects/crossword-puzzle` — same scaffolding (grid generator, Claude API plumbing, validation, JS engine, mobile UX), retuned for a weekly local audience.

### Differentiator from CtS

CtS is **news-first**: every clue must tie to a real news story. The Tucson Mini is **Tucson-vocabulary-first**: the puzzle's identity is local flavor (saguaros, monsoons, U of A, Sonoran food, Tucson place names), with past-week TDB stories as a small accent rather than the spine. This was a deliberate editorial decision the user articulated explicitly during the May 6 build: "Tucson is a small city; not much news happens. Don't twist ourselves into knots trying to match news events to the puzzle."

### Editorial posture (encoded in the LLM prompt)

- **NORTH STAR**: Tucson vocabulary leads. Wordbank entries surface first; news is reached for only when natural (typically 1-3 of 10 clues).
- **HARD RULE — DO NOT INVENT TUCSON REFERENCES**: prompt enforced, with concrete examples of past failures ("a common Tucson dog-park name" — invented). Every Tucson reference must come from the wordbank `context`, the thematic_lexicon, or the past-week TDB stories.
- **HARD RULE — DO NOT INVENT FACTS, EVER**: applies to all clues. Real fabrications caught and prompt-fixed: "the Colorado River was named for a biblical patriarch" (false — Spanish for 'colored red'), "EDEMA, a concern in Tucson's dry summer heat" (medically wrong). When in doubt, write a simple definition or wordplay clue.
- **Soft-hedging on uncertain news items**: filings/agendas/proposed openings must use "planned," "proposed," "listed" — never assert as fact.
- **Tucson and southern Arizona only — no Phoenix-area landmarks.** This is an explicit user constraint.

### Pipeline

```
Past 7 days of TDB posts (read_tdb_posts.py)
    ↓
Tucson wordbank + thematic lexicon (wordbank-tucson.json)
    ↓
Filtered wordlist (STWL → Zipf ≥ 2.5 → filter_wordlist.py → wordlist.json)
    ↓
Grid generation (generate_grid.py: backtracking with wordbank preference)
    ↓
Clue generation (generate_puzzle.py: Sonnet 4.6, prompt with wordbank context first)
    ↓
Validate + cross-clue dedup pass
    ↓
Output: puzzles/YYYY-MM-DD-XXXXXX.json with unguessable hex slug
```

### Word filtering: frequency floor + blocklist + wordbank whitelist

The grid solver pulls from STWL (12.7K words, 3-5 letters, score 50+). Three filters layered on top:

1. **Frequency floor (Zipf ≥ 2.5)** — built once via `filter_wordlist.py`, output committed as `wordlist.json`. Auto-excludes obscure fill (UGALI 1.43, BOPIT 0, AROAR 0, RAGAS 1.86, SAGET 2.24, SESH 2.45) without hand-tagging. Tunable.
2. **Editorial blocklist** (`wordlist-blocklist.json`) — small hand-maintained list for words that pass the frequency filter but still feel wrong (currently includes BRET, ESSO, AAMCO).
3. **Wordbank whitelist** (`wordbank-tucson.json`) — Tucson-specific words always pass through, even if their Zipf is low (NOPAL 1.67, ELOTE 1.40, MARANA 1.97). Without the whitelist, half the local vocabulary would be filtered.

`wordfreq` is a Python library used at *build time* only, not at runtime. Install in `.venv` if regenerating:
```
.venv/bin/pip install wordfreq
.venv/bin/python3 crossword/tools/filter_wordlist.py
```

Re-run after editing the wordbank or blocklist, then commit the new `wordlist.json`.

### Wordbank as the editorial north star

`wordbank-tucson.json` holds 163 curated 3-5 letter Tucson/southern Arizona answers plus a 45-term thematic lexicon (longer words like SAGUARO, MONSOON, JAVELINA biased into clue *text* rather than answers). Each entry has:

- `tucson_strength` (high/medium/low) — how unmistakably Tucson it is
- `clue_styles` — sample warm clue angles
- `context` — the *why* (used by the LLM for evidenced clues)

The grid generator biases toward wordbank entries via `preferred_words` in `solve_grid()`. Currently only ACROSS slots are biased; DOWN slots emerge from intersections. Typical run: 3-5 of 10 answers come from the wordbank.

### URLs and unlisted publishing

Each puzzle gets an unguessable hex slug: `puzzles/YYYY-MM-DD-XXXXXX.json`. The play page reads `?p={slug}` from the URL:

- `tucsondailybrief.com/crossword/play.html?p=2026-05-10-49c6f1` — solvable puzzle
- `tucsondailybrief.com/crossword/play.html` — empty state ("no puzzle, you'll find the link in the newsletter")

`play.html` has `<meta name="robots" content="noindex,nofollow">`. No public link to the crossword from anywhere on the site. Subscribers get URLs only via the newsletter.

### Running it

```
.venv/bin/python3 crossword/tools/generate_puzzle.py [YYYY-MM-DD]
.venv/bin/python3 crossword/tools/generate_puzzle.py --force  # re-run for the same date
```

Outputs to `crossword/puzzles/{date}-{6char}.json` plus updates `.latest.txt` (gitignored, build-state pointer for the newsletter generator).

### Cost

~$0.02-0.03 per puzzle (Sonnet 4.6, two API calls: clue generation + dedup-references check). Negligible at weekly cadence.

### Editorial review — Saturday ritual (added 2026-06-27)

Generation is **manual and not cron'd**, so two failure modes recur and must be caught by a human before send:

1. **Silent non-generation — structurally fixed 2026-07-04.** Previously, if nobody ran `generate_puzzle.py` for the send date, the newsletter generator found no puzzle ("exact-date match, else earliest puzzle dated after") and the draft landed with `(no puzzle available — pick one before sending)` in both the Tucson Mini section and the metadata header (happened for the 2026-06-21 and 2026-06-28 sends, and again 2026-07-05 — the trigger for de-cron'ing). **Root cause:** the newsletter was cron'd Friday 6pm and generated the day *before* the Saturday puzzle existed. **Fix:** the Friday cron is removed; the newsletter is now generated by hand *after* the puzzle is locked, and `generate_newsletter.py` **hard-stops with exit 1 if no puzzle is locked for the send date** (`--allow-missing-puzzle` escape hatch). So the placeholder can no longer ship silently — worst case is a loud stop telling you to lock the puzzle first.
2. **Fabricated pop-culture clues.** The Sonnet clue generator has produced wrong celebrity/pop-culture clues repeatedly: 6/14 *"Judd of 'Twin Peaks' fame"*→NAOMI (Naomi Judd was a country singer, no Twin Peaks link — shipped); 6/28 *"Hugh ___, the Wolverine himself"*→LOGAN (the actor is Hugh **Jackman** — caught + fixed pre-send); 7/05 *"Actor Steven of 'Above the Law'"*→SEGAL (Steven **Seagal** spells it S-E-A-G-A-L, 6 letters ≠ the 5-letter SEGAL — caught + reclued to George Segal) AND *"Charles Dickens's illiterate foundling heroine"*→NELL (Little Nell has a grandfather and is literate — fabricated characterization; reclued). Violates the no-fabrication bar (`feedback_ai_content_quality_bar` memory). Pop-culture answers stay the highest-scrutiny category.

**The ritual (user's standing process, updated 2026-07-04 — puzzle now gates the newsletter):** every Saturday, generate + review that week's puzzle *together* FIRST, lock it in, and only then generate the newsletter. Steps: (1) `generate_puzzle.py YYYY-MM-DD` for the Sunday send date; (2) validate grid crossings AND fact-check every clue, with extra scrutiny on pop-culture answers; (3) fix bad clues by editing the puzzle JSON directly; (4) `git add` + commit + push the puzzle JSON — it must be on GitHub Pages for `play.html?p=<slug>` to resolve (drafts are gitignored, stay local); (5) **now** run `./run_newsletter.sh` — because the puzzle is locked, `get_crossword_link()` picks it up automatically and embeds the play URL in the Tucson Mini section + metadata header, then uploads to Buttondown (no manual URL-pasting needed). If the fabricated-clue pattern recurs, tighten the clue prompt's anti-fabrication guard around celebrity/pop-culture references.

### Deferred work (as of 2026-05-06)

- **Cron wiring** — **resolved by design 2026-07-04: deliberately kept manual.** Puzzle generation needs the together-review (fact-check step), so it isn't cron'd; and the newsletter was *de*-cron'd so it runs by hand after the puzzle is locked. The old "both should run Saturday afternoon via cron" idea is retired — the human-in-the-loop ordering is the point.
- **DOWN-slot bias** — only ACROSS is preferred toward the wordbank; DOWN words emerge from intersections.
- **Newsletter integration** — ✅ done: `generate_newsletter.py`'s `get_crossword_link()` picks the puzzle for the send date and embeds the play URL; it now hard-stops if none is locked.
- **More wordbank growth** — 163 entries is enough for years of weekly puzzles, but additions are welcome. Phoenix-area references explicitly excluded.
