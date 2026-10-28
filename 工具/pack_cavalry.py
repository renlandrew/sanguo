# 黄巾骑兵八方向：沿用步兵 rects / anchor / stand 格式，透明调色板控制网页体积。
import json, sys
from pathlib import Path
from PIL import Image

src, dst = map(Path, sys.argv[1:3]); dst.mkdir(parents=True, exist_ok=True)
scale = 4.8; size = 512; anchor = [256, round(256 + .70 * size / scale)]
for colors in [192, 128, 96, 64]:
    for direction in range(8):
        groups = []
        for act in ['Gallop', 'Fall']:
            images = [Image.open(p).convert('RGBA') for p in sorted((src / str(direction)).glob(act + '_*.png'))]
            if not images: raise RuntimeError('缺少方向 %s 的 %s 帧' % (direction, act))
            boxes = [im.getbbox() for im in images]; box = (max(0, min(b[0] for b in boxes) - 2), max(0, min(b[1] for b in boxes) - 2), min(size, max(b[2] for b in boxes) + 2), min(size, max(b[3] for b in boxes) + 2))
            groups.append((act, [im.crop(box) for im in images], box))
        width = max(sum(im.width for im in ims) for _, ims, _ in groups)
        height = sum(ims[0].height for _, ims, _ in groups)
        atlas = Image.new('RGBA', (width, height)); meta = {'frame': size, 'stand': round(2.4 * size / scale, 1), 'direction': direction, 'yaw': direction * 45, 'light': 'lit', 'anims': {}}; y = 0
        for act, ims, box in groups:
            x = 0; rects = []
            for im in ims: atlas.paste(im, (x, y)); rects.append([x, y, im.width, im.height]); x += im.width
            key = 'run' if act == 'Gallop' else 'die'
            meta['anims'][key] = {'rects': rects, 'anchor': [anchor[0] - box[0], anchor[1] - box[1]]}; y += ims[0].height
        meta['anims']['ram'] = meta['anims']['run']
        meta['anims']['hit'] = dict(meta['anims']['run'], rects=meta['anims']['run']['rects'][:1])
        meta['anims']['fly'] = meta['anims']['die']
        atlas.quantize(colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(dst / ('enemy_qibing_%d.png' % direction), optimize=True)
        (dst / ('enemy_qibing_%d.json' % direction)).write_text(json.dumps(meta, ensure_ascii=False, separators=(',', ':')))
    total = sum((dst / ('enemy_qibing_%d.png' % d)).stat().st_size for d in range(8))
    if total <= 2_000_000: break
if total > 2_000_000: raise RuntimeError('骑兵图集超出 2MB：%d 字节' % total)
print('八方向骑兵图集', total, '字节，调色板', colors)
