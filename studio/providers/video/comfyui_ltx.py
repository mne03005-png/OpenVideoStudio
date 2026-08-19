"""VideoProvider backed by ComfyUI + LTX-Video.

The graph below is a proven, tuned node wiring — same checkpoint, same T5
text encoder, same LTXVPreprocess/LTXVConditioning/LTXVImgToVideo wiring,
same ManualSigmas schedule and euler_ancestral sampler. Not retuned.

Image-to-video only in this provider — image_path is required here and
will raise if missing, but the VideoProvider interface itself keeps it
optional so a future text-to-video provider (e.g. Kling) can implement the
same interface without this constraint.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from providers._comfy_client import ComfyClient

_LTXV_SIGMAS = "1.0000, 0.9937, 0.9875, 0.9812, 0.9750, 0.9094, 0.7250, 0.4219, 0.0"


class ComfyUILTXProvider:
    checkpoint = "ltxv-2b-0.9.8-distilled-fp8.safetensors"
    clip_name = "t5xxl_fp8_e4m3fn.safetensors"
    fps = 24.0

    def __init__(self, client: Optional[ComfyClient] = None):
        self.client = client or ComfyClient()

    def generate_video(
        self, prompt: str, duration_seconds: float, width: int = 448, height: int = 768,
        image_path: Optional[Path] = None, seed: Optional[int] = None,
        negative_prompt: str = "",
    ) -> Path:
        if image_path is None:
            raise ValueError("ComfyUILTXProvider is image-to-video only — image_path is required")

        seed = seed if seed is not None else 0
        frames = max(int(round(duration_seconds * self.fps)), 9)
        input_name = self.client.upload_input_image(image_path)
        prefix = "OpenVideoStudio/clip"

        graph = {
            "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": self.checkpoint}},
            "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": self.clip_name, "type": "ltxv", "device": "default"}},
            "3": {"class_type": "LoadImage", "inputs": {"image": input_name}},
            "4": {"class_type": "LTXVPreprocess", "inputs": {"image": ["3", 0], "img_compression": 38}},
            "17": {"class_type": "RepeatImageBatch", "inputs": {"image": ["4", 0], "amount": 9}},
            "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": negative_prompt}},
            "7": {"class_type": "LTXVConditioning", "inputs": {"positive": ["5", 0], "negative": ["6", 0], "frame_rate": 24}},
            "8": {
                "class_type": "LTXVImgToVideo",
                "inputs": {
                    "positive": ["7", 0], "negative": ["7", 1], "vae": ["1", 2], "image": ["17", 0],
                    "width": width, "height": height, "length": frames, "batch_size": 1, "strength": 1.0,
                },
            },
            "9": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
            "10": {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": ["8", 0], "negative": ["8", 1], "cfg": 1.0}},
            "11": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler_ancestral"}},
            "12": {"class_type": "ManualSigmas", "inputs": {"sigmas": _LTXV_SIGMAS}},
            "13": {
                "class_type": "SamplerCustomAdvanced",
                "inputs": {"noise": ["9", 0], "guider": ["10", 0], "sampler": ["11", 0], "sigmas": ["12", 0], "latent_image": ["8", 2]},
            },
            "14": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 1], "vae": ["1", 2]}},
            "15": {"class_type": "CreateVideo", "inputs": {"images": ["14", 0], "fps": self.fps, "bit_depth": 8}},
            "16": {"class_type": "SaveVideo", "inputs": {"video": ["15", 0], "filename_prefix": prefix, "format": "mp4", "codec": "h264"}},
        }

        if not self.client.is_available():
            raise RuntimeError("ComfyUI is not reachable at " + self.client.server)

        prompt_id = self.client.submit(graph, client_id_prefix="ovs-video")
        entry = self.client.wait_for_result(prompt_id, timeout_minutes=20.0)
        # ComfyUI's SaveVideo node reports its output under "images" (with an
        # "animated": true flag), same key SaveImage uses — not "videos".
        return self.client.output_path(entry, node_id="16", media_key="images")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate one test clip via ComfyUI/LTX from a keyframe image")
    parser.add_argument("image", type=Path)
    parser.add_argument("prompt")
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--width", type=int, default=448)
    parser.add_argument("--height", type=int, default=768)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    provider = ComfyUILTXProvider()
    path = provider.generate_video(args.prompt, args.duration, args.width, args.height, args.image, args.seed)
    print(f"Generated: {path}")
