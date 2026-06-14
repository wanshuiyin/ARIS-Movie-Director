---
name: comic-panel-prompt-builder
description: "Phase-1 step of comic-author — the DETERMINISTIC compiler (搬运工原則) that turns ONE gate-approved panel_spec + its status:locked blueprint into the EXACT fixed-section bake string for the spiral engine via the shipped scripts/build_prompt.py (+ the canonical scripts/_validate.py vetoes). No Codex call in the happy path; it only emits, the engine bakes. Composes style_prefix + condition_string, injects the active failure_mode repair note on retry, and hard-REJECTS banned vocab (camera/lens/lighting/quality padding). Routes html_bubbles[] to the JSON viewer overlay, NEVER into the bake string (no baked bubbles unless the panel is text_mode:baked). Refuses unless the upstream blueprint is status==locked (the cross-layer gate's hand-off token) and every ref is a REAL locked asset path. Use when a panel_spec is locked and you need its prompt_bundle, just before comic-director's panel_gate."
argument-hint: [panel_id | panel_spec.json] [--retry --reason "<text>"]
allowed-tools: Bash(python3:*), Read, Write, Edit, Grep, Glob
---

# comic-panel-prompt-builder — the Deterministic Bake Compiler (搬运工原則)

The **last authoring step before a pixel ever gets baked**. Given ONE upstream-approved `panel_spec` and its
`status: locked` `blueprint`, this skill COMPILES — it does not brainstorm — the *exact* message
[`comic-director`](../comic-director/SKILL.md) (Phase 2/3) will hand to `codex image_gen`, plus the locked
identity-ref list. It is the comic twin of the framework's `shot-prompt-builder`: a pure Layer-3 transform
with **no Codex call in the happy path** — it only emits a `prompt_bundle`; the spiral engine submits it.
Everything the generation backend ever sees passes through here, so this is where the **搬运工原則** is
enforced at emit time: the backend (Codex/gpt-image-2) owns optics; `ART_BIBLE.md` owns style; **no camera /
lens / lighting / "8K hyperrealistic cinematic" padding leaks into the bake**, and **no bubble text gets
baked** unless the panel is explicitly `text_mode: "baked"`. The author (storyboard/blueprint layers) decides
*what*; this skill decides *nothing* — it transcribes a locked spec into a backend-legal string and FAILS
(it never papers over) when the spec is malformed.

```text
  panel_spec (status:locked) ─▶ ① RESOLVE  — load panel_spec + its blueprint + ART_BIBLE style_prefix
        + blueprint (status:locked)    enforce 4 prerequisites (node_type, blueprint status:locked, REAL refs, style_prefix resolves)
                              ▼
                        ② COMPOSE  — fixed-section condition_string (order is load-bearing, do NOT refactor)
                              ▼   style_prefix + [BAKED DIALOGUE only if text_mode==baked] + SCENE + FIXED ELEMENTS
                              ▼   + ALLOWED CHANGE vs prior panel + FORBIDDEN + SCREEN-TEXT WHITELIST(expected_literals)
                              ▼
                        ②·5 INJECT (retry only) — active failure_mode positive-invariants to the FRONT
                              ▼
                        ③ VALIDATE  — banned-vocab + length + no-baked-bubbles + real-refs on the COMPOSED string
                              ▼          (the hard gate — ANY hit = fail-closed, push the fix UPSTREAM)
                              ▼
                        ④ EMIT  — write the prompt_bundle node; route html_bubbles[] to the JSON viewer ONLY
                              ▼
                   pass? ─ no ─▶ exit 4 (banned/length) | exit 7 (failure_mode trigger still fires) | exit 3 (prereq)
                              │ yes
                              ▼
                        ⑤ stdout one-line JSON {prompt_bundle_id, panel_id, source_blueprint_id}
```

