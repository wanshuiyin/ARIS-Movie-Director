export const meta = {
  name: 'aris-comic-spiral-engine',
  description: 'ARIS COMIC per-panel spiral (fork of the video spiral_engine, §16.9 shape preserved). Per panel: generatePanel (PREPARES the bake — render content blueprint → PNG + assemble the ART_BIBLE-constrained prompt + emit the bake contract: blueprint + duo refs by absolute path, NO text, leave safe-zone; the in-engine exec bake is RETIRED and hard-fails, so the ACTUAL agent mcp__codex__codex sidecar bake is fulfilled OUT-OF-PROCESS by the Python SOP `run_comic.py --bake-mode=agent` and verified by `pickup_image.py --out-existing`) → panel_gate (CC narrative ‖ Gemini visual-CLI ‖ Codex visual-CLI → deterministic JS verdict, scored against ART_BIBLE) → WRITE wiki (panel_attempt/review/decision/failure_mode) → keep/retry/rollback (force-regen with failure_mode positive-invariant; attempt-path bypass; caps 4/panel, 6/run) → page assembly_gate. Swapped vs video: generator (Seedance i2v → agent mcp__codex__codex image bake, fulfilled out-of-process via the Python SOP), rubric (motion dims → static/identity/style dims), output (mp4 → PNG + comic.json projection). NOT batch.',
  phases: [
    { title: 'Panels', detail: 'per panel: generate → panel_gate (3 cross-model) → wiki → keep/retry/rollback' },
    { title: 'Assembly', detail: 'page-level assembly_gate: cross-panel identity/style + reading order + safe-zones' },
  ],
}

// The engine runs in the Workflow sandbox (NO process.env / fs) → paths MUST come from `args`, not env.
// Caller passes args.projectRoot = ABSOLUTE path to the project/example dir (manifest-driven). No hardcoded paths.
// The Workflow harness has been observed to deliver `args` as a raw JSON STRING (not a parsed object) —
// every key read off it silently came back undefined and the engine ran its defaults. Normalize once:
const ARGS = (() => { if (typeof args === 'string') { try { return JSON.parse(args) } catch { return {} } } return args || {} })()
const PROJ = ARGS.projectRoot || ''
const REPO = ARGS.repoRoot || PROJ.replace(/\/examples\/[^/]+\/?$/, '')
const SEEDS = PROJ + '/seeds'
const PANELS = PROJ + '/panels'
const NODES = PROJ + '/wiki/nodes'
const CANON = PROJ + '/assets/duo_canonical_ref_v001.png'
const BIBLE = PROJ + '/ART_BIBLE.md'
const COMICJSON = PROJ + '/comic.json'
const STORY = COMICJSON  // comic.json carries per-panel beat/narration/dialogue (replaces the video storyboard)

// P0 default target = the B08 audit page (the centerpiece, 4 panels). Override via args.panelIds.
const PAGE = ARGS.page || 'P02_b08'
// panelIds accepts an ARRAY or a COMMA-STRING ("S01,S02") — array args have been observed not to forward
// through some Workflow harness paths, so the string form is the reliable override.
const _rawIds = ARGS.panelIds
const PANEL_IDS = Array.isArray(_rawIds) ? _rawIds
  : (typeof _rawIds === 'string' && _rawIds.trim() ? _rawIds.split(',').map(s => s.trim()).filter(Boolean) : ['S12', 'S13', 'S14', 'S15'])
// fail fast: PAGE + every panel id flow into shell paths, /tmp filenames and wiki node filenames → whitelist them up front
const ID_RE = /^[A-Za-z0-9_-]+$/
if (!ID_RE.test(PAGE) || !Array.isArray(PANEL_IDS) || !PANEL_IDS.every(p => typeof p === 'string' && ID_RE.test(p))) {
  throw new Error(`unsafe page/panelIds (must match ${ID_RE}): page=${JSON.stringify(PAGE)} panelIds=${JSON.stringify(PANEL_IDS)}`)
}
// PROJ/REPO flow UNQUOTED-ish into shell strings (bake heredoc, gate CLIs, /tmp paths). For an external
// user whose checkout path contains a quote / $ / backtick / ; etc. that is a command-injection surface.
// Require a plain ABSOLUTE path with no shell metacharacters; abort loudly otherwise.
// No spaces either: several shell uses (e.g. stat -f%z ${cpng}) are unquoted, so a space would word-split.
const PATH_RE = /^\/[A-Za-z0-9._/-]+$/
for (const [k, v] of [['projectRoot', PROJ], ['repoRoot', REPO]]) {
  if (!v || !PATH_RE.test(v)) throw new Error(`unsafe ${k} (must be an absolute path with no spaces or shell metacharacters, matching ${PATH_RE}): ${JSON.stringify(v)}`)
}
const MAX_TOTAL = 4, MAX_ROLLBACKS = 6, STRIKE_ESCALATE = 2   // a panel drifting ≥2 assembly rounds → author-layer rewrite, not more bakes   // per-panel bakes in the main loop / extra repair rounds at assembly (unified budget = MAX_TOTAL + MAX_ROLLBACKS)
const FINALIZE = ARGS.finalize === true
const absImg = (p) => !p ? '' : (p.startsWith('/') ? p : PROJ + '/' + p)  // resolve panel image path (abs or project-rel) — one helper
const relImg = (p) => !p ? '' : (p.startsWith(PROJ + '/') ? p.slice(PROJ.length + 1) : p)  // project-relative for wiki nodes — NEVER persist an absolute path (leaks $HOME/username on a public release)
// throttle = the DETERMINISTIC class set by the bash wrapper (failure_kind), with the old prose regex only as a fallback
const isThrottle = (gen, reason) => gen?.failure_kind === 'throttle' || (!gen?.failure_kind && /rate|limit|throttl|server|unavailable|429|quota/i.test(reason || ''))

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
  // FAIL-CLOSED: both visual reviewers must return ALL core scores. Otherwise the filter(x!=null) below would
  // silently degrade to ONE reviewer's score carrying the panel (identity is partly guarded by disagree<2, but
  // style/comp were not) — a missing/partial visual reviewer that didn't set timed_out must NOT slip a KEEP.
  const visCore = r => [r?.identity_consistency, r?.style_consistency, r?.composition_readability, r?.artifact_severity]
  if (![gem, cdx].every(r => visCore(r).every(x => x != null))) {
    return { v: 'retry_panel', reason: 'a visual reviewer returned incomplete core scores (fail-closed)', invariant: '' }
  }
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
  // ANATOMY veto (both modes — characters appear in html AND baked panels). A CLEAR anatomical error (wrong hand count,
  // a 3rd/floating/duplicated/merged hand, fused fingers) is a SINGLE-vote veto: like content_corruption, one reviewer
  // seeing it blocks KEEP no matter how high the beauty scores. (The literal token-diff is blind to anatomy — this closes
  // the gap that let a 3-handed cover ship.) Reviewers leave it false/unset for character-less panels ⇒ fail-safe no-veto.
  const anatomyDefect = gem?.anatomy_defect_present === true || cdx?.anatomy_defect_present === true
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
    // EXACT atomic-token match (NOT substring — "+6.25"/"+16.2" must NOT satisfy "+6.2"), and each authored literal must be
    // transcribed by BOTH reviewers INDEPENDENTLY (not the union): a single over-helpful / hallucinating reviewer must not be
    // able to satisfy a missing literal. toks() is Array.isArray-safe → a malformed extraction returns null ⇒ fail closed.
    // Each reviewer's transcription → two token sets: COARSE (keeps "+6.2" / "warn_corrected" / "a.b" whole) and FINE (alnum
    // runs, splitting on . _ - and the sign). A reviewer "read" an authored literal e if: for a NUMBER, e is an exact COARSE
    // token (so a wrong "+6.25" can NOT satisfy "+6.2"); for a CODE/LABEL, e is a coarse token OR all of e's fine parts are
    // present (so "jsonschema" matches "jsonschema.validate", "warn_corrected" matches "WARN corrected"). Each authored literal
    // must be read by BOTH reviewers independently (no union — a single over-helpful/hallucinating reviewer can't satisfy it).
    const sets = arr => { if (!Array.isArray(arr)) return null; const c = new Set(), f = new Set()
      for (const s of arr) { if (typeof s !== 'string') continue; const t = s.toLowerCase()
        ;(t.match(/[a-z0-9+._:|/-]+/g) || []).forEach(x => c.add(x)); (t.match(/[a-z0-9]+/g) || []).forEach(x => f.add(x)) }  // COARSE keeps :|/ → timestamps/versions stay whole
      const joined = arr.filter(s => typeof s === 'string').join(' ').toLowerCase().replace(/\s+/g, ' ')
      return { c, f, joined } }
    const gemS = sets(gem?.observed_literals), cdxS = sets(cdx?.observed_literals)
    const reviewersOk = !!gemS && !!cdxS                                              // both reviewers returned a usable array
    const structured = e => /[0-9:]/.test(e)                                          // number/timestamp/version/code → EXACT coarse token only (no subtoken fallback)
    const hit = (e, S) => { e = e.toLowerCase().trim()
      if (e.includes(' ')) return S.joined.includes(e)                                // multi-word phrase → ordered substring
      if (structured(e)) return S.c.has(e)                                            // "+6.25"/"t-24:00:01" must NOT satisfy "+6.2"/"t-24:00:00"
      if (S.c.has(e)) return true
      const parts = e.match(/[a-z0-9]+/g) || []; return parts.length > 0 && parts.every(p => S.f.has(p)) }
    const exp = Array.isArray(cfg.expected_literals) ? cfg.expected_literals.filter(e => typeof e === 'string') : []
    const missing = reviewersOk ? exp.filter(e => !(hit(e, gemS) && hit(e, cdxS))) : exp   // BOTH reviewers must have read it
    const figureUngated = !!cfg.content_svg && exp.length === 0                        // baked figure w/ no gateable literal ⇒ fail closed (also pre-screened in main loop)
    const tokensOK = reviewersOk && !figureUngated && missing.length === 0
    textOK = bothBtq && minBtq >= 4 && !corruption && tokensOK
    textReason = `btq=${bothBtq ? minBtq : 'NO-reviewer'} corruption=${corruption} reviewersOk=${reviewersOk} missing(¬both)=[${missing.join('|')}]${figureUngated ? ' UNGATED-figure' : ''}`
  } else {
    const safezone = gem?.safezone_present === true || cdx?.safezone_present === true   // either confirms
    const strayText = (gem?.stray_text_present === true) || (cdx?.stray_text_present === true) // either sees text → fail
    textOK = safezone && !strayText
    textReason = `safezone=${safezone} stray=${strayText}`
  }
  const reason = `[${mode}] narr=${narr} identity=${minIdent} style=${minStyle}/${maxStyle} comp=${minComp}/${maxComp} art(g/c)=${gemArt}/${cdxArt} ${textReason} anatomyDefect=${anatomyDefect} disagreeId=${disagree}`
  if (narr >= 4 && minIdent >= 4 && styleOK && compOK && !artifactBad && textOK && !anatomyDefect && disagree < 2) {
    return { v: 'keep', reason: 'KEEP — ' + reason, invariant: '' }
  }
  // everything else = retry the SAME panel with the repair invariant injected (no cross-panel rollback for seed-anchored comics)
  return { v: 'retry_panel', reason: 'RETRY — ' + reason, invariant: repair }
}

