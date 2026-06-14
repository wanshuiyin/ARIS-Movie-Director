#!/usr/bin/env python3
"""preflight.py — verify a fresh machine has what BOTH pipelines need, BEFORE the first (metered) run.

Checks the external tools the README names (codex CLI, gemini CLI, a headless Chrome/Chromium) plus the one
Python module the docs use (jsonschema), and prints a per-check table. Exits non-zero if any REQUIRED check
fails, so a user discovers a missing tool/auth here (free) instead of mid-bake. Pure stdlib.

    python3 cli/preflight.py            # check everything
    python3 cli/preflight.py --figure   # only the method-figure path's needs
    python3 cli/preflight.py --comic    # only the comic path's needs
"""
import argparse
import importlib.util
import os
import shutil
import sys

# (name, kind, how-to) — kind: "bin" = on PATH, "pybin"-alts = any-of, "mod" = importable
CHECKS = {
    "codex": ("bin", "codex", "OpenAI Codex CLI — needed for the image bake + the Codex reviewer (must be authed)"),
    "gemini": ("bin", "gemini", "Gemini CLI — the Gemini reviewer; must run as `gemini --model auto-gemini-3`"),
    "chrome": ("anyof", ["chromium", "google-chrome", "chromium-browser", "chrome",
                          "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                          "/Applications/Chromium.app/Contents/MacOS/Chromium"],
               "headless Chrome/Chromium — rasterizes the content-SVG blueprint / comic pages (matches render_condition.py's finder)"),
    "jsonschema": ("mod", "jsonschema", "Python module — the documented schema-validate step (pip install jsonschema)"),
}
# which checks each pipeline needs
NEED = {
    "figure": ["codex", "gemini", "chrome", "jsonschema"],
    "comic":  ["codex", "gemini", "chrome", "jsonschema"],
}


def probe(kind, target):
    if kind == "bin":
        return shutil.which(target) is not None, shutil.which(target) or "not on PATH"
    if kind == "anyof":
        for t in target:
            p = shutil.which(t) or (t if (t.startswith("/") and os.path.exists(t)) else None)
            if p:
                return True, p
        return False, "none found (PATH or macOS app path)"
    if kind == "mod":
        spec = importlib.util.find_spec(target)
        return spec is not None, (spec.origin if spec else "not importable")
    return False, "unknown check"


def main():
    ap = argparse.ArgumentParser(description="preflight: verify external tools before a run")
    ap.add_argument("--figure", action="store_true", help="only the method-figure path")
    ap.add_argument("--comic", action="store_true", help="only the comic path")
    a = ap.parse_args()
    needed = set()
    if a.figure:
        needed |= set(NEED["figure"])
    if a.comic:
        needed |= set(NEED["comic"])
    if not needed:
        needed = set(NEED["figure"]) | set(NEED["comic"])

    print(f"[preflight] checking {len(needed)} requirement(s)\n")
    missing = []
    for name in sorted(needed):
        kind, target, how = CHECKS[name]
        ok, detail = probe(kind, target)
        print(f"  {'✓' if ok else '✗'} {name:12s} {detail}")
        if not ok:
            missing.append((name, how))
    if missing:
        print(f"\n[preflight] FAIL — {len(missing)} missing:")
        for name, how in missing:
            print(f"  - {name}: {how}")
        print("\nInstall/auth the above, then re-run. (Tools are also auth-gated — `codex`/`gemini` must be "
              "logged in; a baked run additionally needs image-generation entitlement on the Codex account.)")
        sys.exit(1)
    print("\n[preflight] PASS — all required tools present. (Note: presence != auth — confirm `codex` and "
          "`gemini --model auto-gemini-3` actually return before a long run.)")


if __name__ == "__main__":
    main()
