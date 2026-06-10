# B01–B13 Comic Outline — "ARIS：我把那 24 小时交出去了 / I Handed Over Those 24 Hours"
LENS: faithful adaptation of the 22-shot video storyboard → static pixel-art comic panels. Centerpiece B08 (S12–S15, M3 audit) is DONE and kept as-is.

---

**B01 — 卧夜·倒计时锚 / Bedroom, the Countdown Anchor** — owns S01
- **S01:** WARM palette. Wide static panel: researcher slumped at laptop, coffee mug steaming, wall clock + corner HUD `DDL T-24:00:00`. Side-narration: "还有 24 小时。一个 dllm schema 任务，一夜的睡眠。" Baked: tiny laptop sticky-note "dllm-schema-keyword-first". *Motif: mug STEAMING; DDL 24:00:00; Tok|yo absent.*

**B02 — 交接·executor 弹起 / The Hand-off** — owns S02
- **S02:** Split WARM→DARK. Top: hand on Enter, terminal `$ aris run --task dllm-schema-keyword-first --deadline 24h`. Bottom (DARK): duo wakes inside the laptop, blue executor mid-bounce 🟦↑, green reviewer steady. Baked exec: "交给我！" reviewer: "我盯着。" Side-narration: tagline "你不在的时候，研究在。" *Motif: bounce HIGH (arc start); DDL 23:59.*

**B03 — 双线·校园∥头脑风暴 / Parallel: Campus ∥ Idea-Creator** — owns S03, S04
- **S03:** WARM. User walking to class, backpack, phone in hand, empty hall. Side-narration: "她去上课了。" *Motif: mug left behind on desk (steam fading).*
- **S04:** DARK. idea-creator panel: duo around a floating idea-board, sticky candidates fanning out. exec gesturing 🟦. Baked reviewer: "先铺想法。" Side-narration: "ARIS 在脑暴。"

**B04 — 查新·14/20 存活 / Novelty-Check, Survives** — owns S05
- **S05:** DARK. Content-SVG blueprint: a novelty gauge needle at **14/20**, one idea card glowing, others greyed. Stamp: `NOVEL ✓`. Baked exec: "这个能活！" Side-narration: "14/20——过线，留下。"

**B05 — 课堂·一拍怀疑 / Classroom, a Beat of Doubt** — owns S06
- **S06:** WARM. User in lecture seat, chin on hand, faint thought-bubble of the laptop. Side-narration (inner monologue): "……它现在到哪了？我是不是太冒险了。" *Motif: DDL faint in bubble ~T-19:00; mug absent (she's away).*

**B06 — 实验桥·曲线起飞 / Experiment-Bridge, the Curve Lifts** — owns S07, S08, S09
- **S07:** DARK. GPU rack spinning up, fans as pixel-glow, `wandb` boot line. Baked exec: "上 GPU！"
- **S08:** DARK. Content-SVG: **exact_parse curve climbing 0.60 → 0.71**, reviewer reading the plot. Side-narration: "曲线在爬。"
- **S09:** DARK. exec proud pose 🟦✨ beside the rising curve. Baked exec: "看见没，涨了。" *Motif: bounce still HIGH.*

**B07 — 审稿环·REJECT 与碎 JSON / Auto-Review REJECT** — owns S10, S11
- **S10:** DARK. Round-3 panel: curve DIPS, alarm tint. Content-SVG: broken `{"city":"Tok|yo"}` glitching on screen. Side-narration: "第 3 轮——有东西不对。" *Motif: Tok|yo FIRST APPEARANCE.*
- **S11:** DARK. Big red `REJECT` stamp slams down; exec deflates 🟦↓ shoulders dropping; reviewer steps forward. Baked reviewer: "别急着信这个数。" *Motif: bounce DROPS (pre-low).*

**B08 — 🌀 诚实审计中心幕（已完成）/ THE M3 AUDIT CENTERPIECE (DONE)** — owns S12, S13, S14, S15
- **KEEP AS PRODUCED.** Corrected M3-audit story: schema-keyword-first looked **+6.2** → adversarial audit finds the evaluator secretly ran a JSON sanitizer repairing malformed output BEFORE scoring → raw `json.loads` + `jsonschema` re-eval collapses gap to **+1.4** → verdict **WARN_corrected**（诚实但不杀稿）. exec SILENT 🟦… (arc low point); reviewer drives. *Motif: Tok|yo is the smoking gun; bounce ZERO.*

**B09 — 重跑·ACCEPT / Honest Re-run, ACCEPT** — owns S16
- **S16:** DARK. Content-SVG: honest curve settles **0.78 → 0.89**; green `ACCEPT` stamp (mirror of B07's REJECT). exec recovers, smaller upright posture 🟦 (tempered, not bouncing). Baked exec: "这次……是真的。" Side-narration: "诚实地重跑，过了。" *Motif: bounce RETURNS but smaller; Tok|yo resolved.*

**B10 — 收尾·诚实成稿 / Paper-Writing, Written Honestly** — owns S17
- **S17:** DARK. Duo at a draft page: claim text "+1.4, scope-limited" + a small inset of the fixed JSON. reviewer nods. Baked reviewer: "照实写，带上边界。" Side-narration: "+1.4，写清楚它的边界。" *Motif: Tok|yo CALLBACK as the now-clean snippet.*

**B11 — 深夜·投出去 / Late Night, Submission Goes In** — owns S18, S19
- **S18:** WARM. User walking home, dark street, phone glow. Side-narration: "她在回家的路上。"
- **S19:** Split. DARK terminal `submission: SENT`, HUD `DDL T-00:42`. Baked exec: "投了。" *Motif: DDL 00:42 (tight); bounce small.*

**B12 — 归家·凉掉的咖啡 / Homecoming, the Cold Mug** — owns S20, S21
- **S20:** WARM. User opens laptop, sees it done; same mug now **COLD** (no steam, callback to S01). Side-narration: "她回来了。咖啡，凉了。" *Motif: mug STEAM→COLD payoff.*
- **S21:** WARM∥DARK seam. Quiet hand-clap: user's palm meets the duo's tiny raised hands through the screen. exec bounce SMALLEST 🟦 (arc payoff — humbled, warm). Baked exec: "……欢迎回来。" Side-narration: "干得好。"

**B13 — 品牌·星座收束 / Brand Release, the Constellation** — owns S22
- **S22:** DARK→starfield. Duo + the night's research nodes drawn as a constellation; ARIS logo. Tagline baked: "你不在的时候，研究在 / While you're away, the research carries on." *Motif: all motifs resolved; mug-cold + clean-JSON + ACCEPT as faint constellation stars.*

---

**Through-line I optimized & deltas vs the 22-shot skeleton:**
- **One-to-one fidelity:** all 22 shots → 22 panels, no cuts/merges/adds; beat boundaries B01–B13 preserved exactly so the comic stays a faithful adaptation.
- **Three carried motif-arcs** thread every relevant panel and pay off in B12–B13: **mug** (steam S01 → fading S03 → COLD S20), **executor bounce** (HIGH S02/S09 → DROP S11 → ZERO S12–15 → small-return S16 → smallest-warm S21), **Tok|yo JSON** (born S10 → smoking-gun S12–15 → clean-callback S17 → constellation star S22), with **DDL countdown** (24:00 → 19:00 → 00:42) as the ticking spine.
- **REJECT(S11)↔ACCEPT(S16)** framed as deliberate mirror stamps so the centerpiece audit reads as the hinge between them; WARM/DARK two-world palette split is the constant visual grammar (human beats warm, ARIS beats dark-cyber, with three explicit seam panels S02/S21).