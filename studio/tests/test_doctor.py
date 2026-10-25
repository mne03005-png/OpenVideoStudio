"""Doctor must report unreachable providers gracefully, never raise, and
skip providers without a health check (issue-seeded acceptance criteria)."""

from providers.doctor import run_doctor


class FakeUp:
    def __init__(self, result):
        self.result = result

    def is_available(self, timeout: float = 5.0) -> bool:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_all_reachable_returns_true(capsys):
    assert run_doctor([("llm", "fake", FakeUp(True))]) is True


def test_unreachable_is_reported_not_raised(capsys):
    assert run_doctor([("llm", "fake", FakeUp(False))]) is False
    assert "[down ] llm/fake" in capsys.readouterr().out


def test_raising_provider_is_reported_gracefully(capsys):
    assert run_doctor([("llm", "fake", FakeUp(RuntimeError("boom")))]) is False
    assert "boom" in capsys.readouterr().out


def test_missing_health_check_is_skipped_and_does_not_fail(capsys):
    assert run_doctor([("tts", "edge_tts", None)]) is True
    assert "[skip ] tts/edge_tts" in capsys.readouterr().out
