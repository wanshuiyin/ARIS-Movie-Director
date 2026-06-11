#!/usr/bin/env python3
"""asset_lib.py — shared single-source builders for the canonical asset library (storyboard §asset_requests).

Every cross-panel element (DDL chip, stamps, mug states, wandb curve, Tok|yo chip, star-map) renders from
THESE functions so the film never grows two visual dialects. Per-panel gens import from here.
Palette = comic.json ui_tokens; stamp geometry matches the already-baked S15 WARN_corrected look
(amber rounded-rect border + bold mono label).
"""

MONO = "JetBrains Mono, Menlo, monospace"
RED = "#FF3366"; AMBER = "#FFB000"; PURPLE = "#B066FF"; GREEN = "#00C896"
VOID = "#0A0E27"; BOARD = "#171F38"; ST = "#2A3552"; INK = "#E4E9F7"; DIM = "#8C97B8"
WARM = "#FFB46B"


def text(x, y, s, fill=INK, size=15, weight="700", anchor="middle", spacing=None):
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}"'
            f' font-family="{MONO}" text-anchor="{anchor}"{sp}>{s}</text>')


def rect(x, y, w, h, fill, rx=10, stroke=None, sw=0, opacity=1.0):
    e = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" opacity="{opacity}"'
    if stroke:
        e += f' stroke="{stroke}" stroke-width="{sw}"'
    return e + "/>"


def svg_doc(w, h, body, bg=VOID):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            + rect(0, 0, w, h, bg, 0) + body + "</svg>")


# ── #1 DDL widget — the single timeline authority ──────────────────────────────
def ddl_chip(x, y, t, state="amber", skin="corner", submitted=False, scale=1.0):
    """state: amber|red|green. skin: corner (screen-corner chip) | phone (lockscreen) | dash (dashboard)."""
    c = {"amber": AMBER, "red": RED, "green": GREEN}[state]
    s = scale
    o = []
    if skin == "phone":
        w, h = 150 * s, 64 * s
        o.append(rect(x, y, w, h, "#0B1020", 12 * s, ST, 1.5))
        o.append(text(x + w / 2, y + 22 * s, "ARIS · running", DIM, 10 * s, "400"))
        o.append(text(x + w / 2, y + 47 * s, t, c, 19 * s, "800"))
    elif skin == "dash":
        w, h = 168 * s, 44 * s
        o.append(rect(x, y, w, h, "#0B1020", 8 * s, c, 1.5))
        o.append(text(x + 14 * s, y + 28 * s, "DDL", DIM, 12 * s, "700", "start"))
        o.append(text(x + w - 12 * s, y + 28 * s, t, c, 17 * s, "800", "end"))
    else:  # corner
        w, h = 132 * s, 34 * s
        o.append(rect(x, y, w, h, "#0B1020", 7 * s, c, 1.5))
        o.append(text(x + w / 2, y + 23 * s, t, c, 16 * s, "800"))
    if submitted:
        o.append(rect(x, y - 26 * s, 118 * s, 22 * s, "#0E2A22", 6 * s, GREEN, 1.2))
        o.append(text(x + 59 * s, y - 10 * s, "SUBMITTED ✓", GREEN, 12 * s, "800"))
    return "".join(o)


# ── #2 stamp family — matches the baked S15 WARN_corrected geometry ────────────
STAMPS = {
    "DUP":            (RED,   "#241019"),
    "SURVIVES":       (GREEN, "#0E2A22"),
    "REJECT":         (RED,   "#241019"),
    "ACCEPT":         (GREEN, "#0E2A22"),
    "WARN_corrected": (AMBER, "#1A1330"),
    "SUBMITTED":      (GREEN, "#0E2A22"),
    "AUDIT":          (AMBER, "#1A1330"),
}


def stamp(x, y, label, scale=1.0, tilt=0):
    c, bgc = STAMPS[label]
    s = scale
    w = (34 + 17 * len(label)) * s
    h = 52 * s
    glyph = "⚠ " if label in ("WARN_corrected", "AUDIT") else ""
    body = (rect(x, y, w, h, bgc, 10 * s, c, 3 * s)
            + text(x + w / 2, y + h / 2 + 9 * s, glyph + label, c, 26 * s, "800"))
    if tilt:
        return f'<g transform="rotate({tilt} {x + w / 2} {y + h / 2})">{body}</g>'
    return body


