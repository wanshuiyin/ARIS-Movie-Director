#!/usr/bin/env python3
"""gen_workflow_figure.py — ARIS-Movie-Director method-overview figure (deterministic vector SVG).
Self-contained (no deps). Design = docs/WORKFLOW_FIGURE_DESIGN.md v2, codex+gemini APPROVED.
Layout: top legend + title · LEFT authored source-of-truth · CENTER audited-spiral (main flow + two nested
loop-backs: inner green = literal correctness ≤4/panel, outer purple = page coherence ≤6/run) · the
beautiful-but-wrong REJECT "crime scene" on the retry branch · wiki exhaust nodes · escape-velocity red
arrow → human · RIGHT release projection."""
import os

VOID="#0A0E27"; INK="#E4E9F7"; DIM="#8C97B8"; ST="#2A3552"; PANEL="#10162B"; CARD="#0E1322"
AMBER="#FFB000"; GREEN="#00C896"; RED="#FF3366"; PURPLE="#B066FF"; BLUE="#5B8CFF"; WARM="#FFB46B"
MONO="JetBrains Mono, Menlo, monospace"; DISP="Inter, Helvetica Neue, sans-serif"
W,H=1680,960
o=[]

def t(x,y,s,fill=INK,size=15,wt="700",anc="middle",fam=MONO,sp=None,op=1.0):
    sa=f' letter-spacing="{sp}"' if sp else ""
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{wt}" '
            f'font-family="{fam}" text-anchor="{anc}"{sa} opacity="{op}">{s}</text>')
def r(x,y,w,h,fill,rx=10,stroke=None,sw=0,op=1.0,dash=None):
    e=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" opacity="{op}"'
    if stroke: e+=f' stroke="{stroke}" stroke-width="{sw}"'
    if dash: e+=f' stroke-dasharray="{dash}"'
    return e+"/>"
def line(x1,y1,x2,y2,c=ST,w=1.5,op=1.0,dash=None):
    d=f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}" opacity="{op}"{d}/>'
def circ(x,y,rad,fill,stroke=None,sw=0,op=1.0):
    e=f'<circle cx="{x}" cy="{y}" r="{rad}" fill="{fill}" opacity="{op}"'
    if stroke: e+=f' stroke="{stroke}" stroke-width="{sw}"'
    return e+"/>"
def chibi(x,y,s,hood,hair="#2A2A33",beard=False):
    """tiny chibi head+torso glyph. hood=hoodie color."""
    g=[circ(x,y,7*s,"#F0C89B")]  # face
    g.append(f'<path d="M{x-8*s},{y-2*s} q{8*s},{-11*s} {16*s},0 z" fill="{hair}"/>')  # hair
    g.append(r(x-2.5*s,y-1*s,1.6*s,1.6*s,"#243049",0)); g.append(r(x+1*s,y-1*s,1.6*s,1.6*s,"#243049",0))  # eyes
    if beard: g.append(f'<path d="M{x-5*s},{y+3*s} q{5*s},{6*s} {10*s},0" fill="none" stroke="{hair}" stroke-width="{2*s}"/>')
    g.append(r(x-7*s,y+7*s,14*s,11*s,hood,3*s))  # torso
    return "".join(g)
def arrow(x1,y1,x2,y2,c=INK,w=2.2,op=1.0):
    import math
    a=math.atan2(y2-y1,x2-x1); L=8
    h=(f'<path d="M{x2},{y2} L{x2-L*math.cos(a-0.5):.1f},{y2-L*math.sin(a-0.5):.1f} '
       f'L{x2-L*math.cos(a+0.5):.1f},{y2-L*math.sin(a+0.5):.1f} Z" fill="{c}" opacity="{op}"/>')
    return line(x1,y1,x2,y2,c,w,op)+h

# ── ground ──
o.append(r(0,0,W,H,VOID,0))
o.append(r(0,0,W,H,"none",0,"#1b2240",2))

