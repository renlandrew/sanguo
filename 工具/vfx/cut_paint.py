"""ChatGPT 画的法术画稿 → 华彩层的画稿图集（10-25，用户：「需要的话就先用gpt 画剑气刀气」）。
照雾港 tools/vfx-spectacle-20260926/paint_atlas.py 的「光」模式：黑底上的光转成带透明度的光——透明度取最亮的那个通道，颜色除以透明度还原，
这样在预乘的着色器里它加的是光，只把底下压暗一点，不会画出一块黑方块。
一张黑底图上画了几样（从左到右），按连通块分开，按 x 排序依次命名；每样裁到内容、留边，等比放进 512 的格子（2×2，共 1024）。
输出 原型/img/fx_paint.png + .json（每格的名字 → 格子 rect、内容在格子里的外框）。
名字后面带 :cw / :ccw 表示切下来先顺时针 / 逆时针转 90°（游戏里约定画稿「朝上」是飞的方向：月牙外弧朝上、矛尖朝上）。
用法：<media-venv>/bin/python 三国志/工具/vfx/cut_paint.py <画稿.jpg> 名字1[:cw] 名字2 …
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / '原型' / 'img'
src, names = Path(sys.argv[1]), [a.split(':')[0] for a in sys.argv[2:]]
turns = [(a.split(':') + [''])[1] for a in sys.argv[2:]]
a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
v = a.max(axis=2)
floor = float(np.percentile(np.concatenate([v[:8].ravel(), v[-8:].ravel(), v[:, :8].ravel(), v[:, -8:].ravel()]), 95)) + 6
mask = ndi.binary_dilation(v > floor + 18, iterations=12)
lab, n = ndi.label(mask); sizes = ndi.sum(np.ones_like(v), lab, range(1, n + 1))
keep = [i + 1 for i in np.argsort(sizes)[::-1][:len(names)]]
boxes = sorted([ndi.find_objects((lab == k).astype(int))[0] for k in keep], key=lambda b: b[1].start)
CELL, PAD = 512, 14
atlas = Image.new('RGBA', (CELL * 2, CELL * 2)); meta = {}
for j, (nm, turn, (ys, xs)) in enumerate(zip(names, turns, boxes)):
    crop = a[ys, xs]; cv = crop.max(axis=2)
    alpha = np.clip((cv - floor) / (255 - floor) * 2.0, 0, 1) ** .85            # 最亮的通道当透明度；增益拉到 2，贴在浅色纸底上不发淡
    col = np.clip((crop - floor * (1 - alpha[..., None])) / np.maximum(alpha[..., None], .06), 0, 255)   # 颜色还原
    im = Image.fromarray(np.dstack([col, alpha * 255]).astype(np.uint8), 'RGBA')
    if turn: im = im.rotate(-90 if turn == 'cw' else 90, expand=True)
    w, h = im.size; k = (CELL - 2 * PAD) / max(h, w); W2, H2 = max(1, round(w * k)), max(1, round(h * k))
    im = im.resize((W2, H2), Image.Resampling.LANCZOS)
    cx, cy = (j % 2) * CELL, (j // 2) * CELL; ox, oy = cx + (CELL - W2) // 2, cy + (CELL - H2) // 2
    atlas.paste(im, (ox, oy))
    meta[nm] = {'cell': [cx, cy, CELL, CELL], 'box': [ox - cx, oy - cy, W2, H2]}
    print(nm, '原图外框', xs.start, ys.start, w, h, '→', W2, H2)
atlas.save(OUT / 'fx_paint.png', optimize=True); (OUT / 'fx_paint.json').write_text(json.dumps(meta, ensure_ascii=False))
print('画稿图集', OUT / 'fx_paint.png')
