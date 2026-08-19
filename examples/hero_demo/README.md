# Hero Demo

A real, unedited run of the actual release-candidate pipeline — not a
mockup, not hand-touched-up frames. Produced against live Ollama +
ComfyUI using this repository's own code, following the spec in
`docs/HERO_DEMO_SPEC.md`.

## What's here

| File | In git? | Notes |
|---|---|---|
| `final.mp4` | **No** (gitignored — see below) | The complete output: 32.9s, 448×768, H.264/AAC, 19 MB |
| `preview.gif` | Yes | Compact 2×-speed, 8fps, 240px-wide preview for embedding directly in the README — 3.4 MB |
| `keyframes/*.png` | **No** (gitignored) | All 6 full-resolution SDXL keyframes, one per scene |
| `storyboard.json` | Yes | The complete generated storyboard: character/environment identity, per-scene prompts, narrative purposes |
| `script.json` | Yes | The generated script this storyboard was built from |

**Why `final.mp4` and the keyframes aren't committed:** 19 MB (and
another ~3 MB of keyframe PNGs) is real content, not a fabrication, but
it's not the kind of thing that belongs in git history forever — every
future clone would carry it permanently. The plan is to upload
`final.mp4` and the keyframes as GitHub release assets or attach them
directly in a README edit on GitHub.com (which hosts the file on GitHub's
own CDN and gives it a permanent URL) at actual launch time — see
`docs/GITHUB_LAUNCH_SETUP.md`. Until then, both are present on disk in
this directory for review; `.gitignore` just keeps them out of the
commit.

## Provenance

- **Prompt:** "A lone astronaut explores the quiet, sunlit corridors of
  an abandoned space station, drifting past reflective windows overlooking
  Earth, searching for a way home."
- **Style:** cinematic sci-fi · **Language:** en · **Aspect ratio:** 9:16
- **Target duration:** 30s → **actual:** 32.856s (9.5% overshoot,
  consistent with this pipeline's known LTX frame-count-quantization
  behavior, documented in `CHANGELOG.md`)
- **Generated title:** "Echoes of Home" (LLM-generated, not hand-picked)
- **Scenes:** 6, `has_recurring_character: true`,
  `narrative_quality_warnings: []` (the storyboard's own soft-QC found
  nothing to flag)
- **`final.mp4` SHA-256:**
  `29735D454C0E7EB26EE6BFF9423072563EECF980D421B5D166A2A267D3C22FEA`

## QC notes (read this before assuming "zero issues")

- All 6 keyframes generated on the first attempt (no retries needed).
- All 6 clips passed the pipeline's own freeze-detection QC
  (`_detect_freeze_seconds`, 0.6s threshold) — `clip_freeze_seconds: 0.0`
  for every scene in the final `storyboard.json`.
- **One judgment call worth disclosing:** scene 6's *first* generated
  clip technically passed that QC threshold but was, on direct visual
  inspection, very close to a static shot for its final ~3 seconds — a
  real instance of the LTX-Video low-motion behavior this project has
  documented before (see `docs/COMMUNITY_TRACKS.md` Track G's "final-video
  freeze QC" gap: today's QC checks raw pre-retime clips, not the
  fully-assembled final video). Rather than ship that or hand-edit
  around it, the same scene was regenerated three more times with
  different seeds using the pipeline's real, documented scene-level
  regeneration mechanism (edit `storyboard.json`, clear the scene's
  `clip_path`, rerun with `force=True`) — all three real pipeline
  outputs, no synthetic frames. The clip actually used shows real,
  visible motion in roughly its first half (the astronaut turning from
  facing camera to facing the window) and is a genuine improvement over
  the original attempt — **but it is not fully dynamic for its whole
  length**: after the turn completes, the shot settles into a held final
  pose for its last second or so, which independent review of this exact
  clip correctly flagged as still-present low motion. The honest
  characterization is "a real motion beat followed by a brief settle,"
  not "fully solved" — every frame in `final.mp4` came from the real
  pipeline either way; this note exists so neither the improvement nor
  its limits are overstated.
- **Character/environment identity does not hold well across scenes in
  this run — this is a real, visible instance of a known, unsolved
  limitation, not a minor detail.** Comparing all 6 keyframes directly:
  hair color and style change scene to scene (silver-cropped in scene 1,
  dark brown in scene 2, pale blue-toned in scene 3, near-white in scene
  4, dirty-blonde in scene 5), facial structure is visibly not the same
  person across several scenes, and even the suit's specific accent
  colors/placement shift (red/blue striped patches vs. a plain red collar
  vs. a blue shoulder patch vs. red diagonal straps) rather than staying
  fixed. What *does* hold, loosely: every scene shows a person in a
  predominantly white spacesuit in a metallic/silver-blue space-station
  environment — a broad aesthetic consistency, not a precise
  identity-continuity one. `storyboard.json`'s `narrative_quality_warnings: []`
  reflects the *narrative* soft-QC (duplicate purposes, missing
  continuity notes) finding nothing — it does not and cannot validate
  visual facial identity, and shouldn't be read as having done so. This
  demo is, honestly, real evidence for why Track C (Character
  Consistency) exists as an open research track: today's prompt-text-only
  identity approach (generate the description once, reuse the same text
  every scene) keeps the *words* every scene's prompt receives identical,
  but SDXL Lightning at low step counts does not reliably turn identical
  words into a visually identical face across independent generations.
  See `docs/COMMUNITY_TRACKS.md` Track C for what a real fix (reference-image
  conditioning) would need.

## Reproducing this

```bash
cd studio
python -c "
from creative.pipeline import new_run, run_to_storyboard, approve_storyboard, run_after_review, run_dir_for
from pathlib import Path
runs_root = Path('runs')
state = new_run(runs_root, 'A lone astronaut explores the quiet, sunlit corridors of an abandoned space station, drifting past reflective windows overlooking Earth, searching for a way home.', 30.0, 'cinematic sci-fi', aspect_ratio='9:16', language='en')
run_dir = run_dir_for(runs_root, state.run_id)
state = run_to_storyboard(run_dir, state)
state = approve_storyboard(run_dir, state)
state = run_after_review(run_dir, state)
print(run_dir)
"
```

Output won't be pixel-identical (the LLM and image/video models aren't
seeded for exact reproducibility across runs), but should be structurally
the same: a 6-ish-scene video following an astronaut character through a
space-station environment. Whether the character's specific appearance
holds together better or worse than this run's is exactly the kind of
variance the QC notes above are honest about — don't expect a
reproduction to fix that on its own.
