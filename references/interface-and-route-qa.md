# Interface and Route QA

Use this reference for real equipment, front panels, connectors, jumpers,
cables, fibers, tubes, supports, endpoints, and correction-driven repair.

## Why this gate exists

Repeated failures in scientific-system rendering tend to come from a small set
of process errors rather than difficult materials or lighting:

1. A crowded overview is treated as permission to invent a plausible chassis,
   adapter, support, or instrument.
2. Port count is copied while port identity, order, and face position remain
   unverified.
3. An unused port produces only a weak warning even though the real setup needs
   a short jumper or terminal connection.
4. A component is guessed from convention before asking the user or consulting
   an authoritative source.
5. Curves are drawn by appearance, causing overshoot, off-frame detours,
   fascia crossings, detached endpoints, or passage through opaque geometry.
6. Routes are collision-free in 3D but form misleading X-crossings in the final
   camera projection.
7. Whole-frame review misses connector seating, support gaps, and small port
   order errors.
8. Labels are added before geometry is stable and become ambiguous after every
   route correction.
9. A user correction is applied locally while dependent geometry, annotations,
   caption text, QA, or logs keep the old interpretation.
10. Private photos, papers, local paths, and project files leak into a reusable
    or public skill package.

The remedy is a sequence of evidence locks and local visual tests, not more
photorealism.

## 1. Component-existence inventory

Create this table before detailed modeling:

| Component ID | Shown in final view | Existence status | Evidence | Function evidence | Geometry evidence | Blocking question |
|---|---:|---|---|---|---|---|

Allowed existence states are:

- `user-confirmed`;
- `source-visible`;
- `authoritative-source`;
- `schematic-placeholder`.

Do not merge existence and function into one claim. A manual may prove what a
device does without proving that the device is present in this setup. A wide
photograph may prove presence without revealing its exact model or ports.

If a device cannot be justified, ask the user. If the user cannot resolve it,
search the exact manufacturer documentation or primary setup description. If
it remains uncertain, omit it or mark it visibly schematic.

## 2. Per-face port map

For every depicted device face, create a stable interface map:

| Port ID | Device face | Face position | Connector | Direction | Medium | Identity evidence | Confidence | Expected state |
|---|---|---|---|---|---|---|---|---|

Use positions such as `front-row-1-left`, `front-column-2-upper`, or
`rear-right-lower`. Keep IDs stable across the manifest, Blender anchors,
connection metadata, labels, and QA crops.

An approximate row of anonymous connectors is unacceptable when the figure is
supposed to explain a real setup. Prefer a close-up or user annotation over a
wide photograph. Do not transfer labels from a similar-looking model.

Every port must declare exactly one expected state:

- `connected`: a route must use it;
- `intentionally-open`: the reason and evidence must be recorded;
- `outside-figure`: the continuation and omission must be stated and evidenced.

There are no silent open ports.

## 3. Port-to-port connection table

Freeze connectivity before routing geometry:

| Connection ID | Source port | Target port | Medium | Route class | Physical cause of bends/branches | Evidence |
|---|---|---|---|---|---|---|

Separate physical transport, field coupling, logical flow, temporal sequence,
contact, containment, and motion envelopes. A bend is not a component. A split
or merge requires a real splitter, coupler, manifold, hub, switch, or other
declared cause.

Short front-panel jumpers deserve their own connection rows. They are easy to
omit in an overview and often determine whether two adjacent ports are being
interpreted correctly.

## 4. Route construction

Build routes from port-anchor coordinates rather than from housing centers.

- Keep a route corridor inside the visible platform or figure bounds.
- Use controlled intermediate points; inspect Bezier handles for overshoot.
- Seat both endpoints on the connector face without a visible gap or buried
  segment.
- Do not pass through opaque housings, panels, supports, table fascias, or
  unrelated connectors.
- Keep route thickness and bend radius plausible for the represented medium.
- Use explicit outside-figure notation when a long route cannot be shown.
- Do not add decorative terminal caps, couplers, adapters, or strain reliefs
  without evidence.

## 5. Required camera-space QA

World-space collision checks are necessary but insufficient. Project route
centerlines through the final camera and inspect:

- unrelated interior X-crossings;
- apparent connection to the wrong nearby port;
- routes hidden behind a housing or support;
- routes leaving the frame and re-entering;
- branch points that appear to float;
- endpoint gaps masked by perspective.

An intentional bridge or junction needs clear geometry. Otherwise move the
route, component, or camera until the topology reads directly.

## 6. Mandatory crop matrix

Create a full-resolution crop for each item:

| Crop class | What must be visible |
|---|---|
| component existence | complete silhouette, support, and neighboring context |
| port cluster | all ports in order, labels if physical, and face boundaries |
| endpoint | connector seat plus the first/last route segment |
| short jumper | both endpoints and the full jumper |
| branch or junction | incoming and outgoing routes plus the causal component |
| support contact | body, bracket/post, base, and attachment surfaces |
| route corridor | every bend and any dense crossing region |
| final sink | last transport segment and the actual measurement interface |

Use `generate_detail_crops.py` with a checked-in project-specific
`qa_regions.json`. The crop index is part of QA evidence, not a decorative
contact sheet.

## 7. Correction invalidation protocol

A user correction outranks a prior accepted render. When the user changes a
component identity, port position, connection, state, or physical mechanism:

1. mark the prior QA round superseded;
2. update the source ledger and manifest first;
3. identify every dependent component, route, label, caption sentence, and
   crop;
4. rebuild from the reproducible source;
5. rerun manifest validation, Blender audit, render QA, and detail crops;
6. record the correction and new evidence in the work log;
7. accept only the new artifacts.

Do not patch only the visible symptom. A corrected port map can change cable
routing, camera readability, annotation placement, and architecture text.

## 8. Public-release boundary

Reusable skills and public repositories must contain only original general
instructions, code, generic templates, and synthetic fixtures. Exclude user
photos, videos, papers, extracted figures, project renders, `.blend` files,
private logs, personal paths, and unlicensed manufacturer media. Run
`audit_public_release.py` before publication.
