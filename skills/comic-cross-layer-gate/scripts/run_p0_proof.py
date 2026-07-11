#!/usr/bin/env python3
"""run_p0_proof.py — deterministic MINTER/VERIFIER for the p0_proof spending gate (pure stdlib).

Mints the ONE artifact run_comic.py's spending preflight accepts (a decision:p0_proof_* wiki node) — and
ONLY after verifying, fail-closed, that the agent-driven cross-model fan-out actually acquitted THIS
comic.json (same-digest PASS) under THIS resolved spend plan (bakereq/v1 digest). It NEVER runs a reviewer
itself: the agent fan-out produces the review JSONs; this script only checks them and mints the certificate,
so the certificate is deterministic and auditable while the reviewing stays cross-model.

FAIL-CLOSED contract (every violation → clear stderr reason + exit 1):
  • comic_sha     = sha256 of the project comic.json BYTES — the cert binds to the exact compiled version;
  • bake_plan_sha = pickup_image.bake_plan_digest(run_comic.get_bake_plan(args)) — binds the resolved spend
    plan (contract bakereq/v1: model/effort/include_image_gen_tool/sandbox/min_bytes/aspect/bake_timeout);
    pass --min-bytes/--bake-timeout to mint a cert matching a NON-default audited run;
  • a COUNTED review = a JSON dict with family ∈ {openai, google, anthropic}, blockers == [], an affirmative
    verdict (pass/clean/approve/advance), AND review.comic_sha == the computed comic_sha (a review of a
    DIFFERENT comic.json version does NOT count);
  • quorum = BOTH non-author families {openai, google} among the counted reviews; --author-family declares
    who DROVE the run (default anthropic) — a quorum-family author is REFUSED outright (it can drive, never
    acquit); a missing/unparseable/timeout review simply does not count — NEVER proceed on timeout.

Usage:
  python3 run_p0_proof.py --project examples/comic_m3_audit --target decision:compile_r1 \
      --reviews p0_codex.json p0_gemini.json [--min-bytes 500000] [--bake-timeout 600] [--author-family anthropic]
The comic file is ALWAYS <project>/comic.json and the cert ALWAYS lands in <project>/wiki/nodes — neither is
overridable (an elsewhere-minted cert is one the consumer's preflight never sees). On success: atomically
writes wiki/nodes/decision_p0_proof_<comicid-slug>_<utcstamp>.json, prints the node JSON to stdout, exits 0.
"""
import argparse, hashlib, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE.rsplit("/skills/", 1)[0]
# same rsplit sys.path recipe run_comic.py uses for pickup_image (contract-v2 §0a): both shared helpers are
# IMPORTED, never inlined — an inlined digest copy re-introduces the cross-engine drift the contract kills.
sys.path.insert(0, ROOT + "/skills/method-figure/scripts")
sys.path.insert(0, ROOT + "/skills/comic-director/scripts")

FAMILIES = ("openai", "google", "anthropic")
QUORUM = {"openai", "google"}      # the two non-author families; the Claude author can never self-acquit
AFFIRM = {"pass", "clean", "approve", "advance"}

def die(reason):
    print(f"FAIL-CLOSED: {reason}", file=sys.stderr); sys.exit(1)

def load_review(path):
    """Parse one fan-out review file → (dict, None) or (None, why it does not count)."""
    if not os.path.isfile(path): return None, "file missing (reviewer timeout/skip?) — never counts"
    try:
        obj = json.loads(open(path, encoding="utf-8", errors="ignore").read())
    except ValueError as e:
        return None, f"unparseable JSON ({e}) — never counts"
    if not isinstance(obj, dict): return None, "not a JSON dict — never counts"
    return obj, None

def uncounted_reason(rv, comic_sha):
    """Why this PARSED review does NOT count toward quorum (None = it counts)."""
    if str(rv.get("family", "")).lower() not in FAMILIES:
        return f"family {rv.get('family')!r} not in {FAMILIES}"
    if rv.get("blockers") != []:
        return f"blockers not the empty list: {rv.get('blockers')!r}"
    if str(rv.get("verdict", "")).lower() not in AFFIRM:
        return f"verdict {rv.get('verdict')!r} not affirmative {sorted(AFFIRM)}"
    if rv.get("comic_sha") != comic_sha:
        return "comic_sha mismatch — this review acquitted a DIFFERENT comic.json version (same-digest PASS required)"
    return None

