---
name: comic-blueprint-author
description: "Phase-1 (S7 of the comic-author suite) — turn ONE locked panel_spec into a deterministic content-SVG blueprint that becomes the codex image_gen condition, by WRITING A PYTHON GENERATOR (never raw SVG in chat — LLMs botch coordinates). The HEADLINE comic-pivot rule: the image bakes NO bubbles at all — draw only characters + scene + leave negative-space SAFE ZONES; HTML/CSS owns the entire bubble. Every panel gets a content_svg (a figure OR a layout blueprint); a baked figure-panel must declare expected_literals verbatim. Single-source collision check is mandatory. Gated by comic-cross-layer-gate --gate blueprint. Use when the storyboard is locked and you need each panel's deterministic generation condition; do NOT use to bake the panel (that is comic-director) or to write the verdict-stamp/curve assets (that is comic-asset-ref-generator)."
---

# comic-blueprint-author — one panel_spec → a deterministic content-SVG blueprint (S7)

The **per-panel condition author** of the [`comic-author`](../comic-author/SKILL.md) Phase-1 suite. It sits
between the storyboard ([`comic-storyboard-creator`](../comic-storyboard-creator/SKILL.md)) and the bake
([`comic-director`](../comic-director/SKILL.md)): for ONE locked `panel_spec` it produces ONE deterministic
`content_svg` — the answer-key composition image that the spiral feeds to `codex image_gen` as `-i` ref #1.
Unlike video, **the panel IS the deliverable** — there is no i2v start-frame residue, no motion, no temporal
chaining. The whole job is to LOCK what the panel must contain (numbers, layout, where the empty bubble
real-estate lives) so the image model has a precise composition to finalize and the `blueprint` gate has a
ground truth to diff against. You author this **by writing a Python generator script** — mirroring
[`examples/comic_m3_audit/gen/asset_lib.py`](../../examples/comic_m3_audit/gen/asset_lib.py) +
`gen_*_blueprints.py` — because hand-writing raw SVG coordinates in chat is exactly how LLMs botch a figure
(misplaced rects, off-canvas text, collisions). The script is the artifact; the SVG is its deterministic,
re-runnable output.

```text
  locked panel_spec ─▶ ⓪ PREFLIGHT  (assert refs status=locked + output_ref present; build input_refs; non-empty)
                            ▼
                       ① TEXT-MODE BIFURCATION  (baked → expected_literals verbatim · scene/no-numbers → html)
                            ▼
                       ② WRITE A PYTHON GENERATOR  (import only from asset_lib · palette pinned to ui_tokens)
                            │   draws characters+scene+figures · leaves negative-space SAFE ZONES · NO bubbles
                            ▼
                       ③ EMIT content_svg  + run check_asset_collisions.py (single-source, mandatory)
                            │   + zero-text assert for no-text panels (constellation etc.)
                            ▼
                       ④ WRITE the blueprint node  (content_svg, expected_literals, safe_zones, html_bubbles,
                            │   crop, negative_space_policy, generator_script, file_sha256)
                            ▼
                       ⑤a PRE-GATE FAN-OUT  (raster→PNG · CC render/lint ‖ Codex xhigh ‖ Gemini → write
                            │   review:* nodes + `reviews` edges → blueprint   ·never call the gate cold·)
                            ▼
                       ⑤b comic-cross-layer-gate <blueprint_id> --gate blueprint   (FUSES the reviews)
                            │   refs_present≥4 ∧ spatial_correctness≥4 ∧ blueprint_renders≥4 (+ text_preservation
                            │   if baked) → approve · safezone_quality<3 → fallback(→HTML) · MAX_REGEN=3
                            │   hard veto: image-bubble text · content_svg:null
                       verdict? ─ revise ─▶ ② (fix the generator, re-emit) ─ fallback ─▶ route text→HTML, re-emit
                            │   approve ─▶ gate flips status=locked
```

## Constants
- **AUTHORING MEDIUM = a Python generator script**, not raw SVG. One `gen_<panel>_blueprints.py` per panel (or
  per beat-group), importing the single-source builders from
  [`asset_lib.py`](../../examples/comic_m3_audit/gen/asset_lib.py). **Never** paste SVG coordinates into chat
  and never hand-edit the emitted `.svg` — re-run the script.
