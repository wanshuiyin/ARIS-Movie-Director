#!/usr/bin/env python3
"""S15 verdict figure: WARN_corrected — claim narrows, effect real, not killed (诚实但不杀稿)."""
import os
W,H=1280,720; BG="#12182E"; BOARD="#171F38"; ST="#2A3552"; INK="#E4E9F7"; DIM="#8C97B8"
RED="#FF3366"; GREEN="#00C896"; AMBER="#FFB000"; PUR="#B066FF"; MONO="JetBrains Mono, Menlo, monospace"
def t(x,y,s,f=INK,sz=15,w="400",a="start",deco="none"): return f'<text x="{x}" y="{y}" fill="{f}" font-size="{sz}" font-weight="{w}" font-family="{MONO}" text-anchor="{a}" text-decoration="{deco}">{s}</text>'
def r(x,y,w,h,f,rx=10,s="none",sw=0,o=1.0):
    e=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{f}" opacity="{o}"'
    return (e+(f' stroke="{s}" stroke-width="{sw}"' if s!="none" else "")+"/>")
def build():
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',r(0,0,W,H,BG,0),
       r(60,56,1160,608,BOARD,16,ST,2,0.5),
       t(640,98,"VERDICT — WARN_corrected",INK,22,"800","middle"),
       t(640,122,"诚实但不杀稿 · the bug was caught before it reached the paper",DIM,13,"400","middle")]
    # big amber WARN stamp
    o+=[r(470,150,340,86,"#1A1330",12,AMBER,3),t(640,206,"⚠ WARN_corrected",AMBER,30,"800","middle")]
    # claim narrows: over-claim (struck) -> narrowed claim
    o+=[t(120,300,"the claim NARROWS (not retracted):",DIM,14,"700"),
        r(120,320,1040,64,"#241019",10,RED,1.5),
        t(140,360,'✗  "schema-keyword-first is BEST"',RED,18,"700","start","line-through"),
        f'<path d="M580,352 L640,352 M636,345 L644,352 L636,359" stroke="{INK}" stroke-width="2.5" fill="none"/>',
        r(660,332,480,40,"#0E2A22",8,GREEN,1.5),
        t(680,360,'✓  "...BEST under an external validator"',GREEN,16,"700")]
    # ledger entry
    o+=[t(120,440,"claim ledger (research-wiki):",DIM,14,"700"),
        r(120,460,1040,150,"#0E1322",10,ST,1.5),
        t(150,494,"claim_id   = C7",INK,15,"400"),
        t(150,522,"evidence   = results/json_2026_05_06.json",INK,15,"400"),
        t(150,550,"integrity  = WARN_corrected",AMBER,15,"700"),
        t(150,578,'scope      = "under external jsonschema only"',GREEN,15,"400"),
        t(640,640,"effect REAL (+1.4) · audit caught the inflation · paper stays honest",INK,14,"700","middle"),"</svg>"]
    return "\n".join(o)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","assets","warn_corrected_v1.svg"),"w").write(build())
print("wrote warn_corrected_v1.svg")
