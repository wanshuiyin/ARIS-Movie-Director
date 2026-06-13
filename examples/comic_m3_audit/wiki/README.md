# Production Wiki — the full 24-panel film, as it actually ran

This is the **research-wiki trace** for the entire reference comic (24 panels / 19 pages) — the authentic
record of how every panel was produced and judged. It is the same spiral-engine active memory the pipeline
writes on every gate decision; nothing here is reconstructed after the fact.

## The loop (per panel)

```
generatePanel  — codex bakes the panel from a deterministic content blueprint + the canonical identity ref
   → panel_gate — 3 INDEPENDENT cross-model reviewers:
        • CC      narrative  (does the panel deliver its story beat?)
        • Gemini  visual     (identity / style / artifacts / baked-text legibility / number transcription)
        • Codex   visual     (a second, different-model-family eye)
   → deterministic JS verdict   (blind observed_literals token-diffed vs authored expected_literals;
                                 content_corruption is a single-vote veto; no single model self-acquits)
   → decision node (keep | retry | rollback) + a failure_mode node when rejected
   → (cross-frame) page assembly_gate
```

## What this trace contains — **174 nodes**

| node_type | count | what it records |
|---|---|---|
| `panel_attempt` | 33 | every bake attempt (24 panels, 33 total attempts) |
| `review` | 99 | 3 per attempt (`_cc` narrative ‖ `_gemini` visual ‖ `_codex` visual), each with blind `observed_literals` + 5-dim scores |
| `decision` | 34 | the keep/retry/rollback verdict per attempt + 1 human-override |
| `failure_mode` | 8 | the positive repair invariant fed back into the next bake, per rejected attempt |

**Generation stats** (derivable from the nodes): 24 panels · **33 attempts** · 18 first-try keeps · **6 panels needed retries** — `S10×4`, `S03×3`, `S01 / S09 / S13 / S17 ×2`.

## The loop is real, not a rubber stamp — three worked examples in this trace

1. **S10 took four attempts (the hardest literal set).** Attempts `s10_a01/a02/a03` were each vetoed by
   `content_corruption_present=true` from **both** the codex and gemini visual reviewers (garbled baked
   text in the hero `{"city":"Tok|yo"}` crack / `json.loads → ParseError` / `0.66`). The deterministic
   corruption veto drove three re-bakes; `s10_a04` finally passed. See `review_panel_s10_a0{1,2,3}_*` and
   `fail_s10_a0{1,2,3}`.
2. **S13 a02 was rejected** because a required figure literal was **not independently transcribed by BOTH**
   visual reviewers — faithfulness is a token-diff against authored `expected_literals`, and reviewers are
   never shown the expected values (no confirmation bias). A beautiful panel with an unconfirmed number
   does not pass. See `fail_s13_a02`.
3. **A cross-frame FALSE drift, caught and corrected.** On page B03 (a parallel 2-up with disjoint casts:
   S03 researcher-only / S04 duo-only) the assembly gate scored "duo identity across panels" = 0 twice
   with **identical** scores — the fingerprint of a broken rubric, not a broken artifact. The bounded loop
   stopped and flagged a human; the human inspected, accepted, and recorded
   `decision_assembly_p_b03_human_override`. The engine was then fixed to be cast-aware. The override node
   is in this trace verbatim — failures are kept as memory.

This is exactly the discipline the comic is *about*: an evaluator that repairs output before scoring
inflates the result — so the production loop refuses to score its own bake.

## Honesty notes

- **Cross-model:** the executor (Claude) never judges its own bake; visual verdicts come from a different
  model family (codex / gemini). No single model self-acquits.
- **Timestamps are logical, not wall-clock.** `Date.now()` is unavailable in the generation sandbox (it
  would break resume determinism), so `created_at` is a placeholder; node order is by attempt id, not real
  time. Do not read the timestamps as a real timeline.
- Absolute paths / usernames are redacted (`image_path` is project-relative; verified 0 absolute paths in
  `nodes/`). See `../REDACTION.md`.

## Files

- `nodes/` — `panel_attempt` / `review` (×3) / `decision` / `failure_mode` JSON nodes (174 total)
- `edges.jsonl` — the graph (`attempt_of`, `reviews`, `decides`, `fails`)
- `active_memory.md` — the live gate criteria + standing lessons
- `validation_report.md` — node counts, schema-validation result, redaction confirmation
