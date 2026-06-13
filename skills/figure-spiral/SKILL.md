---
name: figure-spiral
description: "Generate a publication-grade method / architecture / pipeline figure as an AUDITABLE object, not a prompt artifact. A deterministic JSON blueprint locks the content; an image model (gpt-image-2, driven by Codex GPT-5.5 xhigh) bakes the aesthetic from a labeled-condition render + the project's real identity refs; a 3-model panel (Claude ‖ Gemini ‖ Codex) blind-transcribes the result and a script hard-diffs it against the blueprint; the loop regenerates until the panel + the diff unanimously pass. Use for README/paper Figure-1, system/architecture diagrams, method/workflow illustrations — NOT statistical plots or photo scenes."
argument-hint: [system-description | blueprint.json]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, mcp__codex__codex, mcp__codex__codex-reply, mcp__gemini-cli__ask-gemini, mcp__gemini__chat
---

# figure-spiral

Turn "draw our method figure" from a one-shot gamble into the **same audited spiral the framework uses for
comics**: a blueprint is the source of truth, the image model bakes the look, a cross-model panel + a
deterministic diff keep it honest, and the loop converges to a publication-grade figure that is
**reproducible** (re-run the blueprint) and **auditable** (a trace of every round).

This skill exists because two things are simultaneously true: (a) image models like gpt-image-2 CAN render
a clean Figure-1 with legible labels when *conditioned on a labeled blueprint* — do not assume they garble
text; (b) left to a free prompt they DRIFT (rename phases, invent nodes, garble a token, paste-looking
floating labels). The blueprint + blind-transcribe-then-hard-diff loop is what turns (a) into a reliable
result and catches (b) every round.

```text
  system description ──▶ ① BLUEPRINT (JSON, content lock)
                              │  validate_blueprint.py
                              ▼
                        ② CONDITION (white-bg labeled PNG)  +  identity sheet (real chibi, optional)
                              │  render_condition.py
                              ▼
                        ③ BAKE  — codex MCP gpt-5.5-xhigh, sandbox:read-only → gpt-image-2
                              │  pickup_image.py  (lock + marker + sha/size/dims verify · fail-closed)
                              ▼
                        ④ PANEL — Claude ‖ Gemini ‖ Codex  BLIND-transcribe tokens/edges/identity
                              │  content_diff.py  (observed  ⊖  blueprint.expected → missing/wrong/extra)
                              ▼
                        ⑤ CONSOLIDATE blockers only → re-bake re-asserting locked labels
                              │  (carry positive_invariants forward; never chase nice_to_have)
                              ▼
                   converged?  ── no ──▶ back to ③   (bounded: max_rounds → escalate to human)
                              │ yes
                              ▼
                        ⑥ APPROVE → output PNG + blueprint + trace.jsonl
```

## Constants

- **GENERATOR** = `mcp__codex__codex` with `model_reasoning_effort: xhigh`, **`sandbox: "read-only"`** — the
  read-only sandbox FORCES the native `image_generation` tool (otherwise Codex pivots to writing an SVG
  renderer). Pick up the PNG from `~/.codex/generated_images`.
- **PANEL** = Claude (this agent) ‖ `mcp__gemini-cli__ask-gemini` (model `auto-gemini-3`) ‖ `mcp__codex__codex` (gpt-5.5 xhigh).
- **CROSS-MODEL ACQUITTAL RULE** — Codex is the GENERATION family, so a Codex "approve" can only *veto* or
  *diagnose*; it can NEVER be the sole acquitter. Final accept requires **Gemini approve + the deterministic
  hard-diff empty** (and Claude structural approve). The maker is not the only judge.
- **MAX_ROUNDS** = 4 (then escalate to human with the best-so-far + the open blockers).
- **LABEL_POLICY** (in the blueprint, `render_policy.label_policy`):
  - `baked` (**default**) — the image model renders ALL text. Fully generated, nothing hand-pasted.
  - `hybrid` — image model renders the look + atmospheric text; the skill vector-overlays only the
    structured labels (group/node/edge) at blueprint coords for zero-tolerance accuracy.
  - `overlay` — image model renders a near-textless aesthetic base; ALL labels are crisp vector overlay.
  Pick `baked` for READMEs/talks; pick `hybrid`/`overlay` for a paper where a single wrong glyph is fatal.
- **OUTPUT_DIR** = `figures/figure_spiral/<figure_id>/` (the approved PNG, the blueprint, `trace.jsonl`).
- **NATIVE-IMAGE FAIL-CLOSED** — accept a bake ONLY if a real PNG appeared after the marker, sha/size/dims
  check out, and there is no shell/python/SVG-fallback in the codex log. Never let a hand-written SVG
  renderer masquerade as a generated image.

## Workflow — execute all steps

