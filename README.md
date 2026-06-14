<p align="center">
  <img src="docs/aris_logo.svg" alt="ARIS — Auto Research in Sleep" width="640">
</p>

# ARIS-Movie-Director

> Hand a fuzzy story to your agent, wake up to a **cross-model-audited movie** 🎬 — image-based today, **video next**.

**📚 Jump to** — [▶ Watch the movie](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/) · [⚡ Quickstart](#quickstart) · [🔬 How it works](#how-it-works) · [📝 Author your own](skills/comic-author/references/authored_source_of_truth.md) · [🧩 Layout](#layout)

[![ARIS Stars](https://img.shields.io/github/stars/wanshuiyin/Auto-claude-code-research-in-sleep?style=flat&logo=github&logoColor=white&color=gold&label=ARIS%20Stars)](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/stargazers) · [![arXiv](https://img.shields.io/badge/arXiv-2605.03042-b31b1b?style=flat&logo=arxiv)](https://huggingface.co/papers/2605.03042) · [![HF Daily #1](https://img.shields.io/badge/HF%20Daily%20Papers-%231-yellow?style=flat)](https://huggingface.co/papers/2605.03042) · [![PaperWeekly](https://img.shields.io/badge/Featured%20on-PaperWeekly-red?style=flat)](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) · [![awesome-agent-skills](https://img.shields.io/badge/Featured%20in-awesome--agent--skills-blue?style=flat&logo=github)](https://github.com/VoltAgent/awesome-agent-skills)

**ARIS-Movie-Director is the multimodal vertical of the [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) series — a director for AI-generated movies.** ARIS taught a research agent to work while you sleep; its **research-wiki + multi-agent-debate** philosophy applies just as well to *making things you can watch*. Same loop — **author a deterministic source of truth → let a generative model bake the look → ratify it with a cross-model adversarial panel** — now producing **character-consistent, fact-checked visual stories** instead of papers. *Looks right ≠ passes:* a beautiful frame whose number is wrong is rejected by a deterministic token-diff. **The ARIS series unlocks multimodal generation for the first time:** text-first research → multimodal-first storytelling.

**This first release is image-based** — the movie is told in baked still frames you flip through. **Video-based generation is what comes next; this is just the beginning.**

The framework knows nothing about any particular story — a project plugs in via
`examples/<name>/movie.project.json` + a `comic.json` IR. The reference example builds a 24-frame
pixel-art movie about an autonomous research run, and ships the **real generation trace** (198 wiki
nodes) as proof the multi-agent loop actually ran.

---

> **▶ [Watch the image-based movie in your browser](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/)** — flip through all 19 scenes of the cross-model-audited reference run.

[![Watch the movie — cover](docs/comic_cover_v4.webp)](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/)

<table><tr><td width="33%"><a href="https://wanshuiyin.github.io/ARIS-Movie-Director/comic/"><img src="docs/preview_audit.webp" alt="audit page"></a></td><td width="33%"><a href="https://wanshuiyin.github.io/ARIS-Movie-Director/comic/"><img src="docs/preview_panels.webp" alt="multi-panel page"></a></td><td width="33%"><a href="https://wanshuiyin.github.io/ARIS-Movie-Director/comic/"><img src="docs/preview_fix.webp" alt="the fix beat"></a></td></tr></table>

<sub>A few frames from the reference movie — *looks right ≠ passes*: a beautiful frame whose number is wrong (`+6.2` reported vs `+1.4` real) is caught by the gate. **[Watch all 19 scenes →](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/)**</sub>

![ARIS-Movie-Director — method overview](docs/method_figure.png)

> **Figure 1.** From story intent to a verified movie, end-to-end. **(1) Authored source of truth** —
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

This framework produces two things — a **character-consistent movie** (image-based today) and a
**research/method figure**. Pick the path for the output you want.

**A · See the reference movie — zero setup, no API**
```bash
python3 cli/validate_wiki.py examples/comic_m3_audit          # verify the shipped trace -> PASS (198 nodes, 26 edges)
python3 packages/viewer/build_comic.py examples/comic_m3_audit   # (re)build the single-file viewer from comic.json + panels
open  examples/comic_m3_audit/outputs/index.html
```
…or just open the hosted one: **https://wanshuiyin.github.io/ARIS-Movie-Director/comic/**

**B · Make a method figure — input: a brief → output: `figure.png`**
Feed ONE ARIS-format artifact — a `method_figure_brief.json` (the same brief `paper-plan` emits after its
claims_matrix) — and one command runs the whole spiral (Step-0 compile → render condition → `gpt-image-2` bake →
Gemini+Codex blind panel + `content_diff` → retry until clean → Claude structural sign-off):
```bash
# OUR example brief bakes ARIS's own Figure 1 — swap in your own method_figure_brief.json
python3 skills/method-figure/scripts/run_spiral.py \
    skills/method-figure/examples/method_figure/method_figure_brief.json \
    --out-dir figures/method_figure/demo
#  -> figures/method_figure/demo/figure.png   (the PANEL-CLEAN candidate, awaiting your structural sign-off)
#     (+ blueprint.json + traceability.json + trace.jsonl of every round)
#  first run? use --p0-only (zero image credits: validate+compile+render+lint). NOTE: --dry-run still writes these files.
```
The brief is auto-compiled into the content-locked `blueprint.json` (**Step-0 is a deterministic step inside the
skill** — you never hand-write a blueprint or place coordinates), the identity sheet is resolved from the brief's
`identity_refs[].path` (no separate `--identity` to manage), and every node is traceability-checked back to a
brief field (an un-traceable node fails closed). Needs the **`codex` and `gemini` CLIs** on PATH and headless Chrome.

> **Only have a paper, no brief yet?** Point your coding agent — e.g. the
> **[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) main project** — at your paper to
> emit the `method_figure_brief.json` first (claims/numbers verbatim) — the exact SOP + prompt is
> [`paper_to_brief.md`](skills/method-figure/references/paper_to_brief.md), then run the command above.
> **Power-user:** already have a hand-tuned blueprint? `run_spiral.py blueprint.json --identity sheet.png
> --out-dir … --from-blueprint` runs the legacy path. The worked 4-round convergence (the exact prompts) is in
> [`PROMPTS.md`](skills/method-figure/examples/method_figure/PROMPTS.md).

**C · Make your own movie — input: a fuzzy idea → output: frames + viewer**
Phase 1 is an **agent workflow, not a shell CLI**: you point your coding agent (Claude, Codex, … — e.g. the
**[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) main project**) at the
**[`comic-author`](skills/comic-author/SKILL.md)** orchestrator; the agent FOLLOWS its ordered steps
(intent → outline → storyboard → assets → blueprints → `comic.json`), each step a detailed skill it runs, each
`--gate` an agent procedure (cross-model review → fuse), authoring the wiki nodes + the `comic.json`. (Per-layer
detail: [`authored_source_of_truth.md`](skills/comic-author/references/authored_source_of_truth.md); IR fields:
[`docs/comic-json.md`](docs/comic-json.md) / [`schemas/comic.schema.json`](schemas/comic.schema.json); copy
`examples/comic_m3_audit/comic.json` as a template.) Then Phase 2/3 IS a real one-command CLI — the spiral:
```bash
python3 skills/comic-director/scripts/run_comic.py \
    --project examples/comic_m3_audit --page P02_b08 --panels S12,S13,S14,S15 \
    --dry-run                 # validate + print every bake prompt (no image_gen) — run this FIRST
# drop --dry-run to bake; add --finalize to rebuild the viewer when the run is shippable
```
Per panel it renders the content-SVG blueprint, bakes with `codex image_gen`, runs the 3-model `panel_gate`,
writes the wiki, and on KEEP projects to `comic.json`. Needs the **`codex` + `gemini` CLIs** + headless Chrome.
> `run_comic.py` is a standalone subprocess port of the movie spiral engine — no agent runtime needed. (Inside an
> agent runtime you can instead drive `packages/core/spiral_engine.js` via the Workflow tool — same result.)
> Args + runtime behavior (caps 4/panel · 6/run, throttle → fresh run, assembly): **[`docs/spiral-runtime.md`](docs/spiral-runtime.md)**.
>
> **image_gen throttling:** a rate-limited bake stops cleanly with `fresh_run_required`. After cooldown,
> launch a **fresh** run for the remaining panels — do **not** resume cached state.

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
- **schemas/** — versioned IR + wiki schemas (`comic.schema.json`, `node_schema.json`, `edge_schema.json`)
- **cli/** — `validate_wiki.py` (the stdlib release gate for a project's wiki)
- **docs/** — `comic-json.md` (the authored-input spec), `architecture.md` (SSOT), `spiral-runtime.md`, `GENERATION_RETRO.md`
- **examples/comic_m3_audit/** — the reference movie: `comic.json` IR, `gen/` blueprint scripts,
  `panels/` baked art, `wiki/` the 198-node generation trace, `outputs/` the built viewer

## License

Dual-licensed (see `NOTICE`):

- **Source code** — MIT (`LICENSE`)
- **Generated example artwork** (`examples/*/panels/`, `examples/*/assets/`, `examples/*/outputs/`) —
  CC-BY-4.0 (`LICENSE-IMAGES`). The images are **AI-generated**; see the AI-generation disclosure in
  `LICENSE-IMAGES`, and review your image-model provider's terms before reuse.
