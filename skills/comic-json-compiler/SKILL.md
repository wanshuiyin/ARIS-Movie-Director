---
name: comic-json-compiler
description: "Phase-1 (S9, the FINAL comic-author step) — assemble the LOCKED storyboard + locked per-panel blueprints into ONE schema-valid `comic.json` (the comic-ir/1.0 contract boundary handed to comic-director / run_comic.py). Project the page_order + each panel's condition{} + render fields into `pages[]` + keyed `panels{}` per schemas/comic.schema.json; author ONLY authored fields and leave image_path/active_attempt_id/wiki_node_id EMPTY for the engine. THE step where page-count integrity is reconciled and the orphan-panel class of bug is caught (a panel defined in panels{} that no page references — ship that and the finale silently vanishes) — caught by an INLINE whole-comic reconcile this skill runs (page_refs vs panels{} keys vs the storyboard page_order), because the deterministic scripts are per-page and the schema leaves condition/content_svg OPTIONAL. Gated by comic-cross-layer-gate --gate compile (the DETERMINISTIC gate: both run_comic.py --dry-run AND cli/validate_wiki.py must exit 0). Use when the user says '编译 comic.json', 'compile the comic', 'assemble comic.json', '出 comic.json', or the storyboard + all blueprints are locked and you need the single IR to hand to Phase 2/3. Do NOT use to author the page order (that is comic-storyboard-creator) or to bake panels (that is comic-director)."
---

# comic-json-compiler — locked storyboard + blueprints → one schema-valid `comic.json` (S9)

The **last node of the left third of Figure 1**: take the locked `storyboard_spec` (the authoritative page
order + the MOTIF STATE TABLE) and the locked per-panel `blueprint` nodes and **compile** them into the single
`comic.json` (comic-ir/1.0) that is the contract boundary to [`comic-director`](../comic-director/SKILL.md)
(Phase 2/3). You don't hand-write this file panel-by-panel — that already happened upstream; this step is the
deterministic *projection* + *reconciliation* that turns the authoring nodes into the IR and **catches the
integrity bugs that only show up once everything is assembled** — chiefly the page-count / orphan-panel
mismatch (the **orphan-panel class**). The two deterministic scripts the compile gate runs are
**per-page** (`run_comic.py` needs `--page`/`--panels`) and the JSON schema leaves `condition`/`content_svg`
OPTIONAL — so **neither of them sees the whole `pages[]`/`panels{}` set and neither catches an orphan.** That
whole-comic reconciliation against the storyboard authority is **THIS skill's own inline job** (the ~7-line set
diff below), run *before* the gate; the gate then certifies the per-page + wiki-conformance floor.

```text
  locked storyboard_spec (page_order = AUTHORITY)            ┐
  locked motif_ledger    (per-panel ground-truth)           │
  locked panel_spec × N  (the 9-field specs)                 ├─▶ ① ASSEMBLE  pages[] + panels{}  per comic.schema.json
  locked blueprint × N   (content_svg + expected_literals)   │        (author ONLY authored fields; engine fields EMPTY)
  locked prompt_bundle × N (optional, identity refs)         ┘        ▼
                                                                ② RECONCILE page-count integrity  ── INLINE python (this skill; no phantom script)
                                                                   (orphans · dangling refs · page_count vs page_order · grid2x2==4 · recap legitimacy)
                                                                      ▼
                                                                ③ VALIDATE  jsonschema(comic.schema.json) — SHAPE only (it does NOT enforce content_svg/literals)
                                                                      ▼
                                                                ④ FAIL-CLOSED contracts  (every panel a content_svg · baked figure ⇒ expected_literals)  ← THIS skill asserts; schema won't
                                                                      ▼
                                                                ⑤ comic-cross-layer-gate decision:compile_<slug> --gate compile  (DETERMINISTIC: run_comic.py --dry-run per page AND cli/validate_wiki.py both exit 0)
                                                                      ▼
                                                            approve? ─ revise ─▶ fix the OFFENDING node upstream, recompile  (you don't invent content)
                                                                      │ approve
                                                                      ▼
                                                                ⑥ EMIT comic.json (output-versioning) + movie.project.json pointer-hub + asset-copy manifest
```

## Constants
- **CONTRACT BOUNDARY** = `comic.json` (`comic-ir/1.0`) + the assets it references. Everything downstream
  (`comic-director`, `run_comic.py`, the Phase-3 viewer build `packages/viewer/build_comic.py`) reads ONLY this
  file + its assets — so a bug that survives this step survives to production.
