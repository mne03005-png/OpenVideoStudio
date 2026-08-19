"""Canonical character/environment identity — generated ONCE per project,
then reused verbatim (by code, not by re-asking the LLM) everywhere a
prompt needs it.

V0.2's `visual_identity` was a single free-text string the LLM had to
reproduce consistently across every scene in the SAME storyboard call —
in practice this drifted in testing (wardrobe/environment held up,
facial identity didn't). The fix here isn't a bigger/smarter model,
it's a smaller surface for drift: identity is generated in its own
focused LLM call, structured into fields, formatted into text by code
(format_character_identity/format_environment_identity), and that
IDENTICAL formatted text is what every downstream prompt gets — the LLM
never has to remember or re-derive it per scene.
"""
from __future__ import annotations

from typing import Optional

from providers.base import LLMProvider
from creative._json_utils import extract_json

CHARACTER_IDENTITY_FIELDS = [
    "character_id", "name_or_role", "gender_presentation", "approx_age", "hair",
    "face_shape", "skin_tone", "eye_features", "distinctive_features", "wardrobe",
    "accessories", "body_build", "visual_style",
]

ENVIRONMENT_IDENTITY_FIELDS = [
    "location_id", "architecture", "materials", "lighting", "weather", "time_of_day",
    "color_palette", "landmarks", "props", "camera_language",
]

_SYSTEM = """You design the canonical visual identity for a short AI-generated video, \
BEFORE any per-scene storyboard is written. Output ONLY a JSON object (no prose, no \
markdown fences) with this exact shape:

{
  "has_recurring_character": true or false,
  "character_identity": {
    "character_id": "char_1",
    "name_or_role": "short label, e.g. 'the cartographer' or a name",
    "gender_presentation": "",
    "approx_age": "",
    "hair": "color, length, style",
    "face_shape": "",
    "skin_tone": "",
    "eye_features": "",
    "distinctive_features": "scars, glasses, freckles, etc. — empty string if none",
    "wardrobe": "specific recurring clothing, in enough visual detail to draw consistently",
    "accessories": "bag, jewelry, tools, etc. — empty string if none",
    "body_build": "",
    "visual_style": "art/rendering style descriptor shared by the whole video"
  } or null if has_recurring_character is false,
  "environment_identity": {
    "location_id": "loc_1",
    "architecture": "",
    "materials": "",
    "lighting": "",
    "weather": "",
    "time_of_day": "",
    "color_palette": "2-4 dominant colors, concrete (e.g. 'deep blue, warm amber, grey stone')",
    "landmarks": "one or two recurring, recognizable visual anchors",
    "props": "recurring objects, empty string if none",
    "camera_language": "recurring visual/cinematographic language, e.g. 'handheld, low angle, shallow depth of field'"
  }
}

Rules:
- Every field is a short, CONCRETE, visual English phrase — no abstract or emotional \
language, this text gets fed directly into an image generator's prompt.
- has_recurring_character should be true whenever the script clearly follows one \
protagonist across scenes (most short narratives do); false only for scripts with no \
single recurring subject (e.g. a montage of different unrelated subjects/places).
- environment_identity should describe ONE cohesive primary setting/visual world for \
the whole video, even if scenes move around within it.
- Output valid JSON only."""


def _validate_identities(data: dict) -> None:
    """Raises ValueError with a specific reason on the first problem found,
    so the retry loop can hand the LLM one clear reason.

    Deliberately stricter than "the key exists": a parseable-but-wrong-shaped
    response (has_recurring_character: true with character_identity: null,
    or a JSON string "false" instead of the boolean false) previously passed
    straight through and silently produced empty identity text downstream —
    the entire V0.3 feature defeated with no error and no test failure.
    bool is a subclass of int and bool("false") is True in Python, so both
    fields are checked with isinstance(x, bool), never coerced with
    bool(...)."""
    if not isinstance(data, dict):
        raise ValueError(f"identities response is not a JSON object (got {type(data).__name__})")

    has_character = data.get("has_recurring_character")
    if not isinstance(has_character, bool):
        raise ValueError(f"has_recurring_character must be a JSON boolean, got {has_character!r}")

    if has_character:
        character = data.get("character_identity")
        if not isinstance(character, dict) or not (character.get("name_or_role") or "").strip():
            raise ValueError(
                "character_identity must be a populated object with name_or_role when "
                "has_recurring_character is true"
            )

    environment = data.get("environment_identity")
    if not isinstance(environment, dict) or not any(
        (environment.get(field) or "").strip() for field in ENVIRONMENT_IDENTITY_FIELDS
    ):
        raise ValueError("environment_identity must be a populated object with at least one concrete field")


