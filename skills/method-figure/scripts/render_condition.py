#!/usr/bin/env python3
"""render_condition.py — blueprint -> a clean WHITE-BG labeled CONDITION (SVG; pure stdlib).

The condition is the image references' structural anchor: pale phase panels, labeled node cards
(title=label_exact + one desc_exact line), labeled arrows, character PLACEHOLDER zones, the callout, the
rail. It is NOT the final figure — image_gen redraws it into the aesthetic while keeping the locked text.
Emit SVG (no deps); rasterize with headless Chrome:
  chrome --headless=new --screenshot=condition.png --window-size=W,H --force-device-scale-factor=2 file://<svg>

Usage: python3 render_condition.py blueprint.json --out condition.svg
"""
import argparse, json, math

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("blueprint"); ap.add_argument("--out", default="condition.svg")
    ap.add_argument("--png", help="also rasterize to this PNG via headless Chrome (the bake needs a PNG condition)")
    a = ap.parse_args()
    bp = json.load(open(a.blueprint, encoding="utf-8"))
    W = bp["canvas"]["width"]; H = bp["canvas"]["height"]; BG = bp["canvas"].get("background", "#FFFFFF")
    PAL = (bp.get("style") or {}).get("palette", {})
    TONE = {"blue": ("#E5EEFB", "#9DBDEB", "#2563EB"), "peach": ("#FDEBD8", "#F4C18A", "#EA580C"),
            "green": ("#DEF5E6", "#9BD9B0", "#0E9F6E"), "grey": ("#F1F3F6", "#CBD2DC", "#6B7280")}
    INK = PAL.get("text", "#1F2937"); MUT = PAL.get("muted", "#6B7280"); RED = PAL.get("red", "#DC2626")
    FONT = (bp.get("style") or {}).get("font_family", "Inter, Arial, sans-serif")
    NODES = {n["id"]: n for n in bp["nodes"]}
    o = []
    def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    def T(x, y, s, fill, sz, wt="700", anc="middle"):
        return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{sz}" font-weight="{wt}" font-family="{FONT}" text-anchor="{anc}">{esc(s)}</text>'
    def R(x, y, w, h, fill, rx=12, st=None, sw=0, dash=None):
        e = f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx}" fill="{fill}"'
        if st: e += f' stroke="{st}" stroke-width="{sw}"'
        if dash: e += f' stroke-dasharray="{dash}"'
        return e + "/>"
    def lab(n, k): return n.get(k + "_exact", n.get(k, ""))
    def box(n):
        s = n.get("size", {}); w = s.get("w", 200); h = s.get("h", 76)
        return n["pos"]["x"] - w / 2, n["pos"]["y"] - h / 2, w, h
    def arrow(x1, y1, x2, y2, c, w=2.6, dash=None, curve=0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        if curve:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - curve
            p = f'<path d="M{x1:.0f},{y1:.0f} Q{mx:.0f},{my:.0f} {x2:.0f},{y2:.0f}" fill="none" stroke="{c}" stroke-width="{w}"{d}/>'
            ang = math.atan2(y2 - my, x2 - mx)
        else:
            p = f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{c}" stroke-width="{w}"{d}/>'
            ang = math.atan2(y2 - y1, x2 - x1)
        L = 11
        head = (f'<path d="M{x2:.0f},{y2:.0f} L{x2-L*math.cos(ang-0.45):.0f},{y2-L*math.sin(ang-0.45):.0f} '
                f'L{x2-L*math.cos(ang+0.45):.0f},{y2-L*math.sin(ang+0.45):.0f} Z" fill="{c}"/>')
        return p + head

    o.append(R(0, 0, W, H, BG, 0))
    tt = bp.get("title", {})
    if tt.get("main"): o.append(T(56, 78, tt["main"], INK, 40, "800", "start"))
    if tt.get("sub"): o.append(T(58, 110, tt["sub"], MUT, 17, "500", "start"))
    EK = {"flow": "#4B5563", "keep": "#0E9F6E", "retry": "#EA580C", "repair": "#2563EB", "write": MUT, "audit": MUT, "human": RED}
    # phase panels
    for g in bp.get("groups", []):
        b = g["bounds"]; t = TONE.get(g.get("tone", "grey"), TONE["grey"])
        o.append(R(b["x"], b["y"], b["w"], b["h"], t[0], 18, t[1], 2))
        o.append(T(b["x"] + 20, b["y"] + 32, lab(g, "label"), t[2], 18, "800", "start"))
    # edges + labels
    for e in bp.get("edges", []):
        af = NODES.get(e["from"]); at = NODES.get(e["to"])
        if not af or not at: continue
        ax, ay, bx, by = af["pos"]["x"], af["pos"]["y"], at["pos"]["x"], at["pos"]["y"]
        c = EK.get(e["kind"], "#4B5563")
        dash = "8 5" if e["kind"] in ("retry", "repair", "write", "audit") else None
        curve = 120 if e["kind"] == "retry" else (-150 if e["kind"] == "repair" else 0)
        o.append(arrow(ax, ay, bx, by, c, 2.6, dash, curve))
        el = lab(e, "label")
        if el:
            mx, my = (ax + bx) / 2, (ay + by) / 2 - (120 if e["kind"] == "retry" else (-150 if e["kind"] == "repair" else 0))
            tw = len(el) * 7 + 14
            o.append(R(mx - tw / 2, my - 11, tw, 19, "#FFFFFF", 4) + T(mx, my + 3, el, c, 11.5, "700"))
    # nodes
    for n in bp["nodes"]:
        x, y, w, h = box(n); shp = n.get("shape", "process")
        acc = PAL.get(n.get("accent", ""), n.get("accent", "")) or "#CBD2DC"
        fill = "#F8FAFD" if shp == "datastore" else "#FFFFFF"
        if shp == "diamond":
            cx, cy = n["pos"]["x"], n["pos"]["y"]
            o.append(f'<path d="M{cx},{y} L{x+w},{cy} L{cx},{y+h} L{x},{cy} Z" fill="{fill}" stroke="{acc}" stroke-width="2.4"/>')
        else:
            o.append(R(x, y, w, h, fill, 12, acc, 2, dash="6 5" if shp == "character" else None))
        title = lab(n, "label"); desc = lab(n, "desc"); cx = n["pos"]["x"]
        if shp == "character":
            o.append(T(cx, y + 26, title, INK, 14, "800"));
            if desc: o.append(T(cx, y + 44, desc, MUT, 11, "600"))
            o.append(T(cx, y + h - 12, "〔ARIS chibi here〕", MUT, 10, "600"))
        else:
            ty = n["pos"]["y"] - (7 if desc else -5)
            o.append(T(cx, ty, title, INK, 18, "800"))
            if desc:
                for i, dl in enumerate(desc.split("\n")):
                    o.append(T(cx, ty + 22 + i * 18, dl, MUT, 13, "600"))
    # callouts
    for c in bp.get("callouts", []):
        p = c.get("pos", {}); s = c.get("size", {})
        cw, ch = s.get("w", 360), s.get("h", 140); cx0, cy0 = p.get("x", W / 2) - cw / 2, p.get("y", H - 120) - ch / 2
        o.append(R(cx0, cy0, cw, ch, "#FDECEC", 12, RED, 2.4))
        o.append(T(p.get("x", W / 2), cy0 + 26, lab(c, "title"), RED, 17, "800"))
        for i, ln in enumerate(c.get("lines_exact", c.get("lines", []))):
            o.append(T(p.get("x", W / 2), cy0 + 52 + i * 22, ln, INK, 12.5, "700"))
    rail = bp.get("rail", {})
    if rail.get("label_exact") or rail.get("label"):
        o.append(T(W / 2, H - 22, lab(rail, "label"), MUT, 13, "600"))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + "".join(o) + "</svg>"
    svg_path = a.out if a.out.endswith(".svg") else a.out + ".svg"
    open(svg_path, "w", encoding="utf-8").write(svg)
    print(f"[render_condition] wrote {svg_path} ({len(svg)} bytes, {W}x{H})")
    if a.png:
        import shutil, subprocess, os
        png_path = a.png if a.png.endswith(".png") else a.png + ".png"
        chrome = next((c for c in [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chromium-browser")] if c and os.path.exists(c) if c), None) \
            or shutil.which("google-chrome") or shutil.which("chromium")
        if not chrome:
            print(f"[render_condition] no headless Chrome found; rasterize manually:\n"
                  f"  <chrome> --headless=new --disable-gpu --screenshot='{os.path.abspath(png_path)}' "
                  f"--window-size={int(W)},{int(H)} --force-device-scale-factor=2 'file://{os.path.abspath(svg_path)}'")
        else:
            subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            f"--screenshot={os.path.abspath(png_path)}", f"--window-size={int(W)},{int(H)}",
                            "--force-device-scale-factor=2", f"file://{os.path.abspath(svg_path)}"],
                           timeout=60, capture_output=True)
            ok = os.path.exists(png_path) and os.path.getsize(png_path) > 1000
            print(f"[render_condition] {'rasterized → ' + png_path if ok else 'rasterize FAILED (use the manual command)'}")

if __name__ == "__main__":
    main()
