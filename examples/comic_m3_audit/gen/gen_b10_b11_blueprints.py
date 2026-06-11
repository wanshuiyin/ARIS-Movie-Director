#!/usr/bin/env python3
"""gen_b10_b11_blueprints.py — S17 honest paper (repaired Tokyo authored in) + S18 24H sign + S19 submit terminal."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import (svg_doc, text, rect, ddl_chip, stamp, tokyo_chip,
                       INK, DIM, GREEN, AMBER, RED, ST, WARM)

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def w(name, content):
    open(os.path.join(A, name), "w").write(content)
    print("wrote", name)


# ── S17: PAPER — RESULTS (the honest page) ─────────────────────────────────────
W, H = 1180, 660
o = [text(W / 2, 44, "PAPER — RESULTS", INK, 20, "800", spacing="3")]
# the glowing paper page
o.append(rect(120, 80, 600, 500, "#F2EFE6", 8, "#C9C2AE", 2))
o.append(text(420, 124, "Results", "#2A2A33", 22, "800"))
o.append(rect(150, 150, 540, 50, "#1A1330", 6, AMBER, 2))
o.append(text(420, 182, "schema-keyword-first  +1.4 (scope-limited)", AMBER, 19, "800"))
# ghost +6.2 struck through in the margin
o.append(text(660, 232, "+6.2", "#B9B2A0", 16, "700"))
o.append(f'<line x1="630" y1="226" x2="692" y2="230" stroke="{RED}" stroke-width="2" opacity="0.6"/>')
# body lines (abstract)
for i, wd in enumerate([460, 500, 430, 480, 380]):
    o.append(rect(150, 250 + i * 28, wd, 11, "#D9D2BE", 4))
o.append(text(150, 432, "Limitations:", "#2A2A33", 15, "800", "start"))
o.append(text(150, 458, "holds under an external validator", "#6A6453", 14, "400", "start"))
for i, wd in enumerate([420, 360]):
    o.append(rect(150, 478 + i * 24, wd, 10, "#D9D2BE", 4))
# side terminal: the healed Tokyo
o.append(rect(770, 150, 360, 200, "#0B1020", 12, ST, 2))
o.append(text(790, 184, "$ validate results.json", DIM, 14, "400", "start"))
o.append(tokyo_chip(800, 210, scale=1.25, repaired=True))
o.append(text(950, 300, "✓ parsed · 2048/2048 clean", GREEN, 15, "700"))
# claim ledger glow behind (echo of S15)
o.append(rect(770, 390, 360, 130, "#0E1322", 10, ST, 1.2, opacity=0.8))
o.append(text(790, 422, "claim_id  = C7", DIM, 13, "400", "start"))
o.append(text(790, 448, "integrity = WARN_corrected", AMBER, 13, "700", "start"))
o.append(text(790, 474, 'scope     = "external validator"', GREEN, 13, "400", "start"))
o.append(ddl_chip(W - 220, 40, "T-01:57", "amber", "dash", scale=1.0))
w("paper_scope_limited_v1.svg", svg_doc(W, H, "".join(o)))

# ── S18: the OPEN / 24H neon sign (the ONLY salient text of the panel) ─────────
W, H = 620, 420
o = [rect(110, 60, 400, 280, "#241A0E", 18, "#6A4A20", 3)]
o.append(text(310, 175, "OPEN", WARM, 84, "800", spacing="8"))
o.append(text(310, 290, "24H", AMBER, 96, "800", spacing="10"))
o.append(f'<rect x="126" y="76" width="368" height="248" rx="12" fill="none" stroke="{WARM}" stroke-width="3" opacity="0.5"/>')
o.append(f'<rect x="100" y="50" width="420" height="300" rx="20" fill="none" stroke="{AMBER}" stroke-width="2" opacity="0.25"/>')
w("street_24h_sign_v1.svg", svg_doc(W, H, "".join(o)))

# ── S19: SUBMIT terminal ───────────────────────────────────────────────────────
W, H = 1100, 620
o = [rect(170, 60, 760, 480, "#0B1020", 16, ST, 2.5)]
o.append(rect(170, 60, 760, 52, "#10162B", 16))
o.append(text(550, 94, "SUBMIT", INK, 24, "800", spacing="6"))
o.append(text(220, 170, "paper.pdf ✓", INK, 24, "700", "start"))
o.append(text(220, 206, "supplementary.zip ✓", DIM, 16, "400", "start"))
# progress bar 100%
o.append(rect(220, 240, 660, 30, "#10162B", 8, ST, 1.5))
o.append(rect(224, 244, 652, 22, "#0E2A22", 6))
o.append(rect(224, 244, 652, 22, "none", 6, GREEN, 1.5))
o.append(text(550, 261, "100%", "#0A0E27", 15, "800"))
# SUBMITTED stamp centered
o.append(stamp(330, 320, "SUBMITTED", scale=1.7, tilt=-4))
o.append(text(550, 470, "> upload complete · receipt logged to research-wiki", DIM, 14, "400"))
o.append(ddl_chip(700, 488, "T-00:42", "red", "dash", scale=1.35))
w("submit_terminal_v1.svg", svg_doc(W, H, "".join(o)))
print("B10/B11 BLUEPRINTS OK")
