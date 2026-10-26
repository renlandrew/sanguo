"""敌将正面立绘（ChatGPT 画的，中灰纯色底）→ 游戏里等 Veo 期间先顶着用的透明立绘（10-25）。
灰底：取四边像素的中位色当底色，离底色越远越不透明（软阈值）；只留和四边不连通的部分（人身上的灰不抠）；
最大的一块（人）加它周围贴着的小块（兵器、飘带），裁到内容，高缩到 HEIGHT，描一圈细墨线（和城头武将一样）。
输出 原型/img/pt_<名>.png。原图存 美术/<名>/正面.jpg，明天也拿它当 Veo 首帧。
用法：<media-venv>/bin/python 三国志/工具/matte_portrait.py <正面.jpg> <名>
"""
import os, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
src, name = Path(sys.argv[1]), sys.argv[2]
HEIGHT = 520
a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
border = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
bgc = np.median(border, axis=0)
dist = np.sqrt(((a - bgc) ** 2).sum(axis=2))
near = dist < 18
seeds = np.zeros_like(near); seeds[0] = near[0]; seeds[-1] = near[-1]; seeds[:, 0] = near[:, 0]; seeds[:, -1] = near[:, -1]
bg = ndi.binary_propagation(seeds, mask=near)
alpha = np.clip((dist - 10) / 28, 0, 1); alpha[~bg] = np.maximum(alpha[~bg], (dist[~bg] > 6).astype(np.float32)); alpha[bg & (dist < 12)] = 0
lab, n = ndi.label(ndi.binary_dilation(alpha > .4, iterations=4)); sizes = ndi.sum(np.ones_like(dist), lab, range(1, n + 1))
keep = np.isin(lab, [i + 1 for i in range(n) if sizes[i] > sizes.max() * .02]); alpha *= keep
un = np.clip((a - (1 - alpha[..., None]) * bgc) / np.maximum(alpha[..., None], .05), 0, 255)          # 去掉灰边的混色
im = Image.fromarray(np.dstack([un, alpha * 255]).astype(np.uint8), 'RGBA')
im = im.crop(im.getbbox()); w, h = im.size; im = im.resize((round(w * HEIGHT / h), HEIGHT), Image.Resampling.LANCZOS)
ER = int(os.environ.get('ERODE', '0'))                                                              # ERODE=n：边缘往里收 n 像素，去掉一圈发白的毛边（10-26 吕布：「白边明显」）
if ER: im.putalpha(im.split()[3].filter(ImageFilter.MinFilter(2 * ER + 1)).filter(ImageFilter.GaussianBlur(.6)))
al = im.split()[3]; edge = al.filter(ImageFilter.MaxFilter(3))                                       # 一圈细墨线
line = Image.new('RGBA', im.size, (29, 26, 23, 255)); line.putalpha(edge.point(lambda v: min(255, v)))
out = Image.alpha_composite(line, im)
dst = HERE.parent / '原型' / 'img' / f'pt_{name}.png'; out.save(dst, optimize=True)
print(dst.name, out.size, dst.stat().st_size // 1024, 'KB')
