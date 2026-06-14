# Step-0 — brief → blueprint, the compile-first reference

method-figure renders + verifies a `blueprint.json`; it does not decide content. **Step-0** turns an upstream
brief into that blueprint. As of the single-input upgrade, **Step-0 is a deterministic compile, not an LLM
hop**: when a `method_figure_brief.json` exists, `run_spiral.py` calls
[`scripts/compile_brief.py`](../scripts/compile_brief.py) (map → `validate_traceability` → write
`blueprint.json` + `traceability.json`) and proceeds. You do **not** hand-author a blueprint or hand-place
coordinates. The LLM's judgement moves to where it belongs: **upstream** (authoring the brief, when only prose
exists) and **downstream** (the structural sign-off after the cross-model panel passes).

## Source, by authority order
1. an existing `blueprint.json` → use as-is: `run_spiral.py blueprint.json --identity sheet.png --out-dir DIR --from-blueprint` (skip Step-0; `--out-dir` is required).
2. a **`method_figure_brief.json`** ([`schemas/method_figure_brief.schema.json`](../schemas/method_figure_brief.schema.json),
   what **paper-plan** emits after its claims_matrix) → **the canonical single input.** `run_spiral.py brief.json
   --out-dir …` auto-detects it and compiles. **You feed one file.**
3. an `experiment-plan` / `paper-write` method section / free-text description → no brief yet: the agent FIRST
   drafts a `method_figure_brief.json` (NOT a blueprint), copying every claim/number/name **verbatim**, then
   runs the command above. A missing claim/number/identity-trait is a **Refuse-and-Escalate**, never invented.

## The deterministic mapping (ADJ-4 — what `compile_brief.py` does; authoritative)
Every brief field maps to a blueprint object, and every blueprint object records the brief field it came from
(`source`). This table supersedes any older partial mapping.

| brief field | → blueprint | notes |
|---|---|---|
| `components[]` `.label` / `.one_line` | `nodes[]` `label_exact` / `desc_exact` | locked text |
| `components[].role` | `node.semantic_role` | (was previously dropped) |
| `components[].visual_priority` | `node.size` via `auto_layout` (bigger = higher priority) | **size only — NO center-weighting** |
| `components[].identity_ref` | `node.asset_ref` | anchors a character to its sheet |
| `components[].phase` | `node.group` + the group `tone`/`accent` | grouping is driven by `component.phase`; `phases[].members` is **consistency-checked** against it (must agree), not the grouping source |
| `flows[]` | `edges[]` `from/to/kind/label_exact/direction` | every `kind` ∈ the schema edge enum |
| `phases[]` | `groups[]` `label_exact` + `bounds` | bounds computed by `auto_layout`, never hand-set |
| `headline_claim` + `headline_number` | a `callouts[]` punchline: `title_exact` ← claim; the **number lands in `lines_exact` AND `expected_tokens`** | so the blind-diff catches a garbled number (the `+6.2`/`+6.25` failure) |
| `callouts[]` | additional `callouts[]` | |
| `caption_thesis` | `title.sub` **AND** the punchline callout's `lines_exact` | composition intent + the felt thesis line |
| `identity_refs[]` | `assets[]` (`role: identity_sheet`, `lock_traits` ← `traits`) | the single pointer to the sheet |
| `symbol_registry[]` | the relevant node's `expected_tokens` (figure_symbol kept **==** paper_variable) | anti-drift |
| `topology_constraint` | drives `auto_layout` (linear_flow / feedback_loop / hierarchical_stack / left_to_right_phases / free) | don't free-style topology |
| `target_profile` | `render_policy.target_profile` — **passed explicitly** | brief default `paper` must not fall to the blueprint default `readme` |
| `forbidden_tokens` | blueprint **top-level** `forbidden_tokens` + every node's `forbidden_tokens` + the per-round DELETE-list | injected into every bake prompt's DELETE-list |
| `figure_id` | `blueprint.figure_id` + `compiled_from_brief.type` | |
| `figure_purpose` | `title.main` | |
| `inputs[]` / `outputs[]` | leading `document` / trailing `output` nodes (only when not already a component id) | |
| `callouts[].anchor` | `callout.anchor` | passed through |

The compiler also stamps `compiled_from_brief: {type}` (which makes `validate_blueprint.py` require a `source`
on every object) and an honest `acceptance` block (`required_transcribers:["gemini","codex"]`,
`codex_policy:"required_not_sole"` — Codex approve is required but never the sole acquitter,
`claude_structural_signoff_required:true`) matching what `run_spiral.py` actually runs.

## The guards (enforced by the compiler + the gate + the panel — not by a prompt)
1. **Traceability is a gate (GUARD-10).** Every node/edge/group/callout/asset/locked-token maps to `brief:*`.
   No untraced `self_critique` / invented time-tags / renamed phases. `compile_brief.py --strict` (the default)
   refuses to emit and names the offending field — a missing number/claim/trait is an escalation, not license.
