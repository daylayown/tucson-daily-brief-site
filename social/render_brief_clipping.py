#!/usr/bin/env python3
"""
Brief "clipping" renderer — a stylized excerpt of a published daily brief,
typeset in the site's own typography, for the self-contained X strategy.

WHY THIS EXISTS (X-PLAYBOOK.md, 2026-08-08): X hides link-bearing replies
from new accounts outright, so the thread beat that used to be "link to the
brief" becomes a RECEIPT instead — a rendered clipping of the actual
published item, with the domain living inside the image where no filter can
touch it. Pirate Wires' screenshot-of-the-article move, in TDB's visual
language.

The item is parsed from the published posts/YYYY-MM-DD.html, so the clipping
can never say something the brief didn't — zero new claims, zero fabrication
surface. Only the real headline, body, and source names appear.

Usage:
    .venv/bin/python3 social/render_brief_clipping.py 2026-08-06 "Salad and Go"
    (date of the brief, then a substring of the item's bold headline)

Output: social/cards/clipping-<date>-<slug>.png  (1200x1000)
"""
import html as _html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_card import FONTS_HREF, SUN_SVG, render

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Site palette (style.css :root)
SAND, BONE, TERRA, BROWN, BROWN_L, DUST = (
    "#f5f0e6", "#faf4e8", "#c75b39", "#3d3029", "#5c4a3f", "#c7b9a4")

W, H = 1200, 1000


def extract_item(date: str, needle: str):
    """Return (section, headline, body, sources) for the brief item whose
    <strong> headline contains `needle`."""
    path = os.path.join(SITE, "posts", f"{date}.html")
    s = open(path).read()
    items = re.findall(
        r"<p><strong>(.*?)</strong>(.*?)</p>\s*<p class=\"source\">(.*?)</p>",
        s, re.DOTALL)
    sections = [(m.start(), _html.unescape(re.sub(r"<[^>]+>", "", m.group(1))))
                for m in re.finditer(r"<h2>(.*?)</h2>", s)]
    for m in re.finditer(
            r"<p><strong>(.*?)</strong>(.*?)</p>\s*<p class=\"source\">(.*?)</p>",
            s, re.DOTALL):
        head = _html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        if needle.lower() not in head.lower():
            continue
        body = _html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        sources = [_html.unescape(t) for t in
                   re.findall(r"<a [^>]*>(.*?)</a>", m.group(3))]
        section = ""
        for pos, name in sections:
            if pos < m.start():
                section = name
        # strip the emoji prefix off the section header
        section = re.sub(r"^[^\w&]+", "", section).strip()
        return section, head, body, sources
    raise SystemExit(f"no item matching {needle!r} in posts/{date}.html")


def clipping_html(date: str, section: str, head: str, body: str,
                  sources: list[str]) -> str:
    sun = SUN_SVG.replace("{COLOR}", TERRA)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{FONTS_HREF}">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:{W}px; height:{H}px; }}
body {{ background:{SAND}; display:flex; align-items:center; justify-content:center;
       font-family:'Newsreader', serif; }}
.paper {{ width:1040px; background:{BONE}; border:1px solid {DUST};
         box-shadow:0 18px 44px rgba(61,48,41,0.18), 0 3px 10px rgba(61,48,41,0.10);
         padding:64px 72px 52px; }}
.mast {{ display:flex; align-items:center; gap:18px; padding-bottom:26px;
        border-bottom:2px solid {BROWN}; }}
.mast svg {{ width:44px; height:44px; }}
.wordmark {{ font-family:'Fraunces', serif; font-variation-settings:'opsz' 144,'SOFT' 70,'WONK' 1;
            font-weight:700; font-size:40px; color:{BROWN}; letter-spacing:-0.5px; }}
.section {{ margin-top:34px; font-size:20px; font-weight:600; letter-spacing:0.16em;
           text-transform:uppercase; color:{TERRA}; }}
.head {{ margin-top:18px; font-size:41px; line-height:1.22; font-weight:600; color:{BROWN}; }}
.body {{ margin-top:22px; font-size:31px; line-height:1.5; color:{BROWN_L}; }}
.foot {{ margin-top:30px; display:flex; justify-content:space-between; font-size:22px;
        color:{TERRA}; font-weight:600; }}
</style></head><body>
<div class="paper">
  <div class="mast">{sun}<span class="wordmark">Tucson Daily Brief</span></div>
  <div class="section">{_html.escape(section)}</div>
  <div class="head">{_html.escape(head)}</div>
  <div class="body">{_html.escape(body)}</div>
  <div class="foot"><span>Free every morning</span><span>tucsondailybrief.com</span></div>
</div>
</body></html>"""


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: render_brief_clipping.py YYYY-MM-DD <headline substring>")
    date, needle = sys.argv[1], sys.argv[2]
    section, head, body, sources = extract_item(date, needle)
    slug = "clipping-" + date + "-" + re.sub(r"[^a-z0-9]+", "-", needle.lower()).strip("-")
    render(slug, clipping_html(date, section, head, body, sources), size=(W, H))
    print(f"  rendered {slug} ({section} / {head[:50]}…)")
