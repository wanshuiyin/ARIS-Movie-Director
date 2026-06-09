#!/usr/bin/env python3
"""S14 collapse figure: the inflated +6.2 cracks to the honest +1.4 (the +4.8 is a self-repair artifact)."""
import os
W,H=1280,720; BG="#12182E"; BOARD="#171F38"; ST="#2A3552"; INK="#E4E9F7"; DIM="#8C97B8"
RED="#FF3366"; GREEN="#00C896"; AMBER="#FFB000"; MONO="JetBrains Mono, Menlo, monospace"
def t(x,y,s,f=INK,sz=15,w="400",a="start"): return f'<text x="{x}" y="{y}" fill="{f}" font-size="{sz}" font-weight="{w}" font-family="{MONO}" text-anchor="{a}">{s}</text>'
def r(x,y,w,h,f,rx=10,s="none",sw=0,o=1.0):
    e=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{f}" opacity="{o}"'
    return (e+(f' stroke="{s}" stroke-width="{sw}"' if s!="none" else "")+"/>")
def build():
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',r(0,0,W,H,BG,0),
       r(60,56,1160,608,BOARD,16,ST,2,0.5),
       t(640,98,"HONEST RE-EVAL — the gap collapses",INK,22,"800","middle"),
       t(640,122,"re-score with raw json.loads + jsonschema (no sanitizer)",DIM,13,"400","middle")]
    # LEFT: inflated +6.2, fracturing
    o+=[r(120,210,420,300,"#1A1330",14,AMBER,2),t(330,250,"reported (sanitized)",DIM,13,"700","middle"),
        t(330,360,"+6.2",AMBER,86,"800","middle")]
    # crack lines over the +6.2
    o+=[f'<path d="M250,300 L300,360 L270,400 L340,470" stroke="{RED}" stroke-width="3" fill="none" opacity="0.8"/>',
        f'<path d="M400,290 L360,360 L420,420" stroke="{RED}" stroke-width="3" fill="none" opacity="0.8"/>',
        t(330,455,"INFLATED",RED,14,"700","middle")]
    # transition arrow + RAW switch
    o+=[r(560,330,150,60,"#0E1A20",10,GREEN,1.5),t(635,355,"flip RAW",GREEN,13,"700","middle"),t(635,376,"switch",GREEN,13,"700","middle"),
        f'<path d="M548,360 L556,360 M716,360 L744,360" stroke="{INK}" stroke-width="2.5"/>',
        f'<path d="M744,360 L734,353 L734,367 Z" fill="{INK}"/>']
    # RIGHT: honest +1.4 solid
    o+=[r(760,210,400,300,"#0E2A22",14,GREEN,2.5),t(960,250,"true effect (raw)",DIM,13,"700","middle"),
        t(960,360,"+1.4",GREEN,86,"800","middle"),t(960,455,"REAL · not killed",GREEN,14,"700","middle")]
    # the +4.8 falling away
    o+=[f'<path d="M540,470 C620,560 760,560 820,520" stroke="{DIM}" stroke-width="2" stroke-dasharray="5 5" fill="none"/>',
        r(560,540,300,54,"#241019",10,RED,1.5),
        t(710,565,"+4.8 = evaluator self-repair artifact",RED,13.5,"700","middle"),
        t(710,584,"(the sanitizer was scoring repaired output)",DIM,11,"400","middle")]
    o+=[t(640,640,"effect REAL but scope narrowed  →  WARN_corrected, 诚实但不杀稿",INK,14,"700","middle"),"</svg>"]
    return "\n".join(o)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","assets","collapse_6_2_to_1_4_v1.svg"),"w").write(build())
print("wrote collapse_6_2_to_1_4_v1.svg")
