# Changelog

Format loosely follows [Keep a Changelog](https://keepachangelog.com/).
Dates reflect when work landed in the private development repository this
public repository was prepared from.

## v0.3 — 2026-08-19

### Added
- `creative/identity.py`: canonical character/environment identity,
  generated once per project via a focused LLM call, formatted
  deterministically, and reused verbatim across every scene's keyframe
  prompt.
- Storyboard continuity fields: `previous_scene_id`,
  `continuity_from_previous`, `narrative_purpose`, `visual_change`,
  `camera_change`, `allow_generated_text`.
- `check_narrative_quality`: soft, non-raising warnings for duplicate
  narrative purpose, missing continuity, and invalid scene references.
- Anti-text negative-prompt suppression (`ANTI_TEXT_NEGATIVE_PROMPT`),
  applied unless a scene explicitly needs readable in-image text.
- Optional img2img reference-image path on the SDXL provider (available
  infrastructure, not yet wired into the default pipeline).
- Strict semantic validation on LLM JSON output at both the identity and
  storyboard boundaries (rejects parseable-but-wrong-shaped responses,
  e.g. a JSON string `"false"` where a real boolean is required).

### Fixed
- `creative/keyframes.py` was still reading storyboard fields
  (`visual_identity`, `character_continuity`, `environment_continuity`)
  removed by the identity refactor — keyframe prompts would have silently
  lost all identity text.
- A Python `bool("false") == True` coercion bug that could silently
  invert `allow_generated_text` and disable anti-text suppression.

### Changed
- `visual_identity` (a single free-text string) replaced by structured
  `character_identity`/`environment_identity` objects.

## v0.2

### Added
- Duration-accuracy fixes driven by actual narration word count, not
  fixed padding.
- LTX freeze/motion QC with a real regression test proving the fixed
  threshold catches what the old one missed.
- Storyboard schema validation.
- Per-scene checkpointing and resumable runs.
- Prompt-based visual continuity via a single shared `visual_identity`
  string (superseded by v0.3's structured identity).

### Fixed
- Narration truncation (clips trimmed shorter than their narration).
- Subtitle timing drift (cues keyed to the wrong duration source).
- Several ComfyUI VRAM-lifecycle bugs (`/free` failures silently
  swallowed, timed-out jobs not cancelled before retry).

## v0.1-alpha

### Added
- Initial prompt → script → storyboard → keyframes → clips → narration →
  subtitles → final video pipeline.
- Local generation via Ollama (script/storyboard) and ComfyUI (SDXL
  Lightning keyframes, LTX-Video clips).
- Edge TTS narration, FFmpeg/NVENC final assembly.
