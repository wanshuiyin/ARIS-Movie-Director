# Contributing to ARIS-Movie-Director

🌐 [中文](CONTRIBUTING_CN.md) · **English**

Thanks for helping. This repo's whole thesis is that a generated visual story should be **auditable** — so the
one rule that matters here is: **never let a gate lose its teeth.** A change that makes a wrong/unsourced frame
easier to ship is a regression even if every test still passes. When in doubt, fail closed.

New here? Read the [README](README.md) first (what the two pipelines are), then this. The deterministic
guarantees you must not weaken live in `cli/validate_wiki.py`, `skills/comic-director/scripts/run_comic.py`,
`packages/core/spiral_engine.js`, and `skills/method-figure/scripts/{compile_brief,content_diff,validate_blueprint}.py`.

## Dev setup

```bash
python3 -m pip install -r requirements.txt   # jsonschema (the rest is stdlib)
# Node ≥ 18 for `node --check packages/core/spiral_engine.js`
```

External tools (`codex`, `gemini`, headless `chrome`/`chromium`) are needed only for the **metered** stages
(image bake, cross-model review, SVG rasterization) — **not** for contributing to the deterministic gates.
Check your environment with `python3 cli/preflight.py`.

## The green check — run it before every PR

```bash
bash tests/smoke.sh
```

This is exactly what CI runs (`.github/workflows/ci.yml`). It exercises **only** the no-credit, no-Chrome,
no-network gates: `py_compile` + `node --check`, `validate_wiki` on both examples, `run_comic.py --dry-run`,
`compile_brief` Step-0, `validate_blueprint`, and the regression suite in `tests/test_gates.py`. A PR must keep
it green. The metered stages are deliberately out of CI (they need credentials + a browser).

## What to contribute

| Area | Where | Note |
|---|---|---|
| **Author skills (SOPs)** | `skills/comic-*`, `skills/method-figure` | These are procedures a coding agent *follows* — prose is the product. Keep links resolvable. |
| **Deterministic engines / gates** | `cli/`, `packages/core/`, `skills/*/scripts/` | The teeth. See the hard rules below. |
| **Example projects** | `examples/<name>/` | Must pass `validate_wiki`. |
| **Schemas** | `schemas/`, `skills/method-figure/schemas/` | Keep in sync with the enforcer (drift guard below). |
| **Docs** | `README.md`, `docs/`, skill `references/` | Honesty rules below. |

## Hard rules for engine / gate changes

1. **Keep the two comic engines in sync.** `packages/core/spiral_engine.js` is the **canonical** engine;
   `skills/comic-director/scripts/run_comic.py` is its line-for-line port. A fix to one **must** land in the
   other (the JS engine writes wiki via an `agent()` prompt, so its "fix" is a complete schema skeleton in the
   prompt). A real, recurring bug here was fixing only the Python port.
2. **Don't weaken a fail-closed check without a test proving the new behavior.** Every veto in
   `content_diff.py`, the literal-diff exactness in the panel gate, `compile_brief` traceability, and
   `cfg_usable`/`p0_proof` preflights is load-bearing. If you change one, add/adjust a case in
   `tests/test_gates.py` so the intended behavior is locked.
3. **No model self-acquits.** A baked artifact is judged by a **different model family** + a deterministic diff,
   never by the model that made it. If your change touches correctness, get a cross-model review (e.g. have a
   non-Claude model read the diff) before claiming it's sound. See `protocols/acceptance-gate.md`.
4. **Schema ↔ enforcer stay in lock-step.** `validate_wiki.py` has a drift guard: every `node_type` in
   `schemas/node_schema.json` must have a `PAYLOAD_REQUIRED` entry and vice-versa. Update both together.
5. **Honesty in docs and claims.** This project is picky about wording:
   - "checked against the **authored** `expected_literals`" — *not* "fact-checked the world" (a wrong fact in
     `comic.json` is faithfully reproduced; the gate verifies fidelity to the source of truth, not truth itself).
   - the trace is **inspectable**, not bit-for-bit "reproducible" (image generation isn't deterministic).
   - mark framework-constant text (e.g. a blueprint `rail`) with a `framework:*` source, not a `brief:*` one.
   - don't claim novelty the field already has (see the README "Related work" note).
   - `--strict-author-gates` is an **opt-in production check**, not a default: by design `validate_wiki.py`
     permits bare-locked author nodes for dev/experimentation (CI asserts the fixture passes WITHOUT the flag,
     see `tests/test_gates.py`). A project shipping to release/review **should** run `validate_wiki.py
     --strict-author-gates` in its own checklist and gate every author lock with a `decides`/`reviews` edge —
     but do not claim the default smoke/CI enforces it (it does not).

## Adding an example project

A project plugs in via `examples/<name>/movie.project.json` + a `comic.json` IR + a `wiki/` trace. The minimal
copy target is [`examples/comic_min_author/`](examples/comic_min_author/) (one valid node of each author type).
Before you open the PR:

```bash
python3 cli/validate_wiki.py examples/<name>                 # must PASS
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <P> --panels <S..> --dry-run
```

Do **not** commit generated artifacts (the `build_prompt.py` outputs under `wiki/` — `log.md`,
`prompt_build/`, generated `prompt_*` nodes — are regenerable; keep them out of the diff).

## Pull-request checklist

- [ ] `bash tests/smoke.sh` is green.
- [ ] Touched a gate/engine? Both comic engines updated **and** a `tests/test_gates.py` case covers it.
- [ ] Touched a schema? Enforcer (`validate_wiki.py` `PAYLOAD_REQUIRED` / `EDGE_TYPES`) updated to match.
- [ ] No new doc over-claim; wording follows the honesty rules.
- [ ] Links resolve; no generated/temp files staged.
- [ ] **No secrets and no absolute home paths** (`/Users/...`, `/home/...`) anywhere in the diff — this repo is
      **public**. `validate_wiki` scans wiki payloads for this; double-check scripts/docs too.

## Commits & PRs

- Conventional-ish prefixes: `fix(gates):`, `feat(skill):`, `docs(readme):`, `ci:`, `test:`.
- Keep PRs focused; explain *what guarantee* a gate change preserves or strengthens.
- Be kind and specific in review. The bar is correctness + honesty, not volume.

## Issues & security

- Bugs / ideas → open a GitHub issue with repro steps (a failing `tests/smoke.sh` line is ideal).
- Found a way a wrong/unsourced artifact can pass a gate? That's the highest-value report — please flag it
  (privately if you prefer) rather than open a public exploit-style issue.

By contributing you agree your work is licensed under this repo's [MIT License](LICENSE).
