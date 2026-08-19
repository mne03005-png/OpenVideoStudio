# Hero Demo Specification

**Status: flagship demo produced.** See `examples/hero_demo/` — a real,
unedited run of this repository's own pipeline, meeting the requirements
checklist below (verified against the actual output, not assumed). Full
provenance and an honest QC note (one scene was regenerated for quality,
disclosed in detail) in `examples/hero_demo/README.md`. The two secondary
demos below are still spec-only — not generated, real remaining work.

## Why this matters

The README's first screen is the single highest-leverage piece of launch
content. A weak or confusing demo is one of the top launch failure modes
(see `docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`'s failure-mode list). The demo
has to prove the product works, not just claim it does.

## Flagship demo

**Goal:** show both **process** and **result** — a developer should
understand the whole pipeline shape in 20-40 seconds without narration.

**Format:** a single video, structured as a fast visual sequence through
each pipeline stage, ending on the final rendered clip. Not a slideshow of
static screenshots and not only the final MP4 in isolation — the point is
to make the *pipeline* itself legible, since "prompt to full video
pipeline" is the actual differentiator, not just "AI makes a video."

**Proposed flow** (matches the real pipeline stage order in
`creative/pipeline.py`, nothing invented):

1. **Prompt** (1-2s) — the literal text prompt on screen.
2. **Script** (2-3s) — a quick look at the generated `script.json` scene
   breakdown (title, logline, scene list) — proves this isn't just
   "prompt straight to image model."
3. **Character + Environment identity** (3-4s) — the generated
   `character_identity`/`environment_identity` fields, then a cut to the
   canonical reference elements they describe. This is V0.3's actual
   differentiator (identity generated once, reused verbatim) and deserves
   real screen time, not a rushed mention.
4. **Storyboard** (2-3s) — the per-scene breakdown (shot size, camera
   movement, narrative purpose).
5. **Keyframes** (3-4s) — the generated stills, shown as a quick sequence,
   visibly sharing identity/environment across scenes.
6. **Video generation** (3-4s) — keyframes animating into clips (a quick
   before/after: still frame -> motion).
7. **Voice + subtitles** (2-3s) — waveform or subtitle burn-in appearing.
8. **Final video** (remaining time) — the completed output, played at
   normal speed, uncut, long enough to actually judge quality.

**Target length:** 20-40 seconds total, weighted toward the final video
(at least 10-15s of uninterrupted final output — a demo that's all process
and two seconds of result undersells the product as much as the reverse).

**Requirements checklist, verified against the actual `examples/hero_demo/` output:**
- [x] Visually strong — strong first frame (astronaut walking toward
      camera down a lit corridor), no broken/garbled frames across all 6
      keyframes. One real low-motion moment on the first attempt at the
      final scene was caught and addressed by regenerating that scene
      with the pipeline's real scene-regeneration mechanism — disclosed
      in full in `examples/hero_demo/README.md`'s QC notes, not hidden.
- [x] Understandable with sound off — every scene has an on-screen
      subtitle caption; no stage requires narration to follow
- [x] Demonstrates continuity — wardrobe (white/red/blue suit) and
      environment palette (silver/blue metallic corridors) hold clearly
      across all 6 scenes; `storyboard.json`'s
      `narrative_quality_warnings: []` confirms no detected continuity
      breaks at the narrative level either
- [x] Credible — the QC note above *is* the credibility mechanism: a real
      adherence limitation was hit and disclosed, not edited around
      silently
- [x] Shareable as a standalone clip — subtitles make it self-explanatory
      without the README's surrounding text
- [x] Exportable — `final.mp4` (H.264/AAC, 9:16) plus a compact
      `preview.gif` for direct README embedding; both usable across every
      planned channel in `docs/LAUNCH_CONTENT.md`

## Secondary demo A — character continuity

**Purpose:** isolate and prove V0.3's actual claim (identity generated
once, reused verbatim) without the rest of the pipeline competing for
attention.

**Format:** side-by-side or fast-cut sequence of 3-4 keyframes from one
storyboard, same character, different scenes/actions, with the shared
identity text visible as an overlay or caption. Short — under 15 seconds.

## Secondary demo B — environment/style continuity

**Purpose:** same idea, for environment identity (architecture, lighting,
palette, camera language staying consistent across scenes that move around
within one setting).

**Format:** mirrors demo A, using `environment_identity`'s fields as the
overlay/caption instead of character fields.

## Production notes for whoever generates these (future step, not now)

- Use the real pipeline, unmodified, run against live Ollama + ComfyUI —
  no manually touched-up frames presented as pipeline output.
- Prefer a prompt/style that plays to the pipeline's current honest
  strengths (wardrobe/palette/environment continuity, per V0.3's verified
  results) rather than one that's likely to hit the known specific-object
  adherence gap (e.g., avoid requiring a specific small prop to appear
  exactly as described, the way the V0.3 acceptance run's glowing plant
  did not reliably render).
- Capture the intermediate JSON (script/storyboard) alongside the run so
  the "process" segments are real captured output, not mocked-up text.
- Once produced, demo assets belong in `examples/` (per
  `docs/PUBLIC_REPOSITORY_PLAN.md`) and get embedded in `README.md`.

## Approval gate

Do not generate final launch assets from this spec until a human
explicitly approves the flow described above (or an edited version of it).
