#!/usr/bin/env python3
"""gen_method_figure.py — render the ARIS method figure from method_figure.blueprint.json.

Two modes (AutoFigure-style decoupled pipeline):
  skeleton  → a TEXTLESS white-bg layout (pale phase panels + node zones + arrows + character zones, NO
              real labels) used to CONDITION image2 (so the bake respects structure but invents no ghost text).
  overlay <baked.png> → final figure = the image2 raster base + crisp VECTOR labels/arrows drawn on top
              (label_policy: vector_overlay_only) at the blueprint coords, each with a light label_box.
Usage: python3 gen_method_figure.py skeleton
       python3 gen_method_figure.py overlay path/to/baked.png
"""
import json, os, sys, math

HERE=os.path.dirname(os.path.abspath(__file__))
BP=json.load(open(os.path.join(HERE,"figassets","method_figure.blueprint.json")))
W=BP["canvas"]["width"]; H=BP["canvas"]["height"]; PAL=BP["style"]["palette"]
def col(name,default="#000"): return PAL.get(name,name if name and name.startswith("#") else default)
NODES={n["id"]:n for n in BP["nodes"]}
GROUPS={g["id"]:g for g in BP["groups"]}
FONT=BP["style"]["font_family"]
o=[]
def esc(s): return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def T(x,y,s,fill,size,wt="700",anc="middle",sp=None):
    sa=f' letter-spacing="{sp}"' if sp else ""
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{wt}" font-family="{FONT}" text-anchor="{anc}"{sa}>{esc(s)}</text>'
def R(x,y,w,h,fill,rx=12,stroke=None,sw=0,op=1.0,dash=None,filt=None):
    e=f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx}" fill="{fill}" opacity="{op}"'
    if stroke: e+=f' stroke="{stroke}" stroke-width="{sw}"'
    if dash: e+=f' stroke-dasharray="{dash}"'
    if filt: e+=f' filter="{filt}"'
    return e+"/>"
def box(n): return (n["pos"]["x"]-n["size"]["w"]/2, n["pos"]["y"]-n["size"]["h"]/2, n["size"]["w"], n["size"]["h"])
def edge_path(e):
    a=NODES[e["from"]]; b=NODES[e["to"]]; ax,ay=a["pos"]["x"],a["pos"]["y"]; bx,by=b["pos"]["x"],b["pos"]["y"]
    return ax,ay,bx,by
def arrow(x1,y1,x2,y2,c,w=2.6,dash=None,curve=0):
    d=f' stroke-dasharray="{dash}"' if dash else ""
    if curve:
        mx,my=(x1+x2)/2,(y1+y2)/2-curve
        path=f'<path d="M{x1:.0f},{y1:.0f} Q{mx:.0f},{my:.0f} {x2:.0f},{y2:.0f}" fill="none" stroke="{c}" stroke-width="{w}"{d}/>'
        ang=math.atan2(y2-my,x2-mx)
    else:
        path=f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{c}" stroke-width="{w}"{d}/>'
        ang=math.atan2(y2-y1,x2-x1)
    L=11
    head=(f'<path d="M{x2:.0f},{y2:.0f} L{x2-L*math.cos(ang-0.45):.0f},{y2-L*math.sin(ang-0.45):.0f} '
          f'L{x2-L*math.cos(ang+0.45):.0f},{y2-L*math.sin(ang+0.45):.0f} Z" fill="{c}"/>')
    return path+head

MODE=sys.argv[1] if len(sys.argv)>1 else "skeleton"
EK={"flow":col("arrow"),"keep":col("green_accent"),"retry":col("peach_accent"),"write_wiki":col("muted"),"repair":col("blue_accent"),"human_escalation":col("red")}
defs='''<defs>
<filter id="cardShadow" x="-12%" y="-16%" width="124%" height="132%">
  <feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#111827" flood-opacity="0.10"/>
</filter>
<filter id="softShadow" x="-18%" y="-22%" width="136%" height="144%">
  <feDropShadow dx="0" dy="5" stdDeviation="5" flood-color="#111827" flood-opacity="0.12"/>
</filter>
</defs>'''
o.append(defs)
o.append(R(0,0,W,H,BP["canvas"]["background"],0))

