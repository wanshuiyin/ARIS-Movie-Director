// HISTORICAL design-process artifact (paths redacted; ran from the Claude session, not runnable as-is in this repo).
export const meta = {
  name: 'aris-comic-dllm-redesign',
  description: 'Cross-model (codex gpt-5.5 xhigh ‖ gemini-3) deep design to redesign the ARIS comic B08/audit beat so it SHOWS the REAL dllm research (schema-keyword-first denoising; the M3 audit-cascade integrity catch: an in-pipeline JSON sanitizer inflated schema-aware to +6.2 over random-mask, the adversarial experiment-audit caught it, honest re-eval with raw json.loads+jsonschema collapsed the gap to +1.4, verdict WARN_corrected — bug caught before claim amplification). Three design dimensions, each cross-modeled, → synthesis: (1) the method diagram random-mask vs schema-first-mask, (2) the per-panel beat redesign showing the audit/integrity drama, (3) the condition-driven codex generation recipe (feed method+content as condition refs so the chibis AUDIT/DISCUSS the real work — NOT empty void, NOT HTML overlay).',
  phases: [
    { title: 'Design', detail: '3 dims in parallel; each: Claude take + codex xhigh + gemini-3 → reconcile' },
    { title: 'Synthesize', detail: 'merge into one concrete redesign plan + diagram spec + gen recipe' },
  ],
}

const REPO = '@aris_movie'

const STORY = [
  'REAL RESEARCH (from Ruofeng\'s VALSE 2026 talk, the dllm × structured-JSON running example M0→M5):',
  '- METHOD: schema-keyword-first denoising for a Diffusion LLM (DLLM, ~200M) generating tree-shaped JSON (depth 2-4). In diffusion-LM denoising you iteratively UNMASK tokens; the RANDOM-MASK baseline unmasks in random order, while SCHEMA-KEYWORD-FIRST unmasks the schema-structural keys + critical value tokens FIRST, then fills the rest → more reliable structure. Baselines: random-mask, left-to-right AR.',
  '- M1 RESEARCH QUESTION: does schema-keyword-first beat random masking on exact-parse success rate under EXTERNAL jsonschema validation, for DLLM under tree-shaped JSON (depth 2-4)?',
  '- M2 PLAN (correct): 164 schema-constrained records · ~200M DLLM · baselines random-mask + L2R-AR · PRIMARY metric = raw json.loads + jsonschema · 4×A100. The plan is right; the bug will be the execution WRAPPER silently deviating from this spec.',
  '- M3 (THE CENTERPIECE — Audit Cascade Stage-1 experiment-audit, an ADVERSARIAL cross-family reviewer, Codex fresh thread): initial result schema-aware = +6.2 over random-mask (looks great). The audit flags: the EVALUATOR silently used the pipeline\'s JSON SANITIZER that default-fills malformed keys (so malformed model outputs got auto-repaired before scoring → inflated). Re-evaluated with raw json.loads + jsonschema (the honest primary metric) → the gap COLLAPSES to +1.4. The +4.8 was an evaluator self-repair artifact. Verdict: WARN_corrected — effect REAL but scope narrowed; bug caught BEFORE claim amplification.',
  '- M5 MANUSCRIPT prose: "schema-aware denoising improves exact-parse success by +1.4 over random masking (95% CI ±0.8); an additional +4.8 measured under in-pipeline sanitization is an evaluator self-repair artifact." ARIS verdict aesthetic: 诚实但不杀稿 — the claim NARROWS from "X is best" to "X is best when an external validator is used".',
  '- THE THEME (talk slide 3): the dominant failure mode of long-horizon agent research is NOT visible breakdown — it is PLAUSIBLE UNSUPPORTED SUCCESS (results real yet misreported; claims outrun evidence). ARIS\'s cross-family adversarial audit catches it before it propagates. The green REVIEWER chibi is the adversarial auditor; the blue EXECUTOR chibi ran the experiment.',
  '',
  'ASSETS ON HAND: blue executor + green reviewer pixel-chibi (duo_canonical_ref locks identity); existing SVG data-overlays in movie-wiki/assets/overlays/ (tokyo_broken=exact_parse FAIL JSON, correct_json=exact_parse OK, wandb_curve, k3_node/invariant, reject_stamp, accept_stamp). FINDING: codex image_gen renders BOTH CJK and English text bubbles CLEANLY (verified — even a long Chinese sentence), and bakes them integrated into the pixel art (no "widget pasted on image" seam). So codex CAN bake rich technical content + text into a panel.',
  'CURRENT PROBLEM: the existing B08 panels are two chibis floating in an EMPTY dark void with tiny abstract cards — they show NONE of the real research. Ruofeng wants the panels to SHOW the actual work: a method diagram (random vs schema-first mask), the inflated +6.2, the JSON-sanitizer cheat, the collapse to +1.4, the WARN_corrected verdict — with the chibis AUDITING / DISCUSSING / pointing at it. He wants codex to GENERATE this as a conditioned panel (feed the diagram/content as a condition ref), NOT HTML-overlay it on top.',
].join('\n')

