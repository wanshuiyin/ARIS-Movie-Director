#!/usr/bin/env python3
"""check_asset_collisions.py — fail-fast guard for the "one canonical source per token" rule.

Statically scans every gen_*.py in this directory for asset writes — calls of the form
    w("<name>", ...)
— and asserts each output filename is written by EXACTLY ONE generator. Two generators writing the
same path with different content is a silent, run-order-dependent corruption (whoever runs last wins);
this catches it deterministically without running anything.

Deliberately NOT a "skip if the file already exists" guard: that would HIDE the order bug instead of
surfacing it. Run this in CI / before a release. Exit code 0 = clean, 1 = collision(s) found.
"""
import os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
# w("name.ext"  — first string arg to a w(...) call
WRITE = re.compile(r'\bw\(\s*["\']([^"\']+\.(?:svg|json|png))["\']')

def main():
    writers = {}  # filename -> set(script)
    for path in sorted(glob.glob(os.path.join(HERE, "gen_*.py"))):
        script = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            for name in WRITE.findall(f.read()):
                writers.setdefault(name, set()).add(script)
    collisions = {n: sorted(s) for n, s in writers.items() if len(s) > 1}
    total = len(writers)
    if collisions:
        print(f"✗ ASSET COLLISION — {len(collisions)} filename(s) written by >1 generator "
              f"(out of {total} tracked outputs):")
        for name, scripts in sorted(collisions.items()):
            print(f"    {name}  ←  {', '.join(scripts)}")
        print("\nEach asset must have ONE canonical owner ('one visual dialect, never two'). "
              "Give the specialized version a distinct filename, or delete the dead duplicate.")
        return 1
    print(f"✓ no asset collisions — all {total} generator outputs are single-source.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
