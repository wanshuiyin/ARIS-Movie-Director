# Framework Audit — 2026-06-10 (cross-model, codex gpt-5.5 xhigh × 4 dimensions)

> Four parallel codex auditors (engine runtime / framework↔project boundary / viewer+build security /
> open-source readiness) + a synthesis pass. Claude field-verified the objective claims marked ✓.
> **Overall verdict: a working single-example prototype whose hardened center (the cross-model
> panel-verdict math) is real — but everything wrapped around that center is soft. The single biggest
> hole: the gate's verdict is not bound to the artifact it judges.**

## P0 — must fix before relying on unattended runs / project #2

| # | dim | issue |
|---|-----|-------|
| 1 | engine | **Heredoc injection from project content**: comic.json scene/bubble text is interpolated into a fixed-delimiter `<<'PROMPTEOF'` heredoc in the emitted bake bash — a line equal to `PROMPTEOF` in any bubble executes shell. pid/PAGE also reach /tmp paths unvalidated. Fix: whitelist pid/page; pass project text via a file, never inline in a heredoc (or randomized delimiter + containment check). |
| 2 | engine | **Generated-image pickup unsound ×3**: `find ~/.codex/generated_images -newer $M \| sort \| tail -1` scans a GLOBAL dir (concurrent codex sessions / orphaned grandchildren pollute it); `sort` is lexicographic not mtime; watchdog `pkill -P` kills only direct children. A foreign PNG can silently enter the gate. Fix: per-run isolated output dir or parse the artifact path from this run's codex log + hash check; kill the full process tree. |
| 3 | engine | **Resume can replay a cached verdict onto a different image**: run state is in-memory; attempt artifacts + wiki nodes are overwritten on re-run; gate/assembly agent labels carry no attempt index or image hash (unlike `gen:${pid}#${ai}`) — a Workflow resume can stamp attempt-1's KEEP onto attempt-2's file. Fix: attempt-id + image sha256 in every gate label/prompt; durable run-state; immutable attempt paths. |
| 4 | engine | **Gate-failing panels can finalize**: on exhaustion the LAST (gate-FAILING) image is pushed into `kept[]` with only a `needs_human` side-flag; assembly can accept; `finalize:true` ships it. "Best-so-far" is actually last-so-far. Fix: hard non-finalizable status on exhaustion; pick true best by persisted scores; require explicit human override. |
| 5 | boundary | **movie.project.json is dead** — the engine never reads it ✓; all paths/defaults built from `args.projectRoot` with example-#1 values (`P02_b08`, S12-S15) baked in. Fix: engine loads the manifest; defaults come from it. |
| 6 | boundary | **Project-#1 character knowledge hardcoded on BOTH gen + review sides**: duo filename, "blue executor / green reviewer" descriptions in the bake prompt AND gemini review prompt, speaker enum {executor,reviewer}, 2-visual-reviewer topology. Project #2 (other characters / 3 chars) must edit framework code. Fix: characters/refs/reviewer-topology become manifest fields injected into prompts. |

## P1 — should fix soon (selected; full list in the run output)

- **Wiki trace unverified end-to-end**: writeWiki only schema-checks the agent's *reply*, never reads back the files; reviewer payloads truncated `.slice(0,300)` mid-JSON; assembly + cross-frame-repair decisions never written. Add a deterministic validator/readback (and write nodes from the engine, not an agent).
- **Timeout fail-safe contradicts schemas**: prompts say "no parseable scores → timed_out", but schemas REQUIRE numeric scores (and have no 0-5 bounds) → invites fabricated scores. Make schemas oneOf{scores}|{timed_out}; bound 0-5.
- **Throttle detection regexes LLM prose** (`/rate|limit|.../i` over gen_failed_reason) — spoofable both directions. Add a deterministic `failure_kind` classified by the bash wrapper from exit code/stderr.
- **Cross-frame repair bypasses the gen budget** (no MAX_TOTAL check in the repair loop; MAX_LOCAL dead code; pending[] invariants dropped in repair). Unify one budget checked before every bake.
- **Viewer XSS sinks**: `h1.innerHTML=T(pg.title)`, `narr.innerHTML=T(pg.narration)` render comic.json as live HTML on a page meant for GitHub Pages. textContent or sanitize.
- **image_path unconstrained in build_comic.py**: absolute/`../` paths get base64-inlined → local-file exfiltration into a publishable artifact. Constrain to project-relative image extensions.
- **BAKE_LANG=zh + text.zh hardcoded**; **macOS-only bash** (Chrome path, BSD `stat -f%z`, pkill) breaks Linux/CI; **content_svg unconditionally required** even for html/textless panels.
- **docs/architecture.md drifted** (wrong engine path, outdated keep formula, claims "manifest-driven" while the manifest is dead) — misleads contributors.
- **Release-gate items**: LICENSE asset-class boundaries (code/protocols/AI-generated imagery), baked-panel redistribution rights inventory, protocols/ provenance (source commit + license), **schema drift ✓** (node_type enum lacks `panel_attempt` yet 5 example nodes use it; no schema_version in nodes; $id points at the old repo name), **.gitignore corrupted with literal `\n` ✓** (outputs-ignore block dead → 12MB outputs/index.html IS tracked ✓ + stray panel PNGs untracked-floating).

## P2 — nice

Mixed-mode page blind spot (one baked panel disables html safezone checks for the page) + silent assembly skip when kept<2; `</`-only JSON escape leaves `<!--<script>` edge; 13.8MB single-file size guardrail; a11y (alt="", aria); architecture.md carries project-#1 narrative; ARIS branding + fixed fake timestamp in framework-emitted wiki nodes; README quickstart missing; REDACTION unauditable (manual claim, no scan rules).

## Synthesis (verbatim core)

The hardened verdict math is real; the wrapping is soft. **Fix order: (1) bind verdicts to artifacts**
(image hash in gate labels + per-run image isolation + no-finalize-on-exhaustion), **(2) make the
manifest real** (kill dead movie.project.json, move characters/topology/lang/paths into it), **(3) make
the trace trustworthy** (deterministic wiki writes + validator + schema sync), **(4) viewer sanitization
+ build validation**, **(5) release-gate items** (license/rights/provenance/quickstart) before any flip.
