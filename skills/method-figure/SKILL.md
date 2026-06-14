---
name: method-figure
description: "Generate a publication-grade method / architecture / pipeline / workflow figure (a paper or README 'Figure 1') as an AUDITABLE object, not a one-shot prompt. A deterministic JSON blueprint LOCKS the content; an image model (gpt-image-2, driven by Codex GPT-5.5 xhigh, sandbox read-only) bakes the aesthetic from a labeled-condition render + the project's real identity refs; a cross-model panel (Gemini + Codex) blind-transcribes the result and a script hard-diffs it against the blueprint; the loop regenerates until Gemini approves, Codex does not veto, and the diff is empty — then the calling agent (Claude) gives the structural sign-off. NOT for statistical plots (use a plotting tool) or photo scenes."
argument-hint: [method_figure_brief.json | blueprint.json]
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
                        ③ BAKE  — codex exec --sandbox read-only (gpt-5.5-xhigh) → gpt-image-2  ── pickup_image.py (lock+marker+sha+dims+log, fail-closed)
                              ▼
                        ④ PANEL — Gemini ‖ Codex BLIND-transcribe → content_diff.py (observed ⊖ blueprint) → Claude structural sign-off
                              ▼
                        ⑤ agent reads the diff + the panel blockers → re-bake re-asserting the locked labels
                              ▼
                   converged? ─ no ─▶ ③   (bounded: max_rounds → escalate to human)
                              │ yes
                              ▼
                        ⑥ APPROVE → figure.png + blueprint.json + trace.jsonl
