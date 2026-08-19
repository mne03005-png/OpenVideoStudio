# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities privately, not as a public GitHub
issue — use GitHub's private [Security Advisory](../../security/advisories/new)
feature on this repository so the report isn't visible before a fix is
available.

Include: what you found, how to reproduce it, and its potential impact.
We'll acknowledge reports within a reasonable timeframe and keep you
updated as we investigate and fix.

## Scope

This project runs entirely local models against locally-running services
(Ollama, ComfyUI) by default. Relevant security surface includes:

- Anything that could read/write files outside the intended run/output
  directories
- Anything that could execute unintended commands (this project shells
  out to FFmpeg — command construction matters)
- Credential handling for any configured cloud provider (`.env` values)
- Anything that could make the local Gradio UI (`app.py`) reachable or
  exploitable beyond its intended localhost use

Out of scope: vulnerabilities in third-party dependencies (Ollama,
ComfyUI, FFmpeg, model weights themselves) — please report those to their
respective projects. If a vulnerability there has a specific, exploitable
interaction with OpenVideoStudio's own code, that interaction is in scope.

## Supported versions

This project is pre-1.0 and moves quickly; security fixes target the
latest `main` branch. There is no separate long-term-support branch at
this stage.

## Our commitment

No secrets are ever intentionally committed to this repository — see
`docs/OPEN_SOURCE_SECURITY_AUDIT.md` for the pre-launch audit. If you find
one anyway, please report it privately as above so it can be rotated and
removed from history, not just deleted from the latest commit.
