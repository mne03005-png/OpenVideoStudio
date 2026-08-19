# Hero Demo Specification

**Status: specification only. No demo assets have been generated yet —
per instruction, final launch assets are produced only after this
specification is approved.**

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

**Requirements checklist:**
- [ ] Visually strong (no rough/broken frames — SDXL Lightning at low
      step counts doesn't reliably render every specific requested detail;
      pick or regenerate scenes that don't hit that gap, see
      `docs/COMMUNITY_TRACKS.md` Track C)
- [ ] Understandable with sound off (captions/on-screen labels for each
      stage, not narration-dependent)
- [ ] Demonstrates continuity (the character/environment visibly
      consistent across at least 2-3 keyframes/clips)
- [ ] Credible — no cherry-picked frame that misrepresents typical output
      quality; if adherence issues are visible, that's honest, not a
      launch blocker (see `docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`'s
      overclaiming failure mode)
- [ ] Shareable as a standalone clip (works without the README's
      surrounding context — self-explanatory via on-screen labels)
- [ ] Exportable in formats/aspect ratios that work across GitHub README
      (mp4/gif), X, Reddit, Hacker News (a plain link + the README's
      embedded version), YouTube, and Bilibili

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
