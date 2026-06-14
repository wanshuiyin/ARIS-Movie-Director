---
name: comic-cross-layer-gate
description: The ONE parameterized score-fuser for EVERY comic-author authoring gate — `--gate intent|outline|asset|storyboard|blueprint|continuity|p0_proof|compile`. A single fuser (not a per-layer split) prevents drift. It NEVER re-runs a reviewer; it collects the reviewer score-nodes already on the wiki (via `reviews` edges), fuses them deterministically (min-fuse per dim, max for inverted dims, SKIP missing dims — never substitute 0), then a Codex gpt-5.5 xhigh adjudicator that sees ONLY structured inputs (scores + tags + raw artifact PATHS + verbatim source context + verbatim rubric — NEVER reviewer prose) makes an asymmetric call (threshold HARD-vetoes "advance"; Codex SOFT-vetoes everything else). The `--gate p0_proof` mode is the zero-credit pre-production proof: a text-only cross-model adversarial review of the pipeline's CODE + IR-CONTRACT + ENGINE state-machine that MUST clear all blockers BEFORE a single metered image-generation credit is spent. Use when a sibling step (intent-parser, outline-creator, asset-review-loop, storyboard-creator, blueprint-author, continuity-audit, json-compiler) defers its acquittal to "the gate", or the user says "过 gate", "cross-layer gate", "审这一层", "p0 proof", "证明流水线再花钱".
---

# comic-cross-layer-gate — the Universal Authoring Score-Fuser + the Zero-Credit P0 Proof (Phase 1)

The **acquittal organ of the [`comic-author`](../comic-author/SKILL.md) suite**. Every authoring step
(intent → style → outline → asset → storyboard → blueprint → continuity → the compiled `comic.json`) is a
*generator*; **none of them acquits itself**. They each emit their node(s), fan out independent reviewers, and
then **defer to this one skill** to fuse the scores into a verdict, mint the audit trail, and flip the target's
`status`. It is the image-comic port of aris_movie's 6-gate adversarial decision skill — but folded into **one
parameterized fuser** (Codex's single-fuser design, against the per-layer split that *drifts*: six near-copies
diverge, one fuser stays honest). The downstream per-panel `panel_gate` / page `assembly_gate` are NOT this
skill — those live in [`packages/core/spiral_engine.js`](../../packages/core/spiral_engine.js) and run at bake
time; this skill is the **authoring-side, pre-bake** gate that decides whether a *spec* may advance.

> **Cardinal lesson, landed as a guard not prose:** *identical scores across rounds = the judge is broken —
> audit the rubric, do not regenerate the artifact* (memory: `feedback_gate_identical_scores_judge_broken`).
> Concretely: this gate carries a `_score_fingerprint` in every `decision` node; if round N's fused per-dim
> vector equals round N−1's **after the artifact changed**, the gate **HALTS and flags `judge_suspect`** —
> the rubric (this skill), not the spec, is the suspect. A gate that emits the same verdict regardless of the
> work is worse than no gate.

```text
  upstream step emits node(s) + fans out independent reviewers (writes review:* score-nodes + `reviews` edges)
                              │
   comic-cross-layer-gate <target_node_id> --gate <kind>
                              ▼
   ⓪ PRE-CHECK   structural facts the GATE computes (asset-resolve / policy / count-band / continuity) — RAW, not opinion
                              ▼
   ① COLLECT     reviewer score-nodes via `reviews` edges — NEVER re-run a reviewer; hard-fail if none
                              ▼
   ② THRESHOLD   per-dim min-fuse (max for inverted dims); SKIP missing dims (NEVER 0-substitute); per-gate floor → threshold_verdict
                              ▼
   ③ ADJUDICATE  Codex gpt-5.5 xhigh — sees ONLY {scores + failure_mode tags + threshold_block + raw PATHS + ≤200w verbatim source + verbatim rubric}
                              ▼               (NEVER reviewer prose / notes / overall — that is the contamination vector)
   ④ ASYMMETRIC  threshold HARD-VETO over "advance"; Codex SOFT-VETO over everything else
                              ▼
   ⑤ WRITE       decision node (full audit) + (on FAIL only) a positive-invariant failure_mode the NEXT step preloads as a banlist
                              ▼
   ⑥ FLIP        target status → locked (advance) · under_review (needs-work) · rejected (terminal) ;  stdout last line: VERDICT=<v> GATE=<kind> TARGET=<id>
```

