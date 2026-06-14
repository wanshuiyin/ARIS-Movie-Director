# Phase 1 — Authored Source of Truth (the SOP your agent follows)

This is the **left third of Figure 1** — *Asset Library → Outline → Storyboard → `comic.json`* — turned into a
followable procedure so it isn't left for the user to reinvent. You (the user) hand your agent a fuzzy idea;
your agent runs **these layers** to produce `comic.json` + its assets; then [`run_comic.py`](../scripts/run_comic.py)
(Phase 2/3) bakes + adversarially verifies it. The reference movie's own Phase 1 was produced exactly this way —
its executed form is the `gen/` scripts under `examples/comic_m3_audit/` (cited per layer below). This mirrors
the [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) main project's intent→outline→
storyboard authoring pipeline; ARIS main is one such authoring agent (optional, not a runtime dependency).

> **Answer to "does the user have to make the asset library themselves?"** No — that's what this SOP is for.
> The agent builds it, by following the Asset Library layer below. But the asset library IS required input:
> `comic.json` references content-SVG blueprints + identity refs that must exist before a bake. They are
> *authored*, not free — the framework verifies them, it doesn't invent your numbers or your cast.

Each layer ends with a **gate** (cross-model where it's a quality/correctness call — executor ≠ reviewer,
same rule as the panel_gate). Author once, lock, move on.

---

## Layer 0 · Intent (fuzzy idea → locked premise)
**In:** a one-liner / script / mixed source. **Out:** the top of a `comic_brief`
([`schemas/comic_brief.schema.json`](../schemas/comic_brief.schema.json)): `logline`, `thesis`, `cast[]`
(+ identity refs), `worlds[]` (the palette tags, e.g. `warm-lab` / `dark-cyber`), `bake_lang`.
**Gate:** completeness (no unresolved "what is this about / who is in it / how many pages"). Capture
uncertainties explicitly rather than guessing.

## Layer 1 · Asset Library ("one visual dialect, never two")
**In:** the cast + recurring visual tokens implied by the premise. **Out:** one **single-source** asset per
recurring element — identity sheets (one canonical `.png` per character; BYO, the ARIS duo is only the
example) and every cross-panel motif (clocks, stamps, mugs, charts, star-maps…) authored **once** as a
deterministic SVG so the movie never grows two looks.
- **Worked example:** `examples/comic_m3_audit/gen/asset_lib.py` (shared single-source builders) →
  `gen_core_assets.py` (emits the canonical asset library) → `assets/`.
- **Enforce single-source:** `examples/comic_m3_audit/gen/check_asset_collisions.py` fails if any asset
  filename is written by >1 generator (the "one visual dialect" rule, in code).
- **Gate:** identity-lock + single-source + reuse-readiness. (ARIS main does this with a cross-model
  "准 ×3" asset-review loop; at minimum, no two sources for one token, and each identity sheet is on-model.)

## Layer 2 · Outline (premise → beats, one per page)
**In:** locked intent + cast. **Out:** `comic_brief.beats[]` — an ordered list of story beats, each tagged
with its page `type` (cover / single / grid / grid2x2 / feature / finale), the cast/world it uses, and a
one-line narration. (The reference movie = 13 beats / 19 pages.)
**Gate:** coverage (the beats tell the whole thesis) + every beat is render-feasible with the locked assets.

## Layer 3 · Storyboard (beats → per-panel spec)
**In:** locked outline + asset manifest. **Out:** for each panel, the `condition` block:
- `world` · `scene` · `chibi_action` (per-character staging) · `dialogue` (`{zh,en}` bubbles),
- and **for any figure-bearing panel:** a **content-SVG blueprint** you author (`condition.content_svg`,
  the deterministic GROUND TRUTH) **plus** `condition.expected_literals` — the exact numbers/keys/code
  tokens that must survive the bake, copied VERBATIM.
- **Worked example:** `examples/comic_m3_audit/gen/gen_b0*_blueprints.py` (per-beat content_svg authoring,
  importing the Layer-1 `asset_lib`).
- **Fail-closed gate (enforced by run_comic.py):** a `baked` panel with a `content_svg` but **no**
  ascii-tokenizable `expected_literals` is refused — there'd be nothing to verify, so a wrong number could
  slip. So every figure-panel MUST declare its literals here.

## Layer 4 · Compile → `comic.json`
Assemble `pages[]` + `panels{}` per [`schemas/comic.schema.json`](../../../schemas/comic.schema.json)
(fields in [`docs/comic-json.md`](../../../docs/comic-json.md)); copy `examples/comic_m3_audit/comic.json`
as the shape. Validate (jsonschema). The agent fills the **authored** fields only; `image_path` /
`active_attempt_id` / `wiki_node_id` are left empty — Phase 2/3 writes them on KEEP.
**Gate:** `comic.json` validates; every page's `panel_ids` resolve; every figure-panel has `expected_literals`.

---

## Hand-off to Phase 2/3
```bash
python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <P> --panels S01,S02 --dry-run
```
`--dry-run` prints each panel's concrete bake prompt from your authored `comic.json` — if it shows real
scenes + real literals (no placeholders) and the fail-closed gate passes, Phase 1 is done correctly. Then
drop `--dry-run` to bake. See [`comic_authoring.md`](comic_authoring.md) for the brief→comic.json field
mapping, and [`SKILL.md`](../SKILL.md) for the whole pipeline.
