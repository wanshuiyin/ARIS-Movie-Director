#!/usr/bin/env python3
"""content_diff.py — deterministic content-accuracy diff: blueprint EXPECTED vs panel OBSERVED (pure stdlib).

Reviewers BLIND-transcribe what they see (observed_tokens / observed_edges / anomalies) WITHOUT being shown
the expected labels; this script diffs that against the blueprint's LOCKED text. Empty diff == content-accurate.

HARD vetoes (any one fails acceptance):
  - missing_tokens : a locked token (from label_exact / desc_exact / lines_exact / rail / expected_tokens)
                     that was NOT read by EVERY visual reviewer.  (catches dropped / garbled text)
  - unaccounted_numeric : a NUMBER/code token EVERY visual reviewer read that the blueprint never declared.
                     (a figure must not state a number the brief never authored — the unsourced-number veto)
  - forbidden_present : a DELETE-list term (a competing/wrong name) that ANY reviewer read anywhere.
  - wrong_edges : an expected arrow that EVERY reviewer saw REVERSED (and none forward) = wrong direction.
  - anomalies : the Negative-Space-Audit items any reviewer flagged (floating/pasted labels, artifacts).
Informational (flagged, not a veto): word-level unaccounted_tokens (a legit paraphrase must not false-veto).

Usage:  python3 content_diff.py blueprint.json review1.json review2.json [review3.json ...]
Prints a JSON report; exits non-zero if not content_accurate.
"""
import json, sys, re

TOKEN_RE = re.compile(r"[a-z0-9_.+|/-]+")

def keep_token(t):
    """meaningful tokens only — drop pure punctuation / single chars / bare digits / structure numbers."""
    t = t.strip(".,;:()[]{}\"'")
    if len(t) <= 1: return False
    if t.isdigit(): return False                       # "1","2" phase numbers, bare counts
    if not re.search(r"[a-z]", t): return False        # must contain a letter (keeps comic.json, panel_gate, content-svg; drops "+6", "6.25"? -> see keepnum)
    return True

def keep_numeric(t):
    """keep meaningful numeric/code tokens like +6.2, +6.25, 24h (they carry the audit point)."""
    t = t.strip(".,;:()[]{}\"'")
    return bool(re.fullmatch(r"[+-]?\d[\d.]*[a-z]*", t)) and any(c.isdigit() for c in t) and len(t) >= 2

def tokenize(strings):
    out = set()
    for s in strings or []:
        for m in TOKEN_RE.findall(str(s).lower()):
            if keep_token(m) or keep_numeric(m):
                out.add(m)
    return out

def main():
    bp = json.load(open(sys.argv[1], encoding="utf-8"))
    reviews = [json.load(open(p, encoding="utf-8")) for p in sys.argv[2:]]
    visual = [r for r in reviews if isinstance(r.get("observed_tokens"), list)]
    if not visual:
        print(json.dumps({"error": "no visual reviewer returned observed_tokens"})); sys.exit(2)
    obs_sets = [tokenize(r.get("observed_tokens")) for r in visual]

    # EXPECTED = all locked text: node label_exact + desc_exact, group label_exact, edge label_exact,
    # callout title_exact + lines_exact, rail label_exact, plus explicit expected_tokens.
    exp_strings = []
    for n in bp.get("nodes", []):
        exp_strings += [n.get("label_exact", n.get("label", "")), n.get("desc_exact", n.get("desc", ""))]
        exp_strings += n.get("expected_tokens", [])
    for g in bp.get("groups", []): exp_strings.append(g.get("label_exact", g.get("label", "")))
    for e in bp.get("edges", []):
        exp_strings.append(e.get("label_exact", e.get("label", ""))); exp_strings += e.get("expected_tokens", [])
    for c in bp.get("callouts", []):
        exp_strings.append(c.get("title_exact", c.get("title", ""))); exp_strings += c.get("lines_exact", c.get("lines", []))
        exp_strings += c.get("expected_tokens", [])
    exp_strings.append((bp.get("rail", {}) or {}).get("label_exact", (bp.get("rail", {}) or {}).get("label", "")))
    expected = tokenize(exp_strings)

    # missing: a locked token not read by EVERY visual reviewer (no union — both must read it)
    missing = sorted(t for t in expected if not all(t in s for s in obs_sets))
    # unaccounted: a token read by EVERY visual reviewer that the blueprint never declared (hallucinated text)
    common_observed = set.intersection(*obs_sets) if obs_sets else set()
    unaccounted = sorted(t for t in common_observed if t not in expected)
    # a hallucinated NUMBER/code token (read by both, authored by none) is a HARD veto — a figure must not state
    # a number the brief never authored (the analogue of the comic's expected_literals contract).
    unaccounted_numeric = sorted(t for t in unaccounted if keep_numeric(t))
    # forbidden DELETE-list (a competing/wrong name): veto if ANY reviewer read it anywhere (union — stricter).
    forbidden = tokenize(bp.get("forbidden_tokens", []))
    obs_union = set().union(*obs_sets) if obs_sets else set()
    forbidden_present = sorted(t for t in forbidden if t in obs_union)
    # edge topology: an expected arrow that EVERY reviewer saw REVERSED (and none forward) = wrong direction → veto.
    # conservative: exact normalized-label match only fires on a clear both-reviewer reversal, so a transcription gap
    # can't false-veto; a merely missing arrow stays informational (reviewers don't always transcribe every edge).
    nlabel = lambda s: re.sub(r"\s+", " ", str(s or "").strip().lower())
    id2label = {n.get("id"): nlabel(n.get("label_exact", n.get("label", ""))) for n in bp.get("nodes", [])}
    exp_edges = set()
    for e in bp.get("edges", []):
        s, d = id2label.get(e.get("from", e.get("src"))), id2label.get(e.get("to", e.get("dst")))
        if s and d: exp_edges.add((s, d))
    def obs_edge_set(r):
        out = set()
        for e in (r.get("observed_edges") or []):
            if isinstance(e, dict):
                f, t = nlabel(e.get("from_label", "")), nlabel(e.get("to_label", ""))
                if f and t: out.add((f, t))
        return out
    oe = [obs_edge_set(r) for r in visual]
    wrong_edges = sorted(f"{a} -> {b} (seen reversed)" for (a, b) in exp_edges
                         if oe and all((b, a) in s for s in oe) and not any((a, b) in s for s in oe))
    # anomalies (Negative-Space Audit) — union across all reviewers
    anomalies = sorted({str(a).strip().lower() for r in reviews for a in (r.get("anomalies") or []) if a})

    # HARD vetoes; word-level unaccounted stays informational (a legit paraphrase must not false-veto).
    accurate = not (missing or anomalies or forbidden_present or unaccounted_numeric or wrong_edges)
    report = {"missing_tokens": missing, "unaccounted_tokens": unaccounted,
              "unaccounted_numeric": unaccounted_numeric, "forbidden_present": forbidden_present,
              "wrong_edges": wrong_edges, "anomalies": anomalies,
              "visual_reviewers": len(visual), "content_accurate": accurate,
              "note": "HARD vetoes: missing / anomalies / forbidden_present / unaccounted_numeric / wrong_edges; word-level unaccounted is informational"}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if accurate else 1)

if __name__ == "__main__":
    main()
