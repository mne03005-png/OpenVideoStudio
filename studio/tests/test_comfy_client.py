"""Tests for ComfyUI path handling that do not require live services."""
from __future__ import annotations

from pathlib import Path

import pytest

from providers._comfy_client import ComfyClient


def _forward_separators(path: Path) -> str:
    return path.as_posix()


def _backslash_separators(path: Path) -> str:
    return path.as_posix().replace("/", "\\")


def _mixed_separators(path: Path) -> str:
    separator_index = 0
    mixed_path = []
    for character in path.as_posix():
        if character == "/":
            mixed_path.append("\\" if separator_index % 2 == 0 else "/")
            separator_index += 1
        else:
            mixed_path.append(character)
    value = "".join(mixed_path)
    assert "/" in value and "\\" in value
    return value


def _forward_trailing_separator(path: Path) -> str:
    return f"{path.as_posix()}/"


def _backslash_trailing_separator(path: Path) -> str:
    return f"{_backslash_separators(path)}\\"


@pytest.mark.parametrize(
    "format_root",
    [
        _forward_separators,
        _backslash_separators,
        _mixed_separators,
        _forward_trailing_separator,
        _backslash_trailing_separator,
    ],
    ids=[
        "forward-slashes",
        "backslashes",
        "mixed-separators",
        "forward-trailing-separator",
        "backslash-trailing-separator",
    ],
)
def test_comfy_root_env_resolves_input_and_output(
    tmp_path, monkeypatch, format_root
):
    root = tmp_path / "ComfyUI"
    source = tmp_path / "keyframe.png"
    source.write_bytes(b"image")
    monkeypatch.setenv("COMFYUI_ROOT", format_root(root))
    client = ComfyClient()

    name = client.upload_input_image(source, dest_name="keyframe.png")
    output_path = client.output_path(
        {
            "outputs": {
                "save": {
                    "images": [
                        {"filename": "frame.png", "subfolder": "nested"}
                    ]
                }
            }
        },
        "save",
    )

    assert client.comfy_root == root
    assert name == "keyframe.png"
    assert (root / "input" / name).read_bytes() == b"image"
    assert output_path == root / "output" / "nested" / "frame.png"


def test_explicit_path_preserves_literal_backslashes(monkeypatch):
    explicit_root = Path("literal\\backslash")
    monkeypatch.setenv("COMFYUI_ROOT", "ignored/environment/root")

    client = ComfyClient(comfy_root=explicit_root)

    assert client.comfy_root == explicit_root
