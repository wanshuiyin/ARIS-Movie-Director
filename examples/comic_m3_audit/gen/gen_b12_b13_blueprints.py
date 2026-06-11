#!/usr/bin/env python3
"""gen_b12_b13_blueprints.py — S20 SUBMITTED status bar + S21 screen high-five frame.
(S22 reuses constellation_layout_v1.svg — already derived from the star-map coordinate truth file.)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import svg_doc, text, rect, ddl_chip, INK, DIM, GREEN, ST

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def w(name, content):
    open(os.path.join(A, name), "w").write(content)
    print("wrote", name)


# ── S20: the laptop's one green status band (the panel's star is the COLD mug, not this) ──
W, H = 760, 220
o = [rect(40, 40, 680, 140, "#0B1020", 14, ST, 2)]
o.append(rect(70, 70, 230, 44, "#0E2A22", 9, GREEN, 2))
o.append(text(185, 99, "SUBMITTED ✓", GREEN, 22, "800"))
o.append(ddl_chip(340, 70, "T-00:27", "green", "dash", scale=1.25))
o.append(text(380, 156, "receipt logged · all done · she can sleep", DIM, 13, "400"))
w("s20_submitted_bar_v1.svg", svg_doc(W, H, "".join(o)))

# ── S21: the screen high-five frame (top bar MUST be large enough to blind-transcribe) ──
W, H = 1000, 600
o = [rect(60, 40, 880, 520, "#0B1020", 18, ST, 3)]
o.append(rect(60, 40, 880, 64, "#10162B", 18))
o.append(rect(330, 52, 230, 42, "#0E2A22", 9, GREEN, 2))
o.append(text(445, 80, "SUBMITTED ✓", GREEN, 22, "800"))
o.append(text(860, 82, "ARIS", DIM, 20, "800", "end"))
# center left open for the duo (condition注入); palm-contact glow marker placeholder
o.append(f'<circle cx="500" cy="330" r="84" fill="{GREEN}" opacity="0.07"/>')
o.append(f'<circle cx="500" cy="330" r="46" fill="{GREEN}" opacity="0.10"/>')
o.append(text(500, 540, "", DIM, 10, "400"))
w("screen_highfive_frame_v1.svg", svg_doc(W, H, "".join(o)))
print("B12 BLUEPRINTS OK (S22 uses constellation_layout_v1)")
