"""Provider registry — the one file that knows about concrete provider
classes. creative/*.py only ever calls get_provider(); nothing else imports
a concrete provider directly. Adding a new provider means writing one file
matching the interface in providers/base.py and adding one line here.
"""
from __future__ import annotations

from providers.llm.ollama_provider import OllamaProvider
from providers.image.comfyui_sdxl import ComfyUISDXLProvider
from providers.video.comfyui_ltx import ComfyUILTXProvider
from providers.tts.edge_tts_provider import EdgeTTSProvider

PROVIDERS = {
    "llm": {
        "ollama": OllamaProvider,
        # Future: "deepseek": DeepSeekProvider, "claude": ClaudeProvider,
        # "openai": OpenAIProvider, "gemini": GeminiProvider, "grok": GrokProvider
    },
    "image": {
        "comfyui_sdxl": ComfyUISDXLProvider,
    },
    "video": {
        "comfyui_ltx": ComfyUILTXProvider,
    },
    "tts": {
        "edge_tts": EdgeTTSProvider,
    },
}


def get_provider(kind: str, name: str, **kwargs):
    try:
        cls = PROVIDERS[kind][name]
    except KeyError:
        available = list(PROVIDERS.get(kind, {}).keys())
        raise ValueError(f"Unknown {kind} provider '{name}'. Available: {available}")
    return cls(**kwargs)
