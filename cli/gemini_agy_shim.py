#!/usr/bin/env python3
"""gemini_agy_shim.py — legacy `gemini` CLI interface → Antigravity `agy` (the google-family reviewer seam).

The legacy Gemini CLI is dead upstream (IneligibleTierError — Gemini Code Assist for individuals deprecated;
Google's migration target is Antigravity). This shim keeps every engine invocation of the form
`gemini [--model <name>] -p "@/abs/file.png ... <prompt>"` working (run_comic.py / run_spiral.py reviewer
seams, via --gemini-cmd) by translating it to Antigravity's non-interactive `agy -p ... --sandbox`.

Translation: leading @-prefixed tokens that name existing files become a numbered open-these-first preamble
plus one `--add-dir <parent>` grant per distinct directory (agy reads files — images as pixels — only when
instructed AND granted access). Response text passes through on stdout, untouched; exit code passes through.

FAMILY PIN — do not weaken: this slot must stay a GEMINI (google-family) model. Antigravity also serves
Claude and GPT-OSS models; routing this reviewer there would silently corrupt cross-model quorum provenance
(the "google" slot would score with an anthropic/openai model). The caller's --model value is therefore
noted-and-ignored; the pin is GEMINI_SHIM_MODEL (default "Gemini 3.1 Pro (High)") and must only ever be
overridden with another Gemini model. Print timeout: GEMINI_SHIM_PRINT_TIMEOUT (default "8m").

    python3 cli/gemini_agy_shim.py --model auto-gemini-3 -p "@/abs/panel.png Review this panel ..."
"""
import os, shutil, subprocess, sys

PIN = os.environ.get("GEMINI_SHIM_MODEL", "Gemini 3.1 Pro (High)")
TIMEOUT = os.environ.get("GEMINI_SHIM_PRINT_TIMEOUT", "8m")

PREAMBLE = ("This is a pure-analysis review task. First OPEN and inspect these files in order "
            "(they correspond to the image #N / file references below; images must be viewed as pixels):\n"
            "{listing}\n"
            "Then follow the instructions below exactly — do not perform any other action and do not "
            "modify any file.\n\n{body}")


def parse_prompt(args):
    """Legacy interface: [--model <ignored>] -p|--prompt|--print "<prompt>" (or bare positional)."""
    prompt = None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-p", "--prompt", "--print") and i + 1 < len(args):
            return args[i + 1]
        if a == "--model":
            i += 2; continue          # requested model noted-and-ignored: family pin wins (see docstring)
        if a.startswith("--model="):
            i += 1; continue
        if prompt is None and not a.startswith("-"):
            prompt = a  # bare-positional fallback
        i += 1
    return prompt


def split_attachments(prompt):
    """Peel leading @/abs/path attachment tokens (legacy CLI syntax). A leading @token counts as a file
    ONLY if it exists on disk; scanning stops at the first token that is not an existing @file."""
    toks = prompt.split(" ")
    files = []
    for t in toks:
        if t.startswith("@") and os.path.exists(t[1:]):
            files.append(os.path.abspath(t[1:]))
        else:
            break
    return files, " ".join(toks[len(files):]).strip()


def main():
    prompt = parse_prompt(sys.argv[1:])
    if not prompt:
        sys.stderr.write('gemini_agy_shim: no prompt given (expected -p/--prompt/--print "<prompt>")\n')
        return 2
    if not shutil.which("agy"):
        sys.stderr.write("gemini_agy_shim: Antigravity CLI (agy) not found — install + login "
                         "(https://antigravity.google) or point --gemini-cmd at your own google-family CLI\n")
        return 2

    files, body = split_attachments(prompt)
    if files:
        listing = "\n".join(f"  {n}. {p}" for n, p in enumerate(files, 1))
        body = PREAMBLE.format(listing=listing, body=body)

    cmd = ["agy", "-p", body, "--model", PIN, "--sandbox", "--print-timeout", TIMEOUT]
    dirs = []
    for p in files:
        d = os.path.dirname(p)
        if d not in dirs:
            dirs.append(d); cmd += ["--add-dir", d]  # repeatable grant — without it agy's sandbox can't open the file
    r = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(r.stdout or "")
    sys.stderr.write(r.stderr or "")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
