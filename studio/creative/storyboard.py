"""Stage 2: script scenes -> per-scene image prompts, narration text, and
durations, via LLMProvider. This is what the review gate reviews — nothing
after this stage runs without explicit approval (enforced in
creative/pipeline.py, not just here).

V0.3: character/environment identity is generated ONCE (creative/identity.py,
a separate focused LLM call) before this function's own call, rather than
asked of the LLM once per storyboard alongside 6-12 scenes' worth of other
fields. That call's output becomes fixed context text handed to THIS
prompt — the per-scene fields below only ever describe how a scene APPLIES
the already-decided identity (pose, action, framing), never re-invent it.
"""
from __future__ import annotations

from typing import Optional

from providers.base import LLMProvider
from creative._json_utils import extract_json
from creative.validation import validate_storyboard, check_narrative_quality
from creative.identity import generate_identities, format_character_identity, format_environment_identity

# Empirical Edge TTS speaking rate, measured from 6 real narration clips
# across the two 2026-08-19 overnight acceptance runs (2.82-2.91 words/sec,
# averaging ~2.85). duration_seconds is DERIVED from this rather than
# trusted from the LLM's own number: the LLM's numeric duration_seconds
# guess routinely didn't match the length of narration_text it wrote in the
# same response (both overnight runs had every scene land on the same 4.5s
# regardless of actual narration length), which is what caused every scene
# to overshoot its target once the real (longer) narration forced a
# freeze-pad/retime in the edit stage. Computing duration from the actual
# text word count keeps the two in sync from the start.
_WORDS_PER_SECOND = 2.8
_MIN_SCENE_SECONDS = 3.0
_MAX_SCENE_SECONDS = 8.0

_SYSTEM = """You are a storyboard artist for an AI image/video pipeline. The video's \
character and setting identity have ALREADY been decided (given to you as fixed \
context below) — your job is to write what HAPPENS in each scene, not to redescribe \
who/where. Output ONLY a JSON object (no prose, no markdown fences) with this exact shape:

{
  "scenes": [
    {
      "scene_number": 1,
      "previous_scene_id": <integer scene_number of the preceding scene, or null for scene 1>,
      "continuity_from_previous": "one short phrase on what carries over from the prior \
scene (position, action, object, emotional beat) — empty string for scene 1",
      "narrative_purpose": "one short phrase: what this scene accomplishes in the story \
(must be DISTINCT from every other scene's purpose — no two scenes should exist for the \
same reason)",
      "visual_change": "one short phrase: what's visually different in THIS scene vs the \
previous one (new framing, new action, new detail revealed) — empty string for scene 1",
      "camera_change": "how the camera/framing differs from the previous scene, e.g. \
'cuts from wide to close-up', 'same angle, character has moved closer' — empty string for scene 1",
      "shot_size": "one of: extreme wide, wide, medium, close-up, extreme close-up",
      "camera_movement": "short phrase, e.g. 'static', 'slow push-in', 'pan left', \
'slow pull-back'",
      "mood": "1-3 words, e.g. 'tense, quiet' or 'awe, wonder'",
      "transition_intent": "one of: hard cut, match cut, cross-fade, continuous motion",
      "allow_generated_text": false,
      "image_prompt": "detailed English visual prompt for an SDXL image generator: what \
the subject is DOING, camera angle, lighting for this moment. Describes a single STILL \
frame. Do NOT redescribe the character's appearance or the environment's fixed features — \
that's handled separately. Only include what's specific to THIS scene's action/moment.",
      "negative_prompt": "things to avoid, in English: e.g. blurry, low quality, extra limbs",
      "video_motion_prompt": "short English phrase describing only the MOTION to \
animate this still into a clip, incorporating camera_movement: e.g. 'camera slowly \
pushes in, dust drifts in the wind' — not a re-description of the scene content, just \
the movement",
      "video_negative_prompt": "motion artifacts to avoid, in English: e.g. \
jitter, warping, flickering",
      "narration_text": "what the narrator says during this scene, in the \
requested language, one or two sentences",
      "subtitle_text": "the on-screen subtitle text for this scene, in the requested \
language — normally identical to narration_text; only make it shorter if narration_text \
is unusually long and a condensed version reads better on screen"
    }
  ]
}

Rules:
- image_prompt and video_motion_prompt must always be in English, regardless of \
the requested narration language — the image/video models only understand English.
- narration_text and subtitle_text must be in the requested language.
- image_prompt describes only what's NEW/specific to this scene (action, framing, moment) \
— never restate the character's face/hair/clothing or the environment's architecture/palette, \
those are added automatically from the fixed identity context.
- Keep narration_text natural to actually speak aloud — don't pad it to hit a \
duration target, duration is computed from what you write, not the other way around.
- allow_generated_text must be true ONLY if the story specifically requires readable \
in-image text (a sign, a letter, a screen) for this exact scene to make sense — false \
in every other case, including maps/books/displays where the text itself doesn't matter.
- Every narrative_purpose must be distinct — if two scenes would serve the same purpose, \
merge or differentiate them.
- Output valid JSON only, one storyboard entry per input scene, same scene_number values."""


