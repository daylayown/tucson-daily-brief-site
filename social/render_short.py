#!/usr/bin/env python3
"""
TDB short-form video generator (v1) — text-only motion.

Renders a sequence of vertical "beat" cards (1080x1920, desert palette) and
ffmpeg-stitches them with crossfades into a muted 1080x1920 MP4 — the locked
"text-only motion first" format. No TTS yet (word-karaoke captions come later,
once we add a TTS+Deepgram timing pass).

Usage:
    .venv/bin/python3 social/render_short.py

Output: social/cards/short-<slug>.mp4 (+ per-scene PNGs as scene-NN.png)

Design note: scenes are defined as a SCRIPT list (eyebrow + text per beat).
For the real pipeline this list is produced by an LLM from a story; here it's
the hand-built "Only in Tucson" prototype (Moonbead & Pretzel).
"""
import subprocess, os, html as _html
from render_card import THEMES, FONTS_HREF, SUN_SVG, CARDS_DIR

VW, VH = 1080, 1920          # IG/TikTok/Shorts vertical
SCENE_DUR = 3.2              # seconds each beat holds
XFADE = 0.5                  # crossfade seconds
FPS = 30
T = THEMES["terracotta"]     # "Only in Tucson" = warm terracotta identity

# --- the clip script (LLM-produced in the real pipeline) ---
SLUG = "only-in-tucson-moonbead"
SCRIPT = [
    {"eyebrow": "Only in Tucson", "text": "Tucson kids got to name two orphaned mountain lion cubs."},
    {"eyebrow": "", "text": "Rescued in April — found in the wild without their mother."},
    {"eyebrow": "", "text": "Meet Moonbead\nand Pretzel. 🦁", "big": True},
    {"eyebrow": "", "text": "Named by kids from Beads of Courage, a nonprofit for children facing serious illness."},
    {"eyebrow": "", "text": "Only in Tucson. 🌵", "cta": True},
]


def _esc(s):
    return _html.escape(s, quote=False).replace("\n", "<br>")


def scene_html(scene):
    n = len(scene["text"])
    size = 132 if scene.get("big") else (118 if n <= 40 else 104 if n <= 70 else 88)
    eyebrow = ""
    if scene.get("eyebrow"):
        eyebrow = (f'<div class="eyebrow">{SUN_SVG.replace("{COLOR}", T["sun"])}'
                   f'<span>{_esc(scene["eyebrow"])}</span></div>')
    footer = ('@tucsondailybrief' if scene.get("cta") else 'Tucson Daily Brief')
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{FONTS_HREF}">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  html,body{{width:{VW}px;height:{VH}px}}
  body{{background:{T['bg']};position:relative;overflow:hidden;
        font-family:'Newsreader',serif;-webkit-font-smoothing:antialiased;
        display:flex;flex-direction:column;justify-content:center;
        padding:150px 110px}}
  body::before{{content:"";position:absolute;inset:0;
    background:radial-gradient(900px 760px at 82% 12%, {T['glow']} 0%, transparent 60%);}}
  .eyebrow{{position:absolute;top:150px;left:110px;right:110px;
    display:flex;align-items:center;gap:24px}}
  .eyebrow svg{{width:58px;height:58px;flex:0 0 auto}}
  .eyebrow span{{font-weight:600;font-size:40px;letter-spacing:0.30em;
    text-transform:uppercase;color:{T['kicker']}}}
  .text{{position:relative;z-index:1;font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 144,'wght' 600,'SOFT' 0,'WONK' 1;
    color:{T['ink']};line-height:1.07;letter-spacing:-0.012em;font-size:{size}px}}
  .footer{{position:absolute;bottom:150px;left:110px;right:110px;
    border-top:4px solid {T['rule']};padding-top:34px;
    font-family:'Fraunces',serif;font-variation-settings:'opsz' 60,'wght' 600,'WONK' 1;
    font-size:42px;color:{T['accent']};letter-spacing:0.02em}}
</style></head><body>
  {eyebrow}
  <div class="text">{_esc(scene['text'])}</div>
  <div class="footer">{_esc(footer)}</div>
</body></html>"""


def render_scene_png(idx, scene):
    html_path = os.path.join(CARDS_DIR, f"scene-{idx:02d}.html")
    png = os.path.join(CARDS_DIR, f"scene-{idx:02d}.png")
    with open(html_path, "w") as f:
        f.write(scene_html(scene))
    subprocess.run(["chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", f"--force-device-scale-factor=1",
        f"--window-size={VW},{VH}", "--virtual-time-budget=7000",
        f"--screenshot={png}", f"file://{html_path}"], check=True, capture_output=True)
    os.remove(html_path)
    return png


def build_video(pngs, out_path):
    n = len(pngs)
    cmd = ["ffmpeg", "-y"]
    for p in pngs:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", str(SCENE_DUR), "-i", p]
    # chain xfade crossfades; offset_k = k*(SCENE_DUR - XFADE)
    fc, cur = "", "[0:v]"
    for k in range(1, n):
        off = round(k * (SCENE_DUR - XFADE), 3)
        out = f"[vx{k}]" if k < n - 1 else "[vout]"
        fc += f"{cur}[{k}:v]xfade=transition=fade:duration={XFADE}:offset={off}{out};"
        cur = out
    fc += "[vout]format=yuv420p[v]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium", "-movflags", "+faststart",
            out_path]
    subprocess.run(cmd, check=True, capture_output=True)


if __name__ == "__main__":
    os.makedirs(CARDS_DIR, exist_ok=True)
    print(f"rendering {len(SCRIPT)} scenes ...")
    pngs = [render_scene_png(i, s) for i, s in enumerate(SCRIPT)]
    out = os.path.join(CARDS_DIR, f"short-{SLUG}.mp4")
    print("stitching video ...")
    build_video(pngs, out)
    dur = len(SCRIPT) * SCENE_DUR - (len(SCRIPT) - 1) * XFADE
    sz = os.path.getsize(out) / (1024 * 1024)
    print(f"done -> {out}  (~{dur:.1f}s, {sz:.1f} MB, {VW}x{VH})")
