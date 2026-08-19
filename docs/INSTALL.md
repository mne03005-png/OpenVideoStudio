# Installation Guide

Target: under 10 minutes for a technically capable developer who already
has the required models downloaded. Getting the models themselves can take
much longer (they're multi-gigabyte downloads) — this guide doesn't hide
that.

Currently verified on **Windows 10/11** only — see `docs/HARDWARE.md` for
the full compatibility matrix and known Linux/macOS gaps.

## 1. Prerequisites

- **Python 3.11+**
- **[Ollama](https://ollama.com)** — the default local LLM provider
- **[ComfyUI](https://github.com/comfyanonymous/ComfyUI)** (portable
  Windows build or standard install) — the default image/video backend
- **FFmpeg**, with NVENC support (`h264_nvenc`, `libass`, `cuvid`) —
  verify with `ffmpeg -encoders | findstr nvenc`. Final video encoding
  currently **requires** an NVIDIA GPU with NVENC; there's no CPU/other-GPU
  encoder fallback yet (tracked in `docs/HARDWARE.md`/`docs/ISSUES_SEED.md`).
- An NVIDIA GPU with **6GB+ VRAM** is the only configuration actually
  tested end-to-end so far (see `docs/HARDWARE.md`)
- Internet access for narration: the default TTS provider (Edge TTS) is
  Microsoft's free online text-to-speech service, not a local model —
  narration text is sent to it. Script/storyboard/image/video generation
  are fully local; narration currently is not. See `README.md`'s "Local
  by default, with one disclosed exception" section.

## 2. Get the code

```bash
git clone <repository-url>
cd OpenVideoStudio/studio
pip install -r requirements.txt
```

## 3. Get the required models

None of these are bundled in this repository — see
`docs/PUBLIC_REPOSITORY_PLAN.md`'s model file policy for why.

The shipped ComfyUI graphs (`providers/image/comfyui_sdxl.py`,
`providers/video/comfyui_ltx.py`) reference checkpoints **by exact
filename** — ComfyUI won't find a same-purpose checkpoint saved under a
different name. These are the exact filenames the code currently expects
(not yet configurable — see `docs/ISSUES_SEED.md` for making this a
config option):

| Model | Exact filename the code expects | Purpose | Verified source | Size |
|---|---|---|---|---|
| `qwen3:8b` (or another Ollama-compatible model) | n/a — set via `config.toml`'s `ollama_model` | Script/storyboard/identity generation | `ollama pull qwen3:8b` | ~5 GB |
| SDXL checkpoint | `RealVisXL_V5.0_Lightning_fp16.safetensors` | Keyframe image generation | [`SG161222/RealVisXL_V5.0_Lightning`](https://huggingface.co/SG161222/RealVisXL_V5.0_Lightning) on Hugging Face — download into ComfyUI's `models/checkpoints/`, keeping this exact filename; see the checkpoint's own license/distribution terms | |
| LTX-Video checkpoint | `ltxv-2b-0.9.8-distilled-fp8.safetensors` | Image-to-video clip generation | [`Lightricks/LTX-Video`](https://huggingface.co/Lightricks/LTX-Video) on Hugging Face — download into ComfyUI's `models/checkpoints/`, keeping this exact filename | 4.46 GB |
| T5XXL text encoder | `t5xxl_fp8_e4m3fn.safetensors` | Required by the LTX-Video graph | [`comfyanonymous/flux_text_encoders`](https://huggingface.co/comfyanonymous/flux_text_encoders) on Hugging Face — download into ComfyUI's `models/text_encoders/`, keeping this exact filename | 4.89 GB |
| MediaPipe face detector | `face_detector.tflite` | Media Remix's photo scoring (not required for the AI Creation pipeline) | `https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite` — save into `assets/face_detector.tflite` (relative to `studio/` — you're already inside it from step 2; the directory exists but is empty in a fresh clone) | 228 KB |

These sources were confirmed by directly checking each repository's/URL's
actual file listing at prep time — filenames and hosting can change; if a
link goes stale, search Hugging Face for the exact filename in the table,
which is the part that actually has to match for ComfyUI (or, for the
MediaPipe model, `core/score.py`'s `_FACE_MODEL_PATH`) to find it.

These are **open-weight models** with their own individual licenses —
review each model's license before use, especially for any commercial
application. OpenVideoStudio's own license (see `docs/LICENSE_STRATEGY.md`)
covers this repository's code only, not any model weight. If you use a
different checkpoint, rename the file to match the exact filename above,
or edit the `checkpoint`/`clip_name` class attribute in the relevant
provider file.

## 4. Configure

You're already in `OpenVideoStudio/studio` from step 2:

```bash
cp .env.example .env
```

Edit `.env` (loaded automatically on startup via `python-dotenv`) and set
`COMFYUI_ROOT` to your ComfyUI installation's `ComfyUI/` directory (the
one directly containing `input/` and `output/` subfolders) — for example:

```
COMFYUI_ROOT=C:\ComfyUI_windows_portable\ComfyUI
```

Review `config.toml` (in the current directory) — in particular `[providers].ollama_server`
(default `http://127.0.0.1:11434`; change this if you run Ollama on a
non-default port, e.g. because a system-wide instance already occupies
the default one and can't be reconfigured without a restart) and
`[providers].ollama_model` (must match a model you've pulled).

## 5. Start the required services

```bash
ollama serve            # if not already running as a service
# start ComfyUI per its own install instructions, default port 8188
```

## 6. Run

Still in `OpenVideoStudio/studio`:

```bash
python app.py
```

Opens a local Gradio UI with two tabs: **AI Creation** (the
prompt-to-video pipeline) and **Media Remix** (personal photo/video
montage — a separate, secondary tool sharing the same FFmpeg/audio/scoring
core).

## Troubleshooting

- **"Ollama is not reachable"** — confirm `ollama serve` is running and
  `[providers].ollama_server` in `config.toml` matches the port it's
  listening on.
- **ComfyUI errors / `comfy_root is not configured`** — confirm
  `COMFYUI_ROOT` is set in `.env` (in `studio/` — not just `.env.example`)
  and points at the directory containing `input/`/`output/`, not the
  portable build's top-level folder.
- **ComfyUI can't find checkpoints** — if you're using the portable
  Windows build with models stored outside its own `models/` folder, you
  need an `extra_model_paths.yaml` in the `ComfyUI/` directory itself
  (not the portable root) pointing at your actual model locations.
- **Ran out of VRAM** — this pipeline is tuned for 6GB by never keeping
  two heavy models resident at once (Ollama unloads before ComfyUI/SDXL
  loads, which frees before ComfyUI/LTX loads). If you're seeing OOM
  anyway, confirm no other GPU-heavy process is running concurrently.
- **Font/subtitle rendering fails on Linux/macOS** — known gap, see
  `docs/HARDWARE.md`.

## Verify your install

From `OpenVideoStudio/studio`:

```bash
python -m pytest tests/ -q
```

Should report all tests passing with no live services required — the test
suite uses fakes/mocks for LLM, image, and video providers.
