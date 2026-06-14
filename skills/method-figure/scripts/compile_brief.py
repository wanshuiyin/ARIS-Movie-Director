#!/usr/bin/env python3
"""compile_brief.py — Step-0: deterministically compile a method_figure_brief.json into a content-locked
blueprint.json (+ traceability.json). Pure stdlib, fail-closed.

This is the auto-Step-0 that makes method-figure single-input: the user feeds ONE ARIS-format artifact
(the brief that paper-plan emits after its claims_matrix); this compiler turns it into the blueprint the
spiral renders + cross-model verifies. It NEVER invents content — every blueprint object traces back to a
brief field (recorded in traceability.json), and a missing scientific number / claim / identity-trait /
component is a Refuse-and-Escalate (non-zero exit naming the field), not creative license (GUARD-10).

  CLI:  compile_brief.py brief.json --out blueprint.json --trace traceability.json [--strict|--no-strict]

Mapping (ADJ-4, verified against method_figure_brief.schema.json ↔ blueprint.schema.json):
  components[]  -> nodes[]      (label->label_exact, one_line->desc_exact, role->semantic_role,
                                 identity_ref->asset_ref, phase->group, visual_priority->size/weight)
  flows[]       -> edges[]      (from/to/kind/label->label_exact/direction)
  phases[]      -> groups[]     (auto-bounds enclose member nodes)
  identity_refs[]-> assets[]    (role=identity_sheet, traits->lock_traits)
  callouts[]    -> callouts[]   (+ a synthesized punchline from headline_claim/headline_number)
  symbol_registry[] -> the relevant node's expected_tokens (figure_symbol kept == paper_variable)
  forbidden_tokens -> blueprint top-level + every node's forbidden_tokens
  topology_constraint + visual_priority -> auto_layout() positions/sizes/canvas (no hand-placed coords)
  target_profile -> render_policy.target_profile (passed through EXPLICITLY — brief default 'paper' must
                    not silently fall to the blueprint default 'readme')
"""
import argparse
import json
import re
import sys
from pathlib import Path

# --- deterministic layout constants (the renderer refines; this only needs to be valid + readable) ---
SIZE_BY_PRIORITY = {            # (w, h) per visual_priority — core gets the most visual weight
    "core":       (250, 100),
    "primary":    (210, 78),
    "secondary":  (185, 66),
    "background": (155, 58),
}
DEFAULT_SIZE = SIZE_BY_PRIORITY["primary"]
TONE_CYCLE = ["blue", "peach", "green", "violet", "amber"]   # group tones, cycled by phase order
MARGIN = 120                    # canvas outer margin
TITLE_H = 70                    # reserved band at the top for the figure title
GROUP_LABEL_H = 46              # reserved band at the top of each phase group for its label
COL_GAP = 110                   # horizontal gap between columns/phases
V_GAP = 46                      # vertical gap between stacked nodes in a column
PAD = 30                        # padding between a group's bound and its member boxes

# shape heuristic: brief components carry no shape; derive deterministically from role/label keywords.
SHAPE_KEYWORDS = [
    ("character", ("mascot", "chibi", "persona", "researcher", "executor", "reviewer", "user", "human")),
    ("gate",      ("gate", "review", "audit", "panel", "check", "verify")),
    ("diamond",   ("verdict", "decision", "decide", "branch", "switch")),
    ("datastore", ("wiki", "memory", "store", "db", "database", "log", "cache", "buffer", "ledger")),
    ("document",  ("doc", "json", "brief", "spec", "outline", "blueprint", "report", "file", "config")),
    ("output",    ("release", "output", "viewer", "result", "figure", "render", "publish")),
]

# the deterministic default style block (palette/arrow DEFAULTS only — NOT content authority).
DEFAULT_STYLE = {
    "theme": "academic_flat",
    "font_family": "Inter, Arial, sans-serif",
    "palette": {
        "text": "#1F2937", "muted": "#6B7280",
        "blue_fill": "#E5EEFB", "blue_stroke": "#9DBDEB", "blue_accent": "#2563EB",
        "peach_fill": "#FDEBD8", "peach_stroke": "#F4C18A", "peach_accent": "#EA580C",
        "green_fill": "#DEF5E6", "green_stroke": "#9BD9B0", "green_accent": "#0E9F6E",
        "violet_fill": "#EDE9FE", "violet_stroke": "#C4B5FD", "violet_accent": "#7C3AED",
        "amber_fill": "#FEF3C7", "amber_stroke": "#FCD34D", "amber_accent": "#D97706",
        "red": "#DC2626", "node_fill": "#FFFFFF", "node_stroke": "#CBD2DC",
    },
    "arrow": {"stroke": "#4B5563", "width": 2.6},
}
TONE_ACCENT = {  # phase tone -> the per-node accent key used for member nodes of that group
    "blue": "blue_accent", "peach": "peach_accent", "green": "green_accent",
    "violet": "violet_accent", "amber": "amber_accent",
}

