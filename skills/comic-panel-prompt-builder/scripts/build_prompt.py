#!/usr/bin/env python3
"""build_prompt.py — the DETERMINISTIC bake compiler (搬运工原則) for ONE locked panel_spec.

Turns ONE gate-approved `panel_spec` node + its `status:locked` `blueprint` node into the EXACT fixed-section
bake message the spiral engine will hand to the backend, plus the locked identity-ref list, then runs the
canonical _validate.py vetoes and (on pass) emits a `prompt_bundle` node + LEGAL edges. It is a pure transform:
it never calls Codex on the happy path, never invents a scene/number/cast/style adjective, and FAILS closed
(pointing upstream) on a malformed spec instead of papering over it.

    python3 build_prompt.py <project_dir> <panel_id> [--retry --reason "<text>"]

Reads wiki node JSON from <project_dir>/wiki/nodes/<node_id with ':'->'_'>.json (the example layout) and the
world-keyed style_prefix from <project_dir>/ART_BIBLE.md. Writes _resolved.json / _meta.json / _validation.json
under <project_dir>/wiki/prompt_build/<panel_id>/ for the trace.

Exit codes (= the verdict surface):
  0  validated + emitted + gate pass
  2  input missing / malformed CLI (--retry w/o --reason; panel_spec not node_type panel_spec or not status:locked)
  3  upstream prereq unmet (blueprint not status:locked / ref not real / content_svg missing / expected_literals
     missing on a baked figure-panel / style_prefix bad / failure_mode query failed)
  4  banned-vocab | length | baked-bubble | ref fail (gate -> fail, _validation.json preserved)
  7  Phase 1.6 regenerate (a trigger_pattern still matches after repair; failure_of edge written)
"""
import argparse, hashlib, json, os, re, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _validate  # the ONE canonical validator (MAX_MESSAGE_CHARS / BANNED_VOCAB / vetoes)

NODE_ID_RE = re.compile(r"^(intent|style|outline|asset|storyboard|panel|blueprint|prompt|motif|cont|attempt|review|decision|fail):[a-z0-9_-]+$")
LEGAL_STATUS = {"draft", "pending", "under_review", "locked", "rejected", "superseded", "active", "complete", "final"}


def slug(s):
    """node_id slugs are lowercase `[a-z0-9_-]+` (schema pattern); the display panel_id may carry case."""
    return re.sub(r"[^a-z0-9_-]+", "-", str(s).lower()).strip("-")


def die(code, msg):
    """Exit with the CONTRACTED numeric code (sys.exit(str) would force code 1 and break the exit-code surface)."""
    print(f"[build_prompt] exit {code}: {msg}", file=sys.stderr)
    sys.exit(code)


def node_path(project_dir, node_id):
    return os.path.join(project_dir, "wiki", "nodes", node_id.replace(":", "_") + ".json")


def load_node(project_dir, node_id):
    p = node_path(project_dir, node_id)
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def resolve_panel_node(project_dir, panel_arg):
    """panel_arg may be a node_id (panel:foo) or a payload panel_id; resolve to the panel_spec node."""
    if panel_arg.startswith("panel:"):
        return load_node(project_dir, panel_arg)
    nd = os.path.join(project_dir, "wiki", "nodes")
    if not os.path.isdir(nd):
        return None
    for fn in os.listdir(nd):
        if not fn.endswith(".json"):
            continue
        n = json.load(open(os.path.join(nd, fn), encoding="utf-8"))
        if n.get("node_type") == "panel_spec" and n.get("payload", {}).get("panel_id") == panel_arg:
            return n
    return None


