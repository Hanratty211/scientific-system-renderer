# Evidence and Provenance

## Source hierarchy

Prefer sources in this order:

1. manufacturer CAD, dimensional drawing, datasheet, and manual;
2. standards, patents, or official application notes;
3. peer-reviewed methods figures and supplementary setup descriptions;
4. user-supplied laboratory photos and measurements;
5. distributor images that clearly identify the exact product;
6. generic images used only for style or device-class reference.

Do not infer port placement, transparency, internal behavior, or scale from a visually similar product when the exact device matters.

## Source ledger

Maintain `references/source_ledger.csv` with:

- `source_id`
- `component_id`
- `claim`
- `source_type`
- `title_or_model`
- `url_or_path`
- `publisher_or_manufacturer`
- `accessed_date`
- `license_or_usage_note`
- `confidence`
- `notes`

Use stable local paths for user-supplied files and direct URLs for web sources. Cite the exact page or figure when possible.

## Claim tracing

Trace these claims independently:

- component existence in the depicted setup;
- system topology;
- component function;
- reflective, transmissive, or boundary behavior;
- port type and direction;
- port order and face position;
- connected, intentionally open, or out-of-frame port state;
- dimensions and scale;
- active-area location;
- mounting interface;
- sequence or simultaneity;
- performance shown in labels or caption.

A source that proves function may not prove geometry. A product photo may prove geometry but not internal operation.

Use separate evidence fields for existence, function, geometry, and interface
identity. A wide setup photograph can prove that a chassis is present while a
front-panel close-up proves connector order. Neither one automatically proves
the hidden rear-panel topology.

## Use of reference images

- Learn visual grammar, camera angle, material treatment, and label density without copying artwork.
- Rebuild geometry from documented features.
- Use product photos as private modeling references or licensed textures when permitted.
- Do not paste an image into a 3D scene in a way that makes a detached plane look like a modeled device.
- Do not reproduce a paper figure's distinctive composition, labels, or artwork verbatim.
- Record whether a texture is original, generated, user-provided, or sourced.

## AI-generated content

Use generative images for generic style exploration, backgrounds, or non-critical textures only when appropriate. Do not use them as evidence of real hardware geometry, port placement, or physical connectivity. Verify every factual visual detail independently.

Treat a journal figure as evidence only for the claims it actually supports. A system schematic can establish topology or operating sequence, while a device photograph can support silhouette and relative placement; neither automatically supplies connector geometry, hidden internals, exact dimensions, or a reusable art license. Rebuild the scene from facts and independent geometry rather than tracing or redistributing the figure.

The built-in regression fixtures are original synthetic test definitions. They are not evidence for a user project and must never be cited as support for a real component, topology, or physical claim.

## Parameter and Texture Evidence

Before repeating geometry or fixing proportions, extract a short parameter
ledger from the caption and relevant methods: semantic unit count, pitch,
diameter, thickness, gap, active area and operating state. Record each value's
source location and whether it is measured, specified, visually estimated or
intentionally schematic. A visible strip, chamber wall or repeated surface mark
is not necessarily one functional unit. Do not choose an attractive array count
when the paper specifies the count elsewhere.

Use real cavities, contacts and supports for structural features. Use material
roughness for unresolved surface texture; decorative perforations or repeated
cells must not masquerade as measured microstructure. If a fine detail cannot be
resolved, omit it or disclose a representative display density without claiming
it as the actual count. Never combine alternative connection states into one
physical object.

For a paper evaluation, pair each render with the exact source panel, confirmed
facts, omitted unknowns and audit scope. A component-only study cannot validate
the omitted bench connections. Report those zero-coverage areas prominently;
do not aggregate scoped passes into a claim of complete system reconstruction.
Reference retrieval must identify figure numbers/IDs explicitly: article pages
may mix tables with figures, so list position is not a reliable figure number.

## Detail Confidence

Classify important details as:

- `verified`: directly supported by authoritative evidence;
- `inferred`: derived from multiple compatible sources;
- `schematic`: intentionally simplified and not dimensionally literal;
- `unknown`: missing evidence and potentially blocking.

Put unresolved assumptions in `scene_manifest.json` and the caption/QA notes. Never let an unverified detail silently appear photorealistic and authoritative.

## Mandatory uncertainty escalation

When a factual property is unsupported, do not select a plausible value on the
user's behalf. Add a blocking `open_questions` entry and ask the user with the
smallest useful visual context. If the user cannot answer, search in this
priority order: exact manufacturer documentation, primary research describing
the same setup, applicable standards or patents, then multiple independent
high-quality secondary sources. Record supporting and conflicting sources.

Only four resolutions permit the affected detail to enter a deliverable:

- `user-confirmed`: the user directly identifies or approves the fact;
- `authoritative-source`: a cited primary/manual/standard source resolves it;
- `intentionally-omitted`: the uncertain detail is removed from the view;
- `schematic-placeholder`: it is visibly non-literal and labeled unresolved.

Visual similarity, convention, prior generated artwork, or agent preference are
not valid resolutions. If sources conflict, return to the user with the
conflict instead of choosing one silently.
