---
name: comic-outline-creator
description: "Phase-1 Layer-2 of a comic — turn a LOCKED skeleton (intent_spec + the pre-locked beat/shot list) into an approved outline_spec: a 6-column beat table that binds every ARIS capability to a STORY COST, plus the continuity-motif contract the storyboard layer will be held to. NOT free creation — editorial adaptation of a pre-locked skeleton via 3 parallel lenses → cross-model (Codex) synthesis → a density/restructure pass → a USER-approval HARD GATE. Cross-model synthesis is part of authoring here, not post-review. Author the comic.json downstream with comic-storyboard-creator + comic-blueprint-author; this skill only produces the outline + motif contract."
argument-hint: [intent_node_id | --revise-from <beat_id>]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, mcp__codex__codex, mcp__codex__codex-reply, mcp__gemini-cli__ask-gemini
---

# comic-outline-creator — the Outline + Motif Contract (Phase 1, Layer 2)

The **middle-left of Figure 1**: take a locked `intent_spec` (+ the pre-locked beat/shot skeleton it
carries — OR, for an **idea-first comic with NO pre-locked skeleton**, the 3 lenses first **synthesize** a beat
skeleton from the intent's `logline` / `subjects` / `constraints` / `format`, then adapt it the same way; the
synthesized skeleton is recorded so the deltas-vs-skeleton discipline still applies) and produce a single
**approved `outline_spec`** — the 6-column beat table that drives the
storyboard, and the continuity-motif arcs that become the storyboard's checkable contract. This is the
comic twin of aris_movie's `movie-outline-creator` (a Layer-2 authoring-time **plan gate** before any
pixels), specialized for our image-comic route: the deliverable is a *plan*, never a frame.

Two things are simultaneously true, and the whole skill is built around them:
**(a)** the outline is NOT a free brainstorm — it is an **editorial adaptation of a pre-locked skeleton**
(N beats / M shots, beat boundaries fixed), so every candidate must self-report its **deltas vs the
skeleton**; **(b)** an unbounded "ARIS capability showcase" silently rots into a **product manual** unless
every capability is bound to a concrete **story cost** and skill-name tags are banned from the 画面. The
3-lens → Codex-synthesis → density-pass → user-approval loop turns (a) into a faithful, debated outline and
the 侧栏讲解铁律 + the gate catch (b) every round.

```text
  intent_spec (logline + tagline + dual-identity + LOCKED skeleton)
        │
        ▼  ① FAN-OUT: 3 parallel named lenses over the SAME skeleton (faithful ∥ comicnative ∥ clarity)
        │     each ends with a self-authored "through-line + deltas vs the skeleton" section
        ▼
  ② SYNTHESIZE — Codex (different model family) reconciles the 3 → OUTLINE v2
        ▼
  ③ DENSITY/DESIGN pass — Codex MAY restructure panel count (e.g. centerpiece 4→5 pages, +mid-act page)
        │     AUTHORS the 侧栏讲解铁律 (anti "product manual" guard)
        ▼
  ④ Emit the 6-column BEAT TABLE + the centerpiece sub-plan + the 5 motif arcs (exact per-shot values)
        ▼
  ⑤ READINESS gate (PRE-user, cross-model, blind to orchestrator prose) — scores ONLY the author-controllable
        │   dims; EXCLUDES user_decision_record + the unresolved-questions veto (those are not yet satisfiable).
        │   Two-step (never cold): write review:* nodes + `reviews` edges → THEN comic-cross-layer-gate <id> --gate outline
        ▼ readiness:advance
  ⑥ USER APPROVAL = HARD GATE — present; record ✅ APPROVED + fill 已定决策 + EMPTY 待确认 block
        │   THEN the FINAL gate (now user_decision_record==5 IS satisfiable) → write outline_spec node (locked)
        │ revise ─▶ ② (bounded: MAX_OUTLINE_REVISIONS=3 → auto-abandon → failure_mode node)
        ▼ approve + signed
  outline_spec (locked) → SOURCE OF TRUTH for the storyboard layer
```

## Constants
- **LENS_COUNT** = **3, mandatory** (`faithful`, `comicnative`, `clarity`) — Tier-1 Workflow fan-out
  ([`fan-out-pattern`](../../protocols/fan-out-pattern.md)). Fewer than 3 lenses is a hard veto.
- **SYNTHESIZER** = `mcp__codex__codex`, `model_reasoning_effort: xhigh` — a **different model family** from
  the Claude lens authors. Codex both *reconciles* the 3 candidates AND runs the density/restructure pass;
  the outline layer is itself a cross-model artifact (executor ≠ reviewer, [`reviewer-independence`](../../protocols/reviewer-independence.md)).