function assemblyVerdict(cc, gem, mode = 'html') {
  // mode-aware: baked pages have intended text → judge baked_text_legibility, NOT html safezone fit (deferred #12 fixed).
  const textDim = mode === 'baked' ? (gem?.baked_text_legibility ?? 0) : (gem?.text_fits_safezone ?? 0)
  const dims = [cc?.reading_order ?? 0, cc?.page_rhythm ?? 0, gem?.cross_panel_identity ?? 0, gem?.cross_panel_style ?? 0, textDim]
  const minDim = Math.min(...dims), sum = dims.reduce((a, b) => a + b, 0)
  const drift = Array.isArray(gem?.drift_panels) ? gem.drift_panels.filter(x => typeof x === 'string') : []   // which panels the reviewer says break the page
  // point_of_divergence = the first named drifter (the caller re-orders by reading order); surfaced for the
  // audit + to anchor which panel the cross-frame repair / author-escalation starts from.
  if (minDim < 2 || sum < 16) return { v: 'rollback', reason: `[${mode}] assembly weak (min=${minDim} sum=${sum}/25)`, drift_panels: drift, point_of_divergence: drift[0] || null }
  return { v: 'accept', reason: `[${mode}] assembly ok (min=${minDim} sum=${sum}/25)`, drift_panels: [], point_of_divergence: null }
}

// ── schemas ──
const SCORE = { type: 'number', minimum: 0, maximum: 5 }   // every reviewer score is bounded 0-5 (a stray 50 can't slip through)
const GEN_SCHEMA = { type: 'object', required: ['status', 'image_path'], properties: {
  status: { type: 'string', enum: ['panel_ready', 'generation_failed'] }, image_path: { type: 'string' }, bytes: { type: 'number' }, gen_failed_reason: { type: 'string' },
  failure_kind: { type: 'string', enum: ['throttle', 'other'] },   // DETERMINISTIC failure class (set by the bash wrapper from the codex log), not parsed from prose
  text_mode: { type: 'string' }, content_figure_png: { type: 'string' }, image_sha256: { type: 'string' }, baked_numbers_verified: { type: 'string' }, notes: { type: 'string' } } }
const COND_SCHEMA = { type: 'object', required: ['panels'], properties: { panels: { type: 'object' } } }
// Reviewer schemas: scores are NOT required, so a reviewer can return {timed_out:true} cleanly instead of being forced to
// invent numbers (audit P1). A missing score defaults to 0 in the verdict → fail-closed → retry. All scores are 0-5 bounded.
const CC_SCHEMA = { type: 'object', properties: {
  narrative_beat_fidelity: SCORE, composition_story: SCORE, timed_out: { type: 'boolean' }, notes: { type: 'string' } } }
// VIS_SCHEMA: html reviewers fill safezone_present/stray_text_present; baked reviewers fill observed_literals (verbatim
// transcription of the numbers/labels/code they can READ — NOT told the expected values), content_corruption_present, baked_text_quality.
const VIS_SCHEMA = { type: 'object', properties: {
  identity_consistency: SCORE, style_consistency: SCORE, composition_readability: SCORE,
  artifact_severity: SCORE, safezone_present: { type: 'boolean' }, stray_text_present: { type: 'boolean' },
  baked_text_quality: SCORE, observed_literals: { type: 'array', items: { type: 'string' } }, content_corruption_present: { type: 'boolean' },
  // anatomy gate (added after the cover shipped a 3-handed chibi the literal-diff couldn't see): character_hand_count
  // is a per-character enumeration ("blue:2","green:2") for the audit trail; anatomy_defect_present is a SINGLE-vote veto.
  character_hand_count: { type: 'array', items: { type: 'string' } }, anatomy_defect_present: { type: 'boolean' },
  failure_mode_positive_invariant: { type: 'string' }, timed_out: { type: 'boolean' }, notes: { type: 'string' } } }
const WIKI_SCHEMA = { type: 'object', required: ['wrote_nodes'], properties: { wrote_nodes: { type: 'array', items: { type: 'string' } }, failure_mode_id: { type: ['string', 'null'] } } }
const ASM_CC_SCHEMA = { type: 'object', properties: { reading_order: SCORE, page_rhythm: SCORE, notes: { type: 'string' } } }
const ASM_VIS_SCHEMA = { type: 'object', properties: { cross_panel_identity: SCORE, cross_panel_style: SCORE, text_fits_safezone: SCORE, baked_text_legibility: SCORE, drift_panels: { type: 'array', items: { type: 'string' } }, timed_out: { type: 'boolean' }, notes: { type: 'string' } } }

