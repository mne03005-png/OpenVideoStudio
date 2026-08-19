# Community Tracks

OpenVideoStudio's core is deliberately small: a working, tested,
maintainer-led pipeline from prompt to finished video. Everything past
that core is scoped as an independently claimable community track. This
document exists so a contributor can find "the AI Art person," "the
platform-support person," or "the model-gateway person" version of this
project and know exactly what's theirs to build, what boundaries to
respect, and where to start.

**Rule for maintainers as much as contributors: do not build out an entire
track solo before launch.** A track with everything already done is not a
contribution opportunity, it's a fait accompli. Ship the core, seed each
track with real starter issues, and let the track grow through PRs.

---

## CORE — Maintainer-Led

**Owns:** `studio/creative/` (script → storyboard → identity → keyframes →
clips → narration → subtitles → pipeline orchestration),
`studio/providers/base.py` (the provider interfaces every provider type
must implement), `studio/core/` (shared FFmpeg/audio/scoring utilities
used by both the AI Creation pipeline and Media Remix), the review-gate
and resumability model in `creative/pipeline.py`.

**Stability bar:** every change here needs tests, and a change that breaks
the provider interface contract breaks every downstream track. Changes to
`providers/base.py`'s abstract interfaces, `CreativeRunState`'s stage
model, or the review-gate mechanics require a maintainer-approved design
discussion first (open a GitHub Discussion, not straight to a PR).

