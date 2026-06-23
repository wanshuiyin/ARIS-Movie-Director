# Spiral Runtime — how to launch comic generation

`packages/core/spiral_engine.js` is a **workflow script**, not a bare CLI. It begins with
`export const meta = {…}` and calls `agent()` / `phase()` / `parallel()` — those primitives only exist
inside an **agent/workflow runtime** (e.g. Claude Code's **Workflow tool**), which is what drives the
deterministic core (blueprint render + the `codex` / `gemini` cross-model gate calls). The JS engine does
**not** itself bake: its in-engine `codex image_gen` path is **retired** (`generatePanel` HARD-FAILS it
with `exec-bake-retired`), and the **real** per-panel bake is the **agent `mcp__codex__codex` sidecar**
serviced via the Python SOP (`run_comic.py --bake-mode=agent`, which emits `.bakereq.json` / awaits
`.bakestatus.json`). So you don't run it with `node`; you launch it through that runtime.

## Launch (the concrete call)
In Claude Code, the simplest trigger is natural language — *"generate panels S01,S02 for
examples/mycomic"* — which makes the agent issue this Workflow call:

```js
Workflow({
  scriptPath: "packages/core/spiral_engine.js",
  args: {
    projectRoot: "/ABS/PATH/TO/examples/mycomic",   // REQUIRED — abs path to the project dir (has comic.json, panels/, wiki/)
    panelIds:    "S01,S02"                            // which panels to bake (array OR comma-string)
  }
})
```

Per panel the deterministic core (driven by the Workflow engine) does: render the `condition.content_svg`
blueprint → **agent `mcp__codex__codex` sidecar bake** (blueprint + identity ref) via the Python SOP
(`run_comic.py --bake-mode=agent` emits `.bakereq.json` / awaits `.bakestatus.json`), verified by
`pickup_image.py --out-existing` — **not** an in-engine `codex image_gen` bake → `panel_gate`
(CC ‖ Gemini ‖ Codex → deterministic verdict) → write wiki nodes → keep / retry (≤4/panel) → page
`assembly_gate` → project the kept panels into `comic.json`. Then build the viewer:
`python3 packages/viewer/build_comic.py examples/mycomic`.

## args
| arg | required | default | meaning |
|---|---|---|---|
| `projectRoot` | **yes** | — | absolute path to the project/example dir (manifest-driven; no hardcoded paths) |
| `panelIds` | no | the page's panels | the panels to bake — an array `["S01","S02"]` or a comma-string `"S01,S02"` |
| `page` | no | `P02_b08` | which page to generate when `panelIds` isn't given |
| `repoRoot` | no | derived from `projectRoot` | framework root (auto-stripped from `…/examples/<name>`) |
| `bakeLang` | no | `zh` | which bubble language is baked into the image (one language per bake) |
| `finalize` | no | `false` | run the finalize/assembly projection pass |

> `args` may arrive as a JSON **string** in some runtimes — the engine normalizes it (`JSON.parse` with
> fallback), so both an object and a stringified object work. `panelIds`/`page` are validated against a
> strict id pattern (a bad value throws rather than baking the wrong page).

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
  panels — do **not** `resumeFromRunId`, which replays the cached throttle and instantly "throttles" again.
- **Seed-anchored:** a failed panel is retried in place (with the failure's repair invariant injected); it
  never rolls back to a previously-kept panel.

See [`docs/comic-json.md`](comic-json.md) for the input you author, and [`architecture.md`](architecture.md)
for the full design.
