#!/usr/bin/env python3
"""
Weekend heat social pair for 2026-07-24.

Two-slide carousel per house convention, each in IG 4:5 (1080x1350) + a
crop-proof FB square (1200x1200), same copy:
  1. Extreme Heat Warning safety card (terracotta)
  2. "How we know" BTS card — the forecast comes straight from the NWS public
     API (BTS/how-it's-made angle performs well for TDB; see IG-BTS-STRATEGY).

Facts verified live 2026-07-24 against the National Weather Service:
  - api.weather.gov/alerts/active?point=32.2226,-110.9747 -> "Extreme Heat
    Warning issued July 24 at 2:13AM MST until July 25 at 8:00PM MST by NWS
    Tucson AZ" (i.e. through 8 p.m. Saturday). An Air Quality Alert is also
    active. This is a REAL, in-effect warning product — kicker is "Extreme Heat
    Warning" (contrast the 2026-07-21 "Extreme Heat Ahead" forecast card, when
    no alert was in effect).
  - api.weather.gov/gridpoints/TWC/91,49/forecast: Today high ~109 (heat index
    to 111); Saturday high ~110 (heat index to 112), then showers/tstorms likely
    after 2pm (60%); Sunday ~106 with a chance of storms.
Numbers on the card: 110° Saturday (the weekend peak) and 109° today, heat index
to 112°. All within what NWS published; nothing rounded up.
"""
from render_card import build_card, render

CARDS = [
    # Slide 1 — the safety alert (terracotta, urgent).
    dict(slug="heat-warning-2026-07-24", theme="terracotta",
         kicker="Extreme Heat Warning",
         headline="110° Saturday. Treat it as dangerous.",
         dek=("An Extreme Heat Warning is in effect across metro Tucson through "
              "8 p.m. Saturday — 109° today, 110° Saturday, with a heat index up "
              "to 112°. Hydrate now, move outdoor work to early morning, never "
              "leave people or pets in a parked car, and check on older "
              "neighbors. An Air Quality Alert is up too."),
         meta_text="swipe → where our forecast comes from"),
    dict(slug="heat-warning-2026-07-24-fb", theme="terracotta", size=(1200, 1200),
         kicker="Extreme Heat Warning",
         headline="110° Saturday. Treat it as dangerous.",
         dek=("An Extreme Heat Warning is in effect across metro Tucson through "
              "8 p.m. Saturday — 109° today, 110° Saturday, with a heat index up "
              "to 112°. Hydrate now, move outdoor work to early morning, never "
              "leave people or pets in a parked car, and check on older "
              "neighbors. An Air Quality Alert is up too."),
         meta_text="Check on your neighbors"),
    # Slide 2 — BTS: where the number comes from.
    dict(slug="heat-howweknow-2026-07-24", theme="light",
         kicker="How we know",
         headline="Straight from the source.",
         dek=("There’s no TV-weather middleman here. Every morning we pull "
              "Tucson’s forecast and active alerts directly from the National "
              "Weather Service’s free public API — the government’s own data, "
              "pinned to a spot downtown. This warning came from NWS Tucson at "
              "2:13 a.m. today."),
         meta_text="tucsondailybrief.com"),
    dict(slug="heat-howweknow-2026-07-24-fb", theme="light", size=(1200, 1200),
         kicker="How we know",
         headline="Straight from the source.",
         dek=("There’s no TV-weather middleman here. Every morning we pull "
              "Tucson’s forecast and active alerts directly from the National "
              "Weather Service’s free public API — the government’s own data, "
              "pinned to a spot downtown. This warning came from NWS Tucson at "
              "2:13 a.m. today."),
         meta_text="tucsondailybrief.com"),
]

if __name__ == "__main__":
    for c in CARDS:
        slug = c.pop("slug")
        size = c.pop("size", None)
        print(f"rendering {slug} ...")
        render(slug, build_card(size=size, **c), size=size)
    print("done.")
