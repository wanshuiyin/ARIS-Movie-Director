# B08 Production Wiki — the multi-agent loop, as it actually ran

This is the **research-wiki trace** for the comic's centerpiece page (B08 *"The Inflation Audit"*,
panels S12–S15). It is the authentic record of how each panel was produced and judged — the same
spiral-engine active memory the pipeline writes on every gate decision.

## The loop (per panel)

```
generatePanel  — codex bakes the panel from a deterministic content blueprint + the canonical duo
   → panel_gate — 3 INDEPENDENT cross-model reviewers:
        • CC      narrative  (does the panel deliver its story beat?)
        • Gemini  visual     (identity / style / artifacts / baked-text legibility / number transcription)
        • Codex   visual     (a second, different-model-family eye)
   → deterministic JS verdict   (no single model self-acquits)
   → decision node (keep | retry) + a failure_mode node when rejected
```

## What this trace contains (26 nodes)

| panel | outcome | confirmed figure literals |
|---|---|---|
| **S12** | KEEP (a01) | `+6.2` |
| **S13** | a02 **REJECTED** → a01 KEEP | `sanitizer`, `+6.2`, `+1.4` |
| **S14** | KEEP (a01) | `+6.2`, `+1.4`, `+4.8` |
| **S15** | KEEP (a01) | `WARN_corrected`, `+1.4` |

## The real rejection (S13 a02) — why it's kept

The gate is **sound, not a rubber stamp.** Attempt `s13_a02` was **REJECTED** because a required figure
literal was **not independently transcribed by BOTH visual reviewers**. Faithfulness here is a
deterministic *token-diff* against the panel's authored `expected_literals`, and the reviewers are never
shown the expected values (no confirmation bias) — a beautiful panel with an unconfirmed number does not
pass. `fail_s13_a02` records the positive repair invariant fed back into the next bake. (This rejection
also drove a real refinement: the required literals were re-chosen to the *salient* figure numbers
reviewers reliably read, rather than a buried code token.)

This is exactly the discipline the comic is *about*: an evaluator that repairs output before scoring
inflates the result — so the production loop refuses to score its own bake.

## Honesty notes

- **Cross-model:** the executor (Claude) never judges its own bake; verdicts come from a different model family.
- The gate itself was adversarially reviewed (codex gpt-5.5 xhigh, two rounds) and acquitted **PASS**.
- Absolute paths / usernames **redacted** (see `../REDACTION.md`); `image_path` is project-relative.

## Files

- `nodes/` — `panel_attempt` / `review` (×3) / `decision` / `failure_mode` JSON nodes
- `edges.jsonl` — the graph (attempt→panel, review→attempt, decision→attempt, failure→attempt)
- `active_memory.md` — the live gate criteria + the rejection's standing lesson
- `validation_report.md` — node counts, final-decision check, redaction confirmation
