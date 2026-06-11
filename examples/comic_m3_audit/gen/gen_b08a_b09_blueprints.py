#!/usr/bin/env python3
"""gen_b08a_b09_blueprints.py — S12a audit gate + S16 ACCEPT (the S11 mirror)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import (svg_doc, text, rect, ddl_chip, stamp, tokyo_chip, verdict_card,
                       INK, DIM, GREEN, AMBER, RED, ST)

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def w(name, content):
    open(os.path.join(A, name), "w").write(content)
    print("wrote", name)


# ── S12a: EVAL PIPELINE — AUDIT GATE ───────────────────────────────────────────
W, H = 1200, 640
o = [text(W / 2, 46, "EVAL PIPELINE — AUDIT GATE", INK, 22, "800", spacing="2")]
# pipeline: outputs → evaluator → score → [GATE] → claim
stages = [("outputs", 90), ("evaluator", 330), ("score", 570)]
for name, x in stages:
    o.append(rect(x, 260, 170, 90, "#10162B", 12, ST, 1.8))
    o.append(text(x + 85, 312, name, INK, 19, "700"))
for x in (262, 502):
    o.append(f'<path d="M{x},305 h 56 m -10,-8 l 10,8 l -10,8" stroke="{DIM}" stroke-width="3" fill="none"/>')
# the glowing gate between score and claim
o.append(rect(800, 180, 26, 260, "#1A1330", 8, AMBER, 2.5))
o.append(f'<rect x="792" y="170" width="42" height="280" rx="10" fill="none" stroke="{AMBER}" stroke-width="2" opacity="0.45"/>')
o.append(stamp(770, 120, "AUDIT", scale=1.0, tilt=-5))
# the +6.2 claim card HELD at the gate
o.append(rect(880, 250, 190, 110, "#1A1330", 12, AMBER, 2.5))
o.append(text(975, 308, "+6.2", AMBER, 44, "800"))
o.append(rect(906, 322, 138, 26, "#241019", 6, RED, 1.4))
o.append(text(975, 340, "HOLD · not a claim", RED, 11, "700"))
o.append(text(975, 226, "claim?", DIM, 14, "400"))
# magnifier pressed on the evaluator block
o.append(f'<circle cx="415" cy="290" r="58" fill="none" stroke="{INK}" stroke-width="6" opacity="0.9"/>')
o.append(f'<line x1="455" y1="334" x2="505" y2="386" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>')
o.append(f'<circle cx="415" cy="290" r="52" fill="{AMBER}" opacity="0.07"/>')
# tiny tokyo shard pinned at the pipeline INPUT (as prior evidence)
o.append(tokyo_chip(96, 372, scale=0.3))
o.append(text(126, 366, "prior evidence", DIM, 9.5, "400"))
o.append(ddl_chip(W - 220, 40, "T-05:12", "amber", "dash", scale=1.0))
w("audit_gate_v1.svg", svg_doc(W, H, "".join(o)))

# ── S16: HONEST RE-RUN — RAW SCORING (the S11 mirror: same card geometry, +6 tilt) ─
W, H = 1180, 660
o = [text(W / 2, 44, "HONEST RE-RUN — RAW SCORING", INK, 20, "800", spacing="2")]
o.append(f'<circle cx="{W/2}" cy="{H/2}" r="260" fill="{GREEN}" opacity="0.05"/>')
o.append(verdict_card(
    W / 2 - 280, H / 2 - 170,
    "REVIEW · RE-RUN",
    [("2048 samples · raw", INK, 22),
     ("sanitizer: BYPASSED", DIM, 16),
     ("json.loads ✓ clean", GREEN, 16)],
    "ACCEPT",
    big_chip=("0.89", "exact_parse", GREEN),
    scale=1.0, tilt=6))
# rising curve strip (0.78 → 0.89), both endpoints called out
o.append(rect(56, 96, 300, 200, "#0B1020", 10, ST, 1.5))
o.append(text(80, 124, "wandb · exact_parse", DIM, 11, "400", "start"))
pts = [(0.0, 0.78), (0.3, 0.81), (0.6, 0.85), (1.0, 0.89)]
pp = " ".join(f"{'M' if i == 0 else 'L'}{80 + t * 240:.0f},{266 - (v - 0.74) / 0.18 * 120:.0f}" for i, (t, v) in enumerate(pts))
o.append(f'<path d="{pp}" stroke="{GREEN}" stroke-width="4" fill="none"/>')
o.append(rect(64, 238, 78, 32, "#10162B", 7, ST, 1.5))
o.append(text(103, 261, "0.78", "#AEB9D6", 19, "800"))
o.append(rect(280, 120, 78, 34, "#0E2A22", 7, GREEN, 2))
o.append(text(319, 144, "0.89", GREEN, 20, "800"))
# RAW switch chip locked ON (echo of S14)
o.append(rect(56, 330, 120, 56, "#0E2A22", 10, GREEN, 2.2))
o.append(text(100, 366, "RAW", GREEN, 22, "800"))
o.append(f'<circle cx="150" cy="358" r="11" fill="{GREEN}"/>')
o.append(text(116, 406, "locked ON", DIM, 11, "400"))
o.append(ddl_chip(W - 220, 40, "T-02:58", "amber", "dash", scale=1.0))
w("accept_rerun_v1.svg", svg_doc(W, H, "".join(o)))
print("S12a + S16 BLUEPRINTS OK")
