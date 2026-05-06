#!/usr/bin/env python3
"""Filter the STWL-derived wordlist by word-frequency (Zipf scale).

Reads wordlist-source.json (the unfiltered STWL-at-score-50 baseline) and
writes wordlist.json (used by generate_grid.py at runtime). Removes obscure
fill that's valid English but feels weird in a warm Sunday mini —
UGALI/AROAR/BOPIT-class words. Tucson wordbank entries are whitelisted
regardless of frequency so curated local words (NOPAL, ELOTE, SAGUARO…)
always pass through. Blocklist entries are still excluded.

This is a build-time tool, not a runtime dep. Run it whenever the threshold,
wordbank, or blocklist changes; commit the resulting wordlist.json.

Usage (run from repo root):
    .venv/bin/python3 crossword/tools/filter_wordlist.py
    .venv/bin/python3 crossword/tools/filter_wordlist.py --threshold 2.0

Requires: pip install wordfreq (in the venv that runs this script).
"""

import argparse
import json
from pathlib import Path

from wordfreq import zipf_frequency

THIS_DIR = Path(__file__).parent
SOURCE_PATH = THIS_DIR / "wordlist-source.json"
OUTPUT_PATH = THIS_DIR / "wordlist.json"
WORDBANK_PATH = THIS_DIR / "wordbank-tucson.json"
BLOCKLIST_PATH = THIS_DIR / "wordlist-blocklist.json"

DEFAULT_THRESHOLD = 2.5


def load_wordbank_words() -> set[str]:
    if not WORDBANK_PATH.exists():
        return set()
    with open(WORDBANK_PATH) as f:
        data = json.load(f)
    return {entry["word"].upper() for entry in data.get("words", [])}


def load_blocklist() -> set[str]:
    if not BLOCKLIST_PATH.exists():
        return set()
    with open(BLOCKLIST_PATH) as f:
        data = json.load(f)
    return {w.upper() for w in data.get("blocklist", [])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--threshold", type=float, default=DEFAULT_THRESHOLD,
        help=f"Zipf frequency floor (default {DEFAULT_THRESHOLD}). Higher = stricter.",
    )
    parser.add_argument(
        "--lang", default="en",
        help="wordfreq language code (default 'en').",
    )
    args = parser.parse_args()

    if not SOURCE_PATH.exists():
        raise SystemExit(
            f"Source wordlist not found at {SOURCE_PATH}. "
            "Did you rename the original wordlist.json to wordlist-source.json?"
        )

    with open(SOURCE_PATH) as f:
        source = json.load(f)

    wordbank = load_wordbank_words()
    blocklist = load_blocklist()

    print(f"Source list: {sum(len(w) for w in source['words'].values())} words")
    print(f"Wordbank whitelist: {len(wordbank)} entries")
    print(f"Blocklist: {len(blocklist)} entries")
    print(f"Frequency floor: Zipf >= {args.threshold}\n")

    output_words: dict[str, list[str]] = {}
    stats = {
        "kept_freq": 0,
        "kept_wordbank_low_freq": 0,
        "dropped_low_freq": 0,
        "dropped_blocklist": 0,
        "added_from_wordbank": 0,
    }

    for length_str, words in source["words"].items():
        kept: list[str] = []
        for w in words:
            wu = w.upper()
            if wu in blocklist:
                stats["dropped_blocklist"] += 1
                continue
            zipf = zipf_frequency(w.lower(), args.lang)
            if wu in wordbank:
                if zipf < args.threshold:
                    stats["kept_wordbank_low_freq"] += 1
                else:
                    stats["kept_freq"] += 1
                kept.append(w)
            elif zipf >= args.threshold:
                stats["kept_freq"] += 1
                kept.append(w)
            else:
                stats["dropped_low_freq"] += 1
        output_words[length_str] = sorted(kept)

    # Add any wordbank words missing from source (curated entries override).
    existing_upper = {w for words in output_words.values() for w in (x.upper() for x in words)}
    for wbw in wordbank:
        if wbw not in existing_upper:
            length_key = str(len(wbw))
            if length_key not in output_words:
                output_words[length_key] = []
            output_words[length_key].append(wbw)
            output_words[length_key].sort()
            stats["added_from_wordbank"] += 1

    output_data = {
        "source": source.get("source", "Spread The Wordlist (STWL)"),
        "license": source.get("license", "CC BY-NC-SA 4.0"),
        "min_score": source.get("min_score", 50),
        "min_zipf_freq": args.threshold,
        "filter_notes": (
            f"Filtered from wordlist-source.json by Zipf frequency floor "
            f"({args.threshold}) using wordfreq library. Tucson wordbank "
            "entries are whitelisted regardless of frequency. Blocklist "
            "entries (wordlist-blocklist.json) are excluded. Regenerate by "
            "running: .venv/bin/python3 crossword/tools/filter_wordlist.py"
        ),
        "counts": {k: len(v) for k, v in output_words.items()},
        "words": output_words,
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output_data, f, indent=2)

    total_in = sum(len(w) for w in source["words"].values())
    total_out = sum(len(w) for w in output_words.values())
    print("Filtering complete:")
    print(f"  Source words: {total_in}")
    print(f"  Filtered words: {total_out}")
    if total_in:
        print(f"  Reduction: {total_in - total_out} ({(total_in - total_out) / total_in:.0%})")
    print(f"  By length: {output_data['counts']}")
    print("\nDetails:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"\nWrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
