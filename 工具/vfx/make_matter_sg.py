"""三国志华彩层的材质图集（10-25）。照雾港 tools/vfx-spectacle-20260926/make_matter.py 的做法：可平铺的条带，四个通道意义一致——
  R = 亮线（按身份的线色画）  G = 体积/明暗（调色阶）  B = 闪点  A = 覆盖
用户（10-25）：「不要密集恐怖症，尽量简笔，大片色块」——只留四种大块质感，频率调低，B 闪点通道全空，不用雾港的密鳞、泡沫、点点：
  行 0 丝：宽褶加几道稀疏的长纤维（刀光、剑气、龙身）
  行 1 火：大火舌加几道热芯（矛刺、地裂）
  行 2 烟：大团烟云加亮边（一喝的声浪、扬尘）
  行 3 晶：大块平面晶格、亮缝（偃月刀光、飞剑剑身）
  行 4 墨：干笔飞白的墨痕（用户：「加一些水墨风格」），雾港的墨行，溅点从 160 个减到 18 个大点
  行 5–7 空（凑成 8 行，和雾港的着色器一样按 8 行取）
输出 原型/img/fx_matter.png（1024×2048，八行各 1024×256；WebGL1 要平铺，所以边长是 2 的幂）。
用法：<media-venv>/bin/python 三国志/工具/vfx/make_matter_sg.py
"""
import math, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'tools' / 'vfx-spectacle-20260926'))
import make_matter as M                                                  # 借雾港的周期噪声、平滑、晶格写法

W, H = M.W, M.H
y = np.arange(H)[:, None] / H

def row_silk():
    w1, w2 = M.pnoise(2, 2, 41), M.pnoise(4, 3, 42)
    phase = y * 6 + (w1 - .5) * 3 + (w2 - .5) * .8                         # 雾港是 20 道，这里 6 道，又粗又稀
    r = np.power(.5 + .5 * np.cos(2 * math.pi * phase), 18) * (.4 + .6 * w2)
    folds = .5 + .5 * np.sin(2 * math.pi * (y * 1.4 + (w1 - .5) * 1.2))
    g = .45 + .55 * folds
    return np.dstack([r, g, np.zeros_like(g), np.clip(.85 + .15 * g, 0, 1)])

def row_flame():
    n1, n2, n3 = M.pnoise(3, 5, 11), M.pnoise(6, 9, 12), M.pnoise(2, 2, 13)
    tongues = n1 * .7 + n2 * .3
    g = M.smooth(.28, .7, tongues) * (.8 + .2 * n3)
    phase = y * 5 + (n1 - .5) * 3
    r = np.clip(np.power(.5 + .5 * np.cos(2 * math.pi * phase), 10) * M.smooth(.4, .7, n2) * g * 1.6, 0, 1)
    return np.dstack([r, g, np.zeros_like(g), np.clip(np.maximum(g, r), 0, 1)])

def row_smoke():
    n1, n2 = M.pnoise(3, 3, 71), M.pnoise(6, 5, 72)
    cloud = n1 * .7 + n2 * .3
    g = M.smooth(.25, .72, cloud)
    gy, gx = np.gradient(g)
    r = np.clip(np.sqrt(gx * gx * M.ASPECT * M.ASPECT + gy * gy) * 7, 0, 1) * M.smooth(.3, .6, g)
    return np.dstack([r, g, np.zeros_like(g), np.clip(g * .95 + r * .3, 0, 1)])

def row_crystal():
    rng = np.random.default_rng(31); n = 12                                 # 雾港 34 块，这里 12 块大晶面
    sx, sy = rng.uniform(0, W, n), rng.uniform(0, H, n); shade = rng.uniform(.35, 1.0, n); ang = rng.uniform(0, 2 * math.pi, n)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    d = np.stack([np.sqrt((np.minimum(np.abs(xx - sx[k]), W - np.abs(xx - sx[k])) / M.ASPECT) ** 2 + (yy - sy[k]) ** 2) for k in range(n)], 0)
    order = np.argsort(d, 0); ds = np.take_along_axis(d, order, 0); d1, d2 = ds[0], ds[1]; idx = order[0]
    r = np.exp(-((d2 - d1) / 2.4) ** 2)
    ex = (xx - sx[idx] + W / 2) % W - W / 2
    facet = (np.cos(ang[idx]) * ex / M.ASPECT + np.sin(ang[idx]) * (yy - sy[idx])) / 60.0
    g = np.clip(shade[idx] + facet * .35, .2, 1)
    return np.dstack([r, g, np.zeros_like(g), np.ones_like(g)])

def row_ink():
    streak, clump, fine = M.pnoise(3, 30, 51), M.pnoise(6, 5, 52), M.pnoise(18, 40, 53)
    body = M.smooth(.42, .53, streak * .55 + clump * .30 + fine * .15)
    upper = np.roll(body, 2, axis=0)
    r = np.clip(body - upper, 0, 1) * .9
    splat = M.dots(54, 18, 1.2, 3.2)                                       # 雾港 160 个小溅点，这里 18 个大的
    g = np.clip(body + splat * .9, 0, 1)
    return np.dstack([r, g, np.zeros_like(g), np.clip(np.maximum(g, r), 0, 1)])

blank = np.zeros((H, W, 4))
rows = [row_silk(), row_flame(), row_smoke(), row_crystal(), row_ink(), blank, blank, blank]
atlas = np.concatenate([np.clip(r, 0, 1) for r in rows], axis=0)
out = HERE.parents[1] / '原型' / 'img' / 'fx_matter.png'
Image.fromarray((atlas * 255 + .5).astype(np.uint8)).save(out)
vis = np.concatenate([np.dstack([r[..., 0], r[..., 1], r[..., 1] * .5]) for r in rows[:5]], axis=0)
Image.fromarray((np.clip(vis, 0, 1) * 255).astype(np.uint8)).resize((512, 640)).save(HERE / 'fx_matter_vis.png')
print('材质图集', out, atlas.shape)
