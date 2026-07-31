# Character Animation Stack — how to animate the mascot, and could it be a product?

**Status: research note, nothing started. GATED behind the short-form-video
distribution push** (same gate as everything in `ROADMAP.md`). Captured
2026-07-29/30 out of the HeyGen bake-off.

Two threads live here because they share one architecture analysis:

1. **Near term:** what should actually drive TDB's mascot videos.
2. **Speculative:** what it would take to build a HeyGen-alternative that
   specialises in stylised 2D character animation.

Prerequisite reading: `MASCOT.md` (the character, the proven patch pipeline,
the alignment lessons). Working files + all bake-off videos are in the
gitignored `design-explorations/bakeoff-2026-07-29/`.

---

## The central finding: generative video is the WRONG tool for cel art

Established empirically on 2026-07-29. HeyGen Avatar IV, driven by our accepted
saguaro, produced:

- a mouth that essentially **held one shape and wobbled it** — near-closed on
  only 8% of frames, and mouth aperture correlated **−0.12** with the speech
  envelope (i.e. not at all)
- **morphing arms and a head that changed width** across the clip
- letterboxed output that ignored the requested 9:16

Our own deterministic viseme pipeline, on the *same audio*, scored coeff of
variation **0.560 vs 0.318** and correlation **+0.24 vs −0.12**, and closed the
mouth on 44% of frames.

**Why:** a diffusion model hallucinates pixels. HeyGen needs that because it is
synthesising a photoreal human face which does not exist in its input — and it
is very good at it (the stock human avatar on `avatar_v` was excellent). For a
*drawn* character we already possess the artwork, so there is nothing to
imagine, and the model's freedom to invent becomes pure downside: drift.

Corroborating signal: our cactus photo avatar only ever offered
`supported_api_engines: ["avatar_iv","avatar_iii"]`, while stock human avatars
also offered `avatar_v`. The top-tier engine appears gated to well-formed human
faces.

**Design consequence:** the right architecture is *rig + timing + compositing*,
not *image → video model*. Deterministic, zero marginal cost, no drift.

---

## Three tiers, wildly different costs

### Tier 1 — no ML training at all (the one that works)

Essentially Adobe Character Animator's architecture, and half-built already:

| Stage | Have | Want |
|---|---|---|
| Phoneme timing | Rhubarb 1.14.0 (`~/.local/bin/rhubarb`) | WhisperX or Montreal Forced Aligner — true phoneme-level timestamps |
| Character rig | manual ImageMagick patches, eye-anchored | named layers (mouth / eyes / brows / head / body) |
| Compositor | `build_visemes.py` + `render9.py` | layer transforms, not just mouth swaps |
| Secondary motion | blink layer (proven) | procedural head sway, brow accents from prosody |

Runs on a laptop, no GPU, no per-render fee, nothing drifts. Ceiling is
charming limited/TV animation — which is *correct* for 30-second social, but it
is the ceiling.

Off-the-shelf ML that helps here with **zero training**:

- **WhisperX / Montreal Forced Aligner** — phoneme-level alignment, materially
  better than Rhubarb's 9-shape guess. Cheapest real upgrade available.
- **SAM-family segmentation** — auto-slice a character sheet into named layers.
  Rigging is the tedious part, so this is also the product wedge.
- **Prosody → expression heuristics** — emphasis drives brow raise / head nod.

### Tier 2 — fine-tune an existing open model (plausible solo project)

Do **not** train from scratch; adapt open weights. Candidates, several of which
already handle stylised or animal faces better than HeyGen: **LivePortrait,
SadTalker, AniPortrait, Hallo, LatentSync, MuseTalk**.

**Hardware on hand: NVIDIA RTX 5080 (16GB-class VRAM).** VRAM is the binding
constraint. That is comfortably enough for **LoRA / adapter training** on these
talking-head models; it is *not* enough for full fine-tunes of large video
diffusion models. Plan for LoRA, expect to quantise, verify actual VRAM with
`nvidia-smi` before sizing a run.

