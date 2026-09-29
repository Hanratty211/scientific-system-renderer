"""Blender geometry checks. Sampling is reported as sampling, never a proof."""

import math

from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def evaluated_geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    if mesh is None:
        return None
    try:
        mesh.calc_loop_triangles()
        vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        triangles = [tuple(face.vertices) for face in mesh.loop_triangles]
        if not triangles:
            return None
        edge_counts = {}
        for tri in triangles:
            for a, b in zip(tri, tri[1:] + tri[:1]):
                edge = tuple(sorted((a, b)))
                edge_counts[edge] = edge_counts.get(edge, 0) + 1
        return {
            "tree": BVHTree.FromPolygons(vertices, triangles, all_triangles=True),
            "vertices": vertices,
            "closed": all(value == 2 for value in edge_counts.values()),
        }
    finally:
        evaluated.to_mesh_clear()


def inside_closed(tree, point):
    direction = Vector((0.83219, 0.31247, 0.45731)).normalized()
    origin = point.copy()
    hits = 0
    for _ in range(256):
        hit, _, _, _ = tree.ray_cast(origin, direction)
        if hit is None:
            return bool(hits % 2)
        hits += 1
        origin = hit + direction * 1e-6
    return None


def route_radius(obj):
    if obj.type == "CURVE" and obj.data.bevel_depth > 0:
        scale = max(abs(value) for value in obj.matrix_world.to_scale())
        point_radii = [p.radius for spline in obj.data.splines
                       for p in (spline.bezier_points if spline.type == "BEZIER" else spline.points)]
        return obj.data.bevel_depth * scale * max(point_radii, default=1.0)
    value = obj.get("ssr_radius")
    return float(value) * max(abs(v) for v in obj.matrix_world.to_scale()) if value is not None and float(value) > 0 else None


def route_limitations(obj):
    """Reject unsupported shapes before treating a proxy as rendered geometry."""
    if obj.type != "CURVE":
        return ["Mesh route metadata is a proxy; rendered centerline/radius not verified"]
    reasons = []
    if len(obj.data.splines) != 1:
        reasons.append("Multiple splines are not a verified continuous route")
    if any(s.type not in {"POLY", "BEZIER"} for s in obj.data.splines):
        reasons.append("NURBS/evaluated centerline unsupported")
    if any(s.use_cyclic_u for s in obj.data.splines):
        reasons.append("Cyclic routes need a loop-specific audit")
    if any(m.show_render for m in obj.modifiers):
        reasons.append("Render modifiers can change the route geometry")
    scales = [abs(v) for v in obj.matrix_world.to_scale()]
    if max(scales) - min(scales) > 1e-6:
        reasons.append("Nonuniform scale creates a noncircular cross-section")
    radii = [p.radius for s in obj.data.splines for p in (s.bezier_points if s.type == "BEZIER" else s.points)]
    if radii and max(radii) - min(radii) > 1e-6:
        reasons.append("Variable radius requires local-profile collision checks")
    if obj.data.bevel_object or obj.data.taper_object or obj.data.bevel_mode != "ROUND":
        reasons.append("Custom bevel/taper cross-section unsupported")
    return reasons


def render_inventory(scene, view_layer):
    """Collection-level render visibility, including text in collection instances.

    Instance geometry is deliberately uncovered until transformed auditing exists.
    Viewport-disabled renderable collections are also disclosed as uncovered.
    """
    excluded = set()
    def layers(layer, parent_excluded=False):
        off = parent_excluded or layer.exclude
        if off:
            excluded.add(layer.collection.as_pointer())
        for child in layer.children:
            layers(child, off)
    layers(view_layer.layer_collection)
    objects, instances, text_objects, limitations = {}, [], [], []
    def visit(collection, hidden=False, instanced=False, stack=()):
        if collection.as_pointer() in stack:
            return
        hidden = hidden or collection.hide_render or (not instanced and collection.as_pointer() in excluded)
        if hidden:
            return
        if collection.hide_viewport:
            limitations.append(f"{collection.name}: renderable collection disabled in viewport depsgraph")
        for obj in collection.objects:
            if obj.hide_render:
                continue
            if obj.type == "FONT":
                text_objects.append(obj.name)
            if not instanced:
                objects[obj.name] = obj
            if obj.hide_viewport:
                limitations.append(f"{obj.name}: renderable object disabled in viewport depsgraph")
            if obj.instance_type == "COLLECTION" and obj.instance_collection:
                instances.append(obj.name)
                visit(obj.instance_collection, False, True, stack + (collection.as_pointer(),))
        for child in collection.children:
            visit(child, hidden, instanced, stack + (collection.as_pointer(),))
    visit(scene.collection)
    return list(objects.values()), instances, text_objects, limitations


