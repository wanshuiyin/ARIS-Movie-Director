#!/usr/bin/env python3
"""build_comic.py — comic.json (content-graph IR) -> self-contained comic/index.html.

Reads comic.json, VALIDATES it, base64-inlines every panel image (single-file contract:
NO runtime fetch, works on GitHub Pages + offline PDF), injects the IR into
comic_kit/comic_template.html at the {{COMIC_JSON}} slot, writes comic/index.html.
Pure stdlib. Re-run after any panel regen or comic.json edit (one-panel swap = flip
active_attempt_id + re-run).

Hard-fails (review blockers): missing inlined image, unknown panel_id in a page,
safe_zone without id, bubble.anchor not in its panel's safe_zones, unknown text_mode.

Usage:  python3 build_comic.py              # inline (default, release)
        python3 build_comic.py --no-inline  # reference image (dev only, NOT single-file)
"""
import json, base64, sys, mimetypes
from pathlib import Path

PROJ = Path(__file__).resolve().parent
COMIC_JSON = PROJ / "comic.json"
TEMPLATE = PROJ / "comic_kit" / "comic_template.html"
OUT = PROJ / "comic" / "index.html"
INLINE = "--no-inline" not in sys.argv
KNOWN_MODES = {"html", "baked", "code"}


def die(msg):
    sys.exit("[build_comic] FATAL: " + msg)


def data_uri(path: Path):
    if not path.is_file():
        return None
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def validate(comic):
    panels = comic.get("panels", {})
    errs = []
    # 1) every page panel_id must exist
    for pg in comic.get("pages", []):
        for pid in pg.get("panel_ids", []):
            if pid not in panels:
                errs.append(f"page {pg.get('id')}: unknown panel_id '{pid}' (not in panels{{}})")
    # 2) text_mode known (global + per-panel)
    gm = comic.get("defaults", {}).get("text_mode", "html")
    if gm not in KNOWN_MODES:
        errs.append(f"defaults.text_mode '{gm}' not in {sorted(KNOWN_MODES)}")
    # 3) per panel: safe_zones have ids; bubble.anchor resolves
    for pid, p in panels.items():
        pm = p.get("text_mode")
        if pm is not None and pm not in KNOWN_MODES:
            errs.append(f"panel {pid}: text_mode '{pm}' not in {sorted(KNOWN_MODES)}")
        zone_ids = set()
        for z in p.get("safe_zones", []):
            if "id" not in z:
                errs.append(f"panel {pid}: a safe_zone has no 'id'")
            else:
                zone_ids.add(z["id"])
        for b in p.get("bubbles", []):
            a = b.get("anchor")
            if a is not None and a not in zone_ids:
                errs.append(f"panel {pid}: bubble.anchor '{a}' not in safe_zones {sorted(zone_ids)}")
    return errs


def main():
    if not COMIC_JSON.is_file():
        die(f"comic.json missing: {COMIC_JSON}")
    comic = json.loads(COMIC_JSON.read_text(encoding="utf-8"))

    errs = validate(comic)
    if errs:
        die("comic.json validation failed:\n  - " + "\n  - ".join(errs))

    panels = comic.get("panels", {})
    inlined, missing = 0, []
    for pid, p in panels.items():
        ip = p.get("image_path")
        if not ip:
            missing.append(pid); continue
        abs_path = Path(ip) if Path(ip).is_absolute() else (PROJ / ip)
        abs_path = abs_path.resolve()
        if INLINE:
            uri = data_uri(abs_path)
            if uri:
                p["image_data"] = uri; inlined += 1
            else:
                missing.append(pid)
        else:
            # dev only: POSIX-slash relative URL from comic/ to the image
            import os
            if abs_path.is_file():
                p["image_data"] = os.path.relpath(abs_path, OUT.parent).replace("\\", "/")
            else:
                missing.append(pid)

    if missing:
        if INLINE:
            die("INLINE build but no image for panels (single-file contract broken): " + str(missing)
                + "\n  Generate the panels (or fix image_path) before an inline build, or use --no-inline for a dev preview.")
        else:
            print(f"[build_comic] WARNING (--no-inline): no image for panels: {missing}")

    if not TEMPLATE.is_file():
        die(f"template missing: {TEMPLATE}")
    tpl = TEMPLATE.read_text(encoding="utf-8")
    if "{{COMIC_JSON}}" not in tpl:
        die("template has no {{COMIC_JSON}} slot")
    blob = json.dumps(comic, ensure_ascii=False).replace("</", "<\\/")  # neutralize </script early-terminate
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(tpl.replace("{{COMIC_JSON}}", blob), encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"[build_comic] OK -> {OUT}  ({kb:.1f} KB, {'inlined ' + str(inlined) + ' images' if INLINE else 'referenced images'})")


if __name__ == "__main__":
    main()
