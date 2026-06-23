#!/usr/bin/env python3
"""run_spiral.py — one-command orchestrator for the method-figure spiral (stdlib + subprocess only).

The executing agent only authors blueprint.json; this runs the whole loop:
  validate → render condition(+png) → [ bake (agent mcp__codex__codex sidecar seam) → pickup(verify) →
  panel: Gemini + Codex blind-transcribe → content_diff (deterministic) → decide ] × rounds → finalize + trace.

Automated panel = Gemini-3 (visual) + Codex-5.5 (arrow/diagnostic) + the deterministic content_diff (the
hard gate). Per the cross-model-acquittal rule the generator family (Codex) can't self-acquit, so a round
is "panel-clean" iff: content_diff clean AND Gemini verdict==approve AND Codex has no blocker. The CALLING
AGENT (Claude) gives the final STRUCTURAL sign-off on the converged figure — the orchestrator never claims
Claude's acquittal for it (it prints a clear "awaiting Claude structural approve" on success).

Long-running (each bake ~3-8 min × rounds) — run it in the background and watch run.log / trace.jsonl.
Usage:
  python3 run_spiral.py blueprint.json --identity identity_sheet.png --out-dir figures/method_figure/<id>
  [--max-rounds 4] [--effort high] [--dry-run]
"""
import argparse, hashlib, json, os, re, subprocess, sys, time, shutil

HERE = os.path.dirname(os.path.abspath(__file__))

# contract-v2 §0a: import the SHARED bake primitives from pickup_image.py (single source of truth — NEVER
# re-define them here; an inlined copy re-introduces cross-engine drift). pickup_image.py lives in HERE.
sys.path.insert(0, HERE)
from pickup_image import build_bake_prompt, emit_bake_request, await_bake_status, _status_path  # noqa: E402

def log(msg):
    print(f"[run_spiral {time.strftime('%H:%M:%S')}] {msg}", flush=True)

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

def extract_json(text, required_key=None):
    """pull the first balanced {...} object out of a CLI model's (prose/fence-wrapped) output. If
    required_key is given, skip fragments (e.g. a {"thought":...} preamble) that lack it — only return the
    real payload."""
    s = text.find("{")
    while s != -1:
        depth = 0
        for i in range(s, len(text)):
            if text[i] == "{": depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        j = json.loads(text[s:i + 1])
                        if required_key is None or (isinstance(j, dict) and required_key in j): return j
                    except Exception: pass
                    break
        s = text.find("{", s + 1)
    return None

# ---- blueprint → the locked-label re-assertion block (re-fed every round so the image model can't drift) ----
def locked_labels(bp):
    L = []
    for g in bp.get("groups", []): L.append(f'phase "{g.get("label_exact", g.get("label",""))}"')
    for n in bp.get("nodes", []):
        t = n.get("label_exact", n.get("label", "")); d = n.get("desc_exact", n.get("desc", ""))
        L.append(f'box "{t}"' + (f' — "{d}"' if d else ""))
    for e in bp.get("edges", []):
        el = e.get("label_exact", e.get("label", ""))
        if el: L.append(f'arrow {e["from"]}→{e["to"]} "{el}"')
    for c in bp.get("callouts", []):
        L.append(f'callout "{c.get("title_exact", c.get("title",""))}": ' + " / ".join(c.get("lines_exact", c.get("lines", []))))
    r = (bp.get("rail", {}) or {}).get("label_exact", "")
    if r: L.append(f'bottom rail "{r}"')
    return "\n".join("  - " + x for x in L)

