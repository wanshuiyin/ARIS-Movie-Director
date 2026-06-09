// HISTORICAL design-process artifact (paths redacted; ran from the Claude session, not runnable as-is in this repo).
export const meta = {
  name: 'aris-comic-pivot-design',
  description: 'Cross-model design for the ARIS-Movie → HTML comic/连环画 pivot (swap Seedance i2v video for Codex panel image-gen; keep wiki + cross-model gate + rollback). 5 dimensions fan out, each gets codex gpt-5.5 xhigh ‖ gemini-3 independent takes → Claude reconciles → synthesis writes a design doc → codex+gemini adversarial critique → finalize.',
  phases: [
    { title: 'Design', detail: '5 dimensions in parallel; each: Claude take + codex xhigh + gemini-3 → reconcile' },
    { title: 'Synthesize', detail: 'merge 5 dimensions into one design doc' },
    { title: 'Critique', detail: 'codex + gemini adversarially attack the written doc' },
    { title: 'Finalize', detail: 'revise the doc per critique; surface forks for the human' },
  ],
}

const REPO = '@aris_movie'
const DOC = REPO + '/COMIC_PIVOT_DESIGN.md'

const SCOUT = [
  '- The promo film aris_promo_v1 = 22 shots / 13 beats / 112s. Story: a researcher 24h before the ICLR DDL delegates a concrete dllm task to ARIS and leaves; two PIXEL CHIBI ARIS characters (blue executor + green reviewer) run /idea-creator→/novelty-check→/experiment-bridge→/auto-review-loop on his laptop, hit a Round-3 REJECT, perform the CENTERPIECE WIKI ROLLBACK (diagnose / upgrade invariant / rewrite downstream), re-run, ACCEPT, /paper-writing finishes; user returns to a submission_ready.pdf. Tagline: 你不在的时候，研究在。',
  '- EXISTING ASSETS (pixel-art chibi style, all on disk, reusable): chars = user_chibi (+v002, +biking), aris_executor (blue), aris_reviewer (green), aris_chibi, supervisor_chibi. props = bicycle, coffee_mug, gpu_server, macbook, wandb_dashboard. scenes = bedroom, cafeteria_window, campus_road (day/night), classroom, wiki_space. sprites = duo_canonical_ref_v001 (THE cross-shot identity lock for the duo), sprite_aris_duo_sheet.',
  '- 22 BAKED FIRST FRAMES exist (S01..S22, 1280x720, pixel-art; the duo is baked into 15 of them). These are ALREADY composed scene panels — essentially comic panels in pixel style.',
  '- 24 SVG OVERLAYS exist: k3_sidebar(+violated), k3_node(+invariant), ddl_widget_template, wandb_curve(template/dropped), reject_stamp, accept_stamp, wiki_edges, constellation, invariant_bloom, novelty_grid, correct_json, submission_package, aris_logo_lockup(+s02), pipeline_tracker_{idea,novelty,experiment,review,paper}, coffee_steam, tokyo_broken. This is the UI / text / diagram / stamp layer.',
  '- SCRIPT + STORYBOARD locked: script-stage/final_script.v2.json, storyboard-stage/final_storyboard.v2.json (per-shot: beat, dialogue, narration, camera, on_screen_text). 22 shots map 1:1 to 22 comic panels with captions.',
  '- THE SPIRAL ENGINE (currently for video, the NON-NEGOTIABLE core): per-shot generate → clip_gate (CC narrative ‖ Gemini visual ‖ Codex visual → DETERMINISTIC JS verdict) → wiki active-memory (clip_attempt / review / decision / failure_mode nodes) → seam → assembly_gate → retry/rollback (force-regenerate with the failure_mode positive-invariant injected; attempt-path bypass; caps 4 attempts/shot, 6 rollbacks/run) → final assembly. Cross-model gate + wiki memory + REAL rollback MUST survive the pivot.',
  '- COST PROBLEM driving the pivot: Seedance 2.0 i2v = 88 credits/gen, full film ~2000+ credits. THE SWAP: replace Seedance i2v VIDEO-gen with CODEX IMAGE-GEN of static COMIC PANELS. Codex image-gen runs via: codex exec -i <ref1> -i <ref2> ... "<prompt>" --sandbox workspace-write -c model_reasoning_effort=high ; output lands in ~/.codex/generated_images/<id>/*.png. It accepts MULTIPLE condition images, so prev-panel + duo_canonical_ref + scene-ref + char-refs can ALL condition the next panel (consistency stronger than video).',
  '- REFERENCE FORM (inspiration only, do NOT copy): github nexu-io/html-video = HTML→MP4 via animated HTML frames + headless Chromium record + ffmpeg. Reusable PATTERNS only: (1) template-as-contract = templates expose JSON slots agents fill; (2) content-graph IR = an intermediate node/edge representation that decouples narrative decisions from rendering. OUR panels are Codex-generated PNGs, NOT HTML-drawn art.',
  '- EXISTING HTML SKILLS to extend (do NOT hand-write HTML): render-html (~/.claude/skills/render-html/scripts/render_html.py — pure stdlib, XSS-sanitized, academic/dashboard templates) and paper-poster-html (single HTML/CSS, measurement-gated, print-quality).',
  '- USER (Ruofeng) intent: an HTML comic/连环画, N panels per page (4/6/8), click-to-flip pages, with a SIDE narration/explanation panel. Speech bubbles + in-panel text. He believes comic-image-gen and HTML-narration are DECOUPLED layers. OPEN FORKS he flagged: (a) keep pixel-art style vs restyle to manga/comic line-art vs painted 连环画; (b) reuse the aris_movie repo vs a NEW repo. He wants MAXIMUM codex + gemini cross-model discussion.',
].join('\n')