- **GATE REVIEWERS** = `mcp__codex__codex` (gpt-5.5 xhigh) ‖ Gemini (`auto-gemini-3`, readability dims) — each
  sees ONLY `outline_spec.json` + `intent_spec.json` (the skeleton) + the lens files, never Claude's prose. They
  do **not** acquit; they each persist a `review:<slug>` node (payload `{target_node_id, reviewer, gate_kind:
  "outline", review_scores:{...}}`) with a `reviews` edge `review:<slug> → <outline_id>`, and the SOLE acquittal
  organ [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) `--gate outline` then **fuses** those
  score-nodes (D4: never invoke the gate cold — write the reviews FIRST, then call the gate).
- **THE GATE IS RUN TWICE** (the deadlock fix): a **READINESS** pass BEFORE user approval (scores only the
  author-controllable dims; the gate's own `user_decision_record == 5` floor and the unresolved-questions veto
  are **not yet satisfiable**, so the readiness reviewers explicitly omit them), then the **FINAL** pass AFTER
  the user signs + the `待确认` block is emptied (now `user_decision_record == 5` IS satisfiable). See §EXACT gate.
- **MAX_OUTLINE_REVISIONS** = 3, then auto-abandon → write a `failure_mode` node so a re-run must diverge. Its
  payload is **exactly** what `validate_wiki.py` PAYLOAD_REQUIRED demands for `failure_mode`: `{"layer":
  "outline", "affected_shot_ids": [<the abandoned skeleton shots, e.g. all S01..SMM>], "active": true}`
  (node_id `fail:<slug>`, node_type `failure_mode`, status `active`). There is **NO `encoding_style` field** in
  the schema — carry the "a re-run must diverge" positive-invariant in `title` or a non-required note, never a
  fabricated required-looking key; the node must pass `cli/validate_wiki.py`.
- **MAX_DRAFT_ATTEMPTS** = 3 — schema-repair loop for the `outline_spec` node; on each fail, `codex-reply`
  quoting the validator errors **verbatim**. Never silently coerce a value to pass schema (change the
  narrative + document it, or surface to the user).
- **TARGET_PAGE_CEILING** (soft cap, exceed ⇒ Codex must justify in `rationale.beat_count_justification`,
  not a hard stop): `mvp=2`, `demo=6`, `longform=12` beats per tier (ported from `MAX_BEATS_PER_TIER`).
- **MIN_CAST_PER_BEAT** = every beat names **≥1 world/scene + the cast in it** (text-panel beats: a
  text-panel scene + its world). Ported from aris_movie's `MIN_ASSETS_PER_BEAT=2`; a structural check
  JSON-Schema can't express.
- **NODE** = `outline_spec` (this skill **reads** `intent_spec`, **writes** one `outline_spec`). See §Node.
- **APPROVAL IS NON-AUTOMATABLE** — the loop can DRIVE to a clean gate, but **only the user ACQUITS** the
  outline ([`acceptance-gate`](../../protocols/acceptance-gate.md)). Nothing proceeds to the storyboard
  layer until the user signs off, recorded inline.