def bake_prompt(bp, condition_png, identity_png, fixes, invariants):
    tt = bp.get("title", {}); ident = ""
    if identity_png:
        traits = "; ".join(t for a in bp.get("assets", []) for t in a.get("lock_traits", []))
        ident = (f"\nReference IMAGE 2 = the ONLY characters allowed ({traits}). Place them exactly where the "
                 f"condition marks a character; never invent robots/mascots; shrink a character before it covers any label.")
    fixblock = ("\nAPPLY THIS ROUND'S FIXES (from the cross-model panel):\n" + "\n".join("  - " + f for f in fixes)) if fixes else ""
    keepblock = ("\nKEEP (do not regress):\n" + "\n".join("  - " + i for i in invariants)) if invariants else ""
    forbidden = bp.get("forbidden_tokens", []) or []
    forbidblock = ("\nFORBIDDEN — NONE of these terms may appear ANYWHERE in the image (DELETE-list — a competing/wrong name):\n"
                   + "\n".join("  - " + str(t) for t in forbidden)) if forbidden else ""
    return f"""Use your IMAGE GENERATION tool to output ONE PNG. Image generation only — do NOT write or edit code/SVG/files; only generate one image.

Reference IMAGE 1 = the EXACT layout to reproduce ({os.path.basename(condition_png)}): every box already shows its title + one description line, arrows are labeled, three pale pastel phase panels on a WHITE background. Reproduce this layout faithfully.{ident}

STYLE: top ML-paper "Figure 1" — pure WHITE background, soft pastel phase panels, rounded white node cards, soft shadows, clean thin labeled arrows, crisp sans-serif (monospace for code/number tokens). Hand-designed, not a screenshot.

TEXT IS LOCKED — render every string below VERBATIM and crisp; do NOT rename, paraphrase, add, drop, garble, or insert spaces; do NOT invent any node/term/time-tag:
{locked_labels(bp)}{forbidblock}
{fixblock}{keepblock}

Title top-left: "{tt.get('main','')}" / "{tt.get('sub','')}". Output the single finished figure, same wide aspect as IMAGE 1, white background."""

REVIEW_PROMPT = """Visual QA of a generated academic figure — look ONLY at the image: {png}
Do NOT assume what labels SHOULD say; transcribe what you ACTUALLY see, and hunt for what should NOT be there.
Return ONLY strict JSON (no prose) with these keys:
{{"verdict":"approve|retry","scores":{{"text_fidelity":0,"arrow_topology":0,"layout_readability":0,"character_identity":0,"style_fit":0}},
"observed_tokens":["...verbatim strings you can read..."],
"observed_edges":[{{"from_label":"","to_label":"","direction":"forward"}}],
"identity_audit":[{{"node":"","status":"MATCH|DRIFT","issue":""}}],
"character_anatomy":[{{"char":"","hands_visible":2,"defect":"none|extra_hand|merged|wrong_count"}}],"anatomy_defect":false,
"anomalies":["floating/pasted-looking labels, artifacts, stray lines, duplicated characters, invented nodes"],
"blockers":["concrete image-gen-fixable instruction"],"nice_to_have":[],"positive_invariants":["what is right, keep it"]}}
Scores are 0-5. A vague "looks good" is rejected — you MUST list observed_tokens.
If the figure contains characters/mascots, do NOT eyeball it: ENUMERATE each character's visible hands one by one,
fill character_anatomy, and set anatomy_defect=true if ANY character has a wrong hand count (!=2), a third/floating/
duplicated/merged hand, or fused/extra fingers (character_anatomy=[] and anatomy_defect=false if there are no characters)."""

def run_codex(prompt, images, effort, timeout, logf):
    # R4: run_codex now serves ONLY the read-only VISION REVIEW (with -i image attach). The bake NEVER routes
    # through it — codex exec hand-draws a non-native fallback. No surviving path passes image_gen.
    cmd = ["codex", "exec", prompt]
    for im in images: cmd += ["-i", im]
    cmd += ["--sandbox", "read-only", "-c", f"model_reasoning_effort={effort}", "--skip-git-repo-check"]
    r = sh(cmd, timeout)
    if logf: open(logf, "w").write((r.stdout or "") + "\n---STDERR---\n" + (r.stderr or ""))
    return (r.stdout or "") + (r.stderr or "")

def review_gemini(png, timeout):
    p = REVIEW_PROMPT.format(png="the attached image")
    r = sh(["gemini", "--model", "auto-gemini-3", "-p", f"@{png} {p}"], timeout)
    return extract_json((r.stdout or "") + (r.stderr or ""), required_key="verdict")

def review_codex(png, timeout):
    # MUST attach the image with -i (a path in the prompt does NOT let Codex see the pixels).
    out = run_codex(REVIEW_PROMPT.format(png="the attached image"), [png], "xhigh", timeout, None)
    return extract_json(out, required_key="verdict")

