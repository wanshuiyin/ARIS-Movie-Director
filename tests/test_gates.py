#!/usr/bin/env python3
"""Deterministic gate regression tests — pure stdlib; NO image_gen / Chrome / network / credentials.

These lock the cross-model-audited gate guarantees so a future edit can't silently re-open a fail-open hole:
  - content_diff.py hard vetoes (hallucinated number / forbidden token / reversed edge) + clean pass
  - compile_brief.py --strict fail-closed on a bad enum
  - validate_wiki.py --strict-author-gates flags a bare-locked author node (and default still passes)
  - pickup_image.py --out-existing fails-closed when the HARD-VETO transcript is whitespace-only OR omitted
    (a fresh valid >500KB PNG must NOT slip through merely by withholding a transcript — veto can't be made inert)
  - pickup_image.py mcp_output fail-closed AT THE PICKUP LEVEL: an `ok` status whose `mcp_output` is null / "" /
    non-string makes the veto inert → must fail even with a valid >500KB PNG; a valid non-empty string passes.
    Plus in-process parity: verify_existing_png(valid_png, transcript=None)["ok"] is False (function-level fail-closed)
  - VETO_PATS parity: spiral_engine.js VETO_PATS ≡ pickup_image.py _VETO_PATS (same length + order, string-by-string)
  - SIZE-BOUNDARY parity: spiral_engine.js verifyExistingPng applies the SAME floor as pickup_image.py — a PNG of EXACTLY
    min_bytes is REJECTED (ok:false), min_bytes+1 ACCEPTED (ok:true) — so the size comparator is parity-locked, not just VETO_PATS
  - the comic literal-diff exactness contract (a wrong timestamp must NOT satisfy the expected one)
  - p0_proof DIGEST BINDING (N3/N4): run_comic's spending preflight accepts ONLY a cert whose payload binds
    comic_sha == sha256(comic.json BYTES) AND bake_plan_sha == bake_plan_digest(get_bake_plan()) — a digest-less
    (old-shape) cert and a stale cert (comic.json modified after mint) both fail-closed; run_p0_proof.py mints
    e2e ONLY on a both-families {openai,google} same-digest quorum (one family / wrong comic_sha -> exit 1)
  - run_spiral.extract_json uses a real decoder (raw_decode): braces INSIDE string values (observed_tokens)
    can't truncate the payload — parity with run_comic.extract_json (N11)
  - run_comic --page must NAME an existing comic.json page (a valid-charset ghost id exits !=0, --dry-run
    included); _p0_clean requires the cert's reviewer_quorum to carry BOTH {openai,google} — correct digests
    alone never clear the gate; run_p0_proof refuses a quorum-family --author-family (openai -> exit 1,
    self-acquittal) and --min-bytes N binds bake_plan_sha to the consumer's --min-bytes N plan digest
    (≠ the default-plan digest)

Run locally:  python3 tests/test_gates.py    (exit 0 = all pass).  Also invoked by tests/smoke.sh + CI.
"""
import json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MF = os.path.join(ROOT, "skills", "method-figure")
PY = sys.executable
fails = []


def check(name, cond):
    print(("  ok   " if cond else "  FAIL ") + name)
    if not cond:
        fails.append(name)


# ── 1. content_diff.py vetoes (built from the freshly-compiled example blueprint) ──
with tempfile.TemporaryDirectory() as td:
    bp = os.path.join(td, "blueprint.json")
    rc = subprocess.run([PY, os.path.join(MF, "scripts", "compile_brief.py"),
                         os.path.join(MF, "examples", "method_figure", "method_figure_brief.json"),
                         "--out", bp, "--trace", os.path.join(td, "tr.json")],
                        capture_output=True, text=True)
    check("compile_brief: example brief compiles clean", rc.returncode == 0)

    B = json.load(open(bp, encoding="utf-8"))
    exp = []
    for n in B.get("nodes", []):
        exp += [n.get("label_exact", ""), n.get("desc_exact", "")] + n.get("expected_tokens", [])
    for g in B.get("groups", []):
        exp.append(g.get("label_exact", ""))
    for e in B.get("edges", []):
        exp.append(e.get("label_exact", ""))
    for c in B.get("callouts", []):
        exp.append(c.get("title_exact", "")); exp += c.get("lines_exact", [])
    exp.append((B.get("rail") or {}).get("label_exact", ""))
    id2l = {n["id"]: n.get("label_exact", "") for n in B["nodes"]}
    edges = [{"from_label": id2l.get(e["from"]), "to_label": id2l.get(e["to"]), "direction": "forward"}
             for e in B["edges"] if id2l.get(e.get("from")) and id2l.get(e.get("to"))]

    def review(extra=None, edges_override=None):
        return {"verdict": "approve", "observed_tokens": [s for s in exp if s] + (extra or []),
                "observed_edges": edges if edges_override is None else edges_override, "anomalies": []}

    def run_cd(r1, r2):
        a, b = os.path.join(td, "a.json"), os.path.join(td, "b.json")
        json.dump(r1, open(a, "w")); json.dump(r2, open(b, "w"))
        return subprocess.run([PY, os.path.join(MF, "scripts", "content_diff.py"), bp, a, b],
                              capture_output=True, text=True).returncode

    check("content_diff: clean transcription → accept (exit 0)", run_cd(review(), review()) == 0)
    fb = (B.get("forbidden_tokens") or ["self-judge"])[0]
    check("content_diff: forbidden token → veto", run_cd(review([fb]), review([fb])) != 0)
    check("content_diff: hallucinated number (+9.9) → veto", run_cd(review(["+9.9"]), review(["+9.9"])) != 0)
    rev = [dict(e) for e in edges]
    if rev:
        rev[0] = {"from_label": edges[0]["to_label"], "to_label": edges[0]["from_label"], "direction": "forward"}
    check("content_diff: reversed edge → veto", run_cd(review(edges_override=rev), review(edges_override=rev)) != 0)

# ── 2. compile_brief --strict fail-closed on a bad enum ──
with tempfile.TemporaryDirectory() as td:
    b = json.load(open(os.path.join(MF, "examples", "method_figure", "method_figure_brief.json"), encoding="utf-8"))
    b["flows"][0]["kind"] = "bogus_kind"
    bad = os.path.join(td, "bad.json"); json.dump(b, open(bad, "w"))
    rc = subprocess.run([PY, os.path.join(MF, "scripts", "compile_brief.py"), bad, "--out", os.path.join(td, "x.json")],
                        capture_output=True, text=True)
    check("compile_brief: invalid flow.kind → fail-closed", rc.returncode != 0)

# ── 3. validate_wiki --strict-author-gates ──
vw = os.path.join(ROOT, "cli", "validate_wiki.py")
fix = os.path.join(ROOT, "examples", "comic_min_author")
check("validate_wiki --strict-author-gates: flags un-gated locks",
      subprocess.run([PY, vw, fix, "--strict-author-gates"], capture_output=True, text=True).returncode != 0)
check("validate_wiki: fixture passes by default",
      subprocess.run([PY, vw, fix], capture_output=True, text=True).returncode == 0)

# ── 3b. pickup_image.py HARD-VETO (--out-existing): a clean-sig >500KB PNG must STILL fail if the transcript shows a fallback ──
import struct as _struct, zlib as _zlib, binascii as _binascii
PICKUP = os.path.join(MF, "scripts", "pickup_image.py")
def _real_png(path, w=1280, h=720):
    # a structurally-valid PNG whose IDAT is INCOMPRESSIBLE (os.urandom) so the real file exceeds 500KB —
    # this proves the size gate can't bypass the veto (highly-repetitive raw would shrink to ~3.7KB and fail).
    def _chunk(typ, data):
        return _struct.pack(">I", len(data)) + typ + data + _struct.pack(">I", _binascii.crc32(typ + data) & 0xffffffff)
    ihdr = _struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + os.urandom(3 * w) for _ in range(h))   # incompressible -> >500KB after deflate
    idat = _zlib.compress(raw, 6)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", idat) + _chunk(b"IEND", b""))
