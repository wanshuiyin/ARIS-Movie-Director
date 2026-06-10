# Active Memory — B08 panel_gate

The wiki is **prompt active-memory, not a passive log**: these constraints are fed back into generation.

## Gate criteria (sound, cross-model-acquitted PASS)

- **Identity lock** — canonical duo (blue executor: brown hair, no beard / green reviewer: dark hair,
  beard). Both visual reviewers must agree (id disagreement < 2).
- **Figure faithfulness — the plausible-unsupported-success guard.** Every authored `expected_literal`
  must be EXACTLY transcribed by **BOTH** visual reviewers, who are *blind* to the expected values.
  Numbers match an exact token (`+6.25` ≠ `+6.2`); code/labels match by component. A literal read by
  *neither* reviewer ⇒ retry. This is a deterministic token-diff, never a visual "looks-right" score.
- **Content corruption** — a *single* reviewer flagging a garbled/illegible glyph ⇒ veto (no corroboration
  required; a wrong number is fatal even if only one eye catches it).
- **Baked-text legibility ≥ 4** from both reviewers.
- **Style / composition** softened to one-reviewer strictness; **background atmospheric gradients are
  allowed** (atmosphere, not a pixel-art violation).

## Active failure_mode

- **`fail:s13_a02`** — a required literal was not both-reviewer-confirmed.
  Repair invariant: re-bake with the technical figure rendered crisply and legibly; (meta) author
  `expected_literals` as the **salient** figure numbers reviewers reliably read, not a buried code token.

## Standing lesson

Faithfulness must be a deterministic diff over **blind** transcriptions — the moment an evaluator is shown
the answer (or repairs the output before scoring), the score inflates. The production loop encodes the
same audit it depicts.
