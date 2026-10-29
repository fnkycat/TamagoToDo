from pathlib import Path
import bpy

ASSET_DIR = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ASSET_DIR / "tamago_pet.blend"))
root = bpy.data.objects.get("Tamago root")
if root is None:
    raise RuntimeError("Tamago root is missing from the source model")

mouth = bpy.data.objects.get("Gentle smile")
if mouth is None:
    raise RuntimeError("Mouth is missing from the source model")
bpy.data.objects.remove(mouth, do_unlink=True)
material = bpy.data.materials.get("Smile dark brown")
if material is None:
    material = bpy.data.materials.new("Smile dark brown")
material.diffuse_color = (0.14, 0.064, 0.042, 1.0)


def curve(name, points, depth):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 16
    data.bevel_depth = depth
    data.bevel_resolution = 4
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coords in zip(spline.bezier_points, points):
        point.co = coords
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj.parent = root
    obj.matrix_parent_inverse = root.matrix_world.inverted()
    return obj


curve("Grumpy mouth", [(-0.15, -0.783, 1.19), (0.0, -0.824, 1.26), (0.15, -0.783, 1.19)], 0.025)
curve("Grumpy left brow", [(-0.52, -0.70, 1.66), (-0.38, -0.75, 1.70), (-0.23, -0.77, 1.78)], 0.025)
curve("Grumpy right brow", [(0.23, -0.77, 1.78), (0.38, -0.75, 1.70), (0.52, -0.70, 1.66)], 0.025)

bpy.ops.object.select_all(action="DESELECT")
root.select_set(True)
for obj in root.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(
    filepath=str(ASSET_DIR / "tamago_pet_grumpy_unified.glb"),
    export_format="GLB",
    use_selection=True,
    export_animations=False,
    export_apply=True,
)
