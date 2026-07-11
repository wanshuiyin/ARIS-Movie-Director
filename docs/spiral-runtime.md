# Spiral Runtime — how to launch comic generation

The **working entry point is the Python orchestrator**, not the JS engine:

```bash
python3 skills/comic-director/scripts/run_comic.py \
    --project /ABS/PATH/TO/examples/mycomic \
    --page P02_b08 --panels S12,S13,S14,S15 \
    [--finalize]        # build the viewer after a shippable run (exits 4 if the viewer build fails)
```

`--bake-mode=agent` is the default and the **only real bake path**: per panel the core renders the
`condition.content_svg` blueprint to PNG (headless Chrome, found via `$ARIS_CHROME` → the macOS app path →
`PATH`), emits `<out>.bakereq.json`, and polls `<out>.bakestatus.json`. A coding agent **must service that
sidecar** — the wrapper SOP is [`skills/comic-director/SKILL.md`](../skills/comic-director/SKILL.md) §"Who
runs `--bake-mode=agent`": watch for `*.bakereq.json`, call `mcp__codex__codex` with the request's
model/config/sandbox verbatim, write back `*.bakestatus.json`. Without a running wrapper every bake times
out fail-closed (`generation_failed` — no wrapper, no image). The bake is verified at the explicit
`out_path` (`pickup_image.py --out-existing` + the `request_id` nonce + the HARD-VETO transcript scan),
then gated: 3 reviewer slots (narrative — currently the codex CLI, recorded as family `openai` ‖ Gemini
visual ‖ Codex visual) → the deterministic `panel_verdict` → wiki nodes → keep / retry (≤4/panel) → page
`assembly_gate` → project the kept panels into `comic.json`. Then build the viewer:
`python3 packages/viewer/build_comic.py examples/mycomic`.

## P0 spending prerequisite (fail-closed)

`run_comic.py` refuses to spend any image credit without a **clean, digest-bound `decision:p0_proof_*`
node** in the project wiki. That certificate is minted only by
[`skills/comic-cross-layer-gate/scripts/run_p0_proof.py`](../skills/comic-cross-layer-gate/scripts/run_p0_proof.py),
which fail-closes unless **both** non-author families (`{openai, google}`) passed the **same**
`comic.json` digest — a review being merely parseable is not quorum, and a missing / unparseable / timeout
review simply does not count (never proceed on timeout). The cert binds `comic_sha` (sha256 of the exact
`comic.json` bytes) **and** `bake_plan_sha` (`pickup_image.bake_plan_digest(run_comic.get_bake_plan())`,
the resolved spend plan). Edit `comic.json` — or change the bake plan — after minting and the stale cert is
**rejected** at preflight with a pointer back to `run_p0_proof.py`. `--skip-p0-proof` bakes UNAUDITED and
forces the run non-shippable.

## The JS engine — canonical spec mirror; cannot bake standalone

`packages/core/spiral_engine.js` is the **canonical state-machine / gate + wiki spec** that
`run_comic.py` ports line-for-line — it is *not* a working bake driver. Its in-engine `codex image_gen`
path is **retired** (`generatePanel` HARD-FAILS with `exec-bake-retired`) and it never emits a
`.bakereq.json`, so a Workflow-runtime launch of the JS engine bakes nothing. Use it as the contract of
record (verdict fusion, wiki node shapes, caps) and keep the two engines in sync (CONTRIBUTING hard
rule 1).

### JS engine args (the spec mirror — for reading the engine, not for baking)
| arg | required | default | meaning |
|---|---|---|---|
| `projectRoot` | **yes** | — | absolute path to the project/example dir (manifest-driven; no hardcoded paths) |
| `panelIds` | no | the **fixed list** `S12,S13,S14,S15` (the default page P02_b08's panels — NOT derived from `page`) | the panels to bake — an array `["S01","S02"]` or a comma-string `"S01,S02"` |
| `page` | no | `P02_b08` | page id (changing `page` does NOT change the `panelIds` fallback) |
| `p0ProofClean` | no | `false` | P0 preflight: only the literal boolean `true` clears it (parity with run_comic's `decision:p0_proof_*` scan); anything else escalates before the panel loop |
| `skipP0Proof` | no | `false` | bake UNAUDITED without P0 clearance — forces the run non-shippable (run_comic's `--skip-p0-proof`) |
| `repoRoot` | no | derived from `projectRoot` | framework root (auto-stripped from `…/examples/<name>`) |
| `bakeLang` | no | `zh` | which bubble language is baked into the image (one language per bake) |
| `finalize` | no | `false` | run the finalize/assembly projection pass |

> `args` may arrive as a JSON **string** in some runtimes — the engine normalizes it (`JSON.parse` with
> fallback). `panelIds`/`page` are validated against a strict id pattern (a bad value throws rather than
> baking the wrong page).

## Runtime behavior you should know
- **Caps:** ≤4 attempts per panel, ≤6 rollbacks per run, then it flags for a human (no infinite loops).
- **One bake at a time.** In agent mode the bake writes to an **explicit per-panel `out_path`** and is
  verified there (`pickup_image.py --out-existing`) — there is **no `/tmp` lock**, because the agent wrapper
  serializes the `mcp__codex__codex` calls one bake at a time. The remaining race surface is per-project: two
  runs on the same project/page collide on the per-panel `.bakereq.json`/`.bakestatus.json` sidecars + the
  shared `out_path`, so keep **one runner per project/page** (operator discipline).
  - **LEGACY (exec-only, retired for real bakes):** the old `--bake-mode=exec` path had `codex image_gen` write
    to a **global dir** while the engine picked the **mtime-newest PNG**, so two concurrent bakes could grab
    each other's images and there was **no code lock**. This global-dir / newest-PNG hazard applies ONLY to the
    retired exec path, not to the agent-sidecar reality above.
- **image_gen throttling:** if a bake is rate-limited mid-run the engine stops cleanly and returns
  `escalated.fresh_run_required = true`. After the cooldown, launch a **fresh** run for the remaining
  panels — do **not** resume cached state (in the JS Workflow mirror: never `resumeFromRunId`, which
  replays the cached throttle and instantly "throttles" again).
- **Seed-anchored:** a failed panel is retried in place (with the failure's repair invariant injected); it
  never rolls back to a previously-kept panel.
- **Model honesty:** the bake payload pins `model: gpt-5.5` + effort `xhigh` as a single compatibility
  default in `run_comic.get_bake_plan()` (a config-driven override is planned — the pin is what the P0 cert
  digests today). The Codex CLI **reviewers** pin no model: they follow your local codex config (e.g.
  `gpt-5.6-sol` today) at effort `xhigh` (`--review-effort`).

See [`docs/comic-json.md`](comic-json.md) for the input you author. [`architecture.md`](architecture.md)
is the **historical pre-rewire design** (banner inside) — the live doctrine is this file + the README +
the `skills/` SOPs.
