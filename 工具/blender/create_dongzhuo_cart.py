# 董卓车驾：复用四足马匹与动作，构造车厢、车轮和顶棚；透明底渲染循环帧。
import bpy, math, os, sys
from mathutils import Vector
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'))
OUT=os.path.join(ROOT,'美术/董卓马车')
FRAMES=os.path.join(ROOT,'原型/img/cart_blender_frames')
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT,'素材/3d/qibing.blend'))
sc=bpy.context.scene
for name in ['YellowTurbanRider','SaddleMount','YellowSaddleCloth','YellowSaddleCloth.001']:
 ob=bpy.data.objects.get(name)
 if ob: bpy.data.objects.remove(ob,do_unlink=True)
rig=bpy.data.objects['HorseRig']; horse=bpy.data.objects['Horse']; action=rig.animation_data.action
# 两匹马共用网格与骨骼动作，错开半个步态周期；马的位置固定在车辕前。
rig2=rig.copy(); rig2.data=rig.data.copy(); sc.collection.objects.link(rig2); rig2.name='右马骨架'
for r, x in [(rig,-.48),(rig2,.48)]:
 mount=bpy.data.objects.new('马位',None);sc.collection.objects.link(mount);mount.location=(x,-.65,0);r.parent=mount
horse2=horse.copy(); horse2.data=horse.data; sc.collection.objects.link(horse2); horse2.name='右马'; horse2.parent=rig2
for mod in horse2.modifiers:
 if mod.type=='ARMATURE': mod.object=rig2
# 四拍慢走：四腿依次错相、减小步幅，两匹马稍微错开；每圈最后一帧回到首姿。
for r in (rig,rig2): r.animation_data_clear()
chains=[('upper_arm.L','forearm.L','forefoot.L',0),('thigh.R','lower_leg.R','hind_foot.R',math.pi/2),('upper_arm.R','forearm.R','forefoot.R',math.pi),('thigh.L','lower_leg.L','hind_foot.L',math.pi*1.5)]
for i in range(9):
 sc.frame_set(i+1);phase=math.tau*i/8
 for r,offset in ((rig,0),(rig2,math.pi/2)):
  for upper,knee,foot,shift in chains:
   q=phase+offset+shift; lift=max(0,math.cos(q))
   for name,val in ((upper,.22*math.sin(q)),(knee,.20*lift),(foot,-.12*math.sin(q)-.08*lift)):
    b=r.pose.bones[name];b.rotation_mode='XYZ';b.rotation_euler.x=val;b.keyframe_insert('rotation_euler',frame=i+1)
  r.location.z=0
 bpy.context.view_layer.update()
 for r,h in ((rig,horse),(rig2,horse2)):
  ev=h.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh(); low=min((ev.matrix_world @ v.co).z for v in me.vertices); ev.to_mesh_clear()
  r.location.z=-low;r.keyframe_insert('location',frame=i+1)
 bpy.context.view_layer.update()
# 车厢和车轮为独立物件，材质采用红木、暗金与深色车轮。
def mat(name,c,metal=0,rough=.6):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough;return m
red=mat('朱红车厢',(.36,.045,.023)); gold=mat('暗金',(.55,.29,.06),.45,.36); wood=mat('车轮深木',(.12,.047,.018)); roof=mat('黄绢顶棚',(.71,.40,.075)); dark=mat('车辕',(.11,.055,.026))
def cube(name,loc,scale,material,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 if bevel: m=o.modifiers.new('边缘','BEVEL');m.width=bevel;m.segments=2; o.modifiers.new('法线','WEIGHTED_NORMAL')
 return o
def rod(name,a,b,r,material,parent=None):
 a,b=Vector(a),Vector(b); d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=d.length,location=(a+b)*.5);o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(material)
 if parent: o.parent=parent; o.matrix_parent_inverse=parent.matrix_world.inverted()
 return o
cube('车厢', (0,1.55,1.28),(1.28,1.25,1.25),red)
cube('车架',(0,1.55,.62),(1.55,1.5,.14),wood)
# 车厢两侧的深红木门与框线，避免纯色箱体。
for side in [-1,1]:
 for yy in [1.25,1.86]:
  cube('红木门板',(side*.648,yy,1.29),(.025,.50,1.02),red,.006)
  for dy in [-.24,.24]: rod('门框',(side*.67,yy+dy,.78),(side*.67,yy+dy,1.8),.014,gold)
  for z in [.78,1.8]: rod('门框',(side*.67,yy-.24,z),(side*.67,yy+.24,z),.014,gold)

