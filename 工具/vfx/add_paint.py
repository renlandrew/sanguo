"""往画稿图集（原型/img/fx_paint.png + .json）里加一样（10-25：关羽普攻专用的细长刀风——用户：「普攻和青龙斩不能一模一样」）。
和 cut_paint.py 同一套「光」转换（黑底上的光 → 带透明度的光，亮度增益 2），一张黑底图只取最大的那一块，放进图集里第一个空格（2×2，每格 512）。
名字后面带 :cw / :ccw 表示先顺时针 / 逆时针转 90°（约定画稿「朝上」是飞的方向）。同名的就替换那一格。
用法：<media-venv>/bin/python 三国志/工具/vfx/add_paint.py <画稿.jpg> 名字[:cw|:ccw]
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / '原型' / 'img'
src, arg = Path(sys.argv[1]), sys.argv[2]
name, turn = (arg.split(':') + [''])[:2]
CELL, PAD = 512, 14
a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
v = a.max(axis=2)
floor = float(np.percentile(np.concatenate([v[:8].ravel(), v[-8:].ravel(), v[:, :8].ravel(), v[:, -8:].ravel()]), 95)) + 6
lab, n = ndi.label(ndi.binary_dilation(v > floor + 18, iterations=12)); sizes = ndi.sum(np.ones_like(v), lab, range(1, n + 1))
ys, xs = ndi.find_objects((lab == int(np.argmax(sizes)) + 1).astype(int))[0]
crop = a[ys, xs]; cv = crop.max(axis=2)
alpha = np.clip((cv - floor) / (255 - floor) * 2.0, 0, 1) ** .85
col = np.clip((crop - floor * (1 - alpha[..., None])) / np.maximum(alpha[..., None], .06), 0, 255)
im = Image.fromarray(np.dstack([col, alpha * 255]).astype(np.uint8), 'RGBA')
if turn: im = im.rotate(-90 if turn == 'cw' else 90, expand=True)
w, h = im.size; k = (CELL - 2 * PAD) / max(h, w); W2, H2 = max(1, round(w * k)), max(1, round(h * k))
im = im.resize((W2, H2), Image.Resampling.LANCZOS)
atlas = Image.open(OUT / 'fx_paint.png').convert('RGBA'); meta = json.loads((OUT / 'fx_paint.json').read_text())
cells = [[(j % 2) * CELL, (j // 2) * CELL] for j in range(4)]
used = {tuple(m['cell'][:2]): nm for nm, m in meta.items()}
spot = next((c for c in cells if used.get(tuple(c)) == name), None) or next((c for c in cells if tuple(c) not in used), None)
if spot is None: sys.exit('图集四格都满了')
cx, cy = spot; atlas.paste(Image.new('RGBA', (CELL, CELL)), (cx, cy))
ox, oy = cx + (CELL - W2) // 2, cy + (CELL - H2) // 2; atlas.paste(im, (ox, oy))
meta[name] = {'cell': [cx, cy, CELL, CELL], 'box': [ox - cx, oy - cy, W2, H2]}
atlas.save(OUT / 'fx_paint.png', optimize=True); (OUT / 'fx_paint.json').write_text(json.dumps(meta, ensure_ascii=False))
print(name, '放在格', spot, '外框', meta[name]['box'])
