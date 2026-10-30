# 基于用户选定的完整插画，用 Blender 网格形变和材质坐标制作 8 帧循环。
import bpy, math, os
R=os.path.abspath(os.path.join(os.path.dirname(__file__),'../..'));OUT=os.path.join(R,'原型/img/ram_2d_walk');os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
N=128;verts=[];faces=[]
for y in range(N+1):
 for x in range(N+1):verts.append((x/N-.5,.5-y/N,0))
for y in range(N):
 for x in range(N):
  a=y*(N+1)+x;faces.append((a,a+N+1,a+N+2,a+1))
me=bpy.data.meshes.new('冲车画稿网格');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('冲车画稿与行走形变',me);sc.collection.objects.link(o)
uv=me.uv_layers.new(name='原图坐标')
for poly in me.polygons:
 for li in poly.loop_indices:
  v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v.x+.5,v.y+.5)
o.shape_key_add(name='原始');feet=[(205,1080,0),(306,990,math.pi),(420,1090,math.pi),(520,990,0),(690,1070,0),(735,1120,math.pi),(940,1080,math.pi),(1037,1160,0)]
for frame in range(8):
 key=o.shape_key_add(name=f'走路_{frame:02}');t=math.tau*frame/8
 for j,v in enumerate(verts):
  px=(v[0]+.5)*1254;py=(.5-v[1])*1254;dx=dy=0
  for cx,cy,phase in feet:
   weight=math.exp(-((px-cx)/48)**2-((py-cy)/105)**2)*max(0,min(1,(py-885)/100))
   dx+=weight*10*math.sin(t+phase);dy+=weight*13*max(0,math.sin(t+phase))
  key.data[j].co=(v[0]+dx/1254,v[1]+dy/1254,0)
 for f in range(1,10):key.value=1.0 if (f-1)%8==frame else 0.0;key.keyframe_insert(data_path='value',frame=f)
# 材质中按椭圆轮面转动原画纹理；车身与轮廓仍是原图像素。
m=bpy.data.materials.new('原画与轮面转动');m.use_nodes=True;nodes=m.node_tree.nodes;nodes.clear();links=m.node_tree.links
uvn=nodes.new('ShaderNodeUVMap'); current=uvn.outputs['UV']; wheel_masks=[]
for label,cx,cy,rx,ry in [('左轮',195,729,20,85),('右轮',1040,765,20,88)]:
 center=(cx/1254,1-cy/1254,0);sub=nodes.new('ShaderNodeVectorMath');sub.operation='SUBTRACT';links.new(uvn.outputs['UV'],sub.inputs[0]);sub.inputs[1].default_value=center
 norm=nodes.new('ShaderNodeVectorMath');norm.operation='MULTIPLY';links.new(sub.outputs['Vector'],norm.inputs[0]);norm.inputs[1].default_value=(1254/rx,1254/ry,1)
 length=nodes.new('ShaderNodeVectorMath');length.operation='LENGTH';links.new(norm.outputs['Vector'],length.inputs[0]);mask=nodes.new('ShaderNodeMath');mask.operation='LESS_THAN';links.new(length.outputs['Value'],mask.inputs[0]);mask.inputs[1].default_value=.88;wheel_masks.append(mask.outputs[0])
 rotate=nodes.new('ShaderNodeVectorRotate');rotate.rotation_type='AXIS_ANGLE';rotate.inputs['Axis'].default_value=(0,0,1);links.new(norm.outputs['Vector'],rotate.inputs['Vector'])
 for f in range(1,10):rotate.inputs['Angle'].default_value=math.tau*(f-1)/8;rotate.inputs['Angle'].keyframe_insert('default_value',frame=f)
 den=nodes.new('ShaderNodeVectorMath');den.operation='MULTIPLY';links.new(rotate.outputs['Vector'],den.inputs[0]);den.inputs[1].default_value=(rx/1254,ry/1254,1)
 add=nodes.new('ShaderNodeVectorMath');add.operation='ADD';links.new(den.outputs['Vector'],add.inputs[0]);add.inputs[1].default_value=center
 mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';links.new(mask.outputs[0],mix.inputs[0]);links.new(current,mix.inputs[1]);links.new(add.outputs['Vector'],mix.inputs[2]);current=mix.outputs[0]
tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(os.path.join(R,'美术/冲车/二维原稿/ram_2d.png'),check_existing=True);tex.image.pack();tex.extension='CLIP';links.new(current,tex.inputs['Vector'])
# 图外中灰抠出透明，轮上同色区可能需要人工复核。
diff=nodes.new('ShaderNodeVectorMath');diff.operation='DISTANCE';links.new(tex.outputs['Color'],diff.inputs[0]);diff.inputs[1].default_value=(.205,.205,.205)
cut=nodes.new('ShaderNodeMath');cut.operation='GREATER_THAN';links.new(diff.outputs['Value'],cut.inputs[0]);cut.inputs[1].default_value=.03
alpha=cut.outputs[0]
for wheel_mask in wheel_masks:
 keep=nodes.new('ShaderNodeMath');keep.operation='MAXIMUM';links.new(alpha,keep.inputs[0]);links.new(wheel_mask,keep.inputs[1]);alpha=keep.outputs[0]
transparent=nodes.new('ShaderNodeBsdfTransparent');em=nodes.new('ShaderNodeEmission');links.new(tex.outputs['Color'],em.inputs['Color']);blend=nodes.new('ShaderNodeMixShader');links.new(alpha,blend.inputs[0]);links.new(transparent.outputs[0],blend.inputs[1]);links.new(em.outputs[0],blend.inputs[2]);out=nodes.new('ShaderNodeOutputMaterial');links.new(blend.outputs[0],out.inputs['Surface']);o.data.materials.append(m)
sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.world=bpy.data.worlds.new('世界');sc.world.color=(.1,.1,.1);sc.render.film_transparent=True;sc.render.resolution_x=sc.render.resolution_y=384;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard';sc.render.fps=8
bpy.ops.object.camera_add(location=(0,0,3));cam=bpy.context.object;cam.rotation_euler=(0,0,0);cam.data.type='ORTHO';cam.data.ortho_scale=1;sc.camera=cam
sc.frame_start=1;sc.frame_end=9;sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=os.path.join(R,'美术/冲车/二维原稿/ram_2d_行走.blend'))
for i in range(8):sc.frame_set(i+1);sc.render.filepath=os.path.join(OUT,f'walk_{i:02}.png');bpy.ops.render.render(write_still=True)
print('RAM_2D_WALK_COMPLETE')
