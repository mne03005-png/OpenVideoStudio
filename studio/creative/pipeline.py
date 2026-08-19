"""AI Creation orchestrator. Same RunState/resumability/logging shape as
core/pipeline.py (Media Remix) — copied pattern, not shared code, per the
architecture report.

Hard gate: keyframes, clips, narration, and the final edit ALL individually
refuse to run unless storyboard_reviewed is True — checked inside each
function, not just relied on via call order, so nothing can accidentally
skip the review.

GPU sequencing for this 6GB card:
  Ollama (script+storyboard) -> unload (keep_alive=0 + explicit unload())
  -> ComfyUI/SDXL (keyframes) -> /free
  -> ComfyUI/LTX (clips) -> /free
  -> FFmpeg/NVENC (edit, reusing core/render.py + core/audio.py)
Nothing here runs two heavy models concurrently by design.
"""
from __future__ import annotations

import json
import subprocess
import sys
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# Both inserts are needed for `python creative/pipeline.py ...` (direct
# script invocation, not `python -m creative.pipeline`) to work: sys.path[0]
# is set to creative/ itself in that mode, so neither `core` (Media Remix's
# flat-import style) nor `creative`/`providers` (this package's own imports
# below) would otherwise resolve.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "core"))

import render as render_mod  # noqa: E402
import audio as audio_mod  # noqa: E402

from creative.script import generate_script  # noqa: E402
from creative.storyboard import generate_storyboard  # noqa: E402
from creative.keyframes import generate_keyframes  # noqa: E402
from creative.clips import generate_clips  # noqa: E402
from creative.narration import generate_narration  # noqa: E402
from creative.subtitles import generate_subtitles  # noqa: E402
from providers.registry import get_provider  # noqa: E402
from providers._comfy_client import ComfyClient  # noqa: E402

STAGES = ["script", "storyboard", "keyframes", "clips", "narration", "subtitles", "edit"]

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"


def _config() -> dict:
    import tomllib
    return tomllib.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


def _ollama_server() -> str:
    return _config().get("providers", {}).get("ollama_server", "http://127.0.0.1:11434")


def _provider_name(kind: str, default: str) -> str:
    """Which concrete provider to instantiate for a given provider kind
    (llm/image/video/tts), read from config.toml's [providers] section —
    the whole point of a provider registry is that swapping providers is a
    config change, not a code change (see providers/registry.py)."""
    return _config().get("providers", {}).get(kind, default)


def _default_ollama_model() -> str:
    """config.toml's own [providers] comment says the model name is
    "configurable here on purpose — never hardcode it" — read it instead
    of hardcoding a literal default, here or at any caller that doesn't
    have a more specific choice of its own."""
    return _config().get("providers", {}).get("ollama_model", "qwen3:8b")

_ASPECT_RATIOS = {
    "9:16": (448, 768),   # proven on 6GB VRAM, see docs/HARDWARE.md
    "16:9": (768, 448),   # same pixel budget, swapped; not yet separately validated
    "1:1": (608, 608),    # not yet separately validated
}


@dataclass
class CreativeRunState:
    run_id: str
    prompt: str
    target_duration_seconds: float
    style: str
    aspect_ratio: str
    language: str
    llm_model: str
    bgm_path: Optional[str]
    created_at: str
    updated_at: str
    current_stage: Optional[str] = None
    storyboard_reviewed: bool = False
    stages: dict = field(default_factory=lambda: {
        s: {"status": "pending", "timestamp": None, "error": None, "qc": None} for s in STAGES
    })


def run_dir_for(runs_root: Path, run_id: str) -> Path:
    return Path(runs_root) / run_id


def _now() -> str:
    return datetime.now().isoformat()


