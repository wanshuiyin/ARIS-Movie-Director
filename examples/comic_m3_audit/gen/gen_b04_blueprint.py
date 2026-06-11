#!/usr/bin/env python3
"""gen_b04_blueprint.py — S05 NOVELTY GATE: 20 cards → 6 burn (DUP) / 14 survive; 14/20 + SURVIVES."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import svg_doc, text, rect, ddl_chip, stamp, INK, DIM, GREEN, AMBER, RED, ST

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
W, H = 1180, 660
o = []

# the gate: a glowing wall of literature spines (two readable, rest blurred)
o.append(rect(470, 70, 60, 470, "#10162B", 6, AMBER, 2))
for i in range(11):
    y = 86 + i * 40
    if i == 2:
        o.append(rect(476, y, 48, 30, "#1B2440", 3, ST, 1)); o.append(f'<g transform="rotate(90 500 {y+15})">{text(500, y+19, "PRIOR ART", DIM, 9, "700")}</g>')
    elif i == 7:
        o.append(rect(476, y, 48, 30, "#1B2440", 3, ST, 1)); o.append(f'<g transform="rotate(90 500 {y+15})">{text(500, y+19, "STRUCTURED OUTPUTS", DIM, 6.5, "700")}</g>')
    else:
        o.append(rect(476, y, 48, 30, "#151B33", 3, opacity=0.85))
o.append(f'<rect x="466" y="60" width="68" height="490" rx="8" fill="none" stroke="{AMBER}" stroke-width="2" opacity="0.5"/>')
o.append(text(500, 46, "NOVELTY GATE", AMBER, 17, "800"))

# LEFT: queue — 6 burned cards (ash + red sparks), one BIG foreground DUP card
for i, (x, y, r) in enumerate([(120, 150, -8), (210, 200, 5), (90, 290, 10), (220, 330, -5), (150, 420, 7)]):
    o.append(f'<g transform="rotate({r} {x+55} {y+34})">' + rect(x, y, 110, 68, "#241019", 8, RED, 1.2, opacity=0.8)
             + rect(x + 14, y + 18, 80, 8, "#3A1B25", 3, opacity=0.8)
             + text(x + 88, y + 58, "DUP", RED, 13, "800") + '</g>')
    o.append(f'<circle cx="{x + 20 + i * 7}" cy="{y - 8}" r="2.4" fill="{RED}" opacity="0.8"/>')
# the BIG blind-transcribable DUP card (foreground)
o.append(f'<g transform="rotate(-6 270 520)">' + rect(180, 462, 190, 116, "#241019", 12, RED, 2.5)
         + rect(202, 488, 130, 10, "#3A1B25", 4)
         + text(275, 520, "arXiv 2024", DIM, 12, "400") + '</g>')
o.append(stamp(208, 522, "DUP", scale=1.05, tilt=-6))

# RIGHT: 14 survivors in green-glow file
for i in range(14):
    col, row = i % 5, i // 5
    x, y = 600 + col * 105, 140 + row * 130
    o.append(rect(x, y, 88, 56, "#0E2A22", 7, GREEN, 1.3, opacity=0.92))
    o.append(rect(x + 12, y + 16, 60, 7, "#1E4435", 3))
    o.append(rect(x + 12, y + 32, 40, 6, "#1A3A2E", 3))
    o.append(f'<circle cx="{x + 44}" cy="{y + 62}" r="14" fill="{GREEN}" opacity="0.06"/>')

# scoreboard + SURVIVES
o.append(rect(700, 470, 200, 78, "#0B1020", 12, GREEN, 2.5))
o.append(text(800, 522, "14/20", GREEN, 40, "800"))
o.append(stamp(930, 484, "SURVIVES", scale=1.1, tilt=4))
o.append(ddl_chip(34, 34, "T-18:55", "amber", "dash", scale=1.1))
open(os.path.join(A, "novelty_gate_14of20_v1.svg"), "w").write(svg_doc(W, H, "".join(o)))
print("wrote novelty_gate_14of20_v1.svg")
