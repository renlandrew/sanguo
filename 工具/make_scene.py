# 场景图（10-24，ChatGPT 画的）→ 原型用的素材。
#   城墙：裁掉上面的白，白色（垛口间、射孔）抠成透明，纵向压扁（游戏镜头是从高处往下看），出 1080×234（游戏里 360×78）。
#   背景：竖版铺满 360×640 的画布（3 倍 1080×1920），按宽裁两边。
# 用法：python3 工具/make_scene.py wall <城墙.jpg> <输出.png>  |  python3 工具/make_scene.py bg <背景.jpg> <输出.jpg>
import sys
from PIL import Image, ImageFilter
kind, src, dst = sys.argv[1:4]
im = Image.open(src).convert('RGB')
if kind == 'wall':
    W, H = im.size
    L = im.convert('L')
    rows = [y for y in range(H) if L.crop((0, y, W, y + 1)).getextrema()[0] < 200]            # 第一行有墙的地方 = 垛口顶
    top = max(0, rows[0] - 4); im = im.crop((0, top, W, H))
    m = im.convert('RGB').point(lambda v: v)                                                    # 白 → 透明（215–240 之间渐变）
    mn = Image.merge('RGB', im.split()).convert('L')
    lo = [min(px) for px in im.getdata()]
    a = Image.new('L', im.size); a.putdata([255 if v < 215 else 0 if v > 240 else int(255 * (240 - v) / 25) for v in lo])
    a = a.filter(ImageFilter.GaussianBlur(.8))
    out = im.convert('RGBA'); out.putalpha(a)
    out = out.resize((1080, 234), Image.LANCZOS); out.save(dst, optimize=True)
    print('城墙', out.size, '原图从第', top, '行起')
elif kind == 'bg':
    W, H = im.size; tw = round(H * 1080 / 1920); x0 = (W - tw) // 2
    out = im.crop((x0, 0, x0 + tw, H)).resize((1080, 1920), Image.LANCZOS); out.save(dst, quality=88)
    print('背景', out.size)
