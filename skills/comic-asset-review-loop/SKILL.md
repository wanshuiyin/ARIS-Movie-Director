---
name: comic-asset-review-loop
description: "Phase-1 (S5) UPSTREAM ref-asset gate — the bounded cross-model adversarial loop that LOCKS one reusable identity-locked asset (character sheet / location plate / prop cutout / text-panel / logo-free symbol) BEFORE it can be composited into any panel. This is NOT the panel_gate (composed-output) or the assembly_gate (cross-panel) — it gates the refs that FEED both, so identity drift is caught at the source, not downstream. Two layers: (1) a MANDATORY static single-source collision check (check_asset_collisions.py — 'one visual dialect, never two', enforced by tool) + zero-text/literal build-asserts; (2) a per-round 3-reviewer panel (Claude narrative ‖ Gemini visual ‖ Codex synth) that blind-scores 5 dims and LOCKS only at 准×3 unanimity (prior_lock_count>=3 approvals in the SAME round) — else regenerate (route to comic-asset-ref-generator) or, at MAX_REVIEW_ROUNDS, escalate the asset REQUIREMENT back to outline/storyboard. Hard IP veto. Use when you say 'lock this character ref', 'asset gate', 'ref review', 'is this sheet reusable', '锁角色 ref', before any metered panel bake."
argument-hint: [asset_id | --batch-from-outline | --lite]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, mcp__codex__codex, mcp__codex__codex-reply, mcp__gemini__analyzeFile, mcp__gemini-cli__ask-gemini, mcp__oracle__consult
---

# comic-asset-review-loop — the UPSTREAM ref gate (Phase 1 · S5)

The **ref gate the comic side was missing.** `comic-director`'s `panel_gate` reviews *composed output*; the
`assembly_gate` reviews *cross-panel consistency*. Neither gates the **identity refs that feed both** — so
without this skill, identity drift is only caught *downstream*, after credits are spent on a panel bake. This
skill is the **Layer-2 gate on a SINGLE reusable reference asset** (the character sheets / location plates /
prop cutouts the `ART_BIBLE.md` points every bake at), run **before** any panel composition.

A reusable asset is a one-way door: once a hundred panels condition on `duo_canonical_ref_v001.png`, you cannot
quietly swap it. So the lock must be **earned cross-model**, never self-certified by the generator. This skill
locks an asset **only at 准×3** — Claude *and* Gemini *and* Codex each independently pass the **same** review
round — or it sends the asset back to be regenerated, or (at the round ceiling) escalates the asset
*requirement* itself back to the outline/storyboard layer. The executor (and the generation model family)
**never** acquit their own ref.

```text
  asset (review_status:"pending")  ◀── comic-asset-ref-generator (S4: generates, NEVER self-locks)
        │
        ▼
   LAYER 1 — STATIC CI GATE (deterministic, zero credits)
        check_asset_collisions.py  (one canonical owner per filename — "one visual dialect, never two")
        + build asserts: zero-text contract · literal contract · raster-ref 6-field completeness
        │  pass
        ▼
   LAYER 2 — VISUAL LOOP   (round R = 1 … MAX_REVIEW_ROUNDS=3)
        ① Claude narrative  ‖  ② Gemini visual (primary: identity/iso)  ‖  ③ Codex synth (policy/semantic)
        each reads the REAL asset file · scores 5 dims (0–5 ints) · flags failure_modes from the fixed vocab
        │
        ▼ Codex synthesises: MIN-fuse per dim (max for inverted) · threshold · per-reviewer unanimity
   准×3 ? ── no, a family HARD-FAILS a floor ─▶ comic-asset-ref-generator --regenerate (bump version) ─▶ ① R+1
        │ no, third family just ABSENT (e.g. Gemini down) ─▶ re-VOTE (re-collect the missing reviewer; NO re-bake)
        │ no (safety_ip<3)  ─▶ HARD abandon_shot (IP veto, no retries)
        │ no (R == MAX_REVIEW_ROUNDS) ─▶ ESCALATE the asset REQUIREMENT to outline/storyboard (abandon_shot)
        │ yes
        ▼
   LOCK  — asset.status=locked + payload.review_status=locked  (ONE-WAY DOOR, immutable for the rest of Phase 1)
        + score_progression audit table (ASSET_REVIEW.md) + decision/review/failure_mode wiki nodes + edges
```

## Constants
- **REVIEWERS** = Claude (this agent, narrative) ‖ `mcp__gemini__analyzeFile` (`model: "auto-gemini-3"`, NEVER
  raw `gemini-3.1-pro` — 429 silent-downgrade to 2.5) ‖ `mcp__codex__codex` r1 / `mcp__codex__codex-reply` r2+
  (`gpt-5.5`, `model_reasoning_effort: "xhigh"`, save the `threadId`).
