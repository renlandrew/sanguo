# 以最终人马模型留正、侧、背视图；用户指定马替换最初概念图中的马后，以实装模型为准。
import bpy, sys, os
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scene_lighting import setup_lighting
source, out = sys.argv[sys.argv.index('--')+1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(source))
sc=bpy.context.scene; sc.frame_set(1)
arm=bpy.data.objects['HorseRig']; arm.data.pose_position='REST'; arm.location=(0,0,0)
setup_lighting(sc, {'light':'lit','key':'2.8','rim':'4','amb':'.05'})
sc.render.film_transparent=True; sc.render.resolution_x=sc.render.resolution_y=768; sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGBA'
bpy.ops.object.camera_add(); cam=bpy.context.object; cam.data.type='ORTHO'; cam.data.ortho_scale=3.6; sc.camera=cam
os.makedirs(out, exist_ok=True)
for name, pos in [('front',(0,-10,1.35)),('side',(-10,0,1.35)),('back',(0,10,1.35))]:
    cam.location=pos; cam.rotation_euler=(Vector((0,0,1.35))-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=os.path.abspath(os.path.join(out,'qibing_'+name+'.png')); bpy.ops.render.render(write_still=True)
print('最终人马三视图已渲染')
