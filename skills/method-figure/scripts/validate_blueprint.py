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
    if not isinstance(cw, (int, float)) or not isinstance(ch, (int, float)) or cw <= 0 or ch <= 0:
        errs.append(f"canvas dimensions must be positive numbers (got {cw!r}x{ch!r})")
    nodes = bp.get("nodes", []); groups = bp.get("groups", []); edges = bp.get("edges", [])
    ids = [n.get("id") for n in nodes]
    if len(ids) != len(set(ids)): errs.append(f"duplicate node ids: {[i for i in ids if ids.count(i) > 1]}")
    gids = {g.get("id") for g in groups}
    if len(gids) != len([g.get('id') for g in groups]): errs.append("duplicate group ids")
    nodeset = set(ids)
    asset_ids = {a.get("id") for a in bp.get("assets", [])}
    # when Step-0 compiled this blueprint from a brief, EVERY object must trace back (GUARD-10).
    traced = bool(bp.get("compiled_from_brief"))
    for e in edges:
        if e.get("from") not in nodeset: errs.append(f"edge.from '{e.get('from')}' is not a node id")
        if e.get("to") not in nodeset: errs.append(f"edge.to '{e.get('to')}' is not a node id")
        if traced and not e.get("source"): errs.append(f"edge '{e.get('from')}->{e.get('to')}' missing 'source' (compiled_from_brief)")
    def in_canvas(x, y): return -2 <= x <= cw + 2 and -2 <= y <= ch + 2
    for n in nodes:
        if "label_exact" not in n and "label" not in n: errs.append(f"node '{n.get('id')}' has no label_exact")
        p = n.get("pos") or {}; s = n.get("size") or {}
        if "x" in p and "y" in p:
            w = s.get("w", 0); h = s.get("h", 0)
            if not (in_canvas(p["x"] - w / 2, p["y"] - h / 2) and in_canvas(p["x"] + w / 2, p["y"] + h / 2)):
                errs.append(f"node '{n.get('id')}' box (pos {p}, size {s}) extends outside canvas {cw}x{ch}")
        if n.get("group") and n["group"] not in gids: errs.append(f"node '{n.get('id')}' group '{n['group']}' undefined")
        # asset_ref integrity — checked PER NODE (this block was previously misplaced in the callouts loop,
        # so it only ever saw the last node and never actually validated a character anchor).
        if n.get("asset_ref") and n["asset_ref"] not in asset_ids:
            errs.append(f"node '{n.get('id')}' asset_ref '{n['asset_ref']}' not in assets[]")
        if traced and not n.get("source"): errs.append(f"node '{n.get('id')}' missing 'source' (compiled_from_brief)")
    for g in groups:
        if traced and not g.get("source"): errs.append(f"group '{g.get('id')}' missing 'source' (compiled_from_brief)")
        b = g.get("bounds") or {}
        if not (in_canvas(b.get("x", 0), b.get("y", 0)) and in_canvas(b.get("x", 0) + b.get("w", 0), b.get("y", 0) + b.get("h", 0))):
            errs.append(f"group '{g.get('id')}' bounds {b} outside canvas {cw}x{ch}")
    callout_boxes = []
    for c in bp.get("callouts", []):
        p = c.get("pos") or {}; s = c.get("size") or {}
        if "x" in p and "y" in p:
            w = s.get("w", 0); h = s.get("h", 0)
            if not (in_canvas(p["x"] - w / 2, p["y"] - h / 2) and in_canvas(p["x"] + w / 2, p["y"] + h / 2)):
                errs.append(f"callout '{c.get('id')}' box (pos {p}, size {s}) extends outside canvas {cw}x{ch}")
            if w and h: callout_boxes.append((c.get("id"), p["x"] - w / 2, p["y"] - h / 2, p["x"] + w / 2, p["y"] + h / 2))
        if traced and not c.get("source"): errs.append(f"callout '{c.get('id')}' missing 'source' (compiled_from_brief)")
    # callouts must not overlap each other (the default-stack bug)
    for i in range(len(callout_boxes)):
        for j in range(i + 1, len(callout_boxes)):
            a, b = callout_boxes[i], callout_boxes[j]
            if a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4]:
                errs.append(f"callouts '{a[0]}' and '{b[0]}' overlap (each callout needs its own band slot)")
    for a in bp.get("assets", []):
        if traced and not a.get("source"): errs.append(f"asset '{a.get('id')}' missing 'source' (compiled_from_brief)")
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
