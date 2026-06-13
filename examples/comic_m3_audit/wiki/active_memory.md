# Active Memory — panel_gate + assembly_gate (full film)

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
- **`fail:s10_a01/a02/a03`** — `content_corruption_present=true` from both visual reviewers (garbled hero
  `Tok|yo` crack / `ParseError` / `0.66`). Repair invariant: the hardest literal sets need the technical
  figure baked large and high-contrast; a01–a03 were re-baked until a04 read clean. The corruption veto is
  a single-vote kill and it earned its keep here.

## Standing lesson — assembly must be design-aware (the B03 false-drift)

The cross-frame assembly gate once scored "duo identity across panels" = 0 on a **parallel 2-up with
disjoint casts** (S03 researcher-only / S04 duo-only) — twice, with **identical** scores. Identical scores
across repair rounds are the fingerprint of a broken **rubric**, not a broken artifact: stop regenerating,
audit the judge. Fix shipped: the assembly reviewer now receives each panel's intended cast + all page
identity refs, and absence-of-a-character / warm-vs-dark world contrast are NOT drift. The human override
is recorded as `decision_assembly_p_b03_human_override` — the loop can drive but never acquits.

## Standing lesson

Faithfulness must be a deterministic diff over **blind** transcriptions — the moment an evaluator is shown
the answer (or repairs the output before scoring), the score inflates. The production loop encodes the
same audit it depicts.
