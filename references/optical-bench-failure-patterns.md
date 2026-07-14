# Optical-Bench Failure Patterns

This reference records generalized optical-rendering failure modes. It contains no project-specific scene, paper figure, image, or bibliographic material. Load it for optical benches or repeated physical-review failures.

## What failed and what it taught

| Failure | General lesson |
|---|---|
| Reflective DMD and SLM were drawn as transmissive sheets | Record boundary behavior before modeling; an active image on a face does not make the device transparent. |
| Sixteen phase masks appeared as sixteen physical planes | Separate hardware count from temporal state count. Show one device plus a time-multiplexing inset. |
| Lenses and devices were rotated for appearance rather than path geometry | Derive orientation from local incoming/outgoing vectors and then choose the camera. |
| Light crossed mirror bodies, mounts, and housings | Model ports and active faces; trim a path at opaque endpoints and inspect junction crops. |
| Decorative mirrors did not change the route | Every optical element must have a functional effect or be removed. |
| Beam width changed before reaching a lens or long after it | Encode radius stations at actual optical causes. Keep aperture constant between causes. |
| A nonexistent iris was added to explain a virtual focus | Distinguish a physical aperture from a focal plane or schematic focus. Do not invent hardware to repair a drawing. |
| DMD and detector active regions filled or floated beyond the housing | Model body, inactive face, active area, and beam footprint as attached but separate geometry. |
| Beam footprints were rotated in world coordinates | Attach footprint orientation to the local surface normal. |
| Beam splitter coating floated outside the cube or had the wrong orientation | Model the internal interaction plane and derive its normal from the relevant path branches. |
| Detector branch was visually bent at transmissive optics | Keep a relay collinear unless a real steering component changes direction. |
| Supports intersected or detached from devices | Compute support height and attachment point from component geometry. Inspect every base cluster. |
| Lenses looked like dark filters | Give transparent optics a convex profile, polished edge, open mount, neutral background, and appropriate lighting. |
| Laser looked like a generic metal box | Use the exact product class, front barrel, aperture, body proportions, cooling details, and mount from authoritative references. |
| Labels rotated, overlapped, or used ambiguous leaders | Stabilize the base render first; add short horizontal editable labels near components afterward. |
| A technically improved draft was shown before visual inspection | Render, inspect, record defects, and iterate before reporting completion. |

## Reusable optical checklist

Before rendering:

- identify reflective and transmissive components;
- mark active faces and local normals;
- list all beam turns and the device causing each turn;
- list all beam-radius changes and the element causing each change;
- distinguish physical apertures from virtual focal points;
- distinguish simultaneous paths from sequential device states;
- place polarization, filtering, and detection elements where the real principle requires them;
- calculate support attachment heights from the optical axis.

After rendering:

- inspect DMD/SLM/mirror/beam-splitter junctions at high zoom;
- inspect beam continuity through transparent components;
- inspect every mount and base for contact or interpenetration;
- verify the source-to-detector route in one continuous reading;
- composite transparency on white and dark backgrounds;
- check that the no-text render can accept clean vector labels.
