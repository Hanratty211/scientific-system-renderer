"""Audit a Blender scene for render setup and obvious physical-layout risks.

Run inside Blender:
  blender --background scene.blend --python audit_blender_scene.py -- --output audit.json
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict-metadata", action="store_true")
    parser.add_argument("--strict-endpoints", action="store_true")
    parser.add_argument("--endpoint-tolerance", type=float, default=0.04)
    parser.add_argument("--min-width", type=int, default=3000)
    return parser.parse_args(argv)


def world_aabb(obj: bpy.types.Object) -> tuple[Vector, Vector] | None:
    if obj.type not in {"MESH", "CURVE", "FONT", "SURFACE", "META"}:
        return None
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return minimum, maximum


def aabb_overlap(a: tuple[Vector, Vector], b: tuple[Vector, Vector], tolerance: float = 1e-5) -> bool:
    return all(a[0][axis] <= b[1][axis] - tolerance and a[1][axis] >= b[0][axis] + tolerance for axis in range(3))


def aabb_gap(a: tuple[Vector, Vector], b: tuple[Vector, Vector]) -> float:
    squared = 0.0
    for axis in range(3):
        if a[1][axis] < b[0][axis]:
            delta = b[0][axis] - a[1][axis]
        elif b[1][axis] < a[0][axis]:
            delta = a[0][axis] - b[1][axis]
        else:
            delta = 0.0
        squared += delta * delta
    return squared**0.5


def endpoint_component(value: str) -> str:
    return value.split(":", 1)[0] if value else ""


def endpoint_key(value: str) -> tuple[str, str] | None:
    parts = value.split(":", 1)
    if len(parts) != 2 or not all(parts):
        return None
    return parts[0], parts[1]


def vector_property(obj: bpy.types.Object, key: str) -> Vector | None:
    value = obj.get(key)
    try:
        if value is not None and len(value) == 3:
            return Vector((float(value[0]), float(value[1]), float(value[2])))
    except (TypeError, ValueError):
        pass
    return None


def connection_points(obj: bpy.types.Object) -> list[Vector]:
    if obj.type == "CURVE":
        points: list[Vector] = []
        for spline in obj.data.splines:
            values: list[Vector] = []
            if spline.type == "BEZIER":
                controls = list(spline.bezier_points)
                segment_count = len(controls) if spline.use_cyclic_u else max(0, len(controls) - 1)
                for index in range(segment_count):
                    first = controls[index]
                    second = controls[(index + 1) % len(controls)]
                    for sample in range(13):
                        if index and sample == 0:
                            continue
                        t = sample / 12.0
                        one_minus_t = 1.0 - t
                        value = (
                            one_minus_t**3 * first.co
                            + 3.0 * one_minus_t**2 * t * first.handle_right
                            + 3.0 * one_minus_t * t**2 * second.handle_left
                            + t**3 * second.co
                        )
                        values.append(value)
            else:
                values = [Vector((point.co.x, point.co.y, point.co.z)) for point in spline.points]
            for value in values:
                world = obj.matrix_world @ value
                if not points or (world - points[-1]).length > 1e-7:
                    points.append(world)
        if len(points) >= 2:
            return points
    start_local = vector_property(obj, "ssr_start_anchor_local")
    end_local = vector_property(obj, "ssr_end_anchor_local")
    if start_local is not None and end_local is not None:
        return [obj.matrix_world @ start_local, obj.matrix_world @ end_local]
    start = vector_property(obj, "ssr_start_anchor")
    end = vector_property(obj, "ssr_end_anchor")
    return [start, end] if start is not None and end is not None else []


def projected_points(scene: bpy.types.Scene, points: list[Vector]) -> list[tuple[float, float, float]]:
    if scene.camera is None:
        return []
    return [tuple(world_to_camera_view(scene, scene.camera, point)) for point in points]


def segments_cross(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
    epsilon: float = 1e-5,
) -> bool:
    rx, ry = b[0] - a[0], b[1] - a[1]
    sx, sy = d[0] - c[0], d[1] - c[1]
    denominator = rx * sy - ry * sx
    if abs(denominator) <= epsilon:
        return False
    qpx, qpy = c[0] - a[0], c[1] - a[1]
    t = (qpx * sy - qpy * sx) / denominator
    u = (qpx * ry - qpy * rx) / denominator
    return epsilon < t < 1.0 - epsilon and epsilon < u < 1.0 - epsilon


def main() -> int:
    args = parse_args()
    scene = bpy.context.scene
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    def finding(target: list[dict[str, str]], code: str, location: str, message: str) -> None:
        target.append({"code": code, "location": location, "message": message})

    if scene.camera is None:
        finding(errors, "B001", "scene", "no active camera")
    if scene.render.resolution_x < args.min_width:
        finding(warnings, "B002", "scene", f"render width {scene.render.resolution_x} is below {args.min_width}")
    if not scene.render.film_transparent:
        finding(warnings, "B003", "scene", "film transparency is disabled")
    if scene.render.image_settings.color_mode != "RGBA":
        finding(warnings, "B004", "scene", f"color mode is {scene.render.image_settings.color_mode}, expected RGBA")

    roles = Counter()
    untagged: list[str] = []
    components: dict[str, bpy.types.Object] = {}
    connections: list[bpy.types.Object] = []
    supports: defaultdict[str, list[bpy.types.Object]] = defaultdict(list)
    interfaces: defaultdict[str, list[bpy.types.Object]] = defaultdict(list)
    port_anchors: dict[tuple[str, str], bpy.types.Object] = {}
    motion_envelopes: defaultdict[str, list[bpy.types.Object]] = defaultdict(list)

    for obj in scene.objects:
        role = obj.get("ssr_role")
        if not role:
            untagged.append(obj.name)
            continue
        roles[str(role)] += 1
        if role == "component":
            component_id = str(obj.get("ssr_component_id", ""))
            if not component_id:
                finding(errors, "B010", obj.name, "component lacks ssr_component_id")
            elif component_id in components:
                finding(errors, "B011", obj.name, f"duplicate component id: {component_id}")
            else:
                components[component_id] = obj
            if not obj.get("ssr_opacity"):
                finding(warnings, "B012", obj.name, "component lacks ssr_opacity")
            if not obj.get("ssr_scale_level"):
                finding(warnings, "B015", obj.name, "component lacks ssr_scale_level")
        elif role == "connection":
            connections.append(obj)
            for key in ("ssr_source", "ssr_target", "ssr_medium", "ssr_representation"):
                if not obj.get(key):
                    finding(errors, "B013", obj.name, f"connection lacks {key}")
        elif role == "support":
            supported = str(obj.get("ssr_supports", ""))
            if not supported:
                finding(warnings, "B014", obj.name, "support lacks ssr_supports")
            else:
                supports[supported].append(obj)
        elif role == "interface":
            attached_to = str(obj.get("ssr_attached_to", ""))
            if not attached_to:
                finding(errors, "B016", obj.name, "interface lacks ssr_attached_to")
            else:
                interfaces[attached_to].append(obj)
                port_id = str(obj.get("ssr_port_id", ""))
                if port_id:
                    key = (attached_to, port_id)
                    if key in port_anchors:
                        finding(errors, "B019", obj.name, f"duplicate interface anchor for {attached_to}:{port_id}")
                    else:
                        port_anchors[key] = obj
        elif role == "motion-envelope":
            moving_id = str(obj.get("ssr_envelope_for", ""))
            if not moving_id:
                finding(errors, "B017", obj.name, "motion envelope lacks ssr_envelope_for")
            else:
                motion_envelopes[moving_id].append(obj)
            if str(obj.get("ssr_opacity", "")) not in {"transparent", "translucent"}:
                finding(warnings, "B018", obj.name, "motion envelope should be transparent or translucent")

    if args.strict_metadata and untagged:
        finding(errors, "B020", "scene", f"{len(untagged)} object(s) lack ssr_role metadata")
    elif untagged:
        finding(warnings, "B020", "scene", f"{len(untagged)} object(s) lack ssr_role metadata")

    duplicate_suffix = [obj.name for obj in scene.objects if re.search(r"\.\d{3}$", obj.name)]
    if duplicate_suffix:
        finding(warnings, "B021", "scene", f"default duplicate suffixes found: {', '.join(duplicate_suffix[:8])}")

    for supported_id, support_objects in supports.items():
        component = components.get(supported_id)
        if component is None:
            finding(errors, "B030", supported_id, "support references an unknown component")
            continue
        component_box = world_aabb(component)
        support_boxes = [box for obj in support_objects if (box := world_aabb(obj)) is not None]
        if component_box and support_boxes:
            closest = min(aabb_gap(component_box, box) for box in support_boxes)
            if closest > 0.03:
                finding(warnings, "B031", supported_id, f"support appears detached by {closest:.4f} scene units")

    for component_id, component in components.items():
        if bool(component.get("ssr_requires_support")) and component_id not in supports:
            finding(errors, "B032", component_id, "component requires support but none is tagged")
        parent_id = str(component.get("ssr_parent", ""))
        if parent_id:
            parent = components.get(parent_id)
            if parent is None:
                finding(errors, "B033", component_id, f"component references unknown parent {parent_id}")
            else:
                component_box = world_aabb(component)
                parent_box = world_aabb(parent)
                relation = str(component.get("ssr_assembly_relation", "attached"))
                if component_box and parent_box:
                    gap = aabb_gap(component_box, parent_box)
                    if relation in {"attached", "mounted", "laminated", "contacting"} and gap > 0.03:
                        finding(warnings, "B034", component_id, f"child appears detached from parent {parent_id} by {gap:.4f}")
                    if relation in {"contained", "embedded", "integrated"} and not aabb_overlap(component_box, parent_box, tolerance=-1e-5):
                        finding(warnings, "B035", component_id, f"{relation} child does not overlap parent {parent_id}")

    for attached_id, interface_objects in interfaces.items():
        component = components.get(attached_id)
        if component is None:
            finding(errors, "B036", attached_id, "interface references an unknown component")
            continue
        component_box = world_aabb(component)
        for interface in interface_objects:
            interface_box = world_aabb(interface)
            if component_box and interface_box and aabb_gap(component_box, interface_box) > 0.03:
                finding(warnings, "B037", interface.name, f"interface is detached from {attached_id}")

    for moving_id in motion_envelopes:
        if moving_id not in components:
            finding(errors, "B038", moving_id, "motion envelope references an unknown component")

    for component_id, component in components.items():
        if bool(component.get("ssr_requires_motion_envelope")) and component_id not in motion_envelopes:
            finding(errors, "B039", component_id, "moving component requires a motion envelope")

    opaque = {
        component_id: obj
        for component_id, obj in components.items()
        if str(obj.get("ssr_opacity", "")) == "opaque"
    }
    for connection in connections:
        representation = str(connection.get("ssr_representation", "physical"))
        if representation in {"logical", "temporal"}:
            finding(warnings, "B041", connection.name, f"{representation} connection is modeled as Blender geometry; prefer vector overlay")
        if representation not in {"physical", "contact"}:
            continue
        connection_box = world_aabb(connection)
        if connection_box is None:
            continue
        endpoint_ids = {
            endpoint_component(str(connection.get("ssr_source", ""))),
            endpoint_component(str(connection.get("ssr_target", ""))),
        }
        for component_id, component in opaque.items():
            if component_id in endpoint_ids:
                continue
            component_box = world_aabb(component)
            if component_box and aabb_overlap(connection_box, component_box):
                finding(
                    warnings,
                    "B040",
                    connection.name,
                    f"connection bounding box intersects unrelated opaque component {component_id}; inspect visually",
                )

    physical_connections = [
        connection
        for connection in connections
        if str(connection.get("ssr_representation", "physical")) in {"physical", "contact"}
    ]
    screen_paths: dict[str, list[tuple[float, float, float]]] = {}
    for connection in physical_connections:
        source_text = str(connection.get("ssr_source", ""))
        target_text = str(connection.get("ssr_target", ""))
        source_key = endpoint_key(source_text)
        target_key = endpoint_key(target_text)
        points = connection_points(connection)
        missing_geometry = not points
        if missing_geometry and args.strict_endpoints:
            finding(errors, "B052", connection.name, "connection has no auditable route endpoints; tag ssr_start_anchor/ssr_end_anchor or use a curve")
        for endpoint_name, key, point in (
            ("source", source_key, points[0] if points else None),
            ("target", target_key, points[-1] if points else None),
        ):
            if key is None:
                continue
            anchor = port_anchors.get(key)
            if anchor is None:
                target = errors if args.strict_endpoints else warnings
                finding(target, "B053", connection.name, f"{endpoint_name} has no interface anchor object for {key[0]}:{key[1]}")
                continue
            if point is not None:
                gap = (point - anchor.matrix_world.translation).length
                if gap > args.endpoint_tolerance:
                    finding(
                        errors,
                        "B051",
                        connection.name,
                        f"{endpoint_name} endpoint is detached from {key[0]}:{key[1]} by {gap:.4f} scene units",
                    )
        projected = projected_points(scene, points)
        if projected:
            screen_paths[connection.name] = projected
            if any(point[2] > 0 and not (0.0 <= point[0] <= 1.0 and 0.0 <= point[1] <= 1.0) for point in projected):
                finding(warnings, "B054", connection.name, "physical route leaves the active camera frame; inspect for off-frame re-entry")

    connection_by_name = {connection.name: connection for connection in physical_connections}
    for first_name, second_name in itertools.combinations(screen_paths, 2):
        first = connection_by_name[first_name]
        second = connection_by_name[second_name]
        first_endpoints = {str(first.get("ssr_source", "")), str(first.get("ssr_target", ""))}
        second_endpoints = {str(second.get("ssr_source", "")), str(second.get("ssr_target", ""))}
        if first_endpoints & second_endpoints:
            continue
        first_points = screen_paths[first_name]
        second_points = screen_paths[second_name]
        crossed = any(
            segments_cross(a[:2], b[:2], c[:2], d[:2])
            for a, b in zip(first_points, first_points[1:])
            for c, d in zip(second_points, second_points[1:])
        )
        if crossed:
            finding(
                warnings,
                "B050",
                f"{first_name} / {second_name}",
                "physical routes form an interior X-crossing in camera projection; separate them visually or add an explicit bridge/junction",
            )

    report = {
        "scene": bpy.data.filepath,
        "engine": scene.render.engine,
        "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        "film_transparent": scene.render.film_transparent,
        "active_camera": scene.camera.name if scene.camera else None,
        "object_count": len(scene.objects),
        "role_counts": dict(roles),
        "untagged_objects": untagged,
        "errors": errors,
        "warnings": warnings,
        "result": "FAIL" if errors else "PASS",
        "note": "AABB and screen-space crossing findings are conservative candidates and require full-frame plus detail-crop inspection.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"report: {args.output}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