def read_style_prefix(project_dir, world):
    """World-keyed style_prefix from ART_BIBLE.md (§0 register + §0.5 two-world palette). Deterministic line
    lookup keyed by the panel's `world`; no model call. Returns (prefix, problems)."""
    ab = os.path.join(project_dir, "ART_BIBLE.md")
    if not os.path.exists(ab):
        return None, ["ART_BIBLE.md missing"]
    text = open(ab, encoding="utf-8").read()
    # Convention: a line `STYLE_PREFIX[<world>]: <prefix...>` in ART_BIBLE pins each world's style declaration.
    m = re.search(rf"^STYLE_PREFIX\[{re.escape(world)}\]:\s*(.+)$", text, re.MULTILINE)
    if not m:
        return None, [f"no STYLE_PREFIX[{world}] declaration in ART_BIBLE.md"]
    prefix = m.group(1).strip()
    probs = []
    if len(prefix) > 200:
        probs.append(f"style_prefix > 200 chars ({len(prefix)})")  # hard
    return prefix, probs


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_active_failure_modes(project_dir):
    """Query ACTIVE failure_mode nodes (payload.active == true). Returns list or raises -> exit 3 on read error."""
    nd = os.path.join(project_dir, "wiki", "nodes")
    out = []
    if not os.path.isdir(nd):
        return out
    for fn in os.listdir(nd):
        if not fn.endswith(".json"):
            continue
        n = json.load(open(os.path.join(nd, fn), encoding="utf-8"))
        if n.get("node_type") == "failure_mode" and n.get("payload", {}).get("active") is True:
            out.append(n)
    return out


def compose(panel, blueprint, style_prefix, identity_locks, scene_text, retry_invariants):
    """Build the fixed-section condition string. ORDER IS LOAD-BEARING — front = strongest conditioning.
    Reads ONLY real panel_spec/blueprint node fields + identity_lock payloads resolved from asset_ids[]."""
    pp = panel["payload"]
    bp = blueprint["payload"]
    text_mode = pp["text_mode"]
    sections = []
    # POSITIVE INVARIANTS (retry only) — injected at the FRONT, highest priority.
    if retry_invariants:
        sections.append("POSITIVE INVARIANTS (must be present in every panel, highest priority):\n"
                        + "\n".join(f"- {x}" for x in retry_invariants))
    # STYLE PREFIX — world-keyed, NO camera/lens/lighting/quality vocab.
    sections.append(f"STYLE PREFIX: {style_prefix}")
    # BAKED DIALOGUE — only if text_mode == baked; else SKIP (bubbles are the viewer's job).
    if text_mode == "baked":
        bubbles = [b.get("text", "") if isinstance(b, dict) else str(b) for b in pp.get("bubbles", [])]
        bubbles = [b for b in bubbles if b.strip()]
        if bubbles:
            sections.append("BAKED DIALOGUE (draw legible balloons):\n" + "\n".join(f"- {b}" for b in bubbles))
    # SCENE COMPOSITION NARRATIVE — the content authority is the blueprint's content_svg layout + the panel's
    # side_narration / motifs (the node model has NO `condition.scene`; scene staging is carried by the
    # blueprint SVG, summarized here from real node fields).
    sections.append("SCENE COMPOSITION NARRATIVE:\n" + (scene_text or pp.get("side_narration", "")).strip())
    # FIXED ELEMENTS — identity lock resolved by following asset_ids[] to each identity-sheet asset node's
    # identity_lock payload (the node model's identity authority; there is NO identity_desc on panel_spec).
    if identity_locks:
        sections.append("FIXED ELEMENTS (must NOT change):\n" + "\n".join(f"- {x}" for x in identity_locks))
    # ALLOWED CHANGE — the panel's motifs delta vs the prior panel.
    motifs = pp.get("motifs", {})
    allowed = motifs.get("allowed_change") if isinstance(motifs, dict) else None
    if allowed:
        sections.append("ALLOWED CHANGE (vs the prior panel):\n"
                        + "\n".join(f"- {x}" for x in (allowed if isinstance(allowed, list) else [allowed])))
    # FORBIDDEN — fixed baseline + any panel-specific must_not_add.
    forbidden = ["no new character entering frame", "no off-model drift", "no scene/world recolor"]
    must_not = motifs.get("must_not_add") if isinstance(motifs, dict) else None
    if must_not:
        forbidden += (must_not if isinstance(must_not, list) else [must_not])
    sections.append("FORBIDDEN (must NOT happen):\n" + "\n".join(f"- {x}" for x in forbidden))
    # SCREEN-TEXT WHITELIST — the blueprint's expected_literals (char-exact, the upstream of panel_gate's diff).
    # The blueprint is the SOLE literal authority; NEVER fall back to panel literals (that weakens the contract).
    lits = bp.get("expected_literals", [])
    if lits:
        sections.append("SCREEN-TEXT WHITELIST (exact characters to preserve):\n"
                        + " · ".join(json.dumps(x, ensure_ascii=False) for x in lits))
    return "\n\n".join(sections)


