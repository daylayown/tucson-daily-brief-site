#!/usr/bin/env python3
"""
A-10 farewell card for 2026-07-30 — community-nostalgia package.

Single card (IG 4:5 + FB square), light theme, typography-led (no news-photo
rights needed). Facts from today's brief, per KOLD: two A-10s made a final
pass over Davis-Monthan on Wednesday (7/29) before landing, ending the
aircraft's 40-plus-year presence at the base. Attribution kept in the dek.

Deliberately warm, zero civic-scold register (feedback_light_heavy_balance).
The interactivity beat is the whole package: everyone in Tucson has an A-10
memory. Note: no "BRRRT" jokes — the gun runs happen at the ranges, not over
midtown, and the military audience will notice.

Captions (copy-paste; FB carries the UTM'd newsletter link):

--- IG caption ---------------------------------------------------------------
After more than 40 years, the A-10 era at Davis-Monthan is over. Two Warthogs
made one final pass over the base Wednesday before landing for the last time,
KOLD reports.

If you grew up here, you never had to look up to know what was flying over.
That silhouette has been Tucson's soundtrack for four decades.

✈️ So let's hear it: what's your A-10 memory? First air show? A flyover you'll
never forget? A family member who turned wrenches on them? Drop it below — we
read every one.

📬 For the Tucson news you'd otherwise miss, the TDB Weekly newsletter lands
every Sunday — link in bio to subscribe.

#Tucson #DavisMonthan #A10 #Warthog #TucsonHistory

--- FB caption ---------------------------------------------------------------
After more than 40 years, the A-10 era at Davis-Monthan is over. Two Warthogs
made one final pass over the base Wednesday before landing for the last time,
KOLD reports.

If you grew up here, you never had to look up to know what was flying over.
That silhouette has been Tucson's soundtrack for four decades.

✈️ So let's hear it: what's your A-10 memory? First air show? A flyover you'll
never forget? A family member who turned wrenches on them? Tell us in the
comments — we read every one.

📬 For the Tucson news you'd otherwise miss in one Sunday email, subscribe to
TDB Weekly:
https://tucsondailybrief.com/newsletter.html?utm_source=facebook&utm_medium=post&utm_campaign=tdb-weekly
------------------------------------------------------------------------------
"""
from render_card import build_card, render

A10_DEK = ("Two A-10s made a final pass over Davis-Monthan on Wednesday before "
           "landing for the last time, KOLD reports — closing out more than "
           "four decades of the Warthog in Tucson's sky. If you grew up here, "
           "you never had to look up to know what was flying over.")

CARDS = [
    dict(slug="a10-farewell-2026-07-30", theme="light",
         kicker="End of an era",
         headline="One final pass, after 40 years.",
         dek=A10_DEK,
         meta_text="tell us your A-10 memory ↓"),
    dict(slug="a10-farewell-2026-07-30-fb", theme="light", size=(1200, 1200),
         kicker="End of an era",
         headline="One final pass, after 40 years.",
         dek=A10_DEK,
         meta_text="tell us your A-10 memory ↓"),
]

if __name__ == "__main__":
    for c in CARDS:
        slug = c.pop("slug")
        size = c.pop("size", None)
        print(f"rendering {slug} ...")
        render(slug, build_card(size=size, **c), size=size)
    print("done.")
