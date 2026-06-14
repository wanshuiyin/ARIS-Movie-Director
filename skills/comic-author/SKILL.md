---
name: comic-author
description: Phase 1 of a movie — turn a fuzzy story idea into the Authored Source of Truth (asset library + outline + storyboard → a schema-valid comic.json), so the comic-director skill can bake + cross-model-verify it. You don't hand-write comic.json; this skill is the procedure your agent follows to author it.
---

# comic-author — the Authored Source of Truth (Phase 1)

The **left third of Figure 1**: turn a fuzzy idea into a `comic.json` + its asset library, so
[`comic-director`](../comic-director/SKILL.md) (Phase 2/3) can bake + adversarially verify it. The contract
boundary between the two skills is **`comic.json` + the assets it references** (content-SVG blueprints,
identity refs, `ART_BIBLE.md`).

## The procedure (followable, not hand-wavy)
Run the 5-layer SOP — **[`references/authored_source_of_truth.md`](references/authored_source_of_truth.md)**:
0. **Intent** — idea → locked premise + cast + one identity ref per character + worlds + primary `bake_lang`.
1. **Outline** — beats, one per page (cover / single / grid / grid2x2 / feature / finale).
2. **Storyboard** — full per-panel spec **incl. layout** (`text_mode`, `bubbles{zh,en}`, `caption`, `crop`,
   `safe_zones`, cover/finale page fields) + the per-panel blueprint plan; surfaces the consolidated asset_requests.
3. **Asset Library** — build single-source assets + every panel's `content_svg` **by writing a Python
   generator script** (mirror `examples/comic_m3_audit/gen/asset_lib.py` + `gen_*_blueprints.py`), finalize
   `ART_BIBLE.md`. **Mandatory gate:** the single-source collision check (`check_asset_collisions.py`).
4. **Compile → `comic.json`** — assemble + validate; author only authored fields (leave `image_path` etc.
   for Phase 2/3).

Field mapping: [`references/comic_authoring.md`](references/comic_authoring.md). The semantic hand-off schema:
[`schemas/comic_brief.schema.json`](schemas/comic_brief.schema.json). Target IR:
[`../../docs/comic-json.md`](../../docs/comic-json.md) / [`../../schemas/comic.schema.json`](../../schemas/comic.schema.json).

## Two engine contracts to author to (fail-closed)
1. **Every panel needs a `condition.content_svg`** (a deterministic blueprint — figure or layout). Do NOT
   use `content_svg: null`; the engine rejects it.
2. **A `baked` figure-panel must declare `condition.expected_literals`** (exact numbers/keys, verbatim) — or
   the run is refused. A scene panel with no audited numbers → `text_mode: "html"`.

## Two honesty notes
1. **The blueprint is per-figure and YOU author it** — one deterministic SVG (via a generator script) per
   panel + the verbatim `expected_literals`. The ARIS audit story is just the example; swap in your own.
2. **Identity is bring-your-own** — the ARIS chibi duo is one example cast. Each character gets its own
   locked `.png`; point `condition.identity_ref` at yours (or `null` → the project canonical).

## Hand-off
When `comic.json` validates and `comic-director`'s `--dry-run` prints concrete bake prompts (real scenes +
literals, no placeholders) with the fail-closed gate passing, Phase 1 is done. Then:
```bash
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <P> --panels S01,S02 --dry-run
```
Your authoring agent can be any coding agent — e.g. the
[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) main project — but this skill is
self-contained and does not depend on it at runtime.

## Protocols (governance contracts this skill honors)
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — every cross-layer gate's reviewer (Codex/Gemini) gets file paths + an `=== EXTERNAL CONTEXT (advisory) ===` fence, never the author's interpretation.
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — each layer's gate can drive but can't acquit; user approval is the hard gate for intent/outline (never proceed without it).
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — the agent that authors a layer doesn't judge its own layer's correctness; that's the cross-layer gate (a different model family).
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Codex `gpt-5.5` `xhigh`; Gemini `auto-gemini-3`; never downgrade.
- [`review-tracing`](../../protocols/review-tracing.md) · [`output-versioning`](../../protocols/output-versioning.md) · [`resumable-runs`](../../protocols/resumable-runs.md) · [`external-cadence`](../../protocols/external-cadence.md) — trace every gate; version asset refs (`_v{NNN}` + `supersedes`); the orchestrator is resumable + its scheduled runs are fenced.
