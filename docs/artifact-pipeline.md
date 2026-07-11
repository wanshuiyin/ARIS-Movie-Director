# Artifact Pipeline — blueprint → bake → verify → gate (current)

The one metered artifact path both workflows share (movie panels via
`skills/comic-director/scripts/run_comic.py`; method figures via
`skills/method-figure/scripts/run_spiral.py`):

1. **Author the truth first** — a deterministic **content-SVG blueprint** + locked identity ref +
   `expected_literals`, all before any pixels (no literals on a baked figure ⇒ fail-closed, never baked).
2. **Deterministic render** — headless Chrome rasterizes the SVG to a crisp condition PNG.
3. **Sidecar bake** — the core emits `<out>.bakereq.json` (prompt with the blueprint + identity ref as
   literal absolute paths, model/config/sandbox, a `request_id` nonce) and polls `<out>.bakestatus.json`;
   the coding agent services it by calling `mcp__codex__codex` (`include_image_gen_tool: true`) to fire
   Codex's native image-generation tool, then writes the status back. The old in-engine `codex exec` bake
   is **retired** — this sidecar is the only bake path.
4. **Pickup verify (fail-closed)** — `pickup_image.py --out-existing` checks the explicit `out_path`:
   bytes / aspect / mtime, the `request_id` nonce, and a HARD-VETO transcript scan against non-native
   (hand-drawn) fallbacks.
5. **Cross-model gate** — Gemini + Codex blind-transcribe the pixels; a deterministic token-diff vs the
   authored `expected_literals` decides KEEP / RETRY (bounded, with repair invariants). No model
   self-acquits; every attempt/review/decision lands in the wiki trace.

Spending is P0-gated: `run_comic.py` refuses step 3 without a digest-bound `decision:p0_proof_*`
certificate (`skills/comic-cross-layer-gate/scripts/run_p0_proof.py`). Details:
[`spiral-runtime.md`](spiral-runtime.md) · [`comic-director`](../skills/comic-director/SKILL.md) ·
[`method-figure`](../skills/method-figure/SKILL.md).
