"""Original scene regressions; execute inside Blender, no external media."""

import argparse
import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_blender_scene as audit


def box(name, center, size, role="component"):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj["ssr_role"] = role
    obj["ssr_component_id"] = name
    obj["ssr_opacity"] = "opaque"
    obj["ssr_scale_level"] = "device"
    return obj


def anchor(name, position):
    obj = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = position
    obj["ssr_role"] = "interface"
    obj["ssr_attached_to"], obj["ssr_port_id"] = name.split(":")
    return obj


def setup():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    bpy.ops.object.camera_add(location=(0, 0, 10))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 7
    scene.camera = camera
    scene.render.resolution_x = 3000
    scene.render.resolution_y = 1800
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = "RGBA"
    box("source", (-2, 0, 0), (1, 1, 1))
    box("sink", (2, 0, 0), (1, 1, 1))
    anchor("source:out", (-1.5, 0, 0))
    anchor("sink:in", (1.5, 0, 0))
    curve = bpy.data.curves.new("route shape", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.1
    spline = curve.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (-1.5, 0, 0, 1)
    spline.points[1].co = (1.5, 0, 0, 1)
    route = bpy.data.objects.new("route", curve)
    scene.collection.objects.link(route)
    for key, value in {"role": "connection", "source": "source:out", "target": "sink:in", "medium": "electrical", "representation": "physical"}.items():
        route["ssr_" + key] = value
    bpy.context.view_layer.update()
    return route


def run_case(name, mutation, expected, code, directory):
    route = setup()
    mutation(route)
    bpy.context.view_layer.update()
    report = directory / (name + ".json")
    sys.argv = ["audit", "--", "--output", str(report), "--strict-endpoints", "--no-text"]
    with contextlib.redirect_stdout(io.StringIO()):
        audit.main()
    result = json.loads(report.read_text())
    codes = {item["code"] for item in result["errors"] + result["warnings"]}
    passed = result["result"] == expected and (code is None or code in codes)
    return {"case": name, "expected": expected, "observed": result["result"], "code": code, "passed": passed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])

    def empty(route):
        for obj in bpy.context.scene.objects:
            for key in list(obj.keys()):
                del obj[key]

    def detach(route):
        route.data.splines[0].points[-1].co = (1.2, 0, 0, 1)

    def endpoint_intrusion(route):
        bpy.context.scene.objects["source"].scale.x = 1.5

    def enclosed(route):
        box("enclosure", (0, 0, 0), (8, 2, 2))

    def projection(route):
        box("support", (0, 0, -1), (0.4, 0.4, 0.3), role="support")

    def bad_reflection(route):
        mirror = box("mirror", (0, 2, 0), (0.1, 0.3, 0.3))
        for key, value in {"reflector": True, "incident_anchor": "source:out", "outgoing_anchor": "sink:in", "normal_local": [0, 0, 1], "beam_radius": .05, "aperture_radius": .2}.items():
            mirror["ssr_" + key] = value

    def text(route):
        bpy.ops.object.text_add()
        bpy.context.object["ssr_role"] = "annotation"

    def nurbs(route):
        route.data.splines.clear()
        s = route.data.splines.new("NURBS")
        s.points.add(3)
        for p, co in zip(s.points, [(-1.5, 0, 0, 1), (-.5, 1.5, 0, 1), (.5, 1.5, 0, 1), (1.5, 0, 0, 1)]):
            p.co = co
        s.order_u = 4
        s.use_endpoint_u = True
        box("nurbs obstacle", (0, 1.125, 0), (.25, .25, .25))

    def multi_spline(route):
        route.data.splines[0].points[-1].co = (-.3, 0, 0, 1)
        s = route.data.splines.new("POLY")
        s.points.add(1)
        s.points[0].co, s.points[1].co = (.3, 0, 0, 1), (1.5, 0, 0, 1)

    def modified(route):
        mod = route.modifiers.new("Duplicated geometry", "ARRAY")
        mod.use_relative_offset = False
        mod.use_constant_offset = True
        mod.constant_offset_displace = (0, 1, 0)

    def hidden(route):
        for obj in bpy.context.scene.objects:
            if obj.type != "CAMERA":
                obj.hide_render = True

    def hidden_text(route):
        text(route)
        obj = bpy.context.object
        coll = bpy.data.collections.new("Render disabled")
        bpy.context.scene.collection.children.link(coll)
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        coll.objects.link(obj)
        coll.hide_render = True

    def instance_text(route):
        text(route)
        obj = bpy.context.object
        coll = bpy.data.collections.new("Instance text")
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        coll.objects.link(obj)
        instance = bpy.data.objects.new("Collection instance", None)
        bpy.context.scene.collection.objects.link(instance)
        instance.instance_type = "COLLECTION"
        instance.instance_collection = coll
        instance["ssr_role"] = "environment"

    def opacity(route):
        obj = box("opacity mismatch", (0, 0, 0), (.3, .3, .3))
        obj["ssr_opacity"] = "transparent"

    def anchors_float(route):
        for name in ("source:out", "sink:in"):
            bpy.context.scene.objects[name].location.y += 1
        route.location.y += 1

    cases = [("valid", lambda r: None, "PASS", None),
             ("untagged", empty, "UNVERIFIED", None),
             ("detached", detach, "FAIL", "B051"),
             ("endpoint-body", endpoint_intrusion, "FAIL", "B070"),
             ("finite-width", lambda r: box("thin obstacle", (0, .095, 0), (.1, .04, .1)), "FAIL", "B070"),
             ("enclosed", enclosed, "FAIL", "B070"),
             ("projection", projection, "PASS", "B071"),
             ("reflection", bad_reflection, "FAIL", "B080"),
             ("no-text", text, "FAIL", "B060"),
             ("nurbs-unverified", nurbs, "UNVERIFIED", None),
             ("multiple-splines", multi_spline, "UNVERIFIED", None),
             ("modified-route", modified, "UNVERIFIED", None),
             ("tapered-route", lambda r: setattr(r.data.splines[0].points[0], "radius", .1), "UNVERIFIED", None),
             ("hidden-geometry", hidden, "UNVERIFIED", None),
             ("hidden-text", hidden_text, "PASS", None),
             ("instanced-text", instance_text, "FAIL", "B060"),
             ("unknown-role", lambda r: box("unknown", (0, 0, 0), (.2, .2, .2), "componnet"), "UNVERIFIED", "B020"),
             ("opacity-mismatch", opacity, "FAIL", "B070"),
             ("floating-anchors", anchors_float, "UNVERIFIED", "B037")]
    with tempfile.TemporaryDirectory(prefix="ssr-scenes-") as temporary:
        results = [run_case(*case, Path(temporary)) for case in cases]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    if not all(result["passed"] for result in results):
        raise RuntimeError("Scene regression failed")


if __name__ == "__main__":
    main()