const DESIGN_SCHEMA = {
  type: 'object',
  required: ['recommendation', 'codex_take', 'gemini_take', 'open_decisions'],
  properties: {
    recommendation: { type: 'string', description: 'Your reconciled, concrete, opinionated recommendation for this dimension (markdown ok, 300-600 words)' },
    codex_take: { type: 'string', description: 'Summary of codex gpt-5.5 xhigh independent input (and whether the watchdog-CLI call succeeded)' },
    gemini_take: { type: 'string', description: 'Summary of gemini auto-gemini-3 independent input (and whether the watchdog-CLI call succeeded)' },
    agreements: { type: 'array', items: { type: 'string' } },
    disagreements: { type: 'array', items: { type: 'string' }, description: 'where the 3 models disagreed + how you adjudicated' },
    open_decisions: { type: 'array', items: { type: 'string' }, description: 'genuine forks only the human Ruofeng should decide' },
    reusable_assets: { type: 'array', items: { type: 'string' }, description: 'concrete asset reuse/adapt notes if relevant to this dimension' },
  },
}

const SYNTH_SCHEMA = {
  type: 'object',
  required: ['doc_path', 'executive_summary', 'open_decisions'],
  properties: {
    doc_path: { type: 'string' },
    executive_summary: { type: 'string', description: '8-15 line executive summary of the whole design' },
    open_decisions: {
      type: 'array',
      items: { type: 'object', required: ['question', 'options', 'recommendation'], properties: { question: { type: 'string' }, options: { type: 'array', items: { type: 'string' } }, recommendation: { type: 'string' } } },
    },
  },
}

const CRITIQUE_SCHEMA = {
  type: 'object',
  required: ['model', 'biggest_flaws', 'missing', 'risks', 'verdict'],
  properties: {
    model: { type: 'string' },
    biggest_flaws: { type: 'array', items: { type: 'string' } },
    missing: { type: 'array', items: { type: 'string' } },
    risks: { type: 'array', items: { type: 'string' } },
    verdict: { type: 'string', description: 'one-line: is the design sound enough to act on? what is the single most important fix?' },
  },
}

const FINAL_SCHEMA = {
  type: 'object',
  required: ['doc_path', 'final_summary', 'open_decisions', 'changelog'],
  properties: {
    doc_path: { type: 'string' },
    final_summary: { type: 'string' },
    open_decisions: {
      type: 'array',
      items: { type: 'object', required: ['question', 'options', 'recommendation'], properties: { question: { type: 'string' }, options: { type: 'array', items: { type: 'string' } }, recommendation: { type: 'string' } } },
    },
    changelog: { type: 'array', items: { type: 'string' } },
  },
}

