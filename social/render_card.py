#!/usr/bin/env python3
"""
TDB Instagram image-card renderer.

HTML template -> headless Chromium screenshot (2x) -> downscale to 1080x1350 PNG.
Desert-palette / warm-organic visual language matching the site (Fraunces + Newsreader).

Two themes:
  - "terracotta": solid terracotta bg, cream text (matches the avatar; good for intro/identity cards)
  - "light":      bone bg, brown headline, terracotta accents (best for news headline cards)

Usage:
    .venv/bin/python3 social/render_card.py            # render the built-in demo cards
    (or import build_card / render and drive it from another script)

Output: social/cards/<slug>.png  (1080x1350, IG-portrait 4:5)
"""
import subprocess
import sys
import os
import html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS_DIR = os.path.join(HERE, "cards")

# IG portrait 4:5 — most feed real estate.
W, H = 1080, 1350
SCALE = 2  # render at 2x for crisp text, then downscale

FONTS_HREF = ("https://fonts.googleapis.com/css2?"
              "family=Fraunces:opsz,wght,SOFT,WONK@9..144,300..900,0..100,0..1&"
              "family=Newsreader:ital,opsz,wght@0,6..72,300..700;1,6..72,300..700&display=swap")

# 12-ray desert sun, echoes the avatar + site kicker dingbat. {COLOR} is replaced.
SUN_SVG = """<svg width="64" height="64" viewBox="0 0 64 64" aria-hidden="true">
  <circle cx="32" cy="32" r="11" fill="{COLOR}"/>
  <g stroke="{COLOR}" stroke-width="2.4" stroke-linecap="round">
    <line x1="32" y1="3"  x2="32" y2="13"/>
    <line x1="32" y1="51" x2="32" y2="61"/>
    <line x1="3"  y1="32" x2="13" y2="32"/>
    <line x1="51" y1="32" x2="61" y2="32"/>
    <line x1="11.5" y1="11.5" x2="18.5" y2="18.5"/>
    <line x1="45.5" y1="45.5" x2="52.5" y2="52.5"/>
    <line x1="11.5" y1="52.5" x2="18.5" y2="45.5"/>
    <line x1="45.5" y1="18.5" x2="52.5" y2="11.5"/>
    <line x1="32" y1="6"  x2="32" y2="6.5" transform="rotate(30 32 32)"/>
    <line x1="32" y1="6"  x2="32" y2="6.5" transform="rotate(60 32 32)"/>
    <line x1="32" y1="6"  x2="32" y2="6.5" transform="rotate(120 32 32)"/>
    <line x1="32" y1="6"  x2="32" y2="6.5" transform="rotate(150 32 32)"/>
  </g>
</svg>"""

THEMES = {
    "terracotta": {
        "bg": "#c75b39",
        "glow": "rgba(250,244,232,0.16)",
        "ink": "#faf4e8",
        "kicker": "#f1d9c8",
        "accent": "#faf4e8",
        "rule": "rgba(250,244,232,0.5)",
        "sun": "#faf4e8",
        "meta": "#f1d9c8",
    },
    "light": {
        "bg": "#faf4e8",
        "glow": "rgba(199,91,57,0.14)",
        "ink": "#3d3029",
        "kicker": "#a84a2e",
        "accent": "#c75b39",
        "rule": "#d8a98f",
        "sun": "#c75b39",
        "meta": "#5c4a3f",
    },
    # Dark "investigative" desert — for the Buried in the Agenda series.
    "dark": {
        "bg": "#251c17",
        "glow": "rgba(199,91,57,0.22)",
        "ink": "#faf4e8",
        "kicker": "#d97048",
        "accent": "#d97048",
        "rule": "rgba(250,244,232,0.22)",
        "sun": "#d97048",
        "meta": "#c7b9a4",
    },
}

PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="__FONTS__">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html,body { width:__W__px; height:__H__px; }
  body {
    background:__BG__;
    color:__INK__;
    font-family:'Newsreader',Georgia,serif;
    -webkit-font-smoothing:antialiased;
    position:relative;
    overflow:hidden;
  }
  /* sun-cast glow, top-right, echoes the site */
  body::before {
    content:""; position:absolute; inset:0;
    background:radial-gradient(640px 540px at 86% 8%, __GLOW__ 0%, transparent 62%);
    pointer-events:none;
  }
  .card {
    position:relative; z-index:1;
    width:100%; height:100%;
    padding:96px 92px 84px;
    display:flex; flex-direction:column;
  }
  .kicker {
    display:flex; align-items:center; gap:22px;
  }
  .kicker .label {
    font-family:'Newsreader',serif;
    font-weight:600;
    font-size:30px;
    letter-spacing:0.34em;
    text-transform:uppercase;
    color:__KICKER__;
  }
  .headline {
    font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 144,'wght' 600,'SOFT' 0,'WONK' 1;
    color:__INK__;
    line-height:1.06;
    letter-spacing:-0.012em;
    margin-top:auto;
    margin-bottom:28px;
  }
  .headline { font-size:__HSIZE__px; }
  .dek {
    font-family:'Newsreader',serif;
    font-size:38px;
    line-height:1.38;
    color:__INK__;
    opacity:0.92;
    max-width:84%;
    margin-bottom:8px;
  }
  .spacer { margin-top:auto; }
  .footer {
    border-top:3px solid __RULE__;
    padding-top:30px;
    display:flex; align-items:center; justify-content:space-between;
  }
  .wordmark {
    font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 60,'wght' 600,'WONK' 1;
    font-size:34px;
    letter-spacing:0.02em;
    color:__ACCENT__;
  }
  .meta {
    font-family:'Newsreader',serif;
    font-size:27px;
    letter-spacing:0.04em;
    color:__META__;
    text-align:right;
  }
  .source {
    font-family:'Newsreader',serif;
    font-style:italic;
    font-size:30px;
    color:__META__;
    margin-bottom:26px;
  }
