# Authoring a comic — fuzzy idea → `comic.json` (you don't hand-write JSON)

You should **not** type `comic.json` by hand. The intended path mirrors the figure side's
`brief → Step-0 → blueprint`: you give your agent a vague idea, your agent authors the structured IR, and
this repo's tools render + adversarially verify it. `comic.json` is the **contract boundary** — the agent
authors it; the engine (`run_comic.py`) fills the generation results back in.

```
fuzzy idea (one line / a script / mixed)
   │  Step-0 — an LLM authoring step (YOUR agent: Claude, or via the ARIS main repo)
   ▼
comic_brief.json   (schemas/comic_brief.schema.json — the canonical hand-off:
                    beats[] · cast + identity refs · per-panel headline numbers/claims ·
                    world (warm-lab / dark-cyber) · text_mode intent)
   │  Step-0 compiles the brief → a schema-valid comic.json
   │    • pages[] + panel_ids                         (page layout / reading order)
   │    • per-panel condition{} — WHAT TO GENERATE:
   │        content_svg       (author one deterministic SVG blueprint per figure-bearing panel)
   │        expected_literals (REQUIRED when content_svg is set — the numbers/keys that must survive the bake)
   │        world · scene · chibi_action · identity_ref (or null → the project's canonical cast)
   │    • render fields: bubbles{zh,en} · caption · safe_zones · crop · text_mode
   ▼
validate: schemas/comic.schema.json  (jsonschema) + cli/validate_wiki.py (the trace, after a run)
   ▼
run_comic.py  →  bakes each panel, gates it cross-model, and writes back image_path /
                 active_attempt_id / wiki_node_id on KEEP. You never fill those.
```

This is a direct mirror of `skills/method-figure/references/blueprint_authoring.md` +
`method_figure_brief.schema.json`. Full field reference for the target IR: [`docs/comic-json.md`](../../../docs/comic-json.md)
+ [`schemas/comic.schema.json`](../../../schemas/comic.schema.json). **Do not depend on the ARIS main repo at
runtime** — this repo is self-contained; ARIS main is only an *optional* upstream brief producer.

---

## Two honesty notes (read before you point at the example)

> **① The blueprint is per-figure, and YOU author it.** ARIS-Movie-Director does not invent your content.
> For every panel that carries a technical figure, *you* author a deterministic SVG blueprint
> (`condition.content_svg`) and you declare the numbers/labels/code tokens that must survive the bake
> verbatim (`condition.expected_literals`). The framework only *bakes the look* and then *adversarially
> checks* that your authored numbers actually appear — a beautiful panel whose number is wrong (`+6.2`
> authored vs `+6.25` baked) is rejected by the deterministic token-diff. The blueprint is the **ground
> truth**; the image model is never trusted to originate a number. The examples here use ARIS's own audit
> story, but the path is generic: swap in your SVG and your literals. A panel with no technical figure sets
> `content_svg: null` and relies on `scene` + `bubbles` alone.

> **② Identity is bring-your-own; the ARIS chibi duo is just the example.** The reference comic's
> `executor`/`reviewer` chibi pair and `assets/duo_canonical_ref_v001.png` are **one** identity set, shipped
> so the trace is reproducible — not a required cast. Point each panel's `condition.identity_ref` at *your*
> canonical character sheet (a project-relative `.png`), or leave it `null` to fall back to the project's
> canonical ref. The gate judges identity **against the ref you supply**, per character, and never penalizes
> a character for being absent from a panel (cast-aware). Your characters, your world (`warm-lab` /
> `dark-cyber` are the example's two-world palette — define your own in `ART_BIBLE.md`).

---

## Step-0 mapping (brief → comic.json)
| brief field | → comic.json |
|---|---|
| `beats[]` (id, page_type, members) | `pages[]` (`id`, `type`, `panel_ids`) + `narration`/`beat_title` |
| `cast[]` + `identity_refs` | top-level `identity_refs` + each panel's `condition.identity_ref` |
| per-panel `headline_numbers` / `claims` | the SVG blueprint's drawn text **and** `condition.expected_literals` (verbatim) |
| per-panel `world` | `condition.world` (drives ART_BIBLE §0.5 lighting) |
| per-panel `beat`/`staging` | `condition.scene` + `condition.chibi_action.{executor,reviewer}` |
| per-panel `dialogue` | `bubbles[]` `{speaker, style, text:{zh,en}}` |
| `text_mode intent` | panel `text_mode` (`baked` = dialogue drawn into the image; `html` = HTML bubble overlay) |

**Guardrail (same as the figure side):** every panel's drawn numbers must be copied VERBATIM into
`expected_literals`. A baked figure panel with no ascii-tokenizable `expected_literals` is **refused**
(fail-closed) by `run_comic.py` — there'd be nothing to verify, so a wrong number could slip.

## Worked example (the shipped reference)
Panel **S12** (the `examples/comic_m3_audit` audit page) is the template to copy:
```jsonc
"S12": {
  "text_mode": "baked",
  "crop": { "shape": "wide", "position": [0.5, 0.45], "zoom": 1.0 },
  "bubbles": [
    { "speaker": "executor", "style": "shout", "text": { "zh": "赢了 +6.2！", "en": "We won — +6.2!" } },
    { "speaker": "reviewer", "style": "terse", "text": { "zh": "先审评估器。", "en": "Audit the evaluator first." } }
  ],
  "caption": { "zh": "…", "en": "…" },
  "condition": {
    "content_svg": "assets/method_random_vs_schema_first_v1.svg",   // YOU author this SVG
    "expected_literals": ["+6.2"],                                   // the number that must survive the bake
    "world": "warm-lab",
    "identity_ref": null,                                            // → falls back to the canonical duo
    "scene": "warm-lit pixel ML research lab at night … amber Δ +6.2 callout …",
    "chibi_action": { "executor": "arm thrust up in triumph", "reviewer": "arms crossed, skeptical" }
  }
}
```
Then: `python3 skills/comic-director/scripts/run_comic.py --project examples/<name> --page <P> --panels S12`
→ bakes S12, gates it (the `+6.2` must be transcribed by both visual reviewers), and on KEEP writes its
`image_path` back into `comic.json`.
