---
name: method-figure
description: "Generate a publication-grade method / architecture / pipeline / workflow figure (a paper or README 'Figure 1') as an AUDITABLE object, not a one-shot prompt. A deterministic JSON blueprint LOCKS the content; an image model (gpt-image-2, driven by Codex GPT-5.5 xhigh, sandbox read-only) bakes the aesthetic from a labeled-condition render + the project's real identity refs; a 3-model panel (Claude ‖ Gemini ‖ Codex) blind-transcribes the result and a script hard-diffs it against the blueprint; the loop regenerates until the panel + the diff unanimously pass. NOT for statistical plots (use a plotting tool) or photo scenes."
argument-hint: [system-description | blueprint.json]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, mcp__codex__codex, mcp__codex__codex-reply, mcp__gemini-cli__ask-gemini, mcp__gemini__chat
---

# method-figure

Turn "draw our method figure" from a one-shot gamble into the **same audited spiral the framework uses for
comics**: a blueprint is the source of truth, the image model bakes the look, a cross-model panel + a
deterministic diff keep it honest, and the loop converges to a publication-grade figure that is
**reproducible** (re-run the blueprint) and **auditable** (a trace of every round).

Two things are simultaneously true: (a) gpt-image-2 CAN render a clean Figure-1 with legible labels when
*conditioned on a labeled blueprint* — do not assume it garbles text; (b) on a free prompt it DRIFTS
(renames phases, invents nodes, garbles a token, leaves pasted-looking floating labels). The blueprint +
blind-transcribe-then-hard-diff loop turns (a) into a reliable result and catches (b) every round.

```text
  system description ─▶ ① BLUEPRINT (JSON content-lock)  ── validate_blueprint.py
                              ▼
                        ② CONDITION (white-bg labeled SVG → PNG) + identity sheet (real chibi, optional)  ── render_condition.py --png
                              ▼
                        ③ BAKE  — codex MCP gpt-5.5-xhigh, sandbox:read-only → gpt-image-2  ── pickup_image.py (lock+marker+sha+dims+log, fail-closed)
                              ▼
                        ④ PANEL — Claude ‖ Gemini ‖ Codex BLIND-transcribe → content_diff.py (observed ⊖ blueprint)
                              ▼
                        ⑤ agent reads the diff + the panel blockers → re-bake re-asserting the locked labels
                              ▼
                   converged? ─ no ─▶ ③   (bounded: max_rounds → escalate to human)
                              │ yes
                              ▼
                        ⑥ APPROVE → figure.png + blueprint.json + trace.jsonl
```

## Constants
- **GENERATOR** = `mcp__codex__codex`, `model_reasoning_effort: xhigh`, **`sandbox: "read-only"`** — read-only
  FORCES the native `image_generation` tool (else Codex pivots to writing an SVG renderer). Output lands in
  `~/.codex/generated_images`; pick it up with `pickup_image.py` (verifies a real native PNG, fail-closed).
- **PANEL** = Claude (this agent) ‖ `mcp__gemini-cli__ask-gemini` (`auto-gemini-3`) ‖ `mcp__codex__codex` (gpt-5.5 xhigh).
- **CROSS-MODEL ACQUITTAL** — Codex is the generation family, so a Codex `approve` can only *diagnose/veto*,
  never be the sole acquitter. ACCEPT requires **Gemini approve + Claude structural approve + the hard-diff empty**.
- **MAX_ROUNDS** = 4, then escalate to human with best-so-far + open blockers.
- **LABEL_POLICY** = **`baked` only in v0** — the image model renders ALL text; nothing is hand-pasted.
  (`hybrid`/`overlay` — lock structure + vector-overlay the labels for paper zero-tolerance text — are on the
  v1 roadmap; do NOT use a vector overlay as an ad-hoc patch on a finished bake, it reads as pasted.)
- **OUTPUT_DIR** = `figures/method_figure/<figure_id>/` (figure.png, blueprint.json, condition.svg, trace.jsonl).
- **NATIVE-IMAGE FAIL-CLOSED** — accept a bake ONLY if a real PNG appeared after the marker, sha/size/dims
  check out, and the codex log shows no shell/python/SVG fallback (`pickup_image.py --log`).
- **SERIALIZE BAKES** — never run two image generations at once; the global generated-images dir + the
  newest-after-marker pickup will cross-pollinate.

## Input contract / ARIS hand-off (who decides WHAT, who only renders)
This skill is **pure render + verify**. The contract boundary is **`blueprint.json`**. Ownership:
- **Upstream owns the semantics** — what to depict, the labels, the graph, the grouping, the headline
  claim/number, the identity refs. method-figure does NOT choose content and **must not invent** a node,
  claim, number, or method structure (if one is missing it ESCALATES, it does not make it up).
