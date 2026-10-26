# 城头武将（10-24）：从背后渲一段动作，带布料模拟的披风和程序做的兵器。一个进程只渲一段动作（布料缓存不串）。
# 用法：Blender -b -P render_general.py -- <glb> <输出目录> act=<动作名> wpn=glaive|snake|twin cape=r,g,b [n=8] [size=256] [scale=3.2] [ax=x] [lax=-x] [wind=2500]
#   glaive 青龙偃月刀（右手）、snake 丈八蛇矛（右手）、twin 双股剑（两手各一把）；ax / lax 是兵器长轴对着右手 / 左手骨的哪根轴
#   light=studio：立体光加凹陷阴影（城头武将用，平涂光从背后看是一团）
#   cape / edge：披风和镶边的颜色（0–1）；carry={"动作": [x,y,z]}：这段动作兵器朝向定死（待机时竖着拄，免得刀尖正对镜头看不见）；wind：风力（从城外往城里吹，披风往镜头这边飘；2500 左右飘得明显，5000 会整个吹起来）
# 镜头和敌人一样（前上方 35°、正交），人转 180° 背对镜头。原地：镜头每帧跟着髋部的水平位置走（不挪人，免得布料被甩）。
# 披风：两肩之间一块 10×14 的布，上两行钉在背上（跟着 Spine02 走），其余布料模拟，和身体碰撞；动作开始前先空跑 30 帧让它垂好。
import bpy, sys, math, os
from mathutils import Vector, Matrix, Euler
args = sys.argv[sys.argv.index('--') + 1:]
glb, out = args[0], args[1]
opt = dict(a.split('=', 1) for a in args[2:])
ACT = opt['act']; WPN = opt.get('wpn', 'none'); N = int(opt.get('n', 8)); SIZE = int(opt.get('size', 256))
OSCALE = float(opt.get('scale', 3.2)); AX = opt.get('ax', 'x'); LAX = opt.get('lax', '-x'); WIND = float(opt.get('wind', 2500))
CAPE = tuple(float(v) for v in opt['cape'].split(',')) if opt.get('cape') else None
EDGE = tuple(float(v) for v in opt['edge'].split(',')) if opt.get('edge') else None     # 披风镶边的颜色
import json
CARRY = json.loads(opt['carry']) if opt.get('carry') else {}       # {"动作名": [x, y, z]}：这段动作里兵器竖着拄（世界方向），双剑左手自动镜像
PRE = 30
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith('Icosphere'): o.hide_render = True
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
char = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == arm)
sc = bpy.context.scene
arm.rotation_mode = 'XYZ'; arm.rotation_euler = (0, 0, math.pi)          # 背对镜头
act = bpy.data.actions[ACT]
if not arm.animation_data: arm.animation_data_create()
arm.animation_data.action = None
for t in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(t)
# 动作往后挪 PRE 帧放进 NLA，前 PRE 帧保持第一个姿势，让披风先垂好（布料在负数帧不模拟）
strip = arm.animation_data.nla_tracks.new().strips.new(ACT, PRE, act)
strip.extrapolation = 'HOLD'
F0, F1 = PRE + int(act.frame_range[0]), PRE + int(math.ceil(act.frame_range[1]))
sc.frame_start, sc.frame_end = 0, F1

def group(name, w=.4):
    if name not in char.vertex_groups: return []
    gi = char.vertex_groups[name].index
    return [v.index for v in char.data.vertices if any(g.group == gi and g.weight > w for g in v.groups)]
def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); ob = char.evaluated_get(dg); me = ob.to_mesh(); return ob, me
def centroid(ob, me, idx): return sum((ob.matrix_world @ me.vertices[i].co for i in idx), Vector()) / max(1, len(idx))
G_HIPS, G_RH, G_LH = group('Hips', .5), group('RightHand', .5), group('LeftHand', .5)

def mat(name, rgb):
    m = bpy.data.materials.new(name); m.diffuse_color = (*rgb, 1); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*rgb, 1); return m
def prim(kind, m, **kw):
    getattr(bpy.ops.mesh, 'primitive_%s_add' % kind)(**kw); o = bpy.context.object; o.data.materials.append(m); return o
