---
name: comic-continuity-audit
description: The authoring-side DIEGETIC continuity AUDIT — it produces the world-state evidence that comic-cross-layer-gate `--gate continuity` adjudicates against the storyboard's MOTIF STATE TABLE (motif_ledger). It checks each baked panel STRICTLY against the pre-committed table row, then emits a continuity review-node the gate fuses (it does NOT own a bake-time KEEP). Gemini auto-gemini-3 is the per-panel FACT extractor (one analyzeFile per panel image, fact-only); Claude is the deterministic JUDGE against the table row + the global invariants (DDL countdown monotonic never-rewind, bounce S02 = the film's ONLY MAX, the two metric columns never co-mingle, the non-adjacent MIRROR LOCKS). CAST-AWARE: a panel simply NOT containing a character is design, NEVER a drift penalty (absence≠drift). On a same-panel miss it requests `retry_panel`; a cross-frame motif break is routed into the page assembly_gate's drift set (seed-anchored comic panels are independent — no cross-panel rollback). Use when the user says "查连续性", "continuity audit", "连戏检查", "world-state drift", "motif table check", "对一下分镜表", or a panel has been baked and you need to verify it realized its motif-table row.
---

# comic-continuity-audit — the Motif-State-Table Audit (Phase 1, step S11)

The **diegetic-continuity AUDIT step of the [`comic-author`](../comic-author/SKILL.md) suite**: verify that a
baked panel obeys the **WORLD-LOGIC** the comic committed to — time / prop-state / motif-arc / metric-value /
causality across cuts — *distinct from* identity/style (`comic-director`'s `panel_gate` already covers "does
the character LOOK the same"; this covers "does the WORLD stay consistent"). The audit is **not vibes**: it
reads the pre-committed **MOTIF STATE TABLE** authored by [`comic-storyboard-creator`](../comic-storyboard-creator/SKILL.md)
(the `motif_ledger` node) and checks each baked panel STRICTLY against its own row + the film's global
invariants. **This skill is the AUDIT producer, not the gate**: it emits a continuity `review` node (world-state
evidence) that [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) `--gate continuity` collects and
adjudicates — *the loop can DRIVE but it cannot ACQUIT* ([`acceptance-gate`](../../protocols/acceptance-gate.md)).
On a same-panel miss it requests a `retry_panel`; a cross-frame motif break is handed to the page
**assembly_gate's drift set** (seed-anchored comic panels are independent — there is **no cross-panel
rollback** in this image pipeline, [`spiral_engine.js:54`](../../packages/core/spiral_engine.js)). It ports the
real procedure of aris_movie's `continuity-audit` (Gemini-as-fact-extractor → Claude-as-deterministic-judge →
violations → routed repair) onto stills, but anchors it to our **pre-committed per-dimension-per-panel ledger**
instead of asking a holistic judge to infer intent.

> **Cardinal lesson baked in as a predicate, not prose:** *the audit IS the table.* The audit never invents a
> rule — it reads the `motif_ledger` and flags any panel whose observed value contradicts that panel's row. And it is
> **cast-aware**: a panel that simply does not contain a character (the duo are absent in S01/S03/S06/S18/S20/S22
> by design) is **design, NEVER a drift penalty (absence≠drift).** This is the concrete fix for the B03
> cross-frame **FALSE-drift**: *IDENTICAL `min=0` scores across re-bakes were the fingerprint of a broken,
> cast-blind RUBRIC — not a broken artifact.* When scores don't move across repairs, audit the JUDGE (is it
> reading the table? is it penalizing intended absence?), do not keep regenerating the panel.

```text
  motif_ledger (the TABLE) ─▶ ① LOAD  attempt + prior-accepted + this panel's table row + active continuity_constraints
                                  ▼
                            ② EXTRACT  Gemini auto-gemini-3, ONE analyzeFile per panel image, FACT-ONLY (no scoring, no comparison)
                                  ▼
                            ③ JUDGE  Claude deterministic: observed ⊖ table-row  AND  global invariants
                                  │       (DDL monotonic · bounce S02=ONLY MAX · metric columns never co-mingle · MIRROR LOCKS)
                                  ▼
                            ④ CAST-AWARE FILTER  intended-absence ≠ drift; design variation ≠ drift  (read the row's design intent)
                                  ▼
                            ⑤ EMIT  one continuity review node (always) + 0-N continuity_constraint candidates + observed_state patch
                                  ▼
                       contradiction? ─ yes ─▶ same-panel miss: request retry_panel (failure_mode.repair_pattern = positive invariant)
                                  │            cross-frame break: add panel id to the page assembly_gate drift set (NO cross-panel rollback)
                                  │ no
                                  ▼
                            ⑥ the continuity review node is COLLECTED by comic-cross-layer-gate --gate continuity (the gate ACQUITS, not this skill)
```

