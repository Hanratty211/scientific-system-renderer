# Geometry Validation

Use `audit_blender_scene.py` on the saved final scene, not an earlier preview.
It reports the scene file SHA256, scope, tested route count and untagged geometry.
`render_qa.py` similarly binds its report to the PNG SHA256. Rebuild reports and
crops after changes; an old PASS is not transferable to a different artifact.

## Coverage and Limits

- PASS: declared automatic checks ran without errors. It is not scientific or
  user acceptance. Warnings still need documented visual disposition.
- FAIL: a checked invariant failed.
- UNVERIFIED: meaningful coverage is absent, such as missing semantic tags,
  missing routes, missing anchors or missing finite-width radius data.
- `--scope component-sheet` permits intentionally connection-free device views.
- `--no-text` rejects render-visible FONT objects, including collection-instance
  text, and excludes render-disabled collections. Inspect textures and mesh lettering
  visually, since FONT absence alone does not establish absence of all text.

Use component, part, support and environment roles for solid geometry. Parts
can use `ssr_parent` to identify their owning component. Opacity declarations
must agree with actual materials; omitted solid opacity defaults to opaque.

Automatic finite-width checks currently cover single, non-cyclic POLY or Bezier
curves with a uniform circular bevel, uniform scale and no render modifiers.
Mesh proxies, NURBS, multiple splines, tapering, custom cross-sections and
modified routes return UNVERIFIED and are excluded from completed coverage.
They are not replaced with control polygons or fictitious inter-spline chords.
Mesh `ssr_radius` is local-space metadata, scaled for conservative diagnostics;
it does not prove that a mesh has that radius or centerline.

Component counts require visible evaluated geometry, not just tagged empties.
Unknown roles are uncovered. Collection instances are disclosed as spatially
unverified until their transformed geometry is supported. Viewport-disabled
but render-enabled geometry likewise needs review. Simple transmission/alpha
materials actually used by evaluated faces are compared with opacity declarations;
unused material slots do not imply opaque faces. Complex shaders need manual
review. Transparent solids still block cables and tubes. Optical transmission
through them is a separate, explicitly unverified domain question.

The sampler tests a center ray and 16 perimeter rays, plus closed-mesh interior
points, against evaluated geometry. It includes source and destination bodies.
Only hits within `ssr_contact_allowance` of the corresponding interface anchor
are permitted. Keep this allowance smaller than the connector seat and record
its physical purpose. Never use a large allowance to waive housing intrusion.
This finite sample can miss thin objects between rays; critical clearances need
additional sampling, intersection tests or close inspection. Open meshes have
surface checks only. Projected body bounds yield conservative review candidates,
not confirmed collisions. Inspect full beam/cable width against support outlines.

This is not a general part-to-part clash detector. Even a connection-free scene
can contain overlapping chip packages, detached spring ends or floating layers.
Inspect those assemblies separately, using explicit mating/contact constraints
or focused distance tests where possible. Never report a route-only PASS as
proof that all parts fit. Match material character to the photographed object:
a foil pouch should not silently become a machined enclosure, and visual
roughness should not imply a measured pore lattice.

## Reflectors (Optical Tasks Only)

Mark the actual reflecting object with `ssr_reflector=True`, plus
`ssr_incident_anchor` and `ssr_outgoing_anchor` naming scene objects. Declare
`ssr_surface_point_local`, `ssr_normal_local`, `ssr_beam_radius` and
`ssr_aperture_radius`. The checker uses the object's world transform to test
reflection direction, active side and the oblique footprint. These values must
describe the actual geometry, not a disconnected theoretical plane. This check
does not simulate diffraction or validate a complete optical instrument.

## Executable Regressions

Run `blender --background --factory-startup --python-exit-code 1 --python
scripts/run_blender_regressions.py -- --output /tmp/renderer-regressions.json`.
Cases are original generated scenes, not publisher figures. They test empty
coverage, endpoint detachment, endpoint-body intrusion, finite-width intrusion,
enclosed routes, projected support ambiguity, wrong mirror orientation and
no-text enforcement, collection visibility, instanced text, missing geometry,
invalid roles, unsupported splines/modifiers/tapers, opacity mismatch and used
versus unused material slots. Factory startup avoids localization and user-file
state affecting reproducibility; the explicit Python exit code exposes failures.
A test pass does not prove arbitrary domain competence.

For paper-based evaluations, keep article URLs, figure/panel IDs, source rights,
observed facts, omitted unknowns, renders and human feedback in a separate local
project. Do not add paper images or case-specific content to the public skill.
