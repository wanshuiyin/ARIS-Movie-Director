#!/usr/bin/env python3
"""run_comic.py — standalone subprocess port of the COMIC branch of packages/core/spiral_engine.js.

FAITHFUL PORT NOTICE
  This is a pure stdlib + subprocess port of spiral_engine.js so a comic can be generated WITHOUT the
  agent/workflow runtime: it shells the `codex` and `gemini` CLIs directly (the runtime's agent() calls
  become subprocess calls). `panel_verdict()` and `assembly_verdict()` are ported LINE-FOR-LINE from the
  engine — the gate is the contract; do not paraphrase it. Mirrors skills/method-figure/scripts/run_spiral.py
  (shared sh/_Fail/extract_json/sha/log + the /tmp/aris_imagegen.lock pattern) and reuses pickup_image.py.

  Per panel: render condition.content_svg -> blueprint PNG -> codex image_gen bake (blueprint + identity ref)
  -> 3 cross-model reviewers (CC narrative ‖ Gemini visual ‖ Codex visual) -> deterministic panel_verdict
  -> write wiki nodes -> on KEEP update comic.json image_path/active_attempt_id -> page assembly_gate
  (cross-frame repair) -> optional viewer build. Caps: 4 bakes/panel + 6 assembly rollbacks.

Usage:
  python3 run_comic.py --project examples/comic_m3_audit --page P02_b08 --panels S12,S13,S14,S15
  [--bake-lang zh] [--max-total 4] [--max-rollbacks 6] [--finalize] [--dry-run] [--skip-assembly]

The generator family (Codex image_gen) can NOT self-acquit: faithfulness is the deterministic token-diff over
Gemini+Codex blind transcriptions. The calling agent (Claude) gives the final structural sign-off; this
orchestrator prints a run-report JSON and never claims that acquittal for itself.
"""
import argparse, hashlib, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK = "/tmp/aris_imagegen.lock"
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
PATH_RE = re.compile(r"^/[A-Za-z0-9._/-]+$")
REL_SVG_RE = re.compile(r"^[\w][\w./-]*\.svg$")
REL_PNG_RE = re.compile(r"^[\w][\w./-]*\.png$")
THROTTLE_RE = re.compile(r"rate.?limit|429|quota|too many requests|overloaded|unavailable|server_?error|50[23]|capacity|MODEL_CAPACITY_EXHAUSTED", re.I)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# ── shared infra (copied verbatim from run_spiral.py) ──
def log(msg): print(f"[run_comic {time.strftime('%H:%M:%S')}] {msg}", flush=True)

class _Fail:
    def __init__(self, msg): self.returncode = 1; self.stdout = ""; self.stderr = msg

def sh(cmd, timeout, **kw):
    try:
        return subprocess.run(cmd, timeout=timeout, capture_output=True, text=True, **kw)
    except subprocess.TimeoutExpired as e:
        return _Fail(f"timeout after {timeout}s: {e}")
    except Exception as e:
        return _Fail(f"subprocess error: {e}")

def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16] if os.path.exists(path) else ""

def bake_run(cmd, timeout):
    """Run the codex image bake in its OWN process group and kill the WHOLE group on timeout — the engine's
    `pkill -P` watchdog, so a runaway image_gen child can't keep writing into the global dir and pollute the
    next panel's pickup. (sh()/subprocess.run timeout would orphan the children.)"""
    import signal
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    except Exception as e:
        return _Fail(f"bake spawn error: {e}")
    try:
        out, _ = p.communicate(timeout=timeout)
        r = _Fail(""); r.returncode = p.returncode; r.stdout = out or ""; r.stderr = ""; return r
    except subprocess.TimeoutExpired:
        try: os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except Exception:
            try: p.kill()
            except Exception: pass
        try: out, _ = p.communicate(timeout=10)
        except Exception: out = ""
        return _Fail(f"bake timeout after {timeout}s (process group killed)\n{out or ''}")

# clamp every reviewer score to a finite 0..5 (the engine's SCORE schema bound). The pure-subprocess port has
# NO schema validation, so a stray 50 could KEEP and a numeric string could crash min(); out-of-range/non-numeric
# → None (fail-closed: the verdict's completeness check then forces a retry). Numeric strings ("4") → 4.0.
SCORE_KEYS = ("identity_consistency", "style_consistency", "composition_readability", "artifact_severity",
              "baked_text_quality", "narrative_beat_fidelity", "composition_story", "reading_order", "page_rhythm",
              "cross_panel_identity", "cross_panel_style", "text_fits_safezone", "baked_text_legibility")
def clamp_scores(rv):
    if not isinstance(rv, dict): return rv
    for k in SCORE_KEYS:
        if k in rv:
            try: f = float(rv[k])
            except (TypeError, ValueError): rv[k] = None; continue
            rv[k] = f if 0 <= f <= 5 else None
    return rv

def extract_json(text, required_key=None):
    """pull the first JSON object that (optionally) has required_key — uses a real JSON decoder so braces
    inside string values (e.g. observed_literals, repair text) don't break parsing; skips prose preambles."""
    dec = json.JSONDecoder()
    s = text.find("{")
    while s != -1:
        try:
            j, _ = dec.raw_decode(text[s:])
            if isinstance(j, dict) and (required_key is None or required_key in j): return j
        except Exception: pass
        s = text.find("{", s + 1)
    return None

# ── paths + ids (ported from engine 15-48) ──
def derive_paths(project, repo):
    PROJ = os.path.abspath(project)
    REPO = os.path.abspath(repo) if repo else re.sub(r"/examples/[^/]+/?$", "", PROJ)
    if not PATH_RE.match(PROJ): sys.exit(f"unsafe --project (abs path, no spaces/metachars, {PATH_RE.pattern}): {PROJ}")
    if not PATH_RE.match(REPO): sys.exit(f"unsafe --repo: {REPO}")
    return {
        "PROJ": PROJ, "REPO": REPO,
        "PANELS": PROJ + "/panels", "NODES": PROJ + "/wiki/nodes",
        "CANON": PROJ + "/assets/duo_canonical_ref_v001.png", "BIBLE": PROJ + "/ART_BIBLE.md",
        "COMICJSON": PROJ + "/comic.json",
        "PICKUP": HERE.rsplit("/skills/", 1)[0] + "/skills/method-figure/scripts/pickup_image.py",
        "BUILD": REPO + "/packages/viewer/build_comic.py",
    }

