"""TTSProvider backed by Edge TTS — free, no API key, good multilingual
voice coverage. Genuinely new capability for this codebase: the only
prior voice work in this codebase's earlier private prototypes was a
placeholder Windows SAPI setup, flagged as unreliable in that prototype's
own known-issues notes.

edge-tts can emit boundary-timing events via its SSML stream. This
installed version emits SentenceBoundary (not WordBoundary) — confirmed by
inspecting the actual chunk stream rather than assuming — so word_timings
here is populated at sentence granularity, which is what subtitle cueing
actually needs anyway.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import edge_tts

from providers.base import TTSResult

_DEFAULT_VOICES = {
    "en": "en-US-AriaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
}


class EdgeTTSProvider:
    def synthesize(self, text: str, voice: Optional[str] = None, language: str = "en") -> TTSResult:
        voice = voice or _DEFAULT_VOICES.get(language, _DEFAULT_VOICES["en"])
        return asyncio.run(self._synthesize_async(text, voice))

    async def _synthesize_async(self, text: str, voice: str) -> TTSResult:
        import tempfile

        out_path = Path(tempfile.gettempdir()) / f"ovs_tts_{abs(hash(text)) % 10**8}.mp3"
        communicate = edge_tts.Communicate(text, voice)

        word_timings: list[tuple[float, str]] = []
        with open(out_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    word_timings.append((chunk["offset"] / 1e7, chunk["text"]))  # 100ns units -> seconds

        duration = self._probe_duration(out_path)
        return TTSResult(audio_path=out_path, duration_seconds=duration, word_timings=word_timings or None)

    @staticmethod
    def _probe_duration(path: Path) -> float:
        import subprocess

        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        try:
            return float(proc.stdout.strip())
        except ValueError:
            return 0.0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Synthesize one line of narration via Edge TTS")
    parser.add_argument("text")
    parser.add_argument("--language", default="en")
    parser.add_argument("--voice", default=None)
    args = parser.parse_args()

    provider = EdgeTTSProvider()
    result = provider.synthesize(args.text, args.voice, args.language)
    print(f"Audio: {result.audio_path}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    print(f"Word timings: {len(result.word_timings or [])} words")
