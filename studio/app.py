"""Gradio V1 interface. Minimal by design — no timeline editor. Plan review
happens through an editable table (enable/reorder/duration/title text),
which is the deliberately low-tech way to satisfy the review requirements
in Step 6 of the spec without building a drag-and-drop UI.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

STUDIO_ROOT = Path(__file__).resolve().parent
load_dotenv(STUDIO_ROOT / ".env")  # must run before any provider is constructed

sys.path.insert(0, str(STUDIO_ROOT / "core"))
import pipeline  # noqa: E402  (Media Remix orchestrator)
import creative.pipeline as creative_pipeline  # noqa: E402  (AI Creation orchestrator)
RUNS_ROOT = STUDIO_ROOT / "runs"
CONFIG_PATH = STUDIO_ROOT / "config.toml"

TABLE_HEADERS = ["shot_id", "type", "enabled", "order", "duration", "title_text", "quality_score"]
TABLE_TYPES = ["str", "str", "bool", "number", "number", "str", "number"]

STORYBOARD_HEADERS = ["scene_number", "image_prompt", "video_motion_prompt", "narration_text", "duration_seconds"]
STORYBOARD_TYPES = ["number", "str", "str", "str", "number"]


def _default_target_duration() -> float:
    try:
        import tomllib
        data = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return float(data.get("output", {}).get("target_duration_seconds", 180))
    except Exception:
        return 180.0


def _configured_ollama_model() -> str:
    """config.toml's own [providers] comment says the model name is
    "configurable here on purpose — never hardcode it" — this reads it
    instead of the UI hardcoding a literal model name."""
    try:
        import tomllib
        data = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return data.get("providers", {}).get("ollama_model", "qwen3:8b")
    except Exception:
        return "qwen3:8b"


def pick_folder() -> str:
    """Native Windows folder picker. Falls back to empty string (leaving the
    manual textbox path usable) if tkinter can't open a dialog in this
    process context."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askdirectory()
        root.destroy()
        return path or ""
    except Exception:
        return ""


def _status_lines(state: pipeline.RunState, stage_names: list[str]) -> str:
    lines = []
    for s in stage_names:
        info = state.stages[s]
        qc = info.get("qc")
        err = info.get("error")
        line = f"{s}: {info['status']}"
        if qc:
            line += f" — {qc}"
        if err:
            line += f" — ERROR: {err.splitlines()[0] if isinstance(err, str) else err}"
        lines.append(line)
    return "\n".join(lines)


def generate_plan(folder_path: str, style: str, target_duration: float, bgm_file):
    if not folder_path or not Path(folder_path).is_dir():
        return None, "Please choose a valid media folder first.", [], gr.update(visible=False)

    bgm_path = Path(bgm_file) if bgm_file else None
    state = pipeline.new_run(RUNS_ROOT, Path(folder_path), style, float(target_duration), bgm_path)
    run_dir = pipeline.run_dir_for(RUNS_ROOT, state.run_id)
    state = pipeline.run_to_plan(run_dir, state)

    status = _status_lines(state, ["scan", "score", "plan"])

    if state.stages["plan"]["status"] != "done":
        return str(run_dir), status, [], gr.update(visible=False)

    plan_path = run_dir / "plan.json"
    plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
    rows = [
        [s["shot_id"], s["type"], s["enabled"], s["order"], s["duration"], s.get("title_text") or "", s["quality_score"]]
        for s in plan_data["shots"]
    ]
    return str(run_dir), status, rows, gr.update(visible=True)


def render_final(run_dir_str: str, table_data):
    if not run_dir_str:
        return "No active run — generate a plan first.", None

    run_dir = Path(run_dir_str)
    state = pipeline.load_run_state(run_dir)

    plan_path = run_dir / "plan.json"
    plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
    shots_by_id = {s["shot_id"]: s for s in plan_data["shots"]}

    rows = table_data.values.tolist() if hasattr(table_data, "values") else table_data
    for row in rows:
        shot_id, _type, enabled, order, duration, title_text, _score = row
        shot = shots_by_id.get(shot_id)
        if not shot:
            continue
        shot["enabled"] = bool(enabled)
        shot["order"] = int(order)
        shot["duration"] = round(float(duration), 2)
        shot["title_text"] = title_text or None

    plan_data["shots"].sort(key=lambda s: s["order"])
    plan_data["total_planned_duration"] = round(sum(s["duration"] for s in plan_data["shots"] if s["enabled"]), 2)
    plan_path.write_text(json.dumps(plan_data, ensure_ascii=False, indent=2), encoding="utf-8")

    state = pipeline.approve_plan(run_dir, state)
    state = pipeline.run_after_review(run_dir, state)

    status = _status_lines(state, ["render", "audio"])
    final_path = run_dir / "final.mp4"
    video = str(final_path) if final_path.exists() else None
    return status, video


