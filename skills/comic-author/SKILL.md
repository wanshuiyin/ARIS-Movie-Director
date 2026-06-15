---
name: comic-author
description: Phase 1 ORCHESTRATOR of a movie/comic — turn a fuzzy story idea into the Authored Source of Truth (a schema-valid comic.json + its locked asset library) by driving the detailed author skills in order (intent → style → outline → storyboard → assets → blueprints → prompts → comic.json), each gated by comic-cross-layer-gate, so comic-director (Phase 2/3) can bake + cross-model-verify it. You don't hand-write comic.json; this is the workflow your agent runs to author it. Use when the user says "做个漫画/电影", "from this idea make a comic", "author the comic.json", "run the comic pipeline".
---

# comic-author — the Pipeline-A Orchestrator (Phase 1)

The **left third of Figure 1**, as an **agent-run workflow**: a fuzzy idea → a `comic.json` + its locked asset
library, so [`comic-director`](../comic-director/SKILL.md) (Phase 2/3) bakes + adversarially verifies it. This
skill is **thin** — it owns the ORDER, the BARRIERS, and the HAND-OFF; each step's real procedure lives in its
own detailed skill.

> **End-to-end in one slash-command?** [`movie-pipeline`](../movie-pipeline/SKILL.md) is the single entry that
> drives THIS skill (Phase 1) → the `p0_proof` gate → `comic-director` (Phase 2/3 bake) → viewer. comic-author is
> the Phase-1 half it calls; use it directly when you only want to author + lock the `comic.json`. The contract boundary to Phase 2/3 is **`comic.json` + the assets it references**
(content-SVG blueprints, identity refs, `ART_BIBLE.md`).

> **How you "run" this — it is an AGENT workflow, not a shell CLI.** You point your coding agent (Claude,
> Codex, …) at this skill; the agent FOLLOWS the steps below — authoring the wiki nodes and calling the few
> deterministic helper scripts that ARE real CLIs: [`comic-director/scripts/run_comic.py`](../comic-director/scripts/run_comic.py),
> [`cli/validate_wiki.py`](../../cli/validate_wiki.py), [`comic-panel-prompt-builder/scripts/build_prompt.py`](../comic-panel-prompt-builder/scripts/build_prompt.py).
> The **`--gate <kind>`** notations below are the **agent PROCEDURE** in
> [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) (fan out the cross-model reviewers → fuse → flip
> `status`) — **not** a binary you `exec`. This mirrors every ARIS skill: the SOP is the product, a coding agent is the runtime.

> **Two hard human gates (never auto-proceed):** the **intent** and the **outline** are story decisions — the
> user must approve each before the next layer starts (the story-first rule; the gate is
> [`acceptance-gate`](../../protocols/acceptance-gate.md)). Everything downstream is agent-driven + cross-model gated.

## The pipeline (run in order; each step = a detailed skill + its gate)
Dependencies are the node_schema `source_*` fields, not invented — each step consumes the prior locked node.

| # | Step → skill | Produces (locked node) | Gate (via [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md)) |
|---|---|---|---|
| 1 | [`comic-intent-parser`](../comic-intent-parser/SKILL.md) | `intent_spec` | **USER approves** → `--gate intent` |
| 2 | [`comic-style-bible-lock`](../comic-style-bible-lock/SKILL.md) | `style_anchor`×N + `ART_BIBLE.md` | style lock (design-aware) |
| 3 | [`comic-outline-creator`](../comic-outline-creator/SKILL.md) | `outline_spec` (3-lens → synth) | **USER approves** → `--gate outline` |
| 4 | [`comic-storyboard-creator`](../comic-storyboard-creator/SKILL.md) | `storyboard_spec` + `panel_spec`×N + `motif_ledger` + consolidated `asset_requests` | `--gate storyboard` |
| 5 | [`comic-asset-ref-generator`](../comic-asset-ref-generator/SKILL.md) | `asset`×N (single-source, from the requests) | — |
| 6 | [`comic-asset-review-loop`](../comic-asset-review-loop/SKILL.md) | each `asset` → `status: locked` (准×3) | `--gate asset` · **ASSET-LOCK BARRIER ↓** |
| 7 | [`comic-blueprint-author`](../comic-blueprint-author/SKILL.md) | `blueprint`×N (content-SVG, no baked bubbles) | `--gate blueprint` |
| 8 | [`comic-panel-prompt-builder`](../comic-panel-prompt-builder/SKILL.md) | `prompt_bundle`×N (搬运工原則) | build asserts: literal / zero-text / ref-count |
| 9 | [`comic-json-compiler`](../comic-json-compiler/SKILL.md) | `comic.json` (authored fields only) | `--gate compile` (`run_comic --dry-run` + `validate_wiki`) |

Two services woven across the pipeline (not sequential steps):
- [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) — the ONE score-fuser every `--gate <kind>`
  above calls. **Never invoked cold:** each step first fans out its cross-model reviewers (writes `review:*`
  nodes + `reviews` edges), THEN calls the gate to fuse + flip `status` (`locked` on advance, `rejected` on a
  terminal fail; `revise`/`regenerate`/`fallback` are verdicts, never statuses). Reviewer routing: Codex
  `gpt-5.5 xhigh` ‖ (Gemini `auto-gemini-3` when available) — a different model family from this Claude author,
  paths only.