def G(body,tx=0,ty=0,scale=1):
    return f'<g transform="translate({tx:.1f} {ty:.1f}) scale({scale:.3f})">{body}</g>'

def Px(x,y,w,h,fill,stroke=None,sw=0):
    e=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" shape-rendering="crispEdges"'
    if stroke: e+=f' stroke="{stroke}" stroke-width="{sw}"'
    return e+"/>"

def chibi(kind):
    if kind=="researcher":
        hair="#171A22"; hoodie="#151922"; pants="#111827"; shoe="#F8FAFC"; skin="#F6C99B"
        body=[
            Px(15,0,18,4,hair), Px(9,4,30,6,hair), Px(6,10,36,12,hair),
            Px(9,22,30,8,hair), Px(15,24,18,4,skin), Px(18,28,12,4,skin),
            Px(12,18,24,18,skin), Px(8,20,8,16,hair), Px(32,18,8,16,hair),
            Px(14,22,8,6,"#FFFFFF"), Px(26,22,8,6,"#FFFFFF"),
            Px(14,23,8,3,"#111827"), Px(26,23,8,3,"#111827"), Px(22,24,4,2,"#111827"),
            Px(13,29,6,2,"#1F2937"), Px(28,30,6,2,"#1F2937"),
            Px(13,38,24,26,hoodie), Px(8,42,6,24,skin), Px(37,42,6,24,skin),
            Px(16,64,8,28,pants), Px(26,64,8,28,pants),
            Px(14,92,12,5,shoe), Px(26,92,12,5,shoe)
        ]
        return "".join(body)
    if kind=="executor":
        hair="#A86936"; hoodie="#2563EB"; skin="#F6C99B"
        body=[
            Px(10,0,30,5,hair), Px(5,5,40,9,hair), Px(3,14,44,13,hair),
            Px(8,25,34,22,skin), Px(5,22,9,18,hair), Px(36,20,8,20,hair),
            Px(14,32,5,8,"#111827"), Px(31,32,5,8,"#111827"), Px(22,42,10,2,"#BE6B4E"),
            Px(8,49,36,28,hoodie), Px(8,49,7,12,"#1D4ED8"), Px(37,49,7,12,"#1D4ED8"),
            Px(3,54,8,22,skin), Px(43,54,8,22,skin), Px(15,77,10,20,"#1F2937"), Px(28,77,10,20,"#1F2937"),
            Px(12,97,14,5,"#FFFFFF"), Px(27,97,14,5,"#FFFFFF"),
            Px(21,52,4,18,"#93C5FD"), Px(31,52,4,18,"#93C5FD")
        ]
        return "".join(body)
    hair="#1F2937"; hoodie="#15803D"; skin="#F6C99B"
    return "".join([
        Px(9,0,32,5,hair), Px(4,5,42,9,hair), Px(2,14,46,12,hair),
        Px(8,24,36,20,skin), Px(5,20,8,20,hair), Px(39,20,7,20,hair),
        Px(14,31,5,8,"#111827"), Px(32,31,5,8,"#111827"),
        Px(12,40,28,13,hair), Px(17,39,18,7,"#5B2C20"), Px(19,44,14,5,"#5B2C20"),
        Px(8,53,36,27,hoodie), Px(3,58,8,22,skin), Px(43,58,8,22,skin),
        Px(16,80,9,18,"#111827"), Px(28,80,9,18,"#111827"),
        Px(12,98,14,5,"#FFFFFF"), Px(27,98,14,5,"#FFFFFF"),
        Px(20,56,4,17,"#86EFAC"), Px(31,56,4,17,"#86EFAC")
    ])

