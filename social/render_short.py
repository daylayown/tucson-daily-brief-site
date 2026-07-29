#!/usr/bin/env python3
"""
TDB short-form video generator (v1) — text-only motion, series-aware.

Renders a sequence of vertical "beat" cards (1080x1920) and ffmpeg-stitches them
with crossfades into a muted-friendly 1080x1920 MP4 (locked "text-only motion
first" format; word-karaoke captions come later with a TTS+Deepgram pass).

Two launch series, each with its own look + own AI-generated track:
  - "Only in Tucson"      → warm terracotta theme  (feel-good / reach)
  - "Buried in the Agenda"→ dark investigative theme (civic finds / moat)

A clip = {series, script[]}. The script list is hand-built here; the real
pipeline will LLM-generate it from a story (brief item / agenda find).

Usage:
    python3 render_short.py [clip_key]     # default: buried-ov-bodycam
    python3 render_short.py --all
"""
import subprocess, os, sys, html as _html
from render_card import THEMES, FONTS_HREF, SUN_SVG, CARDS_DIR

VW, VH = 1080, 1920
SCALE = 3  # supersample scenes at 3x for crisp text, then downscale to spec
SCENE_DUR = 3.2
XFADE = 0.5
FPS = 30
MUSIC_VOLUME = 0.7
_HERE = os.path.dirname(os.path.abspath(__file__))


def _music(name):
    return os.path.join(_HERE, "assets/music", name)


# Series presets: theme + own AI track (ElevenLabs, commercial-licensed).
SERIES = {
    "only-in-tucson": {"theme": "terracotta", "music": _music("tdb-only-in-tucson.mp3")},
    "buried-in-the-agenda": {"theme": "dark", "music": _music("tdb-buried-in-the-agenda.mp3")},
    # "How it's made" BTS series — proven strong on IG. Reuses the terracotta
    # theme + the only-in-tucson track until it gets its own music.
    "behind-the-scenes": {"theme": "terracotta", "music": _music("tdb-only-in-tucson.mp3")},
    # Geographic editions ("What to Watch: {Town}") — one design, per-town
    # accent. Light/utility register (dark stays reserved for Buried in the
    # Agenda); footer raised into the Reels safe zone (IG/FB UI covers the
    # bottom ~340px). See SHORT-FORM-VIDEO.md § Geographic editions.
    "edition-marana": {"theme": "light", "music": _music("tdb-editions.mp3"),
                       "town": "Marana", "accent": "#d97048",  # adobe
                       "boundary": "marana", "safe_zone": True},
    "edition-orovalley": {"theme": "light", "music": _music("tdb-editions.mp3"),
                          "town": "Oro Valley", "accent": "#7a8b6f",  # sage
                          "boundary": "orovalley", "safe_zone": True},
}

# Reels/Stories UI safe zone: keep critical text out of the bottom ~340px and
# ~120px off the right edge. Editions render the footer at this offset; the
# older series keep the original 150px until their own safe-zone pass.
SAFE_BOTTOM = 380

