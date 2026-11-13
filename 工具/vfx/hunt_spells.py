"""11-13 讨伐怪物的招数配法术（用户：「我们有那么多招数，在法术平台那个chat，要让老虎有法术啊」）。
素材来自 ../spell-store/fight（法术售卖平台那套，侧面视角：施法者在左、目标在右，前后两层逐帧 PNG + spells_db.json 里的偏移和命中点）。
这里只取「打中目标」那一段：从第一次命中前 LEAD 秒起到结束，前后层合成，围着命中点裁一块，隔一帧取一帧，排成图集
原型/img/msp_<招>.webp，原型/img/msp.json 记格子、命中点锚点、帧率、命中那一帧。
用法：python3 工具/vfx/hunt_spells.py
"""
import json, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops
R = Path(__file__).resolve().parents[2]; SRC = R.parent / 'spell-store' / 'fight'; OUT = R / '原型' / 'img'
DB = json.load(open(SRC / 'spells_db.json')); LEAD, STEP, CELL, COLS = .32, 2, 300, 6
PICK = {  # 招 → 法术
 'juling_0': 'earth_shatter', 'juling_1': 'flame_fist', 'juling_2': 'bone_grasp',
 'shanjun_0': 'white_tiger', 'shanjun_1': 'resounding_peal', 'shanjun_2': 'shadow_claws',
 'jiao_0': 'breaching_whale', 'jiao_1': 'moonpull_tide', 'jiao_2': 'geyser_chain',
 'juling_ba': 'comet_strike', 'shanjun_ba': 'cross_slash', 'jiao_ba': 'tide_pearls' }   # _ba：普攻用的小法术（用户：「不是普通的碰一下打一下，要法术效果」）
meta = {}; FADE = 90; EDGE = None
for key, sp in PICK.items():
    v = DB[sp]; W, H = v['size']; n = v['n']; fps = n / v['dur']; hit = min(h['t'] for h in v['hits']); i0 = max(0, round((hit - LEAD) * fps)); tx, ty = v['tx'], v['ty']
    x0, x1, y0, y1 = max(0, tx - 330), min(W, tx + 330), max(0, ty - 460), min(H, ty + 130); fr = []
    for i in range(i0, n, STEP):
        cv = Image.new('RGBA', (W, H))
        for L in 'bf':
            o = v[L][i] if i < len(v[L]) else None; p = SRC / 'fx' / sp / f'{L}_{i + 1:03d}.png'
            if o and p.exists(): cv.alpha_composite(Image.open(p).convert('RGBA'), (o[0], o[1]))
        c = cv.crop((x0, y0, x1, y1))
        # 11-13 用户：「很多法术还是有明显的直线边缘」——飞行的拖尾、地缝、烟超出裁切窗的地方原来被一刀切平：靠近窗边 FADE 像素内按距离渐隐（四边都做）
        if EDGE is None or EDGE.size != c.size:
            w, h = c.size; xs = np.minimum(np.arange(w), w - 1 - np.arange(w)); ys = np.minimum(np.arange(h), h - 1 - np.arange(h))
            m = np.clip(np.minimum.outer(ys, xs) / FADE, 0, 1); m = m * m * (3 - 2 * m)
            # 再压一个椭圆：方窗四边各自渐隐后，铺满整窗的法术（声浪、影爪的烟）看上去仍是一块软边的方块；按到窗心的椭圆距离 0.62–1 淡出，四角收圆，就没有直的边了
            r = np.sqrt((((np.arange(w) + .5) / w * 2 - 1) ** 2)[None, :] + (((np.arange(h) + .5) / h * 2 - 1) ** 2)[:, None]); e = np.clip((1 - r) / .38, 0, 1); e = e * e * (3 - 2 * e)
            EDGE = Image.fromarray((np.minimum(m, e) * 255).astype(np.uint8))
        c.putalpha(ImageChops.multiply(c.getchannel('A'), EDGE)); fr.append(c)
    bb = None
    for f in fr:
        b = f.getbbox()
        if b: bb = b if not bb else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
    s = min(1, CELL / max(bb[2] - bb[0], bb[3] - bb[1])); fw, fh = round((bb[2] - bb[0]) * s), round((bb[3] - bb[1]) * s); rows = -(-len(fr) // COLS)
    sheet = Image.new('RGBA', (fw * COLS, fh * rows))
    for j, f in enumerate(fr): sheet.alpha_composite(f.crop(bb).resize((fw, fh), Image.Resampling.LANCZOS), ((j % COLS) * fw, (j // COLS) * fh))
    dst = OUT / f'msp_{key}.webp'; sheet.save(dst, quality=84, method=6)
    meta[key] = {'n': len(fr), 'cols': COLS, 'fw': fw, 'fh': fh, 'ax': round((tx - x0 - bb[0]) * s, 1), 'ay': round((ty - y0 - bb[1]) * s, 1), 'fps': round(fps / STEP, 2), 'hit': round((hit * fps - i0) / STEP, 1), 'src': sp}
    print(key, sp, len(fr), '帧', (fw, fh), sheet.size, dst.stat().st_size // 1024, 'KB', meta[key])
(OUT / 'msp.json').write_text(json.dumps(meta))