The `--gate p0_proof` branch is a different shape (a text-only adversarial *review* of the pipeline machinery,
not a score-fuse over a spec) — it is documented in its own section below. It is the **single most important
contract this skill owns**: it runs AFTER [`comic-json-compiler`](../comic-json-compiler/SKILL.md) and
**BEFORE** any metered `codex image_gen` bake, costs **zero generation credits**, and must clear all blockers
or the spiral is forbidden to spend a credit.

## Constants
- **GATE KINDS** = `intent | outline | asset | storyboard | blueprint | continuity | p0_proof | compile`. The
  legal verdict set is **per-gate** (below) and enforced — a verdict outside a gate's set is a hard error (the
  `intent` gate can never emit `keep`; the `asset` gate can emit `locked`, the `intent` gate cannot). The legal
  node `status` tokens a FLIP may write are ONLY `{draft, pending, under_review, locked, rejected, superseded,
  active, complete, final}` (schema enum) — a *verdict* (`revise`/`regenerate`/`fallback`) is never a status.
- **REVIEWERS** (collected, never re-run here): **Codex `gpt-5.5` `model_reasoning_effort: xhigh`** for
  every gate's ambiguity / correctness / logic pass; **Gemini `auto-gemini-3`** wherever a second family or a
  *visual* read is needed (image inputs, UX/design). Never downgrade the tier
  ([`reviewer-routing`](../../protocols/reviewer-routing.md)).
- **ADJUDICATOR** = **Codex `gpt-5.5` `xhigh`**, fed ONLY structured inputs (§③). Its `effort` is **always
  xhigh** regardless of the run's `--effort` — effort widens fan-out, it never weakens the judge.
- **FUSE RULE** = **min** per dimension (most-pessimistic), **EXCEPT inverted dims** (`artifact_severity`,
  `*_severity`, anything where higher = worse) use **max**; **SKIP a dim no reviewer scored** (filter the
  `null`s) — **NEVER substitute 0** (the v1.0 bug: a lite reviewer leaving a dim unscored must neither slip an
  advance nor force a fail).
- **ASYMMETRIC TRUST** = the deterministic threshold has **HARD VETO over "advance"** (Codex cannot overrule
  `approve`/`locked` if the deterministic floor failed); Codex has **SOFT VETO over everything else** (a Codex
  `revise` overrules a threshold `approve`). Structural facts (§⓪) **also hard-veto advance**.
- **CAPS** — `MAX_ASSET_REGEN = 4` then escalate the asset gate to the outline gate (`abandon_shot`);
  re-gate (re-vote) caps fold into the calling step's attempt budget. The **`准 ×3`** convention (asset gate,
  owned by [`comic-asset-review-loop`](../comic-asset-review-loop/SKILL.md)): a `locked` verdict requires
  **cross-model UNANIMITY in the SAME round** — CC **and** Gemini **and** Codex all approve the asset that round
  (≥3 distinct reviewer families lock-pass together). Fewer than 3 families approving → `regenerate
  --another-voter` (**re-vote to reach the third family, not re-bake**); a family's hard-fail → re-bake. (NOT
  "three consecutive rounds" — that aris_movie video port is wrong for this repo; the owner is same-round unanimity.)
- **P0 GATE THRESHOLD** = `blockers.length == 0` — a **HARD HALT**. Zero image-generation credits are spent
  until clear. The review is deliberately text-only → not rate-limited → free.
- **CODEX UNAVAILABLE** → emit the **threshold-only provisional** verdict with `_confidence: "low"`, exit code
  2, and **skip** `failure_mode` compilation. Malformed adjudicator JSON → `codex-reply` retry ×2, then fall
  back to threshold-only.
- **OUTPUT** — a `decision` node in `wiki/nodes/`, the `decides` edge, a `review-tracing` entry per collected
  reviewer + the adjudicator, and (on a FAIL verdict only) a `failure_mode` node. Final stdout line is
  **EXACTLY** `VERDICT=<v> GATE=<kind> TARGET=<id>` for the caller to parse.

## Input contract — what the gate is given, what it refuses
The direct input is **a `target_node_id` + a `--gate <kind>`**. The gate **reads from the wiki**, it is not
handed prose:
- **It NEVER re-runs a reviewer.** The upstream step already fanned out and wrote `review:*` score-nodes with
  `reviews` edges → the target. The gate **collects those nodes**; if **zero** reviews are attached, it
  **hard-fails** (`no reviews — gate is a score-fuser, not a reviewer`). This is the load-bearing separation:
  the executor that authored the spec must not also be the one whose read of it acquits it.