## Role
You are a **fail-closed transcriber**, not an author. You take a `panel_spec` that an upstream layer already
gate-approved and its `blueprint` that the cross-layer gate already flipped to `status: locked`, and you
produce the single exact `composed_prompt` (style_prefix + a fixed-section condition string) + the locked
identity-ref paths that the spiral engine will bake — together with the deterministic proof (a clean
`banned_vocab_scan`) that the message is backend-legal. You **never** invent a scene element, a number, a cast
member, or a style adjective; you **never** silently fix a malformed spec (you FAIL and point upstream); and
you **never** call Codex on the happy path (a Codex call only ever appears as a reported upstream bug). The
cross-model *judgement* of the baked pixels is not yours — that lives downstream in `comic-director`'s
`panel_gate`; keeping you deterministic is what stops the executor from self-acquitting.

## Node — what this skill reads / writes (`schemas/node_schema.json`)
- **Reads `panel_spec`** (node prefix `panel:`) — payload fields used: `source_storyboard_id`, `page_id`,
  `panel_id`, `sequence_index`, `page_type`, `world`, `asset_ids[]`, `text_mode`, `expected_literals[]`,
  `content_blueprint`, `bubbles[]`, `side_narration`, `motifs`. The `panel_spec` must be its layer's
  gate-approved output (`status: locked`), not a draft.
