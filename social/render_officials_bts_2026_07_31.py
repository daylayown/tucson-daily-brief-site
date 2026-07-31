#!/usr/bin/env python3
"""
Behind-the-scenes package for "What Your Officials Are Saying" — the election
hook, the machinery, the fairness rule, and where to read it.

Four slides, each IG 4:5 (1080x1350) + crop-proof FB square (1200x1200):
  1. Why now — early ballots hit mailboxes Oct 7.
  2. How — eleven channels, checked every morning.
  3. The fairness rule — written into the code, not promised in a mission statement.
  4. Where to read it. Closes with the interactivity beat.

RELATIONSHIP TO render_officials_2026_07_30.py
That package was the reader-facing *announcement* and deliberately mentioned no
tooling (IG-BTS-STRATEGY: lead with what the reader gets). This one is the BTS
cut the user asked for on 7/31 — same feature, different job. It may repeat the
"silence isn't balance" idea because that is the single best thing about the
feature, but it earns it here by showing the mechanism instead of asserting it.
Do not post the two on the same day.

THE FAIRNESS CLAIM — READ BEFORE EDITING THIS COPY
The honest claim is about the RULE, not a headcount, and the distinction matters
because the headcount version is false and trivially attackable.

Verified against officials_watch.py on 2026-07-31:
  - 10 channels: 7 officeholder (5 press pages + 2 Bluesky feeds) + 3 campaign.
  - Officeholders by PARTY are 4 D / 1 R — Kelly (D), Gallego (D), Grijalva (D),
    Hobbs (D), Ciscomani (R). That is simply who holds the seats. NEVER put a
    "we cover both parties equally" headcount on a card; it is not true and
    invites exactly the fight we don't need.
  - What IS symmetric is RACE_FIELDS: every side of a Cook-rated competitive
    race is named in code, and (since 2026-07-31) every name has a real source
    behind it. Both CD6 candidates and both governor candidates are fetched.
    ⚠️ An earlier draft of this caption said no Ciscomani campaign channel
    existed. That was wrong — juanciscomani.com has an active news section, and
    the missing source was silently marking him "silent" daily. Fixed same day;
    see the LESSON note in officials_watch.py SOURCES.
  - build_block() emits an explicit note when a named candidate posted nothing
    ("do not imply parity by omission").
  - Best detail, and the reason slide 3 exists: a FAILED scraper suppresses the
    silence note and reports "could not check" instead. Our own bug is never
    allowed to become a factual claim that a real person stayed silent.

OTHER FACTS, verified 2026-07-31:
  - Early voting / early-ballot mailing begins Oct 7, 2026; general election is
    Tue Nov 3, 2026 (Arizona Secretary of State). Oct 7 is also the registration
    deadline — deliberately NOT on the card, to keep one date per slide.
  - Window is 48 hours (officials_watch.DEFAULT_WINDOW_HOURS), derived, not assumed.
  - Channel mix: congressional press pages (Kelly, Gallego, Ciscomani, Grijalva),
    the governor's newsroom, campaign sites (Hobbs, Biggs, Mendoza), and two
    Bluesky feeds (Kelly, Gallego).
  - SECTION PLACEMENT: 📢 runs LAST in the brief, after Community & Events;
    Weather runs first. The 7/30 FB caption said it "sits just above the
    weather" — that was wrong. Slide 4 says "at the end of the brief."

Deliberately NOT on these cards: candidate names, party labels, poll numbers,
race ratings. Same reasoning as the 7/30 package — this is about how the brief
works, and naming toss-up candidates on a promo card picks a fight for nothing.

CAPTIONS

Written to ADD to the cards, not restate them. The cards carry the pitch; the
captions carry the specifics the cards deliberately omit — the officials by
name, the "said in a release" rule, what happens on a quiet morning, and the
CD6 campaign-channel asymmetry. Do not paste the card deks in here.

INSTAGRAM
  Your senators and representatives put out a press release every few days.
  Almost none of it ever reaches you. 🗳️

  The Tucson Daily Brief now collects them every morning — Mark Kelly, Ruben
  Gallego, Juan Ciscomani, Adelita Grijalva, Katie Hobbs, plus every campaign in
  the two Arizona races independent raters call competitive.

  Three decisions we made up front:

  → Everything is reported as a claim. "Said in a release," never "did."
  → Some mornings nobody posted anything. On those mornings the section simply
    isn't there. We'd rather skip it than pad it.
  → Both sides of both competitive races get checked by name. If one campaign
    posts and the other doesn't, the brief says so. And if our own scraper
    fails, we report that we couldn't check — never that they said nothing.

  None of that is a promise about our intentions. It's written into the
  software, which is a much harder thing to quietly stop doing.

  Want it once a week instead of every morning? TDB Weekly is free, Sunday
  mornings — link in bio.

  When's the last time you heard from your rep — not *about* them? 👇

  #Tucson #TucsonNews #PimaCounty

FACEBOOK
  There's a whole layer of Tucson news that never actually reaches Tucsonans.

  Your senators and representatives publish constantly — funding awards,
  legislation, disaster declarations, things that land directly in Pima County.
  It goes out to a press list, a few reporters pick through it, and the rest
  evaporates. That's not a conspiracy, it's just how the plumbing works.

  So the Tucson Daily Brief now reads it for you, every morning: Sens. Mark
  Kelly and Ruben Gallego, Reps. Juan Ciscomani and Adelita Grijalva, Gov. Katie
  Hobbs, and the campaigns on both sides of the races rated competitive heading
  into the November 3 election.

  A few things worth saying plainly, since this is election season and you
  should know how the sausage is made:

  Nothing is presented as established fact. If Sen. Kelly announces a grant, the
  brief says he said so in a release. That distinction is the whole ballgame.

  Both candidates in a competitive race get checked by name every morning. If
  one campaign posts and the other doesn't, the brief tells you that, rather
  than running one side and letting the silence look like balance.

  And if our own software fails to reach someone's site that morning, we report
  that we couldn't check it — we won't let a bug on our end turn into a claim
  that a real person had nothing to say.

  It's free, there's no account, and it runs at the end of the brief every
  morning. Prefer a weekly roundup instead? TDB Weekly lands free on Sunday
  mornings — link in the first comment.

  When's the last time you actually heard from your representative — not about
  them, but from them?

FACEBOOK FIRST COMMENT (post this immediately after publishing)
  TDB Weekly — free, Sunday mornings, no account needed:
  https://tucsondailybrief.com/newsletter.html?utm_source=facebook&utm_medium=post&utm_campaign=officials-watch

INSTAGRAM BIO / STORY LINK (same page, IG-tagged so the two don't blur together)
  https://tucsondailybrief.com/newsletter.html?utm_source=instagram&utm_medium=bio&utm_campaign=officials-watch

POSTING NOTES
  - FB: the link goes in the FIRST COMMENT, never the post body — Meta throttles
    in-body links (SOCIAL-AUTOPOST.md). The body says "link in the first
    comment" so the pointer isn't dangling.
  - UTM campaign is `officials-watch`, not `tdb-weekly`: source/medium already
    say where the click came from, so the campaign should name the package that
    earned the signup. Matches the existing `utm_source=facebook&utm_medium=post`
    convention in generate_post.py.
  - IG: 3 hashtags on purpose. The 5-cap is real and local tags outperform;
    don't pad with #arizona / #localnews (SOCIAL-CARDS.md).
  - Channel count is ELEVEN as of 2026-07-31 (Ciscomani's campaign site added).
    Slide 2 was re-rendered to match. If a source is ever added or dropped,
    re-render — a stale number on a card is the easiest kind of error to ship.

⚠️ BEFORE POSTING: the section is skipped on mornings when nobody posted in the
previous 48 hours. Check that day's brief actually carries it.
"""
from render_card import build_card, render

