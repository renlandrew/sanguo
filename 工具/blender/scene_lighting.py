# 步兵和骑兵共用真光照，避免参数或色彩管理跑偏。
import bpy, math

def setup_lighting(sc, opt):
    if opt.get('light') == 'lit':
        # light=lit（10-28 用户：「黄巾军感觉有点像纸片，尤其是骑兵」）：Eevee 真光照——左上主光、背后轮廓光、天光补暗面，环境光遮蔽 + 软阴影，不描边；
        # 平涂（Workbench）只有贴图颜色，侧面一片平，所以看着像纸片。Blender 4.2 起引擎叫 BLENDER_EEVEE_NEXT
        for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
            try: sc.render.engine = eng; break
            except TypeError: pass
        ee = sc.eevee
        for k, v in (('use_gtao', True), ('gtao_distance', .4), ('use_soft_shadows', True), ('taa_render_samples', 32), ('use_shadows', True)):
            if hasattr(ee, k): setattr(ee, k, v)
        def lamp(name, kind, energy, rot, color=(1, 1, 1), size=None):
            ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
            if size is not None and hasattr(ld, 'angle'): ld.angle = size
            ob = bpy.data.objects.new(name, ld); ob.rotation_euler = [math.radians(a) for a in rot]; sc.collection.objects.link(ob); return ob
        lamp('key', 'SUN', float(opt.get('key', 3.2)), (50, -10, -35), (1, .96, .88), .15)       # 主光：左上前方，暖
        lamp('rim', 'SUN', float(opt.get('rim', 2.4)), (-120, 0, 160), (.85, .9, 1))             # 轮廓光：背后上方，冷，勾出边
        w = sc.world or bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
        bg = w.node_tree.nodes.get('Background'); bg.inputs[0].default_value = (.55, .52, .48, 1); bg.inputs[1].default_value = float(opt.get('amb', .6))   # 天光补暗面
        for vt in ('AgX', 'Filmic'):                                                 # 亮部渐变不截断（Standard 一过曝就成一片平，10-28 第一轮对比 B、C 看不出差别）
            try: sc.view_settings.view_transform = vt; break
            except TypeError: pass
        try: sc.view_settings.look = opt.get('look', 'AgX - Medium High Contrast' if sc.view_settings.view_transform == 'AgX' else 'Medium High Contrast')
        except TypeError: pass
    else:
        sc.render.engine = 'BLENDER_WORKBENCH'
        sh = sc.display.shading; sh.light = 'STUDIO' if opt.get('light') == 'studio' else 'FLAT';   # light=studio：有明暗体积（10-26 去水墨）
        sh.color_type = 'TEXTURE'; sh.show_object_outline = True; sh.object_outline_color = (.08, .07, .06)
