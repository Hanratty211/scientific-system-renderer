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

- system topology;
- component function;
- reflective, transmissive, or boundary behavior;
- port type and direction;
- dimensions and scale;
- active-area location;
- mounting interface;
- sequence or simultaneity;
- performance shown in labels or caption.

A source that proves function may not prove geometry. A product photo may prove geometry but not internal operation.

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

## Uncertainty

Classify important details as:

- `verified`: directly supported by authoritative evidence;
- `inferred`: derived from multiple compatible sources;
- `schematic`: intentionally simplified and not dimensionally literal;
- `unknown`: missing evidence and potentially blocking.

Put unresolved assumptions in `scene_manifest.json` and the caption/QA notes. Never let an unverified detail silently appear photorealistic and authoritative.
