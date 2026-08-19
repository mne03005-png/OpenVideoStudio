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
- [ ] License selected — **NOT DECIDED**, see `docs/LICENSE_STRATEGY.md`;
      recommendation given (Apache-2.0 + DCO), awaiting explicit user
      approval. The README headline reads "open source in progress"
      rather than an unqualified claim, specifically because no license
      currently exists.
- [x] README/README_CN ready (draft) — headline, local-by-default
      disclosure, provider-selection claim, Quick Mode description, and
      License section all verified against actual current code behavior,
      not just written and assumed correct. Still drafts pending the hero
      demo.
- [ ] Hero demo ready — **spec only**, no assets generated yet
      (`docs/HERO_DEMO_SPEC.md`), by design, pending approval
- [x] Install guide written and verified against a fresh copy of the
      repository, including: `.env` values actually reach the code,
      `pip install -r requirements.txt` completes without error, every
      documented path resolves without nesting errors, and the three
      large model downloads point at sources independently confirmed to
      host the exact filenames the code requires
- [ ] Clean-machine test — verified against fresh *copies* of this
      repository multiple times (see above); a fully clean machine/VM
      with no pre-existing Python/tooling at all, per
      `docs/LAUNCH_72H_PLAN.md`, is still outstanding
- [x] Tests green — full suite passes in the current working tree (run
      `cd studio && python -m pytest tests/ -q` to verify the current
      count yourself rather than trusting a number written here)
- [x] Media Remix regression-safe — unmodified except comment edits and
      one UI label addition; its own tests still pass
- [ ] 30+ Issues ready — drafted in `docs/ISSUES_SEED.md` (verify the
      actual count by reading the file — it has previously been
      mis-stated in this checklist), not yet created as real GitHub
      issues (repo isn't public/created yet)
- [x] Good first issues ready — each with full spec (problem, why it
      matters, relevant files, expected result, acceptance criteria, how
      to test)
- [x] Help wanted issues ready
- [x] Governance ready — `GOVERNANCE.md`
- [x] Contributing guide ready — `CONTRIBUTING.md`
- [x] Security policy ready — `SECURITY.md`
- [x] Roadmap ready — `ROADMAP.md`, verified against actual shipped
      behavior (not overstating what's automated vs. manual)
- [x] Sponsorship structure prepared — `.github/FUNDING.yml` prepared,
      deliberately **not activated**
- [x] CI/branch/tooling consistency — branch name, CI triggers, and
      CONTRIBUTING's instructions verified to actually agree with each
      other; third-party CI Actions pinned to a real release, not a
      floating branch
- [ ] Launch posts drafted — channel-by-channel plan and title candidates
      exist in `docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`, verified against the
      same accuracy bar as README (a launch post title is a public claim
      too); full post copy not yet written
- [ ] **USER EXPLICITLY APPROVED PUBLIC LAUNCH** — **not given.** Without
      this, nothing gets published, regardless of every other item's
      status.

## Independent review

This candidate has been reviewed multiple times by an independent
reviewer with no access to this document's claims in advance, specifically
including review of this document's and the security audit's own
accuracy, not just the code. That process has repeatedly found real
issues in what looked like a finished draft — including issues in this
checklist itself. Given that track record, the honest position is: this
document reflects genuine verification at the time it was last updated,
not a guarantee that a further independent pass would find nothing. A
final independent pass with no open findings, immediately before
requesting the user's launch decision, is the actual bar — not this
document's state at any earlier point.

## What "GO" actually authorizes

Even a fully-checked list above does **not** itself authorize publishing.
The final item — explicit user approval — is a separate, deliberate act,
not something that becomes true by the other items being true.
