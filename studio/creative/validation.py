"""Storyboard JSON schema validation. Split out of storyboard.py so both the
generation retry loop and any future caller (tests, resumed runs) can check
a storyboard's shape without re-implementing the rules.

Previously storyboard.py only checked scene count — a storyboard with the
right number of scenes but a missing/wrong-typed field (e.g. narration_text
absent, duration_seconds as a string) passed straight through to downstream
stages and failed later with a less clear error, or silently degraded via
.get() defaults. This validates the fields every downstream stage actually
reads before any of them run.
"""
from __future__ import annotations

_REQUIRED_STRING_FIELDS = [
    "image_prompt",
    "negative_prompt",
    "video_motion_prompt",
    "video_negative_prompt",
    "narration_text",
]


def validate_storyboard(data: dict, expected_scene_count: int) -> None:
    """Raises ValueError with a specific reason on the first problem found.
    Intentionally fails fast (one clear reason) rather than collecting every
    issue — the caller's retry loop only needs one reason to hand back to
    the LLM."""
    if not isinstance(data, dict):
        raise ValueError(f"storyboard is not a JSON object (got {type(data).__name__})")

    scenes = data.get("scenes")
    if not isinstance(scenes, list):
        raise ValueError("storyboard has no 'scenes' list")
    if len(scenes) != expected_scene_count:
        raise ValueError(f"scene count {len(scenes)} != expected {expected_scene_count}")

    seen_numbers = set()
    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise ValueError(f"scene at index {i} is not a JSON object")

        n = scene.get("scene_number")
        if not isinstance(n, int):
            raise ValueError(f"scene at index {i} has non-integer scene_number: {n!r}")
        if n in seen_numbers:
            raise ValueError(f"duplicate scene_number {n}")
        seen_numbers.add(n)

        for field in _REQUIRED_STRING_FIELDS:
            value = scene.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"scene {n} missing or empty required string field '{field}'")

        duration = scene.get("duration_seconds")
        if duration is not None and not isinstance(duration, (int, float)):
            raise ValueError(f"scene {n} has non-numeric duration_seconds: {duration!r}")

        prev_id = scene.get("previous_scene_id")
        if prev_id is not None and not isinstance(prev_id, int):
            raise ValueError(f"scene {n} has non-integer previous_scene_id: {prev_id!r}")

        # bool is a subclass of int, so isinstance(x, bool) must be checked
        # before/separately from any int check. Rejecting non-bool here (e.g.
        # the string "false", which Python's own bool("false") == True) is
        # deliberate: a naive bool(...) coercion downstream would otherwise
        # silently invert this flag and disable anti-text negative-prompt
        # suppression without ever raising.
        if "allow_generated_text" in scene and not isinstance(scene["allow_generated_text"], bool):
            raise ValueError(
                f"scene {n} has non-boolean allow_generated_text: {scene['allow_generated_text']!r}"
            )

    expected_numbers = set(range(1, expected_scene_count + 1))
    if seen_numbers != expected_numbers:
        raise ValueError(f"scene_number values {sorted(seen_numbers)} != expected {sorted(expected_numbers)}")


def check_narrative_quality(data: dict) -> list[str]:
    """Soft, non-raising checks (V0.3 Priority 8) — collected as warnings
    rather than triggering an LLM retry, since these are quality signals,
    not schema breakage: a duplicate narrative_purpose or a missing
    continuity note doesn't make the storyboard unusable the way a missing
    narration_text does.

    Deliberately does NOT attempt to detect "incompatible character/
    environment descriptors" via keyword matching — that would need real
    semantic understanding this pipeline doesn't have, and a fake check
    that doesn't actually catch contradictions is worse than no check
    (same principle as not pretending to have face-identity detection the
    stack can't support — see continuity.py)."""
    warnings: list[str] = []
    scenes = data.get("scenes", [])

    purposes: dict[str, list[int]] = {}
    for scene in scenes:
        n = scene.get("scene_number")
        purpose = (scene.get("narrative_purpose") or "").strip().lower()
        if purpose:
            purposes.setdefault(purpose, []).append(n)

        if n and n > 1 and not (scene.get("continuity_from_previous") or "").strip():
            warnings.append(f"scene {n}: missing continuity_from_previous (scene > 1)")

        prev_id = scene.get("previous_scene_id")
        if n and n > 1 and prev_id is not None:
            valid_numbers = {s.get("scene_number") for s in scenes}
            if prev_id not in valid_numbers:
                warnings.append(f"scene {n}: previous_scene_id {prev_id} does not reference an existing scene")

    for purpose, scene_numbers in purposes.items():
        if len(scene_numbers) > 1:
            warnings.append(f"scenes {scene_numbers} share the same narrative_purpose ({purpose!r})")

    return warnings
