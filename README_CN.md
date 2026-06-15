<p align="center">
  <img src="docs/aris_logo.svg" alt="ARIS — Auto Research in Sleep" width="640">
</p>

# ARIS-Movie-Director

🌐 **中文** · [English](README.md)

> 把一个模糊的故事丢给你的 agent,睡一觉醒来收获一部**跨模型审计过的电影** 🎬 —— 不丢事实,也没有哪一帧自己给自己盖章。<br>
> *🎞️ 当下是图像版,**下一步视频版**。*<br>
> *🤖 智能体驱动的设计 —— 规划 · 把关 · 跨模型评审都放在 **agent** 上;渲染交给 **diffusion 模型**。*

**📚 跳转** — [▶ 看电影](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/) · [⚡ 快速开始](#quick-start) · [🔄 工作流](#workflows) · [📝 做你自己的](skills/movie-pipeline/SKILL.md) · [🧩 结构](#layout) · [💬 社区](#community) · [📖 引用](#citation) · [🤝 贡献](CONTRIBUTING_CN.md)

[![Join Community](https://img.shields.io/badge/💬_Join-Community-7C3AED?style=flat)](#community) · [![Cite](https://img.shields.io/badge/📖_Cite-BibTeX-2E7D32?style=flat)](#citation) · [![CI](https://github.com/wanshuiyin/ARIS-Movie-Director/actions/workflows/ci.yml/badge.svg)](https://github.com/wanshuiyin/ARIS-Movie-Director/actions/workflows/ci.yml) · [![ARIS Stars](https://img.shields.io/github/stars/wanshuiyin/Auto-claude-code-research-in-sleep?style=flat&logo=github&logoColor=white&color=gold&label=ARIS%20Stars)](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/stargazers) · [![arXiv](https://img.shields.io/badge/arXiv-2605.03042-b31b1b?style=flat&logo=arxiv)](https://huggingface.co/papers/2605.03042) · [![HF Daily #1](https://img.shields.io/badge/HF%20Daily%20Papers-%231-yellow?style=flat)](https://huggingface.co/papers/2605.03042) · [![PaperWeekly](https://img.shields.io/badge/Featured%20on-PaperWeekly-red?style=flat)](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) · [![awesome-agent-skills](https://img.shields.io/badge/Featured%20in-awesome--agent--skills-blue?style=flat&logo=github)](https://github.com/VoltAgent/awesome-agent-skills)

**这是一个智能体驱动的、长程的视觉生成任务:** 把一个模糊的故事交给 agent,产出**一整部图像版电影**(参考样片是 **19 场 / 24 帧**的故事),而不是单张图。具体要做的是
`模糊故事 → 撰写出的 comic.json → 审计过的画格 → 单文件查看器`。

**难点在于"随时间保持忠实"。** 生成出来的视觉故事可以看着很连贯,却悄悄改掉了事实 —— 图表把数字四舍五入、标签变了样、角色的脸发生漂移 —— 而整次生成还是照样发布,因为**画这一帧的系统,正是那个说"看起来没问题"的系统**。在长程之下,有两个主导的失败模式:

- 🧠 **长距离遗忘** —— 跨越许多帧后,身份、既定事实、早先的决定都会漂移。
- 🗣️ **线性、自我批准的流式生成** —— 每一帧都由画它的那个模型自己拍板,于是错误一路累积、无人核查。

**🔬 方法一览。** 从左到右看这张图 —— [`/movie-pipeline`](skills/movie-pipeline/SKILL.md) 这个 agent 工作流跑完整条环路(*撰写真值源 → 烤制 → 跨模型 gate*):**(1)**
[`comic-author`](skills/comic-author/SKILL.md) 把模糊意图变成撰写出的 `comic.json` + 锁定的引用,**(2)**
[`comic-director`](skills/comic-director/SKILL.md) 逐格跑审计螺旋 —— 也就是 **multi-agent debate(多智能体辩论)**(CC ‖ Gemini ‖ Codex 盲读 → 确定性 diff),把每次尝试 / 决定都写入
**[research-wiki](examples/comic_m3_audit/wiki/)** —— **(3)** 流水线把通过的画格组装进发布的查看器。左下角那个失败就是全部规则:*好看但数字错了照样不过*
(`+6.2` 期望 vs `+6.25` 实际)。

![ARIS-Movie-Director — method overview](docs/method_figure.png)

<sub>**图 1** — 从故事意图到一部被验证的电影,端到端(上面描述的那条环路)。完整图注 ↓</sub>

<details><summary><b>图 1 — 阶段、gate 与出处</b>(点击展开)</summary>

> **(1) 撰写出的真值源** —— 资产库 · 大纲 · 分镜编译成 `comic.json`(`content_svg · expected_literals · identity_ref`)。**(2) 审计螺旋(逐格)** —— 一张 content-SVG 蓝图由 image_gen 烤制,然后一个 3 审的跨模型 `panel_gate`(CC 叙事 ‖ Gemini + Codex 视觉*盲读转录* → 确定性 token-diff · 单票否决)给出确定性 `verdict`:**KEEP**,或 **RETRY**(每格 ≤4)带着上次失败的修复提示重烤;每一次 尝试/评审/决定/失败 都记入 `research-wiki`。**(3) 组装 + 发布** —— 一个 cast-aware 的 `page_assembly_gate`(修复漂移 → 重烤,每次运行 ≤6)输出 PNG 画格 + 单文件 HTML 查看器。点睛之笔(左下):**好看但数字错的画格不会通过** —— `+6.2` 期望 vs `+6.25` 实际,被 token-diff 拦下。
>
> *这张图本身就是用它所描绘的那条环路做出来的:一张带标注的蓝图作为条件喂给 `gpt-image-2`(由 Codex GPT-5.5 xhigh 驱动),随后 4 轮生成由 method-figure 审议团 —— **Gemini + Codex 盲读转录 + 确定性 `content_diff`,再加一道 Claude 的结构签字** —— 直到干净。**烤出这张图的确切 prompt 序列**(全部 4 轮 + 跨模型批评)原样发布作为参考:[`skills/method-figure/examples/method_figure/PROMPTS.md`](skills/method-figure/examples/method_figure/PROMPTS.md)。*

</details>

**ARIS-Movie-Director 把每一帧都当作可审计的 artifact:** 先撰写一份确定性的 `comic.json`(在任何像素之前就**锁死** `expected_literals` + 身份引用),让生成模型烤出观感,然后在一格被接受之前**强制要求独立的跨模型盲读转录 + 一次确定性 token-diff**。
*看着对 ≠ 通过* —— 一帧好看但数字错的画格会被拒。它用 [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) 系列的两个想法,正面回应上面两个失败模式:
- 🧠→ 一个 **[research-wiki](examples/comic_m3_audit/wiki/)** —— 持久、可审阅的记忆(锁定引用 · `expected_literals` · 每个决定与失败都作为一个节点),把后段的帧锚回前段的真值。
- 🗣️→ **multi-agent debate(多智能体辩论)** —— 独立的跨模型审稿人盲读每一帧,再由确定性 diff 判 **KEEP / RETRY**,于是**没有哪一帧自己给自己盖章**。每一次 尝试/决定 都落在那份 wiki trace 里。

**本次首发是图像版** —— 电影由你一帧帧翻看的烤制静帧讲述。**视频版生成是下一步;这只是开始。**

> **▶ [在浏览器里看图像版电影](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/)** —— 翻看这部跨模型审计过的参考样片的全部 19 场。

[![Watch the movie — cover](docs/comic_cover_v4.webp)](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/)

<table><tr><td width="33%"><a href="https://wanshuiyin.github.io/ARIS-Movie-Director/comic/"><img src="docs/preview_audit.webp" alt="audit page"></a></td><td width="33%"><a href="https://wanshuiyin.github.io/ARIS-Movie-Director/comic/"><img src="docs/preview_panels.webp" alt="multi-panel page"></a></td><td width="33%"><a href="https://wanshuiyin.github.io/ARIS-Movie-Director/comic/"><img src="docs/preview_fix.webp" alt="the fix beat"></a></td></tr></table>

<sub>参考样片里的几帧 —— 其中包含故事自身的"诚信桥段":一次**汇报 `+6.2`** 提升、却**实际只动了 `+1.4`** 的实验(这是*剧情*,跟图里那个烤制期 `+6.2`/`+6.25` 的 token-diff 是两回事)。**[看全部 19 场 →](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/)**</sub>

<details><summary><b>⚡ 审计 gate 到底拦住了什么</b> —— 问题 → 机制 对照表</summary>

| 问题 | ARIS-Movie-Director 怎么应对 |
|---|---|
| 一格可以看着对,却改了某个数字、标签或代码 token。 | `comic.json` 锁死 `expected_literals`;独立视觉审稿人**盲读转录**像素里实际有的内容;一次精确 token-diff 拒掉任何错的或缺的 literal。 |
| 烤出图的那个模型可以自己把自己放行。 | 烤制从不自证 —— 由独立视觉模型(与生成器**不同家族**)盲读,再由一次**确定性** diff(而非某个模型的意见)判 **KEEP / RETRY**。 |
| 一格被烤出来,却没有任何东西可供核对。 | Phase 1 在像素**之前**就撰写 `content_svg` · `identity_ref` · `ART_BIBLE` · `expected_literals`;一个**没有**可门控 literal 的烤制 figure 格会**fail-closed**(拒绝放行)。 |
| 角色与风格在长序列中累积漂移。 | 锁定身份引用 + 资产评审(准×3)+ style bible + 一个 **cast-aware** 的组装 gate 检查一致性,*同时允许*有意的场景/角色变化(缺席 ≠ 漂移)。 |
| 重试循环变得不透明或没完没了。 | 每格尝试与组装修复都是**有上界的**;每次失败带一条修复提示;不收敛的画格会被**标给人工**,绝不静默发布。 |
| 一个 demo 把试过又丢弃的东西藏起来。 | 每一次 尝试/评审/决定/失败模式 都写进 research-wiki —— 参考样片随附一份 **198 节点**的可读 trace。 |

</details>

---

<a id="quick-start"></a>

## ⚡ 快速开始

```bash
# 1 · 拿到仓库 + Python 依赖(除 jsonschema 外都是标准库)
git clone https://github.com/wanshuiyin/ARIS-Movie-Director.git && cd ARIS-Movie-Director
python3 -m pip install -r requirements.txt

# 2 · 烤制/评审阶段需要的外部工具 —— 安装 + 登录,然后自检:
#     codex CLI  ·  gemini CLI(使用 auto-gemini-3)·  无头 Chrome / Chromium
python3 cli/preflight.py
```
**没有打包的安装器** —— `skills/` 是由*你那个指向本仓库的 coding agent 来"跟随"执行*的;确定性 CLI 在仓库内直接跑。

**跑两个工作流** —— 在一个装有这些 skill 的 coding agent 里(`/…` 是一个**斜杠命令式 agent 工作流**,*不是* shell 二进制):
```text
> /movie-pipeline "a short film about an autonomous research run"   # 工作流 1 — 模糊想法 → 审计电影 + 查看器(在 intent + outline 处暂停)
> /method-figure  path/to/method_figure_brief.json                 # 工作流 2 — 一份 brief → 审计过的 Figure-1(渲染 + 验证 → Claude 签字)
```

**先看成品 —— 零配置、无需 API:** ▶ 打开在线电影 **<https://wanshuiyin.github.io/ARIS-Movie-Director/comic/>**(全部 19 场 / 24 帧)。想本地重建,见下方 **工作流 1 → 看参考电影**。

<sub>**全景图** — `模糊故事 → /movie-pipeline → comic.json + 审计画格 + outputs/index.html`  ·  `method_figure_brief.json → /method-figure → figure.png + blueprint + trace`</sub>

---

<a id="workflows"></a>

## 🔄 工作流

两个跨模型审计的工作流。每个都是**一条斜杠命令式 agent 工作流**(ARIS `/research-pipeline` 的范式 —— 由 agent 来跑,在人工 gate 处暂停),并各自带一个你也可以单独运行的**确定性 CLI 内核**(CI 测的就是这部分)。

### 🎬 工作流 1 · 电影流水线 — `/movie-pipeline`(模糊想法 → 审计电影)
把一个模糊故事交给你的 agent,批准两道剧情 gate,睡醒就得到一部烤好的、跨模型审计过的电影 + 一个可点击查看器:
```text
> /movie-pipeline "a short film about an autonomous research run"
```
它串起 [`comic-author`](skills/comic-author/SKILL.md)(Phase 1 —— 撰写真值源)→ 零信用的
`p0_proof` gate → [`comic-director`](skills/comic-director/SKILL.md)(Phase 2/3 —— 审计螺旋 → 查看器);编排器是
[`movie-pipeline`](skills/movie-pipeline/SKILL.md)。它是一个 **agent** 工作流,不是 shell 二进制 ——
它需要一个 coding-agent 运行时,并在 **intent + outline 处暂停等你批准**。*(某一步没触发也是安全的 —— 每一层都消费上一层那个 LOCKED 节点,所以漏掉的一步会在下一道 gate 处 fail-closed,绝不会发布出错的帧。)*

- 🧭 **Intent(意图)** —— 模糊想法 → `intent_spec` · **停下等你批准**
- 🎨 **Style lock(风格锁)** —— `ART_BIBLE.md` + 锁定的 `style_anchor`(warm-lab / dark-cyber / starfield)
- 🧱 **Outline(大纲)** —— 三视角辩论 → 综合 → `outline_spec` · **停下等你批准**
- 🎞️ **Storyboard(分镜)** —— 页 · 格 · MOTIF 状态表 · 汇总的 `asset_requests`
- 🧑‍🎨 **Assets(资产)** —— 单一来源的资产库,评审到 `locked`(准×3 同轮一致)
- 📐 **Blueprints(蓝图)** —— 每格一张确定性 `content_svg`(不烤气泡)
- 🧾 **Prompts** —— 确切的烤制 prompt + 逐字的 `expected_literals`(搬运工原則)
- ✅ **Compile(编译)** —— schema 合法的 `comic.json`;零信用的 `p0_proof` gate 在任何图像信用之前先跑
- 🔥 **Spiral bake(螺旋烤制)** —— 渲染 → `codex image_gen` → 3 审 `panel_gate` → keep / retry / 跨帧回滚 → 组装 → 查看器

**📐 流程 —— skill 链(可从上往下逐条追):**

```text
/movie-pipeline "fuzzy idea"            一条斜杠命令 · 由 agent 跑,不是 shell 二进制
   │
   ▼   comic-author 按顺序驱动这些 Phase-1 skill(它们不是各自独立的斜杠命令):
   comic-intent-parser
     → ⟨人工批准 — intent⟩
     → comic-style-bible-lock
     → comic-outline-creator
     → ⟨人工批准 — outline⟩
     → comic-storyboard-creator
     → comic-asset-ref-generator → comic-asset-review-loop          (准×3 一致 → 资产 LOCKED)
     → comic-blueprint-author → comic-panel-prompt-builder → comic-json-compiler
   ├──────────────── Phase 1 · comic-author —— 撰写真值源 ────────────────┤
   │
   │   → comic.json + 锁定资产 + 撰写期 wiki trace
   ▼
   comic-cross-layer-gate --gate p0_proof     ├─ P0 · 零信用证明 —— 必须在任何图像信用之前通过 ─┤
   │
   ▼   comic-director —— 审计螺旋     (run_comic.py  |  packages/core/spiral_engine.js)
   逐格:  content_svg → codex image_gen → panel_gate
                  审稿人: CC 叙事 ‖ Gemini 视觉 ‖ Codex 视觉
                  → 盲读转录 → 对 expected_literals 做确定性 token-diff
               verdict ─ KEEP → 入页池
                       ├ RETRY ≤4   (重烤同一格 + 修复提示)
                       └ rollback ≤6 (重烤被点名的先前格 —— 跨帧漂移)
   page assembly_gate → 把通过的格投影回 comic.json → build_comic.py → outputs/index.html
   ├──────────────── Phase 2/3 · comic-director —— 审计螺旋 + 查看器 ────────────────┤

   📚 research-wiki —— 每层之前读取锁定的真值源节点;每道 gate 与每次烤制之后写入每一次
                      尝试/评审/决定/失败(可审阅的审计 trace)。
   🔄 human-in-loop —— intent + outline 是硬性停点;失败的 p0 / panel / assembly gate 会停下或
                      升级;不收敛的画格会被标给你,绝不静默发布。
```

**`panel_gate`**(Phase 2/3,逐格):烤出的图由 **3 个独立审稿人**读 —— CC *叙事*
(有没有落点剧情?)‖ Gemini *视觉* ‖ Codex *视觉*(第二只、不同家族的眼睛)—— 它们
**盲读转录**像素;再由对 `observed_literals` 与撰写出的 `expected_literals` 的**确定性** token-diff 判 KEEP / RETRY;`content_corruption` 是单票否决,两个视觉审稿人都必须打分,并且**没有任何模型能自证通过**。每一次 尝试/评审×3/决定/失败 都写入 `research-wiki`。

**Phase 2/3 单独跑**(确定性、无需 agent —— 就是 CI 测的那部分),前提是 `comic.json` 已存在:
```bash
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <PAGE> --panels S01,S02 --dry-run    # 零信用:打印烤制 prompt
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <PAGE> --panels S01,S02 --finalize   # 烤制 + 重建查看器
```
`run_comic.py` 是 [`packages/core/spiral_engine.js`](packages/core/spiral_engine.js) 的子进程移植版(无需 agent 运行时);它从一个已存在的 `comic.json` 起步 —— **它不能从模糊想法起步**。**限流:** 被限速的烤制会带着 `fresh_run_required` 干净地停下 —— 冷却后,为剩余画格启动一次**全新**运行,**不要**复用缓存状态。上限:**每格 ≤4 次尝试 · 每次运行 ≤6 次回滚 · 不并发烤制**
([`docs/spiral-runtime.md`](docs/spiral-runtime.md))。

**撰写模板:** 加新项目时,从 [`examples/comic_min_author/`](examples/comic_min_author/) 复制 Phase-1 的作者节点形状。
上面那张流程图就是规范的 skill 链 —— 两道人工 gate 和各处 fail-closed gate 都画在那里;前置依赖(codex + gemini + 无头 Chrome)见 [快速开始](#quick-start)。

#### ▶️ 看参考电影 —— 工作流 1 的产物(零配置、无需 API)
```bash
python3 cli/validate_wiki.py examples/comic_m3_audit             # 校验随附的 trace → PASS(198 节点,26 边)
python3 packages/viewer/build_comic.py examples/comic_m3_audit  # 从 comic.json + panels (重)建单文件查看器
open  examples/comic_m3_audit/outputs/index.html
```
…或直接打开在线版:**<https://wanshuiyin.github.io/ARIS-Movie-Director/comic/>** —— 这部跨模型审计参考样片的全部 **19 场 / 24 帧**。

### 🖼️ 工作流 2 · 方法图 — `/method-figure`(一份 brief → Figure-1)
一条**斜杠命令** [`/method-figure`](skills/method-figure/SKILL.md) —— 给它一份 `method_figure_brief.json`
(就是 `paper-plan` 在它的 claims_matrix 之后产出的那种 brief),它会把整条审计螺旋跑到一张签过字的图(Step-0 编译 → 渲染条件图 → `gpt-image-2` 烤制 → Gemini + Codex 盲读审议 + `content_diff` →
重试到干净 → **Claude 结构签字**):

```text
> /method-figure path/to/method_figure_brief.json
```

**确定性内核**(从一份 brief 起步、无需 agent 运行时)是一条命令 —— `run_spiral.py`:
```bash
# 我们的示例 brief 烤的就是 ARIS 自己的 Figure 1 —— 换成你自己的 method_figure_brief.json 即可
python3 skills/method-figure/scripts/run_spiral.py \
    skills/method-figure/examples/method_figure/method_figure_brief.json \
    --out-dir figures/method_figure/demo
#  → figures/method_figure/demo/figure.png   (PANEL-CLEAN 候选,等你做结构签字)
#     (+ blueprint.json + traceability.json + 每一轮的 trace.jsonl)
#  第一次跑?加 --p0-only(零图像信用:校验 + 编译 + 渲染 + lint)。注意:--dry-run 也会写出这些文件。
```

<details><summary>📐 流程 —— /method-figure(brief → 审计渲染 → 签字)</summary>

```text
(上游 —— 只有当你手上只有论文时;不属于 /method-figure):
   paper_to_brief.md  →  method_figure_brief.json      由 agent 撰写;数字 / 主张 逐字照抄
        │
        ▼
/method-figure  <method_figure_brief.json | blueprint.json>        该 skill = 纯渲染 + 验证
   run_spiral.py —— 确定性内核(从一份 brief 起步):
     compile_brief.py (Step-0) → blueprint.json + traceability.json     每个节点都可追溯到某个 brief 字段 —— 否则 FAIL-CLOSED
       → validate_blueprint.py → render_condition.py                    带标注的条件图 SVG → PNG
       → codex exec --sandbox read-only → gpt-image-2 烤制
       → Gemini 盲读转录 ‖ Codex 盲读转录 → content_diff.py     确定性否决
       → RETRY ≤4(重申锁定标签)→ Claude 结构签字
   → figure.png   (+ blueprint.json + traceability.json + 每一轮的 trace.jsonl)
   ├──────────────── method-figure · 审计渲染 / 验证 螺旋 ────────────────┤
```
</details>

Step-0 是**在该 skill 内部**的确定性步骤 —— 你从不手写蓝图、也不手摆坐标;身份图从 brief 的
`identity_refs[].path` 解析(不必单独管 `--identity`);每个节点都被追溯校验回某个 brief 字段(追溯不到 → fail-closed)。**没有任何模型能自证通过** —— 烤出的图由 Gemini + Codex 盲读 + 一次确定性 `content_diff` 评定,再加一道单独的 **Claude 结构签字**。需要 **`codex` + `gemini` CLI** + 无头 Chrome(`python3 cli/preflight.py`)。

> **只有论文、还没有 brief?** 先撰写 brief —— 让你的 coding agent(例如
> **[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) 主项目**)按
> [`paper_to_brief.md`](skills/method-figure/references/paper_to_brief.md)(数字/主张逐字)读你的论文,再
> `/method-figure`。**进阶玩法:** 已经有一份手调好的蓝图?`run_spiral.py blueprint.json
> --identity sheet.png --out-dir … --from-blueprint` 走传统路径。那段做到收敛的 4 轮实录(确切 prompt)在
> [`PROMPTS.md`](skills/method-figure/examples/method_figure/PROMPTS.md)。

### 🛡️ 两道 gate 为何不同(都对,刻意为之)
**电影**的 `panel_gate` 是一个 **3 审**审议团(CC *叙事* ‖ Gemini *视觉* ‖ Codex *视觉*)—— 一格剧情画必须既落点剧情、又在视觉上贴模。**方法图**的审议团是 **Gemini + Codex
盲读转录 + 确定性 `content_diff`**,再由 **Claude** 做后置结构签字 —— 一张图没有"剧情落点",所以标准是确切标签 + 干净版式,而非叙事。两者都遵守同一条规则:

> gate 才是重点:一张好看但数字错的画格/图**不会**通过。忠实 = 一次 token-diff,而审稿人从不被告知期望值。

<a id="positioning"></a>

## 🧭 定位 —— ARIS 血统;一个审计层,*而非*生成/编排上的主张

ARIS-Movie-Director 是 **[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) 系列的多模态分支**:ARIS 教会一个研究 agent 在你睡觉时干活,而它的 **research-wiki + multi-agent-debate** 这两个想法,正是让一个生成出来的故事*可审计*的关键 —— 同一条环路(撰写真值源 → 让模型烤出观感 → 用跨模型审议团裁定),现在产出的是角色一致的视觉故事,而不是论文。

这个框架对任何具体故事一无所知 —— 一个项目通过 `examples/<name>/movie.project.json` + 一份 `comic.json` IR 接入。参考样例做出一部 **19 场 / 24 帧**的像素风电影、讲一次自主研究运行,并随附其**真实、可审阅的生成 trace**,作为多智能体环路确实跑过的证据。

**相关工作 —— 我们在哪个位置。** 这个领域已经把视觉故事生成和编排做得很好了,我们是在此之上、而非与之对立:**[JoyAI-Echo](https://github.com/jd-opensource/JoyAI-Echo)**(京东)长于带同步音频、靠记忆保角色一致的长片 text→video;**[FireRed-OpenStoryline](https://github.com/FireRedTeam/FireRed-OpenStoryline)**(小红书)是一个强大的对话式视频剪辑 agent —— NL 规划、工具编排、human-in-the-loop、可复用 style skill;**[NEWTON](https://arxiv.org/abs/2605.18396)** 展示了用于*物理*合理视频的 planner+verifier 闭环。ARIS-Movie-Director 是**互补的** —— 它不主张更强的生成或更广的编排;它在一个生成出的视觉故事之外加了那一层**审计**:盲读跨模型 → 确定性 literal-diff → 有界重试 → 一份可审阅的 trace。

---

<a id="layout"></a>

## 🧩 结构

- **packages/** —— 框架运行时(核心螺旋、各 gate、条件化、查看器)
- **protocols/** —— 跨模型评审 / 治理契约(框架自有)
- **schemas/** —— 带版本的 IR + wiki schema(`comic.schema.json`、`node_schema.json`、`edge_schema.json`)
- **cli/** —— `validate_wiki.py`(项目 wiki 的标准库发布 gate)
- **docs/** —— `comic-json.md`(撰写输入规范)、`architecture.md`(SSOT)、`spiral-runtime.md`、`GENERATION_RETRO.md`
- **examples/comic_m3_audit/** —— 参考电影:`comic.json` IR、`gen/` 蓝图脚本、
  `panels/` 烤制画作、`wiki/` 那份 198 节点的生成 trace、`outputs/` 构建好的查看器

<a id="community"></a>

## 💬 社区

**欢迎新的工作流、gate、示例项目。** ARIS-Movie-Director 是 [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) 系列的一部分 —— 欢迎提交 PR,加一个审计工作流、一道有牙齿的 gate、一个示例项目或一个领域适配(从 [CONTRIBUTING_CN.md](CONTRIBUTING_CN.md) 开始)。

加入微信群(与 ARIS 主项目共用),一起聊 Claude Code + AI 驱动的多模态生成:

<img src="docs/wechat_group.jpg" alt="WeChat Group QR Code" width="300">

<a id="citation"></a>

## 📖 引用

ARIS-Movie-Director 是 **ARIS** 系列的多模态分支。如果你在研究中用到它,请引用 ARIS 论文:

```bibtex
@article{yang2026aris,
  title={ARIS: Autonomous Research via Adversarial Multi-Agent Collaboration},
  author={Yang, Ruofeng and Li, Yongcan and Li, Shuai},
  journal={arXiv preprint arXiv:2605.03042},
  year={2026}
}
```

## 📄 许可证

**MIT** —— 见 [`LICENSE`](LICENSE)。

示例画作是 **AI 生成**的 —— 这是一条说明,不是第二份许可证;复用时仍应遵守你所用图像模型供应商的条款。