- **Reads the upstream `blueprint`** (node prefix `blueprint:`, found via the panel's `content_blueprint`) —
  payload fields used (the schema's 9 `blueprint` required fields, verbatim from `validate_wiki.py`
  PAYLOAD_REQUIRED): `source_panel_id`, `content_svg`, `expected_literals[]`, `safe_zones[]`,
  **`html_bubbles[]`**, `crop`, `negative_space_policy`, `generator_script`, `file_sha256`. **Refuse unless
  the blueprint is `status: locked`** — that is the schema signal that the cross-layer gate signed off (the
  gate's ⑥ FLIP writes `status → locked` on advance; `comic-blueprint-author` emits blueprints at
  `status: locked`). The `blueprint` node has **NO `review_status` field** (only the `asset` node does, and
  `"approved"` is not even a legal `status` enum value) — never gate on `review_status` here. `html_bubbles[]`
  is the JSON viewer-overlay payload — it is **routed to the viewer, NEVER concatenated into the bake string**.
- **Writes one `prompt_bundle`** (node prefix `prompt:`, node_id a lowercase `[a-z0-9_-]+` slug of the
  `panel_id`) — payload required by the schema (the 6 `prompt_bundle` PAYLOAD_REQUIRED fields, verbatim):
  `source_panel_id`, `source_blueprint_id`, `style_prefix`, `composed_prompt`, `banned_vocab_scan`,
  `identity_ref_paths`. Status canon: author `draft`/`pending` → `under_review` → **`locked`** on a clean
  validate (or `rejected`). Write **LEGAL** edges (every `type` ∈ `validate_wiki.py` EDGE_TYPES):
  `derived_from` (prompt_bundle → panel_spec) and `uses_blueprint` (prompt_bundle → blueprint). On retry, the
  failure_mode trace uses a **legal `derived_from`** edge (prompt_bundle → failure_mode, with
  `evidence.consulted_failure_mode` + score); if a trigger still fires after repair, a legal **`failure_of`**
  edge (failure_mode → prompt_bundle — `failure_of` points failure_mode → target, matching the gate + the script,
  trigger in `evidence`). There is **NO `generated_from` /
  `consulted_failure_mode` / `violates_failure_mode` edge type** in EDGE_TYPES — those would fail the release
  gate. Emit **node IDs only** to stdout — the orchestrator re-reads the node file from disk (no filename guessing).

## Two engine contracts to compile to (fail-closed)
These are the same two contracts `comic-author` authors to — this skill is where they are *enforced at emit
time*, on the resolved spec, before any credit is spent:
1. **Every panel needs a content_svg.** On the wiki node this is **`blueprint.payload.content_svg`** (top-level
   on the blueprint payload — NOT nested under any `condition.` key; the `condition.content_svg` prefix exists
   ONLY in the runtime `comic.json` the engine reads). The blueprint's `content_svg` is the content authority +
   the bake's layout reference. If it is `null` / missing / not on disk (or its `file_sha256` mismatches) →
   **refuse** (exit 3). A scene-only panel still has a *layout* blueprint SVG; there is no such thing as a
   panel with no `content_svg`.
2. **A `baked` figure-panel must declare non-empty, ascii-tokenizable `expected_literals`.** If
   `text_mode == "baked"` and the blueprint carries a figure but `expected_literals` is empty → **refuse**
   (exit 3). Those literals become the **SCREEN-TEXT WHITELIST** block (below) and are exactly what
   `panel_gate`'s blind token-diff later verifies. A scene panel with no audited numbers must be
   `text_mode: "html"` (dialogue is an HTML overlay, no baked-literal contract).

## Procedure (numbered — an agent can execute this step by step)
**The shipped entrypoint (do NOT hand-roll the validator):**
```bash
python3 skills/comic-panel-prompt-builder/scripts/build_prompt.py <project_dir> <panel_id|panel:slug> \
    [--retry --reason "<text>"]
```
`scripts/build_prompt.py` IS this procedure made executable — it reads the `panel_spec` + `blueprint` nodes
from `<project_dir>/wiki/nodes/`, resolves the identity lock + refs, composes the fixed-section message, and
calls the **single canonical** `scripts/_validate.py` (which owns `MAX_MESSAGE_CHARS = 4000`, the ~80-pattern
`BANNED_VOCAB`, `no_baked_bubbles`, `real_refs` — imported, never duplicated). It writes the trace files
`wiki/prompt_build/<panel_slug>/{_resolved.json,_meta.json,_validation.json}` and, on a clean validate, the
`prompt_bundle` node + its legal edges. `--retry` **REQUIRES** `--reason` (exit 2 otherwise) — a retry must
name the active failure it is repairing. Run `python3 scripts/_validate.py --composed <f> --text-mode <m>
--bubbles ... --refs ...` standalone for a quick re-check of an already-composed message.

0. **Phase −1 · parse + scaffold.** Parse `$2` (the `panel_id` or `panel:slug` node_id); make
   `wiki/prompt_build/<panel_slug>/`. `--retry` without `--reason` → **exit 2**. The emitted node_id is
   `prompt:<lowercase-slug-of-panel_id>` (the schema `node_id` pattern is `[a-z0-9_-]+`; the display
   `panel_id` may carry case). Never guess output filenames.
1. **Phase 0 · resolve + prerequisites (refuse to proceed unless ALL hold).** Load into one
   `_resolved.json`: the `panel_spec` node; its `blueprint` node (via `panel_spec.payload.content_blueprint`);
   and the `style_prefix` from `ART_BIBLE.md` (the world-keyed `STYLE_PREFIX[<world>]:` line — §0 register +
   §0.5 two-world palette). Enforce:
   - (a) `node_type == "panel_spec"` and `status == "locked"` — else **exit 2** (input missing/malformed).
   - (b) the upstream **`blueprint.status == "locked"`** — the schema signal that the cross-layer gate signed
     off (the gate's ⑥ FLIP writes `status → locked`). The `blueprint` node has **no `review_status` field**;
     gating on `review_status == "approved"` is unreachable (not even a legal `status` value) → never do it.
     Optionally also assert the legal `decision` node / `decides` edge for this blueprint exists as gate proof.
     Else **exit 3**.
   - (c) **every ref is a REAL locked asset path**, not a placeholder: `blueprint.payload.content_svg` exists on
     disk (and `file_sha256` matches), and each identity ref — resolved by following
     `panel_spec.payload.asset_ids[]` to its identity-sheet `asset` node (the asset must be `status: locked`,
     and publishes a real `.png` via its `ref_requirements`) — is a real `.png` (NOT `pending:*`, NOT `null`
     where one is required). A `null` ref is allowed ONLY as the documented "use project canonical" fallback;
     an unresolved `pending:*` → **exit 3**.
   - (d) the `style_prefix` resolves and is sane: ≤ 200 chars (hard), ≤ 32 words (warn). Else **exit 3**.
   Also resolve asset **names** (scene/prop/identity `asset_ids[]` → display names) for the whitelist/reviewer
   context only — names go in the whitelist, raw IDs never go in the prompt.
2. **Phase 1 · compose the condition string DETERMINISTICALLY in this EXACT load-bearing layout** (order is
   load-bearing — it empirically drives baked-text fidelity; do NOT refactor headings or order without an A/B
   test). Front = strongest conditioning weight.
   - **STYLE PREFIX** — from `ART_BIBLE.md`: tone + two-world palette + texture, world-keyed by
     `panel_spec.world` (e.g. `warm` / `seam` / `dark-cyber` / `starfield`). **NO camera/lens/lighting/quality
     vocab.**
   - **[BAKED DIALOGUE]** — **only if `text_mode == "baked"`** lift the panel's `bubbles[]` text into the
     prompt (so the image model draws legible balloons). **If `text_mode == "html"` (or `code`): SKIP this
     block entirely** — the bubbles are the viewer's job (see Phase 4). This is the single switch that decides
     baked-vs-overlay text.
   - **SCENE COMPOSITION NARRATIVE** — the scene staging authority is the **`blueprint.payload.content_svg`**
     layout (the content blueprint already lays out the scene) summarized with the panel's
     `panel_spec.payload.side_narration`. **There is NO `condition.scene` / `condition.characters` /
     `chibi_action` on the panel_spec node** — those keys live ONLY in the runtime `comic.json` (do not read
     them off the node). The world's warm/cold contrast is *by design*, not drift.
   - **"FIXED ELEMENTS (must NOT change):"** — the identity lock, obtained by following
     `panel_spec.payload.asset_ids[]` to each identity-sheet `asset` node and reading its
     **`asset.payload.identity_lock`** (the canonical-cast hex/beard/silhouette lock — there is NO
     `identity_desc` field on the panel_spec node; the node-model identity authority is the asset's
     `identity_lock`) + the locked props the motif ledger pins for this panel.
   - **"ALLOWED CHANGE (vs the prior panel):"** — from the panel's `motifs` delta (the comic reinterpretation
     of "ALLOWED MOTION": what may legitimately differ from the previous panel).
   - **"FORBIDDEN (must NOT happen):"** — the FIXED baseline `["no new character entering frame", "no off-model
     drift", "no scene/world recolor"]` + any panel-specific `must_not_add`.
   - **"SCREEN-TEXT WHITELIST (exact characters to preserve):"** — the `expected_literals[]` from the
     blueprint (e.g. `["REJECT","37","T-16:05"]`) + any baked-in signage/label names. Even when HTML owns the
     bubbles, baked-in figure text (chips, stamps, code) still needs char-exact preservation — this whitelist
     is the upstream of `panel_gate`'s literal diff.
   Write `_meta.json` (character/element counts) for the trace.
3. **Phase 1·5 · failure_mode positive-invariant injection (retry only — the spiral active-memory hook).**
   On `--retry`, query the wiki for **ACTIVE** `failure_mode` nodes scoped to this panel via
   `target_layer ∈ {prompt_pattern, visual_transition, global}`; rank by `recency*severity`
   (recency `= 1.0/age_days`, severity default 3); take the top 10. Match the composed string against each
   mode's `semantic_signature` by weighted Jaccard
   (`0.35*assets + 0.25*cterms + 0.20*kw + 0.20*frags`); **threshold 0.55** fires a match. For a matched mode,
   inject its `repair_pattern` **ONLY if `encoding_style == "positive_invariant"`** (else WARN + skip —
   negatives like "no missing ears" make diffusion fixate on the negated concept). Inject each as a
   **"POSITIVE INVARIANTS (must be present in every panel, highest priority):"** block at the **FRONT** of the
   message. Record the consult as a **legal `derived_from`** edge (prompt_bundle → failure_mode) with
   `evidence.consulted_failure_mode: true` + the match score (there is no `consulted_failure_mode` edge type).
   This is exactly the `--reason` a retry must name.
4. **Phase 1·6 · trigger re-scan.** Re-scan the FULL message against the `trigger_patterns` of EVERY active
   banlist mode (not just injected ones). If a matched mode is a `positive_invariant` whose `repair_pattern`
   isn't present yet → append it in-place into the POSITIVE INVARIANTS block. If any violation STILL remains
   → write a **legal `failure_of`** edge (failure_mode → prompt_bundle — failure_mode → target, trigger in `evidence`; there is no
   `violates_failure_mode` edge type) and **exit 7** (a regenerate signal to the orchestrator).
5. **Phase 2 · VALIDATE = the hard gate (runs on the FULL composed message; this is the rubric).** Delegate to
   `scripts/_validate.py` (the single source): `passes_all = length_ok AND no_banned_vocab AND no_baked_bubbles
   AND real_refs_ok`. ANY failure → preserve `_validation.json`, set the panel's
   `review_gates.storyboard_json_gate = "fail"`, and **exit 4** — see the EXACT gate below. **Do NOT silently
   add quotes / fix the spec** — a malformed spec FAILS validation so the fix is pushed back to the authoring
   layer.
6. **Phase 3 · emit.** Write the `prompt_bundle` node (payload = the schema's 6 required fields exactly:
   `{source_panel_id, source_blueprint_id, style_prefix, composed_prompt, banned_vocab_scan,
   identity_ref_paths}`); set its status `locked`. Write the **LEGAL** edges (every `type` ∈ EDGE_TYPES):
   `derived_from` (prompt_bundle → panel_spec) and `uses_blueprint` (prompt_bundle → blueprint) — **NOT
   `generated_from`** (illegal, fails the release gate). **Route `html_bubbles[]` to the JSON viewer overlay
   only** — they are NOT in `composed_prompt`. Append a timeline entry to `wiki/log.md`.
7. **Phase 4 · stdout.** Emit one-line JSON `{"prompt_bundle_id":"prompt:...","panel_id":"...",
   "source_blueprint_id":"blueprint:..."}` — the canonical orchestrator input. Set
   `panel_spec.review_gates.storyboard_json_gate = "pass"`.

## The EXACT gate (deterministic fail-closed — dimensions + thresholds + veto)
This is a **transform**, so there is **NO cross-model / scored gate here** (that lives downstream in
`comic-director`'s `panel_gate`). The gate is a deterministic contract/banned-vocab validator on the
**COMPOSED message** — ported verbatim from `shot-prompt-builder` / `segment-intent-builder`. Each dimension
is binary; ANY hit is a hard fail (no single-vote averaging — this is detect-only).

- **`length_ok`** — `len(composed_prompt) ≤ MAX_MESSAGE_CHARS = 4000` (~600 words, the empirical backend
  tolerance). Over cap → fail.
- **`no_banned_vocab`** — the **搬运工 v2** validator: ~80 case-insensitive, word-boundary patterns the backend's
  own agents own. **Veto = any single hit fails the whole message.** The list below is the human-readable map;
  the **single source of truth is `scripts/_validate.py`'s `BANNED_VOCAB`** (imported by `build_prompt.py`, so
  the list never forks). Categories:
  - *Quality padding:* `\b8K\b`, `\b4K\b`, `hyperrealistic`, `photorealistic`, `ultra-realistic`, `cinematic`,
    `professional`, `award-winning`, `masterpiece`, `high/best quality`, `highly detailed`, `intricate details`,
    `trending on artstation`.
  - *Camera:* `the camera`, camera `moves/pans/tilts/zooms/tracks/pushes/pulls/cranes`,
    `wide/close-up/medium/long/establishing/POV shot`, `over-the-shoulder`, `dolly`, `tilt`, `pan`, `crane`,
    `drone`, `aerial`, `orbital`, `whip-pan`, `tracking shot`, `push-in`, `pull out`, `zoom`, `rack focus`,
    `focus pull`, `jib`, `steadicam`, `handheld`.
  - *Lens:* `\d{2,3}mm`, `f/\d`, `bokeh`, `depth of field`, `shallow DOF`, `DOF`, `lens`, `wide-angle`,
    `telephoto`, `anamorphic`, `lens flare`.
  - *Lighting:* bare `lighting`, `rim/key/fill light`, `three-point lighting`, `golden hour`, `blue hour`,
    `studio lighting`, `soft/hard light`, `low-key`, `volumetric`, `god rays`, `chiaroscuro`.
  - *Engine/brand:* `Unreal Engine`, `Octane`, `V-Ray`, `Blender`, `Midjourney`, `Stable Diffusion`, `Sora`,
    `Runway`, `Pika`.
  - *Clichés:* `epic`, `breathtaking`, `stunning`, `gorgeous`, `mesmerizing`, `otherworldly`,
    `surreal masterpiece`.
- **`no_baked_bubbles` (comic-specific veto)** — if `text_mode != "baked"` and any of the panel's
  `html_bubbles[]` / `bubbles[]` quoted dialogue text appears in `composed_prompt` → **fail**. HTML owns the
  bubbles; baking them is the exact drift this gate exists to catch. (When `text_mode == "baked"` the dialogue
  is allowed in the BAKED DIALOGUE block by design — this veto fires only for html/code panels.)
- **`real_refs_ok` (single-source ref veto)** — `identity_ref_paths[]` must be REAL locked `.png` paths, and
  the **ref set is exact**: no silent concatenation of extra identity IDs, no `pending:*`, no raw `asset_id`
  strings smuggled into the prose. (Single-source discipline — the ref-count linchpin; concatenating refs
  silently is forbidden.)

**Exit-code contract (= the verdict surface; `scripts/build_prompt.py` returns these EXACT numeric codes):**
`0` validated + emitted + gate pass · `2` input missing / malformed CLI (`--retry` w/o `--reason`; panel_spec
not `node_type panel_spec` or not `status: locked`) · `3` upstream prereq unmet (**blueprint not
`status: locked`** / ref not real / `content_svg` missing / `expected_literals` missing on a baked
figure-panel / style_prefix bad / failure_mode query failed) · `4` banned-vocab | length | baked-bubble | ref
fail (gate → fail, `_validation.json` preserved) · `7` Phase 1·6 regenerate (a `trigger_pattern` still matches
after repair; a legal **`failure_of`** edge written).

## Worked example
The reference movie's per-panel `condition` blocks —
**[`../../examples/comic_m3_audit/comic.json`](../../examples/comic_m3_audit/comic.json)** — are the
**compiled-artifact (comic.json runtime) OUTPUT shape this skill produces** (the spiral engine inlines exactly
these `condition.*` keys). They are NOT the node fields this skill *reads* — those are the flat `panel_spec` /
`blueprint` / `asset` node payloads (the `condition.` prefix exists only in comic.json). Copy these output
patterns, but source each from its node field as noted:

- **A baked figure-panel — `S11` (the REJECT verdict).** Compiled output (comic.json):
  `condition.content_svg: "assets/reject_verdict_round1_v1.svg"`, `text_mode: "baked"`,
  `condition.expected_literals: ["REJECT","37","T-16:05"]`, `world: "dark-cyber"`. **Node sources:**
  `content_svg` ← `blueprint.payload.content_svg`; `expected_literals` ← `blueprint.payload.expected_literals`;
  the identity lock ← the identity-sheet `asset.payload.identity_lock` reached via `panel_spec.payload.
  asset_ids[]`. The compiler emits: STYLE PREFIX (dark-cyber palette, no camera vocab) → **BAKED DIALOGUE**
  (because `text_mode==baked`: from `panel_spec.payload.bubbles[]`, reviewer "Rejected. Fix it, then come
  back." / executor "...Copy that.") → SCENE COMPOSITION NARRATIVE (from the `blueprint.content_svg` layout +
  `panel_spec.side_narration`: the verdict chamber + the REVIEW·ROUND 1 card) → FIXED ELEMENTS (from
  `asset.identity_lock`: "blue executor brown hair NO beard / green reviewer dark hair beard") → FORBIDDEN (no
  new character, no off-model drift) → **SCREEN-TEXT WHITELIST `REJECT` · `37` · `T-16:05`**. Those three
  literals are exactly what `panel_gate` blind-diffs — they MUST be present and char-exact, and this is why a
  baked figure-panel that omits `expected_literals` is refused at Phase 1.
- **The 搬运工 line in the data.** Note what is *absent* from every compiled `condition.scene`/`characters`
  string (and from the node fields they were compiled from): no "the camera pushes in", no "85mm", no
  "cinematic lighting", no "8K". The author already speaks backend-legal; the validator is the second line of
  defense that keeps it that way when a style adjective sneaks in.
- **An HTML-bubble panel — `S22` (the constellation endcard).** `text_mode: "html"`, `bubbles: []`,
  `expected_literals: []`, plus `safe_zones` for the HTML tagline. Here the compiler **SKIPS the BAKED
  DIALOGUE block** and routes nothing-text into the prompt; the scene string even hard-asserts "NO text, NO
  glyphs anywhere in the image". For a panel like `S02` whose bubbles ARE drawn (`text_mode: "baked"`,
  bubbles researcher/executor/reviewer), those same bubbles would instead go in the BAKED DIALOGUE block — the
  identical `bubbles[]` field is routed to the *prompt* or to the *viewer* solely by `text_mode`. That switch,
  applied per panel, is the whole "no baked bubbles unless baked" guard made concrete.
