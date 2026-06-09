#!/usr/bin/env python3
"""gen_method_diagram.py — the dllm method figure: random-mask vs schema-keyword-first denoising.

Deterministic 1280x720 SVG "DLLM JSON UNMASKING — ORDER MATTERS" (the cross-model-converged
two-row denoising filmstrip). Same target JSON grows L->R across denoising steps in BOTH rows;
only the UNMASK ORDER differs. Top = random-mask -> structure commits late/interleaved -> a value
splits across a token boundary -> exact_parse FAIL (red). Bottom = schema-keyword-first -> the
{} + KEY skeleton locks first -> values fill fixed slots -> exact_parse OK (green).

Doubles as (a) the standalone overlay and (b) the S12 blueprint content-authority. Side gutters
(x<184, x>1096) left blank = reserved chibi zones for the blueprint.

Usage: python3 gen_method_diagram.py   -> writes method_random_vs_schema_first_v1.svg (+ _num variant)
"""
import os

W, H = 1280, 720
BG = "#12182E"; BOARD = "#171F38"; STROKE = "#2A3552"
INK = "#E4E9F7"; DIM = "#8C97B8"; MASK = "#33405F"
BLUE = "#5B8Cff"; KEY = "#7FB0FF"; VAL = "#9CE0B4"; PUNC = "#6E7CA8"
RED = "#FF3366"; GREEN = "#00C896"; AMBER = "#FFB000"
MONO = "JetBrains Mono, 'SF Mono', Menlo, monospace"

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def rect(x, y, w, h, fill, rx=8, stroke="none", sw=0, op=1.0):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" opacity="{op}"'
    if stroke != "none": s += f' stroke="{stroke}" stroke-width="{sw}"'
    return s + "/>"

def text(x, y, s, fill=INK, size=15, weight="400", anchor="start", mono=True, ls="0"):
    fam = MONO if mono else "Inter, sans-serif"
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" '
            f'font-family="{fam}" text-anchor="{anchor}" letter-spacing="{ls}">{esc(s)}</text>')

def arrow(x1, y, x2, color=DIM):
    return (f'<line x1="{x1}" y1="{y}" x2="{x2-7}" y2="{y}" stroke="{color}" stroke-width="2"/>'
            f'<path d="M{x2-7},{y-5} L{x2},{y} L{x2-7},{y+5} Z" fill="{color}"/>')

# a small JSON-cell: lines = list of (segments) where seg = (text, color) or ("MASK", n)
def cell(x, y, w, h, title, lines, border, title_color):
    out = [rect(x, y, w, h, BOARD, rx=10, stroke=border, sw=2)]
    out.append(text(x + 12, y + 22, title, fill=title_color, size=12, weight="700"))
    ly = y + 46
    for line in lines:
        lx = x + 14
        for seg in line:
            if seg[0] == "MASK":
                n = seg[1]
                out.append(rect(lx, ly - 12, 13 * n, 15, MASK, rx=3))
                lx += 13 * n + 3
            else:
                t, c = seg
                out.append(text(lx, ly, t, fill=c, size=13.5))
                lx += int(len(t) * 8.0) + 2
        ly += 22
    return "\n".join(out)

# token shorthands
def k(s): return (s, KEY)
def v(s): return (s, VAL)
def p(s): return (s, PUNC)
def m(n): return ("MASK", n)

