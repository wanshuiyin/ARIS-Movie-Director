---
name: comic-director
description: Phase 2/3 of a movie — bake + cross-model-verify a movie from an authored comic.json. Per frame: render the content-SVG blueprint, bake with codex image_gen, gate with a 3-model panel (CC ‖ Gemini ‖ Codex), keep/retry/assemble, write the wiki trace, project to the viewer. The movie-side twin of method-figure's render half. (Author the comic.json first with the comic-author skill.)
---

# comic-director — the Audited Spiral + Release (Phase 2/3)

The **middle + right of Figure 1**: take an authored `comic.json` (produced by the
[`comic-author`](../comic-author/SKILL.md) skill, Phase 1) and turn it into baked frames + a clickable
viewer, through the audited spiral. Per frame: render a deterministic content-SVG blueprint → bake a
pixel-art frame (`codex image_gen`) → a 3-reviewer cross-model `panel_gate` → keep / retry → page assembly →
projection. The movie twin of `method-figure`'s render half. (Image-based today; video-based is next.)

## Input contract — `comic.json` (authored upstream)
The contract boundary is **`comic.json` + the assets it references** (content-SVG blueprints, identity refs,
`ART_BIBLE.md`) — authored by [`comic-author`](../comic-author/SKILL.md). This skill is **render + verify**:
- It **never invents** a number or a cast — faithfulness is a deterministic token-diff over reviewers who
  never see the expected values; identity is judged against the ref the author supplied (cast-aware).
- It writes back **only** `image_path` / `active_attempt_id` / `wiki_node_id` (+ the wiki trace) on KEEP.
- **The generator family (Codex image_gen) can NOT self-acquit.** A KEEP needs the token-diff clean **and**
  the cross-model visual panel (Gemini + Codex) to pass. The calling agent (Claude) gives the final
  structural sign-off.

Full IR spec: [`../../docs/comic-json.md`](../../docs/comic-json.md) /
[`../../schemas/comic.schema.json`](../../schemas/comic.schema.json).

## Run it (one command — `scripts/run_comic.py`)
A standalone, pure-stdlib **faithful port** of `packages/core/spiral_engine.js`'s movie branch — it shells
the `codex` + `gemini` CLIs directly, so it runs WITHOUT the agent/workflow runtime.
```bash
python3 skills/comic-director/scripts/run_comic.py \
    --project examples/comic_m3_audit --page P02_b08 --panels S12,S13,S14,S15 \
    [--bake-lang zh] [--finalize] [--dry-run] [--skip-assembly]
```
- `--dry-run` validates + prints each frame's concrete bake prompt (no image_gen) — **run this first**; it's
  also how `comic-author` confirms Phase 1 is correct.
- `--finalize` rebuilds the single-file viewer (`packages/viewer/build_comic.py`) **only if the run is
  shippable** (nothing escalated/throttled/flagged-for-human; assembly accepted).
- Needs the **`codex` and `gemini` CLIs** on PATH + headless Chrome (to rasterize the content-SVG blueprint).
  Reuses `skills/method-figure/scripts/pickup_image.py`.

It prints a JSON run-report (`kept`, `flagged_for_human`, `needs_human`, `shippable`, `throttled`,
`escalated`, `assembly`, `attempts_per_panel`). Engine semantics it ports (caps 4/panel + 6/run, the
deterministic verdict, anatomy single-vote veto, throttle → fresh-run): [`../../docs/spiral-runtime.md`](../../docs/spiral-runtime.md).

## Hard do / don't
- **Do** author `comic.json` first with [`comic-author`](../comic-author/SKILL.md); copy
  `examples/comic_m3_audit/comic.json` as the shape.
- **Do** `--dry-run` first; confirm every baked figure-panel carries ascii-tokenizable `expected_literals`
  (else the fail-closed gate refuses to run).
- **Don't** run two bakes at once (codex image_gen writes to a global dir; `/tmp/aris_imagegen.lock`
  serializes, but one runner per project).
- **Don't** resume after an image_gen throttle — launch a FRESH run for the remaining panels.
- **Don't** treat a `needs_human`/flagged panel as shippable.

## Protocols (governance contracts this skill honors)
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — reviewers get file paths only; the executor (Codex image_gen) ≠ the visual judges (Gemini + Codex vision).
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — the loop can DRIVE but can't ACQUIT: a KEEP needs the deterministic token-diff clean **and** Gemini+Codex visual pass; the generator family never self-acquits; Claude gives the final structural sign-off.
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — the model that bakes a frame does not judge its own faithfulness; numbers are *verified*, never originated.
- [`review-tracing`](../../protocols/review-tracing.md) — every reviewer's prompt+response is saved (`trace.jsonl`) so each verdict is auditable.
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Codex `gpt-5.5` `xhigh`; Gemini `auto-gemini-3`; never downgrade the reviewer tier.
