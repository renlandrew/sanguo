# 把 ChatGPT 的三视图（白底、三人并排）按空白切成 正面.png、侧面.png、背面.png（1024 方图，三张同一比例）。
# 用法：python3 split_turn.py <三视图.jpg> <输出目录>
import sys
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB'); W, H = im.size
mask = im.convert('L').point(lambda v: 255 if v < 225 else 0)
col = [mask.crop((x, 0, x + 1, H)).getbbox() is not None for x in range(W)]
# 找所有空白列段，取中间最宽的两条缝切开（人挨得近时，缝可能只有几个像素宽）
gaps, x = [], 0
while x < W:
    if not col[x]:
        s0 = x
        while x < W and not col[x]: x += 1
        if s0 > 0 and x < W: gaps.append((x - s0, s0, x))
    else: x += 1
gaps = sorted(sorted(gaps, reverse=True)[:2], key=lambda g: g[1])
if len(gaps) < 2: sys.exit('没找到两条缝')
first = next(i for i, c in enumerate(col) if c); last = W - 1 - next(i for i, c in enumerate(reversed(col)) if c)
segs = [(first, gaps[0][1]), (gaps[0][2], gaps[1][1]), (gaps[1][2], last + 1)]
print('切在', [(g[1], g[2]) for g in gaps])
crops = []
for x0, x1 in segs:
    bb = mask.crop((x0, 0, x1, H)).getbbox(); crops.append(im.crop((x0, bb[1], x1, bb[3])))
side = int(max(max(c.size) for c in crops) * 1.12)
for c, n in zip(crops, ['正面', '侧面', '背面']):
    cv = Image.new('RGB', (side, side), 'white'); cv.paste(c, ((side - c.width) // 2, (side - c.height) // 2))
    cv.resize((1024, 1024), Image.LANCZOS).save('%s/%s.png' % (out, n)); print(n, c.size)
