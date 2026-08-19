"""Stage-based, resumable orchestration: scan -> score -> plan -> [review
gate] -> render -> audio/final.

Deliberately NOT a "Full Auto" black box: run_render() is never called
automatically after run_plan() finishes. The caller (app.py) must present
plan.json for review and get an explicit go-ahead first. This mirrors a
safety pattern found in an earlier private orchestrator, which
deliberately disabled its own fully-automatic mode so QC decisions
couldn't be skipped by automation.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import scan as scan_mod
import score as score_mod
import plan as plan_mod
import render as render_mod
import audio as audio_mod

STAGES = ["scan", "score", "plan", "render", "audio"]


@dataclass
class RunState:
    run_id: str
    source_folder: str
    style: str
    target_duration_seconds: float
    bgm_path: Optional[str]
    created_at: str
    updated_at: str
    current_stage: Optional[str] = None
    stages: dict = field(default_factory=lambda: {
        s: {"status": "pending", "timestamp": None, "error": None, "qc": None} for s in STAGES
    })
    plan_reviewed: bool = False


def run_dir_for(runs_root: Path, run_id: str) -> Path:
    return Path(runs_root) / run_id


def _now() -> str:
    return datetime.now().isoformat()


def new_run(runs_root: Path, source_folder: Path, style: str, target_duration_seconds: float,
            bgm_path: Optional[Path] = None) -> RunState:
    run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    rd = run_dir_for(runs_root, run_id)
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "logs").mkdir(exist_ok=True)

    state = RunState(
        run_id=run_id, source_folder=str(Path(source_folder).resolve()), style=style,
        target_duration_seconds=target_duration_seconds,
        bgm_path=str(bgm_path) if bgm_path else None,
        created_at=_now(), updated_at=_now(),
    )
    save_run_state(rd, state)
    return state


def load_run_state(run_dir: Path) -> RunState:
    data = json.loads((Path(run_dir) / "run_state.json").read_text(encoding="utf-8"))
    return RunState(**data)


def save_run_state(run_dir: Path, state: RunState) -> None:
    state.updated_at = _now()
    Path(run_dir, "run_state.json").write_text(
        json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _log(run_dir: Path, stage: str, message: str) -> None:
    log_path = Path(run_dir) / "logs" / f"{stage}.log"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{_now()}] {message}\n")


def _mark(state: RunState, stage: str, status: str, error: Optional[str] = None, qc: Optional[dict] = None) -> None:
    state.stages[stage] = {"timestamp": _now(), "status": status, "error": error, "qc": qc}
    state.current_stage = stage


def _stage_ok(state: RunState, stage: str) -> bool:
    return state.stages.get(stage, {}).get("status") == "done"


def run_scan(run_dir: Path, state: RunState, force: bool = False) -> RunState:
    run_dir = Path(run_dir)
    if _stage_ok(state, "scan") and not force:
        return state
    _mark(state, "scan", "running")
    save_run_state(run_dir, state)
    try:
        assets_path = run_dir / "assets.json"
        scan_mod.scan(Path(state.source_folder), assets_path)
        payload = json.loads(assets_path.read_text(encoding="utf-8"))
        count = payload["count"]
        qc = {"asset_count": count}
        if count == 0:
            _mark(state, "scan", "failed", error="no_media_found", qc=qc)
        else:
            _mark(state, "scan", "done", qc=qc)
        _log(run_dir, "scan", f"found {count} assets")
    except Exception as e:
        _mark(state, "scan", "failed", error=f"{e}\n{traceback.format_exc()}")
        _log(run_dir, "scan", f"FAILED: {e}")
    save_run_state(run_dir, state)
    return state


def run_score(run_dir: Path, state: RunState, force: bool = False) -> RunState:
    run_dir = Path(run_dir)
    if not _stage_ok(state, "scan"):
        _mark(state, "score", "failed", error="scan_not_done")
        save_run_state(run_dir, state)
        return state
    if _stage_ok(state, "score") and not force:
        return state
    _mark(state, "score", "running")
    save_run_state(run_dir, state)
    try:
        assets_path = run_dir / "assets.json"
        score_mod.score_assets(assets_path, assets_path)
        payload = json.loads(assets_path.read_text(encoding="utf-8"))
        scored = [a for a in payload["assets"] if not a.get("error") and not a.get("score_error")]
        qc = {"scored_count": len(scored), "total_count": len(payload["assets"])}
        if not scored:
            _mark(state, "score", "failed", error="nothing_scored_successfully", qc=qc)
        else:
            _mark(state, "score", "done", qc=qc)
        _log(run_dir, "score", f"scored {len(scored)}/{len(payload['assets'])} assets")
    except Exception as e:
        _mark(state, "score", "failed", error=f"{e}\n{traceback.format_exc()}")
        _log(run_dir, "score", f"FAILED: {e}")
    save_run_state(run_dir, state)
    return state


def run_plan(run_dir: Path, state: RunState, force: bool = False) -> RunState:
    run_dir = Path(run_dir)
    if not _stage_ok(state, "score"):
        _mark(state, "plan", "failed", error="score_not_done")
        save_run_state(run_dir, state)
        return state
    if _stage_ok(state, "plan") and not force:
        return state
    _mark(state, "plan", "running")
    save_run_state(run_dir, state)
    try:
        assets_path = run_dir / "assets.json"
        plan_path = run_dir / "plan.json"
        cfg = plan_mod.PlanConfig(target_duration_seconds=state.target_duration_seconds)
        plan_mod.write_plan(assets_path, plan_path, cfg)
        p = json.loads(plan_path.read_text(encoding="utf-8"))
        qc = {
            "shot_count": len(p["shots"]),
            "enabled_shot_count": sum(1 for s in p["shots"] if s["enabled"]),
            "total_planned_duration": p["total_planned_duration"],
        }
        if qc["enabled_shot_count"] == 0:
            _mark(state, "plan", "failed", error="no_enabled_shots", qc=qc)
        else:
            _mark(state, "plan", "done", qc=qc)
        state.plan_reviewed = False  # every new/rerun plan needs re-review
        _log(run_dir, "plan", f"{qc}")
    except Exception as e:
        _mark(state, "plan", "failed", error=f"{e}\n{traceback.format_exc()}")
        _log(run_dir, "plan", f"FAILED: {e}")
    save_run_state(run_dir, state)
    return state


def approve_plan(run_dir: Path, state: RunState) -> RunState:
    """Explicit review-gate confirmation. render() refuses to run without this."""
    state.plan_reviewed = True
    save_run_state(Path(run_dir), state)
    return state


def run_render(run_dir: Path, state: RunState, force: bool = False) -> RunState:
    run_dir = Path(run_dir)
    if not _stage_ok(state, "plan"):
        _mark(state, "render", "failed", error="plan_not_done")
        save_run_state(run_dir, state)
        return state
    if not state.plan_reviewed:
        _mark(state, "render", "failed", error="plan_not_reviewed")
        save_run_state(run_dir, state)
        return state
    if _stage_ok(state, "render") and not force:
        return state
    _mark(state, "render", "running")
    save_run_state(run_dir, state)
    try:
        plan_path = run_dir / "plan.json"
        work_dir = run_dir / "render_work"
        output_path = run_dir / "output.mp4"
        render_json_path = run_dir / "render.json"
        cfg = render_mod.RenderConfig.from_toml(Path(__file__).resolve().parent.parent / "config.toml")
        result = render_mod.render_plan(plan_path, work_dir, output_path, cfg, render_json_path)
        qc = {"succeeded": result["succeeded"], "failed": result["failed"], "status": result["status"]}
        if result["status"] != "ok":
            _mark(state, "render", "failed", error="render_failed", qc=qc)
        else:
            _mark(state, "render", "done", qc=qc)
        _log(run_dir, "render", f"{qc}")
    except Exception as e:
        _mark(state, "render", "failed", error=f"{e}\n{traceback.format_exc()}")
        _log(run_dir, "render", f"FAILED: {e}")
    save_run_state(run_dir, state)
    return state


def run_audio(run_dir: Path, state: RunState, force: bool = False) -> RunState:
    run_dir = Path(run_dir)
    if not _stage_ok(state, "render"):
        _mark(state, "audio", "failed", error="render_not_done")
        save_run_state(run_dir, state)
        return state
    if _stage_ok(state, "audio") and not force:
        return state
    _mark(state, "audio", "running")
    save_run_state(run_dir, state)
    try:
        output_path = run_dir / "output.mp4"
        final_path = run_dir / "final.mp4"
        cfg = audio_mod.AudioConfig.from_toml(Path(__file__).resolve().parent.parent / "config.toml")
        bgm_path = Path(state.bgm_path) if state.bgm_path else None
        ok, log = audio_mod.mix_bgm(output_path, bgm_path, final_path, cfg)
        qc = {"final_exists": final_path.exists()}
        if not ok or not final_path.exists():
            _mark(state, "audio", "failed", error=log or "mix_failed", qc=qc)
        else:
            _mark(state, "audio", "done", qc=qc)
        _log(run_dir, "audio", f"{qc}")
    except Exception as e:
        _mark(state, "audio", "failed", error=f"{e}\n{traceback.format_exc()}")
        _log(run_dir, "audio", f"FAILED: {e}")
    save_run_state(run_dir, state)
    return state


def run_to_plan(run_dir: Path, state: RunState) -> RunState:
    """Runs scan -> score -> plan, stopping at the review gate. Resumable:
    stages already marked 'done' are skipped."""
    state = run_scan(run_dir, state)
    if not _stage_ok(state, "scan"):
        return state
    state = run_score(run_dir, state)
    if not _stage_ok(state, "score"):
        return state
    state = run_plan(run_dir, state)
    return state


def run_after_review(run_dir: Path, state: RunState) -> RunState:
    """Runs render -> audio. Only proceeds if the plan has been explicitly
    approved via approve_plan()."""
    state = run_render(run_dir, state)
    if not _stage_ok(state, "render"):
        return state
    state = run_audio(run_dir, state)
    return state


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the V1 pipeline end-to-end (CLI/testing use)")
    parser.add_argument("source_folder", type=Path)
    parser.add_argument("--runs-root", type=Path, default=Path(__file__).resolve().parent.parent / "runs")
    parser.add_argument("--style", default="Family Memory")
    parser.add_argument("--target-seconds", type=float, default=180.0)
    parser.add_argument("--bgm", type=Path, default=None)
    parser.add_argument("--auto-approve", action="store_true", help="skip manual review gate (CLI testing only)")
    args = parser.parse_args()

    st = new_run(args.runs_root, args.source_folder, args.style, args.target_seconds, args.bgm)
    rd = run_dir_for(args.runs_root, st.run_id)
    st = run_to_plan(rd, st)
    print(json.dumps(st.stages, indent=2))

    if args.auto_approve and _stage_ok(st, "plan"):
        st = approve_plan(rd, st)
        st = run_after_review(rd, st)
        print(json.dumps(st.stages, indent=2))
