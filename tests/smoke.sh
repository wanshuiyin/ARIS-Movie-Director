#!/usr/bin/env bash
# Deterministic gate smoke test — the CI green check. Pure stdlib Python + Node syntax only;
# NO image_gen / Chrome / network / credentials, so it always runs in a clean CI runner.
# Run locally:  bash tests/smoke.sh
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0
step() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }
ok()   { echo "  ok   $1"; }
bad()  { echo "  FAIL $1"; fail=1; }

step "1. Python syntax (py_compile)"
if python3 -m py_compile \
    cli/validate_wiki.py cli/preflight.py \
    skills/comic-director/scripts/run_comic.py \
    skills/comic-panel-prompt-builder/scripts/build_prompt.py \
    skills/method-figure/scripts/run_spiral.py \
    skills/method-figure/scripts/compile_brief.py \
    skills/method-figure/scripts/content_diff.py \
    skills/method-figure/scripts/validate_blueprint.py \
    tests/test_gates.py
then ok "all scripts compile"; else bad "py_compile"; fi

step "2. JS syntax (node --check)"
if command -v node >/dev/null 2>&1; then
  node --check packages/core/spiral_engine.js && ok "spiral_engine.js" || bad "spiral_engine.js"
else bad "node not found"; fi

step "3. validate_wiki — both examples"
python3 cli/validate_wiki.py examples/comic_m3_audit  >/dev/null 2>&1 && ok "comic_m3_audit (198 nodes)" || bad "comic_m3_audit"
python3 cli/validate_wiki.py examples/comic_min_author >/dev/null 2>&1 && ok "comic_min_author (fixture)" || bad "comic_min_author"

step "4. comic engine — run_comic.py --dry-run (no image_gen)"
python3 skills/comic-director/scripts/run_comic.py --project examples/comic_m3_audit --page P00_cover --panels S01 --dry-run >/dev/null 2>&1 \
  && ok "dry-run prints bake prompts" || bad "run_comic --dry-run"

step "5. method-figure Step-0 — compile_brief (brief → traceable blueprint, no Chrome)"
python3 skills/method-figure/scripts/compile_brief.py \
  skills/method-figure/examples/method_figure/method_figure_brief.json \
  --out /tmp/ci_blueprint.json --trace /tmp/ci_trace.json >/dev/null 2>&1 \
  && ok "compile_brief OK" || bad "compile_brief"

step "6. method-figure — validate_blueprint on the example"
python3 skills/method-figure/scripts/validate_blueprint.py skills/method-figure/examples/method_figure/blueprint.json >/dev/null 2>&1 \
  && ok "blueprint valid" || bad "validate_blueprint"

step "7. gate regression tests (vetoes / fail-closed / literal-diff exactness)"
python3 tests/test_gates.py && ok "test_gates.py" || bad "test_gates.py"

echo
if [ "$fail" = 0 ]; then echo "✅ ALL GATES GREEN"; exit 0; else echo "❌ SOME GATES FAILED"; exit 1; fi
