"""Regression tests for bugs found during real AI Creation acceptance
testing. Each test protects a specific bug that was actually hit, not
speculative coverage.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import creative.pipeline as pipeline
from creative._json_utils import extract_json
from creative.subtitles import generate_subtitles
from creative.keyframes import generate_keyframes
from creative.clips import generate_clips


# --------------------------------------------------------- provider config ---
def test_provider_name_reads_config_toml(tmp_path, monkeypatch):
    """Bug: run_script/run_storyboard/run_keyframes/run_clips/run_narration
    all hardcoded literal provider names (e.g. get_provider("image",
    "comfyui_sdxl")) instead of reading config.toml's [providers] section,
    even though that section exists specifically to make provider choice a
    config change, not a code change (providers/registry.py's whole
    purpose). _provider_name() must actually consult config.toml."""
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        '[providers]\nimage = "some_future_provider"\n', encoding="utf-8"
    )
    monkeypatch.setattr(pipeline, "_CONFIG_PATH", config_path)
    assert pipeline._provider_name("image", "comfyui_sdxl") == "some_future_provider"


def test_default_ollama_model_reads_config_toml(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text('[providers]\nollama_model = "sentinel-model:1b"\n', encoding="utf-8")
    monkeypatch.setattr(pipeline, "_CONFIG_PATH", config_path)
    assert pipeline._default_ollama_model() == "sentinel-model:1b"


def test_new_run_uses_configured_model_when_llm_model_not_passed(tmp_path, monkeypatch):
    """Bug: new_run()'s own default (not just app.py's UI call site) hardcoded
    the literal "qwen3:8b" as its llm_model default value, and the CLI's
    --model argparse default did too -- so a caller that omitted llm_model
    (the CLI's default path, or any future caller) silently ignored
    config.toml's [providers].ollama_model regardless of what app.py's UI
    path did. This proves new_run() itself now falls back to config, not
    just that a config-reading helper function exists somewhere unused."""
    config_path = tmp_path / "config.toml"
    config_path.write_text('[providers]\nollama_model = "sentinel-model:1b"\n', encoding="utf-8")
    monkeypatch.setattr(pipeline, "_CONFIG_PATH", config_path)

    state = pipeline.new_run(tmp_path / "runs", "a prompt", 15.0, "cinematic")
    assert state.llm_model == "sentinel-model:1b"


def test_new_run_explicit_llm_model_overrides_config(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text('[providers]\nollama_model = "sentinel-model:1b"\n', encoding="utf-8")
    monkeypatch.setattr(pipeline, "_CONFIG_PATH", config_path)

    state = pipeline.new_run(
        tmp_path / "runs", "a prompt", 15.0, "cinematic",
        llm_model="explicit-override:1b",
    )
    assert state.llm_model == "explicit-override:1b"


def test_provider_name_falls_back_to_default_when_unset(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text("[providers]\n", encoding="utf-8")
    monkeypatch.setattr(pipeline, "_CONFIG_PATH", config_path)
    assert pipeline._provider_name("video", "comfyui_ltx") == "comfyui_ltx"


# --------------------------------------------------------------- extract_json ---
def test_extract_json_plain():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced():
    raw = "```json\n{\"a\": 1, \"b\": [1, 2]}\n```"
    assert extract_json(raw) == {"a": 1, "b": [1, 2]}


def test_extract_json_with_prose_wrapper():
    raw = "Sure, here is the JSON:\n{\"a\": 1}\nLet me know if you need anything else."
    assert extract_json(raw) == {"a": 1}


# --------------------------------------------------------------- subtitles ---
def test_subtitle_duration_prefers_clip_actual_duration(tmp_path):
    """Bug: cursor used narration_duration/duration_seconds while the final
    edit times the video off clip_actual_duration (ffprobe), causing every
    later cue to drift. Cursor must now prefer clip_actual_duration."""
    storyboard = {
        "scenes": [
            {
                "scene_number": 1, "narration_text": "first",
                "duration_seconds": 6.0, "narration_duration": 5.0, "clip_actual_duration": 2.0,
            },
            {
                "scene_number": 2, "narration_text": "second",
                "duration_seconds": 6.0, "narration_duration": 5.0, "clip_actual_duration": 3.0,
            },
        ]
    }
    out = generate_subtitles(storyboard, tmp_path / "subs.ass", 448, 768)
    text = out.read_text(encoding="utf-8")
    # scene 2 should start at 2.0s (clip 1's actual duration), not 5.0s or 6.0s
    assert "0:00:02.00,0:00:05.00,Default,second" in text


def test_subtitle_style_is_single_line(tmp_path):
    """Bug: legacy header split 'Style:' and its values across two lines,
    which is invalid ASS syntax and made libass silently fall back to
    Arial. The Style line must stay on one line."""
    storyboard = {"scenes": [{"scene_number": 1, "narration_text": "x", "duration_seconds": 3.0}]}
    out = generate_subtitles(storyboard, tmp_path / "subs.ass", 448, 768)
    lines = out.read_text(encoding="utf-8").splitlines()
    style_lines = [l for l in lines if l.startswith("Style:")]
    assert len(style_lines) == 1
    assert "Microsoft YaHei" in style_lines[0]


# --------------------------------------------------------- resume/checkpoint ---
class _FakeImageProvider:
    def __init__(self, work_dir: Path):
        self.calls = 0
        self.work_dir = work_dir

    def generate_image(self, prompt, negative_prompt, width, height, seed=None):
        self.calls += 1
        p = self.work_dir / f"fake_keyframe_{self.calls}.png"
        p.write_bytes(b"fake")
        return p


class _FakeVideoProvider:
    def __init__(self, work_dir: Path):
        self.calls = 0
        self.last_negative_prompt = None
        self.work_dir = work_dir

    def generate_video(self, prompt, duration_seconds, width, height, image_path=None, seed=None, negative_prompt=""):
        self.calls += 1
        self.last_negative_prompt = negative_prompt
        p = self.work_dir / f"fake_clip_{self.calls}.mp4"
        p.write_bytes(b"fake")
        return p


def test_generate_keyframes_skips_existing_scene(tmp_path):
    """Bug: a failure partway through the scene loop forced full
    regeneration on retry. A scene whose keyframe file already exists must
    be skipped."""
    existing = tmp_path / "existing.png"
    existing.write_bytes(b"already here")
    storyboard = {
        "scenes": [
            {"scene_number": 1, "image_prompt": "a", "keyframe_path": str(existing)},
            {"scene_number": 2, "image_prompt": "b"},
        ]
    }
    provider = _FakeImageProvider(tmp_path)
    result = generate_keyframes(provider, storyboard, tmp_path / "out")
    assert provider.calls == 1  # only scene 2 generated
    assert result["scenes"][0]["keyframe_path"] == str(existing)
    assert result["scenes"][1]["keyframe_path"]


def test_generate_keyframes_calls_checkpoint_per_scene(tmp_path):
    checkpoints = []
    storyboard = {
        "scenes": [
            {"scene_number": 1, "image_prompt": "a"},
            {"scene_number": 2, "image_prompt": "b"},
        ]
    }
    generate_keyframes(_FakeImageProvider(tmp_path), storyboard, tmp_path / "out", checkpoint=lambda sb: checkpoints.append(json.dumps(sb)))
    assert len(checkpoints) == 2  # once per scene, not once at the end


def test_generate_clips_forwards_video_negative_prompt(tmp_path):
    """Bug: video_negative_prompt was generated by the storyboard stage but
    never actually passed to the video provider."""
    keyframe = tmp_path / "kf.png"
    keyframe.write_bytes(b"fake")
    storyboard = {
        "scenes": [
            {
                "scene_number": 1, "keyframe_path": str(keyframe), "duration_seconds": 4.0,
                "video_motion_prompt": "pan left", "video_negative_prompt": "jitter, warping",
            }
        ]
    }
    provider = _FakeVideoProvider(tmp_path)
    generate_clips(provider, storyboard, tmp_path / "out")
    assert provider.last_negative_prompt == "jitter, warping"


def test_generate_clips_skips_existing_scene(tmp_path):
    keyframe = tmp_path / "kf.png"
    keyframe.write_bytes(b"fake")
    existing_clip = tmp_path / "existing.mp4"
    existing_clip.write_bytes(b"already here")
    storyboard = {
        "scenes": [
            {"scene_number": 1, "keyframe_path": str(keyframe), "duration_seconds": 4.0, "clip_path": str(existing_clip)},
        ]
    }
    provider = _FakeVideoProvider(tmp_path)
    generate_clips(provider, storyboard, tmp_path / "out")
    assert provider.calls == 0


# ----------------------------------------------------------- ComfyClient ---
def test_comfy_free_returns_false_on_request_failure(monkeypatch):
    """Bug: free() swallowed every error and callers logged 'called'
    regardless of outcome, hiding a real cleanup failure before the next
    heavy model load."""
    from providers._comfy_client import ComfyClient
    import requests

    client = ComfyClient()

    def _raise(*a, **kw):
        raise requests.RequestException("connection refused")

    monkeypatch.setattr(requests, "post", _raise)
    assert client.free() is False


def test_comfy_free_returns_true_on_200(monkeypatch):
    from providers._comfy_client import ComfyClient

    client = ComfyClient()

    class _Resp:
        status_code = 200

    monkeypatch.setattr("requests.post", lambda *a, **kw: _Resp())
    assert client.free() is True


def test_comfy_cancel_does_not_interrupt_unrelated_running_job(monkeypatch):
    """Bug: cancel() called POST /interrupt unconditionally, which is a
    global stop with no target — if our own timed-out prompt was still only
    queued while a DIFFERENT job was actually running, this would kill that
    unrelated job."""
    from providers._comfy_client import ComfyClient
    import requests

    client = ComfyClient()
    calls = []

    class _QueueResp:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"queue_running": [[0, "some-other-job-id"]], "queue_pending": [[1, "our-job-id"]]}

    def _get(url, timeout=None):
        calls.append(("GET", url))
        return _QueueResp()

    def _post(url, json=None, timeout=None):
        calls.append(("POST", url, json))

        class _R:
            status_code = 200
        return _R()

    monkeypatch.setattr(requests, "get", _get)
    monkeypatch.setattr(requests, "post", _post)

    client.cancel("our-job-id")

    posts = [c for c in calls if c[0] == "POST"]
    assert any(c[1].endswith("/queue") for c in posts)  # dequeued since it was pending
    assert not any(c[1].endswith("/interrupt") for c in posts)  # NOT running, so no interrupt