def validate_ids(page, panel_ids):
    if not ID_RE.match(page): sys.exit(f"unsafe page id: {page!r}")
    for p in panel_ids:
        if not ID_RE.match(p): sys.exit(f"unsafe panel id: {p!r}")

def rel_img(paths, p):
    if not p: return ""
    return p[len(paths["PROJ"]) + 1:] if p.startswith(paths["PROJ"] + "/") else p

def abs_img(paths, p):
    if not p: return ""
    return p if p.startswith("/") else paths["PROJ"] + "/" + p

# ── conditions: read comic.json directly (no agent round-trip; the sandbox-fs reason is gone) ──
def loc_text(x, lang):
    if x is None: return ""
    if isinstance(x, str): return x
    if isinstance(x, dict): return x.get(lang) or x.get("en") or x.get("zh") or ""
    return str(x)

def load_conditions(comic, panel_ids, bake_lang):
    panels = comic.get("panels", {})
    out = {}
    for pid in panel_ids:
        p = panels.get(pid, {}) or {}
        c = p.get("condition", {}) or {}
        bubbles = []
        for b in p.get("bubbles", []) or []:
            t = loc_text(b.get("text"), bake_lang)
            if t and t.strip(): bubbles.append(f"{b.get('speaker','')} says: {t}")
        chibi = c.get("chibi_action", {}) or {}
        out[pid] = {
            "text_mode": p.get("text_mode") or comic.get("defaults", {}).get("text_mode") or "html",
            "content_svg": c.get("content_svg"),
            "world": c.get("world", ""),
            "scene": c.get("scene", ""),
            "identity_ref": c.get("identity_ref"),
            "identity_desc": c.get("identity_desc", ""),
            "characters": c.get("characters", ""),
            "chibi_executor": chibi.get("executor", ""),
            "chibi_reviewer": chibi.get("reviewer", ""),
            "bubbles_all": bubbles,
            "expected_literals": c.get("expected_literals", []) or [],
        }
    return out

def cfg_usable(c):
    # FAIL-CLOSED: EVERY panel needs a content_svg blueprint (engine contract — null is rejected); a baked figure
    # ALSO needs ascii-tokenizable expected_literals (engine 346-348). (was: an html panel with no svg slipped through.)
    if not c or not c.get("text_mode"): return False
    if not c.get("content_svg"): return False
    if c["text_mode"] != "baked": return True
    exp = c.get("expected_literals")
    return isinstance(exp, list) and len(exp) > 0 and all(
        isinstance(e, str) and re.findall(r"[a-z0-9+._-]+", e.lower()) for e in exp)

# ── deterministic verdicts — PORTED LINE-FOR-LINE from spiral_engine.js (do not paraphrase) ──
def _num(x, d=0):
    return x if isinstance(x, (int, float)) else d