def new_run(
    runs_root: Path, prompt: str, target_duration_seconds: float, style: str,
    aspect_ratio: str = "9:16", language: str = "en", llm_model: Optional[str] = None,
    bgm_path: Optional[Path] = None,
) -> CreativeRunState:
    llm_model = llm_model or _default_ollama_model()
    run_id = datetime.now().strftime("create_%Y%m%d_%H%M%S")
    rd = run_dir_for(runs_root, run_id)
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "logs").mkdir(exist_ok=True)

    state = CreativeRunState(
        run_id=run_id, prompt=prompt, target_duration_seconds=target_duration_seconds,
        style=style, aspect_ratio=aspect_ratio, language=language, llm_model=llm_model,
        bgm_path=str(bgm_path) if bgm_path else None, created_at=_now(), updated_at=_now(),
    )
    save_run_state(rd, state)
    return state


def load_run_state(run_dir: Path) -> CreativeRunState:
    data = json.loads((Path(run_dir) / "run_state.json").read_text(encoding="utf-8"))
    return CreativeRunState(**data)


def save_run_state(run_dir: Path, state: CreativeRunState) -> None:
    state.updated_at = _now()
    Path(run_dir, "run_state.json").write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")


def _log(run_dir: Path, stage: str, message: str) -> None:
    with open(Path(run_dir) / "logs" / f"{stage}.log", "a", encoding="utf-8") as f:
        f.write(f"[{_now()}] {message}\n")


def _mark(state: CreativeRunState, stage: str, status: str, error: Optional[str] = None, qc: Optional[dict] = None) -> None:
    state.stages[stage] = {"timestamp": _now(), "status": status, "error": error, "qc": qc}
    state.current_stage = stage


def _stage_ok(state: CreativeRunState, stage: str) -> bool:
    return state.stages.get(stage, {}).get("status") == "done"


def _require_review(state: CreativeRunState, stage: str, run_dir: Path) -> bool:
    """The hard gate. Every generation-adjacent stage calls this first."""
    if not state.storyboard_reviewed:
        _mark(state, stage, "failed", error="storyboard_not_reviewed")
        save_run_state(run_dir, state)
        _log(run_dir, stage, "REFUSED: storyboard not yet approved")
        return False
    return True


