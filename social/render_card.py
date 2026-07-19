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
SCALE = 3  # supersample at 3x for crisp text, then downscale to spec

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


# Centered emblem lockup: big desert sun over a Fraunces wordmark + small caps
# sub-line. For a faux "logo" (e.g. a LinkedIn share image) where post text does
# the explaining — no kicker/dek/footer.
LOGO_PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="__FONTS__">
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html,body { width:__W__px; height:__H__px; }
  body {
    background:__BG__; color:__INK__;
    font-family:'Newsreader',Georgia,serif;
    -webkit-font-smoothing:antialiased;
    position:relative; overflow:hidden;
    display:flex; align-items:center; justify-content:center;
  }
  body::before {
    content:""; position:absolute; inset:0;
    background:radial-gradient(760px 760px at 50% 40%, __GLOW__ 0%, transparent 64%);
    pointer-events:none;
  }
  .lockup {
    position:relative; z-index:1;
    display:flex; flex-direction:column; align-items:center; text-align:center;
  }
  .mark { line-height:0; margin-bottom:48px; }
  .mark svg { width:208px; height:208px; }
  .wordmark {
    font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 144,'wght' 600,'SOFT' 0,'WONK' 1;
    font-size:__WSIZE__px;
    letter-spacing:-0.02em;
    color:__INK__;
    line-height:1;
  }
  .sub {
    margin-top:40px;
    font-family:'Newsreader',serif;
    font-weight:600;
    font-size:30px;
    letter-spacing:0.34em;
    text-transform:uppercase;
    color:__KICKER__;
  }
</style></head>
<body>
  <div class="lockup">
    <div class="mark">__SUN__</div>
    <div class="wordmark">__WORDMARK__</div>
    __SUB__
  </div>
