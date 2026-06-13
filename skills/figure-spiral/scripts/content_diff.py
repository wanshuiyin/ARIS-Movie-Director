#!/usr/bin/env python3
"""content_diff.py — deterministic content-accuracy diff: blueprint EXPECTED vs panel OBSERVED (pure stdlib).

The reviewer panel BLIND-transcribes what they actually see (observed_tokens, observed_edges, anomalies)
WITHOUT being shown the expected labels — this script then diffs their transcription against the blueprint's
LOCKED `*_exact` text and `expected_tokens`. This is what catches image-model drift (a garbled token, a
renamed phase, a reversed/invented edge, a floating pasted-looking label) objectively, instead of a
reviewer's subjective "looks fine". Empty diff == content-accurate.

Usage:  python3 content_diff.py blueprint.json review.cc.json review.gemini.json review.codex.json
Each review JSON: {observed_tokens:[...], observed_edges:[{from_label,to_label,direction}], anomalies:[...]}
Prints a JSON report and exits non-zero if the diff is non-empty.
"""
import json, sys, re

def norm(s):
    return re.sub(r"\s+", " ", str(s).strip().lower())

def coarse_tokens(strings):
    """token set from a list of observed strings — keep code-ish tokens (comic.json, +6.2) whole + word parts."""
    c = set()
    for s in strings or []:
        t = norm(s)
        for m in re.findall(r"[a-z0-9_.+|/-]+", t): c.add(m)
        for w in re.findall(r"[a-z0-9]+", t): c.add(w)
    return c

def main():
    bp = json.load(open(sys.argv[1], encoding="utf-8"))
    reviews = [json.load(open(p, encoding="utf-8")) for p in sys.argv[2:]]
    # the VISUAL reviewers (anyone who returned observed_tokens) — both must have read a token for it to count
    visual = [r for r in reviews if isinstance(r.get("observed_tokens"), list)]
    token_sets = [coarse_tokens(r.get("observed_tokens")) for r in visual]

    # 1) every blueprint expected_token / label_exact must be read by EVERY visual reviewer
    expected = set()
    def add(s):
        for m in re.findall(r"[a-z0-9_.+|/-]+", norm(s)):
            if m: expected.add(m)
    for n in bp.get("nodes", []):
        add(n.get("label_exact") or n.get("label", ""))
        for tk in n.get("expected_tokens", []): add(tk)
    for g in bp.get("groups", []): add(g.get("label_exact", ""))
    for e in bp.get("edges", []):
        add(e.get("label_exact", ""))
        for tk in e.get("expected_tokens", []): add(tk)
    for c in bp.get("callouts", []):
        add(c.get("title_exact", ""));
        for tk in c.get("expected_tokens", []): add(tk)
    expected.discard("")
    missing = sorted(t for t in expected if not all(t in ts for ts in token_sets)) if token_sets else sorted(expected)

    # 2) edges: blueprint forward edges should be observed in the right direction (best-effort, by endpoint labels)
    def lbl(nid):
        for n in bp.get("nodes", []):
            if n.get("id") == nid: return norm(n.get("label_exact") or n.get("label", ""))
        return nid
    bp_edges = {(lbl(e["from"]), lbl(e["to"])) for e in bp.get("edges", []) if e.get("must_render", True)}
    obs_edges = set()
    for r in visual:
        for oe in r.get("observed_edges", []) or []:
            obs_edges.add((norm(oe.get("from_label", "")), norm(oe.get("to_label", ""))))
    # an expected edge is "wrong" if neither its forward nor any reviewer saw it (only flag when reviewers gave edges)
    wrong_edges = sorted([f"{a} -> {b}" for (a, b) in bp_edges if obs_edges and (a, b) not in obs_edges]) if obs_edges else []

    # 3) anomalies (Negative Space Audit) — anything any reviewer flagged as not-belonging
    anomalies = sorted({norm(a) for r in reviews for a in (r.get("anomalies") or []) if a})

    report = {"missing_tokens": missing, "wrong_edges": wrong_edges, "anomalies": anomalies,
              "visual_reviewers": len(visual), "content_accurate": not (missing or wrong_edges or anomalies)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["content_accurate"] else 1)

if __name__ == "__main__":
    main()
