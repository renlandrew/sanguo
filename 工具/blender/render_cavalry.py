# 骑兵八方向渲染：与步兵共用机位、真光照和脚底原点。
import bpy, math, os
from mathutils import Vector
from scene_lighting import setup_lighting


def render_cavalry(glb, out, opt):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
    sc = bpy.context.scene
    roots = [o for o in sc.objects if o.parent is None]
    meshes = [o for o in sc.objects if o.type == 'MESH']
    if not meshes: raise RuntimeError('骑兵模型没有网格')
    pivot = bpy.data.objects.new('Direction', None); sc.collection.objects.link(pivot)
    for o in roots: o.parent = pivot
    setup_lighting(sc, opt)
    size = int(opt.get('size', 512)); n = int(opt.get('n', 8)); scale = float(opt.get('scale', 4.8))
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = size; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    sc.render.image_settings.color_depth = '8'; sc.render.fps = 24
    cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = scale
    cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
    elev = math.radians(35); dist = 10
    cam.location = (0, -dist * math.cos(elev), .85 + dist * math.sin(elev))
    cam.rotation_euler = (math.radians(90) - elev, 0, 0)
    f0, f1 = sc.frame_start, sc.frame_end
    # GLB 导入不自动改变场景时间范围，按奔跑 clip 的实际关键帧取样。
    actions = [a for a in bpy.data.actions if a.name.startswith('Gallop')]
    if actions: f0, f1 = actions[0].frame_range
    only = [int(x) for x in opt.get('dirs', '0,1,2,3,4,5,6,7').split(',')]
    for d in only:
        dst = os.path.join(out, str(d)); os.makedirs(dst, exist_ok=True)
        pivot.rotation_euler = (0, 0, d * math.pi / 4)
        for i in range(n):
            # 端点相同，固定机位和整段共用裁框，避免循环换帧时跳动。
            f = f0 + (f1 - f0) * i / max(1, n - 1)
            sc.frame_set(int(f), subframe=f - int(f)); pivot.location = (0, 0, 0)
            sc.render.filepath = os.path.join(dst, 'Gallop_%02d.png' % i)
            bpy.ops.render.render(write_still=True)
        # 倒地另存四帧；受击用奔跑第一帧，冲城沿用奔跑，落马仍由原规则处理。
        sc.frame_set(int(f0))
        for i in range(4):
            t = i / 3; pivot.rotation_euler = (0, -t * math.pi / 2, d * math.pi / 4)
            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get(); low = 1e9
            for ob in meshes:
                ev = ob.evaluated_get(dg); me = ev.to_mesh()
                used = {i for p in me.polygons for i in p.vertices}
                low = min(low, min((ev.matrix_world @ me.vertices[i].co).z for i in used)); ev.to_mesh_clear()
            pivot.location.z -= low
            bpy.context.view_layer.update()
            sc.render.filepath = os.path.join(dst, 'Fall_%02d.png' % i); bpy.ops.render.render(write_still=True)
            pivot.location = (0, 0, 0)
        pivot.rotation_euler = (0, 0, d * math.pi / 4)
    print('渲完', out)