for x in [-.64,.64]:
 for y in [.93,2.17]: rod('车厢立柱',(x,y,.65),(x,y,1.95),.035,gold)
 for z in [.76,1.36,1.88]: rod('车厢横梁',(x,.93,z),(x,2.17,z),.025,gold)
for y in [.93,2.17]:
 for z in [.76,1.36,1.88]: rod('前后横梁',(-.64,y,z),(.64,y,z),.025,gold)
for x in [-.48,.48]: rod('车辕',(x,-.45,.63),(x,1.2,.63),.04,dark)
rod('顶棚立柱',(0,1.55,1.9),(0,1.55,2.45),.045,wood)
# 低圆顶的黄绢顶棚，参考原车驾的伞形顶。
bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=1.05,radius2=0,depth=.22,location=(0,1.55,2.43)); canopy=bpy.context.object;canopy.name='黄绢伞顶';canopy.scale.y=.83;canopy.data.materials.append(roof)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.07,location=(0,1.55,2.57));bpy.context.object.data.materials.append(gold)
for side in [-1,1]:
 x=side*.78; y=1.57; z=.55; bpy.ops.object.empty_add(location=(x,y,z));wheel=bpy.context.object;wheel.name='左轮' if side<0 else '右轮'
 bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=10,location=(x,y,z),major_radius=.49,minor_radius=.055,rotation=(0,math.pi/2,0));t=bpy.context.object;t.name='轮圈';t.data.materials.append(wood);t.parent=wheel;t.matrix_parent_inverse=wheel.matrix_world.inverted()
 for i in range(8):
  a=math.tau*i/8; rod('轮辐',(x,y,z),(x,y+.46*math.sin(a),z+.46*math.cos(a)),.027,gold,wheel)
 rod('轮毂',(x-.07,y,z),(x+.07,y,z),.09,wood,wheel)
 for frame in (1,9): wheel.rotation_euler.x=math.radians(45)*(frame-1)/8;wheel.keyframe_insert(data_path='rotation_euler',frame=frame)
# 慢走与轮转一圈八帧，首尾姿势相接。
sc.frame_start=1;sc.frame_end=9;sc.render.fps=12
sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.world=bpy.data.worlds.new('环境');sc.world.color=(.18,.18,.18)
sc.render.film_transparent=True;sc.render.resolution_x=384;sc.render.resolution_y=384;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='AgX'
def light(name,loc,energy,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,.5,1))-o.location).to_track_quat('-Z','Y').to_euler()
light('主光',(2,-5,7),900,5);light('轮廓光',(-4,4,5),650,4)
bpy.ops.object.camera_add(location=(3.0,-10,7.2));cam=bpy.context.object;cam.rotation_euler=(Vector((0,.55,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.25;sc.camera=cam
# 保留游戏绘画感：车厢以绘制素材贴到朝向机位的平面；马和车轮仍为真实三维动作。
for ob in sc.objects:
 if ob.type=='MESH' and ob.name.split('.')[0] in {'车厢','车架','红木门板','门框','车厢立柱','车厢横梁','前后横梁','顶棚立柱','黄绢伞顶'}: ob.hide_render=True
# 隐藏伞尖；图片里已有完整顶棚。
for ob in sc.objects:
 if ob.type=='MESH' and ob.name.startswith('Sphere'): ob.hide_render=True
image=bpy.data.images.load(os.path.join(OUT,'车厢_透明.png'),check_existing=True)
material=bpy.data.materials.new('车厢绘画贴图');material.use_nodes=True
nodes=material.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');mix=nodes.new('ShaderNodeMixShader');trans=nodes.new('ShaderNodeBsdfTransparent');em=nodes.new('ShaderNodeEmission');tex=nodes.new('ShaderNodeTexImage');tex.image=image
links=material.node_tree.links;links.new(tex.outputs['Color'],em.inputs['Color']);links.new(tex.outputs['Alpha'],mix.inputs[0]);links.new(trans.outputs[0],mix.inputs[1]);links.new(em.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
bpy.ops.mesh.primitive_plane_add(size=2,location=(0,1.30,1.62));plane=bpy.context.object;plane.name='绘画车厢';plane.rotation_euler=cam.rotation_euler;plane.scale=(1.25,1.57,1);plane.data.materials.append(material)
image.pack()

os.makedirs(OUT,exist_ok=True);os.makedirs(FRAMES,exist_ok=True)
sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'董卓车驾_步行.blend'))
for f in range(1,9):
 sc.frame_set(f);sc.render.filepath=os.path.join(FRAMES,f'{f-1:02d}.png');bpy.ops.render.render(write_still=True)
print('DONE CART')
