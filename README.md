# aris-movie-director

A reusable **director framework** for generating narrative comics/连环画 (and later, other
visual stories) with cross-model adversarial review, a persistent wiki, and a
deterministic-SVG → codex-bake narrative-figure pipeline.

- **packages/** — the framework runtime (core spiral, gates, conditioning, viewer)
- **protocols/** — the cross-model review/governance contracts (copied, framework-owned)
- **schemas/** — versioned IR + wiki node/edge schemas
- **docs/** — architecture SSOT (`architecture.md`), runtime, artifact pipeline, history
- **examples/comic_m3_audit/** — **example #1**: the ARIS dllm-audit comic, incl. its
  redacted wiki (the "multi-agent loop really ran" proof)

Status: **private dev**. The framework API is NOT frozen — it crystallizes as example #2
(a different theme) is built. Boundary: the framework knows nothing about ARIS/DLLM/any
character; a project plugs in via `examples/*/movie.project.json`.
