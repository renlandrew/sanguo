# 保持 512 画布，只平移透明帧，把真正可见的蹄底对齐步兵基线；不缩放、不逐帧裁框。
import sys
from pathlib import Path
from PIL import Image
src, dst = map(Path, sys.argv[1:3]); baseline = round(256 + .70 * 512 / 4.8)
for d in range(8):
    out = dst / str(d); out.mkdir(parents=True, exist_ok=True)
    for p in sorted((src / str(d)).glob('*.png')):
        im = Image.open(p).convert('RGBA'); box = im.getbbox()
        if box is None: raise RuntimeError('空帧：'+str(p))
        dy = baseline - box[3]
        if box[1] + dy < 1: raise RuntimeError('对齐后矛尖会被裁掉：'+str(p))
        frame = Image.new('RGBA', im.size); frame.paste(im, (0, dy)); frame.save(out / p.name)
print('骑兵脚底基线', baseline)