## Input contract — what this skill reads, what it must not invent
The contract boundary is the **`intent_spec` node** ([§Node](#node)) — produced upstream by
`comic-intent-parser`, carrying: the **logline** (a single sentence whose climax may be an editorial
inversion — e.g. *"the climax is NOT winning — it's that ARIS didn't let itself off the hook"*); the
**tagline**; the **`dual_identity`** constraint (*"an emotional story of honest research + an ARIS capability
showcase"*) the whole debate optimizes against; and the **`source_skeleton`** — the pre-locked beat list
(`B01…BNN`), shot list (`S01…SMM`), and beat boundaries. **The skeleton is LOCKED; this skill ADAPTS it,
never re-derives it.**

This skill is **plan + verify**: it **never bakes a pixel** (image gen is `comic-director` / Phase 2-3) and
**never invents a beat boundary or a shot**. Adding a *page* (a density-pass split) is allowed and must be
accounted for in the deltas; **moving a beat boundary or dropping a shot is a delta that must be justified +
surfaced to the user**. If `intent.status != locked` → **REFUSE** (the upstream hand-off token is `locked` =
approved + frozen; an `under_review`/`draft` intent is not ready — re-run `comic-intent-parser` to its user
gate). If the skeleton is missing → **REFUSE and ESCALATE** (do not fabricate one).

## Procedure (an agent can execute this step by step)

### 0. Load + refuse-guard
Snapshot the `intent_spec` node. Pull cumulative wiki context: prior LOCKED assets (for reuse-over-invention),
and `failure_mode` nodes with `layer="outline"` (rejected/superseded outlines — a re-run must diverge from
them). Refuse if `intent.status != locked` (the upstream author-node hand-off token is `locked`, not `active`).
Checkpoint an `OUTLINE_STATE.json` (resumable —
[`resumable-runs`](../../protocols/resumable-runs.md)).

### 1. FAN-OUT — write 3 parallel candidate LENSES over the SAME locked skeleton
This is **Tier-1 Workflow fan-out** ([`fan-out-pattern`](../../protocols/fan-out-pattern.md)): three
independent passes, each a *named lens* over the identical skeleton, NOT three free drafts. Write each to its
own file (`story/outline_candidate_{faithful,comicnative,clarity}.md`). The three lenses are fixed:

- **`faithful`** — one-to-one fidelity: **M shots → M panels, no cut / merge / add**, beat boundaries
  `B01…BNN` preserved exactly. The conservative anchor (palette grammar + stamp mirrors live here).
- **`comicnative`** — comic-as-a-medium: **collapse runtime / motion shots into static-friendly pages**
  (in our run `S07-S09 → one 2×2 page`; `22 shots → 12 panels`); choose a `full-bleed / 2-up / 2×2`
  page-rhythm for scroll-reading.
- **`clarity`** — legibility for a **non-ML reader**: foreground the through-line so the headline number-arc
  (in our run `+6.2 → +1.4`) is readable via **one concrete physical prop** (the `Tok|yo` broken-JSON
  evidence) + **one wordless emotional gauge** (executor bounce height).

**Each candidate MUST end with a self-authored section: `## through-line + deltas vs the skeleton`** stating
exactly what it **merged / added / kept** and **why** (e.g. *"merged S07-S09 → one 2×2 page (motion is
redundant in a static page); kept all 13 beats; moved Tok|yo's first plant earlier to B06-S09 as a
re-pointable物证"*). A candidate with **no deltas section is a hard veto** — delta-accounting is the
discipline that proves it is an adaptation, not a guess.

### 2. SYNTHESIZE — Codex reconciles the 3 → OUTLINE v2
Call the **SYNTHESIZER** (different model family). Feed it the three lens files + the `intent_spec` +
`schemas/node_schema.json`'s `outline_spec` shape, inside a demarcated `=== EXTERNAL CONTEXT (advisory) ===`
fence; Claude's prose lives ONLY in that fence ([`reviewer-independence`](../../protocols/reviewer-independence.md)).
The synthesis takes the **best of each lens** — in our run: `faithful`'s two-world WARM/DARK palette grammar
+ the REJECT↔ACCEPT mirror, `comicnative`'s page-rhythm, `clarity`'s motif arcs + countdown spine. Emit
`{outline, rationale}`.

### 3. DENSITY / DESIGN pass — Codex MAY restructure panel count
Codex then does a **density / design pass** that may materially change panel count where the read demands it
(in our run: the centerpiece B08 went **4 panels → 5 single-read pages** by adding an "audit entry" panel,
with the 2×2 kept only as recap/hero/GitHub-screenshot; and a **new mid-act page** `B09.5` "research
star-map / wiki" was added *after the audit, before the paper* — flagged as *"the most powerful position"*;
panel count moved `22 → ~24`). This pass also **AUTHORS the 侧栏讲解铁律** (step 6). Adding pages is fine;
account for every one in the deltas.

### 4. Emit the 6-column BEAT TABLE
Emit the canonical table — **fixed columns, in this order**:

| Beat (zh/en) | Panels | 布局/layout | 世界/world | 内容 + 台词 gist | ARIS 特性（绑剧情）|

- **Beat** — bilingual id + name (`**B01 卧室·倒计时**`).
- **Panels** — the shot ids it OWNS (`S01` · `S07,S08,S09大` · `S12-15 + 新增 S12a`).
- **布局/layout** token ∈ {`full-bleed`, `split`, `2-up`, `1-panel`, `竖排3`, `5单张页(默认)/2×2 recap`}.
- **世界/world** token ∈ {`暖/WARM`, `暗/DARK`, `seam`, `暗·星空/starfield`} — human beats warm, ARIS beats
  dark-cyber, **explicit seam panels** at hand-off / payoff. (The warm/cold split is **by-design** — the
  downstream gate must never flag it as drift.)
- **内容 + 台词 gist** — panel action + baked-dialogue gist + a one-line side-narration (旁白).
- **ARIS 特性（绑剧情）** — the bound capability, **phrased as a STORY COST, never a feature name**
  (✅ `experiment-bridge（证据是暂定的）` · `honest re-run（自纠 overclaim）` · `auto-review-loop（对抗审）`;
  ❌ `experiment-audit`, `novelty-check` as bare tags). A bare feature name here is a hard veto.

### 5. Centerpiece sub-plan (the densest beat)
For the centerpiece beat, emit a sub-table `| 页/page | 画面/image | 侧栏（先讲发生了什么，再点能力）|` with the
verbatim **70/30 composition rule**:
> 每页：技术主画面 70% + 角色情绪 30%（右下角蓝 exec bounce 当体温计）+ 侧栏讲解。

Each row's 侧栏 puts the **event-sentence first**, then `· *trait: <skill>*` second (so the side-narration
reads as story, then footnotes the capability).

### 6. Embed VERBATIM the 侧栏讲解铁律 (the anti "product-manual" guard)
This block is **load-bearing** — copy it verbatim into the outline (it is what stops a capability showcase
from rotting into a product manual):
> 🎙️ 侧栏讲解铁律（防止"能力展示"变产品手册 —— codex）
> - 每条能力必须绑一个剧情代价：不写"ARIS has experiment-audit"，写"executor 的庆祝被审计打断，所以 ARIS 没撒谎"。
> - 侧栏第一句永远讲发生了什么；第二句才点能力名。
> - 每个能力都改变角色状态（bounce 高低 / 咖啡冷掉 / 红队介入 / claim 被降级）。
> - 画面里不堆 skill 名标签；skill 名只作侧栏小字或 hover/click metadata。

### 7. Lock the continuity-motif arcs AT OUTLINE TIME (exact per-shot values)
The outline **doubles as the continuity contract** — the storyboard's motif-state table and the
panel/assembly gates will be checked against these arcs, so they must carry **exact per-shot values now**.
Lock the 5 arcs (our run's values, as the worked pattern):
- **mug heat**: `STEAMING(S01) → fading(S03) → COLD(S20)` — B01/B12 bookend.
- **executor bounce** (wordless emotion thermometer): `MAX(S02) → HIGH(S09) → DROP(S11) → ZERO/SILENT(S12–S15,
  arc low point) → tempered-return(S16) → smallest-warm(S21)`. (Storyboard will add the uniqueness
  invariant *"S02 是全片唯一 MAX"*; no post-fall peak.)
- **Tok|yo broken-JSON evidence**: `born/first-plant(B06-S09) → smoking-gun(B08) → clean footnote(S17) →
  faint constellation star(S22)`.
- **DDL countdown spine**: `24:00:00 → ~19:00 → 00:42` — strictly **monotonically non-increasing** across
  the whole film (storyboard enforces; never rewinds).
- **REJECT(S11) ↔ ACCEPT(S16)**: deliberate **mirror stamps** so the centerpiece audit reads as the hinge
  between them.

### 8. Write the 6-column table + sub-plan + 铁律 + motif arcs to `story/OUTLINE_DRAFT.md`
Add a top-of-file `Logline + Tagline + 双重身份` block (mirroring the intent), an empty `## ✅ 已定决策` block,
and an `## ⚠️ 待你确认` block listing every open design question (e.g. *centerpiece 5-page split OK? new
mid-act wiki page OK? 侧栏铁律 OK?*).

### 9. READINESS gate — PRE-user, cross-model, blind (NOT the final gate)
This is the **author-controllable** gate, run **before** the user has decided anything. By construction the
artifact from step 8 has an **empty `已定决策`** + a **non-empty `⚠️ 待确认`** block and **no user sign-off** —
so the FINAL gate's `user_decision_record == 5` floor and its "open questions unresolved but advancing" veto
are **not yet satisfiable**. Applying the full conjunctive APPROVE rule here would deadlock a fresh agent
(stall, or fabricate a user approval). So the readiness pass scores **only** the dims the author controls and
**explicitly EXCLUDES** `user_decision_record` + the unresolved-questions veto (see §EXACT gate → READINESS).

Run it as a **two-step gate invocation (D4 — never call the gate cold)**:
1. **Fan out the GATE REVIEWERS** (Codex `gpt-5.5 xhigh` ‖ Gemini `auto-gemini-3`) on the files only
   (`outline_spec.json` + `intent_spec.json` + the lens files, inside the advisory fence — no orchestrator
   prose). **Persist EACH as a `review` node:** `node_id review:<slug>` (e.g. `review:outline_codex_r1`),
   node_type `review`, payload **required** `{target_node_id: <outline_id>, reviewer: "codex"|"gemini",
   gate_kind: "outline", review_scores:{skeleton_fidelity:…, delta_accounting:…, coverage:…,
   page_rhythm_readability:…, story_cost_binding:…, motif_contract_completeness:…, safety_ip:…}}` — and write a
   `reviews` edge `{src: review:<slug>, dst: <outline_id>, type: "reviews"}` (the gate walks `reviews` edges in;
   `reviewed_by` is the wrong direction and the fuser won't find it).
2. **THEN** invoke `comic-cross-layer-gate <outline_id> --gate outline` to fuse the score-nodes + adjudicate.
   (Its own `--gate outline` floor — `min(coverage, identity_lock_feasibility, scene_lock_feasibility) ≥ 4 AND
   safety_ip ≥ 4` — runs on whatever dims the reviewers scored; the readiness reviewers feed it the
   author-controllable subset and intentionally leave `user_decision_record` unscored, which the gate SKIPs,
   never 0-substitutes.) On a FAIL verdict, fold the blockers and loop back to step 2 (bounded by
   `MAX_OUTLINE_REVISIONS`); on a clean readiness verdict, proceed to step 10.

**Then schema-validate the (still-`under_review`) `outline_spec` node** payload (`cli/validate_wiki.py` mirrors
`node_schema.json`); on a schema error, run the `MAX_DRAFT_ATTEMPTS` repair loop with `codex-reply` quoting the
errors verbatim. **Also run the 2 structural checks JSON-Schema can't express:** (i) **coverage** — every
`intent.dual_identity` "must-land" item and every skeleton beat maps to ≥1 table row; (ii) **MIN_CAST_PER_BEAT**
— every beat names ≥1 world + its cast. Do **not** flip to `locked` yet — that needs the user sign-off (step 10).

### 10. USER APPROVAL = HARD GATE → FINAL gate → then lock
Present the readiness-clean outline to the user. **Nothing proceeds until they sign off.** On approval:
- record inline `✅ APPROVED by user <date>` (with their words, e.g. `("都可以")`),
- fill the `## ✅ 已定决策（用户 <date>）` block — **every resolved open question becomes a recorded decision
  node** (our run: `B06-S09 → big panel`; `Tok|yo pre-plant → very small, narration does NOT spell it out`;
  `B13 constellation → pure glowing star-points, NO labels`),
- empty the `## ⚠️ 待你确认` block (every open question is now in `已定决策`).

Now — and **only** now — run the **FINAL gate** (D4 two-step again): re-fan the GATE REVIEWERS on the
now-complete artifact, persist fresh `review:<slug>` nodes (this round CAN score `user_decision_record`,
since the sign-off + `已定决策` block + emptied `待确认` block exist) with `reviews` edges, then call
`comic-cross-layer-gate <outline_id> --gate outline`. The FINAL gate applies the full conjunctive APPROVE rule
(§EXACT gate → FINAL) including `user_decision_record == 5`, now satisfiable. On the gate's `approve`:
- the gate itself **mints the `decision` node** (`node_id decision:outline_<slug>`, payload **required**
  `{target_node_id: <outline_id>, verdict: "approve", gate_kind: "outline"}`) + the `decides` edge and **flips
  the `outline_spec` node `status: locked`** — that FLIP is the gate's job, not this skill's. (Never write
  `status: locked` by hand without the gate's `approve` verdict node **and** the inline user sign-off.)
- declare the file **"SOURCE OF TRUTH for the storyboard layer."**

Then hand off to `comic-storyboard-creator` (it inherits the locked beats + the motif arcs as its
continuity ledger).

## EXACT gate — this skill's PRE-gate rubric, fused by `comic-cross-layer-gate --gate outline`
**Authority note (D3):** the canonical APPROVE predicate + the status FLIP for the `outline` gate are owned by
[`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) `--gate outline` (its floor:
`min(coverage, identity_lock_feasibility, scene_lock_feasibility) ≥ 4 AND safety_ip ≥ 4`, plus its `outline`
pre-check that every referenced `asset_id` resolves and is `status: locked`). The dims + verdict rules below are
**THIS skill's pre-gate routing** (step 9 step-1 fan-out): the rubric the GATE REVIEWERS score into their
`review:<slug>` nodes, and the local stop-rule this skill uses to loop/abandon **before** deferring to the
fuser. They are not a competing gate — the cross-layer-gate fuses these score-nodes and makes the final call.

Each GATE REVIEWER scores these dims **0–5** seeing ONLY `outline_spec.json` + `intent_spec.json` (the
skeleton) + the lens files — **no orchestrator prose**:

- **`skeleton_fidelity`** — beats / shots / beat boundaries from the locked skeleton are preserved or every
  change is an accounted delta (no silent re-derivation).
- **`delta_accounting`** — every candidate has a `deltas vs the skeleton` section; the synthesized outline's
  added/merged pages are all listed and justified.
- **`coverage`** — every `intent.dual_identity` must-land item + every skeleton beat maps to ≥1 table row
  with the right cast in `must_show` (the comic analog of aris_movie's `coverage` dim).
- **`page_rhythm_readability`** — layout tokens give a real scroll-read rhythm; the centerpiece is single-read
  paced; non-ML reader can follow the headline arc (readability — Gemini co-scores).
- **`story_cost_binding`** — **every** `ARIS 特性` cell is phrased as a story cost that changes a character
  state, **never** a bare feature name.
- **`motif_contract_completeness`** — all motif arcs are locked with **exact per-shot values** (not "a
  recurring mug"); REJECT↔ACCEPT mirror + monotonic DDL declared.
- **`safety_ip`** — no celebrity likeness / copyrighted character / trademarked logo / off-policy content;
  anti-IP `must_avoid` carried into the style bible (HIGHER = better).
- **`user_decision_record`** — the `✅ APPROVED` stamp + `已定决策` block (resolved questions as decision
  nodes) + an EMPTY `⚠️ 待确认` block are all present and consistent. **Scored in the FINAL round ONLY** — at
  step 9 it is not yet satisfiable, so the READINESS reviewers leave it `null` (the fuser SKIPs a `null` dim,
  it does **not** 0-substitute).

### READINESS verdict rule (step 9 — PRE-user; EXCLUDES the user dim + the unresolved-questions veto)
The author-controllable stop-rule the readiness fan-out routes on (this is what makes step 9 actually passable
before the user has decided anything):
```
skeleton_fidelity >= 4 AND delta_accounting >= 4 AND coverage >= 4
AND story_cost_binding >= 4 AND motif_contract_completeness >= 4 AND safety_ip >= 4
```
`user_decision_record` is **NOT** evaluated here, and the **"open questions unresolved but advancing" veto does
NOT apply** at readiness (the `⚠️ 待确认` block is *expected* to be non-empty pre-user). Readiness-clean ⇒
present to the user (step 10).

### FINAL verdict rule (step 10 — POST-user; the full conjunctive rule, now satisfiable)
```
skeleton_fidelity >= 4 AND delta_accounting >= 4 AND coverage >= 4
AND story_cost_binding >= 4 AND motif_contract_completeness >= 4
AND safety_ip >= 4 AND user_decision_record == 5
```
**revise** ⇐ any blocking dim `< 4` but recoverable (loop to step 2, bounded by `MAX_OUTLINE_REVISIONS=3`).
**abandon** ⇐ `safety_ip < 3` **OR** three consecutive `revise` rounds with the **same root cause** →
auto-abandon → write a `failure_mode` node whose payload is **exactly** the validator-required shape `{"layer":
"outline", "affected_shot_ids": [<abandoned skeleton shots>], "active": true}` (node_id `fail:<slug>`, status
`active`; no `encoding_style` key — that is not a schema field).

**Hard veto (any one → not APPROVE, regardless of scores):**
- fewer than **3 lenses**;
- any candidate with **no `deltas vs the skeleton`** section;
- any `ARIS 特性` cell written as a **product-manual feature name** instead of a character cost;
- a **skill-name in a 画面 main label** (skill names allowed ONLY in side-narration small-text / hover
  metadata);
- **open questions unresolved but advancing** (FINAL round only — the `⚠️ 待确认` block must be emptied into
  `已定决策` before the user can lock; this veto is intentionally OFF at readiness, see above);
- **motif arcs not locked** at outline time (no exact per-shot values).

> The loop can DRIVE to a clean gate, but **the gate cannot ACQUIT — only the user can**
> ([`acceptance-gate`](../../protocols/acceptance-gate.md)). A clean cross-model readiness gate is necessary,
> the signed user approval is sufficient; both are required, and the FINAL gate is what mints the `approve`
> decision + flips `outline_spec` to `locked`.

## Node — reads `intent_spec`, writes `outline_spec`
Per [`../../schemas/node_schema.json`](../../schemas/node_schema.json) (`schema_version node/comic/3.0`).

**Reads** `intent_spec` (`node_id intent:<slug>`) — payload required (verbatim from `validate_wiki.py`
PAYLOAD_REQUIRED): `raw_input_refs, user_goal, audience, format, constraints, subjects, source_skeleton,
dual_identity, uncertainties, confidence`. **Refuse unless its `status == locked`** (the author-node hand-off
token is `locked` = approved + frozen, NOT `active`; `comic-intent-parser`'s user gate is what flips it).

**Writes one** `outline_spec` (`node_id outline:<slug>` — matches the schema node_id pattern). Payload
**required fields** — every one of these (verbatim from `validate_wiki.py` PAYLOAD_REQUIRED for `outline_spec`)
must be present: `source_intent_id, title, logline, tagline, design_constraint, target_page_count,
narrative_beats, beat_table, motif_arcs, character_asset_ids, scene_asset_ids, prop_asset_ids,
global_style_bible, budget`:
- `source_intent_id` — the `intent:<slug>` it adapts. Also write the provenance edge `{src: outline:<slug>,
  dst: intent:<slug>, type: "derived_from"}` (the author-layer "this node was authored/derived from that node"
  verb — `derived_from` is in `validate_wiki.py` EDGE_TYPES; `generated_from` is NOT and would FAIL the
  validator). **The edge record itself must pass `cli/validate_wiki.py`** (both endpoints resolve to real
  node_ids; the type is in EDGE_TYPES).
- `title`, `logline`, `tagline`, `design_constraint` — carried from intent (the dual-identity constraint).
- `target_page_count` — within `TARGET_PAGE_CEILING` for the tier, or justified in `rationale`.
- `narrative_beats` — the beat list with each beat's `must_show` (cast/world per beat — enforces
  `MIN_CAST_PER_BEAT`).
- `beat_table` — the 6-column table (the canonical render-source for the storyboard).
- `motif_arcs` — the 5 arcs with **exact per-shot values** (the continuity contract).
- `character_asset_ids`, `scene_asset_ids`, `prop_asset_ids` — flat lists holding the **node_ids of prior
  LOCKED assets** when one matches (reuse over invention); **emit no new asset node here** — that is the asset
  layer's job, where `reuse_of` lives. (There is no `reuse_of` field on `outline_spec` — the asset references
  are these three flat id-lists; don't carry the movie source's `asset_plan[].reuse_of` here.)
- `global_style_bible` — pointer to the locked `ART_BIBLE.md` / `style_anchor` nodes (incl. the warm/dark
  two-world palette + the anti-IP `must_avoid`).
- `budget` — page/asset budget for the downstream layers.

Status lifecycle: `draft → under_review → locked` — `locked` flipped by the FINAL `comic-cross-layer-gate
--gate outline` `approve` (after the inline user sign-off), or `rejected` / `superseded`. (`active` is a RUNTIME
status, never this author node's hand-off token.)
**Fail-closed:** never write `status: locked` without the gate's `decision` node `verdict="approve"` **and** the
inline user sign-off; never silently coerce a value to pass schema.

## Two engine contracts the outline must SET UP (fail-closed, downstream)
The outline does not author blueprints, but it **must make them authorable** — so the centerpiece sub-plan
and any figure-bearing beat are spec'd so the downstream layers can satisfy these without re-litigating. (The
runtime field names below are the **`comic.json` panel** fields the engine reads — `condition.content_svg` /
`condition.expected_literals` — the *only* artifact that uses the `condition.` prefix; do not conflate with the
wiki nodes the downstream layers write, where the field is `blueprint.payload.content_svg` (top-level) and
`panel_spec.payload.content_blueprint` — there is **no** `content_svg` on a panel_spec.)
1. **Every panel will need a `condition.content_svg`** (a deterministic blueprint — figure or layout; the
   engine rejects `condition.content_svg: null`, never write it null). So every figure-bearing beat in the
   table must name **what the blueprint depicts** (the curve, the gauge, the broken-JSON chip), not just "a
   screen" — the storyboard / blueprint authors instantiate the SVG, but the outline owes them a concrete
   subject.
2. **A `text_mode:"baked"` figure-panel will need `condition.expected_literals`** (exact numbers/keys,
   ascii-tokenizable, verbatim) — or the bake is refused. So every beat whose number is the point (`+6.2`,
   `+1.4`, `0.60→0.71`, `REJECT`, `T-00:42`) must surface that **exact literal in the table's gist** as the
   to-be-gated token; a beat with no audited number → its panel becomes `text_mode: "html"` downstream. The
   motif arcs (DDL, exact_parse, claim_delta) are precisely the literal source the gate will token-diff later.

## Worked example
A converged, **user-approved** outline ships in
[`examples/comic_m3_audit/story/`](../../examples/comic_m3_audit/story/) — the ARIS-Movie comic *"我把那 24
小时交出去了 / I Handed Over Those 24 Hours"*. The exact files to copy the shape from:

- **The 3 lenses** —
  [`outline_candidate_faithful.md`](../../examples/comic_m3_audit/story/outline_candidate_faithful.md) (22
  shots → 22 panels, beat boundaries preserved, ends with *"Through-line + deltas: one-to-one fidelity, …"*),
  [`outline_candidate_comicnative.md`](../../examples/comic_m3_audit/story/outline_candidate_comicnative.md)
  (S07-S09 → one 2×2 page P06; 22 → 12 panels; full-bleed / 2-up / 2×2 rhythm), and
  [`outline_candidate_clarity.md`](../../examples/comic_m3_audit/story/outline_candidate_clarity.md) (Tok|yo
  prop + bounce gauge carry the +6.2→+1.4 story for a non-ML reader). **Copy the pattern:** three named
  lenses over the *same* skeleton, each closing with an explicit `deltas vs the skeleton` section.
- **The approved outline** —
  [`OUTLINE_DRAFT.md`](../../examples/comic_m3_audit/story/OUTLINE_DRAFT.md). Copy its **exact** shape:
  - header provenance line: *"OUTLINE v2 — 3-lens debate → codex synthesis → codex design pass (B08 density +
    wiki) → user decisions. … ✅ APPROVED by user 2026-06-10 ('都可以') … Now the SOURCE OF TRUTH for the
    storyboard layer."* — the whole lifecycle is recorded in one line;
  - the `## ✅ 已定决策（用户 2026-06-10）` block (3 resolved open questions as decision nodes: S09 big /
    Tok|yo tiny, narration doesn't spell it out / B13 unlabeled glowing star-points);
  - the verbatim `## 🎙️ 侧栏讲解铁律` block;
  - the 13-row **6-column beat table** (every `ARIS 特性` cell is a story cost, e.g.
    `experiment-bridge（证据是暂定的）`);
  - the **B08 5-page sub-plan** with the 70/30 rule + event-first / trait-second 侧栏;
  - the `## vs v1 的增量` deltas (`22 → ~24` panels, +S12a +S16b) and the `## ⚠️ 待你确认` block.

Copy its shape; swap in your own logline / skeleton / cast.

## Hard do / don't (earned lessons)
- **DO** treat the skeleton as **locked** and make every candidate self-report its `deltas vs the skeleton` —
  adapt, never re-derive; a candidate with no deltas section is a veto.
- **DO** write **3** lenses (faithful ∥ comicnative ∥ clarity) and let **Codex (a different model family)**
  synthesize + run the density pass — the outline layer is a cross-model artifact, not a solo draft.
- **DO** bind **every** capability to a **story cost** and **embed the 侧栏讲解铁律 verbatim** — this is the
  guard that stops a capability showcase from rotting into a product manual.
- **DO** lock the **motif arcs with exact per-shot values at outline time** — the outline is the storyboard's
  continuity contract; vague motifs make the downstream gate uncheckable.
- **DON'T** put a **skill name in a 画面 main label** — skill names live ONLY in side-narration small-text /
  hover metadata.
- **DON'T** advance to the storyboard with **open questions unresolved** — empty the `⚠️ 待确认` block into
  `已定决策` first; resolved questions are recorded decision nodes.
- **DON'T** **batch** ahead, and **never draft (or proceed) without explicit user story approval** — the user
  is the only acquitter; record `✅ APPROVED <date>` inline before locking. (Memory: *never draft
  outline/storyboard without explicit user story approval; confirm intent → outline → storyboard layer by
  layer.*)
- **DON'T** bake or invent — this skill produces a *plan*; pixels are `comic-director`'s job, and a missing
  beat/shot is an **ESCALATE**, not a fabrication.
- **DON'T** silently coerce a value to pass schema or to pass the gate — change the narrative + document it,
  or surface to the user.

## Protocols (governance contracts this skill honors)
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — the Codex synthesizer + the gate
  reviewer get the lens files + `intent_spec` + schema inside an `=== EXTERNAL CONTEXT (advisory) ===` fence,
  never the author's interpretation; the Claude lens authors ≠ the Codex synthesizer/judge.
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — the loop can DRIVE to a clean cross-model gate but
  cannot ACQUIT; **USER approval is the hard gate** for the outline (never proceed without it), recorded
  inline as `✅ APPROVED <date>` + the `已定决策` decision block.
- [`fan-out-pattern`](../../protocols/fan-out-pattern.md) — the 3 lenses are **Tier-1 Workflow fan-out**
  (faithful ∥ comicnative ∥ clarity), all reconciled at the single Codex synthesis seat; `<3` lenses is a
  veto.
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Codex `gpt-5.5` `xhigh` (synthesizer + gate);
  Gemini `auto-gemini-3` (optional readability co-reviewer); never downgrade the tier.
- [`review-tracing`](../../protocols/review-tracing.md) — every gate round's reviewer verdict + the user
  decision are logged as `review` / `decision` nodes so each verdict is auditable.
- [`output-versioning`](../../protocols/output-versioning.md) · [`resumable-runs`](../../protocols/resumable-runs.md)
  — version the outline (`_v{N}` + `supersedes`); `OUTLINE_STATE.json` makes the loop resumable.
