#!/usr/bin/env python3
"""
Tucson fiber-deal social pair for 2026-07-29.

Two slides, each in IG 4:5 (1080x1350) + a crop-proof FB square (1200x1200):
  1. The news — fiber is coming, plainly and positively.
  2. "We read the agenda so you don't have to" — warm BTS, which over-indexes
     on TDB's IG (IG-BTS-STRATEGY).

Keep this copy LIGHT. A first pass put the verification trail on the cards
themselves — resolution numbers, the emergency clause, and a whole slide
separating the public record from the press release. It read as a memo, and the
second slide read as cynical. Instagram is a positive platform; the detail
belongs in the caption, which is also what SOCIAL-CARDS.md already says
("source attribution lives in the caption, not on the card").

VERIFICATION (2026-07-29). Two tiers, and the cards keep them apart:

  CONFIRMED from the City of Tucson's own agenda, which we mined on 2026-07-15
  into agenda-watch/tucson-2026-07-21-full.md:
    "FIBER TO THE PREMISES LICENSE AGREEMENT FOR USE OF THE PUBLIC RIGHT-OF-WAY
     - WYYERD CONNECT, LLC PROJECT (CITY WIDE) ... Resolution No. 24150 relating
     to Transportation and Information Technology; approving and authorizing
     execution of a Fiber to the Premises License Agreement with Wyyerd Connect,
     LLC for Construction and Installation of Fiber Optic Network Infrastructure
     within the City of Tucson Public Right-of-Way; and declaring an emergency."
    Approved at the July 21 Regular Meeting. Note the legal entity is "Wyyerd
    Connect, LLC" -- "Wyyerd Fiber" is the brand name used in marketing.

  COMPANY CLAIMS, not independently verified. "More than $200 million over five
  years," "zero cost to taxpayers," "Arizona's fastest," "8 GIG" all trace to a
  single joint announcement from the city and the company. The wire copies
  (pr-inside, tennesseedaily) and wyyerd.com are the same release syndicated --
  three outlets, one source. KVOA's story carries the same figures.
  So: the $200M is attributed on the card, and the superlatives are not used as
  fact anywhere.

Deliberately NOT on the cards: "Arizona's fastest," "8 GIG," and any speed
claim. Unverifiable marketing.
"""
from render_card import build_card, render

NEWS_KICKER = "Good news"
NEWS_HEAD = "Fiber internet is coming to Tucson."
NEWS_DEK = (
    "The city just cleared the way for Wyyerd to run fiber-optic lines through "
    "Tucson neighborhoods — city-wide. The company says it’s putting in more "
    "than $200 million over five years, at no cost to taxpayers."
)

BTS_KICKER = "How we found it"
BTS_HEAD = "We read the agenda so you don’t have to."
BTS_DEK = (
    "This one was item “b” on a July 21 council agenda, tucked under a "
    "communication number. No press conference. That’s where most Tucson news "
    "actually lives — and reading it every morning is the whole job."
)

CARDS = [
    dict(slug="fiber-2026-07-29", theme="light",
         kicker=NEWS_KICKER, headline=NEWS_HEAD, dek=NEWS_DEK,
         meta_text="swipe →"),
    dict(slug="fiber-2026-07-29-fb", theme="light", size=(1200, 1200),
         kicker=NEWS_KICKER, headline=NEWS_HEAD, dek=NEWS_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="fiber-checked-2026-07-29", theme="terracotta",
         kicker=BTS_KICKER, headline=BTS_HEAD, dek=BTS_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="fiber-checked-2026-07-29-fb", theme="terracotta", size=(1200, 1200),
         kicker=BTS_KICKER, headline=BTS_HEAD, dek=BTS_DEK,
         meta_text="tucsondailybrief.com"),
]

if __name__ == "__main__":
    for c in CARDS:
        slug = c.pop("slug")
        size = c.pop("size", None)
        print(f"rendering {slug} ...")
        render(slug, build_card(size=size, **c), size=size)
    print("done.")
