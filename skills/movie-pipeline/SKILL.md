---
name: movie-pipeline
description: End-to-end Pipeline A in ONE slash-command — turn a fuzzy story idea into a cross-model-audited, image-based movie + a clickable viewer. Chains comic-author (Phase 1 — intent→style→outline draft→provisional storyboard→assets→final locks→blueprints→prompts→comic.json) → the zero-credit p0_proof spending gate (agent fan-out + run_p0_proof.py mints the digest-bound certificate) → comic-director (Phase 2/3 — the agent-sidecar bake spiral, page by page → HTML viewer). Two hard HUMAN gates (intent + outline) pause for approval; everything else is agent-driven + cross-model gated. This is the slash-command entry, like ARIS's /research-pipeline — an AGENT workflow, NOT a shell binary. Use when the user says "/movie-pipeline '…'", "做个电影/漫画 end-to-end", "from this idea make the whole movie", "long-horizon image-based movie generation".
---

# movie-pipeline — Pipeline A, end-to-end (one slash-command)

## 1 · Scope
The whole of Figure 1 as ONE agent workflow: a fuzzy idea → a cross-model-audited, image-based movie + a
clickable viewer. `/movie-pipeline "«your fuzzy idea»"` — and your coding agent (Claude, Codex, …) drives the
chain below, pausing only at the two human story gates. **"One command" = one slash-command an agent RUNS —
not a deterministic shell binary** (the `/research-pipeline` paradigm): it needs a coding-agent runtime, it is
non-deterministic, and a skipped step is *safe* because each layer consumes the prior *locked* artifact — a
missed step leaves the next gate's input unresolved and it **fails closed**, never ships something wrong.