with tempfile.TemporaryDirectory() as td:
    out = os.path.join(td, "S01_panel_a01.png"); _real_png(out)
    assert os.path.getsize(out) > 500000, "test PNG must exceed min_bytes to prove the size gate can't bypass the veto"
    bad_tx = os.path.join(td, "bad.bakestatus.json")
    open(bad_tx, "w").write('{"status":"ok"}\nimport struct\nzlib.compress(raw, 9)\ndef main():\n')
    r = subprocess.run([PY, PICKUP, "--out-existing", "--out", out, "--min-bytes", "500000",
                        "--transcript", bad_tx], capture_output=True, text=True)
    check("pickup --out-existing: clean-sig >500KB PNG + struct/zlib transcript -> HARD-VETO fail", r.returncode != 0)
    check("pickup HARD-VETO: stderr names a fallback marker (not an argparse/no-candidate error)",
          ("fallback" in (r.stderr or "").lower()) and ("struct" in (r.stderr or "").lower() or "zlib" in (r.stderr or "").lower()))
    ok_tx = os.path.join(td, "ok.bakestatus.json")
    open(ok_tx, "w").write('{"status":"ok"}\nrebuilt the structural reconstruction layout\n')   # 'structural'/'reconstruct' must NOT veto
    r2 = subprocess.run([PY, PICKUP, "--out-existing", "--out", out, "--min-bytes", "500000",
                         "--transcript", ok_tx], capture_output=True, text=True)
    check("pickup HARD-VETO: code-context regex does NOT false-veto 'structural'/'reconstruct'", r2.returncode == 0)
    # A) FROM-IMPORT veto: the hand-draw fallback can dodge `import struct`/`import zlib` by writing them as
    # `from struct import pack` / `from zlib import compress`. A valid >500KB PNG + such a transcript MUST still
    # HARD-VETO (the from-import markers are the last two _VETO_PATS / VETO_PATS entries in BOTH engines).
    fi_tx = os.path.join(td, "fromimport.bakestatus.json")
    open(fi_tx, "w").write('{"status":"ok","mcp_output":"from struct import pack\\nfrom zlib import compress\\nrebuilt the png by hand\\n"}')
    rfi = subprocess.run([PY, PICKUP, "--out-existing", "--out", out, "--min-bytes", "500000",
                          "--transcript", fi_tx], capture_output=True, text=True)
    check("pickup HARD-VETO: 'from struct import pack' + 'from zlib import compress' transcript + valid >500KB PNG -> fail",
          rfi.returncode != 0 and "fallback" in (rfi.stderr or "").lower()
          and ("from" in (rfi.stderr or "").lower() and ("struct" in (rfi.stderr or "").lower() or "zlib" in (rfi.stderr or "").lower())))

# ── 3c. pickup --out-existing must FAIL-CLOSED when the transcript can't carry the HARD-VETO ──
# A fresh, valid, >500KB PNG must NOT be accepted if the transcript the veto scans is whitespace-only or omitted —
# otherwise the HARD-VETO is INERT (a code-drawn fallback PNG with a clean sig/dims/size would sail through merely
# by withholding a transcript). This locks the "empty/missing transcript -> fail-closed" guard in pickup_image.main().
with tempfile.TemporaryDirectory() as td:
    out = os.path.join(td, "S01_panel_a01.png"); _real_png(out)   # reuse the >500KB incompressible-PNG helper
    assert os.path.getsize(out) > 500000, "test PNG must exceed min_bytes to prove the fresh PNG itself is acceptable"
    # (i) WHITESPACE-ONLY transcript -> veto inert -> must fail-closed even though the PNG is valid+big
    ws_tx = os.path.join(td, "ws.bakestatus.json"); open(ws_tx, "w").write("   \n\t  \n   ")
    rw = subprocess.run([PY, PICKUP, "--out-existing", "--out", out, "--min-bytes", "500000",
                         "--transcript", ws_tx], capture_output=True, text=True)
    check("pickup --out-existing: whitespace-only transcript + valid >500KB PNG -> fail-closed (veto not inert)",
          rw.returncode != 0 and "transcript" in (rw.stderr or "").lower())
    # (ii) --transcript OMITTED entirely -> no transcript to scan -> must fail-closed even though the PNG is valid+big
    ro = subprocess.run([PY, PICKUP, "--out-existing", "--out", out, "--min-bytes", "500000"],
                        capture_output=True, text=True)
    check("pickup --out-existing: NO --transcript + valid >500KB PNG -> fail-closed (HARD-VETO can't be made inert)",
          ro.returncode != 0 and "transcript" in (ro.stderr or "").lower())

