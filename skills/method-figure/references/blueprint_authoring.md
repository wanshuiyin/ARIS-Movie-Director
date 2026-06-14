# Step-0 — authoring a blueprint (the prose/brief → blueprint.json reasoning step)

method-figure renders+verifies a `blueprint.json`; it does not decide content. **Step-0** is the LLM step that
produces that blueprint from an upstream source. It is a reasoning/compression task (NOT a deterministic
script) — but it has hard guardrails so it can't hallucinate a figure.

## Source, by authority order
1. an existing `blueprint.json` → use as-is (skip Step-0).
2. a **`method_figure_brief`** (`schemas/method_figure_brief.schema.json`) from **paper-plan** — the canonical input.
3. an `experiment-plan` method spec — fallback for an implementation/workflow diagram.
4. a `paper-write` method section (prose) — weakest; lossy; reverse-engineering risk.
5. a free-text system/method description.

If a needed claim / number / component identity is absent from the source, **ESCALATE for clarification —
do NOT invent it.** Numbers and claims are copied VERBATIM into `*_exact` / `expected_tokens`.

## The mapping (brief → blueprint)
| brief field | → blueprint |
|---|---|
| `components[]` (label, one_line) | `nodes[]` (`label_exact`, `desc_exact`); `visual_priority` → size/accent/center placement |
| `flows[]` (from,to,kind,label,direction) | `edges[]` (`label_exact`, `kind`, `direction`) |
| `phases[]` | `groups[]` (`label_exact`, `bounds`) + each node's `group` |
| `headline_claim` / `headline_number` / `callouts[]` | `callouts[]` (`title_exact`, `lines_exact`) — the figure's punchline |
| `identity_refs[]` | `assets[]` (role=identity_sheet, `lock_traits`) + node `asset_ref` |
| `caption_thesis` | the figure's intent (drives composition; not necessarily on-canvas) |
| `topology_constraint` | the layout logic (linear / feedback_loop / hierarchical / left_to_right_phases) — don't free-style it |
| `symbol_registry` | keep figure symbols == paper variables; put both in `expected_tokens` if shown |
| `forbidden_tokens` | node `forbidden_tokens[]` (terms the figure must not contain) |
| exact on-canvas text | `*_exact` fields (LOCKED, re-asserted every bake round) |
| audit-required text | `expected_tokens[]` (what the panel must blind-transcribe and the diff checks) |

## Guardrail — the traceability matrix (anti-hallucinated-logic)
The #1 Step-0 risk is the LLM adding an intermediate step / control flow that "looks professional" but is
NOT in the source. So:
- Every blueprint `node` and `edge` MUST trace to a specific brief field. Populate the optional node
  field **`source`** with the brief component id it came from (`"source": "brief:components/<id>"`).
- After authoring, emit a small **traceability matrix** (`{node_id|edge: brief_field}`) alongside the blueprint.
- An un-traceable node/edge is a **Refuse-and-Escalate**, never a silent render. (A reviewer/agent can scan
  for nodes whose `source` is empty when a brief was provided.)

## Worked authoring prompt (paste to the authoring LLM)
```
You are Step-0 of method-figure. Convert the attached method_figure_brief (or method description) into a
schema-valid blueprint.json per schemas/blueprint.schema.json. Rules:
- Map components→nodes (label_exact + desc_exact), flows→edges, phases→groups, headline claim/number→a callout.
- Copy every number/claim/name VERBATIM into *_exact and expected_tokens. Do NOT paraphrase or invent.
- Do NOT add any node, edge, phase, or term that is not in the brief. If something needed is missing, STOP
  and ask — do not fill the gap.
- Set each node's `source` to the brief field it came from. Also output a traceability matrix mapping every
  node/edge to its brief field.
- Honor topology_constraint for the layout; give `visual_priority:core` components more size/center.
- Lay out positions on the canvas (white bg) so the three phases read left→right and nothing overlaps;
  run scripts/validate_blueprint.py and fix any error before finishing.
Output: blueprint.json + the traceability matrix.
```
Then hand `blueprint.json` (+ identity sheet) to `run_spiral.py`. method-figure renders + the cross-model
panel verifies; if pixels contradict the blueprint it returns FAILED/Logic-Drift rather than shipping it.
