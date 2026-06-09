export const meta = {
  name: 'aris-comic-spiral-engine',
  description: 'ARIS COMIC per-panel spiral (fork of the video spiral_engine, §16.9 shape preserved). Per panel: generatePanel (codex image_gen -i seed -i duo_canonical, ART_BIBLE-constrained, NO text, leave safe-zone) → panel_gate (CC narrative ‖ Gemini visual-CLI ‖ Codex visual-CLI → deterministic JS verdict, scored against ART_BIBLE) → WRITE wiki (panel_attempt/review/decision/failure_mode) → keep/retry/rollback (force-regen with failure_mode positive-invariant; attempt-path bypass; caps 4/panel, 6/run) → page assembly_gate. Swapped vs video: generator (Seedance i2v → codex image_gen), rubric (motion dims → static/identity/style dims), output (mp4 → PNG + comic.json projection). NOT batch.',
  phases: [
    { title: 'Panels', detail: 'per panel: generate → panel_gate (3 cross-model) → wiki → keep/retry/rollback' },
    { title: 'Assembly', detail: 'page-level assembly_gate: cross-panel identity/style + reading order + safe-zones' },
  ],
}

// The engine runs in the Workflow sandbox (NO process.env / fs) → paths MUST come from `args`, not env.
// Caller passes args.projectRoot = ABSOLUTE path to the project/example dir (manifest-driven). No hardcoded paths.
const PROJ = (args && args.projectRoot) || ''
const REPO = (args && args.repoRoot) || PROJ.replace(/\/examples\/[^/]+\/?$/, '')
const SEEDS = PROJ + '/seeds'
const PANELS = PROJ + '/panels'
const NODES = PROJ + '/wiki/nodes'
const CANON = PROJ + '/assets/duo_canonical_ref_v001.png'
const BIBLE = PROJ + '/ART_BIBLE.md'
const COMICJSON = PROJ + '/comic.json'
const STORY = COMICJSON  // comic.json carries per-panel beat/narration/dialogue (replaces the video storyboard)

// P0 default target = the B08 wiki-rollback page (the centerpiece, 4 panels). Override via args.panelIds.
const PAGE = (args && args.page) || 'P02_b08'
const PANEL_IDS = (args && args.panelIds) || ['S12', 'S13', 'S14', 'S15']
const MAX_LOCAL = 3, MAX_TOTAL = 4, MAX_ROLLBACKS = 6
const FINALIZE = (args && args.finalize === true) || false
const absImg = (p) => !p ? '' : (p.startsWith('/') ? p : PROJ + '/' + p)  // resolve panel image path (abs or project-rel) — one helper

