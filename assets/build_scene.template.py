"""Starter Blender scene for an evidence-grounded scientific system render.

Replace `build_system()` with project-specific constructors while preserving
the object metadata and output conventions used by the audit tools.
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
FINAL_DIR = ROOT / "final"
BLEND_PATH = FINAL_DIR / "system.blend"
PNG_PATH = FINAL_DIR / "system_no_text.png"


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def material(
    name: str,
    rgba: tuple[float, float, float, float],
    *,
    metallic: float = 0.0,
    roughness: float = 0.35,
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    node = next(n for n in mat.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    node.inputs["Base Color"].default_value = rgba
    node.inputs["Metallic"].default_value = metallic
    node.inputs["Roughness"].default_value = roughness
    node.inputs["Alpha"].default_value = rgba[3]
    if emission_strength:
        node.inputs["Emission Color"].default_value = rgba
        node.inputs["Emission Strength"].default_value = emission_strength
    if rgba[3] < 1.0:
        mat.surface_render_method = "DITHERED"
    return mat


def tag(obj: bpy.types.Object, role: str, **properties: str) -> bpy.types.Object:
    obj["ssr_role"] = role
    for key, value in properties.items():
        obj[f"ssr_{key}"] = value
    return obj


def box(
    name: str,
    location: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    mat: bpy.types.Material,
    *,
    bevel: float = 0.02,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("edge bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    return obj


def set_between(obj: bpy.types.Object, start: Vector, end: Vector) -> None:
    direction = end - start
    obj.location = (start + end) * 0.5
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()


def tube_between(
    name: str,
    start: Vector,
    end: Vector,
    radius: float,
    mat: bpy.types.Material,
    *,
    source: str,
    target: str,
    medium: str,
    representation: str = "physical",
) -> bpy.types.Object:
    direction = end - start
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=48,
        radius=radius,
        depth=direction.length,
        location=tuple((start + end) * 0.5),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    set_between(obj, start, end)
    tagged = tag(
        obj,
        "connection",
        source=source,
        target=target,
        medium=medium,
        representation=representation,
    )
    tagged["ssr_start_anchor_local"] = [0.0, 0.0, -direction.length * 0.5]
    tagged["ssr_end_anchor_local"] = [0.0, 0.0, direction.length * 0.5]
    return tagged


def interface_anchor(
    component_id: str,
    port_id: str,
    location: Vector,
    parent: bpy.types.Object,
) -> bpy.types.Object:
    obj = bpy.data.objects.new(f"{component_id}:{port_id} interface", None)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    obj.location = parent.matrix_world.inverted() @ location
    obj.empty_display_type = "SPHERE"
    obj.empty_display_size = 0.05
    obj.hide_render = True
    return tag(obj, "interface", attached_to=component_id, port_id=port_id)


def support(
    component_id: str,
    x: float,
    y: float,
    attachment_z: float,
    metal: bpy.types.Material,
    dark: bpy.types.Material,
) -> None:
    foot_height = 0.12
    foot = box(
        f"{component_id} support foot",
        (x, y, foot_height * 0.5),
        (0.44, 0.38, foot_height),
        metal,
        bevel=0.025,
    )
    tag(foot, "support", supports=component_id)
    post_height = max(attachment_z - foot_height, 0.05)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=0.035,
        depth=post_height,
        location=(x, y, foot_height + post_height * 0.5),
    )
    post = bpy.context.object
    post.name = f"{component_id} support post"
    post.data.materials.append(dark)
    tag(post, "support", supports=component_id)


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def build_system() -> None:
    clear_scene()
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    table_mat = material("neutral table", (0.78, 0.80, 0.82, 1.0), metallic=0.18, roughness=0.32)
    metal = material("brushed metal", (0.62, 0.65, 0.68, 1.0), metallic=0.60, roughness=0.24)
    dark = material("dark housing", (0.035, 0.040, 0.050, 1.0), metallic=0.20, roughness=0.30)
    path_mat = material("connection", (0.05, 0.45, 0.95, 0.72), roughness=0.18, emission_strength=0.35)

    table = box("work surface", (0.0, 0.0, -0.08), (7.0, 3.8, 0.16), table_mat, bevel=0.04)
    tag(table, "environment")

    source_point = Vector((-2.2, 0.0, 1.0))
    sink_point = Vector((2.2, 0.0, 1.0))

    support("source", source_point.x, source_point.y, 0.78, metal, dark)
    source = box("source", tuple(source_point), (0.72, 0.56, 0.52), dark, bevel=0.04)
    tag(
        source,
        "component",
        component_id="source",
        opacity="opaque",
        scale_level="device",
        mobility="fixed",
        requires_support=True,
    )

    support("sink", sink_point.x, sink_point.y, 0.78, metal, dark)
    sink = box("sink", tuple(sink_point), (0.72, 0.56, 0.52), dark, bevel=0.04)
    tag(
        sink,
        "component",
        component_id="sink",
        opacity="opaque",
        scale_level="device",
        mobility="fixed",
        requires_support=True,
    )

    start = source_point + Vector((0.38, 0.0, 0.0))
    end = sink_point - Vector((0.38, 0.0, 0.0))
    interface_anchor("source", "out", start, source)
    interface_anchor("sink", "in", end, sink)
    tube_between(
        "source-to-sink connection",
        start,
        end,
        0.055,
        path_mat,
        source="source:out",
        target="sink:in",
        medium="generic",
        representation="physical",
    )

    bpy.ops.object.light_add(type="AREA", location=(-2.5, -3.0, 4.5))
    key = bpy.context.object
    key.name = "large soft key"
    key.data.energy = 700
    key.data.shape = "DISK"
    key.data.size = 4.5
    tag(key, "light")

    bpy.ops.object.light_add(type="AREA", location=(2.5, 2.0, 3.2))
    fill = bpy.context.object
    fill.name = "soft fill"
    fill.data.energy = 180
    fill.data.size = 3.5
    tag(fill, "light")

    bpy.ops.object.camera_add(location=(4.8, -6.5, 4.2))
    camera = bpy.context.object
    camera.name = "technical overview camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 8.5
    look_at(camera, (0.0, 0.0, 0.65))
    tag(camera, "camera")
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 3000
    scene.render.resolution_y = 1688
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(PNG_PATH)
    scene.view_settings.look = "AgX - Medium High Contrast"


def main() -> None:
    build_system()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    bpy.ops.render.render(write_still=True)
    print(f"saved: {BLEND_PATH}")
    print(f"rendered: {PNG_PATH}")


if __name__ == "__main__":
    main()