# ── TITLE + TOP LEGEND ──
o.append(t(54,58,"ARIS-Movie-Director",AMBER,30,"800","start",DISP,"1"))
o.append(t(56,84,"Audited Spiral Generation for Narrative Comics",DIM,15,"500","start",MONO,"2"))
# legend rail (right side of header)
lx=W-690; o.append(r(lx,30,640,62,PANEL,10,ST,1.2))
o.append(chibi(lx+30,56,1.5,BLUE)); o.append(t(lx+48,53,"Claude",INK,12,"700","start"))
o.append(t(lx+48,69,"executor · makes",DIM,10.5,"400","start"))
o.append(chibi(lx+185,56,1.5,GREEN,beard=True)); o.append(t(lx+204,53,"GPT-5.5 · Gemini",INK,12,"700","start"))
o.append(t(lx+204,69,"reviewers · judge (other families)",DIM,10.5,"400","start"))
o.append(t(lx+430,53,"👤 human",INK,12,"700","start",DISP))
o.append(t(lx+430,69,"approves story · overrides flags",DIM,10.5,"400","start"))
o.append(t(W-54,108,"“the one who makes can't be the only one who judges.”",DIM,12.5,"500","end",MONO,None,0.85))

# ════════ LEFT COLUMN — AUTHORED SOURCE OF TRUTH ════════
LX=44; LW=330; ytop=150
o.append(t(LX,ytop,"① AUTHORED SOURCE OF TRUTH",GREEN,13,"800","start",MONO,"1"))
o.append(t(LX,ytop+18,"design layer · human-approved",DIM,10.5,"400","start"))
# asset library card (icons only)
def card(x,y,w,h,title,sub,accent):
    g=[r(x,y,w,h,CARD,11,ST,1.4), r(x,y,w,26,PANEL,11), t(x+12,y+18,title,accent,12.5,"800","start")]
    if sub: g.append(t(x+12,y+h-10,sub,DIM,10,"400","start"))
    return "".join(g)
ay=ytop+34
o.append(card(LX,ay,LW,86,"素材库 · Asset Library","one single-source builder → one visual dialect",AMBER))
# mini motif icons
ix=LX+16; iy=ay+44
o.append(r(ix,iy,46,20,"#0B1020",5,AMBER,1.2)); o.append(t(ix+23,iy+14,"T-18:40",AMBER,9,"800"))
o.append(r(ix+58,iy-2,52,26,"#241019",6,RED,1.6)); o.append(t(ix+84,iy+15,"REJECT",RED,10,"800"))
o.append(r(ix+122,iy-2,52,26,"#0E2A22",6,GREEN,1.6)); o.append(t(ix+148,iy+15,"ACCEPT",GREEN,10,"800"))
o.append(circ(ix+200,iy+10,4,"#FFFFFF")); o.append(circ(ix+216,iy+4,3,AMBER)); o.append(circ(ix+228,iy+14,3,RED)); o.append(line(ix+200,iy+10,ix+216,iy+4,INK,1,0.5)); o.append(line(ix+216,iy+4,ix+228,iy+14,INK,1,0.5))
o.append(t(ix+214,iy+30,"star-map",DIM,8.5,"400"))
by=ay+98
o.append(card(LX,by,LW,52,"大纲 · Outline","13 beats",PURPLE))
for i in range(13): o.append(circ(LX+150+i*13,by+34,3.4,PURPLE if i%4 else AMBER,op=0.9))
sy=by+64
o.append(card(LX,sy,LW,72,"分镜 · Storyboard","per-panel spec",BLUE))
o.append(t(LX+12,sy+44,"world · scene · characters · bubbles",DIM,10,"400","start"))
o.append(t(LX+12,sy+60,"expected_literals  ← gate's truth",GREEN,10.5,"700","start"))
# compile → comic.json
cy=sy+88
o.append(r(LX,cy,LW,52,"#12182f",11,GREEN,1.8))
o.append(t(LX+LW/2,cy+22,"comic.json",GREEN,16,"800"))
o.append(t(LX+LW/2,cy+40,"content_svg · expected_literals · identity_ref",DIM,9.5,"400"))
o.append(t(LX+LW/2,cy+86,"Claude proposes ‖ codex+gemini critique → 👤 approve",DIM,10,"500",fam=MONO,op=0.9))
o.append(r(LX,cy+96,LW,2,PURPLE,0,op=0.4))
# arrow into center
o.append(arrow(LX+LW+6,cy+26,LX+LW+58,cy+26,INK,2.4))