# ── 3c-mcp. LOCK the `mcp_output` fail-closed contract AT THE PICKUP LEVEL ──
# The agent status file is valid JSON whose `mcp_output` field carries the raw codex bake output the HARD-VETO scans.
# An `ok` status with mcp_output null / "" / non-string makes the veto INERT — a code-drawn fallback PNG with a clean
# sig/dims/size could then sail through. The orchestrators (run_spiral.py / run_comic.py) already fail-closed on
# `not isinstance(m, str) or not m.strip()` BEFORE pickup; this locks the SAME guarantee redundantly at the pickup
# verifier itself (defense-in-depth: pickup must not be bypassable even when invoked directly, not via an engine).
# A fresh VALID >500KB PNG (reusing _real_png) is supplied in every case so a pass/fail can ONLY come from mcp_output.
with tempfile.TemporaryDirectory() as td:
    out = os.path.join(td, "S01_panel_a01.png"); _real_png(out)   # reuse the >500KB incompressible-PNG helper
    assert os.path.getsize(out) > 500000, "test PNG must exceed min_bytes so the verdict turns ONLY on mcp_output"

    def _pick_mcp(tx_body):
        tx = os.path.join(td, "mcp.bakestatus.json"); open(tx, "w").write(tx_body)
        return subprocess.run([PY, PICKUP, "--out-existing", "--out", out, "--min-bytes", "500000",
                               "--transcript", tx], capture_output=True, text=True)

    # (1) mcp_output: null  -> veto inert -> MUST fail-closed (even with a valid fresh >500KB PNG present)
    r_null = _pick_mcp('{"status":"ok","mcp_output":null}')
    check("pickup mcp_output: ok + null mcp_output + valid >500KB PNG -> fail-closed (returncode!=0)",
          r_null.returncode != 0)
    # (2) mcp_output: ""    -> veto inert -> MUST fail-closed
    r_empty = _pick_mcp('{"status":"ok","mcp_output":""}')
    check("pickup mcp_output: ok + empty-string mcp_output -> fail-closed (returncode!=0)",
          r_empty.returncode != 0)
    # (3) mcp_output: 123   -> non-string -> MUST fail-closed (and must NOT crash .strip())
    r_int = _pick_mcp('{"status":"ok","mcp_output":123}')
    check("pickup mcp_output: ok + non-string (123) mcp_output -> fail-closed (returncode!=0)",
          r_int.returncode != 0)
    # (4) mcp_output: valid non-empty string with NO veto markers -> MUST pass (returncode 0)
    r_ok = _pick_mcp('{"status":"ok","mcp_output":"codex bake output text"}')
    check("pickup mcp_output: ok + valid non-empty string (no veto markers) -> PASS (returncode 0)",
          r_ok.returncode == 0)

    # G) NONCE fail-closed (--request-id): emit_bake_request stamps a uuid4 request_id into the bakereq + the agent
    # echoes it back in the bakestatus; pickup --request-id rejects a bakestatus whose request_id ≠ the expected one
    # (a stale/foreign bake at the same path). A VALID >500KB PNG + a clean string mcp_output is supplied so the
    # verdict turns ONLY on the nonce. Mismatch -> fail-closed; the matching id (control) -> PASS.
    nonce_tx = os.path.join(td, "nonce.bakestatus.json")
    open(nonce_tx, "w").write('{"status":"ok","mcp_output":"native bake output","request_id":"aaaa1111"}')
    r_badid = subprocess.run([PY, PICKUP, "--out-existing", "--out", out, "--min-bytes", "500000",
                              "--transcript", nonce_tx, "--request-id", "bbbb2222"], capture_output=True, text=True)
    check("pickup nonce: bakestatus request_id ≠ --request-id + valid >500KB PNG -> fail-closed (stale/foreign bake)",
          r_badid.returncode != 0 and "request_id" in (r_badid.stderr or "").lower())
    r_goodid = subprocess.run([PY, PICKUP, "--out-existing", "--out", out, "--min-bytes", "500000",
                               "--transcript", nonce_tx, "--request-id", "aaaa1111"], capture_output=True, text=True)
    check("pickup nonce: MATCHING request_id (control) -> PASS (returncode 0) — proves G fails ONLY on the nonce",
          r_goodid.returncode == 0)

    # G-nondict) NONCE not inert for NON-DICT transcripts: opting into --request-id is opting into nonce enforcement,
    # so a transcript that carries no addressable request_id (it can't echo back the nonce) MUST fail-closed — NOT be
    # silently passed. Two non-dict shapes, each with a fresh VALID >500KB PNG (reusing _real_png's `out` above) and a
    # request_id supplied, so the verdict turns ONLY on the nonce guard refusing to go inert:
    #   (a) a plain NON-JSON log (parses to None) and (b) a JSON LIST (not a dict) BOTH return returncode!=0.
    # Were the guard still `isinstance(_st, dict) and ...`, a non-dict transcript would skip the check and a valid PNG
    # would slip through (rc=0). The control above (matching DICT -> PASS) + the dict-mismatch fail above stay intact.
    nd_log = os.path.join(td, "nonce_plain.bakelog")   # plain NON-JSON log -> json.loads fails -> None (not a dict)
    open(nd_log, "w").write("native bake output ran; image saved to the out path.\n")
    r_ndlog = subprocess.run([PY, PICKUP, "--out-existing", "--out", out, "--min-bytes", "500000",
                              "--transcript", nd_log, "--request-id", "aaaa1111"], capture_output=True, text=True)
    check("pickup nonce: --request-id + plain NON-JSON log transcript + valid >500KB PNG -> fail-closed (nonce not inert for non-dict)",
          r_ndlog.returncode != 0 and "request_id" in (r_ndlog.stderr or "").lower())
    nd_list = os.path.join(td, "nonce_list.bakestatus.json")   # JSON LIST (valid JSON, but NOT a dict) -> no addressable request_id
    open(nd_list, "w").write('["status","ok","native bake output","request_id","aaaa1111"]')
    r_ndlist = subprocess.run([PY, PICKUP, "--out-existing", "--out", out, "--min-bytes", "500000",
                               "--transcript", nd_list, "--request-id", "aaaa1111"], capture_output=True, text=True)
    check("pickup nonce: --request-id + JSON LIST (non-dict) transcript + valid >500KB PNG -> fail-closed (nonce not inert for non-dict)",
          r_ndlist.returncode != 0 and "request_id" in (r_ndlist.stderr or "").lower())

    # C) JS-mirror parity for the mcp_output fail-closed contract: spiral_engine.js verifyExistingPng must ALSO
    # return ok:false on a bakestatus whose mcp_output is null / "" / non-string (mirror the Python (1)-(3) above),
    # and ok:true on a valid non-empty string. The engine has a top-level await/return (Workflow-harness shape) so it
    # can't be `import`ed directly — extract verifyExistingPng + its VETO_PATS source with stdlib regex (the same way
    # §3d extracts VETO_PATS) and eval it inside a tiny CommonJS node harness. Skip gracefully if node is absent.
    import shutil as _shutil
    _node = _shutil.which("node")
    if not _node:
        check("JS verifyExistingPng mcp_output: SKIPPED (node not installed) — Python parity above still locks the contract", True)
    else:
        _harness = r'''
const fs = require('fs');
const [enginePath, pngPath, txBody] = [process.argv[2], process.argv[3], process.argv[4]];
const src = fs.readFileSync(enginePath, 'utf8');
const vetoM = src.match(/const\s+VETO_PATS\s*=\s*\[[\s\S]*?\]/);
const fi = src.indexOf('function verifyExistingPng');
if (!vetoM || fi < 0) { console.log(JSON.stringify({ok: null, reason: 'could not extract verifyExistingPng/VETO_PATS from spiral_engine.js'})); process.exit(0); }
let depth = 0, i = src.indexOf('{', fi);
for (; i < src.length; i++) { if (src[i] === '{') depth++; else if (src[i] === '}') { depth--; if (depth === 0) { i++; break; } } }
const fnSrc = src.slice(fi, i);
const verifyExistingPng = new Function('require', vetoM[0] + '\n' + fnSrc + '\nreturn verifyExistingPng;')(require);
const tx = pngPath + '.jsnodetx.json';
fs.writeFileSync(tx, txBody);
console.log(JSON.stringify(verifyExistingPng(pngPath, 500000, null, null, tx)));
'''
        _hpath = os.path.join(td, "js_verify_harness.cjs"); open(_hpath, "w").write(_harness)
        _ENGINE = os.path.join(ROOT, "packages", "core", "spiral_engine.js")

        def _js_verify(tx_body):
            rr = subprocess.run([_node, _hpath, _ENGINE, out, tx_body], capture_output=True, text=True, timeout=30)
            try:
                return json.loads((rr.stdout or "").strip().splitlines()[-1])
            except Exception:
                return {"ok": "PARSE_ERR", "stdout": rr.stdout, "stderr": rr.stderr}
        check("JS verifyExistingPng mcp_output: ok + null mcp_output + valid >500KB PNG -> ok:false (mirror Python)",
              _js_verify('{"status":"ok","mcp_output":null}').get("ok") is False)
        check("JS verifyExistingPng mcp_output: ok + empty-string mcp_output -> ok:false (mirror Python)",
              _js_verify('{"status":"ok","mcp_output":""}').get("ok") is False)
        check("JS verifyExistingPng mcp_output: ok + non-string (123) mcp_output -> ok:false (mirror Python)",
              _js_verify('{"status":"ok","mcp_output":123}').get("ok") is False)
        check("JS verifyExistingPng mcp_output: ok + valid non-empty string -> ok:true (control, proves the harness loads the real fn)",
              _js_verify('{"status":"ok","mcp_output":"codex bake output text"}').get("ok") is True)

    # in-process function-level parity with the JS mirror: verify_existing_png MUST fail-close with NO transcript.
    # (a code-drawn fallback PNG with a clean sig/dims/size must not slip through merely because transcript=None).
    sys.path.insert(0, os.path.join(MF, "scripts"))
    from pickup_image import verify_existing_png as _verify_existing_png   # SHARED verifier (contract-v2 §0a)
    check("verify_existing_png(valid >500KB png, transcript=None)['ok'] is False (function-level fail-closed)",
          _verify_existing_png(out, transcript=None).get("ok") is False)

