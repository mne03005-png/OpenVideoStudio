"""Tests for V0.3 Priority 1/3: canonical character/environment identity,
generated once and formatted deterministically for reuse across scenes."""
from __future__ import annotations

import json

import pytest

from creative.identity import (
    generate_identities, format_character_identity, format_environment_identity,
    CHARACTER_IDENTITY_FIELDS, ENVIRONMENT_IDENTITY_FIELDS, ANTI_TEXT_NEGATIVE_PROMPT,
)
from creative.validation import check_narrative_quality


class _FakeLLM:
    def __init__(self, response: str):
        self.response = response
        self.calls = 0

    def generate(self, prompt, system=None, max_tokens=2000):
        self.calls += 1
        return self.response


def test_generate_identities_with_recurring_character():
    response = json.dumps({
        "has_recurring_character": True,
        "character_identity": {"character_id": "char_1", "name_or_role": "a knight", "hair": "black, short"},
        "environment_identity": {"location_id": "loc_1", "architecture": "stone castle"},
    })
    llm = _FakeLLM(response)
    script = {"title": "t", "theme": "th", "scenes": [{"scene_number": 1, "description": "d"}]}
    identities = generate_identities(llm, script, "en")
    assert identities["character_identity"]["name_or_role"] == "a knight"
    # every declared field present even if the LLM only wrote a couple
    for field in CHARACTER_IDENTITY_FIELDS:
        assert field in identities["character_identity"]
    for field in ENVIRONMENT_IDENTITY_FIELDS:
        assert field in identities["environment_identity"]


def test_generate_identities_without_recurring_character():
    response = json.dumps({
        "has_recurring_character": False,
        "character_identity": None,
        "environment_identity": {"location_id": "loc_1", "architecture": "empty plaza"},
    })
    llm = _FakeLLM(response)
    script = {"title": "t", "theme": "th", "scenes": [{"scene_number": 1, "description": "d"}]}
    identities = generate_identities(llm, script, "en")
    assert identities["character_identity"] is None


def test_generate_identities_raises_after_retry_on_malformed_response():
    llm = _FakeLLM("not json at all")
    script = {"title": "t", "theme": "th", "scenes": [{"scene_number": 1, "description": "d"}]}
    with pytest.raises(ValueError, match="did not return valid identities"):
        generate_identities(llm, script, "en")
    assert llm.calls == 2  # one retry, not an infinite loop


# --------------------------------------------------- semantic validation ---
# A parseable-but-wrong-shaped response (e.g.
# has_recurring_character: true with character_identity: null, or a JSON
# string "false" instead of the boolean false) previously passed straight
# through the old "environment_identity" in data check and silently produced
# empty identity text downstream, with every existing test still green.
def test_generate_identities_retries_when_character_identity_null_despite_true_flag():
    bad = json.dumps({
        "has_recurring_character": True, "character_identity": None,
        "environment_identity": {"architecture": "stone castle"},
    })
    good = json.dumps({
        "has_recurring_character": True,
        "character_identity": {"name_or_role": "a knight"},
        "environment_identity": {"architecture": "stone castle"},
    })

    class _TwoResponseLLM:
        def __init__(self):
            self.calls = 0

        def generate(self, prompt, system=None, max_tokens=2000):
            self.calls += 1
            return bad if self.calls == 1 else good

    llm = _TwoResponseLLM()
    script = {"title": "t", "theme": "th", "scenes": [{"scene_number": 1, "description": "d"}]}
    identities = generate_identities(llm, script, "en")
    assert identities["character_identity"]["name_or_role"] == "a knight"
    assert llm.calls == 2


def test_generate_identities_raises_when_character_identity_stays_null():
    response = json.dumps({
        "has_recurring_character": True, "character_identity": None,
        "environment_identity": {"architecture": "stone castle"},
    })
    llm = _FakeLLM(response)
    script = {"title": "t", "theme": "th", "scenes": [{"scene_number": 1, "description": "d"}]}
    with pytest.raises(ValueError, match="did not return valid identities"):
        generate_identities(llm, script, "en")
    assert llm.calls == 2


