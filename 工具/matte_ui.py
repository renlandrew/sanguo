"""界面美术（ChatGPT 画的，中灰纯色底）→ 透明底 PNG（10-25 结算页照雾港重做：用户「这个界面太html，参考雾港」）。
抠法同 matte_portrait.py：四边像素的中位色当底色，离底色越远越不透明，只去掉和四边连通的灰；不描墨线。
一张图里画了几样（如上下两块牌匾）就按连通块从上到下、从左到右分开，依次存成给的几个名字；每样裁到内容、缩到 WIDTH 宽。
输出 原型/img/<名>.png，原图存 美术/界面/。
用法：<media-venv>/bin/python 三国志/工具/matte_ui.py <图> 宽 名1 [名2 ...]
"""
import os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
src, WIDTH, names = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3:]
a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
border = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
bgc = np.median(border, axis=0)
dist = np.sqrt(((a - bgc) ** 2).sum(axis=2))
near = dist < 20
seeds = np.zeros_like(near); seeds[0] = near[0]; seeds[-1] = near[-1]; seeds[:, 0] = near[:, 0]; seeds[:, -1] = near[:, -1]
bg = ndi.binary_propagation(seeds, mask=near)
mx, mn = a.max(axis=2), a.min(axis=2); sat = (mx - mn) / np.maximum(mx, 1); lum = a.mean(axis=2); bl = bgc.mean()
near |= (sat < .1) & (lum > bl - 25) & (lum < bl + 70)                                  # 光芒后面那圈发白的灰光，也算底
holes, nh = ndi.label(near & ~bg); hs = ndi.sum(np.ones_like(dist), holes, range(1, nh + 1))   # 光芒、戟杆围住的灰：成片的也是底
if not os.environ.get('NOHOLES'): bg |= np.isin(holes, [i + 1 for i in range(nh) if hs[i] > 120])
else:                                                                                   # 围住的灰：平整的（真背景）才算底，有纹理的（石头、铁）不算
    dm = ndi.mean(dist, holes, range(1, nh + 1)); ds = ndi.standard_deviation(dist, holes, range(1, nh + 1))
    bg |= np.isin(holes, [i + 1 for i in range(nh) if hs[i] > 120 and dm[i] < 9 and ds[i] < 3.5])
    flat, nf = ndi.label((dist < 6) & ~bg); fs = ndi.sum(np.ones_like(dist), flat, range(1, nf + 1))   # 和石头连在一起的那片底：只取离底色特别近、成片的
    bg |= ndi.binary_dilation(np.isin(flat, [i + 1 for i in range(nf) if fs[i] > 150]), iterations=2) & (dist < 14)   # NOHOLES=1：东西本身是灰的（石头、铁），围住的灰不当底
alpha = np.clip((dist - 10) / 30, 0, 1); solid = ~bg & (dist > 6) & (sat > .18); alpha[solid] = 1; alpha[bg & (dist < 12)] = 0
if os.environ.get('NOHOLES'): alpha[ndi.binary_erosion(~bg, iterations=1)] = 1   # 发灰的光晕只按离底色多远给半透明，不硬填满
lab, n = ndi.label(ndi.binary_dilation(alpha > .4, iterations=6)); sizes = ndi.sum(np.ones_like(dist), lab, range(1, n + 1))
big = [i + 1 for i in range(n) if sizes[i] > sizes.max() * .08]                       # 几样东西各是一大块；更小的碎块（远处的光点）丢掉
boxes = []
for b in big:
    ys, xs = np.where(lab == b); boxes.append((b, ys.min(), xs.min()))
boxes.sort(key=lambda t: (round(t[1] / 200), t[2]))
un = np.clip((a - (1 - alpha[..., None]) * bgc) / np.maximum(alpha[..., None], .05), 0, 255)          # 去掉灰边的混色
keep_all = np.isin(lab, big)
if len(names) == 1: groups = [keep_all]
else:
    if len(boxes) != len(names): sys.exit(f'找到 {len(boxes)} 样，给了 {len(names)} 个名字')
    groups = [lab == b for b, _, _ in boxes]
for name, m in zip(names, groups):
    al = alpha * m
    im = Image.fromarray(np.dstack([un, al * 255]).astype(np.uint8), 'RGBA'); im = im.crop(im.getbbox())
    w, h = im.size; im = im.resize((WIDTH, round(h * WIDTH / w)), Image.Resampling.LANCZOS)
    dst = HERE.parent / '原型' / 'img' / f'{name}.png'; im.save(dst, optimize=True)
    print(dst.name, im.size, dst.stat().st_size // 1024, 'KB')
