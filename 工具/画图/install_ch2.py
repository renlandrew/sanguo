"""11-08 第二章：美术/第二章/剧情/story_sN.png → 原型/img/story_sN.jpg（720 宽，同第一章剧情图）。用法：python3 工具/画图/install_ch2.py 31 32 …（不给就装全部已画的）"""
import sys
from pathlib import Path
from PIL import Image
R = Path(__file__).resolve().parents[2]; SRC = R / '美术' / '第二章' / '剧情'; IMG = R / '原型' / 'img'
ns = sys.argv[1:] or sorted(p.stem[7:] for p in SRC.glob('story_s*.png'))
for n in ns:
    p = SRC / f'story_s{n}.png'
    if not p.exists(): continue
    im = Image.open(p).convert('RGB'); im.resize((720, round(720 * im.height / im.width)), Image.Resampling.LANCZOS).save(IMG / f'story_s{n}.jpg', quality=85, optimize=True); print('ok', n)
