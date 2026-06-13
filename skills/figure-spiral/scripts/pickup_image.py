#!/usr/bin/env python3
"""pickup_image.py — fail-closed pickup + verify of a natively-generated image (pure stdlib).

codex image_generation writes to a GLOBAL dir (~/.codex/generated_images). Picking "the newest file" is a
footgun across concurrent runs, and we must never accept a hand-written SVG/PNG masquerading as a native
bake. This picks the newest PNG created AFTER a marker timestamp, verifies the PNG signature + size +
dimensions, records the sha256, and copies it to --out. Exits non-zero (fail-closed) if nothing valid.

The bake call + this pickup MUST be serialized by the orchestrator (one bake at a time) — see SKILL.md.

Usage: python3 pickup_image.py --marker <epoch_seconds> --out path/round1.png [--min-bytes 200000]
       [--dir ~/.codex/generated_images]   # prints a JSON {ok,path,sha256,bytes,width,height}
"""
import argparse, hashlib, json, os, struct, sys, glob, shutil

def png_dims(path):
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != b"\x89PNG\r\n\x1a\n": return None
        f.read(4); ctype = f.read(4)
        if ctype != b"IHDR": return None
        w, h = struct.unpack(">II", f.read(8))
        return w, h

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marker", type=float, required=True, help="epoch seconds; accept files with mtime >= this")
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-bytes", type=int, default=200000)
    ap.add_argument("--dir", default=os.path.expanduser("~/.codex/generated_images"))
    a = ap.parse_args()
    cands = [p for p in glob.glob(os.path.join(os.path.expanduser(a.dir), "*.png"))
             if os.path.getmtime(p) >= a.marker - 1]
    cands.sort(key=os.path.getmtime, reverse=True)
    for p in cands:
        b = os.path.getsize(p)
        if b < a.min_bytes:
            continue
        dims = png_dims(p)
        if not dims:
            continue
        sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        shutil.copy(p, a.out)
        print(json.dumps({"ok": True, "path": a.out, "src": os.path.basename(p), "sha256": sha,
                          "bytes": b, "width": dims[0], "height": dims[1]}, ensure_ascii=False))
        return 0
    print(json.dumps({"ok": False, "reason": "no valid native PNG after marker (fail-closed)",
                      "checked": len(cands), "dir": a.dir, "min_bytes": a.min_bytes}), file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
