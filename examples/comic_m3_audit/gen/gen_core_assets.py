#!/usr/bin/env python3
"""gen_core_assets.py — emit the canonical asset library (storyboard CONSOLIDATED ASSET_REQUESTS #1-#7).

Outputs (all under ../assets/):
  ddl_widget_template_v1.svg      — the 3 skins + color states + SUBMITTED variant (timeline authority sheet)
  stamp_family_v1.svg             — DUP/SURVIVES/REJECT/ACCEPT/WARN_corrected/SUBMITTED/AUDIT + mini glyphs
  mug_states_ref_v1.svg           — HER 'ML RESEARCH' motif cup: hot / fading / cold
  wandb_curve_template_v1.svg     — the curve template sheet (3 named instances side by side)
  wandb_exact_parse_060_071_v1.svg / wandb_exact_parse_071_066_v1.svg / wandb_exact_parse_078_089_v1.svg
  tokyo_fragment_chip_v1.svg      — the broken-JSON chip at 4 scales + the repaired variant (S17-internal use)
  wiki_starmap_nodes_v1.json      — THE single truth source of star coordinates (S16b + S22)
  wiki_starmap_v1.svg             — S16b labeled star-map (only 4 big gated labels)
  constellation_layout_v1.svg     — S22 PURE stars (ZERO text — hard stray-text-absence contract)
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import (svg_doc, text, rect, ddl_chip, stamp, mini_stamp_glyph, mug, curve_panel,
                       tokyo_chip, STARMAP_NODES, STARMAP_EDGES, STAR_COLOR,
                       INK, DIM, RED, AMBER, GREEN, ST, VOID, WARM)

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def w(name, content):
    p = os.path.join(A, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(content)
    print("wrote", name)


# 1) DDL widget sheet
o = [text(640, 40, "ddl_widget_template_v1 — the ONLY timeline renderer (17 instances across the film)", INK, 17)]
o.append(text(120, 90, "corner / amber", DIM, 12, "400", "start")); o.append(ddl_chip(120, 104, "T-19:42", "amber", "corner"))
o.append(text(320, 90, "corner / red", DIM, 12, "400", "start"));   o.append(ddl_chip(320, 104, "T-00:42", "red", "corner"))
o.append(text(520, 90, "corner / green", DIM, 12, "400", "start")); o.append(ddl_chip(520, 104, "T-02:58", "green", "corner"))
o.append(text(120, 190, "phone lockscreen", DIM, 12, "400", "start")); o.append(ddl_chip(120, 204, "T-18:40", "amber", "phone"))
o.append(text(320, 190, "dashboard chip", DIM, 12, "400", "start"));   o.append(ddl_chip(320, 204, "T-05:12", "amber", "dash"))
o.append(text(560, 190, "green + SUBMITTED ✓ (S20)", DIM, 12, "400", "start")); o.append(ddl_chip(560, 232, "T-00:27", "green", "corner", submitted=True))
o.append(text(640, 320, "T-24:00:00 → 19:42 → 19:42 → 18:55 → 18:40 → 18:30 → 17:46 → 17:02 → 16:21 → 16:05 → 05:12 → 02:58 → 02:41 → 01:57 → 00:42 → 00:27(SUBMITTED)", AMBER, 12.5, "700"))
o.append(text(640, 344, "monotonic — the countdown NEVER moves backward (codex fix #1)", DIM, 11, "400"))
w("ddl_widget_template_v1.svg", svg_doc(1280, 380, "".join(o)))

# 2) stamp family sheet
o = [text(640, 40, "stamp_family_v1 — ONE stamp dialect for the whole film (matches the baked S15 geometry)", INK, 17)]
xs = 60
for lbl in ["DUP", "SURVIVES", "REJECT", "ACCEPT"]:
    o.append(stamp(xs, 70, lbl)); xs += (34 + 17 * len(lbl)) + 28
xs = 60
for lbl in ["WARN_corrected", "SUBMITTED", "AUDIT"]:
    o.append(stamp(xs, 160, lbl)); xs += (34 + 17 * len(lbl)) + 60
o.append(text(180, 268, "mini node glyphs (star-map):", DIM, 12, "400", "start"))
o.append(mini_stamp_glyph(420, 263, "fail")); o.append(mini_stamp_glyph(460, 263, "audit")); o.append(mini_stamp_glyph(500, 263, "ok"))
o.append(text(640, 300, "S11 REJECT ↔ S16 ACCEPT must reuse this exact card geometry (mirror pair)", DIM, 11, "400"))
w("stamp_family_v1.svg", svg_doc(1280, 330, "".join(o)))

# 3) mug states sheet
o = [text(640, 40, "mug_states_ref_v1 — HER 'ML RESEARCH' motif cup (the </> mug is env, NOT this)", INK, 17)]
for i, (st_, cap) in enumerate([("hot", "HOT · two steady plumes (S01 origin · S02 same)"),
                                ("fading", "FADING · one thin wisp (S03 inset)"),
                                ("cold", "COLD · no steam + milk film (S20 / S21 corner)")]):
    x = 200 + i * 340
    o.append(mug(x, 130, st_, 1.4))
    o.append(text(x + 60, 260, cap, DIM, 12, "400"))
w("mug_states_ref_v1.svg", svg_doc(1280, 300, "".join(o)))

# 4) curve template sheet + the 3 named instances
P1 = [(0.0, 0.60), (0.2, 0.62), (0.45, 0.66), (0.7, 0.69), (1.0, 0.71)]
P2 = [(0.0, 0.71), (0.3, 0.70), (0.55, 0.69), (0.75, 0.675), (1.0, 0.66)]
P3 = [(0.0, 0.78), (0.25, 0.80), (0.5, 0.84), (0.75, 0.87), (1.0, 0.89)]
o = [text(640, 38, "wandb_curve_template_v1 — exact_parse curve, three canonical instances", INK, 17)]
o.append(curve_panel(60, 64, 360, 220, P1, "0.60→0.71", GREEN))
o.append(curve_panel(460, 64, 360, 220, P2, "0.71→0.66", RED, dip_at=4))
o.append(curve_panel(860, 64, 360, 220, P3, "0.78→0.89", GREEN))
w("wandb_curve_template_v1.svg", svg_doc(1280, 320, "".join(o)))
w("wandb_exact_parse_060_071_v1.svg", svg_doc(640, 360, curve_panel(20, 20, 600, 320, P1, "0.60→0.71", GREEN)))
w("wandb_exact_parse_071_066_v1.svg", svg_doc(640, 360, curve_panel(20, 20, 600, 320, P2, "0.71→0.66", RED, dip_at=4)))
w("wandb_exact_parse_078_089_v1.svg", svg_doc(640, 360, curve_panel(20, 20, 600, 320, P3, "0.78→0.89", GREEN)))

# 5) tokyo chip sheet (multi-scale + repaired)
o = [text(640, 40, "tokyo_fragment_chip_v1 — one source, four scales + repaired (S17-internal)", INK, 17)]
o.append(text(120, 92, "S10 hero (gated)", DIM, 12, "400", "start"));      o.append(tokyo_chip(120, 104, 1.6))
o.append(text(520, 92, "S11 evidence thumb", DIM, 12, "400", "start"));    o.append(tokyo_chip(520, 116, 1.0))
o.append(text(770, 92, "S12a shard", DIM, 12, "400", "start"));            o.append(tokyo_chip(770, 124, 0.7))
o.append(text(960, 92, "S09 micro (BELOW transcription threshold, ungated)", DIM, 11, "400", "start"))
o.append(tokyo_chip(960, 130, 0.42))
o.append(text(120, 230, "repaired (authored inside paper_scope_limited_v1, S17):", DIM, 12, "400", "start"))
o.append(tokyo_chip(560, 212, 1.0, repaired=True))
w("tokyo_fragment_chip_v1.svg", svg_doc(1280, 280, "".join(o)))

# 6) star-map: nodes JSON (truth) + S16b labeled SVG + S22 pure constellation
w("wiki_starmap_nodes_v1.json", json.dumps({"nodes": STARMAP_NODES, "edges": STARMAP_EDGES,
  "_contract": "single truth source: wiki_starmap_v1.svg (S16b, labeled) and constellation_layout_v1.svg (S22, ZERO text) both derive from these coordinates — never re-layout by eye."}, indent=1))

W, H = 1280, 720
pos = {n["id"]: (n["x"] * W, n["y"] * H) for n in STARMAP_NODES}


def star(x, y, color, mag, glow=True):
    s = []
    if glow:
        s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{14 * mag:.1f}" fill="{color}" opacity="0.13"/>')
    s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{5.5 * mag:.1f}" fill="{color}" opacity="0.95"/>')
    return "".join(s)


def edges_svg(dim=False):
    s = []
    for a, b in STARMAP_EDGES:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        ember = any(n["id"] in (a, b) and n["kind"] == "ember" for n in STARMAP_NODES)
        op = 0.18 if (ember or dim) else 0.42
        col = RED if ember else INK
        s.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{col}" stroke-width="1.4" opacity="{op}"/>')
    return "".join(s)


# S16b — labeled star-map (only the 4 gated labels are BIG: RESEARCH WIKI / REJECT / WARN_corrected / ACCEPT)
o = [edges_svg()]
for n in STARMAP_NODES:
    x, y = pos[n["id"]]
    o.append(star(x, y, STAR_COLOR[n["kind"]], n["mag"] * (0.7 if n["kind"] == "ember" else 1.0)))
o.append(text(W / 2, 52, "RESEARCH WIKI", INK, 30, "800", spacing="6"))
o.append(text(W / 2, 76, "the night, written into memory", DIM, 12, "400"))
o.append(ddl_chip(W - 210, 44, "T-02:41", "amber", "dash", scale=0.95))
for nid, dy in [("REJECT", 30), ("WARN_corrected", 30), ("ACCEPT", -18)]:
    x, y = pos[nid]
    o.append(text(x, y + dy, nid, STAR_COLOR[next(n["kind"] for n in STARMAP_NODES if n["id"] == nid)], 20, "800"))
for nid, lbl in [("idea", "idea"), ("novelty", "novelty"), ("experiment", "experiment"), ("paper", "paper"), ("sanitizer", "sanitizer")]:
    x, y = pos[nid]
    o.append(text(x, y + 24, lbl, DIM, 11, "400"))
w("wiki_starmap_v1.svg", svg_doc(W, H, "".join(o)))

# S22 — PURE constellation: ZERO text, derived from the SAME coordinates; paper-star thread → tiny warm window
o = [edges_svg(dim=True)]
for n in STARMAP_NODES:
    x, y = pos[n["id"]]
    mag = n["mag"] * (0.6 if n["kind"] == "ember" else 1.0)
    o.append(star(x, y, STAR_COLOR[n["kind"]], mag))
px, py = pos["paper"]
wx, wy = W * 0.84, H * 0.93
o.append(f'<line x1="{px:.0f}" y1="{py:.0f}" x2="{wx:.0f}" y2="{wy:.0f}" stroke="{WARM}" stroke-width="1.2" opacity="0.5"/>')
o.append(rect(wx - 9, wy - 7, 18, 14, WARM, 2))          # the single warm pixel-window (back to B01)
o.append(rect(wx - 30, wy + 7, 60, 5, "#10131F", 1))      # rooftop silhouette
svg = svg_doc(W, H, "".join(o))
assert "<text" not in svg, "constellation must contain ZERO text"
w("constellation_layout_v1.svg", svg)

print("ASSET LIBRARY OK")
