# Blender Patterns for Scientific System Renders

## Scene organization

Use real-world units and one documented coordinate system. Create collections such as:

- `COMPONENTS`
- `CONNECTIONS`
- `INTERFACES`
- `MOTION_ENVELOPES`
- `SUPPORTS`
- `TABLE_OR_ENVIRONMENT`
- `LIGHTS`
- `CAMERAS`
- `ANNOTATION_GUIDES`

Keep coordinates, dimensions, component constructors, connection routes, camera, lighting, and export settings in a Python build script. Save the generated `.blend` after every reproducible render.

Tag objects with `ssr_*` custom properties so the audit script can reason about them. Use one stable `ssr_component_id` across the manifest, object names, labels, and source ledger.

## Geometry

- Start with bounding boxes and active planes before product detail.
- Parameterize body dimensions, active area, port positions, support height, and local orientation.
- Represent ports as empties or small hidden guide objects parented to the component.
- Generate tubes, cables, beams, and arrows between port coordinates rather than eye-aligning them.
- Use straight segments, Bezier curves, elbows, or spline guides according to the real medium.
- Preserve a visible gap between unrelated objects. Use small intentional contact only at mounts, fittings, and interfaces.
- Build supports from the base upward. Compute post height from the component attachment point instead of assigning it independently.
- Use device photos as modeling references or textures on appropriate faces, never as detached cards pasted in front of geometry.

## Connections

For each connection object assign:

```python
obj["ssr_role"] = "connection"
obj["ssr_source"] = "source_component:port"
obj["ssr_target"] = "target_component:port"
obj["ssr_medium"] = "optical"
obj["ssr_representation"] = "physical"
```

For component assemblies and special visual objects, use:

```python
component["ssr_scale_level"] = "device"
child["ssr_parent"] = "parent_component_id"
child["ssr_assembly_relation"] = "laminated"
interface["ssr_role"] = "interface"
interface["ssr_attached_to"] = "component_id"
envelope["ssr_role"] = "motion-envelope"
envelope["ssr_envelope_for"] = "moving_component_id"
```

Keep logical and temporal arrows in the vector overlay. If field coupling must be rendered in 3D, tag it as `ssr_representation=field`, use a visibly non-cable grammar, and exclude it from physical tube collision assumptions.

For a connection that changes width, define a sequence of stations `(position, radius, cause_component)`. Keep a constant radius between stations. Put every change at a lens, reducer, nozzle, aperture, taper, or other explicit cause.

For a reflector, compute orientation from incoming and outgoing vectors. For a transmissive plane, orient its normal to the local path. Check the visible active side separately from the body orientation.

## Materials

- Use neutral matte or brushed materials for housings and supports.
- Use transparent glass with restrained roughness and a visible polished edge so lenses read as lenses.
- Use emission sparingly for light, screens, detector cells, or status indicators.
- Keep connection colors saturated enough to survive transparency and white backgrounds.
- Avoid dark world backgrounds for paper figures unless the user explicitly needs them.
- Prefer a transparent film render and inspect it composited on white, gray, and dark backgrounds.

## Camera and composition

- Use orthographic or a long focal length for technical overviews to reduce perspective distortion.
- Keep the full source-to-sink path in frame.
- Expose every critical bend and branch; move the camera or route, not the laws of physics.
- Leave quiet space near devices for later labels.
- Avoid placing dense component clusters along the same screen-space line.
- Render detail crops from additional cameras when junctions are difficult to judge.

## Lighting

- Use one large soft key and one weaker fill as a stable starting point.
- Keep shadows soft enough to read mounts and contact points.
- Add rim or area lights only when they reveal transparent optics or dark silhouettes.
- Do not let lighting make transparent components look opaque or hide the active face.

## Rendering

- Use Cycles for final material realism; use Eevee or low-sample Cycles for iteration.
- Enable denoising for final renders.
- Render the no-text master at 3000 px width or greater; use 5000 px or more when cropping is expected.
- Use RGBA PNG for the transparent master.
- Save a white-background inspection image separately.
- Keep labels outside the Blender render unless they are physical markings on hardware.

## Performance and reproducibility

- Seed procedural textures and layouts.
- Reuse materials instead of creating a new material per object.
- Use linked duplicates for repeated hardware.
- Separate preview and final settings in code.
- Print output paths, render engine, resolution, samples, and elapsed time.
- Make missing reference assets fail with a clear message instead of silently replacing them with unrelated imagery.

## UI inspection

Background rendering proves reproducibility; it does not replace visual inspection. Open the `.blend` or inspect rendered PNGs after each round. Check:

- whole frame;
- each junction and active face;
- mounts and bases;
- transparent parts against white and dark backgrounds;
- label-safe empty areas;
- final image at manuscript and slide sizes.
