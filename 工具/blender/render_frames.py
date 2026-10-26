# 把一个带动作的 glb 按游戏视角渲成一帧帧透明 PNG（10-24）：Workbench 平涂 + 描边，水墨着色在 ink_post.py 里做。
# 用法：Blender -b -P render_frames.py -- <glb> <输出目录> [n=8] [size=256] [wpn=spear|club|bow|blade|none] [ax=z] [only=动作1,动作2] [carry=JSON] [yaw=JSON] [scale=2.8]
#   wpn：程序做的兵器，长矛、棒挂右手，弓挂左手，大刀挂右手；saber 环首刀（右手，10-25 西凉兵）、axe 大斧（右手，飞熊军）
#   shield=1：左手再挂一面圆盾（西凉兵），盾面朝前
#   ax：兵器跟着手骨转时，兵器的长轴对着手骨的哪根轴（x/-x/y/-y/z/-z，每种兵器试一次定下来）
#   carry：{"动作名": [x, y, z]} 这些动作里兵器朝向定死（世界坐标，-Y 是朝镜头），只跟着手走；其余动作跟着手骨转
#   yaw：{"动作名": 度} 这段动作整个人绕竖轴转多少度
# 视角：敌人朝镜头（城墙）冲过来，镜头在前上方 35°，正交。
# Meshy 绑的骨架自带 0.01 缩放、骨头坐标和网格不在一个尺度上，所以位置都从变形后的网格上取：
#   原地跑：每帧把「髋」那块网格的水平位移扣掉；兵器：放在那只手的网格中心，朝向跟手骨转（转角不受缩放影响）。
import bpy, sys, math, os, json
from mathutils import Vector, Matrix, Euler
args = sys.argv[sys.argv.index('--') + 1:]
glb, out = args[0], args[1]
opt = dict(a.split('=', 1) for a in args[2:])
SHIELD = opt.get('shield') == '1'
N = int(opt.get('n', 8)); SIZE = int(opt.get('size', 256)); WPN = opt.get('wpn', 'spear'); AX = opt.get('ax', 'z')
ONLY = opt['only'].split(',') if opt.get('only') else None
CARRY = json.loads(opt['carry']) if opt.get('carry') else {}
YAW = json.loads(opt['yaw']) if opt.get('yaw') else {}            # {"动作名": 度}：这段动作把人整个转过来（射箭动作是朝侧面射的，转成朝镜头）
OSCALE = float(opt.get('scale', 2.8))
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith('Icosphere'): o.hide_render = True      # Meshy 带的一个占位球
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
char = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == arm)
sc = bpy.context.scene
HAND = 'LeftHand' if WPN == 'bow' else 'RightHand'

def group(name, w=.5):
    gi = char.vertex_groups[name].index
    return [v.index for v in char.data.vertices if any(g.group == gi and g.weight > w for g in v.groups)]
G_HIPS, G_HAND = group('Hips'), group(HAND)
G_LHAND = group('LeftHand') if SHIELD else []

def mat(name, rgb):
    m = bpy.data.materials.new(name); m.diffuse_color = (*rgb, 1); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*rgb, 1); return m

