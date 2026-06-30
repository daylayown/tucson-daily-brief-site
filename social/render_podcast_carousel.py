#!/usr/bin/env python3
"""
TDB Instagram carousel — behind the scenes on the daily podcast, ending on the
voice-clone reveal, for a general (non-technical) audience.

Cover (terracotta) -> "how it's made" steps (light) -> voice reveal (light)
-> CTA (terracotta). Reuses the generic slide renderer + theme/render() from the
feature carousel.

Copy is factually faithful to the real pipeline: the daily brief is condensed by
Claude to the five biggest stories in broadcast style, then read aloud by an AI
clone of founder Nicholas De Leon's own voice (cloned by him in ElevenLabs), and
auto-published to Apple Podcasts and YouTube. No fabrication — every claim here
is literally true of run_podcast.sh / generate_podcast.py.

Usage:
    .venv/bin/python3 social/render_podcast_carousel.py

Output: social/cards/podcast-NN-<slug>.png  (1080x1350 each)
"""
from render_card import render
from render_feature_carousel import slide_html

# Each slide: theme, kicker, headline, dek (+ optional swipe/cta flags).
SLIDES = [
    dict(slug="cover", theme="terracotta",
         kicker="Behind the scenes",
         headline="How we make a\nTucson news podcast\nevery morning.",
         dek="From overnight headlines to a 90-second listen by sunrise — "
             "here’s the whole pipeline.",
         swipe=True),

    dict(slug="brief", theme="light",
         kicker="Step 1 · The brief",
         headline="First, we gather\nthe day’s news.",
         dek="Every morning the Tucson Daily Brief pulls together what’s "
             "happening across the metro — city, county, Marana, Oro Valley "
             "and beyond."),

    dict(slug="script", theme="light",
         kicker="Step 2 · The script",
         headline="Then AI writes\nthe rundown.",
         dek="We have Claude condense the brief down to the five biggest "
             "stories, written to be read out loud — short, clear, no fluff."),

    dict(slug="voice", theme="light",
         kicker="Step 3 · The voice",
         headline="That voice?\nIt’s not a recording.",
         dek="It’s an AI clone of founder Nicholas De Leon’s voice — made in "
             "ElevenLabs — reading the day’s news. Same voice every morning, "
             "without him ever touching a mic."),

    dict(slug="publish", theme="light",
         kicker="Step 4 · Publish",
         headline="Live before\nyour coffee.",
         dek="The finished episode posts itself to Apple Podcasts and YouTube — "
             "the whole thing runs start to finish on its own."),

    dict(slug="cta", theme="terracotta",
         kicker="Listen free",
         headline="Tucson, in\n90 seconds.",
         dek="A new episode every morning on Apple Podcasts and YouTube — "
             "link in bio.",
         cta=True),
]


if __name__ == "__main__":
    total = len(SLIDES)
    for i, s in enumerate(SLIDES, 1):
        slug = f"podcast-{i:02d}-{s['slug']}"
        print(f"rendering {slug} ...")
        render(slug, slide_html(s, i, total))
    print(f"done. {total} slides -> social/cards/podcast-*.png")