const DIMS = [
  { key: 'form', title: 'Form & Reading UX (the HTML comic viewer)', charge: 'Design the reader experience. Decide panels-per-page (4 / 6 / 8) for a 22-panel story over 13 beats — recommend with reasoning (consider beat grouping: a page ≈ a beat). Decide page navigation (click-to-flip pages vs vertical-scroll webtoon vs keyboard arrows) — recommend one as default, note the alternative. Design the SIDE narration/explanation panel (placement, how much text, collapsible, beat header). Decide in-panel speech bubbles vs HTML captions (coordinate with the decouple dimension). Address responsive/mobile. Decide how it SHIPS on the ARIS GitHub homepage: README embed vs GitHub Pages single-file HTML vs linked artifact. Borrow template-as-contract + content-graph-IR patterns from html-video but image-based. MUST extend render-html / paper-poster-html, not hand-write HTML. Give a concrete page→panel layout grid (ASCII mock is welcome).' },
  { key: 'imagegen', title: 'Codex Comic-Panel Image Pipeline + cross-panel consistency', charge: 'Design how Codex generates each comic panel. (a) STYLE: keep existing pixel-art chibi, OR restyle to manga line-art, OR painted 连环画 — recommend, stating what each costs in asset-reuse vs visual appeal for a GitHub promo. (b) prev-panel-as-condition: confirm feasible and design the EXACT condition stack per panel (which refs as -i: prev panel PNG, duo_canonical_ref, scene ref, char refs). (c) reuse of the 22 baked frames as composition seeds. (d) panel aspect ratio + resolution. (e) speech bubbles baked-by-Codex vs HTML-overlaid (coordinate w/ decouple). (f) identity-lock mechanism across 22 panels + how to fight slow style/identity drift. Give the concrete `codex exec -i ... "..."` command shape.' },
  { key: 'spiral', title: 'Spiral integrity mapping (wiki + cross-model gate + rollback) onto comics', charge: 'Map the video spiral onto static comics. Define panel_gate DIMENSIONS for a static panel (identity consistency vs duo_canonical_ref; narrative-beat fidelity; style consistency w/ prior panels; speech-bubble/text legibility & textual correctness; visual artifact / anatomy; composition & readability). Define the cross-model gate (CC narrative ‖ Gemini visual ‖ Codex visual → deterministic JS verdict) with concrete thresholds. Define a page-level assembly_gate (does a 4/6/8-panel page read coherently; do panels flow). Define what ROLLBACK means for a comic (since prev-panel conditions the next: regenerate panel K and everything downstream of it) and the chain semantics + caps. Reuse the existing engine concepts (attempt-path, failure_mode active memory, deterministic JS verdict). Note: static panels remove temporal drift — say which gate dimensions get EASIER and which (cross-panel identity/style drift) get HARDER.' },
  { key: 'repo_assets', title: 'Repo decision + asset reuse/adaptation inventory', charge: '(a) DECIDE: reuse the aris_movie repo (e.g. a new project movie-wiki/projects/aris_comic_v1 sharing the asset library + wiki + spiral skills) vs a NEW standalone repo — give a clear recommendation with reasoning (shared assets/wiki/skills & single source of truth vs clean separation / different audience / lighter clone). (b) ASSET INVENTORY: classify each existing asset group (5 char refs, 5 props, 7 scene plates, 22 baked frames, 2 sprites incl duo_canonical_ref, 24 SVG overlays) as REUSE-AS-IS / ADAPT (state the change) / NOT-NEEDED. Especially decide: do the 24 SVG overlays become in-panel insets, HTML-side diagrams, or both? Do the 22 baked frames seed the panels (and how, given a possible restyle)? (c) list NEW assets a comic needs (speech-bubble kit, panel borders/gutters, page furniture, chapter dividers).' },
  { key: 'decouple', title: 'Decoupling: comic-gen layer vs HTML-narration layer + the data contract', charge: 'The user believes comic-image-gen and HTML-narration are decoupled. Confirm/refine, then DESIGN THE CONTRACT: a single manifest (comic.json — the content-graph IR) that the image pipeline WRITES (per panel: image path, in-panel bubbles list, identity/condition refs used, beat id, page id, gate status, attempt index) and the HTML viewer READS (+ side-narration text, captions, beat/chapter headers). Give the concrete JSON schema. Clarify which text lives IN the panel (speech bubbles, baked by Codex) vs in HTML (narration, explanation, captions). Show how regenerating ONE panel does NOT require rebuilding the HTML (viewer reads manifest at load). Note how optional TTS audio narration could attach later via the same manifest. This IS the html-video content-graph-IR pattern applied to our case.' },
]

