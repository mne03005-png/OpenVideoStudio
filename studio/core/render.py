"""FFmpeg/NVENC render pipeline.

Reused, proven parameters, each carried over from a specific earlier
private prototype (not all from the same one — this file consolidates
several prototypes' individually-proven pieces, not one prototype's
complete pipeline):
- one prototype's scale/pad/fps/setsar normalize chain, NVENC bitrate
  10M + maxrate 13M + bufsize 20M, and the "silent audio track for
  photos" trick so photo clips concat cleanly alongside real video clips.
  -movflags +faststart is standardized here from a different, single
  prototype that used it (see config.toml's own note on this — it was
  not universal across all of them).
- another prototype's PIL ratio-compare-and-center-crop math (make_photo()).
- two other prototypes' zoompan formulas (one supplied zoom-in/out, a
  different one supplied pan-left/right), reused as-is and selected
  deterministically by shot index (not randomly) for shot-to-shot
  variety.
- another prototype's -f concat demuxer pattern for the final assembly.

Face-aware crop is new: one of those earlier prototypes never actually
called its face detector — it always center-cropped.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageOps

from score import detect_faces, imread_unicode, load_face_detector

FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"


@dataclass
class RenderConfig:
    width: int = 1920
    height: int = 1080
    fps: int = 25
    codec: str = "h264_nvenc"
    preset: str = "p5"
    pix_fmt: str = "yuv420p"
    bitrate: str = "10M"
    maxrate: str = "13M"
    bufsize: str = "20M"
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"
    audio_samplerate: int = 48000
    audio_channels: int = 2
    faststart: bool = True
    jpeg_quality: int = 95
    target_ratio: float = 16 / 9
    zoom_increment: float = 0.0008
    zoom_max: float = 1.12
    pan_px_per_frame: int = 2

    @classmethod
    def from_toml(cls, path: Path) -> "RenderConfig":
        import tomllib
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        out = data.get("output", {})
        enc = data.get("encode", {})
        kb = data.get("kenburns", {})
        crop = data.get("crop", {})
        return cls(
            width=out.get("width", 1920), height=out.get("height", 1080), fps=out.get("fps", 25),
            codec=enc.get("codec", "h264_nvenc"), preset=enc.get("preset", "p5"),
            pix_fmt=enc.get("pix_fmt", "yuv420p"), bitrate=enc.get("bitrate", "10M"),
            maxrate=enc.get("maxrate", "13M"), bufsize=enc.get("bufsize", "20M"),
            audio_codec=enc.get("audio_codec", "aac"), audio_bitrate=enc.get("audio_bitrate", "192k"),
            audio_samplerate=enc.get("audio_samplerate", 48000), audio_channels=enc.get("audio_channels", 2),
            faststart=enc.get("faststart", True), jpeg_quality=crop.get("jpeg_quality", 95),
            target_ratio=crop.get("target_ratio", 16 / 9), zoom_increment=kb.get("zoom_increment", 0.0008),
            zoom_max=kb.get("zoom_max", 1.12), pan_px_per_frame=kb.get("pan_px_per_frame", 2),
        )


def _run(cmd: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = proc.returncode == 0
    log = proc.stderr[-4000:] if not ok else ""
    return ok, log


def smart_crop_image(src: Path, out: Path, cfg: RenderConfig, face_bbox: Optional[dict] = None) -> None:
    """Crop to target_ratio then resize. Centers on the largest detected face
    when available (real face-aware crop); otherwise reuses an earlier
    private prototype's proven center-crop math."""
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        w, h = im.size
        ratio = w / h

        if ratio > cfg.target_ratio:
            new_w = int(h * cfg.target_ratio)
            new_h = h
            if face_bbox:
                center_x = face_bbox["x"] + face_bbox["width"] / 2
                left = int(min(max(center_x - new_w / 2, 0), w - new_w))
            else:
                left = (w - new_w) // 2
            box = (left, 0, left + new_w, h)
        else:
            new_w = w
            new_h = int(w / cfg.target_ratio)
            if face_bbox:
                center_y = face_bbox["y"] + face_bbox["height"] / 2
                top = int(min(max(center_y - new_h / 2, 0), h - new_h))
            else:
                top = (h - new_h) // 2
            box = (0, top, w, top + new_h)

        cropped = im.crop(box).convert("RGB").resize((cfg.width, cfg.height))
        cropped.save(out, quality=cfg.jpeg_quality)