// ── deterministic verdicts (formula over independent cross-model reviewers) ──
// Verdict for a SEED-ANCHORED comic panel. Calibrated after the first real B08 run:
//  - panels are independent (no chain) → only KEEP or RETRY-SAME-PANEL, NEVER rollback-to-prior.
//  - artifact must be CORROBORATED by both visual reviewers (a lone pixel-purist scoring the
//    background atmospheric glow as artifact=5 must not single-vote-veto — ART_BIBLE allows bg gradients).
//  - safe-zone present if EITHER reviewer confirms (they disagree on detection); stray text fails if EITHER sees it.
//  - identity stays strict (linchpin, reviewers agree); style/comp soften to tolerate one-reviewer strictness.
function panelVerdict(cc, gem, cdx, cfg = {}) {
  const mode = cfg.text_mode || 'html'
  const timeout = cc?.timed_out || gem?.timed_out || cdx?.timed_out
  if (timeout) return { v: 'retry_panel', reason: 'a reviewer timed out — fail-safe retry', invariant: '' }
  const baked = mode === 'baked'
  const narr = Math.min(cc?.narrative_beat_fidelity ?? 0, cc?.composition_story ?? 5)
  const idents = [gem?.identity_consistency, cdx?.identity_consistency].filter(x => x != null)
  const styles = [gem?.style_consistency, cdx?.style_consistency].filter(x => x != null)
  const comps = [gem?.composition_readability, cdx?.composition_readability].filter(x => x != null)
  const minIdent = idents.length ? Math.min(...idents) : 0
  const minStyle = styles.length ? Math.min(...styles) : 0, maxStyle = styles.length ? Math.max(...styles) : 0
  const minComp = comps.length ? Math.min(...comps) : 0, maxComp = comps.length ? Math.max(...comps) : 0
  const gemArt = gem?.artifact_severity ?? 0, cdxArt = cdx?.artifact_severity ?? 0
  const artifactBad = (gemArt >= 4 && cdxArt >= 3) || (cdxArt >= 4 && gemArt >= 3)   // corroborated only
  const disagree = Math.abs((gem?.identity_consistency ?? 0) - (cdx?.identity_consistency ?? 0))
  const styleOK = minStyle >= 4 || (minStyle >= 3 && maxStyle >= 4)   // soften subjective dims to one-reviewer strictness
  const compOK = minComp >= 4 || (minComp >= 3 && maxComp >= 4)
  const repair = cdx?.failure_mode_positive_invariant || gem?.failure_mode_positive_invariant || ''
  // ── TEXT-MODE-AWARE check (the §16.9 fork point; HARDENED after the cross-model engine review) ──
  //  html mode  : the image is TEXTLESS → require a clean SAFE-ZONE for HTML overlay, fail on ANY baked glyph.
  //  baked mode : dialogue + the technical figure are baked IN on purpose. The figure is the CONTENT AUTHORITY, so faithfulness
  //    is NOT a (rubber-stampable) visual score — it is a DETERMINISTIC TOKEN-DIFF: every authored cfg.expected_literal must be
  //    independently READ by a reviewer (reviewers are NOT told the expected values → no confirmation bias), AND any garbled/
  //    wrong glyph is a SINGLE-vote veto (content_corruption_present), AND both reviewers must score bubble legibility ≥4.
  //    This is the plausible-unsupported-success guard: a beautiful panel with a WRONG number must NOT keep.
  let textOK, textReason
  if (baked) {
    const btqs = [gem?.baked_text_quality, cdx?.baked_text_quality]
    const bothBtq = btqs.every(x => x != null)                                   // BOTH reviewers must score legibility
    const minBtq = bothBtq ? Math.min(...btqs) : 0
    const corruption = gem?.content_corruption_present === true || cdx?.content_corruption_present === true  // single-vote veto
    const norm = s => String(s).toLowerCase().replace(/\s+/g, '')
    const exp = (cfg.expected_literals || []).map(norm).filter(Boolean)
    const seen = [...(gem?.observed_literals || []), ...(cdx?.observed_literals || [])].map(norm)
    const missing = exp.filter(e => !seen.some(s => s.includes(e) || e.includes(s)))   // each authored literal read by ≥1 reviewer
    const tokensOK = missing.length === 0
    textOK = bothBtq && minBtq >= 4 && !corruption && tokensOK
    textReason = `btq=${bothBtq ? minBtq : 'MISSING-reviewer'} corruption=${corruption} missingLiterals=[${missing.join('|')}]`
  } else {
    const safezone = gem?.safezone_present === true || cdx?.safezone_present === true   // either confirms
    const strayText = (gem?.stray_text_present === true) || (cdx?.stray_text_present === true) // either sees text → fail
    textOK = safezone && !strayText
    textReason = `safezone=${safezone} stray=${strayText}`
  }
  const reason = `[${mode}] narr=${narr} identity=${minIdent} style=${minStyle}/${maxStyle} comp=${minComp}/${maxComp} art(g/c)=${gemArt}/${cdxArt} ${textReason} disagreeId=${disagree}`
  if (narr >= 4 && minIdent >= 4 && styleOK && compOK && !artifactBad && textOK && disagree < 2) {
    return { v: 'keep', reason: 'KEEP — ' + reason, invariant: '' }
  }
  // everything else = retry the SAME panel with the repair invariant injected (no cross-panel rollback for seed-anchored comics)
  return { v: 'retry_panel', reason: 'RETRY — ' + reason, invariant: repair }
}

