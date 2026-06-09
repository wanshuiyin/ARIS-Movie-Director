// HISTORICAL design-process artifact (paths redacted; ran from the Claude session, not runnable as-is in this repo).
export const meta = {
  name: 'aris-comic-p0-review',
  description: 'Cross-model adversarial review of the P0 comic-pipeline artifacts (engine, comic.json, ART_BIBLE, build_comic.py, comic_template.html), authored solo by Claude. codex gpt-5.5 xhigh reviews code/logic correctness; gemini-3 reviews design/contract/UX; a 3rd codex pass deep-checks the spiral engine logic. Synthesis dedups + prioritizes blocker/should/nice. Text review only — NOT image_gen, so not rate-limited.',
  phases: [
    { title: 'Review', detail: 'codex(code) ‖ codex(engine-logic) ‖ gemini(design) read the real files' },
    { title: 'Synthesize', detail: 'merge + dedup + prioritize the fix list' },
  ],
}

const REPO = '@aris_movie'
const PROJ = REPO + '/movie-wiki/projects/aris_comic_v1'
const ENGINE = '@workflows/aris-comic-spiral-engine.js'
const BUILDER = PROJ + '/build_comic.py'
const TEMPLATE = PROJ + '/comic_kit/comic_template.html'
const BIBLE = PROJ + '/comic_kit/ART_BIBLE.md'
const CJSON = PROJ + '/comic.json'
const DESIGN = REPO + '/COMIC_PIVOT_DESIGN.md'

const FIND = {
  type: 'object', required: ['reviewer', 'blockers', 'should_fix', 'overall'],
  properties: {
    reviewer: { type: 'string' },
    blockers: { type: 'array', items: { type: 'object', required: ['file', 'issue', 'fix'], properties: { file: { type: 'string' }, issue: { type: 'string' }, fix: { type: 'string' } } } },
    should_fix: { type: 'array', items: { type: 'object', required: ['file', 'issue', 'fix'], properties: { file: { type: 'string' }, issue: { type: 'string' }, fix: { type: 'string' } } } },
    nice: { type: 'array', items: { type: 'string' } },
    overall: { type: 'string' },
  },
}

function codexReview(label, files, focus) {
  const catCmd = files.map(f => `echo "===== ${f} ====="; cat "${f}"`).join('; ')
  return agent([
    `You are an independent CODEX (gpt-5.5 xhigh) reviewer of ARIS comic-pipeline code authored solo by Claude — a DIFFERENT model family, this is the cross-model check. FOCUS: ${focus}`,
    `Build the review input then call codex (watchdog-bounded; codex TEXT review is not rate-limited):`,
    '```bash',
    `{ printf '%s\\n' "Review these files for ${focus}. Be concrete and harsh. For each real problem give: file, the exact issue, and a concrete fix. Separate BLOCKERS (will break/produce wrong results) from SHOULD-FIX (correctness/robustness) from NICE. End with a one-line overall verdict. Files:"; ${catCmd}; } > /tmp/crv_${label}.txt`,
    `( codex exec "$(cat /tmp/crv_${label}.txt)" --skip-git-repo-check -c model_reasoning_effort=xhigh < /dev/null > /tmp/crv_${label}.out 2>&1 ) & P=$!`,
    `( sleep 540; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 9000 /tmp/crv_${label}.out`,
    '```',
    `If codex times out/errors, say so in overall and give your own best-effort review from reading the files (cat them yourself). Distill into FIND (reviewer="codex:${label}").`,
  ].join('\n'), { label: `codex:${label}`, phase: 'Review', schema: FIND })
}

phase('Review')
const reviews = (await parallel([
  () => codexReview('code', [BUILDER, TEMPLATE], 'CODE CORRECTNESS — build_comic.py (base64 inlining, the </ escaping in the JSON blob vs the <script> block, missing-image handling, path resolution) and comic_template.html (the JS renderer: comic.json parsing, T()/locale toggle, safe_zone anchor resolution, bubble positioning, text_mode html/baked/code handling, XSS via innerHTML of T(), ?p= bounds)'),
  () => codexReview('engine', [ENGINE], 'ENGINE LOGIC — aris-comic-spiral-engine.js: panelVerdict formula (can it deadlock or wrongly keep/reject? skip-missing-dim handling? disagree gate), the retry/rollback/caps state machine (infinite-loop risk, rollback target math, kept[] filtering, localByPanel reset), generatePanel codex image_gen invocation + the rate-limit/gen_failed path, the gate prompts eliciting PARSEABLE JSON from gemini/codex CLI, the path bug `img` line (REPO+"/"+REPO replace hack), Promise.all races, edge cases'),
  () => agent([
    `You are an independent GEMINI (auto-gemini-3) reviewer — DIFFERENT model family from the Claude author. FOCUS: DESIGN / CONTRACT / UX coherence, NOT line-level code.`,
    `Run (watchdog-bounded CLI):`,
    '```bash',
    `( gemini --model auto-gemini-3 -p "@${BIBLE} @${CJSON} @${TEMPLATE} @${DESIGN} 你在跨模型审一套'AI宣传片→HTML像素连环画'流水线的P0产物(Claude独自写的)。重点审设计/契约/UX一致性(不是逐行代码):(1) ART_BIBLE 是否真能当 panel_gate 的可执行收敛靶,有没有致命空白?(2) comic.json 这个 IR 契约能否支撑扩到22格全片+双语+三种 text_mode,字段够不够、有没有自相矛盾?(3) 模板 viewer 的阅读体验/双语切换/留白气泡定位有没有设计问题?(4) 整条流水线和 COMIC_PIVOT_DESIGN.md 的决定有没有偏离?把问题分 BLOCKER/SHOULD/NICE,每条给 文件+问题+修法,最后一句总评。中文。" < /dev/null > /tmp/grv_design.out 2>&1 ) & P=$!`,
    `( sleep 360; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 9000 /tmp/grv_design.out`,
    '```',
    `If gemini errors, say so + give your own review. Distill into FIND (reviewer="gemini:design").`,
  ].join('\n'), { label: 'gemini:design', phase: 'Review', schema: FIND }),
])).filter(Boolean)

phase('Synthesize')
const synth = await agent([
  `Synthesize ${reviews.length} cross-model reviews of the ARIS comic P0 pipeline into ONE prioritized fix list for the Claude author to apply. Reviews (JSON):`,
  JSON.stringify(reviews, null, 1),
  `Dedup overlapping findings. Keep ONLY real, actionable issues (drop vague/duplicate/wrong ones — note if you dropped a reviewer point as invalid). Order: BLOCKERS first, then SHOULD-FIX, then NICE. For each: which file, the issue, the concrete fix. Return FIND (reviewer="synthesis"); put blockers/should_fix/nice; overall = how sound is P0 + the single most important fix.`,
].join('\n'), { label: 'synthesize', phase: 'Synthesize', schema: FIND })

return { reviews, synthesis: synth, blocker_count: (synth?.blockers || []).length, should_count: (synth?.should_fix || []).length }
