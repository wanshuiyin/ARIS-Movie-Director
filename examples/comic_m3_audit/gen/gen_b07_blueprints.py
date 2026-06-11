#!/usr/bin/env python3
"""gen_b07_blueprints.py — B07: the pinned broken-JSON zoom (S10) + the ROUND-1 REJECT verdict card (S11,
sharing the verdict-card geometry that S16's ACCEPT will mirror)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import (svg_doc, text, rect, ddl_chip, tokyo_chip, verdict_card, curve_panel,
                       INK, DIM, GREEN, AMBER, RED, ST)

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def w(name, content):
    open(os.path.join(A, name), "w").write(content)
    print("wrote", name)


# ── S10: tokyo_parse_error_zoom — the hero chip pinned dead-center ─────────────
W, H = 1180, 660
o = []
# left edge: the 0.71→0.66 dip strip
o.append(curve_panel(36, 110, 300, 210, [(0.0, 0.71), (0.3, 0.70), (0.55, 0.69), (0.78, 0.675), (1.0, 0.66)],
                     "0.71→0.66", RED, dip_at=4))
o.append(text(336 - 36, 96, "ghost: 0.71", DIM, 12, "400", "end"))
o.append(rect(208, 268, 96, 38, "#241019", 7, RED, 2))
o.append(text(256, 295, "0.66", RED, 25, "800"))
# center: the HERO Tok|yo chip, giant, with a hard crack through the |
o.append(f'<circle cx="{W/2+60}" cy="{H/2-20}" r="240" fill="{RED}" opacity="0.06"/>')
o.append(tokyo_chip(W / 2 - 240, H / 2 - 120, scale=3.1))
o.append(f'<path d="M{W/2+96},{H/2-130} l -18,52 l 26,18 l -14,46" stroke="{RED}" stroke-width="5" fill="none" opacity="0.9"/>')
# pin + thread back to the tiny S09 thumbnail (bottom-left)
o.append(f'<circle cx="{W/2+60}" cy="{H/2-130}" r="10" fill="{AMBER}"/>')
o.append(f'<line x1="{W/2+60}" y1="{H/2-130}" x2="170" y2="{H-80}" stroke="{AMBER}" stroke-width="1.6" opacity="0.5" stroke-dasharray="6 5"/>')
o.append(tokyo_chip(120, H - 96, scale=0.27))
o.append(text(120 + 26, H - 104, "S09 · corner", DIM, 10, "400"))
# terminal line under the hero chip → ParseError
o.append(rect(W / 2 - 250, H / 2 + 64, 620, 56, "#0B1020", 9, ST, 1.5))
o.append(text(W / 2 - 228, H / 2 + 99, 'json.loads(sample_1207)  →', INK, 18, "700", "start"))
o.append(rect(W / 2 + 168, H / 2 + 72, 196, 42, "#241019", 9, RED, 2.4))
o.append(text(W / 2 + 266, H / 2 + 101, "ParseError", RED, 22, "800"))
o.append(text(W / 2 - 240, H / 2 + 150, "batch 2048/2048 · 37 malformed", DIM, 14, "400", "start"))
o.append(ddl_chip(W - 220, 40, "T-16:21", "amber", "dash", scale=1.05))
w("tokyo_parse_error_zoom_v1.svg", svg_doc(W, H, "".join(o)))

# ── S11: REJECT verdict card (the geometry S16's ACCEPT will mirror) ───────────
W, H = 1180, 660
o = []
o.append(f'<circle cx="{W/2}" cy="{H/2}" r="260" fill="{RED}" opacity="0.05"/>')
o.append(verdict_card(
    W / 2 - 280, H / 2 - 190,
    "REVIEW · ROUND 1",
    [("2048 samples scored", INK, 22),
     ("evaluator: exact_parse", DIM, 16),
     ("evidence attached:", DIM, 16)],
    "REJECT",
    big_chip=("37", "malformed", RED),
    scale=1.0, tilt=-6))
# the Tok|yo thumbnail clipped onto the card as evidence
o.append(tokyo_chip(W / 2 - 240, H / 2 + 16, scale=0.62))
# impact sparks
for dx, dy in [(-320, -210), (310, -190), (-340, 180), (330, 200)]:
    o.append(f'<path d="M{W/2+dx},{H/2+dy} l 14,-6 m -14,6 l 6,14" stroke="{RED}" stroke-width="3" opacity="0.7" fill="none"/>')
# dim 0.66 flatline ghost behind
o.append(rect(60, 80, 250, 130, "#0B1020", 9, ST, 1, opacity=0.55))
o.append(f'<path d="M80,150 L290,158" stroke="{RED}" stroke-width="2.5" opacity="0.5"/>')
o.append(text(185, 196, "0.66 · flat", DIM, 12, "400"))
# loop arrow relief on the floor (the loop restarts)
o.append(f'<path d="M420,{H-56} a 36,16 0 1 1 72,0" stroke="{ST}" stroke-width="3" fill="none" opacity="0.7"/>')
o.append(f'<path d="M492,{H-56} l -8,-7 m 8,7 l -10,4" stroke="{ST}" stroke-width="3" fill="none" opacity="0.7"/>')
o.append(ddl_chip(W - 256, 40, "T-16:05", "amber", "dash", scale=1.45))   # BIG this panel: the burned time is the cost
w("reject_verdict_round1_v1.svg", svg_doc(W, H, "".join(o)))
print("B07 BLUEPRINTS OK")
