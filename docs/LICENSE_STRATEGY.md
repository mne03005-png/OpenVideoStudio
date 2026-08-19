# License Strategy

**Status: DECIDED.** Apache-2.0 + DCO, per the recommendation below. The
`LICENSE` and `NOTICE` files are in place in the candidate repository.
MIT remains the documented fallback if this decision is revisited before
launch. This still does not authorize publishing the repository —
that's a separate, later gate (see `docs/OPEN_SOURCE_READINESS.md`).

## What we're optimizing for

From the project goals: open development, real community participation
(users, forks, contributors, companies), founder/project governance
protection, and the future option of commercial offerings (hosted service,
enterprise support) without giving that up by accident.

## Options compared

### MIT

- **Contributor friendliness**: highest. Nearly zero-friction for
  contributors and adopters to reason about.
- **Commercial use**: unrestricted, including closed-source derivatives
  and SaaS.
- **Forks**: anyone can fork and relicense a derivative as they wish
  (within MIT's terms).
- **Patents**: no explicit patent grant or defense clause.
- **SaaS use**: a competitor could take the code, host it as a paid
  service, and owe the project nothing — no "give back" requirement.
- **Company adoption**: highest — many companies default to MIT-only
  dependency policies.
- **Future dual licensing**: possible but the community edition itself
  offers no leverage — anyone can already do anything with it.
- **Ecosystem impact**: maximizes reuse and adoption; weakest at ensuring
  contributions flow back.

### Apache-2.0

- **Contributor friendliness**: high, slightly more legal text than MIT
  but well understood.
- **Commercial use**: unrestricted, same as MIT.
- **Forks**: same freedom as MIT.
- **Patents**: explicit patent grant *and* a defensive termination clause
  (if you sue over patents, you lose your license) — meaningfully better
  protection for a project that may attract corporate contributors with
  patent portfolios (relevant given this project sits adjacent to
  ComfyUI/AI-model tooling, where patent risk is non-zero).
  **This is Apache-2.0's main practical advantage over MIT for this
  project.**
- **SaaS use**: same as MIT — no reciprocity requirement.
  **Company adoption**: as high as MIT, often preferred by larger
  companies specifically because of the patent clause.
- **Future dual licensing**: same limitation as MIT.
- **Ecosystem impact**: similar to MIT with better legal safety for
  contributors and adopters.

### GPLv3

- **Contributor friendliness**: moderate — copyleft is a known
  friction point for some contributors and companies.
- **Commercial use**: allowed, but any distributed derivative must also
  be GPLv3 and its source made available — no closed-source forks.
- **Forks**: must stay open under GPLv3 if distributed.
- **Patents**: includes a patent grant similar to Apache-2.0.
- **SaaS use**: **GPLv3's copyleft does NOT trigger on network use** — a
  company can run a privately modified GPLv3 fork as a SaaS product and
  never publish the changes. This is the well-known "SaaS loophole" GPLv3
  does not close (AGPL exists specifically to close it — see below).
- **Company adoption**: significantly lower — many companies' legal teams
  restrict or forbid GPL dependencies, especially for anything that might
  get linked into internal tooling.
- **Future dual licensing**: GPL is actually the license family most
  commonly used as the "free" side of an open-core dual-license model,
  because the copyleft creates real incentive for companies to pay for a
  commercial license instead of complying with GPL's source-disclosure
  terms. This is a genuine strategic option if a future paid/enterprise
  tier is likely.
- **Ecosystem impact**: attracts a community that values software freedom
  strongly; repels some corporate contributors and integrators.

### AGPLv3

- Same as GPLv3, **plus** the copyleft explicitly extends to network use
  (SaaS) — anyone running a modified AGPLv3 version as a network service
  must make their source available to users of that service.
- **Commercial use**: allowed, but this is the strongest deterrent of the
  four options against a well-funded competitor standing up a hosted
  "OpenVideoStudio Cloud" without contributing back.
- **Company adoption**: lowest of the four — AGPL is the license most
  commonly blocked outright by corporate legal/compliance policies,
  specifically because of the network-copyleft clause. This directly
  conflicts with the stated goal of attracting "companies and
  institutions."
- **Future dual licensing**: the strongest lever of the four for a future
  open-core/commercial-license split, for the same reason it repels casual
  corporate adoption — that tension is a deliberate tradeoff, not a bug.

## Contributor agreement comparison

- **CLA (Contributor License Agreement)**: gives the project (or a
  foundation/company behind it) broad rights over contributions, including
  the ability to relicense later (e.g., for a future dual-license
  commercial tier). Friction: many contributors, especially individuals,
  are wary of signing CLAs; it's an extra step before a first PR can be
  reviewed at all, which cuts against the "meaningful contribution within
  10 minutes" goal.
- **DCO (Developer Certificate of Origin)**: a lightweight `git commit -s`
  sign-off certifying the contributor has the right to submit the code,
  with no rights transfer and no separate agreement to sign. Standard in
  large, healthy open-source projects (Linux kernel, Docker, many CNCF
  projects). Much lower friction than a CLA while still documenting
  provenance.
- **No agreement**: zero friction, but leaves no documented trail if a
  licensing question or dispute ever arises, and forecloses any future
  relicensing that would need contributor consent.

## Recommendation

1. **License: Apache-2.0.** It gets nearly all of MIT's adoption-friendliness
   and community growth while adding real patent protection, which matters
   for a project integrating with a fast-moving, patent-adjacent AI/model
   ecosystem. GPLv3/AGPLv3's copyleft would work against the explicit goal
   of attracting companies and institutions as users and contributors,
   and this project's monetization path (if any) is more plausibly hosted
   services/support/sponsorship than "sell a proprietary fork," which
   Apache-2.0 doesn't block anyway — a permissive license doesn't stop the
   project itself from also offering a paid hosted version later.
2. **Contributor agreement: DCO**, not a CLA. Keeps the "first PR in
   under 10 minutes" goal intact while still documenting provenance.
   Revisit only if a future commercial/dual-license tier becomes concrete
   enough to need CLA-level rights.
3. Do **not** select AGPLv3 given the explicit target audience includes
   companies/institutions — AGPL is the single biggest deterrent to
   corporate adoption of the four options compared.

## Decision

**Apache-2.0, with DCO for contributor sign-off.** Apache-2.0 vs. MIT
came down to how much weight to put on patent protection vs. absolute
simplicity — patent protection won given this project's proximity to
fast-moving, patent-adjacent AI/model tooling. `LICENSE` (the verbatim
Apache License 2.0 text) and `NOTICE` (the copyright/attribution
statement, held by "OpenVideoStudio Contributors" rather than a single
named individual, matching common practice for community-owned projects)
are both in the candidate repository root. `CONTRIBUTING.md`'s DCO
sign-off requirement was already in place before this decision.

**MIT remains the documented fallback** if this decision needs revisiting
before the repository is actually made public — swapping `LICENSE`'s text
is a low-cost, low-risk change at that point, and this document's MIT
comparison above stays accurate either way.

## A license does not protect the brand

Choosing Apache-2.0 governs the *code* — copying, modifying,
redistributing, using it commercially. It says nothing about who gets to
call their fork "OpenVideoStudio," use its name or logo, or claim to be
the official project. That's handled separately, deliberately not by the
license:

- The **OpenVideoStudio name, logo, official builds, official website,
  and official release channels** stay under the Core Maintainer /
  project organization's control — see `GOVERNANCE.md`'s "Brand control"
  section.
- **Organization ownership** (the eventual GitHub organization, domain,
  and any registered trademark) is a separate, explicit decision at
  launch time — see `docs/GITHUB_LAUNCH_SETUP.md`.
- Anyone may fork the *code* under Apache-2.0's terms. They may not
  present that fork as the official OpenVideoStudio project without
  separate permission.

**Legal uncertainty, marked plainly:** nothing above constitutes a formal
trademark registration or legal opinion. "Preserving" the name/logo/brand
today means asserting and documenting the intent, plus normal
first-use/common-law protections that come from actually using the name
publicly — it does not mean a registered trademark exists. If brand
protection ever needs to be enforced against a bad-faith fork, that
requires actual legal review at the time, not just this document.