def resolve_input(a):
    """Step-0 input sniffing — the single-input entry. A *brief* is auto-compiled into a blueprint (so the
    user feeds ONE ARIS-format artifact and never hand-writes a blueprint or hand-places coordinates); a
    *blueprint* is used as-is (legacy/power-user). Returns (blueprint_path, identity_path). Fail-closed on
    ambiguity. The identity sheet is resolved from the brief's identity_refs[0].path unless --identity
    overrides it (so the sheet stops being a second hand-managed argument)."""
    if a.from_brief and a.from_blueprint:
        sys.exit("[run_spiral] pass at most one of --from-brief / --from-blueprint")
    raw = json.load(open(a.blueprint, encoding="utf-8"))
    is_bp = raw.get("version") == "method-figure/blueprint/v1"
    is_brief_sv = raw.get("schema_version") == "method-figure/brief/v1"     # the AUTHORITATIVE brief signal
    is_brief_shape = ("components" in raw and "flows" in raw)               # legacy shape (no schema_version)
    is_brief = is_brief_sv or is_brief_shape
    if is_bp and is_brief and not (a.from_brief or a.from_blueprint):
        sys.exit("[run_spiral] input looks like BOTH a blueprint (has version) and a brief (has components+flows) "
                 "— pass --from-blueprint or --from-brief to disambiguate (fail-closed, no guessing).")
    if a.from_blueprint or (is_bp and not a.from_brief):
        return a.blueprint, a.identity
    # auto-detect a brief ONLY via schema_version; a components+flows JSON with NO schema_version must be opted in
    # explicitly (--from-brief), so a random non-method-figure JSON can't be silently compiled + baked.
    if is_brief_shape and not is_brief_sv and not is_bp and not a.from_brief:
        sys.exit("[run_spiral] input has components+flows but no `schema_version: method-figure/brief/v1` — "
                 "pass --from-brief to compile it as a brief (fail-closed; refusing to guess).")
    if a.from_brief or (is_brief_sv and not is_bp):
        sys.path.insert(0, HERE)
        import compile_brief as cb
        blueprint, trace, errors = cb.compile_brief(raw, strict=True)
        if errors:
            print("[run_spiral] Step-0 traceability errors:", file=sys.stderr)
            for e in errors:
                print("  -", e, file=sys.stderr)
            sys.exit("[run_spiral] Step-0 REFUSED: the brief is not fully traceable (a missing "
                     "number/claim/trait/component is an escalation, not creative license) — fix the brief.")
        os.makedirs(a.out_dir, exist_ok=True)
        bp_path = os.path.join(a.out_dir, "blueprint.json")
        tr_path = os.path.join(a.out_dir, "traceability.json")
        with open(bp_path, "w", encoding="utf-8") as f:
            json.dump(blueprint, f, indent=2, ensure_ascii=False)
        with open(tr_path, "w", encoding="utf-8") as f:
            json.dump(trace, f, indent=2, ensure_ascii=False)
        log(f"Step-0: compiled brief → {bp_path} ({len(blueprint['nodes'])} nodes) + traceability.json")
        identity = a.identity
        if not identity:
            refs = raw.get("identity_refs") or []
            if refs and refs[0].get("path"):
                p = refs[0]["path"]
                if not os.path.isabs(p):
                    p = os.path.join(os.path.dirname(os.path.abspath(a.blueprint)), p)
                if os.path.exists(p):
                    identity = p
                    log(f"Step-0: resolved identity sheet from brief.identity_refs[0] → {refs[0]['path']}")
                else:
                    log(f"Step-0: brief identity_refs[0].path '{refs[0]['path']}' not found beside the brief "
                        f"— bake will run without an identity ref (pass --identity to supply one)")
        return bp_path, identity
    sys.exit("[run_spiral] cannot tell if the input is a brief or a blueprint "
             "(no version, no components+flows) — pass --from-brief or --from-blueprint.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("blueprint"); ap.add_argument("--identity"); ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-rounds", type=int, default=0, help="0 = use blueprint render_policy.max_rounds")
    ap.add_argument("--effort", default="xhigh"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--bake-timeout", type=int, default=600); ap.add_argument("--review-timeout", type=int, default=300)
    ap.add_argument("--from-brief", action="store_true", help="force: treat the input as a method_figure_brief (Step-0 compile)")
    ap.add_argument("--from-blueprint", action="store_true", help="force: treat the input as a ready blueprint (legacy/power-user)")
    ap.add_argument("--p0-only", action="store_true", help="run validate + render the condition (the zero-credit P0 gate), then stop")
    ap.add_argument("--bake-mode", choices=["agent", "exec"], default="agent",
                    help="agent = real bake via the mcp__codex__codex sidecar seam (default); exec = legacy/CI non-image path that RAISES if it reaches a real bake (codex exec hand-draws a non-native fallback)")
    a = ap.parse_args()
    a.blueprint, a.identity = resolve_input(a)   # Step-0: sniff brief vs blueprint; auto-compile a brief
    # ABSOLUTE-REF INVARIANT (mirror run_comic.py): the identity sheet must be an absolute, on-disk path before
    # it is embedded (as a literal) in the bake prompt — a relative/missing ref would silently desync the agent's
    # write target from our pickup probe. Absolutize, then existence-check fail-closed.
    if a.identity:
        a.identity = os.path.abspath(a.identity)
    if a.identity and not os.path.exists(a.identity):
        print(f"[run_spiral] identity sheet not found: {a.identity}", file=sys.stderr); sys.exit(2)
    bp = json.load(open(a.blueprint, encoding="utf-8"))
    fid = bp.get("figure_id", "figure"); cw = bp["canvas"]["width"]; ch = bp["canvas"]["height"]
    rounds = a.max_rounds or (bp.get("render_policy", {}).get("max_rounds", 4))
    minscore = (bp.get("acceptance", {}) or {}).get("min_core_score", 4)
    # RELATIVE-PATH FIX (mirror run_comic.py's abspath(project)): resolve out_dir to a TRUE absolute path ONCE,
    # and derive EVERY downstream path (trace/cond_svg/cond_png + the per-round png/blog + the finalize copies)
    # from it. build_bake_prompt + emit_bake_request emit refs/out_path under the literal "(absolute path)" label,
    # so the embedded ref/out paths, the agent's write target, and our own pickup probe (--out png) must all be
    # the SAME absolute files — a relative out_dir would silently desync them against the agent's cwd.
    out_dir = os.path.abspath(a.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    trace = os.path.join(out_dir, "trace.jsonl"); open(trace, "w").close()
    cond_svg = os.path.join(out_dir, "condition.svg"); cond_png = os.path.join(out_dir, "condition.png")

    log(f"validate {a.blueprint}")
    r = sh(["python3", os.path.join(HERE, "validate_blueprint.py"), a.blueprint], 60)
    print(r.stdout, r.stderr)
    if r.returncode != 0: sys.exit("blueprint invalid — fix it first")
    log("render condition")
    rc0 = sh(["python3", os.path.join(HERE, "render_condition.py"), a.blueprint, "--out", cond_svg, "--png", cond_png], 90)
    print(rc0.stdout, rc0.stderr)
    if rc0.returncode != 0 or (not a.dry_run and not os.path.exists(cond_png)):
        sys.exit("render_condition failed to produce condition.png (need headless Chrome to rasterize)")
    if a.p0_only:
        # zero-credit P0 gate: brief→blueprint validated + condition rendered (above) AND the would-be bake
        # prompt LINTED — background white, identity sheet resolved (if the blueprint declares one), every
        # forbidden token carried into the DELETE-list, locked labels present. A blocker here costs ZERO credits.
        prompt0 = bake_prompt(bp, cond_png, a.identity, [], [])
        p0 = []
        if str((bp.get("canvas") or {}).get("background", "#FFFFFF")).upper() not in ("#FFFFFF", "#FFF", "WHITE"):
            p0.append(f"canvas background is not white: {(bp.get('canvas') or {}).get('background')}")
        if bp.get("assets") and not a.identity:
            p0.append("blueprint declares an identity asset but no identity sheet resolved (--identity / brief.identity_refs[].path)")
        for t in (bp.get("forbidden_tokens") or []):
            if str(t) not in prompt0:
                p0.append(f"forbidden token '{t}' not carried into the bake prompt's DELETE-list")
        if "TEXT IS LOCKED" not in prompt0 or not locked_labels(bp).strip():
            p0.append("bake prompt carries no locked labels")
        log("p0-only: zero-credit gate (validate + compile + render + bake-prompt lint)")
        if p0:
            for b in p0: print("   ✗ P0 blocker:", b)
            sys.exit("[run_spiral] P0 gate FAILED — fix the blockers above before spending any image credit.")
        print(f"   ✓ P0 clean — condition: {cond_svg}; identity={'resolved' if a.identity else 'none'}; "
              f"{len([x for x in locked_labels(bp).splitlines() if x.strip()])} locked labels + "
              f"{len(bp.get('forbidden_tokens') or [])} forbidden tokens carried into the prompt")
        return
    if a.dry_run:
        log("dry-run: printing the round-1 bake prompt then exiting")
        print("\n===== BAKE PROMPT (round 1) =====\n" + bake_prompt(bp, cond_png, a.identity, [], []))
        return

    # FAIL-CLOSED: a blueprint that declares identity asset(s) must NOT bake without its identity sheet — otherwise
    # the character figure bakes unconstrained. (--p0-only enforces the same check; enforce it on the real bake too.)
    if bp.get("assets") and not a.identity:
        sys.exit("[run_spiral] blueprint declares identity asset(s) but no identity sheet resolved "
                 "(--identity / brief.identity_refs[].path) — refusing to bake a character figure without its identity ref.")

    invariants, last_fixes = [], []
    images = [cond_png] + ([a.identity] if a.identity else [])
    for rd in range(1, rounds + 1):
        log(f"=== round {rd}/{rounds} : BAKE ===")
        png = os.path.join(out_dir, f"round{rd}.png"); blog = os.path.join(out_dir, f"round{rd}.bakelog.txt")
        # R4: the exec path NEVER bakes (codex exec hand-draws a non-native fallback) — it RAISES. R3: in agent
        # mode the core does NOT hold /tmp/aris_imagegen.lock (the agent wrapper is the sole serializer; the
        # foreground core blocking on the agent that must service the sidecar would deadlock).
        if a.bake_mode != "agent":
            raise RuntimeError("exec bake retired — it hand-draws a non-native fallback; use --bake-mode=agent")
        # BAKE via the AGENT (mcp__codex__codex) over the sidecar seam: refs+out_path embedded as ABSOLUTE PATHS
        # inside prompt_text (the MCP schema has no -i); sandbox=workspace-write; model_reasoning_effort=xhigh via
        # config{}. The agent writes <png>.bakestatus.json carrying status + raw mcp_output (for the HARD-VETO).
        created_at = time.time()
        prompt_text = build_bake_prompt(bake_prompt(bp, cond_png, a.identity, last_fixes, invariants),
                                        cond_png, a.identity or "", png)
        # B-NONCE: capture the per-bake request_id RETURNED by emit_bake_request. The shared pickup_image.py
        # (single source of truth, contract-v2 §0a) mints a uuid4 nonce, stamps it into the bakereq.json payload,
        # and returns it; we forward it via --request-id so pickup fail-closes if the bakestatus carries a
        # mismatched id (a stale/foreign bake at <png>.bakestatus.json can't be silently honored). The id never
        # needs pre-seeding into the dict here — emit owns minting it. Fallback to created_at if a future/legacy
        # emit ever returns None (mirrors run_comic.py's guard) so request_id is always a usable string.
        request_id = emit_bake_request(png, {"prompt_text": prompt_text, "out_path": png, "content_png": cond_png,
                                "identity_ref": a.identity or "", "model": "gpt-5.5",
                                "config": {"model_reasoning_effort": "xhigh", "include_image_gen_tool": True},
                                "sandbox": "workspace-write",
                                # the agent's cwd is a STABLE ABSOLUTE repo root (mirrors run_comic.py's cwd=paths["PROJ"]),
                                # NOT the parent of out_dir — every ref/out_path is already an absolute path in prompt_text,
                                # so the bake resolves the same files regardless of cwd, and the cwd never drifts per-run.
                                "cwd": HERE.rsplit("/skills/", 1)[0],
                                "created_at": created_at, "min_bytes": 500000, "aspect": cw / ch})
        if not request_id: request_id = str(created_at)   # defensive: emit always returns a uuid today; keep a usable id
        status = await_bake_status(png, a.bake_timeout)   # polls <png>.bakestatus.json; {} on timeout
        if not isinstance(status, dict): status = {}   # await guard: a non-dict return (foreign/future) → treat as timeout
        # FAIL-CLOSED: ONLY status=="ok" may proceed to verify (an empty/timeout/non-ok status must NOT fall
        # through to pickup — a stale/foreign PNG at png could otherwise be accepted). A timeout is "other", NOT
        # "throttle" (only an explicit wrapper failure_kind=="throttle" is a throttle — consistent with run_comic.py).
        if status.get("status") != "ok":
            kind = "throttle" if status.get("failure_kind") == "throttle" else "other"
            why = "agent bake timed out (no <png>.bakestatus.json — is the agent wrapper running?)" if not status \
                  else f"agent bake not ok [{kind}]: {str(status.get('mcp_error') or status.get('status'))[:300]}"
            log(f"BAKE not ok [{kind}] (round {rd}) — escalate")
            open(trace, "a").write(json.dumps({"round": rd, "decision": "escalate", "reason": "agent bake not ok", "failure_kind": kind, "detail": why}) + "\n")
            print("ESCALATE: image generation failed (throttle? non-native fallback?). See", _status_path(png)); sys.exit(2)
        # HARD-VETO ENFORCEMENT (status==ok): the HARD-VETO scans status.mcp_output (where a hand-draw leaves
        # struct/zlib/PIL/SVG/matplotlib traces). An ok status carrying an EMPTY/missing mcp_output would make the
        # veto INERT — a code-drawn fallback could then sail through pickup. Fail-closed exactly like a failed bake
        # (same escalate trace + sys.exit(2)), classified "other", BEFORE we ever probe the PNG.
        m = status.get("mcp_output")
        if not isinstance(m, str) or not m.strip():
            # isinstance (not `(... or "").strip()`): blocks null/empty AND a non-string mcp_output that would
            # otherwise CRASH .strip() — fail-closed exactly like a failed bake (same escalate trace + sys.exit(2)).
            why = "agent status ok but mcp_output missing/empty/non-string — HARD-VETO inert, fail-closed"
            log(f"BAKE ok but EMPTY/non-string mcp_output (round {rd}) — HARD-VETO inert, escalate")
            open(trace, "a").write(json.dumps({"round": rd, "decision": "escalate", "reason": "agent status ok but mcp_output missing/empty/non-string — HARD-VETO inert, fail-closed", "failure_kind": "other", "detail": why}) + "\n")
            print("ESCALATE: image generation failed (throttle? non-native fallback?). See", _status_path(png)); sys.exit(2)
        pk = sh(["python3", os.path.join(HERE, "pickup_image.py"), "--out-existing", "--out", png,
                 "--min-bytes", "500000", "--aspect", str(cw / ch), "--created-at", str(created_at),
                 "--request-id", request_id, "--transcript", _status_path(png)], 60)
        if pk.returncode != 0:
            log(f"BAKE produced no valid native image (round {rd}) — escalate");
            open(trace, "a").write(json.dumps({"round": rd, "decision": "escalate", "reason": "no native image", "detail": pk.stderr.strip()}) + "\n")
            print("ESCALATE: image generation failed (throttle? non-native fallback?). See", _status_path(png)); sys.exit(2)
        log(f"baked → {png} ({sha(png)})  : PANEL (Gemini + Codex)")
        rg = review_gemini(png, a.review_timeout); rc = review_codex(png, a.review_timeout)
        reviews = {}
        for name, rv in (("gemini", rg), ("codex", rc)):
            j = os.path.join(out_dir, f"round{rd}.{name}.json")
            json.dump(rv or {"verdict": "retry", "parse_error": True, "observed_tokens": []}, open(j, "w"), ensure_ascii=False, indent=1)
            reviews[name] = j
        df = sh(["python3", os.path.join(HERE, "content_diff.py"), a.blueprint, reviews["gemini"], reviews["codex"]], 60)
        diff = extract_json(df.stdout) or {"content_accurate": False, "missing_tokens": ["<diff failed>"], "anomalies": [], "unaccounted_tokens": []}
        # decide — fail-closed: BOTH reviewers must have returned parseable JSON with observed_tokens, both
        # must approve, the deterministic diff must be clean, core scores (incl. identity if a sheet was given)
        # >= threshold, and neither anomalies nor codex blockers present.
        gv = (rg or {}).get("verdict", "retry"); cv = (rc or {}).get("verdict", "retry")
        both_parsed = isinstance((rg or {}).get("observed_tokens"), list) and isinstance((rc or {}).get("observed_tokens"), list)
        gscores = (rg or {}).get("scores", {})
        core_keys = ["text_fidelity", "arrow_topology", "layout_readability", "style_fit"] + (["character_identity"] if a.identity else [])
        core_ok = bool(gscores) and all(gscores.get(k, 0) >= minscore for k in core_keys)
        codex_block = (rc or {}).get("blockers", []); g_anom = (rg or {}).get("anomalies", [])
        anatomy_defect = (rg or {}).get("anatomy_defect") is True or (rc or {}).get("anatomy_defect") is True  # single-reviewer veto (figures w/ characters)
        panel_clean = (both_parsed and diff.get("content_accurate") and gv == "approve" and cv == "approve"
                       and core_ok and not codex_block and not g_anom and not anatomy_defect)
        # consolidate BLOCKERS only; carry positive_invariants
        anatomy_chars = [c for r in (rg, rc) for c in (r or {}).get("character_anatomy", []) if isinstance(c, dict) and c.get("defect") not in (None, "none")]
        last_fixes = sorted(set((rg or {}).get("blockers", []) + codex_block +
                                [f"render the missing token exactly: {t}" for t in diff.get("missing_tokens", [])[:12]] +
                                [f"remove the anomaly: {x}" for x in diff.get("anomalies", [])[:8]] +
                                [f"DELETE the forbidden term (must not appear anywhere): {t}" for t in diff.get("forbidden_present", [])[:8]] +
                                [f"REMOVE the unsourced number (not authored in the brief): {t}" for t in diff.get("unaccounted_numeric", [])[:8]] +
                                [f"fix the arrow direction — {t}" for t in diff.get("wrong_edges", [])[:8]] +
                                ([f"fix anatomy: give {c.get('char','a character')} exactly two hands ({c.get('defect')})" for c in anatomy_chars[:4]] if anatomy_defect else [])))
        invariants = sorted(set(invariants + (rg or {}).get("positive_invariants", []) + (rc or {}).get("positive_invariants", []))) [:12]
        rec = {"round": rd, "blueprint_sha": sha(a.blueprint), "condition_sha": sha(cond_png), "generated_sha": sha(png),
               "reviewers": {"gemini": gv, "codex": cv}, "core_scores_ok": core_ok,
               "hard_diff": {"missing_tokens": diff.get("missing_tokens", []), "anomalies": diff.get("anomalies", []),
                             "unaccounted_tokens": diff.get("unaccounted_tokens", []),
                             "unaccounted_numeric": diff.get("unaccounted_numeric", []),
                             "forbidden_present": diff.get("forbidden_present", []), "wrong_edges": diff.get("wrong_edges", [])},
               "fixes": last_fixes, "decision": "accept_candidate" if panel_clean else ("retry" if rd < rounds else "escalate")}
        open(trace, "a").write(json.dumps(rec, ensure_ascii=False) + "\n")
        log(f"round {rd}: gemini={gv} codex={cv} core_ok={core_ok} diff_clean={diff.get('content_accurate')} anatomy_ok={not anatomy_defect} → {rec['decision']}")
        if panel_clean:
            shutil.copy(png, os.path.join(out_dir, "figure.png"))
            bp_dst = os.path.join(out_dir, "blueprint.json")
            # skip the copy when src and dst are the SAME file (Step-0 already wrote it there) — samefile() also
            # catches a symlink/hardlink that abspath string-compare would miss (avoids a shutil SameFileError).
            same = os.path.exists(bp_dst) and os.path.samefile(a.blueprint, bp_dst)
            if not same:
                shutil.copy(a.blueprint, bp_dst)
            open(trace, "a").write(json.dumps({"final_approve": "panel_clean_awaiting_claude_structural",
                "image": "figure.png", "blueprint": "blueprint.json", "accepted_round": rd,
                "verdicts": {"gemini": gv, "codex": cv, "diff": "clean"}}, ensure_ascii=False) + "\n")
            log(f"PANEL-CLEAN at round {rd} → {out_dir}/figure.png")
            print(f"\n✅ PANEL-CLEAN (Gemini approve + Codex no-veto + deterministic diff empty) at round {rd}.")
            print(f"   figure: {out_dir}/figure.png   trace: {trace}")
            print("   NEXT: the calling agent (Claude) gives the final STRUCTURAL sign-off — the orchestrator")
            print("   does not self-acquit the generator family. Inspect the figure and approve or send one more fix.")
            return
    log("MAX_ROUNDS reached without panel-clean → escalate to human")
    print(f"\n⚠ ESCALATE: {rounds} rounds without convergence. Best-so-far + open blockers in {trace}.")
    sys.exit(3)

if __name__ == "__main__":
    main()