// ── generation: CONTENT-CONDITIONED BAKE (the deterministic-SVG → codex narrative-figure technique) ──
// Per panel the engine reads comic.json .condition {content_svg, world, scene, chibi_action} + .bubbles, renders the
// content_svg → a deterministic PNG blueprint, then bakes ONE comic panel via the agent mcp__codex__codex sidecar using EXACTLY TWO refs
// (the blueprint #1 + the canonical duo #2 — a 3rd ref dilutes identity). The blueprint is the CONTENT AUTHORITY: its
// numbers/labels/code are ground truth and must survive verbatim (verified in STEP 4 = the gate's faithfulness contract).
const BAKE_LANG = ARGS.bakeLang || 'zh'   // which bubble language to bake (image bakes one); zh proven clean

// loadConditions: read comic.json ONCE (the sandbox has no fs) → structured per-panel config. This is the source of truth
// for text_mode + expected_literals + concrete scene/bubbles (so the gen command has NO placeholders for an agent to fill).
function loadConditions() {
  return agent([
    `Read "${COMICJSON}" and return the per-panel generation config for EXACTLY these panels: ${JSON.stringify(PANEL_IDS)}.`,
    `For each pid return an object with: text_mode (the panel's .text_mode), content_svg (.condition.content_svg, a project-relative path or null), world (.condition.world), scene (.condition.scene), identity_ref (.condition.identity_ref, a project-relative .png path or null), identity_desc (.condition.identity_desc or ""), characters (.condition.characters or ""), chibi_executor (.condition.chibi_action.executor or ""), chibi_reviewer (.condition.chibi_action.reviewer or ""), bubbles_all (an ARRAY with one string per .bubbles entry, each formatted "<speaker> says: <text.${BAKE_LANG}>" — empty array if the panel has no bubbles), expected_literals (copy the panel's .condition.expected_literals array verbatim, or []).`,
    `Return COND_SCHEMA: {panels: {"S12": {...}, ...}}. READ ONLY — do not generate or render anything.`,
  ].join('\n'), { label: 'load-conditions', phase: 'Panels', schema: COND_SCHEMA })
}

// ── contract-v2 §0a (JS port — out-of-sandbox engine-side mirror of pickup_image.py): buildBakePrompt +
// verifyExistingPng. The three engines do NOT share ONE implementation: the two Python engines REUSE the single
// source of truth (pickup_image.py) by importing it; this JS engine instead MIRRORS its bake-prompt + verifier +
// VETO list under a test-locked byte-parity guard (tests/test_gates.py), which re-derives the JS VETO_PATS regex
// sources straight from this file and asserts they are BYTE-IDENTICAL to pickup_image._VETO_PATS (14 entries, same
// order; drift = a fallback slipping through one engine but not the other — the guard, not a shared module, is what
// keeps the mirror honest). buildBakePrompt embeds the absolute ref + out paths LITERALLY (the mcp__codex__codex
// schema has no -i). The in-sandbox engine has NO fs and NEVER bakes in-process (the in-process exec bake is
// RETIRED — see the retired BAKE bash below) — these helpers serve the out-of-sandbox host / the Python SOP verifier.
function buildBakePrompt(body, contentPngAbs, idRefAbs, outAbs) {
  const lines = [
    'Use your native image generation tool to produce ONE PNG. Generate an image — do not write or edit any code or files; only generate the single image.',
    body,
    `Reference image 1 (absolute path): ${contentPngAbs}`,
  ]
  if (idRefAbs) lines.push(`Reference image 2 (absolute path): ${idRefAbs}`)
  lines.push(`Save the final native PNG to this exact path: ${outAbs}`)
  return lines.filter(Boolean).join('\n')
}
// VETO_PATS + verifyExistingPng are NOT a hard security boundary — they are a BEST-EFFORT DENYLIST against the ONE
// KNOWN failure mode: codex's hand-drawn (struct/zlib/PIL/<svg>/matplotlib) fallback when it can't run its native
// image tool. They catch that specific non-native artifact (and a stale/undersized/non-PNG out_path); they do NOT,
// and cannot, certify that the panel is FAITHFUL — a determined adversary or an unknown fallback path could still
// dodge these patterns. The load-bearing FAITHFULNESS gate is the cross-model panel (CC narrative ‖ Gemini visual
// ‖ Codex visual → deterministic JS verdict, with the blind token-diff for baked figures); this denylist is only a
// cheap upstream filter so an obvious non-native fallback never even reaches that panel.
const VETO_PATS = [/\bimport\s+struct\b/, /\bstruct\.pack\b/, /\bimport\s+zlib\b/, /\bzlib\.compress\b/,
  /\bfrom\s+pil\b/, /\bimport\s+pil\b/, /<svg/, /\bmatplotlib\b/, /\bdef\s+main\s*\(/,
  /\brsvg-convert\b/, /\bcairosvg\b/, /\bwritefile\b/, /\bfrom\s+struct\s+import\b/, /\bfrom\s+zlib\s+import\b/]
function verifyExistingPng(outPath, minBytes = 500000, aspect = null, createdAt = null, transcript = null) {
  let fs, crypto
  try { fs = require('fs'); crypto = require('crypto') } catch { return { ok: false, reason: 'no fs (sandbox) — verification is delegated to the Python SOP verifier (pickup_image.py)' } }
  // mirror pickup_image.py: a missing/empty transcript makes the HARD-VETO INERT → fail-closed (a hand-drawn
  // fallback PNG with a clean sig+dims+size must NOT be accepted merely because no transcript was scanned).
  if (!transcript || !fs.existsSync(transcript) || !fs.readFileSync(transcript, 'latin1').trim()) {
    return { ok: false, reason: 'empty/missing transcript — HARD-VETO inert, fail-closed' }
  }
  // mirror pickup_image.py: if the transcript is a JSON status dict (the agent's <png>.bakestatus.json carries
  // status + raw mcp_output), require mcp_output to be a NON-EMPTY string — an ok status whose mcp_output is
  // missing/empty/non-string makes the HARD-VETO scan vacuous (nothing to denylist), so fail-closed. A NON-JSON
  // transcript (a plain log) skips this so the regex-denylist path still applies on its own.
  let _txObj = null
  try { _txObj = JSON.parse(fs.readFileSync(transcript, 'latin1')) } catch { _txObj = null }
  if (_txObj && typeof _txObj === 'object' && !Array.isArray(_txObj) && 'status' in _txObj) {
    const _m = _txObj.mcp_output
    if (typeof _m !== 'string' || !_m.trim()) {
      return { ok: false, reason: 'bakestatus mcp_output missing/empty/non-string — HARD-VETO inert, fail-closed' }
    }
  }
  {
    const low = fs.readFileSync(transcript, 'latin1').toLowerCase()
    const hits = VETO_PATS.filter(p => p.test(low)).map(p => p.source)
    if (hits.length) return { ok: false, reason: `non-native fallback markers (HARD-VETO): ${hits}` }
  }
  if (!fs.existsSync(outPath)) return { ok: false, reason: 'out_path does not exist (agent bake never wrote it — fail-closed)' }
  const buf = fs.readFileSync(outPath)
  if (buf.length <= minBytes) return { ok: false, reason: `out_path too small (${buf.length} <= ${minBytes}) — likely non-native fallback` }
  const sig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
  if (!buf.slice(0, 8).equals(sig) || buf.slice(12, 16).toString('latin1') !== 'IHDR') return { ok: false, reason: 'out_path is not a valid PNG (bad signature/IHDR)' }
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20)
  if (aspect) { const ar = w / h; if (!(0.6 * aspect <= ar && ar <= 1.6 * aspect)) return { ok: false, reason: `out_path aspect ${ar.toFixed(3)} off blueprint ${aspect.toFixed(3)}` } }
  if (createdAt != null && fs.statSync(outPath).mtimeMs / 1000 < createdAt - 1) return { ok: false, reason: 'out_path older than the bake request (stale prior bake) — fail-closed' }
  const sha = crypto.createHash('sha256').update(buf).digest('hex')
  return { ok: true, path: outPath, sha256: sha, bytes: buf.length, width: w, height: h }
}

