# 第 26 关冲车：固定机位、透明底，分别渲染推行、撞击和毁坏。
import bpy, math, os
from mathutils import Vector
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..')); OUT=os.path.join(R,'原型/img/ram_blender_frames_v2'); os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene

def mat(n,c,metal=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.7;return m
wood=mat('深棕木',(.24,.105,.04)); edge=mat('木材边缘',(.38,.19,.075)); iron=mat('包铁',(.12,.13,.14),.5); skin=mat('湿牛皮顶棚',(.39,.31,.20)); rope=mat('粗麻绳',(.43,.29,.13)); red=mat('汉军红绑带',(.36,.035,.025))
# 粗尺度色差表现木纹和湿牛皮，不添加密集斑点。
def broad_surface(m,c1,c2,scale,roughness):
 nodes=m.node_tree.nodes; links=m.node_tree.links;p=nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=roughness
 noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=1;noise.inputs['Roughness'].default_value=.35
 ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=(*c1,1);ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(*c2,1)
 links.new(noise.outputs['Fac'],ramp.inputs['Fac']);links.new(ramp.outputs['Color'],p.inputs['Base Color'])
broad_surface(wood,(.12,.047,.015),(.33,.16,.05),3,.7)
broad_surface(skin,(.09,.055,.03),(.22,.14,.075),2.5,.88)   # 10-29：原来浅色又亮（粗糙度 .32）渲出来近乎白色，战场上像个白盒子；改成深褐、哑光的湿牛皮
def box(n,loc,dim,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=dim;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);be=o.modifiers.new('边缘','BEVEL');be.width=.025;be.segments=2;o.modifiers.new('法线','WEIGHTED_NORMAL');return o
def rod(n,a,b,r,m,parent=None):
 a,b=Vector(a),Vector(b);v=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.name=n;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();o.data.materials.append(m)
 if parent:o.parent=parent;o.matrix_parent_inverse=parent.matrix_world.inverted()
 return o
# 冲车前进方向为 +Y，摄影机在 -Y 一侧，看见车尾。
for x in [-.72,.72]:
 for y in [-.72,.92]:box('立柱',(x,y,1.12),(.13,.13,1.5),wood)
for x in [-.72,.72]:
 for z in [.44,1.78]:box('纵梁',(x,.10,z),(.14,1.9,.14),wood)
for y in [-.72,.92]:
 for z in [.46,1.77]:box('横梁',(0,y,z),(1.56,.13,.13),wood)
# 车尾横推杆突出车架，供四人双手扶持。
rod('车尾推杆',(-1.04,-1.32,1.0),(1.04,-1.32,1.0),.06,edge)
for x in [-.65,.65]: rod('推杆连接', (x,-1.32,1.0),(x,-.72,.78),.045,wood)
# 双坡顶棚采用大块连续湿牛皮，不使用密集花纹。
verts=[(-.98,-.92,1.78),(0,-.92,2.17),(.98,-.92,1.78),(-.98,1.12,1.78),(0,1.12,2.17),(.98,1.12,1.78)]
me=bpy.data.meshes.new('双坡牛皮');me.from_pydata(verts,[],[(0,3,4,1),(1,4,5,2)]);me.update();ob=bpy.data.objects.new('湿牛皮棚',me);sc.collection.objects.link(ob);ob.data.materials.append(skin)
# 牛皮为几幅大块皮料，用少量接缝和边缘表现。
for y in [-.45,.35,.92]:
 rod('牛皮接缝',(-.96,y,1.79),(0,y,2.18),.008,rope,ob);rod('牛皮接缝',(0,y,2.18),(.96,y,1.79),.008,rope,ob)
rod('棚脊',(0,-.92,2.18),(0,1.12,2.18),.018,wood,ob)
for x in [-.72,.72]:
 for y in [-.55,.76]:
  bpy.ops.object.empty_add(location=(x,y,.30));wheel=bpy.context.object;wheel.name='实心车轮'
  # 实心木轮与铁箍都随车轴旋转，车轮有少量木条便于看见转动。
  bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.30,depth=.13,location=(x,y,.30),rotation=(0,math.pi/2,0));o=bpy.context.object;o.name='实心木轮';o.data.materials.append(wood);o.parent=wheel;o.matrix_parent_inverse=wheel.matrix_world.inverted()
  bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=8,major_radius=.29,minor_radius=.025,location=(x,y,.30),rotation=(0,math.pi/2,0));o=bpy.context.object;o.name='车轮铁箍';o.data.materials.append(iron);o.parent=wheel;o.matrix_parent_inverse=wheel.matrix_world.inverted()
  for angle in [0,math.pi/2]:
   dy=.25*math.cos(angle);dz=.25*math.sin(angle);rod('轮面木纹',(x-.072,y-dy,.30-dz),(x-.072,y+dy,.30+dz),.014,edge,wheel);rod('轮面木纹',(x+.072,y-dy,.30-dz),(x+.072,y+dy,.30+dz),.014,edge,wheel)
  wheel['wheel']=True