function assemblyVerdict(cc, gem) {
  const minDim = Math.min(cc?.reading_order ?? 0, cc?.page_rhythm ?? 0, gem?.cross_panel_identity ?? 0, gem?.cross_panel_style ?? 0, gem?.text_fits_safezone ?? 0)
  const sum = (cc?.reading_order ?? 0) + (cc?.page_rhythm ?? 0) + (gem?.cross_panel_identity ?? 0) + (gem?.cross_panel_style ?? 0) + (gem?.text_fits_safezone ?? 0)
  if (minDim < 2 || sum < 16) return { v: 'rollback', reason: `assembly weak (min=${minDim} sum=${sum}/25)` }
  return { v: 'accept', reason: `assembly ok (min=${minDim} sum=${sum}/25)` }
}

// ── schemas ──
const GEN_SCHEMA = { type: 'object', required: ['status', 'image_path'], properties: {
  status: { type: 'string', enum: ['panel_ready', 'generation_failed'] }, image_path: { type: 'string' }, bytes: { type: 'number' }, gen_failed_reason: { type: 'string' },
  text_mode: { type: 'string' }, content_figure_png: { type: 'string' }, baked_numbers_verified: { type: 'string' }, notes: { type: 'string' } } }
const COND_SCHEMA = { type: 'object', required: ['panels'], properties: { panels: { type: 'object' } } }
const CC_SCHEMA = { type: 'object', required: ['narrative_beat_fidelity', 'composition_story'], properties: {
  narrative_beat_fidelity: { type: 'number' }, composition_story: { type: 'number' }, timed_out: { type: 'boolean' }, notes: { type: 'string' } } }
// VIS_SCHEMA: html reviewers fill safezone_present/stray_text_present; baked reviewers fill observed_literals (verbatim
// transcription of the numbers/labels/code they can READ — NOT told the expected values), content_corruption_present, baked_text_quality.
const VIS_SCHEMA = { type: 'object', required: ['identity_consistency', 'style_consistency', 'composition_readability', 'artifact_severity'], properties: {
  identity_consistency: { type: 'number' }, style_consistency: { type: 'number' }, composition_readability: { type: 'number' },
  artifact_severity: { type: 'number' }, safezone_present: { type: 'boolean' }, stray_text_present: { type: 'boolean' },
  baked_text_quality: { type: 'number' }, observed_literals: { type: 'array', items: { type: 'string' } }, content_corruption_present: { type: 'boolean' },
  failure_mode_positive_invariant: { type: 'string' }, timed_out: { type: 'boolean' }, notes: { type: 'string' } } }
const WIKI_SCHEMA = { type: 'object', required: ['wrote_nodes'], properties: { wrote_nodes: { type: 'array', items: { type: 'string' } }, failure_mode_id: { type: ['string', 'null'] } } }
const ASM_CC_SCHEMA = { type: 'object', required: ['reading_order', 'page_rhythm'], properties: { reading_order: { type: 'number' }, page_rhythm: { type: 'number' }, notes: { type: 'string' } } }
const ASM_VIS_SCHEMA = { type: 'object', required: ['cross_panel_identity', 'cross_panel_style', 'text_fits_safezone'], properties: { cross_panel_identity: { type: 'number' }, cross_panel_style: { type: 'number' }, text_fits_safezone: { type: 'number' }, timed_out: { type: 'boolean' }, notes: { type: 'string' } } }

// ── generation: CONTENT-CONDITIONED BAKE (the deterministic-SVG → codex narrative-figure technique) ──
// Per panel the engine reads comic.json .condition {content_svg, world, scene, chibi_action} + .bubbles, renders the
// content_svg → a deterministic PNG blueprint, then bakes ONE comic panel with codex image_gen using EXACTLY TWO refs
// (the blueprint #1 + the canonical duo #2 — a 3rd ref dilutes identity). The blueprint is the CONTENT AUTHORITY: its
// numbers/labels/code are ground truth and must survive verbatim (verified in STEP 4 = the gate's faithfulness contract).
const BAKE_LANG = (args && args.bakeLang) || 'zh'   // which bubble language to bake (image bakes one); zh proven clean

