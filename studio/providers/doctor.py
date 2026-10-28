"""Provider health-check: is everything configured actually reachable?

Run from the studio/ directory:

    python -m providers.doctor

Mirrors the creative pipeline's provider selection: names come from
config.toml's ``[providers]`` table with the same defaults
(``creative/pipeline.py::_provider_name`` is the source of truth for the
selection semantics), construction goes through
``providers.registry.get_provider`` — the single construction path.

One ``[ok]``/``[down]``/``[skip]``/``[fail]`` line per configured provider;
exit 0 only when every probeable provider is up. An unknown configured
provider name or a construction failure is reported as a failure, not
silently replaced by a default.

Reachability scope: the ComfyUI checks hit ``/system_stats``, which proves
the server is up — they do not verify SDXL/LTX checkpoints, T5, required
custom nodes, or filesystem readiness. Deeper readiness checks are a
future track.

Providers without a meaningful reachability probe are reported as skipped
rather than guessed at. The ``identity`` kind is intentionally not probed:
the pipeline constructs it only when a character asset exists, so there is
no unconditional health check to mirror.
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from providers._config_utils import default_ollama_model, default_ollama_server
from providers.registry import get_provider

_KIND_DEFAULTS = {
    "llm": "ollama",
    "image": "comfyui_sdxl",
    "video": "comfyui_ltx",
    "tts": "edge_tts",
}


@dataclass(frozen=True)
class Check:
    """One provider's health-check entry.

    ``probe`` is an object exposing ``is_available(timeout=...)``, or None
    when the provider has no meaningful reachability check. ``error`` is set
    when the configured name is unknown or construction failed — the check
    then counts as a failure without probing.
    """

    kind: str
    name: str
    probe: object | None = None
    error: str | None = None


def _config() -> dict:
    """config.toml as a dict; the same file the pipeline reads."""
    path = Path(__file__).resolve().parent.parent / "config.toml"
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def _configured_name(kind: str, config: dict) -> str:
    """Same selection as creative/pipeline.py's _provider_name."""
    return config.get("providers", {}).get(kind, _KIND_DEFAULTS[kind])


def _probe_for(provider: object) -> object | None:
    """The pipeline never probes uniformly: llm exposes ``is_available`` on
    the provider, the ComfyUI families carry it on their shared client."""
    if hasattr(provider, "is_available"):
        return provider
    client = getattr(provider, "client", None)
    if client is not None and hasattr(client, "is_available"):
        return client
    return None


def collect_checks(config: dict | None = None, factory=get_provider) -> list[Check]:
    """Build the health-check list for the configured provider selection.

    ``config`` overrides the studio config.toml (used by tests); ``factory``
    replaces the registry construction (used by tests). Providers are built
    through the registry exactly as the pipeline does; an unknown configured
    name or a construction failure becomes a failing check instead of a
    silent fallback to the default or a crash.
    """
    config = config if config is not None else _config()
    providers_cfg = config.get("providers", {})
    checks: list[Check] = []

    for kind, default in _KIND_DEFAULTS.items():
        name = _configured_name(kind, config)
        try:
            if kind == "llm":
                provider = factory(
                    "llm", name,
                    model=providers_cfg.get("ollama_model", default_ollama_model()),
                    server=providers_cfg.get("ollama_server", default_ollama_server()),
                )
            else:
                provider = factory(kind, name)
        except Exception as e:  # noqa: BLE001 — construction failure is data, not a crash
            checks.append(Check(kind=kind, name=name, error=f"{type(e).__name__}: {e}"))
            continue
        checks.append(Check(kind=kind, name=name, probe=_probe_for(provider)))

    return checks


def run_doctor(checks: list[Check], timeout: float = 5.0, out=print) -> bool:
    """Probe every check; return True when all probeable providers are up."""
    all_ok = True

    for check in checks:
        label = f"{check.kind}/{check.name}"

        if check.error is not None:
            out(f"[fail ] {label} ({check.error})")
            all_ok = False
            continue

        if check.probe is None:
            out(f"[skip ] {label} (in-process or per-request; no health check)")
            continue

        try:
            ok = check.probe.is_available(timeout=timeout)
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