## Constants
- **THE GATE = THE TABLE.** The audit reads the `motif_ledger` node (its `columns` / `rows` / `invariants` /
  `mirror_locks`) and checks each panel against its own row. It **does not invent rules**; an un-tabled claim
  is out of scope (escalate to the storyboard layer, do not adjudicate it).
- **MOTIF_TABLE_COLUMNS** (verbatim, the dimensions the audit reads) =
  `Panel | Mug（ML RESEARCH motif 杯）| DDL | Tok|yo | exact_parse | claim_delta | bounce`.
- **FACT-EXTRACTOR** = Gemini `auto-gemini-3` via `mcp__gemini__analyzeFile` — **ONE call PER panel image**
  (`analyzeFile` takes ONE `filePath`, never a batched array). Prompt is **FACT-ONLY**: *"Do NOT score quality.
  Do NOT compare to anything. Just extract what you SEE in THIS ONE panel."* For a multi-panel **page**, sample
  the salient panels (first + last + the dominant `big-frame` panel), one `analyzeFile` each.
- **JUDGE** = Claude (this agent), **deterministic predicate evaluator** over the observed JSON vs the table row
  + the global invariants. The judge is logic, not per-pixel taste.
- **CROSS-MODEL INDEPENDENCE** — the executor that **baked** the panel (Codex `image_gen`) is NOT a judge here;
  it never self-acquits ([`reviewer-independence`](../../protocols/reviewer-independence.md)). Gemini extracts,
  Claude judges; the generator family is excluded from this audit.
- **GEMINI_FALLBACK** — a frame Gemini fails: retry once; if it still fails, **mark that dimension
  `indeterminate`, never default to satisfied/violated**. A false negative wastes a re-bake; surface ambiguity.
- **MAX_CONSTRAINTS_TO_CHECK = 20** (cap; archived/superseded `continuity_constraint` nodes skipped) ·
  **GEMINI_MODEL = auto-gemini-3** (never downgrade, [`reviewer-routing`](../../protocols/reviewer-routing.md)).
- **OUTPUT** = a `review` node (always) + `story/CONTINUITY_TRACE.md` + `observed_state.json` per panel +
  0-N `continuity_constraint` candidate nodes + (on mismatch) a `decision` + a `failure_mode` + edges.