// loadConditions: read comic.json ONCE (the sandbox has no fs) → structured per-panel config. This is the source of truth
// for text_mode + expected_literals + concrete scene/bubbles (so the gen command has NO placeholders for an agent to fill).
function loadConditions() {
  return agent([
    `Read "${COMICJSON}" and return the per-panel generation config for EXACTLY these panels: ${JSON.stringify(PANEL_IDS)}.`,
    `For each pid return an object with: text_mode (the panel's .text_mode), content_svg (.condition.content_svg, a project-relative path or null), world (.condition.world), scene (.condition.scene), chibi_executor (.condition.chibi_action.executor), chibi_reviewer (.condition.chibi_action.reviewer), bubble_executor (the .bubbles entry with speaker=="executor" → its text.${BAKE_LANG}, else ""), bubble_reviewer (speaker=="reviewer" → text.${BAKE_LANG}, else ""), expected_literals (copy the panel's .condition.expected_literals array verbatim, or []).`,
    `Return COND_SCHEMA: {panels: {"S12": {...}, ...}}. READ ONLY — do not generate or render anything.`,
  ].join('\n'), { label: 'load-conditions', phase: 'Panels', schema: COND_SCHEMA })
}

function generatePanel(pid, cfg = {}, ctx = {}) {
  const ai = ctx.attemptIndex || 1
  const aTag = 'a' + String(ai).padStart(2, '0')
  const out = `${PANELS}/${pid}_panel_${aTag}.png`
  const cdir = `${PANELS}/_content_refs`
  const cpng = `${cdir}/${pid}_${aTag}.png`   // PERSISTENT blueprint (NOT /tmp) — the gate + wiki reference it across resume/cleanup
  // shell-safe: content_svg must be a project-relative .svg with no traversal/metachars (it is interpolated into a file:// path)
  const svgRel = cfg.content_svg || ''
  if (!/^[\w][\w./-]*\.svg$/.test(svgRel) || svgRel.includes('..')) {
    return Promise.resolve({ status: 'generation_failed', image_path: '', text_mode: cfg.text_mode || '', gen_failed_reason: `unsafe/empty content_svg: ${JSON.stringify(svgRel)} (expected project-relative *.svg)` })
  }
  const repairLine = (ctx.invariants || []).filter(Boolean).length
    ? 'REPAIR CONSTRAINTS (earlier attempts failed for these reasons — honor every one): ' + ctx.invariants.filter(Boolean).join('  |  ')
    : ''
  // Build the bake prompt body with CONCRETE values (no <placeholders>). The agent writes it via a quoted heredoc, so
  // quotes / CJK / special chars in scene+bubbles can't break the shell command.
  const promptBody = [
    `WORLD = ${cfg.world}  → apply the ART_BIBLE §0.5 two-world lighting (warm-lab = warm Edison-glow human world; dark-cyber = dark screen-lit digital world).`,
    `SCENE: ${cfg.scene}`,
    `Render the CANONICAL DUO from reference image #2 (blue executor: brown hair, NO beard; green reviewer: dark hair, beard). executor action: ${cfg.chibi_executor}. reviewer action: ${cfg.chibi_reviewer}.`,
    `Integrate the technical figure from reference image #1 onto a board/screen/dashboard in the scene. Reproduce its numbers, labels and code EXACTLY as they appear in image #1 — do NOT alter, re-spell, round, or invent any number or token.`,
    `Bake these two speech bubbles as clean readable comic lettering (${BAKE_LANG}): executor says: ${cfg.bubble_executor}  ||  reviewer says: ${cfg.bubble_reviewer}`,
    `ONE coherent flat pixel-art comic panel. No watermark. No UI text beyond the integrated figure and the two bubbles.`,
    repairLine,
  ].filter(Boolean).join('\n')
  return agent([
    `You are the Codex CONTENT-CONDITIONED BAKE executor for ARIS comic panel ${pid} (attempt ${ai}, mode=${cfg.text_mode}). Bake ONE pixel-art panel fusing a deterministic technical FIGURE (the content blueprint = GROUND TRUTH; its numbers must survive verbatim) with the canonical chibi duo + baked dialogue.`, '',
    `STEP 1 — render the content blueprint SVG → a PERSISTENT PNG (watchdog-bounded):`,
    '```bash',
    `mkdir -p "${cdir}"`,
    `CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`,
    `( "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 --window-size=1280,720 --screenshot="${cpng}" "file://${PROJ}/${svgRel}" >/dev/null 2>&1 ) & P=$!; ( sleep 30; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null`,
    `[ -s "${cpng}" ] && echo "CONTENT_PNG_OK $(stat -f%z ${cpng})" || { echo "CONTENT_PNG_FAIL"; exit 0; }`,
    '```',
    `STEP 2 — assemble the bake prompt = ART_BIBLE rules + the panel body below, then BAKE (codex image_gen; EXACTLY 2 refs: blueprint #1 + canonical duo #2). image_gen may be RATE-LIMITED — on error DO NOT fall back to PIL/SVG, report generation_failed:`,
    '```bash',
    `cat > /tmp/bake_${pid}_${aTag}.txt <<'PROMPTEOF'`,
    promptBody,
    `PROMPTEOF`,
    `( printf 'Paste these style rules first:\\n%s\\n\\nThen render this panel:\\n' "$(cat "${BIBLE}")"; cat /tmp/bake_${pid}_${aTag}.txt ) > /tmp/bakefull_${pid}_${aTag}.txt`,
    `M=/tmp/cm_${pid}_${aTag}; touch "$M"`,
    `setsid codex exec "$(cat /tmp/bakefull_${pid}_${aTag}.txt)" -i "${cpng}" -i "${CANON}" --sandbox workspace-write -c model_reasoning_effort=high --skip-git-repo-check < /dev/null > /tmp/cm_${pid}_${aTag}.log 2>&1 & P=$!`,
    `( sleep 480; kill -9 -$P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; pkill -9 -P $P 2>/dev/null`,   // kill the whole process group → no orphan image_gen polluting the next panel
    `NEW=$(find ~/.codex/generated_images -name '*.png' -newer "$M" 2>/dev/null | sort | tail -1); SZ=$(stat -f%z "$NEW" 2>/dev/null || echo 0)`,
    `if [ -n "$NEW" ] && [ "$SZ" -gt 500000 ]; then cp "$NEW" "${out}"; echo "GEN_OK ${out} $SZ"; else echo "GEN_FAIL size=$SZ (image_gen errored / rate-limited)"; fi`,
    '```',
    `STEP 3 — return GEN_SCHEMA: status MUST be "panel_ready" ONLY if you saw "GEN_OK" and "${out}" is >500KB, else "generation_failed". image_path="${out}", bytes (the real size), text_mode="${cfg.text_mode}", content_figure_png="${cpng}", gen_failed_reason (quote the codex/image_gen error if failed), notes. Do NOT self-attest the numbers — faithfulness is judged by the gate.`,
  ].join('\n'), { label: `gen:${pid}#${ai}`, phase: 'Panels', schema: GEN_SCHEMA })
}

