#!/usr/bin/env python3
"""
TDB brand-asset renderer — unify YouTube + Apple Podcasts branding with IG.

Reproduces the IG/Threads avatar lockup (terracotta bg, desert sun, "TDB",
hand rule, "TUCSON DAILY BRIEF") at the sizes each platform needs, plus a
matching YouTube channel banner. Uses vmin/vh units so one template scales to
any dimension. Reuses fonts/palette from render_card.py.

Usage:
    .venv/bin/python3 social/render_brand.py

Outputs to social/cards/:
    brand-cover-3000.png       Apple Podcasts / square cover (3000x3000)
    brand-avatar-1080.png      Channel avatar (1080x1080; matches ~/tdb-fb-profile.png)
    brand-banner-2048x1152.png YouTube channel banner (safe area 1235x338 centered)
"""
import subprocess, os
from render_card import THEMES, FONTS_HREF, SUN_SVG, CARDS_DIR

T = THEMES["terracotta"]


def _render_at(slug, html_str, w, h, scale=1):
    os.makedirs(CARDS_DIR, exist_ok=True)
    html_path = os.path.join(CARDS_DIR, f"{slug}.html")
    big = os.path.join(CARDS_DIR, f"{slug}.raw.png")
    final = os.path.join(CARDS_DIR, f"{slug}.png")
    with open(html_path, "w") as f:
        f.write(html_str)
    subprocess.run([
        "chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", "--default-background-color=00000000",
        f"--force-device-scale-factor={scale}", f"--window-size={w},{h}",
        "--virtual-time-budget=8000", f"--screenshot={big}", f"file://{html_path}",
    ], check=True, capture_output=True)
    subprocess.run(["convert", big, "-resize", f"{w}x{h}", "-strip",
                    "-quality", "94", final], check=True, capture_output=True)
    os.remove(big); os.remove(html_path)
    print(f"  wrote {final}")


def _square_html(w, h):
    """The avatar lockup, sized in vmin so it scales to any square."""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{FONTS_HREF}">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  html,body{{width:{w}px;height:{h}px}}
  body{{background:{T['bg']};display:flex;align-items:center;justify-content:center;
        font-family:'Newsreader',serif;-webkit-font-smoothing:antialiased}}
  .lock{{display:flex;flex-direction:column;align-items:center;gap:0}}
  .sun{{width:24vmin;height:24vmin;margin-bottom:4.5vmin}}
  .sun svg{{width:100%;height:100%}}
  .tdb{{font-family:'Fraunces',serif;
        font-variation-settings:'opsz' 144,'wght' 600,'SOFT' 0,'WONK' 1;
        font-size:34vmin;line-height:0.9;color:{T['ink']};letter-spacing:-0.01em}}
  .rule{{width:26vmin;height:0.55vmin;background:{T['ink']};opacity:0.85;
         margin:4vmin 0 3.2vmin}}
  .wm{{font-family:'Newsreader',serif;font-weight:600;color:{T['ink']};
       font-size:5vmin;letter-spacing:0.28em;text-transform:uppercase;
       white-space:nowrap;text-align:center;padding-left:0.28em}}
</style></head><body>
  <div class="lock">
    <div class="sun">{SUN_SVG.replace("{COLOR}", T['ink'])}</div>
    <div class="tdb">TDB</div>
    <div class="rule"></div>
    <div class="wm">Tucson Daily Brief</div>
  </div>
</body></html>"""


def _banner_html(w, h):
    """YouTube banner — keep the lockup inside the centered safe area."""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{FONTS_HREF}">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  html,body{{width:{w}px;height:{h}px}}
  body{{background:{T['bg']};position:relative;overflow:hidden;
        font-family:'Newsreader',serif;-webkit-font-smoothing:antialiased;
        display:flex;align-items:center;justify-content:center}}
  body::before{{content:"";position:absolute;inset:0;
    background:radial-gradient(60vh 60vh at 78% 12%, {T['glow']} 0%, transparent 62%);}}
  /* safe area ~1235x338 centered — keep all text within ~300px tall band */
  .lock{{position:relative;z-index:1;display:flex;align-items:center;gap:4.2vh}}
  .sun{{width:22vh;height:22vh;flex:0 0 auto}}
  .sun svg{{width:100%;height:100%}}
  .txt{{display:flex;flex-direction:column;gap:1.4vh}}
  .wm{{font-family:'Fraunces',serif;
       font-variation-settings:'opsz' 144,'wght' 600,'WONK' 1;
       font-size:13vh;line-height:0.92;color:{T['ink']};letter-spacing:-0.012em}}
  .tag{{font-family:'Newsreader',serif;font-size:4.2vh;color:{T['kicker']};
        letter-spacing:0.02em}}
</style></head><body>
  <div class="lock">
    <div class="sun">{SUN_SVG.replace("{COLOR}", T['ink'])}</div>
    <div class="txt">
      <div class="wm">Tucson Daily Brief</div>
      <div class="tag">Local Tucson news, every morning.</div>
    </div>
  </div>
</body></html>"""


if __name__ == "__main__":
    print("rendering brand assets ...")
    _render_at("brand-cover-3000", _square_html(3000, 3000), 3000, 3000, scale=1)
    _render_at("brand-avatar-1080", _square_html(1080, 1080), 1080, 1080, scale=2)
    _render_at("brand-banner-2048x1152", _banner_html(2048, 1152), 2048, 1152, scale=1)
    print("done.")