def mini_stamp_glyph(x, y, kind, scale=1.0):
    """tiny node glyphs for the star-map: red/amber/green dots with ring."""
    c = {"fail": RED, "audit": AMBER, "ok": GREEN}[kind]
    s = scale
    return (f'<circle cx="{x}" cy="{y}" r="{7 * s}" fill="{c}" opacity="0.9"/>'
            f'<circle cx="{x}" cy="{y}" r="{11 * s}" fill="none" stroke="{c}" stroke-width="{1.5 * s}" opacity="0.45"/>')


# ── #4 mug — HER 'ML RESEARCH' motif cup, three states ─────────────────────────
def mug(x, y, state="hot", scale=1.0):
    """state: hot (two steady plumes) | fading (one thin wisp) | cold (no steam + milk film)."""
    s = scale
    o = [rect(x, y, 84 * s, 74 * s, "#5A6B85", 9 * s, "#3D4A60", 2 * s),
         rect(x + 84 * s, y + 14 * s, 20 * s, 34 * s, "none", 9 * s, "#3D4A60", 5 * s),
         rect(x + 8 * s, y + 26 * s, 68 * s, 26 * s, "#E8EDF7", 4 * s)]
    o.append(text(x + 42 * s, y + 38 * s, "ML", "#243049", 11 * s, "800"))
    o.append(text(x + 42 * s, y + 49 * s, "RESEARCH", "#243049", 8.5 * s, "800"))
    if state == "cold":
        o.append(rect(x + 7 * s, y + 4 * s, 70 * s, 7 * s, "#C9CFBE", 3.5 * s, opacity=0.95))  # milk film
    if state == "hot":
        for dx in (24, 56):
            o.append(f'<path d="M{x + dx * s},{y - 6 * s} c {6 * s},{-10 * s} {-6 * s},{-18 * s} {2 * s},{-30 * s}"'
                     f' stroke="{INK}" stroke-width="{3 * s}" fill="none" opacity="0.65" stroke-linecap="round"/>')
    elif state == "fading":
        o.append(f'<path d="M{x + 40 * s},{y - 6 * s} c {4 * s},{-8 * s} {-4 * s},{-14 * s} {1.5 * s},{-24 * s}"'
                 f' stroke="{INK}" stroke-width="{2 * s}" fill="none" opacity="0.32" stroke-linecap="round"/>')
    return "".join(o)


# ── #5 wandb exact_parse curve template ────────────────────────────────────────
def curve_panel(x, y, w, h, pts, label, color=GREEN, dip_at=None, callout=None):
    """pts: [(t,v)] with v in 0..1 plotted in the box; label like '0.60→0.71'."""
    o = [rect(x, y, w, h, "#0B1020", 10, ST, 1.5),
         text(x + 14, y + 22, "wandb · exact_parse", DIM, 11, "400", "start")]
    x0, y0, iw, ih = x + 16, y + h - 18, w - 32, h - 56
    for fv in (0.6, 0.8):
        gy = y0 - fv * ih
        o.append(f'<line x1="{x0}" y1="{gy}" x2="{x0 + iw}" y2="{gy}" stroke="{ST}" stroke-width="1" opacity="0.5"/>')
        o.append(text(x0 - 2, gy + 4, f"{fv:.1f}", DIM, 9, "400", "end"))
    path = " ".join(f"{'M' if i == 0 else 'L'}{x0 + t * iw:.1f},{y0 - v * ih:.1f}" for i, (t, v) in enumerate(pts))
    o.append(f'<path d="{path}" stroke="{color}" stroke-width="3" fill="none" stroke-linejoin="round"/>')
    tx, tv = pts[-1]
    o.append(f'<circle cx="{x0 + tx * iw:.1f}" cy="{y0 - tv * ih:.1f}" r="4.5" fill="{color}"/>')
    o.append(text(x + w - 12, y + 22, label, color, 15, "800", "end"))
    if dip_at is not None:
        dt, dv = pts[dip_at]
        o.append(f'<circle cx="{x0 + dt * iw:.1f}" cy="{y0 - dv * ih:.1f}" r="7" fill="none" stroke="{RED}" stroke-width="2.5"/>')
    if callout:
        o.append(rect(x + w - 96, y + h - 44, 84, 30, "#1A1330", 7, AMBER, 1.5))
        o.append(text(x + w - 54, y + h - 23, callout, AMBER, 16, "800"))
    return "".join(o)