// ── panel_gate: 3 independent cross-model reviewers → deterministic JS verdict ──
async function panelGate(pid, gen, cfg = {}) {
  const mode = cfg.text_mode || gen.text_mode || 'html'   // comic.json (cfg) is the SOURCE OF TRUTH for mode, not the generator's self-report
  const baked = mode === 'baked'
  const img = absImg(gen.image_path)
  const cc = agent([
    `You are the CC NARRATIVE reviewer in ARIS comic panel_gate for ${pid} (mode=${mode}). Judge STORY only (you may glance at the panel at "${gen.image_path}" but score narrative, not pixels).`,
    `Read panel ${pid} from "${COMICJSON}": its .condition.scene, its .bubbles (the intended dialogue), .caption, and the page's beat narration. Score 0-5: narrative_beat_fidelity (does this panel deliver its beat in the audit story?), composition_story (does the staging${baked ? ' + the baked figure/dialogue' : ''} read the story right?). Return CC_SCHEMA.`,
  ].join('\n'), { label: `gate-cc:${pid}`, phase: 'Panels', schema: CC_SCHEMA })

  // Visual reviewers get ONLY the panel + canonical duo + ART_BIBLE — NOT the content blueprint. baked faithfulness is judged by a
  // BLIND transcription (observed_literals) deterministically diffed against authored ground truth in JS, so reviewers must never
  // see the expected numbers (else they rubber-stamp). They also flag content_corruption_present (garbled/illegible glyphs).
  const gemJson = baked
    ? `{\\"identity_consistency\\":n,\\"style_consistency\\":n,\\"composition_readability\\":n,\\"artifact_severity\\":n,\\"baked_text_quality\\":n,\\"observed_literals\\":[\\"...\\"],\\"content_corruption_present\\":true/false,\\"failure_mode_positive_invariant\\":\\"...\\"}。baked_text_quality=气泡对白文字是否清晰可读不乱码;observed_literals=逐字转录你能在画中【技术图】里确实看清的数字/标签/代码token(如 +6.2、jsonschema),只转录看清的,严禁猜测或补全;content_corruption_present=技术图里是否有明显乱码/残缺/不合法的数字或代码。`
    : `{\\"identity_consistency\\":n,\\"style_consistency\\":n,\\"composition_readability\\":n,\\"artifact_severity\\":n,\\"safezone_present\\":true/false,\\"stray_text_present\\":true/false,\\"failure_mode_positive_invariant\\":\\"...\\"}。safezone=有没有留干净文字区;stray_text=图里有没有冒出文字/字形。`
  const gem = agent([
    `You are the GEMINI VISUAL reviewer in ARIS comic panel_gate for ${pid} (mode=${mode}, independent — do not consult other scores). Use watchdog-bounded CLI:`,
    '```bash',
    `( gemini --model auto-gemini-3 -p "@${img} @${CANON} @${BIBLE} 评这张漫画面板(第1张):对照 canonical 双人(蓝executor棕发无须/绿reviewer黑发有须)与 ART_BIBLE。打分0-5并只输出一行紧凑JSON: ${gemJson}" < /dev/null > /tmp/gg_${pid}.txt 2>&1 ) & P=$!`,
    `( sleep 240; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 1500 /tmp/gg_${pid}.txt`,
    '```',
    `Parse the JSON gemini emitted into VIS_SCHEMA. If gemini gave no parseable scores, set timed_out=true.`,
  ].join('\n'), { label: `gate-gem:${pid}`, phase: 'Panels', schema: VIS_SCHEMA })

  const cdxJson = baked
    ? `{\\"identity_consistency\\":n,\\"style_consistency\\":n,\\"composition_readability\\":n,\\"artifact_severity\\":n,\\"baked_text_quality\\":n,\\"observed_literals\\":[\\"...\\"],\\"content_corruption_present\\":true/false,\\"failure_mode_positive_invariant\\":\\"...\\"} (0-5)。baked_text_quality=气泡烤字是否清晰不乱码;observed_literals=逐字转录画中技术图你确实看清的数字/标签/代码,严禁猜测;content_corruption_present=有无明显乱码/残缺/不合法数字或代码。`
    : `{\\"identity_consistency\\":n,\\"style_consistency\\":n,\\"composition_readability\\":n,\\"artifact_severity\\":n,\\"safezone_present\\":true/false,\\"stray_text_present\\":true/false,\\"failure_mode_positive_invariant\\":\\"...\\"} (0-5)。`
  const cdx = agent([
    `You are the CODEX VISUAL reviewer in ARIS comic panel_gate for ${pid} (mode=${mode}, independent SECOND visual model — covers what Gemini's eye misses). Use watchdog-bounded CLI (codex vision review is NOT image_gen, not rate-limited):`,
    '```bash',
    `( codex exec "审这张漫画面板(第1张):对照 canonical 双人参考与 ART_BIBLE,评身份/画风/构图/瑕疵${baked ? ' + 气泡烤字清晰度 + 逐字转录技术图数字' : '/留白/有无杂字'}。只输出一行JSON: ${cdxJson}" -i "${img}" -i "${CANON}" -i "${BIBLE}" --skip-git-repo-check < /dev/null > /tmp/cc_${pid}.txt 2>&1 ) & P=$!`,
    `( sleep 300; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 1500 /tmp/cc_${pid}.txt`,
    '```',
    `Parse codex's JSON into VIS_SCHEMA. If none, timed_out=true.`,
  ].join('\n'), { label: `gate-cdx:${pid}`, phase: 'Panels', schema: VIS_SCHEMA })

  const [ccR, gemR, cdxR] = await Promise.all([cc, gem, cdx])
  return { cc: ccR, gem: gemR, cdx: cdxR, mode, verdict: panelVerdict(ccR, gemR, cdxR, cfg) }
}

