#!/usr/bin/env python3
"""validate_wiki.py — check a project's wiki nodes against schemas/node_schema.json (pure stdlib).

Catches the drift a hand-written validation_report can't: unknown node_type/status, missing required
fields, malformed JSON, and malformed edges. Exits non-zero on any failure so CI / a release gate can
enforce it. This is the reproducible check behind wiki/validation_report.md.

Usage:  python3 cli/validate_wiki.py <project_dir>      # e.g. examples/comic_m3_audit
        python3 cli/validate_wiki.py                    # defaults to the repo root
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "node_schema.json"


def main():
    proj = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT
    nodes_dir = proj / "wiki" / "nodes"
    if not SCHEMA.is_file():
        sys.exit(f"[validate_wiki] FATAL: schema missing: {SCHEMA}")
    if not nodes_dir.is_dir():
        sys.exit(f"[validate_wiki] FATAL: no wiki/nodes/ under {proj}")

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    props = schema.get("properties", {})
    required = schema.get("required", [])
    nt_enum = set(props.get("node_type", {}).get("enum", []))
    st_enum = set(props.get("status", {}).get("enum", []))

    errs, n_nodes = [], 0
    for f in sorted(nodes_dir.glob("*.json")):
        n_nodes += 1
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            errs.append(f"{f.name}: invalid JSON ({e})")
            continue
        for r in required:
            if r not in d:
                errs.append(f"{f.name}: missing required field '{r}'")
        nt = d.get("node_type")
        if nt is not None and nt not in nt_enum:
            errs.append(f"{f.name}: node_type '{nt}' not in schema enum")
        st = d.get("status")
        if st is not None and st not in st_enum:
            errs.append(f"{f.name}: status '{st}' not in schema enum")

    n_edges = 0
    edges = proj / "wiki" / "edges.jsonl"
    if edges.is_file():
        for i, line in enumerate(edges.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            n_edges += 1
            try:
                e = json.loads(line)
                if not all(k in e for k in ("src", "dst", "type")):
                    errs.append(f"edges.jsonl:{i}: missing src/dst/type")
            except Exception as ex:
                errs.append(f"edges.jsonl:{i}: invalid JSON ({ex})")

    print(f"[validate_wiki] {proj.name}: {n_nodes} nodes, {n_edges} edges, schema={SCHEMA.name}")
    if errs:
        print(f"[validate_wiki] FAIL ({len(errs)} issue(s)):")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print("[validate_wiki] PASS — every node conforms to node_schema (required fields + node_type/status enums); edges well-formed.")


if __name__ == "__main__":
    main()
