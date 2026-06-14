---
name: comic-storyboard-creator
description: Phase-1 comic-author step — turn a LOCKED, user-approved outline into the page-first storyboard that IS the authoring source of truth: a fixed page order BEFORE any prose, the MOTIF STATE TABLE (the master per-panel continuity ledger), a fixed 9-field per-panel spec, and one deduped canonical asset contract. Decompose beats→pages→panels, 抽卡 K page/panel-order lineages by feasibility, then fill every panel one unit at a time. Writes a storyboard_spec + a motif_ledger (read by comic-continuity-audit) + N panel_spec nodes. Use when the user says "做分镜", "storyboard", "排页", "panel spec", "分镜稿", or the outline layer is locked and approved and you need the per-panel authoring layer the thin comic-author SOP defers to references/.
---

# comic-storyboard-creator — the Page-First Storyboard + Master Continuity Ledger (Phase 1, step S6)

The **storyboard step of the [`comic-author`](../comic-author/SKILL.md) suite**: take a LOCKED, user-approved
[`outline_spec`](../comic-outline-creator/SKILL.md) and produce the artifact that IS the authoring source of
truth — a **fixed page order authored as its own section BEFORE any per-panel prose**, the **MOTIF STATE
TABLE** (the master per-panel ledger that pins every continuity variable for all panels *before* any bake),
a **fixed 9-field per-panel spec**, and **one deduped canonical asset contract**. This is the deep
Layer-2 the 150-line comic-author SOP defers to `references/`; it ports the rigor of aris_movie's
`movie-storyboard-creator` (抽卡 lineages → score → gate) and `-v4` (locked-inputs precondition → beat→panel
budget → deterministic spec) onto stills, and it emits the `panel_spec` fields the downstream
[`comic-blueprint-author`](../comic-blueprint-author/SKILL.md) and [`comic-director`](../comic-director/SKILL.md)
consume. The downstream baking spiral is **not** this skill's job — this is pure authoring + ledger.