- **PALETTE PINNED** to `comic.json` `ui_tokens` (and the per-character hexes in `ART_BIBLE.md` §1 / §0.5),
  imported as constants from `asset_lib` (`VOID`, `BOARD`, `INK`, `GREEN`, `AMBER`, `RED`, …) **so the film
  never grows two visual dialects.**
- **THE IMAGE BAKES NO BUBBLES** — see the Headline rule below. The blueprint draws characters + scene +
  diegetic figures and leaves the bubble real-estate EMPTY (low-detail safe zones). `html_bubbles[]` live in
  the JSON view only.
- **NODE = `blueprint`** — read the upstream `panel_spec` node; write a `blueprint` node (`blueprint:<slug>`).
- **GATE = `comic-cross-layer-gate <blueprint_id> --gate blueprint`** — the SOLE gate authority; verdicts
  `{approve, revise, fallback}`, ADVANCE iff `refs_present ≥ 4 ∧ spatial_correctness ≥ 4 ∧ blueprint_renders ≥ 4`
  (+ `text_preservation ≥ 4` when baked text), `safezone_quality < 3 → fallback`, cap `MAX_BLUEPRINT_REGEN = 3`
  (see EXACT gate). The gate is a score-FUSER — you must FIRST fan out the reviewers (Claude render/lint ‖ Codex
  `gpt-5.5` `xhigh` ‖ Gemini `auto-gemini-3`) and write their `review:*` nodes + `reviews` edges (⑤a), never call
  it cold. The author never self-acquits.
- **SINGLE-SOURCE = mandatory** — `check_asset_collisions.py` must exit 0 (no filename written by >1
  generator) before the gate runs.
- **SCOPE** — one panel per invocation. You author the *condition*; you do NOT bake the frame (that's
  [`comic-director`](../comic-director/SKILL.md)) and you do NOT compose the final text prompt (that's
  [`comic-panel-prompt-builder`](../comic-panel-prompt-builder/SKILL.md)).

## Headline rule (the comic-pivot, COMIC_PIVOT_DESIGN §"two headline authoring rules")
> **The image generates NO bubbles at all — not even empty ones.** It draws only characters + scene + diegetic
> figures, and leaves negative-space **SAFE ZONES** where text will go. HTML/CSS owns the **entire** bubble
> (background + border + tail + text), auto-sizing to fluid bilingual text. The earlier "bake empty bubbles +
> overlay" plan was **rejected** — a dual system that drifts and produces garbled pseudo-glyphs (risk R2).

Concretely, in every blueprint you author:
- The generator draws **zero** speech bubbles, tails, captions, narration, headers, or labels-as-dialogue.
- It draws diegetic, in-world signage that **is the art** (a terminal `$ aris run …`, a wandb curve label, a
  `REJECT`/`ACCEPT` stamp, a DDL chip, a MacBook screen UI) — these are *figure literals*, not bubbles, and
  for a `baked` panel they go into `expected_literals` verbatim.
- It reserves the bubble real-estate as **low-detail negative space** (a soft gradient / empty desk surface /
  sparse sky band) and records those rectangles as `safe_zones[]` (normalized `{id,x,y,w,h}`, 0..1) so the
  `html` bubble layer has a clean budget to anchor into.
- **`text_mode:"html"` that bakes a bubble inside the SVG = HARD FAIL.** **`content_svg:null` = HARD FAIL.**

"If a human might edit / translate / reposition it, it's HTML; if it's a pixel object in the world, it's art."
(COMIC_PIVOT §3.5 TEXT SPLIT RULE.) Whole bubbles + captions + narration + headers → 100% HTML; only diegetic
signage may be baked.

## Two fail-closed engine contracts (author to these or the run is refused)
1. **Every panel needs a `condition.content_svg`** — a deterministic blueprint, *figure OR layout*. A
   dialogue/scene panel with no audited numbers still needs a **layout blueprint** (the scene composition with
   the safe zones drawn as low-detail regions). Never `content_svg:null`; the engine rejects it.
