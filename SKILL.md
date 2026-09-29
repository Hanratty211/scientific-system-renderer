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
Extract caption/method parameters before choosing repeated unit counts, gaps or
active-area dimensions. Distinguish structural geometry from illustrative
surface texture; keep source values separate from visual estimates.

Read [evidence-and-provenance.md](references/evidence-and-provenance.md) when
copyright, product fidelity, citations, or source tracing matters.

Before geometry, lock two inventories:

- component existence: every shown device must be user-confirmed, visible in a
  supplied source, supported by an authoritative source, or visibly schematic;
- interface identity: every shown port needs a stable ID, face position,
  direction, medium, evidence, and expected connection state.

An overview photograph can establish context but does not override a close-up
for port order or connector identity. Read
[interface-and-route-qa.md](references/interface-and-route-qa.md) for physical
setups and repair tasks.

### 4. Resolve uncertainty before modeling

Treat every uncertain factual detail as blocked, not as permission to
improvise. This includes component identity, scale, port meaning, direction,
hidden topology, material behavior, support, route, termination, and operating
state. Use this order without skipping steps:

1. Record the uncertainty in `open_questions` and stop modeling the affected
   detail.
2. Ask the user one concise, concrete question, preferably with a crop or two
   clearly distinguished alternatives.
3. If the user cannot confirm it, search primary literature, manufacturer
   manuals/datasheets, standards, patents, or other authoritative sources and
   record the citation in the source ledger.
4. If authoritative evidence still does not resolve it, omit the detail or use
   a visibly schematic placeholder labeled `unresolved`. Never silently choose
   the most plausible-looking option.

User confirmation outranks visual guesswork. A similar product photograph,
common practice, prior generated image, or aesthetic preference is not enough
to resolve a factual unknown. Pure styling choices may use neutral defaults
only when they do not imply a scientific or hardware fact.

### 5. Initialize and validate the truth model

Lock a delivery contract first: requested views, annotation mode, background,
pixel dimensions, editable formats, simplification permission and revision
scope. A no-text request excludes annotation generation. Separate inherited
geometry from newly verified geometry; a local repair is not full-system approval.

For a new package, run:

```bash
python3 "$SKILL_DIR/scripts/init_render_project.py" OUTPUT_DIR \
  --title "System title" --domain general \
  --views physical-setup --annotations none
```

Complete `scene_manifest.json` before detailed modeling. Declare components,
ports, active faces, opacity, capabilities, scale, parent assemblies, supports,
states, contacts, routes, loops, motions, and evidence. Model each relationship
as physical, field, logical, temporal, contact, containment, or motion envelope.
Schema `1.3` also requires component-existence evidence and an explicit
`connection_expectation` for every port. A port expected to be connected is a
validation error when unused. An intentionally open or out-of-frame port needs
a reason and evidence.

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

### 6. Lock topology before detail

Create a simple 2D engineering storyboard or gray-box scene. Confirm source to
sink order, port directions, branch-causing components, path width changes,
supports, clearances, state reuse, and camera visibility. Every bend, split,
merge, conversion, focus, resize, or switch must have a physical cause.

Freeze a port-to-port table before cable, tube, beam, or fiber routing. Never
route to a housing center when the destination is a connector. Never infer a
hidden jumper or termination from convention.

Load [physical-plausibility.md](references/physical-plausibility.md) for
domain-specific rules. For optical benches, also load
[optical-bench-failure-patterns.md](references/optical-bench-failure-patterns.md).

### 7. Build script-first

Prefer a reproducible Blender Python scene. Keep geometry constructors,
materials, coordinates, paths, camera, lighting, and exports in code. Use the
Blender UI for inspection and refinement when useful. Load
[blender-patterns.md](references/blender-patterns.md) before modeling.

Where practical, assign these object properties:

- component: `ssr_role=component`, `ssr_component_id`, `ssr_opacity`;
- connection: `ssr_role=connection`, `ssr_source`, `ssr_target`, `ssr_medium`;
- support: `ssr_role=support`, `ssr_supports`;
- annotation: `ssr_role=annotation`.

Represent each physical port as an interface anchor tagged with
`ssr_attached_to` and `ssr_port_id`. Give each route auditable
`ssr_start_anchor` and `ssr_end_anchor` coordinates or build it as a curve whose
endpoints coincide with the anchors.

### 8. Audit, render, and inspect

Audit a saved scene:

```bash
blender --background final/system.blend \
  --python "$SKILL_DIR/scripts/audit_blender_scene.py" -- \
  --output qa/blender_scene_audit.json --strict-endpoints
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
support, reflector, branch device, and endpoint. Record actual findings and
corrections; a genuine first-pass success is allowed. Never manufacture a
rejected round or pre-write acceptance. Keep agent self-review separate from
user acceptance.

Check part-to-part fit and material character separately from route audits.
Connection-free views can still contain intersecting packages, detached joints
or a soft material rendered as rigid hardware; record these as visual findings.

The scene audit returns PASS, FAIL or UNVERIFIED with coverage counts. Zero
audited components or missing route data cannot pass. Component-only views may
use `--scope component-sheet`; physical setups must not use that option to hide
missing routes. Use `--no-text` when requested. See
[geometry-validation.md](references/geometry-validation.md) for radius, contact
and reflection metadata, limitations and executable scene regressions.

Generate deterministic crops from normalized review regions:

```bash
python3 "$SKILL_DIR/scripts/generate_detail_crops.py" \
  final/system_no_text.png qa/qa_regions.json qa/crops \
  --contact-sheet qa/detail_contact_sheet.png --report qa/detail_crops.md
```

Three-dimensional separation does not excuse an ambiguous X-crossing in the
final camera projection. Move the route or camera, or show a documented bridge
or junction.

### 9. Annotate and package

Only generate annotations when the delivery contract requests them.
Add labels after geometry and paths pass QA. Keep text horizontal,
editable, concise, and directly associated with its target. Use an SVG overlay
for labels, arrows, equations, and compact mechanism panels. Load
[visual-and-delivery.md](references/visual-and-delivery.md) before export.

An annotated package can contain the following; omit annotation files for a
no-text contract:

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
- every shown component has explicit existence evidence;
- every port has a verified or explicitly schematic identity and an evidenced
  connected/open/out-of-frame state;
- every factual uncertainty was user-confirmed, authoritatively resolved,
  intentionally omitted, or explicitly left as an unresolved schematic;
- every turn, branch, merge, conversion, and width change has a valid cause;
- no path crosses opaque or unrelated geometry;
- active areas are attached to the correct housing face;
- elevated parts contact plausible, collision-free supports;
- temporal states are not misrepresented as simultaneous hardware;
- fields, logical links, contact, transport paths, and motion envelopes use
  distinct visual grammars;
- the no-text render passes whole-frame and close-crop inspection;
- labels, when requested, remain editable and unambiguous;
- sources, assumptions, QA rounds, regeneration commands, and outputs are
  recorded.

Any user correction to component identity, port order, topology, or operating
state invalidates prior acceptance for all dependent geometry, routes, labels,
captions, and QA. Update the manifest first, rebuild downstream artifacts, and
record the new review evidence.