- **Step-0 (an LLM authoring step) owns translation** — turn the upstream brief/prose into a schema-valid
  `blueprint.json` (`schemas/blueprint.schema.json`), preserving every claim/number verbatim. See
  `references/blueprint_authoring.md`.
- **method-figure owns** validation → condition render → image bake → cross-model panel → diff → retry, and
  has VETO power: it returns `FAILED / Logic Drift` rather than ship a figure whose pixels contradict the blueprint.

**The direct input** = `blueprint.json` (+ optional `identity_sheet.png` — the project's "visual constitution",
read-only here). **Where the blueprint comes from**, in authority order:
1. an existing `blueprint.json` (use as-is) ·
2. **a `method_figure_brief`** (`schemas/method_figure_brief.schema.json`) — the canonical ARIS hand-off ·
3. an `experiment-plan` method spec (fallback for an implementation/workflow diagram) ·
4. a `paper-write` method section (prose — weakest, lossy) ·
5. a free-text system/method description.

**ARIS integration:** the canonical producer is **`paper-plan`** — after its `claims_matrix`, it emits a
**`method_figure_brief`** (the components, flows, phases, the headline claim/number, identity refs,
`forbidden_tokens`). The ARIS main agent runs **Step-0** to convert that brief into `blueprint.json` (with a
**traceability matrix**: every node/edge must trace to a brief field — an un-traceable node is a Refuse-and-
Escalate, not a render), then runs method-figure. `experiment-plan`/`paper-write`/free-text are accepted
alternates when no plan exists. The identity sheet is created once (e.g. by `research-refine`) and locked by
`paper-plan`; method-figure only reads it.

## Fast path — one command
After you author `blueprint.json` (step ① below), the whole loop is one command:
```bash
python3 scripts/run_spiral.py blueprint.json --identity identity_sheet.png --out-dir figures/method_figure/<id>
#  validates → renders condition(+png) → [bake (codex image_gen, read-only, serialized under a lock) →
#  pickup+verify (fail-closed) → Gemini + Codex blind-transcribe → content_diff → consolidate blockers] × rounds
#  → on PANEL-CLEAN writes figure.png + blueprint.json + trace.jsonl.
#  --dry-run prints the round-1 bake prompt (no image gen);  --max-rounds N;  --effort high|xhigh.
```
Long-running (each bake ~3-8 min) — run it in the background; watch `trace.jsonl`. It converges to
**PANEL-CLEAN** — BOTH reviewers returned parseable JSON, **Gemini approve AND Codex approve**, the
deterministic `content_diff` empty, core scores (incl. `character_identity` when an identity sheet is given)
≥ threshold, and no anomalies/blockers — then STOPS and hands to the calling agent (Claude) for the final
**structural** sign-off (the generator family never self-acquits). The manual steps below are exactly what
`run_spiral.py` automates (run them to debug one stage).

## Workflow (what run_spiral.py automates — or run by hand)

### ① Author the BLUEPRINT (content lock)
Write `blueprint.json` per `schemas/blueprint.schema.json`. The `*_exact` fields (`label_exact`, `desc_exact`,
group/edge/callout `*_exact`, `rail.label_exact`) are the **LOCKED text re-asserted verbatim every round**;
`expected_tokens[]` are what the panel must blind-transcribe and the diff checks. Then:
```bash
python3 scripts/validate_blueprint.py blueprint.json   # jsonschema (if installed) + unique ids · edges resolve · box/group/callout bounds · no dup labels
```

### ② Render the CONDITION
```bash
python3 scripts/render_condition.py blueprint.json --out condition.svg --png condition.png   # white-bg labeled layout → rasterized
```
Prepare `identity_sheet.png` from the project's REAL characters if the figure has any (never invent robots).
The condition PNG + the identity sheet are the two image references.

### ③ BAKE (round N) — serialized
Record a marker timestamp, then call `mcp__codex__codex` (sandbox **read-only**, effort xhigh) with the
prompt from `references/prompt_templates.md §A` — it RE-ASSERTS every `*_exact` label + the round-N blockers
+ the carried `positive_invariants`, with `condition.png` + `identity_sheet.png` as read-only references. Then:
```bash
python3 scripts/pickup_image.py --marker <epoch> --out figures/method_figure/<id>/round<N>.png --log codex_bake.log --aspect <W/H>
```