CLIPS = {
    "only-in-tucson-moonbead": {
        "series": "only-in-tucson",
        "script": [
            {"eyebrow": "Only in Tucson", "text": "Tucson kids got to name two orphaned mountain lion cubs."},
            {"text": "Rescued in April — found in the wild without their mother."},
            {"text": "Meet Moonbead\nand Pretzel. 🦁", "big": True},
            {"text": "Named by kids from Beads of Courage, a nonprofit for children facing serious illness."},
            {"text": "Only in Tucson. 🌵", "cta": True, "nowrap": True},
        ],
    },
    "bts-podcast-voice": {
        "series": "behind-the-scenes",
        # The voice-clone reveal. Renders the muted/music version. The "killer"
        # variant layers ~4.8s of a real episode at the reveal beat (~8.2s) with
        # the music ducked — a manual ffmpeg post-pass, not part of this render:
        #   ffmpeg -y -i cards/short-bts-podcast-voice.mp4 -i voice-clip.mp3 \
        #     -filter_complex "[0:a]volume='if(between(t,8.0,13.3),0.15,1)':eval=frame[mus];\
        #       [1:a]aformat=channel_layouts=stereo,adelay=8200|8200[vo];\
        #       [mus][vo]amix=inputs=2:normalize=0:duration=first[a]" \
        #     -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k cards/short-bts-podcast-voiced.mp4
        # (grab voice-clip.mp3 from a clean sentence in the day's podcast MP3 on R2).
        "script": [
            {"eyebrow": "Behind the scenes", "text": "We publish a Tucson news podcast every single morning."},
            {"text": "An AI condenses the day’s news into a tight rundown."},
            {"text": "And the voice reading it to you?"},
            {"text": "It’s an AI clone of\nour founder’s own voice. 🎙️", "big": True},
            {"text": "New episode every\nmorning. 🎧", "cta": True},
        ],
    },
    "bts-tucson-mini": {
        "series": "behind-the-scenes",
        # How-it's-made for the weekly Tucson Mini. Arc: what it is -> local
        # vocab -> your week's real news -> concrete news-tie example -> the
        # human-fact-check reveal (trust beat) -> CTA. Honest per the no-
        # fabrication bar: we DO fact-check every clue by hand before it ships.
        "script": [
            {"eyebrow": "Behind the scenes", "text": "Every Sunday, we build a\ntiny Tucson crossword."},
            {"text": "It starts with 160+ genuinely\nTucson answers. 🌵"},
            {"text": "Then we fold in the real news\nfrom your week here."},
            {"text": "So a clue can wink at the news —\nlike Dante’s farewell whiskey dinner. 🥃"},
            {"text": "AI drafts it —\na human checks every clue.", "big": True},
            {"text": "Free every Sunday in\nour newsletter. 🎟️", "cta": True},
        ],
    },
    "buried-ov-bodycam": {
        "series": "buried-in-the-agenda",
        "script": [
            {"eyebrow": "Buried in the Agenda", "text": "Oro Valley is changing what it costs to see police body-camera footage."},
            {"text": "Before:\n$25 per video."},
            {"text": "Now:\n$46 per hour of footage reviewed."},
            {"text": "It’s all public record."},
            {"text": "We read every agenda\nso you don’t have to.", "cta": True},
        ],
    },
}


def _esc(s):
    return _html.escape(s, quote=False).replace("\n", "<br>")


def _boundary_svg(boundary_key, stroke, w=760, h=980):
    """Town boundary as a hand-drawn-style SVG (stroke only, all rings) with a
    dropped pin at the largest ring's centroid. Polygons are cached Census
    TIGERweb incorporated-place geometry (lon/lat rings) in
    assets/boundaries/{key}.json — no map tiles, no attribution burden."""
    import json as _json, math
    path = os.path.join(_HERE, "assets/boundaries", f"{boundary_key}.json")
    rings = _json.load(open(path))["rings"]
    pts = [p for ring in rings for p in ring]
    lats = [p[1] for p in pts]
    # Equirectangular with cos(mid-lat) x-correction, fit into w x h, pad 6%.
    k = math.cos(math.radians((min(lats) + max(lats)) / 2))
    xs = [p[0] * k for p in pts]
    ys = lats
    sx, sy = max(xs) - min(xs), max(ys) - min(ys)
    scale = min(w * 0.88 / sx, h * 0.88 / sy)
    ox = (w - sx * scale) / 2 - min(xs) * scale
    oy = (h - sy * scale) / 2 + max(ys) * scale

    def xy(p):
        return (round(p[0] * k * scale + ox, 1), round(oy - p[1] * scale, 1))

    paths = []
    for ring in rings:
        d = "M" + " L".join(f"{x},{y}" for x, y in (xy(p) for p in ring)) + " Z"
        paths.append(f'<path d="{d}" fill="none" stroke="{stroke}" '
                     f'stroke-width="7" stroke-linejoin="round" '
                     f'stroke-linecap="round" opacity="0.95"/>')
    big = max(rings, key=len)
    cx = sum(xy(p)[0] for p in big) / len(big)
    cy = sum(xy(p)[1] for p in big) / len(big)
    pin = (f'<g transform="translate({cx:.0f},{cy:.0f})">'
           f'<path d="M0,0 C-34,-52 -34,-96 0,-96 C34,-96 34,-52 0,0 Z" '
           f'fill="{stroke}"/><circle cx="0" cy="-62" r="16" fill="#251c17"/></g>')
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(paths)}{pin}</svg>')


