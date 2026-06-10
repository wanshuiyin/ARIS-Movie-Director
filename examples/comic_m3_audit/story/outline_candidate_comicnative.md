# B01–B13 漫画分镜大纲 / Full Comic Outline
*ARIS — 我把那 24 小时交出去了 (I Handed Over Those 24 Hours)*
*Tagline: 你不在的时候,研究在 / While you're away, the research carries on*

---

**B01 — 交付前夜 / The Eve (T-24:00:00)** · `S01` · WARM
- **P01** [1-panel, full bleed] 暖光卧室,研究员伏案笔记本,咖啡杯**冒热气**;墙上 DDL 计数器亮红 `T-24:00:00`。侧栏旁白:"距离截止 24 小时。我只剩一个想法和一夜睡眠。" · *motif: 🟢mug=steaming, ⏱DDL=24:00*

**B02 — 交接 / The Hand-Off** · `S02` · WARM→DARK split
- **P02** [2-up, 左暖右暗] 左:手敲下 `$ aris run --task dllm-schema-keyword-first --deadline 24h`;右:笔记本内部 cyber 空间里蓝(执行)绿(审查)二人组睁眼苏醒,蓝人**蹦起来**。烘焙台词 蓝:"接到!上工——" 绿:"……先看清楚需求。" · *motif: 🦘bounce=MAX(弧起点)*

**B03 — 并行 / Parallel Cut** · `S03,S04` · split
- **P03** [2-up] 左暖:研究员背包走向教学楼,晨光;右暗:idea-creator 面板,绿人贴便签脑暴想法群。侧栏:"他去上课。我们开始想。" · *mug 已不在画面;DDL=21:30*

**B04 — 查新存活 / Novelty Survives** · `S05` · DARK
- **P04** [1-panel] novelty-check 仪表盘,一条想法亮 `14/20 ✓ SURVIVES`,其余灰掉。烘焙 绿:"14 分,够独。留下。" 蓝(小字):"我就说!" · *bounce=high*

**B05 — 教室里的迟疑 / A Beat of Doubt** · `S06` · WARM
- **P05** [1-panel] 教室剪影,研究员望窗外,头顶思想气泡半透:`它真能跑对吗…?`。侧栏旁白:"我把它交出去了。然后开始怀疑自己。" · *纯人世界喘息拍*

**B06 — 实验桥 / Experiment Bridge** · `S07,S08,S09→1 panel` · DARK
- **P06** [2x2 合一页] 四格:①GPU 点亮 ②wandb `exact_parse` 曲线起步 `0.60→0.71↗` ③绿人读 schema ④蓝人**叉腰得意**。侧栏:"GPU 醒了。曲线在爬。" · *bounce=proud；曲线 motif 首现*

**B07 — 第三轮驳回 / REJECT (Round 3)** · `S10,S11` · DARK
- **P07** [2-up] 左:曲线**回落**一截;右:破损 JSON `{"city":"Tok|yo"}` 浮现,**REJECT** 红章砸下。烘焙 绿:"Round 3，驳回。" 蓝**蔫下来**:"……哪儿错了?" · *bounce↓deflate；🧩Tok\|yo motif 首现（埋钩）*

**B08 — 🌀 诚实审计中心台 / THE M3 AUDIT [已完成]** · `S12,S13,S14,S15` · DARK
- **保持现状**:schema-keyword-first 表面 `+6.2` → 对抗审计揪出 evaluator 偷偷跑了 JSON sanitizer 在评分前修好坏输出(虚高)→ 裸 `json.loads`+`jsonschema` 重评把差距塌缩到 `+1.4` → 判决 **WARN_corrected「诚实但不杀稿」**。蓝人此处**全程沉默**(弧最低点),绿人主导审计。 · *bounce=SILENT；Tok\|yo 在此被复用为证据*

**B09 — 诚实重跑通过 / Honest Re-run ACCEPT** · `S16` · DARK
- **P08** [1-panel,与 P07 镜像对称] 重跑曲线稳落 `0.78→0.89`,**ACCEPT** 绿章落下(REJECT 的反面)。烘焙 蓝(收敛地):"这次…是真的。" · *bounce=tempered 恢复*

**B10 — 诚实成稿 / Honest Write-up** · `S17` · DARK
- **P09** [1-panel] paper-writing 面板,稿纸写下 `+1.4 (corrected), scope-limited`,角落贴着那张修好的 `Tok\|yo` 卡作脚注。绿:"照实写。范围标清楚。" · *🧩Tok\|yo 第三次回收闭环*

**B11 — 深夜投出 / Submission Goes In** · `S18,S19` · WARM→split
- **P10** [2-up] 左暖:研究员夜路回家,路灯;右暗:进度条 `SUBMITTED`,DDL `T-00:42`。侧栏:"他还在回家路上。稿子已经投出去了。" · *⏱DDL=00:42*

**B12 — 到家 / Coming Home** · `S20,S21` · WARM
- **P11** [2-up] 左:研究员推门见屏幕亮着 `DONE`,**咖啡杯已凉**(回扣 P01);右:隔屏与二人组**轻轻击掌**,蓝人这次**只是微微一颠**。侧栏:"它做完了。咖啡早就凉了。" · *🟢→⚪mug=cold(闭环)；bounce=small(弧收束)*

**B13 — 品牌收尾 / Brand Release** · `S22` · DARK→星图
- **P12** [1-panel, full bleed] 二人组与整夜研究化作**星座连线**,ARIS logo 升起。大字 Tagline:"你不在的时候,研究在 / While you're away, the research carries on." · *收束镜*

---

### 我优化的贯穿线 & 增删说明 / Through-line + Changes vs 22-shot skeleton
- **Through-line**:三条 motif 缝合静态阅读——咖啡杯(热→凉 P01→P11)锚定人世时间,`exact_parse` 曲线(爬→落→稳 P06→P07→P08)锚定研究节律,蓝人弹跳(MAX→沉默→微颠)做角色弧;`Tok|yo` 破损 JSON 三次回收(P07 埋钩→B08 当证据→P09 当脚注)是中心台的逻辑钩。REJECT(P07)与 ACCEPT(P08)做镜像对称,让翻页有"翻面"快感。
- **合并**:S07-S09→P06 一页 2x2(运动镜在静态里冗余);B08 四镜保持为已完成中心台,不动。
- **未增删 beat**:13 beats 全保留;22 shot 压到 **12 panels**(B08 内部 4 shot 仍算 1 个中心跨页单元),页面节奏 full-bleed / 2-up / 2x2 交替,适配滚动翻页 + 侧栏旁白。