function generatePanel(pid, cfg = {}, ctx = {}) {
  const ai = ctx.attemptIndex || 1
  const aTag = 'a' + String(ai).padStart(2, '0')
  if (!/^[A-Za-z0-9_-]+$/.test(pid)) {   // pid flows into /tmp paths + output filenames + bash → whitelist it (no metachars/traversal)
    return Promise.resolve({ status: 'generation_failed', image_path: '', text_mode: cfg.text_mode || '', gen_failed_reason: `unsafe panel id ${JSON.stringify(pid)} (must match [A-Za-z0-9_-])` })
  }
  const out = `${PANELS}/${pid}_panel_${aTag}.png`
  const cdir = `${PANELS}/_content_refs`
  const cpng = `${cdir}/${pid}_${aTag}.png`   // PERSISTENT blueprint (NOT /tmp) — the gate + wiki reference it across resume/cleanup
  // shell-safe: content_svg must be a project-relative .svg with no traversal/metachars (it is interpolated into a file:// path)
  const svgRel = cfg.content_svg || ''
  if (!/^[\w][\w./-]*\.svg$/.test(svgRel) || svgRel.includes('..')) {
    return Promise.resolve({ status: 'generation_failed', image_path: '', text_mode: cfg.text_mode || '', gen_failed_reason: `unsafe/empty content_svg: ${JSON.stringify(svgRel)} (expected project-relative *.svg)` })
  }
  // Per-panel IDENTITY (boundary fix): the identity ref + description come from cfg (comic.json), defaulting to
  // the duo for back-compat. identity_ref is shell-safe-validated like content_svg (it lands in a bash -i arg).
  const idRel = cfg.identity_ref || ''
  if (idRel && (!/^[\w][\w./-]*\.png$/.test(idRel) || idRel.includes('..'))) {
    return Promise.resolve({ status: 'generation_failed', image_path: '', text_mode: cfg.text_mode || '', gen_failed_reason: `unsafe identity_ref: ${JSON.stringify(idRel)} (expected project-relative *.png)` })
  }
  const idRefAbs = idRel ? `${PROJ}/${idRel}` : CANON
  const idDesc = cfg.identity_desc || 'the CANONICAL DUO — blue executor: brown hair, NO beard; green reviewer: dark hair, beard'
  const charsLine = cfg.characters || [cfg.chibi_executor ? `executor action: ${cfg.chibi_executor}.` : '', cfg.chibi_reviewer ? `reviewer action: ${cfg.chibi_reviewer}.` : ''].filter(Boolean).join(' ')
  const bubblesArr = Array.isArray(cfg.bubbles_all) ? cfg.bubbles_all.filter(b => typeof b === 'string' && b.trim()) : []
  const bubbleLine = bubblesArr.length
    ? `Bake these speech bubbles as clean readable comic lettering (${BAKE_LANG}): ${bubblesArr.join('  ||  ')}`
    : (cfg.bubble_executor || cfg.bubble_reviewer
      ? `Bake these speech bubbles as clean readable comic lettering (${BAKE_LANG}): executor says: ${cfg.bubble_executor}  ||  reviewer says: ${cfg.bubble_reviewer}`
      : `This panel has NO speech bubbles — bake NO dialogue text (the technical figure's text is the only text).`)
  const repairLine = (ctx.invariants || []).filter(Boolean).length
    ? 'REPAIR CONSTRAINTS (earlier attempts failed for these reasons — honor every one): ' + ctx.invariants.filter(Boolean).join('  |  ')
    : ''
  // Build the bake prompt body with CONCRETE values (no <placeholders>). The agent writes it via a quoted heredoc, so
  // quotes / CJK / special chars in scene+bubbles can't break the shell command.
  const promptBody = [
    `WORLD = ${cfg.world}  → apply the ART_BIBLE §0.5 two-world lighting (warm-lab = warm Edison-glow human world; dark-cyber = dark screen-lit digital world).`,
    `SCENE: ${cfg.scene}`,
    `Render the character(s) from reference image #2 EXACTLY as depicted there — ${idDesc}. ${charsLine}`,
    `Integrate the technical figure from reference image #1 onto a board/screen/dashboard in the scene. Reproduce its numbers, labels and code EXACTLY as they appear in image #1 — do NOT alter, re-spell, round, or invent any number or token.`,
    bubbleLine,
    `ONE coherent flat pixel-art comic panel. No watermark. No UI text beyond the integrated figure and the bubbles (if any).`,
    repairLine,
  ].filter(Boolean).join('\n')
  // heredoc-injection guard: project text (scene/bubbles) is written via a quoted heredoc; if any body line equaled the
  // delimiter the rest would execute as shell. Use an unlikely fixed delimiter AND assert the body can't contain it (fail closed).
  const BAKE_DELIM = 'ARIS_BAKE_HEREDOC_EOF_b7f3a91c'
  if (promptBody.split('\n').some(l => l.trim() === BAKE_DELIM)) {
    return Promise.resolve({ status: 'generation_failed', image_path: '', text_mode: cfg.text_mode || '', gen_failed_reason: 'prompt body collided with the heredoc delimiter (refusing to risk shell injection)' })
  }
  return agent([
    `You are the Codex CONTENT-CONDITIONED BAKE executor for ARIS comic panel ${pid} (attempt ${ai}, mode=${cfg.text_mode}). Bake ONE pixel-art panel fusing a deterministic technical FIGURE (the content blueprint = GROUND TRUTH; its numbers must survive verbatim) with the canonical chibi duo + baked dialogue.`, '',
    `STEP 1 — render the content blueprint SVG → a PERSISTENT PNG (watchdog-bounded):`,
    '```bash',
    `mkdir -p "${cdir}"`,
    `CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`,
    `( "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 --window-size=1280,720 --screenshot="${cpng}" "file://${PROJ}/${svgRel}" >/dev/null 2>&1 ) & P=$!; ( sleep 30; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null`,
    `[ -s "${cpng}" ] && echo "CONTENT_PNG_OK $(stat -f%z ${cpng})" || { echo "CONTENT_PNG_FAIL"; exit 0; }`,
    '```',
    `STEP 2 — assemble the bake prompt (ART_BIBLE rules + the panel body below) into a file. The in-engine codex-exec bake is RETIRED (it hand-draws a non-native fallback), so this bash HARD-FAILS with exec-bake-retired; the REAL bake is the agent mcp__codex__codex sidecar (run_comic.py --bake-mode=agent): buildBakePrompt body + EXACTLY 2 refs (blueprint #1 + canonical duo #2) by absolute path + exact out_path, sandbox workspace-write. NEVER fall back to PIL/SVG/codex-exec:`,
    '```bash',
    `cat > /tmp/bake_${pid}_${aTag}.txt <<'${BAKE_DELIM}'`,
    promptBody,
    `${BAKE_DELIM}`,
    `( printf 'Paste these style rules first:\\n%s\\n\\nThen render this panel:\\n' "$(cat "${BIBLE}")"; cat /tmp/bake_${pid}_${aTag}.txt ) > /tmp/bakefull_${pid}_${aTag}.txt`,
    // CONCURRENT-BAKE LOCK — RETIRED-EXEC-PATH rationale only (kept for context): the OLD codex-exec bake wrote to
    // the GLOBAL ~/.codex/generated_images dir and picked the mtime-newest PNG, so concurrent bakes could grab each
    // other's images and needed an mkdir lock. The AGENT seam does NOT use that dir or newest-pickup — each bake
    // writes its OWN explicit out_path and run_comic.py's agent wrapper serializes the mcp__codex__codex calls, so
    // the core holds NO machine-wide lock (R3 — HELD=1 below makes the old lock a no-op).
    `HELD=1`,   // R3: agent mode does NOT hold /tmp/aris_imagegen.lock — the agent wrapper is the sole bake serializer; the core blocking on the agent that must service the sidecar would deadlock. (The bake itself is retired from this bash block — see the BAKE line below, which exit 0's.)
    `if [ "$HELD" != 1 ]; then echo "GEN_FAIL size=0 FAILKIND=other lock_contended"; exit 0; fi`,   // never run unlocked: if we never acquired, abort the bake (transient → retried) rather than risk grabbing another run's image / removing a lock we don't own
    `M=/tmp/cm_${pid}_${aTag}; touch "$M"`,
    `echo "BAKE retired from codex exec — the agent fulfills it via mcp__codex__codex over the .bakereq.json sidecar (buildBakePrompt body + abs ref paths + exact out_path; model=gpt-5.5; config={model_reasoning_effort:xhigh}; sandbox=workspace-write; cwd=PROJ; the status file MUST carry raw mcp_output for the HARD-VETO). The native PNG is written to ${out} and verified by pickup_image.py --out-existing (sig+IHDR+size>=500000+mtime>=created_at, HARD-VETO struct/zlib/PIL/<svg>/matplotlib in the transcript). DO NOT call codex exec for a bake — it hand-draws a non-native fallback." >&2; echo "GEN_FAIL size=0 FAILKIND=other exec-bake-retired"; exit 0`,   // R4: in-engine exec bake retired (hand-draws a non-native fallback). HARD-FAIL here, BEFORE probing ${out}, so a stale prior PNG at ${out} can NEVER be accepted. Real bake = the Python SOP (run_comic.py --bake-mode=agent).
    `: # R4: exec bake retired — no codex child to watchdog ($P is gone; a bare 'wait' here would block ~480s on the watchdog subshell). The real bake (agent seam via mcp__codex__codex) is watchdogged by run_comic.py's await_bake_status(--bake-timeout).`,
    `NEW=""; SZ=0`,   // R4: exec bake retired (see the BAKE line above, which exit 0's before reaching here). NEVER point NEW at ${out} — that would let a stale prior PNG be accepted with no native bake + no HARD-VETO. The agent seam writes ${out} and pickup_image.py --out-existing verifies it.
    `if [ -n "$NEW" ] && [ "$SZ" -gt 500000 ]; then cp "$NEW" "${out}"; H=$(shasum -a 256 "${out}" 2>/dev/null | cut -d' ' -f1); echo "GEN_OK ${out} $SZ sha=$H"; else if grep -qiE 'rate.?limit|429|quota|server_?error|too many requests|overloaded|unavailable|50[23]' /tmp/cm_${pid}_${aTag}.log 2>/dev/null; then K=throttle; else K=other; fi; echo "GEN_FAIL size=$SZ FAILKIND=$K"; fi`,
    `rmdir "$LOCK" 2>/dev/null; trap - EXIT`,   // release the bake lock immediately after pickup (trap is the crash safety-net)
    '```',
    `STEP 3 — return GEN_SCHEMA: status MUST be "panel_ready" ONLY if you saw "GEN_OK" and "${out}" is >500KB, else "generation_failed". image_path="${out}", bytes (the real size), image_sha256 (the value printed after "sha=" on the GEN_OK line — REQUIRED on success, it binds the gate verdict to this exact image), failure_kind (on failure, copy the token after "FAILKIND=" — "throttle" or "other" — this is the DETERMINISTIC class, do NOT infer it from prose), text_mode="${cfg.text_mode}", content_figure_png="${cpng}", gen_failed_reason (quote the codex/image_gen error if failed), notes. Do NOT self-attest the numbers — faithfulness is judged by the gate.`,
  ].join('\n'), { label: `gen:${pid}#${ai}`, phase: 'Panels', schema: GEN_SCHEMA })
}

