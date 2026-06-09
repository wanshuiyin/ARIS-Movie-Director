# Artifact Pipeline (assets · refs · SVG-bake · retry)

> TODO: extract + generalize from `architecture.md` §4-5.
THE CORE TECHNIQUE: deterministic-content SVG → render PNG → codex image_gen with ≤2 -i refs
(content-authority + identity-lock) → narrative panel (bake evidence + dialogue). Accuracy
discipline: human/gate-verify must-match fields (numbers, JSON keys, fn names, verdict tokens).
Generator-adapter contract: {refs, prompt, panel_id} → {status, image_path, failure_reason, metadata}.