def join(parts):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); o = bpy.context.object
    sc.cursor.location = (0, 0, 0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')     # 原点放回握把（合并后会落在第一个零件的中心）
    return o

def prim(kind, m, **kw):
    getattr(bpy.ops.mesh, 'primitive_%s_add' % kind)(**kw); o = bpy.context.object; o.data.materials.append(m); return o

# 兵器都沿本地 +Z 摆，握把在原点
weapon = None
WOOD, IRON, RED = mat('wood', (.22, .16, .1)), mat('iron', (.12, .12, .13)), mat('red', (.6, .12, .08))
if WPN == 'spear':      # 长矛：杆 2.1 米，矛头 0.22 米，矛头下一撮红缨；握在杆的下三分之一
    weapon = join([prim('cylinder', WOOD, radius=.016, depth=2.1, vertices=10, location=(0, 0, .35)),
                   prim('cone', IRON, radius1=.035, radius2=0, depth=.22, vertices=8, location=(0, 0, 1.51)),
                   prim('uv_sphere', RED, radius=.05, segments=8, ring_count=6, location=(0, 0, 1.37))])
elif WPN == 'club':     # 狼牙棒：粗木棒 1.1 米，头上一个带钉的大疙瘩
    parts = [prim('cone', WOOD, radius1=.03, radius2=.06, depth=1.1, vertices=10, location=(0, 0, .4)),
             prim('uv_sphere', WOOD, radius=.11, segments=10, ring_count=8, location=(0, 0, .98))]
    for k in range(8):
        a = k / 8 * math.tau; parts.append(prim('cone', IRON, radius1=.025, radius2=0, depth=.09, vertices=6, location=(math.cos(a) * .11, math.sin(a) * .11, .98), rotation=(0, math.pi / 2, a)))
    weapon = join(parts)
elif WPN == 'bow':      # 弓：一段弧（竹木）加一根弦，弧在 YZ 平面里朝 -Y 鼓出，握把在原点
    bpy.ops.curve.primitive_bezier_curve_add(); cu = bpy.context.object; sp = cu.data.splines[0]
    pts = [(0, .12, -.62), (0, -.08, 0), (0, .12, .62)]
    sp.bezier_points.add(1)
    for bp, p in zip(sp.bezier_points, pts): bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    cu.data.dimensions = '3D'; cu.data.bevel_depth = .016; cu.data.bevel_resolution = 2; cu.data.materials.append(WOOD)
    bpy.ops.object.convert(target='MESH'); limb = bpy.context.object
    string = prim('cylinder', IRON, radius=.004, depth=1.24, vertices=6, location=(0, .12, 0))
    weapon = join([limb, string])
elif WPN == 'blade':    # 大刀：杆 1.9 米，头上一片弯刀（压扁的弧形块），刀背一缕红缨
    blade = prim('cube', IRON, size=1, location=(0, .06, 1.42)); blade.scale = (.012, .11, .42)
    bpy.ops.object.transform_apply(scale=True)
    bm = blade.data
    for v in bm.vertices:                                                                 # 往刀刃一侧弯
        t = (v.co.z - 1.0) / .84; v.co.y += .09 * t * t
    weapon = join([prim('cylinder', WOOD, radius=.02, depth=1.9, vertices=10, location=(0, 0, .25)), blade,
                   prim('uv_sphere', RED, radius=.055, segments=8, ring_count=6, location=(0, -.05, 1.2))])
elif WPN == 'saber':    # 环首刀：0.85 米直身单刃，刀柄末端一个铁环，柄上缠红布
    blade = prim('cube', IRON, size=1, location=(0, .012, .5)); blade.scale = (.008, .045, .72); bpy.ops.object.transform_apply(scale=True)
    for v in blade.data.vertices:
        if v.co.z > .8: v.co.y -= .03 * (v.co.z - .8) / .06                              # 刀尖斜收
    bpy.ops.mesh.primitive_torus_add(major_radius=.03, minor_radius=.007, location=(0, 0, -.13), rotation=(0, math.pi / 2, 0)); ring = bpy.context.object; ring.data.materials.append(IRON)
    weapon = join([blade, prim('cylinder', RED, radius=.016, depth=.2, vertices=8, location=(0, 0, 0)), ring])
elif WPN == 'axe':      # 大斧：1.4 米粗柄，头上一片宽月牙斧刃
    head = prim('cube', IRON, size=1, location=(0, .13, 1.12)); head.scale = (.02, .24, .3); bpy.ops.object.transform_apply(scale=True)
    for v in head.data.vertices:
        t = (v.co.z - 1.12) / .15; v.co.y += .06 * (1 - t * t) * (1 if v.co.y > .13 else -.3)   # 刃口外凸成月牙
    weapon = join([prim('cylinder', WOOD, radius=.024, depth=1.4, vertices=10, location=(0, 0, .45)), head,
                   prim('cone', IRON, radius1=.03, radius2=0, depth=.12, vertices=8, location=(0, 0, 1.2))])
shield = None
if SHIELD:              # 圆盾：直径 0.6 米的扁圆，中间一个铁泡钉，盾面朝本地 -Y
    disc = prim('cylinder', mat('shield', (.45, .1, .08)), radius=.3, depth=.04, vertices=20, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0))
    boss = prim('uv_sphere', IRON, radius=.07, segments=10, ring_count=6, location=(0, -.03, 0))
    rim = prim('cylinder', IRON, radius=.31, depth=.03, vertices=20, location=(0, .006, 0), rotation=(math.pi / 2, 0, 0))
    shield = join([rim, disc, boss])
    SHIELD_R = shield.matrix_world.to_quaternion().to_matrix().to_4x4()   # 合并后竖起来的那 90° 只在物体旋转里；每帧摆位置时要带上，不然盾倒回平的（10-26 用户：「盾牌都要竖起来，不是和地面平行拿啊」）
