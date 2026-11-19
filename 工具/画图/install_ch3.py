# -*- coding: utf-8 -*-
"""11-18 第三章美术装进 原型/img（原图在 美术/第三章/<类>/）。重跑安全：已装的覆盖。
  官阶 rank_<人>_<阶>.png → rank_<人>_<阶>.jpg（360 方）；底图 bg_* → 1080×1920、地图 map_* → 720 宽（原色存 美术/底图原色，游戏里降饱和七成，同 install_ch2_bg.py）；
  剧情 story_s<n>.png / story_c3.png → 720 宽 jpg。立绘、兵器、图标另用 matte_portrait.py、matte_weapons.py、matte_ui.py 抠。
用法：python3 工具/画图/install_ch3.py
"""
from pathlib import Path
from PIL import Image, ImageEnhance
R = Path(__file__).resolve().parents[2]; IMG = R / '原型' / 'img'; RAW = R / '美术' / '底图原色'; A = R / '美术' / '第三章'
n = 0
for p in sorted((A / '官阶').glob('rank_*.png')):
    Image.open(p).convert('RGB').resize((360, 360), Image.Resampling.LANCZOS).save(IMG / f'{p.stem}.jpg', quality=88, optimize=True); n += 1
for d in ('底图', '地图'):
    for p in sorted((A / d).glob('*.png')):
        im = Image.open(p).convert('RGB'); W, H = im.size
        if p.stem.startswith('bg_'): tw = min(W, round(H * 1080 / 1920)); x0 = (W - tw) // 2; out = im.crop((x0, 0, x0 + tw, H)).resize((1080, 1920), Image.Resampling.LANCZOS)
        else: out = im.resize((720, round(720 * H / W)), Image.Resampling.LANCZOS)
        out.save(RAW / f'{p.stem}.jpg', quality=88); ImageEnhance.Color(out).enhance(.7).save(IMG / f'{p.stem}.jpg', quality=85, optimize=True); n += 1
for p in sorted((A / '剧情').glob('story_*.png')):
    im = Image.open(p).convert('RGB'); im.resize((720, round(720 * im.height / im.width)), Image.Resampling.LANCZOS).save(IMG / f'{p.stem}.jpg', quality=85, optimize=True); n += 1
print('装了', n, '张')
