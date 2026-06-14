---
name: comic-blind-comparison-review
description: Phase-1 comic-author step (post-final eval) — a DOUBLE-BLIND A/B of two FINAL whole comics: our cross-model-audited progressive render (the comic-author + comic-director output) vs a naive single-shot baseline. A single sealed coin-flip hides which is which; two cross-model reviewers (Codex + Gemini) score both on a fixed rubric reading only a SHARED blind spec (intent + ART_BIBLE); only AFTER both reviews land do we unseal, re-label, and write a Chinese comparison.md + the A/B verdict nodes. editability/traceability is the structural wedge that can win even when the baseline looks prettier. Use when the user says "和 baseline 比", "blind comparison", "A/B 评测", "对比 baseline", "盲评", "whole-comic vs one-shot", or a finished comic needs a baseline-relative honest verdict. NOT an authoring skill and NOT the per-panel panel_gate / assembly_gate — those run DURING production; this runs AFTER, on two complete works.
---

# comic-blind-comparison-review — Double-Blind A/B of Two Finished Comics (Phase 1, step S12, post-final)

The **"vs baseline" capability** the comic side otherwise lacks. The per-panel
[`comic-director`](../comic-director/SKILL.md) `panel_gate` and the cross-panel `assembly_gate` operate
**during** production on single units; this skill operates **after** production, on two **complete works** —
our cross-model-audited progressive comic (authored by the [`comic-author`](../comic-author/SKILL.md) suite,
baked by [`comic-director`](../comic-director/SKILL.md)) **vs a naive single-prompt one-shot baseline** — and
proves the spiral pipeline beats the one-shot, **under a blind so neither reviewer can favor the home team**.
It is a direct, faithful port of aris_movie's `blind-comparison-review` from video to a whole-comic A/B
(`outputs/aris_movie_progressive.mp4` vs `outputs/baseline_sd2_naive.mp4` → two rendered comic page sets), and
it is an **evaluation** skill, not an authoring one: it never edits a comic, it judges two finished ones.

> **Cardinal lesson baked in as a gate, not prose:** *the order of operations IS the integrity guarantee.*
> A single coin-flip seals `.ab_mapping.json` and `chmod 600`s it **before any reviewer is invoked**; the
> seal's mtime MUST precede both reviews; from seal-time until UNSEAL the orchestrator (Claude) may not read
> or quote the mapping; **any home-team token in a reviewer prompt is a HARD-ABORT, not a warning.** If the
> orchestrator reads the mapping before both reviews land, it may subconsciously phrase the synthesis to favor
> the home team — so the timestamp ordering is the audit trail, and "blinding integrity" is **REPORTED, never
> assumed**.

```text
  progressive comic  ┐                                            ┌─▶ comparison.md (Chinese deliverable)
  (our audited)      ├─▶ ⓪ SEAL .ab_mapping.json (1 coin-flip,    │
  baseline comic     ┘       chmod 600, mtime BEFORE any reviewer) │
  (naive one-shot)   │            ▼                                │
                     │      ① STAGE pages → A/ and B/ (sealed ids) │
                     │            ▼                                │
                     │      ② CODEX blind review (xhigh, RO)  ─────┤  (no home-team token; reads SHARED
                     │            ▼                                │   blind spec = intent + ART_BIBLE only)
                     │      ③ GEMINI blind review (per-page + ─────┤
                     │            synthesis, auto-gemini-3)        │
                     │            ▼                                │
                     └─▶  ④ UNSEAL (verify seal_ts < BOTH reviews) ┘
                                ▼
                          ⑤ WRITE comparison.md  +  ⑥ WIKI A/B verdict nodes + edges
```

## Constants
- **ARTIFACTS** = two FINAL whole comics. `progressive` = our spiral output (`comic-director`'s baked frames +
  the single-file viewer, or `comic.json` → render); `baseline` = a naive single-prompt one-shot comic of the
  SAME story+style (no spiral, no per-panel gate). For the worked example the contract boundary is
  [`examples/comic_m3_audit/comic.json`](../../examples/comic_m3_audit/comic.json) (the structured-IR artifact
  under test) + [`examples/comic_m3_audit/ART_BIBLE.md`](../../examples/comic_m3_audit/ART_BIBLE.md) (the
  SHARED blind spec both reviewers read).
- **MAPPING_FILE** = `outputs/.ab_mapping.json` — the seal, `chmod 600`. Written by ⓪ **before** any reviewer.
- **REVIEWERS (two families, the load-bearing diversity)** = Codex `gpt-5.5` `model_reasoning_effort: xhigh`,
  `sandbox: "read-only"` ‖ Gemini `auto-gemini-3` (per-page `mcp__gemini__analyzeFile` + a text-only
  `mcp__gemini-cli__ask-gemini` synthesis). Never downgrade the tier
  ([`reviewer-routing`](../../protocols/reviewer-routing.md)). Optionally fold in the project's CC-narrative
  vote to make it the same tri-reviewer panel as `panel_gate` (CC ‖ Gemini ‖ Codex) — see *Adaptation*.
- **BLIND TOKENS** = the only identifiers a reviewer ever sees are `comic_A` / `comic_B` (and per-page
  `A_p01.png` / `B_p01.png`). **Banned from every reviewer prompt:** `progressive`, `baseline`, `ARIS`,
  `ARIS-Movie`, `SD2`, `naive`, `one-shot`, `spiral`, `our system`, `system under test`, and any rhetorical
  "show that A is better" framing.