## Input contract — what it reads, what it writes (the wiki node it touches)
This skill is **pure audit** — it produces the world-state **evidence** (a continuity `review` node) that
[`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) `--gate continuity` later COLLECTS (via the
`reviews` edge) and fuses against the `motif_ledger`. **The continuity verdict belongs to that gate** (it scores
the gate's four dims `ledger_row_complete / invariants_hold / mirror_locks_paired / design_aware`); this skill
only writes the review + (on a contradiction) requests the engine's bake-time repair (`retry_panel`, or a
cross-frame add to the page assembly_gate's drift set). It does **NOT** feed a bake-time `panel_gate` KEEP —
verified: [`spiral_engine.js`](../../packages/core/spiral_engine.js) `panelVerdict` computes `narr` from
`cc.narrative_beat_fidelity` / `cc.composition_story` and **never reads a `plot_continuity` field**, so this
skill never claims MIN-fusion influence over the bake-time KEEP.

**Reads** (per `schemas/node_schema.json`, `node/comic/3.0`):
- the **`motif_ledger`** node (`node_type: "motif_ledger"`, id `motif:<slug>`) — payload `columns`, **`rows`**
  (the per-panel ground truth), **`invariants`** (DDL monotonic; bounce-uniqueness; metric-column separation),
  **`mirror_locks`** (the non-adjacent paired constraints). *This is THE spec the audit checks against (and the
  gate then adjudicates).*
- the **`panel_attempt`** node under audit (`node_type: "panel_attempt"`, id `attempt:<slug>`) — payload
  `source_panel_id`, **`image_path`** (the single baked panel PNG, or a page of panels), `attempt_index`.
- the **MOST RECENT accepted** `panel_attempt` on the same lineage = `PRIOR_ACCEPTED` (the implicit reference
  for monotonicity); if none → bootstrap-only pass (vacuous-satisfied, still emit a review node).
- all **live `continuity_constraint`** nodes — filter on the **payload boolean `payload.active == true`** (the
  designed institutional-memory "is this constraint live" flag, NOT the node `status`; skip nodes whose `status`
  is `superseded`/`rejected`). Per `validate_wiki.py` `PAYLOAD_REQUIRED["continuity_constraint"]` the payload
  carries exactly `family, constraint_text, applies_to_panel_ids, source_node_id, active` — read all five.

**Writes** (every node-id matches the schema pattern `^(…|review|decision|fail):[a-z0-9_-]+$`; every payload
carries exactly the `validate_wiki.py` `PAYLOAD_REQUIRED` fields for its type):
- **always** one **`review`** node (`node_type: "review"`). **Node-id and reviewer are NAMESPACED to avoid a
  byte-collision** with the bake-time `panel_gate` CC review: id **`review:continuity_<panel>_<attempt>_cc`**
  (NOT `review:<panel>_<reviewer>` — that is byte-identical to the existing `review:panel_s01_a01_cc` and would
  OVERWRITE it), reviewer **`continuity_cc`** (a *logic* judgment, not the bake-time per-pixel `cc`),
  **`gate_kind: "continuity"`**. **The four continuity-gate dims go under `payload.review_scores`** — that map
  is the ONLY copy [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) `--gate continuity` reads (its
  §① loads each review's `payload.review_scores`): `review_scores = {ledger_row_complete, invariants_hold,
  mirror_locks_paired, design_aware}` (each 0–5, the EXACT dims it fuses) + a `timed_out` bool + `notes` at
  payload top-level. The 3 schema-required keys are `target_node_id` (the **`motif_ledger`** = `motif:<slug>`,
  the node `--gate continuity` is passed + adjudicates), `reviewer`, `gate_kind`; `status: "complete"`. Append a
  **`reviews`** edge `review:continuity_<panel>_<attempt>_* → motif:<slug>` (the `motif_ledger` is the exact node
  the continuity gate collects reviews INTO; the audited attempt is named in the review node_id + carried in
  `notes` — never target `attempt:*` (the continuity gate does not adjudicate the attempt), never `reviewed_by`,
  the opposite direction). *(The bake-time `panel_gate` reviews use flat top-level dim keys for the engine's
  reader; this AUTHOR-layer continuity review uses `review_scores` because that is the map the author gate reads.)*
- **on a contradiction** a **`decision`** node (`node_type: "decision"`, id `decision:continuity_<panel>_<slug>`,
  payload schema-required `target_node_id, verdict, gate_kind` — `gate_kind: "continuity"`, `status: "final"`)
  whose **`verdict` is `retry_panel`** (same-panel mug/tokyo/metric miss) **or `assembly_drift`** (a cross-frame
  motif break — routed to the page assembly_gate's `drift_panels`, NOT a per-panel rollback) + a
  **`failure_mode`** node (`node_type: "failure_mode"`, id `fail:continuity_<panel>_<slug>`, payload
  schema-required **`layer: "continuity"`**, **`affected_shot_ids`**, **`active: true`**, status `active`) whose
  **`repair_pattern`** is the **POSITIVE INVARIANT** for the next bake — e.g. *"S06 DDL reads exactly `T-18:40`
  so `18:40 > S07's 18:30` holds the countdown"*, never the ban. **(Dataflow, exact:** the engine sources the
  next bake's invariant from the panel-gate reviewer's in-memory `failure_mode_positive_invariant` →
  `verdict.invariant` → `pending[pid]` → the next `generate_panel`; the persisted
  `failure_mode.payload.repair_pattern` is the audit SINK written FROM that same invariant, NOT read back by the
  engine — so author `repair_pattern` as the identical positive invariant the reviewer emits.) Append a **`decides`** edge (`decision → attempt`, verdict on the edge)
  + a **`failure_of`** edge (`failure_mode → attempt`). **No `rollback_of` edge** — that edge is for the
  page-level assembly rollback the engine actually performs, not a (non-existent) per-panel chained rewind.
  Edge vocab used here, all in `validate_wiki.py` EDGE_TYPES: `reviews / decides / failure_of` (+ the existing
  `attempt_of` minted upstream).
- **0-N `continuity_constraint`** candidate nodes (institutional memory; id `cont:<slug>`, payload
  `family, constraint_text, applies_to_panel_ids, source_node_id, active`) — an implicit check that **fires
  twice on the same lineage** gets promoted to an explicit constraint node so the next run checks it cheaply.
- **patches** the attempt payload with `observed_state` (allowed by `additionalProperties: true`) — *this* is the
  progressive chain: the NEXT audit has a verified reference instead of re-inferring it.

## Two fail-closed engine contracts (refuse, do not paper over)
The audit runs only on artifacts the pipeline guarantees; if a precondition is missing it **fails closed** and
points at the offending node rather than silently auditing a malformed unit:
1. **Every panel needs a `content_svg`.** The baked panel must trace to a `blueprint` node whose payload carries
   a non-empty `content_svg` (the deterministic SVG blueprint that was the generation condition). No
   `content_svg` → the panel was free-baked, the table-row comparison has no anchor → **REFUSE**, route back to
   [`comic-blueprint-author`](../comic-blueprint-author/SKILL.md). (You audit what was *committed*, not a vibe.)
