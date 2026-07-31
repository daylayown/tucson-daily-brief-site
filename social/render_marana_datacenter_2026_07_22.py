#!/usr/bin/env python3
"""
Single card for the Marana data-center election In Depth story (2026-07-22).

One message, two aspect ratios per house convention: IG 4:5 (1080x1350) + a
crop-proof FB square (1200x1200), same copy. Light "news headline" theme.

Facts are from the published In Depth piece
(in-depth/marana-data-center-election.html): mayor Post ~54-46; the three
incumbents who approved the Jan. 6 rezoning kept their seats; the anti-data-
center "Marana for the People" slate took just 1 of 4 council seats (McGuire).
Figures are UNOFFICIAL, pre-canvass (99.2% precincts reporting) — the card
says "in unofficial returns"; the caption carries the fuller caveat.
"""
from render_card import build_card, render

KICKER = "Data Center · Marana"
HEADLINE = "Marana kept the council that approved its data center."
DEK = ("In unofficial returns, the town split almost down the middle — but the "
       "mayor and all three incumbents who approved the $5 billion Luckett Road "
       "project won, while the slate that fought it took just one of four "
       "council seats.")
META = "In Depth · tucsondailybrief.com"

CARDS = [
    dict(slug="marana-datacenter-2026-07-22", size=None),            # IG 4:5
    dict(slug="marana-datacenter-2026-07-22-fb", size=(1200, 1200)),  # FB square
]

if __name__ == "__main__":
    for c in CARDS:
        size = c["size"]
        print(f"rendering {c['slug']} ...")
        render(c["slug"],
               build_card(theme="light", kicker=KICKER, headline=HEADLINE,
                          dek=DEK, meta_text=META, size=size),
               size=size)
    print("done.")
