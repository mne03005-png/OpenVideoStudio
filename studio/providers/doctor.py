"""Provider health-check: is everything configured actually reachable?

Run from the studio/ directory:

    python -m providers.doctor

Reports one line per provider and exits 0 when every checkable provider is
reachable, 1 otherwise. Runs fine with all services stopped: unreachable
providers are reported, not raised. Providers without a meaningful health
check (in-process identities, per-request public APIs) are listed as
skipped rather than guessed at.
"""
from __future__ import annotations

import argparse
import sys

from providers._config_utils import default_ollama_model, default_ollama_server
from providers._comfy_client import ComfyClient
from providers.llm.ollama_provider import OllamaProvider


def collect_checks() -> list[tuple[str, str, object]]:
    """Build the health-check list from the providers the pipeline actually
    constructs, with the same config defaults.

    Each entry is ``(kind, name, probe)``. ``probe`` is an object exposing
    ``is_available(timeout=...)`` (mirroring the existing per-provider
    methods), or None for providers without a meaningful reachability check.
    """
    return [
        ("llm", "ollama", OllamaProvider(model=default_ollama_model(), server=default_ollama_server())),
        ("image", "comfyui_sdxl", ComfyClient()),
        ("video", "comfyui_ltx", ComfyClient()),
        ("identity", "text", None),
        ("identity", "image_reference", None),
        ("tts", "edge_tts", None),
    ]


def run_doctor(checks, timeout: float = 5.0, out=print) -> bool:
    """Probe every check; return True when all probeable providers are up."""
    all_ok = True

    for kind, name, probe in checks:
        label = f"{kind}/{name}"

        if probe is None:
            out(f"[skip ] {label} (in-process or per-request; no health check)")
            continue

        try:
            ok = probe.is_available(timeout=timeout)
        except Exception as error:  # noqa: BLE001
            out(f"[down ] {label} ({error})")
            all_ok = False
            continue

        if ok:
            out(f"[  ok ] {label}")
        else:
            out(f"[down ] {label}")
            all_ok = False

    return all_ok


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check whether all configured providers are reachable.",
    )
    parser.add_argument(
        "--timeout", type=float, default=5.0,
        help="Per-provider reachability timeout in seconds.",
    )
    args = parser.parse_args()

    ok = run_doctor(collect_checks(), timeout=args.timeout)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