def test_generate_identities_rejects_string_boolean_has_recurring_character():
    """bool("false") is True in Python — must be rejected as a type error,
    not silently treated as an enabled recurring character."""
    response = json.dumps({
        "has_recurring_character": "false",
        "character_identity": {"name_or_role": "unexpected hero"},
        "environment_identity": {"architecture": "stone castle"},
    })
    llm = _FakeLLM(response)
    script = {"title": "t", "theme": "th", "scenes": [{"scene_number": 1, "description": "d"}]}
    with pytest.raises(ValueError, match="did not return valid identities"):
        generate_identities(llm, script, "en")
    assert llm.calls == 2


def test_generate_identities_rejects_empty_environment_identity():
    response = json.dumps({
        "has_recurring_character": False, "character_identity": None,
        "environment_identity": {},
    })
    llm = _FakeLLM(response)
    script = {"title": "t", "theme": "th", "scenes": [{"scene_number": 1, "description": "d"}]}
    with pytest.raises(ValueError, match="did not return valid identities"):
        generate_identities(llm, script, "en")
    assert llm.calls == 2


def test_format_character_identity_deterministic_and_concatenates_fields():
    character = {
        "character_id": "char_1", "name_or_role": "a cartographer", "gender_presentation": "male",
        "approx_age": "30s", "hair": "brown, short", "face_shape": "", "skin_tone": "",
        "eye_features": "", "distinctive_features": "", "wardrobe": "blue coat",
        "accessories": "leather satchel", "body_build": "", "visual_style": "",
    }
    text = format_character_identity(character)
    assert "a cartographer" in text
    assert "brown, short hair" in text
    assert "wearing blue coat" in text
    assert "with leather satchel" in text
    # same input -> byte-identical output every call (the whole point: no
    # per-scene re-derivation that could drift)
    assert format_character_identity(character) == text


def test_format_character_identity_none_returns_empty_string():
    assert format_character_identity(None) == ""


def test_format_environment_identity_concatenates_fields():
    env = {
        "location_id": "loc_1", "architecture": "stone lighthouse", "materials": "",
        "lighting": "moonlit", "weather": "", "time_of_day": "night",
        "color_palette": "deep blue, warm amber", "landmarks": "", "props": "",
        "camera_language": "",
    }
    text = format_environment_identity(env)
    assert "stone lighthouse" in text
    assert "moonlit" in text
    assert "color palette: deep blue, warm amber" in text


def test_anti_text_negative_prompt_mentions_key_terms():
    assert "text" in ANTI_TEXT_NEGATIVE_PROMPT
    assert "watermark" in ANTI_TEXT_NEGATIVE_PROMPT


# --------------------------------------------------------- narrative quality ---
def _scene(n, **overrides):
    scene = {
        "scene_number": n, "previous_scene_id": n - 1 if n > 1 else None,
        "continuity_from_previous": "walking forward" if n > 1 else "",
        "narrative_purpose": f"purpose {n}",
    }
    scene.update(overrides)
    return scene


def test_check_narrative_quality_no_warnings_for_clean_storyboard():
    data = {"scenes": [_scene(1), _scene(2), _scene(3)]}
    assert check_narrative_quality(data) == []


def test_check_narrative_quality_flags_duplicate_purpose():
    data = {"scenes": [_scene(1, narrative_purpose="introduce hero"), _scene(2, narrative_purpose="introduce hero")]}
    warnings = check_narrative_quality(data)
    assert any("same narrative_purpose" in w for w in warnings)


def test_check_narrative_quality_flags_missing_continuity():
    data = {"scenes": [_scene(1), _scene(2, continuity_from_previous="")]}
    warnings = check_narrative_quality(data)
    assert any("missing continuity_from_previous" in w and "scene 2" in w for w in warnings)


def test_check_narrative_quality_flags_invalid_previous_scene_id():
    data = {"scenes": [_scene(1), _scene(2, previous_scene_id=99)]}
    warnings = check_narrative_quality(data)
    assert any("does not reference an existing scene" in w for w in warnings)
