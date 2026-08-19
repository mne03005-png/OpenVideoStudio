# Roadmap

Status labels used throughout: **DONE** (shipped, tested), **HELP
WANTED** (a real community contribution track, see
`docs/COMMUNITY_TRACKS.md`), **RESEARCH** (open-ended, contributions can
be experiments/benchmarks, not only code), **PLANNED** (maintainer-led,
not started).

## v0.1-alpha — DONE

- Prompt → script → storyboard → keyframes → clips → narration →
  subtitles → final video
- Local generation via Ollama + ComfyUI (SDXL + LTX-Video)
- Edge TTS narration, FFmpeg/NVENC assembly

## v0.2 — DONE

- ~60-second pipeline, duration-accuracy fixes
- Resumable runs, per-scene checkpointing (a scene whose keyframe/clip
  already exists on disk is skipped on rerun — this makes targeted
  regeneration possible by clearing one scene's artifact path and
  rerunning with `force=True`, though there's no UI for it yet; see
  `docs/COMMUNITY_TRACKS.md` Track F)
- LTX freeze/motion QC
- Storyboard schema validation
- Prompt-based visual continuity (single shared `visual_identity` string)

## v0.3 — DONE

- Structured character/environment identity, generated once and reused
  verbatim across every scene (`creative/identity.py`) — replaces v0.2's
  single free-text `visual_identity` string, which drifted on facial
  identity across scenes
- Stronger continuity fields (`narrative_purpose`, `continuity_from_previous`,
  `visual_change`, `camera_change`) plus soft narrative-quality warnings
- Stronger semantic validation at LLM output boundaries (rejects
  parseable-but-wrong-shaped responses instead of silently coercing them)
- Real Ollama + ComfyUI end-to-end validation
- 54/54 tests passing
- Independently reviewed and cleared (see the project's development
  history)

## Community Tracks — HELP WANTED / RESEARCH

Not scheduled to any version — these grow through contribution, on their
own timeline. Full detail in `docs/COMMUNITY_TRACKS.md`.

| Track | Status |
|---|---|
| AI Art Studio (character/environment bibles, reference conditioning, Krita integration) | HELP WANTED |
| Universal Model Gateway (OpenAI-compatible, llama.cpp, vLLM, enterprise endpoints) | HELP WANTED |
| Character Consistency (face-reference conditioning, benchmarks) | RESEARCH / HELP WANTED |
| Provider Integrations (additional image/video models) | HELP WANTED |
| Platform Support (Linux, macOS, Apple Silicon, Docker) | HELP WANTED |
| Timeline / Editor | HELP WANTED |
| AI Video QC (final-video freeze QC, duplicate-shot/audio QC) | HELP WANTED |
| Documentation / Localization | HELP WANTED |

## v0.4+ — PLANNED

Maintainer-led, not yet started, no committed timeline:

- Multi-minute videos (beyond the currently-verified ~60-second range)
- A formal plugin ecosystem for providers (today's registration is a
  one-file-plus-one-line pattern in `providers/registry.py`; a real
  plugin SDK is Track B's "Provider plugin SDK" item, tracked as HELP
  WANTED, but a stable plugin *contract* is a maintainer-led decision)
- Pro Mode UI (script → character design → environment design →
  storyboard review → keyframe review → video generation → edit → final
  video) — the pipeline stages already exist; the guided UI layer over
  them does not
- Additional providers beyond what ships in v0.3 or lands via Track D

## What this roadmap deliberately does not promise

No date commitments beyond what's already DONE. No feature on this list
is claimed to exist in the product until it's actually merged and tested
— see `docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`'s overclaiming failure mode
for why that distinction is enforced strictly here.
