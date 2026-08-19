"""Tests for app.py's config-reading helpers.

Bug: generate_storyboard_ui() hardcoded the literal "qwen3:8b" as the
LLM model passed to creative_pipeline.new_run(), even though
config.toml's own [providers] section comment says the model name is
"configurable here on purpose — never hardcode it." Editing
[providers].ollama_model in config.toml had no effect on the actual UI
path. Fixed by reading it via _configured_ollama_model() instead.
"""
from __future__ import annotations

import app


def test_configured_ollama_model_reads_config_toml(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text('[providers]\nollama_model = "sentinel-model:1b"\n', encoding="utf-8")
    monkeypatch.setattr(app, "CONFIG_PATH", config_path)
    assert app._configured_ollama_model() == "sentinel-model:1b"


def test_configured_ollama_model_falls_back_when_unset(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text("[providers]\n", encoding="utf-8")
    monkeypatch.setattr(app, "CONFIG_PATH", config_path)
    assert app._configured_ollama_model() == "qwen3:8b"


def test_generate_storyboard_ui_passes_configured_model_to_new_run(tmp_path, monkeypatch):
    """Stage-boundary test: proves the configured model actually reaches
    new_run(), not just that the helper function works in isolation."""
    config_path = tmp_path / "config.toml"
    config_path.write_text('[providers]\nollama_model = "sentinel-model:1b"\n', encoding="utf-8")
    monkeypatch.setattr(app, "CONFIG_PATH", config_path)

    captured = {}

    def _fake_new_run(runs_root, prompt, duration, style, aspect_ratio, language, llm_model, bgm_path):
        captured["llm_model"] = llm_model
        raise SystemExit("stop after capturing args")

    monkeypatch.setattr(app.creative_pipeline, "new_run", _fake_new_run)

    try:
        app.generate_storyboard_ui("a prompt", 15.0, "9:16", "cinematic", "en", None)
    except SystemExit:
        pass

    assert captured["llm_model"] == "sentinel-model:1b"