def generate_storyboard(llm: LLMProvider, script: dict, language: str = "en") -> dict:
    identities = generate_identities(llm, script, language)
    character_text = format_character_identity(identities["character_identity"])
    environment_text = format_environment_identity(identities["environment_identity"])

    scenes_desc = "\n".join(
        f"Scene {s['scene_number']}: {s['description']}" for s in script["scenes"]
    )
    expected_count = len(script["scenes"])
    identity_context = (
        f"Character identity (fixed, do not redescribe): {character_text or '(no recurring character)'}\n"
        f"Environment identity (fixed, do not redescribe): {environment_text}\n\n"
    )
    user_prompt = (
        f"Title: {script.get('title', '')}\n"
        f"Theme: {script.get('theme', '')}\n"
        f"Narration language: {language}\n\n"
        f"{identity_context}"
        f"Scenes:\n{scenes_desc}"
    )

    last_error: Optional[str] = None
    data: Optional[dict] = None
    raw = ""
    for attempt in range(2):  # one retry — unattended runs shouldn't abort on one bad response
        try_prompt = user_prompt if attempt == 0 else (
            user_prompt + f"\nYour previous response was invalid ({last_error}). "
            f"Output ONLY the JSON object described above, with exactly {expected_count} "
            "scene entries matching the given scene_number values — no prose, no markdown fences."
        )
        raw = llm.generate(try_prompt, system=_SYSTEM, max_tokens=4500)
        try:
            data = extract_json(raw)
            validate_storyboard(data, expected_count)
        except Exception as e:
            last_error = f"{e}"
            data = None
            continue
        break

    if data is None:
        raise ValueError(f"LLM did not return a valid storyboard after retry: {last_error}; last raw: {raw[:500]}")

    # Merge script description alongside storyboard fields for downstream stages
    # and the review table (both are useful context there), fill in optional-field
    # defaults, and compute duration_seconds from the narration actually written
    # rather than trusting the LLM's own number (see _WORDS_PER_SECOND above).
    by_number = {s["scene_number"]: s for s in script["scenes"]}
    for entry in data["scenes"]:
        src = by_number.get(entry["scene_number"], {})
        entry["description"] = src.get("description", "")
        entry.setdefault("shot_size", "medium")
        entry.setdefault("camera_movement", "static")
        entry.setdefault("mood", "")
        entry.setdefault("transition_intent", "hard cut")
        entry.setdefault("subtitle_text", entry.get("narration_text", ""))
        entry.setdefault("previous_scene_id", entry["scene_number"] - 1 if entry["scene_number"] > 1 else None)
        entry.setdefault("continuity_from_previous", "")
        entry.setdefault("narrative_purpose", "")
        entry.setdefault("visual_change", "")
        entry.setdefault("camera_change", "")
        # validate_storyboard already rejected a non-boolean value above, so
        # this default-only setdefault is safe — no bool(...) coercion here
        # (bool("false") == True in Python, which would silently invert a
        # string-typed LLM response instead of catching it).
        entry.setdefault("allow_generated_text", False)

        word_count = len((entry.get("narration_text") or "").split())
        if word_count:
            estimated = word_count / _WORDS_PER_SECOND + 0.3  # small buffer for TTS lead-in/pauses
            entry["duration_seconds"] = max(_MIN_SCENE_SECONDS, min(_MAX_SCENE_SECONDS, estimated))
        else:
            entry["duration_seconds"] = max(
                _MIN_SCENE_SECONDS, min(_MAX_SCENE_SECONDS, float(entry.get("duration_seconds", 4.0)))
            )

    data["character_identity"] = identities["character_identity"]
    data["environment_identity"] = identities["environment_identity"]
    data["narrative_quality_warnings"] = check_narrative_quality(data)
    return data


if __name__ == "__main__":
    import argparse
    import json

    from providers.llm.ollama_provider import OllamaProvider
    from creative.script import generate_script

    parser = argparse.ArgumentParser(description="Generate a storyboard from a prompt (runs script.py first)")
    parser.add_argument("prompt")
    parser.add_argument("--duration", type=float, default=15.0)
    parser.add_argument("--style", default="cinematic sci-fi")
    parser.add_argument("--language", default="en")
    parser.add_argument("--model", default="qwen3:8b")
    args = parser.parse_args()

    llm = OllamaProvider(model=args.model)
    script = generate_script(llm, args.prompt, args.duration, args.style, args.language)
    storyboard = generate_storyboard(llm, script, args.language)
    print(json.dumps(storyboard, ensure_ascii=False, indent=2))