def panel_verdict(cc, gem, cdx, cfg):
    cc, gem, cdx, cfg = cc or {}, gem or {}, cdx or {}, cfg or {}
    mode = cfg.get("text_mode") or "html"
    if cc.get("timed_out") or gem.get("timed_out") or cdx.get("timed_out"):
        return {"v": "retry_panel", "reason": "a reviewer timed out — fail-safe retry", "invariant": ""}
    vis_core = lambda r: [r.get("identity_consistency"), r.get("style_consistency"), r.get("composition_readability"), r.get("artifact_severity")]
    if not all(all(x is not None for x in vis_core(r)) for r in (gem, cdx)):
        return {"v": "retry_panel", "reason": "a visual reviewer returned incomplete core scores (fail-closed)", "invariant": ""}
    baked = mode == "baked"
    narr = min(_num(cc.get("narrative_beat_fidelity"), 0), _num(cc.get("composition_story"), 5))
    idents = [r.get("identity_consistency") for r in (gem, cdx) if r.get("identity_consistency") is not None]
    styles = [r.get("style_consistency") for r in (gem, cdx) if r.get("style_consistency") is not None]
    comps = [r.get("composition_readability") for r in (gem, cdx) if r.get("composition_readability") is not None]
    min_ident = min(idents) if idents else 0
    min_style, max_style = (min(styles), max(styles)) if styles else (0, 0)
    min_comp, max_comp = (min(comps), max(comps)) if comps else (0, 0)
    gem_art, cdx_art = _num(gem.get("artifact_severity")), _num(cdx.get("artifact_severity"))
    artifact_bad = (gem_art >= 4 and cdx_art >= 3) or (cdx_art >= 4 and gem_art >= 3)
    disagree = abs(_num(gem.get("identity_consistency")) - _num(cdx.get("identity_consistency")))
    style_ok = min_style >= 4 or (min_style >= 3 and max_style >= 4)
    comp_ok = min_comp >= 4 or (min_comp >= 3 and max_comp >= 4)
    repair = cdx.get("failure_mode_positive_invariant") or gem.get("failure_mode_positive_invariant") or ""
    anatomy_defect = gem.get("anatomy_defect_present") is True or cdx.get("anatomy_defect_present") is True
    if baked:
        btqs = [gem.get("baked_text_quality"), cdx.get("baked_text_quality")]
        both_btq = all(x is not None for x in btqs)
        min_btq = min(btqs) if both_btq else 0
        corruption = gem.get("content_corruption_present") is True or cdx.get("content_corruption_present") is True

        def sets(arr):
            if not isinstance(arr, list): return None
            cset, fset = set(), set()
            for s in arr:
                if not isinstance(s, str): continue
                t = s.lower()
                for x in re.findall(r"[a-z0-9+._:|/-]+", t): cset.add(x)   # COARSE: keep : | / so timestamps/versions/paths stay WHOLE
                for x in re.findall(r"[a-z0-9]+", t): fset.add(x)
            joined = re.sub(r"\s+", " ", " ".join(s.lower() for s in arr if isinstance(s, str)))
            return (cset, fset, joined)
        gem_s, cdx_s = sets(gem.get("observed_literals")), sets(cdx.get("observed_literals"))
        reviewers_ok = gem_s is not None and cdx_s is not None
        structured = lambda e: bool(re.search(r"[0-9:]", e))   # number / timestamp / version / code → EXACT coarse token only

        def hit(e, S):
            e = e.lower().strip()
            if " " in e: return e in S[2]                       # multi-word phrase → ordered substring (no token reshuffle)
            if structured(e): return e in S[0]                 # "+6.25"/"t-24:00:01" must NOT satisfy "+6.2"/"t-24:00:00"
            if e in S[0]: return True
            parts = re.findall(r"[a-z0-9]+", e)
            return len(parts) > 0 and all(p in S[1] for p in parts)
        _el = cfg.get("expected_literals")
        exp = [e for e in _el if isinstance(e, str)] if isinstance(_el, list) else []
        missing = [e for e in exp if not (hit(e, gem_s) and hit(e, cdx_s))] if reviewers_ok else exp
        figure_ungated = bool(cfg.get("content_svg")) and len(exp) == 0
        tokens_ok = reviewers_ok and not figure_ungated and len(missing) == 0
        text_ok = both_btq and min_btq >= 4 and not corruption and tokens_ok
        text_reason = f"btq={min_btq if both_btq else 'NO'} corruption={corruption} reviewersOk={reviewers_ok} missing={missing}{' UNGATED' if figure_ungated else ''}"
    else:
        safezone = gem.get("safezone_present") is True or cdx.get("safezone_present") is True
        stray = gem.get("stray_text_present") is True or cdx.get("stray_text_present") is True
        text_ok = safezone and not stray
        text_reason = f"safezone={safezone} stray={stray}"
    reason = (f"[{mode}] narr={narr} identity={min_ident} style={min_style}/{max_style} comp={min_comp}/{max_comp} "
              f"art(g/c)={gem_art}/{cdx_art} {text_reason} anatomyDefect={anatomy_defect} disagreeId={disagree}")
    if narr >= 4 and min_ident >= 4 and style_ok and comp_ok and not artifact_bad and text_ok and not anatomy_defect and disagree < 2:
        return {"v": "keep", "reason": "KEEP — " + reason, "invariant": ""}
    return {"v": "retry_panel", "reason": "RETRY — " + reason, "invariant": repair}

def assembly_verdict(cc, gem, mode="html"):
    cc, gem = cc or {}, gem or {}
    text_dim = _num(gem.get("baked_text_legibility")) if mode == "baked" else _num(gem.get("text_fits_safezone"))
    dims = [_num(cc.get("reading_order")), _num(cc.get("page_rhythm")), _num(gem.get("cross_panel_identity")), _num(gem.get("cross_panel_style")), text_dim]
    min_dim, ssum = min(dims), sum(dims)
    drift = [x for x in (gem.get("drift_panels") or []) if isinstance(x, str)]
    if min_dim < 2 or ssum < 16:
        return {"v": "rollback", "reason": f"[{mode}] assembly weak (min={min_dim} sum={ssum}/25)", "drift_panels": drift, "point_of_divergence": (drift[0] if drift else None)}
    return {"v": "accept", "reason": f"[{mode}] assembly ok (min={min_dim} sum={ssum}/25)", "drift_panels": [], "point_of_divergence": None}

# ── generation: render content_svg -> blueprint PNG -> codex image_gen bake -> pickup (engine 191-271) ──
def bake_prompt_body(cfg, bake_lang, invariants):
    id_desc = cfg.get("identity_desc") or "the CANONICAL DUO — blue executor: brown hair, NO beard; green reviewer: dark hair, beard"
    chars = cfg.get("characters") or " ".join(x for x in [
        f"executor action: {cfg['chibi_executor']}." if cfg.get("chibi_executor") else "",
        f"reviewer action: {cfg['chibi_reviewer']}." if cfg.get("chibi_reviewer") else ""] if x)
    bubbles = [b for b in (cfg.get("bubbles_all") or []) if isinstance(b, str) and b.strip()]
    if bubbles:
        bubble_line = f"Bake these speech bubbles as clean readable comic lettering ({bake_lang}): " + "  ||  ".join(bubbles)
    else:
        bubble_line = "This panel has NO speech bubbles — bake NO dialogue text (the technical figure's text is the only text)."
    repair = [i for i in (invariants or []) if i]
    lines = [
        f"WORLD = {cfg.get('world')}  → apply the ART_BIBLE §0.5 two-world lighting (warm-lab = warm Edison-glow human world; dark-cyber = dark screen-lit digital world).",
        f"SCENE: {cfg.get('scene')}",
        f"Render the character(s) from reference image #2 EXACTLY as depicted there — {id_desc}. {chars}",
        "Integrate the technical figure from reference image #1 onto a board/screen/dashboard in the scene. Reproduce its numbers, labels and code EXACTLY as they appear in image #1 — do NOT alter, re-spell, round, or invent any number or token.",
        bubble_line,
        "ONE coherent flat pixel-art comic panel. No watermark. No UI text beyond the integrated figure and the bubbles (if any).",
        ("REPAIR CONSTRAINTS (earlier attempts failed for these reasons — honor every one): " + "  |  ".join(repair)) if repair else "",
    ]
    return "\n".join(x for x in lines if x)

def acquire_lock():
    for _ in range(600):
        try:
            os.mkdir(LOCK); return True
        except FileExistsError:
            try:
                if os.path.isdir(LOCK) and time.time() - os.path.getmtime(LOCK) > 900: os.rmdir(LOCK)
            except OSError: pass
            time.sleep(2)
    return False

