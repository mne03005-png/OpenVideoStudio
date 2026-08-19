"""Stage 5: per-scene narration_text -> speech audio, via TTSProvider."""
from __future__ import annotations

import shutil
from pathlib import Path

from providers.base import TTSProvider


def generate_narration(tts_provider: TTSProvider, storyboard: dict, out_dir: Path, language: str = "en", voice: str = None) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for scene in storyboard["scenes"]:
        n = scene["scene_number"]
        text = scene.get("narration_text", "").strip()
        if not text:
            scene["narration_error"] = "empty_narration_text"
            continue

        result = tts_provider.synthesize(text, voice=voice, language=language)
        dest = out_dir / f"scene_{n:02d}.mp3"
        shutil.copy(result.audio_path, dest)
        scene["narration_path"] = str(dest)
        scene["narration_duration"] = result.duration_seconds
        scene["narration_word_timings"] = result.word_timings

    return storyboard


if __name__ == "__main__":
    import argparse
    import json

    from providers.tts.edge_tts_provider import EdgeTTSProvider

    parser = argparse.ArgumentParser(description="Generate narration for a storyboard JSON file")
    parser.add_argument("storyboard_json", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("narration_test"))
    parser.add_argument("--language", default="en")
    args = parser.parse_args()

    storyboard = json.loads(args.storyboard_json.read_text(encoding="utf-8"))
    provider = EdgeTTSProvider()
    result = generate_narration(provider, storyboard, args.out_dir, args.language)
    for s in result["scenes"]:
        print(s["scene_number"], "->", s.get("narration_path", s.get("narration_error")), s.get("narration_duration"))
