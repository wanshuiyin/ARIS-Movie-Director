---
name: comic-style-bible-lock
description: "Phase-1 (S2) of the comic-author suite — compile the project's ART_BIBLE.md into an EXECUTABLE convergence target, not aesthetic prose. The bible is the ONE visual dialect read verbatim into every bake prompt AND into every visual reviewer's rubric (`style_consistency`/`identity_consistency` literally = 'conforms to this file'). A `bootstrap` parses the bible into immutable per-dimension `style_anchor` wiki nodes (palette / line / shading / two-world warm-vs-cyber lighting / identity-lock / text-mode / forbidden / by-design exceptions); a deterministic `validate` lints candidate authoring text against the FORBIDDEN list + identity-lock + world-mismatch; an append-only `update` Gemini-harvests recurring drift from KEEP panels into by-design exceptions. Auto-bootstrap if the bible is missing; otherwise LEAVE LOCKED. Locked anchors are immutable — pivoting the style = a fresh project, never an in-place edit."
argument-hint: [bootstrap | validate <authoring_text> | update] [--project <dir>]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, mcp__gemini__analyzeFile, mcp__gemini-cli__ask-gemini
---

# comic-style-bible-lock — the Style Bible as an Executable Gate Rubric (Phase 1 · S2)

The **S2 step of [`comic-author`](../comic-author/SKILL.md)**: turn `ART_BIBLE.md` from a wall of taste
adjectives into a *machine-addressable convergence target*. The bible is the **single visual dialect** that is
(a) read **verbatim into every bake prompt** so each frame converges to the same look, and (b) read **verbatim
into every visual reviewer's prompt** so the cross-model `panel_gate` scores `style_consistency` /
`identity_consistency` against a *ground-truth spec* — not against the reviewer's vibe. The bible literally
declares this of itself:

> `style_consistency` / `identity_consistency` 的字面定义就是"符合本文件",不是凭感觉。
> 无 ground-truth spec,跨模型 gate 会永远吐"style drift"却没有收敛方向。
> — `examples/comic_m3_audit/ART_BIBLE.md`, lines 3–5

That second line is the **whole reason this skill exists**. Without one source of truth a cross-model gate
emits endless "style drift" with **no convergence direction**, and the film silently grows **two visual
dialects**. This skill locks each dimension to a named anchor so the gate has an individually-addressable,
source-pinned target instead of one prose blob — **one visual dialect, never two**.

```text
  ART_BIBLE.md (taste, user-approved, dated, probe-anchored)
        │
        ▼
  ① bootstrap  ── deterministic parse → ONE immutable style_anchor node per dimension
        │           (palette · line · shading · two-world warm/cyber lighting · identity-lock
        │            · text-mode · forbidden · by-design exceptions)  +  EXACT style_bible gate (6 dims ≥4, 5 vetoes)
        ▼
  ② validate <authoring_text>  ── deterministic lint (NO LLM): FORBIDDEN vocab + identity-conflict + world-mismatch
        │                          → called by every downstream author step BEFORE the text enters a bake prompt
        ▼
  ③ update  ── (after ≥1 KEEP panel) Gemini-harvest recurring drift → APPEND-ONLY by-design exception anchors
                (≥50% same-beat quorum, cross-model only) — never rewrites the baseline
```

## Role
Compile, lock, and police the project's locked visual identity across the comic lifecycle. You **own** the
3-subcommand lifecycle — `bootstrap` (bible → immutable anchors + gate), `validate` (deterministic lint of
candidate authoring text), `update` (cross-model drift-harvest into append-only exceptions) — and the
**EXACT `style_bible` gate** below. You do **not** invent taste: every anchor traces to a user-approved, dated,
probe-anchored line in `ART_BIBLE.md`. If the bible is missing you auto-bootstrap a scaffold and **escalate to
the user for approval**; if it exists and is locked you **leave it locked** and only ever *add* by-design
exceptions. The convergence guarantee — "one visual dialect, never two" — is enforced here or nowhere.

## Constants
- **BIBLE** = `<project>/ART_BIBLE.md` — the source of truth; **version-stamped + dated + project-pinned**
  (real: `version art-bible/1.0 · 锁定 2026-06-08 · 项目 aris_comic_v1`).
