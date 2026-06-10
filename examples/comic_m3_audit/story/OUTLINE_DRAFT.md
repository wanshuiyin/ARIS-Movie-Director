<!-- OUTLINE v2 — 3-lens debate → codex synthesis → codex design pass (B08 density + wiki) → user decisions. 2026-06-10. ✅ APPROVED by user 2026-06-10 ("都可以"): B08 5-page split + B09.5 wiki star-map page + side-narration rules. Now the SOURCE OF TRUTH for the storyboard layer. -->

# 漫画大纲 v2 / Comic Outline — "ARIS：我把那 24 小时交出去了 / I Handed Over Those 24 Hours"

> **Logline:** 截止前 24 小时，研究员把 dllm schema 任务交给 ARIS 二人组就睡了；这一夜的高潮不是"赢了"，而是 **ARIS 没放过自己** —— 审计揪出虚高的 +6.2、诚实坍缩到 +1.4。Tagline：你不在的时候，研究在 / While you're away, the research carries on.
>
> **双重身份：** 一部诚实研究的情感故事 + 一部 ARIS **能力展示**。

## ✅ 已定决策（用户 2026-06-10）
1. **B06-S09**（被忽略的坏样本伏笔）→ **给大画幅**。
2. **Tok\|yo 坏 JSON 前置埋点** → **极小、旁白不点破**。
3. **B13 星座** → **纯发光星点、无标签**（布局暗合 wiki 图，但读者只感到"留下了结构"）。

## 🎙️ 侧栏讲解铁律（防止"能力展示"变产品手册 —— codex）
- **每条能力必须绑一个剧情代价**：不写"ARIS has experiment-audit"，写"executor 的庆祝被审计打断，所以 ARIS 没撒谎"。
- **侧栏第一句永远讲发生了什么；第二句才点能力名。**
- **每个能力都改变角色状态**（bounce 高低 / 咖啡冷掉 / 红队介入 / claim 被降级）。
- **画面里不堆 skill 名标签**；skill 名只作侧栏小字或 hover/click metadata。

---

## Beats Table（13 beats）

| Beat (zh/en) | Panels | 布局 | 世界 | 内容 + 台词 gist | ARIS 特性（绑剧情）|
|---|---|---|---|---|---|
| **B01 卧室·倒计时** | S01 | full-bleed | 暖 | 伏案，咖啡**冒热气**，`DDL T-24:00`，贴 `dllm-schema-keyword-first`。旁白：「还有 24 小时。我撑不住了。」| 设场 |
| **B02 交接·弹起** | S02 | split 暖→暗 | seam | 按 Enter `$ aris run …`；duo 苏醒，蓝 exec **蹦最高**「交给我！」绿 rev「我盯着。」| 自主交接 |
| **B03 双线** | S03,S04 | 2-up | seam | 左她上课(咖啡热气变淡)∥右 idea-creator 想法卡飞出 | idea-creator（铺想法）|
| **B04 查新存活** | S05 | 1-panel | 暗 | `14/20 SURVIVES`「够新，留下」| novelty-check（先验防重复）|
| **B05 教室怀疑** | S06 | 1-panel | 暖 | 望窗，「它真能跑出能写进论文的?」| 人世喘息拍 |
| **B06 实验·曲线起飞** | S07,S08,**S09大** | 竖排 3，**S09 大画幅** | 暗 | S07 GPU「上 GPU！」· S08 `0.60→0.71` exec 得意 · **S09 大格：exec 没看见角落极小 Tok\|yo，rev 皱眉**（伏笔，无旁白）| experiment-bridge（证据是暂定的）|
| **B07 REJECT·碎JSON** | S10,S11 | 2-up 镜像 | 暗 | Tok\|yo 放大钉中央 rev「这解析不了。」→ 红 `REJECT` 砸下，exec 肩塌 | auto-review-loop（对抗审）|
| **🌀 B08 诚实审计（拆 5 页 + recap）** | S12-15 + **新增 S12a** | **5 单张页**（默认）/ 2×2 recap | 暗 | **见下方 B08 5-page plan** | experiment-audit + honest re-run |
| **B09 重跑·ACCEPT** | S16 | 1-panel（镜像 B07）| 暗 | `0.78→0.89` 绿 `ACCEPT` 章，exec 只**微弹**「这次是真的。」| honest re-run（自纠 overclaim）|
| **🌌 B09.5 研究星图（新增 wiki 页）** | S16b | 1-panel（中段 reveal）| 暗·星空 | 像素夜空"研究星图桌"：节点=发光星、边=细线，duo 站桌边看 `idea→experiment→REJECT→audit→WARN_corrected→ACCEPT→paper` 依次亮起。**可点进 `wiki_trace.html`**。旁白：「ARIS 把这一夜写进 research wiki：想法、被否的 claim、审计、判决、论文决策——都连着。」| **research-wiki 记忆（防重复、给后续 agent 继承上下文）**|
| **B10 诚实成稿** | S17 | 1-panel | 暗 | `+1.4 scope-limited` + 已修复 `Tokyo` 闭环 rev「照实写，边界也写上。」| paper-writing（带边界）|
| **B11 深夜·投出** | S18,S19 | 2-up | seam | 夜路回家 ∥ `SUBMITTED` `T-00:42` | 自主提交 |
| **B12 归家·凉咖啡** | S20,S21 | 2-up | 暖(∥seam) | 同一杯**已冷无热气**(B01 扣合)；隔屏击掌 exec **微弹**「欢迎回来。」| 角色弧兑现 |
| **B13 品牌·星座** | S22 | full-bleed | 暗→星图 | 整夜化作**纯星点星座**(暗合 wiki 主路径亮/失败分支暗，paper 星连回卧室)。**可点进 `wiki_trace.html`**。Tagline。| 收束 |

