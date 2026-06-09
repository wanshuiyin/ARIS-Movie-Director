# ARIS-Movie Architecture (Shared Spec)

This document is the single source of truth for all ARIS-Movie v4 skills. Each skill must conform to the contracts here. When updating, bump the version at the bottom and add a `## Changelog` entry.

**Version**: v2.1 (2026-05-26; supersedes v2.0 of 2026-05-24; v2.0 of 2026-05-24 supersedes v1.1 of 2026-05-21; v3.5 state preserved at `v3.5-final` git tag)

---

## 0.5. Length tiers (canonical)

The pipeline is runnable at **three target lengths**, selected via `--target mvp|demo|longform`. The brief (`MOVIE_BRIEF.md`) defines the canonical tier table; this section is the architectural restatement.

| Tier      | Duration  | Segments    | Use case                                                                |
| --------- | --------- | ----------- | ----------------------------------------------------------------------- |
| `mvp`     | 30s       | 2 × 15s     | first end-to-end pipeline validation, minimal credits burn              |
| `demo`    | 90s       | 4-6 × 15s   | WAICA talk opener, 小红书 horizontal, B 站                              |
| `longform`| 150-180s  | 10-12 × 15s | flagship deliverable: wiki accumulation + cross-segment drift visible   |

**Pipeline invariant**: the same skill code runs at any tier — only `--target` differs.

- `/aris-movie` accepts `--target` and threads it down to `/movie-storyboard-creator`, which sets `MAX_BEATS_PER_LINEAGE` to (2, 6, 12) for (mvp, demo, longform) respectively.
- Reviewer/effort settings (§10) are orthogonal to length tier. A `mvp` run at `effort: max` is legal and cheap; a `longform` run at `effort: lite` is legal but discouraged.
- The brief's `payload.target_tier` records which tier was executed for a given run; the storyboard's `beat_list` length is the ground truth for "what actually got shot".

---

## 1. Project framing

ARIS-Movie applies the ARIS research-pipeline pattern (cross-model adversarial review + persistent wiki) to **long-form video generation**. The deliverable is a `mvp`/`demo`/`longform` coherent video (see §0.5), now produced through a **3-layer pipeline** (intent → outline+assets → storyboard+shots), with every layer audited and every artifact recorded in the wiki.

The v4 redesign is informed by three signals that arrived after v3.5 shipped:

1. **External feedback** that v3.5's "13 platting skills + progressive segment loop" looked like an API wrapper rather than a production architecture.
2. **FireRed-OpenStoryline** as a positive reference for layered tooling — it cleanly separates story/script/storyboard/asset stages and treats AI transitions as a post-stitch tool, not a generation crutch. ARIS-Movie v4 adopts the layered idea but keeps the ARIS adversarial-review philosophy at every layer boundary.
3. **Empirical evidence from v3.5** (image-2 anchor + Seedance i2v at 100% text fidelity) showing the generation route is sound; the bottleneck was the *planning and asset* layer, not the *pixel* layer.

**Differentiation vs prior work** (carried forward from v1.x):

- **vs MovieAgent** (top-down hierarchical CoT + one-shot generation): we are bottom-up + progressive + retryable, and now layer the planning so identity/scene/style locks are explicit assets rather than implicit prompts.
- **vs A²RD** (closed-loop video memory, white-box generator): we treat the generator as a black box (Pippit/Seedance) and put intelligence in the asset library + review + memory layer, not in the generator weights.
- **vs Sora-class end-to-end**: we expose every intermediate decision, every failure mode, every retry; the wiki is the audit trail.
- **vs FireRed-OpenStoryline** (the closest layered tool): we add cross-model adversarial gates between every layer, treat assets as first-class wiki nodes with their own review loop, and refuse end-frame conditions during generation (Seedance breaks).

**ARIS思想 preservation**: the v4 redesign is a layering change, not a philosophy change. Cross-model independence, reviewer-independence rule, audit cascade, persistent wiki, and "executor cannot judge its own work" all transfer verbatim from ARIS research pipelines.

---

## 2. Three-layer architecture

```
External Input (text / video / script)
        │
        ▼
┌─────────────────────────────────────────────┐
│ Layer 1: Intent Parsing                     │
│ raw input -> intent_spec                    │
│ only answers: what does the user want?      │
│ what constraints? what unknowns?            │
└─────────────────────────────────────────────┘
        │ intent gate (ambiguity + scope review)
        ▼
┌─────────────────────────────────────────────┐
│ Layer 2: Script Outline + Asset Library     │
│ intent_spec -> outline_spec                 │
│ scenes / characters / props / audio_bible   │
│ each visual asset: 1:1 white-bg ref,        │
│   data_url + file_path + sha256             │
│ asset refs undergo ARIS adv loop until      │
│   "准 ×3" locked                            │
└─────────────────────────────────────────────┘
        │ outline gate + asset gate (per asset)
        ▼
┌─────────────────────────────────────────────┐
│ Layer 3: Storyboard + Frame Conditions      │
│ outline_spec + locked assets -> shot_spec[] │
│ each shot references asset IDs only         │
│ image-2 multi-ref -> start-frame condition  │
│ Seedance i2v with start frame ONLY          │
│ no tail frame; intermediate guides optional │
└─────────────────────────────────────────────┘
        │ frame_condition gate + clip gate
        ▼
┌─────────────────────────────────────────────┐
│ Clip Runtime                                │
│ upload start frame -> Seedance i2v          │
│ extract last-clear-frame, trim blur tail    │
│ stitch, loudness normalize, subtitles       │
└─────────────────────────────────────────────┘
        │
        ▼
Movie Wiki / Asset Library / Audit Cascade
  intent / outline / asset / shot /
  frame_condition / continuity_anchor /
  clip_attempt / clip_accepted / review /
  decision / failure_mode / audio_profile /
  service_job
```

### Layer mandates

- **Layer 1 — Intent Parsing.** Read whatever the user supplied (text brief, scratch markdown, paste, even a reference video transcript) and produce a single `intent_spec` node. Layer 1 is *not allowed* to invent assets or write shot-level prompts. Its job is to ask "what does the user want, what are the hard constraints, what is still ambiguous?" — and to flush the answer through the **intent gate** before Layer 2 starts.
- **Layer 2 — Outline + Asset Library.** Convert the locked intent into a story outline (`outline_spec`) and the asset list that outline needs (characters, scenes, props, style anchors, audio profiles). Each asset is generated as a 1:1 aspect, white-background reference (via `/asset-ref-generator`) and pushed through an asset-specific adversarial review loop (`/asset-review-loop`) until it gets three independent "准" verdicts ("准 ×3"). The **outline gate** runs once on the outline before any asset gen; the **asset gate** runs per asset and produces an `asset.status = locked` only when identity / scene / style is verifiably reproducible.
- **Layer 3 — Storyboard + Frame Conditions.** Take the locked outline and locked assets and emit `shot_spec[]`. Each shot references existing `asset_id`s by ID only — *never re-describes an asset's appearance in prose*. For each shot, `/frame-condition-builder` calls codex image-2 multi-ref to composite a start frame from the referenced assets, that composite passes the **frame_condition gate**, and only then does `/shot-prompt-builder` assemble the Pippit message (semantic content + voice + dialogue, no camera/lens vocab) for Seedance i2v. Each rendered clip passes the **clip gate** before being accepted.

### Gate map

```
Layer 1 ─[ intent gate ]──► Layer 2 ─[ outline gate ]──► Layer 2 ─[ asset gate × N ]──► Layer 3
Layer 3 ─[ frame_condition gate × N ]──► Clip Runtime ─[ clip gate × N ]──► Wiki commit
```

