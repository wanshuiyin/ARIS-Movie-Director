# paper → `method_figure_brief.json` (the input-generation SOP)

`run_spiral.py` consumes a **`method_figure_brief.json`** (the single input). If you only have a **paper / method
section** and no brief yet, this is the repo-local SOP your coding agent follows to PRODUCE that brief. It is an
**agent procedure** (the agent reads the paper + fills the brief), not a CLI — the same shape as ARIS's
`paper-plan`, which emits this brief after its `claims_matrix`.

## Prerequisites (the bake + review stages need these on PATH)
- **`codex` CLI**, logged in + on PATH — the orchestrator SHELLS it (`codex exec`, NO model pin: it follows your
  local codex config, currently gpt-5.6-sol; effort xhigh) as the Codex blind-transcribe reviewer. The real bake
  is a SEPARATE seam: the calling agent's `mcp__codex__codex` tool services the `.bakereq.json` sidecar
  (`--bake-mode=agent`, `sandbox: workspace-write`, model `gpt-5.5` + `xhigh` — a hardcoded compat default) → the
  native image tool; a fail-closed verifier (not any sandbox setting) keeps it honest. (`codex exec` is retired for real bakes.)
- **`gemini` CLI**, logged in + on PATH — the Gemini blind-transcribe reviewer. REQUIRED for convergence: a round
  is panel-clean only with a parseable Gemini `approve`, so a missing/broken `gemini` CLI fails every round
  (there is NO Codex-only fallback).
- **headless Chrome / Chromium** — the condition SVG is rasterized to PNG for the bake.
- Python ≥ 3.9. Run **`run_spiral.py … --p0-only`** first: it's the zero-credit gate (compile + render + lint), so you confirm the brief is sound *before* spending any image credit. (`--dry-run` also needs no credit.)

## The contract
Output ONE file conforming to [`../schemas/method_figure_brief.schema.json`](../schemas/method_figure_brief.schema.json).
Required: `schema_version` (`"method-figure/brief/v1"` — `run_spiral.py` auto-detects a brief ONLY by this key),
`figure_id`, `figure_purpose`, `components[]`, `flows[]`. Everything is **copied VERBATIM from the
paper** — a number, name, or claim that is not in the source is an **escalation, not invention** (the compiler
re-checks this: `compile_brief.py --strict` refuses an un-traceable blueprint).

## The prompt (paste to your coding agent, with the paper/method section attached)
```
You are Step −1 of method-figure: turn the attached paper / method section into ONE method_figure_brief.json
conforming to skills/method-figure/schemas/method_figure_brief.schema.json. Rules:
- schema_version: "method-figure/brief/v1" VERBATIM — run_spiral.py's auto-detect keys on it; a brief without
  it is refused unless --from-brief is passed.
- figure_id: a slug; figure_purpose: e.g. "Figure 1 — <method> overview".
- components[]: every box the method needs — {id, label (exact on-figure text), one_line (≤1 line), role,
  phase (if the method has phases), visual_priority (core|primary|secondary|background)}. Use the paper's OWN
  component names verbatim.
- flows[]: every arrow — {from, to, kind (flow|keep|retry|repair|write|audit|human), label?, direction?}. from/to
  MUST be component ids.
- phases[] (optional): {id, label, members:[component ids]} — members MUST match each component's `phase`.
- headline_claim + headline_number: the ONE contribution + its featured result number, VERBATIM (e.g. "+1.4",
  "0.89"); leave both unset if the figure features no single number. caption_thesis: the one sentence the figure
  should make a reader feel.
- symbol_registry[]: every figure symbol ↔ its paper variable; keep figure_symbol == paper_variable.
- forbidden_tokens[]: wrong/competing names the figure must NOT contain.
- identity_refs[]: ONLY if the project has a locked visual identity (mascot/persona) — {id, path, traits:[≥1]}.
  Most papers have none → omit. target_profile: paper | readme | slide.
Copy every number/label/name verbatim; invent NOTHING. If a load-bearing piece is missing from the paper, STOP
and ask. Output only the JSON.
```

## Then
From the **repo root**:
`python3 skills/method-figure/scripts/run_spiral.py your_method_figure_brief.json --out-dir
figures/method_figure/<id> --from-brief` (`--from-brief` is belt-and-braces — the `schema_version` above already
auto-detects) — Step-0 (`compile_brief.py`) auto-compiles the brief → blueprint (fail-closed traceability) and
the spiral bakes + cross-model-verifies it. Worked example of a finished brief:
[`../examples/method_figure/method_figure_brief.json`](../examples/method_figure/method_figure_brief.json).
