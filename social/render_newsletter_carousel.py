#!/usr/bin/env python3
"""
TDB Instagram carousel — the free Sunday newsletter + how the Tucson Mini
crossword gets made, explained for a general (non-technical) audience.

Cover (terracotta) -> "how we do it" steps (light) -> CTA (terracotta).
Reuses the generic slide renderer + theme/render() from the feature carousel.

Usage:
    .venv/bin/python3 social/render_newsletter_carousel.py

Output: social/cards/newsletter-NN-<slug>.png  (1080x1350 each)
"""
from render_card import render
from render_feature_carousel import slide_html

# Each slide: theme, kicker, headline, dek (+ optional swipe/cta flags).
# Copy is deliberately plain-language and factually faithful to the real
# pipeline — Tucson-vocabulary-first wordbank, computer-built 5x5 grid, AI-drafted
# clues under strict no-fabrication rules, human review before it ships.
SLIDES = [
    dict(slug="cover", theme="terracotta",
         kicker="Every Sunday",
         headline="A free newsletter.\nA free crossword.",
         dek="Each week we put together a free newsletter on what’s happening "
             "around town — then build an original Tucson-themed mini crossword "
             "to go with it. Here’s how we do it.",
         swipe=True),

    dict(slug="newsletter", theme="light",
         kicker="TDB Weekly",
         headline="The week, the way a friend would tell it.",
         dek="Not a wall of headlines — a warm Sunday-morning read that catches "
             "you up on the stories that actually mattered around Tucson. Always free."),

    dict(slug="tucson-first", theme="light",
         kicker="Step 1 · Tucson first",
         headline="It starts with\nTucson itself.",
         dek="Every puzzle is built from a hand-picked list of local words — "
             "saguaros, monsoons, the U of A, Sonoran food, and street and place "
             "names — with a nod to the week’s news mixed in."),

    dict(slug="grid", theme="light",
         kicker="Step 2 · The grid",
         headline="The grid fits\nitself together.",
         dek="A computer interlocks those words into a tidy 5×5 grid, always "
             "reaching for the most unmistakably-Tucson answers it can."),

    dict(slug="clues", theme="light",
         kicker="Step 3 · The clues",
         headline="AI writes the clues — with a local wink.",
         dek="We use AI to draft clever, Tucson-flavored clues under two hard "
             "rules: never invent a fact, and never fake a local reference."),

    dict(slug="review", theme="light",
         kicker="Step 4 · The human",
         headline="Then a person\nchecks every word.",
         dek="A real human reviews the whole puzzle before it goes out — "
             "fact-checking each clue. Getting it right matters more than getting "
             "it fast."),

    dict(slug="cta", theme="terracotta",
         kicker="Join us",
         headline="Get it free,\nevery Sunday.",
         dek="Subscribe to the free TDB Weekly newsletter — the crossword link "
             "lives inside, just for readers. Always free. Link in bio.",
         cta=True),
]


if __name__ == "__main__":
    total = len(SLIDES)
    for i, s in enumerate(SLIDES, 1):
        slug = f"newsletter-{i:02d}-{s['slug']}"
        print(f"rendering {slug} ...")
        render(slug, slide_html(s, i, total))
    print(f"done. {total} slides -> social/cards/newsletter-*.png")