function writeWiki(pid, gen, gate, ai) {
  const aTag = 'a' + String(ai).padStart(2, '0')
  const sl = pid.toLowerCase()
  const v = gate.verdict.v
  return agent([
    `Write ARIS comic wiki active-memory nodes for panel ${pid} attempt ${ai} into ${NODES}/ (one JSON file each; mirror the video clip nodes). created_at "2026-06-08T00:00:00+00:00".`,
    `1) panel_attempt → ${NODES}/panel_attempt_${sl}_${aTag}.json: {node_id:"attempt:${sl}_${aTag}",node_type:"panel_attempt",status:"under_review",title:"${pid} panel attempt ${ai}",payload:{source_panel_id:"panel:${sl}_aris_comic_v1",image_path:${JSON.stringify(gen.image_path)},attempt_index:${ai},model:"codex_image_gen",is_baked_duo:true}}`,
    `2) review → review_panel_${sl}_${aTag}_{cc,gemini,codex}.json: one per reviewer, node_type:"review", payload holds that reviewer's scores from: CC=${JSON.stringify(gate.cc).slice(0, 300)} GEM=${JSON.stringify(gate.gem).slice(0, 300)} CDX=${JSON.stringify(gate.cdx).slice(0, 300)}`,
    `3) decision → decision_panel_${sl}_${aTag}.json: {node_id:"decision:panel_${sl}_${aTag}",node_type:"decision",status:"final",title:"panel_gate ${pid} a${ai} → ${v}",payload:{gate_kind:"panel",target_node_id:"attempt:${sl}_${aTag}",verdict:"${v}",reasoning:${JSON.stringify(gate.verdict.reason.slice(0, 300))},repair_instruction:${JSON.stringify(gate.verdict.invariant || '')}}}`,
    v !== 'keep' ? `4) failure_mode → fail_${sl}_${aTag}.json: {node_id:"fail:${sl}_${aTag}",node_type:"failure_mode",payload:{active:true,affected_shot_ids:["${pid}"],layer:"panel_visual",repair_pattern:${JSON.stringify(gate.verdict.invariant || '')}}}` : '(no failure_mode on keep)',
    `Return WIKI_SCHEMA {wrote_nodes:[ids], failure_mode_id}.`,
  ].join('\n'), { label: `wiki:${pid}#${ai}`, phase: 'Panels', schema: WIKI_SCHEMA })
}