**What must NOT change without discussion:** the provider interface
contracts (`LLMProvider.generate`, `ImageProvider.generate_image`,
`VideoProvider.generate_video`, `TTSProvider`'s interface) — every
provider adapter across every track depends on these staying stable.
Breaking them silently breaks every community track at once.

---

## TRACK A — AI Art / Visual Development

**Vision:** OpenVideoStudio's keyframe generation today is "one prompt,
one image, hope for consistency." The long-term vision is a real AI Art
Director layer: character bibles, environment bibles, non-destructive
iteration, inpainting/outpainting, pose control, and reference-image
conditioning — without rebuilding Krita or Photoshop from scratch.

**Boundaries:** this track owns everything *upstream* of a finished
keyframe PNG. It does not own video generation, narration, or editing.

**Relevant extension interfaces:** `providers/base.py`'s `ImageProvider`;
`creative/identity.py`'s `format_character_identity` /
`format_environment_identity` (the deterministic-text pattern any richer
identity system should preserve — code formats identity text, the LLM
never re-derives it per scene); `providers/image/comfyui_sdxl.py`'s
already-present but unwired `reference_image_path`/`denoise` img2img path.

**Relevant ecosystems to research/integrate, not rebuild:** Krita +
[krita-ai-diffusion](https://github.com/Acly/krita-ai-diffusion),
ComfyUI's own IPAdapter/ControlNet/InstantID node ecosystem, InvokeAI.

**Starter issues (good first issue):**
- `[Art Studio] Character Bible data model` — a structured, versioned
  on-disk schema for a character's identity beyond the current single
  `character_identity` dict (multiple characters per story, reference
  images, revision history).
- `[Art Studio] Environment Bible` — same idea for recurring locations.
- `[Art Studio] Wardrobe library` / `[Art Studio] Prop library` — reusable
  named assets a character/environment bible can reference instead of
  re-describing inline every time.

**Help wanted (intermediate):**
- `[Art Studio] Character candidate selector` — generate N candidate
  reference portraits from `identity.py`'s output and let a human pick one
  before it's locked in as the canonical reference.
- `[Art Studio] Character reference workflow` — wire the existing
  `reference_image_path` img2img path into `creative/keyframes.py` behind
  a config flag, with tests, once a canonical reference image exists.
- `[Art Studio] ControlNet pose workflow` — optional pose-conditioned
  generation for action-heavy scenes.
- `[Art Studio] IP-Adapter reference workflow` — real identity-specialized
  reference conditioning (the gap `identity.py`'s docstring explicitly
  calls out as unsolved by prompt-text-only identity).
- `[Art Studio] Inpainting integration` / `[Art Studio] Outpainting integration`
- `[Art Studio] Asset lock/unlock` — mark a character/environment/prop
  "final" so later regeneration passes can't silently drift it.
- `[Art Studio] Version comparison` / `[Art Studio] Visual asset history`
- `[Art Studio] Lighting adjustment workflow`

**Advanced / research:**
- `[Art Studio] Krita integration` — a real bridge to
  krita-ai-diffusion-style non-destructive editing for keyframes that need
  human touch-up before video generation.
- Long-form, multi-character identity consistency (see Track C).

---

## TRACK B — Universal Model Gateway

**Vision:** "Bring your own model." Every provider category
(`LLMProvider`, `ImageProvider`, `VideoProvider`, `TTSProvider`, and
future `MusicProvider`/`VisionProvider`/`EmbeddingProvider`) should be
implementable against local models, self-hosted servers, LAN/intranet
endpoints, or any OpenAI-compatible API — so a company or research group
can run the entire pipeline against internal models with no media ever
leaving their network.

**Boundaries:** this track owns `studio/providers/` adapters and
`studio/providers/registry.py`. It does not own pipeline orchestration
logic in `creative/*.py` — providers are swapped, the pipeline stages
that call them stay the same.

**Relevant extension interfaces:** `providers/base.py` (the four current
interfaces), `providers/registry.py`'s `PROVIDERS` dict and `get_provider()`
(the one place new providers get registered — one new file implementing
the relevant interface, plus a two-line registration: an import and an
entry in the `PROVIDERS` dict).

**Starter issues (good first issue):**
- `[Model Gateway] Provider health check` — a standard `is_available()`
  convention already exists on some providers; formalize it across all
  four provider types with a consistent interface and a shared CLI command
  (`python -m providers.doctor`) that reports which configured providers
  are reachable.
- `[Model Gateway] Free/community provider registry` — a docs page listing
  known free-tier-friendly providers per category.

**Help wanted (intermediate):**
- `[Model Gateway] OpenAI-compatible provider` — a generic `LLMProvider`
  implementation configured with `base_url`/`api_key`/`model`, working
  against any OpenAI-compatible endpoint (this is the single highest-value
  provider addition: it unlocks vLLM, LM Studio, most cloud APIs, and most
  enterprise LLM gateways at once).
- `[Model Gateway] Ollama improvements` — multi-instance/remote-host
  support beyond the current single hardcoded `ollama_server` URL.
- `[Model Gateway] llama.cpp adapter`
- `[Model Gateway] vLLM adapter`
- `[Model Gateway] Custom enterprise endpoint` / `[Model Gateway] Custom headers/auth`
  — auth schemes beyond a bearer token (mTLS, custom headers, SSO-fronted
  gateways).
- `[Model Gateway] Provider capability declaration` — providers declare
  what they support (e.g., max tokens, supported resolutions) so the
  pipeline can validate configuration before a run starts instead of
  failing mid-run.
- `[Model Gateway] Cost/privacy metadata` — providers self-report whether
  a call leaves the local network, so a run can be configured to refuse
  non-local providers entirely.

**Advanced / research:**
- `[Model Gateway] Model Manager UI` — a Gradio panel for
  discovering/selecting/testing configured providers.
- `[Model Gateway] Provider plugin SDK` — install a provider from a
  separate package without editing `registry.py` at all.
- `[Model Gateway] Company intranet example` — a full worked example of an
  air-gapped deployment against internal LLM/image/video/TTS endpoints.

---

## TRACK C — Character Consistency

**Vision:** V0.3 solved *textual* identity drift (the same formatted
identity text reaches every scene's prompt, byte-identical). It has not
solved *visual* identity drift — SDXL Lightning at 5 steps does not
reliably render fine-grained facial detail consistently from text alone.
This track is about closing that gap, and about the harder multi-character
/ multi-shot case a single `character_identity` dict doesn't yet model.

**Boundaries:** overlaps Track A (the mechanism is likely
reference-conditioning) but is scoped separately because it's a research
problem, not just an integration problem — "does this actually work" needs
benchmarking, not just wiring.

**Relevant extension interfaces:** `creative/identity.py`,
`providers/image/comfyui_sdxl.py`'s img2img path.

**Help wanted:**
- `[Character Consistency] Face similarity QC` — an automated check
  (face-embedding cosine similarity across a run's keyframes) that flags
  low identity consistency instead of relying on manual review.
- `[Character Consistency] Clothing continuity QC`
- `[Character Consistency] Multi-character identity model` — extend
  `identity.py` beyond one `character_identity` per storyboard.

**Research:**
- `[Research] Face-reference conditioning` — evaluate IPAdapter-FaceID vs.
  InstantID vs. PuLID for this specific pipeline's constraints (6GB-class
  consumer GPU, SDXL Lightning's few-step regime).
- `[Research] Character consistency benchmarks` — a reproducible benchmark
  (prompt set + scoring method) other contributors' approaches can be
  measured against, so "does this actually improve identity consistency"
  has an objective answer instead of eyeballing output images.

---

## TRACK D — Provider Integrations

**Vision:** more provider *implementations* (not new provider
*categories* — that's Track B) — additional video models, image model
adapters, and ready-made ComfyUI workflow presets beyond the current
SDXL Lightning / LTX-Video pairing.

**Help wanted:**
- `[Provider] Wan video provider`
- `[Provider] Additional image model adapters` (e.g., Flux)
- `[Provider] Cloud video adapters`
- `[Provider] ComfyUI workflow presets` — packaged, swappable node-graph
  presets beyond the two hardcoded graphs in `comfyui_sdxl.py`/`comfyui_ltx.py`.

---

## TRACK E — Platform Support

**Vision:** the pipeline is Windows-only in practice today (a hardcoded
Windows font path in `core/render.py`'s subtitle rendering; development
and testing have only happened on Windows + an RTX 3060 Laptop GPU).
Linux and macOS support is real, scoped work, not a checkbox.

**Starter issues (good first issue):**
- `[Platform] Cross-platform subtitle font path` — `core/render.py`'s
  `FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"` has no Linux/macOS fallback;
  needs a per-OS font resolution with a documented, freely-redistributable
  fallback font.
- `[Platform] Windows path handling test pass` — audit remaining
  `pathlib`/string-path handling for Windows-only assumptions.

**Help wanted:**
- `[Platform] Linux install guide + verification`
- `[Platform] macOS install guide + verification`
- `[Platform] Apple Silicon (MPS) support` — Ollama and most image/video
  backends have Apple Silicon paths; this needs someone with the hardware
  to actually verify and document VRAM/unified-memory behavior.
- `[Platform] Docker packaging`
- `[Platform] WSL guide`
- `[Platform] Portable Windows package` — a self-contained distributable,
  closer to the zero-friction install goal than "clone and configure
  Python yourself."

---

## TRACK F — Timeline / Editor

**Vision:** today, "editing" is entirely automated (`creative/pipeline.py`'s
final FFmpeg assembly). Pro Mode's vision includes a real timeline: scene
reorder, trimming, transitions, a subtitle editor, and scene-level
regeneration surfaced in a UI instead of only through the resumability
model already present in `CreativeRunState`.

**Boundaries:** consumes the pipeline's stage outputs (keyframes, clips,
narration, subtitles); does not own generation itself.

**Help wanted:**
- `[Timeline] Timeline UI` (Gradio-based, matching `app.py`'s existing UI
  stack)
- `[Timeline] Shot reorder` / `[Timeline] Trimming` / `[Timeline] Transitions`
- `[Timeline] Audio track mixing UI` (BGM volume/fade, already computed in
  `core/audio.py` — this is UI, not new mixing logic)
- `[Timeline] Subtitle editor`
- `[Timeline] Scene replacement UI` — a UI layer over the scene-level
  regeneration `creative/pipeline.py` already supports at the API level.

---

## TRACK G — AI Video QC

**Vision:** V0.2/V0.3 already ship real automated QC (freeze/motion
detection at the 0.6s threshold, storyboard schema validation, the
`check_narrative_quality` soft warnings). This track extends that: more
QC signals, and QC applied to the *final assembled video*, not just
per-clip.

**Starter issues (good first issue):**
- `[QC] Subtitle timing QC` — automated check that every subtitle cue's
  timing falls within its scene's actual clip duration.

**Help wanted:**
- `[QC] Final-video freeze QC` — the per-clip freeze QC that already
  exists doesn't currently re-run against the final concatenated/retimed
  output; flagged as a known gap in prior acceptance testing.
- `[QC] Duplicate-shot detection`
- `[QC] Audio QC` (clipping, silence gaps, loudness normalization checks)
- `[QC] Quality scoring` — a single composite score per run, building on
  the existing per-signal checks.

**Research:**
- `[Research] Perceptual video-quality scoring` — an automated stand-in
  for "does this look good," beyond freeze/motion/schema checks.

---

## TRACK H — Documentation / Localization

**Vision:** `README_CN.md` exists at launch; every other language is a
community opportunity. Good documentation is as valuable a contribution as
code here.

**Starter issues (good first issue):**
- `[Docs] Fix a typo / broken link / unclear step`
- `[Docs] Add setup screenshots` (Windows install flow)
- `[Docs] Translate README` — Japanese, Spanish, German, or any other
  language not yet covered.

**Help wanted:**
- `[Docs] Tutorial video`
- `[Docs] Architecture deep-dive doc` — the pipeline stage model,
  provider interfaces, and review-gate mechanics, for contributors who
  want to work on Core or Track B.

---

## How a track becomes real

1. Read this document's entry for the track.
2. Pick a starter issue (or open one, using the difficulty guide in
   `CONTRIBUTING.md`) and comment on it before starting significant work,
   so two people don't build the same thing.
3. If the change touches an interface another track depends on
   (`providers/base.py`, `CreativeRunState`, the review-gate), open a
   GitHub Discussion first — see `GOVERNANCE.md`.
4. PRs are reviewed against the track's stated boundaries, not against an
   unwritten maintainer preference — if a PR is in-scope per this
   document, it gets reviewed on its technical merits.
