# ARIS-Movie-Director — Method Figure (design spec v3 · FULL REDO, AutoFigure-style)

The v1/v2 dark hand-drawn SVG was WRONG: a paper Figure-1 / a GitHub README (white page) needs a LIGHT
background and proper academic colors, and the figures must be our REAL baked characters, not hand-drawn
stick people. References (PaperBanana Fig.2, AutoFigure Fig.2) prove an image model CAN produce a clean
publication figure — they ARE AI-generated — so we adopt their method.

## METHOD (decoupled, from AutoFigure — solves the label-garble problem)
1. **Structural blueprint = a JSON layout** (source of truth): nodes {id, label(exact English), pos[x,y],
   group, shape}, edges {from,to,kind,label}, style="academic_flat". This holds the EXACT text.
2. **Aesthetic render via image2** (codex native image_gen): condition the bake on (a) a clean WHITE-BG SVG
   rendered from the JSON [structure lock] + (b) OUR baked ARIS duo crop as the identity ref [characters].
   Prompt = academic-flat style, light pastel phase panels, white background.
3. **Text-accuracy overlay**: image gen blurs text → after the bake, OVERLAY the exact labels as crisp
   vector (SVG/PIL) on top of the raster, positioned from the JSON coords. Perfect labels + pretty base.

So the answer to "JSON or prompt?": BOTH, decoupled. JSON/SVG locks structure+labels; prompt + duo-ref
drives the aesthetic; vector overlay guarantees the words. image2 never has to get the text right alone.

## NON-NEGOTIABLES
- WHITE / very-light background (#FFFFFF / #FAFAF7). Dark theme is for the standalone comic viewer, NOT a
  README figure on a white page.
- Academic-flat palette: pale phase panels (soft blue / soft peach / soft green, like the refs), dark text,
  one accent per phase. English labels only.
- Characters = OUR ARIS duo (blue executor: brown hair, no beard / green reviewer: dark hair, beard),
  cropped from our real bakes (docs/figassets/aris_duo_ref.png) + the researcher
  (docs/figassets/aris_researcher_ref.png). **NEVER the reference papers' generic robots.**
- Must reflect what makes US different: deterministic token-diff gate · cross-model adversarial debate ·
  research-wiki memory · bounded cross-frame repair · human backstop.

## LAYOUT (3 academic phases, left→right, like AutoFigure; white canvas, title top-left)
TITLE: "ARIS-Movie-Director" + subtitle "Audited, cross-model spiral generation for narrative comics".

### INPUTS (far left, small)
- the RESEARCHER (our chibi) + "story brief / deadline" → feeds Phase 1. (she hands the night over)

### PHASE 1 — AUTHORED SOURCE OF TRUTH  (pale blue panel)
- Asset Library (one-source tokens: DDL · stamps · mug · curve · star-map) + Outline (beats) + Storyboard
  → compile to **comic.json** {content_svg · expected_literals · identity_ref}.
- gate between design & production: "Claude proposes ‖ codex + gemini critique → 👤 human approves".

### PHASE 2 — THE AUDITED SPIRAL  (pale peach panel; the hero, an iterative loop like their refinement loop)
- flow: **content-SVG blueprint → render → image_gen BAKE (2 refs)** → **panel_gate**.
- panel_gate = OUR DUO as the reviewers + CC: three reviewer chips (CC narrative · Gemini visual · Codex
  visual) → **deterministic JS token-diff verdict**.
- exits: **KEEP** → Phase 3 · **RETRY** (inner loop back to bake, carrying the `failure_mode` repair_pattern).
- CALLOUT (the punchline, like AutoFigure's "Text Blur!" callout): a *beautiful baked panel* + a token-diff
  box `expected +6.2 / Tok|yo  vs  observed +6.25 / garbled` + a red **REJECT · content_corruption** stamp.
  "a beautiful panel with a wrong number does not pass."
- WIKI: every attempt/review/decision/failure written as nodes (the loop's memory; failures kept).

### PHASE 3 — ASSEMBLY + RELEASE  (pale green panel)
- kept panels → **page assembly_gate (cast-aware)** → if drift, OUTER rollback (re-bake named panels, ≤6) →
  **comic.json** → **single-file HTML viewer** (a real comic-page thumbnail).

### BOUNDS + HUMAN (bottom rail)
- inner retry ≤4/panel · outer rollback ≤6/run → on bound, EJECT to 👤 human. "drives, never self-acquits."

## Open questions for codex + gemini (round 1)
1. Is the AutoFigure-style decoupled method (JSON blueprint → image2 aesthetic w/ OUR duo refs → vector text
   overlay) the right pipeline to PRODUCE this figure? Any better way to guarantee legible labels?
2. Is the 3-phase (Source of Truth / Audited Spiral / Assembly+Release) the right mapping of OUR pipeline,
   matching the academic-fig idiom — or is a phase mis-grouped vs the engine (panel verdict is keep/retry
   only; rollback is at assembly)?
3. For the JSON blueprint fed to image2: what exact schema (nodes/edges/groups/style) and which fields, so
   the structure locks but the aesthetic stays free? 
4. The ONE visual punchline that says "not just prompting an image model" — keep the beautiful-but-wrong
   REJECT callout, or something stronger?
5. What to CUT so a first-time viewer parses it in 5 seconds (the refs are busy but legible — where's our
   line)?