def largest_face_bbox(image_path: Path, detector) -> Optional[dict]:
    img = imread_unicode(image_path)
    if img is None:
        return None
    faces = detect_faces(img, detector)
    if not faces:
        return None
    return max(faces, key=lambda f: f["area_ratio"])


def kenburns_filter(mode: str, duration: float, cfg: RenderConfig) -> str:
    """zoompan formulas reused from earlier private prototypes
    (zoom_in, and zoom_out/pan_left/pan_right), duration parameterized
    instead of those prototypes' fixed 5s/6s."""
    frames = max(int(round(duration * cfg.fps)), 1)
    z_inc, z_max, pan = cfg.zoom_increment, cfg.zoom_max, cfg.pan_px_per_frame

    if mode == "zoom_out":
        zoom = f"if(lte(zoom,1.0),{z_max},zoom-{z_inc})"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif mode == "pan_left":
        zoom = "1.08"
        x = f"iw/2-(iw/zoom/2)+on*{pan}"
        y = "ih/2-(ih/zoom/2)"
    elif mode == "pan_right":
        zoom = "1.08"
        x = f"iw/2-(iw/zoom/2)-on*{pan}"
        y = "ih/2-(ih/zoom/2)"
    else:  # zoom_in, default
        zoom = f"min(zoom+{z_inc},{z_max})"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"

    return f"zoompan=z='{zoom}':x='{x}':y='{y}':d={frames}:s={cfg.width}x{cfg.height}:fps={cfg.fps}"


_KB_MODES = ["zoom_in", "zoom_out", "pan_left", "pan_right"]


def _drawtext_filter(text: str, cfg: RenderConfig) -> str:
    escaped = text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\u2019")
    font = FONT_PATH.replace("\\", "/").replace(":", "\\:")
    return (
        f"drawtext=fontfile='{font}':text='{escaped}':fontcolor=white:fontsize=64:"
        f"borderw=3:bordercolor=black:x=(w-text_w)/2:y=h-th-80:enable='lt(t,3)'"
    )


def render_photo_shot(shot: dict, index: int, work_dir: Path, cfg: RenderConfig, detector) -> tuple[bool, Path, str]:
    src = Path(shot["asset_path"])
    cropped = work_dir / f"{shot['shot_id']}_crop.jpg"
    out = work_dir / f"{shot['shot_id']}.mp4"

    face_bbox = largest_face_bbox(src, detector) if detector else None
    smart_crop_image(src, cropped, cfg, face_bbox)

    mode = _KB_MODES[index % len(_KB_MODES)]
    vf = kenburns_filter(mode, shot["duration"], cfg)
    if shot.get("title_text"):
        vf += "," + _drawtext_filter(shot["title_text"], cfg)

    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(cropped),
        "-f", "lavfi", "-t", str(shot["duration"]),
        "-i", f"anullsrc=channel_layout=stereo:sample_rate={cfg.audio_samplerate}",
        "-t", str(shot["duration"]),
        "-vf", vf,
        "-c:v", cfg.codec, "-preset", cfg.preset, "-b:v", cfg.bitrate, "-pix_fmt", cfg.pix_fmt,
        "-c:a", cfg.audio_codec, "-b:a", cfg.audio_bitrate, "-ar", str(cfg.audio_samplerate), "-ac", str(cfg.audio_channels),
        "-shortest", str(out),
    ]
    ok, log = _run(cmd)
    return ok, out, log


def _has_audio_stream(path: Path) -> bool:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode == 0 and "audio" in proc.stdout


def render_video_shot(shot: dict, work_dir: Path, cfg: RenderConfig) -> tuple[bool, Path, str]:
    """Every clip in the concat list must have an identical stream layout
    (video+audio) or the concat demuxer's stream mapping breaks — so a
    source video with no audio track gets the same synthetic-silence
    treatment an earlier private prototype used for photos, extended here
    to cover the video case that prototype never had to handle."""
    src = Path(shot["asset_path"])
    out = work_dir / f"{shot['shot_id']}.mp4"

    vf = f"scale={cfg.width}:{cfg.height}:force_original_aspect_ratio=decrease,pad={cfg.width}:{cfg.height}:(ow-iw)/2:(oh-ih)/2:black,fps={cfg.fps},setsar=1"
    if shot.get("title_text"):
        vf += "," + _drawtext_filter(shot["title_text"], cfg)

    if _has_audio_stream(src):
        cmd = [
            "ffmpeg", "-y", "-i", str(src),
            "-map", "0:v:0", "-map", "0:a:0",
            "-t", str(shot["duration"]),
            "-vf", vf,
            "-c:v", cfg.codec, "-preset", cfg.preset, "-b:v", cfg.bitrate, "-pix_fmt", cfg.pix_fmt,
            "-c:a", cfg.audio_codec, "-b:a", cfg.audio_bitrate, "-ar", str(cfg.audio_samplerate), "-ac", str(cfg.audio_channels),
            str(out),
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-i", str(src),
            "-f", "lavfi", "-t", str(shot["duration"]),
            "-i", f"anullsrc=channel_layout=stereo:sample_rate={cfg.audio_samplerate}",
            "-map", "0:v:0", "-map", "1:a:0",
            "-t", str(shot["duration"]),
            "-vf", vf,
            "-c:v", cfg.codec, "-preset", cfg.preset, "-b:v", cfg.bitrate, "-pix_fmt", cfg.pix_fmt,
            "-c:a", cfg.audio_codec, "-b:a", cfg.audio_bitrate, "-ar", str(cfg.audio_samplerate), "-ac", str(cfg.audio_channels),
            "-shortest", str(out),
        ]
    ok, log = _run(cmd)
    return ok, out, log


