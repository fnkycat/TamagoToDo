from pathlib import Path
import bpy

ASSET_DIR = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ASSET_DIR / "tamago_pet.blend"))
root = bpy.data.objects.get("Tamago root")
if root is None:
    raise RuntimeError("Tamago root is missing from the source model")

for name in ("Left sprout leaf", "Right sprout leaf"):
    leaf = bpy.data.objects.get(name)
    if leaf is None or leaf.type != "MESH":
        raise RuntimeError(f"{name} is missing from the source model")
    leaf.data = leaf.data.copy()
    direction = 1 if name.startswith("Left") else -1
    for vertex in leaf.data.vertices:
        amount = min(1.0, abs(vertex.co.x) / 0.25)
        vertex.co.z -= 0.075 * amount * amount
    leaf.data.update()

mouth = bpy.data.objects.get("Gentle smile")
if mouth is None:
    raise RuntimeError("Mouth is missing from the source model")
points = [(-0.16, -0.783, 1.19), (0.0, -0.824, 1.245), (0.16, -0.783, 1.19)]
for point, coords in zip(mouth.data.splines[0].bezier_points, points):
    point.co = coords
    point.handle_left_type = "AUTO"
    point.handle_right_type = "AUTO"

bpy.ops.object.select_all(action="DESELECT")
root.select_set(True)
for obj in root.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(
    filepath=str(ASSET_DIR / "tamago_pet_tense.glb"),
    export_format="GLB",
    use_selection=True,
    export_animations=False,
    export_apply=True,
)
