#!/usr/bin/env python3
"""gen_b05_blueprint.py — S06 phone ARIS-status widget (the only gated anchor in a warm scene beat)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import svg_doc, text, rect, ddl_chip, INK, DIM, GREEN, ST

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
o = [rect(40, 30, 380, 250, "#0B1020", 28, ST, 2.5)]
o.append(rect(190, 44, 80, 8, "#1B2440", 4))                       # notch
o.append(f'<circle cx="120" cy="106" r="8" fill="{GREEN}"/>')
o.append(text(245, 114, "ARIS · RUNNING", GREEN, 27, "800"))
o.append(ddl_chip(116, 146, "T-18:40", "amber", "dash", scale=1.7))
o.append(text(230, 262, "running remotely · no action needed", DIM, 12.5, "400"))
open(os.path.join(A, "phone_aris_status_v1.svg"), "w").write(svg_doc(460, 310, "".join(o)))
print("wrote phone_aris_status_v1.svg")
