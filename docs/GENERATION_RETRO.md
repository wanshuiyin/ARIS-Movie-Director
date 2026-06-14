# ARIS-Movie-Director — Generation Retro (empirical, the 24-panel comic run)

This is the ground-truth record of what actually happened while generating the reference comic
(`examples/comic_m3_audit/`, 24 panels / 19 pages) end-to-end through the spiral engine. It exists so a
reviewer can judge whether the FRAMEWORK (not the comic) needs changes before a public release.

## What the framework is (one paragraph)
A per-panel "spiral" generator (`packages/core/spiral_engine.js`, run via the Workflow tool). Per panel:
author a deterministic content-SVG blueprint → render to PNG → `codex image_gen` bakes a narrative
pixel-art panel from 2 refs (blueprint + identity ref) → a 3-reviewer panel_gate (Claude narrative ‖
Gemini visual CLI ‖ Codex visual CLI → a DETERMINISTIC JS verdict: blind `observed_literals` transcribed
by both visual reviewers, JS token-diffs them against authored `expected_literals`; `content_corruption`
is a single-vote veto) → write wiki nodes (attempt/review×3/decision/failure_mode) → keep / retry /
cross-frame rollback (bounded: 4 attempts/panel, 6 rollbacks/run, then flag-for-human) → a page
assembly_gate. Output: PNGs + a `comic.json` projection + a single-file clickable HTML viewer.

## Empirical generation stats (extracted from the 174 wiki nodes)
- 24 panels, **33 total attempts**, 18 first-try keeps, **6 panels needed retries**.
- Retry counts: **S10×4** (hero {"city":"Tok|yo"} crack + json.loads→ParseError + 0.66 — the hardest
  literal set), S03×3 (cross-frame false-drift, see below), S01/S09/S13/S17 ×2.
- S10 a01/a02/a03 were each vetoed by **content_corruption_present=true from BOTH codex and gemini**
  (garbled baked text) — the deterministic veto worked exactly as designed and drove 3 re-bakes.
- Every attempt has a full 3-reviewer record (cc/codex/gemini) with blind observed_literals + 5-dim
  scores; every decision records verdict + reasoning + repair_instruction; rejected attempts have a
  failure_mode node with a repair_pattern. The trace is substantive, not placeholder.

## Incidents that happened during the run (the real stress tests)
1. **`args` arrives as a JSON STRING, not an object.** The Workflow runtime delivers the `args` input
   to the script as a string. An early run read `args.page` (undefined) and silently re-baked the wrong
   page (clobbered 4 finished B08 panels). FIXED with an ARGS normalizer at the top of the engine
   (JSON.parse-with-fallback). This was a major hidden bug; every run before the fix was at risk.
2. **Cross-frame assembly FALSE drift.** B03 is a parallel 2-up with DISJOINT casts (S03 researcher-only
   / S04 duo-only). The assembly reviewer scored "duo identity across panels" = 0 where no duo exists,
   producing IDENTICAL min=0 scores across two re-bake rounds (the fingerprint of a broken rubric, not a
   broken artifact). The bounded loop correctly stopped + flagged human. FIXED: assembly is now
   CAST-AWARE (reviewer receives each panel's intended cast + all page identity refs; absence-of-a-
   character ≠ drift, warm/dark world contrast ≠ drift). Human override recorded as a wiki decision node.
3. **Two image_gen throttles mid-run** (B10/B11 at S17, B12 at S20). The deterministic failure_kind
   classifier caught the throttle, stopped cleanly (shippable=false, escalated), no infinite loop. Manual
   cooldown-probe (poll image_gen every 25–30 min, resume on recovery) cleared both. KEY GOTCHA:
   `resumeFromRunId` CANNOT be used after a throttle — the cached throttle result replays and instantly
   "throttles" again; a FRESH run is required. This is undocumented and easy to get wrong.
4. **Concurrent-bake cross-pollution risk.** `codex image_gen` writes to a GLOBAL dir
   (`~/.codex/generated_images`) and the engine picks up the mtime-newest PNG. Running two bakes
   concurrently would let them grab each other's images. Currently handled ONLY by operator discipline
   (never launch two bakes at once) — there is NO code-level lock or per-run temp dir.
5. **Disconnect mid-run** killed in-flight agents once ("agent stalled on all attempts"); recovered via
   Workflow resume (resumeFromRunId) — the unchanged-prefix cache made S01 a 100% cache hit.
6. **Asset filename collision = silent run-order downgrade.** Two generators wrote the same path
   `wandb_exact_parse_060_071_v1.svg` with different content: `gen_core_assets.py` (a generic single-line
   chart) and `gen_b06_blueprints.py` (the richer two-series S08 "UPGRADE"). With no run-order script,
   whoever ran last won — re-running `gen_core_assets.py` after the upgrade silently reverted S08's chart
   to the wrong version (caught only because git-LFS flagged the working-tree diff; nobody had edited it).
   This is the same "re-run breaks it" class as incident 1. FIXED (option A+): removed the dead duplicate
   so `gen_b06` is the sole owner, and added `gen/check_asset_collisions.py` — a static linter that fails
   fast if ANY filename is written by >1 generator (NOT a "skip if exists" guard, which would hide the
   order bug). Enforces "one visual dialect, never two" at the file level. Cross-model adjudicated (codex
   gpt-5.5 xhigh).

## Known weaknesses still standing (candidates for release)
- **Wiki timestamps are placeholders.** `Date.now()`/`new Date()` are unavailable in the workflow
  sandbox (they'd break resume determinism), so all 174 nodes share one of two hardcoded dates. The
  "temporal trace" is really an attempt-id ordering, not a real timeline. A real timestamp could be
  passed in via `args` at launch and stamped onto nodes.
- **Single-file viewer is 55.8 MB** (24 base64-inlined PNGs). Will be slow on GitHub Pages and near
  per-file limits. No compressed / external-image variant exists yet.
- **No release gate.** No LICENSE, no AI-image-generation disclosure/rights note, no quickstart README,
  no redaction pass for absolute paths / usernames embedded in committed JSON/scripts.
- **Concurrency is unenforced** (see incident 4) — a footgun for anyone who runs the engine in parallel.
- **Throttle/resume foot-gun** (incident 3) is operator-knowledge, not encoded anywhere.

## The question for the reviewer
Given the above empirical record, what changes to the FRAMEWORK (engine, wiki schema, viewer, docs,
release hygiene) are worth making before a public release — ranked by leverage? Distinguish "must fix
before release" from "nice-to-have." Be concrete about the engine code where relevant.
