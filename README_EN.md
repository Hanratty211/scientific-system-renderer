# Scientific System Renderer

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Skill version](https://img.shields.io/badge/skill-v1.6.0-0b7285.svg)](manifest.yaml)
[中文说明](README.md)

An agent-operated skill for Codex, Claude Code, and other tool-using agents.
It turns photographs, manuals, methods papers, CAD, user annotations, and
physical constraints into an auditable truth model before creating or repairing
Blender/SVG system architectures, physical setups, component sheets, and
mechanism figures.

This is not a one-click beautifier. Its purpose is to prevent figures that look
plausible but contain invented devices, swapped ports, missing jumpers,
detached routes, impossible intersections, floating supports, or misleading
time states.

## Where It Helps

- optics, electronics, RF, fluidics, thermal, vacuum, mechanical, robotics,
  biomedical, laboratory, industrial, and hybrid systems;
- publication-grade 3D setups, architecture panels, component views, and
  mechanism insets;
- high-resolution transparent no-text masters plus editable SVG annotation;
- auditing or repairing Blender scenes with interface and physical-layout risk.

## Configuration Evidence and Delivery Review in v1.6.0

- Read cited supplementary setup views before claiming apparatus evidence is absent.
- Lock one specimen and operating configuration; manufacturer geometry does not prove experimental presence or wiring.
- Keep overview/detail geometry consistent and disclose removed windows, liquid or other inspection-only treatments.
- Check selected mating interfaces, restore the main view, and reopen the delivered scene after the last change.
- Deliver accessible source/render images and keep conditional user approval separate from scientific validation.

See [evidence](references/evidence-and-provenance.md),
[saved-scene and view-state checks](references/geometry-validation.md), and
[comparison delivery](references/visual-and-delivery.md). These additions are
agent workflow rules and original behavioral evaluation prompts, not a new
exhaustive collision checker. Papers, manufacturer materials and case renders
are not distributed with the skill.

## Visual Identity in v1.5.0

[Identity, scale and route clarity](references/identity-scale-and-route-clarity.md)
preserves handheld, body-worn, stacked and mechanically coupled assemblies.
It separates material classes, evidence-based instrument identity, true scale
from magnified details, and physical connections from explanatory graphics.
Topology checks cannot certify visual fidelity. Shared failures are repaired
through representative samples with explicit per-case pending status; a skill
update does not retroactively repair prior images.

## Scope Preservation in v1.4.1

A complete-system request must not be silently reduced to a component sheet or
disconnected equipment collection. Lock the boundary, excitation/input, core
apparatus, necessary controls, and output in a separate request contract before
modeling. Replace device-only paper cases or ask for missing evidence rather
than shrinking the task. Component models are assets, not system validations.

```bash
python3 scripts/validate_delivery_scope.py delivery_contract.json scene_manifest.json
python3 scripts/test_delivery_scope.py
```

This gate checks declared views, required nodes, relationship classes and paths.
It does not prove rendered visibility, port correctness or scientific evidence.
Every requested view is required; distinct parallel branches cannot share one
delivered connection. The scope suite has 20 passing tests, with 22 independently
constructed input probes also passing after fixes.

## New in v1.4

Coverage-aware PASS / FAIL / UNVERIFIED results, sampled finite-width geometry
checks including endpoint bodies, reflector checks, projected support review,
artifact SHA256 binding, explicit no-text contracts, installation checks and
executable Blender scene regressions. Sampling is not an exhaustive collision
proof; visual self-review and user acceptance remain separate. See
[Geometry validation](references/geometry-validation.md).

Unsupported NURBS, modifiers, multiple splines, variable radii, mesh proxies
and instances are not counted as completed route checks. The 21 original
Blender regressions test tool behavior, not acceptance of paper-based figures.

## Hard Gates

1. **Component existence is independently evidenced.** A device appears only
   when user-confirmed, source-visible, authoritatively supported, or explicitly
   schematic.
2. **Every visible port has an identity map.** Stable ID, face position,
   direction, medium, evidence, and confidence are required.
3. **There are no silent open ports.** Each port is `connected`,
   `intentionally-open`, or `outside-figure`; the latter two require a reason
   and evidence.
4. **Routes are checked in world and camera space.** Endpoints must seat on
   port anchors; ambiguous projected X-crossings and off-frame re-entry are
   flagged.
5. **User corrections invalidate dependent acceptance.** Truth data, geometry,
   routes, labels, captions, crops, and QA must be rebuilt together.

## Lessons Captured From Real Iteration

The workflow was hardened through an anonymized real-instrument rendering
exercise. No project assets are included. Reusable failures and defenses are:

| Failure | Root cause | Defense |
|---|---|---|
| Invented chassis or instrument | plausibility mistaken for presence | component-existence gate |
| Correct port count, wrong identity/order | no per-face map | schema 1.3 port evidence |
| Missing short jumper still accepted | unused port was only a warning | hard connection expectation |
| Component type guessed before asking | uncertainty did not block work | user-first escalation |
| Cable overshoot, re-entry, detached ends | routes drawn by appearance | corridors and endpoint anchors |
| 3D separation but 2D X-crossing | world-space checks only | camera-space audit |
| Small connector error missed | full-frame review only | deterministic detail crops |
| Old caption/QA survived a correction | change did not propagate | invalidation protocol |
| Transparent output misread | one preview background | white/dark/checkerboard QA |
| Labels repeatedly collided | annotation started too early | approve no-text master first |

## Workflow

```text
evidence intake
  -> component-existence lock
  -> per-face port map and port-to-port table
  -> scene_manifest.json
  -> storyboard / gray box
  -> script-built Blender scene
  -> endpoint, collision, support, and projection audit
  -> high-resolution transparent no-text render
  -> whole-frame and detail-crop QA
  -> editable SVG annotation
  -> delivery and public-release audit
```

The agent enters through [SKILL.md](SKILL.md) and loads only the route-specific
references listed in [manifest.yaml](manifest.yaml).

## Install

### Codex

```bash
git clone https://github.com/Hanratty211/scientific-system-renderer.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -s "$(pwd)/scientific-system-renderer" \
  "${CODEX_HOME:-$HOME/.codex}/skills/scientific-system-renderer"
```

Start a new task and describe the rendering request naturally, or invoke
`$scientific-system-renderer` explicitly.

### Claude Code and other agents

Point the agent to the repository's `SKILL.md`. Keep the complete checkout:
`manifest.yaml`, `static/`, `references/`, `scripts/`, and `assets/` are part of
the skill and should not be replaced by a copied prompt.

## Quick Start

```bash
python3 -m pip install -r requirements.txt

python3 scripts/init_render_project.py render-package \
  --title "Example system" --domain general \
  --views architecture,physical-setup,component-sheet

python3 scripts/validate_scene_manifest.py \
  render-package/scene_manifest.json \
  --report render-package/qa/manifest_validation.md
```

Audit a Blender scene and enforce endpoint anchors:

```bash
blender --background render-package/final/system.blend \
  --python scripts/audit_blender_scene.py -- \
  --output render-package/qa/blender_scene_audit.json \
  --strict-endpoints
```

Render and detail QA:

```bash
python3 scripts/render_qa.py render-package/final/system_no_text.png \
  --require-alpha --min-width 3000 \
  --contact-sheet render-package/qa/background_contact_sheet.png \
  --report render-package/qa/render_qa.md

python3 scripts/generate_detail_crops.py \
  render-package/final/system_no_text.png \
  render-package/qa/qa_regions.json \
  render-package/qa/crops \
  --contact-sheet render-package/qa/detail_contact_sheet.png \
  --report render-package/qa/detail_crops.md
```

## Validation

```bash
python3 scripts/run_synthetic_benchmark.py \
  --report /tmp/ssr_synthetic_benchmark.md
python3 scripts/audit_public_release.py .
python3 -m py_compile scripts/*.py assets/build_scene.template.py
```

The original synthetic benchmark covers optics, digital computing, wearable
and implantable systems, robotics, thermal-fluid systems, soft structures,
mechanics, and microfluidics. It validates rules, not a real project's hardware.

## Repository Layout

```text
SKILL.md                       agent entry and completion gate
manifest.yaml                 route-specific reference loading
static/core/                  always-on truth contract
references/                   evidence, interfaces, physics, Blender, visual QA
scripts/                      manifest, Blender, render, crop, release audits
assets/                       original templates and synthetic fixtures
evals/                        agent behavior examples
agents/                       integration metadata
```

## Open-Source and Privacy Boundary

This repository contains only original general instructions, code, templates,
and synthetic fixtures. It excludes user photographs and videos, paper PDFs or
figures, manufacturer imagery, project renders, `.blend` files, local logs,
private paths, account identifiers, credentials, and identifiable unpublished
connection maps. Run `audit_public_release.py` before publishing changes.

## Limitations

- AABB, endpoint, and projected-crossing checks are conservative candidates and
  do not replace visual review.
- General rules do not certify safety, regulatory compliance, or manufacturability.
- When evidence is missing, the skill blocks, asks, researches, or omits; it
  does not invent factual hardware details.

## License

[Apache License 2.0](LICENSE). User inputs and third-party references remain
subject to their original licenses and terms.
