# Open-Source Readiness Gate

Objective GO/NO-GO checklist. **Launch cannot proceed until every
mandatory item passes — no exceptions, and the final item cannot be
satisfied by anyone but the user.**

This checklist reflects the repository's current state, verified by
direct inspection at the time it was last updated — check the items
yourself against the actual repository rather than trusting the dates
here, since this document has previously gone stale between updates.

## Checklist

- [x] Core pipeline verified — independently reviewed and cleared in the
      private development history this candidate is built from
- [x] No unresolved CRITICAL/HIGH in the reviewed source — this
      candidate's own preparation has been through multiple rounds of
      independent review that found and required fixing real issues each
      time (install flow, overclaimed positioning, self-leaking audit
      docs, hardcoded config that should have been config-driven,
      documentation defects); the current working tree reflects all
      fixes made so far. Whether a *further* round finds something new is
      not something this checklist can promise in advance — see
      "Independent review," below.
- [x] Clean public candidate repo — built by selective copy, not a
      history export; no private identifiers in tracked files or commit
      history (verified directly against `git log`)
- [x] License selected — **Apache-2.0 + DCO**, see
      `docs/LICENSE_STRATEGY.md`. `LICENSE` (verbatim canonical text,
      fetched directly rather than reproduced from memory) and `NOTICE`
      are both in the repository root. README/README_CN updated to
      reflect the decision.
- [x] README/README_CN ready (draft) — headline, local-by-default
      disclosure, provider-selection claim, Quick Mode description, and
      License section all verified against actual current code behavior,
      not just written and assumed correct. Still drafts pending the hero
      demo.
- [x] Hero demo ready — real, unedited pipeline run in
      `examples/hero_demo/` (32.9s final video + compact preview GIF
      embedded in both READMEs), full requirements checklist verified
      against the actual output in `docs/HERO_DEMO_SPEC.md`, including an
      honestly disclosed QC judgment call (one scene regenerated via the
      pipeline's real scene-regeneration mechanism, not hand-edited).
      Two secondary demos remain spec-only — real, scoped, not generated.
- [x] Install guide written and verified against a fresh copy of the
      repository, including: `.env` values actually reach the code,
      `pip install -r requirements.txt` completes without error, every
      documented path resolves without nesting errors, and the three
      large model downloads point at sources independently confirmed to
      host the exact filenames the code requires
- [~] Clean-machine test — strongest practical version done: an isolated
      fresh Python venv plus a fresh repository copy, every documented
      step verified including a path-with-spaces case and a full
      subprocess-quoting audit (`docs/CLEAN_INSTALL_VALIDATION.md`). A
      fully clean machine/VM with none of this host's pre-installed tools
      (FFmpeg, Ollama, ComfyUI) at all is the one item that document is
      explicit it did **not** cover — genuinely outstanding, not just
      unchecked for form's sake.
- [x] Tests green — full suite passes in the current working tree (run
      `cd studio && python -m pytest tests/ -q` to verify the current
      count yourself rather than trusting a number written here)
- [x] Media Remix regression-safe — unmodified except comment edits and
      one UI label addition; its own tests still pass
- [x] 30+ Issues ready — 43 drafted in `docs/ISSUES_SEED.md` (verify by
      reading the file directly — its own count line has previously been
      wrong and was fixed by actually counting). A parser/filer script
      (`scripts/create_github_issues.py`) reads that file directly and is
      ready to run once a real repo exists — dry-run tested, confirmed to
      parse all 43 correctly; not yet executed against a real repo
      (none exists yet)
- [x] Good first issues ready — each with full spec (problem, why it
      matters, relevant files, expected result, acceptance criteria, how
      to test)
- [x] Help wanted issues ready
- [x] Governance ready — `GOVERNANCE.md`
- [x] Contributing guide ready — `CONTRIBUTING.md`
- [x] Security policy ready — `SECURITY.md`
- [x] Roadmap ready — `ROADMAP.md`, verified against actual shipped
      behavior (not overstating what's automated vs. manual)
- [x] Sponsorship structure prepared — full tier proposal, funding-use
      explanation, and ready-to-paste README copy in
      `docs/SPONSORSHIP.md`; `.github/FUNDING.yml` prepared, deliberately
      **not activated**; `docs/LAUNCH_72H_PLAN.md` states explicit timing
      (not launch day — after the first week's retrospective)
- [x] CI/branch/tooling consistency — branch name, CI triggers, and
      CONTRIBUTING's instructions verified to actually agree with each
      other; third-party CI Actions pinned to a real release, not a
      floating branch
- [x] Launch posts drafted — full copy (title, opening paragraph, short
      version, CTA) for all 9 planned channels in `docs/LAUNCH_CONTENT.md`,
      every one held to the same accuracy bar as the README headline (no
      unqualified "runs locally," no unqualified "open source" claims
      independent of the actual license/local-dependency status)
- [ ] **USER EXPLICITLY APPROVED PUBLIC LAUNCH** — **not given.** Without
      this, nothing gets published, regardless of every other item's
      status.

## Independent review

This candidate has been reviewed multiple times by an independent
reviewer, who reads what this project's status notes claim and then
independently re-derives every claim against the actual repository
rather than accepting the narrative — specifically including review of
this document's and the security audit's own accuracy, not just the
code. That process has repeatedly found real issues in what looked like
a finished draft — including issues in this checklist itself. Given that
track record, the honest position is: this
document reflects genuine verification at the time it was last updated,
not a guarantee that a further independent pass would find nothing. A
final independent pass with no open findings, immediately before
requesting the user's launch decision, is the actual bar — not this
document's state at any earlier point.

## What "GO" actually authorizes

Even a fully-checked list above does **not** itself authorize publishing.
The final item — explicit user approval — is a separate, deliberate act,
not something that becomes true by the other items being true.
