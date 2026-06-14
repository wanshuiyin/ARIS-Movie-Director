---
name: comic-director
description: Generate a character-consistent, cross-model-audited narrative comic (连环画) from a comic.json — bake each panel, gate it with a 3-model panel, retry/assemble, project to the viewer. The comic-side twin of method-figure.
---

# comic-director

Turn an authored `comic.json` into baked panels + a clickable viewer, through the **audited spiral**: per
panel, render a deterministic content-SVG blueprint → bake a pixel-art panel (`codex image_gen`) → a
3-reviewer cross-model `panel_gate` → keep / retry → page assembly → projection. The comic twin of
`method-figure` (figures); same philosophy, different output.

## Input contract / who decides WHAT, who only renders
This skill is **render + verify**. The contract boundary is **`comic.json`**.
- **Upstream (your agent) owns the semantics** — the story, panels, scenes, dialogue, the per-panel
  `condition` (content_svg + the verbatim `expected_literals`), identity refs. See
  [`references/comic_authoring.md`](references/comic_authoring.md): a fuzzy idea → `comic_brief`
  ([`schemas/comic_brief.schema.json`](schemas/comic_brief.schema.json)) → Step-0 → `comic.json`. You do
  **not** hand-write JSON.
- **comic-director owns** bake → 3-model gate → keep/retry/assembly, and writes back `image_path` /
  `active_attempt_id` / `wiki_node_id` on KEEP. It never invents a number; faithfulness is a deterministic
  token-diff over reviewers who never see the expected values.
- **The generator family (Codex image_gen) can NOT self-acquit.** A KEEP needs the deterministic token-diff
  clean **and** the cross-model visual panel (Gemini + Codex) to pass. The calling agent (Claude) gives the
  final structural sign-off.

Full field spec for `comic.json`: [`docs/comic-json.md`](../../docs/comic-json.md) /
[`schemas/comic.schema.json`](../../schemas/comic.schema.json).

## Two honesty notes (echoed from references/comic_authoring.md)
1. **The blueprint is per-figure and YOU author it** — one deterministic SVG per figure-bearing panel +
   the verbatim `expected_literals`. The ARIS audit story is just the example; swap in your own.
2. **Identity is bring-your-own** — the ARIS chibi duo / `duo_canonical_ref_v001.png` is one example cast.
   Point `condition.identity_ref` at your own sheet, or `null` to use the project canonical. The gate judges
   identity against the ref you supply, per character, cast-aware (absence ≠ drift).

## Run it (one command — `scripts/run_comic.py`)
A standalone, pure-stdlib **faithful port** of `packages/core/spiral_engine.js`'s comic branch — it shells
the `codex` + `gemini` CLIs directly, so it runs WITHOUT the agent/workflow runtime.
```bash
# author comic.json first (Step-0), then:
python3 skills/comic-director/scripts/run_comic.py \
    --project examples/comic_m3_audit --page P02_b08 --panels S12,S13,S14,S15 \
    [--bake-lang zh] [--finalize] [--dry-run] [--skip-assembly]
```
- `--dry-run` validates + prints each panel's concrete bake prompt (no image_gen) — always run this first.
- `--finalize` rebuilds the single-file viewer (`packages/viewer/build_comic.py`) **only if the run is
  shippable** (nothing escalated/throttled/flagged-for-human; assembly accepted).
- Needs the **`codex` and `gemini` CLIs** on PATH (the bake + the cross-model gate) and headless Chrome
  (to rasterize the content-SVG blueprint). Reuses `skills/method-figure/scripts/pickup_image.py`.

It prints a JSON run-report (`kept`, `flagged_for_human`, `needs_human`, `shippable`, `throttled`,
`escalated`, `assembly`, `attempts_per_panel`). For the engine semantics it ports (caps 4/panel + 6/run,
the deterministic verdict, anatomy single-vote veto, throttle → fresh-run) see
[`docs/spiral-runtime.md`](../../docs/spiral-runtime.md).

## Hard do / don't
- **Do** author `comic.json` via Step-0 from a brief; copy `examples/comic_m3_audit/comic.json` as a template.
- **Do** `--dry-run` first and confirm every baked-figure panel carries ascii-tokenizable `expected_literals`
  (else the fail-closed gate refuses to run).
- **Don't** run two bakes at once (codex image_gen writes to a global dir; the `/tmp/aris_imagegen.lock`
  serializes, but only one runner should drive a project at a time).
- **Don't** `resumeFromRunId` after an image_gen throttle — launch a FRESH run for the remaining panels.
- **Don't** treat a `needs_human`/flagged panel as shippable.