# ── 3d. VETO_PATS parity: spiral_engine.js VETO_PATS ≡ pickup_image.py _VETO_PATS (length + order, string-by-string) ──
# The two engines (JS in-process mirror + the Python SOP verifier) MUST scan for the SAME fallback markers; any drift
# would let a hand-drawn fallback slip through one engine but not the other. Extract both lists with stdlib only —
# Python via ast, JS by parsing the regex-literal SOURCES out of the `const VETO_PATS = [...]` array — and compare.
import ast as _ast
def _py_veto_pats():
    src = open(PICKUP, encoding="utf-8").read()
    for node in _ast.walk(_ast.parse(src)):
        if isinstance(node, _ast.Assign) and any(
                isinstance(t, _ast.Name) and t.id == "_VETO_PATS" for t in node.targets):
            return list(_ast.literal_eval(node.value))   # list of raw-string regex sources
    return None
def _js_veto_pats():
    """Return a list of (source, flags) for every JS /regex/ literal in the `const VETO_PATS = [...]` array.
    FLAG-AWARE (B): a JS regex literal is /SOURCE/FLAGS — we capture BOTH the escape-aware SOURCE between the
    slashes AND the trailing flag chars ([gimsuyd]*). The denylist patterns MUST be flagless: a /g or /y
    mutation silently changes match semantics (a global regex shares lastIndex across .test() calls → can MISS
    on alternating inputs), so a flag drift on any VETO pattern must FAIL this parity test, not just a source edit."""
    src = open(os.path.join(ROOT, "packages", "core", "spiral_engine.js"), encoding="utf-8").read()
    m = re.search(r"const\s+VETO_PATS\s*=\s*\[(.*?)\]", src, re.S)   # the ARRAY literal (the comment mention has no '= [')
    if not m:
        return None
    # each element is a JS /regex/ literal → capture the SOURCE (escape-aware) AND the trailing flags
    return re.findall(r"/((?:\\.|[^/\\\n])+)/([gimsuyd]*)", m.group(1))
_py_pats, _js_pairs = _py_veto_pats(), _js_veto_pats()
_js_pats = [s for s, _f in _js_pairs] if _js_pairs else _js_pairs   # the SOURCEs only, for the source-equality check
check("VETO parity: pickup_image.py _VETO_PATS extracted (non-empty)", bool(_py_pats))
check("VETO parity: spiral_engine.js VETO_PATS extracted (non-empty)", bool(_js_pairs))
check("VETO parity: same length", bool(_py_pats) and bool(_js_pairs) and len(_py_pats) == len(_js_pairs))
check("VETO parity: IDENTICAL string-by-string in order (no marker drift between the two engines)",
      _py_pats == _js_pats)
# FLAG PARITY (B): every JS VETO entry MUST be a flagless literal — a /g or /y (or any flag) mutation changes
# match semantics and must fail HERE even though the source string is unchanged (the equality check above can't see it).
check("VETO parity: every JS VETO_PATS entry has EMPTY flags (a /g or /y mutation must fail this)",
      bool(_js_pairs) and all(f == "" for _s, f in _js_pairs))

# ── 3d-prompt. buildBakePrompt CROSS-ENGINE PARITY: spiral_engine.js buildBakePrompt ≡ pickup_image.py build_bake_prompt ──
# The "three engines share ONE bake-prompt" claim (gate-4 MINOR) was NOT CI-guarded — only VETO_PATS was. The bake-prompt
# string is what actually arms the NATIVE image tool / dodges the hand-draw fallback (no forbid-list, no veto tokens, ref +
# out paths LITERAL because the mcp__codex__codex schema has no -i image param); a silent wording drift between the JS mirror
# and the Python source of truth would mean the two engines hand the agent DIFFERENT prompts. Lock byte-EQUALITY of the two
# implementations over 2 fixtures: (1) WITH an identity ref (body + content_png_abs + identity_ref_abs + out_path_abs → 4
# lines), (2) WITHOUT one (identity_ref empty → the "Reference image 2" line must be DROPPED). Same node harness as §3c-mcp /
# §3d-size: regex-locate `function buildBakePrompt`, brace-match its body, Function-eval it in a CommonJS sandbox, and compare
# against the imported Python build_bake_prompt. Skip gracefully if node is absent (this is the ONLY guard for this claim, so
# the skip is logged loudly). If a REAL wording mismatch surfaces it FAILS here (the test reflects true parity — never papered over).
sys.path.insert(0, os.path.join(MF, "scripts"))
from pickup_image import build_bake_prompt as _py_build_bake_prompt   # SHARED bake-prompt primitive (contract-v2 §0a)
import shutil as _shutil_bp
_node_bp = _shutil_bp.which("node")
if not _node_bp:
    check("buildBakePrompt parity: SKIPPED (node not installed) — UNGUARDED for this run; install node to lock the shared-prompt claim", True)
else:
    with tempfile.TemporaryDirectory() as td:
        # node harness: extract buildBakePrompt's SOURCE from spiral_engine.js (brace-match, same technique as the
        # verifyExistingPng extraction in §3c-mcp/§3d-size), Function-eval it, and emit JSON.stringify(result) so the
        # exact string (incl. the em-dash, newlines, and the conditional Reference-image-2 line) round-trips losslessly.
        _harness_bp = r'''
const fs = require('fs');
const [enginePath, body, contentAbs, idAbs, outAbs] = process.argv.slice(2);
const src = fs.readFileSync(enginePath, 'utf8');
const fi = src.indexOf('function buildBakePrompt');
if (fi < 0) { console.log(JSON.stringify({__err: 'could not find function buildBakePrompt in spiral_engine.js'})); process.exit(0); }
let depth = 0, i = src.indexOf('{', fi);
for (; i < src.length; i++) { if (src[i] === '{') depth++; else if (src[i] === '}') { depth--; if (depth === 0) { i++; break; } } }
const fnSrc = src.slice(fi, i);
const buildBakePrompt = new Function(fnSrc + '\nreturn buildBakePrompt;')();
process.stdout.write(JSON.stringify(buildBakePrompt(body, contentAbs, idAbs, outAbs)));
'''
        _hpath_bp = os.path.join(td, "js_buildbakeprompt_harness.cjs"); open(_hpath_bp, "w").write(_harness_bp)
        _ENGINE_bp = os.path.join(ROOT, "packages", "core", "spiral_engine.js")

        def _js_build_bake_prompt(body, content_abs, id_abs, out_abs):
            rr = subprocess.run([_node_bp, _hpath_bp, _ENGINE_bp, body, content_abs, id_abs, out_abs],
                                capture_output=True, text=True, timeout=30)
            try:
                return json.loads(rr.stdout)
            except Exception:
                return {"__parse_err": True, "stdout": rr.stdout, "stderr": rr.stderr}

        _body = "WORLD = warm-lab → apply the two-world lighting.\nSCENE: the audit room, blue executor + green reviewer at a board"
        # fixture (1): WITH an identity ref — all 4 lines (incl. "Reference image 2 (absolute path): ...")
        _c, _i, _o = "/abs/proj/panels/_content_refs/S01_a01.png", "/abs/proj/assets/duo_canonical_ref_v001.png", "/abs/proj/panels/S01_panel_a01.png"
        _py1 = _py_build_bake_prompt(_body, _c, _i, _o)
        _js1 = _js_build_bake_prompt(_body, _c, _i, _o)
        check("buildBakePrompt parity: WITH identity ref — JS buildBakePrompt ≡ Python build_bake_prompt (byte-EQUAL)",
              isinstance(_js1, str) and _py1 == _js1)
        # fixture (2): WITHOUT an identity ref (identity_ref empty) — the "Reference image 2" line is DROPPED in BOTH
        _py2 = _py_build_bake_prompt(_body, _c, "", _o)
        _js2 = _js_build_bake_prompt(_body, _c, "", _o)
        check("buildBakePrompt parity: WITHOUT identity ref (empty) — JS ≡ Python byte-EQUAL (Reference-image-2 line dropped in BOTH)",
              isinstance(_js2, str) and _py2 == _js2)
        # discriminators: prove the parity check is meaningful (the harness loaded a REAL fn that varies on the ref + the body),
        # not a vacuous string==string — and that the no-ref case actually DROPS exactly the Reference-image-2 line.
        check("buildBakePrompt parity: harness loaded the real fn (output is non-empty + embeds the LITERAL out path)",
              isinstance(_js1, str) and _o in _js1 and "Use your native image generation tool" in _js1)
        check("buildBakePrompt parity: WITH-ref output has the 'Reference image 2' line; WITHOUT-ref drops exactly it (one fewer line)",
              isinstance(_py1, str) and isinstance(_py2, str)
              and ("Reference image 2 (absolute path):" in _py1) and ("Reference image 2 (absolute path):" not in _py2)
              and len(_py1.split("\n")) == len(_py2.split("\n")) + 1)

