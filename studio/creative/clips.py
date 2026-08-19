"""Stage 4: keyframes -> one generated video clip per scene, via
VideoProvider. Uses video_motion_prompt (not image_prompt) — the still's
content is already baked into the keyframe; this text only needs to
describe the motion to animate it with, kept as a separate field from the
image generation prompt rather than reusing it."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from providers.base import VideoProvider

_FREEZE_NOISE_DB = "-60dB"

# This checks the RAW clip, before run_edit's setpts retime (which slows a
# clip down when narration runs longer than the raw LTX output — see
# creative/pipeline.py). 1.0s is "a viewer would actually notice this as
# frozen" for a FINISHED clip, but a raw clip only needs a shorter near-still
# tail to become a viewer-noticeable freeze once slowed down: confirmed live
# on the real 60-second/12-scene run — scene 8's raw clip had a 0.958s
# near-freeze at its tail (invisible to a 1.0s-minimum check) that stretched
# past 1.0s after a ~1.2x retime and only showed up in the FINAL video's
# freeze check, downstream of this one. 0.6s catches that case with margin
# while retiming's ~1.2-1.6x observed slowdown factor.
_FREEZE_MIN_SECONDS = 0.6


def _clip_duration_seconds(clip_path: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(clip_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return 0.0


def _detect_freeze_seconds(clip_path: Path, min_seconds: float = _FREEZE_MIN_SECONDS) -> float:
    """min_seconds is parameterized (rather than always reading the module
    constant) so tests can prove the 0.6s threshold specifically matters —
    i.e. that a given clip is caught at 0.6s but would NOT have been caught
    at the old 1.0s — instead of only exercising whatever the constant
    currently happens to be."""
    proc = subprocess.run(
        [
            "ffmpeg", "-i", str(clip_path),
            "-vf", f"freezedetect=n={_FREEZE_NOISE_DB}:d={min_seconds}",
            "-an", "-f", "null", "-",
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    total = 0.0
    pending_start: Optional[float] = None
    for line in proc.stderr.splitlines():
        if "lavfi.freezedetect.freeze_start" in line:
            try:
                pending_start = float(line.strip().rsplit(":", 1)[1])
            except ValueError:
                pending_start = None
        elif "lavfi.freezedetect.freeze_duration" in line:
            try:
                total += float(line.strip().rsplit(":", 1)[1])
            except ValueError:
                pass
            pending_start = None  # this freeze closed normally, don't double-count it below

    # ffmpeg only emits freeze_duration when a freeze ENDS before the clip
    # does. A freeze that runs all the way to end-of-file — arguably the
    # worst case, a clip that's static for its entire remaining length —
    # leaves a dangling freeze_start with no matching freeze_duration and
    # would otherwise be silently missed (caught by testing against a real
    # fully-frozen synthetic clip, not assumed).
    if pending_start is not None:
        clip_duration = _clip_duration_seconds(clip_path)
        if clip_duration > pending_start:
            total += clip_duration - pending_start

    return total


def generate_clips(
    video_provider: VideoProvider, storyboard: dict, out_dir: Path, width: int = 448, height: int = 768,
    checkpoint: Optional[Callable[[dict], None]] = None,
) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for scene in storyboard["scenes"]:
        n = scene["scene_number"]
        # Resume support: don't regenerate an already-produced clip.
        existing = scene.get("clip_path")
        if existing and Path(existing).exists():
            continue

        keyframe = scene.get("keyframe_path")
        if not keyframe or not Path(keyframe).exists():
            scene["clip_error"] = "missing_keyframe"
            continue

        base_seed = scene.get("keyframe_seed", n)
        path = video_provider.generate_video(
            prompt=scene.get("video_motion_prompt", "subtle camera movement"),
            negative_prompt=scene.get("video_negative_prompt", ""),
            duration_seconds=scene["duration_seconds"], width=width, height=height,
            image_path=Path(keyframe), seed=base_seed,
        )
        freeze_seconds = _detect_freeze_seconds(path)

        # Motion-quality QC: one bounded retry with a different seed if the
        # first generation froze for a viewer-noticeable duration. img2video
        # with a fixed conditioning image + a different sampling seed can
        # produce meaningfully different motion, so this isn't a no-op retry.
        if freeze_seconds > 0.0:
            retry_seed = base_seed + 5000
            retry_path = video_provider.generate_video(
                prompt=scene.get("video_motion_prompt", "subtle camera movement"),
                negative_prompt=scene.get("video_negative_prompt", ""),
                duration_seconds=scene["duration_seconds"], width=width, height=height,
                image_path=Path(keyframe), seed=retry_seed,
            )
            retry_freeze = _detect_freeze_seconds(retry_path)
            if retry_freeze < freeze_seconds:
                path = retry_path
                scene["clip_retry_seed"] = retry_seed
                freeze_seconds = retry_freeze

        scene["clip_freeze_seconds"] = freeze_seconds
        dest = out_dir / f"scene_{n:02d}.mp4"
        shutil.copy(path, dest)
        scene["clip_path"] = str(dest)
        if checkpoint:
            checkpoint(storyboard)

    return storyboard


if __name__ == "__main__":
    import argparse
    import json

    from providers.video.comfyui_ltx import ComfyUILTXProvider

    parser = argparse.ArgumentParser(description="Generate clips for a storyboard JSON file (needs keyframe_path per scene)")
    parser.add_argument("storyboard_json", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("clips_test"))
    args = parser.parse_args()

    storyboard = json.loads(args.storyboard_json.read_text(encoding="utf-8"))
    provider = ComfyUILTXProvider()
    result = generate_clips(provider, storyboard, args.out_dir)
    for s in result["scenes"]:
        print(s["scene_number"], "->", s.get("clip_path", s.get("clip_error")))