# ════════ CENTER — THE AUDITED SPIRAL ════════
CXL=440; CXR=1190
o.append(t((CXL+CXR)/2,150,"② THE AUDITED SPIRAL",AMBER,15,"800","middle",MONO,"2"))
o.append(t((CXL+CXR)/2,170,"generate → cross-model verify → remember · bounded, never self-acquits",DIM,11,"400"))

# main flow nodes (left→right along a center line)
midY=470
def node(x,y,w,h,lab,sub,accent,fill=PANEL):
    g=[r(x-w/2,y-h/2,w,h,fill,10,accent,2)]
    g.append(t(x,y-2 if sub else y+5,lab,INK,14,"800"))
    if sub: g.append(t(x,y+15,sub,DIM,10,"400"))
    return "".join(g)
# BAKE core (blueprint → png)
bakeX=600
o.append(r(bakeX-78,midY-46,156,92,"#12182f",12,AMBER,2.2))
o.append(t(bakeX,midY-28,"BAKE",AMBER,15,"800"))
# blueprint → pixel transform
o.append(r(bakeX-58,midY-12,42,34,"#0B1020",4,DIM,1.2)); o.append(t(bakeX-37,midY+9,"SVG",DIM,9,"700"))
o.append(arrow(bakeX-12,midY+5,bakeX+12,midY+5,INK,2))
o.append(r(bakeX+16,midY-12,42,34,"#13233a",4,GREEN,1.2))
for gx in range(3):
    for gy in range(3): o.append(r(bakeX+22+gx*12,midY-6+gy*10,9,7,[GREEN,BLUE,AMBER][(gx+gy)%3],1,op=0.7))
o.append(t(bakeX,midY+38,"codex image_gen · 2 refs",DIM,9.5,"400"))

# panel_gate (3 reviewer chips)
gateX=880
o.append(r(gateX-86,midY-52,172,104,PANEL,12,GREEN,2.2))
o.append(t(gateX,midY-34,"panel_gate",GREEN,14,"800"))
chips=[("CC","narrative",BLUE),("Gem","visual",GREEN),("Cdx","visual",AMBER)]
for i,(nm,role,c) in enumerate(chips):
    cxp=gateX-56+i*56
    o.append(r(cxp-24,midY-18,48,40,"#0B1020",6,c,1.4))
    o.append(t(cxp,midY-2,nm,c,11,"800")); o.append(t(cxp,midY+12,role,DIM,8,"400"))
o.append(t(gateX,midY+42,"deterministic JS verdict",INK,10.5,"700"))
o.append(t(gateX,midY+56,"blind observed_literals  ⊖  expected_literals",DIM,9,"400"))

o.append(arrow(bakeX+78,midY,gateX-88,midY,INK,2.4))

# KEEP → page pool
poolX=1090
o.append(r(poolX-58,midY-40,116,80,"#0E2A22",10,GREEN,2))
o.append(t(poolX,midY-16,"KEEP",GREEN,14,"800"))
# 2x2 mini page
for gx in range(2):
    for gy in range(2): o.append(r(poolX-26+gx*28,midY-2+gy*20,24,16,"#13233a",2,GREEN,1,op=0.8))
o.append(t(poolX,midY+52,"page pool",DIM,10,"400"))
o.append(arrow(gateX+88,midY,poolX-60,midY,GREEN,2.4))
o.append(t((gateX+poolX)/2,midY-12,"keep",GREEN,10,"700"))

