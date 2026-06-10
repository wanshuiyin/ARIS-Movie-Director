#!/usr/bin/env python3
"""gen_b01_b02_blueprints.py — per-panel content blueprints for B01 (S01) + B02 (S02), from asset_lib.

S01 anchor: a DDL dashboard chip T-24:00:00 (amber) — small, sits on/near the laptop in the bake.
S02 blueprint: the HAND-OFF terminal card — `$ aris run …` prompt line + ARIS ONLINE stamp + DDL chip.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import svg_doc, text, rect, ddl_chip, INK, DIM, GREEN, AMBER, ST

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def w(name, content):
    open(os.path.join(A, name), "w").write(content)
    print("wrote", name)


# S01 — the DDL anchor (dash skin carries the literal "DDL" + the time)
o = [ddl_chip(36, 40, "T-24:00:00", "amber", "dash", scale=2.2)]
w("s01_ddl_anchor_v1.svg", svg_doc(460, 180, "".join(o)))

# S02 — HAND-OFF terminal card (spans the warm→dark seam in the bake)
o = [rect(30, 26, 880, 308, "#0B1020", 14, ST, 2)]
o.append(rect(30, 26, 880, 40, "#10162B", 14))
o.append(text(72, 52, "● ● ●", DIM, 13, "700", "start"))
o.append(text(470, 52, "aris — hand-off", DIM, 12, "400"))
o.append(text(64, 122, "$ aris run", GREEN, 40, "800", "start"))
o.append(text(64, 162, "--task dllm-schema-keyword-first", INK, 21, "700", "start"))
o.append(text(64, 194, "--deadline 24h", INK, 21, "700", "start"))
o.append(rect(64, 224, 232, 46, "#0E2A22", 9, GREEN, 2))
o.append(text(180, 254, "ARIS ONLINE", GREEN, 22, "800"))
o.append(text(64, 308, "> session started · executor + reviewer awake", DIM, 14, "400", "start"))
o.append(ddl_chip(610, 224, "T-24:00:00", "amber", "dash", scale=1.7))
w("handoff_terminal_v1.svg", svg_doc(940, 360, "".join(o)))

print("B01/B02 BLUEPRINTS OK")
