"""11-12 讨伐怪物立绘、姿势图 → 原型/img/mon_<键><形态><姿势>.webp。
原图在 美术/讨伐/<目录>/form<N>[_a|_b].png（Codex 画，要求透明底；有时给的是白底或假棋盘格，这里统一处理）：
  已有透明通道（四角透明）的直接用；否则从四边往里泛洪，把接近底色的抠成透明，边上软一圈。
不裁边（同一只怪物各张姿势靠画面里的位置对齐），按长边缩到 768，存 webp。
用法：python3 工具/画图/install_hunt.py [目录名 …]
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[2]; SRC = R / '美术' / '讨伐'; OUT = R / '原型' / 'img'
KEY = {'黄巾力士': 'juling', '山君': 'shanjun', '蛟': 'jiao'}
for d in (sys.argv[1:] or KEY):
    for p in sorted((SRC / d).glob('form*.png')):
        n, _, v = p.stem[4:].partition('_'); im = Image.open(p).convert('RGBA'); a = np.asarray(im).copy()
        cor = [a[2, 2, 3], a[2, -3, 3], a[-3, 2, 3], a[-3, -3, 3]]
        if min(cor) > 200:   # 没有透明底：泛洪抠
            rgb = a[..., :3].astype(np.float32); edge = np.concatenate([rgb[:4].reshape(-1, 3), rgb[-4:].reshape(-1, 3), rgb[:, :4].reshape(-1, 3), rgb[:, -4:].reshape(-1, 3)])
            bg = np.median(edge, axis=0); near = np.sqrt(((rgb - bg) ** 2).sum(axis=2)) < 34
            lab, _ = ndi.label(near); ids = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])); ids = ids[ids > 0]
            m = np.isin(lab, ids); al = Image.fromarray(((~m) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1))
            a[..., 3] = np.minimum(a[..., 3], np.asarray(al)); how = '抠底'
        else: how = '透明'
        im = Image.fromarray(a); k = 768 / max(im.size); im = im.resize((round(im.width * k), round(im.height * k)), Image.Resampling.LANCZOS)
        dst = OUT / f'mon_{KEY[d]}{n}{v}.webp'; im.save(dst, quality=90, method=6); bb = im.getbbox()
        print(d, p.name, how, im.size, '内容', bb, dst.stat().st_size // 1024, 'KB')
