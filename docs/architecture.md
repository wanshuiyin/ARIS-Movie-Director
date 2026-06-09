# ARIS-Movie 连环画 (Comic) — Unified Architecture v2

> **Single source of truth, consolidated 2026-06-09.** Supersedes the now-partially-stale
> `aris_movie/COMIC_PIVOT_DESIGN.md` (the original cross-model design — still valid for the
> spiral/gate/wiki spine, but its text-mode, story, and several mechanisms have been overtaken
> by what we proved by building). This doc folds in everything absorbed this session.

---

## 0. What changed since the original design (the deltas)

| Original design doc | v2 (proven by building) |
|---|---|
| `text_mode` locked = **html** (image draws no text) | **FULL-BAKE proven + chosen** for content panels: codex bakes the evidence diagram + correct CJK/EN dialogue in-world. html stays an option (bilingual toggle). Per-panel `text_mode` ∈ {baked, html, code}. |
| Story = dramatized "wiki rollback / K3→I-K3 invariant / Tok\|yo split" | **Accurate story = the VALSE-talk M3 audit-cascade**: schema-keyword-first +6.2 over random-mask → adversarial experiment-audit catches the eval's JSON **sanitizer** (auto-fills malformed keys before scoring) → honest raw `json.loads+jsonschema` re-eval → gap collapses to **+1.4** → **WARN_corrected** (effect real, scope narrowed, 诚实但不杀稿). Theme = **plausible unsupported success**, caught by cross-family audit. |
| (none) | **THE CORE TECHNIQUE — deterministic-SVG → codex bake → narrative figure** (§4). The biggest new capability; reusable beyond this comic. |
| (none) | **Two-world palette (B)**: real world = WARM, digital/ARIS world = DARK-cyber (§3). |
| Engine: rollback-to-PRIOR-panel | **Seed-anchored**: each panel independent → retry SAME panel, never roll back to a prior (which wiped good panels). Exhaustion → best-so-far flagged for human, continue. Throttle → stop clean + resumable (§7). |
| Gate: `max(artifact)` single-vote veto, fail-closed safezone | **Recalibrated**: artifact needs CORROBORATION (no lone pixel-purist veto), safezone if EITHER confirms, style/comp softened, ART_BIBLE allows background atmospheric gradients (§7). |
| (none) | **Rate-limit reality**: codex image_gen ~5-6 gens/window → pace, store+resume on throttle; Gemini-nano backend planned (§8). |

---

## 1. Why comic (not the Seedance video)

Cost: Seedance i2v ≈ 88 cr/gen, full film 2000+. Swap → **codex image_gen** of static panels (≈free within the ChatGPT plan). The deeper win is **control**: no temporal drift, no chain seams; and — new this session — **fine-grained deterministic content** via the SVG technique. The spiral (cross-model gate + wiki + retry) survives in shape — but **rollback-to-PRIOR-panel is GONE** (seed-anchored: retry-the-SAME-panel, never wipe a prior good panel; §7).

## 2. Narrative spine (the accurate research)

The film's dllm running example (Ruofeng's VALSE 2026 talk, M0→M5):
- **Method**: schema-keyword-first denoising for a ~200M DLLM → tree-shaped JSON. Unmask schema KEYS + braces FIRST, then values (vs random-mask / L2R-AR baselines). → values can't break the schema boundary.
- **M3 centerpiece (Audit Cascade Stage-1 = experiment-audit, adversarial Codex fresh thread)**: initial schema-aware **+6.2** over random-mask → audit catches the eval silently ran the pipeline **JSON sanitizer** (default-fills malformed keys before scoring → inflated) → honest re-eval (raw `json.loads`+`jsonschema`) → **+1.4** (the +4.8 = evaluator self-repair artifact) → **WARN_corrected**.
- **Characters**: blue **executor** = ran the experiment; green **reviewer** = the adversarial cross-family auditor. **#1 accuracy rule**: sanitizer (cheat) ≠ external jsonschema validator (honest metric) — never conflate.

## 3. Art direction (ART_BIBLE is the gate's convergence target)