# ── 3d-emit. emit_bake_request must carry config.include_image_gen_tool === true through to the bakereq.json ──
# The agent mcp__codex__codex bake only runs its NATIVE image tool when config.include_image_gen_tool is true; without
# it Codex falls back to writing descriptive text / an SVG renderer (the hand-draw fallback the HARD-VETO exists to
# catch). emit_bake_request (the SHARED contract-v2 §0a primitive in pickup_image.py) atomically serializes the bake
# request the orchestrators hand the agent — this locks that it preserves config.include_image_gen_tool verbatim (a
# nested-config drop/mangle here would silently disarm the native-tool flag for EVERY bake). It also returns a uuid4
# request_id that lands in the payload (the G nonce). pure in-process, no MCP / image_gen / network.
sys.path.insert(0, os.path.join(MF, "scripts"))
from pickup_image import emit_bake_request as _emit_bake_request   # SHARED bake primitive (contract-v2 §0a)
with tempfile.TemporaryDirectory() as td:
    _ebr_out = os.path.join(td, "S01_panel_a01.png")
    _ebr_req = {"prompt_text": "bake one png", "out_path": _ebr_out, "model": "gpt-5.5",
                "config": {"model_reasoning_effort": "xhigh", "include_image_gen_tool": True},
                "sandbox": "workspace-write", "created_at": 1.0, "min_bytes": 500000, "aspect": 1280 / 720}
    _rid = _emit_bake_request(_ebr_out, _ebr_req)
    _ebr = json.load(open(_ebr_out + ".bakereq.json", encoding="utf-8"))
    check("emit_bake_request: bakereq.json carries config.include_image_gen_tool === true (native image tool armed)",
          (_ebr.get("config") or {}).get("include_image_gen_tool") is True)
    check("emit_bake_request: returns + stamps a request_id nonce into the bakereq (binds the G nonce check)",
          isinstance(_rid, str) and len(_rid) > 0 and _ebr.get("request_id") == _rid)