// ── panel_gate: 3 independent cross-model reviewers → deterministic JS verdict ──
async function panelGate(pid, gen, cfg = {}, ai = 1) {
  const mode = cfg.text_mode || gen.text_mode || 'html'   // comic.json (cfg) is the SOURCE OF TRUTH for mode, not the generator's self-report
  const baked = mode === 'baked'
  const img = absImg(gen.image_path)
  const sha = (gen.image_sha256 || '').slice(0, 12)   // BIND each reviewer's verdict to THIS attempt's exact image (label+prompt) → a resume can't replay a stale verdict onto a different file
  // per-panel identity (mirrors generatePanel): reviewers judge identity against THIS panel's ref + description
  const gIdRel = cfg.identity_ref && /^[\w][\w./-]*\.png$/.test(cfg.identity_ref) && !cfg.identity_ref.includes('..') ? cfg.identity_ref : ''
  const gIdRef = gIdRel ? `${PROJ}/${gIdRel}` : CANON
  const gIdDesc = cfg.identity_desc || '蓝executor棕发无须/绿reviewer黑发有须'
  const cc = agent([
    `You are the CC NARRATIVE reviewer in ARIS comic panel_gate for ${pid} (mode=${mode}). Judge STORY only (you may glance at the panel at "${gen.image_path}" but score narrative, not pixels).`,
    `Read panel ${pid} from "${COMICJSON}": its .condition.scene, its .bubbles (the intended dialogue), .caption, and the page's beat narration. Score 0-5: narrative_beat_fidelity (does this panel deliver its beat in the audit story?), composition_story (does the staging${baked ? ' + the baked figure/dialogue' : ''} read the story right?). Return CC_SCHEMA.`,
  ].join('\n'), { label: `gate-cc:${pid}#${ai}`, phase: 'Panels', schema: CC_SCHEMA })

  // Visual reviewers get ONLY the panel + canonical duo + ART_BIBLE — NOT the content blueprint. baked faithfulness is judged by a
  // BLIND transcription (observed_literals) deterministically diffed against authored ground truth in JS, so reviewers must never
  // see the expected numbers (else they rubber-stamp). They also flag content_corruption_present (garbled/illegible glyphs).
  const gemJson = baked
    ? `{\\"identity_consistency\\":n,\\"style_consistency\\":n,\\"composition_readability\\":n,\\"artifact_severity\\":n,\\"baked_text_quality\\":n,\\"observed_literals\\":[\\"...\\"],\\"content_corruption_present\\":true/false,\\"failure_mode_positive_invariant\\":\\"...\\"}。baked_text_quality=气泡对白文字是否清晰可读不乱码;observed_literals=逐字转录你能在画中【技术图】里确实看清的数字/标签/代码token(如 +6.2、jsonschema),只转录看清的,严禁猜测或补全;content_corruption_present=技术图里是否有明显乱码/残缺/不合法的数字或代码。另必须输出 \\"character_hand_count\\":[\\"blue:2\\",\\"green:2\\"](逐一数出画中每个角色可见的手数) 与 \\"anatomy_defect_present\\":true/false(任一角色手数≠2,或出现第三只手/悬浮手/重复手/融合多指等明显解剖错误,则为true;画中无角色则false)。`
    : `{\\"identity_consistency\\":n,\\"style_consistency\\":n,\\"composition_readability\\":n,\\"artifact_severity\\":n,\\"safezone_present\\":true/false,\\"stray_text_present\\":true/false,\\"failure_mode_positive_invariant\\":\\"...\\"}。safezone=有没有留干净文字区;stray_text=图里有没有冒出文字/字形。另必须输出 \\"character_hand_count\\":[\\"blue:2\\",\\"green:2\\"](逐一数出画中每个角色可见的手数) 与 \\"anatomy_defect_present\\":true/false(任一角色手数≠2,或出现第三只手/悬浮手/重复手/融合多指等明显解剖错误,则为true;画中无角色则false)。`
  const gem = agent([
    `You are the GEMINI VISUAL reviewer in ARIS comic panel_gate for ${pid} (mode=${mode}, independent — do not consult other scores). Use watchdog-bounded CLI:`,
    '```bash',
    `( gemini --model auto-gemini-3 -p "@${img} @${gIdRef} @${BIBLE} 评这张漫画面板(第1张,文件 ${pid}#${ai} sha ${sha}):对照第2张身份参考(${gIdDesc})与 ART_BIBLE。打分0-5并只输出一行紧凑JSON: ${gemJson}" < /dev/null > /tmp/gg_${pid}_${ai}.txt 2>&1 ) & P=$!`,
    `( sleep 240; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 1500 /tmp/gg_${pid}_${ai}.txt`,
    '```',
    `Parse the JSON gemini emitted into VIS_SCHEMA. If gemini gave no parseable scores, set timed_out=true.`,
  ].join('\n'), { label: `gate-gem:${pid}#${ai}`, phase: 'Panels', schema: VIS_SCHEMA })

  const cdxJson = baked
    ? `{\\"identity_consistency\\":n,\\"style_consistency\\":n,\\"composition_readability\\":n,\\"artifact_severity\\":n,\\"baked_text_quality\\":n,\\"observed_literals\\":[\\"...\\"],\\"content_corruption_present\\":true/false,\\"failure_mode_positive_invariant\\":\\"...\\"} (0-5)。baked_text_quality=气泡烤字是否清晰不乱码;observed_literals=逐字转录画中技术图你确实看清的数字/标签/代码,严禁猜测;content_corruption_present=有无明显乱码/残缺/不合法数字或代码。另必须输出 \\"character_hand_count\\":[\\"blue:2\\",\\"green:2\\"](逐一数出画中每个角色可见的手数) 与 \\"anatomy_defect_present\\":true/false(任一角色手数≠2,或出现第三只手/悬浮手/重复手/融合多指等明显解剖错误,则为true;画中无角色则false)。`
    : `{\\"identity_consistency\\":n,\\"style_consistency\\":n,\\"composition_readability\\":n,\\"artifact_severity\\":n,\\"safezone_present\\":true/false,\\"stray_text_present\\":true/false,\\"failure_mode_positive_invariant\\":\\"...\\"} (0-5)。另必须输出 \\"character_hand_count\\":[\\"blue:2\\",\\"green:2\\"](逐一数出画中每个角色可见的手数) 与 \\"anatomy_defect_present\\":true/false(任一角色手数≠2,或第三只手/悬浮手/重复手/融合多指等明显解剖错误则true,无角色则false)。`
  const cdx = agent([
    `You are the CODEX VISUAL reviewer in ARIS comic panel_gate for ${pid} (mode=${mode}, independent SECOND visual model — covers what Gemini's eye misses). Use watchdog-bounded CLI (codex vision review is NOT image_gen, not rate-limited):`,
    '```bash',
    `( codex exec "审这张漫画面板(第1张,文件 ${pid}#${ai} sha ${sha}):对照第2张身份参考(${gIdDesc})与 ART_BIBLE,评身份/画风/构图/瑕疵${baked ? ' + 气泡烤字清晰度 + 逐字转录技术图数字' : '/留白/有无杂字'}。只输出一行JSON: ${cdxJson}" -i "${img}" -i "${gIdRef}" -i "${BIBLE}" --skip-git-repo-check < /dev/null > /tmp/cc_${pid}_${ai}.txt 2>&1 ) & P=$!`,
    `( sleep 300; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 1500 /tmp/cc_${pid}_${ai}.txt`,
    '```',
    `Parse codex's JSON into VIS_SCHEMA. If none, timed_out=true.`,
  ].join('\n'), { label: `gate-cdx:${pid}#${ai}`, phase: 'Panels', schema: VIS_SCHEMA })

  const [ccR, gemR, cdxR] = await Promise.all([cc, gem, cdx])
  return { cc: ccR, gem: gemR, cdx: cdxR, mode, image_sha256: gen.image_sha256 || null, verdict: panelVerdict(ccR, gemR, cdxR, cfg) }
}

