"""Stage 1: prompt -> concept + scene-by-scene script, via LLMProvider.

New capability — no legacy equivalent. None of this codebase's earlier
private prototypes ever used an LLM.
"""
from __future__ import annotations

from typing import Optional

from providers.base import LLMProvider
from creative._json_utils import extract_json

_SYSTEM = """You are a concise short-video scriptwriter. Given a prompt, target \
duration, visual style, and language, output ONLY a JSON object (no prose, no \
markdown fences) with this exact shape:

{
  "title": "short title",
  "logline": "one sentence describing the video",
  "theme": "the emotional/thematic core in a few words",
  "scene_count": <integer>,
  "scenes": [
    {"scene_number": 1, "description": "what happens in this scene, one or two sentences"}
  ]
}

Rules:
- Write the "description", "title", "logline", "theme", and any narration in \
the requested language.
- scene_count should be sized so that, at roughly 5 seconds per scene, the \
scenes cover the target duration (e.g. 60s target -> ~10-12 scenes; 15s \
target -> ~3 scenes). Never fewer than 2 scenes.
- Each scene should be visually distinct and filmable as a single shot.
- Output valid JSON only."""


def generate_script(
    llm: LLMProvider, prompt: str, target_duration_seconds: float, style: str, language: str = "en"
) -> dict:
    user_prompt = (
        f"Prompt: {prompt}\n"
        f"Target duration: {target_duration_seconds:.0f} seconds\n"
        f"Style: {style}\n"
        f"Language: {language}\n"
    )

    last_error: Optional[str] = None
    for attempt in range(2):  # one retry — unattended runs shouldn't abort on one bad response
        try_prompt = user_prompt if attempt == 0 else (
            user_prompt + f"\nYour previous response was invalid ({last_error}). "
            "Output ONLY the JSON object described above — no prose, no markdown fences, no explanation."
        )
        raw = llm.generate(try_prompt, system=_SYSTEM, max_tokens=1500)
        try:
            data = extract_json(raw)
            if "scenes" not in data or not data["scenes"]:
                raise ValueError("no scenes in response")
        except Exception as e:
            last_error = f"{e}"
            continue
        data["scene_count"] = len(data["scenes"])
        return data

    raise ValueError(f"LLM did not return valid scenes after retry: {last_error}; last raw: {raw[:500]}")


if __name__ == "__main__":
    import argparse
    import json

    from providers._config_utils import default_ollama_model
    from providers.llm.ollama_provider import OllamaProvider

    parser = argparse.ArgumentParser(description="Generate a script from a prompt")
    parser.add_argument("prompt")
    parser.add_argument("--duration", type=float, default=15.0)
    parser.add_argument("--style", default="cinematic sci-fi")
    parser.add_argument("--language", default="en")
    parser.add_argument("--model", default=default_ollama_model())
    args = parser.parse_args()

    llm = OllamaProvider(model=args.model)
    result = generate_script(llm, args.prompt, args.duration, args.style, args.language)
    print(json.dumps(result, ensure_ascii=False, indent=2))
