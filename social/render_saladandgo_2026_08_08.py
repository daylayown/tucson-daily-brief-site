#!/usr/bin/env python3
"""
Salad and Go collapse — social package for 2026-08-08/10.

Three surfaces, one story:
  1. X thread opener image, 16:9 (1200x675) — posts TODAY (Sat) with the
     rise-and-fall thread. Stat-card shape: the "48 hours" number is the
     hook; the thread text carries the arc, the founding year, and the
     $105M twist, so card and text don't duplicate (SOCIAL-CARDS.md rule).
  2. IG 4:5 (1080x1350) — Monday feed post.
  3. FB square (1200x1200) — crop-proof for the Page.

VERIFICATION (2026-08-08, all claims web-verified this morning against
azfamily 8/05 + 8/06, AZPM 8/05, QSR Magazine, Fast Company — see the
newsletter fact-check session):

  SOLID — bankruptcy announced Tuesday Aug 4; all locations closed by end
    of day Wednesday Aug 5 (azfamily: "announced on Tuesday... close all
    locations on Wednesday"). "48 hours" is the announce->dark span,
    rounded up from ~2 days; the dek says "about 48 hours."
  SOLID — seven Tucson-area locations (AZPM; TDB briefs 8/05).
  SOLID — Chapter 11 (azfamily, AZPM).
  SOLID — Boersma Bros LLC (Dutch Bros founders' holding co) agreed to pay
    $105M for 51 AZ/NV drive-thru leases + 14 TX/OK, fixtures and
    equipment — NOT the brand or recipes (QSR, Fast Company). Card says
    only "a company tied to Dutch Bros' founders" — the careful hedge.
  SOLID — conversions expected to start 2027 (Fast Company).

Deliberately NOT on the cards: $105M, lease counts, 2013 founding, brand/
recipes detail — that's thread/caption material.

Usage:
    .venv/bin/python3 social/render_saladandgo_2026_08_08.py
"""
from render_card import build_card, render

KICKER = "Around Town"

# X opener card — stat-card shape, needs the hsize override
X_HEAD = "48 hours."
X_DEK = (
    "That's roughly how long it took Salad and Go to go from bankruptcy "
    "announcement to every drive-thru dark — including all seven in the "
    "Tucson area."
)

# IG/FB card — the question is the hook; caption carries the Dutch Bros story
IGFB_HEAD = "Every Salad and Go, closed overnight."
IGFB_DEK = (
    "All seven Tucson-area drive-thrus went dark Wednesday with one day's "
    "notice. What happens to the empty drive-thrus next is the twist — "
    "story in the caption."
)

CARDS = [
    dict(slug="saladandgo-x-2026-08-08", theme="terracotta", size=(1200, 675),
         kicker=KICKER, headline=X_HEAD, dek=X_DEK, hsize=200,
         meta_text="tucsondailybrief.com"),
    dict(slug="saladandgo-ig-2026-08-10", theme="light",
         kicker=KICKER, headline=IGFB_HEAD, dek=IGFB_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="saladandgo-fb-2026-08-10", theme="light", size=(1200, 1200),
         kicker=KICKER, headline=IGFB_HEAD, dek=IGFB_DEK,
         meta_text="tucsondailybrief.com"),
]

# IG/FB CAPTION (Monday; carries what the cards don't):
#
#   Salad and Go filed for Chapter 11 bankruptcy Tuesday and closed every
#   location by Wednesday night. The Gilbert-founded chain grew for over a
#   decade before it all stopped at once.
#
#   The twist: court filings show a company tied to Dutch Bros Coffee's
#   founders agreed to pay $105 million for dozens of the drive-thru
#   leases, fixtures, and equipment — but not the brand or the recipes.
#   The conversions are expected to start next year. The salads aren't
#   coming back; the coffee is.
#
#   Which closed Tucson drive-thru do you still miss? 👇
#
#   #tucson #tucsonfood #tucsoneats #thingstodointucson #saladandgo

if __name__ == "__main__":
    for c in CARDS:
        slug = c.pop("slug")
        size = c.get("size")
        render(slug, build_card(**c), size=size)
        print(f"  rendered {slug}")
