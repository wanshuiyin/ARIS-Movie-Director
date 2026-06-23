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

## Run it (`scripts/run_comic.py` — agent-driven bake, CLI gates)
A pure-stdlib **faithful port** of `packages/core/spiral_engine.js`'s movie branch. The cross-model **gates**
(Gemini + Codex vision) still shell the `gemini` / `codex` CLIs directly. The **BAKE** is performed by the
skill **agent** via the **`mcp__codex__codex`** MCP tool through `--bake-mode=agent` (the default): the core
emits a deterministic bake-request sidecar (prompt + absolute ref paths + exact out_path), the agent calls
`mcp__codex__codex` (`sandbox: workspace-write`, `model: gpt-5.5`, `config: {model_reasoning_effort: xhigh, include_image_gen_tool: true}`,
`cwd: <project>`), and the core verifies the explicit out_path. (`codex exec` is RETIRED for real bakes — it
forced a hand-drawn SVG/struct+zlib fallback; `--bake-mode=exec` RAISES if it ever reaches a real bake. See
`docs/spiral-runtime.md`.)
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

## Bake seam contract (agent ↔ core) — `--bake-mode=agent`
The bake is a **synchronous sidecar handshake** (contract-v2 §1–§4). The core never returns/exits early on a
bake; only the bake **primitive** moved off `codex exec` onto `mcp__codex__codex`:
- **(A) core writes** `<out>.bakereq.json` =
  `{prompt_text, content_png, identity_ref, out_path, model:"gpt-5.5", config:{model_reasoning_effort:"xhigh", include_image_gen_tool:true}, sandbox:"workspace-write", cwd, created_at, min_bytes:500000, aspect, request_id:"<uuid4 hex>"}`
  (`prompt_text` ALREADY contains the absolute ref + out paths — the schema has **no** `-i`; `config` carries
  **both** `model_reasoning_effort:"xhigh"` AND `include_image_gen_tool:true` — without the latter codex won't fire
  its native image tool; `request_id` is a per-bake uuid4-hex nonce the core mints — see (D)+(E)), pre-deleting any
  stale `out_path` + status.
