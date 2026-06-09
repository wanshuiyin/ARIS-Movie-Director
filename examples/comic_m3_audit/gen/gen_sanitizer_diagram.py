#!/usr/bin/env python3
"""gen_sanitizer_diagram.py — the M3 integrity-bug figure: sanitizer (cheat) vs raw eval (honest).

Deterministic 1280x720 SVG. The #1 accuracy point (both cross-model reviewers): a reader must NOT
conflate the JSON SANITIZER (auto-repairs malformed keys BEFORE scoring -> inflates) with the
EXTERNAL jsonschema VALIDATOR (the honest primary metric). LEFT column = the bug (sanitizer path,
red, +6.2 inflated). RIGHT column = the honest raw path (json.loads + jsonschema, green, +1.4 real).

Doubles as the S13 blueprint content-authority for codex bake. Usage: python3 gen_sanitizer_diagram.py
"""
import os
W, H = 1280, 720
BG = "#12182E"; BOARD = "#171F38"; STROKE = "#2A3552"
INK = "#E4E9F7"; DIM = "#8C97B8"; KEY = "#7FB0FF"; VAL = "#9CE0B4"; CMT = "#6E7CA8"; FN = "#FFB000"
RED = "#FF3366"; GREEN = "#00C896"; AMBER = "#FFB000"
MONO = "JetBrains Mono, 'SF Mono', Menlo, monospace"

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def rect(x,y,w,h,fill,rx=8,stroke="none",sw=0,op=1.0):
    s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" opacity="{op}"'
    if stroke!="none": s+=f' stroke="{stroke}" stroke-width="{sw}"'
    return s+"/>"
def text(x,y,s,fill=INK,size=15,weight="400",anchor="start",mono=True,ls="0"):
    fam=MONO if mono else "Inter, sans-serif"
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" font-family="{fam}" text-anchor="{anchor}" letter-spacing="{ls}">{esc(s)}</text>'
def arrow(x1,y1,x2,y2,color):
    import math
    ang=math.atan2(y2-y1,x2-x1)
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2-8*math.cos(ang)}" y2="{y2-8*math.sin(ang)}" stroke="{color}" stroke-width="2.5"/>'
            f'<path d="M{x2},{y2} L{x2-10*math.cos(ang-0.4)},{y2-10*math.sin(ang-0.4)} L{x2-10*math.cos(ang+0.4)},{y2-10*math.sin(ang+0.4)} Z" fill="{color}"/>')

def codelines(x, y, lines, lh=24):
    out=[]
    ly=y
    for segs in lines:
        lx=x
        for t,c in segs:
            out.append(text(lx,ly,t,fill=c,size=14.5))
            lx+=int(len(t)*8.4)+2
        ly+=lh
    return "\n".join(out)

