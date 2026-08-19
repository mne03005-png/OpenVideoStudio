# Open-Source Security & Privacy Audit

Current-state audit of this repository, built by selectively copying
source and tests out of a private development workspace (not a history
export of it — see `docs/PUBLIC_REPOSITORY_PLAN.md`). This document
describes what's true of the working tree **right now**, verified by
direct inspection — not a log of every fix that got it here. This
repository's git history is a deliberately curated release-preparation
history, not the private workspace's own step-by-step development
history — that process happened elsewhere and isn't reproduced here.
Run `git log --all` yourself to see the current, exact history rather
than trusting a commit count in this document, which — as an earlier
draft of this exact sentence demonstrated by going stale within one
commit of being written — is guaranteed to be wrong again the next time
anything here changes.

**A note on how this document is written, and why:** earlier drafts of
this document repeatedly quoted the specific private information they
described removing, and repeatedly narrated round-by-round review
history with counts and specifics that went stale the next time
something changed. Both were real mistakes, caught by independent
review, more than once. This version deliberately does neither: it
states current facts, verifiable by inspecting the repository yourself,
and avoids reproducing anything sensitive even as an example.

## Scope

Everything in this repository's working tree — source, tests, config,
and documentation. Out of scope by design: the private development
workspace this was built from, which retains its own separate history,
several hundred other tracked files unrelated to this project, and an
unrelated colocated private project. None of that is exported here in
any form.

## Findings

**No secrets.** No API keys, tokens, passwords, credentials, or `.env`
files exist anywhere in this repository. The only environment-variable
template (`studio/.env.example`) contains commented-out placeholder names
for future providers, with no values.

**No exact private identifiers.** No absolute path, username, or the
private workspace's own name appears anywhere in this repository's
tracked files or commit history (verified directly against `git log`,
not by assertion).

**Generic development provenance remains, deliberately.** Several source
files and `config.toml` note that specific parameters or logic were
"carried over from an earlier private prototype." This is honest,
ordinary open-source provenance — nearly every real open-source project
started as private work before release — and does not identify what that
prior work was, where it lived, or anything about it beyond "it existed."
Removing this kind of note entirely was considered and rejected: it would
make the codebase read as if every design decision were invented from
scratch, which isn't true and isn't necessary to hide.

**No model binaries. One tracked media file, deliberately.** No
`.safetensors`, `.gguf`, `.tflite`, checkpoint, or LoRA file is tracked —
checked by extension, not just by convention. The one small (228 KB)
MediaPipe face-detector model Media Remix uses is gitignored and fetched
by the user during setup — see `docs/INSTALL.md` for the verified
download source.

One image file **is** tracked: `examples/hero_demo/preview.gif`
(3.5 MB — currently the single largest tracked file in the repository,
per `git ls-files` checked directly, not assumed). This is the compact
preview embedded in both READMEs for the hero demo — a deliberate
inclusion, not an oversight, and small enough that it doesn't meaningfully
affect clone size. The full-resolution `final.mp4` and the six
full-resolution keyframe PNGs are *not* tracked (gitignored — see
`examples/hero_demo/README.md` for why and how they're meant to be
distributed instead at launch). `examples/hero_demo/storyboard.json`
originally contained 18 absolute local paths pointing at the specific
run directory this demo was generated in
(`.../studio/runs/create_<timestamp>/...`) — real machine/run metadata,
caught during this audit and fixed by rewriting those fields to plain
relative paths (`keyframes/scene_01.png`, etc.) that describe the
repository's own structure instead of one specific machine's. Verify
directly: `grep -c "D:" examples/hero_demo/storyboard.json` should return
`0`.

**No credential file structure.** `git ls-files` confirms no `.env` (only
`.env.example`, values-free) is tracked anywhere in the repository.

**Cross-platform gaps exist and are tracked, not hidden.** Final video
encoding requires an NVENC-capable NVIDIA GPU (no software/other-vendor
fallback yet); subtitle rendering hardcodes a Windows font path; Media
Remix's "open output folder" button is Windows-only. None of these are
privacy issues — see `docs/HARDWARE.md` for the honest compatibility
matrix and `docs/ISSUES_SEED.md` for the seeded issues tracking each one.

## How this was verified

Direct inspection of every file, plus repeated pattern searches across
the whole tree (paths, usernames, project names in both literal-path and
ordinary-prose form, versioned internal script identifiers, coordination
filenames) — broadened each time an independent review found a category
the previous search didn't cover. The searches used to reach the current
state are not reproduced here; re-run your own if you want to verify this
document's claims yourself, which is the actual point of a security
audit that ships with the code it audits.

## Independent review

This document and the repository it describes have been through multiple
rounds of independent review: a separate reviewer reads what this
project's own status notes claim, then re-derives every claim
independently against the actual repository — reading the real files,
running real commands, checking real `git log` output — rather than
accepting the notes' narrative, including review specifically of *this
document's own accuracy*, not just the code. That process is what found
and corrected the self-referential leaks and stale claims earlier
versions of this document had, more than once. Treat any specific claim
above as something you can and should re-verify yourself against the
actual repository state, not as a final word.
