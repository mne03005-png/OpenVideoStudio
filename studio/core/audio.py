"""BGM mixing with fades and beat-aligned shot durations.

The amix filter_complex pattern (original vol 1.0, BGM vol 0.25, amix
duration=first dropout_transition=3, BGM looped via -stream_loop -1,
video stream copied not re-encoded) is carried over from an earlier
private prototype of this mixing logic.

New for V1 (not present in that earlier prototype): fade-in/out on the BGM
track, and librosa beat detection used to nudge shot durations so cuts
land near a beat. Ducking is intentionally NOT implemented — no reliable
ducking logic existed to carry forward.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import librosa


@dataclass
class AudioConfig:
    original_volume: float = 1.0
    bgm_volume: float = 0.25
    fade_seconds: float = 2.0
    amix_dropout_transition: float = 3.0
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"

    @classmethod
    def from_toml(cls, path: Path) -> "AudioConfig":
        import tomllib
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        a = data.get("audio", {})
        enc = data.get("encode", {})
        return cls(
            original_volume=a.get("original_volume", 1.0), bgm_volume=a.get("bgm_volume", 0.25),
            fade_seconds=a.get("fade_seconds", 2.0), amix_dropout_transition=a.get("amix_dropout_transition", 3.0),
            audio_codec=enc.get("audio_codec", "aac"), audio_bitrate=enc.get("audio_bitrate", "192k"),
        )


def _run(cmd: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = proc.returncode == 0
    return ok, (proc.stderr[-4000:] if not ok else "")


def _video_duration(path: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return 0.0


def detect_beats(bgm_path: Path) -> list[float]:
    y, sr = librosa.load(str(bgm_path), sr=None, mono=True)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    return [round(float(t), 3) for t in beat_times]


def align_plan_to_beats(plan: dict, beat_times: list[float], max_shift: float = 0.6) -> dict:
    """Nudges enabled shots' durations (bounded by max_shift seconds) so the
    cumulative cut points land as close as possible to a detected beat.
    Returns a new plan dict; does not mutate the input."""
    if not beat_times:
        return plan

    shots = [dict(s) for s in plan["shots"]]
    enabled = [s for s in shots if s["enabled"]]

    cursor = 0.0
    for shot in enabled:
        boundary = cursor + shot["duration"]
        nearest = min(beat_times, key=lambda b: abs(b - boundary))
        shift = nearest - boundary
        if abs(shift) <= max_shift:
            shot["duration"] = round(max(shot["duration"] + shift, 0.5), 2)
            shot["reason"] = shot.get("reason", "") + "+beat_aligned"
        cursor += shot["duration"]

    new_plan = dict(plan)
    new_plan["shots"] = shots
    new_plan["total_planned_duration"] = round(sum(s["duration"] for s in shots if s["enabled"]), 2)
    new_plan["beat_aligned"] = True
    return new_plan


def mix_bgm(video_path: Path, bgm_path: Optional[Path], out_path: Path, cfg: Optional[AudioConfig] = None) -> tuple[bool, str]:
    cfg = cfg or AudioConfig()
    video_path, out_path = Path(video_path), Path(out_path)

    if not bgm_path:
        # No BGM selected: just copy through so pipeline.py always has a
        # final.mp4 regardless of whether this stage does real work.
        cmd = ["ffmpeg", "-y", "-i", str(video_path), "-c", "copy", str(out_path)]
        return _run(cmd)

    bgm_path = Path(bgm_path)
    duration = _video_duration(video_path)
    fade_out_start = max(duration - cfg.fade_seconds, 0)

    filter_complex = (
        f"[0:a]volume={cfg.original_volume}[a0];"
        f"[1:a]volume={cfg.bgm_volume},afade=t=in:st=0:d={cfg.fade_seconds},"
        f"afade=t=out:st={fade_out_start}:d={cfg.fade_seconds}[a1];"
        f"[a0][a1]amix=inputs=2:duration=first:dropout_transition={cfg.amix_dropout_transition}[a]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-stream_loop", "-1", "-i", str(bgm_path),
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy",
        "-c:a", cfg.audio_codec, "-b:a", cfg.audio_bitrate,
        "-shortest",
        str(out_path),
    ]
    return _run(cmd)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mix BGM into a rendered video, with fades")
    parser.add_argument("video", type=Path)
    parser.add_argument("--bgm", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=Path("final.mp4"))
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parent.parent / "config.toml")
    args = parser.parse_args()

    cfg = AudioConfig.from_toml(args.config) if args.config.exists() else AudioConfig()
    ok, log = mix_bgm(args.video, args.bgm, args.out, cfg)
    print("OK" if ok else f"FAILED\n{log}")
