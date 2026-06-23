#!/usr/bin/env python3
"""pickup_image.py — fail-closed verify of a natively-generated image (pure stdlib).

pickup_image.py is the single source of truth for the shared bake primitives.

PRIMARY mode (`--out-existing`, the default): verify the EXPLICIT `--out` path that the agent's
`mcp__codex__codex` bake wrote — PNG signature + IHDR dims + size floor (+ optional aspect band,
+ `mtime >= --created-at` so a stale prior bake at the same path is rejected). It runs a BEST-EFFORT
denylist (the HARD-VETO) against the KNOWN codex-exec hand-draw fallback markers
(struct/zlib/PIL/SVG/matplotlib) found in the agent `--transcript`: a clean PNG signature NEVER
overrides a fallback marker, because a hand-written struct+zlib PNG can pass sig+dims and exceed the
size floor. The denylist is NOT a complete security boundary — a sufficiently novel hand-draw recipe
could evade it; the load-bearing faithfulness gate is the DOWNSTREAM cross-model blind-transcribe +
content_diff, of which this scan is only a cheap first line of defense.

LEGACY mode (`--legacy-marker-glob`, exec/CI path only): the old "newest PNG after `--marker` in
~/.codex/generated_images" glob, copied into `--out`. Retained only for the non-agent code path.

This module is the SINGLE HOME of the shared bake primitives (contract-v2 §0a):
build_bake_prompt / verify_existing_png / emit_bake_request / await_bake_status / _status_path.
The two Python engines (run_comic.py + run_spiral.py) reuse these pickup_image.py primitives + the
`--out-existing` CLI; packages/core/spiral_engine.js MIRRORS them and is held to a byte-parity test
(tests/test_gates.py) so the in-process JS mirror can't drift from this Python source of truth.

Usage: python3 pickup_image.py --out-existing --out path/round1.png [--min-bytes 500000]
                  [--aspect W/H] [--created-at <epoch>] [--transcript bake.bakestatus.json]
                  [--request-id <uuid4 hex from emit_bake_request>]
       python3 pickup_image.py --legacy-marker-glob --marker <epoch> --out path/round1.png [--dir ...]
       # prints a JSON {ok,path,sha256,bytes,width,height}
"""
import argparse, hashlib, json, os, re, struct, sys, time, glob, shutil, uuid

def png_dims(path):
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != b"\x89PNG\r\n\x1a\n": return None
        f.read(4); ctype = f.read(4)
        if ctype != b"IHDR": return None
        w, h = struct.unpack(">II", f.read(8))
        return w, h

# ── shared bake primitives (contract-v2 §0a) — single source of truth, imported by the engines ──

def build_bake_prompt(body, content_png_abs, identity_ref_abs, out_path_abs):
    """SHARED dead-simple bake prompt (contract-v2 §2). Reference + output paths are LITERAL in the text
    (the mcp__codex__codex schema has no -i image param). Contains NOTHING that triggers the hand-drawn
    fallback (no forbid-list, no escape hatch, no veto tokens) — see codex-gptimage-bake-recipe."""
    lines = [
        "Use your native image generation tool to produce ONE PNG. Generate an image — do not write or "
        "edit any code or files; only generate the single image.",
        body,
        f"Reference image 1 (absolute path): {content_png_abs}",
    ]
    if identity_ref_abs:
        lines.append(f"Reference image 2 (absolute path): {identity_ref_abs}")
    lines.append(f"Save the final native PNG to this exact path: {out_path_abs}")
    return "\n".join(x for x in lines if x)

# code-context veto markers — NEVER a bare 'struct' (that would false-veto 'structural'/'reconstruct')
# The trailing two are the FROM-IMPORT form of the struct/zlib markers (`from struct import` / `from zlib import`),
# appended at the END in this FIXED order (struct then zlib); spiral_engine.js VETO_PATS appends the SAME two in the
# SAME order to keep the byte-parity test (tests/test_gates.py) green → 14 entries.
_VETO_PATS = [r"\bimport\s+struct\b", r"\bstruct\.pack\b", r"\bimport\s+zlib\b", r"\bzlib\.compress\b",
              r"\bfrom\s+pil\b", r"\bimport\s+pil\b", r"<svg", r"\bmatplotlib\b", r"\bdef\s+main\s*\(",
              r"\brsvg-convert\b", r"\bcairosvg\b", r"\bwritefile\b",
              r"\bfrom\s+struct\s+import\b", r"\bfrom\s+zlib\s+import\b"]