function writeWiki(pid, gen, gate, ai) {
  const aTag = 'a' + String(ai).padStart(2, '0')
  const sl = pid.toLowerCase()
  const v = gate.verdict.v
  return agent([
    `Write ARIS comic wiki active-memory nodes for panel ${pid} attempt ${ai} into ${NODES}/ (one JSON file each). EVERY node file MUST carry all 6 top-level fields: node_id, node_type, title, status, created_at:"2026-06-08T00:00:00+00:00", payload — validate_wiki REJECTS a node missing any of them.`,
    `1) panel_attempt → ${NODES}/panel_attempt_${sl}_${aTag}.json: {node_id:"attempt:${sl}_${aTag}",node_type:"panel_attempt",status:"under_review",title:"${pid} panel attempt ${ai}",created_at:"2026-06-08T00:00:00+00:00",payload:{source_panel_id:"panel:${sl}_aris_comic_v1",image_path:${JSON.stringify(relImg(gen.image_path))},attempt_index:${ai},model:"codex_image_gen",is_baked_duo:true}}`,
    `2) review → review_panel_${sl}_${aTag}_{cc,gemini,codex}.json: ONE full node per reviewer who∈{cc,gemini,codex}: {node_id:"review:panel_${sl}_${aTag}_<who>", node_type:"review", status:"final", title:"<who> review ${pid} a${ai}", created_at:"2026-06-08T00:00:00+00:00", payload:{target_node_id:"attempt:${sl}_${aTag}", reviewer:"<who>", gate_kind:"panel", scores:<that reviewer's JSON>}} — node_id/title/created_at top-level AND target_node_id/reviewer/gate_kind in payload are ALL REQUIRED by validate_wiki. scores from: CC=${JSON.stringify(gate.cc).slice(0, 300)} GEM=${JSON.stringify(gate.gem).slice(0, 300)} CDX=${JSON.stringify(gate.cdx).slice(0, 300)}`,
    `3) decision → decision_panel_${sl}_${aTag}.json: {node_id:"decision:panel_${sl}_${aTag}",node_type:"decision",status:"final",title:"panel_gate ${pid} a${ai} → ${v}",created_at:"2026-06-08T00:00:00+00:00",payload:{gate_kind:"panel",target_node_id:"attempt:${sl}_${aTag}",verdict:"${v}",reviewer_families:{cc:"anthropic",gemini:"google",codex:"openai"},reasoning:${JSON.stringify(gate.verdict.reason.slice(0, 300))},repair_instruction:${JSON.stringify(gate.verdict.invariant || '')}}}`,
    v !== 'keep' ? `4) failure_mode → fail_${sl}_${aTag}.json: {node_id:"fail:${sl}_${aTag}",node_type:"failure_mode",status:"active",title:"failure ${pid} a${ai}",created_at:"2026-06-08T00:00:00+00:00",payload:{active:true,affected_shot_ids:["${pid}"],layer:"panel_visual",repair_pattern:${JSON.stringify(gate.verdict.invariant || '')}}}` : '(no failure_mode on keep)',
    `5) APPEND provenance edges to ${NODES}/../edges.jsonl (one JSON object per line; dedup by src+dst+type): {"src":"attempt:${sl}_${aTag}","dst":"panel:${sl}_aris_comic_v1","type":"attempt_of"}; for EACH reviewer who∈{cc,gemini,codex} {"src":"review:panel_${sl}_${aTag}_<who>","dst":"attempt:${sl}_${aTag}","type":"reviews"}; {"src":"decision:panel_${sl}_${aTag}","dst":"attempt:${sl}_${aTag}","type":"decides"}${v !== 'keep' ? `; {"src":"fail:${sl}_${aTag}","dst":"attempt:${sl}_${aTag}","type":"failure_of"}` : ''}.`,
    `Return WIKI_SCHEMA {wrote_nodes:[ids], failure_mode_id}.`,
  ].join('\n'), { label: `wiki:${pid}#${ai}`, phase: 'Panels', schema: WIKI_SCHEMA })
}

