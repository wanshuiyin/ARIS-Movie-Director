# method-figure — prompt templates

## A. Generation prompt (to `mcp__codex__codex`, sandbox: workspace-write, effort xhigh)

Fill `{...}` from the blueprint + the round-N consolidated fixes. The bake is the **agent `mcp__codex__codex`
sidecar** with `sandbox: workspace-write` so Codex can WRITE the native PNG to the explicit out_path. Honesty
is NOT enforced by any sandbox setting — it is enforced by `pickup_image.py --out-existing`'s fail-closed
HARD-VETO (a hand-drawn struct/zlib/SVG fallback is rejected even with a valid PNG signature). `codex exec`
is retired for real bakes; refs + out_path are embedded as absolute paths in the prompt (the MCP schema has no `-i`).

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
- After the bake, `pickup_image.py --out-existing --out <round.png> --transcript <round.png.bakestatus.json>`
  verifies the EXPLICIT out_path (PNG signature + size + dims + `mtime >= created_at`) and HARD-VETOes
  struct/zlib/PIL/`<svg>`/matplotlib markers in the agent transcript — fail-closed otherwise.
- Serialize bakes per the agent SOP (one `mcp__codex__codex` call at a time). Each bake writes to its OWN
  explicit deterministic out_path, so there is no global-dir cross-pollination (the legacy `--bake-mode=exec`
  newest-after-marker glob is the only path with that hazard).