- **The adjudicator sees scores + failure-mode tags + raw artifact PATHS + a ≤200-word VERBATIM source slice +
  the VERBATIM rubric — and NOTHING else.** It **never** sees a reviewer's prose, `notes`, `evidence`,
  `overall_assessment`, or `rationale` ([`reviewer-independence`](../../protocols/reviewer-independence.md)).
  Reviewer prose is the contamination vector; forwarding it re-introduces the correlated blind spot
  cross-model review exists to break. *(Structural facts in §⓪ are an exception — they are RAW artifacts the
  gate itself computed, not reviewer opinion, so forwarding them does not violate independence.)*
- **The upstream gate state machine is `verdict ∈ {approve, locked, revise, regenerate, fallback}`** (plus the
  asset-gate-only `abandon_shot`). Each reviewer call that feeds this gate gets file paths + an explicit
  **`=== EXTERNAL CONTEXT (advisory) ===`** fence around any cross-cutting context — never the author's
  interpretation. The fence is what keeps "here is the situation" from becoming "here is what to conclude".

## The universal architecture (every `--gate` except `p0_proof`)
Ported verbatim from the aris_movie 6-gate skill; the deterministic-JS fuse pattern is the same one the engine
already proves in [`packages/core/spiral_engine.js:59`](../../packages/core/spiral_engine.js) (`panelVerdict`).

### ⓪ Pre-check — the structural facts the gate computes
Before touching reviewers, compute the **raw artifacts** (filesystem facts, not opinions) the gate hard-vetoes
on. These differ per gate (see each rubric) but the shape is constant: *resolve every referenced asset_id*,
*every asset is `status: locked`*, *policy fields match expected*, *count in band*, *continuity links
well-formed (no dangling / out-of-order / cycle)*. Any non-empty violation set → **`revise` regardless of
reviewer scores OR Codex** ("structural failures cannot be voted-around"). Record each as
`_unresolved_asset_refs` / `_policy_violations` / `_count_band` / `_continuity_breaks` in the decision audit.

### ① Collect — reviewer score-nodes, never re-run
Walk `reviews` edges into `target_node_id`; load each `review:*` node's `payload.review_scores`. Build
`per_reviewer = {reviewer: {dim: score, ...}, failure_mode_tags: [...]}`. **Hard-fail** if the set is empty.

### ② Threshold — deterministic per-dim fuse
For each rubric dimension, fuse across reviewers with **min** (or **max** for an inverted dim), **skipping**
any reviewer that left it `null`. Apply the per-gate floor (each rubric below). Yield `threshold_verdict ∈
{advance, revise}` + a `_cited_dimensions` map of every fused value. This is mechanical and reproducible — a
fresh reviewer can re-derive it from the table alone.

### ③ Adjudicate — Codex, structured inputs only
Call Codex `gpt-5.5 xhigh` with EXACTLY: `per_reviewer` scores, `failure_mode_tags`, the `threshold_block`
(the fused values + the floor), the **raw artifact PATHS**, a **≤200-word verbatim slice** of the source node
(not a summary — a literal excerpt), and the **verbatim rubric** for this gate. Ask for a verdict in this
gate's legal set + a one-line `confidence` + the single most important fix. **Trace** the call
([`review-tracing`](../../protocols/review-tracing.md)).

### ④ Asymmetric cross-check
- `threshold_verdict == revise` → the final verdict is a FAIL verdict **no matter what Codex said** (threshold
  hard-vetoes advance).
- `threshold_verdict == advance` AND Codex returns a FAIL verdict → **Codex's FAIL wins** (Codex soft-vetoes
  advance).
- `threshold_verdict == advance` AND Codex advances → **ADVANCE** (`approve` / `locked`, per gate).
- Record `_threshold_verdict`, `_codex_verdict`, `_disagreement` (bool), `_confidence`.