# ── #6 Tok|yo broken-JSON chip (multi-scale, one source) ───────────────────────
def tokyo_chip(x, y, scale=1.0, repaired=False):
    s = scale
    w, h = 196 * s, 40 * s
    if repaired:
        return (rect(x, y, w, h, "#0E2A22", 8 * s, GREEN, 1.6 * s)
                + text(x + w / 2, y + h / 2 + 5.5 * s, '{"city":"Tokyo"} ✓', GREEN, 15 * s, "700"))
    body = (rect(x, y, w, h, "#241019", 8 * s, RED, 1.6 * s)
            + text(x + w / 2, y + h / 2 + 5.5 * s, '{"city":"Tok|yo"}', RED, 15 * s, "700")
            + f'<path d="M{x + w * 0.56},{y + 3 * s} l {-5 * s},{h * 0.45} l {7 * s},{h * 0.2} l {-4 * s},{h * 0.3}"'
              f' stroke="{RED}" stroke-width="{1.6 * s}" fill="none" opacity="0.8"/>')
    return body


# ── #7 wiki star-map — node coordinates, ONE truth source for S16b + S22 ───────
# main path: idea → experiment → REJECT → audit → WARN_corrected → ACCEPT → paper
STARMAP_NODES = [
    {"id": "idea",           "x": 0.10, "y": 0.72, "kind": "main",  "mag": 1.0},
    {"id": "novelty",        "x": 0.20, "y": 0.58, "kind": "main",  "mag": 0.8},
    {"id": "experiment",     "x": 0.33, "y": 0.46, "kind": "main",  "mag": 1.0},
    {"id": "REJECT",         "x": 0.45, "y": 0.60, "kind": "fail",  "mag": 1.1},
    {"id": "audit",          "x": 0.57, "y": 0.42, "kind": "audit", "mag": 1.2},
    {"id": "WARN_corrected", "x": 0.67, "y": 0.55, "kind": "audit", "mag": 1.1},
    {"id": "ACCEPT",         "x": 0.78, "y": 0.38, "kind": "ok",    "mag": 1.1},
    {"id": "paper",          "x": 0.88, "y": 0.20, "kind": "paper", "mag": 1.6},
    # failure side-branches (dim ember): killed ideas + the sanitizer ghost
    {"id": "idea_dup1",      "x": 0.06, "y": 0.50, "kind": "ember", "mag": 0.5},
    {"id": "idea_dup2",      "x": 0.14, "y": 0.38, "kind": "ember", "mag": 0.45},
    {"id": "sanitizer",      "x": 0.50, "y": 0.26, "kind": "ember", "mag": 0.6},
    {"id": "inflated_62",    "x": 0.40, "y": 0.18, "kind": "ember", "mag": 0.5},
]
STARMAP_EDGES = [
    ["idea", "novelty"], ["novelty", "experiment"], ["experiment", "REJECT"],
    ["REJECT", "audit"], ["audit", "WARN_corrected"], ["WARN_corrected", "ACCEPT"], ["ACCEPT", "paper"],
    ["idea", "idea_dup1"], ["idea", "idea_dup2"], ["audit", "sanitizer"], ["sanitizer", "inflated_62"],
]
STAR_COLOR = {"main": INK, "fail": RED, "audit": AMBER, "ok": GREEN, "paper": "#FFFFFF", "ember": RED}


# ── shared verdict-card geometry — S11 REJECT and S16 ACCEPT instantiate the SAME card (mirror pair) ──
def verdict_card(x, y, header, body_rows, stamp_label, big_chip=None, scale=1.0, tilt=-4):
    """body_rows: list of (text, color, size). big_chip: (value, label, color) rendered huge.
    The card face/geometry is identical across instantiations; only contents + stamp differ."""
    s = scale
    w_, h_ = 560 * s, 360 * s
    o = [rect(x, y, w_, h_, "#0E1322", 16 * s, ST, 2.5 * s)]
    o.append(rect(x, y, w_, 54 * s, "#10162B", 16 * s))
    o.append(text(x + w_ / 2, y + 36 * s, header, DIM, 20 * s, "800"))
    ty = y + 100 * s
    for t_, c_, sz in body_rows:
        o.append(text(x + 36 * s, ty, t_, c_, sz * s, "700", "start"))
        ty += (sz + 18) * s
    if big_chip:
        val, lbl, c_ = big_chip
        o.append(rect(x + w_ - 220 * s, y + 86 * s, 184 * s, 120 * s, "#241019" if c_ == RED else "#0E2A22", 12 * s, c_, 2.5 * s))
        o.append(text(x + w_ - 128 * s, y + 162 * s, val, c_, 56 * s, "800"))
        o.append(text(x + w_ - 128 * s, y + 192 * s, lbl, DIM, 13 * s, "400"))
    o.append(stamp(x + w_ * 0.16, y + h_ - 110 * s, stamp_label, scale=1.5 * s, tilt=tilt))
    return "".join(o)
