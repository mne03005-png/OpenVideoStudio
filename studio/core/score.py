"""Media scoring — traditional/local signals only. No cloud upload, no VLM.

An earlier private prototype instantiated a MediaPipe face detector but
never actually called it — the crop logic silently fell back to a plain
center-crop. This module is the first real use of face detection in this
codebase; nothing here is reused from that prototype, it's new.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import imagehash
import numpy as np
from PIL import Image
from mediapipe import Image as MPImage, ImageFormat
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

_FACE_MODEL_PATH = Path(__file__).resolve().parent.parent / "assets" / "face_detector.tflite"


@dataclass
class ScoreConfig:
    sharpness_low: float = 30.0
    sharpness_high: float = 300.0
    brightness_low: float = 25.0
    brightness_high: float = 235.0
    duplicate_hash_distance: int = 5
    burst_window_seconds: float = 2.0
    temporal_cluster_gap_minutes: float = 30.0


def load_face_detector(model_path: Path = _FACE_MODEL_PATH) -> mp_vision.FaceDetector:
    options = mp_vision.FaceDetectorOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
        min_detection_confidence=0.5,
    )
    return mp_vision.FaceDetector.create_from_options(options)


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def laplacian_sharpness(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def brightness(gray: np.ndarray) -> float:
    return float(gray.mean())


def _score_from_range(value: float, low: float, high: float) -> float:
    """0 below low, 1 above high, linear ramp between."""
    if high <= low:
        return 1.0
    return _clamp01((value - low) / (high - low))


def _brightness_score(value: float, low: float, high: float) -> float:
    """Full score inside [low, high], linear falloff outside toward 0/255."""
    if low <= value <= high:
        return 1.0
    if value < low:
        return _clamp01(value / max(low, 1.0))
    return _clamp01((255.0 - value) / max(255.0 - high, 1.0))


def detect_faces(image_bgr: np.ndarray, detector: mp_vision.FaceDetector) -> list[dict]:
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    mp_img = MPImage(image_format=ImageFormat.SRGB, data=rgb)
    result = detector.detect(mp_img)
    h, w = image_bgr.shape[:2]
    faces = []
    for det in result.detections:
        bbox = det.bounding_box
        area_ratio = (bbox.width * bbox.height) / float(w * h) if w and h else 0.0
        faces.append({
            "x": bbox.origin_x, "y": bbox.origin_y,
            "width": bbox.width, "height": bbox.height,
            "area_ratio": round(area_ratio, 4),
            "confidence": round(det.categories[0].score, 4) if det.categories else None,
        })
    return faces


def imread_unicode(path: Path) -> Optional[np.ndarray]:
    """cv2.imread silently returns None for non-ASCII Windows paths (a known
    OpenCV limitation). Reading bytes ourselves and decoding avoids it."""
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None


def score_image(path: Path, detector: mp_vision.FaceDetector, cfg: ScoreConfig) -> dict:
    img = imread_unicode(path)
    if img is None:
        return {"error": "cv2_read_failed"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sharp = laplacian_sharpness(gray)
    bright = brightness(gray)

    faces = detect_faces(img, detector)
    face_count = len(faces)
    largest_face_ratio = max((f["area_ratio"] for f in faces), default=0.0)

    try:
        with Image.open(path) as pil_img:
            phash = str(imagehash.phash(pil_img))
    except Exception:
        phash = None

    sharp_score = _score_from_range(sharp, cfg.sharpness_low, cfg.sharpness_high)
    bright_score = _brightness_score(bright, cfg.brightness_low, cfg.brightness_high)
    face_score = _clamp01(0.6 + largest_face_ratio * 4.0) if face_count else 0.0

    quality_score = round(100 * (0.4 * sharp_score + 0.2 * bright_score + 0.4 * face_score), 1)

    return {
        "sharpness": round(sharp, 2),
        "brightness": round(bright, 2),
        "face_count": face_count,
        "largest_face_ratio": largest_face_ratio,
        "phash": phash,
        "quality_score": quality_score,
    }


def score_video(path: Path, detector: Optional[mp_vision.FaceDetector], cfg: ScoreConfig,
                 duration: Optional[float] = None, sample_count: int = 5) -> dict:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return {"error": "cv2_video_open_failed"}

    frame_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    sharp_vals, bright_vals = [], []
    has_face = False
    largest_face_ratio = 0.0

    if frame_total > 0:
        indices = sorted(set(int(frame_total * i / (sample_count + 1)) for i in range(1, sample_count + 1)))
    else:
        indices = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sharp_vals.append(laplacian_sharpness(gray))
        bright_vals.append(brightness(gray))
        if detector is not None:
            faces = detect_faces(frame, detector)
            if faces:
                has_face = True
                largest_face_ratio = max(largest_face_ratio, max(f["area_ratio"] for f in faces))
    cap.release()

    if not sharp_vals:
        return {"error": "no_frames_sampled"}

    sharp = sum(sharp_vals) / len(sharp_vals)
    bright = sum(bright_vals) / len(bright_vals)

    sharp_score = _score_from_range(sharp, cfg.sharpness_low, cfg.sharpness_high)
    bright_score = _brightness_score(bright, cfg.brightness_low, cfg.brightness_high)
    face_score = _clamp01(0.6 + largest_face_ratio * 4.0) if has_face else 0.0
    duration_penalty = 1.0 if (duration or 999) >= 0.5 else 0.5

    quality_score = round(100 * duration_penalty * (0.4 * sharp_score + 0.2 * bright_score + 0.4 * face_score), 1)

    return {
        "sharpness": round(sharp, 2),
        "brightness": round(bright, 2),
        "has_face": has_face,
        "largest_face_ratio": round(largest_face_ratio, 4),
        "quality_score": quality_score,
    }


def hamming_distance(hash_a: str, hash_b: str) -> int:
    return imagehash.hex_to_hash(hash_a) - imagehash.hex_to_hash(hash_b)


def group_bursts(assets: list[dict], cfg: ScoreConfig) -> None:
    """Mutates assets in place: assigns burst_id and is_duplicate, keeping the
    highest quality_score in each burst as the non-duplicate primary."""
    images = [a for a in assets if a.get("type") == "image" and a.get("phash")]
    images.sort(key=lambda a: a["timestamp"])

    burst_id = 0
    i = 0
    while i < len(images):
        group = [images[i]]
        t0 = datetime.fromisoformat(images[i]["timestamp"])
        j = i + 1
        while j < len(images):
            tj = datetime.fromisoformat(images[j]["timestamp"])
            if (tj - t0).total_seconds() > cfg.burst_window_seconds:
                break
            if hamming_distance(images[i]["phash"], images[j]["phash"]) <= cfg.duplicate_hash_distance:
                group.append(images[j])
                j += 1
            else:
                break

        if len(group) > 1:
            burst_id += 1
            best = max(group, key=lambda a: a.get("quality_score", 0))
            for a in group:
                a["burst_id"] = burst_id
                a["is_duplicate"] = a["id"] != best["id"]
                a["burst_primary_id"] = best["id"]
        else:
            group[0].setdefault("burst_id", None)
            group[0].setdefault("is_duplicate", False)
            group[0].setdefault("burst_primary_id", None)

        i = j if j > i + 1 else i + 1


def assign_temporal_clusters(assets: list[dict], gap_minutes: float, field: str = "temporal_cluster") -> None:
    """Mutates assets in place: assigns a cluster id whenever the gap since the
    previous (chronologically sorted) asset exceeds gap_minutes."""
    ordered = sorted(assets, key=lambda a: a["timestamp"])
    cluster = 0
    prev_t = None
    for a in ordered:
        t = datetime.fromisoformat(a["timestamp"])
        if prev_t is not None and (t - prev_t).total_seconds() / 60.0 > gap_minutes:
            cluster += 1
        a[field] = cluster
        prev_t = t


def score_assets(assets_json_path: Path, out_path: Path, cfg: Optional[ScoreConfig] = None) -> Path:
    cfg = cfg or ScoreConfig()
    payload = json.loads(Path(assets_json_path).read_text(encoding="utf-8"))
    assets = payload["assets"]

    detector = load_face_detector()
    try:
        for asset in assets:
            path = Path(asset["path"])
            if not path.exists():
                asset["score_error"] = "file_missing"
                continue
            if asset["type"] == "image":
                result = score_image(path, detector, cfg)
            else:
                result = score_video(path, detector, cfg, duration=asset.get("duration"))
            asset.update(result)
    finally:
        detector.close()

    group_bursts(assets, cfg)
    assign_temporal_clusters(assets, cfg.temporal_cluster_gap_minutes)

    payload["scored_at"] = datetime.now().isoformat()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Score assets.json in place (or to a new file)")
    parser.add_argument("assets_json", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    out = args.out or args.assets_json
    result = score_assets(args.assets_json, out)
    print(f"Wrote {result}")