> **Cardinal lesson baked in as a gate, not prose:** *decompose beats→pages→panels and 抽卡 K orderings by
> feasibility, then fill ONE panel at a time — never batch-author-then-look.* The MOTIF STATE TABLE is the
> concrete guard: it pre-commits a per-dimension-per-panel ground truth (mug heat / executor bounce /
> Tok|yo evidence / DDL spine / exact_parse / claim_delta) with **machine-checkable global invariants**
> (DDL monotonic never-rewind; bounce S02 = the film's ONLY MAX; REJECT↔ACCEPT mirror), so the audit reads
> intent off a table instead of inferring it.

```text
  locked+approved outline_spec ─▶ ① PRECONDITION (refuse if outline unlocked / unapproved / any asset unlocked)
                                      ▼
                                ② DECOMPOSE  beats → pages → panels  (beat→panel budget arithmetic)
                                      ▼
                                ③ 抽卡 K page/panel-ORDER lineages (Codex xhigh) → score(feasibility/fidelity/novelty) → keep
                                      ▼
                                ④ PAGE ORDER FIRST   (a fixed section, page-type + L/R world per page, BEFORE prose)
                                      ▼
                                ⑤ MOTIF STATE TABLE  (master ledger; monotonic DDL; bounce-uniqueness; mirror locks)
                                      ▼
                                ⑥ PER-PANEL 9-FIELD SPEC  (one unit at a time; DONE panels locked; baked-vs-gate contract)
                                      ▼
                                ⑦ CONSOLIDATE ASSET_REQUESTS  (one canonical owner per token; naming 铁律)
                                      ▼
                                ⑧ EMIT  storyboard_spec + motif_ledger + N panel_spec (+ continuity_constraint)  → cross-layer gate
```

## Constants
- **抽卡 K (lineages of page/panel ordering)** — `K_LITE=3`, `K_BALANCED=6` (default), `K_MAX=8`, `K_BEAST=12`
  (ported verbatim from `movie-storyboard-creator`). Effort tier governs *count of orderings*, not depth.
- **FEASIBILITY_FLOOR = 5** — a lineage scoring `feasibility < 5/10` is dropped (e.g. it needs arbitrary
  un-gateable text rendering, exact UI replication, or face identity it can't anchor). If `<2` survive,
  re-prompt **once** on the same Codex thread; still `<2` → tell the user to lower `--effort` or relax the
  banlist. **Never fall back to a Claude-generated lineage** (violates reviewer independence).
- **REVIEWER** = Codex `gpt-5.5` `model_reasoning_effort: xhigh` for the 抽卡 brainstorm + the cross-layer gate;
  Gemini `auto-gemini-3` where a second family is needed. Never downgrade the tier ([`reviewer-routing`](../../protocols/reviewer-routing.md)).
- **PAGE_TYPES** = `{cover, single, 2-up, vertical-3, grid2x2, big-frame, endcard}`. **WORLDS** = `{warm, dark-cyber,
  seam, starfield}` (human = warm, ARIS = dark-cyber, explicit `seam` at hand-off/payoff, `starfield` for the
  wiki/finale) — the two-world palette grammar inherited from the outline.
- **MOTIF_TABLE_COLUMNS** (per panel, verbatim) = `Panel | <motif-A> | DDL | <motif-B> | exact_parse | claim_delta | bounce`
  — for the worked example: `Panel | Mug | DDL | Tok|yo | exact_parse | claim_delta | bounce`. The two metric
  columns (`exact_parse`, `claim_delta`) **never co-mingle** (different metrics, different value sets).
- **PANEL_TEMPLATE** = the fixed 9 fields (+ title anchor): `text_mode` / `content_blueprint` /
  `expected_literals` / `scene` / `characters` / `bubbles{zh,en}` / `side_narration{zh,en,trait}` / `motifs` /
  `asset_requests`. No free prose outside these fields. (cover/finale panels add `safe_zones`/`endcard` fields.)
- **OUTPUT** = `story/STORYBOARD_DRAFT.md` (the human artifact) + wiki nodes (`storyboard:<slug>`, `motif:<slug>`,
  `panel:<slug>` × N, optional `cont:<slug>`). Versioned per [`output-versioning`](../../protocols/output-versioning.md).

## Input contract — locked + approved upstream (refuse otherwise)
This skill is **pure authoring + ledger**, and it operates ONLY on converged upstream (convergence is the
upstream gates' job, per [`acceptance-gate`](../../protocols/acceptance-gate.md)):
- **Refuse (HALT, point at the offending node) if** the `outline_spec` is not `status: "locked"`, OR it lacks
  the explicit user-approval stamp (the user-first gate — never proceed to asset-library work without a
  recorded `✅ APPROVED by user <date>`), OR any referenced `asset` node it whitelists is not `locked`.
- **Asset-id whitelist is SACRED.** Every panel may reference asset names ONLY from the outline's
  `character_asset_ids` / `scene_asset_ids` / `prop_asset_ids` plus assets you newly request *as*
  `asset_requests`. **Never free-describe an asset inline.** If a panel needs an asset that doesn't exist yet,
  add it to `asset_requests` (which reopens the asset layer) — do not invent it silently.
- Consumed outline fields: `narrative_beats[]`, `beat_table` (the 6-column table: Beat / Panels / layout /
  world / content+台词 gist / ARIS-feature-as-story-cost), `motif_arcs` (the per-shot continuity values),
  `design_constraint` (the dual-identity), `title` / `logline` / `tagline`.

## Procedure (followable, one unit at a time — never batch)

### ① Precondition check
Load the `outline_spec`. Verify `status == "locked"` AND the user-approval stamp is present AND every asset it
whitelists is `locked`. On any failure → HALT with the precise offending node id so the orchestrator routes
back to the outline / asset layer. Record provenance in the header: source outline id, the prior
cross-model verdict it survived (real example: codex critique returned **`REVISE`**; "全部 fix 落地"), and the
`✅ APPROVED by user <date>` line.

### ② Decompose beats → pages → panels (budget arithmetic)
For each outline beat, read its `layout` token to set its page type and per-page panel count, then assign
shot/panel ids. Compute the page budget: a beat tagged `vertical-3` owns 3 panels on one page; `2-up` owns 2;
`grid2x2` owns a recap page; `single`/`full-bleed`/`endcard` own 1. The centerpiece beat may expand
(real: B08 went 4 panels → **5 single-read pages**, adding a NEW `S12a` audit-entry panel, with the 2×2 kept
ONLY as a recap/hero page). Clamp the global total to the project's tier window; if oversize, collapse the
longest multi-panel beat first; if undersize, split the beat with the most slack. **Every panel must land on
exactly one page with a stable page id** (`P00_cover`, `P01_b02`, …, `P03_end`).

### ③ 抽卡 K page/panel-order lineages (Codex xhigh), score, keep
Pass **file paths only** (the locked outline, the style bible, the wiki banlist of prior failed orderings) to
Codex `gpt-5.5` `xhigh` — reviewer independence: Codex forms its own reading, never gets your summary. Demand
`K` (= the tier constant) alternative **page/panel orderings** of the same beat set, each differing on ≥2 of:
*page-rhythm axis* (cover/2-up/grid/vertical-3/big-frame mix) · *cast-presence axis* (which panels show the
duo vs solo) · *world-alternation axis* (warm/dark/seam sequencing) · *reading-order axis*. Score each lineage
0–10 on **Feasibility** (lower if it needs un-gateable arbitrary text / exact UI replication / face identity),
**Brief-fidelity** (does it preserve the locked beat boundaries + the dual-identity), **Novelty-vs-banlist**
(penalize ≥0.6 Jaccard overlap with a prior failed ordering). **Drop any lineage with `feasibility < 5`.**
Promote the top survivor to the active page order; keep the rest as candidate notes (failed orderings become
banlist memory so the next run never re-proposes them). The 抽卡 here is over *orderings*, not panel content —
panel content is filled deterministically in ⑥.

### ④ PAGE ORDER FIRST (its own fixed section, before any prose)
Author the chosen ordering as a **separate, fixed section that comes BEFORE per-panel prose** (the
`page_order` field of the `storyboard_spec`). Assign each panel to its stable page id + page TYPE + per-page
L/R world. End with an explicit `TOTALS` line: panel count · page count · how many NEW bakes vs reused DONE
images. This section is the authority the compiler and the gate check the eventual `comic.json` against.

### ⑤ Author the MOTIF STATE TABLE (master ledger, before per-panel prose)
Author the **MOTIF STATE TABLE** as the single source of truth for the continuity dimensions across **all**
panels, *before* writing any per-panel prose. One row per panel; the columns are `MOTIF_TABLE_COLUMNS`.
Encode every machine-checkable invariant directly in the table + its conventions block:
- **A motif column that is a thermometer** (the worked example's `Mug`): track ONLY the continuity-bearing
  instance (the `ML RESEARCH` motif mug: `hot` two steam wisps = temperature origin → `fading` one thin wisp
  → `cold` no steam + milk skin, a B01↔S20 bookend = "the hardest continuity constraint"). **Disambiguate
  motif-vs-env**: any look-alike that is just an environment prop (the `</>` mug) is tagged `env` and is NOT
  tracked — this is the *absence ≠ drift* / *design-aware gate* rule made concrete (a naive holistic gate
  would false-flag it).
- **DDL = MONOTONIC, NEVER REWIND.** The countdown is non-increasing across the ENTIRE film. Write the exact
  sequence in the conventions block (real: `T-24:00:00 → 19:42 → 19:42 → 18:55 → 18:40 → 18:30 → 17:46 →
  17:02 → 16:21 → 16:05 → 05:12 → 02:58 → 02:41 → 01:57 → 00:42 → 00:27(submitted)`). Two consecutive equal
  values are allowed (a "same-instant rhyme"); an *increase* is a hard veto. If any draft value would rewind,
  fix it inline and annotate the fix (real: `S06 DDL T-15:27 → T-18:40` purely so `18:40 > S07's 18:30`).
- **Two metric columns that NEVER co-mingle.** `exact_parse` carries `{0.60, 0.71, 0.66, 0.78, 0.89}`;
  `claim_delta` carries `{+6.2, +1.4}`. They are different metrics; writing one into the other's column is a
  veto. (Real: S10 shows `exact_parse 0.71→0.66` while `claim_delta` stays `—`; S14 shows
  `claim_delta +6.2→+1.4` while `exact_parse` stays `—`.)
- **bounce = the wordless emotion thermometer with a UNIQUENESS invariant.** `bounce = MAX` appears **exactly
  once** (real: `S02 是全片唯一 MAX`). Every later high is annotated "below S02". After the fall, **NO new peak
  is allowed** — a post-fall celebration must be written as *arrested* (real: `S12a = attempted celebration,
  ARRESTED before becoming a jump`, the codex fix that removed an earlier "MAX" there). The arc closes at the
  smallest bounce (real: `S21 = smallest bounce`, the mirror landing of S02).
- **MIRROR LOCKS** (paired non-adjacent constraints the table also pins): `REJECT card ↔ ACCEPT card` =
  exact same diagonal stamp geometry/angle (real: S11 ↔ S16, both from the shared verdict-card geometry,
  the audit hinge); `S02 unique-MAX bounce ↔ S21 smallest bounce`; a labeled wiki map ↔ its wordless twin
  share node coordinates **programmatically derived from one JSON** (real: S16b ↔ S22 from
  `wiki_starmap_nodes_v1.json`, 禁目测 — no eyeballing).

### ⑥ Per-panel 9-field spec, in comic page order (ONE panel at a time)
Walk the page order and author each panel in the fixed template — **finish one panel fully before starting the
next** (this is the "never batch-generate-then-look" lesson at authoring time). Each panel carries:
1. **title + beat + page-type + world** (the header anchor).
2. **`text_mode`** ∈ `{baked, html}` — `baked` = the image model renders the in-frame text; `html` = the
   panel is a pure scene and ALL text lives in the HTML overlay (zero glyphs in the image).
3. **`content_blueprint`** — which canonical SVG asset is instantiated + the exact literal layout (e.g.
   "from `assets/ddl_widget_template_v1.svg` instantiate `T-24:00:00`, amber on a navy widget, screen-corner").
4. **`expected_literals`** — the blind-transcribable tokens that **will be gated** (see the contract below).
5. **`scene`** — the staged environment (density target, books/props, the warm/dark world rendered).
6. **`characters`** — who is present + their motif-table state (bounce, pose); note who is absent and why.
7. **`bubbles{zh,en}`** — speaker + style + bilingual line. **Skill names NEVER appear in a bubble or in-frame**
   (铁律) — they live only in `side_narration`.
8. **`side_narration{zh,en,trait}`** — first sentence = *what happened*; second = the ARIS capability *bound to
   a story cost*; the `trait` tag names the bound skill. (The 侧栏讲解铁律 inherited from the outline.)
9. **`motifs`** — restate that panel's row of the MOTIF STATE TABLE (must agree with ⑤ exactly).
10. **`asset_requests`** — the canonical asset names this panel consumes (whitelist only).

**In the human `STORYBOARD_DRAFT.md`, a DONE / reused panel's row carries ONLY `status` + `side_narration` +
`motifs (as baked)`** — locked, never retro-edited (real: S12–S15, baked images promoted from a grid to single
pages; their square crops stay in the existing 2×2 recap; no regeneration). A DONE panel that is edited is a
hard veto. **The wiki `panel_spec` node is NOT reduced:** `validate_wiki.py` `PAYLOAD_REQUIRED["panel_spec"]`
unconditionally requires all 13 fields for EVERY panel_spec (no DONE exemption), so a DONE/reused panel's
`panel_spec.payload` must still carry every field, holding its prior locked values unchanged (never retro-edited).
The reduced 3-field form is a STORYBOARD_DRAFT.md convenience only.

### ⑦ Enforce the baked-vs-gate contract per panel
`expected_literals` holds **ONLY the salient, large, blind-transcribable tokens**; everything visible-but-not-
gated is **explicitly excluded in writing**:
- Sub-threshold chips out of contract — real: the S09 `Tok|yo` chip is sized ≤1.5% frame height, *"below
  blind-review transcription threshold"*, NOT in `expected_literals` (it is a deliberate foreshadow, no
  callout, no arrow); it becomes hero/gated only at S10.
- Skill names NEVER in-frame (铁律) — they are side-narration only.
- ASCII-only gating — real: S20 gates `SUBMITTED`; the `✓` is decorative non-ASCII and is out of contract.
- A deliberately *sub-gate* token must never be smuggled into `expected_literals` (hard veto).

### ⑧ Consolidate ASSET_REQUESTS (one canonical owner per token; naming 铁律)
Collect every panel's `asset_requests` into ONE canonical, deduped, authoritative list. Apply the **naming
铁律**: declare all draft-era name variants void and map them to the single canonical name; pin **one
parametric source per recurring motif** (real: ONE `ddl_widget_template_v1.svg` is the sole render source for
the entire 18-instance countdown timeline; ONE `stamp_family_v1.svg` for ALL verdict stamps — no two stamp
sets, and it must match the already-baked S12–S15 stamps; ONE `wiki_starmap_nodes_v1.json` is the single truth
source shared by the labeled map S16b and its wordless twin S22). Flag P0 blockers (real:
`researcher_chibi_canonical_ref_v001.png` missing — only the duo had a canonical ref) and enumerate
zero-new-work reuse (DONE panels, the existing recap page, S01's baked image reused as a set-continuity
condition ref for S20/S21 same-room/same-desk/same-camera).

### ⑨ Emit nodes, attach the review, THEN invoke the gate (two steps — never cold)
Write the wiki nodes (§ below) and append the author edges. The storyboard gate is a **score-FUSER**: it
walks `reviews` edges into the target, fuses the pre-existing `review:*` score-nodes, and **HARD-FAILS if
zero are attached** ("no reviews — gate is a score-fuser, not a reviewer"). So before invoking it:

0. **Asset-lock precondition (ordering).** A panel asset must be `status: locked` AT GATE TIME
   (`panel_assets_referenceable` = *resolves AND locked*). If you filed any `asset_requests`, that REOPENS the
   asset layer — drive those assets through the asset gate to `locked` **before** running the storyboard gate.
   Never run `--gate storyboard` with an un-locked `asset_request` outstanding (it will hard-veto on
   `_unresolved_asset_refs`).
1. **Pre-gate review (fan-out → persist).** The storyboard gate is **structural, CC-only** (no visual
   reviewer — no pixels exist yet), so the cross-model lens here is the structural validator run, not a
   panel of model families. Compute the four structural facts (below) and persist them as a `review` node:
   `node_id: review:<slug>`, `payload {target_node_id: "storyboard:<slug>", reviewer, gate_kind: "storyboard",
   review_scores:{panel_assets_referenceable, global_policies_valid, panel_count_band_aligned,
   continuity_chain_well_formed}}`, with a **`reviews`** edge `review:<slug> → storyboard:<slug>`.
2. **Invoke the fuser.** `python3` / call **[`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md)
   `<storyboard:slug> --gate storyboard`** to fuse + adjudicate against the EXACT predicate below. On an
   `approve` verdict (the gate's verdict set is `{approve, revise}`), the gate flips `storyboard_spec.status`
   → `locked`; on `revise` it sets/keeps `under_review`. (Canon ⑥ FLIP: `locked` is a STATUS reached by the
   advance verdict, never a verdict name.) The gate (a different model
   family) — never this authoring agent — acquits ([`artifact-integrity`](../../protocols/artifact-integrity.md)).
Reviewer routing for any model-family fan-out: Claude (one lens) ‖ Codex `gpt-5.5` `xhigh` ‖ Gemini
`auto-gemini-3`, file paths only ([`reviewer-routing`](../../protocols/reviewer-routing.md)).

## EXACT gate (`storyboard`) — quote [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) `--gate storyboard`
This is **not** this skill's rubric to define — [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md)
is the SOLE gate authority, and `--gate storyboard` is **STRUCTURAL, CC-only** (no visual reviewer; no pixels
yet). Verdict set `{approve, revise}`. The text below is quoted verbatim from that gate so this skill authors
to the real predicate — if the two ever diverge, the gate wins.

**Scored dimensions = exactly FOUR; each scored `0–5`; ADVANCE (`APPROVE`) iff ALL FOUR ≥ 4.** These four are
**file-system facts the gate computes**, not reviewer opinion:
- **`panel_assets_referenceable`** — every asset ref in each *panel* **resolves AND is `status: locked`** (a
  still-unlocked `asset_request` FAILS this dim — see ⑨.0 for the lock-before-gate ordering).
- **`global_policies_valid`** — `global_policies` fields match expected (text-mode rules present; mirror-lock
  policy present; page-order authority declared).
- **`panel_count_band_aligned`** — panels-per-page in band per target tier `{mvp:(2,2), demo:(4,6),
  longform:(10,12)}` (in-range = 5, off-by-one = 3, further = ≤2), AND the `TOTALS` line reconciles (Σ
  panels-per-page == panel count; NEW + reused == total).
- **`continuity_chain_well_formed`** — the MOTIF STATE TABLE has one row per panel; links have no
  dangling / out-of-order / cycle; every per-panel `motifs` field agrees with its table row.

**STRUCTURAL HARD VETO** (forces `revise` **regardless of reviewer scores OR Codex** — these are NOT scored
≥4 dims, they are the gate's computed structural vetoes; "structural failures cannot be voted-around"):
1. Any non-empty `_unresolved_asset_refs` (a referenced asset missing or not `locked`).
2. Any non-empty `_policy_violations` (a missing/inconsistent `global_policies` field, incl. no
   page-order-first section).
3. Any non-empty `_continuity_breaks` (no MOTIF STATE TABLE; a row missing; a `motifs` field disagreeing).
4. An out-of-band `_panel_count_band`.
5. **DDL non-monotonic** (any countdown value increases) — the never-rewind invariant.
6. **bounce uniqueness broken** (more than one `MAX`, or a post-fall peak).
7. **The two metric columns co-mingle** (a `claim_delta` value in the `exact_parse` column or vice-versa).
8. **A DONE/reused panel was retro-edited** (the DONE-lock).
9. **The storyboard page order disagrees with the compiled `comic.json` page order** (the orphan-panel class) —
   the storyboard's page order is the authority; the compiler must conform, not the reverse.

Author-time obligations the structural facts above encode (this skill is responsible for them BEFORE the gate
runs, so the four dims pass and no veto fires): the page-order-first section, the 9-field-per-panel
completeness (DONE panels in the reduced locked form), `expected_literals` = salient blind-transcribable ASCII
only with the deliberate exclusions written out (a sub-gate chip smuggled in is a `baked_vs_gate_contract`
break), the consolidated one-canonical-owner-per-token asset list (no un-normalized alias), the text-mode/
blueprint match (a `baked` panel with no `content_blueprint`, or an `html` panel carrying in-frame literals,
is invalid), and the `✅ APPROVED by user <date>` provenance stamp from the outline layer.

## Two engine contracts to author to (fail-closed)
Author every `panel_spec` so the downstream blueprint + spiral never refuse it. **Mind the payload-vs-runtime
path split** (do NOT conflate them — see `schemas/node_schema.json`):
- `panel_spec.payload.content_blueprint` — what THIS skill writes: a deterministic description of which
  canonical SVG asset is instantiated + the exact literal layout (NOT a raw SVG, and **never** a
  `condition.content_svg` key — that prefix exists only on comic.json).
- `blueprint.payload.content_svg` — the actual SVG, authored later by
  [`comic-blueprint-author`](../comic-blueprint-author/SKILL.md) from this panel's `content_blueprint`.
- `comic.json` panel `condition.content_svg` (+ `condition.expected_literals`) — the RUNTIME fields the spiral
  engine reads (`spiral_engine.js` at `.condition.content_svg`); the compiler maps the blueprint into these.

Author to that chain so the downstream never refuses the panel:
1. **Every panel needs a `content_blueprint`** (a resolvable blueprint description) so the blueprint author can
   produce a non-empty `blueprint.payload.content_svg` → the engine's `condition.content_svg`. Do NOT plan a
   panel with no blueprint; the engine rejects a null `condition.content_svg` at runtime.
2. **A `baked` figure-panel MUST declare `expected_literals`** (exact numbers/keys, verbatim) in the panel_spec
   — these become the comic.json `condition.expected_literals` the engine fail-closes on. A scene panel with no
   audited numbers → `text_mode: "html"` (and its text moves to the HTML overlay).

## Node it reads / writes (`schemas/node_schema.json`)
**Reads** — one `outline_spec` (`node_id` `outline:<slug>`, must be `status: "locked"`): its
`narrative_beats`, `beat_table`, `motif_arcs`, `design_constraint`, `title`/`logline`/`tagline`, and the
`*_asset_ids` whitelists. Also reads the wiki banlist of prior failed orderings (for the 抽卡 novelty score).

**Writes** (status `under_review` → `locked` after the gate):
- **`storyboard_spec`** (`node_id` `storyboard:<slug>`) — payload required:
  `source_outline_id, page_order, page_ids, panel_ids, global_policies, motif_ledger_id,
  consolidated_asset_requests`. This is the envelope; `page_order` is the fixed authoritative ordering.
- **`motif_ledger`** (`node_id` `motif:<slug>`) — payload required: `source_storyboard_id, columns, rows,
  invariants, mirror_locks`. `columns` = the `MOTIF_TABLE_COLUMNS`; `rows` = one object per panel;
  `invariants` = the declarative predicates (`ddl_monotonic_non_increasing`, `bounce_single_max`,
  `metric_columns_disjoint`, `motif_vs_env_disambiguation`); `mirror_locks` = the paired constraints.
  **This node is READ by [`comic-continuity-audit`](../comic-continuity-audit/SKILL.md)** — the table is the
  per-panel ground-truth checklist that turns its cross-model audit from "infer the intent" into "verify
  against the row" (and makes *absence ≠ drift* design-aware).
- **`panel_spec`** × N (`node_id` `panel:<slug>`) — payload required: `source_storyboard_id, page_id,
  panel_id, sequence_index, page_type, world, asset_ids, text_mode, expected_literals, content_blueprint,
  bubbles, side_narration, motifs`. (cover/finale panels additionally carry `safe_zones` + the endcard
  fields.) Every `panel_spec` — including DONE/reused — carries ALL the required payload fields above (the
  reduced 3-field form is the `STORYBOARD_DRAFT.md` convenience only, never the wiki node).
- *(optional)* **`continuity_constraint`** × M (`node_id` `cont:<slug>`) — payload required: `family,
  constraint_text, applies_to_panel_ids, source_node_id, active` — for a constraint the gate should check
  per-panel as a standalone predicate (e.g. one per mirror lock).

Author edges (every `type` MUST be in `validate_wiki.py` `EDGE_TYPES` or the wiki hard-fails — there is no
`contains` / `generated_from` / `references_asset` in that set):
- **`derived_from`** (storyboard_spec → outline_spec) — "this storyboard was authored from that outline".
- **`uses_motif_ledger`** (storyboard_spec → motif_ledger) — the ledger this storyboard owns.
- **`uses_asset`** (panel_spec → each whitelisted *locked* asset it consumes); for a *newly-requested* asset
  (one filed via `asset_requests`, not yet built) emit **`plans_asset`** (panel_spec → asset) instead.
- **No storyboard→panel containment edge** — there is none in the vocab. Membership is already carried by the
  `storyboard_spec.payload.panel_ids` / `motif_ledger_id` fields and each `panel_spec.payload.source_storyboard_id`.

All verdict-bearing runtime edges (`attempt_of`/`reviews`/`decides`/`rollback_of`) belong to Phase 2/3, not
here. Trace every gate round to `trace.jsonl` ([`review-tracing`](../../protocols/review-tracing.md)).

## Worked example
The canonical exhibit is **[`examples/comic_m3_audit/story/STORYBOARD_DRAFT.md`](../../examples/comic_m3_audit/story/STORYBOARD_DRAFT.md)**
— the full real artifact: a **24-panel / 19-page** pixel-art comic of "ARIS handed over 24 hours". Copy its
exact shape:

- **Header / provenance + gate state** (lines 1–2): `storyboard layer draft v1 — revised per codex
  cross-model critique (verdict REVISE applied); ✅ APPROVED by user 2026-06-10 ("批了") — asset-library
  build started`. The user-first gate is honored before any asset work.
- **PAGE ORDER FIRST** (lines 3–6), the real 19-page layout verbatim:
  `P00_cover[S01·full-bleed] → P01_b02[S02·single·seam-split] → P02_b03[2-up S03(L warm)|S04(R dark)] →
  P03_b04[S05] → P04_b05[S06] → P05_b06[vertical-3 S07/S08/S09 big] → P06_b07[2-up mirror S10(L)|S11(R)] →
  P_B08_0[S12a NEW] → P_B08_1..4[S12–S15 reuse] → P02_b08[grid2x2 recap S12–S15 kept] → P_B09[S16
  mirror-of-S11] → P_B09_5[S16b big-frame star-map] → P_B10[S17] → P_B11[2-up seam S18(L)|S19(R)] →
  P_B12[2-up S20(L)|S21(R seam)] → P03_end[S22 endcard]`. **TOTALS: 24 panels · 19 pages · 20 NEW bakes +
  4 reused DONE (S12–S15).**
- **The CORRECTED MOTIF STATE TABLE** (lines 14–39) — the load-bearing artifact. Columns
  `Panel | Mug | DDL | Tok|yo | exact_parse | claim_delta | bounce`. Patterns to copy: the monotonic-DDL fix
  (`S06 T-18:40` so it stays `> S07's 18:30`); split metric columns (`S10 exact_parse 0.71→0.66` with
  `claim_delta —`; `S14 claim_delta +6.2→+1.4` with `exact_parse —`); bounce uniqueness (`S02 是全片唯一 MAX`;
  `S12a = attempted celebration, ARRESTED before becoming a jump`; `S21 = smallest bounce`); motif-vs-env
  (the `</>` mug tagged `env`, never tracked).
- **Per-panel 9-field specs** (e.g. S01 at lines 45–57, S02 at 59–73) — the exact template to fill, including
  `expected_literals: ["DDL", "T-24:00:00"]`, the side_narration `trait` tag, and the `motifs` line restating
  the table row.
- **DONE-panel reduced form** (S12–S15, lines 221–247) — only `status` + `side_narration` + `motifs (as baked)`.
- **Consolidated ASSET_REQUESTS** (lines 369–383) — the 10-entry canonical list + the naming 铁律 (draft
  variants declared void) + the single-source pins + P0 blocker + zero-new-work reuse.

## Hard do / don't (earned lessons)
- **DO** require a LOCKED, user-approved outline + locked assets before authoring; HALT with the offending
  node id otherwise. Convergence is the upstream gate's job, not yours.
- **DO** author the **page order as its own section BEFORE any prose**, and the **MOTIF STATE TABLE before
  any per-panel prose** — both are sources of truth the gate and compiler check against.
- **DO** fill **one panel at a time**, fully, in page order. NEVER batch-author all panels then look — the
  ledger + per-unit spec is precisely the guard against that failure.
- **DO** keep `expected_literals` to salient blind-transcribable ASCII only, and write out the deliberate
  exclusions (sub-threshold chips, decorative non-ASCII, skill names).
- **DO** consolidate assets to one canonical owner per token and map every draft alias to it.
- **DON'T** let a panel free-describe an asset — reference the whitelist or file an `asset_request`.
- **DON'T** ever rewind the DDL, emit a second `MAX` bounce, add a post-fall peak, or co-mingle the two metric
  columns — each is a hard veto.
- **DON'T** retro-edit a DONE/reused panel.
- **DON'T** put a skill name in a bubble or in-frame; it lives in `side_narration` only.
- **DON'T** self-acquit. The cross-layer gate (a different model family) decides; the loop drives, it can't
  acquit.

## Protocols (governance contracts this skill honors)
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — the 抽卡 Codex call and the cross-layer gate get **file paths only** (the locked outline, style bible, banlist) behind an `=== EXTERNAL CONTEXT (advisory) ===` fence, never this agent's interpretation; the brainstorm family ≠ the gate family.
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — the loop can DRIVE but can't ACQUIT; user approval of the outline is the hard precondition gate (never proceed without it); the storyboard gate (different model family) acquits the layer.
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Codex `gpt-5.5` `xhigh`; Gemini `auto-gemini-3`; never downgrade the reviewer tier (effort never lowers reviewer quality).
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — the agent that authors the storyboard does not judge its own correctness; the MOTIF STATE TABLE is the ground-truth spec a fresh reviewer verifies, never the author.
- [`review-tracing`](../../protocols/review-tracing.md) — every 抽卡 round + gate round is logged to `trace.jsonl` so each verdict (and each dropped lineage) is auditable.
