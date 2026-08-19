# Sponsorship

**Status: structure prepared, nothing activated.** No payment platform is
connected; `.github/FUNDING.yml` ships with every line commented out.
Activating any of this is a separate, explicit decision — see
`docs/LAUNCH_72H_PLAN.md` for suggested timing (after launch has
stabilized, not on day one) and `docs/OPEN_SOURCE_READINESS.md` for the
gate.

## Why sponsor

OpenVideoStudio's core promise — a real, tested, locally-run AI video
pipeline — has real costs behind it that a purely volunteer maintainer
model strains under: GPU time for testing across hardware configurations,
CI minutes, keeping pace with a fast-moving model ecosystem, and the
unglamorous ongoing work of documentation and community maintenance.
Sponsorship funds that work directly; it does not buy any say in it.

## What sponsorship funds

- **GPU testing** — verifying claims in `docs/HARDWARE.md` against
  hardware beyond the maintainer's own, instead of leaving that entirely
  to community reports
- **CI** — GitHub Actions minutes, and eventually paid runners if
  matrix testing (Section on Platform Support) grows beyond free-tier
  limits
- **Model integration** — the real time cost of evaluating and wiring in
  new providers (Track B/D) rather than only accepting whatever a
  contributor happens to submit
- **Platform testing** — Linux/macOS/Apple Silicon verification (Track E)
  that the maintainer's own Windows-only dev setup can't self-certify
- **Documentation** — keeping install guides, hardware claims, and
  community-track docs honest and current, which is real, recurring work
- **Community maintenance** — issue triage, PR review turnaround, and
  the first-week response commitments in
  `docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`

## Proposed tiers

Deliberately **not** priced here — setting actual dollar amounts is a
business decision for whoever activates this, informed by what
comparable projects' tiers look like at activation time, not fixed months
in advance in a planning document. What's fixed is the tier *shape* and
what each level of relationship looks like:

| Tier | Who it's for | What sponsors get |
|---|---|---|
| **Supporter** | Individuals who use the project and want to say thanks | Name/handle listed in a sponsors section (opt-in) |
| **Contributor Supporter** | Individuals who both contribute code/docs *and* sponsor | Same recognition as Supporter — contribution and sponsorship are tracked and credited separately, never combined into extra influence |
| **Project Sponsor** | Small companies/teams using OpenVideoStudio, who want to fund its continued development | Logo/name on the README's sponsors section, priority (not exclusive) attention on issues they report |
| **Organization Sponsor** | Larger companies/institutions with a sustained interest (e.g. building on the Model Gateway track for internal deployment) | Same as Project Sponsor, plus a direct line to discuss roadmap *input* — explicitly not roadmap *control*, see below |

## What sponsorship never buys

Stated once in `GOVERNANCE.md` and repeated here because it's the part
most likely to be tested in practice:

- **No merge rights for money.** Sponsoring the project doesn't move
  anyone up `GOVERNANCE.md`'s Contributor → Trusted Contributor →
  Reviewer → Maintainer path — that's earned through contribution, full
  stop.
- **No maintainer status for money.**
- **No roadmap control for money.** A sponsor can advocate for a
  direction the same way any community member can — in a public
  Discussion, on its merits — not through a side channel their sponsorship
  opens.

If a sponsor ever expects influence beyond what's listed above, that
expectation should be corrected explicitly and early, not allowed to
quietly shape decisions.

## README support section (ready to add at activation)

The following is drafted and ready to paste into `README.md` once
sponsorship is actually activated — not added yet, since an inactive
"Sponsor" link/button in a README reads worse than no section at all:

> ## Support OpenVideoStudio
>
> If this project is useful to you, consider supporting its development.
> Sponsorship funds GPU testing, CI, and ongoing maintenance — it never
> buys governance or roadmap control (see `GOVERNANCE.md`). See
> `docs/SPONSORSHIP.md` for tiers and where the funding goes.
>
> [Become a sponsor](#) *(link added at activation)*
