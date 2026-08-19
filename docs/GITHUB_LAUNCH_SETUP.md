# GitHub Launch Setup

Exact, ordered actions to take **once the user has explicitly approved
public launch** — this document is the runbook, not something to execute
preemptively. Nothing in this document has been done yet; it's written so
launch day is mechanical, not improvised.

## 0. Immediately before running any of this

- [ ] Confirm the explicit approval was actually given (see
      `docs/OPEN_SOURCE_READINESS.md`'s final gate)
- [ ] Re-run `cd studio && python -m pytest tests/ -q` one last time
- [ ] Re-run the security/privacy scan one last time (see
      `docs/OPEN_SOURCE_SECURITY_AUDIT.md`) against whatever the tree
      looks like at that moment — not this document's snapshot of it
- [ ] Confirm `LICENSE` and `NOTICE` are present and correct

## 1. Create the repository

- **Name:** `OpenVideoStudio`
- **Owner:** the GitHub organization or account that will hold official
  governance (see `GOVERNANCE.md`'s "Brand control" — decide this
  explicitly, don't default to a personal account if an organization is
  intended long-term, since migrating owners later is disruptive)
- **Visibility:** start **private**, flip to public only after the
  checklist below is complete inside the real repo (labels, branch
  protection, Discussions) — flipping visibility is instant; fixing a
  misconfigured public repo in front of an audience is not
- **Default branch:** `main` (already what the local candidate uses)
- **Description:** the README tagline — "A local-first, Apache-2.0-licensed
  AI video creation studio."
- **Topics:** `ai-video`, `video-generation`, `comfyui`, `ollama`,
  `sdxl`, `text-to-video`, `open-source`

```bash
gh repo create ORG/OpenVideoStudio --private --description "A local-first, Apache-2.0-licensed AI video creation studio."
```

## 2. Push the candidate

```bash
cd D:\OpenVideoStudio
git remote add origin https://github.com/ORG/OpenVideoStudio.git
git push -u origin main
```

This is the **first irreversible-feeling step** in the sequence — even
though the repo is still private, code now exists outside this machine.
Confirm the GO approval covers this, not just the final public flip.

## 2b. Replace the `OWNER` placeholder

`.github/ISSUE_TEMPLATE/config.yml` has two URLs hardcoded to
`github.com/OWNER/OpenVideoStudio` — a placeholder, not a real link.
Replace `OWNER` with the actual org/account chosen in Step 1 before the
repo goes public; otherwise the "Usage question" and "Security
vulnerability" contact links in the Issues UI 404.

## 3. Labels

Create every label `docs/ISSUES_SEED.md` and the issue templates
reference, before filing any issues:

```
good first issue, help wanted, research, provider, art-studio,
character-consistency, model-gateway, enterprise, comfyui, ui, video,
audio, testing, documentation, windows, linux, macos, performance,
security
```

`gh label create NAME --color HEX --description "..."` per label, or use
GitHub's UI. Keep `good first issue`/`help wanted` matching GitHub's own
default color convention (contributors recognize the standard green/purple)
so they're visually familiar to first-time visitors.

## 4. Branch protection

On `main`: require PR review before merge (per `GOVERNANCE.md` — direct
pushes bypass the review process the docs promise), require the CI
workflow to pass, do not allow force-push.

## 5. Discussions

Enable Discussions. Categories, per `docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`:

```
Announcements, Ideas, Show and Tell, Model Providers, AI Art, Research,
Help, General
```

Post one pinned "Welcome" announcement linking `README.md`,
`CONTRIBUTING.md`, and the track selector.

## 6. Seed the issues

Run the parser script against the now-real repo:

```bash
python scripts/create_github_issues.py --repo ORG/OpenVideoStudio --execute
```

This reads `docs/ISSUES_SEED.md` directly (see the script's own docstring)
and files all 43 issues with their labels. Spot-check the first few in
the GitHub UI before assuming the rest went cleanly.

## 7. Release tag and notes

**Tag:** `v0.1.0-alpha` — matches `ROADMAP.md`'s existing version scheme
(v0.1-alpha → v0.2 → v0.3, now public).

**Draft release notes:**

> ## OpenVideoStudio v0.1.0-alpha
>
> First public release. Prompt → script → storyboard → character/
> environment identity → keyframes → video clips → narration → subtitles
> → automated edit → final video, running on local models (Ollama +
> ComfyUI) with one disclosed exception (default narration uses Edge
> TTS). See `docs/HARDWARE.md` for exactly what's verified.
>
> This is an **alpha**: the core pipeline is tested and reviewed, but
> Pro Mode, most community tracks, and broad platform support are not
> built yet — see `ROADMAP.md` and `docs/COMMUNITY_TRACKS.md` for what's
> shipped vs. what's an open contribution opportunity.
>
> Full install guide: `docs/INSTALL.md`. Want to contribute? Start at
> `docs/ISSUES_SEED.md`.

Do not mark this a "Latest Release" until the hero demo is embedded in
the README that ships with the tag — a release without its own headline
demo undersells the tag.

## 8. FUNDING.yml — still not activated

Pushing the repo does **not** activate sponsorship. `.github/FUNDING.yml`
ships with every line commented out; activating it is a separate,
later decision — see `docs/LAUNCH_72H_PLAN.md`'s timing guidance and
Part 9 of the original launch-prep brief. Do not uncomment it as part of
this setup sequence.

## 9. Flip to public

Only after steps 1–8 are verified against the real repo (not assumed from
this document). Settings → General → Danger Zone → Change visibility.

## 10. Immediately after going public

- [ ] Verify the README renders correctly on GitHub (images, badges,
      internal links — GitHub's Markdown renderer has small differences
      from a local preview)
- [ ] Verify all 43 issues are visible and correctly labeled
- [ ] Verify Discussions categories are visible
- [ ] Post the first launch content (see
      `docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`) — per
      `docs/LAUNCH_72H_PLAN.md`'s timing, not all channels at once

## What this document does not authorize

Completing every step above still requires the explicit human GO from
`docs/OPEN_SOURCE_READINESS.md`'s final gate before step 1 begins. This
document being finished and accurate is preparation, not permission.
