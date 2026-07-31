# TDB Mascot — the friendly saguaro (in progress, parked 2026-07-28)

A brand character for TDB's **light content only**: Spotted, Around Town,
Opening Soon, Desert 101, welcome/subscribe moments, and (eventually, as a
controlled step) the geographic editions. **Never fronts accountability
journalism, public safety, or tragedy coverage** — same reserved-register
logic that keeps the dark theme exclusive to Buried in the Agenda. No name
yet (shortlist below). Not yet public — see the repo-is-public warning at
the bottom before committing any art.

## Why a mascot (decision trail, all 2026-07-28)

- User wanted more than "animated text" video but rejected both a synthetic
  human avatar (fabricated provenance — collides with the no-fabrication bar
  and the accountable-human IG principle) and an AI twin of the founder (fine
  in principle; not pursued). A **clearly-fictional cartoon mascot has zero
  deception surface** — nobody thinks the cactus is a correspondent — and the
  no-AI-imagery rule doesn't apply in spirit: a designed illustration depicts
  nothing real.
- First attempt: hand-authored SVG "Correspondent" (glasses + rolled agenda,
  5 iterations, `design-explorations/mascot-concepts-v1.html` →
  `mascot-correspondent-v5.html`). **Rejected by user** — too flat/craft-
  limited. Kept for history; do not resume that direction.
- Locked direction instead: **"90s animated-feature sidekick who happens to
  be a saguaro."** No props, no glasses, no flower, no news motif. BIG
  expressive eyes — explicitly chosen because *eyes that animate are the
  emotional engine*. Concepted via ChatGPT image gen from the prompt kit
  below; two generated sheets accepted as the working model.

## Current assets (ALL LOCAL-ONLY in `design-explorations/`, gitignored)

| File | What |
|---|---|
| `mascot-gen-expressions.png` | First accepted gen: 9-expression exploration (1258×1258) |
| `mascot-gen-modelsheet.png` | **The working model sheet** (1448×1086): turnaround (front/¾/side/back) + 5 consistent expressions (smile, delight, surprised, skeptical, closed-eyes) |
| `pose-smile.png` `pose-delight.png` `pose-surprised.png` `pose-skeptical.png` `pose-closedeyes.png` | Sliced bottom-row poses, ~289×506 each — **demo resolution only** |
| `frame-blink.png` | Composited blink frame: closed-eye patch on the smile body |
| `blink-mask.png`, `eyes-closed-patch.png`, `blink-list.txt` | Intermediates for the blink build |
| `mascot-blink-demo.mp4` / `.gif` | **The proof of life**: 16.8s idle loop, natural blink spacing + one double-blink |
| `mascot-concepts-v1.html`, `mascot-correspondent-v2..v5.html/.png` | The rejected SVG direction (history) |

Originals also in `~/Downloads/ChatGPT Image Jul 28, 2026, 07_12_13 PM.png`
and `..._07_21_09 PM.png`. **These local files are the only copies** —
consider a private backup (NOT this repo — see warning below).

## The proven animation pipeline (no per-use AI, fully deterministic)

Demonstrated working 2026-07-28 with the blink loop:

1. **Patch compositing.** Any facial variant = a feathered elliptical patch
   from one drawing composited onto the base pose. The blink was built with:
   ```bash
   magick -size 289x506 xc:black -fill white \
     -draw "ellipse 124,144 62,56 0,360" -blur 0x7 blink-mask.png
   magick pose-closedeyes.png blink-mask.png -alpha off \
     -compose CopyOpacity -composite eyes-closed-patch.png
   magick pose-smile.png eyes-closed-patch.png -geometry +37-11 -composite frame-blink.png
   ```
   (Eye midpoints: smile ≈ (161,148), closed ≈ (124,159) → offset +37,−11.
   Lesson: make the mask's solid core big enough that the feather falls on
   plain green, not on the eye whites — a small core ghosts the open eyes
   through the feather.)
2. **Loops via ffmpeg concat** with per-frame durations (see
   `blink-list.txt`): open 2.0s / blink 0.12s / … / double-blink cluster.

   **⚠️ Align patches on the EYES (head position), never on the mouth.**
   Learned 2026-07-29 building the talking demo. The `surprised` pose has its
   mouth drawn ~11px lower on the face than `smile` does, so mouth-anchored
   alignment threw the whole head ~15px out of register and the mask's feather
   bled mismatched eyes and cheek blush over the base. Eye-anchored alignment
   keeps every feature in register, so any feather bleed is benign — it bleeds
   matching content. Measured pupil anchors (289×506 pose space):
   `smile` eyecx 167.0 / pupil-floor 171.5 · `delight` 175.8 / 168.0 ·
   `surprised` 166.3 / 166.5 → eye-align shifts `delight` (−9,+4),
   `surprised` (+1,+5). Derive these by dark-blob detection, don't eyeball them.

   Corollary: shift the **source pose**, then cut with ONE fixed mask. Shifting
   the *mask* per viseme is what walks the feather up into the eyes.