const DESIGN_SCHEMA = {
  type: 'object',
  required: ['recommendation', 'codex_take', 'gemini_take', 'open_decisions'],
  properties: {
    recommendation: { type: 'string', description: 'your reconciled concrete design for this dimension (markdown ok, be specific + buildable)' },
    codex_take: { type: 'string' }, gemini_take: { type: 'string' },
    agreements: { type: 'array', items: { type: 'string' } },
    disagreements: { type: 'array', items: { type: 'string' } },
    open_decisions: { type: 'array', items: { type: 'string' }, description: 'genuine forks only Ruofeng should decide' },
  },
}
const SYNTH_SCHEMA = {
  type: 'object', required: ['executive_summary', 'panel_specs', 'diagram_spec', 'gen_recipe', 'open_decisions'],
  properties: {
    executive_summary: { type: 'string' },
    panel_specs: { type: 'array', description: 'per B08 panel: id, scene, what the chibis DO, the technical content shown, dialogue (zh+en)', items: { type: 'object' } },
    diagram_spec: { type: 'string', description: 'the random-mask vs schema-first-mask method diagram spec (concrete enough to generate)' },
    gen_recipe: { type: 'string', description: 'the condition-driven codex generation recipe: which refs to feed (-i), prompt shape, baked vs overlay decision' },
    open_decisions: { type: 'array', items: { type: 'string' } },
  },
}

const DIMS = [
  { key: 'method_diagram', title: 'Method diagram: random-mask vs schema-first-mask',
    charge: 'Design a clear, comic-friendly diagram contrasting RANDOM-MASK denoising vs SCHEMA-KEYWORD-FIRST denoising for DLLM JSON generation. Show the diffusion unmask ORDER difference: random (tokens unmask in arbitrary order → JSON structure emerges late/unstable) vs schema-first (schema keys/structural tokens unmask FIRST → structure locks → values fill reliably). It must read in a pixel-art comic panel (the chibis point at it). Decide: is it a generated codex image, a FigureSpec/SVG (deterministic, crisp), or a hybrid (SVG diagram composited / or fed to codex as a condition)? Give the concrete content (what boxes/arrows/JSON-snippets/mask-grids appear) + the recommended rendering path.' },
  { key: 'beat_redesign', title: 'B08 panel beat redesign (show the M3 audit-integrity drama)',
    charge: 'Redesign the B08 page (currently the abstract "wiki rollback" — make it the REAL M3 audit-cascade integrity catch). Per panel (the page is ~4 panels, page≈beat cap 4): specify scene, what each chibi DOES (executor showed +6.2; reviewer audits the eval code, spots the JSON sanitizer; the number collapses +6.2→+1.4; WARN_corrected verdict), the on-panel technical content (the method diagram, the inflated number, the sanitizer/raw-json contrast, the wandb/exact-parse number, the WARN_corrected stamp), and dialogue (zh+en, short). Keep it dramatic + accurate to the talk. The emotional arc: proud result → adversarial audit catches the inflation → honest correction → 诚实但不杀稿 (not killed, scope-narrowed). Map to the existing overlays (tokyo_broken/correct_json/wandb/stamps) where they fit.' },
  { key: 'condition_gen', title: 'Condition-driven codex panel generation recipe (not overlay, not empty)',
    charge: 'Design HOW to make codex GENERATE rich panels that include the technical content + the chibis interacting with it, conditioned on a method diagram / data artifact — instead of two chibis in empty void or HTML-overlaying afterwards. codex image_gen takes multiple -i condition refs and bakes text/diagrams well (verified). Decide: feed the method-diagram PNG + duo_canonical + scene as -i refs and prompt "the two mascots stand at/point to this diagram/screen showing X"? Bake the data (numbers, JSON, +6.2→+1.4) into the panel via codex, or keep precise data as crisp HTML/SVG overlay on top? What is the per-panel condition stack + prompt pattern? How to keep identity locked while adding a busy technical foreground? Consult codex specifically (it knows its own image_generation conditioning). Give the concrete `codex exec -i ... "..."` recipe.' },
]

