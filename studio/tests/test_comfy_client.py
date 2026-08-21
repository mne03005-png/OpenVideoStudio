"""Tests for ComfyUI path handling that do not require live services."""
from __future__ import annotations

import os

from providers._comfy_client import ComfyClient


def test_comfy_root_env_resolves_output_with_trailing_slash(tmp_path, monkeypatch):
    root = tmp_path / "ComfyUI"
    monkeypatch.setenv("COMFYUI_ROOT", f"{root}{os.sep}")
    client = ComfyClient()

    path = client.output_path(
        {"outputs": {"save": {"images": [{"filename": "frame.png", "subfolder": "nested"}]}}},
        "save",
    )

    assert path == root / "output" / "nested" / "frame.png"


def test_comfy_root_env_normalizes_mixed_separators_for_input(tmp_path, monkeypatch):
    root = tmp_path / "ComfyUI"
    source = tmp_path / "keyframe.png"
    source.write_bytes(b"image")
    monkeypatch.setenv("COMFYUI_ROOT", str(root).replace(os.sep, "\\"))
    client = ComfyClient()

    name = client.upload_input_image(source, dest_name="keyframe.png")

    assert name == "keyframe.png"
    assert (root / "input" / name).read_bytes() == b"image"
