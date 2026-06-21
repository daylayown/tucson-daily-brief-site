#!/usr/bin/env python3
"""
TDB Instagram crossword-promo card.

Renders a 5x5 "Tucson Mini" grid (numbered cells + blocks) plus a few
unmistakably-Tucson clues, on the warm-organic desert palette. Sells the
Sunday newsletter's free crossword perk: "a Tucson crossword, every Sunday."

Reuses fonts/theme/render() from render_card.py. Output 1080x1350 IG-portrait.

Usage:
    .venv/bin/python3 social/render_crossword_card.py
"""
import html as _html
from render_card import THEMES, FONTS_HREF, SUN_SVG, render, W, H

# --- the puzzle to display ----------------------------------------------------
# Based on the real 2026-06-14 Tucson Mini (valid grid). Shown empty + numbered,
# the classic "fresh puzzle" look. Clues carry the Tucson flavor.
# "#" = block cell.
GRID = [
    ["B", "I", "K", "E", "#"],
    ["A", "S", "A", "D", "A"],
    ["R", "A", "R", "E", "R"],
    ["N", "A", "O", "M", "I"],
    ["#", "C", "L", "A", "D"],
]
# Cell numbers (standard crossword numbering), keyed by (row, col).
NUMBERS = {
    (0, 0): 1, (0, 1): 2, (0, 2): 3, (0, 3): 4,
    (1, 0): 5, (1, 4): 6,
    (2, 0): 7,
    (3, 0): 8,
    (4, 1): 9,
}
# The Tucson-flavored clues we surface on the card.
CLUES = [
    ("1A", "Ride it on The Loop, Tucson’s 137-mile car-free path"),
    ("5A", "Carne ___ — the filling in a Sonoran-style taco"),
    ("7A", "Like a Gila monster sighting: uncommon, but it happens"),
]

SHOW_LETTERS = False  # False = empty "solve me" grid; True = filled (spoiler)

T = THEMES["light"]
CELL = 104  # px per cell at 1x


def _esc(s):
    return _html.escape(s, quote=False)


def grid_html():
    cells = []
    for r in range(5):
        for c in range(5):
            ch = GRID[r][c]
            if ch == "#":
                cells.append('<div class="cell block"></div>')
                continue
            num = NUMBERS.get((r, c))
            num_html = f'<span class="num">{num}</span>' if num else ""
            letter = f'<span class="ltr">{ch}</span>' if SHOW_LETTERS else ""
            cells.append(f'<div class="cell">{num_html}{letter}</div>')
    return "".join(cells)


def clues_html():
    rows = []
    for label, text in CLUES:
        rows.append(
            f'<div class="clue"><span class="cnum">{_esc(label)}</span>'
            f'<span class="ctxt">{_esc(text)}</span></div>'
        )
    return "".join(rows)


PAGE = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS_HREF}">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html,body {{ width:{W}px; height:{H}px; }}
  body {{
    background:{T['bg']}; color:{T['ink']};
    font-family:'Newsreader',Georgia,serif;
    -webkit-font-smoothing:antialiased; position:relative; overflow:hidden;
  }}
  body::before {{
    content:""; position:absolute; inset:0;
    background:radial-gradient(640px 540px at 86% 8%, {T['glow']} 0%, transparent 62%);
    pointer-events:none;
  }}
  .card {{
    position:relative; z-index:1; width:100%; height:100%;
    padding:88px 92px 80px; display:flex; flex-direction:column;
  }}
  .kicker {{ display:flex; align-items:center; gap:22px; }}
  .kicker .label {{
    font-weight:600; font-size:29px; letter-spacing:0.30em;
    text-transform:uppercase; color:{T['kicker']};
  }}
  .headline {{
    font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 144,'wght' 600,'SOFT' 0,'WONK' 1;
    color:{T['ink']}; line-height:1.04; letter-spacing:-0.014em;
    font-size:74px; margin-top:30px;
  }}
  .grid {{
    display:grid; grid-template-columns:repeat(5,{CELL}px);
    grid-template-rows:repeat(5,{CELL}px);
    gap:0; margin:52px auto 8px; width:{CELL*5}px;
    border:5px solid {T['ink']};
    box-shadow:0 18px 44px rgba(61,48,41,0.16);
  }}
  .cell {{
    position:relative; background:#fffdf7;
    border:2px solid #c7b9a4;
    display:flex; align-items:center; justify-content:center;
  }}
  .cell.block {{ background:{T['ink']}; border-color:{T['ink']}; }}
  .num {{
    position:absolute; top:6px; left:9px;
    font-size:24px; font-weight:600; color:{T['accent']};
    font-family:'Newsreader',serif;
  }}
  .ltr {{
    font-family:'Fraunces',serif; font-variation-settings:'opsz' 60,'wght' 600;
    font-size:58px; color:{T['ink']};
  }}
  .clues {{ margin-top:auto; margin-bottom:8px; }}
  .clue {{ display:flex; gap:20px; margin-bottom:22px; align-items:baseline; }}
  .cnum {{
    font-family:'Fraunces',serif; font-variation-settings:'opsz' 40,'wght' 600;
    font-size:30px; color:{T['accent']}; min-width:58px;
  }}
  .ctxt {{ font-size:33px; line-height:1.3; color:{T['ink']}; opacity:0.92; }}
  .footer {{
    border-top:3px solid {T['rule']}; padding-top:28px; margin-top:18px;
    display:flex; align-items:center; justify-content:space-between;
  }}
  .wordmark {{
    font-family:'Fraunces',serif; font-variation-settings:'opsz' 60,'wght' 600,'WONK' 1;
    font-size:33px; letter-spacing:0.02em; color:{T['accent']};
  }}
  .meta {{ font-size:27px; letter-spacing:0.03em; color:{T['meta']}; text-align:right; }}
</style></head>
<body>
  <div class="card">
    <div class="kicker">{SUN_SVG.replace("{COLOR}", T['sun'])}<span class="label">The Tucson Mini</span></div>
    <div class="headline">A tiny Tucson crossword,<br>every Sunday.</div>
    <div class="grid">{grid_html()}</div>
    <div class="clues">{clues_html()}</div>
    <div class="footer">
      <span class="wordmark">Tucson Daily Brief</span>
      <span class="meta">Free with the Sunday newsletter</span>
    </div>
  </div>
</body></html>"""


if __name__ == "__main__":
    print("rendering crossword-promo ...")
    render("crossword-promo-2026-06-21", PAGE)
    print("done.")
