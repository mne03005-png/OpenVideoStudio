# Launch Content

Full drafts for every channel in `docs/OPEN_SOURCE_LAUNCH_STRATEGY.md`'s
plan. Titles here already carry that document's local-first/open-source-
in-progress correction — none of these overclaim. **Not posted anywhere.**
Link placeholders (`{REPO_URL}`, `{DEMO_URL}`, `{DISCUSSIONS_URL}`) get
filled in at actual launch time, once those URLs exist.

Recommended posting order (detail in `docs/LAUNCH_72H_PLAN.md`):
**GitHub (anchor, hour 0) → Hacker News + X (day 1) → Reddit (24–48h
after HN, once there's visible traction to point to) → YouTube (week 1)
→ Bilibili + V2EX (same week as YouTube) → Zhihu + Juejin (week 1–2).**

---

## 1. GitHub (the repository itself)

Not a "post" — the README *is* the pitch. See `README.md` and the release
notes drafted in `docs/GITHUB_LAUNCH_SETUP.md` Section 7. No separate
content needed here beyond what those two already carry.

---

## 2. Hacker News

**Title:** Show HN: OpenVideoStudio – a local-first AI video studio that
runs on a 6GB GPU

**Post body** (Show HN posts are typically just a link + the poster
commenting in the thread, but here's the opening comment to post
immediately after submitting, which is standard HN practice):

> Hi HN — I built OpenVideoStudio, a pipeline that turns one text prompt
> into a fully edited, narrated, subtitled video: script → storyboard →
> character/environment identity → keyframes → video clips → narration →
> subtitles → automated edit.
>
> It runs on local models (Ollama + ComfyUI/SDXL/LTX-Video) on my own
> 6GB RTX 3060 laptop — see `docs/HARDWARE.md` in the repo for exactly
> what's tested vs. expected vs. unknown, since I'd rather under-claim
> than have someone's install fail on a claim I didn't actually verify.
> One thing I want to be upfront about: default narration uses
> Microsoft's Edge TTS, which is a cloud call — everything else in the
> pipeline is local, and that's the one exception, disclosed in the
> README, not buried.
>
> The provider layer (LLM/image/video/TTS) is a set of swappable
> interfaces — adding a new one is one file plus a two-line registration,
> not a fork. I'm opening it up specifically because there's real,
> scoped work I didn't build myself on purpose — Linux/macOS support, an
> OpenAI-compatible provider, character-consistency research, a timeline
> editor — see `docs/COMMUNITY_TRACKS.md` if any of that's your kind of
> problem.
>
> Repo: {REPO_URL}
>
> Happy to answer anything about the architecture, the GPU-sequencing
> approach for fitting this on 6GB, or what's still rough.

**Short version** (if a character-limited summary is needed elsewhere):
"An open pipeline that turns a prompt into a full edited video —
local-first, script/image/video generation run on a 6GB GPU, one cloud
call (default TTS) disclosed in the repo — looking for contributors on
the parts I deliberately left unbuilt."

**CTA:** implicit — HN penalizes hard asks. The repo link and an active,
responsive comment thread *are* the CTA.

**Timing:** weekday, US morning (poster needs to be present and
responsive for several hours after posting).

---

## 3. Reddit

Three separate posts, not one crossposted — each written for that
subreddit's actual interests.

### r/StableDiffusion

**Title:** I built a full prompt-to-video pipeline on top of SDXL
Lightning + LTX-Video — script, storyboard, identity, keyframes, clips,
narration, all automated

**Opening paragraph:**

> Posting here because the image/video generation side is where most of
> the interesting technical decisions are. OpenVideoStudio chains SDXL
> Lightning (keyframes) and LTX-Video (image-to-video clips) behind an
> LLM-driven script/storyboard stage, with a canonical character/
> environment identity generated once and reused verbatim across every
> scene's prompt — instead of re-describing the character each time and
> hoping the LLM stays consistent, which is what drifted in an earlier
> version. Runs on a 6GB card by never keeping two heavy models resident
> at once (Ollama unloads before SDXL loads, which frees before LTX
> loads).

**Short version:** "Full prompt-to-video pipeline built on SDXL Lightning
+ LTX-Video, with a canonical identity system instead of re-describing
the character every scene. Open source, looking for contributors."

**CTA:** "Repo + install guide: {REPO_URL} — genuinely interested in
feedback on the identity-consistency approach specifically, that's the
part I'm least sure is the right long-term design."

### r/LocalLLaMA

**Title:** Built a local-first AI video pipeline (Ollama + ComfyUI) —
the LLM does script/storyboard/identity generation, everything chains
off that

**Opening paragraph:**

> Sharing here because the LLM side (Ollama, qwen3:8b by default but
> config-driven, not hardcoded) is doing more than people might expect
> in a "video generation" tool — it writes the script, breaks it into a
> shot-by-shot storyboard, and generates a structured character/
> environment identity in its own focused call before touching any image
> model. Provider selection is genuinely config-driven (verified by
> tests, not just claimed) — swapping the LLM provider doesn't touch
> pipeline code.

**Short version:** "Local-first AI video pipeline — Ollama does script/
storyboard/identity generation, ComfyUI does the visuals. Open source,
provider-agnostic architecture."

**CTA:** "{REPO_URL} — an OpenAI-compatible provider adapter is on the
help-wanted list if anyone wants the highest-leverage contribution
available."

### r/opensource

**Title:** Launched OpenVideoStudio (Apache-2.0): an AI video pipeline
built with real community contribution tracks, not just a code dump

**Opening paragraph:**

> Wanted to share this here specifically because of how the contribution
> model is structured, not just the tool itself. The core pipeline is
> maintainer-led and tested; everything past it — AI art tooling,
> platform support, a timeline editor, character-consistency research —
> is scoped into eight tracks with explicit boundaries, deliberately left
> unbuilt so there's real work available, not busywork. Governance is a
> five-rung earned-trust model (Contributor → Trusted Contributor →
> Reviewer → Maintainer → Core Maintainer); sponsorship, when it's
> eventually activated, explicitly can't buy any of those rungs.

**Short version:** "New Apache-2.0 AI video project with real, scoped
community contribution tracks and an earned-trust governance model —
not just code thrown over the wall."

**CTA:** "{REPO_URL} — `docs/COMMUNITY_TRACKS.md` and 43 seeded issues
if you want to see exactly what's open before you look at any code."

---

## 4. X (Twitter)

**Thread (5 posts):**

1. I built a local-first AI video studio: one prompt → script →
   storyboard → keyframes → clips → narration → subtitles → final video.
   Runs on my own 6GB RTX 3060 laptop. Open-sourcing it today.
   🧵
2. [demo clip embedded here]
3. The pipeline generates a canonical character + environment identity
   *once*, then reuses the exact same text on every scene's prompt —
   instead of re-describing the character every time and hoping it stays
   consistent. That was the fix for the biggest continuity problem in
   earlier versions.
4. Provider layer is genuinely swappable — LLM, image, video, TTS are all
   interfaces, config-driven selection, not hardcoded. One honest
   exception: default narration uses Edge TTS (cloud), disclosed clearly,
   not buried.
5. It's Apache-2.0, and I deliberately didn't build everything —
   character-consistency research, Linux/macOS support, an AI art
   studio layer, a timeline editor are all open, scoped tracks. Repo +
   43 seeded issues: {REPO_URL}

**Short version (single post, if a thread isn't the right format):** "I
built a local-first AI video studio that runs on a 6GB RTX 3060 —
prompt → full edited video, open source. One disclosed exception: default
narration is a cloud call (Edge TTS), everything else stays on-device.
Looking for contributors on the parts I left unbuilt on purpose.
{REPO_URL}"

**CTA:** repo link on the last post, pinned reply with the Discussions
link once live.

**Timing:** day 1, same day as HN.

---

## 5. YouTube

**Video title:** "I Built an Open-Source, Local-First AI Video Studio
(6GB GPU)"

**Description (opening paragraph):**

> OpenVideoStudio turns a single prompt into a complete video — script,
> storyboard, character/environment identity, AI-generated keyframes and
> clips, narration, subtitles, all automated. This video walks through a
> real generation run start to finish, on the same 6GB laptop GPU the
> project is built and tested on. Script, storyboard, identity, keyframes,
> and clips all run on that local GPU; the one disclosed exception is
> default narration, which uses a cloud TTS call (Edge TTS) — covered at
> [timestamp] below. It's open source (Apache-2.0) and actively looking
> for contributors — timestamps and links below.

**Short version (for the video's own hook, first 10 seconds):** "This
entire video — script to final cut — was generated by a prompt, on a
laptop GPU, with software I'm open-sourcing today."

**CTA:** "Full install guide and source: {REPO_URL} — Discussions:
{DISCUSSIONS_URL}"

**Timing:** week 1, not launch day — a real walkthrough needs more
production time than the README's short hero demo.

---

## 6. Bilibili

**标题:** 我做了一个本地优先的开源 AI 视频工作室（6GB 显存笔记本可跑）

**开头段落:**

> OpenVideoStudio 把一句提示词变成一部完整的视频：剧本、分镜、角色/场景
> 一致性设定、AI 生成关键帧和视频片段、配音、字幕，全部自动完成。这期视频
> 展示了一次真实的完整生成过程，就在项目开发和测试所用的同一台 6GB 显存
> 笔记本显卡上跑的。项目开源（Apache-2.0 协议），正在寻找贡献者——链接和
> 时间戳见简介。

**Short version:** "从一句提示词到成片，剧本、分镜、关键帧、视频片段都由这个
我今天开源的软件在一台笔记本显卡上本地生成完成；唯一的例外是默认配音走的是
云端的 Edge TTS，仓库里写清楚了。"

**CTA:** "完整安装指南和源码：{REPO_URL}"

**Timing:** same week as the YouTube video — mirrors it with Chinese
narration/subtitles, links `README_CN.md`.

---

## 7. V2EX

**标题:** 开源了一个本地优先的 AI 视频生成工具，6GB 显存笔记本可跑完整流程

**开头段落（偏技术、低废话，匹配 V2EX 的技术社区调性）:**

> 做了几个月，今天开源。核心流程：提示词 → LLM 生成剧本和分镜（Ollama）→
> 生成一次性的角色/场景一致性设定 → SDXL Lightning 生成关键帧 → LTX-Video
> 生成视频片段 → Edge TTS 配音 → 字幕 → FFmpeg 自动剪辑合成。剧本、分镜、
> 关键帧、视频片段这几步全部在本地跑，6GB 显存笔记本卡（RTX 3060）验证
> 通过；配音目前默认走的是 Edge TTS，是唯一会联网的一步，没有藏着不说。
> 具体哪些硬件配置测试过、哪些只是预期可行，`docs/HARDWARE.md` 里如实写
> 清楚了，没有夸大的硬件宣传。Provider 层（LLM/图像/视频/语音）是可替换
> 接口，配置驱动，不是写死在 pipeline 代码里——这点有测试验证，不是嘴上
> 说说。

**Short version:** "本地优先的 AI 视频生成流水线，6GB 显存笔记本验证通过，
Apache-2.0 开源，欢迎贡献。"

**CTA:** "仓库地址：{REPO_URL}"

**Timing:** same week as HN/day 1 posts.

---

## 8. Zhihu

**标题:** 我用几个月业余时间做了一个开源 AI 视频生成工具，聊聊技术选型和踩过的坑

**开头段落（更长的叙事空间，适合讲"为什么"）:**

> 这篇文章聊聊 OpenVideoStudio 这个项目——一个把提示词自动变成完整视频的
> 开源流水线，以及做的过程中踩过的一些坑：比如角色一致性问题最早是靠 LLM
> 每个分镜重新描述角色外貌来维持的，实际效果会随着分镜数量增多而漂移，后来
> 改成用一次独立的 LLM 调用生成结构化的角色/场景设定，用代码而不是 LLM 来
> 保证每个分镜拿到的描述文本完全一致，这个改动明显改善了角色一致性。再比如
> 6GB 显存下如何避免 Ollama、SDXL、LTX-Video 同时占用显存导致 OOM……

**Short version:** "开源 AI 视频生成工具的技术选型和踩坑记录，包括角色一致性
和 6GB 显存下的显存调度问题。"

**CTA:** "项目地址：{REPO_URL}，欢迎讨论和贡献。"

**Timing:** week 1–2, can follow the initial launch wave once there's
something to reference back to.

---

## 9. Juejin

**标题:** 开源项目实战：如何设计一个可扩展的 AI 视频生成 Provider 架构

**开头段落（偏实现细节，符合 Juejin 的开发者受众）:**

> 这篇讲讲 OpenVideoStudio 里 Provider 抽象层的设计：LLMProvider /
> ImageProvider / VideoProvider / TTSProvider 四个接口，新增一个 provider
> 只需要写一个新文件加 registry.py 里两行注册，pipeline 代码本身不用改。
> 具体使用哪个 provider 完全由 config.toml 驱动，这一点专门写了测试验证——
> 早期版本这里其实是写死在代码里的，被独立审查发现后改成了配置驱动。

**Short version:** "AI 视频生成项目的 Provider 抽象层设计实战，配置驱动而非
硬编码的具体实现方式。"

**CTA:** "完整实现见仓库：{REPO_URL}"

**Timing:** week 1–2, alongside Zhihu.

---

## Cross-channel consistency check

Every title and opening paragraph above was written or reviewed against
the same bar `README.md`'s headline was held to: no unqualified "runs
locally" / "fully local" / 全部在本地 claim stands without the Edge TTS
cloud-call caveat nearby (an earlier draft of this file missed this in
several short-form spots — the YouTube title, the HN and X short/single-
post versions, the Bilibili short version, and a direct
self-contradiction in the V2EX opening paragraph that named Edge TTS and
then said "全部在本地跑" in the same breath — all fixed; "local-first" /
本地优先 titles that don't claim totality were left as-is, since that
phrasing is already accurate without a caveat). No unqualified "open
source" ahead of the Apache-2.0 license actually being in place (it now
is — see `docs/LICENSE_STRATEGY.md`), and no hardware claim beyond what
`docs/HARDWARE.md` actually verifies. This check is a description of what
was done, not a standing guarantee — re-run your own scan for "local" /
"cloud" / "offline" / 本地 / 云端 / 离线 across this file before actually
posting anything, since it's easy for a future edit to reintroduce the
same gap.