function designPrompt(d) {
  const K = d.key
  return [
    `You are a senior design agent for the ARIS-Movie → HTML COMIC / 连环画 pivot. The pivot swaps expensive Seedance i2v VIDEO generation for CODEX static-panel IMAGE generation, keeping the cross-model gate + wiki memory + rollback spiral intact.`,
    `YOUR DIMENSION: **${d.title}**`,
    ``,
    `## GROUNDING (verified facts — treat as ground truth, do not re-discover)`,
    SCOUT,
    ``,
    `## YOUR CHARGE`,
    d.charge,
    ``,
    `## METHOD — MANDATORY cross-model discussion (codex gpt-5.5 xhigh ‖ gemini auto-gemini-3)`,
    `MCP tools are FORBIDDEN here (an unbounded hang would freeze this workflow). Use watchdog-bounded CLI only. Steps:`,
    `1. Form YOUR OWN (Claude) recommendation FIRST, grounded in the facts above.`,
    `2. Get CODEX's independent take. Compose a self-contained question (your dimension's charge + the minimal grounding it needs), write it to a UNIQUE temp file, and run with a watchdog:`,
    '```bash',
    `cat > /tmp/cq_${K}.txt <<'PROMPTEOF'`,
    `«write your full self-contained question for this dimension here — include enough grounding that a fresh model can answer well; ask for a concrete, opinionated design recommendation with tradeoffs, 250-450 words»`,
    `PROMPTEOF`,
    `( codex exec "$(cat /tmp/cq_${K}.txt)" --skip-git-repo-check -c model_reasoning_effort=xhigh < /dev/null > /tmp/cr_${K}.txt 2>&1 ) & P=$!; ( sleep 600; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 6000 /tmp/cr_${K}.txt`,
    '```',
    `3. Get GEMINI's independent take (same question file):`,
    '```bash',
    `( gemini --model auto-gemini-3 --prompt "$(cat /tmp/cq_${K}.txt)" < /dev/null > /tmp/gr_${K}.txt 2>&1 ) & P=$!; ( sleep 300; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 6000 /tmp/gr_${K}.txt`,
    '```',
    `4. If a model's call times out or errors, note it in codex_take/gemini_take and proceed with the others (do not block).`,
    `5. RECONCILE all three views. Where they disagree, JUDGE and pick the best, with reasoning. Keep what is genuinely better from codex/gemini even if it differs from your first take.`,
    `6. Surface as open_decisions ONLY the genuine forks that the human (Ruofeng) should decide — not things you can resolve.`,
    ``,
    `Return DESIGN_SCHEMA. Be concrete and buildable, not vague. This feeds a synthesis that writes the actual design doc.`,
  ].join('\n')
}

function synthPrompt(designs) {
  return [
    `You are the synthesis architect for the ARIS-Movie → HTML COMIC / 连环画 pivot. ${designs.length} dimension designs (each already cross-modeled with codex gpt-5.5 xhigh + gemini-3) are below as JSON.`,
    ``,
    `## GROUNDING`,
    SCOUT,
    ``,
    `## THE ${designs.length} DIMENSION DESIGNS (JSON)`,
    JSON.stringify(designs.map(x => ({ dimension: x.dim.title, key: x.dim.key, recommendation: x.r.recommendation, agreements: x.r.agreements, disagreements: x.r.disagreements, open_decisions: x.r.open_decisions, reusable_assets: x.r.reusable_assets, codex_take: x.r.codex_take, gemini_take: x.r.gemini_take })), null, 1),
    ``,
    `## YOUR TASK`,
    `Merge these into ONE coherent, buildable design document and WRITE it to: ${DOC}`,
    `The document MUST contain, in this order:`,
    `1. Executive summary (what the comic pivot is; why it is more controllable than video, not just cheaper).`,
    `2. End-to-end architecture (the layers: asset library → Codex panel image-gen → panel_gate spiral (wiki + cross-model + rollback) → comic.json manifest → HTML viewer). Include an ASCII data-flow diagram.`,
    `3. Section per dimension (Form/UX, Image pipeline, Spiral mapping, Repo+assets, Decoupling) with the concrete decisions.`,
    `4. The comic.json (content-graph IR) JSON schema — the seam between image-gen and the HTML viewer.`,
    `5. The concrete \`codex exec -i ...\` panel-gen command shape + the per-panel condition stack.`,
    `6. The panel_gate + page assembly_gate definitions with thresholds, and rollback/chain semantics.`,
    `7. Asset inventory table: each asset group → REUSE-AS-IS / ADAPT(change) / NOT-NEEDED + NEW assets needed.`,
    `8. A phased build plan (e.g. P0 spike: 1 page / 4 panels end-to-end; P1 full chapter; P2 full 22-panel comic + ship). Tie back to the existing spiral-engine so we reuse, not rewrite.`,
    `9. A consolidated "DECISIONS FOR RUOFENG" list (the genuine forks — at minimum: art style, repo location, panels-per-page, navigation; merge/dedup the dimensions' open_decisions; for each give 2-3 options + your recommendation).`,
    `Write real markdown with tables and code blocks. Then return SYNTH_SCHEMA (doc_path=${DOC}, executive_summary, open_decisions = the consolidated forks).`,
  ].join('\n')
}

