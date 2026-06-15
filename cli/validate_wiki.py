#!/usr/bin/env python3
"""validate_wiki.py — check a project's wiki nodes against schemas/node_schema.json (pure stdlib).

Catches the drift a hand-written validation_report can't: unknown node_type/status, missing required
fields, malformed JSON, malformed edges, dangling edge endpoints, bad node_id form, and absolute-path
privacy leaks (recursively). Exits non-zero on any failure so CI / a release gate can enforce it.

Usage:  python3 cli/validate_wiki.py <project_dir>      # e.g. examples/comic_m3_audit
        python3 cli/validate_wiki.py                    # defaults to the repo root
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "node_schema.json"

# Per-node-type payload invariants (the fields ALWAYS written for each node type). MUST mirror the
# schemas/node_schema.json oneOf branches (a drift guard below fails the run if they diverge).
PAYLOAD_REQUIRED = {
    # --- Phase 2/3 RUNTIME types (kept EXACTLY — the existing 198-node trace satisfies these;
    #     new fields like acceptance_stage stay OPTIONAL until the engine upgrade writes them) ---
    "panel_attempt": ["source_panel_id", "image_path", "attempt_index"],
    "review":        ["target_node_id", "reviewer", "gate_kind"],
    "decision":      ["target_node_id", "verdict", "gate_kind"],
    "failure_mode":  ["layer", "affected_shot_ids", "active"],
    # --- Phase 1 AUTHOR types (new; mirror schemas/node_schema.json oneOf — keep in sync) ---
    "intent_spec":   ["raw_input_refs", "user_goal", "audience", "format", "constraints", "subjects",
                      "source_skeleton", "dual_identity", "uncertainties", "confidence"],
    "style_anchor":  ["dimension", "value", "source", "locked"],
    "outline_spec":  ["source_intent_id", "title", "logline", "tagline", "design_constraint",
                      "target_page_count", "narrative_beats", "beat_table", "motif_arcs",
                      "character_asset_ids", "scene_asset_ids", "prop_asset_ids", "global_style_bible", "budget"],
    "asset":         ["asset_kind", "name", "visual_description", "identity_lock", "ref_requirements",
                      "review_status", "version"],
    "storyboard_spec": ["source_outline_id", "page_order", "page_ids", "panel_ids", "global_policies",
                        "motif_ledger_id", "consolidated_asset_requests"],
    "panel_spec":    ["source_storyboard_id", "page_id", "panel_id", "sequence_index", "page_type", "world",
                      "asset_ids", "text_mode", "expected_literals", "content_blueprint", "bubbles",
                      "side_narration", "motifs"],
    "blueprint":     ["source_panel_id", "content_svg", "expected_literals", "safe_zones", "html_bubbles",
                      "crop", "negative_space_policy", "generator_script", "file_sha256"],
    "prompt_bundle": ["source_panel_id", "source_blueprint_id", "style_prefix", "composed_prompt",
                      "banned_vocab_scan", "identity_ref_paths"],
    "motif_ledger":  ["source_storyboard_id", "columns", "rows", "invariants", "mirror_locks"],
    "continuity_constraint": ["family", "constraint_text", "applies_to_panel_ids", "source_node_id", "active"],
}
AUTHOR_TYPES = {"intent_spec", "style_anchor", "outline_spec", "asset", "storyboard_spec", "panel_spec",
                "blueprint", "prompt_bundle", "motif_ledger", "continuity_constraint"}  # Phase-1 author layer

EDGE_TYPES = {  # wiki/edges.jsonl vocabulary (src/dst/type)
    "attempt_of", "reviews", "decides", "failure_of", "rollback_of", "supersedes",          # runtime
    "derived_from", "plans_asset", "uses_asset", "uses_style_anchor", "uses_blueprint",      # author layer
    "uses_motif_ledger", "produced_by_image2", "reviewed_by", "violates_continuity", "anchors_continuity",
}


def abs_path_leaks(obj, path="payload"):
    """Recursively yield (json-path, value) for any string holding an absolute home path — a release
    blocker even when nested in a list/sub-object (the old check only saw the first level)."""
    if isinstance(obj, str):
        if "/Users/" in obj or "/home/" in obj:
            yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from abs_path_leaks(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from abs_path_leaks(v, f"{path}[{i}]")


def main():
    _argv = sys.argv[1:]
    strict_author = "--strict-author-gates" in _argv   # opt-in: a locked author node must carry gate evidence
    _pos = [a for a in _argv if not a.startswith("--")]
    proj = Path(_pos[0]).resolve() if _pos else ROOT
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
    nid_pat = props.get("node_id", {}).get("pattern")
    nid_re = re.compile(nid_pat) if nid_pat else None

    errs = []
    # drift guard: the executable PAYLOAD_REQUIRED must cover exactly the schema's node_type enum
    for t in nt_enum - set(PAYLOAD_REQUIRED):
        errs.append(f"schema↔enforcer drift: node_type '{t}' in schema enum but has no PAYLOAD_REQUIRED entry")
    for t in set(PAYLOAD_REQUIRED) - nt_enum:
        errs.append(f"schema↔enforcer drift: PAYLOAD_REQUIRED has '{t}' not in schema node_type enum")

    n_nodes, node_ids, author_locked = 0, set(), []
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
        nid = d.get("node_id")
        if isinstance(nid, str):
            node_ids.add(nid)
            if nid_re and not nid_re.match(nid):
                errs.append(f"{f.name}: node_id '{nid}' does not match schema pattern")
        nt = d.get("node_type")
        if nt is not None and nt not in nt_enum:
            errs.append(f"{f.name}: node_type '{nt}' not in schema enum")
        st = d.get("status")
        if st is not None and st not in st_enum:
            errs.append(f"{f.name}: status '{st}' not in schema enum")
        if strict_author and nt in AUTHOR_TYPES and st == "locked" and isinstance(nid, str):
            author_locked.append((f.name, nid))
        payload = d.get("payload") or {}
        for pk in PAYLOAD_REQUIRED.get(nt, []):
            if pk not in payload:
                errs.append(f"{f.name}: payload missing '{pk}' (required for {nt})")
        # release-gate: NEVER persist an absolute home path anywhere in the payload (privacy leak), nested too
        for p, v in abs_path_leaks(payload):
            errs.append(f"{f.name}: {p} contains an absolute path (must be project-relative): {v[:60]}")

    # valid edge endpoints = wiki nodes ∪ comic.json panel anchors (panels[*].wiki_node_id). Panels are
    # first-class in comic.json (not wiki node files), and attempt_of/reviews edges legitimately point at them.
    valid_endpoints = set(node_ids)
    comic = proj / "comic.json"
    if comic.is_file():
        try:
            cj = json.loads(comic.read_text(encoding="utf-8"))
            for p in (cj.get("panels") or {}).values():
                w = (p or {}).get("wiki_node_id")
                if isinstance(w, str):
                    valid_endpoints.add(w)
        except Exception as e:
            errs.append(f"comic.json: unreadable for edge-endpoint resolution ({e})")

    n_edges = 0
    gate_targets = set()   # dst of decides/reviews edges — evidence a node went through a gate
    edges = proj / "wiki" / "edges.jsonl"
    if edges.is_file():
        for i, line in enumerate(edges.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            n_edges += 1
            try:
                e = json.loads(line)
            except Exception as ex:
                errs.append(f"edges.jsonl:{i}: invalid JSON ({ex})")
                continue
            if not all(k in e for k in ("src", "dst", "type")):
                errs.append(f"edges.jsonl:{i}: missing src/dst/type")
                continue
            if e["type"] not in EDGE_TYPES:
                errs.append(f"edges.jsonl:{i}: edge type '{e['type']}' not in {sorted(EDGE_TYPES)}")
            if e.get("type") in ("decides", "reviews"):
                gate_targets.add(e.get("dst"))
            for end in ("src", "dst"):
                if e[end] not in valid_endpoints:
                    errs.append(f"edges.jsonl:{i}: {end} '{e[end]}' has no matching node or comic.json panel anchor")

    if strict_author:
        for fname, nid in author_locked:
            if nid not in gate_targets:
                errs.append(f"{fname}: locked author node '{nid}' has no decides/reviews edge — "
                            f"locked without gate evidence (--strict-author-gates)")
        print(f"[validate_wiki] --strict-author-gates: audited {len(author_locked)} locked author node(s) for gate evidence")
    print(f"[validate_wiki] {proj.name}: {n_nodes} nodes, {n_edges} edges, schema={SCHEMA.name}")
    if errs:
        print(f"[validate_wiki] FAIL ({len(errs)} issue(s)):")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print("[validate_wiki] PASS — nodes conform (node_type/status enums, node_id form, payload invariants, "
          "no nested abs-path leaks); edges well-formed with resolved endpoints; schema↔enforcer in sync.")


if __name__ == "__main__":
    main()