- [`comic-continuity-audit`](../comic-continuity-audit/SKILL.md) — authors the `motif_ledger` invariants in
  step 4 and runs as `--gate continuity` against that ledger (and at bake time inside the engine): DDL
  monotonic-down, bounce-single-max, metric-columns-disjoint, design-aware (`absence ≠ drift`).

## The barriers (fail-closed — do not cross early)
1. **Story approval** — do NOT author the outline before the user approves the intent; do NOT author the
   storyboard before the user approves the outline.
2. **ASSET-LOCK BARRIER (after step 6)** — **every** `asset` a panel references must be `status: locked`
   before blueprint authoring (step 7) starts. A blueprint/panel referencing a draft asset is a hard veto. (This
   is why the single-source asset library + 准×3 finish before any per-panel blueprint.) **Ordering note for the
   storyboard gate:** step 4 produces the `storyboard_spec` + the consolidated `asset_requests`, but
   `--gate storyboard`'s `panel_assets_referenceable` dim (assets resolve AND are `locked`) is only satisfiable
   AFTER this barrier — so run the storyboard's STRUCTURAL pass at step 4, then its asset-resolution pass + the
   final `locked` flip once steps 5–6 have locked every requested asset (re-run `--gate storyboard` then).
3. **ZERO-CREDIT P0 GATE (after step 9, before ANY bake)** — run
   `comic-cross-layer-gate <comic_id> --gate p0_proof`: a text-only cross-model adversarial review of the
   compiled `comic.json` + the pipeline machinery. It must clear `blockers.length == 0` BEFORE a single metered
   `codex image_gen` credit is spent in Phase 2/3.

## Hand-off to Phase 2/3
When `comic.json` validates, `--gate compile` passes, and `--gate p0_proof` is clean, Phase 1 is done. Then
[`comic-director`](../comic-director/SKILL.md) bakes + verifies:
```bash
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <P> --panels S01,S02 --dry-run
```
`--dry-run` first (it prints concrete bake prompts + literals, no image_gen — also how this skill confirms
Phase 1 is correct); then drop `--dry-run` to bake the audited spiral. After ship, optionally
[`comic-blind-comparison-review`](../comic-blind-comparison-review/SKILL.md) runs a double-blind A/B vs a naive
one-shot baseline to prove the pipeline earned its cost.

## Two engine contracts to author to (fail-closed)
1. **Every panel needs a `condition.content_svg`** (a deterministic blueprint SVG — figure or scene-anchor
   layout). `condition.content_svg: null` is rejected by the engine.
2. **A `text_mode:"baked"` figure-panel must declare `condition.expected_literals`** (exact numbers/keys,
   verbatim, ascii-tokenizable) — or the run is refused. A scene panel with no audited numbers → `text_mode:"html"`.

## Worked examples (the copy targets)
- **The author-node fixture — [`examples/comic_min_author/`](../../examples/comic_min_author/)**: ONE valid node
  of **each of the 10 author types** (intent_spec → … → blueprint + prompt_bundle + motif_ledger +
  continuity_constraint) + the author-layer `wiki/edges.jsonl` + a real `content_svg` / identity `.png` /
  `ART_BIBLE.md` with `STYLE_PREFIX`. **This is what you copy when authoring** — `python3 cli/validate_wiki.py
  examples/comic_min_author` PASSES and `build_prompt.py … panel:demo_s01` RUNS against it.
- **The full reference run — [`examples/comic_m3_audit/`](../../examples/comic_m3_audit/)** is the real authored
  source of truth this pipeline produced: `story/OUTLINE_DRAFT.md` (3-lens → codex synth → user-approved) ·
  `story/STORYBOARD_DRAFT.md` (page order + the MOTIF STATE TABLE) · `ART_BIBLE.md` · `gen/` (the asset +
  blueprint generator scripts) · `comic.json` · `wiki/` (the full *runtime* node/edge trace). The detailed layer→skill index is
[`references/authored_source_of_truth.md`](references/authored_source_of_truth.md); field mapping is
[`references/comic_authoring.md`](references/comic_authoring.md). Your authoring agent can be any coding agent
(e.g. the [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) main project) — this skill is
self-contained and does not depend on it at runtime.

## Protocols (governance contracts this orchestrator honors)
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — each layer's gate can DRIVE but can't ACQUIT; the
  user is the hard gate for intent + outline; a different model family (the gate's Codex adjudicator) acquits the rest.
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — the agent that authors a layer never judges its
  own layer's correctness; the cross-layer gate (a different family) does.
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — every gate's reviewer gets file paths +
  an `=== EXTERNAL CONTEXT (advisory) ===` fence, never the author's interpretation.
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Codex `gpt-5.5` `xhigh`; Gemini `auto-gemini-3`
  when available; never downgrade the tier.
- [`review-tracing`](../../protocols/review-tracing.md) · [`output-versioning`](../../protocols/output-versioning.md)
  · [`resumable-runs`](../../protocols/resumable-runs.md) · [`external-cadence`](../../protocols/external-cadence.md)
  — trace every gate; version asset refs (`_v{NNN}` + `supersedes`); the orchestrator is resumable + its
  scheduled runs are fenced.
