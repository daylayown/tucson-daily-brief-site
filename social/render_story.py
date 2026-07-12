#!/usr/bin/env python3
"""
TDB Instagram Story asset (1080x1920, 9:16 full-screen vertical).

Stories are casual, ephemeral, and interactive — this asset is designed to
pair with an in-app sticker (poll / question / link). The bottom third is left
intentionally open so you can drop a poll or "see more" sticker there in the
IG app without covering the text.

Usage:
    .venv/bin/python3 social/render_story.py
Output: social/cards/story-<slug>.png
"""
import subprocess, os
from render_card import THEMES, FONTS_HREF, SUN_SVG, CARDS_DIR, SCALE

SW, SH = 1080, 1920
T = THEMES["terracotta"]

# Today's story: Saturday-night monsoon storm recap (facts from the 2026-07-12
# brief — KGUN 9 / KOLD / KVOA). Leave bottom open for the poll sticker
# (e.g. "Did you lose power last night?" -> "Yep" / "Kept the lights on").
KICKER = "Monsoon · Saturday night"
HEADLINE = "10,000+ without<br>power. One rescue<br>from a running<br>wash."
SUBHEAD = ("Saturday night’s storm flooded streets and washes across Tucson and "
           "downed trees citywide. Crews pulled one person, uninjured, from the "
           "Alamo Wash — and Tuesday, the county votes on flood-control land.")
STICKER_HINT = "poll below ↓"

PAGE = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS_HREF}">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html,body {{ width:{SW}px; height:{SH}px; }}
  body {{ background:{T['bg']}; color:{T['ink']};
    font-family:'Newsreader',Georgia,serif; -webkit-font-smoothing:antialiased;
    position:relative; overflow:hidden; }}
  body::before {{ content:""; position:absolute; inset:0;
    background:radial-gradient(720px 640px at 84% 10%, {T['glow']} 0%, transparent 60%);
    pointer-events:none; }}
  .wrap {{ position:relative; z-index:1; width:100%; height:100%;
    padding:150px 96px 0; display:flex; flex-direction:column; }}
  .kicker {{ display:flex; align-items:center; gap:24px; margin-bottom:90px; }}
  .kicker .label {{ font-weight:600; font-size:33px; letter-spacing:0.28em;
    text-transform:uppercase; color:{T['kicker']}; }}
  .headline {{ font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 144,'wght' 600,'SOFT' 0,'WONK' 1;
    font-size:104px; line-height:1.03; letter-spacing:-0.015em; color:{T['ink']}; }}
  .sub {{ font-size:44px; line-height:1.36; color:{T['ink']}; opacity:0.92;
    margin-top:44px; max-width:88%; }}
  .hint {{ margin-top:64px; font-size:34px; letter-spacing:0.10em;
    text-transform:uppercase; font-weight:600; color:{T['accent']}; }}
  .wordmark {{ position:absolute; left:96px; bottom:90px;
    font-family:'Fraunces',serif; font-variation-settings:'opsz' 60,'wght' 600,'WONK' 1;
    font-size:38px; letter-spacing:0.02em; color:{T['accent']}; }}
</style></head>
<body><div class="wrap">
  <div class="kicker">{SUN_SVG.replace("{COLOR}", T['sun'])}<span class="label">{KICKER}</span></div>
  <div class="headline">{HEADLINE}</div>
  <div class="sub">{SUBHEAD}</div>
  <div class="hint">{STICKER_HINT}</div>
  <span class="wordmark">Tucson Daily Brief</span>
</div></body></html>"""


def render_story(slug, html_str):
    os.makedirs(CARDS_DIR, exist_ok=True)
    html_path = os.path.join(CARDS_DIR, f"{slug}.html")
    big = os.path.join(CARDS_DIR, f"{slug}.2x.png")
    final = os.path.join(CARDS_DIR, f"{slug}.png")
    with open(html_path, "w") as f:
        f.write(html_str)
    subprocess.run(["chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", "--default-background-color=00000000",
        f"--force-device-scale-factor={SCALE}", f"--window-size={SW},{SH}",
        "--virtual-time-budget=7000", f"--screenshot={big}", f"file://{html_path}"],
        check=True, capture_output=True)
    subprocess.run(["convert", big, "-filter", "Lanczos", "-resize", f"{SW}x{SH}",
        "-unsharp", "0x0.6+0.7+0", "-strip", "-quality", "95", final],
        check=True, capture_output=True)
    os.remove(big); os.remove(html_path)
    print(f"  wrote {final}")


if __name__ == "__main__":
    print("rendering story ...")
    render_story("story-monsoon-2026-07-12", PAGE)
    print("done.")