def release_lock(held):
    if held:
        try: os.rmdir(LOCK)
        except OSError: pass

def generate_panel(paths, pid, cfg, ai, invariants, args, bakelog):
    aTag = "a" + str(ai).zfill(2)
    out = f"{paths['PANELS']}/{pid}_panel_{aTag}.png"
    cdir = f"{paths['PANELS']}/_content_refs"
    cpng = f"{cdir}/{pid}_{aTag}.png"
    svg_rel = cfg.get("content_svg") or ""
    if not REL_SVG_RE.match(svg_rel) or ".." in svg_rel:
        return {"status": "generation_failed", "image_path": "", "gen_failed_reason": f"unsafe/empty content_svg: {svg_rel!r}"}
    id_rel = cfg.get("identity_ref") or ""
    if id_rel and (not REL_PNG_RE.match(id_rel) or ".." in id_rel):
        return {"status": "generation_failed", "image_path": "", "gen_failed_reason": f"unsafe identity_ref: {id_rel!r}"}
    id_ref_abs = f"{paths['PROJ']}/{id_rel}" if id_rel else paths["CANON"]
    os.makedirs(cdir, exist_ok=True)
    # STEP 1 — render the content blueprint SVG -> persistent PNG (deterministic; no lock needed)
    rc = sh([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
             "--window-size=1280,720", f"--screenshot={cpng}", f"file://{paths['PROJ']}/{svg_rel}"], 45)
    if not os.path.exists(cpng) or os.path.getsize(cpng) < 1000:
        return {"status": "generation_failed", "image_path": "", "gen_failed_reason": f"content_svg render failed (need headless Chrome): {getattr(rc,'stderr','')[:200]}"}
    # STEP 2 — assemble prompt = ART_BIBLE + body, then BAKE (codex image_gen, 2 refs) under the global lock
    bible = open(paths["BIBLE"], encoding="utf-8").read() if os.path.exists(paths["BIBLE"]) else ""
    full_prompt = (f"Paste these style rules first:\n{bible}\n\nThen render this panel:\n" if bible else "") + bake_prompt_body(cfg, args.bake_lang, invariants)
    held = acquire_lock()
    if not held:
        return {"status": "generation_failed", "image_path": "", "failure_kind": "other", "gen_failed_reason": "image-gen lock contended >20min"}
    try:
        marker = time.time()
        r = bake_run(["codex", "exec", full_prompt, "-i", cpng, "-i", id_ref_abs,
                      "--sandbox", "workspace-write", "-c", f"model_reasoning_effort={args.effort}", "--skip-git-repo-check"],
                     args.bake_timeout)
        open(bakelog, "w").write((getattr(r, "stdout", "") or "") + "\n---STDERR---\n" + (getattr(r, "stderr", "") or ""))
        pk = sh(["python3", paths["PICKUP"], "--marker", str(marker), "--out", out,
                 "--min-bytes", str(args.min_bytes), "--log", bakelog, "--aspect", str(1280 / 720)], 60)
    finally:
        release_lock(held)
    if pk.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > args.min_bytes:
        pj = extract_json(pk.stdout) or {}
        return {"status": "panel_ready", "image_path": out, "bytes": os.path.getsize(out),
                "image_sha256": pj.get("sha256") or sha(out), "text_mode": cfg.get("text_mode")}
    blog_txt = open(bakelog, encoding="utf-8").read() if os.path.exists(bakelog) else ""
    kind = "throttle" if THROTTLE_RE.search(blog_txt) else "other"
    return {"status": "generation_failed", "image_path": "", "failure_kind": kind,
            "gen_failed_reason": f"no native image (pickup rc={pk.returncode}): {(pk.stderr or '')[:200]}"}

def is_throttle(gen, reason=""):
    if not gen: return False
    if gen.get("failure_kind") == "throttle": return True
    return not gen.get("failure_kind") and bool(re.search(r"rate|limit|throttl|server|unavailable|429|quota", reason or "", re.I))

# ── the 3 cross-model reviewers (ported engine 274-316) ──
def _vis_json(baked):
    if baked:
        return ('{"identity_consistency":n,"style_consistency":n,"composition_readability":n,"artifact_severity":n,'
                '"baked_text_quality":n,"observed_literals":["verbatim tokens you can READ — never guess"],'
                '"content_corruption_present":false,"character_hand_count":["blue:2","green:2"],"anatomy_defect_present":false,'
                '"failure_mode_positive_invariant":""}')
    return ('{"identity_consistency":n,"style_consistency":n,"composition_readability":n,"artifact_severity":n,'
            '"safezone_present":false,"stray_text_present":false,"character_hand_count":["blue:2","green:2"],'
            '"anatomy_defect_present":false,"failure_mode_positive_invariant":""}')

ANATOMY = (' If the panel has characters, ENUMERATE each one\'s visible hands and set anatomy_defect_present=true on any '
           'wrong count (!=2)/third/floating/merged hand (single-vote veto).')

def _id_desc(cfg):
    return cfg.get("identity_desc") or "blue executor: brown hair, NO beard; green reviewer: dark hair, beard"

def review_cc(paths, pid, cfg, img, args):
    # CC scores STORY; it may glance at the actual panel to judge composition_story (engine 284).
    p = (f'You are the CC NARRATIVE reviewer in ARIS comic panel_gate for {pid} (mode={cfg.get("text_mode")}). '
         f'Judge STORY only — you may glance at the attached panel image but score narrative, not pixels. '
         f'Read panel {pid} from "{paths["COMICJSON"]}": its .condition.scene, .bubbles, .caption, and the page beat. '
         f'Score 0-5: narrative_beat_fidelity, composition_story. Output ONLY one JSON line: '
         '{"narrative_beat_fidelity":n,"composition_story":n,"timed_out":false}')
    r = sh(["codex", "exec", p, "-i", img, "--sandbox", "read-only", "-c", f"model_reasoning_effort={args.review_effort}", "--skip-git-repo-check"], args.review_timeout)
    return extract_json((getattr(r, "stdout", "") or "") + (getattr(r, "stderr", "") or ""), required_key="narrative_beat_fidelity") or {"timed_out": True}