2. **White background (GUARD-1).** For `target_profile ∈ {readme,paper,slide}` the canvas is white/light. A
   dark base is a prohibited dead end (see the R1 fossil below). Enforced on BOTH sides: the render/policy sets
   white, AND the reviewer panel's `style_fit` vetoes a dark/low-contrast bake — one check is not enough.
3. **Condition, not paste (GUARD-2).** `condition.svg/png` is a LAYOUT CONTRACT + prompt reference; the final
   image is natively baked from it. No post-hoc vector overlay, no pasted edge-pills, no `*_overlay.svg` repair
   path. `label_policy` stays `baked` in v0 (`hybrid`/`overlay` is a future *policy*, not a fix for a bad bake).
4. **Force the native tool, fail-closed (GUARD-4).** The bake runs Codex `gpt-5.5 xhigh` with
   **`sandbox: read-only`** — read-only is what FORCES the native `image_generation` tool (else Codex pivots to
   writing an SVG renderer). `pickup_image.py` verifies a real native PNG (marker + sha + dims), fail-closed.
5. **Exact locks re-asserted EVERY round (GUARD-3).** `run_spiral.locked_labels(bp)` re-emits every `*_exact`
   (group/node/edge/callout/rail) + every exact numeric token into every bake prompt — a regeneration may not
   silently drop or rename a label.
6. **Identity + anatomy (GUARD-5).** Identity-lock is active ONLY when `identity_refs[]` exists. For character
   figures every reviewer **ENUMERATES each chibi's visible hands**; a wrong count / a 3rd hand / a floating or
   merged limb is a **single-reviewer veto** (the literal-diff is blind to anatomy). Contradictory pose specs
   (crossed arms + raised hand) must fail before the bake, not after.
7. **Blind-transcribe → deterministic diff (GUARD-7).** The panel (Gemini + Codex) transcribes what it SEES
   without being shown the expected values; `content_diff.py` does `observed ⊖ blueprint`. "Looks right" never
   passes — only an empty literal-diff + the visual panel + Claude's structural sign-off does.
8. **Round repair = blockers-only + a DELETE-list (GUARD-8).** Each retry carries blockers + positive
   invariants + an explicit DELETE-list (`brief.forbidden_tokens ∪ prior-round unaccounted_tokens`). Nice-to-have
   is never carried. **Identical score-signatures across rounds ⇒ `judge_audit_required`** — stop regenerating
   and audit the rubric (it has gone design-blind), the lesson from `feedback_gate_identical_scores_judge_broken`.
9. **Zero-credit P0 gate (GUARD-9).** Before any metered `image_gen`: validate the brief → compile the
   blueprint → render the condition → lint that the bake prompt contains ALL locked labels → identity paths
   resolve → background is white → the DELETE-list is present. `run_spiral.py … --p0-only` runs exactly this and
   stops. A blocker here costs zero credits; a blocker found after baking costs a regeneration.
10. **Honest trace (GUARD-11).** Failed rounds STAY in `trace.jsonl`. Manual post-run polish is logged in
    `docs/GENERATION_RETRO.md`, **never** back-written as a synthetic spiral node (that would fake the audit).

## The real R1→R4 journey (the history this crystallizes — see `examples/method_figure/PROMPTS.md` + `trace.jsonl`)
The figure was iterated many times; the dead ends are the lesson, not noise:
- **R1 — dark base.** The first bakes used a dark/moody background. It looked like a product splash, not a
  paper Figure-1: low label contrast, "pasted"-looking floating text. → GUARD-1 (white) was born here.
- **R2 — vector-overlay repair (abandoned).** To "fix" the labels we tried compositing a vector overlay over
  the bake. The result read as pasted-on, and it broke the single-image contract. We abandoned overlay as a
  repair path → GUARD-2 (condition, not paste): the condition is a reference the model bakes FROM, not a layer
  glued ON. (Overlay survives only as a hypothetical future *policy*, never as a fix for a bad bake.)
- **R3 — white + condition + locked labels.** White canvas, the labeled condition as reference image 1, the
  identity sheet as image 2, every `*_exact` re-asserted in the prompt. Close — but a number drifted
  (`+6.2`→`+6.25`) and a chibi came back with a miscounted hand, which "looks right" sailed past a lazy glance.
  → GUARD-7 (blind diff catches the number) + GUARD-5 (enumerate hands) were born here.
- **R4 — converged.** Re-assert exact labels + the number in `expected_tokens` + per-hand enumeration + white
  bg → empty literal-diff + clean visual panel + structural sign-off. `PROMPTS.md` holds the literal prompts and
  critiques of all four rounds; `trace.jsonl` holds the per-round verdicts. That history is the spec, crystallized.

## Power-user / legacy: hand-authoring a blueprint
You rarely need this (the brief path is the default). If you DO hand-tune a blueprint, run
`run_spiral.py blueprint.json --identity sheet.png --out-dir … --from-blueprint`. The same guards apply; the
only difference is you own the field map yourself. Run `scripts/validate_blueprint.py` before baking. Do not
hand-author a blueprint when a brief exists — compile the brief so traceability is enforced for free.
