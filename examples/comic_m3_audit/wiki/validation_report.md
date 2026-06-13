# Validation Report — full-film wiki (clean pass)

> **Reproducible, not hand-written:** `python3 cli/validate_wiki.py examples/comic_m3_audit` → **PASS**
> (174 nodes, 26 edges). The stdlib release gate checks: top-level required fields, node_type/status enums,
> **per-node-type payload invariants**, **no absolute paths** (privacy), and the **edge-type vocabulary**.
> Independently re-verified against `schemas/node_schema.json` + `schemas/edge_schema.json` with a full
> Draft-2020-12 validator (jsonschema): **174/174 nodes + 26/26 edges conform**.

| check | result |
|---|---|
| total nodes | **174** |
| by type | review 99 · decision 34 · panel_attempt 33 · failure_mode 8 |
| edges (`edges.jsonl`) | 26 (`attempt_of` / `reviews` / `decides` / `failure_of`) |
| PII (absolute paths / usernames) | **0** ✓ (verified by the validator; `image_path` is project-relative) |
| generation | 24 panels · 33 attempts · 18 first-try keeps · 6 retried (S10×4, S03×3, S01/S09/S13/S17×2) |
| loop is real | S10 a01–a03 vetoed by `content_corruption` (both visual reviewers) → a04 KEEP; S13 a02 REJECT (unconfirmed literal); B03 cross-frame false-drift → human override |
| cross-model | every attempt judged by CC (narrative) + Gemini (visual) + Codex (visual) — 3 independent reviewers, ≥2 model families |

## Schema reconciliation done in this pass

The shared schemas had drifted from the comic node shapes (they were inherited from the video pipeline):

- **`edge_schema.json`** rewritten to the executable `src/dst/type` convention (was the legacy
  `from/to/edge_type`) with the comic edge vocabulary.
- **`node_schema.json`**: added the `panel_attempt` branch + `$defs/payload_panel_attempt`; relaxed
  `payload_review` / `payload_failure_mode` to the real (flat-score / `layer`+`repair_pattern`) shapes;
  added the comic enum values (`reviewer` cc/codex/gemini, `decision.verdict` retry_panel/accept_by_human,
  `decision.gate_kind` panel, `failure_mode.layer` panel_visual). Video branches left intact.
- **`cli/validate_wiki.py`** deepened: per-node-type payload-required checks + an absolute-path ban +
  edge-type enforcement, so a green PASS now means something.

## Redaction

`image_path` is project-relative across all 174 nodes; the validator FAILS the build if any payload string
contains `/Users/` or `/home/`. No usernames, machine names, API keys, or private-repo paths remain.
See `../REDACTION.md`.

## Honesty note on timestamps

`created_at` is a logical placeholder, not wall-clock — `Date.now()` is unavailable in the generation
sandbox (it would break resume determinism). Node order is by attempt id, not real time.
