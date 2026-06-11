#!/usr/bin/env python3
"""gen_b06_blueprints.py — B06 trio: GPU launch console / two-series wandb curve / the RAW SAMPLE STREAM
wall with the deliberately-sub-gate Tok|yo micro chip (the foreshadow, below blind-review transcription)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asset_lib import (svg_doc, text, rect, ddl_chip, stamp, tokyo_chip,
                       INK, DIM, GREEN, AMBER, RED, ST)

A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def w(name, content):
    open(os.path.join(A, name), "w").write(content)
    print("wrote", name)


# ── S07: GPU LAUNCH CONSOLE ────────────────────────────────────────────────────
W, H = 1100, 620
o = [text(W / 2, 44, "GPU LAUNCH CONSOLE", INK, 20, "800", spacing="3")]
o.append(rect(50, 70, 470, 56, "#0B1020", 9, ST, 1.5))
o.append(text(70, 104, "$ aris exp launch dllm-schema-keyword-first --gpus 8", GREEN, 13.5, "700", "start"))
for i in range(8):
    col, row = i % 4, i // 4
    x, y = 150 + col * 210, 170 + row * 170
    o.append(rect(x, y, 180, 130, "#10162B", 12, GREEN, 1.6))
    o.append(rect(x + 16, y + 18, 148, 56, "#0B1020", 7, ST, 1))
    for j in range(4):
        o.append(rect(x + 24 + j * 35, y + 28, 26, 36, "#16203A", 3))
    o.append(f'<circle cx="{x + 26}" cy="{y + 102}" r="7" fill="{GREEN}"/>')
    o.append(text(x + 100, y + 108, f"gpu{i}", DIM, 13, "700"))
o.append(rect(W / 2 - 160, 510, 130, 56, "#0B1020", 10, GREEN, 2))
o.append(text(W / 2 - 95, 548, "8/8", GREEN, 32, "800"))
o.append(rect(W / 2 + 6, 512, 196, 52, "#0E2A22", 10, GREEN, 2.6))   # status chip, not a verdict stamp (stamp family stays verdict-only)
o.append(text(W / 2 + 104, 547, "RUNNING", GREEN, 27, "800"))
o.append(ddl_chip(W - 230, 80, "T-18:30", "amber", "dash", scale=1.2))
w("gpu_launch_console_v1.svg", svg_doc(W, H, "".join(o)))

# ── S08: two-series wandb exact_parse 0.60→0.71 (UPGRADE of the core instance) ─
W, H = 1000, 560
o = [rect(30, 26, W - 60, H - 52, "#0B1020", 12, ST, 2)]
o.append(text(70, 62, "wandb · exact_parse", DIM, 15, "400", "start"))
x0, y0, iw, ih = 100, H - 90, W - 240, H - 230
for fv in (0.5, 0.6, 0.7, 0.8):
    gy = y0 - (fv - 0.45) / 0.4 * ih
    o.append(f'<line x1="{x0}" y1="{gy:.0f}" x2="{x0 + iw}" y2="{gy:.0f}" stroke="{ST}" stroke-width="1" opacity="0.5"/>')
    o.append(text(x0 - 10, gy + 5, f"{fv:.2f}", DIM, 12, "400", "end"))


def series(pts, color, width=4):
    pp = " ".join(f"{'M' if i == 0 else 'L'}{x0 + t * iw:.0f},{y0 - (v - 0.45) / 0.4 * ih:.0f}" for i, (t, v) in enumerate(pts))
    return f'<path d="{pp}" stroke="{color}" stroke-width="{width}" fill="none" stroke-linejoin="round"/>'


base = [(0.0, 0.585), (0.25, 0.60), (0.5, 0.595), (0.75, 0.605), (1.0, 0.60)]
ours = [(0.0, 0.60), (0.2, 0.625), (0.45, 0.66), (0.7, 0.69), (1.0, 0.71)]
o.append(series(base, "#5A6B85", 3))
o.append(series(ours, GREEN, 4.5))
bx, by = x0 + iw, y0 - (0.60 - 0.45) / 0.4 * ih
ox, oy = x0 + iw, y0 - (0.71 - 0.45) / 0.4 * ih
o.append(text(x0 + iw - 14, by + 30, "random-mask", "#8C97B8", 15, "700", "end"))
o.append(rect(ox + 8, by - 14, 96, 36, "#10162B", 7, "#5A6B85", 1.5))
o.append(text(ox + 56, by + 10, "0.60", "#AEB9D6", 24, "800"))
o.append(text(x0 + iw - 14, oy - 16, "schema-first", GREEN, 15, "700", "end"))
o.append(rect(ox + 8, oy - 22, 96, 38, "#0E2A22", 7, GREEN, 2))
o.append(text(ox + 56, oy + 5, "0.71", GREEN, 25, "800"))
o.append(rect(x0 + iw * 0.36, oy + 44, 150, 40, "#1A1330", 8, AMBER, 1.6))
o.append(text(x0 + iw * 0.36 + 75, oy + 71, "0.60 → 0.71", AMBER, 18, "800"))
o.append(ddl_chip(W - 220, 44, "T-17:46", "amber", "dash", scale=1.0))
w("wandb_exact_parse_060_071_v1.svg", svg_doc(W, H, "".join(o)))

# ── S09: RAW SAMPLE STREAM wall + micro Tok|yo (sub-gate, no callout) ──────────
W, H = 1280, 760
o = [text(W / 2, 40, "RAW SAMPLE STREAM", INK, 19, "800", spacing="4")]
# top band: curve holding at 0.71
o.append(rect(60, 60, 760, 88, "#0B1020", 10, ST, 1.5))
hold = [(0.0, 0.6), (0.3, 0.66), (0.6, 0.70), (1.0, 0.71)]
pp = " ".join(f"{'M' if i == 0 else 'L'}{80 + t * 600:.0f},{136 - (v - 0.55) / 0.2 * 56:.0f}" for i, (t, v) in enumerate(hold))
o.append(f'<path d="{pp}" stroke="{GREEN}" stroke-width="3.5" fill="none"/>')
o.append(rect(700, 76, 96, 40, "#0E2A22", 7, GREEN, 2))
o.append(text(748, 104, "0.71", GREEN, 26, "800"))
o.append(rect(860, 66, 230, 60, "#10162B", 10, AMBER, 1.8))
o.append(text(975, 106, "1024/2048", AMBER, 28, "800"))
o.append(ddl_chip(1096, 70, "T-17:02", "amber", "dash", scale=1.0))
# the log wall: many tiny OK rows
import random as _r  # deterministic: fixed seed
_r.seed(7)
for row in range(14):
    for col in range(3):
        x, y = 70 + col * 400, 180 + row * 38
        wd = 240 + _r.randint(0, 110)
        o.append(rect(x, y, wd, 22, "#10162B", 4, opacity=0.9))
        o.append(rect(x + 8, y + 6, wd - 70, 9, "#1B2440", 3, opacity=0.9))
        o.append(rect(x + wd - 46, y + 4, 38, 15, "#0E2A22", 4))
        o.append(text(x + wd - 27, y + 15.5, "OK", GREEN, 9.5, "800"))
# the micro Tok|yo chip — bottom corner of the stream, ~1.4% of frame height, NO callout, NO arrow
o.append(tokyo_chip(990, 698, scale=0.27))
w("sample_stream_wall_tokyo_seed_v1.svg", svg_doc(W, H, "".join(o)))
print("B06 BLUEPRINTS OK")
