"""Tiny shared helper for standalone CLI entrypoints (creative/*.py's
`__main__` blocks, providers/llm/ollama_provider.py's) that need the
configured Ollama model as their argparse default. config.toml's own
[providers] comment says the model name is "configurable here on
purpose — never hardcode it" — one shared reader instead of each CLI
block duplicating (and risking drifting from) its own copy of the same
few lines."""
from __future__ import annotations

import tomllib
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.toml"
_FALLBACK_MODEL = "qwen3:8b"
_FALLBACK_SERVER = "http://127.0.0.1:11434"


def default_ollama_model() -> str:
    try:
        data = tomllib.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _FALLBACK_MODEL
    return data.get("providers", {}).get("ollama_model", _FALLBACK_MODEL)


def default_ollama_server() -> str:
    try:
        data = tomllib.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _FALLBACK_SERVER
    return data.get("providers", {}).get("ollama_server", _FALLBACK_SERVER)