_TOKEN_RE = re.compile(r"[\w.+\-]+", re.UNICODE)


def tokenize(*texts):
    """Deterministic expected-token extraction matching the existing blueprints: split on whitespace +
    structural punctuation, keep tokens of length>=2 (or any containing a digit, so '+6.2' survives),
    preserve case, dedupe, sort. The reviewer panel blind-transcribes these and the hard-diff checks them."""
    out = set()
    for t in texts:
        if not t:
            continue
        for tok in _TOKEN_RE.findall(str(t)):
            if not re.search(r"[A-Za-z0-9]", tok):
                continue
            if len(tok) >= 2 or re.search(r"\d", tok):
                out.add(tok)
    return sorted(out)


def derive_shape(comp):
    if comp.get("identity_ref"):
        return "character"
    hay = f"{comp.get('id', '')} {comp.get('label', '')} {comp.get('role', '')}".lower()
    for shape, kws in SHAPE_KEYWORDS:
        if any(k in hay for k in kws):
            return shape
    return "process"


def auto_layout(brief, nodes, groups):
    """Compute pos/size for every node, bounds for every group, and the canvas size — from
    topology_constraint + visual_priority. No coordinate is ever hand-authored in the brief.

    Supported precisely: 'left_to_right_phases' (default) and 'linear_flow'. 'hierarchical_stack' is the
    same column algorithm rotated top->bottom. 'feedback_loop' lays out like linear_flow (the back edge is
    drawn by the renderer from the edge's direction:'back'). 'free' falls back to a grid. The chosen mode
    is returned so the caller can log it (no silent topology free-styling)."""
    topo = brief.get("topology_constraint", "left_to_right_phases")
    by_id = {n["id"]: n for n in nodes}
    # column buckets: free-floating nodes first, then one bucket per declared phase (brief order).
    phase_ids = [p["id"] for p in brief.get("phases", [])]
    columns = []
    free = [n for n in nodes if not n.get("group")]
    if free:
        columns.append(("_free", free))
    for pid in phase_ids:
        members = [n for n in nodes if n.get("group") == pid]
        if members:
            columns.append((pid, members))
    # any node whose group isn't a declared phase (shouldn't happen post-validation) -> trailing column
    placed = {n["id"] for _, col in columns for n in col}
    leftover = [n for n in nodes if n["id"] not in placed]
    if leftover:
        columns.append(("_misc", leftover))

    horizontal = topo != "hierarchical_stack"   # hierarchical = same algo, axes swapped
    cur = MARGIN
    group_bounds = {}
    for cid, col in columns:
        col_w = max((n["_w"] for n in col), default=DEFAULT_SIZE[0])
        col_h = sum(n["_h"] for n in col) + V_GAP * (len(col) - 1)
        top = MARGIN + TITLE_H + (GROUP_LABEL_H if cid in phase_ids else 0)
        y = top
        for n in col:
            cx = cur + col_w / 2 if horizontal else top + col_w / 2
            cy = y + n["_h"] / 2 if horizontal else cur + n["_h"] / 2
            n["pos"] = {"x": round(cx if horizontal else cy), "y": round(cy if horizontal else cx)}
            y += n["_h"] + V_GAP
        if cid in phase_ids:
            if horizontal:
                group_bounds[cid] = {"x": cur - PAD, "y": top - GROUP_LABEL_H,
                                     "w": col_w + 2 * PAD, "h": col_h + GROUP_LABEL_H + 2 * PAD}
            else:
                group_bounds[cid] = {"x": top - GROUP_LABEL_H, "y": cur - PAD,
                                     "w": col_h + GROUP_LABEL_H + 2 * PAD, "h": col_w + 2 * PAD}
        cur += col_w + COL_GAP
    # write sizes onto nodes; compute canvas extent
    max_x = max_y = 0
    for n in nodes:
        n["size"] = {"w": n.pop("_w"), "h": n.pop("_h")}
        max_x = max(max_x, n["pos"]["x"] + n["size"]["w"] / 2)
        max_y = max(max_y, n["pos"]["y"] + n["size"]["h"] / 2)
    for b in group_bounds.values():
        max_x = max(max_x, b["x"] + b["w"]); max_y = max(max_y, b["y"] + b["h"])
    for g in groups:
        if g["id"] in group_bounds:
            g["bounds"] = group_bounds[g["id"]]
    canvas = {"width": round(max_x + MARGIN), "height": round(max_y + MARGIN), "background": "#FFFFFF"}
    return canvas, topo


