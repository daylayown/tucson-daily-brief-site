#!/usr/bin/env python3
"""
Tucson fiber-deal social pair for 2026-07-29.

Two slides, each in IG 4:5 (1080x1350) + a crop-proof FB square (1200x1200):
  1. The news — what the Mayor and Council actually approved.
  2. "What's confirmed, what's the pitch" — separating the public record from
     the press release. BTS/how-we-know framing performs well for TDB
     (IG-BTS-STRATEGY), and here it doubles as the accountability angle.

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

NEWS_KICKER = "City of Tucson"
NEWS_HEAD = "Tucson opened its streets to a fiber build."
NEWS_DEK = (
    "On July 21 the Mayor and Council approved Resolution 24150 — a license "
    "letting Wyyerd Connect, LLC install fiber-optic infrastructure in the "
    "city’s public right-of-way, city-wide. It passed with an emergency clause, "
    "so it took effect immediately rather than after the usual waiting period. "
    "The company says it will invest more than $200 million over five years at "
    "no cost to taxpayers."
)

BTS_KICKER = "What we checked"
BTS_HEAD = "The record, and the pitch."
BTS_DEK = (
    "The agreement is public and specific — we read it in the city’s own July 21 "
    "agenda: Resolution 24150, Wyyerd Connect, LLC, city-wide right-of-way. "
    "The headline numbers are a different thing. “$200 million,” “zero cost to "
    "taxpayers” and “Arizona’s fastest” all trace to one joint announcement from "
    "the city and the company. Both can be true — they aren’t the same kind of "
    "fact, and we’ll keep telling you which is which."
)

CARDS = [
    dict(slug="fiber-2026-07-29", theme="light",
         kicker=NEWS_KICKER, headline=NEWS_HEAD, dek=NEWS_DEK,
         meta_text="swipe → what we could confirm"),
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