## 2 · Who does what (roles / boundary)
| Actor | Does | Never does |
|---|---|---|
| **Human** | approves intent + outline; adjudicates `needs_human`/flagged panels | per-panel retries (the spiral's job) |
| **Agent** (Claude runtime) | authors Phase 1; runs the P0 fan-out reviews; services the bake sidecar; iterates pages | acquits its own layer (author family can't self-acquit) |
| **`mcp__codex__codex` sidecar** | the ONLY real bake primitive (Codex native image tool) | judge its own output |
| **Deterministic CLIs** | `run_p0_proof.py` (mints the P0 cert), `run_comic.py` (orchestrates; verdict math is deterministic; gates shell the `codex`/`gemini` CLIs), `validate_wiki.py`, `build_comic.py` | bake (that's delegated to the agent sidecar) |
| **CI** | `--dry-run` + `validate_wiki` + `build_comic` re-render + `tests/` (see §11) | bake, or acquit quality |

## 3 · Phase contract
| Phase | Entry artifact | Exit artifact | Consumer | Gate |
|---|---|---|---|---|
| 1 author | fuzzy idea | schema-valid `comic.json` + locked wiki nodes | P0 gate | per-layer cross-model `--gate` + 2 human gates |
| P0 proof | compiled `comic.json` | digest-bound `decision:p0_proof_*` node | `run_comic.py` preflight | `run_p0_proof.py` quorum (§6) |
| 2 bake | `comic.json` + current P0 cert | KEEP'd panels, wiki trace, updated `comic.json` | assembly / viewer | `panel_gate` + `assembly_gate` |
| 3 ship | shippable run report | `outputs/index.html` | human | `--finalize` viewer build rc=0 (exit 4 on fail) |

## 4 · New-project bootstrap
Copy the author-node shapes from [`examples/comic_min_author/`](../../examples/comic_min_author/); the full
reference run (198-node trace) is [`examples/comic_m3_audit/`](../../examples/comic_m3_audit/). Give the
project a `movie.project.json` with `identity_ref` — `run_comic.py` reads the canonical identity ref from it
(fallback: `assets/duo_canonical_ref_v001.png`). Prereqs: `codex` + `gemini` CLIs + headless Chrome
(`$ARIS_CHROME` > macOS app path > PATH). `python3 cli/preflight.py` checks the reviewer/render CLIs ONLY —
it does NOT verify the `mcp__codex__codex` sidecar tool or an agent runtime, which the real bake needs.

## 5 · Phase 1 — author the source of truth ([`comic-author`](../comic-author/SKILL.md))
The DAG (each arrow is a cross-model `--gate`; two steps are HUMAN):
1. intent *(HUMAN gate)* → style lock → **OUTLINE_DRAFT_VALID** — the outline gate validates
   NARRATIVE + CONTINUITY + safety only; it does **not** require referenced assets to be locked, it requires
   every referenced `asset_id` to be **declared** with a complete, generatable request.
2. **outline approval** *(HUMAN gate)* → **provisional storyboard** (structural pass; may reference draft
   assets) → `consolidated_asset_requests`.
3. **asset generation + review** → assets **LOCKED** → **OUTLINE_FINAL_LOCK** (cheap re-check: the locked
   assets still match the approved outline) → storyboard **FINAL asset-resolution validation**.
4. blueprints — **the hard locked-asset barrier sits HERE, before blueprint authoring** → prompts →
   schema-valid `comic.json`.

This staged order is the contract: it replaces the old single-stage deadlock (an outline gate demanding
locked assets that depend on a storyboard that depends on a locked outline). Draft-then-final-lock is how the
cycle is broken; the asset barrier never moves past the blueprint boundary.

## 6 · P0 spending gate — zero PANEL credit before proof
**Scope, honestly:** the P0 cert gates the **Phase-2/3 PANEL bakes** (every metered `run_comic.py` run). It
cannot gate Phase 1: the raster ASSET refs (S4) are *also paid* sidecar bakes and land **before** any P0 cert
exists (assets must lock before `comic.json` compiles). Those pre-P0 spends are gated instead by the
cross-model [`comic-asset-review-loop`](../comic-asset-review-loop/SKILL.md) + the single-source collision
gate.

Three-step handoff (never conflate them):
1. **Agent fan-out** ([`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) `--gate p0_proof` — an
   agent skill, not a binary): ≥2 cross-model reviews of the compiled `comic.json` + machinery, each written
   as a JSON file `{family: "openai"|"google", verdict, blockers: [], comic_sha}`.
2. **Deterministic mint** — `run_p0_proof.py` verifies and mints; it never runs a reviewer itself:
   ```bash
   python3 skills/comic-cross-layer-gate/scripts/run_p0_proof.py \
       --project examples/<name> --target <compile/intent anchor node_id> \
       --reviews p0_codex.json p0_gemini.json
   ```
   Quorum = BOTH non-author families `{openai, google}` PASS (`blockers == []`, affirmative verdict) on the
   SAME `comic_sha` (sha256 of the exact `comic.json` bytes). Parseable alone is not quorum; a
   missing/unparseable/timed-out review **does not count** — never proceed on timeout (fail-closed). On pass
   it computes `comic_sha` + `bake_plan_sha` (= `pickup_image.bake_plan_digest(run_comic.get_bake_plan())`)
   and atomically writes `decision:p0_proof_<slug>_<utcstamp>` (node_type `decision`, status `final`, verdict
   `advance`, both digests in the payload) into `wiki/nodes/`.
3. **Preflight consume** — `run_comic.py` scans the wiki for that node and REJECTS any cert whose
   `comic_sha`/`bake_plan_sha` is missing or mismatches the CURRENT `comic.json` + bake plan: a stale cert
   after any `comic.json` edit fail-closes with a message pointing back to `run_p0_proof.py`. The JS engine
   (`packages/core/spiral_engine.js`) never scans the wiki — it takes the boolean arg `p0ProofClean:true`
   (skip: `skipP0Proof:true`); only `run_comic.py` does the node scan + digest verification.
`--skip-p0-proof` bakes UNAUDITED and forces the run non-shippable (`p0_skipped:true`).

## 7 · Phase 2/3 — the audited spiral, page by page ([`comic-director`](../comic-director/SKILL.md))
**There is NO whole-movie driver yet** — `run_comic.py` takes exactly one `--page` + its `--panels`; the
agent iterates `comic.json`'s `pages[]` itself (a `run_movie.py` project driver is planned, not shipped):
```bash
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> \
    --page <PAGE> --panels S01,S02 [--bake-mode=agent] [--finalize] [--dry-run]
```
Per panel: render the content-SVG blueprint → **agent `mcp__codex__codex` sidecar bake** → 3-reviewer
`panel_gate` (blind transcribe → deterministic token-diff; a `+6.25` where `+6.2` is expected is rejected) →
KEEP / RETRY (≤4) / cross-frame rollback → page `assembly_gate` (≤6 rounds; a panel drifting ≥2 rounds
escalates to an author-layer `rewrite_storyboard`, because a re-bake can't fix a spec problem) → project to
`comic.json` → `--finalize` builds the single-file viewer and **FAILS (exit 4) if the build rc≠0**.

**Per-page cadence**: every KEEP writes `image_path`/`active_attempt_id` back into `comic.json`, which
changes its bytes — so the P0 cert goes stale between pages by design. Before each subsequent paid page run:
re-run the zero-credit fan-out on the current `comic.json` + re-mint via `run_p0_proof.py`. Cheap, and it is
what "the cert acquits exactly what you are about to spend on" means.

**Model claims, honestly**: the bake model is pinned `gpt-5.5` + `xhigh` as a single compat default in
`run_comic.get_bake_plan()` (contract `bakereq/v1`; config-driven override plumbing is planned, not shipped —
changing any knob invalidates prior P0 certs via `bake_plan_sha`). The Codex CLI reviewers pin NO model —
they follow the local codex config (currently `gpt-5.6-sol`) at effort `xhigh` (`--review-effort`); Gemini
reviewers run `auto-gemini-3`. The narrative "cc" reviewer slot currently shells the `codex` CLI and its wiki
provenance honestly records `"openai"` (a configurable `--narrative-reviewer` is planned, not implemented);
cross-family acquittal vs the Claude author still holds via Gemini + Codex. There is no `--effort` flag on
`run_comic.py` or `run_spiral.py` — only `--review-effort` exists; bake effort lives in the P0-bound plan.

## 8 · The bake sidecar (pointer, not a copy)
The bake is the skill agent calling `mcp__codex__codex`: the core writes `<out>.bakereq.json`, the agent
services it with exactly those params and writes `<out>.bakestatus.json` (bounded raw `mcp_output` +
`request_id` verbatim — both mandatory), and the core verifies the explicit out-path via
`pickup_image.py --out-existing`. The full request/status field contract + agent-wrapper SOP lives in ONE
place: [`comic-director` §"Bake seam contract" + §"Who runs `--bake-mode=agent`"](../comic-director/SKILL.md)
— do not re-derive it here or anywhere else.

## 9 · Failure matrix
| Failure | Signal | SOP |
|---|---|---|
| no/stale P0 cert | FAIL-CLOSED exit before any panel spend | fan-out + re-mint via `run_p0_proof.py` on the CURRENT `comic.json` |
| bake timeout / wrapper missing | `generation_failed`, `failure_kind:"other"`, "is the agent wrapper running?" | start/fix the sidecar wrapper; each failure consumes one of the 4 panel attempts |
| throttle (429 / capacity) | `throttled:true`, exit 2, `fresh_run_required` | wait for cooldown → **FRESH run** for the remaining panels; never reuse cached state |
| flagged panel (attempts exhausted) | `needs_human`, exit 3 | human adjudicates; non-shippable until resolved |
| assembly drift | rollback rounds ≤6; ≥2 strikes → `rewrite_storyboard` | re-bake drifters; escalation = author-layer fix, not more bakes |
| viewer build failure | `finalize` FAILED, exit 4, `finalize:false` | fix the build; a broken viewer never reads as a successful finalize |

## 10 · Resume / fresh-run SOP
Throttle ⇒ fresh run for the remaining panels of that page (the run report names the resume panel); flagged /
`needs_human` panels are non-shippable until a human decides. A crashed run is re-run per page — KEEP'd
panels are already projected into `comic.json`, and the P0 digest binding (§7) tells you whether the cert
must be re-minted first (after any `comic.json` change: yes).

## 11 · CI vs agent boundary
Only these are agent-free (what `tests/smoke.sh` + CI actually exercise):
| Lane | Command | Agent needed? |
|---|---|---|
| CI | `run_comic.py --dry-run` (zero credit; prints bake prompts + validates cfg) | no |
| CI | `python3 cli/validate_wiki.py <project>` | no |
| CI | `python3 packages/viewer/build_comic.py <project>` (re-render from existing `comic.json`) | no |
| CI | `tests/test_gates.py` + `tests/smoke.sh` | no |
| agent | ANY real bake run — **including `--finalize`** (it is a flag on a bake run) | **YES** — the `mcp__codex__codex` sidecar wrapper |

## 12 · Ship checklist
- [ ] Every page's run report: `shippable:true`, `flagged_for_human` empty, all kept panels `page_accepted`.
- [ ] `p0_skipped:false` on every run — `--skip-p0-proof` was never used.
- [ ] Every paid run started from a P0 cert whose digests matched that run's exact `comic.json` + bake plan.
- [ ] `--finalize` exited 0 with `finalize:true` (viewer build rc=0) → `examples/<name>/outputs/index.html`.
- [ ] Optionally [`comic-blind-comparison-review`](../comic-blind-comparison-review/SKILL.md) double-blind
      A/Bs it vs a naive one-shot baseline to prove the pipeline earned its cost.

## Protocols
[`acceptance-gate`](../../protocols/acceptance-gate.md) — the human gates intent+outline; a different model family
acquits the rest (loop can DRIVE, can't ACQUIT) · [`artifact-integrity`](../../protocols/artifact-integrity.md) —
the agent that authors a layer never judges its own layer · [`reviewer-independence`](../../protocols/reviewer-independence.md)
· [`external-cadence`](../../protocols/external-cadence.md).
