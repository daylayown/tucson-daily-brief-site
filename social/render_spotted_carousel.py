#!/usr/bin/env python3
"""
TDB Instagram carousel — behind the scenes on the "Spotted" beat: how new bars
and restaurants get surfaced from buried government agendas before anyone else
reports them, for a general (non-technical) audience.

Cover (terracotta) -> "how it's made" steps (light) -> a real this-week payoff
slide naming the four filings surfaced 2026-07-09 -> CTA (terracotta). Reuses the
generic slide renderer + theme/render() from the feature carousel.

Copy is factually faithful to the real pipeline (public_record_liquor.py): each
week the agenda packets are scanned, Claude extracts every liquor-license filing
(business, address, series, action), and each publishes to the Spotted section.
The four names on the payoff slide are pulled verbatim from the filings published
2026-07-09 for the Pima County Board of Supervisors' July 14, 2026 agenda, and are
framed as *applications/filings* — NOT confirmed openings (recency guardrail).

Usage:
    .venv/bin/python3 social/render_spotted_carousel.py

Output: social/cards/spotted-NN-<slug>.png  (1080x1350 each)
"""
from render_card import render
from render_feature_carousel import slide_html

# Each slide: theme, kicker, headline, dek (+ optional swipe/cta flags).
SLIDES = [
    dict(slug="cover", theme="terracotta",
         kicker="Behind the scenes",
         headline="How we spot new\nbars & restaurants\nbefore anyone\nreports them.",
         dek="Every new spot leaves a paper trail in a government agenda. "
             "Here’s how we catch it.",
         swipe=True),

    dict(slug="license", theme="light",
         kicker="Step 1 · The paper trail",
         headline="It starts with\na liquor license.",
         dek="Before a new restaurant or bar can open in Pima County, it has to "
             "apply for a liquor license — and that application lands on a public "
             "government agenda first."),

    dict(slug="agenda", theme="light",
         kicker="Step 2 · The agenda",
         headline="We read the\nwhole packet.",
         dek="Every week our software pulls the full Board of Supervisors agenda "
             "packet — the kind of dense document almost nobody actually opens."),

    dict(slug="extract", theme="light",
         kicker="Step 3 · The catch",
         headline="AI digs out\nthe filings.",
         dek="Claude reads the packet and pulls every liquor-license filing buried "
             "inside — the business name, the address, and exactly what’s being "
             "applied for."),

    dict(slug="thisweek", theme="light",
         kicker="Up for a vote · July 14",
         headline="Four filings,\nspotted.",
         dek="Frida American Brasserie (Skyline Dr) · Ragazzi Northern Italian "
             "Cuisine (Green Valley) · Talamazka (Green Valley) · QuikTrip on "
             "W. Ajo Hwy — all newly filed, none reported anywhere else."),

    dict(slug="cta", theme="terracotta",
         kicker="See it first",
         headline="What’s opening\nnear you.",
         dek="New filings as we surface them, in the Spotted section at "
             "tucsondailybrief.com — link in bio.",
         cta=True),
]


if __name__ == "__main__":
    total = len(SLIDES)
    for i, s in enumerate(SLIDES, 1):
        slug = f"spotted-{i:02d}-{s['slug']}"
        print(f"rendering {slug} ...")
        render(slug, slide_html(s, i, total))
    print(f"done. {total} slides -> social/cards/spotted-*.png")