- **The single-ref discipline — `S01` / `S20` / `S21`.** Each pins exactly its locked identity sheet
  (`trio_identity_sheet_v001.png` or `researcher_chibi_canonical_ref_v001.png`) as `identity_ref` — one exact
  ref set per panel, never a silent concatenation. `identity_ref_paths[]` in the emitted `prompt_bundle`
  mirrors precisely that set.

(The provenance of these panels — the debate→synthesize outline, the MOTIF STATE TABLE that pins each
literal, the user-approval gate — lives upstream in `comic-outline-creator` / `comic-storyboard-creator`;
by the time a `panel_spec` reaches *this* skill it is locked, and this skill only transcribes it.)

## Hard do / don't (earned lessons)
- **DO** compose the EXACT fixed-section string `style_prefix + condition_string` deterministically — and on
  retry inject the active `failure_mode` `repair_pattern` (positive_invariant ONLY) at the FRONT.
- **DO** run the banned-vocab + length + no-baked-bubble + real-ref validator on the **COMPOSED** message
  (catches `ART_BIBLE`/style contamination, not just per-field text) — and FAIL closed, never paper over.
- **DO** route `html_bubbles[]` to the JSON viewer overlay; the bake string carries dialogue **only** when
  `text_mode == "baked"`.
- **DON'T** call Codex in the happy path — this is a pure transform; a Codex call is only ever a reported
  upstream bug, never a way to "fix" a malformed spec here.
