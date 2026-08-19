# Public Repository Plan

## Source of truth

This repository is built by **selectively copying** files out of a
private development workspace's `studio/` directory — it does not reuse
that workspace's Git history, and it is not a clone, fork, or subtree of
it. The private workspace is untouched: not renamed, not rewritten, and
never used directly as this public repo. Its own path and identity are
deliberately not named here — see `docs/OPEN_SOURCE_SECURITY_AUDIT.md`
for why.

Rationale: the private workspace's root contains several hundred tracked
files spanning an unrelated private project, legacy production scripts,
and archived material entirely unrelated to OpenVideoStudio. Only 35
tracked source/test files under its application directory are the actual
OpenVideoStudio codebase; even
within `studio/`, some files (the AI-coordination logs) are development
process artifacts, not project content. A clean copy, not a history
export, is the only way to guarantee none of that leaks. See
`docs/OPEN_SOURCE_SECURITY_AUDIT.md` for the full audit of what was
included/excluded/fixed.

## What's in the candidate repo

```
OpenVideoStudio/
├── studio/
│   ├── app.py                  # Gradio UI (AI Creation + Media Remix tabs)
│   ├── config.toml             # provider/output/pipeline configuration
│   ├── .env.example            # env var template (no real values)
│   ├── core/                   # shared FFmpeg/audio/scoring — used by
│   │                           # both the AI Creation pipeline and the
│   │                           # secondary Media Remix (personal photo/
│   │                           # video montage) tool
│   ├── creative/                # the AI Creation pipeline: script ->
│   │                           # storyboard -> identity -> keyframes ->
│   │                           # clips -> narration -> subtitles -> edit
│   ├── providers/               # provider interfaces + adapters
│   │   ├── base.py             # LLMProvider/ImageProvider/VideoProvider/
│   │   │                       # TTSProvider interfaces
│   │   ├── registry.py         # provider registration
│   │   ├── _comfy_client.py    # shared ComfyUI HTTP client
│   │   ├── llm/ollama_provider.py
│   │   ├── image/comfyui_sdxl.py
│   │   ├── video/comfyui_ltx.py
│   │   └── tts/edge_tts_provider.py
│   └── tests/                  # 54 tests, all passing in the candidate copy
├── docs/                       # this document and its siblings
├── examples/                   # sample prompts/config (see below)
├── presets/                    # empty at launch — style/preset library,
│                               # a natural first contribution
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/ci.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── FUNDING.yml             # prepared, not activated
├── README.md
├── README_CN.md
├── CONTRIBUTING.md
├── GOVERNANCE.md
├── ROADMAP.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── SUPPORT.md
├── CHANGELOG.md
├── CONTRIBUTORS.md
└── .gitignore
```

`LICENSE` is deliberately **not yet present** — see `docs/LICENSE_STRATEGY.md`;
it requires an explicit decision before it's added.

Adapted from the originally sketched structure: `providers/` stays nested
under `studio/` rather than promoted to the repo root, matching the actual
Python package layout every import statement and test already depends on.
Moving it would be a mechanical but real refactor with no functional
benefit before launch — left as a possible future cleanup, not done here
to avoid re-deriving test coverage for a purely cosmetic change.

## Model file policy

No model weights are ever committed. Concretely excluded (already true in
the private repo's `.gitignore`, carried forward here):

| Model | Where it comes from | Committed? |
|---|---|---|
| Qwen (Ollama LLM) | user pulls via `ollama pull` | No |
| RealVisXL SDXL checkpoint | user downloads separately | No |
| LTX-Video checkpoint | user downloads separately | No |
| T5XXL text encoder | user downloads separately | No |
| MediaPipe face detector (228 KB) | fetched via a documented URL during setup | No |
| Any future LoRA/ControlNet/IPAdapter model | community-track dependent | No |

`docs/INSTALL.md` documents exactly how to obtain each one, and
distinguishes clearly between:

- **open-source software** (this repository's code — license TBD, see
  `docs/LICENSE_STRATEGY.md`)
- **open-weight models** (e.g., Qwen — freely downloadable weights, their
  own separate license)
- **free models** (usable at no cost, may or may not be open-weight)
- **free/community API tiers** (rate-limited or otherwise restricted free
  access to a provider's hosted API)
- **commercial APIs** (paid, e.g., a future cloud LLM/image/video
  provider a user configures via `.env`)

No licensing claim is made on OpenVideoStudio's behalf about any
third-party model's terms — users are responsible for each model's own
license and usage terms, linked from `docs/INSTALL.md`.

## `examples/`

Populated with a small number of **real, reproducible** example
configurations (a sample prompt + target duration + style, matching what
`docs/HERO_DEMO_SPEC.md` describes) — not fabricated sample output. Actual
example run artifacts (images/video) are added only after the hero demo
itself is produced and approved, not before — see
`docs/HERO_DEMO_SPEC.md`'s explicit "do not generate final launch assets
until the specification is approved" constraint.

## What's explicitly deferred, not missing

`scripts/` (setup-check tooling) is intentionally not created yet — there
is no real content for it today, and an empty placeholder directory
implying tooling that doesn't exist yet is worse than not having the
directory. It's listed here as a known near-term addition (a
`scripts/check_setup.py` that verifies Ollama/ComfyUI/ffmpeg reachability
would be a good first issue) rather than shipped as an empty stub.