AXR = {'z': (0, 0, 0), '-z': (math.pi, 0, 0), 'x': (0, math.pi / 2, 0), '-x': (0, -math.pi / 2, 0), 'y': (-math.pi / 2, 0, 0), '-y': (math.pi / 2, 0, 0)}[AX]
E = Euler(AXR).to_matrix().to_4x4()

sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO' if opt.get('light') == 'studio' else 'FLAT';   # light=studio：有明暗体积（10-26 去水墨）
sh.color_type = 'TEXTURE'; sh.show_object_outline = True; sh.object_outline_color = (.08, .07, .06)
sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = SIZE; sc.render.resolution_percentage = 100
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = OSCALE
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
elev = math.radians(35); dist = 10
cam.location = (0, -dist * math.cos(elev), .85 + dist * math.sin(elev)); cam.rotation_euler = (math.radians(90) - elev, 0, 0)
if not arm.animation_data: arm.animation_data_create()
hand_pb = arm.pose.bones[HAND]
arm.rotation_mode = 'XYZ'                                   # 导入时是四元数，改成欧拉角，yaw 才起作用

def centroid(ob, me, idx): return sum((ob.matrix_world @ me.vertices[i].co for i in idx), Vector()) / max(1, len(idx))

for a in list(bpy.data.actions):
    if ONLY and a.name not in ONLY: continue
    arm.animation_data.action = a
    if hasattr(arm.animation_data, 'action_slot') and getattr(a, 'slots', None): arm.animation_data.action_slot = a.slots[0]
    f0, f1 = a.frame_range; arm.rotation_euler = (0, 0, math.radians(YAW.get(a.name, 0)))
    for i in range(N):
        f = f0 + (f1 - f0) * i / N
        arm.location = (0, 0, 0); sc.frame_set(int(f), subframe=f - int(f))
        dg = bpy.context.evaluated_depsgraph_get(); ob = char.evaluated_get(dg); me = ob.to_mesh()
        hip, hand = centroid(ob, me, G_HIPS), centroid(ob, me, G_HAND); lhand = centroid(ob, me, G_LHAND) if SHIELD else None; ob.to_mesh_clear()
        off = Vector((-hip.x, -hip.y, 0)); arm.location = off                       # 原地：髋部水平位移扣掉
        if weapon:
            if a.name in CARRY: rot = Vector(CARRY[a.name]).normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()   # 朝向定死，只跟着手走
            else: rot = (arm.matrix_world @ hand_pb.matrix).to_quaternion().to_matrix().to_4x4() @ E                  # 跟着手骨转
            weapon.matrix_world = Matrix.Translation(hand + off) @ rot
        if shield: shield.matrix_world = Matrix.Translation(lhand + off + Vector((-.04, -.08, 0))) @ SHIELD_R                 # 盾挂在左手前面、面朝镜头
        bpy.context.view_layer.update()
        sc.render.filepath = os.path.join(out, '%s_%02d.png' % (a.name, i)); bpy.ops.render.render(write_still=True)
print('渲完', out)
