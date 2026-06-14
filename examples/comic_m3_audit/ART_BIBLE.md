# ARIS 连环画 — ART BIBLE (画风圣经 / 收敛靶)

> **这份文件是 panel_gate 的评分基准 + 每次生成 prompt 的附加约束。**
> 生成时整段贴进 codex prompt;审稿时每个视觉 reviewer 拿它当 rubric——`style_consistency` / `identity_consistency` 的字面定义就是"符合本文件",不是凭感觉。
> 无 ground-truth spec,跨模型 gate 会永远吐"style drift"却没有收敛方向(设计 §3.6)。

版本 `art-bible/1.0` · 锁定 2026-06-08 · 项目 `aris_comic_v1`

---

## 0. 总风格声明(用户 2026-06-08 批准)

**像素风 chibi 连环画**,定档在"**像素世界 + 像素双人 + 半平滑主角**"这一档(= 批准的 `probe/S02_codexgen_a01.png` 那个程度):

- **场景/家具/道具**:明确像素化(块状、硬边、有限色阶),**不是**平滑插画。
- **ARIS 双人**:扁平细节像素 chibi(对齐 `duo_canonical_ref_v001`),**不是**厚重 3D 体素 —— gemini 发现过 flat-2D↔voxel 漂移,**本片一律走 flat 细节像素,禁止 voxel 立体块**。
- **人类主角(研究者)**:chibi 比例,可保留**略平滑的脸/表情**(别剁成马赛克),但发型/轮廓/环境仍是像素质感。
- **下游渲染**:viewer 一律 `image-rendering: pixelated` + 整数倍缩放,**禁止非整数缩放**(会糊成一团,毁掉像素风的唯一理由)。

---

## 0.5 双世界色调(用户 2026-06-09 选 B —— 暖人间 + 暗赛博,对比生张力)
全片不是一味暗黑极客。**按"世界"分冷暖**,对比才有呼吸和温度:
- **真实世界 = 暖**:卧室 / 校园 / 实验室 / 真人主角 + 物理场景 —— Edison 暖灯、暖木色、夜城窗、温馨。chibi 小人在真实世界出现时也沐在暖光里。
- **数字 ARIS 世界 = 暗黑霓虹极客**:wiki 空洞 / 终端 / 代码 / 方法图 / 审计数据面板 —— `dark_navy_void #0A0E27` + 霓虹色板。
- **technical 产物(方法图/JSON/曲线/审计代码)= 数字世界 → 保持暗黑**,即使出现在暖场景里也是"屏幕里发光的暗物"。
- **审计/讨论的场景**:可走"暖实验室"(人在真实世界看屏)或"暗数字空间"(人进了 wiki 空洞)——按 beat 选,但两者并存、别全暗。
- gate 评 `style_consistency` 时:**冷暖是 by-design 的,不是漂移**;只标"该暖的场景冷了 / 该暗的数字物暖了"这种错配。

### 0.6 STYLE_PREFIX（machine-readable — `build_prompt.py` 按 panel 的 `world` 读取这几行；≤200 字符，无镜头/光圈词）
STYLE_PREFIX[warm-lab]: flat pixel-art comic; warm real-world interior — Edison-lamp glow, warm wood, cozy lab/bedroom, cold-blue night city out the window; chibi cast in warm light; 1-step shading, crisp integer pixels
STYLE_PREFIX[dark-cyber]: flat pixel-art comic; digital ARIS world — dark_navy_void #0A0E27 + neon (warning-red/amber/invariant-purple/success-green); wiki-void / terminal / audit panels; 1-step shading, crisp integer pixels
STYLE_PREFIX[starfield]: flat pixel-art; full-bleed dark-navy starfield — glowing star-nodes + thin connecting lines, NO characters; deep night palette, 1-step shading, crisp integer pixels

## 1. 角色身份锁(authority = `movie-wiki/assets/refs/sprites/duo_canonical_ref_v001.png`)

每个出现双人的格子,**必须**把 `duo_canonical_ref` 作为 condition 注入;身份不对 = panel_gate 直接 reject。

| 角色 | 衣服 | 头发 | 胡子 | 采样 hex |
|---|---|---|---|---|
| **executor(执行者)** | 蓝 hoodie | 棕 | **无** | hoodie `#1D4684` · hair `#925935` |
| **reviewer(审查者)** | 绿 hoodie | 近黑 | **有(络腮)** | hoodie `#30582D` · hair `#0F0D16` |

- 肤色:暖浅棕褐(从 ref 取,约 `#E8B894` 一档,**采样点偏暗勿直接用**,以 ref 视觉为准)。
- **铁律**:executor 永远蓝+棕发+无须;reviewer 永远绿+黑发+有须。**左右位置可变**(gutter 容差),但**颜色/胡子/体型轮廓不可变**。
- 比例:大头小身 chibi,头近方、五官简化。

## 2. 主角(研究者 chibi)
黑框眼镜 + 黑/深色短发 + 黑 T + 双肩包带。chibi 大头比例。脸可略平滑保表情,其余像素。**跨格保持同一人**(眼镜/发型/服装不变)。

## 3. 线条 / 阴影 / 色阶
- 硬边像素,角色 + 实体前景道具上**无抗锯齿渐变**。
- 角色阴影:**flat 或 1 阶**(最多一档暗色块),角色身上**禁止平滑渐变阴影**。
- 有限调色板,块状上色。
- **⚠️ 背景氛围光是允许的(reviewer 校准 2026-06-08)**:wiki 空洞的中心辉光 / bloom / 屏幕发光 / 体积光 / 消失线这类**背景大气光效**,可以用平滑/连续渐变 —— 这是氛围,不是"像素违规"。**"禁渐变"只约束角色表面 + 实体前景物,不约束背景大气光。** 评 `style_consistency`/`artifact_severity` 时不要因为背景辉光是渐变就判高伪影。

