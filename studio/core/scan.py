"""Recursive media scanner. Produces assets.json for any folder — no
assumptions about any particular project layout.

EXIF/video-timestamp tag priority is carried over from an earlier private
prototype, generalized to (a) walk an arbitrary root instead of a
hardcoded one, (b) fall back to file mtime instead of silently dropping
assets with no embedded timestamp, and (c) also capture GPS/orientation/
dimensions, which that prototype never did.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import exifread
from PIL import Image
from pymediainfo import MediaInfo

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".wmv"}

# EXIF tag priority, same order an earlier private prototype used for photos.
_EXIF_DATETIME_TAGS = ("EXIF DateTimeOriginal", "Image DateTime")
_EXIF_DATE_FMT = "%Y:%m:%d %H:%M:%S"
# pymediainfo tag priority, same order that prototype used for video.
_VIDEO_DATETIME_TAGS = ("encoded_date", "tagged_date", "recorded_date")


@dataclass
class Asset:
    id: str
    path: str
    relative_path: str
    type: str  # "image" | "video"
    width: Optional[int] = None
    height: Optional[int] = None
    orientation: Optional[int] = None
    timestamp: Optional[str] = None
    timestamp_source: str = "unknown"  # "exif" | "video_meta" | "mtime"
    gps: Optional[dict] = None
    duration: Optional[float] = None
    fps: Optional[float] = None
    error: Optional[str] = None


def stable_id(relative_path: str) -> str:
    """Deterministic id from the path relative to the scan root, so re-scanning
    the same folder produces the same ids (needed for resumability)."""
    digest = hashlib.sha1(relative_path.encode("utf-8")).hexdigest()[:16]
    return f"a_{digest}"


def _dms_to_decimal(dms, ref) -> Optional[float]:
    try:
        deg, minute, sec = (float(v.num) / float(v.den) for v in dms.values)
        value = deg + minute / 60.0 + sec / 3600.0
        if ref in ("S", "W"):
            value = -value
        return round(value, 6)
    except Exception:
        return None


def _read_exif(path: Path) -> dict:
    out: dict = {}
    try:
        with open(path, "rb") as f:
            tags = exifread.process_file(f, details=False)
    except Exception:
        return out

    for key in _EXIF_DATETIME_TAGS:
        if key in tags:
            try:
                out["timestamp"] = datetime.strptime(str(tags[key]), _EXIF_DATE_FMT).isoformat()
                out["timestamp_source"] = "exif"
                break
            except ValueError:
                continue

    if "Image Orientation" in tags:
        try:
            out["orientation"] = int(str(tags["Image Orientation"]).split()[0]) if str(tags["Image Orientation"]).isdigit() else tags["Image Orientation"].values[0]
        except Exception:
            pass

    lat = tags.get("GPS GPSLatitude")
    lat_ref = tags.get("GPS GPSLatitudeRef")
    lon = tags.get("GPS GPSLongitude")
    lon_ref = tags.get("GPS GPSLongitudeRef")
    if lat and lon and lat_ref and lon_ref:
        lat_dec = _dms_to_decimal(lat, str(lat_ref))
        lon_dec = _dms_to_decimal(lon, str(lon_ref))
        if lat_dec is not None and lon_dec is not None:
            out["gps"] = {"lat": lat_dec, "lon": lon_dec}

    return out


def _read_image(path: Path) -> Asset:
    rel = path.name  # overwritten by caller with true relative path
    asset = Asset(id="", path=str(path), relative_path=rel, type="image")
    try:
        with Image.open(path) as im:
            asset.width, asset.height = im.size
    except Exception as e:
        asset.error = f"pillow: {e}"

    exif = _read_exif(path)
    asset.timestamp = exif.get("timestamp")
    asset.timestamp_source = exif.get("timestamp_source", "unknown")
    asset.orientation = exif.get("orientation")
    asset.gps = exif.get("gps")
    return asset


def _ffprobe_json(path: Path) -> Optional[dict]:
    try:
        proc = subprocess.run(
            [
                "ffprobe", "-v", "error", "-print_format", "json",
                "-show_format", "-show_streams", str(path),
            ],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )
        if proc.returncode != 0:
            return None
        return json.loads(proc.stdout)
    except Exception:
        return None


def _parse_fps(rate: str) -> Optional[float]:
    try:
        if "/" in rate:
            num, den = rate.split("/")
            den = float(den)
            return round(float(num) / den, 3) if den else None
        return float(rate)
    except Exception:
        return None


def _read_video(path: Path) -> Asset:
    asset = Asset(id="", path=str(path), relative_path=path.name, type="video")

    probe = _ffprobe_json(path)
    if probe:
        fmt = probe.get("format", {})
        video_stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), None)
        try:
            asset.duration = float(fmt.get("duration")) if fmt.get("duration") else None
        except (TypeError, ValueError):
            asset.duration = None
        if video_stream:
            asset.width = video_stream.get("width")
            asset.height = video_stream.get("height")
            asset.fps = _parse_fps(video_stream.get("avg_frame_rate", "0/1"))
            rot = video_stream.get("tags", {}).get("rotate")
            if rot:
                try:
                    asset.orientation = int(rot)
                except ValueError:
                    pass
        ctime = fmt.get("tags", {}).get("creation_time")
        if ctime:
            asset.timestamp = ctime
            asset.timestamp_source = "video_meta"
    else:
        asset.error = "ffprobe_failed"

    if asset.timestamp is None:
        # Fall back to pymediainfo's tag priority (matches an earlier
        # private prototype) for containers where ffprobe doesn't surface
        # creation_time.
        try:
            info = MediaInfo.parse(path)
            for track in info.tracks:
                if track.track_type != "Video":
                    continue
                for key in _VIDEO_DATETIME_TAGS:
                    value = getattr(track, key, None)
                    if value:
                        value = str(value).replace("UTC ", "")
                        try:
                            asset.timestamp = datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S").isoformat()
                            asset.timestamp_source = "video_meta"
                            break
                        except ValueError:
                            continue
                if asset.timestamp:
                    break
        except Exception:
            pass

    return asset


def scan_folder(root: Path, image_exts=IMAGE_EXTS, video_exts=VIDEO_EXTS) -> list[Asset]:
    root = Path(root).resolve()
    assets: list[Asset] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        if ext not in image_exts and ext not in video_exts:
            continue

        rel = str(path.relative_to(root)).replace("\\", "/")

        if ext in image_exts:
            asset = _read_image(path)
        else:
            asset = _read_video(path)

        asset.relative_path = rel
        asset.id = stable_id(rel)

        if asset.timestamp is None:
            # An earlier private prototype silently dropped items with no
            # embedded timestamp. We keep the asset and fall back to mtime
            # so nothing selected by the user ever disappears from the scan.
            asset.timestamp = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            asset.timestamp_source = "mtime"

        assets.append(asset)

    return assets


def write_assets_json(assets: list[Asset], root: Path, out_path: Path) -> Path:
    payload = {
        "scan_root": str(Path(root).resolve()),
        "scanned_at": datetime.now().isoformat(),
        "count": len(assets),
        "assets": [asdict(a) for a in assets],
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def scan(root: Path, out_path: Path) -> Path:
    assets = scan_folder(root)
    return write_assets_json(assets, root, out_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scan a folder of photos/videos into assets.json")
    parser.add_argument("folder", type=Path)
    parser.add_argument("--out", type=Path, default=Path("assets.json"))
    args = parser.parse_args()

    out = scan(args.folder, args.out)
    print(f"Wrote {out}")