def transparent_material_supported(obj, depsgraph=None):
    """Only recognize simple transmission/alpha declarations; no shader proof."""
    evaluated = obj.evaluated_get(depsgraph) if depsgraph else obj
    mesh = evaluated.to_mesh()
    if mesh is None:
        return False
    try:
        used = {polygon.material_index for polygon in mesh.polygons}
        materials = [mesh.materials[index] if index < len(mesh.materials) else None for index in used]
    finally:
        evaluated.to_mesh_clear()
    if not materials:
        return False
    for material in materials:
        if not material or not material.use_nodes:
            return False
        nodes = [n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
        if len(nodes) != 1:
            return False
        p = nodes[0]
        transmission = p.inputs.get("Transmission Weight") or p.inputs.get("Transmission")
        alpha = p.inputs.get("Alpha")
        if any(socket and socket.is_linked for socket in (transmission, alpha)):
            return False
        if not ((transmission and transmission.default_value > .01) or (alpha and alpha.default_value < .99)):
            return False
    return True


def sampled_collisions(obj, points, radius, solids, anchors):
    """Check center + 16 perimeter rays and interior points, including end bodies."""
    collisions = []
    allowance = float(obj.get("ssr_contact_allowance", 0.001))
    endpoints = [str(obj.get(key, "")) for key in ("ssr_source", "ssr_target")]

    def legal_contact(name, hit):
        return any(name == component and (hit - anchor).length <= allowance
                   for component, anchor in anchors)

    for solid_id, geometry in solids:
        tree = geometry["tree"]
        found = None
        for a, b in zip(points, points[1:]):
            length = (b - a).length
            if length < 1e-7:
                continue
            direction = (b - a) / length
            side = direction.cross(Vector((0, 0, 1)))
            if side.length < 1e-6:
                side = direction.cross(Vector((0, 1, 0)))
            side.normalize()
            up = direction.cross(side)
            for sample in range(17):
                angle = (sample - 1) * math.tau / 16
                radial = Vector() if sample == 0 else radius * (side * math.cos(angle) + up * math.sin(angle))
                start = a + radial + direction * 1e-6
                remaining = length - 2e-6
                for _ in range(32):
                    hit, _, _, distance = tree.ray_cast(start, direction, remaining)
                    if hit is None:
                        break
                    if not legal_contact(solid_id, hit):
                        found = {"point": list(hit), "sample": sample, "kind": "surface"}
                        break
                    remaining -= distance + 1e-6
                    start = hit + direction * 1e-6
                if found:
                    break
                if geometry["closed"]:
                    for fraction in (0.01, 0.5, 0.99):
                        point = a.lerp(b, fraction) + radial
                        if not legal_contact(solid_id, point) and inside_closed(tree, point):
                            found = {"point": list(point), "sample": sample, "kind": "containment"}
                            break
                if found:
                    break
            if found:
                break
        if found:
            collisions.append({"solid": solid_id, "route": obj.name, **found})
    return collisions


def projection_candidates(scene, obj, points, radius, solids):
    """Conservative finite-width route versus projected body bounds, for review."""
    if scene.camera is None:
        return []
    endpoints = {str(obj.get(key, "")).split(":")[0] for key in ("ssr_source", "ssr_target")}
    projected = [world_to_camera_view(scene, scene.camera, point) for point in points]
    if scene.camera.data.type == "ORTHO":
        margin = radius / scene.camera.data.ortho_scale
    else:
        margin = max((world_to_camera_view(scene, scene.camera, p + scene.camera.matrix_world.to_3x3() @ Vector((radius, 0, 0))) - q).length
                     for p, q in zip(points, projected))
    candidates = []
    for solid_id, geometry in solids:
        if solid_id in endpoints:
            continue
        uv = [world_to_camera_view(scene, scene.camera, p) for p in geometry["vertices"]]
        if not uv or all(p.z <= 0 for p in uv):
            continue
        lower = (min(p.x for p in uv) - margin, min(p.y for p in uv) - margin)
        upper = (max(p.x for p in uv) + margin, max(p.y for p in uv) + margin)
        for a, b in zip(projected, projected[1:]):
            low, high = 0.0, 1.0
            for axis in range(2):
                delta = b[axis] - a[axis]
                if abs(delta) < 1e-12:
                    if not lower[axis] <= a[axis] <= upper[axis]:
                        low, high = 1, 0
                        break
                else:
                    t0, t1 = sorted(((lower[axis] - a[axis]) / delta, (upper[axis] - a[axis]) / delta))
                    low, high = max(low, t0), min(high, t1)
            if low <= high:
                candidates.append(solid_id)
                break
    return candidates


def reflection_checks(scene):
    results, errors = [], []
    for obj in scene.objects:
        if not obj.get("ssr_reflector"):
            continue
        try:
            previous = scene.objects[str(obj["ssr_incident_anchor"])].matrix_world.translation
            following = scene.objects[str(obj["ssr_outgoing_anchor"])].matrix_world.translation
            center = obj.matrix_world @ Vector(obj.get("ssr_surface_point_local", (0, 0, 0)))
            normal = (obj.matrix_world.to_3x3().inverted().transposed() @ Vector(obj.get("ssr_normal_local", (0, 0, 1)))).normalized()
            incoming, outgoing = (center - previous).normalized(), (following - center).normalized()
            error = (incoming - 2 * incoming.dot(normal) * normal - outgoing).length
            radius = float(obj["ssr_beam_radius"])
            aperture = float(obj["ssr_aperture_radius"])
            footprint = radius / max(abs(incoming.dot(normal)), 1e-12)
            result = {"object": obj.name, "reflection_error": error, "footprint_major_radius": footprint, "aperture_radius": aperture}
            results.append(result)
            if error > 1e-5 or footprint > aperture or incoming.dot(normal) >= 0 or outgoing.dot(normal) <= 0:
                errors.append(f"{obj.name}: reflection direction, active face or footprint invalid")
        except (KeyError, ValueError, ZeroDivisionError) as exc:
            errors.append(f"{obj.name}: incomplete reflector metadata: {exc}")
    return results, errors