2. **A `baked` figure-panel MUST declare `condition.expected_literals`** — the exact numbers/keys baked into
   the figure, **verbatim, ASCII-tokenizable** (`["REJECT","+6.2","T-16:05"]`). These are what the gate's
   blind reviewers transcribe and a token-diff checks. A scene panel with **no** audited numbers →
   `text_mode:"html"` with `expected_literals:[]`. (Decorative non-ASCII like a `✓` is **out of contract** —
   gate only the ASCII tokens; e.g. S20 gates `"SUBMITTED"`, the `✓` is decorative.)

## Procedure (an agent can execute this step by step)

### ⓪ Preflight — resolve the panel + assert its refs are locked
1. Load the upstream `panel_spec` node (`node_type=="panel_spec"`); read `panel_id`, `page_id`, `world`,
   `text_mode`, `expected_literals`, `content_blueprint` (the storyboard's blueprint *plan*: which asset to
   instantiate + the literals layout), `asset_ids[]`, `bubbles`, `side_narration`, `motifs`.
2. Build `input_refs = dedup([scene] + characters[] + props[] + text_refs[])` from `asset_ids[]`; **assert
   non-empty** ("must reference ≥1 scene/character"). For each ref load its `asset` node and **HARD-FAIL if
   `status != locked` or `output_ref` (file_path/data_url) is missing** — a blueprint may only compose
   *locked, immutable* assets (ported from frame-condition-builder Phase 0; refs are never mutated). The
   `identity_ref` (the canonical duo/trio sheet) is the identity authority and is **always** present, never
   dropped.
3. Read `ART_BIBLE.md` (§0.5 two-world warm/dark palette, §1 per-character hex iron-law, §6.5 density target)
   and `comic.json` `ui_tokens` — these define the palette your generator imports and the rubric the gate
   scores against. The bible is the convergence target; without it the gate emits "style drift" forever.

### ① Text-mode bifurcation — decide what the gate will check
4. If the panel carries audited numbers/keys baked as diegetic figure literals → **`text_mode:"baked"`**;
   populate `expected_literals` **verbatim** from the storyboard's `content_blueprint` (the salient *large*
   tokens only — the blind-transcribe threshold). A concrete authoring trick ported from
   frame-condition-builder: extract the text-whitelist by matching `content_blueprint` keys
   (`"text:"`, `"label:"`, `"title:"`, quoted strings) into the explicit literal list.
5. If the panel is a pure scene / dialogue beat with **no** audited numbers → **`text_mode:"html"`**,
   `expected_literals:[]`; the generator draws scene + characters + safe zones only.
6. **Sub-threshold exclusions are explicit:** a literal that is sized below the blind-transcribe threshold
   (e.g. the S09 `Tok|yo` chip at ≤1.5% frame height, "foreshadow, not gated") is drawn but is **NOT** in
   `expected_literals`. Skill-name tags (`novelty-check`, `experiment-bridge`, …) **never** appear in-frame
   (the 铁律) — they live only in side-narration metadata.

### ② Write the Python generator (the load-bearing step)
7. Create / extend `gen_<panel>_blueprints.py` next to `asset_lib.py`. Import **only** from `asset_lib`
   (single source per recurring token) + the pinned palette constants. Define the local `w(name, content)`
   emitter (`open(.../assets/name,"w").write(content); print("wrote", name)`) — exactly the
   [`gen_b06_blueprints.py`](../../examples/comic_m3_audit/gen/gen_b06_blueprints.py) shape.
8. Build the panel body as a Python list `o = [...]` of element strings (rects, text, paths, imported
   builders like `ddl_chip(...)`, `stamp(...)`, `curve_panel(...)`, `tokyo_chip(...)`, `verdict_card(...)`).
   Compute coordinates **in code** (loops, fractions of `W`/`H`) so they are deterministic and reproducible —
   never eyeball pixel positions. Wrap with `svg_doc(W, H, "".join(o))`.
