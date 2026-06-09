# Spiral Runtime (execution model)

> TODO: extract + generalize from `architecture.md` §6-7 + `history/legacy-video-arch.md`.
Per-panel spiral: generate → panel_gate (3 cross-model judges → deterministic JS adjudicator)
→ wiki active-memory → keep / retry-same-panel(+repair invariant) / best-so-far→human;
throttle → stop clean + resumable. Seed-anchored (no rollback-to-prior). Caps. watchdog-CLI.
Runtime capabilities (NOT doc advice): watchdog, resume, rate-limit pacing, generator adapter.