def concat_clips(clip_paths: list[Path], work_dir: Path, out_path: Path, cfg: RenderConfig) -> tuple[bool, str]:
    concat_file = work_dir / "concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for p in clip_paths:
            f.write(f"file '{Path(p).resolve().as_posix()}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-map", "0:v:0", "-map", "0:a:0",
        "-c:v", cfg.codec, "-preset", cfg.preset, "-b:v", cfg.bitrate,
        "-maxrate", cfg.maxrate, "-bufsize", cfg.bufsize, "-pix_fmt", cfg.pix_fmt,
        "-c:a", cfg.audio_codec, "-b:a", cfg.audio_bitrate, "-ar", str(cfg.audio_samplerate), "-ac", str(cfg.audio_channels),
    ]
    if cfg.faststart:
        cmd += ["-movflags", "+faststart"]
    cmd.append(str(out_path))

    return _run(cmd)


def render_plan(plan_path: Path, work_dir: Path, output_path: Path, cfg: Optional[RenderConfig] = None,
                 render_json_path: Optional[Path] = None) -> dict:
    cfg = cfg or RenderConfig()
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    enabled_shots = [s for s in plan["shots"] if s["enabled"]]
    detector = load_face_detector()
    steps = []
    clip_paths = []

    try:
        for index, shot in enumerate(enabled_shots):
            src = Path(shot["asset_path"])
            if not src.exists():
                steps.append({"shot_id": shot["shot_id"], "status": "failed", "error": "source_missing"})
                continue

            if shot["type"] == "image":
                ok, out, log = render_photo_shot(shot, index, work_dir, cfg, detector)
            else:
                ok, out, log = render_video_shot(shot, work_dir, cfg)

            steps.append({
                "shot_id": shot["shot_id"], "asset_path": str(src), "output": str(out),
                "status": "ok" if ok else "failed", "error": None if ok else log,
            })
            if ok:
                clip_paths.append(out)
    finally:
        detector.close()

    final_ok = False
    final_log = ""
    if clip_paths:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_ok, final_log = concat_clips(clip_paths, work_dir, output_path, cfg)
        steps.append({
            "shot_id": "__final_concat__", "output": str(output_path),
            "status": "ok" if final_ok else "failed", "error": None if final_ok else final_log,
        })

    result = {
        "rendered_at": datetime.now().isoformat(),
        "plan_path": str(Path(plan_path).resolve()),
        "output_path": str(output_path) if final_ok else None,
        "shot_count": len(enabled_shots),
        "succeeded": sum(1 for s in steps if s["status"] == "ok"),
        "failed": sum(1 for s in steps if s["status"] == "failed"),
        "status": "ok" if final_ok else "failed",
        "steps": steps,
    }

    if render_json_path:
        render_json_path = Path(render_json_path)
        render_json_path.parent.mkdir(parents=True, exist_ok=True)
        render_json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Render plan.json to an MP4")
    parser.add_argument("plan_json", type=Path)
    parser.add_argument("--work-dir", type=Path, default=Path("render_work"))
    parser.add_argument("--out", type=Path, default=Path("output.mp4"))
    parser.add_argument("--render-json", type=Path, default=Path("render.json"))
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parent.parent / "config.toml")
    args = parser.parse_args()

    cfg = RenderConfig.from_toml(args.config) if args.config.exists() else RenderConfig()
    result = render_plan(args.plan_json, args.work_dir, args.out, cfg, args.render_json)
    print(json.dumps({k: v for k, v in result.items() if k != "steps"}, indent=2))