def small_panel(x,y,w,h):
    g=[R(x,y,w,h,"#DCEAFE",6,"#1F2937",1.0,op=1.0)]
    g += [
        Px(x+6,y+6,w-12,8,"#60A5FA"), Px(x+6,y+h-14,w-12,8,"#1F2937"),
        Px(x+10,y+h-28,16,14,"#374151"), Px(x+30,y+h-32,18,18,"#4B5563"),
        Px(x+54,y+h-30,18,16,"#065F46"), Px(x+76,y+h-34,16,20,"#047857"),
        Px(x+18,y+22,8,8,"#FACC15"), Px(x+104,y+18,5,5,"#FACC15"),
        Px(x+112,y+24,4,4,"#FACC15")
    ]
    return "".join(g)

def draw_researcher_art(n):
    x,y,w,h=box(n)
    body=G(chibi("researcher"),x+48,y+60,1.15)
    doc=G(Px(0,0,22,16,"#FFFFFF","#CBD2DC",1)+Px(4,5,14,2,"#CBD2DC")+Px(4,10,11,2,"#CBD2DC"),x+112,y+134,1.35)
    return body+doc

def draw_gate_art(n):
    x,y,w,h=box(n)
    desk=R(x+54,y+110,w-108,35,"#EFF6FF",8,"#CBD5E1",1.0,op=1.0)
    panel=small_panel(x+132,y+78,72,46)
    magnifier=(f'<circle cx="{x+250}" cy="{y+92}" r="15" fill="none" stroke="#1F2937" stroke-width="3"/>'
               f'<line x1="{x+261}" y1="{y+103}" x2="{x+279}" y2="{y+120}" stroke="#1F2937" stroke-width="3" stroke-linecap="round"/>')
    return desk+G(chibi("executor"),x+82,y+68,0.72)+panel+G(chibi("reviewer"),x+238,y+66,0.72)+magnifier

def draw_callout_panel(x,y,w,h):
    return "".join([
        R(x,y,w,h,"#F8FBFF",6,"#CBD5E1",1.0,op=1.0),
        Px(x+4,y+4,w-8,8,"#60A5FA"), Px(x+4,y+h-10,w-8,6,"#1E293B"),
        Px(x+10,y+h-22,12,12,"#2563EB"), Px(x+25,y+h-24,12,14,"#0F172A"),
        Px(x+47,y+h-23,13,13,"#15803D"), Px(x+63,y+h-26,13,16,"#0F172A"),
        Px(x+84,y+14,6,6,"#FACC15"), Px(x+95,y+20,4,4,"#FACC15"),
        Px(x+15,y+16,16,5,"#A78BFA"), Px(x+33,y+18,14,4,"#FB7185")
    ])

