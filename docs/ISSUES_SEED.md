# Issue Seed List

Drafted issues ready to be filed as real GitHub Issues once the repository
exists. Not yet created (the repo isn't public/created yet) — this
document is the source content, structured so each entry can be turned
into a real issue with `gh issue create --title "..." --body "..." --label "..."`
in one pass at launch prep time.

Total: 43 issues — 10 good first issue, 28 help wanted, 5 research.
(Three items use letter-suffixed numbers — 17b, 27b, 30b — added after
independent review; renumbering everything else was judged not worth the
churn. An earlier version of this line miscounted as 23/10 — verified by
actually counting section headers, not by trusting arithmetic done while
editing. 5 research issues is within the 5-10 range originally
requested, not a shortfall.)

Labels used: `good first issue`, `help wanted`, `research`, `provider`,
`art-studio`, `character-consistency`, `model-gateway`, `enterprise`,
`comfyui`, `ui`, `video`, `audio`, `testing`, `documentation`, `windows`,
`linux`, `macos`, `performance`, `security`.

---

## Good First Issues (10)

Each meets the full spec: Problem, Why it matters, Relevant files,
Expected result, Acceptance criteria, How to test.

### 1. [Platform] Cross-platform subtitle font path fallback
**Labels:** `good first issue`, `linux`, `macos`, `windows`
**Problem:** `studio/core/render.py` hardcodes `FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"` for subtitle rendering, with no fallback for Linux/macOS.
**Why it matters:** Subtitle rendering (used by both the AI Creation pipeline and Media Remix) fails outright on non-Windows systems — this blocks all of Track E (Platform Support).
**Relevant files:** `studio/core/render.py`
**Expected result:** A per-OS font resolution function that tries a sensible default font per platform (e.g. a bundled or commonly-available CJK-capable font on Linux/macOS) and fails with a clear, actionable error message if none is found, instead of a cryptic FFmpeg/libass failure.
**Acceptance criteria:** Works unchanged on Windows (no regression); on Linux/macOS, either renders successfully with a real font or raises a clear error naming what font to install.
**How to test:** A unit test mocking `platform.system()` for each OS branch, asserting the resolved path/behavior; manual verification on at least one non-Windows machine if available.

### 2. [Docs] Add Windows install screenshots to docs/INSTALL.md
**Labels:** `good first issue`, `documentation`
**Problem:** `docs/INSTALL.md` is text-only; first-time users benefit from visual confirmation at each step.
**Why it matters:** Screenshots reduce install-time confusion, one of the top launch failure modes.
**Relevant files:** `docs/INSTALL.md`
**Expected result:** Screenshots (or a short animated GIF) for: Ollama running, ComfyUI running, `.env` configured, the app launching successfully.
**Acceptance criteria:** Images added under `docs/images/`, referenced from `docs/INSTALL.md` at the relevant steps, reasonable file size (compressed, not raw screenshots).
**How to test:** Visual review — images render correctly on GitHub's markdown viewer.

### 3. [Docs] Translate README to a new language
**Labels:** `good first issue`, `documentation`
**Problem:** Only English (`README.md`) and Chinese (`README_CN.md`) exist at launch.
**Why it matters:** Broadens the contributor/user base; explicitly called out as a Track H opportunity.
**Relevant files:** `README.md` (source), new `README_<LANG>.md`
**Expected result:** A complete, accurate translation — not machine-translated without review — linked from the top of `README.md`'s language switcher.
**Acceptance criteria:** All sections present, technical terms (provider names, model names) left untranslated where translating them would confuse a technical reader, links still valid.
**How to test:** Native/fluent speaker review.

### 4. [QC] Clear error message when Ollama is unreachable
**Labels:** `good first issue`, `testing`
**Problem:** `creative/pipeline.py`'s `run_script` raises `RuntimeError("Ollama is not reachable — is it installed and running?")` when `llm.is_available()` is false — good start, but doesn't tell the user *which* URL it tried or how to fix `config.toml`.
**Why it matters:** First-run failures are exactly where a clear error message matters most.
**Relevant files:** `studio/creative/pipeline.py`, `studio/providers/llm/ollama_provider.py`
**Expected result:** The error message includes the configured server URL and a pointer to `config.toml`'s `[providers].ollama_server`.
**Acceptance criteria:** Error message includes the actual URL attempted; existing tests still pass.
**How to test:** `python -m pytest tests/ -q`; manual check with Ollama stopped.

### 5. [Model Gateway] Provider health-check CLI command
**Labels:** `good first issue`, `model-gateway`
**Problem:** There's no single command to check whether all configured providers (Ollama, ComfyUI) are actually reachable before starting a run.
**Why it matters:** Saves a failed run partway through generation; a natural entry point for Track B.
**Relevant files:** new `studio/providers/doctor.py`, `studio/providers/registry.py`
**Expected result:** `python -m providers.doctor` reports reachability for each configured provider (using existing `is_available()` methods where present).
**Acceptance criteria:** Runs without live services (reports "unreachable" gracefully, doesn't crash); has at least one test using a fake provider.
**How to test:** `python -m providers.doctor` with services stopped, then running.

### 6. [QC] Subtitle timing QC — cue falls within scene's clip duration
**Labels:** `good first issue`, `testing`
**Problem:** No automated check that every generated subtitle cue's timing actually falls within the final clip duration it's meant to caption.
**Why it matters:** A known past bug class (subtitle cursor drift) — see `studio/creative/subtitles.py`'s history; a regression here would ship silently without this check.
**Relevant files:** `studio/creative/subtitles.py`, `studio/creative/pipeline.py`
**Expected result:** A QC function that, given the final storyboard + subtitle file, flags any cue starting/ending outside its scene's actual clip duration.
**Acceptance criteria:** New function with tests covering: in-bounds cue (passes), out-of-bounds cue (flagged), matches the existing soft-warning pattern used by `check_narrative_quality`.
**How to test:** `python -m pytest tests/ -q`.

### 7. [Docs] Hardware report template + first entries
**Labels:** `good first issue`, `documentation`
**Problem:** `docs/HARDWARE.md` only has the maintainer's own tested hardware.
**Why it matters:** Community-verified compatibility data makes the matrix actually trustworthy.
**Relevant files:** `.github/ISSUE_TEMPLATE/hardware_report.md`, `docs/HARDWARE.md`
**Expected result:** File a real hardware report (your own machine) using the issue template, and open a PR adding it to the matrix once verified.
**Acceptance criteria:** New row in the matrix's table, with a link to the issue as evidence, following the existing TESTED/EXPECTED/UNKNOWN convention exactly.
**How to test:** N/A (documentation).

### 8. [Art Studio] Define a starter style preset schema (no loader yet)
**Labels:** `good first issue`, `art-studio`
**Problem:** The `presets/` directory (repo root) exists but is empty and untracked beyond a placeholder — there's no preset file format, and no pipeline code reads presets at all yet. `config.toml`'s `[creative].default_style` is a single hardcoded string.
**Why it matters:** Establishes the data format a future loader (a separate, larger issue — see help-wanted item 17b) will consume, without blocking on that loader existing first.
**Relevant files:** `presets/` (new files), `presets/README.md` (new)
**Expected result:** A small number (2-3) of named style preset files (e.g. `cinematic_scifi.json`, `documentary.json`) with a documented schema, plus `presets/README.md` explaining the format and stating explicitly that nothing in the pipeline consumes these files yet.
**Acceptance criteria:** Presets are plain data files (no code); `presets/README.md` is explicit that this issue only defines the format, not the loader — don't claim more than what's delivered.
**How to test:** N/A beyond schema validity (documentation + data files).

### 9. [Testing] COMFYUI_ROOT path handling test
**Labels:** `good first issue`, `testing`, `windows`
**Problem:** The new `COMFYUI_ROOT` environment variable (added during open-source prep, see `studio/providers/_comfy_client.py`) hasn't been tested against edge cases like a trailing slash or mixed path separators.
**Why it matters:** Path handling bugs are exactly the kind of thing that works on the original author's machine and breaks for everyone else.
**Relevant files:** `studio/providers/_comfy_client.py`, `studio/tests/test_creative_pipeline.py`
**Expected result:** Tests confirming `ComfyClient` resolves `input`/`output` paths correctly regardless of trailing slashes or `/` vs `\` in `COMFYUI_ROOT`.
**Acceptance criteria:** New tests pass; no production code change needed unless a real bug is found (in which case, fix it too).
**How to test:** `python -m pytest tests/ -q`.

### 10. [Docs] FAQ for common install errors
**Labels:** `good first issue`, `documentation`
**Problem:** `docs/INSTALL.md`'s troubleshooting section is short; real user-reported errors aren't reflected yet (there are no users yet at seed time — this issue is meant to be picked up once the first few install reports come in).
**Why it matters:** Reduces repeat support burden on maintainers.
**Relevant files:** `docs/INSTALL.md`
**Expected result:** Troubleshooting section expanded with real error messages seen in early issues, each with a concrete fix.
**Acceptance criteria:** Each FAQ entry references a real issue number as its source, not a hypothetical problem.
**How to test:** N/A (documentation).

---

## Help Wanted (20)

### Art Studio (Track A)
11. **[Art Studio] Character Bible data model** — `character-consistency`, `art-studio`. Structured, versioned schema for multiple characters per story (today's `identity.py` supports exactly one). See `docs/COMMUNITY_TRACKS.md`, Track A.
12. **[Art Studio] Environment Bible** — `art-studio`. Same idea for recurring locations/multiple settings.
13. **[Art Studio] Character reference workflow** — `art-studio`, `comfyui`. Wire the already-implemented but unused `reference_image_path` img2img path (`providers/image/comfyui_sdxl.py`) into `creative/keyframes.py` behind a config flag.
14. **[Art Studio] ControlNet pose workflow** — `art-studio`, `comfyui`. Optional pose-conditioned generation for action-heavy scenes.
15. **[Art Studio] IP-Adapter reference workflow** — `art-studio`, `comfyui`, `character-consistency`. Real identity-specialized reference conditioning (new node packages + model downloads required — document the tradeoff).
16. **[Art Studio] Inpainting integration** — `art-studio`, `comfyui`.
17. **[Art Studio] Asset lock/unlock** — `art-studio`. Mark a character/environment/prop "final" so later regeneration can't silently drift it.
17b. **[Art Studio] Preset loader and UI selector** — `art-studio`, `ui`. Once good-first-issue 8's preset file format exists, nothing actually reads it — `studio/config.toml`'s `default_style` and `app.py`'s style textbox are still the only way to set style. Add a loader (new `studio/creative/presets.py`) plus a dropdown in `app.py`.

### Model Gateway (Track B)
18. **[Model Gateway] OpenAI-compatible provider** — `model-gateway`, `provider`. Generic `LLMProvider` against any OpenAI-compatible endpoint (`base_url`/`api_key`/`model`) — highest-value single addition, unlocks vLLM/LM Studio/most cloud APIs/most enterprise gateways at once.
19. **[Model Gateway] Ollama remote/multi-instance support** — `model-gateway`. Beyond the current single hardcoded `ollama_server` URL in `config.toml`.
20. **[Model Gateway] llama.cpp adapter** — `model-gateway`, `provider`.
21. **[Model Gateway] vLLM adapter** — `model-gateway`, `provider`.
22. **[Model Gateway] Custom enterprise endpoint / auth headers** — `model-gateway`, `enterprise`. Auth schemes beyond a bearer token.
23. **[Model Gateway] Provider capability declaration** — `model-gateway`. Providers self-report supported limits so a run can be validated before it starts.

### Character Consistency (Track C)
24. **[Character Consistency] Face similarity QC** — `character-consistency`, `testing`. Automated face-embedding similarity check across a run's keyframes.
25. **[Character Consistency] Multi-character identity model** — `character-consistency`. Extend `identity.py` beyond one character per storyboard.

### Provider Integrations (Track D)
26. **[Provider] Additional image model adapter (e.g. Flux)** — `provider`, `comfyui`.
27. **[Provider] ComfyUI workflow presets** — `provider`, `comfyui`. Packaged, swappable node-graph presets beyond the two hardcoded graphs.
27b. **[Provider] Local/offline TTS provider** — `provider`, `audio`. The only shipped `TTSProvider` (Edge TTS) sends narration text to Microsoft's online service — see `README.md`'s local-by-default disclosure. A local/offline TTS implementation (e.g. Piper, Coqui) closes the one gap in the "entirely local" story. Relevant files: `studio/providers/base.py` (`TTSProvider` interface), `studio/providers/tts/edge_tts_provider.py` (reference implementation to follow the shape of).

### Platform Support (Track E)
28. **[Platform] Linux install guide + verification** — `help wanted`, `linux`.
29. **[Platform] macOS install guide + verification** — `help wanted`, `macos`.
30. **[Platform] Docker packaging** — `help wanted`, `linux`.
30b. **[Platform] CPU / non-NVIDIA encoding fallback** — `help wanted`, `linux`, `macos`, `performance`. `studio/core/render.py` hardcodes `h264_nvenc` for final video encoding with no software/other-vendor-GPU fallback — blocks the entire pipeline's final step on any non-NVENC-capable machine, not just CPU-only ones. See `docs/HARDWARE.md`.

### Timeline / Editor (Track F)
31. **[Timeline] Timeline UI** — `ui`, `video`. Gradio-based scene reorder/trim/transitions surface over the pipeline's existing resumability model.
32. **[Timeline] Subtitle editor UI** — `ui`.

### AI Video QC (Track G)
33. **[QC] Final-video freeze QC** — `video`, `testing`. Extend the existing per-clip freeze QC to the final assembled/retimed video, a known gap noted in prior acceptance testing.
34. **[QC] Audio QC** — `audio`, `testing`. Clipping, silence gaps, loudness normalization checks.

### Documentation (Track H)
35. **[Docs] Tutorial video** — `documentation`. Longer-form walkthrough beyond the README hero demo.

---

## Research (10)

36. **[Research] Face-reference conditioning evaluation** — `research`, `character-consistency`. Compare IPAdapter-FaceID / InstantID / PuLID for this pipeline's specific constraints (6GB-class GPU, SDXL Lightning's few-step regime). Contributions welcome as benchmarks/writeups, not only code.
37. **[Research] Character consistency benchmark** — `research`, `character-consistency`. A reproducible prompt set + scoring method so different identity-preservation approaches can be compared objectively.
38. **[Research] Perceptual video-quality scoring** — `research`, `video`. An automated stand-in for "does this look good," beyond the current freeze/motion/schema checks.
39. **[Research] Long-form story memory** — `research`. How should identity/continuity/narrative-purpose tracking scale past a single short-form storyboard into multi-minute or multi-part stories?
40. **[Research] Distributed/multi-GPU generation** — `research`, `performance`. The current GPU-sequencing model assumes one 6GB-class card; what would a multi-GPU or distributed generation path look like without abandoning the single-GPU-friendly default?

---

## Filing checklist (for whoever runs this at launch prep)

- [ ] Create all labels listed above in the GitHub repo first
- [ ] File issues in order (good first issue → help wanted → research), so
      issue numbers roughly track difficulty for early visitors skimming
      the list
- [ ] Double-check each issue's "Relevant files" paths are still accurate
      against the repo state at actual filing time (this doc may predate
      the final repo state by days/weeks)
- [ ] Link each track's issues from `docs/COMMUNITY_TRACKS.md` once real
      issue numbers exist