- **A/B RUBRIC DIMENSIONS** (comparative, each scored **0–5 for `comic_A` AND `comic_B`**) =
  `story_comprehension, visual_consistency, overlay_readability, editability_traceability, reproducibility,
  polish`. **`editability_traceability` is the structural wedge** (see the gate below).
- **NO PASS/FAIL THRESHOLD** — this is comparative A-vs-B, not a gate. Each reviewer emits
  `overall_winner ∈ {comic_A, comic_B, tie}` + `confidence 0.0–1.0`; the consensus is
  `∈ {progressive, baseline, tie, disagree}`.
- **OUTPUTS** = `outputs/.ab_mapping.json` (sealed, 600); `outputs/blind_review_codex_raw.json`;
  `outputs/blind_review_gemini_raw.json` (+ `outputs/gemini_perpage.json`); `comparison.md` (the Chinese human
  deliverable, per [`output-language`](../../protocols/output-language.md)); the wiki A/B verdict nodes + edges
  (§ below). Stdout JSON `{comparison_decision_id, consensus_winner, codex_winner, gemini_winner,
  blinding_integrity, comparison_md_path}`.

## Input contract — two FINISHED comics + ONE shared blind spec
This skill is **pure evaluation**; it never authors, edits, or re-bakes a comic.
- **Two final artifacts, both complete.** Refuse (HALT) if either path is missing, if either comic is not a
  *whole* finished work (a half-baked spiral run is not a fair A/B subject), or if both paths are the same
  artifact. The progressive comic must be the **shippable** output (nothing `escalated`/`needs_human`/`flagged`
  per `comic-director`'s run-report); a non-shippable progressive comic is not eligible for the head-to-head.
- **One SHARED blind spec read by BOTH reviewers** — the story intent (the comic's logline/script, e.g. the
  `intent_spec`'s `logline` + `narrative_beats`) + the style bible (`ART_BIBLE.md`). The spec is the
  identity-stripped ground truth ("what this comic is supposed to be"); it must NOT name which artifact is the
  home team. This is the comic mapping of the video skill's `MOVIE_BRIEF.md` + `style_bible.md`.
- **Reviewer-independence ≠ reviewer-blinding** — BOTH apply (the lesson that names this skill). *Independence*
  = the reviewer sees no Claude prose (the `panel_gate` rule). *Blinding* = the reviewer sees no method
  IDENTITY of which artifact is the home team. The per-panel gate already does independence; this adds the
  second axis (identity-blind) for the whole-artifact A/B.

## Procedure (followable, fail-closed, in strict order)

### ⓪ SEAL the A/B mapping (MUST complete BEFORE any reviewer)
**Inputs (skill args):** `PROG_PATH` = the progressive comic dir/artifact, `BASE_PATH` = the baseline comic
dir/artifact, `PROJECT_DIR` = the project root the wiki lives under (where `comic.json` + `wiki/` sit, e.g.
`examples/comic_m3_audit`). **Bind and FAIL FAST first** (the "fail fast if either missing or identical" the
prose promises must be ACTUAL CODE — the seal is the load-bearing integrity step and must not crash). Then a
**single coin-flip** and write the seal — its mtime MUST precede the first reviewer call:
```bash
# --- bind the three skill args explicitly (these are THIS skill's inputs) ---
PROG_PATH="$1"; BASE_PATH="$2"; PROJECT_DIR="${3:-.}"
# --- fail fast: non-empty, both exist, and the two artifacts differ (prose promise → real code) ---
[ -n "$PROG_PATH" ] && [ -n "$BASE_PATH" ] || { echo "HALT: PROG_PATH and BASE_PATH are required args"; exit 2; }
[ -e "$PROG_PATH" ] || { echo "HALT: progressive artifact not found: $PROG_PATH"; exit 2; }
[ -e "$BASE_PATH" ] || { echo "HALT: baseline artifact not found: $BASE_PATH"; exit 2; }
[ "$(cd "$(dirname "$PROG_PATH")" && pwd)/$(basename "$PROG_PATH")" != \
  "$(cd "$(dirname "$BASE_PATH")" && pwd)/$(basename "$BASE_PATH")" ] \
  || { echo "HALT: the two A/B artifacts are the SAME path — not a fair head-to-head"; exit 2; }
mkdir -p outputs
if [ $(( $(od -An -N2 -tu2 /dev/urandom) % 2 )) -eq 0 ]; then PROG=A; BASE=B; else PROG=B; BASE=A; fi
# pass the two real paths as argv (NOT os.environ — they were never exported) so the heredoc can never KeyError
python3 - "$PROG" "$BASE" "$PROG_PATH" "$BASE_PATH" <<'PY'
import json, sys, datetime, os
prog, base, prog_path, base_path = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
seal = {
  "sealed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
  "comic_A": os.path.abspath(prog_path if prog=="A" else base_path),
  "comic_B": os.path.abspath(base_path if prog=="A" else prog_path),
  "progressive_label": prog, "baseline_label": base,
}
json.dump(seal, open("outputs/.ab_mapping.json","w"), ensure_ascii=False, indent=2)
PY
chmod 600 outputs/.ab_mapping.json
```
(The `outputs/.ab_mapping.json` seal stores `os.path.abspath(...)` and that is FINE — `cli/validate_wiki.py`
only scans `wiki/nodes/*.json`, never the seal file. The abs-path discipline applies to the WIKI NODE payloads
written in ⑥, not to this seal.) From here **until ④ UNSEAL the orchestrator MUST NOT read or quote
`outputs/.ab_mapping.json`.** Reviewers see
only `comic_A` / `comic_B`. (Procedural, not a technical guarantee — but it produces a paper trail sufficient
for a research artefact, and that trail IS the integrity claim.)

### ① STAGE pages into A/ and B/ (the video frame-extraction collapses)
The video skill extracted ~10 frames/video into `comparison-frames/{A,B}/`; **for comics this collapses — the
comic pages ARE the discrete units**, deterministic renders, so no extraction or regeneration is needed. Stage
each comic's **already-rendered** page PNGs into the sealed letter-dirs with identity-free labels
(`A_pNN.png` / `B_pNN.png`) so reviewers cite by page, never by home-team identity. The premise is
*deterministic pages, don't regenerate* — so this skill **stages existing PNGs and never bakes**. Use the
deterministic recipe for whichever input form each side ships as (apply it independently to `comic_A`'s source
and `comic_B`'s source — neither side knows which is which):

**Form (a) — a `comic.json` + WHOLE-PAGE renders (the structured-IR case).** The canonical page order is
`comic.json` `pages[]` (a LIST, each page = a discrete unit). Stage one **page-level** render per page
(`page.page_image` / `page.rendered_path` — the whole page as the reader sees it: panels + HTML bubbles +
narration), **never** a raw per-panel `panel_attempt.image_path` (that drops the bubbles/narration and, on a
multi-panel page, the other panels — see the code's HALT). Copy into the sealed dir as one PNG per page,
renumbered `A_pNN.png`/`B_pNN.png` in `pages[]` order (**never re-bake**):
```bash
mkdir -p outputs/comparison-pages/A outputs/comparison-pages/B
stage() {  # $1=comic.json FILE or a dir containing one   $2=letter (A|B)
  python3 - "$1" "$2" <<'PY'
import json, sys, shutil, os
arg, letter = sys.argv[1], sys.argv[2]
# NORMALIZE the artifact path: accept a comic.json file OR a dir holding one (never assume it's a dir).
cpath = arg if (os.path.isfile(arg) and arg.endswith(".json")) else os.path.join(arg, "comic.json")
if not os.path.isfile(cpath): sys.exit(f"HALT: no comic.json at {arg}")
cdir = os.path.dirname(os.path.abspath(cpath))
cj = json.load(open(cpath))
panels = cj["panels"]                 # dict {"S01": {...}, ...}
pages  = cj.get("pages") or []        # list, the canonical page ORDER; each has panel_ids
if not pages: sys.exit(f"HALT: {cpath} has no pages[] — cannot determine page order")
out = os.path.join("outputs/comparison-pages", letter)
def resolve(rel): return rel if os.path.isabs(rel) else os.path.join(cdir, rel)
n = 0
for pg in pages:                      # pages[] order IS the comic order (don't sort the dict keys)
    pids = pg.get("panel_ids") or []
    if not pids: sys.exit(f"HALT: page {pg.get('id')} has no panel_ids")
    # A fair A/B compares WHOLE PAGES (each panel + its HTML bubbles/narration as the reader sees it). EVERY
    # page needs a page-level render — a raw per-panel PNG is NOT a page (it drops bubbles/narration, and on a
    # multi-panel page the other panels). No single-panel shortcut: even a 1-panel page is rendered as a page.
    src = pg.get("page_image") or pg.get("rendered_path")
    if not src:
        sys.exit(f"HALT: page {pg.get('id')} has no page-level render (page_image/rendered_path) — rasterize the "
                 f"viewer to whole-page PNGs (Form b) before A/B; a per-panel PNG is not a page (no regen here)")
    src = resolve(src)
    if not os.path.isfile(src): sys.exit(f"HALT: missing rendered page image {src} for page {pg.get('id')}")
    n += 1; shutil.copyfile(src, os.path.join(out, f"{letter}_p{n:02d}.png"))
print(f"{letter}: staged {n} pages")
PY
}
# DO NOT call stage() blindly — it is Form-(a) ONLY (a comic.json with page-level renders). Dispatch each
# artifact by TYPE via stage_any() (defined after Form (b) below): comic.json → stage(); .html viewer →
# rasterize_viewer(). Both route by the SEALED coin-flip letter ($PROG/$BASE from ⓪), never by reading the seal.
```
**(Sealing caveat — keep the blind intact.)** The two `stage` calls above route each artifact to its **sealed**
letter via the coin-flip variables `$PROG`/`$BASE` from ⓪ — **not** by reading `comic_A`/`comic_B` from the seal
file, which is FORBIDDEN until ④. The orchestrator knows the letters (it flipped the coin) without ever opening
the mapping, so the blind holds; the reviewer still only ever sees `A_*`/`B_*` filenames.

**Form (b) — a single-file HTML viewer with NO pre-rendered PNGs (the common comic-director ship form).** This
skill does **not** own a bake; it is fail-closed by design. Prefer pre-rendered PNGs; if absent, the caller must
rasterize first via the repo's own deterministic page renderer, then re-invoke this skill pointing at the PNG
dir. If you must rasterize inline, the ONLY sanctioned path is a headless-Chromium screenshot at a FIXED
width/DPI (deterministic), one PNG per page, e.g.:
```bash
# headless rasterize the single-file viewer → one PNG per page (deterministic fixed window so both sides are
# pixel-comparable). The viewer's per-page anchor is `?p=N` (the comic-director viewer convention).
rasterize_viewer() {  # $1=viewer .html   $2=letter   $3=NPAGES (from comic.json pages[])
  CHROME="$(command -v chromium || command -v google-chrome || command -v chromium-browser || true)"
  [ -n "$CHROME" ] || { echo "HALT: no headless chromium to rasterize the viewer — supply pre-rendered page PNGs instead"; exit 2; }
  local v abs; abs="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
  mkdir -p "outputs/comparison-pages/$2"
  for i in $(seq 1 "$3"); do
    pp=$(printf "%02d" "$i")
    "$CHROME" --headless --disable-gpu --window-size=1200,1600 \
      --screenshot="outputs/comparison-pages/$2/$2_p${pp}.png" "file://${abs}?p=${i}" >/dev/null 2>&1 \
      || { echo "HALT: screenshot of page $i failed"; exit 2; }
  done
  echo "$2: rasterized $3 pages from the viewer"
}
# e.g.  rasterize_viewer "$PROG_PATH" "$PROG" "$NPAGES"   (NPAGES = len(comic.json pages[]))
```
If neither pre-rendered PNGs nor a headless renderer is available → **HALT** with that message; never feed the
reviewers a partial or wrong-DPI rasterize (a corrupted page set makes the A/B score garbage).

**Stage dispatch — the actual control flow (picks the form per artifact; never calls `stage()` blindly).**
```bash
stage_any() {  # $1=artifact (a DIR of pre-rendered *_pNN.png / a comic.json / a single-file .html viewer)   $2=sealed letter
  case "$1" in
    *.html)  # the SINGLE-FILE viewer (the common ship form, NO sibling comic.json): rasterize whole-page PNGs.
             # derive NPAGES from the viewer's EMBEDDED JSON island (the build inlines comic.json into a <script>).
      NP=$(python3 - "$1" <<'PY'
import json, re, sys
html = open(sys.argv[1], encoding="utf-8").read()
n = ""
for blob in re.findall(r'<script[^>]*>\s*(\{.*?\})\s*</script>', html, re.S):   # the inlined comic-IR island
    try:
        d = json.loads(blob)
        if isinstance(d.get("pages"), list): n = len(d["pages"]); break
    except Exception:
        pass
print(n)
PY
)
      [ -n "$NP" ] || { echo "HALT: cannot read page count from the viewer's embedded JSON island in $1"; exit 2; } ;
      rasterize_viewer "$1" "$2" "$NP" ;;
    *)
      if [ -d "$1" ] && ls "$1"/*_p[0-9]*.png >/dev/null 2>&1; then   # a DIR of pre-rendered whole-page PNGs
        mkdir -p "outputs/comparison-pages/$2"; i=0
        for f in $(ls "$1"/*_p[0-9]*.png | sort); do i=$((i+1)); cp "$f" "outputs/comparison-pages/$2/$2_p$(printf '%02d' "$i").png"; done
        echo "$2: staged $i pre-rendered page PNGs"
      else
        stage "$1" "$2"   # a comic.json file or a project dir — stage() normalizes + requires page-level renders
      fi ;;
  esac
}
stage_any "$PROG_PATH" "$PROG"   # route by the SEALED letter; no read of the seal file → blind holds until ④
stage_any "$BASE_PATH" "$BASE"
```

**Page-count parity gate (fail-closed).** After staging both sides, assert A and B staged the **same number of
pages** — an unequal A/B is not a fair head-to-head:
```bash
nA=$(ls outputs/comparison-pages/A/*.png 2>/dev/null | wc -l | tr -d ' ')
nB=$(ls outputs/comparison-pages/B/*.png 2>/dev/null | wc -l | tr -d ' ')
[ "$nA" -gt 0 ] && [ "$nA" = "$nB" ] || { echo "HALT: page-count parity failed (A=$nA B=$nB) — not a fair A/B"; exit 2; }
```
Page filenames embed only the sealed letter + a page index (`A_p03.png`) so reviewers cite by page, never by
home-team identity.

### ② CODEX blind review (read-only, xhigh)
A **fresh** `mcp__codex__codex` call (NOT `codex-reply`), `config {"model_reasoning_effort":"xhigh"}`,
`sandbox: "read-only"`. It sees the two page dirs (`comparison-pages/A`, `comparison-pages/B`) + the SHARED
blind spec (the identity-stripped intent + `ART_BIBLE.md`). Scrub the prompt with the **banned-token scan**
(`Constants`) BEFORE submission. The prompt asks Codex to read the pages itself and score **each comic 0–5 on
every A/B rubric dimension**, cite page filenames as evidence, and output **JSON only**. Save verbatim to
`outputs/blind_review_codex_raw.json`. Required JSON shape:
```json
{"comic_A": {"<dim>": {"score": 0-5, "evidence": "...cites A_p0X.png..."}, ...},
 "comic_B": {"<dim>": {"score": 0-5, "evidence": "...cites B_p0X.png..."}, ...},
 "overall_winner": "comic_A|comic_B|tie", "confidence": 0.0-1.0, "rationale": "..."}
```
If Codex returns non-JSON → retry **once**, stricter; still non-JSON → write a `{"parse_failed": true}` stub
and continue **Gemini-only**, noting the degradation in `comparison.md`.

### ③ GEMINI blind review (independent, same blind rules)
**3.1 per-page** — `mcp__gemini__analyzeFile`, `model auto-gemini-3`, **one call per image** (every page in A/
and B/), each page NOT seeing the other comic. Per-page JSON
`{label, page_filename, character_appearance ≤150, scene_signature ≤80, style_features ≤80,
artifact_severity_0_to_5 (int, 0=clean 5=catastrophic), notable_anomalies[]}`; persist to
`outputs/gemini_perpage.json`.
**3.2 synthesis** — `mcp__gemini-cli__ask-gemini` (text-only), fed both per-page observation lists + the blind
spec summaries (≤1000 chars each), scoring the same 0–5 A/B rubric, JSON only. Save verbatim to
`outputs/blind_review_gemini_raw.json`. Gemini is always `auto-gemini-3`. Fail fast if fewer than the staged
pages succeed per comic (the video floor was <6 frames/video → abort; for comics use "every staged page must
return, else re-run that page once then abort").

### ④ UNSEAL — only NOW read the mapping
Read `outputs/.ab_mapping.json` for the first time. **Verify the seal predates BOTH reviews** (its mtime is
older than both raw review files):
```bash
SEAL=$(stat -f %m outputs/.ab_mapping.json)
CODEX=$(stat -f %m outputs/blind_review_codex_raw.json)
GEM=$(stat -f %m outputs/blind_review_gemini_raw.json)
[ "$SEAL" -lt "$CODEX" ] && [ "$SEAL" -lt "$GEM" ] && echo "intact" || echo "compromised"
```
If out of order → `blinding_integrity = "compromised"`: still produce `comparison.md`, but **flag it
prominently, never silently elide.** Re-label `comic_A`/`comic_B` back to `progressive`/`baseline` in the
PARSED reviews; keep `_A`/`_B` in the RAW files for audit (never edit a raw file after it is written).

### ⑤ WRITE comparison.md (Chinese — per output-language)
Six fixed sections, in Chinese:
1. **执行裁定 / Executive verdict** — each reviewer's winner + confidence; the `consensus`.
2. **逐维度评分表 / Per-dimension table** — `维度 | Progressive (Codex / Gemini) | Baseline (Codex / Gemini) | Δ`
   across all six A/B dimensions.
3. **证据 / Evidence** — verbatim per-dimension evidence + page citations (`A_p0X.png` re-labeled to which
   artifact it actually was, after unseal).
4. **可编辑性 / 架构差异表 / Editability table** — the wedge made concrete (single-unit regen cost, failure
   localizability via wiki edges, minimum human-patch unit, audit record). See the worked-example table below.
5. **盲评审计 / Blinding audit** — mapping path, seal→first-review→last-review time window, leakage yes/no,
   `blinding_integrity`.
6. **结论 / Conclusion** — 3–5 sentences, **honestly recording any dimension the baseline won** (hiding it
   defeats the cross-model adversarial check).

### ⑥ WIKI — the A/B verdict as schema-valid nodes + edges
Write the post-final A/B record per `schemas/node_schema.json` (§ below), append the edges, and print the
stdout JSON. The reviewers (different model families) — never this orchestrator — produce the verdict; the
orchestrator only seals, stages, unseals, and records ([`acceptance-gate`](../../protocols/acceptance-gate.md):
the loop drives, it cannot acquit).

**Resolve a REAL `target_node_id` first (no dangling edges).** The slim `node_schema.json` (v3.0) has **no
whole-comic node_type and no top-level `comic.json.wiki_node_id`** — so "the progressive comic's anchor node"
does **not** exist by default and an edge to it would dangle (`cli/validate_wiki.py` resolves an endpoint ONLY
to a wiki `node_id` ∪ a `comic.json panels[*].wiki_node_id`; an unresolved `dst` is a hard FAIL). The A/B record
MUST point `target_node_id` at an endpoint that already resolves. Pick, in priority order:
1. **A caller-supplied AUTHOR anchor** — if the project has an `intent_spec` node (`node_id` `intent:<slug>`) or
   an `outline_spec` node (`node_id` `outline:<slug>`) for the progressive comic, the caller passes that node_id
   as `TARGET_NODE_ID` and the A/B nodes point there
   (this is the cleanest "the whole comic" anchor; it must be a real node in `wiki/nodes/`).
2. **Else, the progressive comic's FIRST panel anchor** — a `panel:<slug>` that exists as a
   `comic.json panels[*].wiki_node_id` (e.g. the worked example has `panel:s01_aris_comic_v1`). This is the
   pragmatic fallback the slim schema supports today: it resolves via the comic.json panel-anchor union, so the
   edges validate. Record in the decision payload that the anchor is the first-panel proxy (the A/B is about the
   whole comic; the panel is just the schema-valid attachment point).
Whichever you choose, **the chosen id MUST already be a resolvable endpoint** — verify with
`python3 cli/validate_wiki.py <PROJECT_DIR>` BEFORE declaring done; if it doesn't resolve, the skill HALTs
rather than write a dangling edge.

## EXACT gate (A/B rubric) — dimensions, scoring, the wedge, vetoes
Ported from the aris_movie `blind-comparison-review` rubric, adapted from video to comic (the video skill's
`narration_sync` dimension is **dropped** and folded into `overlay_readability` = caption/bubble↔panel
reading-order alignment, which the `assembly_gate` already scores). Each reviewer scores **each comic 0–5 on
all six dimensions** — there is **no numeric pass threshold**; the verdict is the comparative `overall_winner`
+ `confidence`, and the consensus across the two families.

- **`story_comprehension`** — can the reader follow the through-line end to end (the comic's logline lands)
  from the pages alone? (video: scene_jumps coherent vs abrupt unexplained jumps.)
- **`visual_consistency`** — character identity (face/clothes/age) + palette/render stable across pages vs
  drifting. **Design-aware:** the two-world warm/dark split is *by-design, not drift* (ART_BIBLE §0.5); a
  reviewer must only flag *miscolored* worlds, never the split itself. (video: character_consistency +
  style_drift.)
- **`overlay_readability`** — bubbles/captions legible, correctly ordered, aligned to the right panel; no
  garble; bilingual text fits. (replaces the video `narration_sync` dimension.)
- **`editability_traceability`** — **THE STRUCTURAL WEDGE.** Could a human editor patch a bad page *without a
  full re-gen*, and is each failure *localizable*? 5 = a single panel + its local prompt is the minimum patch
  unit and every panel traces to its `panel_attempt`/`review`/`decision`/`failure_mode` wiki nodes; 0 = the
  whole comic is one indivisible bake with no trace, so any defect forces a total re-gen. **This is where the
  pipeline's contribution shows even when the baseline's one-shot output is visually strong** — it is an
  architectural FACT (wiki-backed traceability), not a pixel measurement, so it can WIN the A/B even while the
  baseline ties or beats on `polish`. (video: editability_proxy.)
- **`reproducibility`** — can the artifact be re-derived? (re-run the `comic.json` + content-SVG blueprints +
  the audited spiral → the same comic) vs a one-shot whose exact output is unrecoverable. (video: deterministic
  re-render of cached frames.)
- **`polish`** — raw aesthetic finish / artifact floor (the dimension the naive one-shot can plausibly win).
  (video: artifact_floor / artifact_severity.)

**Veto / hard-abort rules (the load-bearing rigor — abort beats taint):**
1. **`MAPPING_FILE` referenced in ANY reviewer prompt → HARD-ABORT** `"Blinding compromised — fix prompt
   template and re-run"`. Better to abort than ship a tainted A/B.
2. **Any home-team token** (`progressive`/`baseline`/`ARIS`/`SD2`/`naive`/`one-shot`/`spiral`/`our system`/
   `system under test`, or a rhetorical "show that A is better") in a reviewer prompt → the prompt is
   **REJECTED before submission** by the banned-token scan.
3. **Reviewer raw files predate `MAPPING_FILE`** → `blinding_integrity = "compromised"`, flag prominently in
   `comparison.md`, **never silently elide**.
4. **Codex non-JSON** → retry once stricter; else `{"parse_failed": true}` stub + continue Gemini-only, noted
   in the md.
5. **Fewer than the staged pages return from a reviewer** → re-run the missing page once, then **fail fast**.

**Invariants (REPORTED, not assumed):** seal written before any reviewer AND `seal_ts < both review-completion
ts`; no home-team token in any reviewer prompt; Codex always `xhigh`, Gemini always `auto-gemini-3`; raw
responses persisted verbatim, never edited after writing; the two reviewers are different families (agreement
is then non-trivial signal — `disagree` is a real finding, not noise to reconcile).

## Two engine contracts (fail-closed) — why a fair A/B is even possible
This skill judges finished comics, but the *reason the progressive side can be re-derived and a baked panel
audited* is the same two contracts the upstream authoring + spiral enforce — name them so a reviewer of THIS
skill knows what "reproducibility" and "editability" are grounded in:
1. **Every panel needs a `condition.content_svg`** — the progressive comic is reproducible precisely because
   each panel was baked from a deterministic SVG blueprint (`comic.json` panels carry
   `condition.content_svg`, e.g. `assets/s01_ddl_anchor_v1.svg`); the engine refuses `content_svg: null`. A
   naive one-shot comic has no such blueprint, which is *why* it scores low on `reproducibility`.
2. **A baked figure-panel needs `expected_literals`** — every baked panel declares its salient ASCII tokens
   (`comic.json`'s `condition.expected_literals`, e.g. `["DDL","T-24:00:00"]`, `["+6.2"]`), which the spiral's
   double-blind token-diff verified during production; a one-shot bake has no audited literals, which is *why*
   its numbers are unverifiable and its `editability_traceability` is 0. Do **not** re-run those gates here —
   this skill only *credits* the progressive side for having honored them, via the editability table.

## Node it reads / writes (`schemas/node_schema.json`)
> **Schema note (read this — it is the orphan-panel-class discipline).** The aris_movie source describes a
> single rich `comparison` node with `baseline_for` / `compared_against` edges. The SLIM comic
> `node_schema.json` (v3.0) has **no `comparison` node_type and no `baseline_for`/`compared_against` edge
> types**; the canonical edge form is **`{src, dst, type}`** (NEVER `from`/`to`/`edge_type`) with `type ∈
> {attempt_of, reviews, decides, failure_of, rollback_of, supersedes}`. So this post-final A/B is recorded
> with the schema's existing verdict vocabulary: **two `review` nodes** (one per reviewer) **+ one `decision`
> node** (the consensus). The rich aris_movie `comparison` payload (per-dim scores, blinding audit) is carried
> as the decision node's payload — the schema is `additionalProperties: true`, so extra fields validate.

**Reads** — two finished comics (the progressive `comic.json` / rendered pages + the baseline rendered pages)
and the SHARED blind spec (the `intent_spec`'s `logline`/`narrative_beats` + `ART_BIBLE.md`). It does **not**
mutate any upstream authoring node.

**Writes** (status `complete` for the reviews, `final` for the decision — the runtime canon). The exact
`PAYLOAD_REQUIRED` from `cli/validate_wiki.py` is **`review` → `["target_node_id","reviewer","gate_kind"]`** and
**`decision` → `["target_node_id","verdict","gate_kind"]`**; `node_id` must match the schema pattern
`^(…|review|decision|…):[a-z0-9_-]+$` (lowercase + `_`/`-` only — `cmp_…` is fine, `<YYYYMMDD>` is digits):
- **`review`** × 2 (`node_id` `review:cmp_<reviewer>_<YYYYMMDD>`) — payload **required** (all three): `target_node_id`
  (the resolved anchor from ⑥ — the caller's `intent_spec`/`outline_spec` id, or the first-panel proxy
  `panel:<slug>`; NEVER an id that doesn't resolve), `reviewer` (`codex` | `gemini`), `gate_kind`
  (`"blind_comparison"`). Recommended optional fields (validate under `additionalProperties`): `raw_path`
  (the verbatim `blind_review_*_raw.json`, **project-RELATIVE** — see the path rule below), `winner`
  (`progressive`|`baseline`|`tie`, **after unseal**), `confidence`, `per_dim_scores` (the unblinded 0–5
  per-dimension scores for both artifacts). The **raw** reviews live in files; the node only summarizes (no
  separate "review-node per dimension").
- **`decision`** × 1 (`node_id` `decision:cmp_progressive_vs_baseline_<YYYYMMDD>`) — payload **required** (all
  three): `target_node_id` (the SAME resolved anchor), `verdict` (the consensus
  `"progressive"|"baseline"|"tie"|"disagree"`), `gate_kind` (`"blind_comparison"`). Recommended optional:
  `progressive_path`, `baseline_path`, `comparison_md_path` (**all project-RELATIVE**, see below), `codex_winner`,
  `gemini_winner`, `anchor_kind` (`"author"` | `"first_panel_proxy"` — record which ⑥ option was used),
  `blinding_audit{sealed_at, first_review_started, last_review_completed, integrity, leakage_reason}`. This is
  the single authoritative A/B record (the aris_movie `comparison` node's role).

> **Path fields MUST be project-relative (release-gate rule).** `cli/validate_wiki.py` runs `abs_path_leaks()`
> over EVERY `wiki/nodes/*.json` payload and **hard-fails (`sys.exit 1`) on any string containing `/Users/` or
> `/home/`**. The only in-skill source of these paths is the seal, which stored them via `os.path.abspath(...)`
> — so before writing the nodes you MUST relativize: `progressive_path`, `baseline_path`, `comparison_md_path`,
> and any `raw_path` = `os.path.relpath(p, PROJECT_DIR)` (or just the `outputs/…` tail). Add a one-line guard
> mirroring the validator before writing each node — fail fast rather than emit an invalid node:
> ```python
> import json
> for s in (json.dumps(review_payload), json.dumps(decision_payload)):
>     assert "/Users/" not in s and "/home/" not in s, "HALT: payload has an absolute path; relativize before writing"
> ```
> (The `outputs/.ab_mapping.json` seal itself keeps `os.path.abspath` and is fine — the validator never scans it,
> only `wiki/nodes/`.)

**Edges** (canonical `{src, dst, type}` only; `type` ∈ `validate_wiki.py` `EDGE_TYPES`). The `dst` is the
**resolved `target_node_id`** from ⑥ (the caller's `intent_spec`/`outline_spec` id, or the first-panel proxy
`panel:<slug>` — an id that already resolves; **never the literal string `<progressive anchor>`**):
`review:cmp_codex_… --reviews--> <target_node_id>` and `review:cmp_gemini_… --reviews--> <target_node_id>` (each
with the optional `reviewer` + `verdict` edge fields); `decision:cmp_… --decides--> <target_node_id>` (with the
optional `verdict` field). `reviews`/`decides` are both legal `EDGE_TYPES` and exactly the verbs the example wiki
uses for review→target / decision→target. All verdict edges carry only logical-order `created_at`, never
wall-clock. After appending, **`python3 cli/validate_wiki.py <PROJECT_DIR>` MUST pass** (every `dst` resolves).
Trace every reviewer prompt+response to `trace.jsonl` ([`review-tracing`](../../protocols/review-tracing.md)).

## Worked example
The canonical exhibits are **[`examples/comic_m3_audit/comic.json`](../../examples/comic_m3_audit/comic.json)**
(the structured-IR artifact under test — the `progressive` side) and
**[`examples/comic_m3_audit/ART_BIBLE.md`](../../examples/comic_m3_audit/ART_BIBLE.md)** (the SHARED blind
spec both reviewers read). The concrete pattern to copy:

- **The progressive side is the structured IR, the baseline is its one-shot foil.** `comic.json` is a
  24-panel / 19-page comic-ir/1.0 with, per panel, a `condition.content_svg` and (for baked panels)
  `condition.expected_literals` — e.g. `S01 → content_svg: "assets/s01_ddl_anchor_v1.svg",
  expected_literals: ["DDL","T-24:00:00"]`; `S12 → content_svg:
  "assets/method_random_vs_schema_first_v1.svg", expected_literals: ["+6.2"]`. The baseline for the A/B is a
  naive single-prompt render of the SAME story+style (no blueprint, no per-panel gate). The reviewers never
  learn which is which.
- **`ART_BIBLE.md` is the SHARED blind spec, and it is identity-free** — it declares the convergence target
  ("`style_consistency` 的字面定义就是符合本文件"), the two-world warm/dark palette (§0.5: "冷暖是 by-design
  的,不是漂移" — copy this verbatim into the reviewer's `visual_consistency` instruction so the reviewer does
  not false-flag the by-design split), the identity hex-lock (§1), and the env-density taste calibration
  (§6.5). Feed it to BOTH reviewers; it never says which artifact is the home team.
- **The editability table (comparison.md §4) — the wedge made concrete.** Copy this exact shape (filled from
  the `comic_m3_audit` facts):

  | 维度 / dimension | Progressive (our structured render) | Baseline (naive one-shot) |
  |---|---|---|
  | 单元再生成成本 / single-unit regen cost | 1 panel + its local content-SVG blueprint + local prompt | 整本重生成 / the whole comic |
  | 失败可定位 / failure localizable | yes — each panel → `panel_attempt`/`review`/`decision`/`failure_mode` wiki nodes | no — one indivisible bake, no trace |
  | 最小人工补丁单元 / min human-patch unit | 1 panel (re-bake just S14) | 整本 / the whole comic |
  | 数字可审计 / numbers auditable | yes — `expected_literals` token-diff'd during the spiral (`+6.2`→`+1.4` audit) | no — no audited literals |
  | 可复现 / reproducible | yes — re-run `comic.json` + blueprints + spiral | no — exact output unrecoverable |

  This is exactly the case where the baseline may tie or win on `polish` yet the progressive side wins overall
  on `editability_traceability` + `reproducibility` — **KEEP ≠ final**: a structured-but-uglier render can
  beat a one-shot pretty one, and the comparison must say so honestly.
- **Disagreement is a finding, not noise.** If Codex picks the progressive comic and Gemini picks the baseline
  → `consensus = "disagree"`, recorded as such in the decision node and §1 of `comparison.md` — a real
  research result (single-reviewer "we win" could just be that family's bias).

## Hard do / don't (earned lessons)
- **DO** SEAL `.ab_mapping.json` with a single coin-flip, `chmod 600`, **before any reviewer**; never read or
  quote it until ④ UNSEAL; verify `seal_ts < both review ts` and **report** the integrity (intact/compromised).
- **DO** scrub every reviewer prompt with the banned-token scan; a `MAPPING_FILE` reference is a HARD-ABORT,
  any home-team token is a pre-submission REJECT.
- **DO** use two different reviewer families (Codex xhigh ‖ Gemini auto-gemini-3); agreement is then real
  signal and `disagree` is a finding to record, never to reconcile away.
- **DO** persist raw reviews verbatim and keep `_A`/`_B` in the raw files for audit; only the PARSED copies get
  re-labeled to progressive/baseline after unseal.
- **DO** record honestly any dimension the baseline won (especially `polish`); hiding it defeats the
  cross-model adversarial check.
- **DON'T** treat this as the per-panel gate — `panel_gate`/`assembly_gate` run DURING production on single
  units; this runs AFTER, on two complete works. It is an evaluation, not authoring.
- **DON'T** regenerate the comic pages for the A/B — they are deterministic renders; stage the existing pages.
- **DON'T** let the orchestrator (Claude) acquit the winner — the two reviewer families produce the verdict;
  Claude only seals, stages, unseals, and writes the record. The loop drives, it cannot acquit.
- **DON'T** invent a `comparison` node_type or `baseline_for`/`compared_against` edges — record the A/B with
  the slim schema's `review`+`decision` nodes and canonical `{src,dst,type}` edges.

## Adaptation note (video → image-comic)
What changed from aris_movie's `blind-comparison-review`: **DROP** the ffmpeg/ffprobe frame-extraction (comic
pages ARE the discrete deterministic units — stage `A_p01.png`-style directly); **DROP** the `narration_sync`
dimension (folded into `overlay_readability` = bubble/caption↔panel reading-order alignment, which
`assembly_gate` already scores); **KEEP** the other dims and add the comic-native ones the `panel_gate` uses
(identity consistency under `visual_consistency`; baked-text fidelity via `expected_literals` under
`overlay_readability`). Optionally fold the project's CC-narrative reviewer into the panel so the blind A/B
uses the same tri-reviewer set as production (CC ‖ Gemini ‖ Codex) instead of two. Everything else — the seal,
the blind tokens, the timestamp audit, the unseal, the editability table, and the A/B verdict record — ports
1:1. This is an EVALUATION skill that *complements* the authoring suite by giving the finished comic a
baseline-relative honest verdict; it does not replace any authoring step.

## Protocols (governance contracts this skill honors)
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — reviewers get **file paths only** (the
  staged page dirs + the SHARED blind spec) and read them directly; they never receive this orchestrator's
  summary or interpretation. *Plus* the second axis this skill adds: identity-blinding (no home-team token).
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — this is a **post-final evaluation**, the
  KEEP-≠-final companion to the per-panel gate: the loop can DRIVE (seal/stage/unseal/record) but can't ACQUIT
  — the **two reviewer families** produce the A/B verdict; the consensus is read off *their* scores, not a
  Claude re-judgment, and is saved as an inspectable artifact (`comparison.md` + the decision node).
- [`output-language`](../../protocols/output-language.md) — `comparison.md` is the Chinese human deliverable
  (headings, analysis, the editability/blinding tables localized); raw review JSON, file paths, node fields,
  and `expected_literals` stay machine-form.
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Codex `gpt-5.5` `xhigh`; Gemini `auto-gemini-3`;
  `— reviewer: oracle-pro` may route the Codex side to GPT-5.5-Pro on explicit request; never downgrade the
  tier (effort never lowers reviewer quality).
- [`review-tracing`](../../protocols/review-tracing.md) — every reviewer prompt + verbatim response (and the
  seal→unseal timeline) is logged to `trace.jsonl` so the blinding audit is independently inspectable.