# ── INNER LOOP-BACK (green): RETRY → bake, ≤4 attempts/panel (literal correctness) ──
# arc above the flow from gate back to bake
o.append(f'<path d="M{gateX-40},{midY-52} C{gateX-120},{midY-150} {bakeX+40},{midY-150} {bakeX},{midY-46}" stroke="{GREEN}" stroke-width="2.4" fill="none"/>')   # inner = SOLID (tight, frequent literal-retry)
o.append(arrow(bakeX+4,midY-58,bakeX,midY-46,GREEN,2.2))
o.append(t((bakeX+gateX)/2,midY-158,"RETRY  ·  re-bake with failure_mode invariant",GREEN,11,"800"))
o.append(t((bakeX+gateX)/2,midY-142,"inner perimeter · literal correctness · ≤4 attempts/panel",DIM,9.5,"400"))

# ── OUTER LOOP-BACK (purple): assembly drift → re-bake named panels, ≤6 rollbacks/run ──
asmX=1090; asmY=720
o.append(r(asmX-92,asmY-34,184,68,PANEL,11,PURPLE,2))
o.append(t(asmX,asmY-12,"page assembly_gate",PURPLE,13,"800"))
o.append(t(asmX,asmY+6,"cast-aware: reading order/rhythm",DIM,9,"400"))
o.append(t(asmX,asmY+20,"identity/style · legibility/safe-zone",DIM,9,"400"))
o.append(arrow(poolX,midY+40,asmX,asmY-36,GREEN,2.2))
# drift arc back to bake (wide, purple, below)
o.append(f'<path d="M{asmX-92},{asmY} C{bakeX-40},{asmY+120} {bakeX-120},{midY+150} {bakeX-10},{midY+46}" stroke="{PURPLE}" stroke-width="2.6" fill="none" stroke-dasharray="9 6"/>')
o.append(arrow(bakeX-16,midY+58,bakeX-10,midY+46,PURPLE,2.6))
o.append(t((bakeX+asmX)/2-30,asmY+118,"DRIFT  ·  re-bake the named drifting panels",PURPLE,11,"800"))
o.append(t((bakeX+asmX)/2-30,asmY+134,"outer perimeter · page coherence · ≤6 rollbacks/run",DIM,9.5,"400"))

# ── WIKI exhaust nodes: a compact trail just under the BAKE→gate flow ──
wy0=midY+78
o.append(t(bakeX-78,wy0-8,"research-wiki · the loop's exhaust trail",DIM,10,"700","start",MONO))
wnodes=[(bakeX-70,wy0+14,GREEN,"attempt"),(bakeX-8,wy0+22,RED,"failed"),(bakeX+54,wy0+14,AMBER,"review"),(bakeX+116,wy0+20,GREEN,"keep")]
for i,(wx,wy,c,lab) in enumerate(wnodes):
    if i: o.append(line(wnodes[i-1][0],wnodes[i-1][1],wx,wy,DIM,1,0.4))
    o.append(circ(wx,wy,5,c,op=0.5 if c==RED else 0.95))
    o.append(t(wx,wy+15,lab,DIM,8,"400",op=0.55 if c==RED else 0.9))
# the failed node's repair_pattern loops back up into BAKE
o.append(f'<path d="M{bakeX-8},{wy0+22} q-70,-10 -52,-110" stroke="{GREEN}" stroke-width="1.4" fill="none" stroke-dasharray="3 4" opacity="0.6"/>')
o.append(t(bakeX-86,wy0-26,"repair_pattern ↻",GREEN,9,"700","middle",MONO,None,0.85))

# ── ESCAPE VELOCITY (the ONLY bright red; one clear eject → human) ──
o.append(arrow(asmX+92,asmY,W-150,asmY,RED,2.8))
o.append(r(W-150,asmY-22,118,44,"#241019",8,RED,2))
o.append(t(W-91,asmY-2,"👤 FLAG",RED,13,"800",fam=DISP))
o.append(t(W-91,asmY+14,"human override",RED,9.5,"600"))
o.append(t(W-91,asmY+40,"bound hit (4/6) → eject",DIM,9,"400"))
o.append(t(W-91,asmY+54,"drives, never self-acquits",DIM,9,"400"))

