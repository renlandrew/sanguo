"""11-18 新皮肤主页底图：美术/界面/新主页底图/home_<名>.png → 原型/img/home_<名>.jpg（宽 1080 以内，jpg 86）。
游戏里按原比例铺满（高对齐、左右裁一点），这里不裁不拉，只缩、转 jpg、打印平均亮度（原来的夜战场主页底图 0.25，参考手游 0.4–0.6）。
用法：python3 工具/画图/install_home_bg.py
"""
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
SRC = R / '美术' / '界面' / '新主页底图'
OUT = R / '原型' / 'img'
for p in sorted(SRC.glob('home_*.png')):
    im = Image.open(p).convert('RGB')
    if im.width > 1080:
        im = im.resize((1080, round(im.height * 1080 / im.width)), Image.Resampling.LANCZOS)
    a = np.asarray(im).astype(float) / 255
    y = (0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]).mean()
    dst = OUT / f'{p.stem}.jpg'
    im.save(dst, quality=86, optimize=True, progressive=True)
    print(p.name, im.size, '亮度 %.2f' % y, dst.name, dst.stat().st_size // 1024, 'KB')
