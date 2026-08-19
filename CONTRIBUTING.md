# Contributing to OpenVideoStudio

Thanks for considering it. This guide covers how to find something to
work on, how the review process works, and how you earn more trust (and
more repository access) over time.

## Find something to work on

1. Check [`docs/ISSUES_SEED.md`](docs/ISSUES_SEED.md) / the repo's Issues
   tab for a `good first issue` if this is your first contribution here —
   each one has a full spec (problem, why it matters, relevant files,
   expected result, acceptance criteria, how to test).
2. Browse [`docs/COMMUNITY_TRACKS.md`](docs/COMMUNITY_TRACKS.md) if you
   want to work in a specific area (AI Art, Model Gateway, Character
   Consistency, Platform Support, Timeline/Editor, AI Video QC,
   Documentation/Localization) — it lists that track's vision, boundaries,
   and starter/help-wanted/research issues.
3. Have an idea that isn't in either? Open a
   [GitHub Discussion](../../discussions) under **Ideas** before writing
   code, especially if it touches a shared interface (see "What needs
   discussion first" below).

**Comment on the issue before starting significant work** — it's the
easiest way to avoid two people building the same thing.

## Difficulty levels

- **good first issue** — genuinely small and well-scoped, with every field
  in the issue spec filled in. If you find a `good first issue` that's
  actually vague or huge, say so — it was mislabeled.
- **help wanted** — meaningful, independently implementable work that
  doesn't require rewriting core architecture.
- **research** — open-ended; contributions can be papers, benchmarks,
  experiments, or prototypes, not only finished PRs.

## Development setup

See [`docs/INSTALL.md`](docs/INSTALL.md). To run the test suite (no live
services required — LLM/image/video providers are faked in tests):

```bash
cd studio
python -m pytest tests/ -q
```

## Making a change

1. Fork the repo, branch from `main`.
2. Write tests for what you change — this project's test suite exists
   specifically because past bugs (see commit history) were caught by
   exactly this discipline. A PR that changes pipeline behavior without a
   test covering it will be asked to add one before review.
3. Sign off your commits (`git commit -s`) — see "Developer Certificate of
   Origin" below.
4. Open a PR using the template in
   `.github/PULL_REQUEST_TEMPLATE.md`.

## What needs discussion first

Changes to shared interfaces affect every downstream community track at
once, so they need a Discussion before a PR, not after:

- `studio/providers/base.py`'s provider interfaces
  (`LLMProvider`/`ImageProvider`/`VideoProvider`/`TTSProvider`)
- `CreativeRunState`'s stage model or the review-gate mechanics in
  `studio/creative/pipeline.py`
- Anything in `studio/core/` that Media Remix also depends on

Everything else — new providers, new community-track features, docs,
tests, bug fixes — can go straight to a PR.

## Developer Certificate of Origin (DCO)

Every commit must be signed off (`git commit -s`), certifying you wrote it
or otherwise have the right to submit it under the project's license, per
the standard [DCO](https://developercertificate.org/) text. This is
lighter-weight than a CLA — no separate agreement to sign, just a
sign-off line in your commit message.

## Review process

- `good first issue` PRs get reviewed fastest — a quick first-contribution
  experience matters more than review-queue ordering.
- Every PR gets a response (approval, requested changes, or "still
  reviewing, thanks for your patience") within a reasonable window; if
  it's been quiet for a while with no response, a bump comment is
  completely fine.
- Review feedback is about the code, not the contributor — see
  [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Recognition

Every merged PR gets you added to [`CONTRIBUTORS.md`](CONTRIBUTORS.md) and
a specific thank-you, not just a silent merge. See
[`GOVERNANCE.md`](GOVERNANCE.md) for how sustained contribution turns into
Trusted Contributor / Reviewer / Maintainer status.