- **ANCHOR_DIR** = `<project>/wiki/nodes/` — one `style:<slug>.json` per dimension (`node_type: style_anchor`).
- **DRIFT_REVIEWER** = `mcp__gemini__analyzeFile` (`auto-gemini-3`) — the **visual** drift reviewer for `update`.
  Cross-model independence: the executor (Claude) only *aggregates* Gemini's JSON; it never judges drift itself.
- **QUORUM** = `(n+1)//2` (≥50%) of the **same-beat** multi-panel drift samples must flag a dimension before an
  exception is written (bump to 75% if drift-from-noise floods). One noisy panel must **not** mutate the bible.
- **MAX_PANELS_PER_UPDATE** = 6 (cost cap on the Gemini drift pass).
- **GATE** = the deterministic `style_bible` gate (6 dims ≥4 + 5 hard vetoes) — **rule-check, NO cross-model
  gate** (the bible IS the rubric the *other* skills' cross-model gates consume; here we only certify it compiles).
- **IMMUTABLE BASELINE** — `bootstrap` anchors and the §0–§7 spine are **locked**. `update` only *appends*
  exception anchors; pivoting the baseline = a **fresh bootstrap in a NEW project dir**, never an in-place edit
  (the cross-model gate must always compare new output against the ORIGINAL anchors). See `acceptance-gate` (locked=immutable).

## The §0–§7 section spine `bootstrap` asserts (the worked example's structure)
`bootstrap` requires the bible to carry this exact spine — each section is the source of one or more anchors.
Copy `examples/comic_m3_audit/ART_BIBLE.md` as the shape:

| § | Section | What it pins | Anchor(s) emitted |
|---|---|---|---|
| **§0** | 总风格声明 (overall style) | register, anchored to a **NAMED probe image** + **dated user approval** (real: `= 批准的 probe/S02_codexgen_a01.png 那个程度`); `image-rendering: pixelated` + integer-multiple scaling | `style:overall_register` |
| **§0.5** | 双世界色调 (two-world palette) | **warm 人间** vs **dark 赛博** (`dark_navy_void #0A0E27`), with the baked gate instruction **`冷暖是 by-design 的,不是漂移`** | `style:palette_warm_world`, `style:palette_dark_world`, `style:by_design_warm_cyber` |
| **§1** | 角色身份锁 (identity lock) | authority-ref pointer (`duo_canonical_ref_v001.png`) + per-character **hex table** + the 铁律 | `style:identity_executor`, `style:identity_reviewer`, `style:identity_authority_ref` |
| **§2** | 主角 chibi (researcher) | researcher chibi spec (glasses/hair/backpack, same person across panels) | `style:researcher_chibi` |
| **§3** | 线条 / 阴影 / 色阶 | hard-edge pixels, **no smooth gradient on character/foreground** + the **reviewer-calibrated background-atmosphere carve-out** (dated `2026-06-08`) | `style:line_shading` |
| **§4** | UI / 叙事色板 | overlay token palette (warning_red / amber / invariant_purple / success_green / dark_navy_void) | `style:ui_palette` |
| **§6** | 文字 / 气泡 | **text modes `html \| baked \| code`** + the decision history (incl. the explicit PENDING duel) | `style:text_mode_contract` |
| **§6.5** | 环境叙事密度 | density target image, marked **quality-gradient-NOT-hard-reject** (target `cal_S12_a01`) | `style:env_density` (`hard_reject: false`) |
| **§7** | FORBIDDEN | the explicit ban list (incl. the **voxel ban** after gemini found flat-2D↔voxel drift) | `style:forbidden` |

## Procedure

### ① `bootstrap` — compile the bible into immutable anchors (+ certify the gate)
Run once per project, before any other S-step authors text. Re-run is **idempotent** (overwrites byte-identical).

1. **Assert the bible exists.** If `<project>/ART_BIBLE.md` is **missing** → **auto-bootstrap**: write a §0–§7
   scaffold from the table above with every taste field a `TODO(user-approve)` placeholder, append a log line,
   and **STOP — escalate to the user** for the §0 probe-image + §0.5 world choice + §1 hex table + §6 text-mode
   approval. Never fabricate a probe image, a hex, or a user-approval date. (exit 2)
2. **Assert version + lock + project stamp + user-approval dates.** Grep for the `version art-bible/…` line,
   the `锁定 <date>` lock, the project id, and at least one dated user-attributed approval line (`(用户 <date> …)`).
   Any missing → **veto** (see gate); do not proceed.
3. **Assert the §0–§7 spine compiles.** Grep each section header from the table above. A missing §0 (no probe +
   approval), §0.5 (no by-design instruction), §1 (no authority ref / hex table), §6 (no text-mode), or §7
   (no FORBIDDEN list) is a **hard veto**.
4. **Deterministic parse → ONE `style_anchor` node per dimension.** Regex-grab the §0.5 palette block, the §1
   hex table, the §3/§4 rules, the §6 mode list, the §7 FORBIDDEN list, and the §0.5 by-design exceptions. Emit
   exactly the anchors in the table's right column. Node shape (matches `schemas/node_schema.json` →
   `style_anchor`, payload **required** `dimension, value, source, locked`):
   ```json
   {
     "node_id": "style:identity_executor",
     "node_type": "style_anchor",
     "title": "identity-lock — executor (blue hoodie, brown hair, NO beard)",
     "status": "locked",
     "created_at": "2026-06-08T00:00:00Z",
     "tags": ["style_anchor", "baseline", "identity"],
     "payload": {
       "dimension": "identity:executor",
       "value": {"hoodie": "#1D4684", "hair": "#925935", "beard": false,
                  "iron_law": "executor 永远蓝+棕发+无须;L/R 位置可变,颜色/胡子/体型轮廓不可变"},
       "source": "ART_BIBLE.md §1 (authority duo_canonical_ref_v001.png)",
       "locked": true
     }
   }
   ```
   Every anchor sets `status: "locked"`, `payload.locked: true`, `payload.source` = the exact §-section it came
   from, and `tags` include `["style_anchor","baseline"]`. The §6.5 density anchor additionally carries
   `payload.value.hard_reject: false` (quality gradient, NOT a hard reject).