function critiquePrompt(model, docPath) {
  const isCodex = model === 'codex'
  const runBlock = isCodex
    ? `( codex exec "$(cat /tmp/crit_in.txt)" --skip-git-repo-check -c model_reasoning_effort=xhigh < /dev/null > /tmp/crit_codex.txt 2>&1 ) & P=$!; ( sleep 600; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 8000 /tmp/crit_codex.txt`
    : `( gemini --model auto-gemini-3 --prompt "$(cat /tmp/crit_in.txt)" < /dev/null > /tmp/crit_gemini.txt 2>&1 ) & P=$!; ( sleep 300; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 8000 /tmp/crit_gemini.txt`
  return [
    `You are running an ADVERSARIAL cross-model critique of a design document, using ${isCodex ? 'CODEX gpt-5.5 xhigh' : 'GEMINI auto-gemini-3'} as the independent critic (a DIFFERENT model family than the Claude author — this is the whole point).`,
    `The design doc is at: ${docPath}`,
    `Steps:`,
    `1. Build the critic prompt: concatenate an instruction + the FULL doc into a temp file:`,
    '```bash',
    `{ printf '%s\\n\\n' "You are a skeptical senior engineer + comics art director. Attack this ARIS comic-pivot design. Find the BIGGEST flaws (things that will not work / will look bad / will not stay consistent), what is MISSING, and the top RISKS. Be specific and harsh. End with a one-line verdict: is it sound enough to act on, and the single most important fix. Here is the design:"; cat "${docPath}"; } > /tmp/crit_in.txt`,
    `${runBlock}`,
    '```',
    `2. If the call times out/errors, say so and give your own best-effort critique from having read the doc yourself (Read ${docPath}).`,
    `3. Distill the critic's output into CRITIQUE_SCHEMA (model="${isCodex ? 'codex-gpt-5.5-xhigh' : 'gemini-auto-3'}"). Do NOT soften it — pass through the sharpest valid points.`,
  ].join('\n')
}

function finalPrompt(docPath, crits) {
  return [
    `You are the finalizer for the ARIS comic-pivot design doc at ${docPath}.`,
    `Two independent cross-model critiques (codex + gemini) are below as JSON.`,
    JSON.stringify(crits, null, 1),
    ``,
    `Task:`,
    `1. Read ${docPath}.`,
    `2. For each VALID critique point, REVISE the doc in place (Edit/Write) — fix flaws, fill gaps, add a "Risks & mitigations" section capturing the real risks. Ignore invalid/low-value points but note why in changelog.`,
    `3. Make sure the "DECISIONS FOR RUOFENG" list is crisp: each fork has 2-3 options + a clear recommendation.`,
    `Return FINAL_SCHEMA (doc_path=${docPath}, final_summary, open_decisions = the polished forks, changelog = what you changed from the critiques).`,
  ].join('\n')
}

// ── run ──────────────────────────────────────────────────────────────────
phase('Design')
const designsRaw = await parallel(DIMS.map(d => () => agent(designPrompt(d), { label: `design:${d.key}`, phase: 'Design', schema: DESIGN_SCHEMA })))
const designs = designsRaw.map((r, i) => ({ dim: DIMS[i], r })).filter(x => x.r)
log(`Design phase done: ${designs.length}/${DIMS.length} dimensions returned`)

phase('Synthesize')
const synth = await agent(synthPrompt(designs), { label: 'synthesize', phase: 'Synthesize', schema: SYNTH_SCHEMA })
log(`Synthesis written to ${synth?.doc_path || DOC}`)

phase('Critique')
const crits = (await parallel([
  () => agent(critiquePrompt('codex', DOC), { label: 'critique:codex', phase: 'Critique', schema: CRITIQUE_SCHEMA }),
  () => agent(critiquePrompt('gemini', DOC), { label: 'critique:gemini', phase: 'Critique', schema: CRITIQUE_SCHEMA }),
])).filter(Boolean)
log(`Critique phase done: ${crits.length}/2 critics returned`)

phase('Finalize')
const final = await agent(finalPrompt(DOC, crits), { label: 'finalize', phase: 'Finalize', schema: FINAL_SCHEMA })

return {
  doc_path: (final && final.doc_path) || (synth && synth.doc_path) || DOC,
  final_summary: (final && final.final_summary) || (synth && synth.executive_summary),
  open_decisions: (final && final.open_decisions) || (synth && synth.open_decisions) || [],
  dimensions: designs.map(x => ({ key: x.dim.key, recommendation: x.r.recommendation, open_decisions: x.r.open_decisions, codex_ok: !!x.r.codex_take, gemini_ok: !!x.r.gemini_take })),
  critiques: crits,
  changelog: (final && final.changelog) || [],
}