WHY_KICKER = "Why now"
WHY_HEAD = "Early ballots go out October 7."
WHY_DEK = (
    "Arizona's general election is November 3. Between now and then, the people "
    "who represent Tucson will say a great deal about what they intend to do — "
    "most of it in press releases that never get past a press list."
)

HOW_KICKER = "How it works"
HOW_HEAD = "So we built something to read them."
HOW_DEK = (
    "Every morning it checks eleven channels — both senators' and both local "
    "House members' press pages, the governor's newsroom, all four campaign "
    "sites, and their Bluesky feeds — for anything posted in the last 48 hours."
)

FAIR_KICKER = "How we stay fair"
FAIR_HEAD = "Fairness is a rule in the code."
FAIR_DEK = (
    "Every side of a competitive race is named in the software, whether or not "
    "they posted. If one campaign goes quiet, the brief says so — silence "
    "doesn't get to pass as balance. And if our own scraper breaks, we say we "
    "couldn't check, rather than let our bug become “they said nothing.”"
)

WHERE_KICKER = "Where to read it"
WHERE_HEAD = "Every morning. Free."
WHERE_DEK = (
    "“What Your Officials Are Saying” runs at the end of the daily "
    "brief, seven days a week, at tucsondailybrief.com. No paywall, no account. "
    "When's the last time you heard from your representative — not about them? "
    "Tell us 👇"
)

SLIDES = [
    ("officials-why-now", "terracotta", WHY_KICKER, WHY_HEAD, WHY_DEK),
    ("officials-how", "light", HOW_KICKER, HOW_HEAD, HOW_DEK),
    ("officials-fair", "light", FAIR_KICKER, FAIR_HEAD, FAIR_DEK),
    ("officials-where", "terracotta", WHERE_KICKER, WHERE_HEAD, WHERE_DEK),
]

CARDS = []
for i, (slug, theme, kicker, head, dek) in enumerate(SLIDES):
    last = i == len(SLIDES) - 1
    CARDS.append(dict(slug=f"{slug}-2026-07-31", theme=theme, kicker=kicker,
                      headline=head, dek=dek,
                      meta_text="tucsondailybrief.com" if last else "swipe →"))
    CARDS.append(dict(slug=f"{slug}-2026-07-31-fb", theme=theme, size=(1200, 1200),
                      kicker=kicker, headline=head, dek=dek,
                      meta_text="tucsondailybrief.com"))

if __name__ == "__main__":
    for c in CARDS:
        slug = c.pop("slug")
        size = c.pop("size", None)
        print(f"rendering {slug} ...")
        render(slug, build_card(size=size, **c), size=size)
    print("done.")
