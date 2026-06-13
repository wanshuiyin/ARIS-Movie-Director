#!/usr/bin/env python3
"""run_spiral.py — one-command orchestrator for the method-figure spiral (stdlib + subprocess only).

The executing agent only authors blueprint.json; this runs the whole loop:
  validate → render condition(+png) → [ bake (codex image_gen, read-only) → pickup(verify) →
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
LOCK = "/tmp/aris_imagegen.lock"

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
    return f"""Use your IMAGE GENERATION tool to output ONE PNG. Image generation only — do NOT write or edit code/SVG/files; only generate one image.

Reference IMAGE 1 = the EXACT layout to reproduce ({os.path.basename(condition_png)}): every box already shows its title + one description line, arrows are labeled, three pale pastel phase panels on a WHITE background. Reproduce this layout faithfully.{ident}

STYLE: top ML-paper "Figure 1" — pure WHITE background, soft pastel phase panels, rounded white node cards, soft shadows, clean thin labeled arrows, crisp sans-serif (monospace for code/number tokens). Hand-designed, not a screenshot.

TEXT IS LOCKED — render every string below VERBATIM and crisp; do NOT rename, paraphrase, add, drop, garble, or insert spaces; do NOT invent any node/term/time-tag:
{locked_labels(bp)}
{fixblock}{keepblock}

