#!/usr/bin/env python3
"""
Mosaic Quarter Iceplex social pair for 2026-08-01 (weekend / light register).

Two slides, each IG 4:5 (1080x1350) + a crop-proof FB square (1200x1200):
  1. The hook — it is 110 degrees out and Tucson is building three ice rinks.
  2. The interactivity beat — a prompt answerable from the reader's own life.

WHY THIS ONE. The weekend rule (MARKETING.md, "Editorial register: light vs
heavy") is newsletter promo + light/fun only. Three heat cards had already
shipped in eight days (07-24, 07-30) so a fourth would be repetitive; the ice
rink carries the same heat without being a heat card. Instagram is a positive
platform — let it inform and delight, no caveat-stacking.

VERIFICATION (2026-08-01). Everything on the cards, and where it comes from:

  SOLID — location. Mosaic Quarter is on Tucson's SOUTH side, at the Kino Sports
    Complex (2500 E. Ajo Way, near Kino Parkway and I-10). KGUN files its
    coverage under "southside-news"; KOLD's 2024 headline reads "Tucson's
    southside." ⚠️ The 2026-08-02 newsletter draft originally said "north side"
    — a generator fabrication caught and fixed pre-send. Do not reintroduce it.

  SOLID — this week's news peg. Our own 2026-07-31 brief: "Construction
    continues at Tucson's Mosaic Quarter development, and KVOA reported a first
    look inside the project's ice complex, one of its main attractions."

  SOLID — the heat. NWS Extreme Heat Warning in effect through 8 p.m. Mon Aug 3;
    Sunday Aug 2 forecast high near 110°F (NWS Tucson, via our 2026-08-01 brief).
    "110 degrees" on the card is the actual Sunday forecast, not a round number.

  WELL-SOURCED, attributed in caption not on card — the Iceplex spec: 175,000
    sq ft, three NHL-sized sheets, targeting a March 2027 opening. Carried by
    AZPM, JLG Architects (the project architect), Tucson Sentinel and Cronkite
    News. The CARDS deliberately say only "three ice rinks" and "2027" — the
    squarest-sourced pieces — and the fuller spec lives in the caption.

Deliberately NOT on the cards: the $425M phase-one figure and "Southern
Arizona's ice sports epicenter." Developer-side framing; unverified by us.

Usage:
    .venv/bin/python3 social/render_icerink_2026_08_01.py
"""
from render_card import build_card, render

NEWS_KICKER = "Around Town"
NEWS_HEAD = "It’s 110 degrees out. Tucson is building three ice rinks."
NEWS_DEK = (
    "Cameras got the first look inside the Iceplex at Mosaic Quarter this week — "
    "the sports and entertainment district going up on the south side, out by the "
    "Kino Sports Complex. It’s targeting a 2027 opening."
)

ASK_KICKER = "Around Town"
ASK_HEAD = "Be honest: what’s the first thing you’d do in there right now?"
ASK_DEK = (
    "Lace up? Lie down at center ice? Just stand in the cold air with your eyes "
    "closed? No wrong answers today — tell us below 👇"
)

CARDS = [
    dict(slug="icerink-2026-08-01", theme="light",
         kicker=NEWS_KICKER, headline=NEWS_HEAD, dek=NEWS_DEK,
         meta_text="swipe →"),
    dict(slug="icerink-2026-08-01-fb", theme="light", size=(1200, 1200),
         kicker=NEWS_KICKER, headline=NEWS_HEAD, dek=NEWS_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="icerink-ask-2026-08-01", theme="terracotta",
         kicker=ASK_KICKER, headline=ASK_HEAD, dek=ASK_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="icerink-ask-2026-08-01-fb", theme="terracotta", size=(1200, 1200),
         kicker=ASK_KICKER, headline=ASK_HEAD, dek=ASK_DEK,
         meta_text="tucsondailybrief.com"),
]

if __name__ == "__main__":
    for c in CARDS:
        slug = c.pop("slug")
        size = c.pop("size", None)
        print(f"rendering {slug} ...")
        render(slug, build_card(size=size, **c), size=size)
    print("done.")
