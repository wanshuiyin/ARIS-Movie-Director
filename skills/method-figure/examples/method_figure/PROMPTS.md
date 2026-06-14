# The real prompts that baked `docs/method_figure.png` (the README Figure 1)

This is the **actual, unedited prompt sequence** that produced the README's "Figure 1 — method
overview" (`docs/method_figure.png`). It is published verbatim (paths redacted to repo-relative) so you
can see *how detailed an image-generation condition has to be* — this skill's whole thesis is **"condition
it exhaustively, don't hand-paste."** Nothing in that figure was overlaid by hand; every box, arrow, and
character was rendered by the model from the text below.

**How it was run.** Each bake is one call to **codex (`gpt-5.5`, `model_reasoning_effort: xhigh`) with
`sandbox: read-only`** — the read-only sandbox is deliberate: it removes codex's ability to "helpfully"
write an SVG/script, forcing it to use its native `gpt-image-2` image-generation tool. Between bakes, a
**3-model panel (Codex ‖ Gemini ‖ Claude)** critiques the rendered pixels; the consolidated fix-list
becomes the next bake. It converged in **4 rounds**; v4 was unanimously APPROVED and shipped.
The round-by-round verdicts are in `trace.jsonl` next to this file.

Two reference images were attached to every bake (read-only):
- `docs/figassets/aris_identity_sheet.png` — the **exact** chibi cast (don't invent robots/mascots).
- `docs/figassets/condition_cond.png` — a rough layout draft, used only for the left→right 3-phase arrangement.

> Reuse note: the four BAKE prompts are the **condition** exemplars; the round-1 CRITIQUE and the final
> APPROVAL are the reusable **review** templates. Copy the shape, swap the content. See also
> `references/prompt_templates.md` (the generic templates) and `references/reviewer_protocol.md`.

---

## Round 1 — BAKE (the full initial condition: this is "how detailed")

```
TASK: produce ONE publication-quality "Figure 1 — method overview" image for a GitHub README, by USING
YOUR IMAGE GENERATION TOOL (gpt-image-2) to render the final PNG. This is an image-generation task — do
NOT write or edit code, do NOT output SVG, do NOT touch repo files. Just generate the best image you can,
iterate it in your head, and output the final raster image.

You have two reference images to read first (read-only):
- docs/figassets/aris_identity_sheet.png  → the EXACT character cast you must use (do NOT invent
  robots/mascots): researcher = black hair, rectangular glasses, black tee; executor = brown hair, blue
  hoodie, NO beard; reviewer = black hair, full beard, green hoodie. All are cute pixel-art chibi.
- docs/figassets/condition_cond.png  → a ROUGH layout draft. Use it ONLY for the overall left→right
  3-phase arrangement. IMPROVE on it: its arrows are messy and its little white floating label-pills look
  pasted-on — replace those with clean arrows whose labels sit naturally on the line; and its boxes are
  too hollow — make each box genuinely informative.

STYLE: the visual language of a top ML-paper Figure 1 (think PaperBanana / AutoFigure): PURE WHITE
background, three soft pastel phase panels (pale blue, pale peach, pale green), rounded white node cards
with subtle soft shadows, clean thin connector arrows with small inline labels, a confident title
top-left. Crisp legible sans-serif text; monospace for code/number tokens. It must look hand-designed by
a researcher, not like a game screenshot.

CONTENT — render this pipeline richly (every box gets a short, substantive description, not one vague word):

TITLE (top-left): "ARIS-Movie-Director"  ·  subtitle: "Audited, cross-model spiral generation for
narrative comics".

PHASE 1 — "Authored Source of Truth" (pale blue):
 • Asset Library — one canonical source for every recurring visual token (DDL clock, stamps, mugs, charts,
   star-map) → "one visual dialect, never two".
 • Outline — the 13 story beats.
 • Storyboard — per-panel spec: world · scene · dialogue · expected_literals.
 • These compile into comic.json — {content_svg, expected_literals, identity_ref}, the single source of
   truth the gate later checks against.
 The researcher chibi stands at the far left, exhausted, handing a "story brief (24h deadline)" document
 into Phase 1.

PHASE 2 — "The Audited Spiral (per panel)" (pale peach) — the hero of the figure:
 • content-SVG blueprint — exact numbers & labels drawn deterministically.
 • image_gen BAKE — codex bakes a pixel-art comic panel from (blueprint + identity ref).
 • panel_gate — THREE independent cross-model reviewers: CC (narrative) ‖ Gemini (visual) ‖ Codex
   (visual). They blind-transcribe the panel's literals and a deterministic token-diff compares them to
   expected_literals; content_corruption is a single-vote veto. Draw the blue executor and the green
   bearded reviewer here, inspecting a freshly baked panel (the reviewer with a magnifier) — they ARE the gate.
 • verdict (deterministic) → KEEP, or RETRY (re-bake with the failed attempt's repair note; max 4 / panel).
 • research-wiki — every attempt / review / decision is logged; failures are kept as memory.
 • A highlighted callout "looks right ≠ passes": a gorgeous baked panel that still fails — expected +6.2
   vs observed +6.25 → content_corruption → verdict RETRY. (the punchline: aesthetic beauty never
   bypasses the deterministic check.)

PHASE 3 — "Assembly + Release" (pale green):
 • page assembly_gate — cast-aware page coherence; if a panel drifts, re-bake the named panels (max 6 / run).
 • Release — the kept panels become comic.json + a single-file clickable HTML viewer (show a tiny
   finished comic page).

BOTTOM RAIL: "bounded retries (≤4/panel) · localized repair (≤6/run) → human backstop · the loop drives,
never self-acquits".

Arrows: left→right main flow through the three phases; a RETRY loop-back from verdict to BAKE inside
Phase 2; a dashed "repair drift" loop from assembly_gate back to BAKE; gate writes to research-wiki. Keep
arrows clean and non-crossing; labels small and ON the arrows.

Output the single finished figure image. Make the text accurate and legible, the characters on-model (our
chibi only), and the composition genuinely beautiful.
```

## Round 1 — CRITIQUE (reusable review template: blind, pixel-level, prioritized fix-list)

```
PURE-ANALYSIS visual critique. Open and VIEW this image file, then critique it (read-only; do NOT
edit/generate/code now): docs/figassets/method_codexmcp_v1.png

You (codex, gpt-5.5) generated it via gpt-image-2 from a method-figure brief. We're now running an
iterative refine loop: each round YOU will regenerate an improved version via image generation, after a
3-model panel (you, Gemini, Claude) critiques. This is the CRITIQUE step.

Inspect the actual rendered pixels and give a CONCRETE, prioritized fix-list:
1. TEXT fidelity: list any label that is misspelled / garbled / blurry / illegible, with the correct text.
   (must be exact: comic.json, content-SVG, image_gen BAKE, panel_gate, research-wiki, page
   assembly_gate, "expected +6.2 / observed +6.25", "CC | Gemini | Codex".)
2. ARROWS/FLOW: broken/crossing/ambiguous arrows? Is left→right + the RETRY loop (verdict→bake) +
   repair-drift loop (assembly→bake) + gate→wiki clear?
3. LAYOUT: crowding, dead space, misalignment, uneven phase panels, box-size inconsistency.
4. CHARACTERS: are our 3 chibi on-model (researcher black-hair+glasses; executor blue-hoodie no-beard;
   reviewer green-hoodie beard) and correctly placed (duo AT panel_gate)? any duplication/weirdness?
5. The 3 highest-impact changes to make it look like a real top-ML-paper Figure 1.
If you genuinely cannot see the image pixels, say so explicitly. Otherwise return a tight numbered
fix-list, each item a concrete instruction usable as an image-gen prompt edit.
```

*Panel verdict v1 → RETRY. Consolidated fixes: floating pasted-looking edge labels (`source`/`keep`/
`accept`) → labels on the line; put BOTH chibi at panel_gate; shields on both gates; single-direction
repair-drift arrow; highlight +6.2/+6.25.*

---

## Round 2 — BAKE (apply the consolidated v1 fix-list)

```
REGENERATE the method figure — round 2. Use your IMAGE GENERATION tool (gpt-image-2) to output ONE
improved PNG. This is image generation, NOT coding: do not write/edit code or files, only generate the image.

Read these (read-only):
- docs/figassets/method_codexmcp_v1.png  → YOUR previous version. Improve it; keep its good parts (white
  bg, 3 pastel phases, the researcher/duo chibi style, the overall left→right story).
- docs/figassets/aris_identity_sheet.png  → the exact character cast (researcher: black hair+glasses;
  executor: brown hair, blue hoodie, NO beard; reviewer: black hair, full beard, green hoodie). Use ONLY these.

A 3-model panel (you + Gemini + Claude) reviewed v1. Apply ALL these consolidated fixes in the regeneration:

TEXT (render EXACT, crisp, no extra spaces, no garble):
- "comic.json" (NOT "comic .json"), "content-SVG", "image_gen BAKE", "panel_gate", "research-wiki",
  "page_assembly_gate" (with underscore), "verdict", "KEEP", "Release".
- panel_gate subtitle EXACTLY "CC | Gemini | Codex" (drop the long "narrative/visual" form), plus one
  short line "blind token-diff · single-vote veto".
- bottom callout EXACTLY "looks right ≠ passes" and "expected +6.2 / observed +6.25".
- improve sharpness of all small text so nothing is blurry.

ARROWS / FLOW (clean, non-crossing):
- MAIN flow = a single thicker left→right path: content-SVG → image_gen BAKE → panel_gate → verdict →
  KEEP → page_assembly_gate → Release.
- RETRY loop = a clear curved ORANGE arrow starting at the verdict diamond and returning to image_gen
  BAKE, labelled "RETRY · repair note · max 4/panel".
- repair-drift = ONE single-direction dashed BLUE arrow from page_assembly_gate back to image_gen BAKE,
  labelled "repair drift · max 6/run".
- audit trace = a thin grey arrow from panel_gate to research-wiki, labelled "write audit trace".

CHARACTERS (this is important):
- EXACTLY three character placements, nowhere else: (1) the researcher chibi at the far-left input
  handing over the "story brief (24h deadline)"; (2) BOTH the blue-hoodie executor AND the green-hoodie
  bearded reviewer standing together AT panel_gate, inspecting a freshly baked panel (executor holding
  the panel, reviewer with a magnifier).
- Do NOT duplicate the chibi anywhere else. The kept-panel, the bottom "beautiful panel" callout, and the
  Release thumbnail must show COMIC ARTWORK / scenes (e.g. a little pixel landscape or city), NOT the duo again.

LAYOUT / AESTHETIC (make it a clean top-ML-paper Figure 1):
- Balance the three phases: spread Phase 2 vertically so panel_gate / verdict / research-wiki / callout
  are not cramped; enlarge the Release content in Phase 3 so the green panel isn't mostly empty.
- Uniform node widths, equal margins, consistent font sizes and line weights; add a subtle soft
  drop-shadow to each of the 3 pastel phase panels; pure white background, lighten/remove any background
  grid noise.
- Give BOTH gates (panel_gate, page_assembly_gate) a small consistent shield/gate icon.
- Highlight the "+6.2 vs +6.25" mismatch with a small yellow highlight so the content_corruption point is
  the visual centerpiece.
- Compress the bottom legend to ONE short line: "bounded retries (max 4/panel) · localized repair (max
  6/run) · human backstop".

Keep all the box descriptions substantive (one short informative line each) — do not make boxes hollow.
Output the single improved figure image.
```

*Panel verdict v2 → RETRY. Flagged: top title dropped, Asset Library too bare, callout/Release used
generic landscapes instead of comic panels.*

---

## Round 3 — BAKE (restore title + density + character-driven callout)

```
REGENERATE — round 3. Use your IMAGE GENERATION tool (gpt-image-2) to output ONE improved PNG. Image
generation only, no code/files.

Base to improve (read-only): docs/figassets/method_codexmcp_v2.png — keep ALL of v2's good parts (3
pastel phases, exact text, the duo at panel_gate, shields on both gates, the +6.2/+6.25 yellow highlight,
the compressed legend, the clean left→right flow).
Characters (read-only): docs/figassets/aris_identity_sheet.png — our exact chibi.

The 3-model panel (you + Gemini + Claude) reviewed v2 and asked for ONE more round. Apply EXACTLY these
deltas, change nothing else:

1. TITLE: restore a strong top-left header — "ARIS-Movie-Director" in large bold, with the muted subtitle
   "Audited, cross-model spiral generation for narrative comics" beneath it. (v2 lost the title; the top
   is too empty.)
2. RETRY arrow: draw a clear ORANGE curved arrow that STARTS at the "verdict" diamond and ENDS at
   "image_gen BAKE", labelled "RETRY · repair note · max 4/panel". Its origin must unambiguously be the
   verdict diamond (not research-wiki, not the gate).
3. repair-drift arrow: make it ONE dashed BLUE arrow with a SINGLE arrowhead, going FROM
   "page_assembly_gate" TO "image_gen BAKE" (a drift sends panels back to be re-baked), labelled "repair
   drift · max 6/run". Remove the second/extra arrowhead — no bidirectional ambiguity.
4. Fix the "single-vote veto" text under panel_gate: render it crisp BLACK, no red strike-through, no ghosting.
5. Phase 1 "Asset Library" is too bare — enrich it with a row of small pixel-art icons (a DDL clock, a
   stamp, a coffee mug, a tiny chart, a star-map) and the small motto "one visual dialect, never two".
   Bring back v1's density here.
6. SEMANTICS: the bottom "looks right ≠ passes" callout panel and the "Release" thumbnails currently show
   generic landscapes — replace them with CHARACTER-DRIVEN pixel-art COMIC panels (a tiny research-desk /
   city-at-night scene with our chibi style), so it reads as "narrative comics", not stock scenery.
   Inside the callout's comic panel, show a small score/number readout where "+6.2" is highlighted and
   conflicts with the observed "+6.25" — make the literal mismatch visible in the art.
7. CHARACTERS — keep EXACTLY three placements, no more, no fewer: (1) the researcher chibi at the FAR
   LEFT handing over "story brief (24h deadline)" — this is intentional (the human hands the night over),
   DO NOT remove it and it is NOT a duplicate; (2) the blue-hoodie executor AND green-hoodie bearded
   reviewer together inside panel_gate. No chibi anywhere else.
8. Give "write audit trace" clean spacing so it doesn't crowd the arrow.

Everything else stays as in v2. Output the single improved figure.
```

*Panel verdict v3 → RETRY. The aesthetics jumped — but the model **drifted the content**: it renamed the
phases to PLAN/BAKE/RELEASE, invented `self_critique` / `VLM pass-fail` / `(≤24h)` time-tags / `8 panels`,
and moved research-wiki into Phase 1. This is the canonical failure mode: **a prettier round silently
rewrites your labels.** The fix is to LOCK the exact text in round 4.*

---

## Round 4 — BAKE (lock exact labels, keep v3's look) → this produced `docs/method_figure.png`

```
REGENERATE — round 4 (final polish). Use your IMAGE GENERATION tool (gpt-image-2) to output ONE PNG.
Image generation only.

Base to improve (read-only): docs/figassets/method_codexmcp_v3.png
Characters (read-only): docs/figassets/aris_identity_sheet.png

KEEP v3's visual style EXACTLY — it's good: the big top-left "ARIS-Movie-Director" title + subtitle, the
Asset Library icon row, the bottom-left LEGEND box, the "looks right ≠ passes" callout showing the two
comic panels comparing +6.2 vs +6.25, and the "Release (example panels)" row of comic panels, the soft
pastel phase panels, drop shadows, clean academic look.

BUT v3 DRIFTED the text content. A 3-model panel says: restore the CANONICAL pipeline text EXACTLY. The
box labels are LOCKED — use these exact words, do NOT rename, do NOT invent any extra node/term/time-tag:

PHASE 1 header: "1 · Authored Source of Truth"  (NOT "PLAN")
  box: "Asset Library"  — sub: "one visual dialect, never two"
  box: "Outline"  — sub: "13 beats"
  box: "Storyboard"  — sub: "world · scene · dialogue · expected_literals"
  box: "comic.json"  — sub: "content_svg · expected_literals · identity_ref"
  (flow: Asset Library → Outline → Storyboard → comic.json)

PHASE 2 header: "2 · The Audited Spiral (per panel)"  (NOT "BAKE")
  box: "content-SVG blueprint"
  box: "image_gen BAKE"  — sub: "blueprint + identity ref"
  box: "panel_gate"  — sub line 1: "CC | Gemini | Codex"  — sub line 2: "blind token-diff · single-vote
       veto"   (with a small shield icon; the blue executor + green bearded reviewer chibi inspecting a
       baked panel here)
  diamond: "verdict"  — sub: "KEEP / RETRY"
  box: "research-wiki"  — sub: "attempts · reviews · decisions · failures"
  (flow: content-SVG blueprint → image_gen BAKE → panel_gate → verdict → KEEP)

PHASE 3 header: "3 · Assembly + Release"  (NOT "RELEASE" alone)
  box: "page_assembly_gate"  — sub: "cast-aware coherence · repair drift → re-bake"  (small shield icon)
  box: "Release"  — sub: "PNG panels + single-file HTML viewer"

DELETE everything invented in v3: the "(≤24h)" / "(≤3×24h)" time tags, "self_critique", "VLM pass/fail",
"storyboard_plan / 8 panels", "PDF", "pass/retry/escalate", and the misplaced research-wiki in Phase 1.
research-wiki belongs ONLY in Phase 2.

ARROWS (fix direction, single arrowhead each):
- main flow: thicker left→right through the three phases.
- "RETRY · max 4/panel": ONE orange arrow, arrowhead ONLY at image_gen BAKE, starting at the verdict
  diamond (verdict → image_gen BAKE).
- "repair drift · max 6/run": ONE dashed blue arrow, arrowhead ONLY at image_gen BAKE, from
  page_assembly_gate → image_gen BAKE.
- thin grey "write audit trace": panel_gate → research-wiki.

TEXT: make all small subtitles + bottom comic captions slightly LARGER and crisp — no blurry/garbled characters.

CHARACTERS: exactly the researcher chibi at the far-left input (handing the story brief — keep it), and
the executor+reviewer duo inside panel_gate. No chibi anywhere else.

Output the single final figure.
```

## Final — APPROVAL check (reusable acceptance template; codex is diagnostic, not sole acquitter)

```
FINAL approval check. VIEW v4 (read-only, no gen): docs/figassets/method_codexmcp_v4.png

Round 4 after the content-accuracy fixes. Canonical it must show: Phase 1 "Authored Source of Truth"
(Asset Library/"one visual dialect, never two" → Outline 13 beats → Storyboard → comic.json
content_svg·expected_literals·identity_ref); Phase 2 "The Audited Spiral (per panel)" (content-SVG
blueprint → image_gen BAKE → panel_gate "CC | Gemini | Codex · blind token-diff · single-vote veto" →
verdict KEEP/RETRY → research-wiki); Phase 3 "Assembly + Release" (page_assembly_gate cast-aware
coherence·repair drift→re-bake → Release "PNG panels + single-file HTML viewer"). Arrows: RETRY max
4/panel verdict→bake (single head), repair drift max 6/run assembly→bake (single head).

Answer crisply:
1. Did all content corrections land? Any leftover invented terms (self_critique / VLM / time-tags / PDF /
   8 panels / misplaced research-wiki)?
2. Are the two loop arrows now single-headed and correctly directed?
3. Any text still garbled/blurry (name the label)?
4. VERDICT: APPROVED (ship) or ONE-MORE-ROUND with the few exact remaining image-gen instructions.
Be decisive and tight.
```

**v4 → APPROVED by all three (Codex ‖ Gemini ‖ Claude).** Shipped as `docs/method_figure.png`.

---

## What this example teaches (the transferable lessons)
1. **Detail is the product.** The round-1 condition is ~4.3k chars and names every box, sub-line, arrow
   color/direction, and the exact character placement. image_gen renders figure text *legibly* when you
   condition it this hard — it garbles when you're vague.
2. **`sandbox: read-only` forces the image tool.** Without it codex tends to "help" by writing an SVG.
3. **Condition, never paste.** Every literal in the figure was rendered by the model from text above; we
   pasted nothing on top.
4. **Lock exact labels or a prettier round will rewrite them** (the v3 drift → v4 lock). This is exactly
   what the blueprint's `*_exact` fields and the deterministic content-diff enforce in the automated loop.
5. **Cross-model critique drives convergence; the generator is diagnostic, not the sole acquitter** — v4
   shipped only on a 3-model APPROVE.
6. **Use OUR identity sheet, never a generic mascot.** The cast was anchored to
   `aris_identity_sheet.png` on every round.