def main():
    ap = argparse.ArgumentParser(description="mint/verify the decision:p0_proof_* spending certificate (fail-closed)")
    ap.add_argument("--project", required=True, help="project dir (must contain comic.json + wiki/nodes/)")
    ap.add_argument("--target", required=True, help="target_node_id the certificate points at (the compile/intent anchor)")
    ap.add_argument("--reviews", required=True, nargs="+", help=">=2 review JSONs from the agent-driven cross-model fan-out")
    # plan passthrough — PARITY: these defaults MUST equal run_comic.py's argparse defaults (--min-bytes 500000,
    # --bake-timeout 600). Drift here mints certs the default consumer preflight rejects — or worse, accepts wrongly.
    ap.add_argument("--min-bytes", type=int, default=500000, help="the run_comic --min-bytes this cert certifies")
    ap.add_argument("--bake-timeout", type=int, default=600, help="the run_comic --bake-timeout this cert certifies")
    ap.add_argument("--author-family", choices=list(FAMILIES), default="anthropic",
                    help="model family driving this run — must stay OUTSIDE the acquittal quorum")
    a = ap.parse_args()

    if a.author_family in QUORUM:
        die(f"--author-family {a.author_family!r}: the author family cannot participate in its own acquittal — "
            "this pipeline currently requires a non-quorum author, e.g. anthropic; a third-family quorum option is planned")

    proj = os.path.abspath(a.project)
    if not os.path.isdir(proj): die(f"--project is not a directory: {proj}")
    comic_path = os.path.join(proj, "comic.json")     # fixed name — the exact file the consumer preflight digests
    if not os.path.isfile(comic_path): die(f"comic.json missing: {comic_path}")
    out_dir = os.path.join(proj, "wiki", "nodes")     # fixed dir — the ONLY dir _p0_clean scans (no override)
    # the preflight (_p0_clean) only scans the project's wiki/nodes — a cert minted into a non-existent dir
    # would be invisible to it, so require the dir up front rather than silently creating one elsewhere.
    if not os.path.isdir(out_dir): die(f"node dir missing (the certificate would land where no preflight looks): {out_dir}")
    if len(a.reviews) < 2: die(f"need >=2 review files, got {len(a.reviews)}")

    # (a) bind to the exact comic.json BYTES: same-digest PASS — reviews of any other version never count.
    comic_bytes = open(comic_path, "rb").read()
    comic_sha = hashlib.sha256(comic_bytes).hexdigest()
    try:
        comic_id = str(json.loads(comic_bytes.decode("utf-8", errors="ignore")).get("comic_id") or "")
    except ValueError:
        comic_id = ""
    if not comic_id: die(f"comic_id missing/unparseable in {comic_path} — cannot derive the certificate slug")
    slug = re.sub(r"[^a-z0-9_-]+", "_", comic_id.lower())

    # (b) bind to the RESOLVED spend plan (contract bakereq/v1). Both helpers are the shared single source of
    # truth; a missing/renamed helper or a non-bakereq/v1 plan is a broken contract → fail-closed, no default.
    try:
        from pickup_image import bake_plan_digest
        from run_comic import get_bake_plan
        plan = get_bake_plan(a)   # the argparse namespace IS the args-like object (min_bytes/bake_timeout)
    except Exception as e:
        die(f"cannot resolve the spend plan (pickup_image.bake_plan_digest / run_comic.get_bake_plan): {e}")
    if not isinstance(plan, dict) or plan.get("contract") != "bakereq/v1":
        die(f"run_comic.get_bake_plan() returned a non-bakereq/v1 plan: {plan!r}")
    bake_plan_sha = bake_plan_digest(plan)

    # (c) quorum: BOTH of {openai, google} among the counted reviews; every uncounted file is only noted.
    counted, families = [], set()
    for path in dict.fromkeys(a.reviews):   # dedupe exact paths; distinct families come from the set below
        rv, why = load_review(path)
        if rv is not None: why = uncounted_reason(rv, comic_sha)
        if why:
            print(f"[p0_proof] NOT counted {os.path.basename(path)}: {why}", file=sys.stderr); continue
        counted.append(os.path.basename(path)); families.add(str(rv["family"]).lower())
    if not QUORUM <= families:
        die(f"quorum unmet — counted families {sorted(families)} lack {sorted(QUORUM - families)}; "
            "a missing/unparseable/timeout review never counts (NEVER proceed on timeout)")

    # (d) mint: atomic tmp + os.replace (the emit_bake_request recipe) so a crash never leaves a half cert.
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    node = {"node_id": f"decision:p0_proof_{slug}_{stamp}", "node_type": "decision", "status": "final",
            "title": f"p0_proof gate {comic_id} → advance",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
            "payload": {"gate_kind": "p0_proof", "verdict": "advance", "target_node_id": a.target,
                        "comic_sha": comic_sha, "bake_plan_sha": bake_plan_sha,
                        "reviewer_quorum": sorted(families), "review_files": counted}}
    out_path = os.path.join(out_dir, f"decision_p0_proof_{slug}_{stamp}.json")
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(node, f, ensure_ascii=False, indent=1)
    os.replace(tmp, out_path)
    print(json.dumps(node, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