9. **Draw NO bubbles** (Headline rule). Draw the diegetic figure(s) carrying the `expected_literals`. Reserve
   the bubble real-estate as low-detail negative space and note the rectangles for `safe_zones`.
10. **Reuse the canonical builder** for any cross-panel motif (mirror-pair verdict cards, the one star-map
    coordinate source, the DDL chip family) — do not re-implement it locally; that is what would split the
    visual dialect. (E.g. S11 `REJECT` and S16 `ACCEPT` BOTH call `verdict_card(...)` so they are a precise
    geometric mirror; S16b labeled star-map and S22 wordless constellation BOTH derive from
    `STARMAP_NODES` — "禁目测 / no eyeballing".)
11. Run the generator. Inspect the emitted `.svg` (and, if rasterizing to PNG to eyeball, do it via headless
    Chrome — never re-hand-edit the SVG; fix the *script*).

### ③ Single-source + zero-text gates (deterministic, pre-gate)
12. **MANDATORY: run `check_asset_collisions.py`** — it statically scans every `gen_*.py` for `w("…")` writes
    and fails if any output filename has >1 owner. Must exit 0 (`✓ no asset collisions — all N generator
    outputs are single-source`). If a specialized generator now owns a richer version of a shared asset,
    **delete the dead duplicate** (the inline ownership-transfer discipline) rather than letting two writers
    race (run-order corruption — "skip if file exists" is explicitly rejected because it hides the bug).
13. For a **no-text** panel (constellation, wordless geometric twin) add a build-time assert in the emitter:
    `assert "<text" not in svg, "constellation must contain ZERO text"` — the S22 zero-text contract. (Also
    forbid re-layout-by-eye on shared coordinate JSON via a `_contract` field.)

### ④ Write the `blueprint` node
14. Write a `blueprint` node (`node_id: blueprint:<slug>`, `status: under_review`). Payload **must** carry the
    9 required fields (`schemas/node_schema.json` → `blueprint`):
    `source_panel_id` · `content_svg` (relative path to the emitted SVG) · `expected_literals` (verbatim;
    `[]` for html) · `safe_zones[]` (`{id,x,y,w,h}` 0..1) · `html_bubbles[]` (the JSON-view bubbles, anchored
    to a named safe-zone, each with `text{zh,en}` — these are **NOT** baked) · `crop` (`shape ∈
    {hero16x9|wide|tall|square}` + window) · `negative_space_policy` (where the empty bubble real-estate is
    and why it is low-detail) · `generator_script` (the `gen_*.py` path — provenance, so the SVG is
    reproducible) · `file_sha256` (of the emitted SVG). Add edges (`type` ∈ `cli/validate_wiki.py` EDGE_TYPES):
    `derived_from` (`blueprint:<slug>` → `panel:<slug>`, the panel_spec node's real id; `source_panel_id` payload = that same `panel:<slug>`) and one `uses_asset` (`blueprint:<slug>` →
    `asset:<id>`) per locked asset ref. (`composes_from` is NOT a legal edge type — it is a video-era leftover
    that survives only in `docs/history/legacy-video-arch.md`; the live author-layer asset-composition verb is
    `uses_asset`. Writing `composes_from` makes `python3 cli/validate_wiki.py` exit 1.)
15. Mirror the authored condition into `comic.json` under `panels.<id>.condition`: `content_svg`,
    `expected_literals`, `world`, `identity_ref`, `identity_desc` (the §1 hex iron-law restated),
    `characters`, `scene` (the §0.5 / §6.5 rubric restated per panel) — and `panels.<id>.safe_zones[]` +
    `panels.<id>.text_mode`. (See the worked `condition` blocks in
    [`examples/comic_m3_audit/comic.json`](../../examples/comic_m3_audit/comic.json), e.g. S01, S02, S08, S22.)

### ⑤a Pre-gate fan-out — raster + reviewers + `review` nodes (NEVER call the gate cold)
`comic-cross-layer-gate` is a **score-FUSER**: it reads pre-existing `review:*` nodes via `reviews` edges and
**HARD-FAILS if zero reviews are attached** (`no reviews — gate is a score-fuser, not a reviewer`). So you must
fan out the reviewers and persist them FIRST — the gate collects, it does not run them:
15a. **Rasterize the emitted SVG to a non-empty PNG** via headless Chrome (this also pre-confirms the
    `blueprint_renders` RAW check). Run the deterministic pre-gate checks once more: `check_asset_collisions.py`
    exit 0; zero-text assert for no-text panels.
