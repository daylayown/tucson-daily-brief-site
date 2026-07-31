#!/usr/bin/env python3
"""
Extreme-heat social pair for 2026-07-30.

Two-slide carousel per house convention, each in IG 4:5 (1080x1350) + a
crop-proof FB square (1200x1200), same copy:
  1. Extreme Heat Warning safety card (terracotta)
  2. Cooling-centers service card (light) — the county heat plan has logged
     60,000+ visits (KOLD, via today's brief); pima.gov/heat verified live
     (301 -> "Beat the Heat | Pima County", 43 cooling-center mentions).

Facts verified live 2026-07-30 against the National Weather Service:
  - api.weather.gov/alerts/active?point=32.2226,-110.9747 -> "Extreme Heat
    Warning issued July 30 at 2:57AM MST until August 2 at 8:00PM MST by NWS
    Tucson AZ"; onset 10 AM today; 107-113 in the metro; Major to Extreme
    HeatRisk. NO Air Quality Alert active this time (unlike 7/24 — do not
    mention one).
  - api.weather.gov/gridpoints/TWC/91,49/forecast: Today 109 / Fri 111 /
    Sat 112 / Sun 109; overnight lows 83 / 85 / 86 -> "mid-80s after dark"
    is supported. Nothing rounded up.

Captions (copy-paste; FB carries the UTM'd newsletter link, IG says link
in bio because IG captions don't link):

--- IG caption ---------------------------------------------------------------
An Extreme Heat Warning is in effect from 10 a.m. today through 8 p.m. Sunday:
109° today, 111° Friday, 112° Saturday — and overnight lows only in the
mid-80s, so the desert barely cools off after dark. That's when heat gets
dangerous.

Pima County's cooling centers have logged 60,000+ visits this season. They're
free, air-conditioned, and listed at pima.gov/heat — no reason to tough it out.

Hydrate before you're thirsty, move outdoor work to dawn, never leave anyone —
two- or four-legged — in a parked car, and check on the neighbors who won't
ask for help.

🌡️ What's your beat-the-heat move? Swamp-cooler loyalty? Blackout curtains?
Grocery-store laps? Tell us below.

📬 The TDB Weekly newsletter rounds up the Tucson news you'd otherwise miss,
every Sunday — link in bio to subscribe.

#Tucson #TucsonWeather #ExtremeHeat #PimaCounty #SonoranDesert

--- FB caption ---------------------------------------------------------------
An Extreme Heat Warning is in effect from 10 a.m. today through 8 p.m. Sunday:
109° today, 111° Friday, 112° Saturday — and overnight lows only in the
mid-80s, so the desert barely cools off after dark. That's when heat gets
dangerous.

Pima County's cooling centers have logged 60,000+ visits this season. They're
free, air-conditioned, and listed at pima.gov/heat — no reason to tough it out.

Hydrate before you're thirsty, move outdoor work to dawn, never leave anyone —
two- or four-legged — in a parked car, and check on the neighbors who won't
ask for help.

🌡️ What's your beat-the-heat move? Swamp-cooler loyalty? Blackout curtains?
Grocery-store laps? Tell us in the comments.

📬 Want the week's Tucson news in one Sunday email? Subscribe to TDB Weekly:
https://tucsondailybrief.com/newsletter.html?utm_source=facebook&utm_medium=post&utm_campaign=tdb-weekly
------------------------------------------------------------------------------
"""
from render_card import build_card, render

WARN_DEK = ("An Extreme Heat Warning is in effect from 10 a.m. today through "
            "8 p.m. Sunday — 109° today, 111° Friday, 112° Saturday, with "
            "overnight lows only in the mid-80s. Little relief after dark. "
            "Hydrate early, move outdoor work to dawn, never leave people or "
            "pets in a parked car, and check on older neighbors.")

COOL_DEK = ("Pima County's heat plan has logged more than 60,000 cooling-center "
            "visits this season. If your AC is losing the fight — or the power "
            "bill is — the centers are free and air-conditioned. Locations: "
            "pima.gov/heat. A heat hotline and rides to the centers are in the "
            "works, per the county's update this week.")

CARDS = [
    # Slide 1 — the safety alert (terracotta, urgent).
    dict(slug="heat-warning-2026-07-30", theme="terracotta",
         kicker="Extreme Heat Warning",
         headline="112° Saturday. Four days of this.",
         dek=WARN_DEK,
         meta_text="swipe → free cooling centers near you"),
    dict(slug="heat-warning-2026-07-30-fb", theme="terracotta", size=(1200, 1200),
         kicker="Extreme Heat Warning",
         headline="112° Saturday. Four days of this.",
         dek=WARN_DEK,
         meta_text="Check on your neighbors"),
    # Slide 2 — cooling centers (light, service).
    dict(slug="heat-cooling-2026-07-30", theme="light",
         kicker="Free cooling centers",
         headline="60,000 visits and counting.",
         dek=COOL_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="heat-cooling-2026-07-30-fb", theme="light", size=(1200, 1200),
         kicker="Free cooling centers",
         headline="60,000 visits and counting.",
         dek=COOL_DEK,
         meta_text="tucsondailybrief.com"),
]

if __name__ == "__main__":
    for c in CARDS:
        slug = c.pop("slug")
        size = c.pop("size", None)
        print(f"rendering {slug} ...")
        render(slug, build_card(size=size, **c), size=size)
    print("done.")
