# Evidence-to-Render Workflow

## Contents

1. Deliverable contract
2. Stage gates
3. Iteration protocol
4. Completion criteria

## 1. Deliverable contract

Define the figure before opening Blender:

| Field | Required decision |
|---|---|
| Audience | paper, slide, proposal, manual, patent, outreach |
| Figure role | architecture, physical setup, component sheet, mechanism, hybrid |
| Truth level | dimensionally faithful, topology faithful, or explicitly schematic |
| Views | one overview plus any required detail/inset views |
| Outputs | `.blend`, no-text PNG, annotated SVG/PNG, optional PDF/TIFF |
| Editability | which elements must remain editable |
| Evidence | supplied files, authoritative web sources, measured dimensions |
| Governance | task log, naming, git, citation, and folder rules |

Split incompatible goals. A realistic physical setup and an abstract network analogy normally belong in separate panels.

## 2. Stage gates

### Gate 0: source intake and component-existence lock

- Inventory papers, screenshots, product photos, manuals, CAD, and prior figures.
- Create a component-existence table before modeling. Record whether each shown
  device is user-confirmed, directly source-visible, authoritatively supported,
  or a visibly schematic placeholder.
- Identify the user's approved reference and the aspect to learn from it: topology, product form, camera angle, material, or label style.
- Do not treat a decorative render as proof of physical behavior.

Pass when every essential component has at least one source and no unexplained
device, chassis, adapter, support, or instrument remains in the storyboard. A factual unknown
cannot pass as a self-declared assumption: record it, ask the user first, and
search authoritative sources only if the user cannot confirm it. If it remains
unresolved, omit it or reserve it for an explicitly unresolved schematic inset.

### Gate 1: evidence and per-face interface matrix

For each component record:

- role in the system;
- body shape and approximate dimensions;
- active face or functional region;
- ports and local coordinate directions;
- opacity or boundary behavior;
- mount and support;
- connection capabilities;
- evidence source and confidence.

For each port also record:

- stable port ID and visible face position such as row/column or upper/lower;
- connector class, direction, and accepted medium;
- identity evidence and confidence;
- expected state: connected, intentionally open, or outside the figure;
- reason and evidence for any intentionally open or out-of-frame state.

Pass when the information needed to orient and connect every component is explicit. Port count without identity and position is insufficient.

### Gate 2: topology manifest

Represent the system as components and directed edges. Use explicit intermediate components for splitters, valves, mirrors, hubs, manifolds, converters, and junctions. Never hide behavior inside an arbitrary bend in a drawn path.

For mixed-domain systems, also declare:

- component scale, parent assembly, mobility, states, and medium-specific boundary behavior;
- whether each relationship is physical, field, logical, temporal, contact, containment, or a motion envelope;
- anatomical, thermal, mechanical, adhesive, sterile, electrical, or optical contact class;
- ordered hardware-reuse sequences, open transport routes, closed loops, and robot/deformation envelopes.

Freeze a separate port-to-port table. Every row must identify source component
and port, target component and port, medium, route class, and evidence. Pass
`validate_scene_manifest.py` with no errors. Schema 1.3 treats silently missing
expected connections as errors.

When changing the skill or validator itself, run the original synthetic regression suite:

```bash
python3 scripts/run_synthetic_benchmark.py --report /tmp/ssr_synthetic_benchmark.md
```

Read [synthetic-self-test.md](synthetic-self-test.md) for coverage and known limits.

### Gate 3: engineering storyboard

Draw a simple top or isometric plan with named ports and local path directions. Check:

- source-to-sink order;
- valid bends and branches;
- enough spacing for mounts and labels;
- no path crossing through a housing;
- critical junctions visible from the proposed camera.

Pass when the topology can be explained without relying on the 3D model.

### Gate 4: gray-box scene

Model only bounding boxes, active faces, ports, supports, and connections. Use flat materials. Do not spend time on product details yet.

Pass when a screenshot confirms topology, orientation, scale class, support contact, and camera framing.

### Gate 5: component fidelity

Refine silhouettes, lenses, ports, connectors, knobs, flanges, active areas, and materials from references. Keep dimensions parameterized. Use textures only where they improve fidelity and do not conceal geometry errors.

Pass when close crops resemble the reference device class and all functional faces remain visible.

### Gate 6: path fidelity

Model connections from port to port. Encode thickness or aperture changes at physical causes. Use a single visual envelope unless core and halo convey different documented quantities.

Pass when every segment is continuous, correctly oriented, seated on both port
anchors, and collision-free in endpoint and junction crops. Inspect the entire
route for off-frame detours, Bezier overshoot, fascia crossings, and re-entry.
Also inspect final camera projection: depth separation alone does not make a
screen-space X-crossing unambiguous.

### Gate 7: lighting and final camera

Use broad neutral lights, restrained reflections, and an orthographic or long-focal-length camera. Keep critical connections from being hidden behind components. Prefer transparent output plus white-background inspection.

Pass when the whole figure reads at manuscript width and slide width.

### Gate 8: annotation and packaging

Add editable labels only after the base render is accepted. Generate the caption, source ledger, QA record, and regeneration command. Separate final, engineering, intermediate, references, and QA files.

Pass when another agent can reproduce the render and understand which details are sourced or schematic.

## 3. Iteration protocol

For every visual round:

1. Render the whole frame.
2. Generate white, dark, and checkerboard composites when alpha is present.
3. Inspect the whole image and crops around every path junction and dense component cluster.
4. Inspect every declared port group, each connection endpoint, each support contact, and the complete path corridor at native resolution.
5. Record the agent's scoped result (`pass`, `fail` or `unverified`) separately
   from user status (`pending`, `rejected`, `conditionally-usable` or `accepted`).
   Preserve any qualified user wording; “looks better” alone is not a full pass.
6. List observable defects, not intentions.
7. Map each defect to a script or scene change.
8. Re-render from the reproducible source.

Treat user annotations and screenshots as high-value test cases. Translate each complaint into a reusable invariant. Examples:

- “The beam passes through the mirror” becomes “a connection may terminate on an opaque reflective face but may not continue through its body.”
- “The support is detached” becomes “every supported component must contact its mount at the modeled attachment interface.”
- “The label points at the wrong item” becomes “a label must be nearest to its target or use one unambiguous short leader.”
- “That instrument does not exist” becomes “component existence needs its own evidence field and blocks detailed modeling.”
- “These two ports are not connected” becomes “every expected connection is a hard validation requirement, not a generic warning.”

When a user correction changes a device, port, route, or state, revoke prior
acceptance for all dependent artifacts. Update the manifest first, rebuild the
scene and overlays, regenerate crops, and append a new QA round.

## 4. Completion criteria

A complex render is complete only when:

- evidence and assumptions are recorded;
- the manifest validates;
- the `.blend` scene and generation script are saved;
- the no-text high-resolution master exists;
- at least two real QA rounds are documented;
- critical path and support crops pass visual inspection;
- labels remain editable;
- final and intermediate files are separated;
- repository logging and git requirements are satisfied when applicable.