function designPrompt(d) {
  const K = d.key
  return [
    `You are a senior design agent for redesigning the ARIS pixel-art comic's centerpiece so it depicts the REAL dllm research accurately and richly (not an empty void). YOUR DIMENSION: **${d.title}**`,
    ``, `## GROUNDING (the real research + assets + constraints)`, STORY, ``,
    `## YOUR CHARGE`, d.charge, ``,
    `## METHOD — mandatory cross-model (codex gpt-5.5 xhigh ‖ gemini auto-gemini-3, watchdog-bounded CLI; MCP forbidden — a hang would freeze this workflow):`,
    `1. Form YOUR OWN recommendation first.`,
    `2. Codex's independent take — compose a self-contained question, write to a unique file, run:`,
    '```bash',
    `cat > /tmp/dq_${K}.txt <<'PROMPTEOF'`,
    `«your full self-contained question for this dimension — include the relevant real-research grounding; ask for a concrete, opinionated, buildable design with tradeoffs»`,
    `PROMPTEOF`,
    `( codex exec "$(cat /tmp/dq_${K}.txt)" --skip-git-repo-check -c model_reasoning_effort=xhigh < /dev/null > /tmp/dr_${K}.out 2>&1 ) & P=$!`,
    `( sleep 540; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 6000 /tmp/dr_${K}.out`,
    '```',
    `3. Gemini's independent take (same question file):`,
    '```bash',
    `( gemini --model auto-gemini-3 --prompt "$(cat /tmp/dq_${K}.txt)" < /dev/null > /tmp/gr_${K}.out 2>&1 ) & P=$!`,
    `( sleep 300; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 6000 /tmp/gr_${K}.out`,
    '```',
    `4. If a model errors/times out, note it and proceed. RECONCILE all three; where they differ, judge + pick with reasoning. Surface genuine forks for Ruofeng as open_decisions.`,
    `Return DESIGN_SCHEMA. Be concrete + buildable.`,
  ].join('\n')
}

phase('Design')
const designs = (await parallel(DIMS.map(d => () => agent(designPrompt(d), { label: `design:${d.key}`, phase: 'Design', schema: DESIGN_SCHEMA }))))
  .map((r, i) => ({ dim: DIMS[i], r })).filter(x => x.r)
log(`Design done: ${designs.length}/${DIMS.length}`)

phase('Synthesize')
const synth = await agent([
  `Synthesize ${designs.length} cross-modeled design dimensions into ONE concrete plan to redesign the ARIS comic B08/audit beat to SHOW the real dllm research (the M3 audit-cascade integrity catch). Designs (JSON):`,
  JSON.stringify(designs.map(x => ({ dimension: x.dim.title, key: x.dim.key, recommendation: x.r.recommendation, open_decisions: x.r.open_decisions, codex_take: x.r.codex_take, gemini_take: x.r.gemini_take })), null, 1),
  ``, `## GROUNDING`, STORY, ``,
  `Produce: (1) executive_summary; (2) panel_specs = per B08 panel {id, scene, chibi_action, technical_content_shown, dialogue_zh, dialogue_en}; (3) diagram_spec = the random-mask vs schema-first-mask method diagram (concrete enough to build); (4) gen_recipe = the condition-driven codex generation recipe (which -i refs, prompt pattern, baked-vs-overlay decision per element); (5) open_decisions = the genuine forks for Ruofeng. Return SYNTH_SCHEMA.`,
].join('\n'), { label: 'synthesize', phase: 'Synthesize', schema: SYNTH_SCHEMA })

return { synthesis: synth, dimensions: designs.map(x => ({ key: x.dim.key, recommendation: x.r.recommendation, open_decisions: x.r.open_decisions })) }