15b. **Fan out the independent reviewers** on the blueprint dims (`refs_present`, `spatial_correctness`,
    `blueprint_renders`, `text_preservation` [only when baked text], `safezone_quality`), file paths only,
    behind an `=== EXTERNAL CONTEXT (advisory) ===` fence, NEVER the author's `expected_literals` list:
    **Claude render/lint ‖ Codex `gpt-5.5` `xhigh` ‖ Gemini `auto-gemini-3`**
    ([`reviewer-routing`](../../protocols/reviewer-routing.md)).
15c. **Write one `review` node per reviewer** (`node_id: review:<slug>`, `node_type:"review"`). Payload **must**
    carry the 3 required fields from `cli/validate_wiki.py` `PAYLOAD_REQUIRED["review"]` — `target_node_id`
    (the `blueprint:<slug>`), `reviewer`, `gate_kind:"blueprint"` — plus `review_scores:{dim:score,...}` (the
    per-dim numbers the fuser reads). Append a **`reviews` edge `review:<slug>` → `blueprint:<slug>`** (the
    direction the gate walks — NOT `reviewed_by`, which points the other way and the fuser would miss).

### ⑤b Cross-layer gate (fuse + adjudicate)
16. **Only now** run `comic-cross-layer-gate <blueprint_id> --gate blueprint`. It fuses the `review:*` scores
    (min per dim), runs the Codex adjudicator on scores + paths + a verbatim slice + the verbatim rubric, and
    emits `VERDICT=<v> GATE=blueprint TARGET=<id>`. Route on the gate's THREE real verdicts:
    - **`approve`** → the gate flips the `blueprint` node to `status: locked` (the cross-layer hand-off token).
    - **`revise`** → **edit the generator script** and re-emit (never hand-patch the SVG), redo ⑤a (new
      reviews), re-gate. Counts against `MAX_BLUEPRINT_REGEN = 3`; on the cap, escalate to **rewrite the
      `panel_spec`** (the gate's own escalation target), not infinite regen.
    - **`fallback`** (`safezone_quality < 3`, floor otherwise passing) → a **route switch, NOT a regen**: set
      the panel `text_mode:"html"`, `expected_literals:[]`, drop any whitelisted baked text, re-emit the
      layout-blueprint with clean safe zones, then redo ⑤a and re-gate.
    - **Hard veto** (image-bubble text / `content_svg:null`, computed in the gate's ⓪ pre-check) → the run is
      refused; remove the baked bubble or supply a real blueprint, then redo ⑤a.
    Escalate to human after repeated same-root failure (acceptance-gate: the loop can drive but cannot acquit).

## EXACT gate (`--gate blueprint`) — the BINDING contract is owned by comic-cross-layer-gate
The single source of truth for `--gate blueprint` is
[`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) (§`--gate blueprint`). This skill MUST NOT invent
a parallel rubric — it quotes the gate's real contract verbatim and routes on the gate's real verdicts.

**Verdicts: `{approve, revise, fallback}`** (the IMAGE analog of aris_movie's `frame_condition` gate; the
motion dims are dropped). The gate is a score-FUSER over `reviews`-edge `review:*` nodes (see ⑤a below); it does
not re-run reviewers.

**The 5 real dims (0–5 scale) and the ADVANCE logic (mirror comic-cross-layer-gate exactly):**
- **`refs_present` ≥ 4** — every composed ref resolves and was `status: locked`.
- **`spatial_correctness` ≥ 4** — subject / eyeline / figure / safe-zone geometry is laid out correctly (the
  composition is buildable, nothing cramped or colliding, reading order sane).
- **`blueprint_renders` ≥ 4** — the SVG rasterizes to a non-empty PNG (a RAW pre-check the gate computes, not a
  vote).
- **`text_preservation`** — required **ONLY** when the panel has whitelisted **baked** text; for an `html`
  panel it is N/A (`null`). When present: each `expected_literal` is drawn verbatim and ASCII-tokenizable.
- **`safezone_quality`** (html panels) — a clean low-detail region exists where each `html` bubble anchors.

**ADVANCE (`approve`) iff `refs_present ≥ 4` AND `spatial_correctness ≥ 4` AND `blueprint_renders ≥ 4`** (with
`text_preservation ≥ 4` additionally required when baked text is whitelisted). The advance rule is ASYMMETRIC —
those three (plus conditional `text_preservation`) gate; the rest ride into the audit.

**`fallback` verdict:** `safezone_quality < 3` while the floor otherwise passes ⇒ **`fallback`** = route the
panel's text to the **HTML overlay** (a route switch, **NOT** a regen): set the panel `text_mode:"html"`,
`expected_literals:[]`, drop any whitelisted baked text, and re-emit the layout-blueprint with clean safe zones.
Handle this in step ⑤ — do not treat `fallback` as a hard veto or as a normal regen.

**Cap:** `MAX_BLUEPRINT_REGEN = 3` regenerations → escalate to **rewrite the `panel_spec`** (not infinite regen).

**Structural hard vetoes the gate's ⓪ pre-check computes (RAW, not a vote — any one → `revise`/refuse):**
- **Any image-bubble text in the blueprint** — a speech bubble / tail / caption / narration / dialogue-label
  drawn into the SVG (`text_mode:"html"` with a baked bubble is the canonical violation). The image bakes NO
  bubbles.
- **`content_svg:null`** (or missing) — every panel must have a blueprint.
- A `baked` panel with empty/absent `expected_literals`; a stray non-diegetic glyph in a declared no-text panel
  (constellation must be zero-text).

**(Advisory, NON-binding) what each real dim is checking on this static condition** — this is explanatory prose,
not a separate rubric; the binding floors are the 5 dims above:
- *content_authority* → folded into `spatial_correctness` + (baked) `text_preservation`: the blueprint pins the
  diegetic figure(s), composition/camera/layout, and every `expected_literal` verbatim.
- *literal_contract* → `text_preservation`: `baked` ⇒ non-empty ASCII literals matching drawn figure literals;
  `html` ⇒ `expected_literals:[]` and no audited numbers drawn.
- *negative_space_overlay_safety* → `safezone_quality`: `safe_zones[]` present, non-overlapping, over genuinely
  low-detail pixels (not over a face / busy figure).
- *layout_readability* → `spatial_correctness`: one-glance legibility; no motion to clarify a static panel.
- *deterministic_asset_integrity* → `refs_present` + the deterministic pre-gate `check_asset_collisions.py`:
  every recurring motif renders from its single canonical `asset_lib` builder (mirror-pairs identical, star-map
  from one coordinate source).
- *style_bible_alignment* → rides into the audit (scored against `ART_BIBLE.md` §0.5 / §1 / §6.5, not a vibe):
  palette pinned to `ui_tokens`; warm/dark split is **by-design, not drift** — only a *mis-colored* world flags.

**Reviewers (cross-model, independent) — the upstream fan-out in ⑤a, NOT the gate itself:** Claude render/lint
(does the SVG render? do the literals appear? are safe zones over low-detail pixels? any baked bubble?) ‖ Gemini
visual (`auto-gemini-3`) ‖ Codex `gpt-5.5` `xhigh`. Each writes a `review:*` node; the gate COLLECTS them via
`reviews` edges and hard-fails if none exist. The author (this agent) never self-acquits; ACCEPT needs the
deterministic checks clean **and** the fused cross-model verdict to advance.

## Node read / written (per `schemas/node_schema.json`)
- **Reads:** the upstream `panel_spec` node (`node_type:"panel_spec"`) — required payload incl.
  `source_storyboard_id, page_id, panel_id, sequence_index, page_type, world, asset_ids, text_mode,
  expected_literals, content_blueprint, bubbles, side_narration, motifs`; plus each referenced `asset` node
  (must be `status:locked`, `output_ref` present) and the `motif_ledger` / `continuity_constraint` nodes that
  pin this panel's required values.
- **Writes:** ONE `blueprint` node (`node_id: blueprint:<slug>`, `node_type:"blueprint"`,
  `status: under_review → locked`). **Required payload (9 fields, verbatim from `cli/validate_wiki.py`
  `PAYLOAD_REQUIRED["blueprint"]`):** `source_panel_id`, `content_svg`, `expected_literals`, `safe_zones`,
  `html_bubbles`, `crop`, `negative_space_policy`, `generator_script`, `file_sha256`. **Edges (every `type`
  ∈ `validate_wiki.py` EDGE_TYPES):** `derived_from` (`blueprint:<slug>` → `panel:<slug>`, the panel_spec node's real id; `source_panel_id` payload = that same `panel:<slug>`); one `uses_asset`
  (`blueprint:<slug>` → `asset:<id>`) per locked `asset`. (On regenerate: mark the prior blueprint
  `status: superseded` and add a `supersedes` edge (new `blueprint:<slug>` → prior `blueprint:<slug>`); record
  the reason into a `failure_mode` node and add a `failure_of` edge (`fail:<slug>` → the prior `blueprint:<slug>`)
  — the positive-invariant memory. `composes_from` and `repairs_failure_mode` are NOT legal edge types and will
  fail `validate_wiki.py`; `uses_asset` / `supersedes` / `failure_of` are their real-vocabulary replacements.)

## Worked example
Ground every blueprint in the real ARIS-Movie-Director comic
([`examples/comic_m3_audit/`](../../examples/comic_m3_audit/)) — copy these exact patterns:

- **The single-source builder library** —
  [`gen/asset_lib.py`](../../examples/comic_m3_audit/gen/asset_lib.py). ONE parameterized function per
  recurring token, palette pinned at the top as module constants:
  ```python
  MONO = "JetBrains Mono, Menlo, monospace"
  RED = "#FF3366"; AMBER = "#FFB000"; GREEN = "#00C896"; VOID = "#0A0E27"; INK = "#E4E9F7"; ...
  def ddl_chip(x, y, t, state="amber", skin="corner", ...): ...   # the SINGLE timeline authority
  def stamp(x, y, label, scale=1.0, tilt=0): ...                  # geometry matches the baked S15 stamp
  def verdict_card(x, y, header, body_rows, stamp_label, ...): ...# S11 REJECT & S16 ACCEPT = SAME card (mirror)
  def tokyo_chip(x, y, scale=1.0, repaired=False): ...            # one source, multi-scale
  STARMAP_NODES = [...]                                           # ONE coord truth for S16b + S22
  ```
  Cross-panel reuse contracts live in the docstrings ("S11 REJECT ↔ S16 ACCEPT = same card mirror pair";
  "star-map JSON is the one truth source for S16b + S22"). **Copy this:** never re-implement a motif locally —
  import the builder so the film keeps one visual dialect.

- **A per-panel blueprint generator** —
  [`gen/gen_b06_blueprints.py`](../../examples/comic_m3_audit/gen/gen_b06_blueprints.py). The exact shape to
  mirror: `sys.path.insert(0, …)` → `from asset_lib import (svg_doc, text, rect, ddl_chip, tokyo_chip, …)` →
  a local `w(name, content)` emitter → build `o = [...]` with coordinates computed in code (the GPU grid is a
  `for i in range(8)` loop over `col,row`), call imported builders for the shared chips, `w("…_v1.svg",
  svg_doc(W, H, "".join(o)))`. Note the **deterministic seed** for the log-wall (`_r.seed(7)`) and the
  **sub-gate** `Tok|yo` micro chip drawn at `scale=0.27` with **no callout, no arrow** — it is the foreshadow,
  deliberately below the transcription threshold, so it is **NOT** in `expected_literals`.

- **The mandatory single-source gate** —
  [`gen/check_asset_collisions.py`](../../examples/comic_m3_audit/gen/check_asset_collisions.py). Regex
  `\bw\(\s*["']([^"']+\.(?:svg|json|png))["']` over every `gen_*.py`; exit 1 if any filename has >1 writer.
  Verified clean on the real comic: **26 outputs, all single-source.** Run this before the gate, every time.

- **The blueprint → gate join in the IR** —
  [`comic.json`](../../examples/comic_m3_audit/comic.json). The `panels.<id>.condition` block is the contract
  surface this skill writes. Two canonical shapes to copy:
  - **`baked` figure-panel** (S08, line ~519): `"content_svg": "assets/handoff_terminal_v1.svg"`,
    `"expected_literals": ["T-24:00:00","ARIS ONLINE","$ aris run"]`, `world`, `identity_desc` (§1 hex
    iron-law restated), `characters`, `scene` (§0.5 seam + §6.5 density restated). The bubbles
    (`这一轮交给 ARIS 了` / `交给我！` / `我盯着。`) are NOT in the condition — they are `html_bubbles`.
  - **`html` no-text panel** (S22 constellation, line ~752): `"content_svg":
    "assets/constellation_layout_v1.svg"`, `"expected_literals": []`, `"characters": "NONE. No characters, no
    figures, no text anywhere in the image"`, plus a `safe_zones` band for the HTML tagline. The blueprint
    bakes zero glyphs (build-time `assert "<text" not in svg`).

## Hard do / don't (earned lessons)
- **DO** author every blueprint by **writing a Python generator** that imports from `asset_lib` — LLMs botch
  raw SVG coordinates; the script is deterministic and re-runnable, the SVG is its output.
- **DO** draw **NO bubbles** in the image — only characters + scene + diegetic figures + low-detail safe
  zones. HTML/CSS owns the entire bubble. (`text_mode:"html"` with a baked bubble = hard fail.)
- **DO** give every panel a `content_svg` (figure OR layout). Never `content_svg:null`.
- **DO** declare `expected_literals` **verbatim, ASCII-tokenizable** for every `baked` figure-panel; a scene
  with no audited numbers → `text_mode:"html"` with `[]`.
- **DO** run `check_asset_collisions.py` (exit 0) before the gate — single canonical owner per token; delete
  dead duplicates rather than letting two generators race.
- **DO** reuse the one canonical builder for every cross-panel motif (mirror-pair cards, the single star-map
  coordinate source) — that is the only defence against discrete style scatter (risk R13).
- **DON'T** hand-edit the emitted `.svg` to "fix" a coordinate — fix the *generator script* and re-emit; a
  hand-patched SVG is no longer reproducible from its `generator_script`.
- **DON'T** bake skill-name tags, sub-threshold chips, or decorative `✓` into `expected_literals` (only the
  salient large ASCII tokens are gated; skill names never appear in-frame at all).
- **DON'T** flag the warm/dark world split as drift — it is by-design (§0.5); only a *mis-colored* world is a
  violation (design-aware gate).
- **DON'T** compose an unlocked / mutated asset ref — a blueprint may only compose `status=locked` assets, and
  never mutates an asset node.
- **DON'T** self-acquit — the blueprint gate is cross-model (CC ‖ Gemini ‖ Codex); the author drives the loop
  but cannot ACCEPT its own blueprint.

## Protocols (governance contracts this skill honors)
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — the upstream pre-gate reviewers (⑤a:
  Claude ‖ Codex ‖ Gemini, whose `review:*` nodes the gate later fuses) get the SVG / PNG + an
  `=== EXTERNAL CONTEXT (advisory) ===` fence and blind-transcribe the literals; they never see the author's
  `expected_literals` list. The gate fuses scores + paths only — never reviewer prose.
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — the loop can DRIVE but can't ACQUIT: a `locked`
  blueprint needs the deterministic checks clean (collision-free, literals coherent, zero-text where required)
  **and** the cross-model panel to pass; the author never self-acquits.
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — the agent that authors a blueprint does not
  judge its own blueprint's correctness; numbers are *originated by the storyboard and verified* by the blind
  diff, never invented at blueprint time.
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — Codex `gpt-5.5` `xhigh`; Gemini `auto-gemini-3`;
  never downgrade the reviewer tier.