- **DON'T** invent or "improve" a scene element, number, cast member, or style adjective — if the spec is
  malformed or a ref is `pending:*`, exit non-zero pointing upstream (creator bug vs blueprint-not-`locked`
  vs ART_BIBLE contamination), do NOT patch locally.
- **DON'T** let camera / lens / lighting / "8K hyperrealistic cinematic" padding into the prompt, and **DON'T**
  concatenate extra identity refs — the backend owns optics, `ART_BIBLE` owns style, and the ref set is exact.
- **DON'T** emit on a blueprint that is not `status: locked` or a panel_spec that is not `status: locked` —
  refuse (exit 3 / exit 2). And **DON'T** write an edge `type` outside `validate_wiki.py` EDGE_TYPES (no
  `generated_from` / `consulted_failure_mode` / `violates_failure_mode` — they fail the release gate).

## Protocols (governance contracts this skill honors)
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — this compiler does NOT judge the panel it
  builds; it transcribes a locked spec and emits a deterministic banned-vocab proof. Numbers
  (`expected_literals`) are *carried through verbatim*, never originated; the pixels are judged downstream.
- [`reviewer-independence`](../../protocols/reviewer-independence.md) — there is no reviewer in this step (it's
  a transform). The downstream judge (`comic-director`'s `panel_gate`) gets the baked image + the blueprint's
  `expected_literals`, never this compiler's interpretation.
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — a clean validate here is a *transform pass*, not an
  acquittal: a deterministic same-model check is allowed to confirm "the message is backend-legal", but the
  quality/correctness verdict on the result is the cross-model `panel_gate`, never this skill.
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — N/A on the happy path (no model call); if a
  blocked retry ever escalates to an external consult, Codex `gpt-5.5` `xhigh` / Gemini `auto-gemini-3`, never
  downgraded.
- [`review-tracing`](../../protocols/review-tracing.md) — every emit logs to `wiki/log.md`; every retry writes
  a legal **`derived_from`** edge to the consulted `failure_mode` (consult + score in `evidence`), and a legal
  **`failure_of`** edge if a trigger still fires, so the spiral memory is auditable (both edge types are in
  `validate_wiki.py` EDGE_TYPES).
- [`output-versioning`](../../protocols/output-versioning.md) — the `prompt_bundle` records `file_sha256` of
  the blueprint it compiled, so a re-bake traces to the exact `content_svg` version.