def write_node(project_dir, node):
    os.makedirs(os.path.join(project_dir, "wiki", "nodes"), exist_ok=True)
    p = node_path(project_dir, node["node_id"])
    json.dump(node, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def append_edge(project_dir, src, dst, etype, **extra):
    p = os.path.join(project_dir, "wiki", "edges.jsonl")
    rec = {"src": src, "dst": dst, "type": etype}
    rec.update(extra)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def make_bundle(bundle_id, panel, blueprint, style_prefix, composed, ref_paths, status, banned):
    """Build a schema-valid prompt_bundle node (the 6 PAYLOAD_REQUIRED fields). Used on the happy path
    (status='locked') AND on the exit-7 regenerate path (status='rejected'), so the failure_of edge endpoint
    always resolves to a real node — never a dangling src."""
    return {
        "node_id": bundle_id,
        "node_type": "prompt_bundle",
        "status": status,
        "title": f"bake bundle for {panel['payload']['panel_id']}",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "payload": {
            "source_panel_id": panel["node_id"],
            "source_blueprint_id": blueprint["node_id"],
            "style_prefix": style_prefix,
            "composed_prompt": composed,
            "banned_vocab_scan": banned if banned is not None else {"hits": [], "clean": None},
            "identity_ref_paths": ref_paths,
        },
    }


def main():
    ap = argparse.ArgumentParser(description="deterministic bake compiler for one locked panel_spec")
    ap.add_argument("project_dir")
    ap.add_argument("panel", help="panel node_id (panel:foo) or payload panel_id")
    ap.add_argument("--retry", action="store_true")
    ap.add_argument("--reason", default=None)
    a = ap.parse_args()

    # Phase -1 — parse + scaffold. --retry REQUIRES --reason.
    if a.retry and not a.reason:
        die(2, "--retry requires --reason")
    proj = a.project_dir
    panel = resolve_panel_node(proj, a.panel)

    # Phase 0(a) — panel_spec must be node_type panel_spec AND status locked.
    if panel is None:
        die(2, f"panel_spec for '{a.panel}' not found")
    if panel.get("node_type") != "panel_spec":
        die(2, f"node '{panel.get('node_id')}' is {panel.get('node_type')}, not panel_spec")
    if panel.get("status") != "locked":
        die(2, f"panel_spec status is '{panel.get('status')}', not 'locked' (not gate-approved)")
    pid = panel["payload"]["panel_id"]
    bundle_id = "prompt:" + slug(pid)  # lowercase node_id slug (schema pattern); pid keeps display case
    outdir = os.path.join(proj, "wiki", "prompt_build", slug(pid))
    os.makedirs(outdir, exist_ok=True)

    # Phase 0(b) — resolve the blueprint via content_blueprint; it must be status:locked (the schema's signal
    # that the cross-layer gate signed off — blueprint nodes have NO review_status field).
    bp_id = panel["payload"].get("content_blueprint")
    blueprint = load_node(proj, bp_id) if bp_id else None
    if blueprint is None:
        die(3, f"blueprint '{bp_id}' (panel.content_blueprint) not found")
    if blueprint.get("node_type") != "blueprint":
        die(3, f"'{bp_id}' is {blueprint.get('node_type')}, not blueprint")
    if blueprint.get("status") != "locked":
        die(3, f"blueprint status is '{blueprint.get('status')}', not 'locked' (gate not signed off)")

    bp = blueprint["payload"]
    # Two engine contracts: content_svg must exist on disk (+ sha match); baked figure-panel needs expected_literals.
    csvg = bp.get("content_svg")
    if not csvg:
        die(3, "blueprint.content_svg is null/missing (no panel has no content_svg)")
    csvg_path = csvg if os.path.isabs(csvg) else os.path.join(proj, csvg)
    if not os.path.exists(csvg_path):
        die(3, f"content_svg not on disk: {csvg}")
    if bp.get("file_sha256") and sha256_file(csvg_path) != bp["file_sha256"]:
        die(3, "content_svg file_sha256 mismatch (stale blueprint)")
    text_mode = panel["payload"]["text_mode"]
    if text_mode == "baked":
        bp_lits = bp.get("expected_literals") or []
        if not bp_lits:
            die(3, "baked figure-panel with empty blueprint.expected_literals — the blueprint is the SOLE "
                   "authority; panel literals are NOT an accepted fallback (no baked-literal contract)")
        # EVERY baked literal must be an ascii-tokenizable string — mirror run_comic.py cfg_usable EXACTLY
        # (all(...), isinstance str, lowercase token), so this pre-gate refuses precisely what the engine floor
        # would later reject (never weaker than the deterministic enforcer). A non-audited scene panel → 'html'.
        if not all(isinstance(x, str) and re.findall(r"[a-z0-9+._-]+", x.lower()) for x in bp_lits):
            die(3, "baked expected_literals must each be an ascii-tokenizable string (cfg_usable contract); "
                   "route a non-audited scene panel to text_mode:'html' instead of 'baked'")

    # Phase 0(c) — every ref is a REAL locked asset path; resolve identity locks from asset_ids[] -> asset nodes.
    identity_locks, ref_paths = [], []
    for aid in panel["payload"].get("asset_ids", []):
        an = load_node(proj, aid)
        if an is None:
            die(3, f"asset '{aid}' (panel.asset_ids) not found")
        if an.get("node_type") == "asset":
            if an.get("status") != "locked":
                die(3, f"asset '{aid}' status '{an.get('status')}', not 'locked'")
            il = an["payload"].get("identity_lock")
            if il:
                identity_locks.append(il if isinstance(il, str) else json.dumps(il, ensure_ascii=False))
            # the locked .png ref the asset publishes (ref_requirements / a published path field)
            ref = an["payload"].get("ref_requirements")
            if isinstance(ref, dict):
                ref = ref.get("output_ref") or ref.get("path")
            ref_abs = (ref if os.path.isabs(ref) else os.path.join(proj, ref)) if isinstance(ref, str) else None
            real_png = bool(isinstance(ref, str) and ref.lower().endswith(".png") and ref_abs and os.path.exists(ref_abs))
            if real_png:
                ref_paths.append(ref)
            elif il:
                # an IDENTITY asset MUST publish a real on-disk .png ref — silently dropping it (the old bug)
                # defeats the ref-count veto, the linchpin that an identity figure is anchored to its sheet.
                die(3, f"identity asset '{aid}' publishes no real .png ref (got {ref!r}: missing/non-png/"
                       f"nonexistent) — cannot anchor identity; fix the asset's ref or drop its identity_lock")
    if "pending:" in json.dumps(panel["payload"].get("asset_ids", [])):
        die(3, "an asset ref is still pending:* (unresolved)")

    # Phase 0(d) — style_prefix resolves and is sane (<=200 chars hard).
    world = panel["payload"]["world"]
    style_prefix, sp_probs = read_style_prefix(proj, world)
    if style_prefix is None or any("> 200" in p for p in sp_probs):
        die(3, f"style_prefix bad for world '{world}': {sp_probs}")

    json.dump({"panel": panel, "blueprint": blueprint, "style_prefix": style_prefix,
               "identity_locks": identity_locks, "ref_paths": ref_paths},
              open(os.path.join(outdir, "_resolved.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # Phase 1.5 — failure_mode positive-invariant injection (retry only).
    retry_invariants = []
    failure_node_for_edge = None
    if a.retry:
        try:
            fms = collect_active_failure_modes(proj)
        except Exception as e:
            die(3, f"failure_mode query failed: {e}")
        # rank by recency*severity; inject repair_pattern ONLY if encoding_style == positive_invariant.
        for fm in sorted(fms, key=lambda f: f["payload"].get("severity", 3), reverse=True)[:10]:
            if fm["payload"].get("encoding_style") == "positive_invariant":
                rp = fm["payload"].get("repair_pattern")
                if rp:
                    retry_invariants.append(rp)
                    failure_node_for_edge = fm["node_id"]

    scene_text = panel["payload"].get("side_narration", "")
    composed = compose(panel, blueprint, style_prefix, identity_locks, scene_text, retry_invariants)
    json.dump({"identity_count": len(identity_locks), "ref_count": len(ref_paths),
               "text_mode": text_mode, "retry_invariants": len(retry_invariants)},
              open(os.path.join(outdir, "_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # Phase 1.6 — trigger re-scan against active banlist trigger_patterns (a still-firing trigger -> exit 7).
    if a.retry:
        for fm in collect_active_failure_modes(proj):
            for trig in fm["payload"].get("trigger_patterns", []):
                if re.search(trig, composed, re.IGNORECASE) and fm["payload"].get("encoding_style") != "positive_invariant":
                    # persist a REJECTED bundle FIRST so the edge endpoint resolves (the bundle node is only
                    # otherwise created on the happy path); the failure_of edge then points failure_mode -> bundle.
                    write_node(proj, make_bundle(bundle_id, panel, blueprint, style_prefix, composed, ref_paths,
                                                 status="rejected", banned=None))
                    append_edge(proj, fm["node_id"], bundle_id, "failure_of",
                                evidence={"trigger": trig, "note": "trigger still matches after repair"})
                    die(7, f"trigger_pattern '{trig}' of {fm['node_id']} still matches; failure_of edge written")

    # Phase 2 — VALIDATE = the hard gate (the four binary vetoes on the FULL composed message).
    bubble_texts = [b.get("text", "") if isinstance(b, dict) else str(b) for b in panel["payload"].get("bubbles", [])]
    val = _validate.validate(composed, text_mode, bubble_texts, ref_paths, proj)
    json.dump(val, open(os.path.join(outdir, "_validation.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if not val["passes_all"]:
        # set the panel's gate field to fail and exit 4 (push the fix UPSTREAM; never silently patch the spec).
        panel.setdefault("payload", {}).setdefault("review_gates", {})["storyboard_json_gate"] = "fail"
        write_node(proj, panel)
        print(json.dumps({"gate": "fail", "panel_id": pid, "validation": val}, ensure_ascii=False))
        sys.exit(4)

    # Phase 3 — emit the prompt_bundle node (payload = the schema's 6 required fields) + LEGAL edges.
    bundle = make_bundle(bundle_id, panel, blueprint, style_prefix, composed, ref_paths, status="locked",
                         banned={"hits": val["banned_hits"], "clean": val["no_banned_vocab"]})
    write_node(proj, bundle)
    # LEGAL author-layer edges (validate_wiki.py EDGE_TYPES): derived_from -> panel_spec; uses_blueprint -> blueprint.
    append_edge(proj, bundle["node_id"], panel["node_id"], "derived_from")
    append_edge(proj, bundle["node_id"], blueprint["node_id"], "uses_blueprint")
    # retry failure_mode trace: a LEGAL `derived_from` edge to the failure_mode node, score in edge evidence
    # (there is NO consulted_failure_mode edge type in EDGE_TYPES).
    if failure_node_for_edge:
        append_edge(proj, bundle["node_id"], failure_node_for_edge, "derived_from",
                    evidence={"consulted_failure_mode": True, "reason": a.reason})

    # html_bubbles[] from the blueprint route to the JSON viewer overlay ONLY (never into composed_prompt).
    log = os.path.join(proj, "wiki", "log.md")
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"- {datetime.datetime.now(datetime.timezone.utc).isoformat()} build_prompt {pid} -> {bundle['node_id']} (gate pass)\n")

    # Phase 4 — stdout one-line JSON; set the panel's storyboard_json_gate = pass.
    panel.setdefault("payload", {}).setdefault("review_gates", {})["storyboard_json_gate"] = "pass"
    write_node(proj, panel)
    print(json.dumps({"prompt_bundle_id": bundle["node_id"], "panel_id": pid,
                      "source_blueprint_id": blueprint["node_id"]}, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