5. **Run the EXACT `style_bible` gate** (below). All 6 dims ≥4 and **no** veto → write the anchors, append a
   line to `<project>/wiki/log.md`, print `{anchors_written, n_anchors, gate}`. Any dim <4 or any veto → **fail
   closed**, write nothing, print the failing dim/veto + the §-section to fix (exit 1).
6. **Wire the convergence target.** The bible pointer lives in the **pointer-hub manifest
   [`movie.project.json`](../../examples/comic_m3_audit/movie.project.json), field `art_bible`** — NOT in
   `comic.json` (comic.json has no `style_bible`/`art_bible` key; its top keys are
   `schema_version/comic_id/asset_root/meta/defaults/ui_tokens/identity_refs/pages/panels`, and
   [`comic-json-compiler`](../comic-json-compiler/SKILL.md) is the owner that emits `movie.project.json` as "the
   pure pointer-hub manifest"). Confirm `movie.project.json.art_bible` resolves to this project's `ART_BIBLE.md`
   (and `movie.project.json.comic_json` to `comic.json`); if the `art_bible` field is missing, **escalate to
   comic-json-compiler to add it** — do not invent a `comic.json` edit. Then confirm every downstream
   bake-prompt builder reads the bible verbatim (the [`comic-panel-prompt-builder`](../comic-panel-prompt-builder/SKILL.md)
   prepends `style:overall_register` + the relevant world/identity/forbidden anchors). This is the
   "one dialect into every prompt" guarantee, made mechanical.

### ② `validate <authoring_text>` — deterministic lint (NO LLM)
Called by **every** downstream author step (intent / outline / storyboard / blueprint / prompt) **BEFORE** the
text is allowed into a bake prompt. Pure Python, no model call — fast, reproducible, fork-proof.

1. **FORBIDDEN-vocab scan** of §7 (whole-word, `re.IGNORECASE`): any hit on the §7 ban list (voxel 立体块 /
   写实照片质感 / non-canonical mascot colors / 非整数缩放 / smooth gradient *on a character or solid
   foreground prop*) → `passes=false`, return `forbidden_hits[]`.
2. **Identity-conflict lint** against `style:identity_*`: flag text that puts the **reviewer without a beard**,
   the **executor with a beard**, or any mascot color outside `{blue,green,brown,black}` → `passes=false`.
3. **World-mismatch lint** against `style:by_design_warm_cyber`: flag only **mis-colored** worlds — "a warm
   scene gone cold" or "a digital/technical artifact gone warm" — and **NEVER** flag the warm↔dark split
   itself (it is by-design). This is the concrete embodiment of *intended-variation ≠ drift*.
4. **(Optional, mostly DROPPED for us) over-prompt / quality-padding guard** — the video source banned camera/
   lighting/`8K`/`hyperrealistic` vocab because it hijacks Pippit's per-beat decomposition and triggers a
   silent model downgrade. **codex image_gen has no per-beat decomposition to hijack**, so this whole category
   DROPs by default; keep only a thin quality-padding check if a baked title ever shows the over-prompt signature.
5. **Conservative-refuse rule:** prefer a **false-positive** (force a human glance) over letting an
   identity/world/forbidden violation slip into a paid bake. Merge → `passes_all`; exit 0 (clean) / 1 (fail).

### ③ `update` — Gemini-harvest drift into append-only by-design exceptions
Run **only after ≥1 KEEP panel** exists (else exit 2). This folds the bible into the spiral's wiki memory —
recurring, *intended* deviations become written exceptions; one-off noise does not.

1. **Gather** the most-recent KEEP panel images of a beat, capped at `MAX_PANELS_PER_UPDATE`, into a manifest.
   (Image-panels swap the video source's "frames" for **PNG panels** — one image per panel, so the quorum is
   *across panels in a beat*, not within-clip frames.)
2. **Per panel, call `mcp__gemini__analyzeFile` (`auto-gemini-3`)** extracting ONLY, in strict JSON, with the
   baseline anchor values pasted inline: `color_palette` (3–5 hex), `lighting` (dir / hardness / temp),
   `subjects_present`, `subjects_absent_but_expected`, `drift_from_bible` (item-by-item deviation vs each
   baseline anchor), `safety_flags` (faces / logos / celebrity). **Gemini, not Claude, is the visual judge** —
   if Gemini-MCP is down → **exit 3**, NEVER fall back to a Claude-only read (that violates cross-model
   independence).
3. **Aggregate (Claude's only job here).** A per-beat exception locks **only** when a dimension's drift is
   reported in **≥ QUORUM** panels of the **SAME beat**. Then: write a NEW `style_anchor`
   (`tags: ["style_anchor","exception"]`, `payload.value` adds `support_frames`/`total_frames`,
   `payload.locked: true`), and add a `uses_style_anchor` edge to `wiki/edges.jsonl` in the **exact
   `{src, dst, type}` shape `cli/validate_wiki.py` enforces** (line 149: every edge needs `src`/`dst`/`type`;
   line 153: `type` ∈ `EDGE_TYPES`; both endpoints must resolve to a wiki `node_id` **or** a `comic.json` panel
   anchor `panels.<id>.wiki_node_id`). Endpoints: `src` = a representative KEEP panel of the beat addressed by
   its **legal panel anchor** `panel:<panel_id>` (e.g. `panel:s12_aris_comic_v1`, copied from
   `comic.json panels.<id>.wiki_node_id` — **never** a `<beat_id>`, which is not a legal `node_id` prefix; the
   only legal prefixes are `intent|style|outline|asset|storyboard|panel|blueprint|prompt|motif|cont|attempt|review|decision|fail`),
   `dst` = the new `style:<anchor_slug>` exception node. Carry the evidence on extra (validator-ignored) keys:
   ```json
   {"src": "panel:s12_aris_comic_v1", "dst": "style:s12_env_density_exception",
    "type": "uses_style_anchor", "evidence": "drift in c/n panels", "reviewer": "Gemini"}
   ```
   Then **APPEND** a line to the bible's `## Per-beat exceptions` section:
   `- **<beat>** — <dim>: <val> (observed in c/n panels, Gemini)`.
4. **Never rewrite the baseline.** `update` is append-only. Log the append; print `{exceptions_added, anchors}`.

## EXACT gate — `style_bible` (ported verbatim from the aris_movie source · deterministic, NO cross-model gate)
`bootstrap` certifies the compiled bible against this gate. It is a **deterministic rule-check** — there is no
cross-model judge here, because the bible *is* the rubric every other skill's cross-model gate consumes; this
gate only proves the rubric itself is complete and conflict-free.

**Dimensions — ALL must score `≥4`:**
- **`anchor_completeness`** — every §0–§7 dimension compiled to an addressable `style_anchor` node (no prose-only blob).
- **`authority_ref_resolved`** — the §1 identity authority ref (`duo_canonical_ref_v001.png`) exists on disk and is pointed at.
- **`identity_lock_specificity`** — per-character hex + beard + silhouette iron-law is concrete, not adjectives
  (executor 蓝+棕发+无须 / reviewer 绿+黑发+有须; L/R free; color/beard/silhouette immutable).
- **`text_mode_contract`** — §6 declares the mode vocabulary (`html | baked | code`) AND **every observed
  `text_mode` is licensed by an explicit §6 clause** (the checkable rule, NOT a global equality): read
  `comic.json defaults.text_mode` (and `movie.project.json.text_mode_default`) plus every `panels.<id>.text_mode`,
  collect the *distinct* observed modes, and require each one to be permitted by a named §6 clause. (Scores `<4`
  only if §6 omits a mode that some panel actually uses.) NB §6 is a *decision ledger* that licenses **multiple**
  modes at once — in the worked example it carries both the `默认锁 html` clause AND the `2026-06-09 B08 已切
  baked` update clause, so a project that is `defaults.text_mode: html` but 23 baked / 1 html is **fully
  licensed** (do NOT score it down for the html-default-vs-baked-majority spread — both are §6-clauseed).
- **`by_design_exception_contract`** — §0.5 carries the explicit `冷暖是 by-design 的,不是漂移` instruction so
  the consuming gate flags only mis-colored worlds, never the warm↔dark split.
- **`forbidden_coverage`** — §7 FORBIDDEN list exists and covers the known traps (voxel, character-surface
  smooth gradient, non-canonical mascot color, non-integer scaling, identity inversion).

**Hard vetoes — ANY one fails the gate outright (no score can rescue it):**
1. **No user-approval / version / project lock** — bible lacks a dated user approval, a `art-bible/N.N` version,
   or a project id.
2. **No duo authority ref** — §1 has no resolvable identity authority image.
3. **Warm/dark not declared by-design** — §0.5 missing the explicit by-design instruction (the gate would then
   false-flag the intended split forever).
4. **An observed `text_mode` has NO licensing §6 clause** — some `comic.json` panel (or `defaults.text_mode` /
   `movie.project.json.text_mode_default`) uses a mode that §6 never permits (e.g. a panel bakes text but §6
   carries no `baked` clause, so a baked panel would be gated on the wrong fields — `safezone`/`stray_text`
   instead of `baked_text_quality` + the `expected_literals` token-diff). Veto fires **only** on an
   un-licensed mode — NOT on a mere html-default-vs-baked-majority spread, which §6's multi-clause ledger
   legitimately allows.
5. **No FORBIDDEN list** — §7 absent (the lint has nothing to enforce; "style drift" becomes unfalsifiable).

## Node it reads / writes (per `schemas/node_schema.json`)
- **Reads:** `ART_BIBLE.md` (source of truth) · the pointer-hub manifest **`movie.project.json`** (the
  `art_bible` field is the convergence-pointer this skill verifies in bootstrap step 6 — **not** `comic.json`,
  which has no such key) · `comic.json` (read ONLY for `defaults.text_mode` + per-panel `text_mode`, which feed
  the gate's `text_mode_contract` dim — comic.json genuinely carries those) · KEEP `panel_attempt` images (for
  `update`).
- **Writes:** one **`style_anchor`** node per dimension under `wiki/nodes/style:<slug>.json`. `node_id` prefix
  is **`style:`** (per the schema's id pattern). The payload's **required** fields are exactly
  `dimension, value, source, locked`:
  - `dimension` — the locked axis (e.g. `palette:dark_world`, `identity:reviewer`, `line_shading`, `forbidden`,
    `by_design:warm_cyber`, `text_mode`, `env_density`).
  - `value` — the concrete spec (hexes / rule text / the by-design instruction / the mode set / the ban list).
  - `source` — the exact `ART_BIBLE.md §N` the value traces to (un-sourced anchor = refuse, never fabricate).
  - `locked` — `true` for baseline anchors (immutable) and exception anchors alike.
  - baseline `status: "locked"`, `tags ⊇ ["style_anchor","baseline"]`; exception anchors add the `exception`
    tag + `support_frames`/`total_frames` and an **incoming** `uses_style_anchor` edge in `wiki/edges.jsonl`
    written `{src: "panel:<panel_id>", dst: "style:<anchor_slug>", type: "uses_style_anchor"}` (a legal panel
    anchor → the exception node; `src`/`dst`/`type` + resolvable endpoints, per `cli/validate_wiki.py`).

## Two engine contracts this skill upholds (fail-closed)
The bible is what makes the [`comic-author`](../comic-author/SKILL.md) engine contracts *enforceable*, so the
gate certifies them at the bible layer:
1. **Every panel needs a `condition.content_svg`** — the §0–§7 dialect is what every deterministic blueprint is
   rendered *in*; the bible must be lockable so a blueprint has a single style to instantiate (no `content_svg:
   null`; the engine rejects it).
2. **A baked figure-panel needs `condition.expected_literals`** — §6's `text_mode_contract` dim is a **hard
   veto** precisely so a `baked` panel's gate fields line up: a baked figure-panel swaps `safezone`/`stray_text`
   for `baked_text_quality` (≥4) **plus a blind token-diff of `observed_literals` vs the authored
   `expected_literals`**. If a `comic.json` panel uses a `text_mode` that **§6 never licenses** (e.g. a panel
   bakes text but §6 carries no `baked` clause), veto #4 fires — the gate would check the wrong fields and a
   baked panel could ship with no `expected_literals`. (A §6-licensed mix — its html-default clause AND its
   baked update clause both present — does NOT fire the veto.)

## Worked example
The canonical bible is **[`examples/comic_m3_audit/ART_BIBLE.md`](../../examples/comic_m3_audit/ART_BIBLE.md)**
(`version art-bible/1.0`, locked 2026-06-08, project `aris_comic_v1`) — copy its §0–§7 spine verbatim. The
**concrete pattern to copy**:

- **The bible declares ITSELF the gate rubric** (lines 3–5): `style_consistency / identity_consistency 的字面
  定义就是"符合本文件"` and the load-bearing warning `无 ground-truth spec,跨模型 gate 会永远吐"style drift"
  却没有收敛方向`. **Copy this header verbatim** into any new bible — it is the contract that makes the
  downstream cross-model gate converge.
- **§0 anchors to a NAMED probe + a dated user approval**, never adjectives: `定档在 … (= 批准的
  probe/S02_codexgen_a01.png 那个程度)`. Every later taste decision is a **dated, user-attributed line** (§0.5
  `用户 2026-06-09 选 B`; §6.5 `用户 2026-06-09 品味校准, 靶 = cal_S12_a01`).
- **§0.5 is the by-design exception archetype** — `真实世界 = 暖` vs `数字 ARIS 世界 = 暗黑霓虹极客
  (dark_navy_void #0A0E27)`, then the gate instruction `gate 评 style_consistency 时:冷暖是 by-design 的,
  不是漂移;只标"该暖的场景冷了 / 该暗的数字物暖了"这种错配`. This single line is what stops a naive gate from
  flagging the intended two-world split round after round (the `feedback_gate_identical_scores_judge_broken`
  lesson: design-aware gates are the fix).
- **§1 is the identity-lock archetype** — authority `duo_canonical_ref_v001.png` + a per-character hex table
  (executor hoodie `#1D4684` / hair `#925935` / **no beard**; reviewer hoodie `#30582D` / hair `#0F0D16` /
  **beard**) + the 铁律 `executor 永远蓝+棕发+无须;reviewer 永远绿+黑发+有须. 左右位置可变…但颜色/胡子/体型
  轮廓不可变`. → emit `style:identity_executor`, `style:identity_reviewer`, `style:identity_authority_ref`.
- **§3 carries a reviewer-calibrated carve-out** (dated `2026-06-08`): `背景氛围光是允许的` — wiki-void center
  glow / bloom / volumetric light MAY use smooth gradients; the no-gradient rule constrains **only character
  surfaces + solid foreground props**. This is a *drift-that-became-a-by-design-exception* — exactly what
  `update` produces, here recorded by hand after a reviewer round.
- **§7 FORBIDDEN includes the voxel ban** (`3D 体素立体块 (本片走 flat 像素)`) added **after gemini found a
  flat-2D↔voxel drift** — the canonical case of a cross-model finding hardening into the FORBIDDEN list.
- **§6 carries the full text-mode decision history** including the explicit PENDING duel (`仅当实测 AI 烤 CJK
  干净 且 用户明确偏好,才把 text_mode 切到 baked;在用户拍板前,默认锁 html`) — the bible is a *decision
  ledger*, and the pending item does NOT unlock the default.

The sibling artifacts that *consume* these anchors — `gen/asset_lib.py` (palette pinned to the IR's
`ui_tokens`, "so the film never grows two visual dialects"), `gen/check_asset_collisions.py` (the single-source
gate), and `comic.json`'s per-panel `condition.identity_desc` / `condition.world` / `condition.expected_literals`
(the runtime fields the engine reads under each panel's `condition`) — are the proof that a locked bible turns
into a mechanical, fork-proof convergence target.

## Hard do / don't (earned lessons)
- **DO** make the bible the SINGLE convergence target read **verbatim** into every bake prompt **and** every
  visual reviewer's prompt — "one visual dialect, never two". If two prompts disagree on the look, you have
  two dialects and the gate can never converge.
- **DO** anchor §0 to a **named probe image + a dated user approval**, never adjectives; record every taste
  decision as a dated, user-attributed line.
- **DO** keep baseline anchors **immutable** — `update` only *appends* by-design exceptions; pivoting the style
  = a **fresh bootstrap in a new project dir**, never an in-place edit (the cross-model gate must always compare
  against the ORIGINAL anchors). See `acceptance-gate` (locked = immutable).
- **DO** declare warm↔dark as **by-design** (§0.5) so the gate flags only *mis-colored* worlds — intended
  variation ≠ drift.
- **DO** auto-bootstrap a §0–§7 scaffold **and escalate to the user** when the bible is missing; **DON'T**
  fabricate a probe image, a hex, or an approval date.
- **DON'T** let the executor (Claude) judge visual drift in `update` — that's Gemini's job (cross-model
  independence); Gemini-down → exit 3, never a Claude-only fallback.
- **DON'T** let one noisy panel mutate the bible — require the **≥50% same-beat quorum** before an exception is
  written.
- **DON'T** port the video source's camera/lighting/`8K`/`hyperrealistic` banned-vocab wholesale — codex
  image_gen has no per-beat decomposition to hijack, so that category DROPs; keep the FORBIDDEN-list +
  identity + world lint, which is what bites *us*.
- **DON'T** ship a bible whose §6 fails to license a `text_mode` that some `comic.json` panel actually uses —
  veto #4 fires, and that panel could otherwise be gated on the wrong fields (or ship with no
  `expected_literals`). (Conversely, DON'T veto a §6-licensed mix — html-default + baked-update clauses both
  present — just because the project is baked-majority; that is intended, not a contradiction.)

## Protocols (governance contracts this skill honors)
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — **locked = immutable**: this gate can DRIVE
  (bootstrap, lint, append exceptions) but can't ACQUIT the *taste* — user approval is the hard gate for §0/§0.5/
  §1/§6, and a locked baseline anchor is never edited in place (a style pivot is a fresh project, not a rewrite).
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — the `update` drift reviewer is Gemini
  `auto-gemini-3`; never downgrade. (The compile-time `style_bible` gate is a deterministic rule-check with no
  model call, by design.)
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — in `update`, Gemini gets the panel
  image + the baseline anchor values inline, never Claude's interpretation; the executor only aggregates the JSON.
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — every anchor's `payload.source` traces to a
  §-section of the bible; an un-sourced anchor is a refuse-and-escalate, never a fabricated value.
- [`review-tracing`](../../protocols/review-tracing.md) · [`output-versioning`](../../protocols/output-versioning.md)
  — log each bootstrap/update to `wiki/log.md`; version the bible (`art-bible/N.N` + lock date) and never
  silently overwrite a locked one.