3. **Lip-sync — timing engine PROVEN 2026-07-29.** **Rhubarb 1.14.0 is
   installed** (`~/.local/bin/rhubarb` → `~/.local/share/rhubarb`; GitHub
   release, not in the Arch repos). It produced 237 viseme cues across all 9
   Preston-Blair shapes from a 36s track: `rhubarb -f json -o visemes.json
   --extendedShapes GHX --dialogFile line.txt vo.wav` (wants mono 16-bit WAV;
   passing the dialog text improves accuracy). `render.py` in
   `design-explorations/bakeoff-2026-07-29/` maps cues → mouth states → frames
   → 9:16 H.264.

   Two findings from the first end-to-end render:
   - **Enforce a minimum 2-frame hold.** Raw Rhubarb output gave 18 one-frame
     mouth changes out of 179 runs, which reads as buzzy flicker, not speech.
     `apply_min_hold()` absorbs short runs into the preceding state — 0 one-frame
     runs after.
   - **Three mouth shapes is not enough.** Standing in with closed / round-O /
     wide-open (cut from `smile` / `surprised` / `delight`) produced clean,
     pixel-stable compositing but mechanical alternation, and the mouth sits
     open ~91% of frames with no true slight-open. **This is the evidence that
     the 9-viseme sheet is required, not optional.**

4. **The viseme system as designed:** ~9 mouth
   shapes (rest, M/B/P closed, slight-open, AH, EE, OH, OO, F/V, L) as
   patches over the hero pose; timing from **Rhubarb Lip Sync** (open
   source, offline, audio→viseme timeline) or ElevenLabs character
   timestamps; a script swaps mouth patches per frame; blinks + brow raises
   layer independently on top. Quality register = charming limited/TV
   animation, not Disney-feature articulation — correct for 30s social.
5. **Voice: a distinct licensed ElevenLabs character voice — NOT the
   founder's clone** (`Apm0doIVFfoMAodKmEYB`, used by `run_podcast.sh`). The
   clone is the accountable-founder surface (podcast, BTS); the mascot must
   never blur into it. **Note the repo's ElevenLabs key is TTS-scoped only** —
   it lacks `voices_read`, so the voice library can't be enumerated from the
   CLI; pick the character voice in the ElevenLabs UI and record the ID here.
   Stock voice IDs do work for throwaway timing tracks.

## Resume checklist (in order)

1. **High-res hero pose** — the current slices (~289px wide) don't survive
   1080p. Regenerate the winning front pose as a single large image (or
   upscale), THEN cut production layers from it. Everything downstream
   depends on this.
2. **Mouth-shape sheet** on that exact high-res face (prompt below).
3. **Matting** — transparent-background cutout (flat cream bg makes this
   easy with flood-fill/chroma matting) so he can sit on cards and video
   scenes.
4. **Name.** Shortlist: **Scoop** (the Saguaro; session favorite), Needles,
   Rita (Santa Ritas / Rita Ranch), Gary the Saguaro.
5. **Rhubarb integration** + the mouth-patch render script; pick the
   character voice.
6. **Write usage rules into `SOCIAL-CARDS.md`** when locked, and move final
   production assets to `social/assets/mascot/` (see warning first).
7. **Debut as a controlled step:** editions run text-only for baseline weeks
   first; mascot then enters BOTH editions the same week so
   `social/editions-log.md` captures a clean before/after (variable-isolation
   discipline). Ready-made IG intro moment: "meet the newest member of the
   TDB newsroom."

## Prompt kit (for further ChatGPT/imagegen riffing)

**Master character prompt** — friendly saguaro, 1990s hand-drawn feature
style, big expressive eyes with lids/brows for full emotional range, no
props/clothing/flower/glasses, warm sage/olive cel shading, cream bg, clean
varied-weight ink line, character-sheet layout, no text. (Full text in the
2026-07-28 session; reconstruct from these constraints — the two accepted
sheets are themselves the best reference input now.)

**Consistency pass:** "Using this exact character design, create a clean
character model sheet: identical proportions in every drawing … front,
three-quarter, side, back … then the identical front-view body in five
expressions …" — attach the accepted sheet as reference; re-run naming the
drifted panel if proportions wander.

**Mouth sheet (next gen to run):**
> Using this exact character, create a mouth-shape reference sheet for
> animation: the identical saguaro face repeated nine times in a grid,
> changing ONLY the mouth: 1 closed relaxed smile, 2 lips pressed (M/B/P),
> 3 slightly open, 4 open "AH", 5 wide smile "EE", 6 round open "OH",
> 7 small pucker "OO", 8 top teeth on lower lip "F/V", 9 open with tongue
> visible "L". Same eyes, same brows, same head angle and proportions in
> every panel, plain warm cream background, no text.

**Standing avoid-list:** glasses, flowers, hats, props, clothing, news
motifs, photorealism, menacing spines, neon greens, tiny dot eyes, 3D
render, busy backgrounds, text/logos.

## ⚠️ Repo-is-public warning

This repo serves tucsondailybrief.com and is publicly readable. **Do not
commit mascot art before the character debuts** — pre-release concepts would
leak (and the final asset set should be committed deliberately, post-debut,
if at all). Keep working art in `design-explorations/` (gitignored) and back
it up privately (e.g. the notes repo outside this one, or Drive).