// ── main loop: per-panel spiral with attempt-path (SEED-ANCHORED: retry the SAME panel, NEVER roll back to a prior panel) ──
phase('Panels')
// Load the per-panel condition ONCE (the sandbox has no fs). CONFIG is the SOURCE OF TRUTH for text_mode + expected_literals
// + the concrete scene/bubbles the gen command interpolates — so the gate's mode + faithfulness check can't be bypassed.
let CONFIG = (await loadConditions())?.panels || {}
if (CONFIG.panels && !CONFIG[PANEL_IDS[0]]) CONFIG = CONFIG.panels   // tolerate the agent double-wrapping its output as {panels:{panels:{...}}}
log(`args(typeof ${typeof args}) projectRoot=${ARGS.projectRoot ? 'set' : 'MISSING'} panelIds=${JSON.stringify(ARGS.panelIds)} PANEL_IDS=${JSON.stringify(PANEL_IDS)} | loaded cfg keys: ${Object.keys(CONFIG).join(' ') || '(NONE)'}`)
let kept = []
const totalByPanel = {}, pending = {}
let escalated = null, throttled = false
const flagged = []                 // panels accepted best-so-far for HUMAN review (design R10)
const driftStrikes = {}            // per-panel assembly-drift strike counter → strike-escalation to the author layer
const rewriteStoryboard = []       // KEEP≠final: panels assembly bounced back for an author-layer storyboard/blueprint rewrite
// FAIL-CLOSED: if comic.json couldn't be loaded, every cfg would be empty → mode defaults + the faithfulness token-check goes
// vacuous (a bad panel could keep). Refuse to run rather than run an ungated gate.
const asciiTok = e => typeof e === 'string' && (e.toLowerCase().match(/[a-z0-9+._-]+/g) || []).length > 0
const cfgUsable = c => !!c && !!c.text_mode && !!c.content_svg   // EVERY panel needs a content_svg blueprint (was: html w/ no svg slipped through)
  && (c.text_mode !== 'baked'
  || (Array.isArray(c.expected_literals) && c.expected_literals.length > 0 && c.expected_literals.every(asciiTok)))  // a baked figure MUST carry ASCII-tokenizable expected_literals
const missingCfg = PANEL_IDS.filter(p => !cfgUsable(CONFIG[p]))
if (missingCfg.length) { escalated = { pid: missingCfg[0], why: `unusable cfg for [${missingCfg.join(',')}] (missing text_mode, missing content_svg blueprint, or a baked figure with no ASCII-tokenizable expected_literals) — refusing to run an ungated gate` } }
// P0-PROOF PREFLIGHT (parity with run_comic.py): the orchestrator MUST pass p0ProofClean:true (it ran the zero-credit
// p0_proof gate) before any metered bake; skipP0Proof bakes UNAUDITED and forces the run non-shippable.
const p0Skipped = ARGS.p0ProofClean !== true   // STRICT boolean: only literal true clears P0 (a "false"/"0"/non-bool truthy must NOT pass)
if (p0Skipped && ARGS.skipP0Proof !== true) {
  escalated = escalated || { pid: PANEL_IDS[0] || null, why: 'no p0_proof clearance — run the zero-credit p0_proof gate and pass p0ProofClean:true, or skipP0Proof:true to bake UNAUDITED (forces non-shippable)' }
}
for (let i = 0; i < PANEL_IDS.length && !throttled && !escalated; i++) {
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
      log(`  ✗ gen failed [${gen?.failure_kind || '?'}]: ${reason}`)
      if (isThrottle(gen, reason)) {  // image_gen throttled → stop cleanly; a FRESH run (NOT resumeFromRunId) is required after cooldown
        throttled = true
        escalated = { pid, why: 'image_gen throttled mid-run — stop and wait for cooldown',
          resume_allowed: false, fresh_run_required: true, resume_from_panel: pid,
          how_to_resume: `wait for image_gen cooldown, then launch a FRESH workflow run for the remaining panelIds starting at ${pid}. Do NOT use resumeFromRunId — the cached throttle result would replay and immediately re-throttle.` }
        break
      }
      continue  // non-throttle gen failure → retry this panel (until cap)
    }
    lastGen = gen
    const gate = await panelGate(pid, gen, cfg, ai)
    await writeWiki(pid, gen, gate, ai)
    log(`  panel_gate ${pid}#${ai}: ${gate.verdict.v} — ${gate.verdict.reason}`)
    if (gate.verdict.v === 'keep') { kept.push({ pid, image_path: gen.image_path, image_sha256: gen.image_sha256 || null, attempt: ai, needs_human: false }); done = true; break }
    if (gate.verdict.invariant) pending[pid] = [...(pending[pid] || []), gate.verdict.invariant]  // retry SAME panel w/ repair
  }
  if (throttled) break
  if (!done) {
    if (lastGen) { kept.push({ pid, image_path: lastGen.image_path, image_sha256: lastGen.image_sha256 || null, attempt: totalByPanel[pid], needs_human: true }); flagged.push(pid); log(`  ⚑ ${pid} exhausted ${MAX_TOTAL} attempts → best-so-far flagged for HUMAN review (does NOT auto-finalize), continuing`) }
    else { escalated = escalated || { pid, why: 'no panel ever generated (image_gen down?)' }; break }
  }
}

// ── page assembly_gate + CROSS-FRAME REPAIR ──
// Seed-anchored panels are independent, so within-panel retry handles per-panel quality. The ONE genuinely cross-panel
// concern is DRIFT (the duo identity / pixel style diverging across the page). Cross-frame repair lives HERE: if assembly
// flags drift, the reviewer NAMES the offending panel(s); we re-bake ONLY those with a cross-panel-consistency invariant,
// re-gate them, swap the keepers into `kept`, and re-assemble — bounded by MAX_ROLLBACKS. (NOT the video chain-rollback;
// this is page-coherence repair, the right shape of "fix across frames" for an independent-panel comic.)
let asm = null
const pageMode = kept.some(k => (CONFIG[k.pid] || {}).text_mode === 'baked') ? 'baked' : 'html'
async function runAssembly() {
  const list = kept.map(k => `@${absImg(k.image_path)}`).join(' ')
  const acc = agent([
    `You are the CC reviewer for ARIS comic PAGE assembly_gate (page ${PAGE}). Kept panels in reading order: ${kept.map(k => k.pid).join(' → ')}.`,
    `Read the page's narration/beat from "${COMICJSON}" (page ${PAGE}). Score 0-5: reading_order, page_rhythm. Return ASM_CC_SCHEMA.`,
  ].join('\n'), { label: `asm-cc:${PAGE}`, phase: 'Assembly', schema: ASM_CC_SCHEMA })
  const ids = kept.map(k => k.pid).join(',')
  const textKey = pageMode === 'baked' ? '\\"baked_text_legibility\\":n' : '\\"text_fits_safezone\\":n'
  const textDesc = pageMode === 'baked' ? 'baked_text_legibility=各格烤字是否都清晰' : 'text_fits_safezone=各格留白是否够放气泡'
  // CAST-AWARE assembly (fix after the false B03 rollback): a parallel 2-up may have DISJOINT casts and
  // different worlds BY DESIGN — identity is judged per-character across the panels where that character
  // appears (+ vs the identity refs), never penalised for a character being absent from a panel.
  const castLines = kept.map(k => `${k.pid}=「${((CONFIG[k.pid] || {}).characters || (CONFIG[k.pid] || {}).identity_desc || 'the duo').slice(0, 90)}」`).join(' ')
  const asmRefs = [...new Set(kept.map(k => { const r = (CONFIG[k.pid] || {}).identity_ref; return r && /^[\w][\w./-]*\.png$/.test(r) && !r.includes('..') ? `${PROJ}/${r}` : CANON }))].slice(0, 3)
  const refsStr = asmRefs.map(r => `@${r}`).join(' ')
  const avis = agent([
    `You are the GEMINI visual reviewer for ARIS comic PAGE assembly (page ${PAGE}, mode=${pageMode}); judge the panels SIDE BY SIDE for cross-panel DRIFT. Watchdog CLI:`,
    '```bash',
    `( gemini --model auto-gemini-3 -p "${refsStr} 这些是同一页并排的漫画格,顺序=[${ids}]: ${list} . 每格的预期阵容: ${castLines} 。并排审跨格一致性。只输出一行JSON {\\"cross_panel_identity\\":n,\\"cross_panel_style\\":n,${textKey},\\"drift_panels\\":[\\"漂移格id\\"]} (0-5; identity=同一角色在TA出现的各格之间、以及与身份参考图,是否同一人——**阵容不同/某格没有某角色 = 分镜设计,绝不扣分**;style=像素画风是否同一部片——**冷暖世界差异是设计,不是漂移**;${textDesc};drift_panels=只列出现可识别角色断裂或画风崩坏的格id,没有就[])。" < /dev/null > /tmp/asm_${PAGE}.txt 2>&1 ) & P=$!`,
    `( sleep 240; kill -9 $P 2>/dev/null ) & WD=$!; wait $P 2>/dev/null; kill $WD 2>/dev/null; tail -c 1400 /tmp/asm_${PAGE}.txt`,
    '```',
    `Parse into ASM_VIS_SCHEMA (timed_out=true if none; drift_panels = the panel ids that visibly drift from the rest).`,
  ].join('\n'), { label: `asm-gem:${PAGE}`, phase: 'Assembly', schema: ASM_VIS_SCHEMA })
  const [accR, avisR] = await Promise.all([acc, avis])
  return { cc: accR, gem: avisR, verdict: assemblyVerdict(accR, avisR, pageMode) }
}

