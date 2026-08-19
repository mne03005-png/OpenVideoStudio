"""Tests for the optional img2img branch in providers/image/comfyui_sdxl.py.

This branch was added as available infrastructure but had zero test
coverage, so a regression to its graph wiring (wrong node IDs, wrong
denoise/steps, wrong latent source) would go unnoticed even though the
txt2img path is fully exercised elsewhere via the pipeline."""
from __future__ import annotations

from pathlib import Path

from providers.image.comfyui_sdxl import ComfyUISDXLProvider


class _FakeComfyClient:
    def __init__(self):
        self.submitted_graph = None
        self.uploaded_path = None

    def is_available(self, timeout: float = 5.0) -> bool:
        return True

    def upload_input_image(self, local_path, dest_name=None) -> str:
        self.uploaded_path = local_path
        return "uploaded_ref.png"

    def submit(self, graph: dict, client_id_prefix: str = "openvideostudio") -> str:
        self.submitted_graph = graph
        return "fake-prompt-id"

    def wait_for_result(self, prompt_id: str, timeout_minutes: float = 6.0) -> dict:
        return {"outputs": {"7": {"images": [{"filename": "out.png", "subfolder": ""}]}}}

    def output_path(self, entry: dict, node_id: str, media_key: str = "images") -> Path:
        return Path("fake_output") / entry["outputs"][node_id][media_key][0]["filename"]


def test_generate_image_txt2img_uses_empty_latent_and_five_steps():
    client = _FakeComfyClient()
    provider = ComfyUISDXLProvider(client=client)
    provider.generate_image("a cat", "blurry", 448, 768, seed=1)

    graph = client.submitted_graph
    assert graph["4"]["class_type"] == "EmptyLatentImage"
    assert graph["5"]["inputs"]["latent_image"] == ["4", 0]
    assert graph["5"]["inputs"]["steps"] == 5
    assert graph["5"]["inputs"]["denoise"] == 1.0
    assert "8" not in graph and "9" not in graph
    assert client.uploaded_path is None


def test_generate_image_img2img_uses_loaded_reference_and_requested_denoise():
    client = _FakeComfyClient()
    provider = ComfyUISDXLProvider(client=client)
    ref = Path("some_reference.png")
    provider.generate_image("a cat", "blurry", 448, 768, seed=1, reference_image_path=ref, denoise=0.6)

    graph = client.submitted_graph
    assert client.uploaded_path == ref
    assert graph["8"] == {"class_type": "LoadImage", "inputs": {"image": "uploaded_ref.png"}}
    assert graph["9"]["class_type"] == "VAEEncode"
    assert graph["9"]["inputs"]["pixels"] == ["8", 0]
    assert graph["5"]["inputs"]["latent_image"] == ["9", 0]
    assert graph["5"]["inputs"]["denoise"] == 0.6
    assert graph["5"]["inputs"]["steps"] == 10
    assert "4" not in graph  # no empty-latent node in the img2img branch
