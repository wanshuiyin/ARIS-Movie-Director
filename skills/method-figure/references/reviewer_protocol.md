# method-figure — cross-model review-panel protocol

The panel is the gate. Its job is to make figure quality **objective**, not a vibe. Three rules make it work:

1. **Blind transcribe, then diff.** Reviewers are NEVER shown the blueprint's expected labels first. They
   transcribe what they actually SEE (tokens, edges, characters) and flag what shouldn't be there. A SCRIPT
   (`content_diff.py`) then diffs that transcription against the blueprint. This removes confirmation bias —
   a reviewer told "the box should say comic.json" will hallucinate reading it; a reviewer asked "what does
   that box say?" reports `comic .json` (the real, broken render).
2. **Negative-Space Audit.** Beyond "what's there", every reviewer must hunt for what does NOT belong:
   floating / pasted-looking labels, background artifacts, stray lines, duplicated characters, invented
   nodes. These go in `anomalies` and are a veto.
3. **The maker can't acquit alone.** Codex is the generation family. A Codex `approve` may *diagnose* or
   *veto* but can NEVER be the sole acquitter. ACCEPT requires **Gemini approve + Claude structural approve +
   the hard-diff empty**.

## Per-reviewer lens (fixed — do not free-style)
- **Claude** — structure / narrative readability: first-read order, phase grouping, does the flow tell the
  story L→R, is the hierarchy clear. Owns `layout_readability`.
- **Gemini** — visual / identity / legibility / artifacts. Owns `character_identity`, `text_fidelity` (is
  each token crisp & legible), `style_fit`, and the `anomalies` audit.
- **Codex** — second visual + code-native critique (arrow topology, exact-token spelling). Owns
  `arrow_topology`. Diagnostic/veto only; not an acquitter.

## Strict per-round output (every reviewer returns THIS JSON)
```json
{
  "verdict": "approve | retry | escalate",
  "scores": {"text_fidelity": 0, "arrow_topology": 0, "layout_readability": 0,
             "character_identity": 0, "style_fit": 0},        // 0-5 each
  "observed_tokens": ["...verbatim strings you can READ..."],
  "observed_edges": [{"from_label": "...", "to_label": "...", "direction": "forward|back", "label": "..."}],
  "identity_audit": [{"node_id": "gate", "status": "MATCH|DRIFT", "issue": "..."}],
  "anomalies": ["floating pasted-looking 'source' label", "duplicate reviewer chibi in Release", "..."],
  "blockers": ["concrete, image-gen-fixable instruction", "..."],
  "nice_to_have": ["non-blocking polish"],
  "positive_invariants": ["things that are RIGHT — keep them next round"]
}
```

## Consolidation (anti-oscillation)
`consolidate_reviews.py` merges **`blockers` only** across the three reviewers (de-duplicated), and carries
every `positive_invariant` forward into the next bake prompt so good parts aren't lost. **Never** act on
`nice_to_have` during the loop — chasing polish makes it oscillate and never converge.

## Stop rule
- **ACCEPT** iff: `content_diff` empty (no missing_tokens / wrong_edges / anomalies) AND Gemini `approve`
  AND Claude structural `approve` AND every core score ≥ `acceptance.min_core_score` (default 4) AND no timeout.
- **RETRY** iff: blockers are prompt/condition-fixable AND `round < max_rounds` → re-bake re-asserting the
  locked `*_exact` labels + the consolidated blockers + the positive_invariants.
- **ESCALATE** to human iff: the same root failure recurs `max_repeated_failure` rounds (default 2);
  reviewers give irreconcilable instructions; `max_rounds` reached; or the failure isn't prompt-fixable
  (image_gen throttle, persistent identity drift, no native image artifact).

## What "drift" looks like (catch it every round)
Image models silently re-interpret content each regeneration. Watch for: phases renamed (e.g.
"Authored Source of Truth" → "PLAN"), invented nodes ("self_critique", "VLM pass/fail"), invented time tags
("≤24h"), a token mutated (`comic.json` → `comic .json`), an edge reversed or dropped, a character
duplicated into thumbnails. The blueprint's `*_exact` + `expected_tokens` are the anchor — re-assert them.
