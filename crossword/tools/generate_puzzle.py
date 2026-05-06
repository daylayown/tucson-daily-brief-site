#!/usr/bin/env python3
"""Full puzzle generation pipeline for The Tucson Mini.

Adapted from Crosswording the Situation. Same scaffolding (grid generator,
Claude API plumbing, validation, dedup). The only meaningful divergences:

  1. News corpus is the past 7 days of Tucson Daily Brief posts (read_tdb_posts),
     not Google News + Bluesky.
  2. Clue-generation prompt is loosened: prefer Tucson-flavored, local-news, or
     wordbank-aware clues, but generic crossword fill is acceptable when warmly
     clued. No NO_NEWS_HOOK escape hatch.
  3. Soft-hedging guard: clues based on early filings / planned openings /
     proposed items must not imply certainty.
  4. Local wordbank context is injected for any grid answer that appears in
     wordbank-tucson.json, plus the thematic_lexicon is provided globally so
     iconic Tucson terms (SAGUARO, MONSOON, JAVELINA…) get biased into clue
     text whenever natural.
  5. Output filename has an unguessable slug: puzzles/YYYY-MM-DD-XXXXXX.json
     so the URL is unlisted-by-obscurity (not auto-discoverable from the date).
"""

import json
import math
import os
import random
import re
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

# Import our modules
sys.path.insert(0, str(Path(__file__).parent))
from generate_grid import solve_grid, grid_to_json
from read_tdb_posts import read_recent_posts, format_posts_for_prompt

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-6"
API_URL = "https://api.anthropic.com/v1/messages"

CROSSWORD_DIR = Path(__file__).parent.parent
PUZZLES_DIR = CROSSWORD_DIR / "puzzles"
WORDBANK_PATH = Path(__file__).parent / "wordbank-tucson.json"


def parse_json_response(text: str) -> dict:
    """Parse JSON from a Claude response, handling markdown code blocks."""
    json_str = text.strip()
    if json_str.startswith("```"):
        json_str = re.sub(r"^```\w*\n?", "", json_str)
        json_str = re.sub(r"\n?```$", "", json_str)
    if not json_str.startswith("{"):
        match = re.search(r"\{.*\}", json_str, re.DOTALL)
        if match:
            json_str = match.group(0)
    return json.loads(json_str)


