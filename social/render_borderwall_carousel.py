#!/usr/bin/env python3
"""
TDB Instagram carousel — "What They Decided": the Pima County Board of
Supervisors' 4-1 vote (Resolution 2026-37) backing the Tohono O’odham
Nation's federal lawsuit against a border wall on its lands, July 14, 2026.

The post-meeting sibling of the "Buried in the Agenda" franchise: that one
previews what's coming, this one reports what happened. Terracotta cover ->
light story slides -> terracotta CTA. Reuses the generic slide renderer +
themes/render() from the feature carousel.

EDITORIAL NOTE — every claim here is verified against two sources:
  - the meeting transcript (transcripts/pima-county-2026-07-14.json), and
  - the Legistar packet (webapi.legistar.com/v1/pima/events/1821/eventitems),
    which supplied the resolution's official title and sponsor.
Non-advocacy framing per the TDB editorial thesis: the vote is reported
neutrally (it was 4-1 — one supervisor dissented), and every claim made by
Chairman Verlan Jose is attributed to him rather than asserted by TDB.
The dissenter is deliberately unnamed: the chair never names them on the
audio record, and Legistar roll calls do not populate until minutes are
approved (expected after the July 28 meeting).

Usage:
    .venv/bin/python3 social/render_borderwall_carousel.py

Output: social/cards/borderwall-0714-NN-<slug>.png  (1080x1350 each)
"""
from render_card import render
from render_feature_carousel import slide_html

SLIDES = [
    dict(slug="cover", theme="terracotta",
         kicker="What they decided",
         headline="Pima County just\nbacked a lawsuit\nagainst Trump’s\nborder wall.",
         dek="On Tuesday night the Board of Supervisors voted 4-1 to support "
             "the Tohono O’odham Nation’s federal case. We were in the "
             "meeting. Here’s what was said.",
         swipe=True),

    dict(slug="vote", theme="light",
         kicker="Resolution 2026-37",
         headline="The vote:\n4 to 1.",
         dek="The resolution formally opposes President Trump’s executive "
             "order to build a wall on the Tohono O’odham Nation’s border "
             "with Mexico, and backs the tribe’s lawsuit against the "
             "Department of Homeland Security. One supervisor voted no."),

    dict(slug="lawsuit", theme="light",
         kicker="Why the nation sued",
         headline="They were still\nnegotiating when\nthe contracts\nmoved.",
         dek="Chairman Verlan Jose told the board the nation filed suit in "
             "federal court in Washington on June 16 after learning DHS was "
             "preparing to award construction contracts — while talks were "
             "still underway."),

    dict(slug="ninetyfive", theme="light",
         kicker="The argument",
         headline="“If no one is\ncrossing, why do\nwe need a\nborder wall?”",
         dek="Jose said the nation spends millions of its own tribal funds on "
             "border security — barriers, patrol roads, sensor towers, "
             "checkpoints, the all-native Shadow Wolves unit — and that "
             "apprehensions on the reservation have fallen more than 95% in "
             "two years, by the federal government’s own data."),

    dict(slug="monument", theme="light",
         kicker="What he told the board",
         headline="“Thousands of\nyears destroyed.”",
         dek="Jose said earlier wall construction blew through Monument Hill "
             "— a marked archaeological burial site — leaving “fragments of "
             "bones scattered all over that mountain.” A tribal monitor had "
             "been assigned to the area, he said, and was sent elsewhere."),

    dict(slug="quitobaquito", theme="light",
         kicker="What’s next",
         headline="Three species\nthat exist\nnowhere else.",
         dek="A planned second wall would hit Quitobaquito Springs in Organ "
             "Pipe Cactus National Monument, Jose said — home to three "
             "endangered species found nowhere else on earth. He said crews "
             "are already working 150 to 200 feet past the 60-foot federal "
             "boundary they said they’d stay within."),

    dict(slug="cta", theme="terracotta",
         kicker="How we covered it",
         headline="We sit in every\nmeeting. All\nthree hours.",
         dek="This one ran past 8:30pm. We transcribe the whole thing, and a "
             "working journalist reviews every word before it publishes. The "
             "full report is free at tucsondailybrief.com — link in bio.",
         cta=True),
]


if __name__ == "__main__":
    total = len(SLIDES)
    for i, s in enumerate(SLIDES, 1):
        slug = f"borderwall-0714-{i:02d}-{s['slug']}"
        print(f"rendering {slug} ...")
        render(slug, slide_html(s, i, total))
    print(f"done. {total} slides -> social/cards/borderwall-0714-*.png")
