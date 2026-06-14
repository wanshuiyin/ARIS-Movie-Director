# comic_min_author — minimal Phase-1 authoring fixture

The **copy target** for the comic-author workflow: ONE valid node of each of the 10 author types
(`intent_spec, style_anchor, outline_spec, asset, storyboard_spec, panel_spec, blueprint, prompt_bundle,
motif_ledger, continuity_constraint`) under `wiki/nodes/`, the author-layer `wiki/edges.jsonl`, an
`ART_BIBLE.md` with a `STYLE_PREFIX[warm-lab]` line, and the real on-disk `assets/panel_demo_v1.svg`
(content_svg) + `assets/cast_sheet_v1.png` (identity ref). Unlike `examples/comic_m3_audit/` (a 198-node
*runtime* trace), THIS shows the authoring layer.

Verify + demo:
```bash
python3 cli/validate_wiki.py examples/comic_min_author        # all 10 author node types conform
python3 skills/comic-panel-prompt-builder/scripts/build_prompt.py examples/comic_min_author panel:demo_s01
#   ^ emits a prompt_bundle (prompt:panel-demo_s01) + wiki/log.md — those are GENERATED, regenerate freely.
```