# ════════ THE PUNCHLINE — beautiful-but-wrong REJECT (called-out crime scene, bottom-left) ════════
px,py,pw,ph=58,628,310,214
# leader from the gate's reject side, curving DOWN BELOW the wiki trail to the inset (never crossing label text)
o.append(f'<path d="M{gateX-60},{midY+40} C{gateX-180},{midY+150} {px+pw+60},{midY+150} {px+pw-20},{py-6}" stroke="{RED}" stroke-width="1.6" fill="none" opacity="0.55" stroke-dasharray="4 4"/>')
o.append(t(px+pw-30,py-14,"on REJECT",RED,9,"700","end",MONO,None,0.8))
o.append(r(px,py,pw,ph,"#160a12",12,RED,2.4))
o.append(t(px+pw/2,py+22,"a beautiful panel can still be WRONG",RED,12.5,"800"))
# mini "beautiful" baked panel
o.append(r(px+18,py+34,120,84,"#1a2740",6,ST,1.2))
o.append(circ(px+50,py+70,12,"#5B8CFF")); o.append(circ(px+86,py+70,12,GREEN))  # two chibi blobs
o.append(r(px+30,py+96,96,10,"#0B1020",3)); o.append(t(px+78,py+104,'{"city":"Tok|ya"}',RED,8.5,"700"))
# JS diff box
dx=px+150
o.append(r(dx,py+34,134,84,"#0B1020",6,ST,1.2))
o.append(t(dx+10,py+50,"JS token-diff",DIM,9,"700","start"))
o.append(t(dx+10,py+66,"expected: +6.2  Tok|yo",GREEN,9,"700","start"))
o.append(t(dx+10,py+82,"Gemini:  +6.25  ✗",RED,9,"700","start"))
o.append(t(dx+10,py+98,"Codex:   garbled ✗",RED,9,"700","start"))
# REJECT stamp slamming down
o.append(f'<g transform="rotate(-8 {px+pw/2} {py+150})">')
o.append(r(px+pw/2-92,py+134,184,34,"#241019",6,RED,2.6))
o.append(t(px+pw/2,py+157,"REJECT · content_corruption",RED,13,"800"))
o.append("</g>")
o.append(t(px+pw/2,py+192,"single-vote veto · +6.25 ≠ +6.2 · aesthetic ≠ verified",DIM,9.5,"600"))

# ════════ RIGHT COLUMN — RELEASE PROJECTION ════════
RX=1290; markY=625
o.append(t(RX,150,"③ RELEASE",GREEN,13,"800","start",MONO,"1"))
o.append(t(RX,168,"downstream products",DIM,10.5,"400","start"))
o.append(r(RX,markY-330,330,150,CARD,11,ST,1.4))
o.append(t(RX+165,markY-305,"accepted pages",INK,13,"800"))
o.append(arrow(RX+165,markY-292,RX+165,markY-268,INK,2))
o.append(r(RX+90,markY-262,150,30,"#12182f",6,GREEN,1.6)); o.append(t(RX+165,markY-242,"comic.json",GREEN,12,"800"))
o.append(arrow(RX+165,markY-230,RX+165,markY-206,INK,2))
# viewer thumbnail (mini comic page)
o.append(r(RX+70,markY-200,190,118,"#0B1020",6,GREEN,1.8))
o.append(t(RX+165,markY-186,"single-file HTML viewer",GREEN,9.5,"700"))
for gx in range(3):
    o.append(r(RX+82+gx*60,markY-176,52,30,"#16203a",3,ST,1))
o.append(r(RX+82,markY-142,170,30,"#13233a",3,ST,1))
o.append(r(RX+82,markY-108,80,22,"#16203a",3,ST,1)); o.append(r(RX+170,markY-108,82,22,"#16203a",3,ST,1))

# footer
o.append(t(W/2,H-20,"deterministic blueprint → cross-model adversarial gate → wiki memory → bounded repair → human backstop",DIM,11,"500",fam=MONO,op=0.85))

svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'+"".join(o)+"</svg>")
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"workflow_figure.svg")
open(out,"w").write(svg)
print("wrote",out,len(svg),"bytes")
