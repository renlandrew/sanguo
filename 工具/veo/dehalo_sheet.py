"""去掉 Veo 图集外面那圈纸色光晕，只留墨线（10-25 用户看张角：「背景白色有点太厚，可以改为那种墨色的烟？有点像之前我们做的青龙斩那种墨」）。
cut_generals.py 切图时 ink(halo=4) 在人外面垫了一圈纸色光晕（246,240,226，透明度 ≤ .55），城头武将靠它从城砖上托出来；敌将不需要，换成游戏里实时的墨烟。
做法：人身上（不透明）不动；半透明的像素里，发灰的按「离纸色多远、离墨色多近」拆出墨线那一份透明度，纸色那一份去掉；有颜色的（衣服边）不动。
原图先拷一份到 <备份目录>，再覆盖 原型/img/<名>.png。
用法：<media-venv>/bin/python 三国志/工具/veo/dehalo_sheet.py <名> <备份目录>
"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
name, bak = sys.argv[1], Path(sys.argv[2])
src = HERE.parents[1] / '原型' / 'img' / f'{name}.png'
bak.mkdir(parents=True, exist_ok=True); shutil.copy2(src, bak / src.name)
INK, PAPER = np.array([29, 26, 23], np.float32), np.array([246, 240, 226], np.float32)
a = np.asarray(Image.open(src).convert('RGBA')).astype(np.float32)
rgb, al = a[..., :3], a[..., 3] / 255
mx, mn = rgb.max(axis=2), rgb.min(axis=2); sat = (mx - mn) / np.maximum(mx, 1)
w = np.clip((PAPER.mean() - rgb.mean(axis=2)) / (PAPER.mean() - INK.mean()), 0, 1)       # 0 是纯纸色光晕，1 是纯墨线
gray = (al < .98) & (sat < .2)
new_al = np.where(gray, al * w ** .8, al)
new_rgb = np.where(gray[..., None], INK + (rgb - INK) * (1 - w[..., None]) * .3, rgb)       # 留下来的那份按墨色
out = np.dstack([new_rgb, new_al * 255]); out[new_al < .03] = 0
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA').save(src, optimize=True)
print(src.name, '光晕像素', int((gray & (w < .3)).sum()), '→ 去掉；备份在', bak / src.name)
