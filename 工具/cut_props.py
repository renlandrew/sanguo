"""ChatGPT 画的场上道具（白底，几列几行分开摆）→ 原型用的透明道具图集（10-25，用户指着程序画的拒马：「这个也要gpt 重新画」）。
白底抠透明：离白色越远越不透明（软阈值），只留和四边不连通的部分；按连通块分开，先按行（上下）再按列（左右）排序，依次命名。
每样裁到内容、留边，长边缩到 SIZE，横排进一张图集。
输出 原型/img/props.png + .json（名字 → rect；锚点约定：底边中点）。
用法：<media-venv>/bin/python 三国志/工具/cut_props.py <道具图.jpg> 行数 名字1 名字2 …
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / '原型' / 'img'
src, rows, names = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3:]
SIZE, PAD = 256, 6
a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
dist = 255 - a.min(axis=2)                                                     # 离纯白多远
near = dist < 14
seeds = np.zeros_like(near); seeds[0] = near[0]; seeds[-1] = near[-1]; seeds[:, 0] = near[:, 0]; seeds[:, -1] = near[:, -1]
bg = ndi.binary_propagation(seeds, mask=near)                                  # 和四边连着的白才算背景（物件里的白不抠）
alpha = np.clip((dist - 6) / 26, 0, 1); alpha[~bg] = np.maximum(alpha[~bg], 1.0 * (dist[~bg] > 3)); alpha[bg & (dist < 8)] = 0
lab, n = ndi.label(ndi.binary_dilation(alpha > .3, iterations=10)); sizes = ndi.sum(np.ones_like(dist), lab, range(1, n + 1))
keep = [i + 1 for i in np.argsort(sizes)[::-1][:len(names)]]
boxes = [ndi.find_objects((lab == k).astype(int))[0] for k in keep]
H = a.shape[0]; boxes.sort(key=lambda b: (int((b[0].start + b[0].stop) / 2 / (H / rows)), b[1].start))
ims = []
for nm, (ys, xs) in zip(names, boxes):
    col = a[ys, xs]; al = alpha[ys, xs]
    un = np.clip((col - (1 - al[..., None]) * 255) / np.maximum(al[..., None], .05), 0, 255)     # 去掉白边的混色
    im = Image.fromarray(np.dstack([un, al * 255]).astype(np.uint8), 'RGBA'); w, h = im.size; k = SIZE / max(w, h)
    ims.append((nm, im.resize((max(1, round(w * k)), max(1, round(h * k))), Image.Resampling.LANCZOS)))
AW = sum(im.width + 2 * PAD for _, im in ims); AH = max(im.height for _, im in ims) + 2 * PAD
atlas = Image.new('RGBA', (AW, AH)); meta = {}; x = 0
for nm, im in ims:
    atlas.paste(im, (x + PAD, PAD)); meta[nm] = [x + PAD, PAD, im.width, im.height]; x += im.width + 2 * PAD
    print(nm, im.size)
atlas.save(OUT / 'props.png', optimize=True); (OUT / 'props.json').write_text(json.dumps(meta, ensure_ascii=False))
print('道具图集', atlas.size)
