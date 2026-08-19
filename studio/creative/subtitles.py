"""Stage 6: narration timing + script text -> .ass subtitle file.

Reuses a proven ASS style block and time-formatting approach (Microsoft
YaHei, 52pt, white text with black outline, bottom-center) from an earlier
private prototype — only the generation logic is new: that prototype
hardcoded its dialogue text and timestamps by hand, this computes both
from actual per-scene narration duration.
"""
from __future__ import annotations

from pathlib import Path

# Same style VALUES as an earlier private prototype (Microsoft YaHei,
# white/black outline, bottom-center) — but with two real bugs fixed.
# First: that prototype split "Style:" and its CSV values across two
# lines, which isn't
# valid ASS syntax; libass silently ignores a malformed Style line and falls
# back to Arial, discovered by actually burning a test subtitle in and
# inspecting the frame. Also added
# PlayResX/PlayResY, which the legacy header omitted, so libass scales
# correctly onto whatever resolution the video actually is instead of
# guessing. Second (2026-08-19 V0.2): the legacy 52pt size was tuned for
# 1920x1080 landscape; at this pipeline's 448x768 portrait resolution it
# wrapped to 4-5 lines and covered roughly a third to half of the frame
# (flagged by independent review) — reduced to 34pt, still comfortably
# legible on a portrait clip this size, without redesigning the style.
_ASS_HEADER = """[Script Info]
Title: OpenVideoStudio AI Creation
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BorderStyle, Outline, Shadow, Alignment, MarginV
Style: Default,Microsoft YaHei,34,&H00FFFFFF,&H00000000,1,2,1,2,40

[Events]
Format: Layer, Start, End, Style, Text
"""


def ass_time(seconds: float) -> str:
    """Same shape as an earlier private prototype's ass_time(), taking a
    float seconds value (programmatically computed) instead of a
    hand-typed "HH:MM:SS" string."""
    cs = int(round(seconds * 100))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def generate_subtitles(storyboard: dict, out_path: Path, width: int = 448, height: int = 768) -> Path:
    lines = [_ASS_HEADER.format(width=width, height=height)]
    cursor = 0.0

    for scene in storyboard["scenes"]:
        # clip_actual_duration (the real, ffprobe-measured clip length) is what
        # the final edit actually times the timeline to — LTX's frame-count
        # rounding means it can differ from narration_duration/duration_seconds,
        # and using the wrong one drifts every later cue's start/end.
        duration = scene.get("clip_actual_duration") or scene.get("narration_duration") or scene.get("duration_seconds", 4.0)
        # subtitle_text (V0.2 storyboard field) lets the LLM show a condensed
        # on-screen line distinct from the spoken narration_text; falls back
        # to narration_text for older storyboards that don't set it.
        text = (scene.get("subtitle_text") or scene.get("narration_text") or "").replace("\n", "\\N")
        if text:
            start, end = ass_time(cursor), ass_time(cursor + duration)
            lines.append(f"Dialogue: 0,{start},{end},Default,{text}")
        cursor += duration

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate an .ass subtitle file from a storyboard JSON file")
    parser.add_argument("storyboard_json", type=Path)
    parser.add_argument("--out", type=Path, default=Path("subtitles_test.ass"))
    args = parser.parse_args()

    storyboard = json.loads(args.storyboard_json.read_text(encoding="utf-8"))
    out = generate_subtitles(storyboard, args.out)
    print(f"Wrote {out}")