# 吊挂撞木：旋转中心在顶棚下，撞击时作前后摆动。
bpy.ops.object.empty_add(location=(0,.05,1.72));swing=bpy.context.object;swing.name='撞木摆动轴'
for y in [-.43,.53]: rod('吊绳',(0,y,1.70),(0,y,1.13),.025,rope,swing)
rod('撞木',(0,-.90,1.13),(0,1.15,1.13),.15,wood,swing);rod('撞木铁头',(0,1.13,1.13),(0,1.30,1.13),.17,iron,swing)
# 导入已有西凉兵步行动作，四名士兵放在车尾；动作素材不是汉军专门模型。
bpy.ops.import_scene.gltf(filepath=os.path.join(R,'美术/西凉兵/v2/绑骨/basic_animations_walking_glb_url.glb'))
rig=next(o for o in bpy.context.selected_objects if o.type=='ARMATURE'); meshes=[o for o in bpy.context.selected_objects if o.type=='MESH']; walk=rig.animation_data.action
for j,x in enumerate([-.66,-.22,.22,.66]):
 if j==0:r=rig;parts=meshes
 else:
  r=rig.copy();r.data=rig.data.copy();sc.collection.objects.link(r);parts=[]
  for src in meshes:
   m=src.copy();m.data=src.data;sc.collection.objects.link(m);m.parent=r
   for mod in m.modifiers:
    if mod.type=='ARMATURE':mod.object=r
   parts.append(m)
 mount=bpy.data.objects.new('推车士兵位',None);sc.collection.objects.link(mount);mount.location=(x,-.95-(j%2)*.06,.04);mount.rotation_euler=(math.radians(-24),0,math.pi);r.parent=mount;r.name=f'推车士兵{j+1}'
 r.animation_data_create();r.animation_data.action=None;track=r.animation_data.nla_tracks.new();strip=track.strips.new('推行步态',1,walk);strip.scale=8/(walk.frame_range[1]-walk.frame_range[0]);strip.repeat=2;strip.frame_start=1-j*.5
 # 用 IK 约束让每名士兵的前臂朝向车尾推杆，步行动画仍驱动腿部。
 for side,dx in [('Left',-.20),('Right',.20)]:
  target=bpy.data.objects.new(f'推杆握点_{j}_{side}',None);sc.collection.objects.link(target);target.location=(x+dx,-1.32,1.00)
  c=r.pose.bones[side+'ForeArm'].constraints.new('IK');c.name='双手扶推杆';c.target=target;c.chain_count=2;c.use_stretch=False

# 统一灯光和董卓车驾机位。
sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.world=bpy.data.worlds.new('环境');sc.world.color=(.18,.18,.18);sc.render.film_transparent=True
sc.render.resolution_x=sc.render.resolution_y=384;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='AgX';sc.render.fps=12
def light(n,loc,power):
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=5;o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,.5,1))-o.location).to_track_quat('-Z','Y').to_euler()
light('主光',(2,-5,7),900);light('轮廓光',(-4,4,5),650)
bpy.ops.object.camera_add(location=(3,-10,7.2));cam=bpy.context.object;cam.rotation_euler=(Vector((0,.55,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5.25;sc.camera=cam
# 统一时间轴：1–8 推行，9–16 撞击；推行轮转一周期，撞木小幅摆动。
for wheel in [o for o in sc.objects if o.get('wheel')]:
 for f in range(1,10):wheel.rotation_euler.x=(f-1)*math.tau/8;wheel.keyframe_insert('rotation_euler',frame=f)
 for f in (10,16):wheel.rotation_euler.x=math.tau;wheel.keyframe_insert('rotation_euler',frame=f)
for f in range(1,9):swing.rotation_euler.x=.035*math.sin(math.tau*(f-1)/8);swing.keyframe_insert('rotation_euler',frame=f)
for f,v in [(9,0),(10,-.08),(11,-.30),(12,-.43),(13,-.22),(14,.38),(15,.18),(16,0)]:swing.rotation_euler.x=v;swing.keyframe_insert('rotation_euler',frame=f)
sc.frame_start=1;sc.frame_end=16;sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=os.path.join(R,'美术/冲车/冲车_细化.blend'))
for prefix,start in [('push',1),('hit',9)]:
 for j in range(8):sc.frame_set(start+j);sc.render.filepath=os.path.join(OUT,f'{prefix}_{j:02}.png');bpy.ops.render.render(write_still=True)
# 毁坏图：移除四名士兵，倾倒棚顶，撞木下落，展示断裂木架。
sc.frame_set(1)
for o in sc.objects:
 if o.name.startswith('推车士兵位'):o.hide_render=True
 if o.parent and (o.parent.name.startswith('推车士兵') or (o.parent.parent and o.parent.parent.name.startswith('推车士兵位'))):o.hide_render=True
roofob=bpy.data.objects.get('湿牛皮棚');roofob.rotation_euler.y=.38;roofob.location.z=-.7
swing.rotation_euler.x=.20;swing.location.z=-.20
for o in sc.objects:
 if o.name.startswith('立柱') and o.location.x>0:o.rotation_euler.y=.65
sc.render.filepath=os.path.join(OUT,'destroyed.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(R,'美术/冲车/冲车_毁坏_细化.blend'))
print('RAM_COMPLETE')
