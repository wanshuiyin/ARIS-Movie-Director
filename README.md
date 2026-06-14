# ARIS-Movie-Director

A reusable **director framework** for generating narrative comics / 连环画 (and, later, other
visual stories) with **cross-model adversarial review**, a **persistent research wiki**, and a
**deterministic-SVG → codex-bake** narrative-figure pipeline.

The framework knows nothing about any particular story — a project plugs in via
`examples/<name>/movie.project.json` + a `comic.json` IR. The reference example builds a 24-panel
pixel-art comic about an autonomous research run, and ships the **real generation trace** (198 wiki
nodes) as proof the multi-agent loop actually ran.

> **▶ [Read the interactive comic in your browser](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/)** — flip through all 19 pages of the cross-model-audited reference run.

[![Read the interactive comic — cover](docs/comic_cover_v4.webp)](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/)

<table><tr><td width="33%"><a href="https://wanshuiyin.github.io/ARIS-Movie-Director/comic/"><img src="docs/preview_audit.webp" alt="audit page"></a></td><td width="33%"><a href="https://wanshuiyin.github.io/ARIS-Movie-Director/comic/"><img src="docs/preview_panels.webp" alt="multi-panel page"></a></td><td width="33%"><a href="https://wanshuiyin.github.io/ARIS-Movie-Director/comic/"><img src="docs/preview_fix.webp" alt="the fix beat"></a></td></tr></table>

<sub>A few pages from the reference comic — *looks right ≠ passes*: a beautiful panel whose number is wrong (`+6.2` reported vs `+1.4` real) is caught by the gate. **[Read all 19 pages →](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/)**</sub>

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
> (Claude ‖ Gemini-3 ‖ GPT-5.5) until all three APPROVED. The **exact prompt sequence that baked this
> image** (all 4 rounds + the cross-model critiques) is published verbatim as a reference:
> [`skills/method-figure/examples/method_figure/PROMPTS.md`](skills/method-figure/examples/method_figure/PROMPTS.md).*

## Quickstart

This framework produces two things — a **character-consistent comic** and a **research/method figure**.
Pick the path for the output you want.

**A · See the reference comic — zero setup, no API**
```bash
python3 cli/validate_wiki.py examples/comic_m3_audit          # verify the shipped trace -> PASS (198 nodes, 26 edges)
python3 packages/viewer/build_comic.py examples/comic_m3_audit   # (re)build the single-file viewer from comic.json + panels
open  examples/comic_m3_audit/outputs/index.html
```
…or just open the hosted one: **https://wanshuiyin.github.io/ARIS-Movie-Director/comic/**

**B · Make a method figure — input: a blueprint → output: `figure.png`**
One command runs the whole spiral (render condition → `gpt-image-2` bake → 3-model gate → retry until clean):
```bash
python3 skills/method-figure/scripts/run_spiral.py \
    skills/method-figure/examples/method_figure/blueprint.json \
    --identity docs/figassets/aris_identity_sheet.png \
    --out-dir figures/method_figure/demo
#  -> figures/method_figure/demo/figure.png   (+ trace.jsonl of every round)
```
Needs the **`codex` and `gemini` CLIs** on PATH (the cross-model gate + the bake) and headless Chrome.
Author your own input against [`schemas/blueprint.schema.json`](skills/method-figure/schemas/blueprint.schema.json)
to draw any figure — see the worked example in [`PROMPTS.md`](skills/method-figure/examples/method_figure/PROMPTS.md).

**C · Make your own comic — input: a `comic.json` → output: panels + viewer**
Author `examples/<name>/comic.json` (per panel: `scene` · `expected_literals` · `identity_ref`; copy
`examples/comic_m3_audit/comic.json` as the template), then drive `packages/core/spiral_engine.js` through an
**agent / workflow runtime** (e.g. Claude Code's Workflow tool). Per panel it bakes with `codex image_gen`,
runs the 3-model `panel_gate`, writes the wiki, and on KEEP projects to `comic.json` → the viewer.
> It's a *workflow script* (not a bare `node` CLI): it needs the runtime that supplies the `codex`/`gemini`
> calls. See [`docs/spiral-runtime.md`](docs/spiral-runtime.md).
>
> **image_gen throttling:** if a bake is rate-limited mid-run the engine stops cleanly and returns
> `escalated.fresh_run_required = true`. After cooldown, launch a **fresh** run for the remaining panels —
> do **not** `resumeFromRunId` (it replays the cached throttle).

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
  `panels/` baked art, `wiki/` the 198-node generation trace, `outputs/` the built viewer

## License

Dual-licensed (see `NOTICE`):

- **Source code** — MIT (`LICENSE`)
- **Generated example artwork** (`examples/*/panels/`, `examples/*/assets/`, `examples/*/outputs/`) —
  CC-BY-4.0 (`LICENSE-IMAGES`). The images are **AI-generated**; see the AI-generation disclosure in
  `LICENSE-IMAGES`, and review your image-model provider's terms before reuse.