def generate_identities(llm: LLMProvider, script: dict, language: str = "en") -> dict:
    scenes_desc = "\n".join(
        f"Scene {s['scene_number']}: {s['description']}" for s in script["scenes"]
    )
    user_prompt = (
        f"Title: {script.get('title', '')}\n"
        f"Theme: {script.get('theme', '')}\n\n"
        f"Scenes:\n{scenes_desc}"
    )

    last_error: Optional[str] = None
    data: Optional[dict] = None
    raw = ""
    for attempt in range(2):
        try_prompt = user_prompt if attempt == 0 else (
            user_prompt + f"\nYour previous response was invalid ({last_error}). "
            "Output ONLY the JSON object described above — no prose, no markdown fences."
        )
        raw = llm.generate(try_prompt, system=_SYSTEM, max_tokens=1200)
        try:
            data = extract_json(raw)
            _validate_identities(data)
        except Exception as e:
            last_error = f"{e}"
            data = None
            continue
        break

    if data is None:
        raise ValueError(f"LLM did not return valid identities after retry: {last_error}; last raw: {raw[:500]}")

    has_character = data["has_recurring_character"]
    character = data.get("character_identity") if has_character else None
    if character is not None:
        for field in CHARACTER_IDENTITY_FIELDS:
            character.setdefault(field, "")

    environment = data.get("environment_identity") or {}
    for field in ENVIRONMENT_IDENTITY_FIELDS:
        environment.setdefault(field, "")

    return {"character_identity": character, "environment_identity": environment}


def format_character_identity(character_identity: Optional[dict]) -> str:
    """Deterministic text form of the identity dict — called every place a
    prompt needs it, so the wording is byte-identical every time, not
    re-derived by the LLM per scene."""
    if not character_identity:
        return ""
    c = character_identity
    parts = [
        c.get("name_or_role", ""),
        f"{c.get('approx_age', '')} {c.get('gender_presentation', '')}".strip(),
        f"{c.get('hair', '')} hair" if c.get("hair") else "",
        c.get("face_shape", ""),
        c.get("skin_tone", ""),
        c.get("eye_features", ""),
        c.get("distinctive_features", ""),
        f"wearing {c['wardrobe']}" if c.get("wardrobe") else "",
        f"with {c['accessories']}" if c.get("accessories") else "",
        c.get("body_build", ""),
        c.get("visual_style", ""),
    ]
    return ", ".join(p.strip() for p in parts if p and p.strip())


def format_environment_identity(environment_identity: Optional[dict]) -> str:
    if not environment_identity:
        return ""
    e = environment_identity
    parts = [
        e.get("architecture", ""),
        e.get("materials", ""),
        e.get("lighting", ""),
        e.get("weather", ""),
        e.get("time_of_day", ""),
        f"color palette: {e['color_palette']}" if e.get("color_palette") else "",
        e.get("landmarks", ""),
        e.get("props", ""),
        e.get("camera_language", ""),
    ]
    return ", ".join(p.strip() for p in parts if p and p.strip())


# Reusable negative-prompt fragment for suppressing unwanted generated text —
# SDXL/LTX are both unreliable at rendering coherent in-image text (V0.2's
# scene-3 map had nonsensical lettering). Only injected when a scene doesn't
# explicitly need readable text (storyboard's allow_generated_text: false,
# the default — see creative/storyboard.py).
ANTI_TEXT_NEGATIVE_PROMPT = (
    "text, letters, words, caption, logo, watermark, signage, garbled writing, "
    "unreadable typography, random symbols"
)
