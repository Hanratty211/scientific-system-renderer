# Synthetic Self-Test

The validator regression suite uses original, compact system definitions stored
in `assets/synthetic_benchmark.json`. The fixtures contain no external paper
text, artwork, figure metadata, DOI, publisher URL, or copied composition.

## Purpose

The suite checks that a valid truth model passes and that a deliberately
injected, materially misleading failure is detected. It currently exercises:

- optical boundary behavior;
- multiscale assembly hierarchy;
- logical versus physical connections;
- anatomical contact classification;
- wireless field representation;
- mobile and deformable motion envelopes;
- ordered hardware states;
- open driven routes;
- closed transport loops;
- linked microstructure views.

Run:

```bash
python3 scripts/run_synthetic_benchmark.py \
  --report /tmp/ssr_synthetic_benchmark.md \
  --json /tmp/ssr_synthetic_benchmark.json
```

## Limits

A passing fixture confirms validator behavior only. It does not prove that a
Blender scene is physically correct, visually clear, dimensionally faithful,
or supported by adequate project evidence. Every completed render still needs
source tracing, scene audit, whole-frame inspection, and critical-junction
crops.

When adding a new domain, define an original synthetic case and one deliberate
failure that would materially mislead a reader. Do not add publisher figures,
screenshots, paper-specific prose, or bibliographic corpora to this repository.