# ---------------------------------------------------------------- script ---
def run_script(run_dir: Path, state: CreativeRunState, force: bool = False) -> CreativeRunState:
    run_dir = Path(run_dir)
    if _stage_ok(state, "script") and not force:
        return state
    _mark(state, "script", "running")
    save_run_state(run_dir, state)
    try:
        llm = get_provider("llm", _provider_name("llm", "ollama"), model=state.llm_model, server=_ollama_server())
        if not llm.is_available():
            raise RuntimeError("Ollama is not reachable — is it installed and running?")
        script = generate_script(llm, state.prompt, state.target_duration_seconds, state.style, state.language)
        (run_dir / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
        qc = {"scene_count": len(script["scenes"]), "title": script.get("title")}
        _mark(state, "script", "done", qc=qc)
        _log(run_dir, "script", f"{qc}")
    except Exception as e:
        _mark(state, "script", "failed", error=f"{e}\n{traceback.format_exc()}")
        _log(run_dir, "script", f"FAILED: {e}")
    save_run_state(run_dir, state)
    return state


# ------------------------------------------------------------ storyboard ---
def run_storyboard(run_dir: Path, state: CreativeRunState, force: bool = False) -> CreativeRunState:
    run_dir = Path(run_dir)
    if not _stage_ok(state, "script"):
        _mark(state, "storyboard", "failed", error="script_not_done")
        save_run_state(run_dir, state)
        return state
    if _stage_ok(state, "storyboard") and not force:
        return state
    _mark(state, "storyboard", "running")
    save_run_state(run_dir, state)
    try:
        script = json.loads((run_dir / "script.json").read_text(encoding="utf-8"))
        llm = get_provider("llm", _provider_name("llm", "ollama"), model=state.llm_model, server=_ollama_server())
        storyboard = generate_storyboard(llm, script, state.language)
        (run_dir / "storyboard.json").write_text(json.dumps(storyboard, ensure_ascii=False, indent=2), encoding="utf-8")

        # Last LLM call in the pipeline — release VRAM now, before ComfyUI needs it.
        llm.unload()

        has_character = storyboard.get("character_identity") is not None
        qc = {
            "scene_count": len(storyboard["scenes"]),
            "has_recurring_character": has_character,
            "narrative_quality_warnings": len(storyboard.get("narrative_quality_warnings", [])),
        }
        _mark(state, "storyboard", "done", qc=qc)
        state.storyboard_reviewed = False  # any new/rerun storyboard needs re-review
        _log(run_dir, "storyboard", f"{qc}; LLM unloaded")
        for warning in storyboard.get("narrative_quality_warnings", []):
            _log(run_dir, "storyboard", f"WARNING: {warning}")
    except Exception as e:
        _mark(state, "storyboard", "failed", error=f"{e}\n{traceback.format_exc()}")
        _log(run_dir, "storyboard", f"FAILED: {e}")
    save_run_state(run_dir, state)
    return state


def approve_storyboard(run_dir: Path, state: CreativeRunState) -> CreativeRunState:
    state.storyboard_reviewed = True
    save_run_state(Path(run_dir), state)
    return state


def _free_with_retry(client, attempts: int = 3, delay_seconds: float = 2.0) -> bool:
    """VRAM release between SDXL and LTX is load-bearing on this 6GB card —
    an unconfirmed /free must not be treated as a soft warning while the
    pipeline barrels on into the next heavy model. Retry briefly, and let
    the caller decide the stage failed if it's still unconfirmed."""
    import time
    for i in range(attempts):
        if client.free():
            return True
        if i < attempts - 1:
            time.sleep(delay_seconds)
    return False


# -------------------------------------------------------------- keyframes ---
def run_keyframes(run_dir: Path, state: CreativeRunState, force: bool = False) -> CreativeRunState:
    run_dir = Path(run_dir)
    if not _require_review(state, "keyframes", run_dir):
        return state
    if not _stage_ok(state, "storyboard"):
        _mark(state, "keyframes", "failed", error="storyboard_not_done")
        save_run_state(run_dir, state)
        return state
    if _stage_ok(state, "keyframes") and not force:
        return state
    _mark(state, "keyframes", "running")
    save_run_state(run_dir, state)
    try:
        storyboard = json.loads((run_dir / "storyboard.json").read_text(encoding="utf-8"))
        width, height = _ASPECT_RATIOS.get(state.aspect_ratio, _ASPECT_RATIOS["9:16"])
        image_provider = get_provider("image", _provider_name("image", "comfyui_sdxl"))

        def _checkpoint(sb: dict) -> None:
            (run_dir / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")

        freed = False
        try:
            storyboard = generate_keyframes(
                image_provider, storyboard, run_dir / "keyframes", width, height, checkpoint=_checkpoint
            )
        finally:
            # Always attempt VRAM release before LTX needs it, even on failure —
            # a partial SDXL failure must not leave SDXL resident going into clips.
            freed = _free_with_retry(image_provider.client)
            _checkpoint(storyboard)

        ok_count = sum(1 for s in storyboard["scenes"] if s.get("keyframe_path"))
        total = len(storyboard["scenes"])
        qc = {"generated": ok_count, "total": total}
        if ok_count == total and freed:
            _mark(state, "keyframes", "done", qc=qc)
        elif ok_count == total:
            # All scenes generated, but SDXL release was never confirmed —
            # don't let LTX start on top of it. Downstream stages check
            # keyframe_path directly on resume, so nothing generated is lost.
            _mark(state, "keyframes", "failed", error="comfy_free_unconfirmed", qc=qc)
        else:
            _mark(state, "keyframes", "failed", error="incomplete_keyframes", qc=qc)
        _log(run_dir, "keyframes", f"{qc}; ComfyUI /free {'confirmed' if freed else 'FAILED after retries'}")
    except Exception as e:
        _mark(state, "keyframes", "failed", error=f"{e}\n{traceback.format_exc()}")
        _log(run_dir, "keyframes", f"FAILED: {e}")
    save_run_state(run_dir, state)
    return state


# ------------------------------------------------------------------ clips ---
def run_clips(run_dir: Path, state: CreativeRunState, force: bool = False) -> CreativeRunState:
    run_dir = Path(run_dir)
    if not _require_review(state, "clips", run_dir):
        return state
    if not _stage_ok(state, "keyframes"):
        _mark(state, "clips", "failed", error="keyframes_not_done")
        save_run_state(run_dir, state)
        return state
    if _stage_ok(state, "clips") and not force:
        return state
    _mark(state, "clips", "running")
    save_run_state(run_dir, state)
    try:
        storyboard = json.loads((run_dir / "storyboard.json").read_text(encoding="utf-8"))
        width, height = _ASPECT_RATIOS.get(state.aspect_ratio, _ASPECT_RATIOS["9:16"])
        video_provider = get_provider("video", _provider_name("video", "comfyui_ltx"))

        def _checkpoint(sb: dict) -> None:
            (run_dir / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")

        freed = False
        try:
            storyboard = generate_clips(
                video_provider, storyboard, run_dir / "clips", width, height, checkpoint=_checkpoint
            )
        finally:
            # Always attempt release before the FFmpeg/NVENC edit stage, even on failure.
            freed = _free_with_retry(video_provider.client)
            _checkpoint(storyboard)

        ok_count = sum(1 for s in storyboard["scenes"] if s.get("clip_path"))
        total = len(storyboard["scenes"])
        qc = {"generated": ok_count, "total": total}
        if ok_count == total and freed:
            _mark(state, "clips", "done", qc=qc)
        elif ok_count == total:
            _mark(state, "clips", "failed", error="comfy_free_unconfirmed", qc=qc)
        else:
            _mark(state, "clips", "failed", error="incomplete_clips", qc=qc)
        _log(run_dir, "clips", f"{qc}; ComfyUI /free {'confirmed' if freed else 'FAILED after retries'}")
    except Exception as e:
        _mark(state, "clips", "failed", error=f"{e}\n{traceback.format_exc()}")
        _log(run_dir, "clips", f"FAILED: {e}")
    save_run_state(run_dir, state)
    return state


# -------------------------------------------------------------- narration ---
def run_narration(run_dir: Path, state: CreativeRunState, force: bool = False) -> CreativeRunState:
    run_dir = Path(run_dir)
    if not _require_review(state, "narration", run_dir):
        return state
    if not _stage_ok(state, "clips"):
        _mark(state, "narration", "failed", error="clips_not_done")
        save_run_state(run_dir, state)
        return state
    if _stage_ok(state, "narration") and not force:
        return state
    _mark(state, "narration", "running")
    save_run_state(run_dir, state)
    try:
        storyboard = json.loads((run_dir / "storyboard.json").read_text(encoding="utf-8"))
        tts_provider = get_provider("tts", _provider_name("tts", "edge_tts"))
        storyboard = generate_narration(tts_provider, storyboard, run_dir / "narration", state.language)
        (run_dir / "storyboard.json").write_text(json.dumps(storyboard, ensure_ascii=False, indent=2), encoding="utf-8")

        ok_count = sum(1 for s in storyboard["scenes"] if s.get("narration_path"))
        total = len(storyboard["scenes"])
        _mark(
            state, "narration", "done" if ok_count == total else "failed",
            qc={"generated": ok_count, "total": total},
            error=None if ok_count == total else "incomplete_narration",
        )
        _log(run_dir, "narration", f"{{'generated': {ok_count}, 'total': {total}}}")
    except Exception as e:
        _mark(state, "narration", "failed", error=f"{e}\n{traceback.format_exc()}")
        _log(run_dir, "narration", f"FAILED: {e}")
    save_run_state(run_dir, state)
    return state


# -------------------------------------------------------------- subtitles ---
def run_subtitles(run_dir: Path, state: CreativeRunState, force: bool = False) -> CreativeRunState:
    run_dir = Path(run_dir)
    if not _require_review(state, "subtitles", run_dir):
        return state
    if not _stage_ok(state, "narration"):
        _mark(state, "subtitles", "failed", error="narration_not_done")
        save_run_state(run_dir, state)
        return state
    if _stage_ok(state, "subtitles") and not force:
        return state
    _mark(state, "subtitles", "running")
    save_run_state(run_dir, state)
    try:
        storyboard = json.loads((run_dir / "storyboard.json").read_text(encoding="utf-8"))
        width, height = _ASPECT_RATIOS.get(state.aspect_ratio, _ASPECT_RATIOS["9:16"])

        # clip_actual_duration is the single authoritative per-scene timeline
        # length — used for subtitle cues, video retiming, and narration
        # sync in run_edit, all three reading the same number so they can't
        # drift relative to each other. It's the LTX clip's real (ffprobe)
        # duration UNLESS narration naturally runs longer, in which case the
        # scene is extended to fit the narration (run_edit retimes the video
        # with setpts to play it back slower rather than freezing a held
        # frame, which independent review caught producing multi-second
        # static tails — see _ensure_silent_audio) rather than cutting speech
        # off mid-sentence — LTX's 8k+1 frame rounding routinely produces
        # clips shorter than requested (confirmed live: 4.38s clips for
        # 4.5-5.0s requests), which was silently truncating 1.3-2.7s of
        # narration per scene before this fix.
        for scene in storyboard["scenes"]:
            clip = scene.get("clip_path")
            if clip and Path(clip).exists():
                raw_duration = _clip_duration(Path(clip))
                narration_dur = scene.get("narration_duration") or 0.0
                scene["clip_actual_duration"] = max(raw_duration, narration_dur)
                if narration_dur > raw_duration + 0.15:
                    _log(
                        run_dir, "subtitles",
                        f"scene {scene['scene_number']}: narration_duration={narration_dur:.2f}s > "
                        f"raw clip duration={raw_duration:.2f}s — extending scene to {scene['clip_actual_duration']:.2f}s "
                        "(motion-preserving retime) in the edit stage so narration isn't cut off",
                    )
        (run_dir / "storyboard.json").write_text(json.dumps(storyboard, ensure_ascii=False, indent=2), encoding="utf-8")

        out = generate_subtitles(storyboard, run_dir / "subtitles.ass", width, height)
        qc = {"path": str(out)}
        _mark(state, "subtitles", "done", qc=qc)
        _log(run_dir, "subtitles", f"{qc}")
    except Exception as e:
        _mark(state, "subtitles", "failed", error=f"{e}\n{traceback.format_exc()}")
        _log(run_dir, "subtitles", f"FAILED: {e}")
    save_run_state(run_dir, state)
    return state


# ------------------------------------------------------------------- edit ---
_LTX_FPS = 24.0  # matches ComfyUILTXProvider.fps — LTX's fixed output frame rate


def _ensure_silent_audio(
    clip_path: Path, out_path: Path, cfg: render_mod.RenderConfig, target_duration: Optional[float] = None
) -> None:
    """Every clip needs an audio stream for the concat demuxer to work
    reliably — LTX produces video-only clips, so add synthetic silence,
    same trick core/render.py already uses for photos and audio-less video
    sources in Media Remix.

    If target_duration is longer than the clip's own length, RETIME (slow
    down) the video with setpts rather than freeze the last frame to fill
    the gap. An earlier freeze-pad version (tpad stop_mode=clone) passed
    ffprobe/decode/spot-checked frames, but ffmpeg's freezedetect filter
    caught 1.25-3.2s of fully static video per scene on both real acceptance
    runs — motion actually stops for a large fraction of the extended
    portion, which fails a real motion-quality check even though no single
    frame is corrupt. setpts keeps continuous (slowed) motion for the
    (observed ~1.2-1.6x) factor narration overrun requires instead.
    anullsrc has no natural duration, so -shortest always bounds the output
    to the (possibly retimed) video length regardless."""
    source_duration = _clip_duration(clip_path)
    cmd = [
        "ffmpeg", "-y", "-i", str(clip_path),
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate={cfg.audio_samplerate}",
        "-map", "0:v:0", "-map", "1:a:0",
    ]
    if target_duration and source_duration > 0.05 and target_duration > source_duration + 0.05:
        pts_factor = target_duration / source_duration
        cmd += [
            "-vf", f"setpts={pts_factor:.6f}*PTS,fps={_LTX_FPS}",
            "-c:v", cfg.codec, "-preset", cfg.preset, "-pix_fmt", cfg.pix_fmt,
        ]
    else:
        cmd += ["-c:v", "copy"]
    cmd += ["-c:a", cfg.audio_codec, "-b:a", cfg.audio_bitrate, "-shortest", str(out_path)]
    subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def _clip_duration(path: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return 0.0


def _sync_narration_track(storyboard: dict, work_dir: Path, cfg: audio_mod.AudioConfig) -> Path:
    """Pads/trims each scene's narration to match clip_actual_duration — the
    same authoritative per-scene duration run_edit uses to retime the
    video, so the two stay 1:1. (clip_actual_duration is already
    max(raw LTX duration, narration_duration) — see run_subtitles — so this
    now only ever pads narration with trailing silence, never trims real
    speech off; the -t here is a safety bound only, e.g. for a scene with
    no narration.)"""
    synced_paths = []
    for scene in storyboard["scenes"]:
        clip = scene.get("clip_path")
        narration = scene.get("narration_path")
        if not clip or not narration:
            continue
        target_duration = scene.get("clip_actual_duration") or _clip_duration(Path(clip))
        synced = work_dir / f"narration_synced_{scene['scene_number']:02d}.wav"
        cmd = [
            "ffmpeg", "-y", "-i", str(narration),
            "-af", "apad", "-t", str(target_duration),
            "-ar", "48000", str(synced),
        ]
        subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        synced_paths.append(synced)

    concat_file = work_dir / "narration_concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for p in synced_paths:
            f.write(f"file '{Path(p).resolve().as_posix()}'\n")

    narration_track = work_dir / "narration_track.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(narration_track)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return narration_track


def run_edit(run_dir: Path, state: CreativeRunState, force: bool = False) -> CreativeRunState:
    run_dir = Path(run_dir)
    if not _require_review(state, "edit", run_dir):
        return state
    if not _stage_ok(state, "subtitles"):
        _mark(state, "edit", "failed", error="subtitles_not_done")
        save_run_state(run_dir, state)
        return state
    if _stage_ok(state, "edit") and not force:
        return state
    _mark(state, "edit", "running")
    save_run_state(run_dir, state)
    try:
        storyboard = json.loads((run_dir / "storyboard.json").read_text(encoding="utf-8"))
        render_cfg = render_mod.RenderConfig.from_toml(Path(__file__).resolve().parent.parent / "config.toml")
        audio_cfg = audio_mod.AudioConfig.from_toml(Path(__file__).resolve().parent.parent / "config.toml")
        work_dir = run_dir / "edit_work"
        work_dir.mkdir(exist_ok=True)

        # 1. Give every clip a silent audio track (retimed via setpts to
        #    clip_actual_duration when narration runs longer than the raw
        #    LTX output — see run_subtitles), then reuse render.concat_clips() unchanged.
        silent_clips = []
        for scene in storyboard["scenes"]:
            clip = scene.get("clip_path")
            if not clip:
                continue
            dest = work_dir / f"silent_{scene['scene_number']:02d}.mp4"
            _ensure_silent_audio(Path(clip), dest, render_cfg, target_duration=scene.get("clip_actual_duration"))
            silent_clips.append(dest)

        video_master = work_dir / "video_master.mp4"
        ok, log = render_mod.concat_clips(silent_clips, work_dir, video_master, render_cfg)
        if not ok:
            raise RuntimeError(f"concat_clips failed: {log}")

        # 2. Build a narration track synced to each clip's actual duration.
        narration_track = _sync_narration_track(storyboard, work_dir, audio_cfg)

        # 3. Mux narration on as the "original" audio track and burn in subtitles —
        #    the one genuinely new step; everything else here is reused.
        subtitles_path = run_dir / "subtitles.ass"
        narrated = work_dir / "narrated.mp4"
        ass_arg = str(subtitles_path).replace("\\", "/").replace(":", "\\:")
        cmd = [
            "ffmpeg", "-y", "-i", str(video_master), "-i", str(narration_track),
            "-map", "0:v", "-map", "1:a",
            "-vf", f"ass='{ass_arg}'",
            "-c:v", render_cfg.codec, "-preset", render_cfg.preset, "-b:v", render_cfg.bitrate, "-pix_fmt", render_cfg.pix_fmt,
            "-c:a", render_cfg.audio_codec, "-b:a", render_cfg.audio_bitrate,
            "-shortest", str(narrated),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0 or not narrated.exists():
            raise RuntimeError(f"narration/subtitle mux failed: {proc.stderr[-2000:]}")

        # 4. Existing, unchanged BGM mixer.
        final_path = run_dir / "final.mp4"
        bgm_path = Path(state.bgm_path) if state.bgm_path else None
        ok, log = audio_mod.mix_bgm(narrated, bgm_path, final_path, audio_cfg)
        if not ok or not final_path.exists():
            raise RuntimeError(f"mix_bgm failed: {log}")

        qc = {"final_exists": final_path.exists(), "scenes": len(storyboard["scenes"])}
        _mark(state, "edit", "done", qc=qc)
        _log(run_dir, "edit", f"{qc}")
    except Exception as e:
        _mark(state, "edit", "failed", error=f"{e}\n{traceback.format_exc()}")
        _log(run_dir, "edit", f"FAILED: {e}")
    save_run_state(run_dir, state)
    return state


# ------------------------------------------------------------ orchestration ---
def run_to_storyboard(run_dir: Path, state: CreativeRunState) -> CreativeRunState:
    """script -> storyboard, stopping at the review gate."""
    state = run_script(run_dir, state)
    if not _stage_ok(state, "script"):
        return state
    state = run_storyboard(run_dir, state)
    return state


def run_after_review(run_dir: Path, state: CreativeRunState) -> CreativeRunState:
    """keyframes -> clips -> narration -> subtitles -> edit. Each stage
    re-checks storyboard_reviewed independently — see _require_review."""
    for fn in (run_keyframes, run_clips, run_narration, run_subtitles, run_edit):
        state = fn(run_dir, state)
        if state.stages[fn.__name__.removeprefix("run_")]["status"] != "done":
            return state
    return state


if __name__ == "__main__":
    import argparse

    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    parser = argparse.ArgumentParser(description="Run the AI Creation pipeline end-to-end (CLI/testing use)")
    parser.add_argument("prompt")
    parser.add_argument("--runs-root", type=Path, default=Path(__file__).resolve().parent.parent / "runs")
    parser.add_argument("--duration", type=float, default=15.0)
    parser.add_argument("--style", default="cinematic sci-fi")
    parser.add_argument("--aspect", default="9:16")
    parser.add_argument("--language", default="en")
    parser.add_argument("--model", default=_default_ollama_model())
    parser.add_argument("--bgm", type=Path, default=None)
    parser.add_argument("--auto-approve", action="store_true")
    args = parser.parse_args()

    st = new_run(args.runs_root, args.prompt, args.duration, args.style, args.aspect, args.language, args.model, args.bgm)
    rd = run_dir_for(args.runs_root, st.run_id)
    st = run_to_storyboard(rd, st)
    print(json.dumps(st.stages, indent=2))

    if args.auto_approve and _stage_ok(st, "storyboard"):
        st = approve_storyboard(rd, st)
        st = run_after_review(rd, st)
        print(json.dumps(st.stages, indent=2))
