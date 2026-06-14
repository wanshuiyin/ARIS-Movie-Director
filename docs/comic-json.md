# `comic.json` — the authored input (comic-ir/1.0)

`comic.json` is the single source of truth for a comic project. It has **two layers**:

| layer | who writes it | fields |
|---|---|---|
| **story + how-to-draw** | **YOU author this** | `pages[]`, each panel's `condition{}` (what to generate), and the render fields (`bubbles`, `caption`, `safe_zones`, `crop`, `text_mode`) |
| **generation results** | **the spiral engine fills this** | `image_path`, `active_attempt_id`, `wiki_node_id` (left empty/absent until a panel is baked + kept) |

To make a new comic you author the first layer; `packages/core/spiral_engine.js` bakes each panel and
writes back the second layer; `packages/viewer/build_comic.py` then projects the whole thing to the viewer.
Formal schema: [`schemas/comic.schema.json`](../schemas/comic.schema.json). Copy
`examples/comic_m3_audit/comic.json` as a working template.

---

## Top level
```jsonc
{
  "schema_version": "comic-ir/1.0",          // required
  "comic_id": "my_comic_v1",                 // required
  "asset_root": "…",                          // optional: base path the engine resolves refs under
  "defaults": {                               // required
    "text_mode": "html",                     // html | baked | code  (per-panel overridable)
    "default_locale": "en",                  // en | zh  (bubbles/captions are {zh,en})
    "panels_per_page_cap": 4,
    "nav_default": "flip",
    "pixel_rendering": true
  },
  "identity_refs": { … },                     // the locked cast (see below) — optional but recommended
  "ui_tokens": { … },                         // optional viewer theming
  "pages":  [ … ],                            // required — reading order
  "panels": { "S01": { … }, "S02": { … } }    // required — the panels referenced by pages
}
```

## `identity_refs` — the locked cast (so characters never drift)
The project's visual constitution: one canonical ref + per-character locked traits. Every panel that
shows a character points at this via its `condition.identity_ref`.
```jsonc
"identity_refs": {
  "duo_canonical": "…/duo_canonical_ref_v001.png",
  "executor":  { "hoodie": "#1D4684", "hair": "#925935", "beard": false },
  "reviewer":  { "hoodie": "#30582D", "hair": "#0F0D16", "beard": true  },
  "researcher":{ "ref": "…/researcher_ref.png", "glasses": "black rectangular", "tee": "black" }
}
```

## `pages[]` — reading order (one entry per displayed page)
```jsonc
{
  "id": "P01_b02",                 // required, unique
  "type": "single",                // required: cover | single | grid | grid2x2 | feature | finale
  "panel_ids": ["S02"],            // required: ids into panels{} (grid2x2 needs EXACTLY 4; never empty)
  "beat": "B02",                   // optional story-beat tag
  "beat_title": {"zh":"…","en":"…"},
  "narration": {"zh":"…","en":"…"},// optional sidebar narration
  "skill": "$ aris run …",         // optional mono "skill/command" chip in the sidebar
  "title": {"zh":"…","en":"…"},    // cover/finale headline
  "links": [ {"label":{…},"url":"https://…"} ]  // cover/endcard buttons (https only)
}
```