### ⑤ Write — decision + (on FAIL only) a positive-invariant failure_mode
Write a `decision` node (full audit). On any FAIL verdict, compile **one** `failure_mode` node whose
`repair_pattern` is a **POSITIVE INVARIANT** ("force a `status:locked` ref for every must_show asset", NOT "no
draft assets") — diffusion *and* the next authoring step focus on what you *mention*, so state the desired
target, not the ban (negative patterns are only for explicit banlists). Default scope is **movie-local**;
`engine-global` needs explicit grounding (an over-broad failure_mode poisons cross-project banlists). The
**next** authoring step preloads this node as its banlist — the spiral's learning loop.

### ⑥ Flip + emit
Flip `target.status` (`locked` on advance for asset/storyboard/etc.; leave/`rejected` on a terminal fail).
Append the `decides` edge. Print the parse line.

## EXACT gates (dimensions · thresholds · vetoes) — ported from the aris_movie source
Every reviewer scores each dim **0–5**. "ADVANCE" verdict in CAPS. Advisory dims do NOT block advance; they
ride into the decision audit and the adjudicator's context.

### `--gate intent` → verdicts `{approve, revise}`
- **ADVANCE (`APPROVE`) iff** `completeness ≥ 4` **AND** `safety_flag_coverage ≥ 4`.
- Advisory: `clarity`, `scope_feasibility`.
- **EXTRA veto:** if the `intent_spec.payload.confidence < 0.6`, **OR** any unresolved high-impact uncertainty
  remains, downgrade `approve → revise` even when both floor dims pass (low-confidence / unresolved intent must
  not lock silently). This is the EXACT predicate [`comic-intent-parser`](../comic-intent-parser/SKILL.md) must
  quote — no `0.5`/`0.6` drift between the parser's stated gate and the gate that actually runs.
- *Note:* the **user-approval** gate for intent is a separate HARD human gate owned by
  [`comic-intent-parser`](../comic-intent-parser/SKILL.md) step ⑥ — this gate is the cross-model adjudication,
  not the human sign-off.

### `--gate outline` → verdicts `{approve, revise}`
- **Pre-check (HARD):** every referenced `asset_id` (scene / character / prop / must_show in the
  `*_asset_ids` lists) must **resolve AND be `status: locked`**, else hard-fail with the missing-asset list
  ("outline cannot be approved with draft assets").
- **ADVANCE (`APPROVE`) iff** `min(coverage, identity_lock_feasibility, scene_lock_feasibility) ≥ 4` **AND**
  `safety_ip ≥ 4`.
- Advisory: `asset_promptability`, `audio_plan`.

### `--gate asset` → verdicts `{approve, regenerate, locked, abandon_shot}`
- **LOCK (`LOCKED`) iff** `identity_lock_satisfied ≥ 4` **AND** `ref_quality ≥ 4` **AND** `bg_isolation ≥ 4`
  **AND** `safety_ip ≥ 4` — **and the `准 ×3` rule holds** (cross-model unanimity in the SAME round: CC AND
  Gemini AND Codex all lock-pass that round; fewer than 3 families approving → `regenerate --another-voter` =
  re-vote to reach the third family, not re-bake; a family's hard-fail → re-bake). See Constants.
- Advisory: `reuse_readiness`.
- **Cross-check (RAW):** `output_ref` exists on disk **AND** its `sha256` matches the node **AND** the
  `data_url` is non-empty — any mismatch hard-vetoes lock.
- **Cap:** `MAX_ASSET_REGEN = 4` → escalate to the outline gate (`abandon_shot`).

### `--gate storyboard` → verdicts `{approve, revise}` — STRUCTURAL, CC-only (no visual reviewer; no pixels yet)
This is the **`comic.json` structural validator** (it supersedes the lone `check_asset_collisions.py`). The
four structural dims are **FILE-SYSTEM FACTS the gate computes**, not reviewer opinion:
- **`panel_assets_referenceable`** — every asset ref in each *panel* resolves **and** is `locked`.
- **`global_policies_valid`** — `global_policies` fields match expected (e.g. text-mode rules present;
  mirror-lock policy present; page-order authority declared).
- **`panel_count_band_aligned`** — panels-per-page in band per target tier `{mvp:(2,2), demo:(4,6),
  longform:(10,12)}` (in-range = 5, off-by-one = 3, further = ≤2), AND the `TOTALS` line reconciles (Σ
  panels-per-page == panel count; NEW + reused == total).
- **`continuity_chain_well_formed`** — the MOTIF STATE TABLE has one row per panel; links have no
  dangling / out-of-order / cycle; every per-panel `motifs` field agrees with its table row.
- **ADVANCE (`APPROVE`) iff ALL FOUR ≥ 4.**
- **STRUCTURAL HARD VETO:** any non-empty `_unresolved_asset_refs` / `_policy_violations` /
  `_continuity_breaks`, or an out-of-band `_panel_count_band`, forces `revise` **regardless of reviewer scores
  OR Codex**. *(Plus the comic-specific structural vetoes the storyboard step also asks for: DDL
  non-monotonic; bounce-uniqueness broken; the two metric columns co-mingling; a DONE panel retro-edited; the
  storyboard page order disagreeing with the compiled `comic.json` page order — the storyboard is the
  authority.)*

### `--gate blueprint` (the IMAGE analog of aris_movie's `frame_condition` gate) → verdicts `{approve, revise, fallback}`
aris_movie's `frame_condition` gate is VIDEO-flavored (`action_freeze`, `harmonization`); the IMAGE analog
drops the motion dims and asks instead: **"is this panel's `condition.content_svg` + `identity_ref` + `scene`
buildable?"**
- **ADVANCE (`APPROVE`) iff** `refs_present ≥ 4` **AND** `spatial_correctness ≥ 4` **AND**
  `blueprint_renders ≥ 4` (the SVG rasterizes to a non-empty PNG — a RAW pre-check, not a vote).
- `text_preservation` required **only** when the panel has whitelisted baked text.
- `safezone_quality` (html panels) **< 3** while the floor otherwise passes → **`fallback`** = route the
  panel's text to the HTML overlay (a route switch, not a regen).
- **Cap:** `MAX_BLUEPRINT_REGEN = 3` → escalate to rewrite the panel_spec.

### `--gate continuity` → verdicts `{approve, revise}`
Adjudicates the [`comic-continuity-audit`](../comic-continuity-audit/SKILL.md) read against the
`motif_ledger`. Dims (all **≥ 4** to ADVANCE):
- **`ledger_row_complete`** — one MOTIF-table row per panel; no missing variable.
- **`invariants_hold`** — the declarative predicates verify against the table: `ddl_monotonic_non_increasing`,
  `bounce_single_max` (S02 = the film's ONLY MAX; no post-fall peak), `metric_columns_disjoint` (no
  `claim_delta` value in the `exact_parse` column or vice-versa).
- **`mirror_locks_paired`** — each paired constraint (REJECT ↔ ACCEPT same stamp geometry; S02-MAX ↔
  S21-smallest; S16b labeled star-map ↔ S22 wordless twin from the same node JSON, `禁目测`) is present and
  consistent.
- **`design_aware`** — MOTIF-vs-ENV disambiguation is honored: only continuity-bearing instances are tracked;
  an intended absence / a tagged `env` prop is **not** flagged as drift (`absence ≠ drift`).
- **Structural HARD VETO:** any invariant violation forces `revise` (invariants are machine-checkable
  predicates, not vibes).

### `--gate compile` → verdicts `{approve, revise}` — DETERMINISTIC (no reviewer fan-out; the scripts ARE the judge)
The compiled-`comic.json` acquittal that [`comic-json-compiler`](../comic-json-compiler/SKILL.md) defers to.
Unlike every other gate this one is **purely deterministic** — NO `review:*` nodes, NO Codex adjudication, so
§① (collect) is skipped and the "hard-fail if zero reviews" rule does NOT apply. It PASSES (`approve`) iff
**both real scripts exit 0**, else `revise` carrying their stderr as the blocker list:
- `python3 skills/comic-director/scripts/run_comic.py --project <dir> --page <P> --panels <ids> --dry-run` —
  validates the comic.json shape, that every `text_mode:"baked"` figure-panel carries ascii
  `condition.expected_literals`, and prints each concrete bake prompt (no placeholders). **`--panels` is
  required** by `run_comic.py` (argparse `required=True`), so run this **once per page** in `pages[]` with that
  page's panel ids — omitting `--panels` exits non-zero (a false blocker).
- `python3 cli/validate_wiki.py <dir>` — node/edge/payload/privacy/node_id conformance against `node_schema.json`.
There is **no `reconcile_pages.py`** (it never existed) — these on-disk scripts are the entire deterministic
core. PASS (`approve`) iff EVERY per-page `run_comic.py` AND `validate_wiki.py` exit 0. Record all exit codes +
any stderr in the decision audit. The §⑥ FLIP target is the schema-valid `decision:compile_<slug>` wiki node
this gate writes (`status: final`) — **NOT `comic.json`**, which is a file, not a wiki node (it has no legal
node_id prefix, carries no `wiki_node_id`, and can never be an edge endpoint).

> The folded-already clip gate (the 11-dim `panel_gate`: `KEEP iff min(narrative_intent, plot_continuity) ≥ 4
> AND artifact_severity < 4 [max-fused] AND safety_ip ≥ 4`; style/visual dims ADVISORY) and the page
> `assembly_gate` are **NOT re-implemented here** — they run at bake time inside
> [`packages/core/spiral_engine.js`](../../packages/core/spiral_engine.js). This skill is the authoring-side
> gate; the engine is the artifact-side gate. They share the same fuse discipline.

## `--gate p0_proof` — the zero-credit visual / code proof (the one contract that gates ALL spending)
Runs **AFTER** [`comic-json-compiler`](../comic-json-compiler/SKILL.md), **BEFORE** any metered image
generation. It is a **text-only cross-model adversarial review** of the pipeline machinery the executor
authored solo — distinct from `experiment-integrity` (audits results after the fact) and from the per-unit
clip/panel gate (audits generated artifacts). It is a **pre-production correctness proof that is deliberately
free** (text review, not `image_gen` → not rate-limited). Ported verbatim from
[`examples/comic_m3_audit/workflows/p0-review.js`](../../examples/comic_m3_audit/workflows/p0-review.js).

**Fan out 3 watchdog-bounded CLI reviewers, each `cat`'ing the REAL files into its prompt (never a Claude
summary), each a DIFFERENT model family from the Claude author:**
1. **`codex` on CODE** — the build script + the viewer: base64 inlining, `</` escaping in the JSON-in-`<script>`
   blob, missing-image handling, path resolution, the locale (`T()`) toggle, bubble positioning, **XSS via
   `innerHTML`** of `T()`, `?p=` bounds.
2. **`codex` on ENGINE LOGIC** — `spiral_engine.js`: the `panelVerdict` formula (deadlock / wrong-keep /
   skip-missing-dim / disagree gate), the retry/rollback/caps state machine (infinite-loop risk, rollback
   target math, `kept[]` filtering, `localByPanel` reset), `generatePanel`'s `image_gen` + the
   `gen_failed`/rate-limit path, the gate prompts eliciting **parseable** JSON, the `REPO + "/" + REPO` path
   hack, `Promise.all` races.
3. **`gemini` on DESIGN / CONTRACT / UX** — is `ART_BIBLE.md` an **executable convergence target** for the
   panel_gate? Does the `comic.json` IR scale to 24 panels + bilingual + 3 `text_mode`s? The viewer reading
   experience? Drift from the design doc?

**Gate schema `FIND` (required `[reviewer, blockers, should_fix, overall]`):** `blockers[]` and `should_fix[]`
are arrays of `{file, issue, fix}` — **all three required per item** (a blocker with no concrete fix is not a
blocker, it is a complaint); plus `nice[]` and a one-line `overall`. Synthesis dedups, drops invalid/duplicate
points (noting the drop), **orders BLOCKER > SHOULD > NICE**, adds `blocker_count` / `should_count`, and
returns the single-most-important fix.

**THRESHOLD: `blockers.length == 0` — HARD HALT.** Clear every blocker, re-run, and only then may the spiral
spend its first `codex image_gen` credit. (Operational hardening copied from the source: **MCP is forbidden**
inside this fan-out — an unbounded hang would freeze it — so every external call is a watchdog-bounded CLI:
`codex sleep 540-600s`, `gemini sleep 300-360s`, `kill -9` on timeout, unique temp file per branch, and a
timed-out model is **noted in its field and the gate proceeds** — never blocks.)

## Two engine contracts the gate enforces (fail-closed)
These mirror the engine's own fail-closed checks ([`spiral_engine.js:202`, `:347`](../../packages/core/spiral_engine.js)) — the gate refuses to ADVANCE a spec that would later make the engine refuse to run:
1. **Every panel needs a blueprint SVG — but the field name differs by artifact (do NOT conflate them):**
   the wiki `blueprint.payload.content_svg` (top-level on the payload), the `panel_spec.payload.content_blueprint`
   (the panel_spec's own field — there is NO `content_svg` on a panel_spec), and the `comic.json` panel's
   `condition.content_svg` (the RUNTIME field the engine reads at `spiral_engine.js` `.condition.content_svg`).
   Any of these `null` / empty / not a project-relative `*.svg` is a **structural hard-veto** at the `blueprint`
   and `storyboard` gates (the engine rejects `condition.content_svg: null` in comic.json outright). Do not let
   a planned panel through with no blueprint.
2. **A baked figure-panel MUST declare `expected_literals`** (exact numbers / keys, verbatim, ASCII-
   tokenizable). The engine's `cfgUsable` refuses to run an *ungated* baked figure (a baked `content_svg` with
   an empty `expected_literals` is a fail-closed refusal). So the `storyboard`/`blueprint` gate hard-vetoes a
   `text_mode: "baked"` figure-panel that carries no `expected_literals`; a scene panel with no audited
   numbers must be `text_mode: "html"` (its text moves to the overlay). This is the *plausible-unsupported-
   success* guard — a beautiful panel with a WRONG number must never keep, so the gate must be able to
   token-diff it later, which requires the literals authored now.

## Node it reads / writes (`schemas/node_schema.json`)
**Reads:**
- The **`target_node_id`** — one of `intent_spec` / `outline_spec` / `asset` / `storyboard_spec` /
  `blueprint` / (for `continuity`) `motif_ledger` / (for `p0_proof`) the compiled `comic.json` + pipeline
  files. Read its required payload (per the schema) — and a **≤200-word verbatim slice** is the only source
  text the adjudicator sees.
- Every **`review`** node attached via a **`reviews`** edge → the target. Required payload `target_node_id,
  reviewer, gate_kind`; the per-dim scores live in the optional `review_scores` map this skill fuses. (Edge
  `reviews` may carry the optional `reviewer ∈ {cc, codex, gemini}` + `weight`.)
- The wiki **banlist** of prior `failure_mode` nodes (so the adjudicator's context includes what already
  failed at this layer).

**Writes** (one JSON file each under `wiki/nodes/`, `created_at` ISO-8601):
- **`decision`** (`node_id` `decision:<gate>_<slug>`) — payload **required** `target_node_id, verdict,
  gate_kind`; this skill additionally writes the audit fields `_threshold_verdict, _codex_verdict,
  _disagreement, _confidence, _cited_dimensions, _score_fingerprint` (+ the structural sets
  `_unresolved_asset_refs / _policy_violations / _count_band / _continuity_breaks` when computed). `status:
  "final"`. Append a **`decides`** edge (`decision → target`, optional `verdict` on the edge).
- **`failure_mode`** (`node_id` `fail:<gate>_<slug>`) — **only on a FAIL verdict**. Payload **required**
  `layer, affected_shot_ids, active`; `repair_pattern` is the **positive invariant**; default scope
  movie-local. `status: "active"`. Append a **`failure_of`** edge (`failure_mode → target`).
- **No** `failure_mode` on an advance verdict, and **none** when Codex was unavailable (provisional verdict).

## Worked example (the pattern to copy)
The canonical exhibits are the three historical orchestration scripts + the engine that ground this skill:

- **The P0 proof — [`examples/comic_m3_audit/workflows/p0-review.js`](../../examples/comic_m3_audit/workflows/p0-review.js).**
  Copy the **`FIND` schema** (`required: ['reviewer','blockers','should_fix','overall']`, each blocker/
  should_fix item `{file, issue, fix}` — all three required), the **3-reviewer fan-out** (`codexReview('code',
  [BUILDER, TEMPLATE], …)` ‖ `codexReview('engine', [ENGINE], …)` ‖ the inline `gemini` design reviewer), the
  **`cat`-the-real-file** rule (`files.map(f => 'echo "===== ${f} ====="; cat "${f}"')` — never a summary), and
  the **synthesis reducer** that dedups → orders BLOCKER>SHOULD>NICE → returns `blocker_count`/`should_count`.
  Its watchdog hardening (`codex … & P=$!; ( sleep 540; kill -9 $P ) & WD=$!; wait $P; kill $WD`) is exactly
  the MCP-forbidden / never-block-on-timeout discipline. **The threshold `blockers.length == 0` before any
  credit is the contract.**

- **The cross-model adjudication shape — [`examples/comic_m3_audit/workflows/pivot-design.js`](../../examples/comic_m3_audit/workflows/pivot-design.js).**
  Copy the **typed gate schemas** that force the gate to be *real*: `DESIGN_SCHEMA`
  (`required: ['recommendation','codex_take','gemini_take','open_decisions']` — a branch **cannot claim a
  cross-model review it did not do**, the `codex_take`/`gemini_take` fields are the evidence), and
  `CRITIQUE_SCHEMA` (`required: ['model','biggest_flaws','missing','risks','verdict']`, prompt forbids
  softening: *"pass through the sharpest valid points"*). The "form your OWN take FIRST → get codex → get
  gemini → **reconcile/judge** → surface only genuine human forks" loop is the adjudicator discipline; the
  **unique temp file per branch** + **note-a-timeout-and-proceed** is the operational guard.

- **The deterministic fuse — [`packages/core/spiral_engine.js:59`](../../packages/core/spiral_engine.js) (`panelVerdict`).**
  This is the **exact min-fuse / skip-missing / max-for-inverted / single-vote-veto** pattern to port into §②:
  `idents = [gem?..., cdx?...].filter(x => x != null); minIdent = idents.length ? Math.min(...idents) : 0`
  (skip-missing, never 0-substitute when *some* reviewer scored it); `artifactBad = (gemArt >= 4 && cdxArt >=
  3) || …` (inverted dim, corroborated — a lone pixel-purist can't single-veto a by-design background glow);
  `anatomyDefect = … === true` (a single-vote veto for a clear defect the literal-diff is blind to); and the
  **fail-closed** guard `if (![gem,cdx].every(r => visCore(r).every(x => x != null))) return retry` (a
  reviewer that returned *incomplete* core scores must not slip an advance). The authoring gate inherits this
  verbatim so reviewer-independence + min-fuse + positive-invariant failure_modes come for free.

## Hard do / don't (earned lessons)
- **DO** treat this gate as a **score-fuser, never a reviewer** — collect the `review:*` nodes the upstream
  step already wrote; **hard-fail if there are none.** Re-running a reviewer here would make the gate part of
  the thing it judges.
- **DO** feed the adjudicator **scores + tags + raw PATHS + ≤200-word verbatim source + verbatim rubric and
  NOTHING ELSE.** Forwarding any reviewer prose/notes/overall is a **CRITICAL** independence violation
  ([`reviewer-independence`](../../protocols/reviewer-independence.md)).
- **DO** `SKIP` a dim no reviewer scored — **NEVER substitute 0.** (The v1.0 bug: a lite reviewer's blank dim
  must neither slip an advance nor force a fail.)
- **DO** keep the trust **asymmetric**: the deterministic threshold (and the structural facts) **hard-veto
  advance**; Codex **soft-vetoes** everything else. Codex can never overrule a *failed* floor into an advance.
- **DO** run **`--gate p0_proof` to a clean `blockers.length == 0` BEFORE the first metered bake.** It is free.
  Skipping it to "save a step" trades zero-cost text review for credit-cost regeneration.
- **DON'T** regenerate the artifact when scores are **identical across rounds** — that means the **judge** is
  broken, not the spec. **HALT and flag `judge_suspect`; audit this rubric** (memory:
  `feedback_gate_identical_scores_judge_broken`). A gate that scores the same regardless of the work is broken.
- **DON'T** let an authoring step acquit itself — the gate (a different model family) acquits; *the loop can
  DRIVE but it cannot ACQUIT* ([`acceptance-gate`](../../protocols/acceptance-gate.md)).
- **DON'T** flag an intended design variation as drift — the warm/dark two-world split, a disjoint cast on a
  2-up, a tagged `env` prop, a deliberate absence are **design, not drift**. The gate is design-aware.
- **DON'T** emit a verdict outside a gate's legal set (the `intent` gate cannot say `keep`; only the `asset`
  gate can say `locked`/`abandon_shot`) — it is a hard error.
- **DON'T** mint a `failure_mode` on an advance, or when Codex was unavailable (the provisional verdict is
  `_confidence: low`, exit 2 — fix and re-gate, don't poison the banlist).
- **DON'T** call MCP inside the `p0_proof` fan-out — watchdog-bounded CLI only; a timed-out model is noted in
  its field and the gate proceeds (never blocks).

## Protocols (governance contracts this skill honors)
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — the adjudicator sees scores + tags +
  raw PATHS + a ≤200-word verbatim source slice + the verbatim rubric only; **never** reviewer prose/notes/
  overall. The p0_proof reviewers each `cat` the real files, never a Claude summary. The
  `=== EXTERNAL CONTEXT (advisory) ===` fence keeps cross-cutting context from becoming a conclusion.
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — this skill IS the acquittal: a generating step can
  DRIVE toward a locked spec but cannot ACQUIT it; a different model family (Codex adjudicator) + the
  deterministic threshold do. Identical-scores-across-rounds → the judge is suspect, not the artifact.
- [`review-tracing`](../../protocols/review-tracing.md) — every collected reviewer + the adjudicator call + the
  p0_proof fan-out is traced (prompt + response + `threadId` + verdict) so each acquittal is auditable and the
  independence claim is checkable after the fact.
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Codex `gpt-5.5` `xhigh` for the adjudicator and
  every correctness/logic reviewer; Gemini `auto-gemini-3` for the visual/design family; never downgrade the
  tier (effort widens fan-out, never weakens the judge).
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — structural facts (asset-resolve / policy /
  count-band / continuity / sha-match / blueprint-renders) are RAW artifacts the gate computes and hard-vetoes
  on; they are *verified*, never originated, and forwarding them to Codex is not an independence breach.
- [`fan-out-pattern`](../../protocols/fan-out-pattern.md) — the p0_proof 3-reviewer fan-out and the per-gate
  multi-reviewer collection are Tier-1/Tier-2 fan-outs that converge on this one cross-model adjudication
  bench.
- [`injection-hygiene`](../../protocols/injection-hygiene.md) — all node ids / paths flowing into the
  watchdog CLI prompts are whitelisted (`[A-Za-z0-9_-]` ids, absolute metachar-free paths) before
  interpolation, exactly as the engine validates them.
