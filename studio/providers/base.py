"""Provider interfaces for AI Creation mode.

Deliberately thin (Protocols, not ABCs with shared machinery) — a contributor
adding a new provider only needs to match one of these shapes and register it
in providers/registry.py. Nothing in creative/ or core/ ever imports a
concrete provider class; they only ever talk to these interfaces.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol


class LLMProvider(Protocol):
    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 2000) -> str: ...


class ImageProvider(Protocol):
    def generate_image(
        self, prompt: str, negative_prompt: str, width: int, height: int, seed: Optional[int] = None
    ) -> Path: ...


class VideoProvider(Protocol):
    def generate_video(
        self, prompt: str, duration_seconds: float, width: int, height: int,
        image_path: Optional[Path] = None,  # None = text-to-video, for future providers
        seed: Optional[int] = None, negative_prompt: str = "",
    ) -> Path: ...


@dataclass
class TTSResult:
    audio_path: Path
    duration_seconds: float
    word_timings: Optional[list[tuple[float, str]]] = None  # None if the provider can't supply it


class TTSProvider(Protocol):
    def synthesize(self, text: str, voice: str, language: str) -> TTSResult: ...