## `panels{}` — one entry per panel id
### (a) `condition{}` — what to GENERATE (you author; the engine reads this to bake)
```jsonc
"condition": {
  "content_svg": "assets/handoff_terminal_v1.svg",  // deterministic blueprint SVG (the CONTENT AUTHORITY)
  "expected_literals": ["T-24:00:00","ARIS ONLINE","$ aris run"],  // REQUIRED if content_svg is set:
                       // the exact tokens the gate blind-diffs against (numbers/keys/fn names/verdicts).
                       // A baked figure with NO ascii-tokenizable expected_literals is REFUSED (fail-closed).
  "world": "seam",                 // palette/world tag (extensible): warm · warm-lab · seam · dark-cyber · starfield
  "identity_ref": "assets/identity/trio_identity_sheet_v001.png",  // the cast sheet fed to image_gen
  "identity_desc": "LEFT = researcher (black glasses…); RIGHT = duo (blue exec no-beard; green reviewer beard)",
  "characters": "who is where, doing what, in this panel (staging prose for the bake)",
  "scene": "the full scene description the bake renders (world · props · lighting · composition)"
}
```
### (b) render fields — for the VIEWER (you author)
```jsonc
"text_mode": "baked",              // html (HTML bubble overlay) | baked (text drawn in image) | code
"crop": { "shape":"wide", "position":[0.5,0.45], "zoom":1.0 },  // shape∈hero|wide|square;
                                   // position [x,y] focal point 0..1; zoom ≥ 1
"safe_zones": [ {"id":"tl","x":0.02,"y":0.03,"w":0.4,"h":0.22} ],  // each needs an id; clean regions for bubbles
"bubbles": [
  { "speaker":"researcher", "style":"say",   "text":{"zh":"…","en":"…"}, "anchor":"tl" },
  { "speaker":"executor",   "style":"shout", "text":{"zh":"…","en":"…"} },
  { "speaker":"reviewer",   "style":"terse", "text":{"zh":"…","en":"…"} }
],                                 // speaker∈researcher|executor|reviewer;
                                   // style∈say|shout|terse|thought|whisper;
                                   // anchor (optional) MUST be one of this panel's safe_zone ids
"overlays": [],
"caption": { "zh":"…", "en":"…" }
```
### (c) engine-filled — leave OUT when authoring; the spiral writes these on KEEP
```jsonc
"image_path": "panels/S02_panel_a01.png",   // project-relative .png/.jpg/.webp under the project
"active_attempt_id": "S02_a01",
"wiki_node_id": "panel:s02_…"
```

## Validation (what `build_comic.py` hard-fails on)
- every `pages[].panel_ids` entry must exist in `panels{}`
- `defaults.text_mode` and any panel `text_mode` ∈ `{html, baked, code}`
- every `safe_zone` has an `id`; every `bubble.anchor` (if set) resolves to one of its panel's safe-zone ids
- no empty pages; a `grid2x2` page has **exactly 4** panel ids
- `image_path` is project-relative (no absolute path, no `..`) and a real `.png/.jpg/.webp` under the project
- `crop.position` is `[x,y]` in `0..1`; `crop.zoom` ≥ 1

And for generation, the gate refuses to run (fail-closed) if a baked-figure panel (`condition.content_svg`
set) has no ascii-tokenizable `expected_literals` — there'd be nothing to verify, so a wrong number could slip.

## Minimal authorable example (before any baking)
```jsonc
{
  "schema_version": "comic-ir/1.0",
  "comic_id": "demo_v1",
  "defaults": { "text_mode": "html", "default_locale": "en" },
  "identity_refs": { "researcher": { "ref": "assets/identity/me.png", "tee": "black" } },
  "pages":  [ { "id": "P1", "type": "single", "panel_ids": ["S01"],
                "narration": { "en": "Night one. 24 hours on the clock." } } ],
  "panels": {
    "S01": {
      "text_mode": "baked",
      "crop": { "shape": "hero", "position": [0.5, 0.45], "zoom": 1.0 },
      "safe_zones": [ { "id": "tl", "x": 0.04, "y": 0.05, "w": 0.45, "h": 0.3 } ],
      "bubbles": [],
      "caption": { "en": "24 hours to the deadline." },
      "condition": {
        "content_svg": "assets/ddl_anchor.svg",
        "expected_literals": ["DDL", "T-24:00:00"],
        "world": "warm",
        "identity_ref": "assets/identity/me.png",
        "scene": "a tired researcher at a warm desk, a dark failed-run terminal, a DDL countdown widget"
      }
    }
  }
}
```
Run the spiral on this → it bakes `S01`, gates it, and fills `image_path`/`active_attempt_id`/`wiki_node_id`.
Then `build_comic.py` → the viewer.