def review_gemini(paths, pid, img, idref, id_desc, baked, args):
    shape = _vis_json(baked)
    p = (f"@{img} @{idref} @{paths['BIBLE']} Review this ARIS comic panel ({pid}). Image #1 is the panel; image #2 is the "
         f"identity reference ({id_desc}) — judge each character against it. Honor ART_BIBLE. Score 0-5. baked={baked}: if baked, "
         f"observed_literals = verbatim transcription of every number/label/code you can READ (never guess); content_corruption_present = "
         f"any garbled/illegal token.{ANATOMY} Output ONLY one JSON line: {shape}")
    r = sh(["gemini", "--model", "auto-gemini-3", "-p", p], args.review_timeout)
    return extract_json((getattr(r, "stdout", "") or "") + (getattr(r, "stderr", "") or ""), required_key="identity_consistency") or {"timed_out": True}

def review_codex(paths, pid, img, idref, id_desc, bible_excerpt, baked, args):
    # NOTE: codex `-i` is --image; do NOT pass ART_BIBLE.md (a .md) via -i. Inline the style rules as text instead;
    # attach only the two images (panel + identity ref).
    shape = _vis_json(baked)
    p = (f"Review this ARIS comic panel ({pid}). Image #1 is the panel; image #2 is the identity reference "
         f"({id_desc}) — judge each character against it. Score 0-5. baked={baked}: if baked, observed_literals = verbatim "
         f"transcription of numbers/labels/code you can READ (never guess); content_corruption_present = garbled tokens.{ANATOMY} "
         f"Style rules to honor:\n{bible_excerpt}\nOutput ONLY one JSON line: {shape}")
    r = sh(["codex", "exec", p, "-i", img, "-i", idref,
            "--sandbox", "read-only", "-c", f"model_reasoning_effort={args.review_effort}", "--skip-git-repo-check"], args.review_timeout)
    return extract_json((getattr(r, "stdout", "") or "") + (getattr(r, "stderr", "") or ""), required_key="identity_consistency") or {"timed_out": True}

def panel_gate(paths, pid, gen, cfg, ai, args):
    mode = cfg.get("text_mode") or gen.get("text_mode") or "html"
    baked = mode == "baked"
    img = abs_img(paths, gen["image_path"])
    id_rel = cfg.get("identity_ref") if cfg.get("identity_ref") and REL_PNG_RE.match(cfg.get("identity_ref") or "") and ".." not in (cfg.get("identity_ref") or "") else ""
    idref = f"{paths['PROJ']}/{id_rel}" if id_rel else paths["CANON"]
    id_desc = _id_desc(cfg)
    bible = (open(paths["BIBLE"], encoding="utf-8").read()[:2500] if os.path.exists(paths["BIBLE"]) else "")
    cc = clamp_scores(review_cc(paths, pid, cfg, img, args))
    gem = clamp_scores(review_gemini(paths, pid, img, idref, id_desc, baked, args))
    cdx = clamp_scores(review_codex(paths, pid, img, idref, id_desc, bible, baked, args))
    return {"cc": cc, "gem": gem, "cdx": cdx, "verdict": panel_verdict(cc, gem, cdx, cfg)}

# ── persistence: wiki nodes + comic.json (reimplemented as direct file writes; engine 311-330) ──
def add_edges(paths, edges):
    """Append runtime edges to wiki/edges.jsonl (dedup by (src,dst,type)) so validate_wiki sees resolved
    attempt_of / reviews / decides / failure_of provenance for what run_comic actually wrote."""
    ep = paths["PROJ"] + "/wiki/edges.jsonl"
    existing = set()
    if os.path.exists(ep):
        for line in open(ep, encoding="utf-8"):
            line = line.strip()
            if not line: continue
            try:
                e = json.loads(line); existing.add((e.get("src"), e.get("dst"), e.get("type")))
            except Exception: pass
    with open(ep, "a", encoding="utf-8") as f:
        for s, d, t in edges:
            if (s, d, t) not in existing:
                f.write(json.dumps({"src": s, "dst": d, "type": t}, ensure_ascii=False) + "\n"); existing.add((s, d, t))

def write_wiki(paths, pid, gen, gate, ai):
    os.makedirs(paths["NODES"], exist_ok=True)
    sl = pid.lower(); aTag = "a" + str(ai).zfill(2); v = gate["verdict"]["v"]
    ts = "2026-06-08T00:00:00+00:00"
    panel_node = f"panel:{sl}_aris_comic_v1"; attempt_node = f"attempt:{sl}_{aTag}"
    def w(name, obj): json.dump(obj, open(f"{paths['NODES']}/{name}.json", "w"), ensure_ascii=False, indent=1)
    w(f"panel_attempt_{sl}_{aTag}", {"node_id": attempt_node, "node_type": "panel_attempt", "status": "under_review",
        "title": f"{pid} panel attempt {ai}", "created_at": ts,
        "payload": {"source_panel_id": panel_node, "image_path": rel_img(paths, gen["image_path"]),
                    "attempt_index": ai, "model": "codex_image_gen", "is_baked_duo": True}})
    edges = [(attempt_node, panel_node, "attempt_of")]
    for rv, who in ((gate["cc"], "cc"), (gate["gem"], "gemini"), (gate["cdx"], "codex")):
        rnode = f"review:panel_{sl}_{aTag}_{who}"
        # schema-valid review payload: target_node_id/reviewer/gate_kind are REQUIRED (validate_wiki); keep the raw
        # reviewer scores too. (explicit keys last so a malformed reviewer JSON can't clobber the required fields.)
        w(f"review_panel_{sl}_{aTag}_{who}", {"node_id": rnode, "node_type": "review",
            "status": "final", "title": f"{who} review {pid} a{ai}", "created_at": ts,
            "payload": {**(rv if isinstance(rv, dict) else {"raw": rv}),
                        "target_node_id": attempt_node, "reviewer": who, "gate_kind": "panel"}})
        edges.append((rnode, attempt_node, "reviews"))
    dnode = f"decision:panel_{sl}_{aTag}"
    w(f"decision_panel_{sl}_{aTag}", {"node_id": dnode, "node_type": "decision", "status": "final",
        "title": f"panel_gate {pid} a{ai} → {v}", "created_at": ts,
        "payload": {"gate_kind": "panel", "target_node_id": attempt_node, "verdict": v,
                    "reviewer_families": {"cc": "anthropic", "gemini": "google", "codex": "openai"},  # cross-family provenance: the visual acquitters (gemini/codex) differ from the Claude author
                    "reasoning": gate["verdict"]["reason"][:300], "repair_instruction": gate["verdict"].get("invariant", "")}})
    edges.append((dnode, attempt_node, "decides"))
    if v != "keep":
        fnode = f"fail:{sl}_{aTag}"
        w(f"fail_{sl}_{aTag}", {"node_id": fnode, "node_type": "failure_mode", "status": "active", "created_at": ts,
            "payload": {"active": True, "affected_shot_ids": [pid], "layer": "panel_visual", "repair_pattern": gate["verdict"].get("invariant", "")}})
        edges.append((fnode, attempt_node, "failure_of"))
    add_edges(paths, edges)

