#!/usr/bin/env python3
"""
TDB Instagram carousel — "Buried in the Agenda": the July 14, 2026 Pima County
Board of Supervisors meeting, for a general audience. The IG-feed sibling of
the weekly YouTube auto-short (same franchise, hand-reviewed copy).

Dark investigative cover -> light item slides (the five strongest agenda items
+ the monsoon/flood-control tie-in) -> dark BTS/CTA closer. Reuses the generic
slide renderer + themes/render() from the feature carousel.

Copy is factually faithful to agenda-watch/pima-county-2026-07-14-preview.md
(generated 2026-07-09 from the Legistar packet). All votes are framed as
pending ("will vote on", "recommends") — nothing is asserted as decided.

Usage:
    .venv/bin/python3 social/render_agenda_carousel.py

Output: social/cards/agenda-0714-NN-<slug>.png  (1080x1350 each)
"""
from render_card import render
from render_feature_carousel import slide_html

# Each slide: theme, kicker, headline, dek (+ optional swipe/cta flags).
SLIDES = [
    dict(slug="cover", theme="dark",
         kicker="Buried in the Agenda",
         headline="60 items on\nTuesday's county\nagenda. We read\nevery one.",
         dek="The Pima County Board of Supervisors meets Tuesday, July 14. "
             "Here's what's in the packet — including what could pass with "
             "zero discussion.",
         swipe=True),

    dict(slug="nonprofits", theme="light",
         kicker="Item 26 · Up for a vote",
         headline="A 61% cut to\nthe safety net.",
         dek="Local nonprofits asked the county for $10.1 million next year. "
             "The committee recommends $3.9 million — deep cuts for the "
             "Community Food Bank and Emerge's domestic-abuse services, and "
             "zero for several programs. The board votes Tuesday."),

    dict(slug="borderwall", theme="light",
         kicker="Item 24",
         headline="A formal stand\nagainst the\nborder wall.",
         dek="Supervisors will vote on a resolution opposing the executive "
             "order to build a border wall through the Tohono O'odham "
             "Nation's land, which straddles the U.S.–Mexico border for "
             "roughly 75 miles."),

    dict(slug="vacancies", theme="light",
         kicker="Items 21 & 22",
         headline="Two of the\ncounty's top jobs,\nopen at once.",
         dek="The board will appoint a new County Treasurer — the office "
             "that manages billions in public funds — and decide how to run "
             "the search for the next County Administrator, who runs "
             "day-to-day county government."),

    dict(slug="rescue", theme="light",
         kicker="Item 23",
         headline="Search & rescue.\nFunding source:\nto be determined.",
         dek="A $100,000 renewal for the Southern Arizona Rescue Association "
             "— the crews who find lost hikers in the backcountry — lists "
             "its funding source as “to be identified.” An unusual "
             "catch worth watching."),

    dict(slug="consent", theme="light",
         kicker="Item 28 · Consent calendar",
         headline="Hundreds of new\nhomes, possibly\nzero discussion.",
         dek="A wastewater-boundary change letting Marana extend sewer "
             "service to Saguaro Bloom sits on the consent calendar — where "
             "it could be approved without any public comment or debate."),

    dict(slug="flood", theme="light",
         kicker="Items 10–12 · Flood control",
         headline="After the weekend\nstorms, flood\nvotes on cue.",
         dek="Supervisors will consider buying 28.86 acres of flood-prone "
             "land along Brawley Wash for $555,000 — part of a multi-year "
             "push against exactly the kind of flooding Tucson saw Saturday "
             "night."),

    dict(slug="cta", theme="dark",
         kicker="How we found this",
         headline="Our software reads\nevery page.",
         dek="Every agenda, every packet, every week — scanned automatically "
             "and analyzed by AI, so nothing slips by unnoticed. The full "
             "preview of Tuesday's meeting is free at tucsondailybrief.com "
             "— link in bio.",
         cta=True),
]


if __name__ == "__main__":
    total = len(SLIDES)
    for i, s in enumerate(SLIDES, 1):
        slug = f"agenda-0714-{i:02d}-{s['slug']}"
        print(f"rendering {slug} ...")
        render(slug, slide_html(s, i, total))
    print(f"done. {total} slides -> social/cards/agenda-0714-*.png")
