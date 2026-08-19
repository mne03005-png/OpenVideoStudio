# 72-Hour Launch Plan

Covers the window immediately around public launch. For the strategic
content around it (taglines, launch posts, channel-by-channel plan,
first-week community plan, failure modes), see
`docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`. This document is the timeline.

All of this remains inert until the final gate in
`docs/OPEN_SOURCE_READINESS.md` — **"USER EXPLICITLY APPROVED PUBLIC
LAUNCH"** — is checked. Nothing here authorizes publishing anything.

## T-14 days

- [ ] License decision made (`docs/LICENSE_STRATEGY.md`) and `LICENSE` +
      `CONTRIBUTING.md`'s DCO section finalized
- [ ] Hero demo specification approved (`docs/HERO_DEMO_SPEC.md`)
- [ ] Begin producing hero demo + two secondary demos
- [ ] Issue seed list reviewed and finalized (`docs/ISSUES_SEED.md`)

## T-7 days

- [ ] Hero demo + secondary demos complete, reviewed for the requirements
      checklist in `docs/HERO_DEMO_SPEC.md`
- [ ] README first-screen draft finalized, tagline selected
- [ ] Clean-machine install test #1 (see below) — first pass, expect to
      find gaps
- [ ] Fix gaps found in install test #1

## T-3 days

- [ ] Clean-machine install test #2 — confirm fixes from test #1, target
      the actual <10-minute goal
- [ ] Codex four-perspective review (`docs/OPEN_SOURCE_READINESS.md`)
      requested and CRITICAL/HIGH findings resolved
- [ ] Secret scan re-run against the final candidate state (not just the
      original audit — anything changed since needs re-auditing)
- [ ] GitHub repo created (private first), Issues seeded, Discussions
      categories configured, labels created
- [ ] Sponsorship files prepared but **not activated**
      (`.github/FUNDING.yml` stays without real payment endpoints until
      explicit approval)

## T-1 day

- [ ] Full readiness checklist review (`docs/OPEN_SOURCE_READINESS.md`)
- [ ] README freeze — no further copy changes without re-review
- [ ] Demo freeze — no further asset changes without re-review
- [ ] Launch posts drafted for every planned channel, reviewed for
      overclaiming against `docs/HARDWARE.md`'s actual tested evidence
- [ ] Final human GO/NO-GO decision requested explicitly

## Launch hour

- [ ] Flip repository visibility to public
- [ ] Verify README renders correctly on GitHub (images, badges, links)
- [ ] Verify Issues, Discussions, and labels are all visible and correct
- [ ] Post to the first 1-2 planned channels only (not all channels
      simultaneously — see `docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`'s
      per-channel timing)

## First 6 hours

- [ ] Monitor for anything that slipped through the readiness gate
      (broken install, exposed secret, broken link) — be ready to fix or
      temporarily revert
- [ ] Respond to every comment/question on the launch posts personally
- [ ] Triage any issues opened by early visitors within a few hours, not
      days

## First 24 hours

- [ ] Post to remaining launch channels, staggered per
      `docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`'s timing recommendations
- [ ] Welcome every first-time issue reporter and PR opener personally,
      not with a template-only response
- [ ] Track: stars, forks, issues opened, PRs opened, install failures
      reported

## 48 hours

- [ ] First round of easy PR reviews (good-first-issue PRs especially —
      fast review turnaround matters most for first-time contributors)
- [ ] Address any install-friction reports as priority-one bugs

## 72 hours

- [ ] Retrospective: what broke, what surprised, what needs to change in
      docs/issues/demo before the next wave of visibility (e.g. a second
      HN/Reddit wave)
- [ ] Update `docs/HARDWARE.md` with any new community hardware reports

## First week

See `docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`'s first-week community plan for
response SLAs, contributor recognition, and burnout avoidance.

## Sponsor activation timing

Deliberately **not** in the launch-hour or first-24-hours checklists
above. `.github/FUNDING.yml` stays fully commented out (see
`docs/SPONSORSHIP.md`) through at least the first week — activating
sponsorship before the project has demonstrated it can sustain a
community (responsive triage, merged first PRs, a functioning
Discussions space) reads as asking for money before proving the thing
being funded is real. Reasonable trigger to revisit: after the first
week's retrospective, once there's a real answer to "what would this
funding actually go toward right now" grounded in real triage/maintenance
load rather than a hypothetical.

## Clean-machine install test — what "clean" means

Not the development machine. A separate machine or VM with no
pre-existing Ollama models, no pre-existing ComfyUI checkpoints, and no
Python environment already configured for this project — literally
following `docs/INSTALL.md` from `git clone` forward, timing it, and
recording every point of friction. Any step that isn't in the doc gets
added; any step that's wrong gets fixed. This is the single highest-value
thing to do before launch, because "setup too complicated" and "broken
install" are the top two failure modes (see
`docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`).