def update_comic_json(paths, comic, pid, gen, ai):
    aTag = "a" + str(ai).zfill(2)
    panel = comic.setdefault("panels", {}).setdefault(pid, {})
    panel["image_path"] = rel_img(paths, gen["image_path"])
    panel["active_attempt_id"] = f"{pid}_{aTag}"
    panel["wiki_node_id"] = f"panel:{pid.lower()}_aris_comic_v1"
    json.dump(comic, open(paths["COMICJSON"], "w"), ensure_ascii=False, indent=2)

# ── assembly_gate + cross-frame repair (ported engine 388-464) ──
def run_assembly(paths, page, kept, cfg_map, page_mode, args):
    ids = ",".join(k["pid"] for k in kept)
    listimgs = " ".join(f"@{abs_img(paths, k['image_path'])}" for k in kept)
    cc_p = (f'You are the CC reviewer for ARIS comic PAGE assembly_gate (page {page}). Kept panels: {ids}. '
            f'Read the page narration/beat from "{paths["COMICJSON"]}". Score 0-5. Output ONLY one JSON line: '
            '{"reading_order":n,"page_rhythm":n}')
    cc_r = sh(["codex", "exec", cc_p, "--sandbox", "read-only", "-c", f"model_reasoning_effort={args.review_effort}", "--skip-git-repo-check"], args.review_timeout)
    cc = clamp_scores(extract_json((getattr(cc_r, "stdout", "") or "") + (getattr(cc_r, "stderr", "") or ""), required_key="reading_order") or {"timed_out": True})
    refs = []
    for k in kept:
        r = (cfg_map.get(k["pid"]) or {}).get("identity_ref")
        refs.append(f"{paths['PROJ']}/{r}" if r and REL_PNG_RE.match(r) and ".." not in r else paths["CANON"])
    refs = list(dict.fromkeys(refs))[:3]
    text_key = '"baked_text_legibility":n' if page_mode == "baked" else '"text_fits_safezone":n'
    # CAST-AWARE (engine 405-414): tell the reviewer each panel's INTENDED cast so a designed cast/world
    # difference (disjoint casts, warm vs cyber world) is never mis-flagged as drift.
    cast_lines = " ".join(f"{k['pid']}=「{((cfg_map.get(k['pid']) or {}).get('characters') or (cfg_map.get(k['pid']) or {}).get('identity_desc') or 'the duo')[:90]}」" for k in kept)
    gp = (" ".join(f"@{r}" for r in refs) + f" These side-by-side comic panels [{ids}]: {listimgs} . Intended cast per panel: {cast_lines} . "
          "Judge cross-panel DRIFT (same character across the panels where they appear + vs the ref = identity — a panel simply "
          "NOT containing a character is design, NEVER a penalty; same pixel style = style — warm vs cyber world is design, not drift). "
          "Output ONLY one JSON line: "
          '{"cross_panel_identity":n,"cross_panel_style":n,' + text_key + ',"drift_panels":["id of a panel with a real identity break or style collapse, else omit"]}')
    g_r = sh(["gemini", "--model", "auto-gemini-3", "-p", gp], args.review_timeout)
    gem = clamp_scores(extract_json((getattr(g_r, "stdout", "") or "") + (getattr(g_r, "stderr", "") or ""), required_key="cross_panel_identity") or {"timed_out": True})
    return {"cc": cc, "gem": gem, "verdict": assembly_verdict(cc, gem, page_mode)}