def _veto_hits(scan_path):
    """Code-context fallback markers found in a transcript/log (empty list = clean)."""
    if not scan_path or not os.path.exists(scan_path):
        return []
    low = open(scan_path, errors="ignore").read().lower()
    return [p for p in _VETO_PATS if re.search(p, low)]

def _verify_png_bytes(out_path, min_bytes, aspect, request_created_at):
    """The pure PNG-bytes check (existence + size floor + sig/IHDR + optional aspect band + mtime>=request).
    Shared by both the normal post-denylist path and the allow_no_transcript=True legacy branch (one impl, no drift)."""
    if not os.path.exists(out_path):
        return {"ok": False, "reason": "out_path does not exist (agent bake never wrote it — fail-closed)"}
    b = os.path.getsize(out_path)
    # reject EXACTLY min_bytes too (b <= min_bytes), accept only strictly greater — matches the downstream
    # acceptance gate (run_comic.py rejects on bytes <= min_bytes), closing an off-by-one where a min_bytes PNG
    # would pass pickup but be rejected downstream.
    if b <= min_bytes:
        return {"ok": False, "reason": f"out_path too small ({b} <= {min_bytes}) — likely non-native fallback"}
    dims = png_dims(out_path)
    if not dims:
        return {"ok": False, "reason": "out_path is not a valid PNG (bad signature/IHDR)"}
    if aspect:
        ar = dims[0] / dims[1]
        if not (0.6 * aspect <= ar <= 1.6 * aspect):
            return {"ok": False, "reason": f"out_path aspect {ar:.3f} off blueprint {aspect:.3f}"}
    if request_created_at is not None and os.path.getmtime(out_path) < request_created_at - 1:
        return {"ok": False, "reason": "out_path older than the bake request (stale prior bake) — fail-closed"}
    sha = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
    return {"ok": True, "path": out_path, "sha256": sha, "bytes": b, "width": dims[0], "height": dims[1]}

def verify_existing_png(out_path, min_bytes=500000, aspect=None, request_created_at=None, transcript=None,
                        allow_no_transcript=False):
    """SHARED verifier (contract-v2 §4). Verify the EXPLICIT out_path; run a BEST-EFFORT denylist (the HARD-VETO)
    over the TRANSCRIPT ONLY (never the prompt — it legitimately mentions 'image'/'PNG'). The denylist targets the
    KNOWN codex-exec hand-draw fallback (struct/zlib/PIL/SVG/matplotlib); it is NOT a complete security boundary —
    the load-bearing faithfulness gate is the downstream cross-model blind-transcribe + content_diff. A clean
    sig/dims/size does NOT override a fallback marker. FAIL-CLOSED by default: a None/missing/empty transcript is
    rejected (the denylist would be INERT), unless allow_no_transcript=True restores the legacy permissive behavior.
    Returns {ok:True, path, sha256, bytes, width, height} or {ok:False, reason}."""
    # FAIL-CLOSED default: with no transcript to scan, the HARD-VETO denylist is INERT, so a code-drawn fallback PNG
    # with a clean sig+dims+size could sail through. Reject up front unless a legacy caller opts back in.
    if not transcript:
        if allow_no_transcript:
            return _verify_png_bytes(out_path, min_bytes, aspect, request_created_at)
        return {"ok": False, "reason": "empty/missing transcript — HARD-VETO inert, fail-closed"}
    # B-CONTRACT defense-in-depth: a GIVEN transcript path that resolves to missing/whitespace-only content also
    # leaves the HARD-VETO scan INERT — fail-closed rather than silently accept.
    if not os.path.exists(transcript) or not open(transcript, errors="ignore").read().strip():
        return {"ok": False, "reason": "empty/missing transcript — HARD-VETO inert, fail-closed"}
    # BLOCKER-central: if the transcript is a JSON status dict (the agent's <png>.bakestatus.json carries
    # status + raw mcp_output), require mcp_output to be a NON-EMPTY string — an ok status whose mcp_output is
    # missing/empty/non-string makes the HARD-VETO scan vacuous (nothing to denylist), so fail-closed. A NON-JSON
    # transcript (a plain log) skips this check so the regex-denylist path still applies on its own.
    try:
        _tx_obj = json.loads(open(transcript, errors="ignore").read())
    except (ValueError, OSError):
        _tx_obj = None
    if isinstance(_tx_obj, dict) and "status" in _tx_obj:
        _m = _tx_obj.get("mcp_output")
        if not isinstance(_m, str) or not _m.strip():
            return {"ok": False, "reason": "bakestatus mcp_output missing/empty/non-string — HARD-VETO inert, fail-closed"}
    hits = _veto_hits(transcript)
    if hits:
        return {"ok": False, "reason": f"non-native fallback markers (HARD-VETO): {hits}"}
    return _verify_png_bytes(out_path, min_bytes, aspect, request_created_at)