```

## Constants
- **GENERATOR** = Codex `gpt-5.5`, `model_reasoning_effort: xhigh`, **`sandbox: "read-only"`** → the native
  `image_generation` tool (gpt-image-2). read-only is what FORCES the image tool (else Codex pivots to writing
  an SVG renderer). `run_spiral.py` drives this via **`codex exec --sandbox read-only`** (no agent runtime
  needed); an interactive agent may equivalently call **`mcp__codex__codex`** with `sandbox:"read-only"` — same
  model + tool. Output lands in `~/.codex/generated_images`; pick it up with `pickup_image.py` (verifies a real
  native PNG, fail-closed).
- **PANEL** (automated blind-transcribe) = `mcp__gemini-cli__ask-gemini` (`auto-gemini-3`) + `mcp__codex__codex`
  (gpt-5.5 xhigh) + the deterministic `content_diff`. **Claude (this agent) is the post-pass STRUCTURAL sign-off,
  not a blind transcriber** — the loop converges on Gemini-approve + Codex-no-veto + empty-diff, then Claude signs off.
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
This skill is **pure render + verify**. Ownership:
- **Upstream owns the semantics** — what to depict, the labels, the graph, the grouping, the headline
  claim/number, the identity refs. method-figure does NOT choose content and **must not invent** a node,
  claim, number, or method structure (if one is missing it ESCALATES, it does not make it up).
- **Step-0 is now DETERMINISTIC** — `run_spiral.py` calls [`scripts/compile_brief.py`](scripts/compile_brief.py)
  to map a `method_figure_brief.json` → a schema-valid `blueprint.json` + `traceability.json`, fail-closed (an
  object that can't trace to a brief field, or a missing claim/number/trait, is refused — not invented). It is
  no longer a manual LLM hop. Full field map + the guards: `references/blueprint_authoring.md`.
- **method-figure owns** validation → condition render → image bake → cross-model panel → diff → retry, and
  has VETO power: it returns `FAILED / Logic Drift` rather than ship a figure whose pixels contradict the blueprint.

**The default single input** = a **`method_figure_brief.json`** (`schemas/method_figure_brief.schema.json`) —
ONE ARIS-format file; the blueprint, the coordinates, and the identity wiring are all derived. The identity
sheet is resolved from the brief's `identity_refs[].path` (no separate `--identity` to manage). **Where the
input comes from**, in authority order:
1. **a `method_figure_brief.json`** — the canonical ARIS hand-off (what `paper-plan` emits); auto-detected + compiled. ·
2. an existing hand-tuned `blueprint.json` — power-user override (`--from-blueprint`, used as-is). ·
3. an `experiment-plan` / `paper-write` method section / free-text — no brief yet: the agent first DRAFTS a
   `method_figure_brief.json` from it (claims/numbers verbatim; anything missing → Refuse-and-Escalate), then compiles.

**ARIS integration:** the canonical producer is **`paper-plan`** — after its `claims_matrix` it emits the
`method_figure_brief` (components, flows, phases, the headline claim/number, identity refs, `forbidden_tokens`).
You feed that **one file** to `run_spiral.py`; Step-0 compiles it and the traceability is enforced by the
compiler (an un-traceable object is a Refuse-and-Escalate, not a render). The identity sheet is created once
upstream and locked; method-figure only reads it.

## Fast path — one command (single input: a brief)
Feed ONE `method_figure_brief.json`; the whole loop is one command:
```bash
python3 scripts/run_spiral.py your_method_figure_brief.json --out-dir figures/method_figure/<id>
#  auto-detects a brief → Step-0 compile_brief.py → blueprint.json + traceability.json (deterministic, fail-closed)
#  → validates → renders condition(+png) → [bake (codex exec --sandbox read-only → gpt-image-2, serialized under
#  a lock) → pickup+verify (fail-closed) → Gemini + Codex blind-transcribe → content_diff → blockers] × rounds
#  → on PANEL-CLEAN writes figure.png + blueprint.json + traceability.json + trace.jsonl.
#  input auto-detect: brief (components+flows) vs blueprint (version) vs ambiguous → fail-closed (--from-brief/--from-blueprint)
#  --identity is OPTIONAL (resolved from the brief's identity_refs[0].path);  --dry-run prints the round-1 bake
#  prompt;  --p0-only runs the zero-credit gate (validate+compile+render) then stops;  --max-rounds N;  --effort high|xhigh.
```
> **Power-user / override:** already have a hand-tuned blueprint? `run_spiral.py blueprint.json --identity
> sheet.png --out-dir … --from-blueprint` runs the legacy path unchanged. A worked example brief lives at
> [`examples/method_figure/method_figure_brief.json`](examples/method_figure/method_figure_brief.json).
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
- **DO** use the project's real identity refs; anchor each character to the identity sheet. For a character
  figure, every reviewer ENUMERATES each chibi's visible hands — a wrong count / 3rd / floating / merged limb
  is a single-reviewer veto (the literal-diff is blind to anatomy).
- **DO** run the zero-credit P0 gate before the first metered bake: `run_spiral.py brief.json --out-dir … --p0-only`
  (validate brief → compile blueprint → render condition → confirm the bake prompt carries ALL locked labels,
  the identity path resolves, the background is white). A blocker caught here costs zero image credits.
- **DON'T** regenerate when the score-signature is IDENTICAL across rounds — that means the judge is broken
  (gone design-blind), not the figure. Stop and audit the rubric (`feedback_gate_identical_scores_judge_broken`).
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
figure.png + condition.svg + the real 4-round `trace.jsonl` (Gemini approve + Codex approve + empty diff, then
Claude's structural sign-off). `PROMPTS.md` there
publishes the **exact, unedited prompt sequence** that baked it (all 4 `gpt-image-2` bakes + the cross-model
critiques, paths redacted) — the canonical exhibit of *how detailed a condition must be*; copy its shape.

## Implemented / roadmap
- ✅ `scripts/compile_brief.py` — **Step-0 automation**: deterministic `method_figure_brief.json` →
  `blueprint.json` + `traceability.json` (the ADJ-4 field map, `auto_layout`, fail-closed
  `validate_traceability`). This is what makes the skill single-input — `run_spiral.py brief.json` auto-detects
  + compiles, so you never hand-write a blueprint or hand-place coordinates.
- ✅ `scripts/run_spiral.py` — the one-command orchestrator (sniff input → [Step-0 if brief] → bake→pickup→
  panel→diff→consolidate→decide loop to PANEL-CLEAN). `--p0-only` runs the zero-credit gate;
  `--from-brief`/`--from-blueprint` disambiguate. Folds blocker-consolidation + invariant-carry inline.
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