**The synthetic-data bootstrap — the genuinely clever bit.** Paired
(still image → talking video) *cartoon* data barely exists, which is why nobody
has trained for this. But the Tier-1 rig can **generate that dataset
synthetically, unlimited, with perfect ground-truth viseme labels.** The
deterministic pipeline becomes the data factory for the learned one. That is
the closest thing here to a defensible moat.

### Tier 3 — train a video model from scratch

Tens of millions of dollars, a research team, a large licensed video corpus.
Not a solo path. Recorded only to rule it out.

---

## Near-term alternatives worth testing before building anything

| Tool | Why it matters | Cost |
|---|---|---|
| **Adobe Character Animator** | Likely the actual answer. Auto-rigs from layer names; `Timeline → Compute Lip Sync Take From Audio`; hand-editable mouth shapes and hold durations; audio-only drive (no webcam needed). **The mouth sheet we generated is already the right input** — verify Adobe's exact required layer names before slicing. | already in Creative Cloud |
| **Hedra (Character-3)** | The one image→video model *explicitly* built for illustrations, cartoons and non-human faces; reviewers rate its lip-sync top of class. Direct apples-to-apples with our HeyGen result. | free tier; $30/mo Creator ≈ 11 min 720p, 6 credits/sec; has an API |
| **D-ID** | Called out specifically for animating cartoon illustrations from one image | — |
| **Pika** | Dedicated anime lip-sync mode | — |
| **Runway Act-One** | Transfers a real actor's performance onto a character image — excellent provenance. **But documented limitation: non-human characters don't work, humanoid do.** A face on a cactus column is exactly the risky case. | — |
| Cartoon Animator 5 / Moho / Live2D Cubism | Same family as Character Animator, more rigging control | — |

---

## If it became a product

**The moat is not the model — it is that nobody has productised 2D-mascot
animation for non-animators.** Character Animator does this well but is a
desktop pro tool with a real learning curve and an Adobe subscription.
"Upload a character sheet and a script, get a vertical short" is a genuine gap,
and Tier 1 reaches it without a single training run.

Honest caveats, recorded so future-me doesn't skip them:

- **This is a tools company, not a local-news company.** Different customers,
  different business. It is not an extension of TDB.
- Tier 1's quality ceiling is limited animation, not feature articulation.
- Portfolio angle: choosing the deterministic architecture over the fashionable
  generative one — and being able to explain *why* — is a stronger CTPO /
  Head-of-AI signal than having trained a model.

---

## Next experiments, cheapest first

1. **WhisperX vs Rhubarb A/B.** Same audio, same rig, compare viseme timelines.
   Free, runs today, and **improves the existing mascot pipeline regardless of
   what else happens** — this is the one to do first.
2. **Slice the mouth sheet into Character Animator layers** and drive it from
   audio. Confirms or kills the likely long-term answer at zero marginal cost.
3. **Hedra free tier** on `heygen-hero-1024.png` + `script.txt` — is any
   image→video model good at stylised faces, or is the whole category wrong?
4. **Only then** consider a LoRA on LivePortrait/SadTalker, with training data
   generated by the Tier-1 rig.

## Open items inherited from the bake-off

- Mouth sheet panel 7 (OO) generated a literal **"3" glyph** instead of a
  pucker — needs a one-panel regen; currently substituting OH.
- Ours has **no blink layer yet** on the new sheet (the proven blink patch came
  from the older pose art at a different scale).
- Still **demo resolution** (~150px face in a 418px panel). The high-res hero
  remains the real production prerequisite for every path.
- HeyGen wallet is down to **$0.47** — no further renders without a top-up.
- Working `heygen_render.py` gotcha worth keeping: the documented
  `POST /v3/assets` upload stores **no image dimensions**, so video creation
  then fails with `missing image dimensions`. The route that works is the
  legacy `upload.heygen.com/v1/asset` raw-binary upload, then create the photo
  avatar from the returned **URL**.