def call_claude(prompt: str, system: str = "") -> str:
    """Call the Anthropic API and return the text response."""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": MODEL,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system
    resp = requests.post(API_URL, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["content"][0]["text"]


def get_recent_clues_and_words(weeks_back: int = 8) -> tuple[list[str], list[str]]:
    """Read recent puzzle JSONs and extract used clue texts and answer words.

    Looks ~8 weeks back since this is a weekly puzzle. Filenames are
    YYYY-MM-DD-XXXXXX.json so we glob by date prefix.
    """
    clues: list[str] = []
    words: list[str] = []
    today = datetime.now()
    cutoff = today - timedelta(weeks=weeks_back)
    if not PUZZLES_DIR.exists():
        return clues, words
    for path in sorted(PUZZLES_DIR.glob("*.json")):
        # Date is the first 10 chars of the filename
        try:
            file_date = datetime.strptime(path.stem[:10], "%Y-%m-%d")
        except ValueError:
            continue
        if file_date < cutoff:
            continue
        try:
            with open(path) as f:
                puzzle = json.load(f)
        except Exception:
            continue
        for direction in ("across", "down"):
            for entry in puzzle.get("clues", {}).get(direction, []):
                clues.append(entry.get("clue", ""))
                words.append(entry.get("answer", ""))
    return clues, words


def load_wordbank() -> dict:
    """Load the Tucson wordbank. Returns {} if missing (graceful degrade)."""
    if not WORDBANK_PATH.exists():
        return {}
    with open(WORDBANK_PATH) as f:
        return json.load(f)


def wordbank_index(wordbank: dict) -> dict[str, dict]:
    """Map word -> entry dict for fast lookup."""
    return {entry["word"].upper(): entry for entry in wordbank.get("words", [])}


def wordbank_context_for_answers(answers: list[str], wb_idx: dict[str, dict]) -> str:
    """Render per-answer Tucson context for the LLM prompt. Returns empty string if no matches."""
    matched: list[str] = []
    for a in answers:
        entry = wb_idx.get(a.upper())
        if not entry:
            continue
        styles = "; ".join(entry.get("clue_styles", [])) or "(no preset clue styles)"
        ctx = entry.get("context", "")
        strength = entry.get("tucson_strength", "")
        matched.append(f"  {a} [{strength}] — {ctx}\n    suggested angles: {styles}")
    if not matched:
        return ""
    return "TUCSON WORDBANK MATCHES (reach for these local angles when fair):\n" + "\n".join(matched)


def thematic_lexicon_block(wordbank: dict) -> str:
    """Render the thematic_lexicon as a clue-bias hint."""
    lex = wordbank.get("thematic_lexicon", {})
    terms = lex.get("terms", [])
    if not terms:
        return ""
    rows = [f"  {t['term']}: {t['context']}" for t in terms]
    return (
        "TUCSON-ICONIC TERMS (too long to be 5x5 answers, but bias these into "
        "CLUE TEXT whenever a clue can naturally reference them — they're what "
        "make a Tucson reader smile):\n" + "\n".join(rows)
    )


def generate_clues(puzzle_json: dict, posts_text: str, wordbank: dict, dedup_context: str = "") -> dict:
    """Use Claude to write Tucson-flavored clues for a crossword grid."""

    across_words = [(c["number"], c["answer"], "across") for c in puzzle_json["clues"]["across"]]
    down_words = [(c["number"], c["answer"], "down") for c in puzzle_json["clues"]["down"]]
    all_words = across_words + down_words
    answers = [a for _, a, _ in all_words]
    word_list = "\n".join(f"  {num}{d[0].upper()}: {answer}" for num, answer, d in all_words)

    wb_idx = wordbank_index(wordbank)
    wordbank_block = wordbank_context_for_answers(answers, wb_idx)
    lex_block = thematic_lexicon_block(wordbank)

    system = """You are an expert crossword editor for The Tucson Mini, a weekly Tucson-themed 5x5 mini crossword. The reader is a regular Tucsonan solving with coffee on a Sunday morning — your clues should make them smile.

NORTH STAR: Tucson vocabulary is the soul of this puzzle. Each clue should, where natural, evoke a Tucson, Sonoran Desert, Southwest, or U of A flavor — through the answer itself, the clue's framing, or a reference to a Tucson place/landmark/landscape that actually exists. This is what makes The Tucson Mini different from a generic mini.

NEWS IS A SMALL ACCENT, NOT THE POINT. Past-week Tucson Daily Brief stories are provided below. Reach for them when a clue can naturally use one — typically 1-3 of the 10 clues, no more. Tucson is a small city; not much news happens in any given week, and that's fine. NEVER strain to manufacture a news tie. If a story doesn't fit naturally, ignore it and write a clean Tucson-flavored or general clue.

Editorial posture:
- WARM, fair, brief, lightly playful when natural. Tucson-flavored, never corny.
- Solvable by a normal Tucson reader (not a 30-year resident who reads every Pima County agenda).
- Avoid bureaucratic jargon, agenda-language, civic-tech vocabulary ("public records," "monitoring the situation"). The puzzle is a perk, not a quiz.
- Avoid stacking too many proper nouns or too many Spanish loanwords.

HARD RULE — DO NOT INVENT TUCSON REFERENCES.
If a clue names a specific Tucson place, business, person, park, road, neighborhood, school, or institution, that thing MUST actually exist AND you must have evidence for it from one of:
  (a) the Tucson wordbank "context" or "clue_styles" entry for the answer,
  (b) the thematic lexicon provided below, or
  (c) the past-week TDB stories provided below.
Do NOT fabricate plausible-sounding local color. Examples of what's forbidden:
  - "a common Tucson dog-park name" (not in any reference — invented)
  - "seen on Speedway" applied to a chain not actually known to be on Speedway
  - "a neighborhood near downtown" for a name that isn't actually a Tucson neighborhood
If you can't make an honest, evidenced local reference for an answer, write a clean GENERAL clue (definition, wordplay, common knowledge) instead. A clean general clue is a feature, not a failure.

HARD RULE — DO NOT INVENT FACTS, EVER. (Applies to ALL clues, not just Tucson ones.)
Every factual claim in a clue must be real, verifiable common knowledge. The puzzle's credibility depends on every clue being TRUE. Specifically forbidden:
  - Inventing etymology or naming origins. Real example to NEVER do: "the Colorado River was named for a biblical patriarch" — false; it's Spanish for 'colored red.'
  - Stretching medical, scientific, or geographic facts to manufacture a Tucson tie. Real example to NEVER do: "EDEMA, a concern in Tucson's dry summer heat" — dry heat causes dehydration, not edema.
  - Connecting a name/person to a news story or institution that doesn't actually feature them. Real example to NEVER do: "a name fit for a UA Guggenheim Fellow" when no person of that name was actually named in the Guggenheim story.
  - Asserting business locations, dates, prices, attendance, scores, or other specific facts not present in the provided source material.
When in doubt, write a SIMPLE DEFINITION or clean WORDPLAY clue. A short, accurate, honest clue is ALWAYS better than a clever-sounding clue that asserts something false. If you find yourself constructing a clue with words like "named for," "known as," "associated with," "famous for" — pause and ask whether you can actually verify that connection from common knowledge or the provided sources. If not, rewrite as a definition.

CRITICAL HEDGING RULE — soft language for uncertain news items:
If a clue is based on something early-stage (a filing, an agenda item, a proposed opening, a planned development, a candidate's pitch), the clue must NOT imply certainty. Use hedged language like "planned," "proposed," "listed," "on the agenda," "would-be," "if approved," or just avoid that angle. Never write a clue that asserts a still-uncertain thing as a settled fact.

Other rules:
- Keep clues concise (under 80 characters ideally).
- Never repeat the answer word in the clue.
- Each clue must reference a DIFFERENT topic — don't double up on the same story or theme across clues."""

    dedup_section = ""
    if dedup_context:
        dedup_section = f"""

---

CLUES AND ANSWER WORDS USED IN RECENT TUCSON MINIS (avoid revisiting these topics; the answers themselves are already excluded from the grid):
{dedup_context}
"""

    # Prompt order is deliberate: wordbank context FIRST (north star), then
    # broader Tucson lexicon, then the grid, then the past-week news as
    # an optional accent. The LLM should be reading Tucson signals first
    # and treating news as supporting material.
    pieces = []
    if wordbank_block:
        pieces.append("PRIMARY MATERIAL — these answers have curated Tucson context. Reach for these angles first:")
        pieces.append("")
        pieces.append(wordbank_block)
        pieces.append("")
        pieces.append("---")
        pieces.append("")
    if lex_block:
        pieces.append("BROADER TUCSON LEXICON — bias these terms into clue text whenever a clue can naturally use one:")
        pieces.append("")
        pieces.append(lex_block)
        pieces.append("")
        pieces.append("---")
        pieces.append("")
    pieces.append("THIS WEEK'S GRID — write a clue for each answer:")
    pieces.append("")
    pieces.append(word_list)
    pieces.append("")
    pieces.append("---")
    pieces.append("")
    pieces.append("OPTIONAL — past-week Tucson Daily Brief stories. Use a story ONLY if it fits an answer naturally; do NOT strain. Typically 1-3 clues at most will draw on news; the rest should be Tucson-flavor or clean general clues:")
    pieces.append("")
    pieces.append(posts_text or "(No recent TDB posts available — that's fine, lean on Tucson lexicon and clean general clues.)")
    pieces.append(dedup_section)
    pieces.append("")
    pieces.append("Return your answer as a JSON object with this exact format:")
    pieces.append("")
    pieces.append('{\n  "clues": {\n    "1A": "Your clue for 1-Across here",\n    "5A": "Your clue for 5-Across here",\n    ...\n    "1D": "Your clue for 1-Down here",\n    ...\n  }\n}')
    pieces.append("")
    pieces.append("Return ONLY the JSON object, no other text.")
    prompt = "\n".join(pieces)

    print("Calling Claude to generate clues...")
    response = call_claude(prompt, system)
    clue_data = parse_json_response(response)
    return clue_data["clues"]


def apply_clues(puzzle_json: dict, clues: dict) -> dict:
    """Apply Claude-generated clues to the puzzle JSON."""
    for entry in puzzle_json["clues"]["across"]:
        key = f"{entry['number']}A"
        if key in clues:
            entry["clue"] = clues[key]
    for entry in puzzle_json["clues"]["down"]:
        key = f"{entry['number']}D"
        if key in clues:
            entry["clue"] = clues[key]
    return puzzle_json


def validate_puzzle(puzzle_json: dict) -> bool:
    """Validate that the puzzle is internally consistent."""
    grid = puzzle_json["grid"]
    size = puzzle_json["size"]
    errors: list[str] = []

    for entry in puzzle_json["clues"]["across"]:
        word = ""
        for i in range(entry["length"]):
            word += grid[entry["row"]][entry["col"] + i]
        if word != entry["answer"]:
            errors.append(f"{entry['number']}A: grid reads '{word}' but answer is '{entry['answer']}'")

    for entry in puzzle_json["clues"]["down"]:
        word = ""
        for i in range(entry["length"]):
            word += grid[entry["row"] + i][entry["col"]]
        if word != entry["answer"]:
            errors.append(f"{entry['number']}D: grid reads '{word}' but answer is '{entry['answer']}'")

    all_answers = [e["answer"] for e in puzzle_json["clues"]["across"]] + \
                  [e["answer"] for e in puzzle_json["clues"]["down"]]
    if len(set(all_answers)) != len(all_answers):
        dupes = [a for a in all_answers if all_answers.count(a) > 1]
        errors.append(f"Duplicate answers: {set(dupes)}")

    for entry in puzzle_json["clues"]["across"] + puzzle_json["clues"]["down"]:
        if not entry["clue"] or entry["clue"].startswith("[Clue for"):
            errors.append(f"{entry['number']}: missing clue")

    if errors:
        print("Validation errors:")
        for e in errors:
            print(f"  - {e}")
        return False
    print("Puzzle validated successfully!")
    return True


def existing_puzzle_for_date(date: str) -> Path | None:
    """Return any existing puzzle file for this date (date-XXXXXX.json), if present."""
    if not PUZZLES_DIR.exists():
        return None
    matches = sorted(PUZZLES_DIR.glob(f"{date}-*.json"))
    return matches[0] if matches else None


def main():
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    args = sys.argv[1:]
    force = False
    if "--force" in args:
        force = True
        args = [a for a in args if a != "--force"]

    date = args[0] if args else datetime.now().strftime("%Y-%m-%d")

    existing = existing_puzzle_for_date(date)
    if existing and not force:
        print(f"Puzzle already exists for {date}: {existing.name}")
        print("Pass --force to generate a new one (will leave the old file in place).")
        sys.exit(0)

    print(f"Generating Tucson Mini for {date}")
    print("=" * 40)

    PUZZLES_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Load recently used answer words (cross-puzzle dedup, ~8 weeks)
    print("\nStep 1: Loading recently used answer words...")
    _, recent_words = get_recent_clues_and_words(weeks_back=8)
    base_excluded_answers = {w.upper() for w in recent_words if w}
    if base_excluded_answers:
        print(f"  Excluding {len(base_excluded_answers)} answer words from recent puzzles")
    else:
        print("  No recent puzzles found — no exclusions")

    # Step 2: Read past-week TDB posts as the news corpus
    print("\nStep 2: Reading past-week Tucson Daily Brief posts...")
    stories = read_recent_posts(days_back=7)
    print(f"  Loaded {len(stories)} stories from TDB")
    posts_text = format_posts_for_prompt(stories) if stories else ""

    # Step 3: Build cross-puzzle dedup context
    print("\nStep 3: Building cross-puzzle dedup context...")
    recent_clues, _ = get_recent_clues_and_words(weeks_back=8)
    dedup_context = ""
    if recent_clues:
        clue_lines = [f"  - {c}" for c in recent_clues if c]
        word_lines = [f"  - {w}" for w in sorted(base_excluded_answers) if w]
        dedup_context = (
            f"Recently used clues:\n{chr(10).join(clue_lines)}\n\n"
            f"Recently used answer words:\n{chr(10).join(word_lines)}"
        )
        print(f"  Found {len(recent_clues)} clues and {len(base_excluded_answers)} unique words from recent puzzles")
    else:
        print("  No recent puzzles found for dedup")

    # Step 4: Load Tucson wordbank
    print("\nStep 4: Loading Tucson wordbank...")
    wordbank = load_wordbank()
    preferred_answers: set[str] = set()
    if wordbank:
        preferred_answers = {entry["word"].upper() for entry in wordbank.get("words", [])}
        print(f"  Wordbank: {len(wordbank.get('words', []))} answer entries, "
              f"{len(wordbank.get('thematic_lexicon', {}).get('terms', []))} thematic terms")
        print(f"  {len(preferred_answers)} answer words will be preferred by the grid generator")
    else:
        print("  Wordbank not found — proceeding without local-flavor context")

    # Step 5: Grid + clues with retry. The retry loop is preserved from the
    # upstream pipeline as defense-in-depth (handles transient API failures
    # and validation issues), even though we no longer reject on news-hook.
    MAX_GRID_ATTEMPTS = 3
    excluded_answers = set(base_excluded_answers)
    puzzle_json = None

    for grid_attempt in range(1, MAX_GRID_ATTEMPTS + 1):
        print(f"\n=== Grid attempt {grid_attempt}/{MAX_GRID_ATTEMPTS} ===")
        random.seed(None)
        grid = solve_grid(
            max_attempts=5000,
            excluded_words=excluded_answers,
            preferred_words=preferred_answers,
        )
        if not grid:
            print("  Could not find grid with full exclusions, falling back to no exclusions...")
            grid = solve_grid(
                max_attempts=5000,
                excluded_words=set(),
                preferred_words=preferred_answers,
            )
        if not grid:
            print("  Failed to generate a valid grid this attempt; retrying.")
            continue

        candidate = grid_to_json(grid, date)

        print("  Generating clues with Claude...")
        try:
            clues = generate_clues(candidate, posts_text, wordbank, dedup_context)
        except Exception as e:
            print(f"  Clue generation failed ({e}); retrying.")
            continue
        candidate = apply_clues(candidate, clues)

        if not validate_puzzle(candidate):
            print("  Validation failed; retrying with a new grid.")
            continue

        puzzle_json = candidate
        break

    if puzzle_json is None:
        print(f"\nFailed to produce a publishable puzzle after {MAX_GRID_ATTEMPTS} grid attempts.")
        sys.exit(1)

    # Step 6: Cross-clue duplicate-story check (keep upstream's editorial pass)
    print("\nStep 6: Checking for duplicate references across clues...")
    all_clue_texts = []
    for entry in puzzle_json["clues"]["across"]:
        all_clue_texts.append(f"{entry['number']}A: {entry['clue']}")
    for entry in puzzle_json["clues"]["down"]:
        all_clue_texts.append(f"{entry['number']}D: {entry['clue']}")

    dedup_prompt = f"""Review these crossword clues and check if any two clues reference the same story, event, person, place, or topic too closely:

{chr(10).join(all_clue_texts)}

If any clues overlap, respond with a JSON object listing the conflicting clue numbers (keep the first, flag the rest for rewrite). If all clues reference different topics, respond with an empty list.

Format: {{"conflicts": ["4D", "7A"]}} or {{"conflicts": []}}

Return ONLY the JSON object."""

    try:
        dedup_response = call_claude(dedup_prompt, "You are a careful editor checking crossword clues for duplicate references.")
        dedup_result = parse_json_response(dedup_response)
    except Exception as e:
        print(f"  Dedup check failed (non-fatal): {e}")
        dedup_result = {"conflicts": []}

    if dedup_result.get("conflicts"):
        conflict_keys = dedup_result["conflicts"]
        print(f"  Found duplicate references in: {conflict_keys}")
        print("  Regenerating clues for conflicting entries...")

        rewrite_keys = conflict_keys[1:] if len(conflict_keys) > 1 else conflict_keys

        existing_topics = []
        for entry in puzzle_json["clues"]["across"]:
            key = f"{entry['number']}A"
            if key not in rewrite_keys:
                existing_topics.append(f"{key}: {entry['clue']}")
        for entry in puzzle_json["clues"]["down"]:
            key = f"{entry['number']}D"
            if key not in rewrite_keys:
                existing_topics.append(f"{key}: {entry['clue']}")

        rewrite_words = []
        for entry in puzzle_json["clues"]["across"]:
            key = f"{entry['number']}A"
            if key in rewrite_keys:
                rewrite_words.append(f"{key}: {entry['answer']}")
        for entry in puzzle_json["clues"]["down"]:
            key = f"{entry['number']}D"
            if key in rewrite_keys:
                rewrite_words.append(f"{key}: {entry['answer']}")

        fix_prompt = f"""These crossword clues are already in use and their topics are OFF LIMITS:

{chr(10).join(existing_topics)}

Write NEW clues for these words that reference DIFFERENT topics. Same Tucson Mini editorial posture as before — warm, fair, brief, hedged on uncertain news items, mix of local-flavor and clean general clues OK:

{chr(10).join(rewrite_words)}

Past-week TDB stories for reference:
{posts_text}

Return ONLY a JSON object: {{"clues": {{"4D": "new clue here", ...}}}}"""

        try:
            fix_response = call_claude(fix_prompt, "You are an expert crossword clue writer for The Tucson Mini.")
            fix_clues = parse_json_response(fix_response)["clues"]
            puzzle_json = apply_clues(puzzle_json, fix_clues)
            print("  Replacement clues applied.")
        except Exception as e:
            print(f"  Replacement failed (non-fatal, keeping original clues): {e}")
    else:
        print("  No duplicate references found.")

    # Step 7: Write output with unguessable slug
    slug = secrets.token_hex(3)  # 6 hex chars
    out_filename = f"{date}-{slug}.json"
    out_path = PUZZLES_DIR / out_filename

    # Add the slug to the puzzle JSON for downstream tooling (newsletter, etc.)
    puzzle_json["slug"] = f"{date}-{slug}"

    with open(out_path, "w") as f:
        json.dump(puzzle_json, f, indent=2)

    # Stash the latest slug for the newsletter generator to pick up
    latest_path = PUZZLES_DIR / ".latest.txt"
    with open(latest_path, "w") as f:
        f.write(f"{date}-{slug}\n")

    print(f"\nPuzzle written to {out_path}")
    print(f"Play URL: /crossword/play.html?p={date}-{slug}")
    print("\n--- Final Puzzle ---")
    print(f"Date: {puzzle_json['date']}  Slug: {puzzle_json['slug']}")
    for r in range(puzzle_json["size"]):
        row = puzzle_json["grid"][r]
        print(" ".join(c if c != "#" else "." for c in row))
    print("\nAcross:")
    for e in puzzle_json["clues"]["across"]:
        print(f"  {e['number']}. {e['clue']} ({e['answer']})")
    print("\nDown:")
    for e in puzzle_json["clues"]["down"]:
        print(f"  {e['number']}. {e['clue']} ({e['answer']})")


if __name__ == "__main__":
    main()