def build(with_numbers: bool):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    o.append(rect(0, 0, W, H, BG, rx=0))
    # board
    o.append(rect(184, 60, 912, 600, BOARD, rx=16, stroke=STROKE, sw=2, op=0.55))
    o.append(text(640, 100, "DLLM JSON UNMASKING — ORDER MATTERS", fill=INK, size=22, weight="800", anchor="middle"))
    o.append(text(640, 124, "same target JSON · same model · only the unmask ORDER differs", fill=DIM, size=13, anchor="middle"))

    # shared start node t0
    o.append(cell(206, 250, 120, 150, "t0 · all [MASK]",
                  [[m(6)], [m(4)], [m(7)], [m(5)]], STROKE, DIM))
    o.append(text(266, 420, "shared start", fill=DIM, size=11, anchor="middle"))
    # fork lines from t0 to both rows
    o.append(f'<path d="M326,300 C360,300 360,210 396,210" stroke="{RED}" stroke-width="2" fill="none" opacity="0.7"/>')
    o.append(f'<path d="M326,350 C360,350 360,470 396,470" stroke="{GREEN}" stroke-width="2" fill="none" opacity="0.7"/>')

    cx = [396, 588, 780]   # t1,t2,t3 x
    cw = 150
    # ---------- TOP: random-mask ----------
    yr = 150
    o.append(text(206, yr + 20, "RANDOM", fill=RED, size=15, weight="800"))
    o.append(text(206, yr + 40, "MASK", fill=RED, size=15, weight="800"))
    # t1: values revealed first, no structure
    o.append(cell(cx[0], yr, cw, 130, "t1 · scattered",
                  [[m(1), v('"Tokyo"'), m(2)], [m(3), v('1603')], [m(5)]], "#5A2740", RED))
    o.append(cell(cx[1], yr, cw, 130, "t2 · interleaved",
                  [[p("{"), m(2), v('"Tok')], [v('yo"'), m(3)], [m(2), v('1603')]], "#5A2740", RED))
    o.append(cell(cx[2], yr, cw, 130, "t3 · structure late",
                  [[p('{'), k('"city"'), p(':')], [v('"Tok'), ("|", RED), v('yo"')], [m(2), p('}')]], "#5A2740", RED))
    for a, b in [(cx[0]+cw, cx[1]), (cx[1]+cw, cx[2])]:
        o.append(arrow(a + 4, yr + 65, b - 4, RED))
    # result FAIL
    rx0 = 956
    o.append(rect(rx0, yr, 120, 130, "#241019", rx=10, stroke=RED, sw=2))
    o.append(text(rx0 + 60, yr + 26, "exact_parse", fill=RED, size=12, weight="700", anchor="middle"))
    o.append(text(rx0 + 60, yr + 46, "✗ FAIL", fill=RED, size=18, weight="800", anchor="middle"))
    o.append(text(rx0 + 60, yr + 78, '"Tok|yo"', fill=RED, size=13, anchor="middle"))
    o.append(text(rx0 + 60, yr + 98, "span 跨边界切碎", fill=DIM, size=10.5, anchor="middle", mono=False))
    o.append(arrow(cx[2]+cw + 4, yr + 65, rx0 - 4, RED))

    # ---------- BOTTOM: schema-keyword-first ----------
    yb = 410
    o.append(text(206, yb + 20, "SCHEMA-", fill=GREEN, size=15, weight="800"))
    o.append(text(206, yb + 40, "KEYWORD", fill=GREEN, size=15, weight="800"))
    o.append(text(206, yb + 60, "-FIRST", fill=GREEN, size=15, weight="800"))
    # t1: skeleton (braces + keys) locks first, values masked
    o.append(cell(cx[0], yb, cw, 130, "t1 · skeleton locks",
                  [[p('{'), k('"city"'), p(':'), m(3)], [k('"pop"'), p(':'), m(3)], [k('"founded"'), p(':'), m(2), p('}')]], "#1F5C4A", GREEN))
    o.append(cell(cx[1], yb, cw, 130, "t2 · fill slots",
                  [[p('{'), k('"city"'), p(':'), v('"Tokyo"')], [k('"pop"'), p(':'), m(3)], [k('"founded"'), p(':'), m(2), p('}')]], "#1F5C4A", GREEN))
    o.append(cell(cx[2], yb, cw, 130, "t3 · values in",
                  [[p('{'), k('"city"'), p(':'), v('"Tokyo"')], [k('"pop"'), p(':'), v('13.9M')], [k('"founded"'), p(':'), v('1603'), p('}')]], "#1F5C4A", GREEN))
    for a, b in [(cx[0]+cw, cx[1]), (cx[1]+cw, cx[2])]:
        o.append(arrow(a + 4, yb + 65, b - 4, GREEN))
    o.append(rect(rx0, yb, 120, 130, "#0E2A22", rx=10, stroke=GREEN, sw=2))
    o.append(text(rx0 + 60, yb + 26, "exact_parse", fill=GREEN, size=12, weight="700", anchor="middle"))
    o.append(text(rx0 + 60, yb + 46, "✓ OK", fill=GREEN, size=18, weight="800", anchor="middle"))
    o.append(text(rx0 + 60, yb + 78, '"Tokyo"', fill=GREEN, size=13, anchor="middle"))
    o.append(text(rx0 + 60, yb + 98, "span ⊆ schema", fill=DIM, size=10.5, anchor="middle"))
    o.append(arrow(cx[2]+cw + 4, yb + 65, rx0 - 4, GREEN))

    # key takeaway strip
    o.append(text(640, 626, "keys + braces unmask FIRST  →  values can't break the schema boundary",
                  fill=INK, size=14, weight="600", anchor="middle"))

    if with_numbers:
        o.append(rect(196, 56, 168, 30, "#1A1330", rx=8, stroke=AMBER, sw=1.5))
        o.append(text(280, 76, "schema-first  +6.2 → +1.4", fill=AMBER, size=12.5, weight="700", anchor="middle"))

    o.append("</svg>")
    return "\n".join(o)

if __name__ == "__main__":
    d = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(d, "..", "assets_new")
    os.makedirs(out, exist_ok=True)
    for nm, num in [("method_random_vs_schema_first_v1.svg", False),
                    ("method_random_vs_schema_first_v1_num.svg", True)]:
        open(os.path.join(out, nm), "w").write(build(num))
        print("wrote", nm)
