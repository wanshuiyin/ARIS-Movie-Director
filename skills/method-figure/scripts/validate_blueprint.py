#!/usr/bin/env python3
"""validate_blueprint.py — structural validation of a method-figure blueprint (pure stdlib).

Checks JSON Schema *shape* loosely (required top-level keys) plus the structural invariants a JSON Schema
can't easily express: unique node/group ids, every edge endpoint resolves, node/group bounds inside the
canvas, and no two LOCKED labels collide (which would make the hard-diff ambiguous). Exits non-zero on any
failure so it can gate the loop.  Usage:  python3 validate_blueprint.py blueprint.json
"""
import json, os, sys

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: validate_blueprint.py blueprint.json")
    bp = json.load(open(sys.argv[1], encoding="utf-8"))
    errs = []
    # real JSON-Schema validation when the lib is available (shape/enum/types/pattern); structural checks always run.
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schemas", "blueprint.schema.json")
    try:
        import jsonschema  # type: ignore
        if os.path.exists(schema_path):
            for e in sorted(jsonschema.Draft202012Validator(json.load(open(schema_path))).iter_errors(bp),
                            key=lambda e: list(e.path)):
                errs.append(f"schema: {'/'.join(map(str, e.path)) or '<root>'}: {e.message[:120]}")
    except ImportError:
        print("[validate_blueprint] note: jsonschema not installed — structural checks only")
    for k in ("version", "figure_id", "canvas", "render_policy", "nodes"):
        if k not in bp: errs.append(f"missing top-level key '{k}'")
    cw = (bp.get("canvas") or {}).get("width", 0); ch = (bp.get("canvas") or {}).get("height", 0)
    nodes = bp.get("nodes", []); groups = bp.get("groups", []); edges = bp.get("edges", [])
    ids = [n.get("id") for n in nodes]
    if len(ids) != len(set(ids)): errs.append(f"duplicate node ids: {[i for i in ids if ids.count(i) > 1]}")
    gids = {g.get("id") for g in groups}
    if len(gids) != len([g.get('id') for g in groups]): errs.append("duplicate group ids")
    nodeset = set(ids)
    for e in edges:
        if e.get("from") not in nodeset: errs.append(f"edge.from '{e.get('from')}' is not a node id")
        if e.get("to") not in nodeset: errs.append(f"edge.to '{e.get('to')}' is not a node id")
    def in_canvas(x, y): return -2 <= x <= cw + 2 and -2 <= y <= ch + 2
    for n in nodes:
        if "label_exact" not in n and "label" not in n: errs.append(f"node '{n.get('id')}' has no label_exact")
        p = n.get("pos") or {}; s = n.get("size") or {}
        if cw and ch and "x" in p and "y" in p:
            w = s.get("w", 0); h = s.get("h", 0)
            if not (in_canvas(p["x"] - w / 2, p["y"] - h / 2) and in_canvas(p["x"] + w / 2, p["y"] + h / 2)):
                errs.append(f"node '{n.get('id')}' box (pos {p}, size {s}) extends outside canvas {cw}x{ch}")
        if n.get("group") and n["group"] not in gids: errs.append(f"node '{n.get('id')}' group '{n['group']}' undefined")
    for g in groups:
        b = g.get("bounds") or {}
        if cw and ch and not (in_canvas(b.get("x", 0), b.get("y", 0)) and in_canvas(b.get("x", 0) + b.get("w", 0), b.get("y", 0) + b.get("h", 0))):
            errs.append(f"group '{g.get('id')}' bounds {b} outside canvas {cw}x{ch}")
    for c in bp.get("callouts", []):
        p = c.get("pos") or {}
        if cw and ch and "x" in p and "y" in p and not in_canvas(p["x"], p["y"]):
            errs.append(f"callout '{c.get('id')}' pos {p} outside canvas {cw}x{ch}")
        if n.get("asset_ref"):
            if n["asset_ref"] not in {a.get("id") for a in bp.get("assets", [])}:
                errs.append(f"node '{n.get('id')}' asset_ref '{n['asset_ref']}' not in assets[]")
    # locked-label collision (would make the blind-transcribe diff ambiguous)
    labels = [(n.get("label_exact") or n.get("label", "")).strip() for n in nodes]
    dup = sorted({l for l in labels if l and labels.count(l) > 1})
    if dup: errs.append(f"duplicate node label_exact (ambiguous for hard-diff): {dup}")
    lp = (bp.get("render_policy") or {}).get("label_policy", "baked")
    if lp not in ("baked", "hybrid", "overlay"): errs.append(f"render_policy.label_policy '{lp}' invalid")

    if errs:
        print(f"[validate_blueprint] FAIL ({len(errs)}):")
        for e in errs: print("  -", e)
        sys.exit(1)
    print(f"[validate_blueprint] PASS — {len(nodes)} nodes, {len(groups)} groups, {len(edges)} edges, "
          f"label_policy={lp}, canvas={cw}x{ch}")

if __name__ == "__main__":
    main()
