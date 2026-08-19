"""ImageProvider backed by ComfyUI + SDXL Lightning.

The graph below is a proven, tuned node wiring (checkpoint, sampler,
scheduler, steps, cfg) — only touch these parameters if a real test proves
it's necessary.

Also supports an OPTIONAL img2img path (reference_image_path). This is
deliberately scoped to what's available with zero new downloads: no
IPAdapter/InstantID/PuLID/ReActor node packages or ControlNet models are
assumed to be installed. img2img (LoadImage + VAEEncode feeding KSampler
instead of an empty latent, denoise < 1.0) is real reference-image
conditioning, just not identity-specialized. True face-identity
preservation would need IPAdapter-FaceID/InstantID/PuLID — new node
packages plus new model downloads, intentionally left as a community
extension track (see creative/identity.py's module docstring and
docs/COMMUNITY_TRACKS.md, Track C).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from providers._comfy_client import ComfyClient


class ComfyUISDXLProvider:
    checkpoint = "RealVisXL_V5.0_Lightning_fp16.safetensors"

    def __init__(self, client: Optional[ComfyClient] = None):
        self.client = client or ComfyClient()

    def generate_image(
        self, prompt: str, negative_prompt: str, width: int, height: int, seed: Optional[int] = None,
        reference_image_path: Optional[Path] = None, denoise: float = 1.0,
    ) -> Path:
        seed = seed if seed is not None else 0
        prefix = f"OpenVideoStudio/keyframe"

        graph = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": self.checkpoint}},
            "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": prompt}},
            "3": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": negative_prompt}},
        }

        if reference_image_path is not None:
            # img2img: encode the reference image as the starting latent
            # instead of empty noise. Lightning's proven txt2img path
            # (steps=5, cfg=1.5) is untouched — this branch uses more steps
            # so a <1.0 denoise still leaves a reasonable number of
            # effective sampling steps for a distilled/few-step checkpoint.
            input_name = self.client.upload_input_image(reference_image_path)
            graph["8"] = {"class_type": "LoadImage", "inputs": {"image": input_name}}
            graph["9"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["8", 0], "vae": ["1", 2]}}
            latent_source = ["9", 0]
            steps = 10
            sample_denoise = denoise
        else:
            graph["4"] = {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}}
            latent_source = ["4", 0]
            steps = 5
            sample_denoise = 1.0

        graph["5"] = {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": latent_source,
                "seed": seed, "steps": steps, "cfg": 1.5,
                "sampler_name": "dpmpp_sde", "scheduler": "karras", "denoise": sample_denoise,
            },
        }
        graph["6"] = {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}}
        graph["7"] = {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": prefix}}

        if not self.client.is_available():
            raise RuntimeError("ComfyUI is not reachable at " + self.client.server)

        prompt_id = self.client.submit(graph, client_id_prefix="ovs-image")
        entry = self.client.wait_for_result(prompt_id, timeout_minutes=6.0)
        return self.client.output_path(entry, node_id="7", media_key="images")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate one test image via ComfyUI/SDXL")
    parser.add_argument("prompt")
    parser.add_argument("--negative", default="blurry, low quality, watermark, text")
    parser.add_argument("--width", type=int, default=448)
    parser.add_argument("--height", type=int, default=768)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    provider = ComfyUISDXLProvider()
    path = provider.generate_image(args.prompt, args.negative, args.width, args.height, args.seed)
    print(f"Generated: {path}")
