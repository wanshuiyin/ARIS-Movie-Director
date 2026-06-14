# method-figure — prompt templates

## A. Generation prompt (to `mcp__codex__codex`, sandbox: read-only, effort xhigh)

Fill `{...}` from the blueprint + the round-N consolidated fixes. The point of read-only is to FORCE the
native `image_generation` tool — Codex cannot write files, so it cannot pivot to "build an SVG renderer".

```
Use your IMAGE GENERATION tool to output ONE PNG. Image generation only — do NOT write or edit code/SVG/files.

References (read-only):
- {condition_png}  → the EXACT layout to reproduce (every box already shows its title + one description line; arrows are labeled; pale phase panels). Reproduce this layout faithfully.
- {identity_sheet_png}  → the ONLY characters allowed. Lock traits: {lock_traits}. Never invent robots/mascots.

STYLE: top ML-paper "Figure 1" — pure WHITE background, soft pastel phase panels, rounded white node cards,
soft shadows, clean thin labeled arrows, crisp sans-serif (monospace for code/number tokens). Target: {target_profile}.

TEXT IS LOCKED — render these strings VERBATIM and crisp, no extra spaces, no garble, no rename, no invented
node/term/time-tag. The exact labels (do not change any character):
{for each node}  "{label_exact}" — "{desc_exact}"
{for each group} "{label_exact}"
{for each edge}  arrow "{from}"→"{to}" labelled "{label_exact}" (direction {direction})
{callout} "{title_exact}" / {lines_exact}

CHARACTERS: place {asset_ref characters} exactly at {their nodes}; e.g. researcher at the input handing the
brief; the duo together at panel_gate inspecting a baked panel. No character anywhere else; if art would
cover a label/arrow, shrink the character.

APPLY THIS ROUND'S FIXES: {consolidated_blockers}
KEEP (do not regress): {positive_invariants}

Output the single finished figure. Same wide aspect as the condition. White background.
```

## B. Reviewer prompt (to each panel model — blind; do NOT reveal expected labels)

```
Visual QA of a generated academic figure. Look ONLY at the image: {round_png}

You are the {Claude structure | Gemini visual/identity | Codex arrow/diagnostic} reviewer. Do NOT assume what
the labels "should" say — transcribe what you ACTUALLY see, and hunt for what should NOT be there.

Return STRICT JSON (the schema in references/reviewer_protocol.md): verdict, scores{text_fidelity,
arrow_topology, layout_readability, character_identity, style_fit} 0-5, observed_tokens[] (verbatim),
observed_edges[], identity_audit[], anomalies[] (floating/pasted labels, artifacts, stray lines, duplicated
characters, invented nodes), character_anatomy[] + anatomy_defect (if the figure has characters, ENUMERATE
each one's visible hands and set anatomy_defect=true on any wrong count / 3rd / floating / merged hand —
a single-reviewer veto), blockers[] (concrete image-gen-fixable), nice_to_have[], positive_invariants[].
A vague "looks good" is rejected — list the transcription, and COUNT the hands (don't eyeball them).
```

## C. Notes
- Re-assert the FULL locked-label list every round (image models drift); don't assume the prior round "kept" it.
- After the bake, `pickup_image.py --marker <epoch>` (set the marker right before the codex call) verifies a
  real native PNG appeared (signature + size + dims) — fail-closed otherwise.
- Serialize bakes: never run two image generations at once (the global generated-images dir + newest-after-
  marker pickup will cross-pollinate).
