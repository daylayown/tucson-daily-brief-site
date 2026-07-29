#!/usr/bin/env python3
"""
Announcement cards for the brief's new "What Your Officials Are Saying" section.

Three slides, each IG 4:5 (1080x1350) + crop-proof FB square (1200x1200):
  1. The news — the section exists, here is what is in it.
  2. Why — they publish constantly and almost nobody reads it.
  3. The rule — if one side of a competitive race is silent, the brief says so.
     Closes with the interactivity beat.

Framing per IG-BTS-STRATEGY: lead with what the reader GETS, never with the
scraper. Nothing here mentions parsers, cron, or HTML. Per MARKETING.md's
editorial register, this is a warm product announcement, not a lecture about
civic disengagement — "almost nobody reads it" is a fact about volume, not a
scold aimed at the reader.

Slide 3 carries the interactivity beat (SOCIAL-CARDS.md): the prompt has to be
answerable from the reader's own life. "What would you want to ask them?" works;
"which district are you in?" was rejected — it reads as a quiz and the readers
who don't know would feel caught out.

FACTS, all verified 2026-07-29 while building officials_watch.py:
  - Coverage: Sens. Kelly and Gallego, Reps. Ciscomani (CD6) and Grijalva (CD7),
    Gov. Hobbs. Tucson metro spans both CD6 and CD7, so "both members of
    Congress" is accurate for this audience.
  - Publishing cadence: Ciscomani posted Jul 24, 23, 22, 17, 16; Grijalva Jul 22,
    20, 14, 10; Kelly through Jul 28; Gallego through Jul 23. "Several times a
    week" is conservative.
  - The pairing rule triggers only where Cook Political Report rates a race
    competitive — governor and CD6 are toss-ups. The card says "rated
    competitive" rather than naming Cook, which belongs in the caption.
Deliberately NOT on the cards: candidate names, poll numbers, party labels. This
is an announcement about how the brief works, not election coverage, and putting
a toss-up race's names on a promo card invites a fight we have no reason to pick.
"""
from render_card import build_card, render

NEWS_KICKER = "New in the brief"
NEWS_HEAD = "What your officials are saying."
NEWS_DEK = (
    "The daily brief has a new section: press releases from the people who "
    "represent Tucson — both senators, both members of Congress, and the "
    "governor. Every morning, in plain language."
)

WHY_KICKER = "Why we built it"
WHY_HEAD = "They publish constantly. It mostly goes unread."
WHY_DEK = (
    "Your representatives put out releases several times a week — funding, "
    "legislation, things that actually land in Tucson. Most of it never reaches "
    "anyone outside a press list. Now it will."
)

RULE_KICKER = "One rule"
RULE_HEAD = "If one side goes quiet, we say so."
RULE_DEK = (
    "In races rated competitive we carry both candidates — and when one campaign "
    "posts and the other doesn’t, the brief says that out loud. Silence isn’t the "
    "same as balance. What would you want to ask your rep? Tell us 👇"
)

CARDS = [
    dict(slug="officials-2026-07-30", theme="light",
         kicker=NEWS_KICKER, headline=NEWS_HEAD, dek=NEWS_DEK,
         meta_text="swipe →"),
    dict(slug="officials-2026-07-30-fb", theme="light", size=(1200, 1200),
         kicker=NEWS_KICKER, headline=NEWS_HEAD, dek=NEWS_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="officials-why-2026-07-30", theme="terracotta",
         kicker=WHY_KICKER, headline=WHY_HEAD, dek=WHY_DEK,
         meta_text="swipe →"),
    dict(slug="officials-why-2026-07-30-fb", theme="terracotta", size=(1200, 1200),
         kicker=WHY_KICKER, headline=WHY_HEAD, dek=WHY_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="officials-rule-2026-07-30", theme="light",
         kicker=RULE_KICKER, headline=RULE_HEAD, dek=RULE_DEK,
         meta_text="tucsondailybrief.com"),
    dict(slug="officials-rule-2026-07-30-fb", theme="light", size=(1200, 1200),
         kicker=RULE_KICKER, headline=RULE_HEAD, dek=RULE_DEK,
         meta_text="tucsondailybrief.com"),
]

if __name__ == "__main__":
    for c in CARDS:
        slug = c.pop("slug")
        size = c.pop("size", None)
        print(f"rendering {slug} ...")
        render(slug, build_card(size=size, **c), size=size)
    print("done.")