def _status_path(out_path):
    return out_path + ".bakestatus.json"

def emit_bake_request(out_path, req):
    """Atomically write <out_path>.bakereq.json; pre-delete a stale out_path + status so a prior bake
    can't be silently reused (contract-v2 §3(i)). GENERATE a per-request nonce (uuid4 hex), stamp it into the
    bakereq.json payload as request_id, and RETURN it so the caller can require the matching id back in the
    bakestatus — a stale/foreign bake (mismatched id) is then fail-closed at pickup (--request-id)."""
    request_id = uuid.uuid4().hex
    req["request_id"] = request_id
    for p in (out_path, _status_path(out_path)):
        try: os.remove(p)
        except OSError: pass
    tmp = out_path + ".bakereq.json.tmp"
    with open(tmp, "w") as f:
        json.dump(req, f)
    os.replace(tmp, out_path + ".bakereq.json")
    return request_id

def await_bake_status(out_path, timeout):
    """Poll <out_path>.bakestatus.json until it appears or timeout; return the parsed dict or {} on timeout.
    BLOCKER: return the parsed JSON ONLY when it is a dict — a non-dict payload (scalar/list/null, or a half-written
    file) is treated as NOT-READY (keep polling), so a malformed status file can never become a non-dict that a later
    status.get(...) would crash on. {} on timeout (callers' status.get(...) stays safe)."""
    sp = _status_path(out_path); deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(sp):
            try:
                obj = json.load(open(sp))
                if isinstance(obj, dict):
                    return obj
            except (ValueError, OSError): pass
        time.sleep(2)
    return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-existing", action="store_true",
                    help="PRIMARY mode (default): verify the EXPLICIT --out path (no glob, no marker) — the contract-v2 agent-seam verifier")
    ap.add_argument("--created-at", type=float,
                    help="request epoch; in --out-existing mode require mtime(out) >= this (rejects a stale prior bake)")
    ap.add_argument("--transcript", help="agent bakestatus/bakelog scanned for non-native fallback markers (HARD-VETO)")
    ap.add_argument("--request-id", help="expected bake nonce (emit_bake_request's uuid4 hex); in --out-existing mode the "
                    "transcript MUST parse to a JSON bakestatus DICT whose request_id == this, else fail-closed "
                    "(non-dict/plain-log/list or missing/mismatched id all rejected — stale/foreign bake)")
    ap.add_argument("--marker", type=float, help="LEGACY (exec path only): epoch; accept files with mtime >= this")
    ap.add_argument("--legacy-marker-glob", action="store_true",
                    help="LEGACY: newest-PNG-after-marker glob over --dir (exec/CI only; default is --out-existing)")
    ap.add_argument("--min-bytes", type=int, default=500000)
    ap.add_argument("--dir", default=os.path.expanduser("~/.codex/generated_images"))
    ap.add_argument("--log", help="LEGACY: the codex bake log scanned for a non-native fallback (use --transcript in agent mode)")
    ap.add_argument("--aspect", type=float, help="expected width/height (e.g. blueprint W/H); rejects a wildly off-aspect image")
    a = ap.parse_args()
    if not a.out_existing and not a.legacy_marker_glob:
        a.out_existing = True   # default to the explicit-out verifier
    if a.legacy_marker_glob and a.marker is None:
        print(json.dumps({"ok": False, "reason": "--legacy-marker-glob requires --marker"}), file=sys.stderr); sys.exit(2)

    # PRIMARY (contract-v2): verify the EXPLICIT out_path the agent's mcp__codex__codex bake wrote.
    if a.out_existing:
        # B-CONTRACT (pickup side): the HARD-VETO scans the agent transcript (status file's mcp_output) for
        # struct/zlib/PIL/SVG/matplotlib traces of a hand-drawn fallback. If the transcript is absent, missing,
        # or whitespace-only, the veto is INERT — a code-drawn PNG with a clean sig+dims+size would sail through.
        # Fail-closed BEFORE accepting the PNG: require a present, non-whitespace transcript in --out-existing mode.
        tx = a.transcript or a.log
        if not tx or not os.path.exists(tx) or not open(tx, errors="ignore").read().strip():
            print(json.dumps({"ok": False, "reason": "empty/missing transcript — HARD-VETO inert, fail-closed"},
                             ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
        # NONCE fail-closed (--request-id): when an expected request_id was supplied, the transcript MUST parse to a
        # JSON bakestatus DICT whose request_id == it — otherwise fail-closed BEFORE accepting the PNG. Opting into
        # --request-id is opting into nonce enforcement, so a NON-JSON (plain-log) or JSON-list transcript (which
        # carries no addressable request_id, leaving the nonce check INERT) is itself rejected — NOT silently passed:
        # a fresh valid PNG with a wrong/absent nonce on such a transcript would otherwise be accepted (rc=0). Reject
        # on parse-failure, non-dict, OR missing/mismatched request_id. (The no-request-id path is untouched.)
        if a.request_id:
            try:
                _st = json.loads(open(tx, errors="ignore").read())
            except (ValueError, OSError):
                _st = None
            if not isinstance(_st, dict) or _st.get("request_id") != a.request_id:
                print(json.dumps({"ok": False, "reason": "bakestatus request_id mismatch/absent (non-dict or no match) — stale/foreign bake, fail-closed"},
                                 ensure_ascii=False), file=sys.stderr)
                sys.exit(1)
        res = verify_existing_png(a.out, a.min_bytes, a.aspect, a.created_at, tx)
        if res.get("ok"):
            res.setdefault("src", os.path.basename(a.out))
            print(json.dumps(res, ensure_ascii=False)); return 0
        print(json.dumps(res, ensure_ascii=False), file=sys.stderr); sys.exit(1)

    # LEGACY (exec/CI only): HARD-VETO scan + newest-PNG-after-marker glob over --dir, copied into --out.
    hits = _veto_hits(a.transcript or a.log)
    if hits:
        print(json.dumps({"ok": False, "reason": f"non-native fallback markers (HARD-VETO): {hits}"}), file=sys.stderr)
        sys.exit(1)
    cands = [p for p in glob.glob(os.path.join(os.path.expanduser(a.dir), "**", "*.png"), recursive=True)
             if os.path.getmtime(p) >= a.marker - 1]
    cands.sort(key=os.path.getmtime, reverse=True)
    for p in cands:
        b = os.path.getsize(p)
        if b < a.min_bytes:
            continue
        dims = png_dims(p)
        if not dims:
            continue
        if a.aspect:
            ar = dims[0] / dims[1]
            if not (0.6 * a.aspect <= ar <= 1.6 * a.aspect):
                continue   # wildly off the blueprint aspect → not our figure
        sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        shutil.copy(p, a.out)
        print(json.dumps({"ok": True, "path": a.out, "src": os.path.basename(p), "sha256": sha,
                          "bytes": b, "width": dims[0], "height": dims[1]}, ensure_ascii=False))
        return 0
    print(json.dumps({"ok": False, "reason": "no valid native PNG after marker (fail-closed)",
                      "checked": len(cands), "dir": a.dir, "min_bytes": a.min_bytes}), file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
