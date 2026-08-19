"""Tests for providers/_config_utils.py, the shared helper standalone CLI
entrypoints use for their --model argparse default.

Bug: creative/pipeline.py's new_run()/CLI and app.py's UI were fixed to
read config.toml's [providers].ollama_model, but creative/script.py,
creative/storyboard.py, and providers/llm/ollama_provider.py's own
__main__ blocks each still hardcoded the literal "qwen3:8b" as their
--model argparse default -- found across two separate rounds of
independent review, one file at a time, because each fix only touched
the specific file flagged rather than searching for every CLI with the
same pattern. This module exists so there's exactly one implementation
to test and reuse, not another one to independently drift.
"""
from __future__ import annotations

from providers import _config_utils


def test_default_ollama_model_reads_config_toml(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text('[providers]\nollama_model = "sentinel-model:1b"\n', encoding="utf-8")
    monkeypatch.setattr(_config_utils, "_CONFIG_PATH", config_path)
    assert _config_utils.default_ollama_model() == "sentinel-model:1b"


def test_default_ollama_model_falls_back_when_unset(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text("[providers]\n", encoding="utf-8")
    monkeypatch.setattr(_config_utils, "_CONFIG_PATH", config_path)
    assert _config_utils.default_ollama_model() == "qwen3:8b"


def test_default_ollama_model_falls_back_when_config_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(_config_utils, "_CONFIG_PATH", tmp_path / "does_not_exist.toml")
    assert _config_utils.default_ollama_model() == "qwen3:8b"