def open_output_folder(run_dir_str: str):
    if run_dir_str and Path(run_dir_str).is_dir():
        subprocess.run(["explorer", str(Path(run_dir_str))])
    return None


def _creative_status_lines(state: creative_pipeline.CreativeRunState, stage_names: list[str]) -> str:
    lines = []
    for s in stage_names:
        info = state.stages[s]
        line = f"{s}: {info['status']}"
        if info.get("qc"):
            line += f" — {info['qc']}"
        if info.get("error"):
            err = info["error"]
            line += f" — ERROR: {err.splitlines()[0] if isinstance(err, str) else err}"
        lines.append(line)
    return "\n".join(lines)


def generate_storyboard_ui(prompt: str, duration: float, aspect_ratio: str, style: str, language: str, bgm_file):
    if not prompt or not prompt.strip():
        return None, "Please enter a prompt first.", [], gr.update(visible=False)

    bgm_path = Path(bgm_file) if bgm_file else None
    state = creative_pipeline.new_run(
        RUNS_ROOT, prompt.strip(), float(duration), style, aspect_ratio, language,
        _configured_ollama_model(), bgm_path,
    )
    run_dir = creative_pipeline.run_dir_for(RUNS_ROOT, state.run_id)
    state = creative_pipeline.run_to_storyboard(run_dir, state)

    status = _creative_status_lines(state, ["script", "storyboard"])

    if state.stages["storyboard"]["status"] != "done":
        return str(run_dir), status, [], gr.update(visible=False)

    storyboard = json.loads((run_dir / "storyboard.json").read_text(encoding="utf-8"))
    rows = [
        [s["scene_number"], s["image_prompt"], s.get("video_motion_prompt", ""), s.get("narration_text", ""), s["duration_seconds"]]
        for s in storyboard["scenes"]
    ]
    return str(run_dir), status, rows, gr.update(visible=True)


def approve_and_render_ui(run_dir_str: str, table_data):
    if not run_dir_str:
        return "No active run — generate a storyboard first.", None

    run_dir = Path(run_dir_str)
    state = creative_pipeline.load_run_state(run_dir)

    storyboard = json.loads((run_dir / "storyboard.json").read_text(encoding="utf-8"))
    scenes_by_number = {s["scene_number"]: s for s in storyboard["scenes"]}

    rows = table_data.values.tolist() if hasattr(table_data, "values") else table_data
    for row in rows:
        scene_number, image_prompt, motion_prompt, narration_text, duration_seconds = row
        scene = scenes_by_number.get(int(scene_number))
        if not scene:
            continue
        scene["image_prompt"] = image_prompt
        scene["video_motion_prompt"] = motion_prompt
        scene["narration_text"] = narration_text
        scene["duration_seconds"] = max(3.0, min(6.0, float(duration_seconds)))

    (run_dir / "storyboard.json").write_text(json.dumps(storyboard, ensure_ascii=False, indent=2), encoding="utf-8")

    state = creative_pipeline.approve_storyboard(run_dir, state)
    state = creative_pipeline.run_after_review(run_dir, state)

    status = _creative_status_lines(state, ["keyframes", "clips", "narration", "subtitles", "edit"])
    final_path = run_dir / "final.mp4"
    video = str(final_path) if final_path.exists() else None
    return status, video


