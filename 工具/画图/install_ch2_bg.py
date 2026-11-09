"""11-08 第二章战场底图、战役地图 → 原型/img。
Codex 画的原图在 美术/第二章/底图、美术/第二章/地图（<键>.png）。
  bg_*：竖版铺满 1080×1920（按宽裁两边，同 make_scene.py bg），map_*：缩成 720 宽。
  原色存 美术/底图原色/<键>.jpg；游戏里的那张降饱和七成（11-01 起场景图都离线降好，INK_SAT）。
用法：python3 工具/画图/install_ch2_bg.py [键 …]（不给键就处理两个目录里全部）
"""
import sys
from pathlib import Path
from PIL import Image, ImageEnhance
R = Path(__file__).resolve().parents[2]; IMG = R / '原型' / 'img'; RAW = R / '美术' / '底图原色'
SRC = [R / '美术' / '第二章' / '底图', R / '美术' / '第二章' / '地图']
keys = sys.argv[1:] or sorted(p.stem for d in SRC for p in d.glob('*.png'))
for k in keys:
    p = next((d / f'{k}.png' for d in SRC if (d / f'{k}.png').exists()), None)
    if not p: print('没有', k); continue
    im = Image.open(p).convert('RGB'); W, H = im.size
    if k.startswith('bg_'):
        tw = min(W, round(H * 1080 / 1920)); x0 = (W - tw) // 2
        out = im.crop((x0, 0, x0 + tw, H)).resize((1080, 1920), Image.Resampling.LANCZOS)
    else:
        out = im.resize((720, round(720 * H / W)), Image.Resampling.LANCZOS)
    out.save(RAW / f'{k}.jpg', quality=88)
    ImageEnhance.Color(out).enhance(.7).save(IMG / f'{k}.jpg', quality=85, optimize=True)
    print(k, im.size, '->', out.size)
