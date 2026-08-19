"""Deterministic, rule-based edit planning. No LLM, no semantic model.

An earlier private prototype never varied shot duration by content
quality across its several iterations — each used one fixed duration for
every photo, changing only between prototype versions, never within a
run. Variable duration-by-score is new logic for this project.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from score import assign_temporal_clusters, ScoreConfig


@dataclass
class PlanConfig:
    target_duration_seconds: float = 180.0
    chapter_gap_hours: float = 6.0
    shot_duration_min: float = 2.5
    shot_duration_base: float = 4.0
    shot_duration_max: float = 7.0
    shot_duration_chapter_edge_bonus: float = 1.5
    video_max_seconds: float = 8.0
    high_score_threshold: float = 80.0
    low_score_threshold: float = 50.0
    strong_face_ratio: float = 0.05


def _base_duration(asset: dict, cfg: PlanConfig) -> tuple[float, str]:
    """Rule-based duration before chapter-edge/budget adjustments.
    Returns (seconds, reason) so the plan stays human-readable."""
    if asset["type"] == "video":
        dur = min(asset.get("duration") or cfg.video_max_seconds, cfg.video_max_seconds)
        return round(dur, 2), "video_clip"

    score = asset.get("quality_score", 0.0)
    has_strong_face = asset.get("face_count", 0) > 0 and asset.get("largest_face_ratio", 0.0) >= cfg.strong_face_ratio

    if score >= cfg.high_score_threshold and has_strong_face:
        return cfg.shot_duration_max, "high_score_strong_face"
    if score < cfg.low_score_threshold or asset.get("face_count", 0) == 0:
        return cfg.shot_duration_min, "transitional"
    return cfg.shot_duration_base, "base"


def _fit_to_budget(shots: list[dict], target_seconds: float, cfg: PlanConfig) -> None:
    """Mutates shots in place: disables lowest-quality shots first if over
    budget (keeping >=1 enabled shot per chapter where possible), then applies
    a final proportional scale within [min,max] bounds if still off-target."""
    def enabled_total() -> float:
        return sum(s["duration"] for s in shots if s["enabled"])

    total = enabled_total()
    if total <= target_seconds:
        # Under budget: stretch photo durations proportionally, capped at max,
        # so a short folder doesn't render with a lot of unused target time.
        if total <= 0:
            return
        photos = [s for s in shots if s["enabled"] and s["type"] == "image"]
        if not photos:
            return
        headroom = target_seconds - total
        stretchable = sum(cfg.shot_duration_max - s["duration"] for s in photos)
        if stretchable <= 0:
            return
        for s in photos:
            room = cfg.shot_duration_max - s["duration"]
            if room <= 0:
                continue
            add = headroom * (room / stretchable)
            s["duration"] = round(min(s["duration"] + add, cfg.shot_duration_max), 2)
        return

    # Over budget: drop lowest quality_score shots first, chapter by chapter,
    # never emptying a chapter entirely while alternatives remain.
    by_chapter: dict[int, list[dict]] = {}
    for s in shots:
        by_chapter.setdefault(s["chapter_id"], []).append(s)

    candidates = sorted(
        (s for s in shots if s["enabled"]),
        key=lambda s: s.get("quality_score", 0.0),
    )
    for s in candidates:
        if enabled_total() <= target_seconds:
            break
        chapter_enabled = [x for x in by_chapter[s["chapter_id"]] if x["enabled"]]
        if len(chapter_enabled) <= 1:
            continue  # keep at least one shot per chapter
        s["enabled"] = False
        s["reason"] = "budget_suppressed"

    total = enabled_total()
    if total > target_seconds and total > 0:
        # Still over (every chapter down to one shot each): scale proportionally
        # down to shot_duration_min instead of disabling further.
        scale = target_seconds / total
        for s in shots:
            if not s["enabled"]:
                continue
            s["duration"] = round(max(s["duration"] * scale, cfg.shot_duration_min), 2)


def build_plan(scored_assets_path: Path, cfg: Optional[PlanConfig] = None) -> dict:
    cfg = cfg or PlanConfig()
    payload = json.loads(Path(scored_assets_path).read_text(encoding="utf-8"))
    assets = [a for a in payload["assets"] if not a.get("error") and not a.get("score_error")]

    assign_temporal_clusters(assets, cfg.chapter_gap_hours * 60.0, field="chapter_id")
    assets.sort(key=lambda a: a["timestamp"])

    shots = []
    for order, asset in enumerate(assets):
        duration, reason = _base_duration(asset, cfg)
        enabled = not asset.get("is_duplicate", False)
        if not enabled:
            reason = "duplicate_suppressed"
        shots.append({
            "shot_id": f"s_{order:04d}",
            "asset_id": asset["id"],
            "asset_path": asset["path"],
            "type": asset["type"],
            "chapter_id": asset["chapter_id"],
            "order": order,
            "enabled": enabled,
            "duration": duration,
            "reason": reason,
            "quality_score": asset.get("quality_score", 0.0),
            "timestamp": asset["timestamp"],
            "title_text": None,  # user-editable chapter/title card text
        })

    # Chapter-edge bonus: first/last *enabled* shot in each chapter gets a
    # slightly longer hold, per your spec ("chapter opening/closing shots
    # slightly longer"). Applied to photos only — video length is source-driven.
    chapters: dict[int, list[dict]] = {}
    for s in shots:
        chapters.setdefault(s["chapter_id"], []).append(s)
    for chapter_shots in chapters.values():
        enabled_shots = [s for s in chapter_shots if s["enabled"]]
        for edge_shot in (enabled_shots[:1] + enabled_shots[-1:]):
            if edge_shot["type"] == "image":
                edge_shot["duration"] = round(
                    min(edge_shot["duration"] + cfg.shot_duration_chapter_edge_bonus, cfg.shot_duration_max), 2
                )
                edge_shot["reason"] += "+chapter_edge"

    _fit_to_budget(shots, cfg.target_duration_seconds, cfg)

    chapter_summaries = []
    for chapter_id in sorted(chapters):
        chapter_shots = chapters[chapter_id]
        first_ts = chapter_shots[0]["timestamp"]
        date_label = first_ts.split("T")[0] if "T" in first_ts else first_ts
        chapter_summaries.append({
            "chapter_id": chapter_id,
            "title": f"Chapter {chapter_id + 1} · {date_label}",
            "shot_count": len(chapter_shots),
            "enabled_shot_count": sum(1 for s in chapter_shots if s["enabled"]),
        })

    total_duration = round(sum(s["duration"] for s in shots if s["enabled"]), 2)

    return {
        "created_at": datetime.now().isoformat(),
        "source_assets_json": str(Path(scored_assets_path).resolve()),
        "target_duration_seconds": cfg.target_duration_seconds,
        "total_planned_duration": total_duration,
        "chapters": chapter_summaries,
        "shots": shots,
    }


def write_plan(scored_assets_path: Path, out_path: Path, cfg: Optional[PlanConfig] = None) -> Path:
    plan = build_plan(scored_assets_path, cfg)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build plan.json from a scored assets.json")
    parser.add_argument("scored_assets_json", type=Path)
    parser.add_argument("--out", type=Path, default=Path("plan.json"))
    parser.add_argument("--target-seconds", type=float, default=180.0)
    args = parser.parse_args()

    cfg = PlanConfig(target_duration_seconds=args.target_seconds)
    out = write_plan(args.scored_assets_json, args.out, cfg)
    print(f"Wrote {out}")
