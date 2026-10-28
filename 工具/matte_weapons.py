"""神兵五级（ChatGPT 画的，一张图里五把兵器竖着从左到右并排，中灰底）→ 五张透明底 PNG（10-25，用户发了三张别家「神兵」截图：「画好不同等级的青龙偃月刀等武器，要越来越绚」）。
抠法同 matte_ui.py：四边中位色当底色，离底色越远越不透明，和四边连通的灰算底，兵器围住的成片灰也算底；
分件按左右：每一列有没有东西，空的列把五把隔开（兵器斜一点、穗子飘出去也不会被分到上下两行）。
每把裁到内容、缩到 HEIGHT 高，存 原型/img/<前缀><1..5>.png。
用法：<media-venv>/bin/python 三国志/工具/matte_weapons.py <图> <前缀，如 wpn_guan> [高 640] [几样 5]
"""
import os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
src, prefix = Path(sys.argv[1]), sys.argv[2]
HEIGHT = int(sys.argv[3]) if len(sys.argv) > 3 else 640
COUNT = int(sys.argv[4]) if len(sys.argv) > 4 else 5
GAP = int(os.environ.get('GAP', 12))   # 隔多少列空白才算另一把；刘备一对双股剑挨得近，GAP=60 把一对当一样（10-28）
a = np.asarray(Image.open(src).convert('RGB')).astype(np.float32)
border = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])
bgc = np.median(border, axis=0)
dist = np.sqrt(((a - bgc) ** 2).sum(axis=2))
mx, mn = a.max(axis=2), a.min(axis=2); sat = (mx - mn) / np.maximum(mx, 1)
near = dist < 20
seeds = np.zeros_like(near); seeds[0] = near[0]; seeds[-1] = near[-1]; seeds[:, 0] = near[:, 0]; seeds[:, -1] = near[:, -1]
bg = ndi.binary_propagation(seeds, mask=near)
holes, nh = ndi.label(near & ~bg); hs = ndi.sum(np.ones_like(dist), holes, range(1, nh + 1))
if not os.environ.get('NOHOLES'): bg |= np.isin(holes, [i + 1 for i in range(nh) if hs[i] > 150])
else:                                                                                    # NOHOLES=1：东西本身是灰的（铁锭、铁钉），围住的灰只有平整的才当底（同 matte_ui.py）
    dm = ndi.mean(dist, holes, range(1, nh + 1)); ds = ndi.standard_deviation(dist, holes, range(1, nh + 1))
    bg |= np.isin(holes, [i + 1 for i in range(nh) if hs[i] > 150 and dm[i] < 9 and ds[i] < 3.5])
    flat, nf = ndi.label((dist < 6) & ~bg); fs = ndi.sum(np.ones_like(dist), flat, range(1, nf + 1))
    bg |= ndi.binary_dilation(np.isin(flat, [i + 1 for i in range(nf) if fs[i] > 150]), iterations=2) & (dist < 14)
alpha = np.clip((dist - 10) / 30, 0, 1); alpha[~bg & (dist > 6)] = np.maximum(alpha[~bg & (dist > 6)], (sat[~bg & (dist > 6)] > .15) * 1.0); alpha[bg & (dist < 12)] = 0
if os.environ.get('NOHOLES'): alpha[ndi.binary_erosion(~bg, iterations=1)] = 1                   # 灰色的东西：和四边不连通的整块都不透明
lab, n = ndi.label(alpha > .4); sizes = ndi.sum(np.ones_like(dist), lab, range(1, n + 1))
alpha[np.isin(lab, [i + 1 for i in range(n) if sizes[i] < 80])] = 0                    # 零星的碎点丢掉
cols = (alpha > .4).sum(axis=0) > 2
runs, x = [], 0                                                                          # 有东西的列连成段，宽于 20 的才算一把
while x < len(cols):
    if cols[x]:
        x0 = x
        while x < len(cols) and (cols[x] or (x + GAP < len(cols) and cols[x:x + GAP].any())): x += 1
        if x - x0 > 20: runs.append((x0, x))
    else: x += 1
cnt = (alpha > .4).sum(axis=0)
while len(runs) < COUNT and runs:                                                            # 飘带碰在一起、不够五把：最宽那段从中间最稀的一列切开
    i = max(range(len(runs)), key=lambda j: runs[j][1] - runs[j][0]); x0, x1 = runs[i]; a0, a1 = x0 + (x1 - x0) * 3 // 10, x0 + (x1 - x0) * 7 // 10
    cut = a0 + int(np.argmin(cnt[a0:a1])); runs[i:i + 1] = [(x0, cut), (cut, x1)]
print('找到', len(runs), '把：', runs)
un = np.clip((a - (1 - alpha[..., None]) * bgc) / np.maximum(alpha[..., None], .05), 0, 255)
for k, (x0, x1) in enumerate(runs, 1):
    m = np.zeros_like(alpha); m[:, x0:x1] = alpha[:, x0:x1]
    im = Image.fromarray(np.dstack([un, m * 255]).astype(np.uint8), 'RGBA'); im = im.crop(im.getbbox())
    w, h = im.size; im = im.resize((round(w * HEIGHT / h), HEIGHT), Image.Resampling.LANCZOS)
    dst = HERE.parent / '原型' / 'img' / f'{prefix}{k}.png'; im.save(dst, optimize=True); print(dst.name, im.size, dst.stat().st_size // 1024, 'KB')
