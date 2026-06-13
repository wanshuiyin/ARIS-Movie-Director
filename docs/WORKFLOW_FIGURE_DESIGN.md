# ARIS-Movie-Director — Workflow Figure (design spec, v2 after codex+gemini round 1)

TITLE: **"ARIS-Movie-Director — Audited Spiral Generation for Narrative Comics"**
GOAL: a README "Figure 1: Method overview" that makes a viewer instantly grasp the pipeline AND feel why
this is *not* just prompting an image model. Accurate to the real engine, readable, on-brand.

## Form (AGREED by both reviewers)
DETERMINISTIC VECTOR SVG, authored by code. NOT image_gen ("drawing a figure about how we prevent AI
hallucination with an AI hallucinator undermines the premise" + it garbles the exact labels the figure
depends on). Anti-dry treatment: dark #0A0E27 ground, neon tokens (amber #FFB000 / green #00C896 /
red #FF3366 / purple #B066FF), a retro control-terminal feel, and EMBEDDED pixel-art motifs (chibi
executor/reviewer heads, REJECT/ACCEPT stamps, a tiny blueprint→PNG transform, a small star-map) — all as
crisp vector. Structure stays an engineering diagram.

## Round-1 fixes folded in
- **Rollback was misplaced.** Panel verdict is ONLY keep | retry (engine: seed-anchored comics "NEVER
  rollback-to-prior", spiral_engine.js:53/127/130). Cross-frame rollback happens at the ASSEMBLY gate.
  → Redrawn as **NESTED LOOPS** (two defensive perimeters): inner = literal correctness; outer = narrative
  consistency.
- **Wiki is not a separate horizontal spine** (would be spaghetti). → drawn as the **exhaust trail of the
  spiral**: each attempt drops a node on the orbit; rejected attempts branch off greyed; a glowing
  `repair_pattern` payload loops back into the next bake. "Memory is the shape of the loop."
- **Cross-model debate is not a second big spine** → 3 reviewer chips at the gate + a thin top legend.
- **De-busied**: ONE panel attempt + ONE 4-panel page (not the 13-beat/24-panel arc); 4 score classes only
  (narrative / identity / style / token-diff); 4 wiki nodes only; NO throttle/resume/lock (eng footnotes).

## Layout (landscape ~16:9, three columns + a top legend)

### TOP LEGEND (thin rail)
The cross-model cast: **Claude = executor (makes)** · **GPT-5.5 + Gemini = reviewers (judge)** — DIFFERENT
model families · **👤 human** (approves story, overrides flags). One line: "the one who makes can't be the
only one who judges."

### LEFT COLUMN — AUTHORED SOURCE OF TRUTH
One input region (compress the 3 story layers): **Asset Library** (one-source tokens: DDL chip · stamps ·
mug · curve · star-map → "one visual dialect") + **Outline** (beats) + **Storyboard** → all compile into
**`comic.json`** = {`content_svg`, `expected_literals`, `identity_ref`}, the gate's SOURCE OF TRUTH.
A small "Claude proposes ‖ codex+gemini critique → 👤 approve" tag above it (design-layer debate = same
principle as the gate).

### CENTER — THE AUDITED SPIRAL (the hero; nested orbits)
- **Core:** `content-SVG blueprint → render PNG → codex image_gen bake (refs: blueprint #1 + identity #2)`.
  Show the tiny blueprint→pixel-PNG transform.
- **INNER ORBIT (tight) — panel_gate:** 3 reviewer chips (CC narrative ‖ Gemini visual ‖ Codex visual) →
  **deterministic JS verdict**. Exits: **KEEP → page pool** · **RETRY → re-bake with the `failure_mode`
  positive-invariant** (≤4 attempts/panel).
- **THE PUNCHLINE (at the gate, biggest single visual):** a *beautiful, complete* baked panel, with a
  strict JS diff box over it — `expected_literals: +6.2 · "Tok|yo"` vs `observed: gemini +6.25 / codex
  garbled` — and a heavy mechanical stamp **`REJECT · content_corruption · single-vote veto · +6.25 ≠
  +6.2`**. Caption: *aesthetic beauty does not bypass structural verification.* (engine: token-diff
  :84/:96, veto :114.) The rejected attempt drops a greyed `failure_mode` node that loops its
  `repair_pattern` back to the next bake.
- **OUTER ORBIT (wide) — assembly_gate:** kept panels form a page → **page assembly_gate (cast-aware)** →
  if **drift** detected, **re-bake the NAMED drifting panels** → panel_gate again → re-assemble
  (≤6 rollbacks/run). (engine :380/:423/:436.)
- **ESCAPE VELOCITY:** hitting the 4-retry / 6-rollback bound EJECTS via a bright red arrow to
  **👤 FLAG: HUMAN OVERRIDE** — the loop *drives but never self-acquits*, and can't infinite-loop.

### RIGHT COLUMN — RELEASE PROJECTION (downstream, lighter weight)
accepted pages → **`comic.json` projection** → **single-file clickable HTML viewer** (tiny comic-page
thumbnail). Drawn lighter than the engine core (these are products, not gates).

## Remaining questions for round 2 (confirm before render)
1. Does the nested-orbit (inner=token-diff retry / outer=assembly-drift rollback) + escape-velocity-to-human
   now match the engine exactly?
2. Is the punchline placement (beautiful panel + JS diff + REJECT stamp, at the inner gate) the right focal
   point, or should it be a called-out inset so it doesn't fight the orbit lines?
3. Any remaining busy-ness to cut before we render?