### ④ PANEL — blind transcribe, then hard diff
Ask each reviewer (`references/prompt_templates.md §B`) for the STRICT JSON of
`references/reviewer_protocol.md` — they transcribe `observed_tokens` / `observed_edges` / `identity_audit`
and an `anomalies` list (the **Negative-Space Audit**), NOT shown the expected labels. Save as
`round<N>.{cc,gemini,codex}.json`, then:
```bash
python3 scripts/content_diff.py blueprint.json round<N>.cc.json round<N>.gemini.json round<N>.codex.json
# → missing_tokens / unaccounted_tokens / anomalies ; empty == content-accurate
```

### ⑤ Decide (stop rule) — the agent consolidates
Read the diff report + the three reviewers' `blockers`. The executing agent itself merges **blockers only**
(ignore `nice_to_have` — chasing polish makes it oscillate), carries the union of `positive_invariants`
forward, and writes the round-N+1 bake prompt.
- **ACCEPT** iff: diff has no `missing_tokens`/`anomalies` · Gemini `approve` · Claude structural `approve` ·
  every core score ≥ `acceptance.min_core_score` (default 4). (Codex may veto but can't be the sole acquitter.)
- **RETRY** iff: blockers are prompt/condition-fixable and `round < MAX_ROUNDS` → back to ③.
- **ESCALATE** to human iff: same root failure 2 rounds · irreconcilable reviewers · MAX_ROUNDS hit · or a
  non-prompt-fixable failure (throttle / identity drift / no native image).

### ⑥ Finalize + trace
On ACCEPT: copy the approved PNG to `figures/method_figure/<id>/figure.png`, keep `blueprint.json`, and append
to `trace.jsonl` per round: `{round, blueprint_sha, condition_sha, generated_sha, reviewers:{...verdicts},
hard_diff:{missing_tokens,anomalies}, fixes:[...], decision}` + a final `{final_approve, image, blueprint,
accepted_round, verdicts}`. Failures are kept — the fixes that were needed are the memory (the figure-wiki).

## Hard do / don't (earned lessons)
- **DO** lock content in the blueprint and RE-ASSERT every `*_exact` label in every regeneration — image
  models drift content every round; the blueprint is the anchor.
- **DO** force the native image tool (read-only sandbox) and fail-closed if no real PNG (`pickup_image.py --log`).
- **DO** use the project's real identity refs; anchor each character to the identity sheet.
- **DON'T** hand-paste text onto a finished bake (reads as pasted/fake) — that is what burned us; the whole
  figure, text included, is generated. (Engineered vector overlay is a future *policy*, not a patch.)
- **DON'T** use a dark theme for a paper/README figure — light/pastel on white.
- **DON'T** let one model (especially the generator's family) self-acquit; the panel is cross-model.

## Scope
| Figure type | Fit |
|---|---|
| method overview / pipeline / architecture / workflow | **excellent** |
| conceptual / taxonomy / comparison diagrams | good |
| statistical plots | no → plotting tool |
| exact-topology deterministic vector figures | prefer a pure-vector renderer |
| photo-realistic scenes / long narrative comics | no (comics use the framework's spiral engine) |

A converged worked example ships in `examples/method_figure/`: the ARIS-Movie-Director Figure 1 — blueprint +
figure.png + condition.svg + the real 4-round `trace.jsonl` (unanimous 3-model APPROVE). `PROMPTS.md` there
publishes the **exact, unedited prompt sequence** that baked it (all 4 `gpt-image-2` bakes + the cross-model
critiques, paths redacted) — the canonical exhibit of *how detailed a condition must be*; copy its shape.

## Implemented / roadmap
- ✅ `scripts/run_spiral.py` — the one-command orchestrator (bake→pickup→panel→diff→consolidate→decide loop
  to PANEL-CLEAN). Folds blocker-consolidation + invariant-carry inline, so a separate `consolidate_reviews.py`
  isn't needed.
- 🔭 `scripts/overlay_labels.py` + `label_policy: hybrid/overlay` — vector-overlay the structured labels on
  the bake for paper zero-tolerance text. Default stays `baked` (fully generated).
- 🔭 a Claude-vision reviewer inside the orchestrator (currently the automated panel is Gemini + Codex +
  the deterministic diff; Claude — the calling agent — gives the structural sign-off on the converged figure).

## Protocols (governance contracts this skill honors)
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — reviewers blind-transcribe from the image only; the generator (Codex image_gen) ≠ the visual judges.
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — the loop drives, can't acquit: ACCEPT needs the deterministic content-diff clean + Gemini approve + Codex no-veto + Claude structural sign-off.
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — the baker doesn't judge its own figure's numbers; the blueprint is ground truth, verified by the blind diff.
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Codex `gpt-5.5` `xhigh`; Gemini `auto-gemini-3`; never downgrade.
- [`review-tracing`](../../protocols/review-tracing.md) — every round's reviewer verdicts are logged to `trace.jsonl`.