// ── main loop: per-panel spiral with attempt-path (SEED-ANCHORED: retry the SAME panel, NEVER roll back to a prior panel) ──
phase('Panels')
// Load the per-panel condition ONCE (the sandbox has no fs). CONFIG is the SOURCE OF TRUTH for text_mode + expected_literals
// + the concrete scene/bubbles the gen command interpolates — so the gate's mode + faithfulness check can't be bypassed.
const CONFIG = (await loadConditions())?.panels || {}
log(`loaded conditions: ${Object.keys(CONFIG).join(' ') || '(NONE — comic.json unreadable)'}`)
let kept = []
const totalByPanel = {}, pending = {}
let escalated = null, throttled = false
const flagged = []                 // panels accepted best-so-far for HUMAN review (design R10)
for (let i = 0; i < PANEL_IDS.length && !throttled; i++) {
  const pid = PANEL_IDS[i]
  const cfg = CONFIG[pid] || {}
  let done = false, lastGen = null
  while (!done && (totalByPanel[pid] || 0) < MAX_TOTAL) {
    totalByPanel[pid] = (totalByPanel[pid] || 0) + 1
    const ai = totalByPanel[pid]
    const invariants = (pending[pid] || []).slice()
    log(`▶ ${pid} attempt ${ai} [${cfg.text_mode || '??'}]${invariants.length ? ' +' + invariants.length + ' repair' : ''}`)
    const gen = await generatePanel(pid, cfg, { attemptIndex: ai, invariants })
    // STRICT accept: only a genuine panel_ready with a real >500KB image reaches the gate (no loose status string slips through)
    if (!gen || gen.status !== 'panel_ready' || !gen.image_path || (gen.bytes || 0) <= 500000) {
      const reason = gen?.gen_failed_reason || `not panel_ready (status=${gen?.status} bytes=${gen?.bytes})`
      log(`  ✗ gen failed: ${reason}`)
      if (/rate|limit|throttl|server|unavailable|429|quota/i.test(reason)) {  // image_gen throttled → stop cleanly, resume after cooldown
        throttled = true; escalated = { pid, why: 'image_gen rate-limited mid-run — stop + resume after cooldown' }; break
      }
      continue  // non-throttle gen failure → retry this panel (until cap)
    }
    lastGen = gen
    const gate = await panelGate(pid, gen, cfg)
    await writeWiki(pid, gen, gate, ai)
    log(`  panel_gate ${pid}#${ai}: ${gate.verdict.v} — ${gate.verdict.reason}`)
    if (gate.verdict.v === 'keep') { kept.push({ pid, image_path: gen.image_path, attempt: ai, needs_human: false }); done = true; break }
    if (gate.verdict.invariant) pending[pid] = [...(pending[pid] || []), gate.verdict.invariant]  // retry SAME panel w/ repair
  }
  if (throttled) break
  if (!done) {
    if (lastGen) { kept.push({ pid, image_path: lastGen.image_path, attempt: totalByPanel[pid], needs_human: true }); flagged.push(pid); log(`  ⚑ ${pid} exhausted ${MAX_TOTAL} attempts → best-so-far flagged for HUMAN review (R10), continuing`) }
    else { escalated = escalated || { pid, why: 'no panel ever generated (image_gen down?)' }; break }
  }
}