</style></head>
<body>
  <div class="card">
    <div class="kicker">__SUN__<span class="label">__KICKERTEXT__</span></div>
    __BODY__
    <div class="footer">
      <span class="wordmark">Tucson Daily Brief</span>
      <span class="meta">__METATEXT__</span>
    </div>
  </div>
</body></html>"""


def _esc(s):
    return _html.escape(s, quote=False)


def build_card(*, theme="light", kicker, headline, dek=None, source=None,
               meta_text="tucsondailybrief.com", hsize=None):
    """Return the HTML string for one card."""
    t = THEMES[theme]
    if hsize is None:
        n = len(headline)
        hsize = 92 if n <= 32 else 80 if n <= 50 else 70 if n <= 72 else 60

    body_parts = []
    if dek:
        body_parts.append('<div class="spacer"></div>')
        body_parts.append(f'<div class="headline">{_esc(headline)}</div>')
        body_parts.append(f'<div class="dek">{_esc(dek)}</div>')
    else:
        body_parts.append(f'<div class="headline">{_esc(headline)}</div>')
        if source:
            body_parts.append(f'<div class="source">{_esc(source)}</div>')
    body = "\n    ".join(body_parts)

    out = PAGE
    repl = {
        "__FONTS__": FONTS_HREF, "__W__": str(W), "__H__": str(H),
        "__BG__": t["bg"], "__GLOW__": t["glow"], "__INK__": t["ink"],
        "__KICKER__": t["kicker"], "__ACCENT__": t["accent"], "__RULE__": t["rule"],
        "__META__": t["meta"], "__HSIZE__": str(hsize),
        "__SUN__": SUN_SVG.replace("{COLOR}", t["sun"]),
        "__KICKERTEXT__": _esc(kicker), "__BODY__": body,
        "__METATEXT__": _esc(meta_text),
    }
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


def render(slug, html_str):
    """Render an HTML string to social/cards/<slug>.png at 1080x1350."""
    os.makedirs(CARDS_DIR, exist_ok=True)
    html_path = os.path.join(CARDS_DIR, f"{slug}.html")
    big_path = os.path.join(CARDS_DIR, f"{slug}.2x.png")
    final_path = os.path.join(CARDS_DIR, f"{slug}.png")
    with open(html_path, "w") as f:
        f.write(html_str)

    subprocess.run([
        "chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", "--default-background-color=00000000",
        f"--force-device-scale-factor={SCALE}",
        f"--window-size={W},{H}",
        "--virtual-time-budget=7000",
        f"--screenshot={big_path}",
        f"file://{html_path}",
    ], check=True, capture_output=True)

    # downscale 2x -> exact IG spec with high-quality filter
    subprocess.run([
        "convert", big_path, "-resize", f"{W}x{H}", "-strip",
        "-quality", "92", final_path,
    ], check=True, capture_output=True)
    os.remove(big_path)
    os.remove(html_path)
    print(f"  wrote {final_path}")
    return final_path


# --- built-in first-post cards -------------------------------------------------
DEMO = [
    dict(slug="intro", theme="terracotta",
         kicker="Now on Instagram",
         headline="Local Tucson news, every morning.",
         dek="Government, public safety, food, and what’s opening around the Old Pueblo.",
         meta_text="@tucsondailybrief"),
    dict(slug="news-pedestrian-2026-06-20", theme="light",
         kicker="Public Safety",
         headline="Tucson ranks 4th-most dangerous U.S. metro for pedestrians",
         source="June 20, 2026",
         meta_text="tucsondailybrief.com"),
    dict(slug="news-mountain-lions-2026-06-21", theme="light",
         kicker="Around Town",
         headline="Meet Moonbead and Pretzel",
         dek="The Desert Museum’s two rescued mountain lion brothers finally have names — chosen by kids from Beads of Courage.",
         meta_text="tucsondailybrief.com"),
    # --- 2026-06-23: heat-warning + behind-the-scenes weather (2-slide carousel)
    dict(slug="heat-warning-2026-06-23", theme="terracotta",
         kicker="Extreme Heat Warning",
         headline="109° today. Take it seriously.",
         dek="An Extreme Heat Warning is in effect across metro Tucson through 8 PM Wednesday. Limit outdoor activity to early morning or evening, hydrate, and never leave people or pets in a parked car.",
         meta_text="swipe to see how we know →"),
    dict(slug="behind-weather-2026-06-23", theme="light",
         kicker="How we work",
         headline="Where our weather comes from",
         dek="Every morning we pull the forecast straight from the National Weather Service’s free public API — pinned to one spot downtown (32.22, -110.97, right by Hotel Congress). The government’s own data, no TV-weather middleman.",
         meta_text="tucsondailybrief.com"),
    dict(slug="news-alpr-2026-06-23", theme="light",
         kicker="City Council",
         headline="Tucson approves an independent review of police license-plate readers",
         source="June 23, 2026",
         meta_text="tucsondailybrief.com"),
]

if __name__ == "__main__":
    for c in DEMO:
        slug = c.pop("slug")
        print(f"rendering {slug} ...")
        render(slug, build_card(**c))
    print("done.")