def draw_structure(with_text):
    for g in BP["groups"]:
        b=g["bounds"]; o.append(R(b["x"],b["y"],b["w"],b["h"],col(g["tone"]+"_fill"),18,col(g["tone"]+"_stroke"),2))
        if with_text: o.append(T(b["x"]+20,b["y"]+32,g["label"],col(g["tone"]+"_accent"),18,"800","start"))
    for e in BP["edges"]:
        ax,ay,bx,by=edge_path(e); c=EK.get(e["kind"],col("arrow"))
        dash="8 5" if e["kind"] in ("retry","repair","write_wiki") else None
        curve=120 if e["kind"]=="retry" else (-150 if e["kind"]=="repair" else 0)
        o.append(arrow(ax,ay,bx,by,c,2.6,dash,curve))
        if with_text and e.get("label") and e["kind"]!="write_wiki":
            mx,my=(ax+bx)/2,(ay+by)/2
            if e["kind"]=="retry": my-=120
            if e["kind"]=="repair": my+=150
            tw=len(e["label"])*7.0+14
            o.append(R(mx-tw/2,my-11,tw,19,"#FFFFFF",4,op=0.95)); o.append(T(mx,my+3,e["label"],EK.get(e["kind"],col("text")),11.5,"700"))
    for n in BP["nodes"]:
        x,y,w,h=box(n); acc=col(n.get("accent","node_stroke")); shape=n.get("shape","process")
        fill="#F8FAFD" if shape=="datastore" else col("node_fill")
        if shape=="diamond":
            cx,cy=n["pos"]["x"],n["pos"]["y"]
            o.append(f'<path d="M{cx},{y} L{x+w},{cy} L{cx},{y+h} L{x},{cy} Z" fill="{fill}" stroke="{acc}" stroke-width="2.4"/>')
        else:
            o.append(R(x,y,w,h,fill,12 if shape!="character" else 14,acc,2.6 if n.get("emphasis") else 2,dash="6 5" if shape=="character" else None,filt="url(#cardShadow)" if with_text and shape!="character" else None))
        if not with_text:
            o.append(R(x+14,y+h/2-7,w-28,14,"#EEF1F5",4,op=0.9))   # skeleton: empty zone
            if shape=="character": o.append(T(n["pos"]["x"],y+h/2+4,"〔"+n.get("char","fig")+"〕","#AAB2C0",13,"700"))
            continue
        # CONDITION text: title (bold) + desc (muted) INSIDE the box — BIG enough to survive an image2 redraw.
        title=str(n["label"]).split("\\n")[0]; desc=n.get("desc","")
        cx=n["pos"]["x"]; top=n.get("char") is not None
        ty=(y+26) if top else (n["pos"]["y"]-(7 if desc else -5))
        o.append(T(cx,ty,title,col("text"),18 if shape!="character" else 16,"800"))
        if desc:
            for i,dl in enumerate(desc.split("\n")):
                o.append(T(cx,ty+22+i*18,dl,col("muted"),13,"600"))
        if shape=="character":
            o.append(draw_researcher_art(n))
        if n.get("id")=="gate":
            o.append(draw_gate_art(n))

def draw_callouts(with_text):
    for c in BP.get("callouts",[]):
        x=c["pos"]["x"]-c["size"]["w"]/2; y=c["pos"]["y"]-c["size"]["h"]/2; cx=c["pos"]["x"]
        o.append(R(x,y,c["size"]["w"],c["size"]["h"],"#FDECEC",12,col("red"),2.4))
        if not with_text:
            o.append(R(x+16,y+16,c["size"]["w"]-32,12,"#F6D5D5",4)); continue
        o.append(T(cx,y+26,c["title"],col("red"),17,"800"))
        o.append(draw_callout_panel(cx-78,y+38,156,38))
        for i,ln in enumerate(c["lines"]):
            o.append(T(cx,y+91+i*20,ln,col("text"),12.5,"700"))
        sy=y+91+len(c["lines"])*20+6
        o.append(f'<g transform="rotate(-7 {cx} {sy})"><rect x="{cx-62}" y="{sy-17}" width="124" height="33" rx="6" fill="#FFFFFF" stroke="{col("red")}" stroke-width="2.8"/>{T(cx,sy+5,"verdict: RETRY",col("red"),15,"800")}</g>')

if MODE=="skeleton":
    draw_structure(False); draw_callouts(False)
elif MODE=="condition":
    # the FULLY-LABELED clean layout we hand to image2 (text lives IN the boxes). image2 re-renders this
    # into a polished academic figure, KEEPING the text and ADDING our chibi characters. We paste NOTHING.
    o.append(T(60,80,BP["title"]["main"],col("text"),40,"800","start"))
    o.append(T(62,112,BP["title"]["sub"],col("muted"),17,"500","start"))
    draw_structure(True); draw_callouts(True)
    o.append(T(W/2,H-22,BP["rail"]["label"],col("muted"),13,"600"))

svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'+"".join(o)+"</svg>"
out=os.path.join(HERE,"figassets",f"method_{MODE}.svg")
open(out,"w").write(svg); print("wrote",out)
