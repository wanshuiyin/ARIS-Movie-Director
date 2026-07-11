# Live bake smoke — 2026-07-11 (agent sidecar seam, 1 image credit)

First **live end-to-end run of the agent-mode bake chain** since the June 2026 sidecar rewire, executed on a
**throwaway copy** of `examples/comic_m3_audit` (the shipped reference was not touched). One panel (S12),
`--bake-mode=agent --max-total 1 --bake-timeout 900 --skip-p0-proof`.

![S12 smoke panel](figassets/bake_smoke_S12_2026-07-11.png)

## What was empirically verified

| Link in the chain | Result |
|---|---|
| P0 digest preflight, no cert (zero-cost pre-check) | ✅ fail-closed — `FAIL-CLOSED: no clean decision:p0_proof_* node` |
| `--skip-p0-proof` escape hatch | ✅ honest: run warns UNAUDITED, final report `shippable:false`, `p0_skipped:true` |
| `.bakereq.json` sidecar emit | ✅ full contract — prompt (ART_BIBLE + panel body + abs-path refs + exact out path), `model gpt-5.5`, `config {model_reasoning_effort:xhigh, include_image_gen_tool:true}`, `sandbox workspace-write`, `request_id` nonce, `min_bytes 500000` |
| Agent wrapper → `mcp__codex__codex` bake | ✅ **real native image**: 1,974,602 bytes, 1672×941, saved by codex to the exact `out_path` |
| Baked fidelity (eyeball vs blueprint) | ✅ locked literals all correct (`Δ +6.2`, `89.1%`/`82.9%`, `span 跨边界切碎` / `span ⊆ schema`, `"Tokyo"`/`1603`/`13.9M`, `def exact_parse(json_str, schema):`), duo identity exact, CJK bubbles clean |
| `.bakestatus.json` → `pickup_image.py --out-existing` | ✅ verified (sig+dims+size+mtime+nonce+HARD-VETO); `image_sha256` recorded in the run report |
| 3-reviewer `panel_gate` | ✅ ran; Gemini reviewer timed out → **fail-safe `retry_panel`** (fail-closed, not fail-open) |
| Caps / report / exit codes | ✅ `--max-total 1` respected → best-so-far **flagged for HUMAN**, `needs_human:true`, `finalize:false`, **exit 3** (matches the documented failure matrix) |
| Wiki trace | ✅ `attempt` + 3 `review` + `decision` + `failure_mode` nodes written |

## Known external blocker (environment, not pipeline)

The `gemini` CLI on the test machine is **dead**: `IneligibleTierError — Gemini Code Assist for individuals
is no longer supported for this client` (migrate to the Antigravity suite). Consequences until the operator
migrates (or a configurable second-family reviewer lands):

- panels cannot reach a **KEEP** verdict (the Gemini visual reviewer always times out → fail-safe retry);
- `run_p0_proof.py` cannot reach a real both-family quorum (google reviews unavailable) — `--skip-p0-proof`
  is the only path, which correctly forces every run non-shippable.

This is exactly the failure mode the gates are designed to contain: with a reviewer family missing, the
pipeline **refuses to acquit** rather than shipping unreviewed panels.

## SOP finding (wrapper hardening candidate)

`mcp__codex__codex` returned an **empty `content` string** for this bake (image-only reply). The wrapper must
serialize the **raw MCP response** into `bakestatus.mcp_output` (a non-empty faithful record) or pickup
fail-closes on the empty-transcript guard. The planned shared broker (`service_bake_requests.py`, Wave 3)
should capture the full event stream rather than only the final text.
