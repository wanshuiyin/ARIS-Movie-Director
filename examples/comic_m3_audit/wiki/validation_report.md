# Validation Report — B08 wiki (clean pass, 2026-06-10)

> **Reproducible, not hand-written:** `python3 cli/validate_wiki.py examples/comic_m3_audit` → **PASS**
> (26 nodes, 26 edges conform to `schemas/node_schema.json` — required fields + node_type/status enums).
> The schema was synced to the comic spiral in this pass (added `panel_attempt`, `final`, `complete`).

| check | result |
|---|---|
| total nodes | **26** |
| by type | decision 5 · review 15 · panel_attempt 5 · failure_mode 1 |
| final decisions | 5 / 5 ✓ |
| edges (`edges.jsonl`) | 26 |
| PII (absolute paths / usernames) | **0** ✓ (redacted; `image_path` project-relative) |
| coherence | 4 KEEP (S12/S13/S14/S15 a01) + 1 real REJECT (S13 a02) — **no stale cross-run / old-story nodes** |
| cross-model | every attempt judged by CC + Gemini + Codex (3 independent reviewers, ≥2 model families) |

## What was removed in the clean pass

39 stale nodes from earlier runs were deleted: old-story attempts (the abstract "K3 invariant" narrative
that predates the M3 audit story) and html-mode verdicts (pre-`baked` engine), plus three `failure_mode`
nodes that contradicted their own `KEEP` decision. The kept 26 nodes are exactly one coherent M3-baked
production trace.

## Redaction

Absolute paths (`/Users/.../examples/comic_m3_audit/`) were stripped from 6 node files; `image_path` is now
project-relative. No usernames, machine names, API keys, or private-repo paths remain. See `../REDACTION.md`.
