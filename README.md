# ARIS-Movie-Director

A reusable **director framework** for generating narrative comics / 连环画 (and, later, other
visual stories) with **cross-model adversarial review**, a **persistent research wiki**, and a
**deterministic-SVG → codex-bake** narrative-figure pipeline.

The framework knows nothing about any particular story — a project plugs in via
`examples/<name>/movie.project.json` + a `comic.json` IR. The reference example builds a 24-panel
pixel-art comic about an autonomous research run, and ships the **real generation trace** (174 wiki
nodes) as proof the multi-agent loop actually ran.

![ARIS-Movie-Director — method overview](docs/method_figure.png)

> **Figure 1.** From story intent to a verified comic, end-to-end. **(1) Authored source of truth** —
> asset library · outline · storyboard compile into `comic.json` (`content_svg · expected_literals ·
> identity_ref`). **(2) The audited spiral (per panel)** — a content-SVG blueprint is baked by image_gen,
> then a 3-reviewer cross-model `panel_gate` (CC ‖ Gemini ‖ Codex · *blind token-diff* · single-vote veto)
> returns a deterministic `verdict`: **KEEP**, or **RETRY** (≤4/panel) re-baked with the failed attempt's
> repair note; every attempt/review/decision/failure is logged to the `research-wiki`. **(3) Assembly +
> release** — a cast-aware `page_assembly_gate` (repair drift → re-bake, ≤6/run) ships PNG panels + a
> single-file HTML viewer. The punchline (bottom-left): **a beautiful panel with a wrong number does not
> pass** — `+6.2` expected vs `+6.25` observed fails the token-diff.
>
> *This figure was itself produced by the same loop it depicts: a labeled blueprint conditioned
> `gpt-image-2` (driven by Codex GPT-5.5 xhigh), then 4 generation rounds were ratified by a 3-model panel
> (Claude ‖ Gemini-3 ‖ GPT-5.5) until all three APPROVED.*

## How it works

Per panel, the **spiral engine** (`packages/core/spiral_engine.js`, run via a workflow runtime):

```
author a deterministic content-SVG blueprint  ->  render to PNG
   ->  codex image_gen bakes a narrative pixel-art panel (blueprint ref + identity ref)
   ->  panel_gate: 3 INDEPENDENT cross-model reviewers
        * CC      narrative  (does the panel land its story beat?)
        * Gemini  visual     (identity / style / artifacts / baked-text legibility / number transcription)
        * Codex   visual     (a second, different-model-family eye)
      -> a DETERMINISTIC JS verdict: blind observed_literals token-diffed vs authored expected_literals;
         content_corruption is a single-vote veto; both visual reviewers must score; no model self-acquits
   ->  write wiki nodes (attempt / review x3 / decision / failure_mode)
   ->  keep | retry | bounded cross-frame rollback  ->  page assembly_gate
   ->  project to comic.json  ->  single-file clickable HTML viewer
```

The gate is the point: a beautiful panel with a wrong number does **not** pass. Faithfulness is a
token-diff over reviewers who are never shown the expected values.

## Layout

- **packages/** — the framework runtime (core spiral, gates, conditioning, viewer)
- **protocols/** — the cross-model review / governance contracts (framework-owned)
- **schemas/** — versioned IR + wiki node/edge schemas (`node_schema.json`, `edge_schema.json`)
- **cli/** — `validate_wiki.py` (the stdlib release gate for a project's wiki)
- **docs/** — `architecture.md` (SSOT), `spiral-runtime.md`, `artifact-pipeline.md`, `GENERATION_RETRO.md`
- **examples/comic_m3_audit/** — the reference comic: `comic.json` IR, `gen/` blueprint scripts,
  `panels/` baked art, `wiki/` the 174-node generation trace, `outputs/` the built viewer

## Quickstart

```bash
# 1. validate the example's research-wiki trace (pure stdlib, no deps)
python3 cli/validate_wiki.py examples/comic_m3_audit          # -> PASS (174 nodes, 26 edges)

# 2. (re)build the single-file clickable viewer from comic.json + baked panels
python3 packages/viewer/build_comic.py examples/comic_m3_audit
open  examples/comic_m3_audit/outputs/index.html
```

Generating new panels drives `packages/core/spiral_engine.js` through a workflow runtime that can invoke
the `codex` and `gemini` CLIs (cross-model gate) and `codex image_gen` (bake). See `docs/spiral-runtime.md`.

> **Note on image_gen throttling:** if a bake is rate-limited mid-run the engine stops cleanly and returns
> `escalated.fresh_run_required = true`. After the cooldown, launch a **fresh** run for the remaining
> panels — do **not** `resumeFromRunId`, which would replay the cached throttle.

## License

Dual-licensed (see `NOTICE`):

- **Source code** — MIT (`LICENSE`)
- **Generated example artwork** (`examples/*/panels/`, `examples/*/assets/`, `examples/*/outputs/`) —
  CC-BY-4.0 (`LICENSE-IMAGES`). The images are **AI-generated**; see the AI-generation disclosure in
  `LICENSE-IMAGES`, and review your image-model provider's terms before reuse.
