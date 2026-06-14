# Phase 1 — Authored Source of Truth (the SOP your agent follows)

This is the **left third of Figure 1** — *Asset Library → Outline → Storyboard → `comic.json`* — turned into a
followable procedure so it isn't left for the user to reinvent. You hand your agent a fuzzy idea; your agent
runs **these layers** to produce `comic.json` + its assets; then
[`run_comic.py`](../../comic-director/scripts/run_comic.py) (the `comic-director` skill, Phase 2/3) bakes +
adversarially verifies it. The reference movie's Phase-1 **executed artifacts** are the `gen/` scripts under
`examples/comic_m3_audit/` (cited per layer). This mirrors the
[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) main project's intent→outline→
storyboard pipeline; ARIS main is one such authoring agent (optional, not a runtime dependency).

> **Does the user build the asset library?** No — the agent does, by following Layer 3. But the asset library
> IS required input: `comic.json` references content-SVG blueprints + identity refs that must exist before a
> bake. They are *authored*, not free — the framework verifies your numbers/cast, it doesn't invent them.

Each layer ends with a **gate** (cross-model where it's a quality/correctness call — executor ≠ reviewer,
same rule as the panel_gate). Author once, lock, move on.

## Two engine contracts you must author to (fail-closed — the #1 source of "why won't it bake")
1. **Every panel needs a `condition.content_svg`** — a deterministic blueprint SVG. The engine requires one
   for *every* panel (it's the content authority + the bake's layout ref), not only figure panels. A
   scene-only panel still gets a simple **layout** blueprint SVG.
2. **A `baked` panel that carries a figure must declare `condition.expected_literals`** (the exact
   numbers/keys/code tokens, verbatim) — else the run is *refused*. A scene panel with no audited numbers
   should be `text_mode: "html"` (dialogue as an HTML overlay, no baked-literal contract). **Do NOT use
   `content_svg: null`** — the engine rejects it.

---

## Layer 0 · Intent (fuzzy idea → locked premise + cast)
**Out:** the top of a `comic_brief` ([`../schemas/comic_brief.schema.json`](../schemas/comic_brief.schema.json)):
`logline`, `thesis`, `cast[]` **+ one locked identity ref (.png) per character** (BYO; the ARIS duo is only
the example), `worlds[]` (palette tags, e.g. `warm-lab` / `dark-cyber`), and `bake_lang` (the PRIMARY language
baked into images; the alternate is still authored in Layer 2 for the viewer toggle).
**Gate:** completeness — premise, cast, identity refs, page count are all resolved (capture uncertainties
explicitly, don't guess).

## Layer 1 · Outline (premise → beats, one per page)
**Out:** `comic_brief.beats[]` — ordered story beats, each with a page `type` (cover / single / grid /
grid2x2 / feature / finale), the cast/world it uses, and a one-line narration. (Reference = 13 beats / 19 pages.)
**Gate:** coverage (the beats tell the whole thesis) + each beat is feasible with the locked cast.

## Layer 2 · Storyboard (beats → full per-panel spec — including layout)
For each panel author the complete spec — **not just `condition`, also the render/layout fields the viewer
consumes** (this is where agents otherwise stall):
- `condition`: `world` · `scene` · `chibi_action` (per-character staging) · and the **plan** for its
  `content_svg` blueprint + (if it carries a figure) the `expected_literals` it must preserve.
- **render/layout (author these here):** `text_mode` (`baked` = dialogue drawn in; `html` = HTML bubble
  overlay), `bubbles[]` `{speaker, style, text:{zh,en}}`, `caption{zh,en}`, `crop{shape,position,zoom}` (the
  focal point so faces/figures aren't sliced), and `safe_zones[]` (clean regions; every `bubble.anchor` must
  resolve to one).
- **page-level (cover / finale):** the `kicker` / `title` / `tag` / `links` (cover) and `closing` (finale)
  fields the viewer renders — author them on the page, not the panel.
This layer also **surfaces the consolidated asset_requests**: the list of recurring motifs + the per-panel
blueprints Layer 3 must build.
**Gate:** every panel has a text_mode + a blueprint plan; every baked figure-panel has its `expected_literals`
listed; every bubble anchor has a safe_zone.

## Layer 3 · Asset Library + blueprints ("one visual dialect, never two")
Build, as **single-source** deterministic SVGs, everything Layer 2 requested: the recurring motifs (clocks,
stamps, mugs, charts…) **and** every panel's `content_svg` blueprint.
- **Author SVGs by WRITING A PYTHON GENERATOR SCRIPT, not by emitting raw SVG/XML in chat** — LLMs get raw
  SVG coordinates wrong; a script is precise, debuggable, and keeps one source per asset. Mirror the worked
  example: `examples/comic_m3_audit/gen/asset_lib.py` (shared single-source builders) →
  `gen_core_assets.py` (the asset library) → `gen_b0*_blueprints.py` (per-panel `content_svg`).
- Also finalize **`ART_BIBLE.md`** (the world/style rules — `run_comic.py` reads it into every bake prompt)
  and the identity refs from Layer 0.
- **MANDATORY GATE — single-source:** run the collision check
  (`examples/comic_m3_audit/gen/check_asset_collisions.py`, or the same rule) — it FAILS if any asset
  filename is written by >1 generator. This is "one visual dialect, never two" enforced by tool, not intent.
- **Gate:** identity-lock on-model + single-source clean + every referenced `content_svg`/`identity_ref` exists.

## Layer 4 · Compile → `comic.json`
Assemble `pages[]` + `panels{}` per [`../../../schemas/comic.schema.json`](../../../schemas/comic.schema.json)
(fields in [`../../../docs/comic-json.md`](../../../docs/comic-json.md)); copy
`examples/comic_m3_audit/comic.json` as the shape. Author only the **authored** fields; leave `image_path` /
`active_attempt_id` / `wiki_node_id` empty — Phase 2/3 writes them on KEEP.
**Gate:** `comic.json` validates (jsonschema); every page's `panel_ids` resolve; every figure-panel has
`expected_literals`; every panel has a real `content_svg`.

---

## Hand-off to Phase 2/3 (the `comic-director` skill)
```bash
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <P> --panels S01,S02 --dry-run
```
`--dry-run` prints each panel's concrete bake prompt from your authored `comic.json` — real scenes + real
literals, no placeholders, and the fail-closed gate passes = Phase 1 is done right. Then drop `--dry-run` to
bake. Field mapping: [`comic_authoring.md`](comic_authoring.md). Render/verify contract: the
[`comic-director`](../../comic-director/SKILL.md) skill.
