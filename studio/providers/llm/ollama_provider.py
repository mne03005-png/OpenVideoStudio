"""LLMProvider backed by a local Ollama server. Free, no API key — the
default V0.1 provider so the first runnable version of OpenVideoStudio
doesn't require anyone to pay for anything.

callers are expected to pass model= explicitly, read from config.toml's
ollama_model (see creative/pipeline.py's _default_ollama_model() and
providers/_config_utils.py) — swapping qwen3:8b for a different local
model is meant to be a config change, not a code change in creative/*.py.
This class's own constructor default is only a low-level fallback for a
caller that doesn't supply one, the same way any class's default
argument is a fallback, not a claim that the value is never a literal
anywhere.

keep_alive=0 tells Ollama to unload the model immediately after each
response, which is the mechanism behind "release LLM resources where
possible" on this 6GB card before ComfyUI's SDXL/LTX stages need the VRAM.
"""
from __future__ import annotations

from typing import Optional

import requests


class OllamaProvider:
    def __init__(self, model: str = "qwen3:8b", server: str = "http://127.0.0.1:11434"):
        self.model = model
        self.server = server.rstrip("/")

    def is_available(self, timeout: float = 5.0) -> bool:
        try:
            r = requests.get(f"{self.server}/api/tags", timeout=timeout)
            return r.status_code == 200
        except requests.RequestException:
            return False

    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 2000, think: bool = False) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": think,  # qwen3 is a hybrid-thinking model; off by default so
                              # structured-output callers (script/storyboard) get
                              # clean JSON instead of a <think> reasoning trace first
            "keep_alive": 0,  # unload immediately after this call — see module docstring
            "options": {"num_predict": max_tokens},
        }
        # Fixed 180s was tuned against the original 3-scene/5-field storyboard
        # schema; the V0.2 schema (14 fields/scene, 6-12 scenes) generates far
        # more tokens and genuinely timed out at 180s on real hardware. Scale
        # with max_tokens instead of guessing a new fixed number — this is a
        # local generation with no per-second cost, so generous headroom is
        # free; a 600s floor covers the smallest calls comfortably too.
        timeout = max(600, max_tokens * 0.3)
        r = requests.post(f"{self.server}/api/chat", json=body, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return data["message"]["content"]

    def unload(self) -> None:
        """Explicit unload, for callers that want to force it outside a
        generate() call (e.g. right before starting ComfyUI generation)."""
        try:
            requests.post(
                f"{self.server}/api/generate",
                json={"model": self.model, "prompt": "", "keep_alive": 0},
                timeout=15,
            )
        except requests.RequestException:
            pass


if __name__ == "__main__":
    import argparse

    from providers._config_utils import default_ollama_model, default_ollama_server

    parser = argparse.ArgumentParser(description="Send one prompt to the local Ollama model")
    parser.add_argument("prompt")
    parser.add_argument("--model", default=default_ollama_model())
    parser.add_argument("--server", default=default_ollama_server())
    parser.add_argument("--system", default=None)
    args = parser.parse_args()

    provider = OllamaProvider(model=args.model, server=args.server)
    if not provider.is_available():
        raise SystemExit(f"Ollama is not reachable at {provider.server} — is it installed and running?")
    print(provider.generate(args.prompt, args.system))
