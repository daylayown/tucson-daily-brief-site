#!/usr/bin/env python3
"""
Metro municipal primary results carousel — 2026-07-22 (AZ primary was July 21).

Scope: Tucson-metro MUNICIPAL contests only, per request. Note the City of
Tucson has NO 2026 election — it votes in odd years (next 2027) — so the
municipal races that actually ran are Oro Valley and Marana. The governor
race (Biggs) is intentionally excluded.

Every figure is UNOFFICIAL initial/partial returns from election night;
Pima County does not canvass until ~July 27, so cards say "leads", never
"won". Facts verified 2026-07-22 against KOLD's Pima County results roundup
and the Tucson Sentinel 2026 town-races guide; City-of-Tucson timing
confirmed via tucsonaz.gov Elections + Ballotpedia. Council seats with
sub-2-point margins are described as "too close to call", not named as
winners.
"""
from render_card import build_card, render

SLIDES = [
    # --- Slide 1: Oro Valley — Barrett (mayor) clear; council 3rd seat close ---
    dict(slug="election-2026-07-22-orovalley", theme="light",
         kicker="Oro Valley · Unofficial results",
         headline="Barrett leads in Oro Valley",
         dek="Melanie Barrett leads the race for Oro Valley mayor with about "
             "57% in early, unofficial returns. For the three Town Council "
             "seats, Rosa Dailey and Rhonda Piña lead, with the third seat "
             "still too close to call. Nothing is official until Pima County "
             "canvasses on July 27.",
         meta_text="swipe → Marana"),

    # --- Slide 2: Marana — Post (incumbent mayor) clear; council a dead heat ---
    dict(slug="election-2026-07-22-marana", theme="light",
         kicker="Marana · Unofficial results",
         headline="Post leads in Marana",
         dek="Incumbent Mayor Jon Post leads with about 54% in early, "
             "unofficial returns. The four-seat Town Council race is a dead "
             "heat — six candidates within about two points — and remains too "
             "close to call. Results aren’t official until the July 27 canvass.",
         meta_text="swipe → how we cover it"),

    # --- Slide 3: terracotta BTS closer — the local-first thesis ---
    dict(slug="election-2026-07-22-howwecover", theme="terracotta",
         kicker="How we cover it",
         headline="We watch the races the TV skips.",
         dek="The governor’s race got the airtime. But it’s your mayor, your "
             "council, and your local ballot measures that decide how your "
             "town actually runs — so that’s what we lead with. Local first, "
             "every morning.",
         meta_text="tucsondailybrief.com"),
]

if __name__ == "__main__":
    for c in SLIDES:
        slug = c.pop("slug")
        render(slug, build_card(**c))
