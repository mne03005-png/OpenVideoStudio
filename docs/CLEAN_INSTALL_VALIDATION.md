# Clean-Install Validation

The strongest practical install validation available on this preparation
machine — an isolated Python virtual environment plus a fresh copy of the
repository, exercising the exact steps `docs/INSTALL.md` documents. This
is **not** a literal separate machine or VM (see "What this is not," at
the end) — read this as real evidence within that honest limit, not as a
substitute for the fully clean-machine test still outstanding.

## Environment

- Host OS: Windows 11, **system codepage 936 (GBK, Simplified Chinese
  locale)** — the same locale class that caused a real `pip install`
  failure earlier in this project's preparation (a non-ASCII character in
  `requirements.txt` broke pip's encoding auto-detection). Testing on
  this locale specifically, not a US/UTF-8-default machine, is the point.
- Repository copy: a fresh `cp -r` of the candidate into a directory
  outside both `D:\OpenVideoStudio` and the private development
  workspace, with all caches (`__pycache__`, `.pytest_cache`, any local
  `.env`) stripped before testing — as close to "what a clone actually
  contains" as a same-machine copy can get.
- Python environment: a brand new `python -m venv`, created fresh for
  this test — no dependency or package already *installed* in any other
  environment on this machine could mask a real install problem. This
  does **not** mean pip's own download cache was bypassed: a fresh venv
  isolates installed site-packages, not pip's cache directory, and this
  run wasn't done with `--no-cache-dir` or a cleared cache — so it
  doesn't independently prove a from-scratch package *download* would
  succeed, only that a from-scratch *install into an empty environment*
  did.

## Results

| Step | Result | Evidence |
|---|---|---|
| Fresh venv creation | **PASS** | `python -m venv clean_venv` succeeded |
| `pip install -r requirements.txt` | **PASS** | Clean install into the empty venv — every dependency resolved and installed with no pre-existing *installed* package to hide a resolution failure (pip's own download cache was not cleared for this run — see note above) |
| FFmpeg detection | **PASS** | `ffmpeg -encoders` confirms `h264_nvenc`/`hevc_nvenc`/`av1_nvenc` present |
| `.env` → `COMFYUI_ROOT` reaching the code | **PASS** | `ComfyClient().comfy_root` resolved to the configured value, read through the actual `providers._comfy_client` module, not reimplemented for the test |
| Ollama connection | **PASS** | `OllamaProvider(...).is_available()` returned `True` against a live local server, through the actual provider class |
| ComfyUI connection + model detection | **PASS** | `ComfyClient().is_available()` returned `True`; `/object_info` confirmed all three required checkpoints (SDXL, LTX-Video, T5XXL) visible under their exact expected filenames |
| `app.py` import / UI construction | **PASS** | Full Gradio `Blocks` construction succeeds with no server launch; `_configured_ollama_model()` correctly read `config.toml` |
| Full test suite | **PASS** | 67/67, from the fresh venv, against the fresh copy |
| Path-with-spaces handling | **PASS** | Re-ran the fresh copy from a directory path containing a space (`...ovs test with spaces\OpenVideoStudio`); 67/67 unaffected |
| Shell-injection / quoting safety | **PASS** | Every `subprocess.run()` call in the codebase (audited directly, not sampled) passes a list of arguments; `shell=True` appears nowhere in the codebase — a spaced or unusual path cannot be misparsed as multiple shell tokens |
| Private absolute paths required by any documented step | **PASS (none found)** | The only path a user must supply is their own `COMFYUI_ROOT`; nothing in `config.toml`, `.env.example`, or the documented flow assumes a specific machine's directory layout |

## What this exercised end-to-end

This validation ran alongside — and fed evidence back into — the actual
hero-demo generation run (`docs/HERO_DEMO_SPEC.md`), which exercises the
full pipeline (script → storyboard → identity → keyframes → clips →
narration → subtitles → final edit) against live Ollama and ComfyUI using
the exact release-candidate code, not a synthetic smoke test. Its
recorded output (final MP4, storyboard, logs) is the practical proof that
"clean install, then generate" actually works, not just that each piece
individually connects.

## Real gap found and fixed during this pass

The default `config.toml`'s `ollama_server` (`http://127.0.0.1:11434`) is
the honest, generic default for the shipped candidate — but on **this
specific development machine**, the system-wide Ollama instance on that
port was started before its model directory was configured, and has no
models loaded (a pre-existing, well-documented condition from earlier in
this project's private development history, unrelated to the candidate
code). A user on a normal machine, with a normal single Ollama install,
will not hit this. It's recorded here for completeness, not as a defect
in the candidate: `docs/INSTALL.md`'s troubleshooting section already
covers "system-wide instance can't be reconfigured without a restart" as
a documented scenario with a workaround (a second instance on a different
port with `OLLAMA_MODELS` set explicitly).

## What this is not

- **Not a literal separate machine or VM.** Everything above ran on the
  same physical machine as development, in an isolated venv and a fresh
  file copy — real isolation for dependencies and stale state, but not
  isolation from this machine's installed system tools (FFmpeg, Ollama,
  ComfyUI, Windows itself) or its GPU/driver stack. A genuinely clean
  machine or VM with **none** of those pre-installed, following
  `docs/INSTALL.md` from zero, has not been done and remains a real,
  separate item — see `docs/OPEN_SOURCE_READINESS.md`.
- **Not a test of the documented model-download links themselves.** The
  Hugging Face sources in `docs/INSTALL.md` were verified by checking
  each repository's file listing (see `docs/OPEN_SOURCE_SECURITY_AUDIT.md`),
  not by downloading gigabytes of model weights fresh for this pass — the
  models already present on this machine were reused.
- **Not a test of a from-scratch Ollama/ComfyUI install.** Both were
  already installed; this validation confirmed the *candidate code*
  connects to them correctly, not that installing them from scratch is
  itself friction-free. `docs/INSTALL.md`'s prerequisite links are the
  current best guidance for that step.
