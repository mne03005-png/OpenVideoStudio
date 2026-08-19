# Open-Source Launch Strategy

## Positioning

**OpenVideoStudio** — a local-first AI video creation studio, free to
use, open source in progress. (Not "Free & Open-Source" unqualified as
the headline claim — an earlier draft of this exact document used that
phrasing in three different places, and two independent review rounds
caught it as inaccurate at the point a reader first sees it: no
`LICENSE` currently exists, and default narration isn't local. See
`README.md`'s actual current headline, which this document should always
match, not just describe.)

Core workflow: Prompt → Script → Storyboard → Character/Environment
continuity → Keyframes → AI video clips → Voice → Subtitles → Audio →
Automated editing → Final video.

Differentiators, each backed by something real in the current codebase
(no aspirational claims mixed in with what exists — an earlier draft of
this exact list got two of these wrong, caught in independent review; see
`docs/OPEN_SOURCE_SECURITY_AUDIT.md`'s note on that):
- Free and open source in intent (License section is honest about where
  that actually stands — see `docs/LICENSE_STRATEGY.md`)
- Local-first, with one disclosed exception: script/storyboard/identity/
  keyframes/clips are all local (Ollama + ComfyUI); default narration
  (Edge TTS) is not — see `README.md`'s "Local by default" section
- Consumer-GPU friendly (verified on 6GB — see `docs/HARDWARE.md`;
  NVENC-only encode today, no CPU/other-vendor fallback)
- Provider selection is config-driven, not hardcoded (`config.toml`'s
  `[providers]` section actually controls which provider class runs —
  fixed during open-source prep after independent review caught it was
  previously hardcoded despite the config section implying otherwise)
- ComfyUI-compatible (built on it directly, not a competing engine)
- Resumable generation (`CreativeRunState`'s stage model, already
  shipping); *targeted* per-scene regeneration is possible today by
  editing a run's storyboard.json and using `force=True` — real, but not
  a polished UI feature yet (Track F)
- Automated video QC (freeze/motion detection, schema validation,
  narrative-quality warnings, all shipping; final-assembled-video QC and
  duplicate-shot/audio QC are not — Track G)
- One mandatory human review gate before generation continues past the
  storyboard (already enforced) — Quick Mode is "mostly automatic," not
  fully zero-touch, by design
- Quick Mode now (the current single-pipeline flow, with the one review
  gate above); Pro Mode is roadmap, not shipped — must be labeled as such
  everywhere it's mentioned

## Candidate taglines (ranked, then corrected after review)

1. ~~**"Free & open-source AI video creation studio."**~~ — Originally
   ranked #1 and recommended. **Rejected after two independent review
   rounds**: unqualified at the point a first-time reader sees it, before
   any caveat about the missing `LICENSE` or the default cloud TTS
   dependency. Keyword-dense and plain, but accuracy at first read wins
   over keyword density.
2. **"From one prompt to a complete video — locally."** — Also corrected:
   "locally" unqualified has the same problem as #1 (narration isn't
   local by default). The actual shipped headline (below) keeps this
   line's workflow-breadth framing but qualifies the local claim.
3. **"Local models. Your models. One video workflow."** — Good for a
   technical audience (ComfyUI/self-hosting crowd) but reads oddly to a
   first-time visitor who doesn't yet know why "your models" matters.
   Better as a secondary line under the primary tagline than as the
   headline itself.
4. **"Build AI videos without locking yourself to one provider."** —
   Accurately describes the provider-abstraction architecture, but leads
   with an anti-lock-in pitch before establishing what the product even
   does — too abstract for a first-time visitor's first line.
5. **"An open-source AI video studio that runs on a 6GB laptop GPU."** —
   Compelling and concrete, but should not be the *headline* tagline: it's
   a hardware claim that needs `docs/HARDWARE.md`'s evidence immediately
   next to it, and over-indexing the README's first line on one specific
   GPU risks reading as narrower than the project actually is. Strong as
   a supporting line or as the hook for launch posts specifically (see
   below), not as the permanent README tagline. Also needs the same
   "open source in progress" qualification as #1 if ever used as a
   full sentence, not just a hardware hook fragment.

**What's actually shipped (`README.md`/`README_CN.md`'s real headline):**
*"A local-first AI video creation studio — free to use, open source in
progress."* with subhead *"From one prompt to a complete video — most of
it never leaves your machine."* and an inline note, directly under the
headline (not scrolled past), naming both qualifications (no `LICENSE`
yet, one cloud TTS dependency) instead of only disclosing them later.
Tagline #5's hardware hook remains reserved for launch post titles
specifically, where `docs/HARDWARE.md`'s evidence sits right next to the
claim.

## README first-30-seconds structure

1. Name/logo
2. Headline + subhead + inline qualification note (see above — the note
   is part of the first screen, not an afterthought)
