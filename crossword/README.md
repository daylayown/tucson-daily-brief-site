# The Tucson Mini

Weekly Tucson-themed 5×5 mini crossword. Subscriber perk for the Sunday Tucson Daily Brief newsletter.

Adapted from [Crosswording the Situation](../../crossword-puzzle/) — same scaffolding (grid generator, Claude plumbing, validation, JS engine, mobile UX), retuned for a weekly local audience.

## What's reused vs. what's new

| File | Origin |
|---|---|
| `tools/generate_grid.py` | Verbatim from CtS |
| `tools/wordlist.json` | Verbatim from CtS (Spread The Wordlist, CC BY-NC-SA 4.0) |
| `crossword.js` | CtS, with two small edits: query-param loader (no auto-load by date) and "Tucson Mini" share string |
| `style.css` | CtS structure, repaletted to TDB desert tones (sand / terracotta / sage / brown) |
| `play.html` | CtS shell, retitled, noindex, signup CTA points to TDB newsletter |
| `tools/read_tdb_posts.py` | **New** — replaces CtS's Google News + Bluesky scrapers; reads `posts/YYYY-MM-DD.html` |
| `tools/generate_puzzle.py` | CtS, with: TDB posts as the news corpus; loosened clue prompt (prefer-not-require local/news ties); soft-hedging guard for uncertain items; wordbank context injection; unguessable slug in output filename |
| `tools/wordbank-tucson.json` | **New** — 79 curated 3–5-letter Tucson-flavored answers + 45 thematic-lexicon terms for clue text |

## How it works

1. `read_tdb_posts.py` reads the past 7 days of TDB posts, extracts each bold-headline story with section + summary + source.
2. `generate_grid.py` produces a valid 5×5 grid using STWL (12.7K words, 3–5 letters), preferring grids that don't reuse answer words from the past ~8 weeks.
3. `generate_puzzle.py` sends the grid + past-week TDB stories + Tucson wordbank context to Claude Sonnet 4.6 with a Tucson-Mini editorial prompt, then validates and dedupes.
4. Output: `puzzles/YYYY-MM-DD-XXXXXX.json` where `XXXXXX` is a 6-hex-char unguessable slug. The latest slug is also written to `puzzles/.latest.txt` for the newsletter generator.

## Running it

```bash
# Set the API key (same one used elsewhere in the TDB pipeline)
source ~/.config/environment.d/anthropic.conf

# Generate this week's puzzle
python3 crossword/tools/generate_puzzle.py

# Or for a specific date
python3 crossword/tools/generate_puzzle.py 2026-05-10

# Force regeneration if a puzzle for that date already exists
python3 crossword/tools/generate_puzzle.py --force

# Sanity-check the TDB post reader independently
python3 crossword/tools/read_tdb_posts.py 7
```

## URLs

- Play page (always at this path): `/crossword/play.html?p={slug}`
- Puzzle JSON: `/crossword/puzzles/{slug}.json`
- The play page has `<meta name="robots" content="noindex,nofollow">`, no public link from the rest of the site, and shows a "no puzzle here" empty state if `?p=` is missing or malformed.

## Editorial posture

The clue-generation prompt diverges intentionally from CtS:

- **Not every clue needs a news tie.** Mix of past-week TDB stories, broader Tucson/Sonoran/UA/desert references, and clean general clues — generic crossword fill is acceptable when warmly clued.
- **Soft-hedging on uncertain items.** Clues based on filings, agenda items, planned openings, candidate pitches must not imply certainty. Use "planned," "proposed," "listed," "on the agenda," etc.
- **No bureaucratic register.** Avoid "public records," "monitoring the situation," agenda-language. The puzzle is a perk, not a quiz.
- **Wordbank-aware.** When an answer is in `wordbank-tucson.json`, its `clue_styles` and `context` are passed to Claude as suggested angles. The thematic lexicon (SAGUARO, MONSOON, JAVELINA, …) is also passed globally to bias clue *text* whenever natural.

## Cadence (planned)

Weekly. Likely Saturday night cron, so the puzzle file exists in time for the Sunday newsletter draft. Cron wiring is TBD — `check_agendas.sh`-style shell wrapper to be added once the newsletter generator lands.
