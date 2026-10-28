"""Doctor tests, round 2 (review of PR #52):

- run_doctor still reports unreachable providers gracefully, never raises;
- collect_checks follows the configured provider selection instead of
  hardcoding names: non-default registered providers are selected, unknown
  configured names and construction failures become failures, Ollama
  model/server are forwarded from config;
- main() exit codes and --timeout forwarding behave as documented."""

import pytest

from providers import doctor
from providers.doctor import Check, run_doctor


class FakeUp:
    def __init__(self, result):
        self.result = result

    def is_available(self, timeout: float = 5.0) -> bool:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class FakeProvider:
    """Stands in for a registry-constructed provider; the doctor probes it
    directly when it exposes is_available, else via its client."""

    def __init__(self, available=True, with_client=False):
        self._available = available
        if with_client:
            self.client = FakeUp(available)

    def is_available(self, timeout: float = 5.0) -> bool:
        return self._available


def fake_factory():
    """A registry.get_provider stand-in: records calls, returns providers
    keyed by (kind, name), raises ValueError for unknown names — the same
    contract as providers.registry.get_provider."""
    calls = []
    providers = {}

    def factory(kind, name, **kwargs):
        calls.append((kind, name, kwargs))
        if (kind, name) not in providers:
            raise ValueError(f"Unknown {kind} provider '{name}'. Available: []")
        return providers[(kind, name)]

    factory.calls = calls
    factory.provide = lambda kind, name, provider: providers.__setitem__((kind, name), provider)
    return factory


# ─── run_doctor (unchanged contract) ─────────────────────────────────────


def test_all_reachable_returns_true():
    assert run_doctor([Check("llm", "fake", FakeUp(True))]) is True


def test_unreachable_is_reported_not_raised(capsys):
    assert run_doctor([Check("llm", "fake", FakeUp(False))]) is False
    assert "[down ] llm/fake" in capsys.readouterr().out


def test_raising_provider_is_reported_gracefully(capsys):
    assert run_doctor([Check("llm", "fake", FakeUp(RuntimeError("boom")))]) is False
    assert "boom" in capsys.readouterr().out


def test_missing_health_check_is_skipped_and_does_not_fail(capsys):
    assert run_doctor([Check("tts", "edge_tts", None)]) is True
    assert "[skip ] tts/edge_tts" in capsys.readouterr().out


# ─── configured selection (review round 2) ───────────────────────────────


def test_non_default_registered_provider_is_selected():
    factory = fake_factory()
    factory.provide("image", "instantid_sdxl", FakeProvider(True, with_client=True))
    checks = doctor.collect_checks({"providers": {"image": "instantid_sdxl"}}, factory=factory)
    image = next(c for c in checks if c.kind == "image")
    assert image.name == "instantid_sdxl"
    assert image.error is None
    assert image.probe is not None and hasattr(image.probe, "is_available")


def test_unknown_configured_name_is_a_failure():
    checks = doctor.collect_checks({"providers": {"tts": "does_not_exist"}}, factory=fake_factory())
    tts = next(c for c in checks if c.kind == "tts")
    assert tts.error is not None
    assert run_doctor(checks) is False
    # and the unknown name is not silently replaced by the default
    assert tts.name == "does_not_exist"


def test_ollama_model_and_server_are_forwarded():
    factory = fake_factory()
    factory.provide("llm", "ollama", FakeProvider(True))
    config = {"providers": {
        "llm": "ollama",
        "ollama_model": "custom-model",
        "ollama_server": "http://10.1.2.3:11434",
    }}
    doctor.collect_checks(config, factory=factory)
    kind, name, kwargs = factory.calls[0]
    assert (kind, name) == ("llm", "ollama")
    assert kwargs["model"] == "custom-model"
    assert kwargs["server"] == "http://10.1.2.3:11434"


def test_probe_lives_on_the_client_for_comfyui_families():
    factory = fake_factory()
    factory.provide("image", "comfyui_sdxl", FakeProvider(True, with_client=True))
    checks = doctor.collect_checks({"providers": {"image": "comfyui_sdxl"}}, factory=factory)
    image = next(c for c in checks if c.kind == "image")
    # ComfyUISDXLProvider carries is_available on its ComfyClient
    assert image.probe is not None and hasattr(image.probe, "is_available")


def test_all_four_kinds_are_covered():
    checks = doctor.collect_checks({}, factory=fake_factory())
    assert sorted(c.kind for c in checks) == ["image", "llm", "tts", "video"]


# ─── main() exit codes and --timeout forwarding ──────────────────────────


def test_main_exits_zero_when_everything_is_up(monkeypatch):
    monkeypatch.setattr(doctor, "collect_checks", lambda: [Check("llm", "fake", FakeUp(True))])
    monkeypatch.setattr(__import__("sys"), "argv", ["doctor"])
    assert doctor.main() == 0


def test_main_exits_one_when_a_provider_is_down(monkeypatch):
    monkeypatch.setattr(doctor, "collect_checks", lambda: [Check("llm", "fake", FakeUp(False))])
    monkeypatch.setattr(__import__("sys"), "argv", ["doctor"])
    assert doctor.main() == 1


def test_main_exits_one_on_construction_failure(monkeypatch):
    monkeypatch.setattr(doctor, "collect_checks", lambda: [Check("tts", "does_not_exist", error="ValueError: unknown")])
    monkeypatch.setattr(__import__("sys"), "argv", ["doctor"])
    assert doctor.main() == 1


def test_timeout_is_forwarded_to_the_probe(monkeypatch):
    seen = {}

    class Spy:
        def is_available(self, timeout: float = 5.0) -> bool:
            seen["timeout"] = timeout
            return True

    monkeypatch.setattr(doctor, "collect_checks", lambda: [Check("llm", "fake", Spy())])
    monkeypatch.setattr(__import__("sys"), "argv", ["doctor", "--timeout", "1.5"])
    doctor.main()
    assert seen["timeout"] == 1.5
