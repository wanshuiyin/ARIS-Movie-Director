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

## The pipeline (run in order) — the N1 two-stage DAG (each step = a detailed skill + its gate)
Dependencies are the node_schema `source_*` fields, not invented — each step consumes the prior locked node.
The two-stage shape is the deadlock fix: the outline gate demands every referenced `asset_id` be **DECLARED
with a complete, generatable request** (never `locked` — assets don't exist yet on a fresh project); the
storyboard runs a **provisional structural pass** first; the ONE hard locked-asset barrier sits before
blueprint authoring (step 7), reached via two cheap gate re-passes (6a/6b).

| # | Step → skill | Produces | Gate (via [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md)) |
|---|---|---|---|
| 1 | [`comic-intent-parser`](../comic-intent-parser/SKILL.md) | `intent_spec` | **USER approves** → `--gate intent` |
| 2 | [`comic-style-bible-lock`](../comic-style-bible-lock/SKILL.md) | `style_anchor`×N + `ART_BIBLE.md` | style lock (design-aware) |
| 3 | [`comic-outline-creator`](../comic-outline-creator/SKILL.md) | `outline_spec` (3-lens → synth) | **OUTLINE_DRAFT_VALID** (`--gate outline`: narrative+continuity+safety; asset_ids DECLARED, **not** locked) → **USER approves** → locked |
| 4 | [`comic-storyboard-creator`](../comic-storyboard-creator/SKILL.md) | PROVISIONAL `storyboard_spec` + `panel_spec`×N + `motif_ledger` + consolidated `asset_requests` | `--gate storyboard` **structural pass** (may reference draft assets) |
| 5 | [`comic-asset-ref-generator`](../comic-asset-ref-generator/SKILL.md) | `asset`×N (single-source, from the requests) | — |
| 6 | [`comic-asset-review-loop`](../comic-asset-review-loop/SKILL.md) | each `asset` → `status: locked` (准×3) | `--gate asset` · **assets LOCKED** |
| 6a | **OUTLINE_FINAL_LOCK** (gate re-pass, no new skill) | outline re-check `decision` node | cheap re-check: the locked assets still match the approved outline (`identity/scene_lock_feasibility` scored HERE) |
| 6b | storyboard **FINAL validation** (gate re-pass) | `storyboard_spec` → `locked` | re-run `--gate storyboard`: `panel_assets_referenceable` (resolves AND locked) now satisfiable · **ASSET-LOCK BARRIER ↓** |
| 7 | [`comic-blueprint-author`](../comic-blueprint-author/SKILL.md) | `blueprint`×N (content-SVG, no baked bubbles) | `--gate blueprint` (the locked-asset HARD barrier lives here) |
| 8 | [`comic-panel-prompt-builder`](../comic-panel-prompt-builder/SKILL.md) | `prompt_bundle`×N (搬运工原則) | build asserts: literal / zero-text / ref-count |
| 9 | [`comic-json-compiler`](../comic-json-compiler/SKILL.md) | `comic.json` (authored fields only) | `--gate compile` (`run_comic --dry-run` + `validate_wiki`) |

Entry/exit contract per step (what each consumes → hands off):

| # | Entry | Exit |
|---|---|---|
| 1 | the user's fuzzy idea | locked `intent_spec` |
| 2 | `intent_spec` | locked `ART_BIBLE.md` + `style_anchor`×N |
| 3 | `intent_spec` (+ its skeleton) | locked, user-approved `outline_spec` (motif arcs + declared asset_ids) |
| 4 | locked `outline_spec` | provisional `storyboard_spec` / `panel_spec`×N / `motif_ledger` + consolidated `asset_requests` |
| 5 | consolidated `asset_requests` + `ART_BIBLE.md` | draft `asset`×N (files + nodes) |
| 6 | draft `asset`×N | locked `asset`×N |
| 6a/6b | approved outline + provisional storyboard + locked assets | outline re-check `decision` node → locked `storyboard_spec` |
| 7 | `panel_spec.content_blueprint` + locked assets | locked `blueprint`×N |
| 8 | blueprints + panel_specs + `ART_BIBLE.md` | `prompt_bundle`×N |
| 9 | every locked layer | `comic.json` + compile `decision` node |

Two services woven across the pipeline (not sequential steps):
- [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) — the ONE score-fuser every `--gate <kind>`
  above calls. **Never invoked cold:** each step first fans out its cross-model reviewers (writes `review:*`
  nodes + `reviews` edges), THEN calls the gate to fuse + flip `status` (`locked` on advance, `rejected` on a
  terminal fail; `revise`/`regenerate`/`fallback` are verdicts, never statuses). Reviewer routing: the Codex CLI at
  `xhigh` (it pins NO model — it follows the local codex config, currently `gpt-5.6-sol`) ‖ (Gemini
  `auto-gemini-3` when available) — a different model family from this Claude author, paths only.
- [`comic-continuity-audit`](../comic-continuity-audit/SKILL.md) — authors the `motif_ledger` invariants in
  step 4 and runs as `--gate continuity` against that ledger (and at bake time inside the engine): DDL
  monotonic-down, bounce-single-max, metric-columns-disjoint, design-aware (`absence ≠ drift`).

## The barriers (fail-closed — do not cross early)
1. **Story approval** — do NOT author the outline before the user approves the intent; do NOT author the
   storyboard before the user approves the outline.
2. **ASSET-LOCK BARRIER (before step 7, blueprint authoring)** — **every** `asset` a panel references must be
   `status: locked` before any blueprint is authored; a blueprint/panel referencing a draft asset is a hard
   veto. This is the ONE place the locked-asset demand lands (why the single-source asset library + 准×3
   finish before any per-panel blueprint). Steps 6a/6b are its approach ramp: OUTLINE_FINAL_LOCK re-checks the
   approved outline against the now-locked assets, then the FINAL `--gate storyboard` re-run satisfies
   `panel_assets_referenceable` and flips the storyboard `locked`.
3. **ZERO-CREDIT P0 SPENDING GATE (after step 9, before ANY bake)** — the `--gate p0_proof` procedure: the
   agent fans out ≥2 cross-model reviewers over the compiled `comic.json` + the pipeline machinery, each
   writing a review JSON (`{family, verdict, blockers[], comic_sha}`); the deterministic MINTER
   [`comic-cross-layer-gate/scripts/run_p0_proof.py`](../comic-cross-layer-gate/scripts/run_p0_proof.py) then
   verifies FAIL-CLOSED that BOTH non-author families `{openai, google}` PASS with `blockers == []` on the SAME
   `comic.json` digest (parseable ≠ quorum; a missing/unparseable/timed-out review never counts) and atomically
   mints `decision:p0_proof_*` (verdict `advance`, digest-bound `comic_sha` + `bake_plan_sha`). `run_comic.py`'s
   `_p0_clean` REJECTS a cert with missing/stale digests — a post-mint `comic.json` edit fail-closes the bake.

## Hand-off to Phase 2/3
When `comic.json` validates, `--gate compile` passes, and the digest-bound `decision:p0_proof_*` cert is
minted, Phase 1 is done. Then [`comic-director`](../comic-director/SKILL.md) bakes + verifies:
```bash
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <P> --panels S01,S02 --dry-run
```
`--dry-run` first (it prints concrete bake prompts + literals, spends nothing — also how this skill confirms
Phase 1 is correct). The REAL bake is **not** "just drop `--dry-run`": it runs `--bake-mode=agent` (the
default) and needs a running agent wrapper servicing the `mcp__codex__codex` sidecar (`.bakereq`/`.bakestatus`
+ pickup) — see comic-director's "Who runs `--bake-mode=agent`"; the exec path RAISES (retired). Honest model
split: the BAKE pins `gpt-5.5` + `xhigh` as the single compat default in `run_comic.get_bake_plan()` (the p0
cert digests it; a config-driven override is PLANNED, not yet implemented); the Codex CLI *reviewers* pin NO
model (local codex config, currently `gpt-5.6-sol`) at `xhigh`. After ship, optionally
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
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Codex reviewers at `xhigh`, NO model pin (local
  codex config, currently `gpt-5.6-sol`); Gemini `auto-gemini-3` when available; never downgrade the effort tier.
- [`review-tracing`](../../protocols/review-tracing.md) · [`output-versioning`](../../protocols/output-versioning.md)
  · [`resumable-runs`](../../protocols/resumable-runs.md) · [`external-cadence`](../../protocols/external-cadence.md)
  — trace every gate; version asset refs (`_v{NNN}` + `supersedes`); the orchestrator is resumable + its
  scheduled runs are fenced.