// ── page assembly_gate ──
let asm = null
if (!escalated && kept.length >= 2) {
  phase('Assembly')
  const list = kept.map(k => `@${absImg(k.image_path)}`).join(' ')   // @ prefix so gemini actually loads the panel images (review fix)
  const acc = agent([
    `You are the CC reviewer for ARIS comic PAGE assembly_gate (page ${PAGE}). The kept panels in reading order: ${kept.map(k => k.pid).join(' → ')}.`,
    `Read the page's narration/beat from "${COMICJSON}" (page ${PAGE}). Score 0-5: reading_order (do the panels flow left→right/top→bottom and tell the beat?), page_rhythm (does the 2x2 / sequence pace well?). Return ASM_CC_SCHEMA.`,
  ].join('\n'), { label: `asm-cc:${PAGE}`, phase: 'Assembly', schema: ASM_CC_SCHEMA })
  const avis = agent([
    `You are the GEMINI visual reviewer for ARIS comic PAGE assembly (page ${PAGE}); judge the panels SIDE BY SIDE for drift. Watchdog CLI:`,
    '```bash',
    `( gemini --model auto-gemini-3 -p "@${CANON} 这些是同一页要并排的漫画格(按顺序): ${list} . 并排看跨格一致性,输出一行JSON {\\"cross_panel_identity\\":n,\\"cross_panel_style\\":n,\\"text_fits_safezone\\":n} (0-5; identity=双人跨格是否同一身份;style=画风是否一致;text_fits_safezone=各格留白区是否足够放气泡)。gutter 容差:跨格轻微光照/风格差正常,只标可识别的身份断裂或画风大不一致。" < /dev/null > /tmp/asm_${PAGE}.txt 2>&1 ) & P=$!`,
    `( sleep 240; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 1200 /tmp/asm_${PAGE}.txt`,
    '```',
    `Parse into ASM_VIS_SCHEMA (timed_out=true if none).`,
  ].join('\n'), { label: `asm-gem:${PAGE}`, phase: 'Assembly', schema: ASM_VIS_SCHEMA })
  const [accR, avisR] = await Promise.all([acc, avis])
  asm = { cc: accR, gem: avisR, verdict: assemblyVerdict(accR, avisR) }
  log(`  assembly_gate ${PAGE}: ${asm.verdict.v} — ${asm.verdict.reason}`)
}

return {
  page: PAGE,
  panel_ids: PANEL_IDS,
  kept: kept,
  flagged_for_human: flagged,
  throttled,
  escalated,
  assembly: asm ? asm.verdict : null,
  attempts_per_panel: totalByPanel,
  finalize: FINALIZE,
}
