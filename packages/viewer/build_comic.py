#!/usr/bin/env python3
"""build_comic.py — comic.json (content-graph IR) -> self-contained comic/index.html.

Reads comic.json, VALIDATES it, base64-inlines every panel image (single-file contract:
NO runtime fetch, works on GitHub Pages + offline PDF), injects the IR into
comic_kit/comic_template.html at the {{COMIC_JSON}} slot, writes comic/index.html.
Pure stdlib. Re-run after any panel regen or comic.json edit (one-panel swap = flip
active_attempt_id + re-run).

Hard-fails (review blockers): missing inlined image, unknown panel_id in a page,
safe_zone without id, bubble.anchor not in its panel's safe_zones, unknown text_mode.

Usage:  python3 build_comic.py <project_dir>              # inline (default, release)
        python3 build_comic.py <project_dir> --no-inline  # reference image (dev only, NOT single-file)
        python3 build_comic.py                            # project_dir defaults to this script's dir
"""
import json, base64, sys, mimetypes
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
_args = [a for a in sys.argv[1:] if not a.startswith("--")]
PROJ = Path(_args[0]).resolve() if _args else SCRIPT_DIR   # PROJECT dir (comic.json, panels/, outputs/) — pass as argv[1]
COMIC_JSON = PROJ / "comic.json"
TEMPLATE = SCRIPT_DIR / "comic_template.html"              # FRAMEWORK viewer template, ships next to this script
OUT = PROJ / "outputs" / "index.html"
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


_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _safe_rel_image(ip):
    """image_path must be PROJECT-RELATIVE (no absolute path, no '..'), an image, and resolve UNDER PROJ.
    Otherwise return None — a publishable single-file artifact must never base64-inline arbitrary local files."""
    if not isinstance(ip, str) or not ip or ip.startswith("/") or ".." in ip.replace("\\", "/").split("/"):
        return None
    if Path(ip).suffix.lower() not in _IMG_EXT:
        return None
    ap = (PROJ / ip).resolve()
    try:
        ap.relative_to(PROJ.resolve())
    except ValueError:
        return None
    return ap


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
    # 4) page shape: no empty pages; a grid2x2 needs exactly 4 panels
    for pg in comic.get("pages", []):
        n = len(pg.get("panel_ids", []))
        if n == 0:
            errs.append(f"page {pg.get('id')}: zero panel_ids")
        if pg.get("type") == "grid2x2" and n != 4:
            errs.append(f"page {pg.get('id')}: grid2x2 needs exactly 4 panels, got {n}")
    # 5) per panel: image_path must be a SAFE project-relative image; crop in range
    for pid, p in panels.items():
        ip = p.get("image_path")
        if ip and _safe_rel_image(ip) is None:
            errs.append(f"panel {pid}: unsafe image_path {ip!r} (must be a project-relative .png/.jpg/.webp under the project — no absolute path, no '..')")
        c = p.get("crop") or {}
        pos = c.get("position")
        if pos is not None and (not isinstance(pos, list) or len(pos) != 2 or not all(isinstance(x, (int, float)) and 0 <= x <= 1 for x in pos)):
            errs.append(f"panel {pid}: crop.position must be [x,y] in 0..1, got {pos!r}")
        z = c.get("zoom")
        if z is not None and not (isinstance(z, (int, float)) and z >= 1):
            errs.append(f"panel {pid}: crop.zoom must be >= 1, got {z!r}")
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
        abs_path = _safe_rel_image(ip)   # rejects absolute / '..' / non-image (validate() already flagged it; this is the inline-time backstop)
        if abs_path is None:
            missing.append(pid); continue
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
    # Escape EVERY < and > as </> (valid JSON, JSON.parse decodes them back). The old `</`-only replace
    # left `<!--<script>` able to break out of the <script type=application/json> island; this closes all of them.
    blob = json.dumps(comic, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(tpl.replace("{{COMIC_JSON}}", blob), encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"[build_comic] OK -> {OUT}  ({kb:.1f} KB, {'inlined ' + str(inlined) + ' images' if INLINE else 'referenced images'})")


if __name__ == "__main__":
    main()