with gr.Blocks(title="OpenVideoStudio") as demo:
    gr.Markdown("# OpenVideoStudio\nTwo modes: turn your own photos/videos into a video, or generate one entirely from a prompt.")

    with gr.Tabs():
        with gr.Tab("Media Remix"):
            gr.Markdown("Select a folder → review the plan → render.")
            run_dir_state = gr.State(value=None)

            with gr.Row():
                with gr.Column(scale=1):
                    folder_path = gr.Textbox(label="Media folder", placeholder=r"D:\Photos\Trip2026")
                    browse_btn = gr.Button("Browse (Windows folder picker)...")
                    title = gr.Textbox(label="Title", value="Untitled")
                    style = gr.Dropdown(["Family Memory", "Travel Documentary"], value="Family Memory", label="Style")
                    target_duration = gr.Number(label="Target duration (seconds)", value=_default_target_duration())
                    bgm_file = gr.File(label="BGM (optional)", file_types=["audio"], type="filepath")
                    generate_btn = gr.Button("Generate Plan", variant="primary")
                    status_box = gr.Textbox(label="Status", lines=6, interactive=False)

                with gr.Column(scale=2):
                    plan_table = gr.Dataframe(
                        headers=TABLE_HEADERS,
                        datatype=TABLE_TYPES,
                        label="Plan review — edit enabled / order / duration / title_text, then Continue",
                        interactive=True,
                    )
                    continue_btn = gr.Button("Continue to Render", variant="primary", visible=False)
                    render_status = gr.Textbox(label="Render status", lines=4, interactive=False)
                    output_video = gr.Video(label="Output preview")
                    open_folder_btn = gr.Button("Open Output Folder")

            browse_btn.click(pick_folder, outputs=folder_path)
            generate_btn.click(
                generate_plan,
                inputs=[folder_path, style, target_duration, bgm_file],
                outputs=[run_dir_state, status_box, plan_table, continue_btn],
            )
            continue_btn.click(render_final, inputs=[run_dir_state, plan_table], outputs=[render_status, output_video])
            open_folder_btn.click(open_output_folder, inputs=[run_dir_state])

        with gr.Tab("AI Creation"):
            gr.Markdown(
                "Prompt → local script (Ollama) → storyboard → **review before any GPU generation runs** → "
                "keyframes → clips → narration → subtitles → final video."
            )
            creative_run_dir_state = gr.State(value=None)

            with gr.Row():
                with gr.Column(scale=1):
                    creative_prompt = gr.Textbox(
                        label="Prompt", lines=3,
                        placeholder="An astronaut discovers an abandoned ancient Chinese city on Mars.",
                    )
                    creative_duration = gr.Number(label="Target duration (seconds)", value=15.0)
                    creative_aspect = gr.Dropdown(
                        ["9:16", "16:9", "1:1"], value="9:16", label="Aspect ratio",
                        info="Only 9:16 has been separately validated end-to-end — see docs/HARDWARE.md",
                    )
                    creative_style = gr.Textbox(label="Style", value="cinematic sci-fi")
                    creative_language = gr.Dropdown(["en", "zh"], value="en", label="Language")
                    creative_bgm = gr.File(label="BGM (optional)", file_types=["audio"], type="filepath")
                    creative_generate_btn = gr.Button("Generate Script + Storyboard", variant="primary")
                    creative_status = gr.Textbox(label="Status", lines=6, interactive=False)

                with gr.Column(scale=2):
                    storyboard_table = gr.Dataframe(
                        headers=STORYBOARD_HEADERS,
                        datatype=STORYBOARD_TYPES,
                        label="Storyboard review — edit prompts/narration/duration, then Approve. "
                              "Nothing generates on GPU until you click Approve.",
                        interactive=True,
                    )
                    creative_approve_btn = gr.Button("Approve Storyboard & Generate Video", variant="primary", visible=False)
                    creative_render_status = gr.Textbox(label="Generation status", lines=6, interactive=False)
                    creative_output_video = gr.Video(label="Output preview")
                    creative_open_folder_btn = gr.Button("Open Output Folder")

            creative_generate_btn.click(
                generate_storyboard_ui,
                inputs=[creative_prompt, creative_duration, creative_aspect, creative_style, creative_language, creative_bgm],
                outputs=[creative_run_dir_state, creative_status, storyboard_table, creative_approve_btn],
            )
            creative_approve_btn.click(
                approve_and_render_ui,
                inputs=[creative_run_dir_state, storyboard_table],
                outputs=[creative_render_status, creative_output_video],
            )
            creative_open_folder_btn.click(open_output_folder, inputs=[creative_run_dir_state])


if __name__ == "__main__":
    demo.launch()
