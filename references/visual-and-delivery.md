# Visual Design and Delivery

## Composition

- Lead the eye from source to processing to output.
- Keep one primary physical path per setup view.
- Place abstract sequencing, multiplexing, equations, and classifier logic in separate insets or panels.
- Use shallow isometric, orthographic, or controlled perspective views for technical clarity.
- Leave visible spacing between repeated mounts and devices.
- Keep the system inside the frame with a stable margin; do not crop the source or sink.

## Color grammar

Assign color by meaning, not decoration:

| Meaning | Suggested treatment |
|---|---|
| physical hardware | neutral gray, black, brushed metal |
| transparent optics | pale cyan/gray glass |
| optical or energy path | one saturated wavelength or restrained glow |
| electrical/data path | warm orange or blue line family |
| fluid/sample path | medium-specific color with arrows |
| active/sensor region | controlled accent distinct from the path |
| uncertainty or schematic-only detail | muted gray or dashed outline |

Do not use multiple translucent layers to represent one physical path unless each layer has a documented meaning.

## Labels

- Use short device names near the object.
- Keep text horizontal unless the publication style strongly requires otherwise.
- Avoid labels over beams, active faces, textured regions, and transparent optics.
- Prefer proximity over leader lines. If a leader is necessary, use one short line with a clear endpoint.
- Do not surround every label with a box.
- Keep identical label grammar for equivalent components.
- Use SVG `<text>` or editor-native text, not rasterized labels.
- Verify labels on white, transparent, and slide backgrounds.

## Architecture and mechanism panels

- Use vector modules, arrows, matrices, timelines, and equations for abstract logic.
- Do not draw multiple physical devices when the system reuses one device over time.
- Use a filmstrip, clock, frame stack, or explicit time arrow for sequential states.
- Keep physical setup and neural-network analogy visually related but spatially separate.
- Do not present a schematic response as measured data. Label it `schematic`, `simulation`, or `representative` as appropriate.

## Component sheets

- Use front, side, top, or isometric views that expose ports and active areas.
- Include scale bars or dimensions only when supported by data.
- Use callouts for connector names, active areas, and mounting points.
- Avoid copying manufacturer marketing compositions; rebuild the view from documented geometry.

## Export set

Default deliverables:

- `.blend`: editable 3D scene;
- `.py`: reproducible scene generator;
- `_no_text.png`: high-resolution RGBA master;
- `_annotated.svg`: editable labels and arrows over the render;
- `_annotated.png`: visual preview;
- `scene_manifest.json`: physical truth model;
- `source_ledger.csv`: evidence and license notes;
- `qa_log.md`: actual iteration record.

Optional:

- PDF for manuscript placement;
- TIFF at journal-required DPI;
- separate transparent device cutouts;
- CAD or GLB export when downstream 3D editing is requested;
- contact sheet and junction crops for review.
- a deterministic crop index covering every port cluster, endpoint, support contact, branch, and dense route crossing.

## Resolution and typography

- Render 3000 px wide minimum for normal paper use.
- Render 5000 px wide or greater for large crops or slide zoom.
- Test the figure at final manuscript width rather than only at full monitor size.
- Use one sans-serif family and a compact size hierarchy.
- Keep label strokes and arrowheads visible after downsampling.

## File organization

```text
render-package/
  final/
  engineering/
  intermediate/
  references/
  qa/
  scene_manifest.json
  WORKLOG.md
```

Keep only approved deliverables in `final/`. Put rejected renders, screenshots, temporary textures, and experiments in `intermediate/`. Preserve provenance without making the delivery folder difficult to find.