def compile_brief(brief, *, strict=True):
    """Pure brief->(blueprint, trace_errors) compile. Returns (blueprint_dict, traceability_dict,
    errors_list). Caller decides whether to fail on errors (strict)."""
    fid = brief["figure_id"]
    forbidden = brief.get("forbidden_tokens", []) or []
    profile = brief.get("target_profile", "paper")           # pass EXPLICITLY (don't fall to 'readme')
    trace = {"nodes": {}, "edges": {}, "groups": {}, "callouts": {}, "assets": {}, "symbols": {}}

    # --- assets <- identity_refs ---
    assets = []
    for ref in brief.get("identity_refs", []) or []:
        a = {"id": ref["id"], "path": ref["path"], "role": "identity_sheet",
             "source": f"brief:identity_refs/{ref['id']}"}
        if ref.get("traits"):
            a["lock_traits"] = list(ref["traits"])
        assets.append(a)
        trace["assets"][ref["id"]] = a["source"]
    asset_ids = {a["id"] for a in assets}

    # --- groups <- phases (bounds filled by auto_layout) ---
    groups = []
    for i, ph in enumerate(brief.get("phases", []) or []):
        g = {"id": ph["id"], "label_exact": ph["label"], "bounds": {"x": 0, "y": 0, "w": 0, "h": 0},
             "tone": TONE_CYCLE[i % len(TONE_CYCLE)], "order": i, "source": f"brief:phases/{ph['id']}"}
        groups.append(g)
        trace["groups"][ph["id"]] = g["source"]
    tone_by_group = {g["id"]: g["tone"] for g in groups}

    # --- nodes <- components (+ inputs/outputs as edge documents) ---
    nodes = []
    for comp in brief["components"]:
        prio = comp.get("visual_priority", "primary")
        w, h = SIZE_BY_PRIORITY.get(prio, DEFAULT_SIZE)
        n = {"id": comp["id"], "label_exact": comp["label"], "_w": w, "_h": h,
             "shape": derive_shape(comp), "must_render": True,
             "source": f"brief:components/{comp['id']}",
             "expected_tokens": tokenize(comp["label"], comp.get("one_line")),
             "forbidden_tokens": list(forbidden)}
        if comp.get("one_line"):
            n["desc_exact"] = comp["one_line"]
        if comp.get("role"):
            n["semantic_role"] = comp["role"]
        grp = comp.get("phase")
        if grp and grp in tone_by_group:
            n["group"] = grp
            n["accent"] = TONE_ACCENT.get(tone_by_group[grp])
        if comp.get("identity_ref"):
            n["asset_ref"] = comp["identity_ref"]
        nodes.append(n)
        trace["nodes"][comp["id"]] = n["source"]
    comp_ids = {c["id"] for c in brief["components"]}
    # free-standing inputs / outputs that aren't already components -> small document / output nodes
    for kind, key, shape in (("inputs", "in", "document"), ("outputs", "out", "output")):
        for j, txt in enumerate(brief.get(kind, []) or []):
            nid = f"{key}_{j}"
            if nid in comp_ids:
                continue
            w, h = SIZE_BY_PRIORITY["secondary"]
            n = {"id": nid, "label_exact": txt, "_w": w, "_h": h, "shape": shape, "must_render": True,
                 "source": f"brief:{kind}/{j}", "expected_tokens": tokenize(txt),
                 "forbidden_tokens": list(forbidden)}
            nodes.append(n)
            trace["nodes"][nid] = n["source"]

    # --- symbol_registry -> inject figure_symbol (kept == paper_variable) into the node that mentions it ---
    for sym in brief.get("symbol_registry", []) or []:
        fsym, pvar = sym.get("figure_symbol"), sym.get("paper_variable")
        if not fsym:
            continue
        trace["symbols"][fsym] = pvar or fsym
        hay_keys = [k for k in (fsym, pvar, sym.get("meaning")) if k]
        for n in nodes:
            text = f"{n.get('label_exact', '')} {n.get('desc_exact', '')}".lower()
            if any(str(k).lower() in text for k in hay_keys):
                toks = set(n["expected_tokens"]) | set(tokenize(fsym, pvar))
                n["expected_tokens"] = sorted(toks)
                break

    # --- edges <- flows ---
    edges = []
    node_ids = {n["id"] for n in nodes}
    for fl in brief.get("flows", []) or []:
        e = {"from": fl["from"], "to": fl["to"], "kind": fl["kind"], "must_render": True,
             "source": f"brief:flows/{fl['from']}->{fl['to']}"}
        if fl.get("label"):
            e["label_exact"] = fl["label"]
            e["expected_tokens"] = tokenize(fl["label"])
        if fl.get("direction") and fl["direction"] != "forward":
            e["direction"] = fl["direction"]
        edges.append(e)
        trace["edges"][f"{fl['from']}->{fl['to']}"] = e["source"]

    # --- callouts <- brief.callouts[] + a synthesized punchline from headline_claim/headline_number ---
    callouts = []
    hc, hn = brief.get("headline_claim"), brief.get("headline_number")
    if hc:
        lines = [brief["caption_thesis"]] if brief.get("caption_thesis") else []
        if hn:
            lines.append(f"result: {hn}")
        co = {"id": "punchline", "title_exact": hc, "lines_exact": lines,
              "accent": "red", "source": "brief:headline_claim+headline_number",
              "expected_tokens": tokenize(hc, *lines, hn)}   # hn MUST land in expected_tokens (GUARD-6)
        callouts.append(co)
        trace["callouts"]["punchline"] = co["source"]
    for k, c in enumerate(brief.get("callouts", []) or []):
        cid = f"callout_{k}"
        co = {"id": cid, "title_exact": c["title"], "lines_exact": list(c.get("lines", [])),
              "source": f"brief:callouts/{k}", "expected_tokens": tokenize(c["title"], *c.get("lines", []))}
        if c.get("anchor"):
            co["anchor"] = c["anchor"]
        callouts.append(co)
        trace["callouts"][cid] = co["source"]

    canvas, topo_used = auto_layout(brief, nodes, groups)

    # lay callouts out in a reserved bottom band so MULTIPLE callouts never stack on one default spot (the
    # renderer would otherwise put every callout at the same place). Each gets an explicit pos/size; the band
    # extends the canvas so callouts never overlap the node/group content above.
    if callouts:
        CW, CH, GAP = 420, 150, 40
        total_w = len(callouts) * CW + (len(callouts) - 1) * GAP
        canvas["width"] = max(canvas["width"], total_w + 2 * MARGIN)
        band_top = canvas["height"] - MARGIN + 10
        x0 = max(MARGIN, (canvas["width"] - total_w) // 2)
        for i, co in enumerate(callouts):
            co["pos"] = {"x": round(x0 + i * (CW + GAP) + CW / 2), "y": round(band_top + CH / 2)}
            co["size"] = {"w": CW, "h": CH}
        canvas["height"] = band_top + CH + MARGIN

    blueprint = {
        "version": "method-figure/blueprint/v1",
        "figure_id": fid,
        "compiled_from_brief": {"type": fid},
        "canvas": canvas,
        "render_policy": {"label_policy": "baked", "target_profile": profile, "max_rounds": 4},
        "nodes": nodes,
    }
    if brief.get("figure_purpose") or brief.get("caption_thesis"):
        blueprint["title"] = {}
        if brief.get("figure_purpose"):
            blueprint["title"]["main"] = brief["figure_purpose"]
        if brief.get("caption_thesis"):
            blueprint["title"]["sub"] = brief["caption_thesis"]
    if assets:
        blueprint["assets"] = assets
    if groups:
        blueprint["groups"] = groups
    if edges:
        blueprint["edges"] = edges
    if callouts:
        blueprint["callouts"] = callouts
    if forbidden:
        blueprint["forbidden_tokens"] = list(forbidden)
    blueprint["style"] = DEFAULT_STYLE
    blueprint["rail"] = {"label_exact": f"max {blueprint['render_policy']['max_rounds']} rounds | "
                                        "blind cross-model diff | human backstop"}
    blueprint["acceptance"] = {
        "min_core_score": 4,
        "required_transcribers": ["gemini", "codex"],   # the AUTOMATED panel (match run_spiral.py)
        "codex_policy": "required_not_sole",   # Codex approve required, but never the sole acquitter
        "claude_structural_signoff_required": True,
        "required_approvers": ["gemini", "claude"],
        "veto_fields": ["anomalies", "missing_tokens", "wrong_edges"],
        "max_repeated_failure": 2,
    }

    errors = validate_traceability(blueprint, brief)
    return blueprint, trace, errors


def validate_traceability(blueprint, brief):
    """Every blueprint object must trace to a brief field, and every load-bearing brief element (claim,
    number, identity trait, component, flow) must appear in the blueprint. Returns a list of human-named
    errors; compile_brief's --strict turns any of these into a non-zero exit (Refuse-and-Escalate)."""
    errs = []
    # 1) every object carries a source
    for n in blueprint.get("nodes", []):
        if not n.get("source"):
            errs.append(f"node '{n.get('id')}' has no source (un-traceable)")
    for e in blueprint.get("edges", []):
        if not e.get("source"):
            errs.append(f"edge '{e.get('from')}->{e.get('to')}' has no source")
    for g in blueprint.get("groups", []):
        if not g.get("source"):
            errs.append(f"group '{g.get('id')}' has no source")
    for c in blueprint.get("callouts", []):
        if not c.get("source"):
            errs.append(f"callout '{c.get('id')}' has no source")
    for a in blueprint.get("assets", []):
        if not a.get("source"):
            errs.append(f"asset '{a.get('id')}' has no source")
    # 2) the scientific number must survive into a callout's expected_tokens (GUARD-6: +6.2 vs +6.25)
    hn = brief.get("headline_number")
    if hn:
        toks = {t for c in blueprint.get("callouts", []) for t in c.get("expected_tokens", [])}
        if not any(hn in t or t in hn for t in toks) and hn not in toks:
            errs.append(f"headline_number '{hn}' did not land in any callout's expected_tokens")
    # 3) the headline claim must be a callout title
    hc = brief.get("headline_claim")
    if hc and hc not in {c.get("title_exact") for c in blueprint.get("callouts", [])}:
        errs.append(f"headline_claim '{hc[:40]}...' did not become a callout title_exact")
    # 4) every identity trait must be carried on the matching asset's lock_traits
    for ref in brief.get("identity_refs", []) or []:
        asset = next((a for a in blueprint.get("assets", []) if a["id"] == ref["id"]), None)
        if asset is None:
            errs.append(f"identity_ref '{ref['id']}' did not become an asset")
            continue
        for tr in ref.get("traits", []) or []:
            if tr not in (asset.get("lock_traits") or []):
                errs.append(f"identity trait '{tr}' (ref {ref['id']}) missing from asset lock_traits")
    # 5) every component became a node, every flow became an edge (nothing silently dropped)
    node_labels = {n.get("label_exact") for n in blueprint.get("nodes", [])}
    for comp in brief.get("components", []):
        if comp["label"] not in node_labels:
            errs.append(f"component '{comp['id']}' (label '{comp['label']}') was dropped")
    edge_keys = {(e.get("from"), e.get("to")) for e in blueprint.get("edges", [])}
    for fl in brief.get("flows", []) or []:
        if (fl["from"], fl["to"]) not in edge_keys:
            errs.append(f"flow {fl['from']}->{fl['to']} was dropped")
    # 6) asset_ref integrity (a node anchored to an identity must point at a real asset)
    asset_ids = {a["id"] for a in blueprint.get("assets", [])}
    for n in blueprint.get("nodes", []):
        if n.get("asset_ref") and n["asset_ref"] not in asset_ids:
            errs.append(f"node '{n['id']}' asset_ref '{n['asset_ref']}' has no matching asset")
    # 7) phase resolution — a component.phase not declared in brief.phases is silently dropped from grouping (fail-open)
    phase_ids = {p["id"] for p in brief.get("phases", []) or []}
    for comp in brief.get("components", []):
        if comp.get("phase") and comp["phase"] not in phase_ids:
            errs.append(f"component '{comp['id']}' references phase '{comp['phase']}' not declared in brief.phases")
    # 8) flow-endpoint resolution — every edge endpoint MUST resolve to a real node id (a dangling flow would
    #    otherwise emit an invalid blueprint before validate_blueprint.py even runs)
    node_ids = {n.get("id") for n in blueprint.get("nodes", [])}
    for e in blueprint.get("edges", []):
        for end in ("from", "to"):
            if e.get(end) not in node_ids:
                errs.append(f"flow endpoint '{e.get(end)}' (edge {e.get('from')}->{e.get('to')}) is not a node id")
    # 9) an identity_ref MUST carry ≥1 trait (a locked identity with no traits cannot be verified against)
    for ref in brief.get("identity_refs", []) or []:
        if not (ref.get("traits") or []):
            errs.append(f"identity_ref '{ref['id']}' has no traits (a locked identity needs ≥1 trait to verify against)")
    # 10) symbol_registry — every figure_symbol must bind to a node's expected_tokens, and figure_symbol must
    #     equal paper_variable (anti-drift); an unmatched symbol or a figure≠paper mismatch is an escalation
    all_tokens = {t for n in blueprint.get("nodes", []) for t in n.get("expected_tokens", [])}
    for sym in brief.get("symbol_registry", []) or []:
        fsym, pvar = sym.get("figure_symbol"), sym.get("paper_variable")
        if fsym and fsym not in all_tokens:
            errs.append(f"symbol '{fsym}' did not bind to any node's expected_tokens (unmatched — name it in a component)")
        if fsym and pvar and fsym != pvar:
            errs.append(f"symbol drift: figure_symbol '{fsym}' != paper_variable '{pvar}' (keep them identical)")
    # 11) phases.members consistency — a declared member must be a component whose phase == that phase
    comp_phase = {comp["id"]: comp.get("phase") for comp in brief.get("components", [])}
    for ph in brief.get("phases", []) or []:
        for m in ph.get("members", []) or []:
            if m not in comp_phase:
                errs.append(f"phase '{ph['id']}' lists member '{m}' that is not a component")
            elif comp_phase[m] != ph["id"]:
                errs.append(f"phase '{ph['id']}' member '{m}' has component.phase='{comp_phase[m]}' (mismatch)")
    return errs


def main():
    ap = argparse.ArgumentParser(description="Step-0: compile a method_figure_brief.json into blueprint.json")
    ap.add_argument("brief")
    ap.add_argument("--out", required=True, help="output blueprint.json path")
    ap.add_argument("--trace", help="output traceability.json path (default: alongside --out)")
    ap.add_argument("--strict", dest="strict", action="store_true", default=True,
                    help="fail closed on any un-traceable object or missing claim/number/trait (default)")
    ap.add_argument("--no-strict", dest="strict", action="store_false",
                    help="emit anyway and only warn (NOT recommended)")
    a = ap.parse_args()

    brief = json.loads(Path(a.brief).read_text(encoding="utf-8"))
    for req in ("figure_id", "components", "flows"):
        if req not in brief:
            sys.exit(f"[compile_brief] FATAL: brief missing required field '{req}'")

    blueprint, trace, errors = compile_brief(brief, strict=a.strict)

    if errors:
        tag = "FAIL" if a.strict else "WARN"
        print(f"[compile_brief] {tag} — {len(errors)} traceability issue(s):", file=sys.stderr)
        for e in errors:
            print("  -", e, file=sys.stderr)
        if a.strict:
            sys.exit("[compile_brief] refusing to emit a blueprint that is not fully traceable to the brief "
                     "(a missing number/claim/trait/component is an escalation, not creative license). "
                     "Fix the brief or pass --no-strict to override.")

    out = Path(a.out)
    out.write_text(json.dumps(blueprint, indent=2, ensure_ascii=False), encoding="utf-8")
    trace_path = Path(a.trace) if a.trace else out.with_name("traceability.json")
    trace_path.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[compile_brief] OK — {len(blueprint['nodes'])} nodes, {len(blueprint.get('edges', []))} edges, "
          f"{len(blueprint.get('groups', []))} groups, {len(blueprint.get('callouts', []))} callouts, "
          f"topology={brief.get('topology_constraint', 'left_to_right_phases')} "
          f"→ {out}  (+ {trace_path.name})")


if __name__ == "__main__":
    main()
