# 将独立骑手装到用户指定的马，烘焙 8 帧四足循环，导出带动作 GLB。
# Blender -b -P assemble_cavalry.py -- horse-rig.blend rider.glb qibing.glb
import bpy, math, sys, os
from mathutils import Vector
horse_file, rider_file, out = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(horse_file))
arm = bpy.data.objects['HorseRig']; horse = bpy.data.objects['Horse']
old = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.abspath(rider_file))
parts = [o for o in bpy.data.objects if o not in old and o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]; bpy.ops.object.join(); rider = bpy.context.object; rider.name = 'YellowTurbanRider'
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=.0001); bpy.ops.object.mode_set(mode='OBJECT')
# 人马合计不超过三万面，给鞍布留出少量余量。
remaining = 29900 - len(horse.data.polygons)
if len(rider.data.polygons) > remaining:
    dec = rider.modifiers.new('骑手减面', 'DECIMATE'); dec.ratio = remaining / len(rider.data.polygons); bpy.ops.object.modifier_apply(modifier=dec.name)
for p in rider.data.polygons: p.use_smooth = True
for m in rider.data.materials:
    if m and m.use_nodes:
        bs = m.node_tree.nodes.get('Principled BSDF')
        if bs:
            for key in ['Emission Color', 'Emission']:
                if key in bs.inputs:
                    for link in list(bs.inputs[key].links): m.node_tree.links.remove(link)
            if 'Emission Strength' in bs.inputs: bs.inputs['Emission Strength'].default_value = 0
            for link in list(bs.inputs['Metallic'].links): m.node_tree.links.remove(link)
            bs.inputs['Metallic'].default_value = .05
saddle = bpy.data.objects.new('SaddleMount', None); bpy.context.scene.collection.objects.link(saddle)
saddle.parent = arm; saddle.location = (0, .10, 1.40)
rider.parent = saddle; rider.location = (0, 0, 0); rider.scale = (1.25,) * 3
clothmat = bpy.data.materials.new('黄巾鞍布'); clothmat.diffuse_color = (.82, .53, .06, 1); clothmat.use_nodes = True
bs = clothmat.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value = (.82, .53, .06, 1); bs.inputs['Roughness'].default_value = .85
for side in [-1, 1]:
    verts = []
    # 鞍布用宽褶和弧形下摆，不做硬纸板一样的矩形片。
    for j in range(6):
        y = -.19 + j * .12
        bottom = .90 + .07 * abs(j - 2.5) / 2.5
        for k in range(4):
            t = k / 3
            verts.append((side * (.30 + .025 * math.sin(j * 1.8) * t + .025 * math.sin(t * math.pi)), y, 1.29 * (1-t) + bottom*t))
    me = bpy.data.meshes.new('SaddleCloth'); me.from_pydata(verts, [], [(j*4+k, (j+1)*4+k, (j+1)*4+k+1, j*4+k+1) for j in range(5) for k in range(3)])
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new('YellowSaddleCloth', me); bpy.context.scene.collection.objects.link(ob); ob.data.materials.append(clothmat); ob.parent = arm
# 四足 FK：左右错相，前后腿有追赶相位；首尾同姿，骑手随鞍部起伏。
for i in range(8):
    phase = math.tau * i / 7
    for side, off in [('L', 0), ('R', math.pi)]:
        for names, shift in [(['upper_arm','forearm','forefoot','f_toe','f_hoof'], 0), (['thigh','lower_leg','hind_foot','r_toe','r_hoof'], math.pi*.6)]:
            t = phase + off + shift; sn = math.sin(t); cs = math.cos(t)
            for name, val in zip(names, [.45*sn, max(0,cs)*.55-.12, -.28*sn-max(0,cs)*.25, .10*sn, 0]):
                b = arm.pose.bones[name+'.'+side]; b.rotation_mode = 'XYZ'; b.rotation_euler.x = val; b.keyframe_insert('rotation_euler', frame=i+1)
    b = arm.pose.bones['neck.002']; b.rotation_mode = 'XYZ'; b.rotation_euler.x = .035*math.sin(phase*2); b.keyframe_insert('rotation_euler', frame=i+1)
    arm.location.z = 0; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); ob = horse.evaluated_get(dg); me = ob.to_mesh()
    low = min((ob.matrix_world @ v.co).z for v in me.vertices); ob.to_mesh_clear()
    arm.location.z = -low; arm.keyframe_insert('location', frame=i+1)
arm.animation_data.action.name = 'Gallop'
sc = bpy.context.scene; sc.frame_start = 1; sc.frame_end = 8; sc.render.fps = 24; sc.frame_set(1)
# 导出实际三角面数也必须不超过三万。
triangles = 0
for ob in [o for o in sc.objects if o.type == 'MESH']:
    ob.data.validate(clean_customdata=True); ob.data.calc_loop_triangles(); triangles += len(ob.data.loop_triangles)
if triangles > 30000: raise RuntimeError('人马合计超出三万三角面：%d' % triangles)
sc['mounted_height'] = 2.4; sc['pipeline'] = 'Rigify horse + Meshy rider, lit'; sc['triangles'] = triangles
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.splitext(out)[0]+'.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), export_format='GLB', export_animations=True, export_force_sampling=True, export_frame_range=True, export_extras=True)
print('骑兵导出', out, '三角面', triangles)
