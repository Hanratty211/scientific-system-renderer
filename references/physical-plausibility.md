# Physical Plausibility Rules

## Universal connection model

Model every system as components with ports and directed connections. A connection has a medium, source port, destination port, width or aperture, and path behavior. A component may expose capabilities such as `reflect`, `split`, `merge`, `switch`, `convert`, `focus`, `resize`, `filter`, `valve`, `pump`, `support`, or `sense`.

Also declare what a visible relationship means. Use `physical` for a real beam, wire, tube, load path, or transported material; `field` for wireless coupling; `logical` for information architecture; `temporal` for state transitions; `contact` for an interface; and `motion-envelope` for reachable or deformable space. A convincing arrow is not evidence that two objects are physically connected.

Reject these universal errors:

- a path begins or ends on an arbitrary housing surface;
- a path crosses an opaque body or support;
- a bend occurs in free space without a reflector, guide, elbow, or routing constraint;
- a path splits or merges without a junction component;
- a width, beam diameter, pipe diameter, or cable bundle changes without a physical cause;
- an active face is detached from or larger than its housing;
- a mount passes through a component or floats below it;
- repeated states are drawn as simultaneous hardware without a multiplexing explanation.

## Hierarchy, scale, and assemblies

- Separate environment, system, subsystem, device, component, microstructure, and anatomical scales.
- Tie every microstructure to a parent component or device. Do not float a transistor cell, microchannel, active layer, or lattice unit beside the product without an inset relationship.
- Use exploded views only to explain assembly. Preserve alignment, layer order, attachment surfaces, and a clear route back to the assembled state.
- Distinguish `mounted`, `contained`, `integrated`, `laminated`, `embedded`, `attached`, and `contacting` relationships.
- Do not imply that an exploded gap exists in the operating device.

## Optics and photonics

- Distinguish reflective, transmissive, partially reflective, absorptive, and diffractive surfaces.
- Orient transmissive optics perpendicular to the local optical axis unless the real setup requires tilt.
- Orient reflectors from incoming and outgoing ray directions; do not rotate only for visual convenience.
- Show beam turns only at mirrors, reflective modulators, prisms, gratings, beam splitters, fibers, or other justified elements.
- Show a splitter or combiner as explicit hardware. Keep all branches continuous through the interaction region.
- Keep a DMD, reflective SLM, mirror, detector package, and camera housing opaque. The beam reaches the documented active surface and reflects or terminates there.
- Distinguish the device body from the active DMD/SLM/sensor area.
- Place lenses, apertures, irises, waveplates, and polarizers on the local beam axis with plausible open mounts.
- Change beam diameter at lenses, focal planes, telescopes, apertures, fibers, or documented propagation effects. Do not change it early or late for composition.
- Keep beam footprints consistent with local beam diameter and attached to the optical surface normal.
- Show time, wavelength, polarization, or spatial multiplexing with correct simultaneity. If one SLM loads many masks sequentially, show one physical SLM plus a time-sequence inset.

## Electronics and data systems

- Connect cables to visible or documented ports, not through enclosure walls.
- Distinguish power, ground, analog, digital, trigger, clock, network, and high-voltage paths when they matter.
- Match connector families and directionality. Mark adapters, hubs, converters, or isolation stages explicitly.
- Do not branch a point-to-point cable without a hub, terminal block, splitter, bus, or daisy-chain port.
- Keep cable bend radius and strain relief plausible. Avoid cables passing through hardware or hanging without support in a physical setup view.
- Separate a logical data-flow arrow from a literal cable. Label the view as logical when port-level fidelity is not intended.

## Fluid, vacuum, pneumatic, and microfluidic systems

- Connect tubing to fittings, valves, manifolds, reservoirs, pumps, chambers, or chips.
- Show reducers and adapters where tube diameter changes.
- Show branch and merge points with tees, manifolds, mixers, or chip junctions.
- Respect directional components such as check valves, pumps, regulators, filters, and flow meters.
- Keep vacuum boundaries closed. Do not terminate a vacuum line in open air unless it is a vent.
- Consider gravity, reservoir height, trapped gas, drainage, and sterile boundaries when relevant.
- Distinguish sample, reagent, waste, coolant, gas, and vacuum media by restrained line grammar.
- Distinguish an open route from a closed loop. An operating cycle such as adsorption/desorption does not make its airflow a recirculating loop.
- Put the pump, fan, compressor, gravity head, or other driver on the route it drives; a nearby unrelated driver is not sufficient.
- For layered microfluidics, tie every channel to its chip and show vias, ports, seals, traps, and layer transitions explicitly.

## Thermal systems

- Trace heat from source to sink through conduction, convection, radiation, heat pipe, coolant, or airflow.
- Attach heat sinks, cold plates, fans, and thermal interfaces to the surfaces they serve.
- Do not use free-floating heat arrows as a substitute for a physical path in a setup figure.
- Show coolant inlet and outlet separately and preserve flow direction.
- Ensure fan airflow is not blocked by solid geometry unless the obstruction is intentional.

## Mechanical and robotic systems

- Show load paths, bases, joints, bearings, actuators, end effectors, and constraints.
- Match displayed motion to joint degrees of freedom.
- Do not let rigid bodies overlap through their motion envelope.
- Attach sensors and tools to actual mounting interfaces.
- Include cable chains, hoses, or slack where moving joints require them.
- Keep the center of mass and support polygon plausible when stability matters.
- Declare reach, flight, toolpath, scan, articulation, or deformation envelopes. Check the envelope against stations, people, walls, adjacent robots, cables, and the workpiece.
- For deformable systems, separate reference, loaded, and programmed states. Do not overlap mutually exclusive shapes as if they occur simultaneously.

## RF, microwave, acoustic, and wave systems

- Connect coaxial cables, waveguides, antennas, probes, transducers, and loads at compatible ports.
- Show bends, couplers, circulators, filters, and splitters as hardware rather than arbitrary path geometry.
- Respect shielding, ground planes, line of sight, polarization, and near-field/far-field distinctions when they are central to the claim.
- Do not depict wave intensity passing through metal shielding unless penetration is the phenomenon being explained.
- Do not render RF, magnetic, acoustic, or other wireless coupling as a literal cable. Show a restrained field region or abstract field arrow and record which boundaries transmit, attenuate, couple, or block that medium.

## Biomedical and laboratory systems

- Separate patient/sample contact, sterile, clean, and non-sterile regions.
- Show sample direction, collection points, waste, sensors, and contamination barriers.
- Distinguish schematic anatomy from a literal device setup.
- Avoid implying clinical validation, scale, or invasiveness not supported by evidence.
- Classify contact interfaces. Anatomical contact, thermal contact, mechanical loading, adhesive bonding, sterile boundaries, and electrodes are not interchangeable.
- Wearables and implants must identify the actual body-contact surface or electrode, not merely sit near schematic anatomy.
- For automated laboratories, separate sample transfer, robot motion, station operation, and software control. A logical scheduler arrow is not a physical sample route.

## Computing and network architectures

- Prefer 2D vector diagrams for logical systems unless racks, ports, cable topology, cooling, or physical deployment are part of the claim.
- Separate control plane, data plane, storage, compute, and user interfaces when relevant.
- Label protocols or interfaces at boundaries; do not imply direct compatibility without an adapter layer.
- Use 3D only when physical arrangement, packaging, latency path, or hardware integration benefits from it.