2. **A baked panel carrying a `content_svg` needs `expected_literals`.** For any panel whose effective
   `text_mode` is `baked` AND that carries a `content_svg` (cfg_usable's exact trigger), the blueprint's
   `expected_literals` (the ascii-tokenizable numbers/labels: e.g. `["REJECT","37","T-16:05"]`) MUST be present;
   they are the literal values the metric/DDL columns are checked against. Missing/empty `expected_literals` on a
   baked figure panel → **REFUSE** (the fail-closed gate cannot verify `exact_parse`/`claim_delta`/`DDL` without
   them). `text_mode: "html"` (pure-scene) panels carry no literals — they are gated on `stray_text_absence`, and
   their continuity is judged on the scene-state columns (mug / bounce / cast presence) only.

## THE AUDIT PREDICATES — what this skill checks and reports to the `continuity` gate
This is the **pre-gate routing** (the audit's own predicates) — NOT the gate's APPROVE condition. The gate's
APPROVE predicate is owned by [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) `--gate continuity`
(`ledger_row_complete ≥ 4 AND invariants_hold ≥ 4 AND mirror_locks_paired ≥ 4 AND design_aware ≥ 4`, with a
structural HARD VETO on any invariant violation). This skill computes the per-column / per-invariant findings
below, folds them into those four dims, and writes them to the review node the gate fuses.

**Audit columns** (the six table columns; each is a machine-checkable predicate the audit verifies from the
table alone — they roll up into the gate's `invariants_hold` + `ledger_row_complete` dims):

- **`mug`** — tracks ONLY the `ML RESEARCH` motif mug. States: `hot` (two stable steam wisps = the film's
  *temperature origin*) / `fading` (one thin wisp) / `cold` (no steam + milk skin). **DESIGN-AWARE
  DISAMBIGUATION:** the `</>` mug is an **environment prop**, tagged `env`, and **ignored** — a panel showing a
  `</>` mug is NOT a motif-mug appearance and must NOT be flagged. The B01↔S20 bookend `cold` is *"the hardest
  continuity constraint"* (S20 must read stone-cold + milk-skin, same mug as S01's hot origin).
- **`ddl`** — global invariant **"DDL 全片单调递减，永不回拨"** (monotonic non-increasing across the ENTIRE
  film, never rewinds). Exact 16-value spine:
  `T-24:00:00 → 19:42 → 19:42 → 18:55 → 18:40 → 18:30 → 17:46 → 17:02 → 16:21 → 16:05 → 05:12 → 02:58 → 02:41 → 01:57 → 00:42 → 00:27(submitted)`.
  Two consecutive `19:42` (S03/S04, same-instant rhyme) are allowed *because non-increasing*; `S06=18:40`
  exists SOLELY so `18:40 > S07's 18:30` holds the never-rewind rule.
- **`tokyo`** — the broken-JSON chip `{"city":"Tok|yo"}` lifecycle:
  `absent → first-micro (S09, sub-threshold, NOT gated) → hero/gated center (S10) → evidence thumbnail (S11) →
  tiny as-prior (S12a) → REPAIRED {"city":"Tokyo"} ✓ parsed (S17) → single unlabeled dark star (S22)`.
- **`exact_parse`** vs **`claim_delta`** — the two metric columns that **"永不混写" / never co-mingle**:
  `exact_parse ∈ {0.60, 0.71, 0.66, 0.78, 0.89}`, `claim_delta ∈ {+6.2, +1.4}`. A value written into the wrong
  column is a violation (a `+6.2` appearing where an `exact_parse` should be, or vice-versa).
- **`bounce`** — uniqueness invariant **"S02 是全片唯一 MAX"** (S02 is the film's ONLY maximum bounce). Every
  later high is annotated *"低于 S02"*; **post-fall peaks are BANNED** (S12a = *"attempted celebration, ARRESTED
  before becoming a jump"*); the arc closes at S21 *"smallest bounce (弧线终读数)"*.

**Cross-panel MIRROR LOCKS** (non-adjacent paired constraints, beyond the per-row table — read from
`motif_ledger.mirror_locks`):
- **S11 REJECT ↔ S16 ACCEPT** — same diagonal stamp **geometry/angle** (both from `stamp_family_v1.svg`'s shared
  verdict-card geometry) + **identical stamping-arm pose**. The audit checks the geometry matches, not the word.
- **S02 unique-MAX ↔ S21 smallest** — the bounce-thermometer endpoints (a second MAX at S21 is a veto).
- **S16b labeled star-map ↔ S22 wordless constellation** — **same node coordinates** from
  `wiki_starmap_nodes_v1.json` (**禁目测 / no eyeballing** — the JSON is the only truth source for both; S22 is
  programmatically derived, never re-laid-out by eye).
- **S20/S21 set-continuity** — same room/desk/camera as S01 (S01's baked image is the additional condition ref).

**HARD VETO FINDINGS** (any one → the audit reports the gate's `invariants_hold` dim as **violated** (≤1) →
the gate structurally HARD-VETOes ADVANCE; this skill requests `retry_panel` for a same-panel miss, or routes a
cross-frame break to the assembly_gate drift set):
- **DDL rewind** — DDL is a **COUNTDOWN of *remaining* time**, declared monotonic **NON-INCREASING** (`永不回拨`).
  Walk the accepted chain in **`sequence_index` order**; the violation is a **LATER panel showing MORE remaining
  time than an earlier panel (the countdown went UP / reset)**, OR any DDL value not matching the committed
  16-value spine in order. An earlier panel having *more* remaining time than a later one is the CORRECT case,
  never a violation. (Canonical bug: S06's draft `T-15:27` showed LESS remaining than S07's `T-18:30` *(15:27 <
  18:30, i.e. the deadline jumped closer then snapped back further away)* — a rewind; fixed to `T-18:40` so the
  remaining-time sequence `18:55(S05) → 18:40(S06) → 18:30(S07)` is non-increasing.)
- **a second bounce == MAX** — any post-S02 panel reading MAX bounce (the uniqueness invariant).
- **a cross-written metric column** — an `exact_parse` value in the `claim_delta` column or vice-versa.
- **a broken MIRROR LOCK** — REJECT/ACCEPT geometry mismatch, or S16b↔S22 coordinates that don't derive from
  the shared JSON, or S20/S21 set drift off S01.

**SCORING — how findings roll into the FOUR continuity-gate dims this audit writes** (`ledger_row_complete`,
`invariants_hold`, `mirror_locks_paired`, `design_aware`, each 0–5; the gate ADVANCES iff all four ≥ 4 with a
HARD VETO on any invariant violation). Per dim: `clean / bootstrap → 5` · `minor finding → 4` · `major → 2` ·
`critical → 1` · `≥2 critical on that dim → 0`. **SEVERITY map:** any `ddl` / `bounce-uniqueness` /
`metric-cross-write` violation = **critical** on `invariants_hold`; a broken **mirror-lock** = **critical** on
`mirror_locks_paired`; a missing/blank table variable = a hit on `ledger_row_complete`; a `mug` / `tokyo` /
motif-state miss = **major** on `invariants_hold`; an intended-absence false-flag (caught in Phase 3) = a hit on
`design_aware`; an `indeterminate` (Gemini-confidence `< 0.6`) = **minor**, surfaced not vetoed. **The gate**
(not this skill) min-fuses these dims across the collected continuity reviewers and decides advance/revise —
this audit only authors the scores. *(Note: this is the AUTHORING-side continuity gate's dim set; it is
distinct from the bake-time `panel_gate`'s `narrative_intent`/`plot_continuity` formula in `spiral_engine.js`,
which this skill does not feed.)*

**CAST-AWARE GUARD (do NOT penalize, per `acceptance-gate` design-awareness):**
- **intended absence ≠ drift** — a panel whose row marks a character/motif `absent` or `n/a` (the duo in
  S01/S03/S06/S18/S20/S22; `bounce = n/a` when the duo aren't on-panel) is **correct by design**; flagging it
  is a FALSE drift. Read the row's intent before scoring.
- **intended variation ≠ drift** — the warm↔dark-cyber world flip, the `env` `</>` mug, a deliberately
  `sub-threshold` Tok|yo chip (S09, `≤1.5%` frame height, *below the blind-review transcription threshold*) are
  all by-design and **out of the drift contract**.
- **IDENTICAL scores across re-bakes ⟹ audit the JUDGE, not the panel.** If the continuity dims
  (`invariants_hold` / `design_aware` / …) don't move after a repair, the rubric is cast-blind or not reading
  the table — stop regenerating, fix the audit/gate (the B03 false-drift lesson).

## Procedure (followable, one panel at a time — never batch the audit)

### ① Phase 0 — Load state (the table is the spec)
Parse the `panel_attempt` id → slug (`:` → `__`); read its `image_path`, `source_panel_id`, `attempt_index`.
Load the **`motif_ledger`** node and pull **this panel's row** + the `invariants` + the `mirror_locks` that name
this panel. Enumerate live `continuity_constraint` nodes (filter on **`payload.active == true`**, skip nodes
whose `status` ∈ {`superseded`,`rejected`}, cap 20, prioritise those whose `applies_to_panel_ids` contains this
panel). Resolve `PRIOR_ACCEPTED` = most-recent accepted attempt
on the lineage. **Fail-closed check now (mirror `run_comic.py` `cfg_usable` EXACTLY — never weaker than the
engine floor):** confirm the panel's `blueprint` carries a non-empty `content_svg`, and — if
`text_mode == "baked"` AND a `content_svg` is present (cfg_usable's EXACT trigger — NO 'figure panel' sub-test,
which would be narrower/weaker than the engine floor) — that `expected_literals` is a non-empty list where
**every** entry is an ascii-tokenizable string (`isinstance(e, str) and re.findall(r"[a-z0-9+._-]+", e.lower())`);
if either is missing or any literal fails that → HALT and route back (do not audit a malformed unit). Snapshot inputs to `continuity_context.json`. If no
`motif_ledger` row exists for this panel → escalate to the storyboard layer (the audit has nothing to check
against; never improvise a row).

### ② Phase 1 — Extract observed state (Gemini, fact-only, one call per image)
Call `mcp__gemini__analyzeFile` with **`auto-gemini-3`**, **ONE `filePath` = the panel PNG** (for a page, one
call per sampled panel: first + last + the dominant `big-frame`). Prompt is strictly fact-only — *"Do NOT score.
Do NOT compare. Extract only what you SEE in THIS ONE panel."* Demand a JSON with the columns this audit reads:
`mug_state ∈ {hot,fading,cold,env,absent,unclear}` (and whether the visible mug is the `ML RESEARCH` mug or the
`</>` env mug); `ddl_value` (the literal countdown string seen, or `none`); `tokyo_state` (absent / micro /
hero / thumbnail / repaired / star, + the literal JSON string seen); `exact_parse_values[]` and
`claim_delta_values[]` (the numbers seen, **kept in separate arrays — do not merge**); `bounce_level`
(the executor's pose: max / high / tempered / deflate / silent / n-a, + "is the duo on-panel?");
`characters_visible[]`; `props_visible[]`; plus a free `anomalies[]` (the **negative-space audit**). Aggregation
is **deterministic Python, no LLM** (majority/last-frame anchor for a page). On a per-frame Gemini failure:
retry once → still failing → that dimension is `indeterminate (conf 0.0)`, **never defaulted**.

### ③ Phase 2 — Deterministic judge (observed ⊖ table row + invariants)
Claude compares the extracted JSON to **this panel's table row** and the global invariants, as predicates:
- **per-column**: does `mug_state` match the row's mug (and is an `env` mug correctly ignored)? does `ddl_value`
  equal the row's DDL? does `tokyo_state` match the row's lifecycle stage? are the metric values in the *right*
  columns and equal to the row?
- **global invariants** (across the whole accepted chain in **`sequence_index` order**, using `PRIOR_ACCEPTED` +
  the spine): **DDL remaining-time monotonic NON-INCREASING** — flag ONLY a later panel showing *more* remaining
  time than an earlier one (a countdown rewind), or a value off the 16-spine; an earlier panel legitimately has
  more remaining time. Bounce S02 = ONLY MAX (no post-fall peak); `exact_parse`/`claim_delta` never cross-written.
- **mirror locks** for this panel: REJECT↔ACCEPT geometry; S16b↔S22 shared JSON coords; S02↔S21 endpoints;
  S20/S21↔S01 set. Geometry/coords are checked structurally (禁目测 where a JSON truth source exists).
Each fired check → `{check, verdict ∈ {violated, satisfied, indeterminate}, evidence, severity}`.

### ④ Phase 3 — Cast-aware filter (absence≠drift) BEFORE scoring
Re-read this panel's row intent and **drop any "violation" that is actually intended**: a character/motif the
row marks `absent`/`n/a`; the warm/dark world flip; an `env` `</>` mug; a sub-threshold Tok|yo chip; an `html`
panel's lack of literals. **A flagged-but-intended item is a FALSE drift and is removed, not scored.** If after
this filter the score is identical to a prior re-bake's score, STOP and audit the rubric (cast-blindness), do
not trigger another bake.

### ⑤ Phase 4 — Emit continuity review + constraints + observed_state patch
Write **one `review` node** (always; **id `review:continuity_<panel>_<attempt>_cc`**, **`reviewer:
"continuity_cc"`**, **`gate_kind: "continuity"`** — the namespacing avoids overwriting the bake-time
`review:<panel>_<reviewer>` panel-gate node; see the Writes contract). Write the four continuity-gate dims
**under `payload.review_scores`** = `{ledger_row_complete, invariants_hold, mirror_locks_paired, design_aware}`
(per the scoring table — that map is what `--gate continuity` reads) + `timed_out` + `notes`, and append a
**`reviews`** edge `review:continuity_<panel>_<attempt>_* → motif:<slug>` (the `motif_ledger` — the exact node
`--gate continuity` is passed and collects reviews INTO; NOT `attempt:*`, which the continuity gate does not
adjudicate). Append the human-readable trace to
`story/CONTINUITY_TRACE.md` and `observed_state.json`. **Patch the attempt** with `observed_state` (the verified
reference for the next audit — the progressive chain). For any implicit check that has now **fired twice on this
lineage**, emit a `continuity_constraint` candidate node (institutional memory) so it becomes an explicit cheap
check next run. Bootstrap pass (no `PRIOR_ACCEPTED`): verdict is vacuously `satisfied`, but STILL emit the
review node and seed candidate constraints from the observed state.

### ⑥ Phase 5 — Request repair on contradiction (executor never self-judges; NO cross-panel rollback)
On ANY hard-veto finding (DDL rewind / second MAX bounce / cross-written metric / broken mirror-lock) or a
`critical`/`major` severity, write a **`decision`** node + a **`failure_mode`** node — the engine reality is the
authority here ([`spiral_engine.js:54`](../../packages/core/spiral_engine.js): *"panels are independent (no
chain) → only KEEP or RETRY-SAME-PANEL, NEVER rollback-to-prior"*), so the verdict is **NOT** a per-panel
rollback:
- **same-panel miss** (mug / tokyo / metric / a DDL value wrong *on this panel*) → `decision.verdict:
  "retry_panel"`. The engine re-bakes THIS panel with the positive invariant injected — sourced from the
  panel-gate reviewer's in-memory `failure_mode_positive_invariant` (→ `verdict.invariant` → `pending[pid]` →
  the next `generate_panel`), NOT read back from the persisted node (`payload.repair_pattern` is the audit SINK).
- **cross-frame break** (a mirror-lock between non-adjacent panels, or a DDL/bounce relation that only shows
  across panels) → `decision.verdict: "assembly_drift"`, and add the offending panel id(s) to the **page
  assembly_gate's `drift_panels`** set (the engine's `assemblyVerdict` returns `rollback` with `drift_panels`
  for page-level cross-frame repair — the ONLY rollback this image pipeline has). Do **not** claim a chained
  downstream re-bake "because each panel conditions the next" — that is false for seed-anchored comic panels.
- **`failure_mode`** node (`layer: "continuity"`, `affected_shot_ids`, `active: true`) — **populate
  `payload.repair_pattern` as a POSITIVE INVARIANT** (the audit record of the same invariant the reviewer emits
  for the re-bake — a sink, not what the engine reads back), e.g. `continuity_ddl_rewind` →
  *"S06 DDL reads exactly `T-18:40` so the remaining-time sequence stays non-increasing (`18:55 → 18:40 →
  18:30`)"*; `continuity_mirror_lock_broken` → *"S22 star coords derive verbatim from
  `wiki_starmap_nodes_v1.json` (禁目测), matching S16b"*. State the desired target, never the ban.

Append a **`decides`** edge (verdict on the edge) + a **`failure_of`** edge — **no `rollback_of` edge** (that
edge type is for the engine's page-level assembly rollback, not a per-panel rewind). The re-bake / assembly
repair is owned by [`comic-director`](../comic-director/SKILL.md) + the engine; this skill only *requests* it.
Canonical failure-mode names to reuse:
`continuity_ddl_rewind` · `continuity_bounce_second_max` · `continuity_metric_cross_write` ·
`continuity_mirror_lock_broken` · `continuity_mug_state_wrong` · `continuity_tokyo_stage_wrong`.

## Worked example
The canonical filled ledger to audit against is
[`examples/comic_m3_audit/story/STORYBOARD_DRAFT.md`](../../examples/comic_m3_audit/story/STORYBOARD_DRAFT.md)
— the **CORRECTED MOTIF STATE TABLE** at **lines 12-14** (the verbatim conventions block + the table header)
and the 24 filled rows (lines 16-39) ARE the `motif_ledger` this audit reads. Copy this pattern exactly:

- **The header + conventions (line 12-14) is the gate spec, verbatim:**
  `| Panel | Mug（ML RESEARCH motif 杯）| DDL | Tok|yo | exact_parse | claim_delta | bounce |` with the
  conventions *"mug 列只追踪 `ML RESEARCH` motif 杯；`</>` 杯是环境道具（标 env）… DDL 全片单调递减，永不回拨 …
  S02 是全片唯一 MAX"*. The audit reads predicates off THIS, it does not author new rules.
- **A real monotonic-DDL fix the audit would catch** (line 21): remaining-time `S05=18:55, S06=18:40, S07=18:30`
  is correctly non-increasing. `S06` was changed from the draft's `T-15:27` to `T-18:40` *purely* so S06 still
  has MORE remaining than S07 (`18:40 > 18:30`) — `T-15:27` would have shown LESS remaining than S07's `18:30`
  (the countdown rewound forward then snapped back). A re-baked S06 reading `T-15:27` → `continuity_ddl_rewind`,
  **critical** on `invariants_hold` → `retry_panel` (same-panel re-bake with the positive-invariant repair).
- **Split metric columns that never co-mingle** (lines 23-31): `exact_parse` carries `{0.60,0.71,0.66,0.78,0.89}`
  (S10 shows `0.71→0.66` while `claim_delta` stays `—`); `claim_delta` carries `{+6.2,+1.4}` (S14 shows
  `+6.2→+1.4` while `exact_parse` stays `—`). A bake that prints `+6.2` in the curve where `0.66` belongs →
  `continuity_metric_cross_write`, **critical**.
- **bounce uniqueness** (lines 17, 27, 38): `S02 = MAX（全片唯一最高跳）`; `S12a = attempted celebration,
  ARRESTED before becoming a jump`; `S21 = smallest bounce（弧线终读数）`. A re-baked S12a leaping to MAX →
  `continuity_bounce_second_max`, **critical**.
- **The CAST-AWARE rows (absence≠drift)** — `S01 bounce = n/a（duo 未醒）`, `S03 bounce = n/a（duo 不在本格）`,
  `S20 mug = COLD … bounce = n/a（duo 未露脸）`. The Gemini extractor will report "no duo on panel" and "no
  motif mug steam"; the judge must read these as **satisfied-by-design**, NOT as drift. If an S01 re-bake keeps
  scoring `0` because the duo are missing, the RUBRIC is cast-blind (the B03 false-drift fingerprint) — fix the
  judge, do not regenerate S01.
- **Mirror locks** — S11 `REJECT` ↔ S16 `ACCEPT` (lines 26, 32: *"同一卡面几何/角度 … 精确镜像"*), and S16b ↔
  S22 (lines 33, 39, the wordless dark star) share `wiki_starmap_nodes_v1.json` *(禁目测)*. The audit checks the
  geometry/coords match the shared source, not the stamp word.

The same project ships the consolidated canonical asset contract (lines 369-381) — the audit uses it to know
WHICH instances are continuity-bearing (one `ddl_widget_template_v1.svg` for the whole 18-instance timeline;
one `stamp_family_v1.svg` for all verdict stamps; one `wiki_starmap_nodes_v1.json` truth source for S16b+S22).

## Hard do / don't (earned lessons)
- **DO** read the `motif_ledger` and check each panel against ITS row — the audit IS the table; never improvise
  a rule the storyboard didn't commit (an un-tabled claim escalates to the storyboard layer, it is not adjudicated here).
- **DO** keep Gemini fact-only (no scoring, no comparison) and **one `analyzeFile` per panel image** — the
  fact-extractor must not see the expected values (reviewer independence); the JUDGE owns the comparison.
- **DO** be cast-aware: read a row's `absent` / `n/a` / `env` intent and treat it as satisfied-by-design.
  **Absence≠drift. Intended variation≠drift.**
- **DO** treat **identical scores across re-bakes as a broken JUDGE**, not a broken artifact — audit the rubric
  for cast-blindness (the B03 false-drift lesson), do not keep regenerating.
- **DO** fail closed: no `content_svg` on the panel, or no `expected_literals` on a baked figure panel → REFUSE
  and route back; never audit a free-baked or un-anchored unit.
- **DON'T** let the model that **baked** the panel (Codex `image_gen`) judge its own continuity — the generator
  family never self-acquits; this audit is Gemini-extract + Claude-judge, and the cross-layer gate adjudicates.
- **DON'T** default an `indeterminate` (Gemini failed / confidence `< 0.6`) to `satisfied` or `violated` —
  surface the ambiguity; a false negative wastes a re-bake.
- **DON'T** flag the warm↔dark-cyber world flip, the `env` `</>` mug, or a deliberately sub-threshold Tok|yo
  chip — they are by-design and out of the drift contract.
- **DON'T** confuse this with identity/style — that is `comic-director`'s `panel_gate`. This lane is WORLD-state
  (time / mug-heat / metric values / bounce arc / mirror geometry / causality) ONLY.
- **DON'T** own ANY verdict — this skill writes a continuity `review` node (the four dims `ledger_row_complete /
  invariants_hold / mirror_locks_paired / design_aware`); [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md)
  `--gate continuity` collects it (via the `reviews` edge), min-fuses, and ACQUITS. It does **NOT** feed the
  bake-time `panel_gate` (`spiral_engine.js` reads no `plot_continuity` field); on a contradiction it only
  *requests* a `retry_panel` (same-panel) or an `assembly_drift` route (cross-frame), never a per-panel rollback.

## Protocols (governance contracts this skill honors)
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — Gemini blind-extracts facts from the
  image only (never shown the expected table row); the executor that baked the panel (Codex `image_gen`) is not
  a judge of its own continuity.
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — the loop can DRIVE but can't ACQUIT: this skill only
  authors the continuity review (the four gate dims); [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md)
  `--gate continuity` (a different model family) fuses + decides, and the gate is **design-aware (absence≠drift)**
  — intended absence/variation is never a drift penalty.
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Gemini `auto-gemini-3` for fact extraction; never
  downgrade the reviewer tier.
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — the baker does not judge its own panel's
  numbers; the `motif_ledger` is ground truth and the observed values are *verified* (blind Gemini extract +
  deterministic diff), never originated by the gate.
- [`review-tracing`](../../protocols/review-tracing.md) — every audit writes a `review` node + the
  `CONTINUITY_TRACE.md` + `observed_state.json` so each verdict (and every rollback) is auditable.
