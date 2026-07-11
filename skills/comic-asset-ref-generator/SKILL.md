---
name: comic-asset-ref-generator
description: "Phase-1 (S4) of a comic movie — PRODUCE the canonical reusable references the whole spiral conditions on. Per asset it bakes ONE canonical 1:1 white-bg identity ref via the agent mcp__codex__codex sidecar bake (Codex native image_gen — conditioned, never hand-pasted) OR, for a deterministic motif (clock/chart/stamp/star-map), emits a single-source parametric SVG from a python generator (asset_lib.py). Hashes + base64-encodes the bake into the asset node's output_ref (all 6 fields or it's a schema violation), versions every ref _v{NNN} with a supersedes self-edge, and runs a single-source collision gate. GENERATES ONLY — it NEVER self-locks/approves (that is the cross-model asset-review-loop's job, a different model family). Identity is BRING-YOUR-OWN; the ARIS chibi duo is only the worked example."
argument-hint: [asset_id | --batch-from-outline <outline_id> | --regenerate <asset_id> --reason "<text>"]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, mcp__codex__codex, mcp__codex__codex-reply
---

# comic-asset-ref-generator — the Reference Producer (Phase 1 · S4)

The **missing Layer-2 of comic-author**: take the storyboard's consolidated `ASSET_REQUESTS` and produce, for
**every** declared asset, the one canonical artifact that **every downstream panel bake will condition on** —
so the film never grows two visual dialects and every panel of the same character/prop/motif reads as the same
thing. This is precisely the producer of `comic.json`'s `identity_refs` (e.g. `duo_canonical_ref_v001.png` +
per-character locks like `executor.hoodie #1D4684` / `reviewer.beard true`) that the proven comic created **by
hand**. It is the upstream sibling of [`comic-blueprint-author`](../comic-blueprint-author/SKILL.md) (which
authors per-panel content-SVGs) and feeds [`comic-asset-review-loop`](../comic-asset-review-loop/SKILL.md) and
the [`comic-director`](../comic-director/SKILL.md) spiral.

Two asset classes, two production routes — **this is the load-bearing fork**:

```text
storyboard.consolidated_asset_requests
   ├── identity / scene / prop  ──▶  RASTER ref:  agent mcp__codex__codex sidecar bake, CONDITIONED on a labeled white-bg
   │      (a face, a hoodie,           condition + real identity refs → 1:1 (or 16:9 scene) PNG
   │       an empty room)              → output_ref{file_path,data_url,sha256,width,height,mime}  (ALL 6)
   │
   └── deterministic motif      ──▶  SVG SOURCE:  ONE parametric builder in asset_lib.py
          (clock / chart / stamp        (ddl_chip / stamp / mug / curve_panel / tokyo_chip / starmap …)
           / mug / star-map)            the "ref" IS the single-source SVG — NOT an image bake
                                        → records generator_script, owner_script, file_sha256

   both routes → review_status:"pending"  (NEVER "locked" here)  → collision gate → asset-review-loop
```

