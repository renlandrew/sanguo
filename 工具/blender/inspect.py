# 看一个 glb 里有哪些物体、骨骼、动作（帧范围）。用法：Blender -b -P inspect.py -- <glb>
import bpy, sys
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for o in bpy.data.objects: print('物体', o.type, o.name, tuple(round(v, 3) for v in o.dimensions))
for a in bpy.data.actions: print('动作', a.name, tuple(a.frame_range))
arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if arm: print('骨骼', len(arm.data.bones), [b.name for b in arm.data.bones])