def build():
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    o.append(rect(0,0,W,H,BG,rx=0))
    o.append(rect(40,52,1200,616,BOARD,rx=16,stroke=STROKE,sw=2,op=0.5))
    o.append(text(640,92,"EVALUATOR INTEGRITY — sanitizer ≠ external validator",fill=INK,size=22,weight="800",anchor="middle"))
    o.append(text(640,116,"same model outputs · two ways to SCORE them · the gap is an artifact",fill=DIM,size=13,anchor="middle"))

    # shared malformed model output (top center)
    o.append(rect(478,140,324,86,"#241019",rx=10,stroke=RED,sw=2))
    o.append(text(640,162,"model output (malformed)",fill=RED,size=12,weight="700",anchor="middle"))
    o.append(codelines(498,190,[[('{"city":', KEY),('"Tok',VAL),('|',RED),('yo"',VAL),(',',CMT)],[('"founded":1603 }',KEY)]]))

    # ---- LEFT: THE BUG (sanitizer path) ----
    lx=70; lw=520
    o.append(rect(lx,270,lw,360,"#1A0F18",rx=12,stroke=RED,sw=2))
    o.append(rect(lx,270,lw,36,"#3A1626",rx=12))
    o.append(text(lx+18,294,"✗  THE BUG — what the pipeline actually ran",fill=RED,size=14,weight="800"))
    o.append(codelines(lx+22,338,[
        [('score',FN),('(',CMT),('json_sanitizer',RED),('(out)',KEY),(')',CMT)],
        [('# default-fills malformed',CMT)],
        [('#   keys BEFORE scoring',CMT)],
    ], lh=26))
    # flow: malformed -> sanitizer -> repaired -> scored
    o.append(arrow(640,226,300,430,RED))
    o.append(rect(lx+40,440,200,40,"#2A1020",rx=8,stroke=RED,sw=1.5))
    o.append(text(lx+140,465,"json_sanitizer",fill=RED,size=14,weight="700",anchor="middle"))
    o.append(text(lx+140,500,"↓ auto-repairs",fill=DIM,size=12,anchor="middle"))
    o.append(rect(lx+40,512,200,42,"#10241A",rx=8,stroke=GREEN,sw=1))
    o.append(codelines(lx+54,538,[[('{"city":',KEY),('"Tokyo"',VAL),(' ✓',GREEN)]]))
    o.append(text(lx+140,580,"scored as PASS (but it was broken)",fill=DIM,size=11.5,anchor="middle"))
    o.append(rect(lx+300,505,180,70,"#1A1330",rx=10,stroke=AMBER,sw=2))
    o.append(text(lx+390,532,"reported",fill=DIM,size=12,anchor="middle"))
    o.append(text(lx+390,562,"+6.2",fill=AMBER,size=26,weight="800",anchor="middle"))
    o.append(text(lx+390,600,"INFLATED",fill=RED,size=12,weight="700",anchor="middle"))

    # ---- RIGHT: HONEST (raw path) ----
    rx0=690; rw=520
    o.append(rect(rx0,270,rw,360,"#0E1A20",rx=12,stroke=GREEN,sw=2))
    o.append(rect(rx0,270,rw,36,"#10342A",rx=12))
    o.append(text(rx0+18,294,"✓  THE PRIMARY METRIC — raw, no repair",fill=GREEN,size=14,weight="800"))
    o.append(codelines(rx0+22,338,[
        [('obj = ',INK),('json.loads',FN),('(out)',KEY)],
        [('jsonschema',FN),('.validate',FN),('(obj, schema)',KEY)],
        [('# external validator, no fix',CMT)],
    ], lh=26))
    o.append(arrow(640,226,980,430,GREEN))
    o.append(rect(rx0+40,440,200,40,"#10241A",rx=8,stroke=GREEN,sw=1.5))
    o.append(text(rx0+140,465,"json.loads + schema",fill=GREEN,size=13,weight="700",anchor="middle"))
    o.append(text(rx0+140,500,"↓ no repair",fill=DIM,size=12,anchor="middle"))
    o.append(rect(rx0+40,512,200,42,"#2A1020",rx=8,stroke=RED,sw=1))
    o.append(codelines(rx0+54,538,[[('"Tok',VAL),('|',RED),('yo"',VAL),('  ✗ FAIL',RED)]]))
    o.append(text(rx0+140,580,"counted as FAIL (honest)",fill=DIM,size=11.5,anchor="middle"))
    o.append(rect(rx0+300,505,180,70,"#0E2A22",rx=10,stroke=GREEN,sw=2))
    o.append(text(rx0+390,532,"true effect",fill=DIM,size=12,anchor="middle"))
    o.append(text(rx0+390,562,"+1.4",fill=GREEN,size=26,weight="800",anchor="middle"))
    o.append(text(rx0+390,600,"REAL",fill=GREEN,size=12,weight="700",anchor="middle"))

    o.append(text(640,656,"the +4.8 gap = evaluator self-repair artifact   →   WARN_corrected, not killed",fill=INK,size=14,weight="700",anchor="middle"))
    o.append("</svg>")
    return "\n".join(o)

if __name__=="__main__":
    d=os.path.dirname(os.path.abspath(__file__))
    out=os.path.join(d,"..","assets_new"); os.makedirs(out,exist_ok=True)
    open(os.path.join(out,"sanitizer_vs_raw_v1.svg"),"w").write(build())
    print("wrote sanitizer_vs_raw_v1.svg")