- **(B) the agent calls** `mcp__codex__codex` with EXACTLY those params.
- **(C) codex writes** a native PNG to `out_path`.
- **(D) the agent writes** `<out>.bakestatus.json` =
  `{status:"ok"|"fail", failure_kind:"throttle"|"other", mcp_output:"<bounded raw codex tool output>", mcp_error, request_id:"<verbatim from bakereq>"}`.
  **`mcp_output` is MANDATORY on BOTH ok and fail** — the core feeds this status file to `pickup --transcript`,
  and the HARD-VETO scans it for `import struct`/`zlib.compress`/`<svg>`/`matplotlib`/… markers. **An `ok`
  status with no raw output makes the HARD-VETO inert** (a hand-drawn struct+zlib/SVG that still emits a
  ≥500KB sig-valid PNG would slip through) — so always embed the bounded raw tool result.
  **`request_id` is EQUALLY MANDATORY on BOTH ok and fail** — copy it VERBATIM from `<out>.bakereq.json` into
  the bakestatus; `pickup_image.py --out-existing --request-id` **fail-closes the bake** if the status
  `request_id` is missing or ≠ the bakereq nonce (a stale/foreign status at the same path can't be silently honored).
- **(E) the core verifies** via `pickup_image.py --out-existing` on the EXPLICIT `out_path` (PNG sig + IHDR dims
  + size > 500000 + aspect band + `mtime >= created_at`), **HARD-VETOES** the markers in the transcript
  (= the status file's `mcp_output`), and (via `--request-id`) **fail-closes** if the status file's `request_id`
  is absent or ≠ the bakereq nonce — but all ONLY after it has read `status:"ok"`. Empty/timeout/any-non-ok =
  fail-closed (no pickup). NO fallback to `codex exec`/PIL/SVG; effort is ALWAYS `xhigh`; sandbox ALWAYS
  `workspace-write`.

### Who runs `--bake-mode=agent` (the agent-wrapper SOP) — REQUIRED for the default mode to function
The comic-director **skill agent** is the bake fulfiller. Concretely:
1. Launch the orchestrator in the **BACKGROUND**:
   `python3 skills/comic-director/scripts/run_comic.py --project … --page … --panels … --bake-mode agent`
   (it blocks on each bake by polling `<out>.bakestatus.json`).
2. **Loop** until the orchestrator prints its final run-report JSON / exits:
   - watch the project's `panels/` dir for a new `*.bakereq.json`;
   - read it; call `mcp__codex__codex` with **exactly** its
     `{prompt: <prompt_text>, model:"gpt-5.5", config:{include_image_gen_tool:true, model_reasoning_effort:"xhigh"}, sandbox:"workspace-write", cwd:<cwd>}`
     (codex writes the native PNG to the sidecar's `out_path`). The `config` MUST carry **both**
     `include_image_gen_tool:true` AND `model_reasoning_effort:"xhigh"`: without `include_image_gen_tool` Codex will
     **not** fire its native image tool (it falls back to descriptive text / an SVG renderer), and `xhigh` is the
     required reasoning tier;
   - then read `request_id` from `<out>.bakereq.json` and write `<out>.bakestatus.json` carrying **the status, a
     bounded raw `mcp_output`, AND that `request_id` VERBATIM** — `mcp_output` so the core's HARD-VETO can scan it,
     and `request_id` because `pickup_image.py --out-existing --request-id` **fail-closes the bake if the status
     `request_id` is missing or mismatched** (it must be written on BOTH ok and fail):
     `{"status":"ok","mcp_output":"<raw>","request_id":"<verbatim from bakereq>"}` on success, or
     `{"status":"fail","failure_kind":"throttle","mcp_output":"<raw>","request_id":"<verbatim from bakereq>"}` on a
     429 / `MODEL_CAPACITY_EXHAUSTED` / overloaded error (otherwise
     `{"status":"fail","failure_kind":"other","mcp_output":"<raw>","mcp_error":"<raw>","request_id":"<verbatim from bakereq>"}`).
3. Stop when the orchestrator exits. (Without this wrapper, every bake polls to `--bake-timeout` and returns
   `generation_failed` with `failure_kind="other"` — fail-closed, not a hang, and never a false `throttle`.)
> `--bake-mode=exec` is the legacy/CI **non-image** path and RAISES if it ever reaches a real bake — never use
> it to produce a panel.

## Hard do / don't
- **Do** author `comic.json` first with [`comic-author`](../comic-author/SKILL.md); copy
  `examples/comic_m3_audit/comic.json` as the shape.
- **Do** `--dry-run` first; confirm every baked figure-panel carries ascii-tokenizable `expected_literals`
  (else the fail-closed gate refuses to run).
- **Don't** run two bakes at once. The default `--bake-mode=agent` writes each native PNG to its **explicit
  per-panel `out_path`** and has **no `/tmp/aris_imagegen.lock`** (that code lock is GONE in agent mode — the
  agent wrapper itself serializes the `mcp__codex__codex` calls). The real race surface: concurrent runs on the
  **same project/page** collide on the per-panel `.bakereq.json`/`.bakestatus.json` sidecars + the shared
  `out_path` — so keep **ONE runner per project/page**. (The global generated-images dir that could
  cross-pollinate concurrent bakes is a hazard of the **LEGACY `--bake-mode=exec` path ONLY**, retired for real
  bakes.)
- **Don't** resume after an image_gen throttle — launch a FRESH run for the remaining panels.
- **Don't** treat a `needs_human`/flagged panel as shippable.

## Protocols (governance contracts this skill honors)
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — reviewers get file paths only; the executor (Codex image_gen) ≠ the visual judges (Gemini + Codex vision).
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — the loop can DRIVE but can't ACQUIT: a KEEP needs the deterministic token-diff clean **and** Gemini+Codex visual pass; the generator family never self-acquits; Claude gives the final structural sign-off.
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — the model that bakes a frame does not judge its own faithfulness; numbers are *verified*, never originated.
- [`review-tracing`](../../protocols/review-tracing.md) — every reviewer's prompt+response is saved (`trace.jsonl`) so each verdict is auditable.
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Codex `gpt-5.5` `xhigh`; Gemini `auto-gemini-3`; never downgrade the reviewer tier.