if (!escalated && kept.length >= 2) {
  phase('Assembly')
  let asmRound = 0
  while (true) {
    asm = await runAssembly()
    const d = asm.verdict.drift_panels || []
    log(`  assembly_gate ${PAGE} (round ${asmRound}): ${asm.verdict.v} — ${asm.verdict.reason}${d.length ? ' drift=[' + d.join(',') + ']' : ''}`)
    if (asm.verdict.v === 'accept') break
    if (asmRound >= MAX_ROLLBACKS) { log(`  ⚑ assembly still drifting after ${MAX_ROLLBACKS} rollbacks → flagged for HUMAN`); flagged.push(`${PAGE}:assembly`); break }
    const drifters = d.filter(p => kept.some(k => k.pid === p))
    if (!drifters.length) { log(`  ⚑ assembly drift not localized to specific panels → flagged for HUMAN (no blind re-bake)`); flagged.push(`${PAGE}:assembly`); break }
    // STRIKE-ESCALATION: a panel that keeps being named a drifter is a STORYBOARD/BLUEPRINT problem, not a
    // re-bake problem — escalate it to the author layer (rewrite_storyboard_from) instead of burning more bakes.
    // (Comic = independent panels → NO prefix-freeze / rollback-to-prior; the escalation unit is the single panel.)
    for (const pid of drifters) driftStrikes[pid] = (driftStrikes[pid] || 0) + 1
    for (const pid of drifters.filter(p => driftStrikes[p] >= STRIKE_ESCALATE)) {
      if (!rewriteStoryboard.includes(pid)) rewriteStoryboard.push(pid)
      if (!flagged.includes(pid)) flagged.push(pid)
      log(`  ⚑ ${pid} drifted ${driftStrikes[pid]}× (≥${STRIKE_ESCALATE}) → ESCALATE to author layer (rewrite_storyboard_from ${pid}); a re-bake can't fix a spec problem`)
    }
    const rebakeable = drifters.filter(p => driftStrikes[p] < STRIKE_ESCALATE)
    if (!rebakeable.length) { log(`  ⚑ all remaining drifters escalated to an author-layer rewrite → stop`); break }
    log(`  ⤺ CROSS-FRAME repair round ${asmRound + 1}: re-bake drift panel(s) [${rebakeable.join(',')}] (point_of_divergence=${asm.verdict.point_of_divergence || rebakeable[0]})`)
    let anyFixed = false
    for (const pid of rebakeable) {
      if (throttled) break
      const cfg = CONFIG[pid] || {}
      if ((totalByPanel[pid] || 0) >= MAX_TOTAL + MAX_ROLLBACKS) {   // unified per-panel generation budget — cross-frame repair does NOT bypass the '4/panel + 6 repair' cap
        log(`  ⚑ ${pid} hit the generation budget (${MAX_TOTAL + MAX_ROLLBACKS}) → flagged for HUMAN, not re-baked`); if (!flagged.includes(pid)) flagged.push(pid); continue
      }
      const ai = (totalByPanel[pid] || 0) + 1; totalByPanel[pid] = ai
      // carry the panel's accumulated repair invariants so a re-bake can't reintroduce an earlier-fixed failure mode
      const inv = [`CROSS-PANEL CONSISTENCY REPAIR: this panel drifted from the rest of page ${PAGE} — match the canonical duo identity AND the page's flat pixel-art style EXACTLY (same chibi proportions, the exact hoodie/hair/beard colors, the same line + 1-step shading as the sibling panels). Assembly flagged: ${asm.verdict.reason}`, ...(pending[pid] || [])]
      const gen = await generatePanel(pid, cfg, { attemptIndex: ai, invariants: inv })
      if (!gen || gen.status !== 'panel_ready' || !gen.image_path || (gen.bytes || 0) <= 500000) {
        const reason = gen?.gen_failed_reason || 'no image'
        if (isThrottle(gen, reason)) { throttled = true; escalated = { pid, why: 'image_gen throttled during cross-frame repair — stop + resume' } }
        log(`  ✗ ${pid} re-bake failed: ${reason}`); continue
      }
      const gate = await panelGate(pid, gen, cfg, ai)
      await writeWiki(pid, gen, gate, ai)
      log(`  panel_gate ${pid}#${ai} (cross-frame): ${gate.verdict.v}`)
      if (gate.verdict.v === 'keep') {
        const idx = kept.findIndex(k => k.pid === pid)
        if (idx >= 0) kept[idx] = { pid, image_path: gen.image_path, image_sha256: gen.image_sha256 || null, attempt: ai, needs_human: false }
        anyFixed = true
      }
    }
    asmRound++
    if (throttled) break
    if (!anyFixed) { log(`  ⚑ cross-frame repair couldn't re-keep any drifter → stop`); flagged.push(`${PAGE}:assembly`); break }
  }
}

// SHIPPABLE gate (audit P0 #4): a run finalizes ONLY if nothing needs a human, nothing escalated/throttled,
// and (if assembled) assembly accepted. A gate-FAILING best-so-far panel (needs_human) can no longer ride
// assembly-accept + finalize:true into downstream consumers.
const anyNeedsHuman = kept.some(k => k.needs_human) || flagged.length > 0
const shippable = !escalated && !throttled && !anyNeedsHuman && !p0Skipped && (asm ? asm.verdict.v === 'accept' : kept.length >= 1)
// STAGED ACCEPTANCE (KEEP≠final): a panel_gate KEEP is only `panel_accepted`; it becomes `page_accepted` ONLY
// when the page assembly accepts (or there was no cross-panel concern — a single kept panel).
const pageAccepted = asm ? asm.verdict.v === 'accept' : kept.length >= 1
for (const k of kept) k.acceptance_stage = (pageAccepted && !k.needs_human && !flagged.includes(k.pid)) ? 'page_accepted' : 'panel_accepted'
return {
  page: PAGE,
  panel_ids: PANEL_IDS,
  kept: kept,
  flagged_for_human: flagged,
  needs_human: anyNeedsHuman,
  shippable,
  p0_skipped: p0Skipped,
  throttled,
  escalated,
  assembly: asm ? asm.verdict : null,
  rewrite_storyboard: rewriteStoryboard,   // KEEP≠final: panels assembly strike-escalated to an author-layer rewrite
  attempts_per_panel: totalByPanel,
  finalize: FINALIZE && shippable,   // a FINALIZE request is HONORED only when the page is actually shippable
}
