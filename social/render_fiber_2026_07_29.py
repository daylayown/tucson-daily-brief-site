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
claim sourced to the company. Unverifiable marketing.

Card 3 speed figures, two different sourcing tiers:
  ARIZONA (solid) -- Ookla state row supplied by the editor: median download
    276.98 Mbps, median upload 53.99, latency 23.72 ms, consistency 91.1%,
    provider column Wyyerd Fiber. Rounded to 277 / 54 on the card.
  US MEDIAN (weaker) -- ~306.86 Mbps, Ookla Speedtest Global Index, May 2026.
    Could NOT be verified against a primary source: speedtest.net, ookla.com,
    and Light Reading are all unfetchable from this environment. Four secondary
    sources agree (Allconnect, Optimum, Ezee Fiber, WorldPopulationReview), all
    ISP-marketing-adjacent. Hedged as "about 307" on the card. Re-verify before
    reusing this number.

Say MEDIAN, never "average" -- Ookla publishes medians, and on speed
distributions a handful of multi-gig lines drag the mean well above what a
typical household sees.

Note the card credits Ookla, not the company, for the fastest-provider line:
the identical claim in the joint press release stays off the cards.
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

SPEED_KICKER = "How fast is yours?"
SPEED_HEAD = "Arizona runs slower than the country."
SPEED_DEK = (
    "Ookla clocks Arizona’s median home connection at 277 Mbps down, 54 up — "
    "under the US median of about 307. The fastest provider in the state: "
    "Wyyerd, the company Tucson just cleared to build here. How fast is yours? "
    "Drop it in the comments 👇"
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
         meta_text="swipe →"),
    dict(slug="fiber-checked-2026-07-29-fb", theme="terracotta", size=(1200, 1200),
         kicker=BTS_KICKER, headline=BTS_HEAD, dek=BTS_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="fiber-speed-2026-07-29", theme="light",
         kicker=SPEED_KICKER, headline=SPEED_HEAD, dek=SPEED_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="fiber-speed-2026-07-29-fb", theme="light", size=(1200, 1200),
         kicker=SPEED_KICKER, headline=SPEED_HEAD, dek=SPEED_DEK,
         meta_text="tucsondailybrief.com"),
]

if __name__ == "__main__":
    for c in CARDS:
        slug = c.pop("slug")
        size = c.pop("size", None)
        print(f"rendering {slug} ...")
        render(slug, build_card(size=size, **c), size=size)
    print("done.")