---

## 🌀 B08 — 5-page plan（codex；默认单张阅读，2×2 留作 recap/hero/GitHub 截图）
> 每页：技术主画面 70% + 角色情绪 30%（右下角蓝 exec bounce 当体温计）+ 侧栏讲解。

| 页 | 画面 | 侧栏（先讲发生了什么，再点能力）|
|---|---|---|
| **B08-0 审计入口**（新增 S12a）| 夜里仪表盘亮，红队 rev 把放大镜按到 evaluation pipeline 上，蓝 exec 正要庆祝被按住 | "ARIS did not accept the best-looking number — it opened an adversarial audit before turning results into claims." · *trait: auto-review-loop + experiment-audit* |
| **B08-1 诱人的胜利**（S12）| schema-first `+6.2`，W&B 曲线漂亮，exec bounce 高 | "The first pass looked clean: schema-keyword-first led by +6.2." · *trait: experiment-bridge — evidence is provisional* |
| **B08-2 暗藏的修复**（S13）| pipeline 剖面，JSON sanitizer 像隐蔽滤镜把坏输出修成可评分；Tok\|yo 角落一闪 | "The audit found the evaluator was silently repairing broken JSON before scoring it." · *trait: experiment-audit checks the apparatus, not just outputs* |
| **B08-3 裸重评坍缩**（S14）| 同批输出绕开 sanitizer raw 重跑，`+6.2`→`+1.4`；exec 被压低、安静 | "ARIS rescored on raw outputs. The claim shrank from +6.2 to +1.4." · *trait: honest re-run — corrects its own overclaim before the paper exists* |
| **B08-4 WARN_corrected**（S15）| verdict 章 `WARN_corrected` "honest, not killed"；exec 重新微弹 | "The result was not deleted — downgraded, labeled, carried forward honestly." · *trait: preserve useful signal while marking uncertainty/failure* |

---

## 🌌 Wiki 展示（codex：三层各司其职）
1. **中段专门 wiki 页 = B09.5**（审计后、论文前——最有力量的位置）：研究星图桌，路径依次点亮。
2. **B13 星座 = wiki 的诗化版**（纯星点无标签，布局暗合 graph）。
3. **可点进 `wiki_trace.html`**：放在 B09.5 + 尾卡两处。文案 = "打开这一夜的研究记忆 / open the night's memory graph"（不写"查看功能演示"）。

---

## vs v1 的增量
- **B08 4 panel → 5 页**（+ 新增 S12a 审计入口）+ 2×2 留作 recap。
- **新增 B09.5 研究星图 wiki 页**（S16b）。
- 三个开放问题已按用户决策落地（S09 大画幅 / Tok\|yo 极小 / B13 纯星点）。
- **panel 总数：22 → ~24**（+S12a +S16b）。B08 中心幕的 4 张已烤面板**复用**，只是改成单张分页 + 新增 1 张入口。

## ⚠️ 待你确认
- B08 拆 5 页（+1 张新入口面板要烤）+ 2×2 recap —— OK？
- 新增 B09.5 wiki 星图页 —— OK？（要新烤 1 张"研究星图桌"）
- 侧栏讲解铁律（每能力绑剧情代价、先事件后能力名）—— OK？
