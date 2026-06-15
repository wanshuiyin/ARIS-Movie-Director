<p align="center">
  <img src="docs/aris_logo.svg" alt="ARIS — Auto Research in Sleep" width="640">
</p>

# ARIS-Movie-Director

> Hand a fuzzy story to your agent, wake up to a **cross-model-audited movie** 🎬 — image-based today, **video next**.

**📚 Jump to** — [▶ Watch the movie](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/) · [⚡ Quickstart](#quickstart) · [🔬 How it works](#how-it-works) · [📝 Make your own (comic-author)](skills/comic-author/SKILL.md) · [🧩 Layout](#layout) · [🤝 Contributing](CONTRIBUTING.md)

[![CI](https://github.com/wanshuiyin/ARIS-Movie-Director/actions/workflows/ci.yml/badge.svg)](https://github.com/wanshuiyin/ARIS-Movie-Director/actions/workflows/ci.yml) · [![ARIS Stars](https://img.shields.io/github/stars/wanshuiyin/Auto-claude-code-research-in-sleep?style=flat&logo=github&logoColor=white&color=gold&label=ARIS%20Stars)](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep/stargazers) · [![arXiv](https://img.shields.io/badge/arXiv-2605.03042-b31b1b?style=flat&logo=arxiv)](https://huggingface.co/papers/2605.03042) · [![HF Daily #1](https://img.shields.io/badge/HF%20Daily%20Papers-%231-yellow?style=flat)](https://huggingface.co/papers/2605.03042) · [![PaperWeekly](https://img.shields.io/badge/Featured%20on-PaperWeekly-red?style=flat)](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) · [![awesome-agent-skills](https://img.shields.io/badge/Featured%20in-awesome--agent--skills-blue?style=flat&logo=github)](https://github.com/VoltAgent/awesome-agent-skills)

Generated visual stories can look coherent while quietly changing the facts — a chart rounds a number, a
label mutates, a character's face drifts — and the run still ships, because the same system that drew the
frame is the one saying it looks fine. **ARIS-Movie-Director treats every frame as an auditable artifact:**
author a deterministic `comic.json` first (lock the `expected_literals` + identity refs *before* any pixels),
let a generative model bake the look, then require **independent cross-model blind-transcription + a
deterministic token-diff** before a panel is kept. *Looks right ≠ passes* — a beautiful frame whose number is
wrong (`+6.2` expected vs `+6.25` observed) is rejected. Every attempt, retry, and decision lands in an
inspectable **research-wiki** trace.

**This is a long-horizon visual generation task** — a whole movie (19 scenes), not a single image — and across
that horizon two failure modes appear that a lone *streaming* model can't fix by itself. Each maps to one idea
ARIS-Movie-Director brings over from [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep):

- 🧠 **Long-range forgetting** — over many frames, identity, established facts, and earlier decisions drift. → a **research-wiki**: persistent, inspectable memory (locked refs · `expected_literals` · every decision & failure as a node) keeps late frames anchored to early truth.
- 🗣️ **Linear, self-approved streaming** — each frame is committed by the same model that drew it, so mistakes compound unchecked. → **multi-agent debate**: independent cross-model reviewers blind-read every frame and a deterministic diff decides **KEEP / RETRY** — no frame signs off on itself.

**🔬 Method at a glance.** Read the figure left-to-right — the loop the paragraph above describes
(*author a source of truth → bake → cross-model gate*) is exactly its three stages: **(1)** authored
`comic.json` + locked refs, **(2)** the per-panel audited spiral, **(3)** assembly + release. The bottom-left
failure is the whole rule: *a beautiful but wrong literal still fails* (`+6.2` expected vs `+6.25` observed).

![ARIS-Movie-Director — method overview](docs/method_figure.png)

<sub>**Figure 1** — from story intent to a verified movie, end-to-end (the loop described above). Full caption ↓</sub>

<details><summary><b>Figure 1 — stages, gates, and provenance</b> (click to expand)</summary>

> **(1) Authored source of truth** — asset library · outline · storyboard compile into `comic.json` (`content_svg · expected_literals · identity_ref`). **(2) The audited spiral (per panel)** — a content-SVG blueprint is baked by image_gen, then a 3-reviewer cross-model `panel_gate` (CC narrative ‖ Gemini + Codex visual *blind-transcribe* → a deterministic token-diff · single-vote veto) returns a deterministic `verdict`: **KEEP**, or **RETRY** (≤4/panel) re-baked with the failed attempt's repair note; every attempt/review/decision/failure is logged to the `research-wiki`. **(3) Assembly + release** — a cast-aware `page_assembly_gate` (repair drift → re-bake, ≤6/run) ships PNG panels + a single-file HTML viewer. The punchline (bottom-left): **a beautiful panel with a wrong number does not pass** — `+6.2` expected vs `+6.25` observed fails the token-diff.
>
> *This figure was itself produced by the same loop it depicts: a labeled blueprint conditioned `gpt-image-2` (driven by Codex GPT-5.5 xhigh), then 4 generation rounds were ratified by the method-figure panel — **Gemini + Codex blind-transcribe + a deterministic `content_diff`, then a Claude structural sign-off** — until clean. The **exact prompt sequence that baked this image** (all 4 rounds + the cross-model critiques) is published verbatim as a reference: [`skills/method-figure/examples/method_figure/PROMPTS.md`](skills/method-figure/examples/method_figure/PROMPTS.md).*

</details>

**This first release is image-based** — the movie is told in baked still frames you flip through. **Video-based generation is what comes next; this is just the beginning.**

> **▶ [Watch the image-based movie in your browser](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/)** — flip through all 19 scenes of the cross-model-audited reference run.

[![Watch the movie — cover](docs/comic_cover_v4.webp)](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/)

<table><tr><td width="33%"><a href="https://wanshuiyin.github.io/ARIS-Movie-Director/comic/"><img src="docs/preview_audit.webp" alt="audit page"></a></td><td width="33%"><a href="https://wanshuiyin.github.io/ARIS-Movie-Director/comic/"><img src="docs/preview_panels.webp" alt="multi-panel page"></a></td><td width="33%"><a href="https://wanshuiyin.github.io/ARIS-Movie-Director/comic/"><img src="docs/preview_fix.webp" alt="the fix beat"></a></td></tr></table>

<sub>A few frames from the reference movie — including the story's own integrity beat: a run that **reported `+6.2`** improvement but **really moved `+1.4`** (that's the *plot*, distinct from the figure's bake-time `+6.2`/`+6.25` token-diff). **[Watch all 19 scenes →](https://wanshuiyin.github.io/ARIS-Movie-Director/comic/)**</sub>

<details><summary><b>⚡ What the audit gate actually catches</b> — the problem → mechanism table</summary>

| The problem | What ARIS-Movie-Director does about it |
|---|---|
| A panel can look right while changing a number, label, or code token. | `comic.json` locks the `expected_literals`; independent visual reviewers **blind-transcribe** what's actually in the pixels; an exact token-diff rejects any wrong or missing literal. |
| The model that baked an image can wave its own output through. | The bake never self-attests — independent visual models (a **different family** from the generator) read it blind, and a **deterministic** diff, not a model's opinion, decides **KEEP / RETRY**. |
| A frame can be baked with nothing to check it against. | Phase 1 authors `content_svg` · `identity_ref` · `ART_BIBLE` · `expected_literals` *before* pixels; a baked figure-panel with **no** gateable literals **fails closed**. |
| Character & style drift accumulate across a long sequence. | Locked identity refs + asset review (准×3) + a style bible + a **cast-aware** assembly gate check consistency *while allowing* intended scene/cast variation (absence ≠ drift). |
| Retry loops go opaque or endless. | Per-panel attempts and assembly repairs are **bounded**; each failure carries a repair note; a non-convergent panel is **flagged for a human**, never silently shipped. |
| A demo hides what was tried and thrown away. | Every attempt / review / decision / failure-mode is written to the research-wiki — the reference run ships a **198-node** trace you can read. |

</details>

<details><summary><b>🧭 Positioning</b> — ARIS lineage; an audit layer, <i>not</i> a generation/orchestration claim</summary>

ARIS-Movie-Director is the **multimodal vertical of the [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) series**: ARIS taught a research agent to work while you sleep, and its **research-wiki + multi-agent-debate** ideas are exactly what make a generated story *auditable* — the same loop (author a source of truth → let a model bake the look → ratify with a cross-model panel), now producing character-consistent visual stories instead of papers.

The framework knows nothing about any particular story — a project plugs in via `examples/<name>/movie.project.json` + a `comic.json` IR. The reference example builds a **19-scene / 24-frame** pixel-art movie about an autonomous research run, and ships its **real, inspectable generation trace** as proof the multi-agent loop actually ran.

**Related work — where we fit.** The field already generates and orchestrates visual stories well, and we build on that, not against it: **[JoyAI-Echo](https://github.com/jd-opensource/JoyAI-Echo)** (JD) is strong at long-form text→video with synced audio and memory-based character consistency; **[FireRed-OpenStoryline](https://github.com/FireRedTeam/FireRed-OpenStoryline)** (Xiaohongshu) is a strong conversational video-editing agent — NL planning, tool orchestration, human-in-the-loop, reusable style skills; **[NEWTON](https://arxiv.org/abs/2605.18396)** shows planner-plus-verifier loops for *physically*-grounded video. ARIS-Movie-Director is **complementary** — it doesn't claim better generation or broader orchestration; it adds the **audit layer** around a generated visual story: blind cross-model reads → deterministic literal-diffs → bounded retry → an inspectable trace.

</details>

---

## Quickstart

This framework makes two **cross-model-audited** things — **your own character-consistent movie** (image-based
today) and a **research/method figure**. Pick your path.

**A · Make your own movie — fuzzy idea → audited frames + a clickable viewer**
One end-to-end **slash-command agent workflow** (the ARIS `/research-pipeline` paradigm) — hand your agent a
fuzzy story, approve two story gates, wake up to a baked, cross-model-audited movie + a clickable viewer:

```text
> /movie-pipeline "a short film about an autonomous research run"
```

It chains [`comic-author`](skills/comic-author/SKILL.md) (Phase 1 — author the source of truth) → the zero-credit
`p0_proof` gate → [`comic-director`](skills/comic-director/SKILL.md) (Phase 2/3 — the audited spiral → viewer);
the orchestrator is [`movie-pipeline`](skills/movie-pipeline/SKILL.md). It is an **agent** workflow, not a shell
binary — it needs a coding-agent runtime and **pauses at intent + outline for your approval**. **Phase 2/3 also
runs standalone** — `run_comic.py` (a subprocess CLI port, no agent runtime; this is the CI-tested slice) **or**
`packages/core/spiral_engine.js` (via a workflow runtime); same result. *(A step that doesn't fire is safe — each
layer consumes the prior LOCKED node, so a skipped step fails closed at the next gate, never shipping a wrong frame.)*

- 🧭 **Intent** — fuzzy idea → `intent_spec` · **stop for your approval**
- 🎨 **Style lock** — the `ART_BIBLE.md` + locked `style_anchor`s (warm-lab / dark-cyber / starfield)
- 🧱 **Outline** — 3-lens debate → synthesis → `outline_spec` · **stop for your approval**
- 🎞️ **Storyboard** — pages · panels · the MOTIF STATE TABLE · consolidated `asset_requests`
- 🧑‍🎨 **Assets** — a single-source library, reviewed to `locked` (准×3 same-round unanimity)
- 📐 **Blueprints** — a deterministic `content_svg` per panel (no baked bubbles)
- 🧾 **Prompts** — exact bake prompts + verbatim `expected_literals` (搬运工原則)
- ✅ **Compile** — schema-valid `comic.json`; the zero-credit `p0_proof` gate runs BEFORE any image credit
- 🔥 **Spiral bake** — render → `codex image_gen` → 3-reviewer `panel_gate` → keep / retry / cross-frame rollback → assembly → viewer

<details><summary>📐 flow — Phase-1 agent workflow → Phase-2/3 spiral</summary>

```text
fuzzy idea
  └─ Phase 1 · comic-author AGENT WORKFLOW (your agent follows the skills)
       intent ─(you approve)─ style ─ outline ─(you approve)─ storyboard ─ assets(locked) ─ blueprints ─ prompts ─ comic.json
                 each step = a detailed skill + its --gate (agent procedure: fan out cross-model reviewers → fuse → flip status)
  └─ comic.json + locked assets + the author wiki trace
  └─ Phase 2/3 · spiral engine   (run_comic.py  OR  spiral_engine.js via a workflow runtime)
       content_svg ─ bake (codex image_gen) ─ panel_gate (CC narrative ‖ Gemini visual ‖ Codex visual ─
                     deterministic token-diff over the blind transcriptions · single-vote veto) ─ keep/retry
                     ─ page assembly_gate ─ project to comic.json ─ single-file HTML viewer
```
</details>

**Two honest ways to run it**

**1) End-to-end (one slash-command, agent-run):**
```text
> /movie-pipeline "«your fuzzy idea»"
```
The agent authors Phase 1 (pausing at **intent + outline** for your approval), clears `p0_proof`, bakes the
audited spiral, and builds the viewer. It's agent-run — non-deterministic + needs a coding-agent runtime — but
every step is gated, and a step that doesn't fire **fails closed** at the next gate.

**2) Phase 2/3 only (deterministic, no agent — the CI-tested slice),** once `comic.json` exists:
```bash
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <PAGE> --panels S01,S02 --dry-run    # zero credit: prints bake prompts
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <PAGE> --panels S01,S02 --finalize   # bake + rebuild the viewer
open examples/<name>/outputs/index.html
```

> **One command, but agent-run — not a shell CLI.** The end-to-end entry is a *slash-command agent workflow*
> (`/movie-pipeline`, like ARIS's `/research-pipeline`), not a `foo.py "idea"` binary: it needs a coding-agent
> runtime and pauses at the two human gates. The deterministic, no-agent part is Phase 2/3 (`run_comic.py`).
> **image_gen throttling:** a rate-limited bake stops cleanly with `fresh_run_required` — after cooldown launch a
> **fresh** run for the remaining panels, do **not** resume cached state. Args + caps (4/panel · 6/run,
> assembly): [`docs/spiral-runtime.md`](docs/spiral-runtime.md).

**Skills involved:** [`movie-pipeline`](skills/movie-pipeline/SKILL.md) (end-to-end) → [`comic-author`](skills/comic-author/SKILL.md) (Phase-1 orchestrator) → comic-intent-parser →
comic-style-bible-lock → comic-outline-creator → comic-storyboard-creator → comic-asset-ref-generator /
comic-asset-review-loop → comic-blueprint-author → comic-panel-prompt-builder → comic-json-compiler →
[`comic-director`](skills/comic-director/SKILL.md) (the spiral). Copy the author-node shapes from
[`examples/comic_min_author/`](examples/comic_min_author/).

🔄 **Human-in-the-loop:** intent + outline are **hard human gates** — your agent drafts + cross-model-reviews them
but never proceeds until you approve; a bake that won't converge flags the panel/storyboard for you, never
silently ships. **Prereqs:** a coding agent for Phase 1; **`codex` + `gemini` CLIs + headless Chrome** for Phase 2/3
(`python3 cli/preflight.py` to verify).

**B · See the reference movie — zero setup, no API**
```bash
python3 cli/validate_wiki.py examples/comic_m3_audit          # verify the shipped trace -> PASS (198 nodes, 26 edges)
python3 packages/viewer/build_comic.py examples/comic_m3_audit   # (re)build the single-file viewer from comic.json + panels
open  examples/comic_m3_audit/outputs/index.html
```
…or just open the hosted one: **https://wanshuiyin.github.io/ARIS-Movie-Director/comic/** — all **19 scenes / 24 frames**.

**C · Make a method figure — input: a brief → output: `figure.png`**
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

## How it works

### Movie pipeline — Phase-1 authoring (agent workflow) + Phase-2/3 spiral
Phase 1: your agent follows the `comic-author` skills to author `comic.json` + locked assets (path A above).
Phase 2/3, per panel — the **spiral engine** (`packages/core/spiral_engine.js` via a workflow runtime, **or** its
standalone subprocess port `run_comic.py`, no agent runtime — same result):

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

### Method-figure pipeline — one command (`run_spiral.py <brief>`)
`method_figure_brief.json` → Step-0 `compile_brief.py` (deterministic, fail-closed traceability) → a content-locked
`blueprint.json` → white-bg condition render → `gpt-image-2` bake → **Gemini + Codex blind-transcribe + a
deterministic `content_diff`** → retry re-asserting the locked labels → **Claude structural sign-off** → `figure.png`.

### Why the two gates differ (both correct, by design)
The **movie** `panel_gate` is a **3-reviewer** panel (CC *narrative* ‖ Gemini *visual* ‖ Codex *visual*) — a story
panel must land its beat AND be visually on-model. The **method-figure** panel is **Gemini + Codex
blind-transcribe + the deterministic `content_diff`**, with **Claude** the post-pass structural sign-off — a
figure has no "beat", so the bar is exact labels + clean layout, not narrative. Both obey the one rule:

> The gate is the point: a beautiful panel/figure with a wrong number does **not** pass. Faithfulness is a
> token-diff over reviewers who are never shown the expected values.

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