### Step 0 — author the BLUEPRINT (content lock)
Write `blueprint.json` per `schemas/blueprint.schema.json`: `canvas`, `render_policy` (label_policy,
target_profile, max_rounds), `assets[]` (identity sheets / refs with `lock_traits`), `groups[]`
(phase panels, `label_exact`), `nodes[]` (`label_exact`, `desc_exact`, `pos`, `shape`, `accent`,
`expected_tokens[]`, optional `asset_ref` for a character), `edges[]` (`from`, `to`, `kind`, `label_exact`,
`direction`), `callouts[]`, `acceptance`. **`*_exact` fields are the locked text** — every regeneration
re-asserts them verbatim. Then:
```bash
python3 scripts/validate_blueprint.py blueprint.json   # unique ids · edges resolve · bounds in canvas · no dup labels
```

### Step 1 — render the CONDITION
```bash
python3 scripts/render_condition.py blueprint.json --out condition.png   # clean white-bg labeled layout
```
Prepare an `identity_sheet.png` if the figure has characters/mascots — use the project's REAL assets
(never invent generic robots). The condition + identity sheet are the two image references.

### Step 2 — BAKE (round N)
Call `mcp__codex__codex` (sandbox **read-only**, effort xhigh) with: the condition + identity sheet as
read-only references, and the prompt from `references/prompt_templates.md` that RE-ASSERTS every `*_exact`
label and the round-N consolidated fix-list. Then:
```bash
python3 scripts/pickup_image.py --marker <ts> --out figures/figure_spiral/<id>/round<N>.png   # lock + verify, fail-closed
```
(If `label_policy != baked`, run `scripts/overlay_labels.py` on the bake before review.)

### Step 3 — PANEL (blind transcribe, then hard diff)
Each reviewer returns STRICT JSON per `references/reviewer_protocol.md` — they transcribe `observed_tokens`,
`observed_edges`, `identity_audit`, and an `anomalies` list (the **Negative Space Audit**: floating/pasted
text, artifacts, stray lines), and a fixed 0-5 rubric. They are NOT shown the expected labels first. Then:
```bash
python3 scripts/content_diff.py blueprint.json round<N>.cc.json round<N>.gemini.json round<N>.codex.json
# → missing_tokens / wrong_edges / extra(anomalies) ; empty == content-accurate
python3 scripts/consolidate_reviews.py ...   # merge BLOCKERS only; emit next-round fixes + decision
```

### Step 4 — decide (stop rule)
- **ACCEPT** iff: hard-diff empty · Gemini `approve` · Claude structural `approve` · all core scores ≥ 4 ·
  no anomalies · no timeout. (Codex may add a veto but cannot be the sole acquitter.)
- **RETRY** iff: blockers are prompt/condition-fixable and `round < MAX_ROUNDS` → consolidate blockers,
  carry `positive_invariants` forward, re-bake (Step 2).
- **ESCALATE** to human iff: the same root failure persists 2 rounds · reviewers conflict irreconcilably ·
  MAX_ROUNDS hit · or the failure is not prompt-fixable (throttle / identity drift / native-image missing).

### Step 5 — finalize
On ACCEPT: copy the approved PNG to `figures/figure_spiral/<id>/figure.png`, keep `blueprint.json`, and
write the `final_approve` record to `trace.jsonl`. The figure is now reproducible (blueprint) + auditable (trace).

## Trace (the figure-wiki)
Append one JSON line per round to `figures/figure_spiral/<id>/trace.jsonl`:
`{round, blueprint_sha, condition_sha, generated_sha, reviewers:{claude,gemini,codex verdicts}, hard_diff:{missing_tokens,wrong_edges}, fixes:[...], decision}`.
Final line: `{final_approve, image, blueprint, sha, accepted_round, verdicts}`. Failures are kept — the
fixes that were needed are the memory (same spirit as the research-wiki: *failures kept as memory*).

## Hard do / don't (the earned lessons)
- **DO** lock content in the blueprint and RE-ASSERT every `*_exact` label in every regeneration prompt —
  image models drift content every round; the blueprint is the anchor.
- **DO** force the native image tool (read-only sandbox) and fail-closed if no real PNG is produced.
- **DO** use the project's real identity refs; anchor each character to the identity sheet.
- **DON'T** hand-paste text onto a finished bake as a shortcut (it reads as fake/pasted). If you need
  guaranteed labels, use `label_policy: hybrid/overlay` (engineered vector overlay at blueprint coords) — a
  deliberate policy, not a patch.
- **DON'T** use a dark theme for a paper/README figure — light/pastel on white.
- **DON'T** let a single model (especially the generator's family) self-acquit; the panel is cross-model.
- **DON'T** chase `nice_to_have`s — consolidate only `blockers`, or the loop oscillates and never converges.

## Scope
| Figure type | Fit |
|---|---|
| method overview / pipeline / architecture / workflow | **excellent** |
| conceptual / taxonomy / comparison diagrams | good |
| statistical plots | no → use a plotting tool |
| deterministic exact-topology vector figures | prefer a pure-vector renderer |
| photo-realistic scenes | no |

A worked, converged example ships in `examples/method_figure/` (the ARIS-Movie-Director Figure 1: blueprint
+ final bake, 4 rounds, unanimous 3-model APPROVE).
