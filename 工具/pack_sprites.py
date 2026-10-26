# 把 ink_post.py 着好色的帧打成一张图集 + json（10-24）。
# 每段动作所有帧用同一个外框裁（整段对齐，不会抖），记下脚底锚点在外框里的位置。
# 渲染时镜头固定、髋部原地，镜头俯 35°，世界原点（脚底）低于画面中心 0.70 米；正交 scale 米 / 256 像素。
# json 里记 stand（人站直有多少像素 = 身高 × 256 / scale），游戏按它缩放。
# 用法：python3 pack_sprites.py <帧目录> <输出名（不带扩展名）> [h=身高米] [scale=正交米数] 动作1=键1 动作2=键2 …
#   例：… h=1.62 scale=2.8 Standard_Forward_Charge=run Attack=ram
import json, os, sys
from PIL import Image

src, outname = sys.argv[1], sys.argv[2]
kv = [a.split('=', 1) for a in sys.argv[3:]]
opt = {k: float(v) for k, v in kv if k in ('h', 'scale')}; pairs = [(k, v) for k, v in kv if k not in ('h', 'scale')]
FRAME = Image.open(os.path.join(src, next(f for f in sorted(os.listdir(src)) if f.endswith('.png')))).width      # 帧的边长（敌人 256、武将 320）
SC = opt.get('scale', 2.8); ANCHOR = (FRAME // 2, round(FRAME / 2 + .70 * FRAME / SC)); PAD = 2
sheets, meta = [], {'frame': FRAME, 'stand': round(opt.get('h', 1.62) * FRAME / SC, 1), 'anims': {}}
for act, key in pairs:
    fs = sorted(f for f in os.listdir(src) if f.startswith(act + '_') and f.endswith('.png'))
    ims = [Image.open(os.path.join(src, f)).convert('RGBA') for f in fs]
    box = None
    for im in ims:
        b = im.getbbox()
        if b: box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    box = (max(0, box[0] - PAD), max(0, box[1] - PAD), min(FRAME, box[2] + PAD), min(FRAME, box[3] + PAD))
    sheets.append((key, [im.crop(box) for im in ims], box))
# 一段动作一行
W = max(sum(c.width for c in cs) for _, cs, _ in sheets); H = sum(cs[0].height for _, cs, _ in sheets)
atlas = Image.new('RGBA', (W, H), (0, 0, 0, 0)); y = 0
for key, cs, box in sheets:
    x = 0; rects = []
    for c in cs: atlas.paste(c, (x, y)); rects.append([x, y, c.width, c.height]); x += c.width
    meta['anims'][key] = {'rects': rects, 'anchor': [ANCHOR[0] - box[0], ANCHOR[1] - box[1]]}
    y += cs[0].height
atlas.save(outname + '.png', optimize=True)
json.dump(meta, open(outname + '.json', 'w'), ensure_ascii=False)
print('图集', atlas.size, os.path.getsize(outname + '.png') // 1024, 'KB', {k: len(v['rects']) for k, v in meta['anims'].items()})
