export const meta = {
  name: 'aris-comic-spiral-engine',
  description: 'ARIS COMIC per-panel spiral (fork of the video spiral_engine, §16.9 shape preserved). Per panel: generatePanel (codex image_gen -i seed -i duo_canonical, ART_BIBLE-constrained, NO text, leave safe-zone) → panel_gate (CC narrative ‖ Gemini visual-CLI ‖ Codex visual-CLI → deterministic JS verdict, scored against ART_BIBLE) → WRITE wiki (panel_attempt/review/decision/failure_mode) → keep/retry/rollback (force-regen with failure_mode positive-invariant; attempt-path bypass; caps 4/panel, 6/run) → page assembly_gate. Swapped vs video: generator (Seedance i2v → codex image_gen), rubric (motion dims → static/identity/style dims), output (mp4 → PNG + comic.json projection). NOT batch.',
  phases: [
    { title: 'Panels', detail: 'per panel: generate → panel_gate (3 cross-model) → wiki → keep/retry/rollback' },
    { title: 'Assembly', detail: 'page-level assembly_gate: cross-panel identity/style + reading order + safe-zones' },
  ],
}

const REPO = process.env.ARIS_ROOT || process.cwd()
const PROJ = REPO + '/examples/comic_m3_audit'
const SEEDS = PROJ + '/seeds'
const PANELS = PROJ + '/panels'
const NODES = PROJ + '/wiki/nodes'
const CANON = PROJ + '/assets/duo_canonical_ref_v001.png'
const BIBLE = PROJ + '/ART_BIBLE.md'
const COMICJSON = PROJ + '/comic.json'
const STORY = PROJ + '/movie.project.json'

// P0 default target = the B08 wiki-rollback page (the centerpiece, 4 panels). Override via args.panelIds.
const PAGE = (args && args.page) || 'P02_b08'
const PANEL_IDS = (args && args.panelIds) || ['S12', 'S13', 'S14', 'S15']
const MAX_LOCAL = 3, MAX_TOTAL = 4, MAX_ROLLBACKS = 6
const FINALIZE = (args && args.finalize === true) || false
const absImg = (p) => !p ? '' : (p.startsWith('/') ? p : REPO + '/' + p)  // resolve panel image path (abs or repo-rel) — one helper, no string hacks

// ── deterministic verdicts (formula over independent cross-model reviewers) ──
// Verdict for a SEED-ANCHORED comic panel. Calibrated after the first real B08 run:
//  - panels are independent (no chain) → only KEEP or RETRY-SAME-PANEL, NEVER rollback-to-prior.
//  - artifact must be CORROBORATED by both visual reviewers (a lone pixel-purist scoring the
//    background atmospheric glow as artifact=5 must not single-vote-veto — ART_BIBLE allows bg gradients).
//  - safe-zone present if EITHER reviewer confirms (they disagree on detection); stray text fails if EITHER sees it.
//  - identity stays strict (linchpin, reviewers agree); style/comp soften to tolerate one-reviewer strictness.
function panelVerdict(cc, gem, cdx) {
  const timeout = cc?.timed_out || gem?.timed_out || cdx?.timed_out
  if (timeout) return { v: 'retry_panel', reason: 'a reviewer timed out — fail-safe retry', invariant: '' }
  const narr = Math.min(cc?.narrative_beat_fidelity ?? 0, cc?.composition_story ?? 5)
  const idents = [gem?.identity_consistency, cdx?.identity_consistency].filter(x => x != null)
  const styles = [gem?.style_consistency, cdx?.style_consistency].filter(x => x != null)
  const comps = [gem?.composition_readability, cdx?.composition_readability].filter(x => x != null)
  const minIdent = idents.length ? Math.min(...idents) : 0
  const minStyle = styles.length ? Math.min(...styles) : 0, maxStyle = styles.length ? Math.max(...styles) : 0
  const minComp = comps.length ? Math.min(...comps) : 0, maxComp = comps.length ? Math.max(...comps) : 0
  const gemArt = gem?.artifact_severity ?? 0, cdxArt = cdx?.artifact_severity ?? 0
  const artifactBad = (gemArt >= 4 && cdxArt >= 3) || (cdxArt >= 4 && gemArt >= 3)   // corroborated only
  const safezone = gem?.safezone_present === true || cdx?.safezone_present === true   // either confirms
  const strayText = (gem?.stray_text_present === true) || (cdx?.stray_text_present === true) // html mode: either sees text → fail
  const disagree = Math.abs((gem?.identity_consistency ?? 0) - (cdx?.identity_consistency ?? 0))
  const styleOK = minStyle >= 4 || (minStyle >= 3 && maxStyle >= 4)   // soften subjective dims to one-reviewer strictness
  const compOK = minComp >= 4 || (minComp >= 3 && maxComp >= 4)
  const repair = cdx?.failure_mode_positive_invariant || gem?.failure_mode_positive_invariant || ''
  const reason = `narr=${narr} identity=${minIdent} style=${minStyle}/${maxStyle} comp=${minComp}/${maxComp} art(g/c)=${gemArt}/${cdxArt} safezone=${safezone} stray=${strayText} disagreeId=${disagree}`
  if (narr >= 4 && minIdent >= 4 && styleOK && compOK && !artifactBad && safezone && !strayText && disagree < 2) {
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
  status: { type: 'string' }, image_path: { type: 'string' }, bytes: { type: 'number' }, gen_failed_reason: { type: 'string' }, notes: { type: 'string' } } }