Title top-left: "{tt.get('main','')}" / "{tt.get('sub','')}". Output the single finished figure, same wide aspect as IMAGE 1, white background."""

REVIEW_PROMPT = """Visual QA of a generated academic figure — look ONLY at the image: {png}
Do NOT assume what labels SHOULD say; transcribe what you ACTUALLY see, and hunt for what should NOT be there.
Return ONLY strict JSON (no prose) with these keys:
{{"verdict":"approve|retry","scores":{{"text_fidelity":0,"arrow_topology":0,"layout_readability":0,"character_identity":0,"style_fit":0}},
"observed_tokens":["...verbatim strings you can read..."],
"observed_edges":[{{"from_label":"","to_label":"","direction":"forward"}}],
"identity_audit":[{{"node":"","status":"MATCH|DRIFT","issue":""}}],
"anomalies":["floating/pasted-looking labels, artifacts, stray lines, duplicated characters, invented nodes"],
"blockers":["concrete image-gen-fixable instruction"],"nice_to_have":[],"positive_invariants":["what is right, keep it"]}}
Scores are 0-5. A vague "looks good" is rejected — you MUST list observed_tokens."""

def run_codex(prompt, images, effort, timeout, logf, image_gen=False):
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("blueprint"); ap.add_argument("--identity"); ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-rounds", type=int, default=0, help="0 = use blueprint render_policy.max_rounds")
    ap.add_argument("--effort", default="xhigh"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--bake-timeout", type=int, default=600); ap.add_argument("--review-timeout", type=int, default=300)
    a = ap.parse_args()
    bp = json.load(open(a.blueprint, encoding="utf-8"))
    fid = bp.get("figure_id", "figure"); cw = bp["canvas"]["width"]; ch = bp["canvas"]["height"]
    rounds = a.max_rounds or (bp.get("render_policy", {}).get("max_rounds", 4))
    minscore = (bp.get("acceptance", {}) or {}).get("min_core_score", 4)
    os.makedirs(a.out_dir, exist_ok=True)
    trace = os.path.join(a.out_dir, "trace.jsonl"); open(trace, "w").close()
    cond_svg = os.path.join(a.out_dir, "condition.svg"); cond_png = os.path.join(a.out_dir, "condition.png")

    log(f"validate {a.blueprint}")
    r = sh(["python3", os.path.join(HERE, "validate_blueprint.py"), a.blueprint], 60)
    print(r.stdout, r.stderr)
    if r.returncode != 0: sys.exit("blueprint invalid — fix it first")
    log("render condition")
    rc0 = sh(["python3", os.path.join(HERE, "render_condition.py"), a.blueprint, "--out", cond_svg, "--png", cond_png], 90)
    print(rc0.stdout, rc0.stderr)
    if rc0.returncode != 0 or (not a.dry_run and not os.path.exists(cond_png)):
        sys.exit("render_condition failed to produce condition.png (need headless Chrome to rasterize)")
    if a.dry_run:
        log("dry-run: printing the round-1 bake prompt then exiting")
        print("\n===== BAKE PROMPT (round 1) =====\n" + bake_prompt(bp, cond_png, a.identity, [], []))
        return

    invariants, last_fixes = [], []
    images = [cond_png] + ([a.identity] if a.identity else [])
    for rd in range(1, rounds + 1):
        log(f"=== round {rd}/{rounds} : BAKE ===")
        png = os.path.join(a.out_dir, f"round{rd}.png"); blog = os.path.join(a.out_dir, f"round{rd}.bakelog.txt")
        # the lock MUST cover marker → bake → pickup (the global generated-images dir is shared); never bake
        # unlocked, and only ever release a lock we actually acquired.
        acquired = False
        for _ in range(300):
            try: os.mkdir(LOCK); acquired = True; break
            except FileExistsError:
                if os.path.isdir(LOCK) and time.time() - os.path.getmtime(LOCK) > 900:
                    try: os.rmdir(LOCK)
                    except OSError: pass
                time.sleep(2)
        if not acquired:
            log("could not acquire image-gen lock (another bake running >20 min?) — escalate")
            open(trace, "a").write(json.dumps({"round": rd, "decision": "escalate", "reason": "image-gen lock timeout"}) + "\n")
            sys.exit(2)
        try:
            marker = time.time()
            run_codex(bake_prompt(bp, cond_png, a.identity, last_fixes, invariants), images, a.effort, a.bake_timeout, blog, image_gen=True)
            pk = sh(["python3", os.path.join(HERE, "pickup_image.py"), "--marker", str(marker), "--out", png,
                     "--log", blog, "--aspect", str(cw / ch)], 60)
        finally:
            if acquired:
                try: os.rmdir(LOCK)
                except OSError: pass
        if pk.returncode != 0:
            log(f"BAKE produced no valid native image (round {rd}) — escalate");
            open(trace, "a").write(json.dumps({"round": rd, "decision": "escalate", "reason": "no native image", "detail": pk.stderr.strip()}) + "\n")
            print("ESCALATE: image generation failed (throttle? non-native fallback?). See", blog); sys.exit(2)
        log(f"baked → {png} ({sha(png)})  : PANEL (Gemini + Codex)")
        rg = review_gemini(png, a.review_timeout); rc = review_codex(png, a.review_timeout)
        reviews = {}
        for name, rv in (("gemini", rg), ("codex", rc)):
            j = os.path.join(a.out_dir, f"round{rd}.{name}.json")
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
        panel_clean = (both_parsed and diff.get("content_accurate") and gv == "approve" and cv == "approve"
                       and core_ok and not codex_block and not g_anom)
        # consolidate BLOCKERS only; carry positive_invariants
        last_fixes = sorted(set((rg or {}).get("blockers", []) + codex_block +
                                [f"render the missing token exactly: {t}" for t in diff.get("missing_tokens", [])[:12]] +
                                [f"remove the anomaly: {x}" for x in diff.get("anomalies", [])[:8]]))
        invariants = sorted(set(invariants + (rg or {}).get("positive_invariants", []) + (rc or {}).get("positive_invariants", []))) [:12]
        rec = {"round": rd, "blueprint_sha": sha(a.blueprint), "condition_sha": sha(cond_png), "generated_sha": sha(png),
               "reviewers": {"gemini": gv, "codex": cv}, "core_scores_ok": core_ok,
               "hard_diff": {"missing_tokens": diff.get("missing_tokens", []), "anomalies": diff.get("anomalies", []),
                             "unaccounted_tokens": diff.get("unaccounted_tokens", [])},
               "fixes": last_fixes, "decision": "accept_candidate" if panel_clean else ("retry" if rd < rounds else "escalate")}
        open(trace, "a").write(json.dumps(rec, ensure_ascii=False) + "\n")
        log(f"round {rd}: gemini={gv} codex={cv} core_ok={core_ok} diff_clean={diff.get('content_accurate')} → {rec['decision']}")
        if panel_clean:
            shutil.copy(png, os.path.join(a.out_dir, "figure.png"))
            shutil.copy(a.blueprint, os.path.join(a.out_dir, "blueprint.json"))
            open(trace, "a").write(json.dumps({"final_approve": "panel_clean_awaiting_claude_structural",
                "image": "figure.png", "blueprint": "blueprint.json", "accepted_round": rd,
                "verdicts": {"gemini": gv, "codex": cv, "diff": "clean"}}, ensure_ascii=False) + "\n")
            log(f"PANEL-CLEAN at round {rd} → {a.out_dir}/figure.png")
            print(f"\n✅ PANEL-CLEAN (Gemini approve + Codex no-veto + deterministic diff empty) at round {rd}.")
            print(f"   figure: {a.out_dir}/figure.png   trace: {trace}")
            print("   NEXT: the calling agent (Claude) gives the final STRUCTURAL sign-off — the orchestrator")
            print("   does not self-acquit the generator family. Inspect the figure and approve or send one more fix.")
            return
    log("MAX_ROUNDS reached without panel-clean → escalate to human")
    print(f"\n⚠ ESCALATE: {rounds} rounds without convergence. Best-so-far + open blockers in {trace}.")
    sys.exit(3)

if __name__ == "__main__":
    main()
