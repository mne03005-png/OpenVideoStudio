"""Tests for the V0.2 fixes: duration-from-narration, storyboard schema
validation, LTX freeze/motion QC, prompt-based continuity, and subtitle
sizing. Each covers a specific issue found during real acceptance testing,
not speculative coverage.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from creative.validation import validate_storyboard
from creative.storyboard import generate_storyboard, _WORDS_PER_SECOND
from creative.keyframes import _composed_image_prompt, _composed_negative_prompt, generate_keyframes
from creative.clips import _detect_freeze_seconds, generate_clips
from creative.subtitles import generate_subtitles
from providers.llm.ollama_provider import OllamaProvider


# ------------------------------------------------------- Ollama timeout ---
def test_ollama_generate_timeout_scales_with_max_tokens(monkeypatch):
    """Bug: the HTTP request timeout was a fixed 180s, tuned against the
    original 3-scene/5-field storyboard schema. The V0.2 schema (14
    fields/scene, up to 6-12 scenes) generates far more tokens and genuinely
    timed out at 180s during the real 30-second acceptance run. Timeout must
    scale with max_tokens, not stay fixed."""
    captured = {}

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "ok"}}

    def _post(url, json=None, timeout=None):
        captured["timeout"] = timeout
        return _Resp()

    monkeypatch.setattr("requests.post", _post)
    provider = OllamaProvider()

    provider.generate("prompt", max_tokens=4000)
    assert captured["timeout"] >= 1000  # well above the old fixed 180s

    provider.generate("prompt", max_tokens=500)
    assert captured["timeout"] >= 600  # floor still generous for small calls


# ------------------------------------------------------------- validation ---
def _valid_scene(n=1, **overrides):
    scene = {
        "scene_number": n,
        "image_prompt": "a desert at sunset",
        "negative_prompt": "blurry",
        "video_motion_prompt": "slow pan",
        "video_negative_prompt": "jitter",
        "narration_text": "hello",
    }
    scene.update(overrides)
    return scene


def test_validate_storyboard_accepts_valid():
    validate_storyboard({"scenes": [_valid_scene(1)]}, 1)  # must not raise


def test_validate_storyboard_rejects_wrong_scene_count():
    with pytest.raises(ValueError, match="scene count"):
        validate_storyboard({"scenes": [_valid_scene(1)]}, 2)


def test_validate_storyboard_rejects_missing_required_field():
    scene = _valid_scene(1)
    del scene["narration_text"]
    with pytest.raises(ValueError, match="narration_text"):
        validate_storyboard({"scenes": [scene]}, 1)


def test_validate_storyboard_rejects_duplicate_scene_number():
    with pytest.raises(ValueError, match="duplicate"):
        validate_storyboard({"scenes": [_valid_scene(1), _valid_scene(1)]}, 2)


def test_validate_storyboard_rejects_non_numeric_duration():
    with pytest.raises(ValueError, match="duration_seconds"):
        validate_storyboard({"scenes": [_valid_scene(1, duration_seconds="four")]}, 1)


def test_validate_storyboard_rejects_wrong_scene_numbers():
    with pytest.raises(ValueError, match="scene_number"):
        validate_storyboard({"scenes": [_valid_scene(1), _valid_scene(3)]}, 2)


def test_validate_storyboard_rejects_string_allow_generated_text():
    """bool("false") is True in Python — a naive downstream bool(...)
    coercion would silently invert this flag and disable anti-text negative-
    prompt suppression with no error. Must be rejected here, as a real type
    error, not silently coerced later."""
    with pytest.raises(ValueError, match="allow_generated_text"):
        validate_storyboard({"scenes": [_valid_scene(1, allow_generated_text="false")]}, 1)


def test_validate_storyboard_accepts_real_boolean_allow_generated_text():
    validate_storyboard({"scenes": [_valid_scene(1, allow_generated_text=True)]}, 1)  # must not raise


# -------------------------------------------------- duration from narration ---
_FAKE_IDENTITIES_RESPONSE = json.dumps({
    "has_recurring_character": True,
    "character_identity": {"character_id": "char_1", "name_or_role": "a traveler"},
    "environment_identity": {"location_id": "loc_1", "color_palette": "warm sand tones"},
})


class _FakeLLM:
    """generate_storyboard() now makes two calls: generate_identities() first
    (creative/identity.py), then its own storyboard call — this fake returns
    the identities shape on the first call and the caller-supplied storyboard
    shape on every call after, matching that real call order."""

    def __init__(self, response: str):
        self.response = response
        self.calls = 0

    def generate(self, prompt, system=None, max_tokens=2000):
        self.calls += 1
        if self.calls == 1:
            return _FAKE_IDENTITIES_RESPONSE
        return self.response


def test_storyboard_duration_computed_from_narration_not_llm_guess():
    """Bug: the LLM's own duration_seconds guess routinely didn't match the
    narration_text length it wrote in the same response (both overnight
    acceptance runs had every scene land on the same 4.5s regardless of
    actual narration length) — this caused every scene to overshoot once
    real (longer) narration forced a retime in the edit stage. Duration must
    now be derived from narration_text's word count, ignoring whatever
    number the LLM proposed."""
    narration = " ".join(["word"] * 14)  # 14 words -> ~14/2.8 + 0.3 = 5.3s
    response = json.dumps({
        "scenes": [{
            "scene_number": 1,
            "image_prompt": "x", "negative_prompt": "y",
            "video_motion_prompt": "z", "video_negative_prompt": "w",
            "narration_text": narration,
            "duration_seconds": 999.0,  # deliberately wrong — must be ignored
        }],
    })
    llm = _FakeLLM(response)
    script = {"title": "t", "theme": "th", "scenes": [{"scene_number": 1, "description": "d"}]}
    storyboard = generate_storyboard(llm, script, "en")
    expected = 14 / _WORDS_PER_SECOND + 0.3
    assert abs(storyboard["scenes"][0]["duration_seconds"] - expected) < 0.01


def test_storyboard_duration_clamped_to_max():
    narration = " ".join(["word"] * 200)  # way over the 8.0s ceiling
    response = json.dumps({
        "scenes": [{
            "scene_number": 1,
            "image_prompt": "x", "negative_prompt": "y",
            "video_motion_prompt": "z", "video_negative_prompt": "w",
            "narration_text": narration,
        }],
    })
    llm = _FakeLLM(response)
    script = {"title": "t", "theme": "th", "scenes": [{"scene_number": 1, "description": "d"}]}
    storyboard = generate_storyboard(llm, script, "en")
    assert storyboard["scenes"][0]["duration_seconds"] == 8.0


# ------------------------------------------------------- prompt continuity ---
def test_composed_image_prompt_includes_character_and_environment_identity():
    storyboard = {
        "character_identity": {"name_or_role": "a woman", "wardrobe": "a red coat"},
        "environment_identity": {"architecture": "a foggy street"},
    }
    scene = {"image_prompt": "walking through fog"}
    composed = _composed_image_prompt(storyboard, scene)
    assert "a woman" in composed
    assert "wearing a red coat" in composed
    assert "a foggy street" in composed
    assert "walking through fog" in composed


def test_composed_image_prompt_handles_missing_identity_fields():
    storyboard = {}  # no character_identity/environment_identity keys at all
    scene = {"image_prompt": "a mountain"}
    assert _composed_image_prompt(storyboard, scene) == "a mountain"


class _FakeImageProvider:
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        self.prompts = []
        self.negative_prompts = []

    def generate_image(self, prompt, negative_prompt, width, height, seed=None):
        self.prompts.append(prompt)
        self.negative_prompts.append(negative_prompt)
        p = self.work_dir / f"fake_kf_{seed}.png"
        p.write_bytes(b"fake")
        return p


def test_generate_keyframes_uses_composed_prompt(tmp_path):
    storyboard = {
        "character_identity": {"name_or_role": "shared identity phrase"},
        "environment_identity": {},
        "scenes": [{"scene_number": 1, "image_prompt": "scene specific"}],
    }
    provider = _FakeImageProvider(tmp_path)
    generate_keyframes(provider, storyboard, tmp_path / "out")
    assert "shared identity phrase" in provider.prompts[0]
    assert "scene specific" in provider.prompts[0]


def test_generate_keyframes_uses_composed_negative_prompt(tmp_path):
    """Stage-boundary regression test: the prior test only covered
    _composed_negative_prompt in isolation, which
    would keep passing even if generate_keyframes regressed to forwarding
    scene['negative_prompt'] straight to the provider without the shared
    anti-text fragment. This asserts what the provider actually receives."""
    storyboard = {
        "character_identity": None,
        "environment_identity": {},
        "scenes": [{"scene_number": 1, "image_prompt": "x", "negative_prompt": "blurry"}],
    }
    provider = _FakeImageProvider(tmp_path)
    generate_keyframes(provider, storyboard, tmp_path / "out")
    assert "blurry" in provider.negative_prompts[0]
    assert "watermark" in provider.negative_prompts[0]  # ANTI_TEXT_NEGATIVE_PROMPT reached the provider


def test_generate_keyframes_omits_anti_text_when_scene_allows_generated_text(tmp_path):
    storyboard = {
        "character_identity": None,
        "environment_identity": {},
        "scenes": [{
            "scene_number": 1, "image_prompt": "x", "negative_prompt": "blurry",
            "allow_generated_text": True,
        }],
    }
    provider = _FakeImageProvider(tmp_path)
    generate_keyframes(provider, storyboard, tmp_path / "out")
    assert "blurry" in provider.negative_prompts[0]
    assert "watermark" not in provider.negative_prompts[0]


def test_composed_negative_prompt_adds_anti_text_by_default():
    scene = {"negative_prompt": "blurry"}
    negative = _composed_negative_prompt(scene)
    assert "blurry" in negative
    assert "watermark" in negative  # from ANTI_TEXT_NEGATIVE_PROMPT


def test_composed_negative_prompt_omits_anti_text_when_generated_text_allowed():
    scene = {"negative_prompt": "blurry", "allow_generated_text": True}
    negative = _composed_negative_prompt(scene)
    assert "blurry" in negative
    assert "watermark" not in negative


# -------------------------------------------------------- freeze/motion QC ---
def _make_test_clip(path: Path, frozen: bool, seconds: float = 2.0, fps: int = 24):
    """Real ffmpeg-generated clip: frozen=True is a single still color frame
    held for the whole duration; frozen=False has continuously changing
    content (testsrc pattern), so this exercises _detect_freeze_seconds
    against real encoded video, not a mock."""
    if frozen:
        source = "color=c=blue:s=64x64:rate=%d" % fps
    else:
        source = "testsrc=size=64x64:rate=%d" % fps
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"{source}:duration={seconds}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_detect_freeze_seconds_on_real_frozen_clip(tmp_path):
    clip = tmp_path / "frozen.mp4"
    _make_test_clip(clip, frozen=True, seconds=2.0)
    assert _detect_freeze_seconds(clip) > 1.0


def test_detect_freeze_seconds_on_real_moving_clip(tmp_path):
    clip = tmp_path / "moving.mp4"
    _make_test_clip(clip, frozen=False, seconds=2.0)
    assert _detect_freeze_seconds(clip) == 0.0


def _make_motion_then_freeze_clip(path: Path, motion_seconds: float, freeze_seconds: float, fps: int = 24) -> None:
    """Real ffmpeg-encoded clip with genuine motion (testsrc) followed by a
    static tail (color) — reproduces the exact defect class found live on
    the 60-second/12-scene run: scene 8's raw LTX clip had continuous motion
    except for a ~0.958s frozen tail, invisible to a 1.0s-minimum freeze
    check but real. Built via two lavfi sources concatenated with the
    concat demuxer (same technique creative/pipeline.py already uses for
    narration), not a mock."""
    work_dir = path.parent
    motion_part = work_dir / f"{path.stem}_motion.mp4"
    freeze_part = work_dir / f"{path.stem}_freeze.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=size=64x64:rate={fps}:duration={motion_seconds}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(motion_part)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=blue:s=64x64:rate={fps}:duration={freeze_seconds}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(freeze_part)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    concat_file = work_dir / f"{path.stem}_concat.txt"
    concat_file.write_text(
        f"file '{motion_part.resolve().as_posix()}'\nfile '{freeze_part.resolve().as_posix()}'\n", encoding="utf-8",
    )
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def test_detect_freeze_seconds_catches_short_tail_that_old_threshold_missed(tmp_path):
    """The specific regression this protects: scene 8's real tail freeze was
    ~0.958s — long enough to matter once retimed, short enough that the
    former 1.0s-minimum check reported 0.0 and let it through. A clip with
    motion followed by a 0.8s frozen tail (inside the 0.6-1.0s gap) must be
    caught at the current 0.6s threshold and would NOT have been caught at
    the old 1.0s threshold — proving the threshold value itself matters,
    not just that freeze detection works in general."""
    clip = tmp_path / "motion_then_freeze.mp4"
    _make_motion_then_freeze_clip(clip, motion_seconds=1.0, freeze_seconds=0.8)

    caught_at_current_threshold = _detect_freeze_seconds(clip, min_seconds=0.6)
    assert caught_at_current_threshold > 0.0

    missed_at_old_threshold = _detect_freeze_seconds(clip, min_seconds=1.0)
    assert missed_at_old_threshold == 0.0


def test_generate_clips_retries_on_short_tail_freeze(tmp_path):
    """Same defect class as above, exercised through generate_clips end to
    end: a clip with a real-but-short frozen tail must trigger the bounded
    retry, not be silently accepted because the tail alone is under 1.0s."""
    keyframe = tmp_path / "kf.png"
    keyframe.write_bytes(b"fake")
    storyboard = {
        "scenes": [{
            "scene_number": 1, "keyframe_path": str(keyframe), "keyframe_seed": 3,
            "duration_seconds": 1.8, "video_motion_prompt": "pan", "video_negative_prompt": "",
        }]
    }

    class _TailFreezeProvider:
        def __init__(self, tmp_path: Path):
            self.tmp_path = tmp_path
            self.calls = 0

        def generate_video(self, prompt, duration_seconds, width, height, image_path=None, seed=None, negative_prompt=""):
            self.calls += 1
            out = self.tmp_path / f"gen_{self.calls}.mp4"
            if self.calls == 1:
                _make_motion_then_freeze_clip(out, motion_seconds=1.0, freeze_seconds=0.8)
            else:
                _make_test_clip(out, frozen=False, seconds=1.8)  # retry: clean motion throughout
            return out

    provider = _TailFreezeProvider(tmp_path)
    result = generate_clips(provider, storyboard, tmp_path / "out")
    assert provider.calls == 2  # the short tail freeze triggered exactly one retry
    assert result["scenes"][0]["clip_freeze_seconds"] == 0.0


class _RetryVideoProvider:
    """First call returns a frozen clip, second call (the QC retry) returns
    a moving one — proves generate_clips actually retries on freeze and
    keeps the better result."""

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.calls = 0
        self.seeds = []

    def generate_video(self, prompt, duration_seconds, width, height, image_path=None, seed=None, negative_prompt=""):
        self.calls += 1
        self.seeds.append(seed)
        out = self.tmp_path / f"gen_{self.calls}.mp4"
        _make_test_clip(out, frozen=(self.calls == 1), seconds=1.5)
        return out


def test_generate_clips_retries_on_frozen_result(tmp_path):
    keyframe = tmp_path / "kf.png"
    keyframe.write_bytes(b"fake")
    storyboard = {
        "scenes": [{
            "scene_number": 1, "keyframe_path": str(keyframe), "keyframe_seed": 7,
            "duration_seconds": 1.5, "video_motion_prompt": "pan", "video_negative_prompt": "",
        }]
    }
    provider = _RetryVideoProvider(tmp_path)
    result = generate_clips(provider, storyboard, tmp_path / "out")
    assert provider.calls == 2  # first attempt froze, triggered exactly one retry
    assert provider.seeds == [7, 5007]  # retry uses a different seed
    assert result["scenes"][0]["clip_freeze_seconds"] == 0.0  # kept the better (retry) result


# ------------------------------------------------------- subtitle sizing ---
def test_subtitle_font_size_reduced_for_portrait():
    storyboard = {"scenes": [{"scene_number": 1, "narration_text": "x", "duration_seconds": 3.0}]}
    out = generate_subtitles(storyboard, Path("/tmp/subs_v02_test.ass"), 448, 768)
    text = out.read_text(encoding="utf-8")
    style_line = next(l for l in text.splitlines() if l.startswith("Style:"))
    fontsize = int(style_line.split(",")[2])
    assert fontsize < 52  # smaller than the legacy landscape-tuned size
    assert fontsize >= 24  # still legible


def test_subtitle_uses_subtitle_text_field_when_present():
    storyboard = {
        "scenes": [{
            "scene_number": 1, "narration_text": "the full spoken narration is long",
            "subtitle_text": "short caption", "duration_seconds": 3.0,
        }]
    }
    out = generate_subtitles(storyboard, Path("/tmp/subs_v02_test2.ass"), 448, 768)
    text = out.read_text(encoding="utf-8")
    assert "short caption" in text
    assert "the full spoken narration is long" not in text
