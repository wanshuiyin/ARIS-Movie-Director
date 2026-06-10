#!/usr/bin/env python3
"""gen_b03_blueprints.py — B03 content blueprints: S03 phone lock-screen anchor + S04 idea deck."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import svg_doc, text, rect, ddl_chip, INK, DIM, GREEN, AMBER, RED, PURPLE, ST

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def w(name, content):
    open(os.path.join(A, name), "w").write(content)
    print("wrote", name)


# S03 — phone lock-screen card: ARIS RUNNING + DDL T-19:42 (small anchor, must be crisp)
o = [rect(40, 30, 360, 230, "#0B1020", 26, ST, 2.5)]
o.append(rect(180, 44, 80, 8, "#1B2440", 4))                       # speaker notch
o.append(text(220, 110, "ARIS RUNNING", GREEN, 30, "800"))
o.append(f'<circle cx="118" cy="100" r="7" fill="{GREEN}"><animate attributeName="opacity" values="1"/></circle>')
o.append(ddl_chip(112, 140, "T-19:42", "amber", "dash", scale=1.6))
o.append(text(220, 242, "no action needed", DIM, 13, "400"))
w("s03_phone_lock_v1.svg", svg_doc(440, 290, "".join(o)))

# S04 — IDEA DECK: 20 cards fanned, badge `20 IDEAS`, only #01 readable, others blurred blocks, DDL chip
W, H = 1100, 620
o = []
cx, cy = W / 2, H + 160                      # fan pivot below frame
colors = ["#1B2440", "#15263A", "#1A1F3D", "#142433", "#1D1B38"]
for i in range(20):
    ang = -62 + i * (124 / 19)               # fan spread
    r = 470
    x = cx + r * math.sin(math.radians(ang))
    y = cy - r * math.cos(math.radians(ang))
    rot = ang * 0.85
    is_front = (i == 9)                       # the single readable card
    cw, ch = (188, 116) if is_front else (150, 96)
    fill = "#0E2A22" if is_front else colors[i % 5]
    stroke = GREEN if is_front else ST
    card = rect(-cw / 2, -ch / 2, cw, ch, fill, 10, stroke, 2.4 if is_front else 1.2)
    if is_front:
        card += text(0, -12, "#01", GREEN, 26, "800")
        card += text(0, 22, "schema-first", INK, 21, "800")
    else:
        # visibly blurred/de-detailed: tone bars only, NO readable glyphs (codex fix — no secondary readable cards)
        card += rect(-cw / 2 + 14, -18, cw - 28, 10, "#2A3552", 4, opacity=0.8)
        card += rect(-cw / 2 + 14, 2, cw * 0.5, 8, "#222B45", 4, opacity=0.7)
    g = f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.1f})" opacity="{1.0 if is_front else 0.82}">{card}</g>'
    if is_front:
        front_g = g          # render the readable card LAST so neighbours can't cover its gated text
    else:
        o.append(g)
o.append(front_g)            # readable #01 card on top of the fan
# generator nozzle + glow
o.append(f'<circle cx="{cx}" cy="{H - 26}" r="40" fill="{PURPLE}" opacity="0.16"/>')
o.append(rect(cx - 34, H - 44, 68, 30, "#10162B", 8, PURPLE, 1.6))
# count badge
o.append(rect(W / 2 - 120, 26, 240, 64, "#1A1330", 14, AMBER, 2.5))
o.append(text(W / 2, 70, "20 IDEAS", AMBER, 34, "800"))
o.append(ddl_chip(W - 230, H - 76, "T-19:42", "amber", "dash", scale=1.1))
w("idea_deck_20_v1.svg", svg_doc(W, H, "".join(o)))
print("B03 BLUEPRINTS OK")