# ── main ──
def parse_args():
    ap = argparse.ArgumentParser(description="standalone comic spiral (faithful subprocess port of spiral_engine.js)")
    ap.add_argument("--project", required=True, help="project/example dir (has comic.json, panels/, wiki/)")
    ap.add_argument("--repo", default="", help="repo root (default: strip /examples/<name> from --project)")
    ap.add_argument("--page", required=True, help="page id")
    ap.add_argument("--panels", required=True, help="comma-separated panel ids, e.g. S12,S13,S14,S15")
    ap.add_argument("--bake-lang", default="zh", help="bubble language baked into the image (zh proven clean)")
    ap.add_argument("--max-total", type=int, default=4); ap.add_argument("--max-rollbacks", type=int, default=6)
    ap.add_argument("--strike-escalate", type=int, default=2)   # a panel drifting ≥N assembly rounds → author-layer rewrite
    ap.add_argument("--finalize", action="store_true"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-assembly", action="store_true")
    ap.add_argument("--skip-p0-proof", action="store_true", help="bake without a clean decision:p0_proof_* node (UNAUDITED; forces the run non-shippable)")
    ap.add_argument("--bake-timeout", type=int, default=600); ap.add_argument("--review-timeout", type=int, default=300)
    ap.add_argument("--effort", default="high"); ap.add_argument("--review-effort", default="xhigh")
    ap.add_argument("--min-bytes", type=int, default=500000)
    return ap.parse_args()

def main():
    args = parse_args()
    panel_ids = [s.strip() for s in args.panels.split(",") if s.strip()]
    paths = derive_paths(args.project, args.repo)
    validate_ids(args.page, panel_ids)
    if not os.path.exists(paths["COMICJSON"]): sys.exit(f"comic.json missing: {paths['COMICJSON']}")
    comic = json.load(open(paths["COMICJSON"], encoding="utf-8"))
    cfg_map = load_conditions(comic, panel_ids, args.bake_lang)

    missing = [p for p in panel_ids if not cfg_usable(cfg_map.get(p))]
    if missing:
        sys.exit(f"FAIL-CLOSED: unusable cfg for {missing} (missing text_mode, missing content_svg blueprint, or a baked figure with no ASCII-tokenizable expected_literals) — refusing to run an ungated gate")

    if args.dry_run:
        log(f"dry-run: {len(panel_ids)} panels, all cfg-usable. Printing bake prompts (NO image_gen):")
        for pid in panel_ids:
            print(f"\n===== BAKE PROMPT {pid} ({cfg_map[pid]['text_mode']}) =====")
            print(bake_prompt_body(cfg_map[pid], args.bake_lang, []))
            print(f"  refs: content_svg={cfg_map[pid]['content_svg']}  identity_ref={cfg_map[pid].get('identity_ref') or '(canonical duo)'}")
            print(f"  expected_literals={cfg_map[pid]['expected_literals']}")
        return

    # P0-PROOF PREFLIGHT — no metered image credit before the zero-credit proof gate cleared: require a clean
    # decision:p0_proof_* node in the wiki, OR an explicit --skip-p0-proof ack (which forces the run non-shippable).
    def _p0_clean():
        nd = paths["NODES"]
        if not os.path.isdir(nd): return False
        for fn in os.listdir(nd):
            if not fn.endswith(".json") or "p0" not in fn.lower(): continue
            try: d = json.load(open(os.path.join(nd, fn), encoding="utf-8"))
            except Exception: continue
            pl = d.get("payload") or {}
            if d.get("node_type") == "decision" and str(d.get("status", "")).lower() == "final" \
               and str(d.get("node_id", "")).startswith("decision:p0_proof") \
               and str(pl.get("gate_kind", "")).lower() == "p0_proof" \
               and str(pl.get("verdict", "")).lower() in ("pass", "clean", "approve", "keep", "ship", "proceed"):
                return True
        return False
    p0_skipped = False
    if not _p0_clean():
        if not args.skip_p0_proof:
            sys.exit("FAIL-CLOSED: no clean decision:p0_proof_* node in the wiki — run the zero-credit p0_proof gate "
                     "(comic-cross-layer-gate <comic> --gate p0_proof) BEFORE spending image credit, "
                     "or pass --skip-p0-proof to bake UNAUDITED (forces the run non-shippable).")
        p0_skipped = True
        log("⚠ --skip-p0-proof: baking WITHOUT a p0_proof gate node → run is UNAUDITED and will be marked non-shippable")

    kept, flagged, total_by, pending = [], [], {}, {}
    throttled, escalated = False, None
    for pid in panel_ids:
        if throttled or escalated: break
        cfg = cfg_map[pid]; done = False; last_gen = None
        while not done and total_by.get(pid, 0) < args.max_total:
            total_by[pid] = total_by.get(pid, 0) + 1; ai = total_by[pid]
            inv = list(pending.get(pid, []))
            log(f"▶ {pid} attempt {ai} [{cfg['text_mode']}]" + (f" +{len(inv)} repair" if inv else ""))
            bakelog = f"{paths['PANELS']}/{pid}_a{ai}.bakelog.txt"
            gen = generate_panel(paths, pid, cfg, ai, inv, args, bakelog)
            if gen.get("status") != "panel_ready" or not gen.get("image_path") or gen.get("bytes", 0) <= args.min_bytes:
                reason = gen.get("gen_failed_reason", "no image")
                log(f"  ✗ gen failed [{gen.get('failure_kind','?')}]: {reason}")
                if is_throttle(gen, reason):
                    throttled = True
                    escalated = {"pid": pid, "why": "image_gen throttled mid-run", "resume_allowed": False, "fresh_run_required": True,
                                 "resume_from_panel": pid, "how_to_resume": f"wait for cooldown, then launch a FRESH run for the remaining panels starting at {pid}; do NOT reuse cached state"}
                    break
                continue
            last_gen = gen
            gate = panel_gate(paths, pid, gen, cfg, ai, args)
            write_wiki(paths, pid, gen, gate, ai)
            log(f"  panel_gate {pid}#{ai}: {gate['verdict']['v']} — {gate['verdict']['reason']}")
            if gate["verdict"]["v"] == "keep":
                update_comic_json(paths, comic, pid, gen, ai)
                kept.append({"pid": pid, "image_path": gen["image_path"], "image_sha256": gen.get("image_sha256"), "attempt": ai, "needs_human": False}); done = True; break
            if gate["verdict"].get("invariant"): pending[pid] = pending.get(pid, []) + [gate["verdict"]["invariant"]]
        if throttled: break
        if not done:
            if last_gen:
                kept.append({"pid": pid, "image_path": last_gen["image_path"], "image_sha256": last_gen.get("image_sha256"), "attempt": total_by[pid], "needs_human": True}); flagged.append(pid)
                log(f"  ⚑ {pid} exhausted {args.max_total} attempts → best-so-far flagged for HUMAN, continuing")
            else:
                escalated = escalated or {"pid": pid, "why": "no panel ever generated (image_gen down?)"}; break

    asm = None
    drift_strikes, rewrite_storyboard = {}, []   # strike-escalation + KEEP≠final author-layer bounce-backs
    page_mode = "baked" if any((cfg_map.get(k["pid"]) or {}).get("text_mode") == "baked" for k in kept) else "html"
    if not escalated and len(kept) >= 2 and not args.skip_assembly:
        asm_round = 0
        while True:
            asm = run_assembly(paths, args.page, kept, cfg_map, page_mode, args)
            d = asm["verdict"].get("drift_panels", [])
            log(f"  assembly_gate {args.page} (round {asm_round}): {asm['verdict']['v']} — {asm['verdict']['reason']}" + (f" drift={d}" if d else ""))
            if asm["verdict"]["v"] == "accept": break
            if asm_round >= args.max_rollbacks: flagged.append(f"{args.page}:assembly"); break
            drifters = [p for p in d if any(k["pid"] == p for k in kept)]
            if not drifters: flagged.append(f"{args.page}:assembly"); break
            # STRIKE-ESCALATION: a panel that keeps drifting is a storyboard/blueprint problem → author-layer
            # rewrite, not more bakes. (Comic = independent panels; the escalation unit is the single panel.)
            for pid in drifters: drift_strikes[pid] = drift_strikes.get(pid, 0) + 1
            for pid in [p for p in drifters if drift_strikes[p] >= args.strike_escalate]:
                if pid not in rewrite_storyboard: rewrite_storyboard.append(pid)
                if pid not in flagged: flagged.append(pid)
                log(f"  ⚑ {pid} drifted {drift_strikes[pid]}× (≥{args.strike_escalate}) → ESCALATE to author layer (rewrite_storyboard_from {pid}); a re-bake can't fix a spec problem")
            rebakeable = [p for p in drifters if drift_strikes[p] < args.strike_escalate]
            if not rebakeable:
                log("  ⚑ all remaining drifters escalated to an author-layer rewrite → stop"); break
            log(f"  ⤺ cross-frame repair round {asm_round + 1}: re-bake {rebakeable} (point_of_divergence={asm['verdict'].get('point_of_divergence') or rebakeable[0]})")
            any_fixed = False
            for pid in rebakeable:
                if throttled: break
                if total_by.get(pid, 0) >= args.max_total + args.max_rollbacks:
                    if pid not in flagged: flagged.append(pid)
                    continue
                ai = total_by.get(pid, 0) + 1; total_by[pid] = ai
                inv = [f"CROSS-PANEL CONSISTENCY REPAIR: this panel drifted from page {args.page} — match the canonical duo identity AND the page's flat pixel-art style EXACTLY. Assembly: {asm['verdict']['reason']}"] + pending.get(pid, [])
                bakelog = f"{paths['PANELS']}/{pid}_a{ai}.bakelog.txt"
                gen = generate_panel(paths, pid, cfg_map[pid], ai, inv, args, bakelog)
                if gen.get("status") != "panel_ready" or gen.get("bytes", 0) <= args.min_bytes:
                    if is_throttle(gen, gen.get("gen_failed_reason", "")): throttled = True; escalated = {"pid": pid, "why": "throttled during cross-frame repair"}
                    continue
                gate = panel_gate(paths, pid, gen, cfg_map[pid], ai, args)
                write_wiki(paths, pid, gen, gate, ai)
                if gate["verdict"]["v"] == "keep":
                    idx = next((i for i, k in enumerate(kept) if k["pid"] == pid), -1)
                    if idx >= 0: kept[idx] = {"pid": pid, "image_path": gen["image_path"], "image_sha256": gen.get("image_sha256"), "attempt": ai, "needs_human": False}
                    update_comic_json(paths, comic, pid, gen, ai); any_fixed = True
            asm_round += 1
            if throttled or not any_fixed:
                if not throttled and not any_fixed: flagged.append(f"{args.page}:assembly")  # throttle breaks before human-flag (engine 461-462)
                break

    assembly_skipped = args.skip_assembly and len(kept) >= 2   # multi-panel page with assembly_gate skipped = UNCERTIFIED
    if assembly_skipped:
        flagged.append(f"{args.page}:assembly-skipped")
        log(f"  ⚑ assembly_gate SKIPPED on a {len(kept)}-panel page → cross-panel drift never checked; page NOT shippable (diagnostic run only)")
    any_needs_human = any(k["needs_human"] for k in kept) or len(flagged) > 0
    shippable = (not escalated) and (not throttled) and (not any_needs_human) and (not p0_skipped) and (asm["verdict"]["v"] == "accept" if asm else len(kept) >= 1)
    # STAGED ACCEPTANCE (KEEP≠final): panel_gate KEEP = panel_accepted; page_accepted only when assembly accepts (skipped ⇒ never).
    page_accepted = False if assembly_skipped else ((asm["verdict"]["v"] == "accept") if asm else len(kept) >= 1)
    for k in kept:
        k["acceptance_stage"] = "page_accepted" if (page_accepted and not k["needs_human"] and k["pid"] not in flagged) else "panel_accepted"

    if args.finalize and shippable and os.path.exists(paths["BUILD"]):
        log("finalize: building viewer")
        sh(["python3", paths["BUILD"], paths["PROJ"]], 120)

    report = {"page": args.page, "panel_ids": panel_ids, "kept": kept, "flagged_for_human": flagged,
              "needs_human": any_needs_human, "shippable": shippable, "assembly_skipped": assembly_skipped, "p0_skipped": p0_skipped, "throttled": throttled, "escalated": escalated,
              "assembly": (asm["verdict"] if asm else None), "rewrite_storyboard": rewrite_storyboard,
              "attempts_per_panel": total_by, "finalize": bool(args.finalize and shippable)}
    print("\n" + json.dumps(report, ensure_ascii=False, indent=2))
    if escalated or throttled: sys.exit(2)
    if any_needs_human: sys.exit(3)

if __name__ == "__main__":
    main()
