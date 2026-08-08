#!/usr/bin/env python3
"""
Pull-quote card renderer — the Pirate Wires quote format in TDB's language.

Layout (from the PW reference, ~/Downloads/pwquote.png, 2026-08-08): solid
dark square; tiny attribution top-left; tiny date top-right; one big bold
centered quote in quotation marks; thin rule; logo centered at the bottom.
Nothing else. TDB translation: dusk-brown ground (warm palette, not black),
cream Fraunces for the quote, the sun + wordmark as the bottom logo.

RULES: the quote must be VERBATIM from a published TDB piece or a named
source in one — never paraphrase onto a quote card (highest-scrutiny
surface, see feedback_ai_content_quality_bar). Trimming trailing clauses is
fine; rewording is not. Quoting our own reporting is the default move (the
PW reference card quotes their own article).

Usage (as a library from a per-story script, or the demo below):
    from render_pullquote import pullquote
    pullquote(slug="...", quote="...", attribution="TUCSON DAILY BRIEF",
              date="AUG. 3, 2026")
"""
import html as _html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_card import FONTS_HREF, SUN_SVG, render

DUSK, SHADOW, CREAM, KICK = "#4a382c", "#251c17", "#faf4e8", "#d9c7ae"
W, H = 1200, 1200


def pullquote(*, slug, quote, attribution, date, size=(W, H), qsize=None):
    w, h = size
    n = len(quote)
    if qsize is None:
        qsize = 76 if n <= 140 else 64 if n <= 220 else 54 if n <= 320 else 46
    sun = SUN_SVG.replace("{COLOR}", CREAM)
    html_str = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{FONTS_HREF}">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:{w}px; height:{h}px; }}
body {{ background:linear-gradient(160deg, {DUSK} 0%, {SHADOW} 100%);
       display:flex; flex-direction:column; padding:56px 72px 48px;
       font-family:'Fraunces', serif; }}
.top {{ display:flex; justify-content:space-between;
       font-family:'Newsreader', serif; font-size:22px; letter-spacing:0.14em;
       color:{KICK}; text-transform:uppercase; }}
.quote {{ flex:1; display:flex; align-items:center; justify-content:center;
         text-align:center; }}
.quote p {{ font-size:{qsize}px; line-height:1.28; font-weight:640; color:{CREAM};
           font-variation-settings:'opsz' 90, 'SOFT' 60, 'WONK' 0;
           letter-spacing:-0.01em; max-width:980px; }}
.rule {{ border-top:1px solid rgba(250,244,232,0.35); margin-bottom:30px; }}
.logo {{ display:flex; align-items:center; justify-content:center; gap:16px; }}
.logo svg {{ width:40px; height:40px; }}
.logo span {{ font-weight:700; font-size:30px; color:{CREAM};
             font-variation-settings:'opsz' 144,'SOFT' 70,'WONK' 1; }}
</style></head><body>
<div class="top"><span>{_html.escape(attribution)}</span><span>{_html.escape(date)}</span></div>
<div class="quote"><p>&ldquo;{_html.escape(quote)}&rdquo;</p></div>
<div class="rule"></div>
<div class="logo">{sun}<span>Tucson Daily Brief</span></div>
</body></html>"""
    render(slug, html_str, size=size)


if __name__ == "__main__":
    # Demo: our own early-ballots scoop, verbatim from
    # news-reports/pima-county-2026-08-03-special-meeting.html (trailing
    # clause trimmed at a clause boundary; no rewording).
    pullquote(
        slug="pullquote-early-ballots-2026-08-03",
        quote=("Pima County issued 349,885 early ballots for the July 21 "
               "primary. Just 161,016 came back to be counted — a 46% return "
               "rate, the lowest for any primary in the three decades of "
               "statistics the county Recorder publishes."),
        attribution="Tucson Daily Brief reporting",
        date="Aug. 3, 2026",
    )
    print("  rendered pullquote-early-ballots-2026-08-03")
