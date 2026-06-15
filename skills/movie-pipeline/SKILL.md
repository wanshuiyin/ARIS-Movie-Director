---
name: movie-pipeline
description: End-to-end Pipeline A in ONE slash-command — turn a fuzzy story idea into a cross-model-audited, image-based movie + a clickable viewer. Chains comic-author (Phase 1 — intent→style→outline→storyboard→assets→blueprints→prompts→comic.json) → the zero-credit p0_proof gate → comic-director (Phase 2/3 — the audited spiral bake → HTML viewer). Two hard HUMAN gates (intent + outline) pause for approval; everything else is agent-driven + cross-model gated. This is the slash-command entry, like ARIS's /research-pipeline — an AGENT workflow, NOT a shell binary. Use when the user says "/movie-pipeline '…'", "做个电影/漫画 end-to-end", "from this idea make the whole movie", "long-horizon image-based movie generation".
---

# movie-pipeline — Pipeline A, end-to-end (one slash-command)

The whole of Figure 1 as ONE agent workflow: a fuzzy idea → a cross-model-audited, image-based movie + a
clickable viewer. You invoke it like an ARIS workflow —
`/movie-pipeline "a short film about an autonomous research run"` — and your coding agent (Claude, Codex, …)
drives the chain below, pausing only at the two human story gates.

> **"One command" = one slash-command an agent RUNS — not a deterministic shell binary** (the same paradigm as
> ARIS's `/research-pipeline`). So: it needs a coding-agent runtime; it is non-deterministic (a step may rarely
> not fire — that is **safe**, because each layer consumes the prior *locked* node, so a skipped step leaves the
> next gate's input unresolved and it **fails closed**, never ships something wrong); and it **pauses** at intent
> + outline for your approval. The deterministic, no-agent slice is Phase 2/3
> ([`comic-director`](../comic-director/SKILL.md)'s `run_comic.py`), which also runs standalone in CI.

## The chain (what the one command runs, in order)
1. **Phase 1 — author the source of truth** → [`comic-author`](../comic-author/SKILL.md): intent *(human gate)*
   → style lock → outline *(human gate)* → storyboard → assets (准×3 locked) → blueprints → prompts →
   schema-valid `comic.json`. Each step is its own detailed skill + a cross-model `--gate`.
2. **Zero-credit proof** → `comic-cross-layer-gate <comic> --gate p0_proof`: a text-only cross-model adversarial
   review of the compiled `comic.json` + the machinery. Must be clean BEFORE one metered image credit is spent.
3. **Phase 2/3 — the audited spiral** → [`comic-director`](../comic-director/SKILL.md): per panel, render the
   content-SVG blueprint → `codex image_gen` → 3-reviewer `panel_gate` (blind-transcribe → deterministic
   token-diff) → KEEP / RETRY (≤4) / cross-frame rollback → page `assembly_gate` (≤6) → project to `comic.json`
   → single-file HTML viewer.
4. **Ship** → `examples/<name>/outputs/index.html`. Optionally
   [`comic-blind-comparison-review`](../comic-blind-comparison-review/SKILL.md) double-blind A/Bs it vs a naive
   one-shot baseline to prove the pipeline earned its cost.

## Run it
```text
> /movie-pipeline "«your fuzzy idea»"
```
Your agent authors Phase 1 (stopping for your **intent + outline** approval), clears the `p0_proof` gate, then
bakes the audited spiral and builds the viewer. To run ONLY Phase 2/3 deterministically (CI / no agent runtime),
once `comic.json` exists:
```bash
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <PAGE> --panels S01,S02 --dry-run    # zero credit: prints bake prompts
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <PAGE> --panels S01,S02 --finalize   # bake + rebuild the viewer
```
(`run_comic.py` is a standalone subprocess port of [`packages/core/spiral_engine.js`](../../packages/core/spiral_engine.js);
both refuse to bake without a clean `decision:p0_proof_*` node unless you pass `--skip-p0-proof`, which forces the run non-shippable.)

## The gates that keep it honest (all fail-closed)
- **Two human gates** — intent + outline are story decisions: the agent drafts + cross-model-reviews them but
  NEVER proceeds without your approval (the story-first rule, [`acceptance-gate`](../../protocols/acceptance-gate.md)).
- **p0_proof before any credit** (step 2) — also enforced in the engine (no clean p0_proof node ⇒ refuse).
- **panel_gate** — a baked frame whose number is wrong (`+6.2` expected vs `+6.25` observed) is rejected by a
  deterministic token-diff; **no model self-acquits**; a non-convergent panel is flagged for you, never silently shipped.
- **A skipped step can't leak** — because each layer's input is the prior *locked* node, a missed step is caught
  by the next gate's unresolved input (fail-closed). That is why "the agent might not tool-call a step" is a
  safety property here, not a risk.

## Prereqs
A coding-agent runtime for Phase 1 + the gates; **`codex` + `gemini` CLIs + headless Chrome** for the Phase-2/3
bake (`python3 cli/preflight.py` to verify). Copy the author-node shapes from
[`examples/comic_min_author/`](../../examples/comic_min_author/); the full reference run (198-node trace) is
[`examples/comic_m3_audit/`](../../examples/comic_m3_audit/).

## Protocols
[`acceptance-gate`](../../protocols/acceptance-gate.md) — the human gates intent+outline; a different model family
acquits the rest (loop can DRIVE, can't ACQUIT) · [`artifact-integrity`](../../protocols/artifact-integrity.md) —
the agent that authors a layer never judges its own layer · [`reviewer-independence`](../../protocols/reviewer-independence.md)
· [`external-cadence`](../../protocols/external-cadence.md).
