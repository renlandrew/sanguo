"""大招特写的 Veo 视频 → 游戏里占满屏幕播的透明图集（10-25，make_ult_pack.py 录的 5 条）。
输入：<帧图目录>/<键>_g<序号>.jpg，每张 2 列 × 2 行、每格 720×1280，是一条视频里按时间顺序取的 4 帧（浏览器里从 Cloud Storage 的视频截出来）。
抠法和 cut_generals.py 同一套（灰底取四边近灰的中位数，和四边连通的近灰算背景，只留最大一块），但不描墨线、不垫纸色光晕
（10-25 用户嫌张角那圈白边太厚）；人物贴着画面底边（腰以下裁掉），所以底边不当背景。
各帧按同一外框裁、缩到 HEIGHT 高，排成图集存 WebP（带透明，体积比 PNG 小一个数量级）。
输出 原型/img/ult_<键>.webp + ult_<键>.json：{ n, w, h, cols, fps }。
用法：<media-venv>/bin/python 三国志/工具/veo/cut_ult.py <帧图目录> [guan zhang liu zhangjiao lvbu] [起:止]（只取第几帧到第几帧）
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1]); OUT = HERE.parents[1] / '原型' / 'img'
import os
HEIGHT, FPS, GRID = int(os.environ.get('HEIGHT', 900)), int(os.environ.get('FPS', 15)), int(os.environ.get('GRID', 2))   # 10-27 学招特写 8 秒：GRID=3（3×3 帧图）HEIGHT=720 FPS=16
args = sys.argv[2:]; rng = next((a for a in args if ':' in a), None); keys = [a for a in args if ':' not in a] or ['guan', 'zhang', 'liu', 'zhangjiao', 'lvbu']

def flat_gray(a):
    edge = np.concatenate([a[:6].reshape(-1, 3), a[:, :6].reshape(-1, 3), a[:, -6:].reshape(-1, 3)])   # 底边是人，不取
    v = edge.max(axis=1); sat = (v - edge.min(axis=1)) / np.maximum(v, 1); g = edge[sat < .06]
    return np.median(g if len(g) > 50 else edge, axis=0)

def matte(a, bg):
    distance = np.max(np.abs(a - bg), axis=2)
    v = a.max(axis=2); bv = bg.max(); sat = (v - a.min(axis=2)) / np.maximum(v, 1)
    near = (distance < 18) | ((sat < .1) & (v > .6 * bv) & (v < bv + 8))
    seeds = np.zeros(near.shape, bool); seeds[0] = near[0]; seeds[:, 0] = near[:, 0]; seeds[:, -1] = near[:, -1]
    bgm = ndi.binary_propagation(seeds, mask=near)
    holes, n = ndi.label((distance < 15) & (sat < .12) & ~bgm)                       # 胳膊和兵器围出来的灰
    sizes = np.bincount(holes.ravel()); sizes[0] = 0
    bgm |= ndi.binary_propagation(np.isin(holes, np.where(sizes > 60)[0]), mask=(distance < 18) & (sat < .14))
    solid = ~bgm
    labels, count = ndi.label(ndi.binary_dilation(solid, iterations=2))
    if count > 1:
        sizes = np.bincount(labels.ravel()); sizes[0] = 0
        solid &= labels == sizes.argmax()
    alpha = ndi.gaussian_filter(solid.astype(np.float32), .7)
    alpha[solid & (ndi.distance_transform_edt(solid) > 1.5)] = 1
    unmix = (a - (1 - alpha[..., None]) * bg) / np.maximum(alpha[..., None], .15)
    rgba = np.dstack([np.clip(unmix, 0, 255), alpha * 255]).astype(np.uint8); rgba[alpha < .02] = 0
    return rgba

for k in keys:
    grids = sorted(SRC.glob(f'{k}_g*.jpg'), key=lambda p: int(p.stem.split('_g')[1]))
    if not grids: print(k, '没有帧图，跳过'); continue
    frames = []
    for gp in grids:
        sh = np.asarray(Image.open(gp).convert('RGB')).astype(np.float32); ch, cw = sh.shape[0] // GRID, sh.shape[1] // GRID
        for i in range(GRID * GRID): frames.append(sh[(i // GRID) * ch:(i // GRID + 1) * ch, (i % GRID) * cw:(i % GRID + 1) * cw])
    if rng: a, b = (int(x) for x in rng.split(':')); frames = frames[a:b]
    mats = [matte(f, flat_gray(f)) for f in frames]
    al = np.stack([m[..., 3] > 40 for m in mats]); ys, xs = np.where(al.any(axis=0))
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1                  # 整段一个外框
    s = HEIGHT / (y1 - y0); w = round((x1 - x0) * s)
    fh, fw = y1 - y0, x1 - x0; sm = lambda v: v * v * (3 - 2 * v)                                    # 左右两边、底边（腰）宽宽地渐隐，视频画面边上切出来的直边看不出来（10-25 用户：「边缘好明显」）
    rx = sm(np.clip(np.minimum(np.arange(fw), np.arange(fw)[::-1]) / (fw * .16), 0, 1)); ry = sm(np.clip(np.arange(fh)[::-1] / (fh * .2), 0, 1))
    edge = ry[:, None] * rx[None, :]
    for m in mats: m[y0:y1, x0:x1, 3] = (m[y0:y1, x0:x1, 3] * edge).astype(np.uint8)
    ims = [Image.fromarray(m[y0:y1, x0:x1], 'RGBA').resize((w, HEIGHT), Image.Resampling.LANCZOS) for m in mats]
    cols = max(1, min(len(ims), 16000 // w, 6)); rows = -(-len(ims) // cols)
    atlas = Image.new('RGBA', (w * cols, HEIGHT * rows))
    for j, im in enumerate(ims): atlas.paste(im, ((j % cols) * w, (j // cols) * HEIGHT))
    dst = OUT / f'ult_{k}.webp'; atlas.save(dst, 'WEBP', quality=82, method=6)
    (OUT / f'ult_{k}.json').write_text(json.dumps({'n': len(ims), 'w': w, 'h': HEIGHT, 'cols': cols, 'fps': FPS}))
    print(k, len(ims), '帧', f'{w}x{HEIGHT}', '图集', atlas.size, dst.stat().st_size // 1024, 'KB')
