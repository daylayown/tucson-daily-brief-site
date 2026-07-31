#!/usr/bin/env python3
"""
"Tucson Words" #1 — the stravenue. Evergreen local-vocabulary pair, 2026-07-27.

Two slides per house convention, each in IG 4:5 (1080x1350) + a crop-proof FB
square (1200x1200):
  1. Terracotta identity card — what a stravenue is (statement/identity =
     terracotta per SOCIAL-CARDS.md).
  2. Light "How we know" BTS card — the national data check behind the claim.
     (BTS/how-it's-made over-indexes on TDB's IG; see IG-BTS-STRATEGY.md.)

FACTS VERIFIED 2026-07-27 — nothing here is second-hand:

  - USPS Publication 28, Appendix C1 (pe.usps.com/text/pub28/28apc_002.htm),
    fetched directly: primary suffix name "STRAVENUE", standard abbreviation
    "STRA", accepted variants STRAV / STRAVEN / STRAVN / STRVN / STRVNUE.

  - Census Bureau TIGERweb, Transportation MapServer, layer 8 "Local Roads"
    (the national local-road file), queried with WHERE SUFTYPEABRV='Stra':
        count           = 52 road segments
        distinct NAMEs  = 43
        national extent = lat 31.401-32.363, lon -111.084 to -109.779
    Layers 2 (Primary Roads) and 6 (Secondary Roads): 0 hits. So every
    stravenue in the United States sits inside that southern-Arizona box.
    Reverse-geocoded outliers: N Cerius Stra -> Marana/Pima County; N Lead
    Stra (31.4018, -109.7797) -> Cochise County. Everything else is metro
    Tucson.

  - OpenStreetMap/Nominatim, independent cross-check: all 50 returned
    "stravenue" results are in Arizona.

WHY THE COPY HEDGES: "only in Tucson" is the popular claim and it is very
slightly false -- one stravenue is in Marana and one is out in Cochise County.
"every single one is in southern Arizona" is literally true, defensible from
the Census pull above, and lands harder anyway. Do not tighten it back to
"only in Tucson" (see the no-fabrication bar, feedback_ai_content_quality_bar).

Origin detail deliberately left OFF the cards: the term appears on a Feb 1948
Country Club Park plat map by surveyor Tony A. Blanton, but sourcing only says
he "likely" coined it. Fine for a caption with a hedge; not card-worthy.
"""
from render_card import build_card, render

HEADLINE_1 = "Neither a street nor an avenue."
DEK_1 = (
    "A stravenue runs diagonally across Tucson’s grid, cutting between the "
    "east–west streets and the north–south avenues. The U.S. Postal "
    "Service keeps an official abbreviation for it — STRA. There are 43 of "
    "them, and every single one is in southern Arizona."
)

HEADLINE_2 = "We counted every one."
DEK_2 = (
    "We ran the Census Bureau’s national road file — every local road "
    "in the United States — and filtered on the ‘Stra’ suffix. It "
    "returns 52 road segments and 43 distinct names, all of them in Arizona. "
    "Almost all are in Tucson; one is in Marana, one out in Cochise County. The "
    "postal abbreviation is in USPS Publication 28."
)

CARDS = [
    # Slide 1 — identity / the fact.
    dict(slug="stravenue-2026-07-27", theme="terracotta",
         kicker="Tucson Words",
         headline=HEADLINE_1, dek=DEK_1,
         meta_text="swipe → how we checked"),
    dict(slug="stravenue-2026-07-27-fb", theme="terracotta", size=(1200, 1200),
         kicker="Tucson Words",
         headline=HEADLINE_1, dek=DEK_1,
         meta_text="tucsondailybrief.com"),
    # Slide 2 — BTS: the verification.
    dict(slug="stravenue-howweknow-2026-07-27", theme="light",
         kicker="How we know",
         headline=HEADLINE_2, dek=DEK_2,
         meta_text="tucsondailybrief.com"),
    dict(slug="stravenue-howweknow-2026-07-27-fb", theme="light", size=(1200, 1200),
         kicker="How we know",
         headline=HEADLINE_2, dek=DEK_2,
         meta_text="tucsondailybrief.com"),
]

if __name__ == "__main__":
    for c in CARDS:
        slug = c.pop("slug")
        size = c.pop("size", None)
        print(f"rendering {slug} ...")
        render(slug, build_card(size=size, **c), size=size)
    print("done.")