const CC_SCHEMA = { type: 'object', required: ['narrative_beat_fidelity', 'composition_story'], properties: {
  narrative_beat_fidelity: { type: 'number' }, composition_story: { type: 'number' }, timed_out: { type: 'boolean' }, notes: { type: 'string' } } }
const VIS_SCHEMA = { type: 'object', required: ['identity_consistency', 'style_consistency', 'composition_readability', 'artifact_severity', 'safezone_present'], properties: {
  identity_consistency: { type: 'number' }, style_consistency: { type: 'number' }, composition_readability: { type: 'number' },
  artifact_severity: { type: 'number' }, safezone_present: { type: 'boolean' }, stray_text_present: { type: 'boolean' },
  failure_mode_positive_invariant: { type: 'string' }, timed_out: { type: 'boolean' }, notes: { type: 'string' } } }
const WIKI_SCHEMA = { type: 'object', required: ['wrote_nodes'], properties: { wrote_nodes: { type: 'array', items: { type: 'string' } }, failure_mode_id: { type: ['string', 'null'] } } }
const ASM_CC_SCHEMA = { type: 'object', required: ['reading_order', 'page_rhythm'], properties: { reading_order: { type: 'number' }, page_rhythm: { type: 'number' }, notes: { type: 'string' } } }
const ASM_VIS_SCHEMA = { type: 'object', required: ['cross_panel_identity', 'cross_panel_style', 'text_fits_safezone'], properties: { cross_panel_identity: { type: 'number' }, cross_panel_style: { type: 'number' }, text_fits_safezone: { type: 'number' }, timed_out: { type: 'boolean' }, notes: { type: 'string' } } }