def _page(theme, body, extra_css=""):
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{FONTS_HREF}">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  html,body{{width:{VW}px;height:{VH}px}}
  body{{background:{theme['bg']};position:relative;overflow:hidden;
        font-family:'Newsreader',serif;-webkit-font-smoothing:antialiased}}
  body::before{{content:"";position:absolute;inset:0;
    background:radial-gradient(900px 760px at 82% 12%, {theme['glow']} 0%, transparent 60%);}}
  {extra_css}
</style></head><body>{body}</body></html>"""


def scene_html(scene, theme, series=None):
    series = series or {}
    accent = series.get("accent") or theme["accent"]
    foot_b = SAFE_BOTTOM if series.get("safe_zone") else 150
    kind = scene.get("kind")

    if kind == "boundary":
        # Cold-open: town outline in the series accent on the dusk ground —
        # instant geographic signal for both the viewer and the algorithm.
        dusk = {"bg": "#251c17", "glow": "rgba(199,91,57,0.22)"}
        svg = _boundary_svg(series["boundary"], accent)
        body = f"""
  <div class="kicker">{SUN_SVG.replace("{COLOR}", accent)}<span>{_esc(scene.get("kicker", "What to Watch"))}</span></div>
  <div class="map">{svg}</div>
  <div class="footer">Tucson Daily Brief</div>"""
        css = f"""
  .kicker{{position:absolute;top:170px;left:110px;right:110px;display:flex;
    align-items:center;gap:24px;z-index:2}}
  .kicker svg{{width:58px;height:58px;flex:0 0 auto}}
  .kicker span{{font-weight:600;font-size:44px;letter-spacing:0.30em;
    text-transform:uppercase;color:{accent};font-family:'Newsreader',serif}}
  .map{{position:absolute;inset:0;display:flex;align-items:center;
    justify-content:center;z-index:1}}
  .footer{{position:absolute;bottom:{foot_b}px;left:110px;right:120px;
    border-top:4px solid rgba(250,244,232,0.25);padding-top:34px;
    font-family:'Fraunces',serif;font-variation-settings:'opsz' 60,'wght' 600,'WONK' 1;
    font-size:42px;color:{accent};letter-spacing:0.02em}}"""
        return _page(dusk, body, css)

    if kind == "title":
        town = scene.get("town", series.get("town", ""))
        body = f"""
  <div class="wrap">
    <div class="eyebrow">{SUN_SVG.replace("{COLOR}", accent)}<span>What to Watch</span></div>
    <div class="town">{_esc(town.upper())}</div>
    <div class="bar"></div>
    <div class="sub">{_esc(scene.get("sub", ""))}</div>
  </div>
  <div class="footer">Tucson Daily Brief</div>"""
        css = f"""
  .wrap{{position:relative;z-index:1;height:100%;display:flex;flex-direction:column;
    justify-content:center;padding:150px 110px}}
  .eyebrow{{display:flex;align-items:center;gap:24px;margin-bottom:56px}}
  .eyebrow svg{{width:58px;height:58px;flex:0 0 auto}}
  .eyebrow span{{font-weight:600;font-size:44px;letter-spacing:0.30em;
    text-transform:uppercase;color:{accent}}}
  .town{{font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 144,'wght' 700,'SOFT' 0,'WONK' 1;
    color:{theme['ink']};font-size:170px;line-height:0.98;letter-spacing:-0.015em}}
  .bar{{width:280px;height:14px;background:{accent};border-radius:7px;margin:52px 0}}
  .sub{{font-family:'Newsreader',serif;font-size:58px;color:{theme['meta']}}}
  .footer{{position:absolute;bottom:{foot_b}px;left:110px;right:120px;
    border-top:4px solid {theme['rule']};padding-top:34px;
    font-family:'Fraunces',serif;font-variation-settings:'opsz' 60,'wght' 600,'WONK' 1;
    font-size:42px;color:{accent};letter-spacing:0.02em}}"""
        return _page(theme, body, css)

    if kind == "ticker":
        items = "".join(
            f'<div class="item"><span class="dot"></span><span>{_esc(t)}</span></div>'
            for t in scene.get("items", []))
        body = f"""
  <div class="wrap">
    <div class="head">Also on the radar</div>
    {items}
  </div>
  <div class="footer">Tucson Daily Brief</div>"""
        css = f"""
  .wrap{{position:relative;z-index:1;height:100%;display:flex;flex-direction:column;
    justify-content:center;padding:150px 110px;gap:64px}}
  .head{{font-weight:600;font-size:44px;letter-spacing:0.30em;
    text-transform:uppercase;color:{accent};margin-bottom:8px}}
  .item{{display:flex;gap:36px;align-items:flex-start}}
  .dot{{flex:0 0 auto;width:26px;height:26px;border-radius:50%;
    background:{accent};margin-top:26px}}
  .item span:last-child{{font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 144,'wght' 550,'SOFT' 0,'WONK' 1;
    color:{theme['ink']};font-size:66px;line-height:1.16}}
  .footer{{position:absolute;bottom:{foot_b}px;left:110px;right:120px;
    border-top:4px solid {theme['rule']};padding-top:34px;
    font-family:'Fraunces',serif;font-variation-settings:'opsz' 60,'wght' 600,'WONK' 1;
    font-size:42px;color:{accent};letter-spacing:0.02em}}"""
        return _page(theme, body, css)

    # Default: the original text scene (+ optional small "meta" line above the
    # footer, used by edition CTA scenes for the meeting time).
    n = len(scene["text"])
    if scene.get("big"):
        size = 132
    elif scene.get("nowrap"):
        size = 96
    else:
        size = 118 if n <= 40 else 104 if n <= 70 else 88
    nowrap = "white-space:nowrap;" if scene.get("nowrap") else ""
    eyebrow = ""
    if scene.get("eyebrow"):
        eyebrow = (f'<div class="eyebrow">{SUN_SVG.replace("{COLOR}", theme["sun"])}'
                   f'<span>{_esc(scene["eyebrow"])}</span></div>')
    meta = ""
    if scene.get("meta"):
        meta = f'<div class="meta">{_esc(scene["meta"])}</div>'
    footer = '@tucsondailybrief' if scene.get("cta") else 'Tucson Daily Brief'
    body = f"""
  {eyebrow}
  <div class="text">{_esc(scene['text'])}</div>
  {meta}
  <div class="footer">{_esc(footer)}</div>"""
    css = f"""
  body{{display:flex;flex-direction:column;justify-content:center;padding:150px 110px}}
  .eyebrow{{position:absolute;top:150px;left:110px;right:110px;
    display:flex;align-items:center;gap:24px}}
  .eyebrow svg{{width:58px;height:58px;flex:0 0 auto}}
  .eyebrow span{{font-weight:600;font-size:40px;letter-spacing:0.30em;
    text-transform:uppercase;color:{theme['kicker']}}}
  .text{{position:relative;z-index:1;font-family:'Fraunces',serif;
    font-variation-settings:'opsz' 144,'wght' 600,'SOFT' 0,'WONK' 1;
    color:{theme['ink']};line-height:1.07;letter-spacing:-0.012em;font-size:{size}px;{nowrap}}}
  .meta{{position:absolute;bottom:{foot_b + 110}px;left:110px;right:120px;
    font-family:'Newsreader',serif;font-size:46px;color:{theme['meta']}}}
  .footer{{position:absolute;bottom:{foot_b}px;left:110px;right:120px;
    border-top:4px solid {theme['rule']};padding-top:34px;
    font-family:'Fraunces',serif;font-variation-settings:'opsz' 60,'wght' 600,'WONK' 1;
    font-size:42px;color:{accent if series.get("safe_zone") else theme['accent']};letter-spacing:0.02em}}"""
    return _page(theme, body, css)


def render_scene_png(idx, scene, theme, series=None):
    html_path = os.path.join(CARDS_DIR, f"scene-{idx:02d}.html")
    big = os.path.join(CARDS_DIR, f"scene-{idx:02d}.{SCALE}x.png")
    png = os.path.join(CARDS_DIR, f"scene-{idx:02d}.png")
    with open(html_path, "w") as f:
        f.write(scene_html(scene, theme, series))
    # Supersample at SCALE x, then downscale to spec with a sharp filter — same
    # treatment as the image cards (render_card.py); a 1x screenshot reads soft.
    subprocess.run(["chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", f"--force-device-scale-factor={SCALE}",
        f"--window-size={VW},{VH}", "--virtual-time-budget=7000",
        f"--screenshot={big}", f"file://{html_path}"], check=True, capture_output=True)
    subprocess.run(["convert", big, "-filter", "Lanczos", "-resize", f"{VW}x{VH}",
        "-unsharp", "0x0.6+0.7+0", "-strip", png], check=True, capture_output=True)
    os.remove(big)
    os.remove(html_path)
    return png


def build_video(pngs, out_path, music=None, durs=None):
    n = len(pngs)
    durs = durs or [SCENE_DUR] * n
    total = sum(durs) - (n - 1) * XFADE
    cmd = ["ffmpeg", "-y"]
    for p, d in zip(pngs, durs):
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", str(d), "-i", p]
    if music and os.path.exists(music):
        cmd += ["-stream_loop", "-1", "-i", music]
    fc, cur = "", "[0:v]"
    off_acc = 0.0
    for k in range(1, n):
        off_acc += durs[k - 1] - XFADE
        off = round(off_acc, 3)
        out = f"[vx{k}]" if k < n - 1 else "[vout]"
        fc += f"{cur}[{k}:v]xfade=transition=fade:duration={XFADE}:offset={off}{out};"
        cur = out
    fc += "[vout]format=yuv420p[v]"
    maps = ["-map", "[v]"]
    if music and os.path.exists(music):
        fade_out = round(total - 1.5, 3)
        fc += (f";[{n}:a]volume={MUSIC_VOLUME},afade=t=in:st=0:d=1.0,"
               f"afade=t=out:st={fade_out}:d=1.5[a]")
        maps += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-filter_complex", fc, *maps, "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium", "-movflags", "+faststart", out_path]
    subprocess.run(cmd, check=True, capture_output=True)


def render_from_config(slug, series_key, script):
    """Render an arbitrary clip (used by the automated generator)."""
    series = SERIES[series_key]
    theme = THEMES[series["theme"]]
    print(f"[{slug}] rendering {len(script)} scenes ({series_key}) ...")
    pngs = [render_scene_png(i, s, theme, series) for i, s in enumerate(script)]
    out = os.path.join(CARDS_DIR, f"short-{slug}.mp4")
    durs = [s.get("dur") or series.get("scene_dur") or SCENE_DUR for s in script]
    build_video(pngs, out, music=series["music"], durs=durs)
    dur = sum(durs) - (len(script) - 1) * XFADE
    sz = os.path.getsize(out) / (1024 * 1024)
    print(f"  done -> {out}  (~{dur:.1f}s, {sz:.1f} MB, {VW}x{VH})")
    return out


def render_clip(slug):
    clip = CLIPS[slug]
    return render_from_config(slug, clip["series"], clip["script"])


if __name__ == "__main__":
    os.makedirs(CARDS_DIR, exist_ok=True)
    arg = sys.argv[1] if len(sys.argv) > 1 else "buried-ov-bodycam"
    if arg == "--all":
        for k in CLIPS:
            render_clip(k)
    else:
        render_clip(arg)
