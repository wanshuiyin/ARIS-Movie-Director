#!/usr/bin/env python3
"""_validate.py — the ONE canonical 搬运工 v2 validator for a composed bake message (pure stdlib).

Single source of truth for the four binary vetoes the panel-prompt compiler enforces at emit time, so the
banned-vocab list / MAX_MESSAGE_CHARS / no-baked-bubble / real-refs rules never fork between SKILL.md prose and
the executable. Imported by build_prompt.py; also runnable standalone for a quick check:

    python3 _validate.py --composed <file.txt> --text-mode html --bubbles "a" "b" \
        --refs assets/x.png assets/y.png

Each dimension is BINARY; ANY hit fails (detect-only, no single-vote averaging). Exit 0 = clean, 4 = a veto
fired (banned-vocab / length / baked-bubble / ref). This is a deterministic transform check, NOT a cross-model
acquittal — the quality verdict on the baked pixels lives downstream in comic-director's panel_gate.
"""
import argparse, json, os, re, sys

# --- single source of the limits/vocab (do NOT duplicate these constants elsewhere) ---
MAX_MESSAGE_CHARS = 4000  # ~600 words, the empirical backend tolerance

# ~80 case-insensitive, word-boundary patterns the backend's OWN agents own (camera/lens/lighting/quality/etc.).
# 搬运工原則: the backend owns optics, ART_BIBLE owns style — none of this may leak into a bake message.
BANNED_VOCAB = [
    # quality padding
    r"\b8K\b", r"\b4K\b", r"hyperrealistic", r"photorealistic", r"ultra-?realistic", r"\bcinematic\b",
    r"\bprofessional\b", r"award-winning", r"\bmasterpiece\b", r"\b(?:high|best)\s+quality\b",
    r"highly detailed", r"intricate details", r"trending on artstation",
    # camera
    r"the camera", r"\bcamera\s+(?:moves|pans|tilts|zooms|tracks|pushes|pulls|cranes)\b",
    r"\b(?:wide|close-?up|medium|long|establishing|POV)\s+shot\b", r"over-the-shoulder", r"\bdolly\b",
    r"\btilt\b", r"\bpan\b", r"\bcrane\b", r"\bdrone\b", r"\baerial\b", r"\borbital\b", r"whip-?pan",
    r"tracking shot", r"push-?in", r"pull out", r"\bzoom\b", r"rack focus", r"focus pull", r"\bjib\b",
    r"steadicam", r"handheld",
    # lens
    r"\b\d{2,3}mm\b", r"\bf/\d", r"\bbokeh\b", r"depth of field", r"shallow DOF", r"\bDOF\b", r"\blens\b",
    r"wide-?angle", r"telephoto", r"anamorphic", r"lens flare",
    # lighting
    r"\blighting\b", r"\b(?:rim|key|fill)\s+light\b", r"three-point lighting", r"golden hour", r"blue hour",
    r"studio lighting", r"\b(?:soft|hard)\s+light\b", r"low-?key", r"volumetric", r"god rays", r"chiaroscuro",
    # engine / brand
    r"Unreal Engine", r"\bOctane\b", r"V-?Ray", r"\bBlender\b", r"Midjourney", r"Stable Diffusion", r"\bSora\b",
    r"\bRunway\b", r"\bPika\b",
    # clichés
    r"\bepic\b", r"breathtaking", r"\bstunning\b", r"\bgorgeous\b", r"mesmerizing", r"otherworldly",
    r"surreal masterpiece",
]
_BANNED_RE = [(p, re.compile(p, re.IGNORECASE)) for p in BANNED_VOCAB]


def scan_banned(composed):
    """Return the list of {pattern, match} hits (empty == clean)."""
    hits = []
    for pat, rx in _BANNED_RE:
        m = rx.search(composed)
        if m:
            hits.append({"pattern": pat, "match": m.group(0)})
    return hits


def check_length(composed):
    return len(composed) <= MAX_MESSAGE_CHARS, len(composed)


def check_no_baked_bubbles(composed, text_mode, bubble_texts):
    """no_baked_bubbles veto: if text_mode != 'baked', no quoted bubble dialogue may appear in the message.
    When text_mode == 'baked' the dialogue is allowed (BAKED DIALOGUE block) — this veto fires only for
    html/code panels. Returns (ok, leaked_texts)."""
    if text_mode == "baked":
        return True, []
    leaked = [b for b in bubble_texts if b and b.strip() and b.strip() in composed]
    return (len(leaked) == 0), leaked


_PENDING_RE = re.compile(r"(?:^|[\s:])pending:", re.IGNORECASE)


def check_real_refs(ref_paths, project_dir):
    """real_refs_ok veto: every identity_ref_path must be a REAL locked .png on disk; the ref set is exact —
    no pending:*, no raw asset_id strings, no missing files. A null entry is the documented 'use project
    canonical' fallback and is allowed. Returns (ok, problems)."""
    problems = []
    for r in ref_paths:
        if r is None:
            continue  # documented canonical-fallback
        if not isinstance(r, str) or _PENDING_RE.search(r) or not r.lower().endswith(".png"):
            problems.append({"ref": r, "why": "not a real .png path (pending:* / raw id / wrong ext)"})
            continue
        p = r if os.path.isabs(r) else os.path.join(project_dir, r)
        if not os.path.exists(p):
            problems.append({"ref": r, "why": "file does not exist on disk"})
    return (len(problems) == 0), problems


def validate(composed, text_mode, bubble_texts, ref_paths, project_dir):
    """Run all four binary vetoes. Returns a dict ready to dump as _validation.json with passes_all."""
    banned = scan_banned(composed)
    length_ok, n = check_length(composed)
    no_bubbles_ok, leaked = check_no_baked_bubbles(composed, text_mode, bubble_texts)
    real_refs_ok, ref_problems = check_real_refs(ref_paths, project_dir)
    no_banned_vocab = len(banned) == 0
    passes_all = length_ok and no_banned_vocab and no_bubbles_ok and real_refs_ok
    return {
        "passes_all": passes_all,
        "length_ok": length_ok, "composed_len": n, "max_message_chars": MAX_MESSAGE_CHARS,
        "no_banned_vocab": no_banned_vocab, "banned_hits": banned,
        "no_baked_bubbles": no_bubbles_ok, "leaked_bubble_texts": leaked,
        "real_refs_ok": real_refs_ok, "ref_problems": ref_problems,
    }


def main():
    ap = argparse.ArgumentParser(description="canonical 搬运工 v2 bake-message validator (binary vetoes)")
    ap.add_argument("--composed", required=True, help="path to the composed message text")
    ap.add_argument("--text-mode", default="html", choices=["baked", "html", "code"])
    ap.add_argument("--bubbles", nargs="*", default=[], help="bubble dialogue strings (for no-baked-bubble veto)")
    ap.add_argument("--refs", nargs="*", default=[], help="identity_ref_paths[] (for real-refs veto)")
    ap.add_argument("--project-dir", default=".", help="project dir to resolve relative ref paths")
    a = ap.parse_args()
    composed = open(a.composed, encoding="utf-8").read()
    out = validate(composed, a.text_mode, a.bubbles, a.refs, a.project_dir)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out["passes_all"] else 4)


if __name__ == "__main__":
    main()