// ── generation ──
function generatePanel(pid, ctx = {}) {
  const ai = ctx.attemptIndex || 1
  const aTag = 'a' + String(ai).padStart(2, '0')
  const seed = `${SEEDS}/${pid}_seed.png`
  const out = `${PANELS}/${pid}_panel_${aTag}.png`
  const invBlock = (ctx.invariants || []).filter(Boolean).length
    ? 'ACTIVE REPAIR MEMORY (from wiki failure_modes — generation constraints because earlier attempts failed for these reasons; honor them):\n' + ctx.invariants.filter(Boolean).map((x, k) => '  ' + (k + 1) + '. ' + x).join('\n')
    : ''
  return agent([
    `You are the Codex IMAGE-GEN executor for ARIS comic panel ${pid} (attempt ${ai}). You command codex's built-in image_generation tool via the CLI; it is the black-box visual generator.`,
    invBlock, '',
    `STEP 1 — READ the style contract + this panel's intent:`,
    `  - cat "${BIBLE}"  (the ART BIBLE — paste its rules into your gen prompt; it is the convergence target)`,
    `  - read panel "${pid}" from "${COMICJSON}" (its beat, safe_zones, and whether it carries the duo)`,
    `  - read shot "${pid}" from "${STORY}" (serves_beat_id, on_screen_text, audio_directives, shot_notes) for the panel's narrative intent`,
    ``,
    `STEP 2 — GENERATE (watchdog-bounded CLI; image_gen may be RATE-LIMITED right now — if it errors, DO NOT fall back to PIL/SVG, report gen_failed):`,
    '```bash',
    `M=/tmp/cm_${pid}_${aTag}; touch "$M"`,
    `( codex exec "<your full prompt: ART_BIBLE rules + finalize seed into a flat pixel-art comic panel matching the canonical duo identity (blue executor brown-hair no-beard / green reviewer dark-hair beard) + this panel's beat intent + 'draw NO text, NO bubbles, NO glyphs; leave a clean low-detail SAFE ZONE per comic.json safe_zones for HTML text' >" -i "${seed}" -i "${CANON}" --sandbox workspace-write -c model_reasoning_effort=high --skip-git-repo-check < /dev/null > /tmp/cm_${pid}_${aTag}.log 2>&1 ) & P=$!`,
    `( sleep 420; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null`,
    `NEW=$(find ~/.codex/generated_images -name '*.png' -newer "$M" 2>/dev/null | head -1); SZ=$(stat -f%z "$NEW" 2>/dev/null || echo 0)`,
    `if [ -n "$NEW" ] && [ "$SZ" -gt 500000 ]; then cp "$NEW" "${out}"; echo "GEN_OK ${out} $SZ"; else echo "GEN_FAIL size=$SZ (image_gen errored / rate-limited)"; fi`,
    '```',
    `STEP 3 — extract first dense frame is N/A (static). Verify "${out}" exists + is a real AI image (>500KB, NOT a tiny PIL render).`,
    `Return GEN_SCHEMA: status ("panel_ready" | "generation_failed"), image_path="${out}" (relative ok), bytes, gen_failed_reason (if failed: quote the codex/image_gen error), notes (include the exact prompt you used + provenance).`,
  ].join('\n'), { label: `gen:${pid}#${ai}`, phase: 'Panels', schema: GEN_SCHEMA })
}

