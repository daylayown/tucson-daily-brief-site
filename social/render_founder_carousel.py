#!/usr/bin/env python3
"""
TDB Instagram carousel — "the person behind the brief": founder intro post.
Completes the 2026-07-11 rebrand ("... by Nicholas De Leon" masthead) by
putting a face to the byline. One-time exception to the faceless-social
posture, decided by the user 2026-07-12; planned for Friday 2026-07-17.

Cover is a full-bleed photo (social/cards/nicholas.jpeg — gitignored, personal
asset, lives outside the repo history) with a dusk scrim + headline; middle
slides are light; CTA terracotta. Reuses slide_html/render() from the
existing carousel tooling.

All copy is publish-ready: the "who" slide uses the founder's own beats
(supplied 2026-07-12), and the why/how slides are sourced from about.html.

Usage:
    .venv/bin/python3 social/render_founder_carousel.py

Output: social/cards/founder-NN-<slug>.png  (1080x1350 each)
"""
import base64
import html as _html
import os

from render_card import THEMES, FONTS_HREF, SUN_SVG, render, W, H
from render_feature_carousel import slide_html

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(HERE, "cards", "nicholas.jpeg")

# Landscape 4:3 photo into a 4:5 canvas: object-position picks the crop
# window. The subject sits ~64% across the frame; 66% keeps him centered
# with the RV door on the left and the mountains on the right.
PHOTO_POS = "66% 35%"

SLIDES = [
    dict(slug="cover", photo=True, theme="terracotta",
         kicker="Behind the brief",
         headline="Hi, I'm Nicholas.",
         dek="The one person behind the Tucson Daily Brief.",
         swipe=True),

    # Founder's own beats (provided 2026-07-12): 20 years a professional
    # journalist, moved to Tucson in 2023, world travel for work, Arizona the
    # most beautiful place he's been, proud to call Tucson home.
    dict(slug="who", theme="light",
         kicker="Who I am",
         headline="A journalist for\n20 years. A Tucsonan\nsince 2023.",
         dek="Work has taken me all over the world, and Arizona is still the "
             "most beautiful place I've ever been. I moved here in 2023, fell "
             "for the Old Pueblo, and I'm proud to call Tucson home."),

    dict(slug="why", theme="light",
         kicker="Why I make this",
         headline="Tucson deserves\nmore coverage\nthan it gets.",
         dek="A metro of a million people, and most days the news cameras "
             "point at Phoenix. City council votes, county budgets, new "
             "restaurants, buried filings — too much of it just goes "
             "unreported. That's the gap this site exists to fill."),

    dict(slug="how", theme="light",
         kicker="How I make it",
         headline="Software does the\nreading. I do the\njudgment.",
         dek="I built tools that read every agenda, watch every meeting, and "
             "scan public records daily — work no one person could do alone. "
             "What gets published runs on my editorial judgment, and "
             "original reporting is reviewed by me before it goes out."),

    dict(slug="cta", theme="terracotta",
         kicker="Say hi",
         headline="I make this\nfor you.",
         dek="A free daily brief, a 90-second podcast, and a Sunday "
             "newsletter with a Tucson crossword. Reply, comment, send tips "
             "— there's a real person on the other end. Link in bio.",
         cta=True),
]


def _esc(s):
    return _html.escape(s, quote=False)


def photo_cover_html(s, idx, total):
    """Full-bleed photo cover: image, dusk scrim, kicker + headline + footer."""
    t = THEMES[s["theme"]]
    with open(PHOTO, "rb") as f:
        photo_uri = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
    swipe = ('<span class="swipe">swipe '
             '<svg width="34" height="20" viewBox="0 0 34 20" aria-hidden="true">'
             '<path d="M2 10h28M22 3l8 7-8 7" stroke="currentColor" '
             'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
             '</svg></span>')
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS_HREF}">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html,body {{ width:{W}px; height:{H}px; }}
  body {{ background:#251c17; color:#faf4e8;
    font-family:'Newsreader',Georgia,serif; -webkit-font-smoothing:antialiased;
    position:relative; overflow:hidden; }}
  .photo {{ position:absolute; inset:0; width:100%; height:100%;
    object-fit:cover; object-position:{PHOTO_POS}; }}
  /* dusk scrim: keeps the sky/photo clean, grounds the text */
  .scrim {{ position:absolute; inset:0;
    background:linear-gradient(to bottom, rgba(37,28,23,0.30) 0%,
      rgba(37,28,23,0) 26%, rgba(37,28,23,0) 46%, rgba(37,28,23,0.86) 82%,
      rgba(37,28,23,0.94) 100%); }}
  .card {{ position:relative; z-index:1; width:100%; height:100%;
    padding:96px 92px 80px; display:flex; flex-direction:column; }}
  .kicker {{ display:flex; align-items:center; gap:22px; }}
  .kicker .label {{ font-weight:600; font-size:30px; letter-spacing:0.30em;
    text-transform:uppercase; color:#f1d9c8;
    text-shadow:0 2px 18px rgba(37,28,23,0.55); }}
  .headline {{ font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 144,'wght' 600,'SOFT' 0,'WONK' 1;
    color:#faf4e8; line-height:1.05; letter-spacing:-0.014em;
    font-size:96px; margin-top:auto; margin-bottom:26px; }}
  .dek {{ font-size:39px; line-height:1.38; color:#faf4e8; opacity:0.95;
    max-width:88%; }}
  .footer {{ border-top:3px solid rgba(250,244,232,0.45); padding-top:30px;
    margin-top:50px; display:flex; align-items:center;
    justify-content:space-between; }}
  .wordmark {{ font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 60,'wght' 600,'WONK' 1;
    font-size:33px; letter-spacing:0.02em; color:#faf4e8; }}
  .swipe {{ display:flex; align-items:center; gap:14px; color:#f1d9c8;
    font-size:29px; letter-spacing:0.10em; text-transform:uppercase;
    font-weight:600; }}
</style></head>
<body>
  <img class="photo" src="{photo_uri}" alt="">
  <div class="scrim"></div>
  <div class="card">
    <div class="kicker">{SUN_SVG.replace("{COLOR}", "#faf4e8")}<span class="label">{_esc(s['kicker'])}</span></div>
    <div class="headline">{_esc(s['headline'])}</div>
    <div class="dek">{_esc(s['dek'])}</div>
    <div class="footer"><span class="wordmark">Tucson Daily Brief</span>{swipe}</div>
  </div>
</body></html>"""


if __name__ == "__main__":
    total = len(SLIDES)
    for i, s in enumerate(SLIDES, 1):
        slug = f"founder-{i:02d}-{s['slug']}"
        print(f"rendering {slug} ...")
        html_str = photo_cover_html(s, i, total) if s.get("photo") else slide_html(s, i, total)
        render(slug, html_str)
    print(f"done. {total} slides -> social/cards/founder-*.png")