The battle lesson, landed as the fork above: a clock, a chart, a verdict stamp, a star-map is **deterministic
content** — you do NOT bake it as a fuzzy image and hope the digits land; you build it once from a python
generator (`asset_lib.py`) so all 18 instances of the DDL timeline, all 7 verdict stamps, both the labeled and
the wordless star-map render from the **same coordinates** and never diverge. An identity (a face, a costume) is
**not** deterministic — that you bake once via the sidecar bake (Codex's native image tool), *conditioned* on a
labeled white-bg reference and the real identity refs, never a free prompt, never a hand-paste.

## Constants
- **GENERATOR** (raster route) = the agent's `mcp__codex__codex` sidecar bake: `model: "gpt-5.5"`,
  `config{ model_reasoning_effort: "xhigh", include_image_gen_tool: true }`, **`sandbox: "workspace-write"`**,
  plus `approval-policy: "never"` — an **mcp-call argument**, NOT a `.bakereq.json` field (the sidecar payload
  carries no such key). This exact shape is the **empirical v3.5 lesson**: without `workspace-write` +
  `approval=never` + `include_image_gen_tool=true`, Codex falls back to writing *descriptive text* (or an SVG
  renderer) instead of firing its native image tool. `image_gen` is **incompatible with `minimal`** effort; the
  shipped bake runs **`xhigh`** — the same `gpt-5.5 + xhigh` single compat default pinned in
  `run_comic.get_bake_plan()` (contract `bakereq/v1`, the digest the p0_proof cert binds to; a config-driven
  model/effort override is **planned**, not yet implemented). **Honest scope: this Phase-1 raster ASSET bake
  is paid and runs PRE-P0** — the p0_proof cert gates the Phase-2/3 PANEL bakes only (no cert can exist before
  `comic.json` compiles, and assets must lock first); the gate on THIS spend is the cross-model
  [`comic-asset-review-loop`](../comic-asset-review-loop/SKILL.md) + the single-source collision gate (P5),
  not P0. NB the Codex CLI *reviewers* elsewhere in the
  pipeline pin **no** model (they follow the local codex config — currently `gpt-5.6-sol`) at effort `xhigh`;
  only the bake payload pins `gpt-5.5`. The authoritative bake reply is the `.bakestatus.json` sidecar
  (`{status, failure_kind, mcp_output, request_id}` — P2r step 3) + the native PNG on disk; codex is **never**
  asked to emit a JSON-line self-report (that was a retired codex-exec-era contract).
- **SVG SOURCE** (deterministic route) = a pure-python parametric builder living in `gen/asset_lib.py`, emitted
  by a thin `gen/gen_core_assets.py` writer. The palette is **pinned to `comic.json` ui_tokens** — never
  re-typed per asset. This route calls **no image model** and spends **zero credits**.
- **MAX_GEN_RETRIES** = 2 (3 attempts total) — on `ok:false` OR a missing / zero-byte / invalid PNG
  (`file <path>` check). Append `"[retry {n}: previous failure was: {reason}]"` to the prompt each retry.
- **VERSIONING** = monotonic 3-digit `_v{NNN}` (`duo_canonical_ref_v001.png`, `ddl_widget_template_v1.svg`).
  Version **only grows**; the prior artifact **stays on disk** for the audit cascade; a `supersedes` self-edge
  links the new version to the old (record `prev_sha256:<hex>` + `prev_version:N` in `tags`).
- **`<refs>` RESOLUTION + SUBDIR** — `<refs>` = `<project>/` + `movie.project.json` `dirs.assets` (default
  `assets/`); the canonical identity target resolves via `movie.project.json` `identity_ref` with fallback
  `assets/duo_canonical_ref_v001.png` (the same resolution `run_comic.py derive_paths()` uses). The
  `characters | scenes | props | text_panels` subdir split is the RECOMMENDED layout for a **new** multi-asset
  project; the worked example predates it and keeps a FLAT layout — duo ref at
  `assets/duo_canonical_ref_v001.png`, extra cast under `assets/identity/`
  (`researcher_chibi_canonical_ref_v001.png`, `trio_identity_sheet_v001.png`). SVG sources under `gen/` +
  `assets/`. Placeholder key: `<project>` = the project dir (e.g. `examples/comic_m3_audit`); `<refs>` as
  above; the pickup verifier lives at the literal repo-relative path
  `skills/method-figure/scripts/pickup_image.py`.
- **NEVER LOCK** — `review_status` is left `"pending"` (node `status` ≤ `under_review`). The executor that
  **produces** an asset is **forbidden** from approving it; locking belongs to the cross-model
  `comic-asset-review-loop` (a different model family). Setting `review_status:"locked"` here is a contract
  violation.
- **ONE RUNNER PER PROJECT** — each raster bake writes its **own explicit `out_path`** via the
  `.bakereq.json`/`.bakestatus.json` sidecar seam, so there is **no global-dir cross-pollination** between
  concurrent bakes. There is **no `/tmp/aris_imagegen.lock`** in agent mode — the agent wrapper itself
  serializes the `mcp__codex__codex` calls. The real race surface is two runners on the **same project**
  colliding on the per-asset `.bakereq.json`/`.bakestatus.json` sidecars + the shared `out_path`, so keep
  **one runner per project**. (The global generated-images dir + newest-after-marker pickup that could
  cross-pollinate is a hazard of the **legacy exec path ONLY**, retired for real bakes.)

## Input contract (3 modes)
This skill **never invents an asset id**. If the outline/storyboard did not declare it, the operator adds it at
the outline layer (`comic-outline-creator`) — not here.

**Pipeline position (the Phase-1 asset DAG — the documented contract):** OUTLINE_DRAFT_VALID (the outline gate
validates narrative + continuity + safety and that every referenced `asset_id` is **DECLARED with a complete,
generatable request** — it does **NOT** require locked assets) → human outline approval → **provisional**
storyboard (structural pass; may reference draft assets) → `consolidated_asset_requests` → **this skill (S4) +
`comic-asset-review-loop` (S5) generate and LOCK the assets** → OUTLINE_FINAL_LOCK (cheap re-check: the locked
assets still match the approved outline) → storyboard FINAL asset-resolution validation → blueprints. The hard
locked-asset barrier sits **before blueprint authoring** — not at the outline gate (the old single-stage
contract deadlocked: an outline demanding locked assets that depend on a storyboard that depends on a locked
outline).

1. **single** `asset_id` matching `^asset:[a-z0-9_-]+$` — produce one asset, await its verdict.
2. **`--batch-from-outline <outline_id>`** — read the human-approved outline's `character_asset_ids[] +
   scene_asset_ids[] + prop_asset_ids[]` ∪ the **provisional** storyboard's `consolidated_asset_requests`
   (structural pass — the storyboard is not asset-resolved yet at this point in the DAG), keep **only**
   `review_status=="pending"`, process **serially** (raster bakes never overlap), fire the review loop **once**
   at the end.
3. **`--regenerate <asset_id> --reason "<text>"`** — force a re-render even if `approved`/`rejected`; prefix the
   generation prompt with `"[regen reason: ...]"`, bump `_v{NNN}`, write a `supersedes` self-edge.

## What it reads / what it writes (wiki nodes & edges)
Per [`schemas/node_schema.json`](../../schemas/node_schema.json) (`node/comic/3.0`):

- **READS** `storyboard_spec` (`payload.consolidated_asset_requests`, `payload.global_policies`) and
  `outline_spec` (`payload.character_asset_ids / scene_asset_ids / prop_asset_ids`, `payload.global_style_bible`).
- **WRITES / MUTATES** the **`asset`** node (`node_id: ^asset:[a-z0-9_-]+$`, `node_type:"asset"`). Required
  payload fields (schema `oneOf → asset`): `asset_kind`, `name`, `visual_description`, `identity_lock`,
  `ref_requirements`, `review_status`, `version`. This skill additionally writes the **produced** ref onto the
  node (see the two contracts below) and leaves `review_status:"pending"`, node `status:"under_review"`.
- **EDGES** ([`schemas/edge_schema.json`](../../schemas/edge_schema.json), `src/dst/type`): on a regenerate,
  emit a `supersedes` **true self-edge** with the **bare** `node_id` on BOTH endpoints (the node_id pattern
  `^(...|asset|...):[a-z0-9_-]+$` forbids `@`/`{`/`}`, and there is ONE `asset:<slug>` node per asset — no
  per-version node files — so any `@v{N}` endpoint would dangle and fail `cli/validate_wiki.py` lines 165-167
  (endpoint resolution; the node_id-pattern check is lines 113-114)):
  `{src: asset:<id>, dst: asset:<id>, type:"supersedes", evidence:"regen v{N}->v{N+1}: <reason>; prev_sha256:<hex>; prev_version:N"}`.
  The cross-version lineage lives in the artifact filename `_v{NNN}` + `prev_sha256`/`prev_version` in `tags`
  (per [`output-versioning`](../../protocols/output-versioning.md)) — NOT in the edge endpoints. (Only if you
  truly need a versioned snapshot node, encode the version IN the slug — `asset:<slug>_v002`, which matches the
  pattern — AND actually write that second node file so both endpoints resolve.)
- **FAILURE** — on retry exhaustion write a `failure_mode` node so the spiral routes around it, and exit
  non-zero. **No asset_ref-layer example node ships in the repo** (every `examples/comic_m3_audit/wiki/nodes/fail_*.json`
  is a downstream SHOT-level node — e.g. `fail_s09_a01.json` carries `layer:"panel_visual"` +
  `affected_shot_ids:["S09"]` — do NOT mirror those for this upstream gate). Write this literal skeleton instead:
  ```jsonc
  { "node_id": "fail:<asset-slug>_image_gen_unavailable", "node_type": "failure_mode", "status": "active",
    "title": "asset_ref bake failed — <asset-slug>", "created_at": "<real UTC now>",
    "tags": ["image_gen_unavailable"],
    "payload": { "layer": "asset_ref", "affected_shot_ids": [], "active": true,
                 "repair_pattern": "<tag-derived hint>" } }
  ```
  (root `status:"active"` is the runtime canon validate_wiki.py enforces for failure_mode; payload has **all 3**
  PAYLOAD_REQUIRED fields — `layer`, `affected_shot_ids` (empty: this is the UPSTREAM asset gate, no shots yet),
  `active`.) Do **not** trigger the review loop on an empty file.

## The two fail-closed engine contracts (honor these or the director refuses to run)
These are the same fail-closed invariants the spiral enforces — produce assets so they **cannot** violate them:

1. **Every panel needs a `content_svg`.** Every deterministic motif a panel will use MUST be produced as a
   single-source SVG in `asset_lib.py`, so the panel's blueprint can name a real `content_svg`. If a recurring
   motif has no parametric source here, the downstream blueprint has nothing to bake-condition on and the
   director's render step fails closed. **One parametric builder per recurring motif — no exceptions.**
2. **A baked figure-panel needs `expected_literals`.** Any motif carrying gated text (a chart with `0.71→0.66`,
   a stamp reading `REJECT`, a DDL chip reading `T-16:05`) must render those literals **deterministically** so
   the panel can declare ascii-tokenizable `expected_literals` for the blind token-diff gate. Conversely, a
   **zero-text** asset (the wordless constellation) must contain **zero glyphs** — assert it at build time
   (`assert "<text" not in svg`). Producing a fuzzy raster of a chart breaks this contract; that is **exactly**
   why charts/clocks/stamps take the SVG route.

## Procedure (numbered — an agent runs this top to bottom)

### P0 · Resolve the target
Read the `asset` node. Assert `node_type=="asset"`. **Abort** if `review_status=="locked"` (`"immutable per
asset gate"`) or `review_status=="approved"` **unless** `--regenerate`. Classify the asset by `asset_kind` into
its production route: `character | scene | prop` (with a non-deterministic appearance) → **raster route (P1r)**;
a deterministic motif (`clock/chart/stamp/mug/symbol/star-map`, anything whose pixels are computable) →
**SVG-source route (P1s)**. When in doubt: *if the asset has gated literals or must be byte-identical across
instances, it is deterministic → SVG route.*

### P1r · RASTER route — build the bake prompt
From `payload`: `asset_kind`, `name`, `visual_description`, `identity_lock.must_preserve[]` (traits that MUST
appear — e.g. `"blue hoodie #1D4684"`, `"beard"`, `"silver hair"`), `identity_lock.must_avoid[]` (→ a
image-prompt "do not add" block — e.g. `"celebrity likeness"`, `"corporate branding"`, `"voxel 3-D blocks"`),
`ref_requirements.{aspect_ratio,background,pose,isolated_reference,data_url_required}`.

1. Run the **STYLE-BIBLE / banned-vocab filter** (see below) over `visual_description`; rewrite inline and
   record each substitution into the composed prompt.
2. Compose the prompt (template):
   ```
   Render a single reference image for asset {id} ({kind}: {name}).
   Subject: {filtered visual_description}
   Identity lock — preserve exactly: {must_preserve[]}
   Identity lock — do not add: {must_avoid[]}
   Reference requirements: {aspect_ratio} canvas; pure {background} fully isolated, no shadow/halo;
     pose = {pose}; isolated reference (no scene around the subject).
   No labels / watermarks / text / captions / contact-sheet grids.
   Output a SINGLE coherent reference image — not a collage, not a variation grid.
   Treat composability (this becomes a reusable identity ref) as the primary goal.
   ```
   **Pose defaults by kind:** `character` = "three-quarter front view, neutral expression, upper-body or
   full-body framing"; `scene` = "establishing wide of the empty location, no characters, neutral daytime
   lighting"; `prop` = "isolated centred view, slight three-quarter angle"; `logo_free_symbol` = "centred
   symbol on white, no scene". Provide the project's **real identity refs** as read-only condition images when
   the asset must match an existing cast member (never invent a face).

### P2r · RASTER route — bake via the `.bakereq`/`.bakestatus` sidecar (CONDITION it, never hand-paste)
This is the same fail-closed bake seam `run_comic.py` / `run_spiral.py` use (no marker, no `/tmp` lock, no
newest-pickup — **each bake writes its OWN explicit `OUTPUT_PATH`**). `OUTPUT_PATH` is a deterministic
project-relative path (`<refs>/{subdir}/{name}_v{NNN}.png` — in the worked example's flat layout that is
`assets/{name}_v{NNN}.png` / `assets/identity/{name}_v{NNN}.png`); canvas guidance in the prompt = `1024x1024`
(1:1 default) or `1280x720` (scene 16:9), background opaque/fully white, ONE image.

> **ONE agent, BOTH sidecar roles.** Unlike `run_comic.py` (a Python orchestrator serviced by an external
> agent wrapper), this skill ships **no runner** — the SAME agent running this SKILL plays the orchestrator
> (emit + verify) **and** the wrapper (call `mcp__codex__codex`, write the status). The one-liners below are
> **transitional until the shared `cli/service_bake_requests.py` broker lands (planned — it does not exist
> yet)**; they import the canonical primitives from `skills/method-figure/scripts/pickup_image.py` (the single
> source of truth) — never hand-assemble a `.bakereq.json` any other way. `<ABS_OUT>` = the absolute
> `OUTPUT_PATH`; `<ABS_PROJECT>` = the absolute project dir; run from the repo root.

1. **Emit the request (orchestrator role).** First write the composed P1r prompt body to
   `<ABS_OUT>.promptbody.txt`, then emit. `emit_bake_request` mints the per-bake uuid4-hex `request_id`
   **itself** (stamps it into the payload and RETURNS it), pre-deletes any stale `out_path` + status so a
   prior bake can't be silently reused, and writes the sidecar atomically (`.tmp → os.replace`). Capture the
   printed id:
   ```bash
   python3 -c 'import sys, time; sys.path.insert(0, "skills/method-figure/scripts"); \
   from pickup_image import build_bake_prompt, emit_bake_request; \
   body = open("<ABS_OUT>.promptbody.txt").read(); \
   pt = build_bake_prompt(body, "<ABS_CONDITION_PNG>", "<ABS_IDENTITY_REF or empty>", "<ABS_OUT>"); \
   print(emit_bake_request("<ABS_OUT>", {"prompt_text": pt, "out_path": "<ABS_OUT>",
     "content_png": "<ABS_CONDITION_PNG>", "identity_ref": "<ABS_IDENTITY_REF or empty>",
     "model": "gpt-5.5",
     "config": {"model_reasoning_effort": "xhigh", "include_image_gen_tool": True},
     "sandbox": "workspace-write", "cwd": "<ABS_PROJECT>", "created_at": time.time(),
     "min_bytes": 500000, "aspect": 1.0}))'
   ```
   `aspect` = W/H as a float (`1.0` for 1:1, `1.7778` for a 16:9 scene). `build_bake_prompt` prepends the
   canonical "use your native image generation tool" header and embeds the reference + output paths LITERALLY
   in `prompt_text` (ref #1 = the labeled white-bg condition, ref #2 = the identity ref — this skill's own
   doctrine: never a free prompt, so ref #1 always exists). Also note the epoch you passed as `created_at`.
2. **Bake (wrapper role).** Call `mcp__codex__codex` with `prompt_text` **verbatim** as the prompt and
   `model` / `config` / `sandbox` / `cwd` exactly as in the `.bakereq.json`, plus `approval-policy: "never"`
   (an **mcp-call argument** — NOT a bakereq field); codex writes the native PNG to `OUTPUT_PATH` (the
   `mcp__codex__codex` schema has no `-i` image param — the paths inside `prompt_text` are the only
   transport). The `config` MUST carry **both** `model_reasoning_effort:"xhigh"` and
   `include_image_gen_tool:true`, else codex is never handed the native image tool and no bake fires.
3. **Write the status (wrapper role).** Use the **Write tool** to create `<ABS_OUT>.bakestatus.json` =
   `{status:"ok"|"fail", failure_kind:null|"throttle"|"other", mcp_output:"<the FULL raw mcp__codex__codex
   reply text, pasted verbatim>", request_id:"<the id step 1 printed, VERBATIM>"}`.
   `mcp_output` is **MANDATORY on BOTH ok and fail** and must be the COMPLETE reply — never a summary or a
   truncation (the HARD-VETO scans it for `import struct`/`zlib.compress`/`<svg`/`matplotlib`/… traces of a
   hand-drawn fallback; an empty `mcp_output` leaves the veto inert and fail-closes). A missing/mismatched
   `request_id` is a stale/foreign bake and fail-closes.
4. **Verify the EXPLICIT `OUTPUT_PATH` (orchestrator role).** Optionally re-read the status through the
   canonical poller (returns immediately in this single-agent flow; kept for parity with the split-role seam):
   ```bash
   python3 -c 'import sys, json; sys.path.insert(0, "skills/method-figure/scripts"); \
   from pickup_image import await_bake_status; print(json.dumps(await_bake_status("<ABS_OUT>", 600)))'
   ```
   Then — only on `status:"ok"` — run the pickup verifier (literal repo-relative path):
   ```
   python3 skills/method-figure/scripts/pickup_image.py --out-existing --out <ABS_OUT> \
     --min-bytes 500000 --aspect <W/H> --created-at <epoch from step 1> \
     --request-id <the id step 1 printed> --transcript <ABS_OUT>.bakestatus.json
   ```
   which checks PNG sig + IHDR dims + size **strictly > `min_bytes`** + `mtime >= created_at` + a non-empty
   `mcp_output`, fail-closes on a `request_id` mismatch, and **HARD-VETOES** `struct`/`zlib`/PIL/`<svg`/
   `matplotlib` markers in the transcript (a clean PNG sig NEVER overrides a fallback marker). **There is no
   newest-pickup** — pickup verifies the one explicit `OUTPUT_PATH` this bake wrote.

**RETRY** per `MAX_GEN_RETRIES`. After exhaustion: keep the best valid PNG if any, else write the `failure_mode`
node + exit non-zero (do **not** call the review loop on an empty file). **Never** patch a failed bake by
hand-pasting the missing trait — re-condition and re-bake.

> **Grid guard.** A 2×2 / contact-sheet / variation-grid output is a **failed attempt** → retry (the
> "single coherent image, not a grid" line is the primary mitigation; a PIL aspect-vs-canvas check + an optional
> codex "is this a grid?" sanity reply is the backstop).

### P3r · RASTER route — hash, encode, update (atomic), honor the 6-field contract
- `SHA256 = shasum -a 256 <png>`; `(W,H)` via PIL; `DATA_URL = "data:image/png;base64,$(base64 -b 0 <png> || base64 -w 0 <png>)"`
  (macOS `-b` / GNU `-w`, cross-platform). `data_url` is a **v4 invariant** — Layer-3 multi-ref composition
  reads it directly; a missing `data_url` silently breaks downstream.
- Mutate the node `output_ref` with **ALL SIX** fields `{file_path, data_url, sha256, width, height, mime}`.
  **A partial write is a schema violation — reject it.** Write `.tmp` then `mv` (atomic; the wiki must validate
  even if interrupted). Leave `review_status:"pending"`, node `status:"under_review"`. Append a `log.md` line.

### P1s–P3s · SVG-SOURCE route — one parametric builder per motif
1. **Add / reuse one builder in `gen/asset_lib.py`** for the motif (`ddl_chip`, `stamp`, `mug`, `curve_panel`,
   `tokyo_chip`, `mini_stamp_glyph`, `verdict_card`, the star-map coord tables). Palette pinned to `comic.json`
   ui_tokens at the top of the file. Encode every cross-panel reuse contract into the **docstring** (e.g. *S11
   REJECT ↔ S16 ACCEPT instantiate the SAME `verdict_card` — mirror pair*; *the star-map JSON is the single
   coordinate truth for S16b labeled + S22 wordless*).
2. **Emit the canonical sheet via `gen/gen_core_assets.py`** — a thin `w(name, content)` writer that imports
   **only** from `asset_lib`. Its docstring maps each output filename → the storyboard `ASSET_REQUEST #`.
   Enforce single-source **inline**: if a specialized generator (e.g. `gen_b06`) takes ownership of a richer
   variant, **delete** the generic duplicate here (don't keep two).
3. **Coordinate-truth motifs** (the star-map): write the **JSON** (`wiki_starmap_nodes_v1.json`) as the *only*
   truth source; both the labeled SVG (S16b) and the wordless SVG (S22) **derive from it programmatically** —
   `禁目测` / never re-layout by eye. The zero-text twin asserts `assert "<text" not in svg` at build time.
4. Record on the node: `generator_script`, `owner_script`, `file_sha256`; **paths project-relative**. Leave
   `review_status:"pending"`.

### P4 · Hand off to the review loop (NEVER self-acquit)
**Single mode:** trigger [`comic-asset-review-loop`](../comic-asset-review-loop/SKILL.md), await its verdict
(`approve` → loop locks it / `regenerate` → recursive `--regenerate` callback, bounded by
`MAX_REVIEW_ROUNDS=3`). **Batch mode:** fire the review loop **once** at the end. This skill **never** writes
`review_status:"locked"` — locking is the cross-model loop's exclusive right.

### P5 · Single-source collision gate (CI / pre-handoff)
Run `gen/check_asset_collisions.py` (static scan of every `gen_*.py` for `w("…")` writes). **Every output
filename must have exactly one generator owner.** Two owners → exit 1 → fix (rename the specialized variant or
delete the dead duplicate) before any handoff. This is a deliberately-not-"skip-if-exists" guard (that would
*hide* the run-order bug).

## EXACT gate — `asset_generation_self_check` (deterministic, ported from aris_movie)
This is the **producer-side** self-check the skill must pass **before** handing to the review loop. It is a set
of **boolean predicates with vetoes** — **not** a numeric rubric (the numeric visual rubric lives in
`comic-asset-review-loop`, the analog of the panel_gate). Verdict ∈ `{ generated | failed }` — **NO
`approve`/`locked`** is ever emitted here.

- **output_exists** — the produced file exists and is **non-zero** bytes. *Veto on fail.*
- **raster_six_field_complete** — for a raster ref, `output_ref` has **ALL** of
  `{file_path, data_url, sha256, width, height, mime}`. A partial write = schema violation. *Veto.*
- **sha256_matches_file** — the recorded `sha256` equals `shasum -a 256` of the file on disk. *Veto.*
- **data_url_present** — `data_url` is populated (v4 invariant for multi-ref composition). *Veto on raster.*
- **svg_path_project_relative** — for an SVG/JSON source, the recorded path is **project-relative** (never an
  absolute machine path). *Veto.*
- **single_source** — `check_asset_collisions.py` exits 0: each output filename has **exactly one** generator
  owner. *Veto.*
- **zero_text_contract** — a zero-text asset (the S22 constellation) contains **no** glyphs:
  `assert "<text" not in svg`. *Veto.*
- **no_two_dialects** — no motif has two visual dialects (e.g. two stamp families, two DDL renderers). The new
  asset must match the **already-baked** instances (e.g. the stamp geometry must match the baked S15
  `WARN_corrected`). *Veto.*
- **not_a_grid** (raster) — PIL aspect-vs-canvas check (+ optional codex "is this a grid?" reply); a
  2×2/contact-sheet is a **failed attempt**, not a pass → retry.
- **banned_vocab_clear** — refuse to call `image_gen` at all if any banned / off-bible term survives the filter.

> **Why no numeric `approve` here:** the executor that *produced* the asset is not allowed to *judge* it
> (cross-model independence). This gate only proves the artifact is *well-formed and single-source*; whether it
> is *good* (identity fidelity, on-bible look) is decided by `comic-asset-review-loop` with a different model
> family.

## STYLE-BIBLE / banned-vocab filter (mandatory before any raster bake)
The aris_movie source bans camera/lens vocab that conflicts with downstream synth and silently regresses
fidelity (`8K, 4K, photorealistic, cinematic, 50mm, dolly, push-in, bokeh, rim light, masterpiece, trending on
artstation, close-up, wide shot, …`). **For the comic, this filter reads `ART_BIBLE.md`** and additionally
enforces the bible's own terms: the **two-world warm-real / dark-cyber palette** (warm = Edison/wood/window;
digital-ARIS = `dark_navy_void #0A0E27`), the **voxel ban** (`禁止 voxel 立体块` — pixel-flat only), and the
**per-character hex/feature locks** (executor blue hoodie `#1D4684` + brown hair + NO beard; reviewer green
hoodie `#30582D` + near-black hair + beard). A surviving banned/off-bible term ⟹ **refuse to call `image_gen`**.
Identity is BRING-YOUR-OWN: swap these locks for whatever the project's `ART_BIBLE.md` + `identity_lock`
declare; the ARIS chibi duo is only the worked example.

## Worked example (copy this exact pattern)
The proven comic is [`examples/comic_m3_audit/`](../../examples/comic_m3_audit/). Copy its shape:

- **The single-source builder library** —
  [`examples/comic_m3_audit/gen/asset_lib.py`](../../examples/comic_m3_audit/gen/asset_lib.py): **one
  parameterized builder per recurring token** — `ddl_chip(x,y,t,state,skin,…)` (the **sole** renderer for the
  whole 18-instance DDL timeline, 3 skins × {amber,red,green} + a `SUBMITTED` variant), the `STAMPS` table +
  `stamp(...)` (DUP / SURVIVES / REJECT / ACCEPT / WARN_corrected / SUBMITTED / AUDIT — **one** stamp dialect,
  geometry matching the baked S15), `mug(...)` (the `ML RESEARCH` cup, `hot|fading|cold`), `curve_panel(...)`
  (the `wandb · exact_parse` curve), `tokyo_chip(...)` (the `{"city":"Tok|yo"}` broken-JSON chip, multi-scale +
  a `repaired=True` twin), and `STARMAP_NODES / STARMAP_EDGES / STARMAP_LOOP` (the **single coordinate truth**)
  + the shared `verdict_card(...)` whose docstring states *S11 REJECT and S16 ACCEPT instantiate the SAME card
  (mirror pair)*. Palette constants (`RED/AMBER/GREEN/VOID/…`) are pinned to `comic.json` ui_tokens at the top.
- **The thin canonical-sheet emitter** —
  [`examples/comic_m3_audit/gen/gen_core_assets.py`](../../examples/comic_m3_audit/gen/gen_core_assets.py): a
  `w(name, content)` writer that imports **only** from `asset_lib`; its docstring maps every output filename →
  storyboard `ASSET_REQUEST #`. It writes `wiki_starmap_nodes_v1.json` as the **only** truth source, then
  derives **both** `wiki_starmap_v1.svg` (S16b, labeled — only the 4 gated literals are big) **and**
  `constellation_layout_v1.svg` (S22, **zero text**) from the same coordinates, ending with the load-bearing
  guard `assert "<text" not in svg, "constellation must contain ZERO text"`. It also shows the **inline
  ownership transfer** discipline: the generic `wandb_exact_parse_060_071` curve was **deleted** here because
  `gen_b06_blueprints.py` owns the richer two-series version (one canonical source per token).
- **The single-source collision gate** —
  [`examples/comic_m3_audit/gen/check_asset_collisions.py`](../../examples/comic_m3_audit/gen/check_asset_collisions.py):
  regex `\bw\(\s*["']([^"']+\.(?:svg|json|png))["']` over every `gen_*.py`; each filename must have exactly one
  writer; exit 0 `"✓ no asset collisions — all N generator outputs are single-source"` (verified clean: 26
  outputs, exit 0). Deliberately **not** a "skip if file exists" guard.

The raster side is grounded by the same project's hand-built `duo_canonical_ref_v001.png` +
`comic.json.identity_refs` (per-character hex/beard/silhouette locks) — the artifact this skill **automates**
producing. (P0 reminder from the real run: a missing `researcher_chibi_canonical_ref_v001.png` was a flagged
**P0 blocker** — every cast member needs its canonical ref before the panels that use it can bake.)

## Hard do / don't (earned lessons)
- **DO** condition the raster bake on a labeled white-bg reference + the real identity refs — and force the
  native tool with `sandbox:workspace-write` + `approval:never` + `include_image_gen_tool:true`, else Codex
  falls back to descriptive TEXT instead of firing `image_gen`.
- **DO** build every clock / chart / stamp / mug / star-map as ONE parametric SVG in `asset_lib.py` — never
  bake deterministic content as a fuzzy image and hope the digits land. The "ref" for a motif IS its
  single-source SVG.
- **DO** populate `data_url` and all 6 `output_ref` fields atomically (`.tmp → mv`); a partial write is illegal.
- **DO** version monotonically (`_v{NNN}`), keep the prior artifact on disk, and write a `supersedes` self-edge
  on every regenerate (`prev_sha256` / `prev_version` in `tags`).
- **DO** run `check_asset_collisions.py` before any handoff — one canonical owner per token, no two dialects.
- **DON'T** hand-paste a missing trait onto a finished bake (reads as pasted/fake) — re-condition and re-bake.
- **DON'T** ever set `review_status:"locked"`/`approved` here — the executor never self-acquits; locking is the
  cross-model `comic-asset-review-loop`'s exclusive right.
- **DON'T** invent an asset id — if the outline didn't declare it, the operator adds it at the outline layer.
- **DON'T** run two runners on the same project at once. Each bake writes its **own explicit `out_path`** via
  the `.bakereq`/`.bakestatus` sidecar, so there is **no global-dir cross-pollination** and **no
  `/tmp/aris_imagegen.lock`** in agent mode (the agent wrapper serializes the `mcp__codex__codex` calls) — but
  two runners on one project still collide on the per-asset sidecars + shared `out_path`, so keep **one runner
  per project**. (The cross-pollinating global generated-images dir is a hazard of the legacy exec path only.)
- **DON'T** trigger the review loop on an empty/failed file — write a `failure_mode` node + exit non-zero so the
  spiral routes around it.

## Protocols (governance contracts this skill honors)
- [`output-versioning`](../../protocols/output-versioning.md) — refs are versioned `_v{NNN}` monotonically; the
  prior artifact stays on disk and a `supersedes` self-edge records the lineage (`prev_sha256` / `prev_version`).
- [`reviewer-routing`](../../protocols/reviewer-routing.md) — the raster BAKE payload pins `gpt-5.5` + `xhigh`
  (the single compat default in `run_comic.get_bake_plan()`, contract `bakereq/v1`; a config-driven override is
  planned, not yet implemented), while the pipeline's Codex CLI *reviewers* pin **no** model (they follow the
  local codex config — currently `gpt-5.6-sol`) at `xhigh`; the visual judging is delegated to
  `comic-asset-review-loop` on a different model family — never downgrade the tier.
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — the model that **produces** an asset does NOT
  judge whether it's good; this skill emits only `generated | failed` (well-formed + single-source), and the
  cross-model review loop owns acquittal — the executor never self-acquits.