// ── panel_gate: 3 independent cross-model reviewers → deterministic JS verdict ──
async function panelGate(pid, gen) {
  const img = absImg(gen.image_path)
  const cc = agent([
    `You are the CC NARRATIVE reviewer in ARIS comic panel_gate for ${pid}. Judge STORY only (you may glance at the panel image at "${gen.image_path}" but score narrative, not pixels).`,
    `Read the panel's beat + intent from "${COMICJSON}" (panel ${pid}) and "${STORY}" (shot ${pid}). Score 0-5: narrative_beat_fidelity (does this panel deliver its beat?), composition_story (does the staging read the story right?).`,
    `Return CC_SCHEMA.`,
  ].join('\n'), { label: `gate-cc:${pid}`, phase: 'Panels', schema: CC_SCHEMA })

  const gem = agent([
    `You are the GEMINI VISUAL reviewer in ARIS comic panel_gate for ${pid} (independent — do not consult other scores). Use watchdog-bounded CLI:`,
    '```bash',
    `( gemini --model auto-gemini-3 -p "@${img} @${CANON} @${BIBLE} 评这张漫画面板:对照第2张 canonical 双人(蓝executor棕发无须/绿reviewer黑发有须)和第3张 ART_BIBLE。打分0-5并输出一行紧凑JSON: {\\"identity_consistency\\":n,\\"style_consistency\\":n,\\"composition_readability\\":n,\\"artifact_severity\\":n,\\"safezone_present\\":true/false,\\"stray_text_present\\":true/false,\\"failure_mode_positive_invariant\\":\\"若有问题给一条可执行的正向修复约束\\"}。identity=是否身份对;style=是否合 ART_BIBLE 的 flat 像素风;artifact=瑕疵严重度;safezone=有没有留干净文字区;stray_text=图里有没有冒出文字/字形。" < /dev/null > /tmp/gg_${pid}.txt 2>&1 ) & P=$!`,
    `( sleep 220; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 1500 /tmp/gg_${pid}.txt`,
    '```',
    `Parse the JSON gemini emitted into VIS_SCHEMA. If gemini gave no parseable scores, set timed_out=true.`,
  ].join('\n'), { label: `gate-gem:${pid}`, phase: 'Panels', schema: VIS_SCHEMA })

  const cdx = agent([
    `You are the CODEX VISUAL reviewer in ARIS comic panel_gate for ${pid} (independent SECOND visual model — covers what Gemini's eye misses). Use watchdog-bounded CLI (codex text/vision review is NOT image_gen, not rate-limited):`,
    '```bash',
    `( codex exec "对照 canonical 双人参考与 ART_BIBLE,审这张漫画面板的身份/画风/构图/瑕疵/留白/有无杂字。只输出一行JSON: {\\"identity_consistency\\":n,\\"style_consistency\\":n,\\"composition_readability\\":n,\\"artifact_severity\\":n,\\"safezone_present\\":true/false,\\"stray_text_present\\":true/false,\\"failure_mode_positive_invariant\\":\\"...\\"} (0-5)。" -i "${img}" -i "${CANON}" -i "${BIBLE}" --skip-git-repo-check < /dev/null > /tmp/cc_${pid}.txt 2>&1 ) & P=$!`,
    `( sleep 300; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 1500 /tmp/cc_${pid}.txt`,
    '```',
    `Parse codex's JSON into VIS_SCHEMA. If none, timed_out=true.`,
  ].join('\n'), { label: `gate-cdx:${pid}`, phase: 'Panels', schema: VIS_SCHEMA })

  const [ccR, gemR, cdxR] = await Promise.all([cc, gem, cdx])
  return { cc: ccR, gem: gemR, cdx: cdxR, verdict: panelVerdict(ccR, gemR, cdxR) }
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

// ── main loop: per-panel spiral with attempt-path + rollback ──
phase('Panels')
let kept = []
const totalByPanel = {}, pending = {}
let escalated = null, throttled = false
const flagged = []                 // panels accepted best-so-far for HUMAN review (design R10)
// SEED-ANCHORED: each panel is independent (no chain) → retry the SAME panel, NEVER roll back to a prior panel.
for (let i = 0; i < PANEL_IDS.length && !throttled; i++) {
  const pid = PANEL_IDS[i]
  let done = false, lastGen = null
  while (!done && (totalByPanel[pid] || 0) < MAX_TOTAL) {
    totalByPanel[pid] = (totalByPanel[pid] || 0) + 1
    const ai = totalByPanel[pid]
    const invariants = (pending[pid] || []).slice()
    log(`▶ ${pid} attempt ${ai}${invariants.length ? ' +' + invariants.length + ' repair' : ''}`)
    const gen = await generatePanel(pid, { attemptIndex: ai, invariants })
    if (!gen || gen.status === 'generation_failed') {
      const reason = gen?.gen_failed_reason || 'no image'
      log(`  ✗ gen failed: ${reason}`)
      if (/rate|limit|throttl|server|unavailable|429|quota/i.test(reason)) {  // image_gen throttled → stop cleanly, resume after cooldown
        throttled = true; escalated = { pid, why: 'image_gen rate-limited mid-run — stop + resume after cooldown' }; break
      }
      continue  // non-throttle gen failure → retry this panel (until cap)
    }
    lastGen = gen
    const gate = await panelGate(pid, gen)
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