</body></html>"""


def _esc(s):
    return _html.escape(s, quote=False)


def build_logo(*, theme="terracotta", wordmark="ChatTDB",
               sub="Tucson Daily Brief", size=(1200, 1200), wsize=170):
    """Return HTML for a centered emblem 'logo' lockup (sun + wordmark + sub)."""
    w, h = size
    t = THEMES[theme]
    sub_html = f'<div class="sub">{_esc(sub)}</div>' if sub else ""
    out = LOGO_PAGE
    repl = {
        "__FONTS__": FONTS_HREF, "__W__": str(w), "__H__": str(h),
        "__BG__": t["bg"], "__GLOW__": t["glow"], "__INK__": t["ink"],
        "__KICKER__": t["kicker"], "__WSIZE__": str(wsize),
        "__SUN__": SUN_SVG.replace("{COLOR}", t["sun"]),
        "__WORDMARK__": _esc(wordmark), "__SUB__": sub_html,
    }
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


def build_card(*, theme="light", kicker, headline, dek=None, source=None,
               meta_text="tucsondailybrief.com", hsize=None, size=None):
    """Return the HTML string for one card. `size=(w,h)` overrides the default
    1080x1350 IG-portrait canvas (e.g. (1200,1200) for a LinkedIn square)."""
    w, h = size or (W, H)
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
        "__FONTS__": FONTS_HREF, "__W__": str(w), "__H__": str(h),
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


def render(slug, html_str, size=None):
    """Render an HTML string to social/cards/<slug>.png. `size=(w,h)` overrides
    the default 1080x1350 canvas (must match the size passed to build_card)."""
    w, h = size or (W, H)
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
        f"--window-size={w},{h}",
        "--virtual-time-budget=7000",
        f"--screenshot={big_path}",
        f"file://{html_path}",
    ], check=True, capture_output=True)

    # downscale supersample -> exact spec: Lanczos for sharp edges, then a gentle
    # unsharp pass to counter the softening every downscale introduces.
    subprocess.run([
        "convert", big_path, "-filter", "Lanczos", "-resize", f"{w}x{h}",
        "-unsharp", "0x0.6+0.7+0", "-strip", "-quality", "95", final_path,
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
    dict(slug="news-alpr-howweknow-2026-06-23", theme="terracotta",
         kicker="How we know",
         headline="We sat in on the whole meeting.",
         dek="Our AI reporter transcribed the full City Council meeting, then a working journalist reviewed and fact-checked the report before we published it. No press release, no secondhand summary — straight from the source.",
         meta_text="tucsondailybrief.com"),
    dict(slug="news-pima-budget-2026-06-23", theme="light",
         kicker="Board of Supervisors",
         headline="Pima County’s $1.8B budget adds bonuses for its lowest-paid workers",
         source="June 23, 2026",
         meta_text="tucsondailybrief.com"),
    # --- 2026-06-24: ChatTDB.com launch — promote the RAG/Ask tool by its new domain
    dict(slug="chattdb-2026-06-24", theme="terracotta",
         kicker="Now live",
         headline="ChatTDB",
         dek="A free AI that answers real questions about the Old Pueblo — how the council voted, what’s opening, who filed for a liquor license — built on everything Tucson Daily Brief has ever reported. No sign-up, no app.",
         meta_text="ChatTDB.com"),
    # LinkedIn square (1200x1200) — crop-proof on desktop+mobile; same message.
    dict(slug="chattdb-linkedin-2026-06-24", theme="terracotta", size=(1200, 1200),
         kicker="Now live",
         headline="ChatTDB",
         dek="A free AI that answers real questions about the Old Pueblo — how the council voted, what’s opening, who filed for a liquor license — built on everything Tucson Daily Brief has ever reported. No sign-up, no app.",
         meta_text="ChatTDB.com"),
    # --- 2026-06-27: second Marana data center filing (2-slide: news + how-we-found-it)
    dict(slug="datacenter-marana-2026-06-27", theme="light",
         kicker="Development · Marana",
         headline="A second data center is proposed in Marana",
         dek="A filing to rezone land off Marana Road for a “technology campus and data center” landed in November — separate from the 600-acre Beale project the Town Council already approved. It’s early, and nothing’s been decided.",
         meta_text="swipe → how we found it"),
    dict(slug="datacenter-howweknow-2026-06-27", theme="terracotta",
         kicker="How we found it",
         headline="Our system found it first.",
         dek="Tucson Daily Brief automatically watches Marana’s public planning records every day. This data-center filing was on our site on June 24 — two days before it reached local TV news.",
         meta_text="tucsondailybrief.com"),
    # --- 2026-07-11: Blowing Dust Advisory (same-day monsoon safety alert)
    dict(slug="dust-advisory-2026-07-11", theme="terracotta",
         kicker="Blowing Dust Advisory",
         headline="Blowing dust likely this evening, 4–11 PM.",
         dek="NWS Tucson warns visibility could drop to a quarter-mile with 50+ mph gusts, worst along I-10. Caught driving in it? Pull off the road, turn your lights off, take your foot off the brake, and wait it out.",
         meta_text="Pull aside, stay alive"),
    # --- 2026-07-12: Saturday-night monsoon storm recap (2-slide: recap + the
    # county's flood-control votes Tuesday). Facts from the 2026-07-12 brief
    # (KGUN 9 / KOLD / KVOA) + the pima-county-2026-07-14 agenda preview.
    dict(slug="monsoon-recap-2026-07-12", theme="terracotta",
         kicker="Monsoon · Saturday night",
         headline="10,000+ lost power. Washes ran fast.",
         dek="Saturday night’s storm knocked out power to more than 10,000 TEP customers across 28 outages, flooded streets and washes citywide, and downed trees. Fire crews pulled one person — uninjured — from the fast-moving Alamo Wash.",
         meta_text="swipe → what the county does about it"),
    dict(slug="monsoon-floodvote-2026-07-12", theme="light",
         kicker="Tuesday · Board of Supervisors",
         headline="Flood votes, right on cue.",
         dek="Three days after the storm, county supervisors vote on buying 28.86 acres of flood-prone land along Brawley Wash — part of a multi-year effort to blunt monsoon flooding in Tucson’s southwest corridor.",
         meta_text="tucsondailybrief.com"),
    # --- 2026-07-16: Flood Watch (same-day monsoon safety alert). Facts verified
    # live against api.weather.gov/alerts/active?point=32.2217,-110.9694 (Flood
    # Watch, onset 2 PM 7/16, ends 5 AM 7/17, "isolated rainfall totals of 1 to 3
    # inches"). Stupid Motorist Law = ARS 28-910: liability attaches on driving
    # around a barricade onto an already-flooded road, not on rain driving.
    dict(slug="flood-watch-2026-07-16", theme="terracotta",
         kicker="Flood Watch",
         headline="Storms this afternoon. The washes will run.",
         dek="NWS Tucson has a Flood Watch up from 2 PM today until 5 AM Friday, metro Tucson out to the Catalinas. Isolated totals of 1 to 3 inches are possible. Never drive around a barricade into a flooded wash — the Stupid Motorist Law can bill you for the rescue.",
         meta_text="Turn Around, Don’t Drown"),
    # --- 2026-07-16: Southwest Record & Vintage Fair, Sun 7/19 (Tucson Weekly).
    # La Rosa = the Benedictine Monastery chapel, 800 N. Country Club (confirmed
    # by two sources). Vendor list held to Zia + Wooden Tooth: the Weekly only
    # said other shops come "from different parts of the state," so no city named.
    dict(slug="record-fair-2026-07-16", theme="light",
         kicker="Around Town",
         headline="A record fair in a monastery. With A/C.",
         dek="The Southwest Record and Vintage Fair lands at La Rosa — the old Benedictine Monastery chapel on Country Club — this Sunday. Zia and Wooden Tooth are digging out the crates, along with shops from around the state. And for the first time, it’s air-conditioned.",
         meta_text="Sun · noon–5 · free"),
    # --- 2026-07-18: Gibson Food Hall reopening, told through Johnny Gibson (reach
    # / "Only in Tucson" identity piece). Facts verified against Tucson Foodie
    # (2024-12-23) + KOLD (2026-07-17) + KGUN: Gibson was a WWII vet, weightlifter,
    # fitness-equipment designer, and barber on Sixth Ave for ~60 yrs; market at
    # 11 S. Sixth Ave carries his name; reopened this week after ~2 yrs of reno,
    # run by the neighboring HighWire owners. DELIBERATELY OMITTED: the year the
    # market opened (sources conflict, 2015 vs 2016) and the Pearl Lounge speakeasy
    # (NOT open — expected mid-August, and reported to sit in the adjacent building).
    dict(slug="gibson-food-hall-2026-07-18", theme="light",
         kicker="Only in Tucson",
         headline="The weightlifting barber of Sixth Avenue",
         dek="Johnny Gibson was a WWII veteran, a weightlifter, and a barber who cut hair on Sixth Avenue for nearly 60 years. The downtown market that still carries his name just reopened as a food hall — four restaurants, a grocery, a coffee bar, and a bar.",
         meta_text="Now open downtown"),
    # Reusable "how we know" card — generic, pairs with any News Report carousel.
    dict(slug="news-howweknow", theme="terracotta",
         kicker="How we know",
         headline="We sat in on the whole meeting.",
         dek="Our AI reporter transcribed the full meeting, then a working journalist reviewed and fact-checked the report before we published it. No press release, no secondhand summary — straight from the source.",
         meta_text="tucsondailybrief.com"),
    # --- 2026-07-18: measles reach post (facts from the day's brief — Arizona
    # Daily Star / KVOA / KOLD; symptom list + locations deliberately omitted).
    dict(slug="news-measles-2026-07-18", theme="terracotta",
         kicker="Public Health",
         headline="Measles case confirmed in Tucson",
         dek="Pima County is investigating possible public exposure locations, and urges anyone who may have been in contact to watch for symptoms.",
         meta_text="tucsondailybrief.com"),
    # --- 2026-07-19: Sunday "it's out" newsletter-conversion card, led with the
    # most urgent/useful item in the issue (Tuesday's ballot) rather than a recap.
    # All facts from the human-reviewed TDB Weekly 2026-07-19 issue that sent this
    # morning: Prop 425 = permanent 75% hike to the county expenditure limit, first
    # in 45 yrs; South Tucson = contested three-seat race, eight candidates; OV
    # mayor = VM Melanie Barrett vs. former Pima County Sheriff Mark Napier; primary
    # is Tue July 21. IG 4:5 + a crop-proof FB square, same copy.
    dict(slug="weekly-itsout-2026-07-19", theme="terracotta",
         kicker="TDB Weekly · Out now",
         headline="What’s on Tuesday’s ballot",
         dek="This morning’s issue breaks down the July 21 primary: Prop 425’s 75% county spending-limit hike, South Tucson’s eight-candidate council race, and the Oro Valley mayor’s race — Barrett vs. Napier. Free in your inbox every Sunday.",
         meta_text="Subscribe · tucsondailybrief.com"),
    dict(slug="weekly-itsout-2026-07-19-fb", theme="terracotta", size=(1200, 1200),
         kicker="TDB Weekly · Out now",
         headline="What’s on Tuesday’s ballot",
         dek="This morning’s issue breaks down the July 21 primary: Prop 425’s 75% county spending-limit hike, South Tucson’s eight-candidate council race, and the Oro Valley mayor’s race — Barrett vs. Napier. Free in your inbox every Sunday.",
         meta_text="Subscribe · tucsondailybrief.com"),
]

if __name__ == "__main__":
    for c in DEMO:
        slug = c.pop("slug")
        size = c.pop("size", None)
        print(f"rendering {slug} ...")
        render(slug, build_card(size=size, **c), size=size)
    print("done.")
