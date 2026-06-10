# B01–B13 漫画分镜大纲 / ARIS Comic Story Outline
**主线**: 一条诚实研究的弧（+6.2 的假象 → 审计 → +1.4 的真相）× executor 的谦卑弧（兴奋 → 被审计噤声 → 沉淀）。世界配色: 暖色=人类世界 / 暗赛博=ARIS 数字世界。

---

**B01 卧室 + DDL 锚点 / Bedroom + Deadline Anchor** — `S01`
- `S01`: 暖色卧室，研究员伏案于笔记本前，咖啡杯**热气升腾**，墙上钟+屏角 `T-24:00:00`。侧栏旁白:「还有 24 小时。我撑不住了。」 ｜ motif: mug=热 · DDL=24:00 起点

**B02 交接 / The Hand-off** — `S02`
- `S02`: 研究员敲下 `$ aris run --task dllm-schema-keyword-first --deadline 24h`，屏幕裂成暗赛博世界，蓝衣 executor（棕发无须）**蹦得老高**、绿衣 reviewer（黑发络腮胡）沉稳站定。气泡: executor「交给我们！」／旁白:「你睡，研究继续。」 ｜ motif: bounce=最高点（弧起点）

**B03 平行剪辑 / Parallel Cut** — `S03`,`S04`
- `S03`: 暖色——研究员背包走向教学楼，晨光。旁白:「他去上课了。」
- `S04`: 暗赛博——idea-creator 面板，executor 抛出一串发光想法卡片，bounce 仍高。气泡:「schema 先行？keyword 先行？」

**B04 查新 / Novelty-check** — `S05`
- `S05`: novelty 仪表盘，一张 idea 卡定格 `14/20 · 存活`，绿勾。reviewer 点头。旁白:「够新，留下。」

**B05 教室 / Classroom Doubt** — `S06`
- `S06`: 暖色教室，研究员望窗出神，思想气泡里是那行命令。旁白（内心）:「它真能跑出能写进论文的东西吗……」 ｜ 埋下"信任 vs 怀疑"

**B06 实验桥 / Experiment-bridge** — `S07`,`S08`,`S09`
- `S07`: GPU 机柜在暗世界点亮，executor 拧动启动阀。气泡:「跑起来了！」
- `S08`: wandb `exact_parse` 曲线开始爬升 `0.60 → 0.71`，executor 指着曲线**得意蹦跳**。
- `S09`: 中途特写——一条样本 `{"city":"Tok|yo"}` 一闪而过（**Tok|yo 首次埋点**），executor 没注意，reviewer 眯眼。｜ motif: Tok|yo 登场 · bounce=骄傲

**B07 审查循环 REJECT / Auto-review REJECT (R3)** — `S10`,`S11`
- `S10`: Round 3 面板，曲线**回落**，那条 `{"city":"Tok|yo"}` 破 JSON 被放大钉在中央。气泡 reviewer:「这解析不了。」
- `S11`: 红色 **REJECT** 印章砸下，executor **泄气、bounce 变小**。旁白:「第一次被拦下。」｜ motif: Tok|yo 回调 · bounce↓（铺垫审计）

**B08 🌀 中心片 M3 审计 / The M3 Audit Centerpiece (已完成)** — `S12`,`S13`,`S14`,`S15`
- 保持现状（已 baked + 声音门控）。要点: schema-keyword-first 看似 **+6.2** → 对抗审计发现 evaluator 评分前偷偷跑了 JSON sanitizer 修复畸形输出（虚高）→ 用裸 `json.loads`+`jsonschema` 重评，差距**坍缩到 +1.4** → 裁决 **WARN_corrected「诚实但不杀稿」**。executor 此处**完全沉默（弧最低点）**，reviewer 主导审计。｜ motif: Tok|yo 即罪证 · bounce=0

**B09 重跑 ACCEPT / Honest Re-run ACCEPT** — `S16`
- `S16`: 诚实重跑面板，`exact_parse` 稳定在 `0.78 → 0.89`，绿色 **ACCEPT** 印章（REJECT 的反面）。executor 轻轻直起身、**小幅度地蹦了一下**。气泡:「这次……是真的。」｜ motif: bounce 回归但收敛（弧恢复·sober）

**B10 论文落笔 / Paper-writing Wrap** — `S17`
- `S17`: 文稿面板，键入诚实结论:「schema-keyword-first 带来 **+1.4**（修正后），范围限定 schema 受限场景。」角落小图标重现已修复的 `{"city":"Tokyo"}`（Tok|yo **闭环**）。旁白:「按它真实的样子写下来。」

**B11 深夜 + 提交 / Late-night + Submission** — `S18`,`S19`
- `S18`: 暖色——研究员夜色中走回家，路灯。旁白:「他往回走。」
- `S19`: 提交界面 `Submitted ✓`，DDL 跳到 `T-00:42`。暗世界里 duo 静静看着。｜ motif: DDL=00:42（呼应 24:00 起点）

**B12 归来 / The Return** — `S20`,`S21`
- `S20`: 暖色清晨，研究员推门，看见屏上完成的工作，怔住。那只**咖啡杯已冷**、无热气（B01 回调）。
- `S21`: 研究员与 duo 隔屏轻轻**击掌**，executor 这次只**微微一蹦**（弧的兑现:兴奋→谦卑→沉淀）。旁白:「我把那 24 小时交出去了——它没辜负。」｜ motif: mug=冷 · bounce=最小

**B13 品牌释出 / Brand Release** — `S22`
- `S22`: duo 与这趟研究化作星座（idea→实验→审计→ACCEPT 连成星轨），下方 **ARIS logo** + tagline:「你不在的时候，研究在 / While you're away, the research carries on.」

---

**优化的 through-line**: 每个非中心 beat 都服务两条线——(1) 把 Tok|yo 破 JSON 从 B09 埋点→B07 现形→B08 定罪→B10 闭环，让非 ML 读者用一个"坏数据被抓"的具体物证看懂 +6.2→+1.4 为何重要；(2) 用 bounce 高度做 executor 的情绪温度计（B02 最高→B07 下挫→B08 归零→B09/B12 收敛回归），无需文字即可读出谦卑弧。咖啡杯（热→冷）与 DDL（24:00→00:42）作贯穿计时器，B01/B12 首尾扣合。

**vs 22-shot skeleton 的增删**: 基本 1:1 保留 13 beats / 22 panels；唯一实质改动是把 Tok|yo 的"首次埋点"明确前移到 B06-S09（原 skeleton 只在 B07 才出现），让 B07 的 REJECT 与 B08 的审计有可回指的物证伏笔，其余 panel 数与归属未变。