def join(parts):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); o = bpy.context.object
    sc.cursor.location = (0, 0, 0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR'); return o
def blade(m, w, l, z0, bend=0.0, wave=0.0, taper=True):
    b = prim('cube', m, size=1, location=(0, 0, z0 + l / 2)); b.scale = (.012, w, l); bpy.ops.object.transform_apply(scale=True)
    for v in b.data.vertices:
        t = (v.co.z - z0) / l
        if taper and t > .8: v.co.y *= max(0.05, (1 - t) / .2)
        v.co.y += bend * t * t + wave * math.sin(t * math.pi * 3)
    return b

WOOD, IRON, RED, GOLD = mat('wood', (.2, .14, .09)), mat('iron', (.16, .17, .18)), mat('red', (.62, .1, .07)), mat('gold', (.55, .42, .15))
weapons = []                                                   # (物体, 手的网格组, 手骨名, 轴)
def axis(a): return Euler({'z': (0, 0, 0), '-z': (math.pi, 0, 0), 'x': (0, math.pi / 2, 0), '-x': (0, -math.pi / 2, 0), 'y': (-math.pi / 2, 0, 0), '-y': (math.pi / 2, 0, 0)}[a]).to_matrix().to_4x4()
if WPN == 'glaive':   # 青龙偃月刀：杆 2.3 米，头上一片宽大的弯刀，刀下一撮红缨
    w = join([prim('cylinder', WOOD, radius=.022, depth=2.3, vertices=10, location=(0, 0, .55)),
              blade(IRON, .3, .72, 1.6, bend=.22), prim('uv_sphere', RED, radius=.06, segments=8, ring_count=6, location=(0, .02, 1.6))])
    weapons.append((w, G_RH, 'RightHand', AX))
elif WPN == 'snake':  # 丈八蛇矛：杆 2.8 米，矛头弯弯曲曲像蛇
    w = join([prim('cylinder', WOOD, radius=.02, depth=2.8, vertices=10, location=(0, 0, .7)),
              blade(IRON, .07, .5, 2.08, wave=.035), prim('uv_sphere', RED, radius=.055, segments=8, ring_count=6, location=(0, 0, 2.06))])
    weapons.append((w, G_RH, 'RightHand', AX))
elif WPN == 'twin':   # 双股剑：两手各一把，剑身 0.75 米，金色护手
    for hand, grp, ax in (('RightHand', G_RH, AX), ('LeftHand', G_LH, LAX)):
        w = join([blade(IRON, .05, .75, .1), prim('cube', GOLD, size=1, location=(0, 0, .08), scale=(.03, .15, .025)),
                  prim('cylinder', WOOD, radius=.016, depth=.2, vertices=8, location=(0, 0, -.03))])
        weapons.append((w, grp, hand, ax))

# 披风：在静止姿势下量出两肩和后背的位置，做一块往下展开的布
cape = None
if CAPE:
    arm.data.pose_position = 'REST'; bpy.context.view_layer.update()
    ob, me = evaluated()
    ls, rs = centroid(ob, me, group('LeftShoulder', .3) or group('LeftArm', .5)), centroid(ob, me, group('RightShoulder', .3) or group('RightArm', .5))
    zs = (ls.z + rs.z) / 2; ys = [ (ob.matrix_world @ v.co).y for v in me.vertices if abs((ob.matrix_world @ v.co).z - zs) < .06 ]
    back = min(ys) - .035                                       # 人转过身，后背朝 -Y（镜头这边）
    tor = [ob.matrix_world @ me.vertices[i].co for i in (group('Spine02', .4) or group('Spine01', .4))]   # 上半身躯干：披风和它一样宽
    xs = [p.x for p in tor]; cx = sum(xs) / len(xs); half = (max(xs) - min(xs)) / 2 * .9; L = zs * .82
    ob.to_mesh_clear()
    nx, ny = 10, 14
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=nx, y_subdivisions=ny, size=1); cape = bpy.context.object
    for v in cape.data.vertices:
        u, t = v.co.x + .5, .5 - v.co.y                           # u 横向 0..1，t 往下 0..1
        wdt = half * (1 + .6 * t); v.co = Vector((cx + (u - .5) * 2 * wdt, back - .12 * t * t, zs + .02 - L * t))
    cm = mat('cape', CAPE); cape.data.materials.append(cm)
    if EDGE:                                                     # 两边和下摆镶一道边
        cape.data.materials.append(mat('edge', EDGE))
        for poly in cape.data.polygons:
            us = [(cape.data.vertices[i].co.x - cx) / max(1e-6, half * (1 + .6 * (zs + .02 - cape.data.vertices[i].co.z) / L)) for i in poly.vertices]
            ts = [(zs + .02 - cape.data.vertices[i].co.z) / L for i in poly.vertices]
            if max(abs(u) for u in us) > .82 or max(ts) > .9: poly.material_index = 1
    pin = cape.vertex_groups.new(name='pin'); sp = cape.vertex_groups.new(name='Spine02')
    for v in cape.data.vertices:
        t = round((zs + .02 - v.co.z) / L * ny)
        sp.add([v.index], 1.0, 'REPLACE')
        if t <= 1: pin.add([v.index], 1.0 if t == 0 else .7, 'REPLACE')
    cape.parent = arm; cape.matrix_parent_inverse = arm.matrix_world.inverted()
    am = cape.modifiers.new('arm', 'ARMATURE'); am.object = arm
    cl = cape.modifiers.new('cloth', 'CLOTH'); s = cl.settings
    s.quality = 8; s.mass = .25; s.tension_stiffness = 12; s.compression_stiffness = 12; s.bending_stiffness = .2; s.air_damping = 1.2
    s.vertex_group_mass = 'pin'
    cl.collision_settings.use_collision = True; cl.collision_settings.distance_min = .012
    cl.point_cache.frame_start, cl.point_cache.frame_end = 0, F1
    char.modifiers.new('coll', 'COLLISION'); char.collision.thickness_outer = .02
    bpy.ops.object.effector_add(type='WIND', location=(0, 1.5, 1.2)); wind = bpy.context.object
    wind.rotation_euler = Vector((.35, -1, .2)).normalized().to_track_quat('Z', 'Y').to_euler()
    wind.field.strength = WIND; wind.field.noise = 1.6; wind.field.flow = .4
    arm.data.pose_position = 'POSE'; bpy.context.view_layer.update()

sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_object_outline = True; sh.object_outline_color = (.08, .07, .06)
if opt.get('light') == 'studio':                              # 10-24 用户嫌城头武将看不清：打立体光加凹陷阴影，衣甲有明暗
    sh.light = 'STUDIO'; sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.cavity_ridge_factor = 1.2; sh.cavity_valley_factor = 1.4
sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = SIZE; sc.render.resolution_percentage = 100
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = OSCALE
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
elev = math.radians(35); dist = 10; CAM0 = Vector((0, -dist * math.cos(elev), .85 + dist * math.sin(elev)))
cam.rotation_euler = (math.radians(90) - elev, 0, 0)
pbs = {h: arm.pose.bones[h] for _, _, h, _ in weapons}
picks = {round(F0 + (F1 - F0) * i / N): i for i in range(N)}
for f in range(0, F1 + 1):                                     # 布料要一帧一帧往前推
    sc.frame_set(f)
    for w, grp, h, ax in weapons:
        ob, me = evaluated(); hand = centroid(ob, me, grp); ob.to_mesh_clear()
        if ACT in CARRY:
            v = Vector(CARRY[ACT]); v.x *= -1 if h == 'LeftHand' else 1
            rot = v.normalized().to_track_quat('Z', 'Y').to_matrix().to_4x4()
        else: rot = (arm.matrix_world @ pbs[h].matrix).to_quaternion().to_matrix().to_4x4() @ axis(ax)
        w.matrix_world = Matrix.Translation(hand) @ rot
    if f in picks:
        ob, me = evaluated(); hip = centroid(ob, me, G_HIPS); ob.to_mesh_clear()
        cam.location = CAM0 + Vector((hip.x, hip.y, 0)); bpy.context.view_layer.update()
        sc.render.filepath = os.path.join(out, '%s_%02d.png' % (ACT, picks[f])); bpy.ops.render.render(write_still=True)
print('渲完', ACT, out)
