---
name: scientific-system-renderer
description: >-
  Research, design, model, render, and validate evidence-grounded scientific
  system figures. Use for 3D architecture overviews, real equipment connection
  diagrams, component or device sheets, mechanism insets, and hybrid Blender
  plus editable SVG figures across optics, electronics, robotics, fluidics,
  vacuum, thermal, RF, biomedical, laboratory, mechanical, and industrial
  systems. Also use to audit or repair impossible paths, wrong ports or
  orientations, collisions, floating supports, misleading scale, temporal
  states shown as simultaneous hardware, or ambiguous labels.
metadata:
  version: "1.1.0"
  author: "Community contribution"
---

# Scientific System Renderer - Router

This is an agent-operated workflow, not a standalone renderer. The agent reads
the truth contract, selects the smallest applicable route, uses the included
scripts and templates, and visually inspects every serious render before
delivery.

## Routing protocol

### 1. Load the core contract

Read [manifest.yaml](manifest.yaml), then read every file listed under
`always_load`. These files define the non-negotiable physical, evidence, QA,
and delivery constraints.

### 2. Select the deliverable route

Choose one primary route from the manifest:

- `architecture_overview`: functional modules and major flows;
- `physical_setup`: real devices, interfaces, mounts, and spatial paths;
- `component_sheet`: a device, its active areas, ports, and mounting interfaces;
- `mechanism_inset`: internal stages, sequencing, multiplexing, or state change;
- `hybrid_figure`: approved no-text 3D base plus editable vector annotation;
- `audit_repair`: inspect and correct an existing scene or figure.

Use more than one route only when the requested deliverables genuinely require
separate views. Do not overload a physical setup with logical architecture,
temporal states, and dense explanatory prose.

### 3. Read project governance and evidence

Inspect repository instructions, task logs, output conventions, and Git status.
Build a source ledger from user-provided files and authoritative sources. Treat
reference figures as evidence, not reusable artwork. Never infer hidden ports,
transparency, exact scale, or internal behavior from visual resemblance alone.

Read [evidence-and-provenance.md](references/evidence-and-provenance.md) when
copyright, product fidelity, citations, or source tracing matters.

### 4. Initialize and validate the truth model

For a new package, run:

```bash
python3 "$SKILL_DIR/scripts/init_render_project.py" OUTPUT_DIR \
  --title "System title" --domain general \
  --views architecture,physical-setup,component-sheet
```

Complete `scene_manifest.json` before detailed modeling. Declare components,
ports, active faces, opacity, capabilities, scale, parent assemblies, supports,
states, contacts, routes, loops, motions, and evidence. Model each relationship
as physical, field, logical, temporal, contact, containment, or motion envelope.

Validate it:

```bash
python3 "$SKILL_DIR/scripts/validate_scene_manifest.py" scene_manifest.json \
  --report qa/manifest_validation.md
```

Do not proceed while errors remain. When changing the skill or entering a new
domain, run the original synthetic regression suite:

```bash
python3 "$SKILL_DIR/scripts/run_synthetic_benchmark.py" \
  --report /tmp/ssr_synthetic_benchmark.md
```

### 5. Lock topology before detail

Create a simple 2D engineering storyboard or gray-box scene. Confirm source to
sink order, port directions, branch-causing components, path width changes,
supports, clearances, state reuse, and camera visibility. Every bend, split,
merge, conversion, focus, resize, or switch must have a physical cause.

Load [physical-plausibility.md](references/physical-plausibility.md) for
domain-specific rules. For optical benches, also load
[optical-bench-failure-patterns.md](references/optical-bench-failure-patterns.md).

### 6. Build script-first

Prefer a reproducible Blender Python scene. Keep geometry constructors,
materials, coordinates, paths, camera, lighting, and exports in code. Use the
Blender UI for inspection and refinement when useful. Load
[blender-patterns.md](references/blender-patterns.md) before modeling.

Where practical, assign these object properties:

- component: `ssr_role=component`, `ssr_component_id`, `ssr_opacity`;
- connection: `ssr_role=connection`, `ssr_source`, `ssr_target`, `ssr_medium`;
- support: `ssr_role=support`, `ssr_supports`;
- annotation: `ssr_role=annotation`.

### 7. Audit, render, and inspect

Audit a saved scene:

```bash
blender --background final/system.blend \
  --python "$SKILL_DIR/scripts/audit_blender_scene.py" -- \
  --output qa/blender_scene_audit.json
```

Render a transparent no-text master and inspect it on a neutral white
composite. Run numeric and crop QA:

```bash
python3 "$SKILL_DIR/scripts/render_qa.py" final/system.png \
  --require-alpha --min-width 3000 \
  --contact-sheet qa/system_contact_sheet.png \
  --report qa/render_qa.md
```

Inspect the whole frame and close crops of every junction, port cluster,
support, reflector, branch device, and endpoint. Record at least one rejected
round and one corrected round for a complex figure. Never pre-write acceptance.

### 8. Annotate and package

Add labels only after geometry and paths pass QA. Keep text horizontal,
editable, concise, and directly associated with its target. Use an SVG overlay
for labels, arrows, equations, and compact mechanism panels. Load
[visual-and-delivery.md](references/visual-and-delivery.md) before export.

The default complete package is:

```text
final/
  system.blend
  system_no_text.png
  system_annotated.svg
  system_annotated.png
engineering/
  build_scene.py
scene_manifest.json
references/source_ledger.csv
qa/qa_log.md
WORKLOG.md
```

Keep drafts and crops in `intermediate/`. State which details are measured,
sourced, inferred, schematic, generated, or unresolved.

## On-demand references

Use the `references.on_demand` table in [manifest.yaml](manifest.yaml). Open only
the files needed for the selected route and domain. The synthetic fixtures are
validator tests, not visual templates and not evidence for a user project.

## Completion gate

Do not call a complex figure complete unless:

- every path starts and ends at a declared interface;
- every turn, branch, merge, conversion, and width change has a valid cause;
- no path crosses opaque or unrelated geometry;
- active areas are attached to the correct housing face;
- elevated parts contact plausible, collision-free supports;
- temporal states are not misrepresented as simultaneous hardware;
- fields, logical links, contact, transport paths, and motion envelopes use
  distinct visual grammars;
- the no-text render passes whole-frame and close-crop inspection;
- labels remain editable and unambiguous;
- sources, assumptions, QA rounds, regeneration commands, and outputs are
  recorded.
