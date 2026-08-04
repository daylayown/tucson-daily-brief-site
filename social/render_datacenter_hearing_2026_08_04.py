#!/usr/bin/env python3
"""
Tucson data-center ordinance hearing — social package for 2026-08-04.

Two slides, each IG 4:5 (1080x1350) + a crop-proof FB square (1200x1200):
  1. The hook — Tucson sets its data-center rules Wednesday; you can speak.
  2. The CTA/ask — "What do you think about data centers?" (user's call:
     simple and direct beats clever).

Promotes: meeting-watch/tucson-council-2026-08-05.html (What to Watch preview).
This is What-to-Watch content on TDB's established Data Center Watch beat —
forward-looking, time-sensitive (hearing is the evening after posting).

COPY RULE (SOCIAL-CARDS.md, "Card copy vs. caption"): cards are hooks — a big
claim and one short line. The caption carries the ordinance number, the stakes,
the meeting details and the link. Cards and caption must not duplicate.

VERIFICATION (2026-08-04). Everything on the cards, and where it comes from:

  SOLID — meeting date/time. Official agenda (mined to
    agenda-watch/tucson-2026-08-05-full.md, line 9): "WEDNESDAY, AUGUST 5,
    2026 - 5:30 PM".

  SOLID — it's a public hearing on data-center regulations. Agenda item 8:
    "PUBLIC HEARING: REGULATIONS FOR LARGE-SCALE DATA CENTERS / UNIFIED
    DEVELOPMENT CODE AMENDMENT - C8-25-04 (CITY WIDE)", Ordinance No. 12268,
    amending UDC sections 4.9.11 and 11.3.11.

  SOLID — "you can speak": it is agendized as a PUBLIC HEARING, and the agenda
    carries the standing call-to-the-audience provision. Card says only "You
    can speak" — no claims about sign-up mechanics, time limits, or format.

Deliberately NOT on the cards: any characterization of what the ordinance
does (water thresholds, cooling requirements, siting rules — the staff-report
details are unverified; our own preview flags exactly that gap); any claim
about specific proposals or which companies want to build. The caption sticks
to the same line: the city is setting the rules, here's when, here's where to
read more.

Usage:
    .venv/bin/python3 social/render_datacenter_hearing_2026_08_04.py
"""
from render_card import build_card, render

KICKER = "What to Watch"

# CALIBRATION (user, 2026-08-04): the one-line deks were "too bare bones."
# The card is still a hook, not a summary — but the dek should carry 2-3
# concrete details (the stakes, the specifics, the when). The caption then
# carries DIFFERENT material: ordinance/item numbers, background, what's
# still unknown, the link. Card and caption must not repeat each other.

HOOK_HEAD = "Data centers: Tucson sets the rules Wednesday."
HOOK_DEK = (
    "A citywide zoning change decides where large-scale data centers can be "
    "built — in a city already planning for Colorado River cuts. Public "
    "hearing at Mayor & Council, 5:30 p.m. You can speak."
)

ASK_HEAD = "What do you think about data centers?"
ASK_DEK = (
    "Jobs and tax base? Water and power strain? Both? Tucson is about to "
    "write the rules — tell us where you land 👇"
)

CARDS = [
    dict(slug="datacenter-hearing-2026-08-04", theme="light",
         kicker=KICKER, headline=HOOK_HEAD, dek=HOOK_DEK,
         meta_text="swipe →"),
    dict(slug="datacenter-hearing-2026-08-04-fb", theme="light", size=(1200, 1200),
         kicker=KICKER, headline=HOOK_HEAD, dek=HOOK_DEK,
         meta_text="tucsondailybrief.com"),

    dict(slug="datacenter-ask-2026-08-04", theme="terracotta",
         kicker=KICKER, headline=ASK_HEAD, dek=ASK_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="datacenter-ask-2026-08-04-fb", theme="terracotta", size=(1200, 1200),
         kicker=KICKER, headline=ASK_HEAD, dek=ASK_DEK,
         meta_text="tucsondailybrief.com"),
]

if __name__ == "__main__":
    for c in CARDS:
        slug = c.pop("slug")
        size = c.pop("size", None)
        print(f"rendering {slug} ...")
        render(slug, build_card(size=size, **c), size=size)
    print("done.")