# ── 3d-size. SIZE BOUNDARY: a PNG of EXACTLY --min-bytes is rejected by pickup --out-existing (accept only strictly >) ──
# The size floor is b <= min_bytes -> reject (matches the downstream run_comic acceptance gate's bytes > min_bytes),
# closing the off-by-one where a min_bytes PNG would pass pickup but be rejected downstream. Build a VALID PNG of an
# EXACT byte count (pad the tail with a benign tEXt chunk; png_dims reads only sig+IHDR, getsize counts every byte) and
# supply a clean string-mcp_output transcript so the verdict turns ONLY on size: EXACTLY min_bytes -> REJECT, min_bytes+1 -> PASS.
def _png_exact(path, target, w=64, h=64):
    raw = b"".join(b"\x00" + os.urandom(3 * w) for _ in range(h))
    idat = _zlib.compress(raw, 1)
    base = (b"\x89PNG\r\n\x1a\n"
            + _png_chunk(b"IHDR", _struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + _png_chunk(b"IDAT", idat) + _png_chunk(b"IEND", b""))
    assert len(base) <= target, f"base PNG {len(base)} already exceeds target {target} — shrink w/h"
    pad = target - len(base)
    out_bytes = base + (_png_chunk(b"tEXt", b"P" * (pad - 12)) if pad >= 12 else b"\x00" * pad)  # tEXt overhead = 12 bytes
    with open(path, "wb") as f:
        f.write(out_bytes)
    return os.path.getsize(path)
def _png_chunk(typ, data):
    return _struct.pack(">I", len(data)) + typ + data + _struct.pack(">I", _binascii.crc32(typ + data) & 0xffffffff)
with tempfile.TemporaryDirectory() as td:
    N = 600000
    sb_out = os.path.join(td, "S01_panel_a01.png")
    assert _png_exact(sb_out, N) == N, "could not build a PNG of EXACTLY N bytes for the boundary test"
    sb_tx = os.path.join(td, "ok.bakestatus.json")
    open(sb_tx, "w").write('{"status":"ok","mcp_output":"native bake output text"}')
    r_eq = subprocess.run([PY, PICKUP, "--out-existing", "--out", sb_out, "--min-bytes", str(N),
                           "--transcript", sb_tx], capture_output=True, text=True)
    check("size boundary: PNG of EXACTLY --min-bytes is REJECTED by pickup --out-existing (b <= min_bytes -> fail)",
          r_eq.returncode != 0 and "too small" in (r_eq.stderr or "").lower())
    r_gt = subprocess.run([PY, PICKUP, "--out-existing", "--out", sb_out, "--min-bytes", str(N - 1),
                           "--transcript", sb_tx], capture_output=True, text=True)
    check("size boundary: PNG of min_bytes+1 (strictly greater) PASSES — pins the floor is exactly b > min_bytes",
          r_gt.returncode == 0)

    # JS-MIRROR SIZE BOUNDARY parity (the size comparator must be parity-locked, not just VETO_PATS): spiral_engine.js
    # verifyExistingPng must apply the SAME floor as pickup_image.py — buf.length <= minBytes -> ok:false (REJECT a PNG of
    # EXACTLY min_bytes), strictly greater -> ok:true. A drift to `<` here would let a min_bytes PNG pass the JS in-process
    # mirror while the Python SOP verifier rejects it (the off-by-one the Python §3d-size test locks). Reuse the SAME exact-N
    # PNG (sb_out) + clean string-mcp_output transcript (sb_tx) as the Python checks above, and the SAME node harness used by
    # §3c-mcp's JS mcp_output tests (regex-extract verifyExistingPng + VETO_PATS from the engine, eval in a CommonJS sandbox),
    # threading minBytes through argv so the verdict turns ONLY on size: minBytes=N -> ok:false, minBytes=N-1 (i.e. N == min_bytes+1) -> ok:true.
    # Skip gracefully if node is absent (the Python §3d-size checks above still lock the floor on their own).
    import shutil as _shutil_sb
    _node_sb = _shutil_sb.which("node")
    if not _node_sb:
        check("JS verifyExistingPng size boundary: SKIPPED (node not installed) — Python size boundary above still locks the floor", True)
    else:
        _harness_sb = r'''
const fs = require('fs');
const [enginePath, pngPath, minBytes, txBody] = [process.argv[2], process.argv[3], parseInt(process.argv[4], 10), process.argv[4 + 1]];
const src = fs.readFileSync(enginePath, 'utf8');
const vetoM = src.match(/const\s+VETO_PATS\s*=\s*\[[\s\S]*?\]/);
const fi = src.indexOf('function verifyExistingPng');
if (!vetoM || fi < 0) { console.log(JSON.stringify({ok: null, reason: 'could not extract verifyExistingPng/VETO_PATS from spiral_engine.js'})); process.exit(0); }
let depth = 0, i = src.indexOf('{', fi);
for (; i < src.length; i++) { if (src[i] === '{') depth++; else if (src[i] === '}') { depth--; if (depth === 0) { i++; break; } } }
const fnSrc = src.slice(fi, i);
const verifyExistingPng = new Function('require', vetoM[0] + '\n' + fnSrc + '\nreturn verifyExistingPng;')(require);
const tx = pngPath + '.jssbtx.json';
fs.writeFileSync(tx, txBody);
console.log(JSON.stringify(verifyExistingPng(pngPath, minBytes, null, null, tx)));
'''
        _hpath_sb = os.path.join(td, "js_size_harness.cjs"); open(_hpath_sb, "w").write(_harness_sb)
        _ENGINE_sb = os.path.join(ROOT, "packages", "core", "spiral_engine.js")
        _sb_txbody = open(sb_tx, encoding="utf-8").read()   # the SAME clean string-mcp_output transcript as the Python checks

        def _js_verify_sb(min_bytes):
            rr = subprocess.run([_node_sb, _hpath_sb, _ENGINE_sb, sb_out, str(min_bytes), _sb_txbody],
                                capture_output=True, text=True, timeout=30)
            try:
                return json.loads((rr.stdout or "").strip().splitlines()[-1])
            except Exception:
                return {"ok": "PARSE_ERR", "stdout": rr.stdout, "stderr": rr.stderr}
        # minBytes == N: the exact-N PNG is EXACTLY min_bytes -> REJECT (ok:false), mirroring Python's b <= min_bytes floor
        check("JS verifyExistingPng size boundary: PNG of EXACTLY minBytes -> ok:false (mirror Python b <= min_bytes -> reject)",
              _js_verify_sb(N).get("ok") is False)
        # minBytes == N-1: the same N-byte PNG is now min_bytes+1 (strictly greater) -> ACCEPT (ok:true) — pins floor is b > min_bytes in BOTH engines
        check("JS verifyExistingPng size boundary: PNG of min_bytes+1 (strictly greater) -> ok:true (size comparator parity-locked, not just VETO_PATS)",
              _js_verify_sb(N - 1).get("ok") is True)

# ── 3e. doctrine guard (D self-enforcing): the LIVE bake-prompt template that SKILL.md §③ points the agent to
# (references/prompt_templates.md) must declare the AGENT-SEAM mechanism, so a future edit can't silently
# re-introduce the retired "read-only forces the native tool" / legacy "pickup_image.py --marker" doctrine.
# Targeted at that one live template ON PURPOSE — correct NEGATIONS elsewhere ("No sandbox setting forces the
# native tool — the verifier is load-bearing") and PROMPTS.md's preserved verbatim historical record are NOT scanned. ──
_PT = open(os.path.join(MF, "references", "prompt_templates.md"), encoding="utf-8").read()
check("doctrine: prompt_templates §A declares sandbox: workspace-write, not read-only",
      "sandbox: workspace-write" in _PT and "sandbox: read-only" not in _PT)
check("doctrine: prompt_templates does NOT re-assert the retired 'point of read-only is to FORCE' claim",
      "point of read-only" not in _PT.lower())
check("doctrine: prompt_templates verifier is --out-existing, not the legacy 'pickup_image.py --marker'",
      "--out-existing" in _PT and "pickup_image.py --marker" not in _PT)

# ── 4. comic literal-diff exactness (mirrors run_comic.panel_verdict / spiral_engine.panelVerdict hit()) ──
def _sets(arr):
    c, f = set(), set()
    for s in arr:
        for x in re.findall(r"[a-z0-9+._:|/-]+", s.lower()):
            c.add(x)
        for x in re.findall(r"[a-z0-9]+", s.lower()):
            f.add(x)
    return (c, f, re.sub(r"\s+", " ", " ".join(s.lower() for s in arr)))


def _hit(e, S):
    e = e.lower().strip()
    if " " in e:
        return e in S[2]
    if re.search(r"[0-9:]", e):
        return e in S[0]
    if e in S[0]:
        return True
    p = re.findall(r"[a-z0-9]+", e)
    return len(p) > 0 and all(x in S[1] for x in p)


check("literal-diff: correct timestamp matches", _hit("T-24:00:00", _sets(["DDL", "T-24:00:00"])) is True)
check("literal-diff: WRONG timestamp rejected", _hit("T-24:00:00", _sets(["DDL", "T-24:00:01"])) is False)
check("literal-diff: +6.2 does not satisfy +6.25", _hit("+6.2", _sets(["+6.25"])) is False)
check("literal-diff: label fine-parts fallback still matches", _hit("jsonschema", _sets(["jsonschema.validate"])) is True)

# ── 5. p0_proof gate: a USABLE comic project with NO decision:p0_proof_* node must fail-closed at the p0 gate ──
# (--bake-mode exec avoids any real MCP; the p0 gate is hit BEFORE any render/bake/exec-raise, so it fail-closes
#  THERE — not at the missing-comic guard and not at the exec-raise. Proves the gate, not the wrong reason.)
RUN_COMIC = os.path.join(ROOT, "skills", "comic-director", "scripts", "run_comic.py")
RUN_P0 = os.path.join(ROOT, "skills", "comic-cross-layer-gate", "scripts", "run_p0_proof.py")
sys.path.insert(0, os.path.join(ROOT, "skills", "comic-director", "scripts"))
from run_comic import get_bake_plan as _get_bake_plan            # the p0-bound spend plan (single source)
from pickup_image import bake_plan_digest as _bake_plan_digest   # canonical bakereq/v1 digest (contract-v2 §0a)
import hashlib as _hashlib

def _p0_proj(td):
    """minimal USABLE comic project (the §5 fixture pattern): svg blueprint + ART_BIBLE + 1-panel comic.json."""
    proj = os.path.join(td, "proj"); nodes = os.path.join(proj, "wiki", "nodes"); os.makedirs(nodes)
    open(os.path.join(proj, "panel_s01.svg"), "w").write('<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720"></svg>')
    open(os.path.join(proj, "ART_BIBLE.md"), "w").write("# art bible\n")
    comic = {"schema_version": "comic-ir/1.0", "comic_id": "t", "defaults": {"text_mode": "html"},
             "pages": [{"id": "P00", "type": "page", "beat": "b", "panel_ids": ["S01"]}],
             "panels": {"S01": {"text_mode": "html",
                                "condition": {"content_svg": "panel_s01.svg", "world": "warm-lab", "scene": "x"}}}}
    json.dump(comic, open(os.path.join(proj, "comic.json"), "w"))
    return proj, nodes

def _comic_sha(proj):
    # BYTES digest, exactly as run_comic._p0_clean / run_p0_proof compute it (full hexdigest, not sha()[:16])
    return _hashlib.sha256(open(os.path.join(proj, "comic.json"), "rb").read()).hexdigest()

def _run_comic_exec(proj, timeout=90, page="P00", extra=()):
    rc = subprocess.run([PY, RUN_COMIC, "--project", proj, "--repo", ROOT, "--page", page, "--panels", "S01",
                         "--bake-mode", "exec", *extra], capture_output=True, text=True, timeout=timeout)
    return rc, ((rc.stderr or "") + (rc.stdout or "")).lower()

def _mint_cert(proj, nodes, with_digests=True, quorum=("google", "openai")):
    """decision:p0_proof_* fixture in run_p0_proof.py's MINTED shape; with_digests=False = the OLD (pre-binding)
    payload shape that used to pass — it must now be REJECTED as an unbound cert; quorum=None OMITS
    reviewer_quorum entirely (the pre-quorum cert shape — correct digests alone must no longer clear the gate)."""
    pl = {"gate_kind": "p0_proof", "verdict": "advance", "target_node_id": "decision:compile_t",
          "review_files": ["r_codex.json", "r_gemini.json"]}
    if quorum is not None:
        pl["reviewer_quorum"] = list(quorum)
    if with_digests:
        # same-way computation as run_comic: sha256(comic.json bytes) + bake_plan_digest(get_bake_plan()) —
        # no-arg get_bake_plan == the argparse defaults, which is what the exec subprocess resolves too.
        pl["comic_sha"] = _comic_sha(proj); pl["bake_plan_sha"] = _bake_plan_digest(_get_bake_plan())
    node = {"node_id": "decision:p0_proof_t_test", "node_type": "decision", "status": "final",
            "title": "p0_proof gate t -> advance", "created_at": "2026-07-11T00:00:00+00:00", "payload": pl}
    json.dump(node, open(os.path.join(nodes, "decision_p0_proof_t_test.json"), "w"))

_P0_FAIL_MSG = "no clean decision:p0_proof"   # the p0 preflight's fail-closed discriminator

def _past_p0(rc, out):
    # evidence the run got PAST the p0 gate into the panel loop: the ▶ attempt log, the exec-bake-retired raise,
    # or the no-panel escalation (Chrome-less CI) — all strictly LATER stops than the p0 preflight.
    return ("exec bake retired" in out) or ("attempt 1" in out) or ("no panel ever generated" in out) \
           or ("▶" in ((rc.stderr or "") + (rc.stdout or "")))

with tempfile.TemporaryDirectory() as td:
    proj, nodes = _p0_proj(td)
    rc5, out5 = _run_comic_exec(proj, timeout=30)
    check("p0_proof: usable comic project, NO p0_proof node -> fail-closed at the p0 gate",
          rc5.returncode != 0 and "p0_proof" in out5)

# ── 5b. p0_proof DIGEST BINDING (P0-3): the OLD digest-less cert shape must now FAIL-CLOSED ──
# FLIPPED from the pre-Wave2 success assertion: this exact fixture (verdict approve / status final, NO
# comic_sha/bake_plan_sha) used to let the run proceed — under the digest requirement it is an UNBOUND cert
# (proves nothing about the CURRENT comic.json + spend plan), so _p0_clean must reject it and the preflight fires.
with tempfile.TemporaryDirectory() as td:
    proj, nodes = _p0_proj(td)
    p0_node = {"node_id": "decision:p0_proof_aris_comic_v1", "node_type": "decision", "status": "final",
               "title": "p0_proof gate -> advance", "created_at": "2026-06-08T00:00:00+00:00",
               "payload": {"gate_kind": "p0_proof", "target_node_id": "p0:pipeline_aris_comic_v1",
                           "verdict": "approve", "reasoning": "zero-credit pre-prod proof: all blockers cleared",
                           "repair_instruction": ""}}
    json.dump(p0_node, open(os.path.join(nodes, "decision_p0_proof_aris_comic_v1.json"), "w"))
    rc5b, out5b = _run_comic_exec(proj, timeout=30)
    check("p0 binding: OLD-shape cert (no comic_sha/bake_plan_sha) -> fail-closed (unbound cert rejected)",
          rc5b.returncode != 0 and _P0_FAIL_MSG in out5b)
    check("p0 binding: the rejection names the missing/stale digests (rejected FOR the binding, not another reason)",
          "missing or stale" in out5b)

# ── 5c. p0_proof DIGEST BINDING success (P0-1): a cert carrying the CORRECT digests clears the p0 gate ──
# The new pass path: mint the digest-carrying cert (run_p0_proof's shape) against the CURRENT comic.json + the
# default spend plan, then run --bake-mode exec. The p0 fail-closed message must be ABSENT and the run must show
# evidence of a strictly LATER stop (attempt log / exec-bake-retired raise / no-panel escalation).
with tempfile.TemporaryDirectory() as td:
    proj, nodes = _p0_proj(td)
    _mint_cert(proj, nodes)
    rc5c, out5c = _run_comic_exec(proj)
    check("p0 binding SUCCESS: cert with correct comic_sha+bake_plan_sha -> proceeds PAST the p0 gate",
          (_P0_FAIL_MSG not in out5c) and _past_p0(rc5c, out5c))

# ── 5d. p0_proof DIGEST BINDING staleness (P0-2): modify comic.json AFTER minting -> stale cert rejected ──
# Same cert as §5c, but comic.json changes post-mint (still cfg-usable, so the run reaches the p0 gate — the
# failure can only come from the digest mismatch). The cert audited a DIFFERENT comic.json -> fail-closed.
with tempfile.TemporaryDirectory() as td:
    proj, nodes = _p0_proj(td)
    _mint_cert(proj, nodes)
    comic = json.load(open(os.path.join(proj, "comic.json"), encoding="utf-8"))
    comic["panels"]["S01"]["condition"]["scene"] = "x2 (edited after the cert was minted)"
    json.dump(comic, open(os.path.join(proj, "comic.json"), "w"))
    rc5d, out5d = _run_comic_exec(proj, timeout=30)
    check("p0 binding STALE: comic.json modified after mint -> fail-closed (stale cert rejected)",
          rc5d.returncode != 0 and _P0_FAIL_MSG in out5d and "missing or stale" in out5d)

# ── 5e. run_p0_proof.py e2e (P0-4/P0-5): mint on a both-families same-digest quorum; fail-closed otherwise ──
# The minter is the ONLY producer of the artifact §5c consumes — lock the handshake end-to-end: two counted
# reviews (openai + google, blockers==[], affirmative verdict, comic_sha == the CURRENT comic.json digest)
# -> exit 0 + a node carrying BOTH digests that run_comic then ACCEPTS; one family only, or the second family
# acquitting a DIFFERENT comic.json version -> exit 1 (quorum/same-digest fail-closed — timeouts never count).
def _review(td, name, family, comic_sha, verdict="pass"):
    p = os.path.join(td, name)
    json.dump({"family": family, "blockers": [], "verdict": verdict, "comic_sha": comic_sha}, open(p, "w"))
    return p

def _run_p0(proj, reviews, extra=()):
    return subprocess.run([PY, RUN_P0, "--project", proj, "--target", "decision:compile_t", *extra,
                           "--reviews"] + reviews, capture_output=True, text=True, timeout=30)

with tempfile.TemporaryDirectory() as td:
    proj, nodes = _p0_proj(td)
    csha = _comic_sha(proj)
    r_ok = _run_p0(proj, [_review(td, "r_codex.json", "openai", csha), _review(td, "r_gemini.json", "google", csha)])
    minted = [f for f in os.listdir(nodes) if f.startswith("decision_p0_proof_") and f.endswith(".json")]
    check("run_p0_proof: openai+google clean reviews, correct comic_sha -> exit 0 + cert minted into wiki/nodes",
          r_ok.returncode == 0 and len(minted) == 1)
    npl = (json.load(open(os.path.join(nodes, minted[0]), encoding="utf-8")).get("payload") or {}) if minted else {}
    check("run_p0_proof: minted payload binds BOTH digests (comic_sha + bake_plan_sha, computed the run_comic way)",
          npl.get("comic_sha") == csha and npl.get("bake_plan_sha") == _bake_plan_digest(_get_bake_plan())
          and npl.get("gate_kind") == "p0_proof" and sorted(npl.get("reviewer_quorum") or []) == ["google", "openai"])
    # the HANDSHAKE: the cert the real minter wrote must clear the real consumer's preflight (B4 closed e2e)
    rc5e, out5e = _run_comic_exec(proj)
    check("run_p0_proof -> run_comic handshake: the MINTED cert clears the p0 preflight (no fail-closed at p0)",
          (_P0_FAIL_MSG not in out5e) and _past_p0(rc5e, out5e))

with tempfile.TemporaryDirectory() as td:
    proj, nodes = _p0_proj(td)
    csha = _comic_sha(proj)
    # (a) ONE family only (two openai reviews): quorum unmet -> exit 1, nothing minted
    r_one = _run_p0(proj, [_review(td, "r_c1.json", "openai", csha), _review(td, "r_c2.json", "openai", csha)])
    check("run_p0_proof: ONE family only (2x openai) -> exit 1 (quorum fail-closed) + no cert minted",
          r_one.returncode != 0 and "quorum" in (r_one.stderr or "").lower() and not os.listdir(nodes))
    # (b) second family present but acquitting a DIFFERENT comic.json (wrong comic_sha) -> does NOT count -> exit 1
    r_stale = _run_p0(proj, [_review(td, "r_c3.json", "openai", csha), _review(td, "r_g1.json", "google", "0" * 64)])
    check("run_p0_proof: google review with WRONG comic_sha -> exit 1 (same-digest fail-closed) + no cert minted",
          r_stale.returncode != 0 and "quorum" in (r_stale.stderr or "").lower() and not os.listdir(nodes))

# ── 5f. NONEXISTENT --page fail-closed: a valid-charset ghost page id must exit !=0 — --dry-run included ──
# A --page that clears the ID_RE charset guard but names NO page in comic.json is a run addressed at a ghost:
# it must never reach the p0 gate / panel loop (real run) nor print bake prompts (dry-run). A VALID cert is
# minted so the ONLY possible failure is the page check itself, not the p0 preflight.
with tempfile.TemporaryDirectory() as td:
    proj, nodes = _p0_proj(td)
    _mint_cert(proj, nodes)
    rc5f, out5f = _run_comic_exec(proj, timeout=30, page="P99")
    check("page check: NONEXISTENT --page P99 (valid chars) -> exit !=0 with a page-related message naming the id",
          rc5f.returncode != 0 and "page" in out5f and "p99" in out5f)
    check("page check: the failure IS the page gate — not the p0 preflight, not the panel loop",
          _P0_FAIL_MSG not in out5f and not _past_p0(rc5f, out5f))
    rc5fd, out5fd = _run_comic_exec(proj, timeout=30, page="P99", extra=("--dry-run",))
    check("page check: --dry-run with a NONEXISTENT --page ALSO fails (no bake prompts for a ghost page)",
          rc5fd.returncode != 0 and "page" in out5fd)

# ── 5g. _p0_clean QUORUM: correct digests alone must NOT clear the p0 gate — the cert needs BOTH families ──
# §5c/§5e are the positive controls (correct digests + reviewer_quorum ["google","openai"] + target -> PASS);
# here the SAME digest-stamping code (_mint_cert) writes certs whose only defect is the quorum field.
with tempfile.TemporaryDirectory() as td:
    proj, nodes = _p0_proj(td)
    _mint_cert(proj, nodes, quorum=None)          # digests correct, reviewer_quorum MISSING
    rc5g, out5g = _run_comic_exec(proj, timeout=30)
    check("p0 quorum: correct digests but reviewer_quorum MISSING -> fail-closed at the p0 gate",
          rc5g.returncode != 0 and _P0_FAIL_MSG in out5g)
with tempfile.TemporaryDirectory() as td:
    proj, nodes = _p0_proj(td)
    _mint_cert(proj, nodes, quorum=["openai"])    # ONE family only — never a cross-model acquittal
    rc5g2, out5g2 = _run_comic_exec(proj, timeout=30)
    check('p0 quorum: correct digests but reviewer_quorum == ["openai"] (one family) -> fail-closed at the p0 gate',
          rc5g2.returncode != 0 and _P0_FAIL_MSG in out5g2)

# ── 5h. run_p0_proof --author-family openai -> REFUSED (a quorum family can drive, never acquit) ──
# Two otherwise-perfect reviews (openai+google, clean, correct comic_sha) — the ONLY defect is that the
# declared author family sits INSIDE the quorum, so its own "review" would be a self-acquittal. exit 1, no cert.
with tempfile.TemporaryDirectory() as td:
    proj, nodes = _p0_proj(td)
    csha = _comic_sha(proj)
    r_af = _run_p0(proj, [_review(td, "r_codex.json", "openai", csha), _review(td, "r_gemini.json", "google", csha)],
                   extra=("--author-family", "openai"))
    check("run_p0_proof: --author-family openai -> exit 1 (self-acquittal refusal) + no cert minted",
          r_af.returncode != 0 and not os.listdir(nodes) and "author" in (r_af.stderr or "").lower())

# ── 5i. run_p0_proof --min-bytes 400000: the minted bake_plan_sha binds the NON-default plan ──
# The cert must acquit the plan the consumer will actually run: bake_plan_sha == bake_plan_digest(
# get_bake_plan(min_bytes=400000)) — i.e. what run_comic --min-bytes 400000 resolves — and must NOT
# equal the default-plan digest (a default-plan cert must not bless a non-default spend, and vice versa).
from types import SimpleNamespace as _NS
with tempfile.TemporaryDirectory() as td:
    proj, nodes = _p0_proj(td)
    csha = _comic_sha(proj)
    r_mb = _run_p0(proj, [_review(td, "r_codex.json", "openai", csha), _review(td, "r_gemini.json", "google", csha)],
                   extra=("--min-bytes", "400000"))
    minted_mb = [f for f in os.listdir(nodes) if f.startswith("decision_p0_proof_") and f.endswith(".json")]
    check("run_p0_proof --min-bytes 400000: exit 0 + cert minted", r_mb.returncode == 0 and len(minted_mb) == 1)
    pl_mb = (json.load(open(os.path.join(nodes, minted_mb[0]), encoding="utf-8")).get("payload") or {}) if minted_mb else {}
    _sha_400k = _bake_plan_digest(_get_bake_plan(_NS(min_bytes=400000)))
    _sha_dflt = _bake_plan_digest(_get_bake_plan())
    check("run_p0_proof --min-bytes 400000: bake_plan_sha == the consumer's --min-bytes 400000 plan digest",
          pl_mb.get("bake_plan_sha") == _sha_400k)
    check("run_p0_proof --min-bytes 400000: bake_plan_sha != the DEFAULT plan digest (the knob really binds)",
          _sha_400k != _sha_dflt and pl_mb.get("bake_plan_sha") != _sha_dflt)

# ── 6. run_spiral.extract_json (N11): braces INSIDE string values must not truncate the payload ──
# A reviewer transcribing figure text routinely puts JSON/code fragments (with unbalanced braces) into
# observed_tokens. The old bare-character depth counter miscounted the escaped `{` inside the string and
# truncated; the raw_decode rewrite (parity with run_comic.extract_json) must round-trip it EXACTLY, and
# required_key must still skip a {"thought":...} preamble fragment.
import run_spiral as _rs   # MF/scripts already on sys.path; import-safe (main guard)
_inner = '{"narrative_beat_fidelity":4,"composition_story":5,"note":"brace { inside string"}'
_blob = 'reviewer prose {"thought":"scanning the panel"} ' \
        + json.dumps({"verdict": "approve", "observed_tokens": [_inner], "blockers": []}) + " trailing prose"
_j6 = _rs.extract_json(_blob, required_key="verdict")
check("run_spiral.extract_json: payload with unbalanced brace INSIDE a string parses (no truncation)",
      isinstance(_j6, dict) and _j6.get("verdict") == "approve")
check("run_spiral.extract_json: the brace-carrying observed_tokens string round-trips EXACTLY",
      isinstance(_j6, dict) and _j6.get("observed_tokens") == [_inner] and _j6.get("blockers") == [])

print()
if fails:
    print(f"❌ {len(fails)} gate test(s) FAILED: {fails}")
    sys.exit(1)
print("✅ all deterministic gate tests passed")