- **准×3 UNANIMITY** — the lock predicate. A Codex-synth `approve` is **NOT** enough: `cc_approves AND
  gemini_approves AND codex_approves` must ALL be true **in the same round** (each reviewer's *own* dim scores
  must independently clear threshold). Codex-approve-without-unanimity is **DOWNGRADED to `revise`** (the "准×3
  bite"). `prior_lock_count` = the count of approvals accumulated this round; **lock iff prior_lock_count >= 3**.
- **MAX_REVIEW_ROUNDS** = 3 (hard ceiling). Even if Codex keeps saying `regenerate`, the loop STOPS at 3 and
  routes back to outline/storyboard — the *requirement* changes; the gate does not grind an image forever.
- **CROSS-MODEL ACQUITTAL** — Codex is the **synth/policy** reviewer and (in the broader pipeline) the
  generation family for raster refs. A Codex `approve` can *diagnose/veto* but is **never the sole acquitter**;
  the lock needs Gemini approve + Claude approve too (acceptance-gate.md: the loop DRIVES, it can't ACQUIT).
- **SAFETY_IP SINGLE-VOTE VETO** — `safety_ip < 3` from **ANY** reviewer = immediate HARD `abandon_shot`, no
  retries (generalises `comic-director`'s anatomy single-vote veto to IP/likeness).
- **`--lite` is NON-ACQUITTING** — when Gemini is unavailable it may set only a PROVISIONAL
  `status: under_review` (tag `lite_provisional: true`), **NEVER a root `status: locked`.** The one-way LOCK
  requires the THIRD family (Gemini) to lock-pass in a later round: 准×3 is CC AND Gemini AND Codex same-round
  unanimity (canon), and the only sanctioned relaxation is the gate's "a model is UNAVAILABLE → threshold-only
  PROVISIONAL, exit 2" — never a Gemini-absent lock. Use `--lite` only to keep progress while Gemini is down;
  never the default; it can never write the locked one-way door.
- **OUTPUT** = `examples/<project>/story/ASSET_REVIEW.md` (the human score-progression audit) + wiki nodes/edges
  under `wiki/nodes/` + per-reviewer trace under `.aris/traces/comic-asset-review-loop/`.

## Input contract / what this skill owns
The contract boundary is the **`asset` wiki node** authored by [`comic-asset-ref-generator`](../comic-asset-ref-generator/SKILL.md) (S4) at
`review_status: "pending"` — generated, never self-locked. This skill is **pure verify + lock**:
- It **never edits the asset's pixels or geometry** — on `regenerate`/`revise` it routes a ≤140-char
  `repair_instruction` back to S4, which bumps the version and emits a new file.
- It **never invents** scores or a verdict on behalf of an absent reviewer — a dim no reviewer scored is
  `not_scored` and **EXCLUDED** from the threshold, never substituted with 0 (the v1.0 bug; see Hard do/don't).
- It writes back **only** `status: "locked"` + `payload.review_status: "locked"` on a 准×3 approve, plus the
  review/decision/failure_mode trace. `locked` is the one-way door — immutable for the rest of Phase 1.

**Read** the `asset` node payload (per `schemas/node_schema.json`, `node_type: "asset"`,
`payload.required = [asset_kind, name, visual_description, identity_lock, ref_requirements, review_status,
version]`):
- `asset_kind` ∈ {character, scene, prop, text_panel, logo_free_symbol} — **routes the per-reviewer query**
  (see §"Asset-kind specialisation").
- `identity_lock.{must_preserve[], must_avoid[]}` — the per-asset rubric (e.g. from `ART_BIBLE.md` §1:
  executor = blue hoodie `#1D4684` + brown hair + **no beard**; reviewer = green hoodie `#30582D` + near-black
  hair + **beard**; "颜色/胡子/体型轮廓不可变").
- `ref_requirements.{aspect_ratio, background (white|transparent), pose, isolated_reference}`.
- `output_ref.{file_path, data_url, sha256, width, height, mime}` for a raster ref (all 6 fields, else schema
  violation) **OR** `{generator_script, owner_script, file_sha256}` for a deterministic SVG/JSON source.

## The EXACT gate (ported from `asset-review-loop`)

### Layer 1 — static CI gate (deterministic, MANDATORY, zero credits)
Run **before** any visual reviewer call (and re-run before lock). Fail-closed; correctness costs no credits.

- **single-source collision check** — `check_asset_collisions.py` static-scans every `gen_*.py` with the regex
  `\bw\(\s*["']([^"']+\.(?:svg|json|png))["']` and asserts **each output filename has EXACTLY ONE generator
  owner**. `len(writers) > 1` → `exit 1`. This is the tool that enforces **"one visual dialect, never two"**:
  two generators writing the same path with different content is a silent, run-order-dependent corruption
  (whoever runs last wins). It is deliberately **NOT** a "skip if file exists" guard — that would *hide* the
  order bug instead of surfacing it. Verdict: `exit 0` (clean) is a **precondition** for entering Layer 2;
  `exit 1` blocks the round and routes to S4 to rename/delete the duplicate. (Verified clean at 26 outputs in
  the worked example.)
- **zero-text contract** — for any asset that must contain no glyphs (e.g. the S22 constellation):
  `assert "<text" not in svg` in the emitter. A zero-text asset that contains text fails the round.
- **literal contract** — for a deterministic SVG/JSON source, its `_contract` field forbids re-layout-by-eye;
  the JSON is the single coordinate truth (e.g. `wiki_starmap_nodes_v1.json` for S16b labeled + S22 wordless).
- **raster 6-field completeness** — a raster `output_ref` has all of `file_path, data_url, sha256, width,
  height, mime`; `sha256` matches the file on disk (a partial write is a schema violation, not a lockable ref).

### Layer 2 — the 5-dim visual rubric (0–5 integers each)
Each reviewer **reads the real asset file** (image bytes via `Read` / `analyzeFile`) and scores all five; the
**Primary** reviewer's score is authoritative for that dim, the **Secondary** corroborates.

1. **identity_lock_satisfied** — preserves EVERY `must_preserve` trait, avoids EVERY `must_avoid`.
   **Primary = Gemini (visual)**, Secondary = Codex (semantic). character → face/age/hair/costume/beard;
   scene → layout + lighting-type + era.
2. **ref_quality** — sharp, well-framed, correctly exposed, artefact-free. **Primary = Gemini**,
   Secondary = Claude. (text_panel → glyph crispness weighted.)
3. **bg_isolation** — background is EXACTLY the required colour, isolated, no halo / shadow-spill / other
   subjects. **Primary = Gemini ONLY.** For a **scene** this dim becomes **scene_emptiness** (no characters or
   props sneaked into a location plate), same 0–5 scale.
4. **reuse_readiness** — compositable into multiple downstream conditions without per-shot rework.
   **Primary = Claude (usage_fit)**, Secondary = Gemini (composability).
5. **safety_ip** — no celebrity likeness / copyrighted character / brand logo. **HIGHER = SAFER** (5 = clean).
   **Primary = Codex (policy)**, Secondary = Gemini (recognition).

### EXACT verdict thresholds (Codex synth) + the 准×3 bite
> **These are THIS skill's pre-gate routing thresholds (the asset-gate step-3 routing this skill OWNS), and
> they are written to MATCH [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md)'s `--gate asset`
> LOCK predicate verbatim.** The gate's `LOCKED` condition is `identity_lock_satisfied >= 4 AND ref_quality >= 4
> AND bg_isolation >= 4 AND safety_ip >= 4` **AND** the `准 ×3` same-round cross-model unanimity rule —
> `reuse_readiness` is **ADVISORY** at the gate and does **not** block the lock. The `approve` rule below uses
> exactly those four floors; `reuse_readiness` only feeds `revise`/`regenerate` routing, never blocks the lock.

Codex **MIN-fuses** each dim across the reviewers who scored it (the gate's deterministic rule: **min** per dim,
**max** for an inverted dim, single scorer → use it, NO scorer → `not_scored` **EXCLUDE** — **never 0-substitute,
never average**: averaging `{5,3}`→4 would slip a sub-floor ref past the `>=4` lock; min=3 correctly fails). So
this inline routing can only be **stricter**, never weaker, than `--gate asset`. The legal asset verdict set is
`{approve, regenerate, locked, abandon_shot}` (gate-enforced); the internal `revise` below is an alias that
routes a `regenerate`. Then:

- **`approve`** ← `identity_lock_satisfied >= 4` **AND** `ref_quality >= 4` **AND** `bg_isolation >= 4`
  **AND** `safety_ip >= 4` (the four gate floors). **`asset_kind == "character"` override:**
  `identity_lock_satisfied == 5` is REQUIRED (a raster character ref locks only at a *perfect* identity score —
  4 is not enough for a face hundreds of panels condition on); the other three floors stay `>= 4`. (准×3
  same-round unanimity still applies on top — see the LOCK note below.)
- **`regenerate`** ← `identity_lock_satisfied < 4` (or `< 5` for a character) OR `bg_isolation < 4` OR
  `ref_quality < 4` OR `safety_ip ∈ [3, 4)` OR `reuse_readiness < 3` (advisory: routes a regen hint, does not
  itself block a lock that already clears the four floors).
- **`revise`** ← mid-band, a single targeted edit likely fixes it (softer hint, still routes a `regenerate`
  with a focused `repair_instruction`).
- **`abandon_shot`** ← `safety_ip < 3` (HARD STOP, IP) **OR** `round >= MAX_REVIEW_ROUNDS` without convergence.

> **Deterministic-SVG / JSON asset branch** (a parametric builder, NOT a raster ref → the visual 5-dim rubric
> does not apply). A deterministic-SVG source **locks iff ALL FOUR hold** (Layer-1 asserts + a 3-dim 0–5 read):
> `single_source_owner == pass` (Layer-1 `check_asset_collisions.py` exit 0 — exactly one generator owns the
> filename) **AND** `render_preview_legible >= 4` (the SVG/JSON rasterizes to a non-empty, on-spec preview PNG —
> a RAW render pre-check, not a vote) **AND** `literal_contract >= 4` (the `_contract` field is honored: literals
> are ascii-tokenizable, the JSON is the single coordinate truth, no eyeball re-layout) **AND**
> `style_family_consistency >= 4` (one visual dialect — palette/stroke/grid match the `ART_BIBLE.md` family).
> Plus the **zero-text / non-gated-text asserts**: a wordless source contains no `<text>` (`assert "<text" not
> in svg`); a labeled source's glyphs are exactly the contract's literals. Same 准×3 same-round unanimity gates
> the SVG lock as the raster lock. (Gemini PRIMARY on `render_preview_legible` + `style_family_consistency`;
> Codex PRIMARY on `literal_contract`; `single_source_owner` is the Layer-1 tool, not a reviewer vote.)

> **LOCK requires 准×3 UNANIMITY, not Codex-synth-approve.** Even on a Codex `approve`, the lock fires **iff**
> `cc_approves AND gemini_approves AND codex_approves` in the **same** round (each reviewer's own 5 scores
> independently clear the per-reviewer thresholds — including the `identity_lock_satisfied == 5` floor for a
> character ref / the four-dim SVG floors for a deterministic source). A Codex `approve` with any reviewer below
> threshold is **DOWNGRADED to `revise`**. (`--lite` is **non-acquitting**: with Gemini absent it may only write
> provisional `status: under_review` + `lite_provisional: true`, and can NEVER satisfy the LOCK predicate or reach P6.) This same-round
> unanimity rule is exactly [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md)'s `准 ×3` for
> `--gate asset` (this skill is the OWNER of that convention) — NOT "three consecutive rounds".

### Veto rules (hard, non-negotiable)
- **safety_ip < 3 from ANY reviewer → immediate `abandon_shot`** (single-vote IP veto, no retries).
- **Layer-1 fail (collision / missing literal / partial raster / zero-text breach) → block the round**, route
  to S4, do not enter Layer 2.
- **round >= MAX_REVIEW_ROUNDS without 准×3 → ESCALATE the asset *requirement*** to
  [`comic-outline-creator`](../comic-outline-creator/SKILL.md) / [`comic-storyboard-creator`](../comic-storyboard-creator/SKILL.md)
  (the spec/outline must change; stop re-baking the image). Mutual recursion is bounded by this ceiling.

### Controlled failure-mode vocabulary (the FIXED set reviewers draw tags from)
`face_drift, age_drift, costume_drift, pose_off, multi_subject_leak, halo_artifact, shadow_spill,
non_white_bg, jpeg_artifact, glyph_break, unintended_text, watermark_present, contact_sheet, celeb_likeness,
copyrighted_character, brand_logo_present, collage_grid, low_resolution, melted_anatomy`. Every reject mints a
`failure_mode` wiki node `fail:<asset-slug>_<tag>` tagged from this set (the `<tag>` must match `[a-z0-9_]+` —
strip any stray punctuation before assembling the node_id; maps to `comic-director`'s anatomy/identity vetoes) and routes
its tag into the S4 `repair_instruction`. The node MUST carry the schema-required shape (see the `fail:*`
skeleton in "Wiki node skeletons" below): root `status: "active"` + payload `{layer, affected_shot_ids, active,
repair_pattern}`. Because this is an **upstream asset gate with no shots yet**, `affected_shot_ids` is `[]`
(empty) — never invented; mirror the real `examples/comic_m3_audit/wiki/nodes/fail:*.json` shape.

## Wiki node skeletons (the EXACT shape each minted node MUST carry — validated by `cli/validate_wiki.py`)
Every node this skill writes obeys `schemas/node_schema.json`: the **root** carries `node_id, node_type, title,
status, created_at, payload` (all six required), the `node_id` matches `^(…|review|decision|fail):[a-z0-9_-]+$`,
and the `payload` carries every field in `validate_wiki.py` `PAYLOAD_REQUIRED` for that type. The canonical root
`status` for each runtime type (schema $comment; the real example nodes carry exactly these): `review →
"complete"`, `decision → "final"`, `failure_mode → "active"`. Copy these skeletons verbatim:

```jsonc
// review:*  — one per reviewer per round (P1 cc, P2 gemini, P3 codex). node_id: review:<asset-slug>_<reviewer>_round{R}
// PAYLOAD_REQUIRED["review"] = [target_node_id, reviewer, gate_kind]  (review_scores carries the 5 dims)
{ "node_id": "review:duo_canonical_ref_v001_cc_round1", "node_type": "review", "status": "complete",
  "title": "CC narrative asset review duo_canonical_ref v1 r1", "created_at": "<ISO-8601>",
  "payload": { "target_node_id": "asset:<asset-slug>", "reviewer": "cc", "gate_kind": "asset",
               "review_scores": { "identity_lock_satisfied": 5, "ref_quality": 4, "bg_isolation": 4,
                                  "reuse_readiness": 4, "safety_ip": 5 },
               "failure_modes_flagged": [], "timed_out": false } }

// decision:*  — one per round after the synth+准×3 (P4). node_id: decision:asset_<asset-slug>_round{R}
// PAYLOAD_REQUIRED["decision"] = [target_node_id, verdict, gate_kind]
{ "node_id": "decision:asset_duo_canonical_ref_v001_round1", "node_type": "decision", "status": "final",
  "title": "asset_gate duo_canonical_ref v1 r1 -> locked", "created_at": "<ISO-8601>",
  "payload": { "target_node_id": "asset:<asset-slug>", "gate_kind": "asset", "verdict": "approve",
               "reasoning": "LOCK 准×3 — identity=5 ref=4 bg=4 safety=5 reuse=4; cc&gemini&codex approve r1",
               "repair_instruction": "", "prior_lock_count": 3 } }

// fail:*  — only on a reject/abandon_shot (P0 Layer-1 fail, P2 parse failure-mode, P5 reject). node_id: fail:<asset-slug>_<tag>
// PAYLOAD_REQUIRED["failure_mode"] = [layer, affected_shot_ids, active]   (upstream gate → affected_shot_ids: [])
{ "node_id": "fail:duo_canonical_ref_v001_costume_drift", "node_type": "failure_mode", "status": "active",
  "title": "asset_gate duo_canonical_ref costume_drift", "created_at": "<ISO-8601>",
  "payload": { "layer": "asset_ref", "affected_shot_ids": [], "active": true,
               "repair_pattern": "executor 蓝衣棕发无须 (must_preserve); 当前绿衣漂移 — 重生为 #1D4684 hoodie" } }
```

After any lock (P6), run `python3 cli/validate_wiki.py examples/<project>` — it MUST PASS (root status enum,
node_id form, payload invariants). A node missing root `status` or `target_node_id` / `layer` /
`affected_shot_ids` / `active` is the exact failure the validator catches.

## The two fail-closed engine contracts (where they bite here)
This is an **upstream** gate, so it enforces the *preconditions* the downstream engine fail-closes on. **Do NOT
conflate the three SVG fields** (per `schemas/node_schema.json` + the engine): the wiki
`blueprint.payload.content_svg` (top-level on the blueprint payload), the `panel_spec.payload.content_blueprint`
(the panel_spec's own field — there is NO `content_svg` on a panel_spec), and the **comic.json** panel's
**runtime** `condition.content_svg` (the field the engine reads at `spiral_engine.js` `.condition.content_svg`).
1. **Every panel needs a renderable blueprint SVG.** A locked asset is only useful if a panel can condition on
   it — so when locking a deterministic SVG/JSON source, verify it rasterizes to a non-empty PNG (a `blueprint`
   node would carry it as `blueprint.payload.content_svg`), because at bake time the engine **refuses** a
   comic.json panel whose `condition.content_svg` is `null`/absent. A ref that cannot become a content-SVG
   condition is not "reuse-ready" — score `reuse_readiness` (and, for an SVG source, `render_preview_legible`)
   accordingly. **Never `condition.content_svg: null`.**
2. **A baked figure-panel needs `condition.expected_literals`.** If the asset is a **text_panel** / figure
   source whose downstream panels bake numbers (e.g. a wandb curve, a verdict stamp, a DDL widget), its lock
   MUST verify the literal contract holds (the literals are ascii-tokenizable and the JSON `_contract` forbids
   eyeball re-layout) — because `comic-director`'s gate **refuses to run** a baked figure-panel whose comic.json
   `condition.expected_literals` is empty. Locking a figure source that cannot supply gateable literals would
   strand the panel; a scene panel with no audited numbers takes `text_mode: "html"` instead.

## Numbered procedure (per round R, start R = 1, loop until 准×3 or R = 3)

**P0 — Resolve + Layer-1 gate.** Resolve the target `asset` node (single `asset_id`, or fan out one branch per
asset under `--batch-from-outline`). Assert `review_status == "pending"`; **abort if already `locked`** (one-way
door). Route by `asset_kind` (visual raster kinds → the raster 5-dim branch; a deterministic SVG/JSON source →
the SVG 4-dim branch; an audio kind would take the audio branch — out of scope for the comic). **Run Layer 1**
(`check_asset_collisions.py` + build-asserts + raster 6-field check); on any failure, write a `failure_mode`
node (root `status: "active"`, payload `{layer:"asset_ref", affected_shot_ids:[], active:true, repair_pattern:
<the Layer-1 tag-derived hint>}` per the `fail:*` skeleton) + a `failure_of` edge `fail:<…> → asset:<asset-slug>`,
route to S4, and stop — do not spend a visual reviewer call.

**P1 — Claude narrative review.** `Read` the PNG (image bytes). Score all 5 dims (Claude **PRIMARY** on
`reuse_readiness`; Codex is PRIMARY on `safety_ip` per the rubric), emit `failure_modes_flagged[]` (from the
fixed vocab) + `narrative_notes`. Write a review-stage scratch JSON and a wiki `review` node
`review:<asset-slug>_cc_round{R}` with **root `status: "complete"`** and payload carrying the three
PAYLOAD_REQUIRED fields **`target_node_id: "asset:<asset-slug>"`, `reviewer: "cc"`, `gate_kind: "asset"`** plus
`review_scores` keyed by the 5 dims (see the `review:*` skeleton above). Append a **`reviews`** edge
`review:<…> → asset:<asset-slug>` (review → target — the direction the gate walks; NEVER `reviewed_by`).
**Atomic write** (`.tmp` → `mv`).

**P2 — Gemini visual review** (skip iff `--lite`). Call `mcp__gemini__analyzeFile` with `model:
"auto-gemini-3"` (NEVER raw `gemini-3.1-pro`), the PNG path, and a **strict-JSON-only** template that asks for
the 5 dim scores (Gemini **PRIMARY** on `identity_lock_satisfied`, `ref_quality`, `bg_isolation`) +
`failure_modes` drawn from the fixed vocab. **Retry once** on non-JSON, then log a `gemini_parse_failure` and
treat those scores as `null` (not 0). Optional focused follow-up if `identity_lock_satisfied < 3`. Write the
`review` node `review:<asset-slug>_gemini_round{R}` with **root `status: "complete"`** and payload
**`target_node_id: "asset:<asset-slug>"`, `reviewer: "gemini"`, `gate_kind: "asset"`** + `review_scores`; append
the **`reviews`** edge `review:<…> → asset:<asset-slug>` (review → target). On a parse failure mint a `fail:*`
node per the `fail:*` skeleton (root `status: "active"`, payload `{layer:"asset_ref", affected_shot_ids:[],
active:true, repair_pattern:"gemini_parse_failure — re-elicit strict JSON"}`).

**P3 — Codex synth gate.** `mcp__codex__codex` (r1) / `mcp__codex__codex-reply` (r2+ with the saved
`threadId`), `gpt-5.5` `xhigh`. Pass **ONLY** numeric scores + `failure_modes` + `asset_metadata` + file paths
+ (optional) numeric prior-round deltas — **NEVER** any reviewer `narrative_notes`/prose (reviewer-independence;
a prose leak ABORTS the call with a loud error). Codex adds its OWN `safety_ip` (PRIMARY) + semantic
`identity_lock_satisfied` + `reuse_readiness` scores. **First persist Codex's OWN reviewer node** (mirroring P1
cc / P2 gemini): `review:<asset-slug>_codex_round{R}` (root `status: "complete"`, payload `{target_node_id:
"asset:<asset-slug>", reviewer: "codex", gate_kind: "asset", review_scores: {the 5 dims Codex scored}}`) + a
`reviews` edge `review:<…>_codex_round{R} → asset:<asset-slug>` — so all THREE reviewer families exist as
first-class collected nodes (准×3 needs Codex as one of the three the gate walks). THEN synthesise: **MIN-fuse**
each dim across the reviewers who scored it (max for an inverted dim; single scorer → use it; no scorer →
`not_scored`, EXCLUDE — never average / 0-substitute) → `verdict` + `per_reviewer_unanimity{cc,gemini,codex}` +
`repair_instruction` (≤140 chars) + `rationale` (≤300 chars — the ONLY Codex prose allowed out).

**P4 — Apply threshold + 准×3 → `decision` node.** Apply the threshold, then the unanimity downgrade. Write a
`decision` node `decision:asset_<asset-slug>_round{R}` with **root `status: "final"`** and payload carrying the
three PAYLOAD_REQUIRED fields **`target_node_id: "asset:<asset-slug>"`, `verdict`, `gate_kind: "asset"`** plus
`reasoning`, `repair_instruction`, `prior_lock_count` (see the `decision:*` skeleton above). `approve` +
`prior_lock_count >= 3` (准×3) → mark **lock**. `approve` without unanimity → downgrade to `revise`, which is
**persisted as `verdict: regenerate`** — the only legal `decision.payload.verdict` tokens are
`{approve, regenerate, locked, abandon_shot}` (a verdict outside the gate's set is a hard error); `revise` is an
internal route label kept in `reasoning`/`repair_instruction`, never written as the verdict. A TERMINAL
fail — `abandon_shot` (IP veto) OR the `R == MAX_REVIEW_ROUNDS` escalation (P5) — sets **BOTH** root
`asset.status: "rejected"` AND `payload.review_status: "rejected"` (canon D2/D3: terminal-fail → root `status`
rejected; mirror the lock path, which sets both). A non-terminal `revise`/`regenerate` keeps root
`status: "under_review"` (provisional), never leaving an abandoned asset stuck at `pending`.
> **Gate handoff (this skill is the asset gate's review-producer).** P1–P3 have now persisted the `review:*`
> score-nodes + `reviews` edges that [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) `--gate
> asset` collects — so the gate is **never invoked cold**. This skill runs the asset-gate synthesis inline (it
> OWNS 准×3); when the orchestrator defers acquittal to `comic-cross-layer-gate <asset:<asset-slug>> --gate
> asset` instead, it fuses the SAME `review:*` nodes via those `reviews` edges and re-derives the `>=4`-floor +
> 准×3 verdict. NOTE this skill applies an ADDITIONAL stricter pre-gate floor (character
> `identity_lock_satisfied == 5`; the deterministic-SVG 4-dim branch for an identity-4 ref), so its inline
> verdict can be **stricter** (never weaker) than the bare gate's `>=4` floor — the deferred gate does not
> reproduce the `==5` character rejection byte-for-byte. The `decides` edge (P5) links this `decision` → the asset.

**P5 — Edges + route.** Write edges using ONLY `validate_wiki.py` `EDGE_TYPES`: a **`reviews`** edge
`review:<…> → asset:<asset-slug>` per reviewer (review → target — the direction `--gate asset` walks; NEVER
`reviewed_by`, the opposite direction, which the gate cannot follow), the **`decides`** edge
`decision:asset_<…> → asset:<asset-slug>`, and on a reject/abandon_shot a **`failure_of`** edge
`{src: "fail:<asset-slug>_<tag>", dst: "asset:<asset-slug>", type: "failure_of"}` (failure_mode → target,
matching the real `examples/comic_m3_audit/wiki/edges.jsonl`). A regen that supersedes the prior version writes a
**`supersedes`** edge `asset:<new> → asset:<old>` (bare node_ids, no `@vN`). Then route:
- **third family merely ABSENT this round** (a reviewer didn't vote — e.g. Gemini down, or `--lite`) and NO
  family hard-failed a floor → **RE-VOTE**: re-collect ONLY the missing reviewer (re-run that one family); do
  **NOT** `--regenerate` (re-baking wastes a credit when the image is fine and only the third vote is missing).
- `regenerate`/`revise` (a family HARD-FAILED a floor) **and R < 3** → call
  [`comic-asset-ref-generator`](../comic-asset-ref-generator/SKILL.md) `--regenerate` with the
  `repair_instruction` (it bumps the version, emits a new PNG with a `supersedes` self-edge, re-fires at **R+1**).
- `regenerate`/`revise` **and the re-bake count reaches `MAX_ASSET_REGEN` = 4** (the gate's re-bake cap,
  [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) lines 70/184 — a SEPARATE ceiling from this
  skill's own `MAX_REVIEW_ROUNDS = 3` visual review-round limit; either hitting its ceiling escalates) → force
  **`abandon_shot`** → **ESCALATE the requirement** to outline/storyboard.
- `abandon_shot` (IP) → exit immediately.

**P6 — Lock** (on `approve` + full 准×3 = CC AND Gemini AND Codex same-round unanimity). Set `status: "locked"`
+ `payload.review_status: "locked"`; append tags `[asset_gate_locked, round_{R}_approve]`. (**`--lite` can NOT
reach P6** — with Gemini down it stays provisional `under_review`, never locked.) Validate against
`schemas/node_schema.json` (`python3 cli/validate_wiki.py examples/<project>`); append a `log.md` line; write
the final **`ASSET_REVIEW.md` score_progression** table (the human audit trail — *why* it locked at r2 vs r3
vs abandoned). **Lock = ONE-WAY DOOR**, immutable for the rest of the pipeline.

## Asset-kind specialisation (drives the per-reviewer query)
- **character** → identity_lock weights face/age/hair/costume/**beard** (the `ART_BIBLE.md` §1 iron law:
  executor never bearded, reviewer always bearded; colours immutable, L/R position free).
- **scene** → `bg_isolation` becomes **scene_emptiness** (a location plate must carry no characters/props).
- **prop** → standard 5 dims; `bg_isolation` weighted (clean cutout, no spill).
- **text_panel** → glyph crispness weighted into `ref_quality` (maps to `comic-director`'s
  `baked_text_quality`); the literal contract (engine contract #2) is checked at lock.
- **logo_free_symbol** → **extra `safety_ip` weight** (the symbol must not resemble a real brand mark).

## The judge-is-broken guard (battle lesson — land it, don't just say it)
**IDENTICAL scores across review rounds mean the rubric/judge is broken — STOP regenerating and audit the
judge.** If round R and round R+1 (on a *regenerated* asset) return the **same** per-dim vector from the same
reviewer, the artifact changed but the score did not → the **rubric** (not the asset) is wrong. Concretely:

- **Detect**: after P4 on R+1, compare the per-reviewer dim vectors to round R's. If `cc`/`gemini`/`codex`
  return a byte-identical 5-vector on a *new* file (different `sha256`), **flag `judge_stuck`**.
- **Halt the bake**: do NOT route another `--regenerate`. Two identical rounds is the ceiling for *grinding*
  even before MAX_REVIEW_ROUNDS.
- **Audit the judge** instead: re-read `identity_lock.{must_preserve,must_avoid}` and the `ART_BIBLE.md` carve-
  outs — is the gate flagging a **by-design** trait as drift? (The classic: the two-world warm/dark palette is
  *intentional* — `ART_BIBLE.md` §0.5 "冷暖是 by-design 的,不是漂移"; a naive gate scores it "style drift"
  every round. The `motif`-vs-`env` disambiguation is the same lesson: the gate must know which instances are
  continuity-bearing.) Fix the rubric (sharpen the per-dim definition / add the carve-out to the reviewer
  query), record it as a `decision` trace node, then resume. **A stuck score is a judge bug, not an asset bug.**

## Worked example
Ground every run in the real M3-audit comic asset set under `examples/comic_m3_audit/` (repo-relative). The exact patterns to copy:

- **Layer-1 collision gate** — `gen/check_asset_collisions.py` (41 lines) is the single-source CI gate
  verbatim: the `WRITE = re.compile(r'\bw\(\s*["']([^"']+\.(?:svg|json|png))["']')` scan over every `gen_*.py`,
  the `len(writers) > 1` collision rule, the `exit 0/1` contract, and the load-bearing comment that it is
  **deliberately NOT** a "skip if the file already exists" guard ("that would HIDE the order bug instead of
  surfacing it"). Its message — *"Each asset must have ONE canonical owner ('one visual dialect, never two')"*
  — is the literal embodiment of this skill's single-source rule. **Verified clean at 26 outputs (exit 0).**
  Run this as Layer 1 of P0; do not enter Layer 2 until it returns 0.

- **The identity-lock rubric** — `ART_BIBLE.md` §1 (`角色身份锁`) is the literal `must_preserve`/`must_avoid`
  source for an `identity_lock_satisfied` score: authority ref `duo_canonical_ref_v001.png`; per-character hex
  table (executor blue hoodie `#1D4684` / brown hair `#925935` / **NO beard**; reviewer green hoodie `#30582D`
  / near-black hair `#0F0D16` / **beard**); the 铁律 *"executor 永远蓝+棕发+无须;reviewer 永远绿+黑发+有须 …
  颜色/胡子/体型轮廓不可变"*. A Gemini visual reviewer cat's the PNG and scores it against **this** — not by
  vibes. §0.5 (the warm/dark two-world palette, *"冷暖是 by-design 的,不是漂移"*) is the canonical carve-out
  for the judge-is-broken guard above. §7 FORBIDDEN (no smooth gradients on character surfaces, no voxel, no
  non-canonical mascot colours, no off-identity beard) is the `must_avoid` list.

- **The P0-blocker pattern** — `story/STORYBOARD_DRAFT.md` flags `researcher_chibi_canonical_ref_v001.png` as
  **missing** (only the duo had a canonical ref). That is exactly the state this gate must catch *before* any
  panel bakes the researcher: a raster ref with no file is not lockable (Layer-1 raster 6-field check fails);
  it routes to S4 to generate the ref, and only then does Layer 2 run. **Copy this:** a panel that conditions
  on a ref whose asset node is not `locked` is a pre-bake blocker, surfaced here, never discovered downstream.

Pattern to copy end-to-end: **Layer 1 (deterministic, free) gates single-source + completeness → Layer 2
(cross-model, metered only after L1 passes) gates the 5 dims against the `ART_BIBLE.md` rubric → lock at 准×3
or route back to S4 (regenerate) / outline (escalate).**

## Hard do / don't (earned lessons)
- **DO** run the static collision gate (`check_asset_collisions.py`) as Layer 1 of **every** run, before any
  reviewer call — "one visual dialect, never two" is enforced by the tool, not by prose.
- **DO** lock **only at 准×3**: Claude AND Gemini AND Codex pass the SAME round. A Codex-synth `approve` alone
  downgrades to `revise`. The generator family never self-acquits its own ref.
- **DO** treat `safety_ip < 3` from **any one** reviewer as an immediate hard `abandon_shot` — IP is a single-vote
  veto, no retries (the same shape as the anatomy single-vote veto).
- **DO** stop at MAX_REVIEW_ROUNDS=3 and escalate the asset **requirement** to outline/storyboard — the spec
  changes; the gate does not grind one image forever.
- **DON'T** zero a missing dim. A dim no reviewer scored is `not_scored` and **EXCLUDED** from the threshold —
  substituting 0 was the v1.0 bug that mis-rejected good refs.
- **DON'T** keep regenerating when rounds return **identical** scores on a *changed* file — that means the
  **judge** is broken (a by-design trait scored as drift). Audit the rubric, not the asset.
- **DON'T** leak reviewer prose into the Codex synth call — pass numeric scores + failure_modes + paths only;
  a prose leak ABORTS the gate (reviewer-independence).
- **DON'T** edit the asset's pixels here. On `regenerate`/`revise`, route a ≤140-char `repair_instruction` to
  `comic-asset-ref-generator`; this skill only verifies and locks.
- **DON'T** re-open a `locked` asset — the lock is a one-way door; a later need for a different ref is a NEW
  asset (new file, `supersedes` edge), not an edit of the locked one.

## Scope
| Target | Fit |
|---|---|
| reusable character sheet / location plate / prop cutout (identity-locked raster ref) | **excellent** |
| deterministic SVG/JSON asset source (one parametric builder per recurring motif) | **excellent** |
| text_panel / figure source whose downstream panels bake gateable literals | good (checks the literal contract) |
| logo-free symbol / mark (extra safety_ip weight) | good |
| a *composed* panel's faithfulness | no → that's `comic-director`'s `panel_gate` |
| cross-panel continuity (motif drift across the film) | no → that's `comic-continuity-audit` / the assembly_gate |

## Protocols (governance contracts this skill honors)
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — each reviewer reads the real asset file; the Codex synth gets **numeric scores + failure_modes + paths only**, never another reviewer's prose (a leak ABORTS).
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — the loop DRIVES (regenerate, re-fire R+1) but can't ACQUIT: the LOCK is a Type-B verdict that needs 准×3 (Gemini + Codex + Claude in the same round); Codex-synth-approve alone is downgraded; same-family N-of-Claude is never a jury.
- [`review-tracing`](../../protocols/review-tracing.md) — every Codex/Gemini reviewer call's full prompt+response is saved under `.aris/traces/comic-asset-review-loop/<date>_run<NN>/`, so each lock/abandon_shot verdict is auditable; the `ASSET_REVIEW.md` score_progression is the human-readable trail.
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Codex `gpt-5.5` `xhigh`; Gemini `auto-gemini-3` (never raw `gemini-3.1-pro`); `— reviewer: oracle-pro` routes the synth to `mcp__oracle__consult` (`gpt-5.5-pro`) on explicit request; never downgrade the tier.