- **AUTHORITY = the storyboard's `page_order`.** When the assembled `comic.json` page set disagrees with the
  locked `storyboard_spec.page_order`, the **storyboard wins** — the compiler conforms, it does NOT silently
  ship its own page count. (This is the converse of the storyboard gate's page-order veto.)
- **GATE** = `comic-cross-layer-gate decision:compile_<slug> --gate compile` (the target is the **real wiki
  `decision` node** this skill writes — there is NO `comic` node type and `comic.json` is not a wiki node, so it
  can never be a gate target or an edge endpoint). Per [`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md)
  the `compile` gate is **purely DETERMINISTIC**: NO `review:*` fan-out, NO Codex adjudication (so unlike every
  other gate, the "create review nodes first" pre-step does NOT apply here). It PASSES (`approve`) **iff BOTH
  on-disk scripts exit 0**: `python3 skills/comic-director/scripts/run_comic.py --project <dir> --page <P>
  --panels <ids> --dry-run` (per page) AND `python3 cli/validate_wiki.py <dir>`; else `revise` with their
  stderr as the blocker list. (The whole-comic orphan/page-count catch is NOT in either script — it is this
  skill's inline step ② below, run before the gate.)
- **VERDICT enum** (the `compile` gate's legal set, per the gate skill): `approve` / `revise`. On `approve` flip
  the compile `decision` to `final` and emit; on `revise` fix the **offending upstream node** and recompile (the
  compiler never patches content into `comic.json` by hand). A *verdict* is never a node `status`: the status the
  FLIP writes is `locked` on advance, `under_review` on needs-work, `rejected` on a terminal fail
  (schema-enum statuses only — `revise`/`regenerate` are verdicts, not statuses).
- **NO INVENTION** — the compiler is a *projection + reconciliation* step. It must NOT invent a panel, a
  number, an `expected_literal`, a page, or a `content_svg`. A missing piece is a HALT with the offending node
  id, not a fabrication ([`artifact-integrity`](../../protocols/artifact-integrity.md)).
- **ENGINE FIELDS STAY EMPTY** — `image_path` / `active_attempt_id` / `wiki_node_id` are written by the spiral
  engine on KEEP. Authoring them is a veto (you'd be claiming a bake that never ran).
- **ASCII node-id discipline** — every wiki touch goes through the one `node_id_to_filename` helper (`:` → `_`),
  per [`wiki-helper-resolution`](../../protocols/wiki-helper-resolution.md).

## Input contract — what must be LOCKED before you compile
This is a *compile* step: it consumes locked upstream nodes, it does not author them.
- One **`storyboard_spec`** (`status: "locked"`) — its `page_order` (the authority), `page_ids`, `panel_ids`,
  `global_policies` (page-order authority, text-mode rules, mirror-lock policy), `motif_ledger_id`,
  `consolidated_asset_requests`.
- The **`motif_ledger`** it points at — the per-panel ground-truth the gate uses to confirm `condition` prose
  agrees with each panel's continuity row.
- One **`panel_spec`** per panel (`status: "locked"`) — `page_type`, `world`, `text_mode`, `expected_literals`,
  `content_blueprint`, `bubbles`, `side_narration`, `motifs`, (cover/finale: `safe_zones` + endcard fields).
- One **`blueprint`** per panel (`status: "locked"`) — `content_svg`, `expected_literals` (verbatim),
  `safe_zones`, `html_bubbles`, `crop`, `negative_space_policy`, `generator_script`, `file_sha256`.
- *(optional)* the **`prompt_bundle`** per panel — for `identity_ref_paths` (else fall back to the project
  canonical from `identity_refs`).
- **HALT if any of these is not `locked`** (or its `content_svg`/`output_ref` file is missing) — name the
  offending node id. Convergence is the upstream gate's job, not yours.

## Workflow (the inline reconcile + the two deterministic gate scripts — all runnable, no phantom tool)

### ① ASSEMBLE `pages[]` + `panels{}`
Project the locked nodes into the IR. Copy `examples/comic_m3_audit/comic.json` as the shape.
1. **Top level** — `schema_version: "comic-ir/1.0"`, `comic_id`, `defaults` (`text_mode`, `default_locale`,
   `panels_per_page_cap`, `nav_default`, `pixel_rendering`), `identity_refs` (the locked cast hex table from
   the style bible — pure pointer/hex hub, never duplicated art), `ui_tokens` (viewer theming, palette pinned).
2. **`pages[]` — reading order, ONE entry per `storyboard_spec.page_order` page, in that exact order.** Each:
   `id` (the stable storyboard page id, e.g. `P00_cover`/`P02_b08`/`P03_end`), `type`
   (`cover|single|grid|grid2x2|feature|finale`), `panel_ids` (the panel ids that page shows), plus optional
   `beat`/`beat_title`/`narration`/`skill`/`title`/`links` (cover/endcard buttons — `https://` only).
3. **`panels{}` — ONE keyed entry per panel id** that appears in any page. Per panel project:
   - **`condition{}`** (what to GENERATE): `content_svg` (the locked blueprint's deterministic SVG = the
     content authority), `expected_literals` (verbatim from the blueprint), `world`, `identity_ref`
     (from the prompt_bundle or `null` → project canonical), `identity_desc`, `characters`, `scene`.
   - **render fields** (for the viewer): `text_mode`, `crop` (`shape∈hero|wide|square`, `position [x,y]` in
     0..1, `zoom ≥ 1`), `safe_zones` (each with an `id`), `bubbles` (`speaker∈researcher|executor|reviewer`,
     `style∈say|shout|terse|thought|whisper`, `text{zh,en}`, optional `anchor` = one of this panel's
     safe-zone ids), `overlays`, `caption{zh,en}`.
   - **leave EMPTY**: `image_path`, `active_attempt_id`, `wiki_node_id`.
4. **Emit `movie.project.json`** — the pure pointer-hub manifest (`project_id`, `title{zh,en}`, `story`,
   `schema_version`, `comic_json`, `art_bible`, `identity_ref`, `dirs`, `text_mode_default`, `palette`). It
   **names** the other artifacts; it NEVER duplicates their content.

### ② RECONCILE page-count integrity (the heart of this skill — INLINE python, NO external script)
**There is no `reconcile_pages.py` — it never existed.** This catch is run *inline* (the schema and the
per-page `run_comic.py` are both blind to it), so paste-and-run this ~15-line whole-comic diff against the
storyboard authority. This is where the orphan-panel class dies. Exit non-zero on ANY blocker; do NOT proceed to
the gate until it is clean.
```python
# inline reconcile — run against the assembled comic.json + the locked storyboard_spec node (NO phantom tool)
import json, sys, re
c  = json.load(open("comic.json", encoding="utf-8"))
sb = json.load(open("wiki/nodes/storyboard_<slug>.json", encoding="utf-8"))["payload"]   # the LOCKED authority
page_refs = [pid for p in c["pages"] for pid in p["panel_ids"]]      # every page→panel reference (with dups)
closing_refs = [(p.get("closing") or {}).get("image") for p in c["pages"] if (p.get("closing") or {}).get("image")]
ref_set   = set(page_refs) | set(closing_refs);  defined = set(c["panels"])  # a finale endcard (closing.image) IS a use
orphans   = sorted(defined  - ref_set)            # defined, not on a page AND not a closing endcard → BLOCKER
dangling  = sorted(ref_set  - defined)            # a page/closing points at a missing panel → BLOCKER
# PAGE-ORDER AUTHORITY — ELEMENT-WISE vs the storyboard (NOT a length check): catches reorder / id-swap / dup /
# over-count that a count comparison silently passes.
comic_order = [p["id"] for p in c["pages"]]
sb_order    = list(sb["page_order"])
order_mismatch = comic_order != sb_order               # STRICT: any reorder / missing / extra / dup → BLOCKER
order_missing  = [pid for pid in sb_order if pid not in comic_order]    # storyboard page absent from comic.json
order_extra    = [pid for pid in comic_order if pid not in sb_order]    # comic.json page not in storyboard
page_id_dups   = sorted({pid for pid in comic_order if comic_order.count(pid) > 1})  # duplicate page id (over-count)
bad_grid  = [p["id"] for p in c["pages"] if p["type"] == "grid2x2" and len(p["panel_ids"]) != 4]  # arity → BLOCKER
empty_pg  = [p["id"] for p in c["pages"] if not p["panel_ids"]]    # empty page → BLOCKER
# FAIL-CLOSED engine contracts — jsonschema leaves these OPTIONAL, so this inline step is the REAL enforcer:
def cond(pn): return pn.get("condition") or {}
no_csvg = sorted(pid for pid, pn in c["panels"].items() if not cond(pn).get("content_svg"))   # null/missing content_svg
# cfg_usable EXACTLY (run_comic.py): the EFFECTIVE mode resolves from defaults (a panel inheriting a baked
# default is still baked); a baked panel WITH a content_svg MUST carry expected_literals as a non-empty LIST
# whose every entry is an ascii-tokenizable string. ONE predicate = never weaker than the engine floor.
def emode(pn): return pn.get("text_mode") or (c.get("defaults") or {}).get("text_mode") or "html"
def baked_lits_bad(pn):
    if emode(pn) != "baked" or not cond(pn).get("content_svg"): return False
    exp = cond(pn).get("expected_literals")
    return not (isinstance(exp, list) and len(exp) > 0
                and all(isinstance(e, str) and re.findall(r"[a-z0-9+._-]+", e.lower()) for e in exp))
baked_lits_fail = sorted(pid for pid, pn in c["panels"].items() if baked_lits_bad(pn))
engine_authored = sorted(pid for pid, pn in c["panels"].items()                 # authored ENGINE fields MUST be empty
                         if pn.get("image_path") or pn.get("active_attempt_id") or pn.get("wiki_node_id"))
# bubble.anchor (if set) MUST resolve to a panel safe_zone id. safe_zones is a panel TOP-LEVEL field
# (comic.schema.json) — NOT under condition; jsonschema only TYPES anchor as a string, so assert it inline.
def sz_ids(pn): return {z.get("id") for z in (pn.get("safe_zones") or [])}
bad_anchor = sorted(f"{pid}:{b.get('anchor')}" for pid, pn in c["panels"].items()
                    for b in (pn.get("html_bubbles") or pn.get("bubbles") or [])
                    if isinstance(b, dict) and b.get("anchor") and b["anchor"] not in sz_ids(pn))
# DECLARED recap reuse is the ONLY legitimate multi-reference — read it from the storyboard, never guess.
gp = sb.get("global_policies", {})
sanctioned = set(gp.get("recap_panel_ids") or gp.get("sanctioned_recap") or [])   # storyboard-declared recap/grid set
dups = sorted({pid for pid in page_refs if page_refs.count(pid) > 1} - sanctioned)  # UNDECLARED panel dup → BLOCKER
blockers = {"orphans": orphans, "dangling": dangling, "order_mismatch": order_mismatch, "order_missing": order_missing,
            "order_extra": order_extra, "page_id_dups": page_id_dups, "bad_grid2x2": bad_grid, "empty_pages": empty_pg,
            "undeclared_dups": dups, "content_svg_null": no_csvg, "baked_literals_invalid": baked_lits_fail,
            "engine_fields_authored": engine_authored,
            "bubble_anchor_unresolved": bad_anchor}
if any(blockers.values()):
    sys.exit(f"RECONCILE BLOCKERS: {blockers}  (pages {len(comic_order)} vs storyboard {len(sb_order)})")
print("reconcile OK")
```
- **The orphan check counts `closing.image`.** In the reference `comic.json`, `S22` (the wordless constellation
  finale) is the **endcard of the finale page `P_B12`** (`P_B12.closing.image = "S22"`) — a legitimate use, NOT
  an orphan. (An earlier draft of this check read only `panel_ids` and FALSE-flagged it.) A **TRUE orphan** is a
  panel in `panels{}` referenced by neither a page's `panel_ids` NOR any `closing.image`; that is a real BLOCKER
  the compiler must catch, not ship — page it, or (if genuinely cut) make an upstream *storyboard* edit + re-lock,
  never a quiet drop. When a locked `storyboard_spec` node is present, its `page_order` is the element-wise page
  authority (reorder / missing / extra / duplicate page id all block).
- **Recap reuse is the ONE legitimate multi-reference** and must be *declared*, not inferred. In the
  reference comic, `S12,S13,S14,S15` are each referenced **twice** — once as individual `single` pages
  (`P_B08_1..4`) and once in the `grid2x2` recap/hero page (`P02_b08`). That is by-design (the storyboard's
  `mirror_locks` / recap policy), so a panel referenced >1 time is a **veto ONLY if it is not on the
  storyboard's declared recap/grid set**. The diff reads the storyboard's `global_policies` (the sanctioned
  recap ids) to know which reuses are sanctioned — an *undeclared* duplicate reference is still a BLOCKER.

### ③ VALIDATE against the schema (SHAPE only — it does NOT enforce the fail-closed contracts)
```bash
python3 -c "import json,jsonschema,sys; jsonschema.validate(json.load(open(sys.argv[1]+'/comic.json')), json.load(open('schemas/comic.schema.json')))" <project_dir>   # run from repo root
```
**Know exactly what this does and does NOT catch.** `schemas/comic.schema.json` leaves `condition`,
`condition.content_svg`, and `condition.expected_literals` **all OPTIONAL** (it constrains their *shape* when
present but never *requires* them). So jsonschema **PASSES** a panel with `content_svg: null`/absent or a baked
panel with empty `expected_literals` — exactly the states vetoes #5/#6 and the two fail-closed contracts forbid.
**Therefore the schema is NOT the contract enforcer** — step ④ (this skill's own assertion) and the
`run_comic.py --dry-run` `cfg_usable` fail-closed (step ⑤) are what bite. Do not rely on jsonschema for them.
- **`build_comic.py` is NOT a compile-time fallback.** It lives at **`packages/viewer/build_comic.py`** and is
  the **Phase-3 post-bake viewer build**: it *requires* every panel's `image_path` to be present and a real
  image on disk. A freshly-authored `comic.json` (engine fields EMPTY, per this skill) would make `build_comic.py`
  hard-fail on the missing images — it is the wrong tool here, and it never checks orphans. Cite it only for the
  post-bake viewer stage (Phase 3), with its real `packages/viewer/` path; the compile-time deterministic floor
  is `cli/validate_wiki.py` + `run_comic.py --dry-run` (step ⑤), not `build_comic.py`.

### ④ Enforce the two FAIL-CLOSED engine contracts (see the dedicated section below)
Every panel has a real `content_svg` (never `null`); every **baked** figure-panel has non-empty,
ASCII-tokenizable `expected_literals`. The one nuance — the **zero-text panel** (S22) — is spelled out below.

### ⑤ Run the compile gate (DETERMINISTIC = both scripts exit 0; no reviewer fan-out)
The `--gate compile` floor is **two real on-disk scripts**. `run_comic.py` is a **per-page** spiral runner —
its argparse marks **both `--page` and `--panels` as required**, so it must be invoked once per page with that
page's panel ids (the project-only command crashes with an argparse error). It does **NOT** validate jsonschema
and **never** sees the whole `pages[]`/`panels{}` set — so it CANNOT catch the orphan/page-count (that was step
②). Its `--dry-run` job is per-page bake-readiness: it asserts every `text_mode:"baked"` figure-panel on that
page carries ascii-tokenizable `expected_literals` (the `cfg_usable` fail-closed) and prints each concrete bake
prompt (real scene + real literals, no placeholders).
```bash
# (a) per page in the storyboard page_order — bake-readiness + fail-closed literals (NOT schema/orphan):
python3 skills/comic-director/scripts/run_comic.py --project examples/comic_m3_audit --page P02_b08 --panels S12,S13,S14,S15 --dry-run
#   …repeat for every page; a baked figure-panel with no ascii expected_literals → run_comic EXITS non-zero
# (b) wiki node/edge/payload/node_id/privacy conformance (the whole project, against node_schema.json):
python3 cli/validate_wiki.py examples/comic_m3_audit
```
First write the compile `decision` node + its edges (§ "Node it reads / writes"), then defer to the gate.
`comic-cross-layer-gate decision:compile_<slug> --gate compile` is **purely deterministic** (per the gate
skill): NO `review:*` nodes, NO Codex adjudication — it simply runs the two scripts above and returns `approve`
iff **both exit 0**, else `revise` carrying their stderr as the blocker list. (This is the one gate where the
"create review nodes first" pre-step does NOT apply — the scripts ARE the judge.) On `approve` → flip the
`decision` to `final` and emit; on `revise` → fix the **offending upstream node** and recompile. The gate (the
deterministic scripts, a different acquittal organ) — never this compiling agent — acquits
([`acceptance-gate`](../../protocols/acceptance-gate.md)).

### ⑥ EMIT
Write `comic.json` + `movie.project.json` via [`output-versioning`](../../protocols/output-versioning.md)
(timestamped + fixed-name latest; downstream reads the fixed name). Emit the **asset-copy manifest** — the
flat list of every `content_svg` / `identity_ref` the IR references and where each lives — so Phase 2/3 can
stage them. Append the wiki nodes/edges (§ below) and trace the gate round to `trace.jsonl`
([`review-tracing`](../../protocols/review-tracing.md)).

## EXACT gate (`compile`) — deterministic checks, thresholds, vetoes
The `compile` gate's legal verdicts are **`{approve, revise}`** (per
[`comic-cross-layer-gate`](../comic-cross-layer-gate/SKILL.md) — this gate is **purely deterministic**: NO
reviewer fan-out, NO 0–5 scoring, NO Codex adjudication). The checks below are therefore **machine predicates,
each PASS/FAIL**, owned by a specific on-disk enforcer — **not reviewer dimensions**. The gate returns `approve`
iff its two scripts (`run_comic.py --dry-run` per page **and** `cli/validate_wiki.py`) exit 0; the whole-comic
structural predicates (orphan / page-count / dangling / grid arity) are this skill's **inline step ②**, asserted
*before* the gate (the scripts are per-page/wiki-only and cannot see them). Each predicate below is tagged with
**[who enforces it]** so there is no claim that a tool checks something it doesn't.

Structural predicates (each PASS/FAIL):
- **`schema_valid`** **[jsonschema, step ③]** — `comic.json` validates against `schemas/comic.schema.json`
  (SHAPE only; required top-level keys present; `schema_version == "comic-ir/1.0"`). NOTE: the schema does NOT
  require `condition`/`content_svg`/`expected_literals`, so it does NOT enforce the contract predicates below —
  those are owned by step ④ + `run_comic.py`. `build_comic.py` is NOT a fallback here (Phase-3 viewer build).
- **`panel_refs_resolve`** **[inline step ②]** — every `pages[].panel_ids` entry exists as a key in `panels{}`
  (no DANGLING ref).
- **`page_count_authority_match`** **[inline step ②]** — the `pages[]` count + ids reconcile with the locked
  `storyboard_spec.page_order` (no short-count, no over-count, no re-ordering). **This is the orphan-panel
  reconciliation predicate** (neither gate script sees it — it MUST run inline).
- **`no_orphan_panels`** **[inline step ②]** — every panel defined in `panels{}` is referenced by at least one
  page; any defined-but-unreferenced panel is surfaced (a sanctioned recap reuse counts as a reference).
- **`grid2x2_arity`** **[inline step ②]** — every `grid2x2` page carries **exactly 4** panel ids; no empty page.
- **`engine_fields_empty`** **[inline step ②]** — `image_path` / `active_attempt_id` / `wiki_node_id` are
  absent/empty on every panel (the engine owns them).
- **`bubble_anchor_safezone`** **[inline step ②]** — every `bubble.anchor` (if set) resolves to one of its
  panel's `safe_zone` ids; `crop.position ∈ [0,1]²`, `crop.zoom ≥ 1`. (jsonschema only TYPES `anchor` as a
  string — it does NOT enforce the cross-reference, so this is asserted inline, not by the schema.)

Contract predicates (each PASS/FAIL — and note the schema does NOT enforce these, so step ④ + `run_comic.py` do):
- **`every_panel_has_content_svg`** **[inline step ④]** — no panel has `condition.content_svg: null` or a
  missing `condition.content_svg`. (jsonschema leaves it optional, so this MUST be asserted inline.)
- **`baked_figure_has_literals`** **[`run_comic.py --dry-run` `cfg_usable`, step ⑤]** — every panel whose
  `text_mode == "baked"` declares a non-empty, ASCII-tokenizable `condition.expected_literals` (`run_comic.py`
  EXITS non-zero otherwise; the actual token blind-diff happens later, at BAKE time in the engine — here it is
  only the *presence* assertion). The **zero-text exception** (`negative_space_policy: "zero_glyph"`, build-time
  `assert "<text" not in svg`) is the ONLY way an empty `expected_literals` passes — and only with
  `text_mode != "baked"` (see the contracts section).
- **`identity_refs_resolve`** **[inline step ④]** — every `condition.identity_ref` resolves to a real file (or
  is `null` → the project canonical exists in `identity_refs`); the cast hex table is present.
- **`asset_manifest_complete`** **[inline step ④/⑥]** — every referenced `condition.content_svg` /
  `identity_ref` exists on disk and appears in the asset-copy manifest; no inline-invented asset.
- **`manifest_is_pointer_hub`** **[inline step ④]** — `movie.project.json` names (does not duplicate)
  `comic.json`, `art_bible`, `identity_ref`; `schema_version` matches.

**Hard vetoes (any one → `revise`):**
1. **An orphan panel** — a panel defined in `panels{}` referenced by neither a page's `panel_ids` NOR any
   `closing.image` endcard (the **orphan-panel class**; a finale endcard via `closing.image` is a legitimate
   use, NOT an orphan — see S22). Authority = the storyboard's page order — conform, do not ship the short count.
2. **A dangling page ref** — a `pages[].panel_ids` entry with no `panels{}` key.
3. **Page count disagrees with the storyboard authority** (short, over, or re-ordered vs `page_order`).
4. **A `grid2x2` page without exactly 4 panel ids**, or any empty page.
5. **A panel with `condition.content_svg: null`** (or missing) — the engine fail-closed rejects it (asserted
   inline at step ④; jsonschema will NOT catch it).
6. **A baked figure-panel with empty/non-ASCII `condition.expected_literals`** (and not the declared zero-glyph
   exception) — `run_comic.py --dry-run` `cfg_usable` refuses it (the later bake-time blind-diff would have
   nothing to verify, so a wrong number could slip).
7. **An engine field authored** (`image_path` / `active_attempt_id` / `wiki_node_id` non-empty) — you'd be
   claiming a bake that never happened.
8. **An undeclared duplicate panel reference** — a panel referenced by >1 page that is NOT on the storyboard's
   sanctioned recap/grid list.
9. **An invented field** — any panel/number/`expected_literal`/page/`content_svg` not traceable to a locked
   upstream node (compiler must not fabricate).
10. **Manifest duplicates content** — `movie.project.json` inlines what it should only point at, or its
    `schema_version` mismatches `comic.json`.

## Node it reads / writes (`schemas/node_schema.json`)
**Reads** (all must be `status: "locked"`):
- one **`storyboard_spec`** (`storyboard:<slug>`) — payload `source_outline_id, page_order, page_ids,
  panel_ids, global_policies, motif_ledger_id, consolidated_asset_requests`. **`page_order` is the page-count
  authority** the compile reconciles against.
- the **`motif_ledger`** (`motif:<slug>`) it names — payload `source_storyboard_id, columns, rows, invariants,
  mirror_locks`; the gate uses `rows` to confirm each panel's `condition` prose agrees with its continuity row,
  and `mirror_locks` to know which recap reuses are sanctioned.
- **`panel_spec`** × N (`panel:<slug>`) — payload `source_storyboard_id, page_id, panel_id, sequence_index,
  page_type, world, asset_ids, text_mode, expected_literals, content_blueprint, bubbles, side_narration,
  motifs`.
- **`blueprint`** × N (`blueprint:<slug>`) — payload `source_panel_id, content_svg, expected_literals,
  safe_zones, html_bubbles, crop, negative_space_policy, generator_script, file_sha256`.
- *(optional)* **`prompt_bundle`** × N (`prompt:<slug>`) — payload `source_panel_id, source_blueprint_id,
  style_prefix, composed_prompt, banned_vocab_scan, identity_ref_paths`.

**Writes:**
- the **`comic.json` artifact** (the comic-ir/1.0 IR — **NOT a wiki node**: there is no `comic` node_type and no
  `comic:` node_id prefix, so it can never be an edge endpoint or a gate target; it is the contract boundary
  *file*) + the **`movie.project.json`** pointer-hub + the **asset-copy manifest**.
- one **`decision`** node (`node_id` `decision:compile_<slug>`, matching the schema pattern
  `^(intent|…|decision|fail):[a-z0-9_-]+$`) — payload **must** contain every PAYLOAD_REQUIRED field for
  `decision`: **`target_node_id, verdict, gate_kind`** (set `gate_kind: "compile"`, `verdict ∈ {approve,
  revise}`, `target_node_id` = the **`storyboard_spec` id** `storyboard:<slug>` — the real wiki node whose
  page_order the compile reconciles against, the only schema-legal target). `status: "final"` on the gate's
  return.
- **NO `review` node here.** The `compile` gate is purely deterministic (no reviewer fan-out, no Codex), so —
  unlike every other gate — this skill does NOT mint `review:*` nodes or a `reviews` edge. (Writing a phantom
  `review` would also fail the gate's own "the two scripts are the judge" contract.)

Author edges (all legal `EDGE_TYPES` in `cli/validate_wiki.py`, all between REAL wiki-node endpoints — NEVER
the `comic.json` file, which has no node_id): `decides` (`decision:compile_<slug>` → `storyboard:<slug>`),
`derived_from` (`decision:compile_<slug>` → `storyboard:<slug>`, the authority it was compiled against), and
one `uses_blueprint` per panel (`decision:compile_<slug>` → each `blueprint:<slug>`, the per-panel provenance).
**There is NO `compiled_from` edge type** — it is not in `EDGE_TYPES`, so writing it fails `validate_wiki.py`;
`derived_from` + `uses_blueprint` are the legal substitutes. The verdict-bearing *runtime* edges
(`attempt_of`/`rollback_of`/`reviews`) belong to Phase 2/3, not here.

## Two engine contracts to author to (fail-closed)
The compiler's last duty is to guarantee the IR can never make the spiral REFUSE a panel for a structural
reason — verify both at compile time, do not defer to the dry run alone:
1. **Every panel needs a `condition.content_svg`** — a deterministic blueprint (figure OR scene-anchor
   layout). `condition.content_svg: null` is rejected by the engine (`spiral_engine.js` reads
   `.condition.content_svg`); assert it INLINE at compile time (jsonschema leaves it optional). A dialogue/scene
   panel with no audited numbers still carries a **layout** blueprint (the scene composition + the
   negative-space safe zones).
2. **A `baked` figure-panel MUST declare non-empty, ASCII-tokenizable `condition.expected_literals`**
   (exact numbers/keys/fn-names/verdicts, **verbatim**) — else `run_comic.py --dry-run`'s `cfg_usable` exits
   non-zero (there'd be nothing for the later bake-time blind-diff to verify, so a wrong number could slip). A
   scene panel with no audited numbers → `text_mode: "html"` (its text becomes an HTML overlay, not baked glyphs).
   - **The ONE documented exception — the zero-text panel.** The reference S22 is the wordless constellation:
     `condition.content_svg` set, `condition.expected_literals: []`, `world: "starfield"`,
     `characters: "NONE … no text anywhere in the image"`, blueprint `negative_space_policy: "zero_glyph"`
     enforced by a build-time `assert "<text" not in svg`. An empty `expected_literals` is legitimate **only**
     when the blueprint is provably zero-glyph **and** `text_mode != "baked"` (the panel gates on
     `stray_text_absence`, not a literal token-diff). Any *other* empty-literals baked figure-panel is veto #6.
     Note S22 (the wordless finale) is the one panel with nothing to literal-gate — it gates on
     `stray_text_absence`, not a token-diff — and it is wired as the finale via `P_B12.closing.image`, the
     legitimate zero-glyph endcard (the closing-aware orphan check counts that as a use, so it is NOT an orphan).

## Worked example
The canonical exhibit is **[`examples/comic_m3_audit/comic.json`](../../examples/comic_m3_audit/comic.json)**
(comic-ir/1.0, `comic_id: aris_comic_v1`) + its pointer-hub
**[`examples/comic_m3_audit/movie.project.json`](../../examples/comic_m3_audit/movie.project.json)**
(`project_id: comic_m3_audit`), the IR for the **24-panel** "ARIS — I Handed Over Those 24 Hours" comic.
Copy its exact shape — and copy how it *fails* the integrity check, because that is the teaching case:

- **The closing-aware orphan check — the reference IS the PASSING fixture.** That file ships **18 pages /
  24 panels** (verified). `S22` (the wordless finale constellation) is **NOT** an orphan: it is wired as the
  finale endcard via **`P_B12.closing.image == "S22"`**, so the step-② reconcile (which counts `closing.image`
  as a use) reports `orphans = []` and prints **`reconcile OK`** on this file. A `panel_ids`-ONLY check would
  FALSE-flag it — exactly the weaker-than-the-floor bug step-② fixes. To watch the orphan blocker FIRE, use a
  deliberately-broken copy (delete `P_B12.closing.image`) → `S22` is then referenced by neither a `panel_ids`
  nor a `closing.image`, a TRUE orphan, and the reconcile exits non-zero. That is the fixture PAIR:
  ```python
  import json
  c = json.load(open("examples/comic_m3_audit/comic.json"))
  page_refs    = {pid for p in c["pages"] for pid in p["panel_ids"]}
  closing_refs = {(p.get("closing") or {}).get("image") for p in c["pages"]} - {None}
  defined      = set(c["panels"])
  print("ORPHANS  :", sorted(defined - page_refs - closing_refs))   # -> []  (S22 is P_B12.closing.image) → PASS
  print("DANGLING :", sorted((page_refs | closing_refs) - defined)) # -> []
  # delete P_B12.closing.image and re-run → ORPHANS == ['S22'] → the reconcile BLOCKS (the negative fixture)
  ```
  (The reference exhibit is a *completed runtime* trace with no Phase-1 `storyboard_*.json` node; in a real
  compile run that node exists and the reconcile compares `pages[]` element-wise to its `page_order`.)
- **The legitimate recap reuse to PASS.** In the same file `S12,S13,S14,S15` are each referenced **twice** —
  the individual `single` pages `P_B08_1..4` *and* the `grid2x2` recap/hero page `P02_b08`. That is the
  storyboard's declared recap (a `mirror_lock`), so those duplicate references are **NOT** veto #8 — the inline
  reconcile (step ②) reads the storyboard's `global_policies` to know they are sanctioned. (A panel referenced
  twice with NO such declaration *would* be a blocker.)
- **A fully-projected baked panel to copy** — `panels.S11` (the REJECT card): `condition.content_svg:
  "assets/reject_verdict_round1_v1.svg"`, `condition.expected_literals: ["REJECT","37","T-16:05"]`,
  `world: "dark-cyber"`, a rich `scene` + `characters`, `text_mode: "baked"`, and `bubbles` carrying
  `{zh,en}`. This is the shape every authored figure-panel takes.
- **The zero-glyph finale to copy** — `panels.S22`: `condition.content_svg: "assets/constellation_layout_v1.svg"`,
  `condition.expected_literals: []`, `condition.world: "starfield"`, `condition.characters: "NONE …"`,
  `text_mode: "html"`. Empty literals are legitimate **only** because the blueprint is provably zero-glyph
  (contract §2 exception); S22 is wired as the finale via **`P_B12.closing.image`** (the endcard), which the
  closing-aware orphan check counts as a use.
- **Engine fields in the reference are FILLED** — every panel in that exhibit already has `image_path` /
  `active_attempt_id` / `wiki_node_id` populated, because it is the artifact of a **completed run**; that is
  what the *engine* wrote back on KEEP. When you **author** a fresh `comic.json`, those fields are **absent**.
  Use the reference for the `condition{}` + render-field shape, not as proof those fields belong in your output.
- **The manifest pattern** — `movie.project.json` is a 13-key pointer hub: it *names* `comic.json`,
  `ART_BIBLE.md`, `assets/duo_canonical_ref_v001.png`, the `dirs{}`, the `text_mode_default`, and the
  two-world palette note — and duplicates **none** of their content.

## Hard do / don't (earned lessons)
- **DO** treat the **storyboard's `page_order` as the page-count authority** — reconcile `comic.json` against
  it and BLOCK on any mismatch; conform to the storyboard, never silently ship a different page set.
- **DO** run the orphan / dangling / page-count check **before** the schema validate — the schema alone does
  NOT catch an orphan panel (it is structurally valid JSON; only the storyboard-reconciliation catches it).
  This is the single bug this skill exists to stop.
- **DO** author **only** the authored fields and leave `image_path` / `active_attempt_id` / `wiki_node_id`
  empty for the engine.
- **DO** verify both fail-closed contracts at compile time: every panel a real `condition.content_svg` (assert
  INLINE — the schema leaves it optional); every baked figure-panel non-empty ASCII
  `condition.expected_literals` (`run_comic.py --dry-run` enforces this) — the zero-glyph panel is the one
  documented exception, and only with `text_mode != "baked"`.
- **DO** keep `movie.project.json` a pure pointer hub; never duplicate `comic.json`/bible/asset content into it.
- **DO** emit via output-versioning (timestamped + fixed-name) and ship the asset-copy manifest so Phase 2/3
  can stage every referenced SVG/ref.
- **DON'T** invent a page, a panel, a number, an `expected_literal`, or a `content_svg` to "make it validate."
  A missing piece is a HALT with the offending node id — the fix lives upstream (storyboard / blueprint), and
  a genuinely-cut finale is a *storyboard* edit + re-lock, not a quiet drop here.
- **DON'T** "fix" an orphan by deleting the panel — the authority is the storyboard's page order, so the fix is
  to add the missing page (or re-lock the storyboard if the cut was real); deleting a defined panel discards
  authored work and authored provenance.
- **DON'T** accept a `condition.content_svg: null`, a `null`-literals baked figure (outside the zero-glyph
  exception), or an undeclared duplicate reference — each is a hard veto.
- **DON'T** write a `compiled_from` edge or make `comic.json` an edge endpoint / gate target — neither is legal
  (`compiled_from ∉ EDGE_TYPES`; `comic.json` has no node_id). Use `derived_from` + `uses_blueprint` from the
  real `decision:compile_<slug>` node, and pass THAT node id to the gate.
- **DON'T** mint a `review:*` node or a `reviews` edge for the compile gate — `--gate compile` is purely
  deterministic (the two scripts ARE the judge); a phantom review would be a fabricated acquittal.
- **DON'T** self-acquit. `--gate compile` acquits via its **two deterministic scripts** (`run_comic.py
  --dry-run` per page + `cli/validate_wiki.py`, both exit 0), gated AFTER this skill's inline reconcile; the
  loop drives, it can't acquit.

## Protocols (governance contracts this skill honors)
- [`acceptance-gate`](../../protocols/acceptance-gate.md) — the loop can DRIVE but can't ACQUIT: the `compile`
  gate's verdict is **purely deterministic** — `approve` iff BOTH `run_comic.py --dry-run` (per page,
  bake-readiness + fail-closed literals) **and** `cli/validate_wiki.py` (wiki/node/edge conformance) exit 0,
  gated AFTER this skill's inline page-count reconcile. The scripts — never this compiling agent — acquit.
- [`output-versioning`](../../protocols/output-versioning.md) — emit `comic.json` + `movie.project.json` as a
  timestamped file plus a fixed-name latest copy; downstream (`comic-director` / `run_comic.py`) reads the
  fixed name and need not know the timestamp.
- [`artifact-integrity`](../../protocols/artifact-integrity.md) — the compiler *projects + reconciles*, it
  never originates content; numbers/literals/pages are verified to trace to a locked upstream node, never
  invented to pass validation.
- [`wiki-helper-resolution`](../../protocols/wiki-helper-resolution.md) — every wiki node id (the
  `decision:compile_<slug>` it writes, the `storyboard:<slug>` / `blueprint:<slug>` it edges to) is resolved to
  a filename through the single `node_id_to_filename` helper (`:` → `_`).
- [`review-tracing`](../../protocols/review-tracing.md) — the compile gate round (the two scripts' commands +
  their exit codes + any stderr) is logged to `trace.jsonl` so the deterministic verdict is auditable.
  *(No reviewer fan-out here — `--gate compile` runs no Codex/Gemini, so `reviewer-independence` /
  `reviewer-routing` do not apply to this gate; they govern the upstream score-fused gates instead.)*
