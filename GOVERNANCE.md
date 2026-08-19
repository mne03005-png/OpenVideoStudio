# Governance

OpenVideoStudio is **community-driven, maintainer-led**. Anyone can
contribute; repository permissions and decision-making authority are
earned progressively through sustained, high-quality contribution — they
are never for sale, and a PR by itself never grants control.

## Roles

| Role | Granted by | Can do |
|---|---|---|
| **Contributor** | Anyone with a merged PR | Submit PRs, comment on issues/discussions |
| **Trusted Contributor** | Sustained quality contributions over time, maintainer nomination | Triage issues, apply labels, request changes on PRs (non-binding) |
| **Reviewer** | Demonstrated technical judgment across multiple reviews, maintainer approval | Formally approve PRs; approval + one maintainer sign-off can merge |
| **Maintainer** | Sustained reviewing/merging track record, existing maintainer consensus | Merge PRs directly, manage labels/milestones, triage authority across the whole repo |
| **Core Maintainer / Founder** | Founding role | Final say on disputes, controls official releases, GitHub Organization ownership, branding |

Promotion criteria, explicitly: contribution quality, consistency over
time, review quality (for Reviewer+), technical judgment, community
conduct, and long-term involvement. There's no fixed PR count or time
threshold — this is a judgment call made transparently, not a formula, and
maintainers should be able to explain their reasoning if asked.

## Who can do what

- **Merge PRs**: Maintainers and Core Maintainer, always. Reviewer
  approval plus one Maintainer sign-off can also merge.
- **Review PRs**: anyone can leave review comments; formal (blocking)
  approval requires Reviewer role or above.
- **Triage issues** (labels, milestones, duplicate-closing): Trusted
  Contributor and above.
- **Control official releases**: Maintainers, coordinated by the Core
  Maintainer.
- **Control the GitHub Organization, official branding, domains**: Core
  Maintainer only — see "Brand control" below.

## Technical disputes

Default to discussion in the relevant GitHub Discussion or PR thread.
Escalation path: Reviewers weigh in → Maintainers decide by rough
consensus → Core Maintainer breaks ties if consensus doesn't form. This is
meant to almost never be needed — most technical disagreements resolve
through normal review.

## Brand control

**Code rights** and **official brand rights** are deliberately separate:

- Anyone may fork the code under its license (see
  `docs/LICENSE_STRATEGY.md`) and do what the license permits.
- The **OpenVideoStudio name, official logo, official website, official
  releases, official builds, and official distribution channels** are
  controlled by the Core Maintainer / project organization, separately
  from the code license. A fork is free to exist; it isn't free to
  present itself as "the official OpenVideoStudio" without permission.

Final trademark/legal specifics are not settled by this document and
require actual legal review before any enforcement action — this section
states the intended principle, not a legal claim.

## Sponsors do not buy governance

Financial sponsorship (see `SUPPORT.md` and `.github/FUNDING.yml`) never
grants review rights, merge rights, roadmap control, or any role listed
above. A sponsor's influence is limited to what any community member's
influence is: making a case in a Discussion or issue.

## Changing this document

Governance changes go through a Discussion (Announcements or Ideas
category) with visible community input before the Core Maintainer finalizes
them — governance shouldn't change silently in a routine PR.
