# Hardware Compatibility Matrix

Only hardware with actual test evidence is marked TESTED. Everything else
is an honest EXPECTED or UNKNOWN — no hardware claim in this project's
marketing (README, launch posts) should ever go further than what's listed
here.

## GPU

| GPU | VRAM | Status | Evidence |
|---|---|---|---|
| NVIDIA RTX 3060 Laptop | 6 GB | **TESTED** | Full pipeline runs completed end-to-end: 30s (6 scenes) and 60s (12 scenes) videos, both independently verified. SDXL Lightning (5-10 steps) + LTX-Video 2B distilled + Ollama qwen3:8b, sequenced (never two heavy models resident at once) to fit 6 GB. Confirmed zero OOM events across both acceptance runs. |
| Other NVIDIA GPUs (8GB+) | 8GB+ | EXPECTED | Same model stack, more headroom — should work at least as well, not independently verified on this hardware yet. |
| NVIDIA GPUs <6GB | <6GB | UNKNOWN | Not tested. The pipeline's GPU sequencing discipline (load → use → free, one heavy model at a time) is designed for tight VRAM budgets, but a lower ceiling than 6GB is unverified. |
| AMD GPUs | any | UNKNOWN | Depends entirely on ComfyUI's AMD/ROCm support, not on this project's own code. Not tested here. |
| Apple Silicon (M-series) | unified memory | UNKNOWN | Ollama and ComfyUI both have Apple Silicon paths, but VRAM-equivalent (unified memory) sequencing behavior under this pipeline is unverified. Tracked as a community help-wanted item — see `docs/COMMUNITY_TRACKS.md`, Track E. |
| CPU-only | n/a | **NOT SUPPORTED for final encoding** | LLM generation (Ollama) and image/video generation (SDXL/LTX via ComfyUI) can run on CPU, much more slowly. But `studio/core/render.py`'s final video encoding is hardcoded to `h264_nvenc` with no CPU/software-encoder fallback — the final assembly step fails outright without an NVENC-capable NVIDIA GPU, regardless of how the earlier stages ran. Tracked as a seeded issue — see `docs/ISSUES_SEED.md`. |

## OS

| OS | Status | Notes |
|---|---|---|
| Windows 10/11 | **TESTED** | All development and both acceptance runs happened on Windows. |
| Linux | EXPECTED, KNOWN GAPS | Three known Windows-only assumptions, none fixed yet: (1) `studio/core/render.py` hardcodes a Windows font path for subtitle rendering with no fallback; (2) final encoding is hardcoded to `h264_nvenc` (see the CPU-only row above — this blocks any non-NVIDIA-GPU Linux box too, not just CPU-only); (3) Media Remix's "open output folder" button shells out to Windows' `explorer` with no Linux/macOS equivalent (degrades ungracefully — the button just fails, the rest of the app is unaffected). Everything else is plain Python/FFmpeg with no other currently-known Windows-only dependency, but none of this has been verified end-to-end on Linux. All three tracked as seeded issues — see `docs/COMMUNITY_TRACKS.md` Track E and `docs/ISSUES_SEED.md`. |
| macOS | UNKNOWN | Same three gaps as Linux, plus entirely unverified. |

## Aspect ratios

Only **9:16** (448×768) has been exercised in the tested acceptance runs.
The UI also offers 16:9 and 1:1 (same pixel budget, different shape) —
these are implemented but explicitly **not separately validated**; treat
them as EXPECTED, not TESTED, until someone runs a real acceptance pass
against them.

## Other requirements

| Component | Tested version | Notes |
|---|---|---|
| Python | 3.11+ (uses `tomllib`, stdlib since 3.11) | |
| FFmpeg | 8.1.2, with `h264_nvenc`, `libass`, `cuvid`/`nvenc` | NVENC is currently **required**, not just assumed — see the CPU-only row above. |
| Ollama | 0.24.0 | |
| ComfyUI | portable Windows build | |

## Contributing a hardware report

Ran OpenVideoStudio on hardware not listed here? Open an issue with the
`documentation` label using the template in
`.github/ISSUE_TEMPLATE/hardware_report.md` — include GPU/VRAM, OS, what
ran successfully, what didn't, and any error output. Real reports from
real runs are what keeps this matrix honest; speculative entries won't be
added.
