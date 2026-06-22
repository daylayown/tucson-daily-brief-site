#!/usr/bin/env python3
"""
TDB Instagram feature carousel — "what sets us apart" week opener.

Renders a multi-slide swipeable carousel (1080x1350 each) introducing the
site's distinctive features. Slide 1 is a terracotta cover; feature slides are
light; final slide is a terracotta CTA. Reuses fonts/theme/render() from
render_card.py.

Usage:
    .venv/bin/python3 social/render_feature_carousel.py

Output: social/cards/feature-NN-<slug>.png
"""
import html as _html
from render_card import THEMES, FONTS_HREF, SUN_SVG, render, W, H

# Each slide: theme, kicker, headline, dek, and footer counter.
SLIDES = [
    dict(slug="cover", theme="terracotta",
         kicker="How we cover Tucson",
         headline="One small team.\nThe whole metro.",
         dek="A week on what makes the Tucson Daily Brief different from any other local outlet.",
         swipe=True),
    dict(slug="meeting-watch", theme="light",
         kicker="Meeting Watch",
         headline="We read every agenda before the meeting.",
         dek="Plain-language previews of what’s coming up at city and town councils across Tucson, Pima County, Marana & Oro Valley — so you know what’s at stake before the vote."),
    dict(slug="spotted", theme="light",
         kicker="Spotted",
         headline="The filings nobody reports on.",
         dek="New liquor licenses and buried agenda items, surfaced from the government documents most people never see."),
    dict(slug="news-reports", theme="light",
         kicker="News Reports",
         headline="We sit in the meetings.",
         dek="When a council meets, we transcribe the whole thing and write it up — and a working journalist reviews every word before it publishes."),
    dict(slug="ask", theme="light",
         kicker="Ask",
         headline="Ask anything\nabout Tucson.",
         dek="Our Q&A tool answers using everything we’ve covered — every brief, meeting, and filing — with links to the sources. No other local outlet has it."),
    dict(slug="podcast", theme="light",
         kicker="The Daily Podcast",
         headline="Tucson, in\n90 seconds.",
         dek="Every morning’s brief, condensed into a quick listen for your commute — on Apple Podcasts and YouTube."),
    dict(slug="cta", theme="terracotta",
         kicker="Every morning",
         headline="Read it. Hear it.\nAsk it.",
         dek="A daily brief and podcast, a Sunday newsletter with a free Tucson crossword, and a Q&A tool that draws on it all. Always free — link in bio.",
         cta=True),
]


def _esc(s):
    return _html.escape(s, quote=False)


def slide_html(s, idx, total):
    t = THEMES[s["theme"]]
    headline = s["headline"].replace("\n", "<br>")
    n = len(s["headline"])
    hsize = 92 if n <= 30 else 82 if n <= 48 else 72

    swipe = ""
    if s.get("swipe"):
        swipe = ('<span class="swipe">swipe '
                 '<svg width="34" height="20" viewBox="0 0 34 20" aria-hidden="true">'
                 '<path d="M2 10h28M22 3l8 7-8 7" stroke="currentColor" '
                 'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
                 '</svg></span>')
    counter = f'<span class="count">{idx} / {total}</span>'
    right = swipe if s.get("swipe") else (
        '<span class="count">tucsondailybrief.com</span>' if s.get("cta") else counter)
    left = '<span class="wordmark">Tucson Daily Brief</span>'

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS_HREF}">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html,body {{ width:{W}px; height:{H}px; }}
  body {{
    background:{t['bg']}; color:{t['ink']};
    font-family:'Newsreader',Georgia,serif; -webkit-font-smoothing:antialiased;
    position:relative; overflow:hidden;
  }}
  body::before {{
    content:""; position:absolute; inset:0;
    background:radial-gradient(640px 540px at 86% 8%, {t['glow']} 0%, transparent 62%);
    pointer-events:none;
  }}
  .card {{ position:relative; z-index:1; width:100%; height:100%;
           padding:96px 92px 80px; display:flex; flex-direction:column; }}
  .kicker {{ display:flex; align-items:center; gap:22px; }}
  .kicker .label {{ font-weight:600; font-size:30px; letter-spacing:0.30em;
                    text-transform:uppercase; color:{t['kicker']}; }}
  .headline {{ font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 144,'wght' 600,'SOFT' 0,'WONK' 1;
    color:{t['ink']}; line-height:1.05; letter-spacing:-0.014em;
    font-size:{hsize}px; margin-top:auto; margin-bottom:30px; }}
  .dek {{ font-size:39px; line-height:1.38; color:{t['ink']}; opacity:0.93; max-width:90%; }}
  .footer {{ border-top:3px solid {t['rule']}; padding-top:30px; margin-top:54px;
    display:flex; align-items:center; justify-content:space-between; }}
  .wordmark {{ font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 60,'wght' 600,'WONK' 1;
    font-size:33px; letter-spacing:0.02em; color:{t['accent']}; }}
  .count {{ font-size:27px; letter-spacing:0.06em; color:{t['meta']}; }}
  .swipe {{ display:flex; align-items:center; gap:14px; color:{t['accent']};
    font-size:29px; letter-spacing:0.10em; text-transform:uppercase; font-weight:600; }}
</style></head>
<body><div class="card">
  <div class="kicker">{SUN_SVG.replace("{COLOR}", t['sun'])}<span class="label">{_esc(s['kicker'])}</span></div>
  <div class="headline">{headline}</div>
  <div class="dek">{_esc(s['dek'])}</div>
  <div class="footer">{left}{right}</div>
</div></body></html>"""


if __name__ == "__main__":
    total = len(SLIDES)
    for i, s in enumerate(SLIDES, 1):
        slug = f"feature-{i:02d}-{s['slug']}"
        print(f"rendering {slug} ...")
        render(slug, slide_html(s, i, total))
    print(f"done. {total} slides -> social/cards/feature-*.png")