`comic_kit/ART_BIBLE.md` is authoritative. Key:
- **Pixel-art chibi** v1; flat detailed pixel (not voxel); `image-rendering:pixelated` + integer scaling.
- **Identity lock**: `duo_canonical_ref_v001.png` injected on every panel; executor = blue `#1D4684`/brown hair/no beard; reviewer = green `#30582D`/dark hair/beard.
- **§0.5 Two-world palette (B)**: real world (bedroom/campus/lab/human) = **WARM** (Edison glow); digital ARIS world (wiki-void/terminal/diagrams/audit) = **DARK neon cyber**. Technical artifacts = dark "glowing screen objects" even in warm scenes. Cold/warm is by-design, not drift.
- **Text** (ART_BIBLE §6 + §5 below): per-panel `text_mode`; baked proven for content/audit panels, html for bilingual/simple.

## 4. ⭐ THE CORE TECHNIQUE — deterministic-SVG → codex bake → narrative panel

The method that makes content panels both PRECISE and RICH (see also memory `feedback-svg-to-codex-narrative-figure`):
1. Author the EXACT technical content (method diagram, JSON, numbers, code, labels) as a **deterministic SVG** → render to PNG (crisp, exact, editable). Generators live in `comic_kit/gen_*.py` (e.g. `gen_method_diagram.py`, `gen_sanitizer_diagram.py`).
2. Feed codex **≤2 `-i` refs**: (1) the content-SVG PNG = content authority, (2) `duo_canonical_ref.png` = identity lock. A 3rd ref dilutes (colors bleed into characters).
3. Prompt: the warm/dark scene + the chibi poses interacting with the content + (full-bake) the exact dialogue to bake.
4. codex **re-renders the content in-style** + bakes characters + (verified) CJK/EN bubbles, integrated, one shot.
- **Proven**: `probe/cal_S12_a01.png` (method panel, teaser/Fig-1 level), `probe/cal_S13_a01.png` (audit panel).
- **Accuracy discipline (this IS the talk's thesis).** Reconcile the two truths: **bubble-level dialogue** bakes reliably (CJK/EN verified) → trust it; **small-font evidence/numbers** can scramble (e.g. S12 random row showed founded=1603 under "pop") → must be item-verified. **MUST-MATCH fields (human/gate verify exact, every content panel):** every number (+6.2 / +1.4 / 13960000 / 1603), every JSON key (city/population/founded), method/function names (json_sanitizer / json.loads / jsonschema.validate), and verdict tokens (exact_parse FAIL/OK / WARN_corrected). If a must-match field is garbled → retry or composite the crisp SVG. A pretty-but-wrong figure = plausible unsupported success; the deterministic SVG (§4) is the precise authority, the bake is the narrative skin.

## 5. Text mode (per panel) — decision table

| Panel kind | `text_mode` | why |
|---|---|---|
| Content / audit beat (diagram + dialogue, max integration) | **baked** | codex bakes evidence + bubbles in-world, no seam |
| Normal dialogue / needs live zh⇄en toggle | **html** | reflow + free bilingual + a11y |
| A precise figure reused formally (paper/正式) | **code / the SVG itself** | exact, editable, audit-safe |

`comic.json defaults.text_mode` + per-panel override:
- **baked** (chosen for the audit-beat content panels): codex bakes dialogue + evidence in-world (max integration, no widget seam; proven CJK-clean). Cost: per-language regen, no live toggle, must verify.
- **html** (default for simple panels / bilingual needs): image textless, HTML bubbles into safe-zones; free zh/EN toggle + reflow + a11y.
- **code**: deterministic PIL/SVG-composited text (perfect, but flat).

## 6. Pipeline layers

```
ASSETS (movie-wiki/assets: duo_canonical, char/scene/prop refs, 24 SVG overlays)
  +  CONTENT SVGs (comic_kit/gen_*.py → assets_new/*.svg → PNG)        ← deterministic facts (§4)
        │  per panel: content-PNG + duo_canonical as -i refs
        ▼
CODEX PANEL-GEN (generatePanel: codex image_gen, ART_BIBLE-constrained, warm/dark per world)
        │  one panel at a time (NEVER batch)
        ▼
PANEL_GATE SPIRAL (CC narrative ‖ Gemini visual-CLI ‖ Codex visual-CLI → deterministic JS verdict)
        │  → WIKI active-memory (panel_attempt/review/decision/failure_mode)
        │  → keep / retry-SAME-panel(+repair invariant) / best-so-far→human / throttle→stop
        ▼
comic.json  (content-graph IR: pages + panels{image_path, text_mode, bubbles|baked, overlays, crop})
        │  inlined by build_comic.py (no runtime fetch)
        ▼
VIEWER (comic_kit/comic_template.html → comic/index.html: bilingual, flip+webtoon, pixel-fidelity)
        → GitHub Pages single file (clean PUBLIC artifact; dev stays in private aris_movie repo)
```

**Two SVG layers (don't confuse):** **content SVG** (`comic_kit/gen_*.py` → `assets_new/*.svg`) = the *fact-authority* fed to codex as a `-i` ref (§4); the **24 SVG overlays** (`movie-wiki/assets/overlays/`) = the *viewer/composition* layer (HTML-side data widgets / in-panel insets), used only when a panel is `text_mode:html`. **Output dirs:** codex panels → `panels/SXX_panel_aNN.png`; calibration bakes → `probe/`; content SVGs/PNGs → `assets_new/`; wiki nodes → `nodes/`; the IR → `comic.json`; built viewer → `comic/index.html`; render screenshots → `build/_renders/`.

**Reviewer/record contracts** (already implemented in the engine — see §7 / the script): each visual reviewer returns `VIS_SCHEMA` (identity/style/composition/artifact/safezone/stray scores), CC returns `CC_SCHEMA` (narrative/composition), the JS `panelVerdict` fuses them; wiki writes `panel_attempt` / `review×3` / `decision` (verdict + repair_instruction) / `failure_mode` (active + repair_pattern) nodes. `attempt` carries `{image_path, attempt_index, needs_human}`.

## 7. The engine (`workflows/scripts/aris-comic-spiral-engine.js`)

Forked from the video spiral, fixed + recalibrated this session:
- **Seed-anchored**: panels independent → on a non-keep verdict, retry the SAME panel with the repair invariant; never rollback-to-prior. Caps 4/panel. Exhaustion → push best-so-far flagged `needs_human` and CONTINUE (design R10). Throttle (`gen_failed_reason` matches rate/limit) → stop clean, resumable via `args.panelIds`.
- **panelVerdict (recalibrated)**: keep iff narr≥4 & identity≥4 & styleOK & compOK & !artifactBad & safezone & !strayText & disagree<2. artifactBad needs BOTH reviewers corroborate (no lone veto). safezone if EITHER confirms. style/comp soften to one-reviewer strictness. ART_BIBLE §3 allows background atmospheric gradients (the calibration root-fix).
- Preflight (stub eval) before every run.

## 8. Build/run workflow + rate-limit reality

- Content panel: write/edit `gen_<x>.py` → render SVG→PNG → bake via the §4 recipe → eyeball + (eventually) panel_gate → set `comic.json` image_path + text_mode → `build_comic.py` → render/open.
- **Rate limit**: codex image_gen ~5-6 gens/window then ~tens-of-min cooldown. PACE (one panel at a time, gate between). On throttle: the engine stops clean; resume with remaining `panelIds`.
- **Generator adapter contract** (so backends are swappable): a generator takes `{refs:[content_png, identity_png], prompt, panel_id}` → returns `{status, image_path, failure_reason, metadata}`. codex image_gen is impl #1. **Gemini-nano (planned)** = impl #2 (faster, different limit) once the user provides the API — must satisfy the same contract + pass the identity-lock gate.
- **Publish flow**: dev stays in the PRIVATE `aris_movie` repo. Release = copy the self-contained `comic/index.html` (+ a print PDF) into a small PUBLIC repo / the ARIS homepage GitHub Pages; never flip the private dev repo public (227M dead video + secrets-scan). Linked from the ARIS homepage.

## 9. Status (2026-06-09)

- ✅ P0 pipeline proven end-to-end (B08 page generated; engine fixed+recalibrated; viewer+IR+gate+wiki).
- ✅ Audit-beat redesign: S12 (method) + S13 (sanitizer audit) baked via §4. **Remaining: S14 (+6.2→+1.4 collapse), S15 (WARN_corrected)** → then comic.json + new B08 page render.
- ⏭ Then the other ~18 panels (rate-limit-paced or Gemini backend); the bedroom/campus warm panels; full assembly; ship a clean public GitHub Pages artifact.

## 10. Accuracy discipline (non-negotiable, = the film's own thesis)

Every baked number/term in a content panel must be **human/gate-verified** against the real research before it counts as final. A beautiful panel that misstates a number is exactly the *plausible unsupported success* this film is about. The deterministic SVG (§4) is the precise authority; the bake is the narrative skin.
