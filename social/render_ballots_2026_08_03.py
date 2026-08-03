#!/usr/bin/env python3
"""
Pima County early-ballot return rate — social package for 2026-08-03.

Three slides, each IG 4:5 (1080x1350) + a crop-proof FB square (1200x1200):
  1. The hook — 46%, the lowest primary return rate in 30 years.
  2. The explainer — why so many ballots go out in the first place.
  3. The interactivity beat — "Did you vote? Sound off."

Promotes: news-reports/pima-county-2026-08-03-special-meeting.html

WHY SLIDE 2 EXISTS AND IS NOT OPTIONAL. The story's rawest number is that
188,869 ballots were not returned for tabulation — more than the 186,600 people
who voted at all. That number is deliberately NOT on any card. Out of context,
on a platform where nobody clicks through, it reads as an allegation that
ballots went missing, and it would be reposted that way. Slide 2 carries the
Active Early Voting List explanation so the package cannot be misread. If these
cards are ever cut down to one slide, cut slide 3, never slide 2.

VERIFICATION (2026-08-03). Everything on the cards, and where it comes from:

  SOLID — 349,885 issued / 161,016 received and processed. Pima County Elections
    Director Constance Hargrove's canvass memorandum to the Board of
    Supervisors, July 30, 2026 ("The Recorder's office issued 349,885 early
    ballots, of which the elections department received and processed 161,016
    ballots"). Carried as an agenda attachment for the Aug 3 special meeting.

  SOLID — 46%. Computed: 161,016 / 349,885 = 46.02%.

  SOLID — lowest primary in 30 years. Pima County Recorder's published Early
    Voting Statistics table, which runs 1996-present. Next lowest primary is
    2024 at 49.9%; the series has fallen three straight primaries (2020 62.5%,
    2022 54.0%, 2024 49.9%, 2026 46.0%). ⚠️ The comparison is only valid
    because the Recorder's "requested"/"returned" columns are the same two
    measures as the memo's "issued"/"received and processed" — confirmed
    against the 2024 official canvass, where the Recorder's reported 173,614
    "returned" matches the canvass line "Total Ballots Turned Over for
    Tabulation" exactly. Do not reuse this claim without that check.

  SOLID — 28.88% turnout. Same canvass memorandum (186,600 of 646,190).

  SOLID — the Active Early Voting List works as slide 2 describes. A.R.S.
    § 16-544: joining means the Recorder mails a ballot for every election the
    voter is eligible for, by the first day of early voting, unless the voter
    says otherwise at least 45 days ahead; removal only on request, on
    registration going inactive, or after two consecutive election cycles
    without voting an early ballot.

  SOLID — postage-paid. Pima County Recorder, Early Voting page: "Mail your
    ballot back to us in the Postage Paid Yellow Envelope included with your
    ballot... No stamp is needed!"

Deliberately NOT on the cards: the 188,869 figure (see above); any claim about
why returns are falling (we don't know — that's the follow-up story); and any
suggestion that the 16-ballot double-count matters at this scale (it's 0.0086%
of ballots cast and was caught and corrected before certification).

Caption should carry the link and the source attribution — per house
convention, outlet/source names stay off the card face.

Usage:
    .venv/bin/python3 social/render_ballots_2026_08_03.py
"""
from render_card import build_card, render

KICKER = "What They Decided"

# COPY RULE (user, 2026-08-03): the card is a hook, not a summary. Keep it
# breezy and scannable — a big claim and one short line under it. The caption
# carries the numbers, the trend and the mechanism. Cards and caption must NOT
# say the same thing; if the caption would be redundant next to the card, the
# card is doing too much.

HOOK_HEAD = "46%"
HOOK_DEK = "of Pima County’s early ballots came back. Lowest in 30 years."

WHY_HEAD = "Nothing went missing."
WHY_DEK = "The ballot comes whether you asked for it or not."

ASK_HEAD = "Did you vote in July?"
ASK_DEK = "Tell us below 👇"

CARDS = [
    # hsize override: build_card sizes type by headline length, so a 3-character
    # stat lands at long-headline size and reads small. A number card should let
    # the number carry the whole frame.
    dict(slug="ballots-2026-08-03", theme="light", hsize=260,
         kicker=KICKER, headline=HOOK_HEAD, dek=HOOK_DEK,
         meta_text="swipe →"),
    dict(slug="ballots-2026-08-03-fb", theme="light", size=(1200, 1200), hsize=260,
         kicker=KICKER, headline=HOOK_HEAD, dek=HOOK_DEK,
         meta_text="tucsondailybrief.com"),

    dict(slug="ballots-why-2026-08-03", theme="light",
         kicker=KICKER, headline=WHY_HEAD, dek=WHY_DEK,
         meta_text="swipe →"),
    dict(slug="ballots-why-2026-08-03-fb", theme="light", size=(1200, 1200),
         kicker=KICKER, headline=WHY_HEAD, dek=WHY_DEK,
         meta_text="tucsondailybrief.com"),

    dict(slug="ballots-ask-2026-08-03", theme="terracotta",
         kicker=KICKER, headline=ASK_HEAD, dek=ASK_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="ballots-ask-2026-08-03-fb", theme="terracotta", size=(1200, 1200),
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