## 4. UI / 叙事色板(继承 `ui_design_system`,叠加层用)
`warning_red #FF3366` · `amber #FFB000` · `invariant_purple #B066FF` · `success_green #00C896` · `dark_navy_void #0A0E27`。
—— 这些用于 overlay 数据图/印章/system tag(REJECT 红、invariant 紫、ACCEPT/RE-RUN 绿、wiki 空间深蓝底)。

## 5. 画幅 / 构图
- 源图 **16:9**(对齐种子;codex 实际可能产 1672×941 等 ≈16:9 大图,viewer 按格 CSS 裁成 hero/宽/方/高,**不重生成别的比例**)。
- 镜头语言:establishing(宽)/ dialogue(中近)/ reaction(近)/ hero(大)。B08 回滚 2×2 用近方裁,保 chibi 不被压扁。

## 6. 文字 / 气泡 —— 两种模式(html 留白 / baked 烤字)

> **更新 2026-06-09(B08 这一页已切 `baked`)**:烤字对弈已做,codex 烤 CJK 实测干净,用户偏好 → B08 panels 默认 `text_mode:"baked"`:**气泡对白 + 技术图文字直接烤进图**。baked 格的 gate **不查** `safezone`/`stray_text`(图里本该有字),改查 `baked_text_quality`(气泡清晰不乱码,≥4)+ `observed_literals` 与 authored `expected_literals` 的**数字保真 token-diff**(双 reviewer 盲转录)。视觉 reviewer 评 baked 格时**不要**把"图里有字"当违规扣分。以下 html 规则保留给仍用 `text_mode:"html"` 的格(如纯场景/无技术图的格)。

**HARD RULE(`text_mode:"html"` 模式)**:**codex 生成的图里不画任何文字/气泡/字形/标签**,只画人+景,并**留一块干净低细节"安全区"**(见 comic.json `safe_zones`)给文字层。整个气泡(框+尾+字)由 HTML/CSS/SVG 画。
- 理由:设计经两轮跨模型锁定 —— 烤字会乱码(尤其 CJK)、且烤死的框框不住会重排的双语文字。
- **双语**(zh + en),英文通常更长,**留白按更长的(一般 EN)留**;`text_fits_safezone` gate 对两种语言都验。
- gate 检查 `safezone_present`(留白区存在)+ `stray_text_absence`(此模式下图里**不得**出现任何字形)。

**显式 PENDING 实验(唯一未决项,不影响默认锁)**:用户 2026-06-08 重新提出"AI 烤字会不会更好"。等 codex image_gen 冷却后补一次烤字对弈(②);**仅当**实测 AI 烤 CJK 干净 **且** 用户明确偏好,才把 `text_mode` 切到 `baked`(届时本节改为"气泡由生成层画,文字必须正确无乱码、放进安全区")。代码画(③,PIL/SVG)是第三备选。在用户拍板前,**默认锁 html 不变**。

## 6.5 环境叙事密度(Environmental Narrative Density —— 用户 2026-06-09 品味校准,靶 = `cal_S12_a01`)

用户偏好的质感:场景要**"满"而有故事**,不是只有人 + 一块主屏幕的空荡构图。最丰富的参考 = `cal_S12_a01`(暖光研究室那张)。每格都按这个密度来:

- **领域叙事道具(要可读、与本格主题相关)**:书脊(如 `LLM DECODING` / `STRUCTURED OUTPUTS` / `EVALS FIRST`)、手写 TODO 便签(如 `better masks ☐ / schema locks ☐ / evals ☑`)、笔记本屏幕上**真实可读的代码片段**(如 `def exact_parse(json_str, schema): ...`)、主题马克杯(`ML RESEARCH` / `</>`)、绿植、纸张/键盘/外设、暖台灯。这些是"讲环境故事"的细节,不是填空。
- **单格内冷暖对比**(§0.5 在一格里也成立):暖室内前景 + **窗外冷蓝夜城**;暗赛博场景里则用霓虹冷光 + 暖点缀(台灯/咖啡)破闷。
- **技术图保持细节**:方法图/审计图**不要简化**,带逐 step 注解(如 `span 跨边界切碎` / `span ⊆ schema`、`t0..t3` 阶段)。技术图是内容权威(来自 content_svg 蓝图),环境道具是次要叙事层 —— 别让道具文字与 `expected_literals` 撞车。
- **文字清晰锐利**:所有 baked 文字(标题/标签/代码/数字/气泡)必须清晰可读、不糊不乱码。
- **gate 取向**:`composition_readability` / `narrative_beat_fidelity` 奖励"环境讲了故事"的丰富度;空荡、道具稀少、技术图被简化 = 偏弱。**但这是质量梯度,不是硬 reject** —— 身份锁 + 数字保真(`expected_literals`)+ 烤字清晰仍是硬门。

## 7. FORBIDDEN(出现即扣分/reject)
- 角色上的平滑抗锯齿渐变 / 写实照片质感
- 3D 体素立体块(本片走 flat 像素)
- mascot 非 canonical 配色(蓝/绿/棕/黑以外乱来)
- 非整数缩放导致的糊像素
- (默认方案下)图里出现任何文字/字形/乱码气泡
- 把 reviewer 画成无须 / executor 画成有须(身份错)

---

## OPEN(待补)
1. **文字渲染方案** —— **默认已锁 html(§6),不阻塞**。唯一 pending:等 image_gen 冷却补"AI 烤字"对弈(②);仅当实测干净且用户偏好才切 baked,否则保持 html。
2. 主角"半平滑"的确切档位 —— P0 第一个真章节出图后微调。
3. 精确肤色 hex —— 从 ref 重采样(当前采样点偏暗)。