3. Hero demo (see `docs/HERO_DEMO_SPEC.md`)
4. Key value proposition (3-5 bullet differentiators, from the list above)
5. "Try it" — link straight to `docs/INSTALL.md`
6. "Contribute" — the track-selection CTA (see below)
7. Core workflow diagram/list

No architecture diagrams, no long prose, no "why we built this" essay
above the fold — all of that belongs further down or in `docs/`.

## README contribution CTA

A visible, early section:

> ### Want to help build OpenVideoStudio?
>
> 🎨 [AI Art Studio](...) · 🧑 [Character Consistency](...) ·
> 🔌 [Model Gateway](...) · 🎬 [Video Models](...) ·
> 🎞 [Timeline Editor](...) · 🧪 [QA](...) · 🐧 [Linux](...) ·
> 🍎 [macOS](...) · 🌍 [Translation](...) · 📚 [Documentation](...)

Each link goes to a GitHub Issues search filtered by that track's label
(see `docs/ISSUES_SEED.md` for the label scheme) — not to
`docs/COMMUNITY_TRACKS.md` directly, since the goal is "find something to
click on and start," and an issue list is more actionable on first visit
than a strategy document.

## Launch channels

| Channel | Audience | Title (candidate) | Structure | CTA | Timing |
|---|---|---|---|---|---|
| GitHub (repo itself) | everyone, always the anchor | n/a — the README is the pitch | n/a | Star, try, contribute | Live from hour 0 |
| Hacker News | technical, skeptical, allergic to hype | "Show HN: OpenVideoStudio – a local-first AI video studio that runs on a 6GB GPU" | one paragraph: what it does, what's real (link `docs/HARDWARE.md`), the one cloud dependency (narration) disclosed up front, what's not built yet; link straight to repo | implicit (HN doesn't want a hard CTA) | Weekday, US morning (Show HN performs best when the poster is present to answer for several hours) |
| Reddit (r/StableDiffusion, r/LocalLLaMA, r/opensource) | practitioners already running local AI models | subreddit-specific — lead with the technical stack for r/StableDiffusion (SDXL Lightning + LTX-Video + ComfyUI), lead with the local/self-hosted angle for r/LocalLLaMA (this audience will ask about the TTS network call unprompted if it isn't disclosed — disclose it) | short post, demo embedded, link to repo, explicit ask for feedback and contributors | 24-48h after HN, so there's already visible traction to point to | Separate posts per subreddit, not one crossposted |
| X | broad tech audience, AI-interested | "I built a local-first AI video studio that runs on a 6GB RTX 3060 — looking for contributors" | thread: hook, embedded demo clip, 3-4 bullet differentiators, repo link, explicit "help wanted" call | Day 1, same day as HN | |
| YouTube | broader/less technical, higher production-value expectation | a longer-form (2-4 min) walkthrough beyond the README's short demo | actual screen recording of a real run, narrated | Week 1, not launch day (needs more production time than the hero demo) | |
| Bilibili | Chinese-speaking developer/creator audience | 我在一台 6GB 显存 RTX 3060 笔记本上做了一个本地优先的 AI 视频工作室，准备让全球开发者一起完善 | mirrors the YouTube video, Chinese narration/subtitles, links `README_CN.md` | Same week as YouTube | |
| V2EX | Chinese technical community, high signal, low tolerance for hype | plain technical writeup, mirrors the HN framing | Same week | |
| Zhihu | Chinese Q&A/long-form, good for explaining the "why" | longer explainer post, can afford more narrative than HN/V2EX | Week 1-2 | |
| Juejin | Chinese developer community, more implementation-focused | technical deep-dive (architecture, provider abstraction) | Week 1-2 | |

**Candidate English title** (for HN/X/Reddit): "I built a local-first AI
video studio that runs on a 6GB RTX 3060 — looking for contributors."
(Originally drafted as "an open-source AI video studio that runs locally"
— corrected after review: "open-source" isn't true until a `LICENSE`
exists, and "runs locally" unqualified omits the default cloud TTS
dependency. "Local-first" is accurate either way.)

**Candidate Chinese title** (for Bilibili/V2EX/Zhihu): "我在一台 6GB 显存
RTX 3060 笔记本上做了一个本地优先的 AI 视频工作室，准备让全球开发者一起
完善。"（同样的修正：不再使用"开源"和"完全本地运行"这类未加限定的说法。）

Both are honest (backed by `docs/HARDWARE.md` and `README.md`'s actual
disclosures) and both lead with the contributor ask, not just "look what
I built" — matching the actual goal (community, not just downloads).

## Human + AI development story

This project was built by a human developer working with Claude
(implementation) and an independent Codex review process (QA) — visible
directly in the commit history and, if the coordination logs are ever
referenced publicly, in how thoroughly issues got caught and fixed (e.g.
the V0.3 semantic-validation defect Codex found and Claude fixed before
any commit landed).

**Recommendation: mention it, but as a footnote, not the hook.** A line
like *"Built with humans + AI agents — see the commit history"* belongs in
`CONTRIBUTING.md` or a `docs/` page about the development process, not in
the README's first screen. The product has to earn interest on its own
merits (a real local video pipeline, working on modest hardware, genuinely
open architecture) — leading with "AI wrote this" invites skepticism about
code quality before a visitor has seen any evidence otherwise, and
distracts from the actual differentiators. Once someone is already
interested, the development story is a *plus* (transparent process, real
independent review), not a liability — so it belongs one click deeper, not
on the first screen.

## First-week community plan

- **Response SLA**: every new issue gets a maintainer response (even just
  "thanks, looking into it") within 24 hours for the first two weeks —
  slower than that reads as an abandoned project to a first-time visitor.
- **PR review speed**: good-first-issue PRs get reviewed fastest — a quick
  first-contribution experience is what turns a one-time contributor into
  a repeat one.
- **Welcoming first contributors**: every first merged PR gets a specific,
  personal thank-you (not just the merge itself) and a name added to
  `CONTRIBUTORS.md` in the same PR or immediately after.
- **Bug vs. feature prioritization**: anything that breaks the documented
  install/quickstart path is priority one, ahead of new features, for the
  first two weeks — a broken quickstart during peak launch traffic does
  disproportionate damage.
- **Duplicate request handling**: link to the existing issue/Discussion,
  thank the reporter, close as duplicate — don't let the same request
  fragment across five open issues.
- **Contributor promotion**: track it explicitly against the funnel in
  `GOVERNANCE.md` — don't let a clearly-trusted repeat contributor wait
  indefinitely for recognition just because no one proposed it.
- **Avoiding maintainer burnout**: if response volume exceeds what one
  maintainer can sustain at the SLA above, say so publicly and ask for
  help triaging rather than silently missing the SLA — a visible "we need
  more reviewers" is healthier than an invisible slowdown.

## Launch failure modes and mitigations

| # | Risk | Mitigation |
|---|---|---|
| 1 | Weak demo | `docs/HERO_DEMO_SPEC.md`'s explicit requirements checklist; don't launch until it's met |
| 2 | Broken install | Two clean-machine install tests before launch (`docs/LAUNCH_72H_PLAN.md`) |
| 3 | Setup too complicated | `docs/INSTALL.md` written and timed against the <10-minute goal; friction points get fixed, not just documented around |
| 4 | Misleading GPU/hardware claim | `docs/HARDWARE.md` is the single source of truth; no launch copy states anything beyond what it lists as TESTED |
| 5 | Empty Issues page | `docs/ISSUES_SEED.md` — 30-50 issues seeded before launch |
| 6 | No good first issues | Minimum 8-12, each meeting the full spec (problem/why/files/expected result/acceptance criteria/how to test) — see `docs/ISSUES_SEED.md` |
| 7 | Unclear license | `docs/LICENSE_STRATEGY.md` resolved and `LICENSE` added before launch — not left ambiguous |
| 8 | Bad docs | `docs/INSTALL.md` verified by actual clean-machine runs, not just written and assumed correct |
| 9 | Poor English README | Native/fluent review pass before freeze, separate from the initial draft |
| 10 | Slow response | First-week SLA above, tracked explicitly |
| 11 | Monolithic architecture (hard to contribute to) | `providers/base.py`'s interface separation and `docs/COMMUNITY_TRACKS.md`'s explicit boundaries are the mitigation — new provider = one file + one registry line |
| 12 | Overclaiming | Every hardware/capability claim traced to `docs/HARDWARE.md` or actual shipped code; roadmap items explicitly labeled ROADMAP/HELP WANTED/RESEARCH, never presented as done |
| 13 | Bad UI | `app.py`'s Gradio UI is functional but not a design showcase — set expectations accordingly in the README, don't lead with UI screenshots as the hook |
| 14 | Unclear differentiation ("just another AI video tool") | Lead with the full pipeline breadth + local-first + provider-agnostic combination — few tools do all three together |
| 15 | Privacy leak | `docs/OPEN_SOURCE_SECURITY_AUDIT.md`, plus a final re-scan at T-3 days per `docs/LAUNCH_72H_PLAN.md` |
| 16 | Secret leak | Same audit; no `.env` file ever committed, verified via `.gitignore` and the final scan |
| 17 | Accidental model upload | `docs/PUBLIC_REPOSITORY_PLAN.md`'s model file policy; `.gitignore` excludes model file extensions explicitly, not just by convention |

## What this document does not do

It doesn't schedule anything or authorize publishing anything — see
`docs/LAUNCH_72H_PLAN.md` for the timeline and
`docs/OPEN_SOURCE_READINESS.md` for the explicit GO/NO-GO gate.
