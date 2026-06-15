#!/usr/bin/env python3
"""Deterministic gate regression tests — pure stdlib; NO image_gen / Chrome / network / credentials.

These lock the cross-model-audited gate guarantees so a future edit can't silently re-open a fail-open hole:
  - content_diff.py hard vetoes (hallucinated number / forbidden token / reversed edge) + clean pass
  - compile_brief.py --strict fail-closed on a bad enum
  - validate_wiki.py --strict-author-gates flags a bare-locked author node (and default still passes)
  - the comic literal-diff exactness contract (a wrong timestamp must NOT satisfy the expected one)

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

print()
if fails:
    print(f"❌ {len(fails)} gate test(s) FAILED: {fails}")
    sys.exit(1)
print("✅ all deterministic gate tests passed")