Every gate is implemented by `/cross-layer-gate` (renamed from v1.1's `/segment-to-narrative`), parameterized by gate kind. Reviewer assignment, rubric, and threshold per gate are listed in §5.

### State machine (verdicts)

```
KEEP             → commit clip to accepted/, extract last-clear-frame as
                   continuity_anchor, build next shot's frame_condition.
RETRY_SEGMENT    → same shot_spec, revised i2v prompt or revised
                   frame_condition (failure_reason → repair instruction);
                   max_attempts_per_shot = 3.
REWRITE_SHOT     → this single shot cannot be expressed as currently planned;
                   regenerate shot_spec (and possibly its frame_condition)
                   without touching the rest of the storyboard.
ABANDON_LINEAGE  → 2-3 consecutive shot failures with the same root cause
                   from the same storyboard lineage; pick a new lineage
                   (or escalate to outline rewrite if no other lineage exists).
STOP             → budget exhausted, or user halt, or 3+ consecutive
                   ABANDON_LINEAGE outcomes.
```

`REWRITE_STORYBOARD` from v1.1 is renamed `REWRITE_SHOT` in v4: because v4 separates the outline (locked, multi-shot) from the storyboard (shot list), regenerating "the whole storyboard" is now reserved for an *outline-level* failure (handled inside the outline gate, not by clip-side gates). A clip-side gate at most asks for the offending *shot* to be rewritten — typically because its frame_condition or audio plan is unrealistic — which is strictly cheaper than a full storyboard rewrite. The legacy verdict name is accepted as an alias during v3.5 → v4 migration but is normalized to `rewrite_shot` on write.

---

## 3. The 16 v4 skills

| # | Skill | Layer | Role | Status |
|---|-------|-------|------|--------|
| 1 | `/aris-movie` | orchestrator | drives all layers + daemon mode | KEPT (gains daemon subcommand) |
| 2 | `/intent-parser` | L1 | raw input → `intent_spec` | NEW |
| 3 | `/movie-outline-creator` | L2 | `intent_spec` → `outline_spec` + asset list | NEW (replaces v3.5 storyboard creator) |
| 4 | `/asset-ref-generator` | L2 | gen 1:1 white-bg ref via codex image-2 | NEW |
| 5 | `/asset-review-loop` | L2 | adv loop on each asset until "准 ×3" | NEW |
| 6 | `/movie-storyboard-creator-v4` | L3 | locked outline → `shot_spec[]` | REWRITTEN |
| 7 | `/shot-prompt-builder` | L3 | shot_spec → Pippit message + audio | REWRITTEN (was segment-intent-builder) |
| 8 | `/frame-condition-builder` | L3 | multi-ref first-frame composite | NEW |
| 9 | `/last-clear-frame-extractor` | L3 | extract clean frame for next shot | NEW |
| 10 | `/movie-wiki` | infra | wiki ops + v4 schema | KEPT |
| 11 | `/movie-review-loop` | infra | cross-model review at any layer | KEPT |
| 12 | `/cross-layer-gate` | infra | gate decisions (renamed from segment-to-narrative) | RENAMED |
| 13 | `/segment-stitch-ffmpeg` | infra | final concat + audio mix | KEPT |
| 14 | `/baseline-sd2-oneshot` | infra | naive baseline | KEPT |
| 15 | `/blind-comparison-review` | infra | A/B compare | KEPT |
| 16 | `/frame-extractor` | infra | n-frame keyframe extraction | KEPT |

**Note on absorbed v3.5 skills**: `/style-bible-lock`, `/character-consistency-check`, `/continuity-audit` from v3.5 are no longer standalone skills in v4. Their work is absorbed:

- *Style bible*: lives inside `outline_spec.global_style_bible` (Layer 2) and is consulted by every asset gate + frame_condition gate; no separate skill is needed because every gate cross-checks against the bible.
- *Character consistency*: each character is an `asset` node with `status: locked`; the asset gate's `identity_lock_satisfied` dim is the consistency check, run at *asset creation time* rather than ad-hoc against clips. Frame-condition gate then verifies the composite preserved the locked identity.
- *Continuity audit*: continuity constraints are folded into `outline.narrative_beats[].must_show` / `must_not_show` fields and into `continuity_anchor` nodes (last-clear-frame per shot). The clip gate's `plot_continuity` dim still checks shot-to-shot transition quality.

This consolidation drops the skill count's audit surface area but *increases* the number of audit triggers, because checks now run at each layer boundary instead of only at clip review time.

---

## 4. Wiki schema v2

Canonical, machine-validated payload contracts live in `movie-wiki/schemas/node_schema.json` (`$defs/payload_<node_type>` + per-type `oneOf` branch). The table below is a human summary; **the JSON schema is the single source of truth** and skills MUST validate writes against it.

Wiki layout (unchanged from v1.1, with `assets/` promoted to a tracked tier):

```
movie-wiki/
├── index.md
├── log.md
├── director_pack.md            # ≤8000 chars; what /aris-movie needs at each decision
├── query_pack.md               # ≤8000 chars; what outline/storyboard creators need
├── graph/
│   └── edges.jsonl
├── nodes/
│   └── <node_id>.json
├── artifacts/
│   ├── assets/                 # locked white-bg refs (tracked, by sha256)
│   ├── frame_conditions/       # composited first frames (tracked, by sha256)
│   ├── attempts/               # raw Pippit outputs (gitignored)
│   ├── accepted/               # final kept clips (tracked)
│   ├── continuity_anchors/     # last-clear-frame extracts (tracked)
│   ├── baselines/              # SD2 one-shot runs (gitignored)
│   ├── reviews/                # review markdown + score JSON
│   └── frames/                 # extracted key frames (gitignored)
└── schemas/
    ├── node_schema.json
    └── edge_schema.json
```

### Node-type prefixes (v4)

```
intent:    intent_spec
outline:   outline_spec
asset:     character / scene / prop / style (asset_kind discriminator)
review:    layer-tagged review (asset_review / outline_review / clip_review / ...)
storyboard:storyboard envelope (lineage + shot_ids[])
shot:      shot_spec (Layer 3 atom)
frame:     frame_condition (composited first frame)
cont:      continuity_anchor (last-clear-frame)
attempt:   clip_attempt (raw Pippit output)
accepted:  clip_accepted (final kept clip)
audio:     audio_profile (reusable voice timbre / dialect / provider)
job:       service_job (daemon-mode job record)

# v3.5 legacy (back-compat alias only — normalized on write):
brief:     -> intent
sb:        -> storyboard
seg:       -> shot / clip_attempt (context-dependent)
char:      -> asset (asset_kind=character)
loc:       -> asset (asset_kind=scene)
style:     -> asset (asset_kind=style) or outline.global_style_bible
fail:      -> failure_mode (still first-class — see below)
baseline:  -> baseline_run (KEPT)
cmp:       -> comparison (KEPT)
decision:  -> decision (KEPT)
```

### Migration map (v3.5 → v4)

| v3.5 node_type | v4 node_type | migration rule |
|---|---|---|
| `movie_brief` | `intent` | wrap `brief.payload` into `intent_spec.creative_brief`; preserve `target_tier`. |
| `character` | `asset` (`asset_kind=character`) | move `visual_description` + `anchor_frames` to `asset.payload`; status starts `draft` until asset gate locks it. |
| `location` | `asset` (`asset_kind=scene`) | same as character. |
| `segment_attempt` | `clip_attempt` | rename; add `source_shot_id` referencing the v4 shot that produced it. |
| `segment_accepted` | `clip_accepted` | rename; add `source_shot_id` and `continuity_anchor_for_next_shot_id`. |
| `segment_intent` | `shot` (partial) | `shot.composition.start_frame_prompt` absorbs `intent_text`; the rest of `shot_spec` is new. |
| `prompt_bundle` | `frame_condition` + part of `shot.video_generation` | `bundle.message` → `shot.video_generation.prompt`; `bundle.asset_ids` → `shot.video_generation.start_frame_asset_id`. |
| `storyboard` (v3.5 lineage) | `outline` + `storyboard` (v4) | v3.5 `storyboard.lineage` splits into `outline.narrative_beats[]` (story arc, multi-shot scope) + `storyboard.shot_ids[]` (concrete shot order). |
| `style_anchor` | `asset` (`asset_kind=style`) or merged into `outline.global_style_bible` | INTERNAL bookkeeping — NEVER sent to Pippit; consulted by gates only. |
| `continuity_constraint` | merged into `outline.narrative_beats[].must_show` / `must_not_show` | first-class node no longer needed; constraint lives where it is enforced. |
| `failure_mode` | `failure_mode` (KEPT) | still first-class — useful across all layers; v4 adds `layer` field. |
| `baseline_run` | `baseline_run` (KEPT) | unchanged. |
| `comparison` | `comparison` (KEPT) | unchanged. |
| `decision` | `decision` (KEPT) | gate decisions are still first-class. |
| `review` | `review` (KEPT, extended) | adds `gate_kind` field (`intent` / `outline` / `asset` / `frame_condition` / `clip`); legacy clip-only reviews are coerced to `gate_kind=clip`. |

### Edge types (v4)

All v1.1 edges remain valid:

```
contains, continuation_of, retry_of, fork_of, supersedes, contradicts,
supports_narrative, violates_narrative, violates_style, violates_character,
violates_continuity, approved_by_reviewer, rejected_by_reviewer, uses_character,
uses_location, uses_style_anchor, caused_failure_mode, repairs_failure_mode,
baseline_for, compared_against, generated_from, reviewed_by, anchor_for
```

**New v4 edges**:

```
references_asset             # shot → asset (and frame_condition → asset)
composes_from                # frame_condition → asset (multi-ref composition source)
i2v_anchors_to               # clip_attempt → frame_condition
continues_via_last_clear_frame  # shot → continuity_anchor (input) and
                                # continuity_anchor → clip_accepted (source clip)
produced_by_image2           # frame_condition / asset → tool=codex_image2
produced_by_seedance         # clip_attempt → tool=seedance_fast_i2v
produced_by_pippit_native_audio  # clip_attempt → tool=pippit_native (when audio is on)
```

The 11-dim clip review payload object remains in `$defs/review_scores` and is referenced by `review` nodes with `gate_kind=clip`. Gates other than clip use their own rubric blocks (see §5). The legacy `shot_list` field stays removed from the schema — Pippit still does its own shot decomposition (搬运工 v2, §6); internal continuity tracking moved into `outline` and `continuity_anchor` nodes.

---

## 5. Cross-layer adversarial review gates

v1.1 had a single 11-dim review rubric applied at clip time. v4 keeps that rubric for the clip gate and adds smaller, focused rubrics for the four upstream gates. Every gate is fired by `/cross-layer-gate`, parameterized by gate kind, and respects the same reviewer-independence rule.

### Intent gate

Triggered when an `intent_spec` is drafted, before Layer 2 starts.

| Dim | Score 0-5 |
|---|---|
| `completeness` | are user goal, constraints, deliverable type, target tier all present? |
| `clarity` | is each field unambiguous? any phrases that could be read two ways? |
| `scope_feasibility` | given current ARIS-Movie capability (Pippit, codex image-2, length tiers), is this achievable? |
| `safety_flag_coverage` | does the intent flag celebrity likeness, copyrighted IP, or sensitive content categories that need explicit handling? |

**Approve when**: `completeness ≥ 4` AND `safety_flag_coverage ≥ 4`. Anything lower returns `revise` with the failing dim's reason.

### Outline gate

Triggered when an `outline_spec` is drafted, before any asset generation kicks off.

| Dim | Score 0-5 |
|---|---|
| `coverage` | does the outline actually cover everything the intent demanded? |
| `asset_promptability` | for each declared asset, is there enough specification to generate a stable white-bg reference? |
| `identity_lock_feasibility` | can the proposed characters be locked to a single visual identity given current ref-gen capability? |
| `scene_lock_feasibility` | same question for scenes — are they distinct enough to be re-renderable? |
| `audio_plan` | is voice timbre + dialect + dialogue density realistic for Pippit-native audio (§8)? |
| `safety_ip` | any plot beats demanding celebrity likeness, copyrighted character, or off-policy content? |

**Approve when**: `min(coverage, identity_lock_feasibility, scene_lock_feasibility) ≥ 4` AND `safety_ip ≥ 4`.

### Asset gate

Triggered for each asset reference (`/asset-review-loop` invokes the gate per attempt; loop continues until `locked` or budget exhausted).

| Dim | Score 0-5 |
|---|---|
| `identity_lock_satisfied` | does the ref preserve the asset's defining attributes (face, pose, age, costume — or, for scenes, layout + lighting type + era)? |
| `ref_quality` | image-2 output sharp, well-framed, no artifacts? |
| `bg_isolation` | true white background, no halo, no shadow spilling, clean alpha-extractable silhouette? |
| `reuse_readiness` | can this ref be safely composited into multiple frame conditions without per-shot rework? |
| `safety_ip` | does the ref accidentally render a recognizable celebrity / copyrighted figure? |

**Locked when**: `identity_lock_satisfied ≥ 4` AND `ref_quality ≥ 4` AND `bg_isolation ≥ 4`. "准 ×3" lock convention: three independent passes (different reviewer seeds / different cross-model voters) must each emit `approve`. On lock, the asset's `status` flips from `draft` → `locked`, sha256 is committed, and downstream layers may reference it.

### Frame_condition gate

Triggered when `/frame-condition-builder` produces a candidate composite for a shot's start frame.

| Dim | Score 0-5 |
|---|---|
| `refs_present` | are all referenced assets actually visible in the composite (not silently dropped by image-2)? |
| `spatial_correctness` | do the spatial relationships match `shot.composition.spatial_relationships`? |
| `action_freeze_quality` | is the action frozen at the right moment (no motion blur, frame is i2v-able)? |
| `text_preservation` | for any in-frame text whitelisted in the shot spec, is every character correctly rendered? |
| `harmonization_quality` | do the multiple refs look like one coherent scene (consistent lighting / palette / perspective), not a paste-up? |

**Approve when**: `refs_present ≥ 4` AND `spatial_correctness ≥ 4` AND `action_freeze_quality ≥ 4`. If `harmonization_quality < 3`, gate emits `fallback_to_python_collage` instead of `regen` (Route B fallback, §9).

### Clip gate

Triggered for each completed Seedance i2v clip; this is the v1.1 rubric, preserved.

```
1.  narrative_intent       — does this clip convey the intended shot beat?
2.  plot_continuity        — does it follow from the prior accepted clip?
3.  character_arc          — is the character's emotional/situational state coherent?
4.  character_visual       — face / clothes / age / identity stable vs locked asset?
5.  location_consistency   — same spatial / lighting / era / weather as scene asset?
6.  style_consistency      — palette / lens / pacing / typography matches bible?
7.  pacing                 — info density right for the target shot duration?
8.  audio_narration_sync   — voiceover / subtitles / dialogue / SFX align with picture?
9.  artifact_severity      — anatomy / text / motion / flicker (HIGHER is worse, 5 = catastrophic)
10. stitchability          — clean entry/exit for ffmpeg concat?
11. safety_ip              — no celebrity likeness, no copyrighted character?
```

### Verdict thresholds (clip gate)

```
KEEP             ← min(narrative_intent, plot_continuity) >= 4
                   AND no critical artifact_severity (< 4)
                   AND no safety flag (safety_ip >= 4 — HIGHER is BETTER for safety_ip).
                   Style/visual dims (4, 5, 6, 9) contribute when present but do NOT
                   block KEEP when the active reviewer tier did not score them
                   (e.g. lite mode has no Gemini visual scores → those dims are skipped).
RETRY_SEGMENT    ← narrative ok (narrative_intent >= 4) but visual/style/character
                   issues fixable by prompt or frame_condition adjustment.
REWRITE_SHOT     ← narrative_intent < 3 OR pacing < 3 OR shot's frame_condition is
                   structurally wrong (e.g. wrong scene asset); regenerate this shot.
ABANDON_LINEAGE  ← 2-3 consecutive failures with the same root cause within one lineage.
STOP             ← budget exhausted, user halt, or 3+ consecutive abandons.
```

The decision gate (`/cross-layer-gate` in clip mode) MUST tolerate missing dims (treat as "not scored, skip") rather than substituting 0. Substituting 0 was the v1.0 bug that made `balanced` unable to achieve KEEP.

### Reviewer assignment per gate

| Gate | CC | Codex (GPT-5.5 xhigh) | Gemini (auto-gemini-3) |
|---|---|---|---|
| intent | scope sanity (does this match user history?) | ambiguity check (gate verdict) | — |
| outline | narrative arc, beat-asset mapping | coverage gate (does the outline fulfill the intent? is the asset list complete?) | — |
| asset | usage_fit (does this ref serve the outline's purpose for this asset?) | semantic (is the asset's role in the story clearly readable from the ref?) | visual (identity_lock + bg_isolation + ref_quality) |
| frame_condition | composition narrative (does the spatial story read correctly?) | action_freeze gate (is the frozen moment the right narrative beat?) | visual (refs preserved + harmonization + text) |
| clip | narrative / pacing / audio (dims 1, 2, 3, 7, 8) | gate synthesizer (reads structured scores, emits verdict) | visual (dims 4, 5, 6, 9) |

**Reviewer-independence rule (verbatim from v1.1, still mandatory)**: Codex receives only structured input (numeric scores, file paths, structured JSON). It NEVER receives CC's `narrative_notes` prose. The same isolation holds at every gate, not just clip gate. CC's narrative interpretation lives in `review.narrative_notes` for human audit but is firewalled from the cross-model voter.

---

## 6. Pippit 搬运工 v2 stance

v1.1's "搬运工原則" was a *hard* invariant: "the user side does not write content, only conveys it". v3.5's empirical results force a softer, sharper statement.

The v2 stance, locked 2026-05-21 and carried into v4:

> **"We supply the semantic and physical control plane (object contracts, text content, second-by-second timing, screen-text whitelists, forbidden failures, voice timbre, quoted dialogue). Pippit supplies the visual implementation plane (camera selection, lighting, motion blur, depth-of-field rendering, native audio synthesis, lip-sync)."**

### Banned vocab in user-side prompts (unchanged from v1.1)

```
8K, 4K, hyperrealistic, photorealistic, cinematic, cinematic lighting,
50mm, dolly, push-in, lens, shallow depth, bokeh, key light, rim light,
low-key, award-winning, masterpiece, high quality, trending on artstation,
ultra-realistic, professional, tracking shot, whip-pan, close-up, wide shot
```

Anything in this list will conflict with Pippit's own prompt synthesis and silently regress the output. The asset-ref-generator, frame-condition-builder, and shot-prompt-builder all lint their outputs against this list and refuse to ship a prompt containing any banned term.

### Empirical justification

- v3.5 *v2* prompts (rich semantic content, no camera vocab) achieved ~85% OCR text accuracy on the ARIS log lines — significantly better than v3.5 v1 (which followed the v1.1 hard-line "no content" rule and got generic screens with placeholder text).
- v3.5 *v3.5* prompts (image-2 anchor + i2v + text-preservation suffix) achieved **100%** text accuracy across all 289 frames per clip × 3 clips. Pippit caption layer was unreliable but the rendered frames were perfect.
- Both data points empirically refute the v1.1 stance that "the user side may not specify content". They confirm the v2 stance: specify the *what* down to the character, leave the *how* to Pippit.

See `outputs/FINAL_REPORT_v35.md` for the full numbers and the route diagram.

### v4 implication

In v4, the asset library is the spine of the "what". A shot's prompt to Pippit references locked asset IDs (which Pippit sees as start-frame asset_ids) plus a small semantic prose block (dialogue with quotes, voice timbre, ambient action description) — no camera vocab. The `/shot-prompt-builder` is the canonical place where this discipline is enforced.

---

## 7. SKILL.md conventions

All SKILL.md files MUST:

1. **Frontmatter** (YAML):
   ```yaml
   ---
   name: <kebab-case-skill-name>
   description: <one-line trigger description — what user phrases trigger this; ≤220 chars>
   argument-hint: [<arg-name-or-subcommand>]
   user-invocable: true
   allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, Skill, mcp__codex__codex, mcp__codex__codex-reply, mcp__gemini-cli__ask-gemini, mcp__gemini__analyzeFile
   ---
   ```
   Adjust `allowed-tools` to actual usage (don't over-grant).

2. **Body sections** (in this order):
   - `# <Skill Name>` (H1, human-readable)
   - One-line purpose
   - `## Constants` (REVIEWER_MODEL, OUTPUT_DIR, MAX_ATTEMPTS, etc.)
   - `## Workflow` (Phase 0, 1, 2, ... with concrete commands)
   - `## Outputs` (file paths produced)
   - `## Wiki integration` (what nodes/edges this skill writes)
   - `## Errors and fallbacks` (what to do when X fails)
   - `## Inputs/Outputs contract` (machine-readable I/O spec)

3. **Constants conventions**:
   - `REVIEWER_MODEL = "gpt-5.5"` (Codex MCP default)
   - `REVIEWER_BACKEND = "codex"` (override: `oracle-pro`)
   - `OUTPUT_DIR` = stage-specific (e.g. `storyboard-stage/`, `review-stage/`)
   - `WIKI_DIR = "movie-wiki/"`
   - `MAX_ATTEMPTS_PER_SEGMENT = 3`
   - `MAX_LINEAGE_RETRIES = 2`

4. **Wiki integration**: Every skill that mutates state writes to wiki via `python3 movie-wiki/tools/movie_wiki.py <subcommand>` (TODO: tool not yet written; for now use direct JSON file writes following the schema).

5. **Reference style**: Model after `~/.claude/skills/idea-creator/SKILL.md` and `~/.claude/skills/research-wiki/SKILL.md` for tone, depth, and section structure.

---

## 8. Pippit access contract + audio

All skills that call Pippit do so via:

```bash
# Set once per session (user provides XYQ_ACCESS_KEY)
export XYQ_ACCESS_KEY="<your_xyq_access_key_here>"

# Resolve xyq-nest-skill scripts location
XYQ_DIR="$HOME/.agents/skills/xyq-nest-skill"
[ -d "$XYQ_DIR" ] || XYQ_DIR="$HOME/.claude/skills/xyq-nest-skill"

# Submit
python3 "$XYQ_DIR/scripts/submit_run.py" --message "..." [--thread-id ...] [--asset-ids ...]

# Poll
python3 "$XYQ_DIR/scripts/get_thread.py" --thread-id ... --run-id ... --after-seq 0

# Upload reference asset (e.g. start-frame i2v anchor)
python3 "$XYQ_DIR/scripts/upload_file.py" /path/to/frame.png

# Download results
python3 "$XYQ_DIR/scripts/download_results.py" --urls ... --output-dir movie-wiki/artifacts/attempts/ --prefix shot_XX
```

If `XYQ_ACCESS_KEY` is unset, every skill that calls Pippit must **fail fast** with a clear message instructing the user to set it. Never silently fall back to mock data.

### Pippit-native audio integration

Pippit / Seedance generates video WITH audio natively if the submitted message includes:

- **voice timbre** as plain text (e.g. `"soft female mid-range zh"`)
- **dialogue inside quote marks** (e.g. `"让我接手吧。"`)

The Pippit backend reads quoted strings as TTS targets and handles lip-sync where applicable. **No separate TTS API is required** — Gemini's v4-proposal recommendation to build an independent audio pipeline was explicitly rejected in the 2026-05-24 decisions memo.

Example fragment of a shot message body:

```
Voice: soft female mid-range zh.
Dialogue: "让我接手吧。"
```

Wiki schema integration:

- Each shot's `audio.dialogue` field is the per-shot string with quote marks already attached. `/shot-prompt-builder` is the canonical assembler; the quotes are *significant* and must not be stripped during prompt assembly.
- `audio_profile` node stores reusable `voice_timbre` + `dialect` + `provider` and is referenced by `shot.audio.voice_profile_id`. The same audio_profile can be reused across all shots starring the same character, which both saves description tokens and gives the asset gate a single place to lock voice identity.
- Dialogue density should respect `outline.audio_plan.dialogue_density_per_shot_sec`. If a shot's dialogue length exceeds what Pippit can comfortably TTS in the shot's duration, the clip gate's `audio_narration_sync` will flag it (manifesting as truncated speech or compressed lip movement).

### What does NOT belong in the Pippit message

- ❌ Any banned vocab from §6 (camera, lens, lighting words).
- ❌ `style_anchor` content (style refs are internal bookkeeping, never sent to Pippit — they inform asset gen and gate decisions, not the i2v call).
- ❌ End-frame asset IDs (see §14 — Seedance crashes when both start+end keyframes are passed).
- ❌ Pippit caption text from prior runs (caption layer is unreliable per v3.5 findings; trust only the rendered frames).

---

## 9. Cross-model orchestration + image-2 multi-ref

| Model | Access | Default config |
|-------|--------|----------------|
| Claude 4.7 | this conversation / `claude` CLI | (the orchestrator) |
| GPT-5.5 | `mcp__codex__codex` | `model: gpt-5.5` (default from `~/.codex/config.toml`), `model_reasoning_effort: xhigh` |
| Gemini 3 | `mcp__gemini-cli__ask-gemini` | `model: auto-gemini-3` (NEVER `gemini-3.1-pro` directly — see global CLAUDE.md) |
| Gemini visual | `mcp__gemini__analyzeFile` | for analyzing extracted frames |
| gpt-image-2 | `mcp__codex__codex` with `config: {"include_image_gen_tool": true}` | pixel-perfect static frame + multi-ref composite |
| Seedance 2.0 fast | Pippit via `xyq-nest-skill` | i2v animator from start-frame asset |
| Pippit-native audio | Pippit (inline in i2v message) | voice timbre + quoted dialogue; no separate TTS |

**Reviewer independence**: when a skill calls Codex or Gemini to review, it must pass only file paths and structured context (storyboard JSON, shot spec, frame_condition path) — NEVER Claude's own assessment, prose summary, or interpretation. The reviewer must form its own judgment from the raw artifacts.

### Multi-ref first-frame composite via codex image-2

**REFINED 2026-05-24 after 3-round POC (C1/C2/C3)**. The original assumption — that codex `image_gen` has a native multi-image input API (`images[]` / `input_image[]` parameter) — is FALSE. The tool's schema exposes only a `prompt` parameter.

The actually-working mechanism (we call it **Route A'**) is:

```
mcp__codex__codex with config: {"include_image_gen_tool": true, "model_reasoning_effort": "xhigh"}
+ in the prompt, pass full FILE PATHS of each reference PNG
+ explicitly instruct codex to call view_image on each ref FIRST
  (this loads the visual content into the multimodal conversation context)
+ then codex calls image_gen with a text prompt that references "the visible
  reference images in this conversation" + composition spec
+ specify: spatial relationships + must-preserve identities + canvas size + must-avoid list
```

Codex's reasoning chain handles `view_image` followed by `image_gen` sequentially in a single MCP call. The model uses its multimodal context (the viewed images) to influence the generated composite.

**POC empirical validation (3/3 pass, 2026-05-24)**:
- **C1 (3-ref scene)**: char_user_chibi + scene_bedroom + prop_macbook → "researcher at desk in bedroom" composite. All 3 ref identities preserved + harmonized lighting + 16:9 ready.
- **C2 (2-ref + critical screen text)**: char_user_chibi + prop_macbook → "chibi at laptop with 6 ARIS log lines on screen". All 6 lines exact (`[23:59] ARIS wake`, `/idea-creator: 20 candidates`, `novelty-check: 14 filtered`, `pilot: 4xA100 2h`, `experiment: dllm_27jobs`, `result: +6.2 exact-parse`). Identity preserved.
- **C3 (1-ref + abstract new scene)**: char_aris_chibi only → "ARIS chibi in wiki space with floating cards + gold accent on wiki:accept". ARIS pixel/voxel style preserved; abstract scene generated cleanly from text; gold mark exactly on the one specified node.

POC composites preserved at `movie-wiki/assets/composites/poc_shot01_first_frame_v001.png`, `poc_shot02_chibi_laptop_text_v001.png`, `poc_shot03_aris_chibi_wiki_space_v001.png`.

If Route A' fails on a specific shot (Gemini visual review detects identity drift exceeding asset gate threshold, or screen text loses precision under strict 16:9 small-area conditions, etc.), fallback is Route B:

```
Python rembg + PIL collage:
  1. For each ref, rembg to alpha-extract the asset onto transparent canvas.
  2. PIL paste each at the spatial position from shot.composition.spatial_relationships,
     using scene asset as the base background.
  3. Optionally hand the collage to GPT-4o (or codex image-2 again in
     "redraw based on this paste-up" mode) for harmonization (lighting / shadow / palette).
  4. Use the harmonized output as the i2v start frame.
```

The `frame_condition` node records `method`:

```
method ∈ {
  codex_image2_multi_ref,
  python_rembg_pil_collage,
  python_collage_then_gpt4o_redraw
}
```

so we can ablation-compare Route A vs Route B over the first 10+ shots and pick the better default per shot complexity.

### Codex image-2 generation prompt template

The canonical prompt template that `/frame-condition-builder` fills in:

```text
Create the first frame for {{shot_id}} using ONLY the attached reference images.

References:
{{ref_asset_table}}    # e.g. char_X (data_url), scene_Y (data_url), prop_Z (data_url)

Canvas: aspect ratio {{aspect_ratio}}, e.g. 16:9 1280x720.
This is a start-frame condition for image-to-video. No motion blur.

Composition:
{{spatial_relationships}}

Action frozen at frame start: {{start_moment}}

Preserve exactly: {{must_preserve_from_refs}}
Text preservation: {{exact_text_if_any}}
Do not add: {{must_not_add}}

Output a single coherent frame, not a collage, not a contact sheet.
```

The "Output a single coherent frame, not a collage, not a contact sheet" line is load-bearing: image-2 will otherwise often produce a 2×2 grid of variations or a side-by-side comparison when given multiple refs. This explicit instruction has reduced collage-output failures in single-ref calibration tests.

---

## 10. Effort tiers

This section is the **single source of truth** for effort tiers. All skills MUST consult this table; if a skill's local default differs, that is a bug to file against the skill (not against this doc). Follows ARIS shared-references `effort-contract.md`.

| Tier      | Storyboard k | Max attempts | CC | Codex | Gemini frames                              | Codex effort |
|-----------|--------------|--------------|----|-------|--------------------------------------------|--------------|
| `lite`    | 3            | 1            | ✅ | ❌    | 0                                          | medium       |
| `balanced` (default) | 6 | 3            | ✅ | ✅    | 2 (first + last)                           | xhigh        |
| `max`     | 8            | 4            | ✅ | ✅    | 5 (key + first + last)                     | xhigh        |
| `beast`   | 12           | 5            | ✅ | ✅    | 5 + adversarial Codex pass (double-blind)  | xhigh        |

**Why `balanced` includes 2 Gemini frames**: the KEEP verdict (§5) considers style/visual dims when scored. Without ANY Gemini call, `balanced` could not achieve KEEP because the visual dims would always be unscored — and the v1.0 implementation incorrectly substituted 0 for missing dims. Two frames (first + last of a 15s clip) is a cheap way to catch style drift at segment boundaries without the cost of full 5-frame analysis. See C10 in the 2026-05-21 audit.

**Effort vs length tier are orthogonal**: `--target mvp --effort max` is legal (and recommended for first validation runs). `--target longform --effort beast` is the flagship but costly. User overrides via `— effort: max` and `--target longform` independently.

---

## 11. Reference SKILL.md to model after

When writing each new v4 SKILL.md, study these existing ARIS skills first to inherit established patterns:

- `~/.claude/skills/research-pipeline/SKILL.md` — for `/aris-movie` (the orchestrator, including daemon-mode subcommand patterns)
- `~/.claude/skills/research-refine/SKILL.md` — for `/intent-parser` (raw → structured spec with clarification loop)
- `~/.claude/skills/idea-creator/SKILL.md` — for `/movie-outline-creator` (structured brainstorm that produces a ranked candidate set)
- `~/.claude/skills/paper-illustration/SKILL.md` — for `/asset-ref-generator` (image generation with built-in review loop)
- `~/.claude/skills/auto-review-loop/SKILL.md` — for `/asset-review-loop` and `/movie-review-loop` (multi-round adversarial review until convergence)
- `~/.claude/skills/research-wiki/SKILL.md` — for `/movie-wiki` (graph + node ops + query packs + lint)
- `~/.claude/skills/result-to-claim/SKILL.md` — for `/cross-layer-gate` (turn structured review scores into a verdict)
- `~/.claude/skills/peer-review/SKILL.md` — for `/blind-comparison-review` (A/B double-blind protocol)

For the layer-3 skills (`/movie-storyboard-creator-v4`, `/shot-prompt-builder`, `/frame-condition-builder`, `/last-clear-frame-extractor`) there is no direct ARIS analog — they should follow the §7 SKILL.md conventions and reference the v4 schema for their I/O contract.

---

## 12. Continuation strategy via last-clear-frame

v3.5 used a mechanical "extract the last frame of the prior clip" approach: ffmpeg `seek=-1`, take frame N, upload as the next clip's i2v anchor. This frequently produced ugly continuations because Seedance often emits a motion-blurred final frame as the action winds down; using that blurred frame as the next i2v start meant the next clip began with the blur baked in.

v4 deprecates the mechanical approach. `/last-clear-frame-extractor` is the canonical skill. The algorithm uses OpenCV Laplacian variance — a classical measure where higher variance correlates with more edge content, which correlates with sharper frames:

```python
import cv2

def get_last_clear_frame(video_path, blur_threshold=100.0):
    """
    Walk backwards from the last frame; return the latest frame with
    Laplacian variance above blur_threshold.

    Returns (frame, frame_index, variance) or (frame, frame_index, None)
    if no frame met the threshold (fallback path).
    """
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    for i in range(total - 1, 0, -1):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if var > blur_threshold:
            return frame, i, var
    # All blurry — fallback to 10 frames before end (typically still cleaner
    # than the very last frame, which is where Pippit dumps motion blur).
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total - 10))
    ret, frame = cap.read()
    return frame, max(0, total - 10), None
```

### Calibration

`blur_threshold = 100.0` is a sensible default for natural-scene video at 1280×720. The threshold *needs calibration* per Seedance output characteristics:

- Run `/last-clear-frame-extractor --calibrate` over a 5-10 clip pilot batch.
- Collect per-frame variance distributions.
- Pick threshold at the 25th percentile of frame variance across the batch (typical clean frames are well above, blurry tails fall below).
- Persist the calibrated value into `movie-wiki/calibration/last_clear_frame_threshold.json` and have the extractor read from it on subsequent runs.

### Output node

The extracted frame is committed as a `continuity_anchor` node:

```json
{
  "node_type": "continuity_anchor",
  "id": "cont:shot_03_to_shot_04",
  "payload": {
    "source_clip_id": "accepted:shot_03_v1",
    "source_clip_path": "movie-wiki/artifacts/accepted/shot_03_v1.mp4",
    "selected_frame_index": 247,
    "selected_frame_path": "movie-wiki/artifacts/continuity_anchors/shot_03_last_clear.png",
    "variance": 142.7,
    "blur_threshold_used": 100.0,
    "motion_blur_tail_trimmed_sec": 0.42,
    "fallback_used": false,
    "extractor_version": "v1.0"
  }
}
```

Edges:

- `continues_via_last_clear_frame` from the *next* shot to this anchor.
- `anchor_for` from this anchor to the *next* clip_accepted (back-fill on commit).

The next shot's `continuation.condition_source` field references this anchor's `id` and `selected_frame_path`. The Layer-3 storyboard pipeline then either:

1. **Uses the last-clear-frame directly** as the next shot's i2v start (cheapest, no Layer-2 churn).
2. **Composites it with new assets** via `/frame-condition-builder` (when the next shot introduces a new character/prop that wasn't in the prior frame); the last-clear-frame becomes one of the multi-refs.

The `motion_blur_tail_trimmed_sec` field also tells the stitcher (`/segment-stitch-ffmpeg`) how much of the clip's tail to consider "blurry tail" — it can crossfade across that region during concat rather than splicing into a blurry frame.

---

## 13. Multi-ref first-frame composite (frame_condition layer)

§9 documented the *mechanism* (codex image-2 with `include_image_gen_tool`, multi-ref input via data URLs, Route A primary / Route B fallback). This section documents the *node-level* and *gating* contract.

### `frame_condition` node payload

```json
{
  "node_type": "frame_condition",
  "id": "frame:shot_03_v1",
  "payload": {
    "shot_id": "shot:shot_03",
    "method": "codex_image2_multi_ref",
    "composed_from_asset_ids": [
      "asset:char_researcher_locked",
      "asset:scene_lab_night_locked",
      "asset:prop_laptop_80deg_locked"
    ],
    "input_ref_data_urls": [
      "...sha256 references only, not the actual data URLs..."
    ],
    "output_frame_path": "movie-wiki/artifacts/frame_conditions/shot_03_v1.png",
    "output_frame_sha256": "...",
    "aspect_ratio": "16:9",
    "canvas_size": "1280x720",
    "composition_prompt": "...the rendered template from §9...",
    "review_id": "review:frame:shot_03_v1",
    "status": "approved",
    "attempt_number": 1
  }
}
```

Edges:

- `composes_from` from this `frame_condition` to each source `asset` (one edge per ref).
- `produced_by_image2` from this `frame_condition` to `tool=codex_image2`.
- `i2v_anchors_to` from the resulting `clip_attempt` back to this `frame_condition` (back-fill once Pippit returns).

### Gate flow

```
/frame-condition-builder produces candidate frame
       │
       ▼
/cross-layer-gate (gate_kind=frame_condition)
       │
       ├── refs_present       (Gemini visual)
       ├── spatial_correctness (Codex semantic)
       ├── action_freeze_quality (Codex semantic)
       ├── text_preservation  (Gemini visual)
       └── harmonization_quality (Gemini visual)
       │
       ▼
verdict ∈ { approve, regen, fallback_to_python_collage, abandon }
       │
   approve → shot proceeds to Pippit i2v with output_frame_path as asset upload
   regen   → re-prompt codex image-2 with reviewer feedback; bump attempt_number
   fallback_to_python_collage → switch method to python_rembg_pil_collage; re-gate
   abandon → escalate to shot rewrite (clip-side gate verdict REWRITE_SHOT)
```

### Route A' empirical results + why it's primary

**2026-05-24 POC: 3/3 pass** (see §9 for the C1/C2/C3 details). The "native multi-ref API" originally hypothesized as Route A does not exist on codex `image_gen`, but the refined **Route A'** (view_image then image_gen with prompt referencing visible images) is empirically reliable across 1-, 2-, and 3-ref compositions, including the critical case of exact screen-text preservation through composition (C2 preserved all 6 ARIS log lines from a v3.5 anchor pattern).

Why Route A' is the primary path:
- **Single-call coherent harmonization**: image-2 chooses perspective, lighting harmony, scale relationships in one pass. No "pasted-up" look that Route B can produce before its harmonization step.
- **Identity preservation works**: chibi style, character clothing, prop details, scene ambience all survive the composition.
- **Text preservation works** (C2 result): the v3.5-validated property that codex image-2 can render exact text carries through into the 2-ref composite.
- **Method enum stays the same**: `frame_condition.method` continues to record `codex_image2_multi_ref` (the schema-stable name) even though the actual mechanism is "view_image + image_gen text-prompt soft-reference". The enum value is a workflow tag, not an API description.

If pilot shots later show Route A' struggling with N≥4 refs simultaneously, or with strict text preservation when the screen area is small, the gate's `fallback_to_python_collage` verdict transparently switches that *shot* to Route B without disturbing other shots' default. We accumulate evidence and may flip the default at outline-level for shots with high ref count.

### `/frame-condition-builder` workflow contract (Route A' canonical)

```
1. Read shot_spec node → composed_from_asset_ids + composition_prompt + canvas_size.
2. Read each referenced asset node → file_path of each locked ref PNG.
3. Build a single codex MCP call:
   - config: {"include_image_gen_tool": true, "model_reasoning_effort": "xhigh"}
   - sandbox: "workspace-write"  (so codex can save the output PNG)
   - approval-policy: "never"
   - prompt body:
     a. State the goal: "generate first frame for shot:<id>".
     b. List each ref by name + full file path.
     c. EXPLICITLY instruct codex to view_image each ref PNG first.
     d. Provide composition_prompt (spatial relationships, must-preserve, must-avoid).
     e. Specify canvas size (e.g. 1280x720) and aspect ratio.
     f. Specify save path (movie-wiki/artifacts/frame_conditions/shot_<id>_v<NNN>.png).
     g. Demand an honest report: "tell me which refs you successfully viewed and incorporated".
4. Codex internally: view_image x N, then image_gen, then save.
5. Parse codex response for the saved file path + sha256.
6. Write frame_condition node with method=codex_image2_multi_ref, composed_from_asset_ids, output_frame_path, attempt_number.
7. Trigger /cross-layer-gate frame_condition (Gemini visual review for ref presence + text preservation + harmonization).
8. On gate approve → upload to Pippit (xyq-nest-skill upload_file.py), record asset_id in shot.start_frame_asset_id.
9. On gate fallback_to_python_collage → switch method to python_rembg_pil_collage and re-run from step 4.
```

---

## 14. End-frame prohibition (CRITICAL)

Pippit / Seedance MUST NEVER receive both `start_frame` AND `end_frame` asset IDs in the same i2v call.

### Symptom of violation

Middle frames collapse erratically: the model tries to interpolate between two keyframes and, in practice, produces 1-3 seconds of clean motion from each end with a chaotic middle section featuring identity drift, exploded geometry, or warping artifacts. The clip is unrecoverable at the frame level; only retry without the end frame works.

### Rule

- The Pippit `--asset-ids` parameter MUST receive at most one asset ID per shot, and that asset MUST be the `frame_condition`'s output (the start frame).
- Optional intermediate guide frames MAY be stored in `shot.intermediate_guide_ids[]` with explicit `policy: "optional_reference_only_not_end_keyframe"`. They serve as:
  - Internal CC / Codex review material (so reviewers can see the intended midpoints when judging plot continuity).
  - Second-pass reference for future Seedance API versions that may support multi-keyframe input safely.
  - But NEVER passed as `--asset-ids` simultaneously with the start frame in the current Pippit contract.

### FireRed AI transition note

FireRed-OpenStoryline's AI Transition feature does use both first+last frames of *adjacent clips* to synthesize transition footage. This is a **post-stitch** operation on already-rendered clips, not a main-generation strategy. v4 ARIS-Movie may eventually adopt a similar post-stitch transition tool (it would live alongside `/segment-stitch-ffmpeg`), but that tool is out of scope for the v4 launch and is explicitly NOT how shots are generated.

### Enforcement

- `/shot-prompt-builder` lints `video_generation.asset_ids` for length-1 and refuses to assemble a message with multiple start/end asset IDs.
- The Pippit access contract (§8) snippet in skill code MUST pass `--asset-ids <single_id>` and not concatenate guide IDs.
- The clip gate's `artifact_severity` dim weights "middle-frame collapse" as 5 (catastrophic), so a violation is caught at the latest by clip review even if upstream enforcement somehow fails.

---

## 15. ARIS background service mode

v3.5 was a foreground-only pipeline: user kicks off `/aris-movie`, watches it run, decides at each gate. v4 introduces `daemon` mode for long-running, sleep-time, or working-while-it-runs scenarios.

### Use case

> "ARIS runs while user works on a deadline."

A `longform` (150-180s, 10-12 shots) production at `effort: max` requires ~2 hours of Pippit time + ~5 min of image-2 + several rounds of cross-model review. The user typically does not want to sit through that. Daemon mode enqueues the job, persists state, runs asset generation in parallel where possible, runs Pippit i2v serially (rate limit), and pings the user at human-checkpoint events (e.g. budget overrun, repeated abandon).

### Subcommands

```
/aris-movie daemon start [--max-credits N --max-parallel-image-gen K]
/aris-movie enqueue <intent_spec_path>
/aris-movie status                  # list all jobs + progress + ETA
/aris-movie resume <job_id>         # resume after a manual checkpoint
/aris-movie cancel <job_id>
/aris-movie watch <job_id>          # tail the per-job log
```

### State persistence

Two layers:

1. **SQLite queue** at `outputs/aris_movie_jobs.sqlite`. Schema:
   - `jobs(job_id PK, intent_spec_path, status, target_tier, effort, created_at, updated_at, budget_credits_max, budget_credits_used)`
   - `job_events(event_id PK, job_id FK, ts, layer, gate_kind, verdict, payload_json)`
   - `job_artifacts(artifact_id PK, job_id FK, kind, path, sha256, committed_to_wiki BOOL)`

   The queue is queryable from any other Claude Code session and survives daemon restarts.

2. **Per-job JSON** at `outputs/jobs/<job_id>/state.json` for human readability and debugging. Mirror of the SQLite job row plus the latest event log, written atomically every gate.

### Parallelism model

| Operation | Concurrency | Reason |
|---|---|---|
| codex image-2 calls (asset gen, frame_condition composite) | parallel up to `--max-parallel-image-gen` (default 4) | codex MCP handles concurrent calls; image-2 is the slow upstream |
| Cross-model review calls (gate evaluation) | parallel per gate | reviewers are independent by construction |
| Pippit i2v submissions | **serial per account** | rate limit on the Pippit account; queueing N i2v calls in parallel triggers backoff or auth issues |
| Pippit polling | parallel | polling is cheap and the rate limit is per-submit, not per-poll |
| Wiki commits | serial per job | avoid edge-list write contention |

### Budget management

- Each job has `budget_credits_max` (default: derived from target tier — mvp 600, demo 2500, longform 6500).
- The daemon tracks `budget_credits_used` after each Pippit run; if remaining < expected-next-shot-cost, the job enters `paused_budget` state.
- `paused_budget` is a **human checkpoint**: daemon notifies the user (`/aris-movie status` shows the pause), and `/aris-movie resume <job_id>` only proceeds with explicit confirmation (and an optional `--bump-budget +N` flag).

### Failure handling

- Transient errors (Pippit timeout, codex MCP transient) auto-retry up to 3 times with exponential backoff.
- Non-transient errors (auth failure, budget overrun, schema validation fail) pause the job and notify.
- Daemon crash is recoverable: on restart, scan SQLite for `status IN ('running', 'pending')` jobs and resume from the last committed gate.

### Integration with main `/aris-movie`

The synchronous `/aris-movie "<intent>"` invocation still works for short interactive runs. `/aris-movie daemon` is layered on top: it uses the same skills internally, just plugs them into the queue runtime and writes events to SQLite instead of streaming to the foreground conversation. Skills MUST NOT need a code change to run under daemon mode — the daemon takes the same SKILL.md output and routes it.

---

## 16. The spiral patch (v2.1): assembly gate + rollback + active failure_mode

**Why this section exists**: v4 (v2.0 of this doc) shipped with 5 per-step gates (intent / outline / asset / frame_condition / clip) and 4 forward verdicts (`keep / retry_shot / rewrite_shot / abandon_shot / stop`). User 2026-05-26 audit caught that this is too forward-linear — ARIS's spiral spirit (generate → review → discover → regenerate from earlier point + wiki as active memory) was missing. v2.1 adds 3 things:

1. **`multi_shot_assembly_gate`** (new skill) — reviews stitched partial preview every K shots / at narrative-beat boundaries / before final stitch
2. **`rollback_to_shot`** + `rewrite_storyboard_from` verdicts — clip-side and assembly-side gates can discard a tail of accepted clips and regenerate from an earlier shot
3. **Active `failure_mode` use** — every shot creation queries wiki failure_modes; the matches enter the Codex prompt as banlist AND as **positive invariants** that get injected into the Pippit message

### 16.1 When the assembly gate fires (hybrid trigger)

Codex argued for fixed stride (`K=3` for longform); Gemini argued for adaptive (narrative beat + cheap visual seam check). The synthesis is **hybrid**:

| Trigger | Cost | What it runs |
|---------|------|--------------|
| **Cheap seam check** (every shot boundary, mandatory) | 1 Gemini visual call (~20s) on `last_clear_frame(K) + first_frame(K+1)` 2-frame grid | Detect adjacent-shot drift only (character/scene/palette). On drift detected → escalate to full assembly gate. |
| **Narrative-beat boundary** (storyboard explicitly marks the end of a beat in `outline.narrative_beats[].beat_id`) | Full assembly gate (CC narrative + Gemini 8-dim visual + Codex synth) | Reviews all shots within the just-completed beat as a unit. |
| **Stride safety net** (if no beat boundary triggered for 3 consecutive shots) | Same as beat-boundary | Catches drift in beats with too many shots / no internal boundary. |
| **Final assembly gate** (always before `/segment-stitch-ffmpeg`) | Same | Reviews the full active chain end-to-end. The only gate that can emit `final_accept`. |
| **Repair check** (after a `rollback_to_shot` is resolved + 1 follow-up shot reaches `clip_gate keep`) | Same, narrowed to `[rollback_target, rollback_target+1]` | Verifies the rollback actually fixed the issue before resuming forward. |

For `mvp` (2 shots) the seam check + final assembly gate is enough; the beat-boundary and stride triggers naturally produce zero extra checkpoints. For `demo` (4-6 shots) expect ~1 mid-storyboard full assembly. For `longform` (10-12 shots) expect 3-4 full assemblies + 9-11 seam checks.

### 16.2 Assembly gate skill: `/multi-shot-assembly-gate`

Reasons it's a separate skill (not folded into `/cross-layer-gate`):
- Its input is an *active accepted clip chain*, not a single target node — different state model
- It owns its own ffmpeg-preview construction, sample frame extraction, and rollback bookkeeping — more complex than a score fuser
- It must be able to invoke `/cross-layer-gate` for the rolled-back shot's clip_gate to re-fire after regeneration

Reviewer division of labor (Gemini's split, which is better here than the per-shot split):

- **CC reads text-only** (no video). Inputs: storyboard JSON, outline beat structure, each shot's `audio.dialogue` + `composition.start_frame_prompt`, optional per-shot accepted clip metadata (duration, sequence). Output: `cc_narrative_assembly_scores` (7-dim, see §16.4) + suspect_shot_indices.
- **Gemini handles all visual** (her exclusive domain). Inputs: stitched preview mp4 + 3-frame-per-shot grid + boundary frames + locked asset refs. Output: `gemini_visual_assembly_scores` (8-dim, see §16.4) + **Point of Divergence (PoD)** — the specific shot where visual drift first becomes irrecoverable.
- **Codex synthesizes** + emits the verdict. Inputs: structured scores only (NOT CC/Gemini prose — reviewer independence preserved). Reads: failure_mode candidates for compilation. Output: verdict + `rollback_target_shot_id` (if rollback) + new `failure_mode` nodes.

### 16.3 Verdict enum extension (schema-stable shape)

Decision verdict adds these enum values (per `node_schema.json` v2.0 + v2.1 patch):

```
continue_forward        # assembly OK, proceed to next shot
rollback_to_shot        # specific earlier shot needs redo (target_shot_id is a separate data field, NOT in verdict string)
rewrite_storyboard_from # storyboard from K+ needs redesign, escalates to outline_gate
final_accept            # only emitted by final assembly gate; clears the pipeline for /segment-stitch-ffmpeg
escalate_to_human       # rollback budget exhausted or unrecoverable; pause + ask user
```

Decision payload gains fields:
- `gate_kind`: enum (intent | outline | asset | frame_condition | clip | assembly | storyboard)
- `rollback_target_shot_id`: string (only for `rollback_to_shot`)
- `rollback_target_sequence_index`: integer
- `rewrite_from_shot_id`: string (only for `rewrite_storyboard_from`)
- `rewrite_from_sequence_index`: integer
- `invalidated_clip_ids`: array (clips marked superseded by this decision)
- `frozen_prefix_clip_ids`: array (clips before rollback target, kept as-is)
- `root_failure_mode_ids`: array (failure_mode nodes implicated)
- `assembly_attempt_id`: string (the preview the assembly gate reviewed)

### 16.4 Cross-shot rubrics (new $defs)

**`cc_narrative_assembly_scores` (CC, 7 dims, 0-5 each)**:
1. `beat_order_fidelity` — does the assembly follow outline.narrative_beats[] order?
2. `causal_continuity` — does shot K's action/info naturally lead to shot K+1?
3. `character_state_continuity` — character's goal/emotion/possession track across shots?
4. `transition_legibility` — can viewer parse the K→K+1 transition?
5. `pacing_rhythm` — information density / pauses / repetitions feel right?
6. `setup_payoff_alignment` — earlier setup supports later payoff?
7. `gap_or_redundancy_absence` — no missing bridges, no redundant beats?

**`gemini_visual_assembly_scores` (Gemini, 8 dims, 0-5 each, per Gemini's strong opinion 2026-05-26)**:
1. `entity_identity_preservation` — same chibi looks same across shots (esp. across scene cuts)
2. `spatial_geometry_anchoring` — room layout / background props stable in their 3D positions
3. `axis_180_compliance` — no axis-of-action violations between adjacent shots
4. `motion_vector_handoff` — shot K's motion direction at end matches shot K+1's start
5. `lighting_palette_persistence` — color temperature + key light direction stable
6. `pacing_temporal_rhythm` — shot duration distribution serves the narrative arc
7. `hallucination_suppression` — no cumulative artifacts (extra limbs, floating objects)
8. `transition_intent_alignment` — shot scale changes (wide→close-up) serve intent

**Threshold**: any dim < 2 OR (sum of CC 7 dims + Gemini 8 dims) < 60 (out of 75) → mandatory rollback. The exact threshold can be loosened by `--effort beast` (allow 55) or tightened by `--effort lite` (require 65).

### 16.5 Rollback bookkeeping (default: discard K through current)

When `rollback_to_shot` is emitted with `rollback_target_sequence_index = K`:

1. **Write `assembly_attempt:<id>` node** — records preview mp4 path, clip list reviewed, sample frames, review_node_ids
2. **Write `decision:<id>` node** — target = assembly_attempt, with all the new payload fields (gate_kind, rollback_target, invalidated_clip_ids, etc.)
3. **Write/update `failure_mode:<id>` node(s)** — Codex compiles failure modes per Gemini's PoD finding. Encoding style: **positive_invariant** (Gemini's insight — "force fluffy ears with backlight" not "no missing ears")
4. **Mark `clip_accepted` nodes K through current** as `status: superseded` (NOT deleted — they remain as wiki audit trail and as negative training samples)
5. **Mark `continuity_anchor` nodes from those clips** as superseded
6. **Freeze the prefix** (clips 0..K-1) — those are immutable for this rollback round
7. **Reset orchestrator state** to `phase_cursor.sequence_index = K`, `attempt_index = 0`, increment `rollback_count_for_shot[K]`
8. **Add edges**:
   - `rollback_targets`: decision → shot (the target shot to redo)
   - `rollback_invalidates`: decision → each invalidated clip_accepted + continuity_anchor
   - `rollback_supersedes`: new clip_accepted (after redo) → old superseded clip_accepted (back-fill on next acceptance)
   - `consulted_failure_mode`: shot → failure_mode (when shot's regeneration queries the mode)
   - `violates_failure_mode`: candidate shot/prompt → failure_mode (when validator catches a near-repeat)

### 16.6 Loop prevention (strikes + hard caps)

Combining Codex's numerical caps with Gemini's strike escalation:

| Strike | Trigger | Response |
|--------|---------|----------|
| **Strike 1** (first rollback to shot K) | rollback_to_shot emitted for shot K | Apply repair_pattern from new failure_mode as positive invariant in the regeneration prompt. Try once. |
| **Strike 2** (second rollback to same shot K with same root failure_mode) | Same shot_id, same mode_name | Force a different generation strategy: change Pippit seed/run randomness, switch frame_condition method (Route A' → Route B fallback), or add new refs. |
| **Strike 3** (third rollback to same shot K, same root cause) | Same shot_id, same mode_name 3rd time | Auto-escalate to `rewrite_storyboard_from K` — the shot itself cannot be filmed under current outline. Triggers outline_gate review. |

Hard caps (Codex):
- `MAX_ROLLBACKS_PER_SHOT = 2` (Strike 3 = escalation, not another rollback)
- `MAX_ROLLBACKS_PER_RUN = 3` (overall budget per `/aris-movie` invocation; longform-beast can override to 5)
- After all rollback budget exhausted → `escalate_to_human` verdict + daemon human checkpoint

### 16.7 Active failure_mode use (positive invariants)

The current `failure_mode` schema is too thin (just `mode_name + description + repair_pattern`). v2.1 extends it (see `node_schema.json` v2.1 patch). Key new fields:

- `encoding_style`: enum (`positive_invariant` | `negative_pattern`) — Gemini's recommendation: prefer positive_invariant because "don't show 3 hands" makes diffusion models focus on 3 hands. Encode as "force visible 2 hands holding the laptop" instead.
- `layer`: enum (asset | shot | prompt_pattern | visual_transition | global)
- `scope`: enum (movie_local | engine_global) — engine_global failures (e.g. "Seedance fast struggles with rapid pan motion") promote to MEMORY-level lessons that persist across movies
- `severity` 0-5 + `confidence` 0-1
- `affected_asset_ids` + `affected_shot_ids` + `trigger_patterns` + `negative_prompt_fragments` + `semantic_signature` (asset_ids + keywords + composition_terms + prompt_fragments for matching)
- `occurrence_count` + `first_seen_at` + `last_seen_at` (for recency/frequency weighting)

Active use:

**At `/movie-storyboard-creator-v4` Phase 0.5**:
```bash
movie_wiki.py failure-banlist --outline <outline_id> --asset-ids ... --target-layer storyboard --limit 20
```
Generates `storyboard-stage/_failure_banlist.json`. The Codex shot-generation prompt is instructed:
> For each shot slot, consult its failure banlist. Do not propose composition.must_preserve_from_refs, must_not_add, start_frame_prompt, or video_generation.prompt patterns that overlap with active failure modes. If unavoidable, include the failure mode's repair_pattern (encoded as positive_invariant) explicitly in the shot's prompt.

**Validator (Phase 3 in storyboard-creator-v4)**:
- For each proposed shot, compose a candidate_signature from {scene_asset_id, character_asset_ids, prop_asset_ids, composition.must_preserve_from_refs, start_frame_prompt, video_generation.prompt, audio.dialogue}
- Match against active failure_modes using **hybrid D+B+A** (Codex's recommendation, since v2.1 doesn't have embedding infra):
  - **D (cheap)**: Codex prompt receives banlist as plain text; Codex respects it during generation
  - **B (structural)**: keyword/asset-overlap scanner; weight by mode.severity * recency
  - **A (semantic, only when B flags ≥0.55)**: dedicated Codex call to judge whether the proposed shot truly repeats the failure
- Score ≥ 0.75 → hard fail, regenerate shot. 0.55-0.75 → soft warn, Codex attempts repair. <0.55 → pass.
- Embedding-based matching (Gemini's preferred Option C) is **deferred to v2.2** — needs embedding cache infra.

**At `/shot-prompt-builder`** (Pippit message construction):
- Read active failure_modes scoped to this shot
- Inject each matched mode's `repair_pattern` (positive_invariant) into the Pippit message as a hard constraint
- After composing the message, scan it against `trigger_patterns` of all active modes — if any match, re-write the message segment OR fail with `regenerate_shot` signal to the orchestrator

### 16.8 Contract bug fix: `--gate storyboard`

Codex caught this during v2.1 design: `/movie-storyboard-creator-v4` Phase 5 calls `/cross-layer-gate <storyboard_id> --gate storyboard`, but `/cross-layer-gate` and §5 only declare 5 gate types (intent | outline | asset | frame_condition | clip). Fix:

- Add `storyboard` to the `gate_kind` enum
- Add the storyboard rubric to `/cross-layer-gate` (4-dim: shot_assets_referenceable / global_policies_valid / shot_count_target_aligned / continuity_chain_well_formed)
- Note that `storyboard` gate is a *structural* gate (does the storyboard JSON make sense?), distinct from `assembly` gate (do the rendered clips together make sense?)

### 16.9 Integration with `/aris-movie` Phase 2 (updated pseudocode)

```python
active_chain = []
rollback_counts = {}     # shot_id → strike count
rollback_count_run = 0
last_assembly_checkpoint = 0

for i in range(resume_index, len(storyboard.shot_ids)):
    shot = load_active_shot(i)

    while True:  # per-shot retry loop
        # 1. Build frame condition (Route A' or B fallback)
        frame = build_frame_condition(shot)
        if cross_layer_gate(frame, gate="frame_condition").verdict != "approve":
            continue

        # 2. Build Pippit message with failure_mode positive invariants injected
        prompt = shot_prompt_builder(
            shot,
            failure_banlist=query_failure_modes(shot, target_layer="prompt_builder"),
        )

        # 3. Pippit i2v
        attempt = submit_pippit_i2v(shot, frame, prompt)
        clip_decision = cross_layer_gate(attempt, gate="clip")

        if clip_decision.verdict == "keep":
            accepted = commit_clip_accepted(attempt)
            extract_last_clear_frame(accepted)
            active_chain.append(accepted)
            break  # shot done, exit retry loop
        if clip_decision.verdict in ["retry_shot", "rewrite_shot"]:
            handle_retry_or_rewrite(clip_decision)
            continue
        if clip_decision.verdict == "rollback_to_shot":
            # clip_gate can only roll back to current-1; deeper rollbacks must come from assembly_gate
            handle_rollback(clip_decision)
            i = clip_decision.rollback_target_sequence_index
            break
        if clip_decision.verdict in ["abandon_shot", "stop"]:
            return pause_or_escalate(clip_decision)

    # 4. Cheap seam check at every shot boundary (after shot 0 has a successor)
    if i > 0 and len(active_chain) >= 2:
        seam_decision = seam_check_gate(
            prev_clip=active_chain[-2],
            curr_clip=active_chain[-1],
        )
        if seam_decision.drift_severity >= 3:
            # escalate to full assembly gate
            run_full_assembly = True
        else:
            run_full_assembly = False
    else:
        run_full_assembly = False

    # 5. Full assembly gate (beat boundary OR stride safety net OR seam check escalation)
    is_beat_end = (i == len(storyboard.shot_ids) - 1) or \
                  (shot.beat_id != load_active_shot(i+1).beat_id)
    is_stride_floor = (i - last_assembly_checkpoint >= 3)
    if run_full_assembly or is_beat_end or is_stride_floor:
        assembly = build_assembly_attempt(
            active_chain[last_assembly_checkpoint:i+1],
            scope="rolling",
            beat_id=shot.beat_id if is_beat_end else None,
        )
        a_decision = multi_shot_assembly_gate(assembly)

        if a_decision.verdict == "continue_forward":
            mark_assembly_checked(active_chain[last_assembly_checkpoint:i+1], assembly)
            last_assembly_checkpoint = i + 1
            continue
        if a_decision.verdict == "rollback_to_shot":
            target = a_decision.rollback_target_sequence_index
            strikes = rollback_counts.get(target, 0) + 1
            rollback_counts[target] = strikes
            if strikes > MAX_ROLLBACKS_PER_SHOT:
                # auto-escalate to rewrite_storyboard_from
                a_decision = escalate_to_rewrite_storyboard(a_decision)
            rollback_count_run += 1
            if rollback_count_run > MAX_ROLLBACKS_PER_RUN:
                return human_checkpoint("rollback budget exhausted")
            handle_rollback(a_decision)
            active_chain = active_chain[:target]
            last_assembly_checkpoint = min(last_assembly_checkpoint, target)
            i = target - 1  # outer loop will increment to target
            continue
        if a_decision.verdict == "rewrite_storyboard_from":
            handle_rewrite_storyboard(a_decision)
            storyboard = movie_storyboard_creator_v4(
                outline_id,
                revise_from=a_decision.rewrite_from_shot_id,
                failure_context=a_decision.root_failure_mode_ids,
            )
            active_chain = active_chain[:a_decision.rewrite_from_sequence_index]
            i = a_decision.rewrite_from_sequence_index - 1
            continue

# 6. Final assembly gate (mandatory before stitch)
final_assembly = build_assembly_attempt(active_chain, scope="final_full")
final_decision = multi_shot_assembly_gate(final_assembly)
if final_decision.verdict != "final_accept":
    return route_final_assembly_failure(final_decision)

segment_stitch_ffmpeg(active_chain)
```

### 16.10 v2.1 semantic shift summary

The single most important semantic change introduced by v2.1:

> **`clip_gate keep` no longer means "permanently accepted". It means "locally acceptable, pending assembly review." The only state that means "permanently in the final cut" is when the clip's parent assembly_attempt has `final_accept` from the final assembly gate.**

Skills that consume `clip_accepted` nodes (most notably `/segment-stitch-ffmpeg`) must check `acceptance_stage` and only stitch clips at `final_accepted` (or `assembly_checked` for partial preview).

---

## Changelog

- **v2.1** (2026-05-26): the **spiral patch** (§16). Adds real ARIS-style rollback + active wiki memory to the otherwise forward-linear v4. New skill `/multi-shot-assembly-gate`; new verdicts `continue_forward`, `rollback_to_shot`, `rewrite_storyboard_from`, `final_accept`, `escalate_to_human`; extended `payload_decision` with `gate_kind` + rollback target fields; extended `payload_failure_mode` with active-use fields (encoding_style=positive_invariant, layer, scope, severity, semantic_signature, occurrence_count); extended `payload_clip_accepted` with `acceptance_stage` enum; new node type `assembly_attempt`; new $defs `cc_narrative_assembly_scores` (CC 7-dim) + `gemini_visual_assembly_scores` (Gemini 8-dim per her 2026-05-26 specialist proposal). Trigger strategy is hybrid (cheap seam check at every boundary + full assembly at narrative-beat boundaries + stride-3 safety net + mandatory final assembly before stitch). Loop prevention combines strike escalation (Gemini) with hard caps (Codex). Failure_mode use is hybrid D+B+A matching (embedding-based deferred to v2.2). Contract bug fixed: `storyboard` is now a declared gate_kind. Critical semantic shift: `clip_gate keep` no longer means "permanently accepted" — only `assembly_gate final_accept` means a clip is in the final cut.
- **v2.0** (2026-05-24): full v4 framework redesign — 3-layer architecture (intent / outline / storyboard), asset library as first-class wiki node, multi-ref first-frame composite via codex image-2, Pippit-native audio (voice timbre + quoted dialogue), last-clear-frame continuation via Laplacian variance, no end-frame condition (Seedance crashes when both start+end keyframes given), ARIS background service mode via `/aris-movie daemon`. FireRed-OpenStoryline reference informed the layered approach; Pippit 搬运工 v1 stance demoted from hard invariant to "ban camera vocab, require semantic detail". Codex GPT-5.5 xhigh + Gemini auto-gemini-3 dual review backed every decision. v3.5 state preserved at `v3.5-final` git tag.
- **v1.1** (2026-05-21, doc-side patch — version line still reads v1.0): post-audit fixes by Subagent F.
  - **C7**: verdict short forms (`retry`/`rewrite`/`abandon`) replaced everywhere with full enum forms (`retry_segment`/`rewrite_storyboard`/`abandon_lineage`); state-machine diagram + node-type table now match `node_schema.json`.
  - **C9**: `node_schema.json` rewritten with `$defs` + per-`node_type` `oneOf` branches; every node type now has a machine-validated required+optional payload contract. The §4 node-types table is downgraded to a human summary and explicitly defers to the schema.
  - **C10**: §5 verdict thresholds rewritten — `balanced` can now achieve KEEP because (a) the §10 tier table now gives `balanced` two Gemini frames, and (b) the gate tolerates missing dims instead of substituting 0.
  - **C11**: §5 `artifact_severity` reversed to "higher is worse, 5 = catastrophic" (matches the schema and the skill implementations).
  - **M1**: §10 declared the single source of truth for effort tiers; effort vs length tier orthogonality made explicit.
  - **Length tiers**: added §0.5 with the canonical `mvp` (30s, 2 segments) / `demo` (90s, 4-6 segments) / `longform` (150-180s, 10-12 segments) table; `MAX_BEATS_PER_LINEAGE` is parameterized per tier and threaded via `--target` from `/aris-movie` → `/movie-storyboard-creator`.
- **v1.0** (2026-05-21): initial spec — locked architecture, 13 skills, 11-dim rubric, 5-state gate, Pippit 搬运工原則.
