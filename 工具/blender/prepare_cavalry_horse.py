# 用用户提供的独立马模型制作 Rigify 四足蒙皮；保留原模型，不调用 Meshy。
# Blender -b -P prepare_cavalry_horse.py -- horse.glb horse-rig.blend
import bpy,math,json,sys,os
args=sys.argv[sys.argv.index('--')+1:]
source,out=args[:2]
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(source))
horse=bpy.context.selected_objects[0];horse.name='Horse';horse.location.z=-min(v.co.z for v in horse.data.vertices)
bpy.context.view_layer.objects.active=horse;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.001);bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT')
mod=horse.modifiers.new('游戏减面','DECIMATE');mod.ratio=21000/len(horse.data.polygons);bpy.ops.object.modifier_apply(modifier=mod.name)
# 原始扫描网格在两腿与尾毛间有薄膜，静止时不明显，运动会拉成长三角。
# 只去掉低于腹部、跨身体中线的连接面，保留四腿各自外表面。
import bmesh
bm=bmesh.new();bm.from_mesh(horse.data)
bad=[]
for f in bm.faces:
 ps=[v.co for v in f.verts]
 if max(p.z for p in ps)<.78 and min(p.x for p in ps)<0<max(p.x for p in ps):bad.append(f)
bmesh.ops.delete(bm,geom=bad,context='FACES');bm.to_mesh(horse.data);bm.free()
print('移除腿间薄膜',len(bad))
for p in horse.data.polygons:p.use_smooth=True
# 保留贴图，取消 Meshy 导出附带的自发光，让光照来自统一灯光。
for m in horse.data.materials:
 if m and m.use_nodes:
  bs=m.node_tree.nodes.get('Principled BSDF')
  if bs:
   for name in ['Emission Color','Emission']:
    if name in bs.inputs:
     for l in list(bs.inputs[name].links):m.node_tree.links.remove(l)
   if 'Emission Strength' in bs.inputs:bs.inputs['Emission Strength'].default_value=0
   # 马毛和皮鞍不应像金属。
   for l in list(bs.inputs['Metallic'].links):m.node_tree.links.remove(l)
   bs.inputs['Metallic'].default_value=0
   bs.inputs['Roughness'].default_value=.72
bpy.ops.preferences.addon_enable(module='rigify')
from rigify.metarigs.Animals import horse as template
bpy.ops.object.armature_add();arm=bpy.context.object;arm.name='HorseRig'
bpy.ops.object.mode_set(mode='EDIT');arm.data.edit_bones.remove(arm.data.edit_bones[0]);bpy.ops.object.mode_set(mode='OBJECT');template.create(arm)
# 模板的四蹄和颈部按这匹短身战马重新对齐。
bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for b in arm.data.edit_bones:
 for a in ['head','tail']:
  p=getattr(b,a).copy();p.x*=1.18;p.y=p.y*.68+.12;p.z*=.94;setattr(b,a,p)
# 分开四条腿，沿模型当前蹄位布置关节。
chains={}
for side,sg in [('L',1),('R',-1)]:
 for front,names,ys,zs in [(True,['upper_arm','forearm','forefoot','f_toe','f_hoof'],[-.29,-.23,-.23,-.28,-.31,-.34],[1.03,.69,.37,.17,.08,.025]),(False,['thigh','lower_leg','hind_foot','r_toe','r_hoof'],[.56,.50,.66,.71,.69,.65],[1.13,.80,.47,.19,.08,.025])]:
  pts=[Vector((sg*(.12 if front else .13),y,z)) for y,z in zip(ys,zs)]
  for i,n in enumerate(names):
   b=arm.data.edit_bones[n+'.'+side];b.head=pts[i];b.tail=pts[i+1];b.roll=0
  chains[('front' if front else 'hind')+'.'+side]=[n+'.'+side for n in names]
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT');horse.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=arm
try:bpy.ops.object.parent_set(type='ARMATURE_AUTO');print('AUTO_WEIGHTS_OK')
except RuntimeError as e:print('AUTO_WEIGHTS_ERROR',str(e))
# 热权重对鞍带等断开的网格失败时，用四足分区距离权重补齐，避免零权重和串腿。
for g in list(horse.vertex_groups):horse.vertex_groups.remove(g)
from mathutils.geometry import intersect_point_line
def distance(p,b):
 q,t=intersect_point_line(p,b.head_local,b.tail_local);t=max(0,min(1,t));return (p-b.head_local.lerp(b.tail_local,t)).length
for v in horse.data.vertices:
 p=v.co;side='L' if p.x>=0 else 'R';chain=None
 # 尾巴、马镫和鞍带优先排除，不能按前后坐标误判成马腿。
 if p.y>.85 or (p.y>.70 and abs(p.x)<.06 and p.z<1.15):
  weights={'tail.003':1}
 else:
  if p.z<1.02 and p.y<0:chain=chains['front.'+side]
  elif p.z<1.12 and p.y>.34:chain=chains['hind.'+side]
  if chain:
   ds=sorted((distance(p,arm.data.bones[n]),n) for n in chain)[:2]
   top=1.02 if p.y<0 else 1.12
   blend=max(0,min(1,(top-p.z)/.23))*max(0,min(1,(.24-ds[0][0])/.10))
   if abs(p.x)>.23:blend*=max(0,1-(abs(p.x)-.23)/.06)
   ww=[1/(d+.035)**3 for d,n in ds];sw=sum(ww)
   weights={n:w/sw*blend for (d,n),w in zip(ds,ww)};weights['spine.003']=1-blend
  elif p.y<-.48 and p.z>1.0:weights={'neck.002':1}
  else:weights={'spine.003':1}
 for n,w in weights.items():
  if w>0:(horse.vertex_groups.get(n) or horse.vertex_groups.new(name=n)).add([v.index],w,'REPLACE')
arm['chains']=json.dumps(chains);arm['source']='Blender Rigify Animals/horse';arm['saddle']=[0,.1,1.25]
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
