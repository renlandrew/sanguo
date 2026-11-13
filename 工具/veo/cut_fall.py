"""11-13 武将倒地动作 Veo → 图集。视频在 美术/武将动作/倒地视频/<键>_fall.mp4（720×1280，96 帧：挨打、踉跄、跪倒、趴下不动）。
抠底借 cut_hunt.py 的 matte；每 4 帧取一帧共 24 帧，同一外框，缩到 SCALE，6×4 存 原型/img/gfall_<键>.webp；
原型/img/gfall.json 记每人的格子、首帧脚底锚点、首帧身高（游戏里按它缩到和站着时一样高）。
用法：python3 工具/veo/cut_fall.py [键 …]
"""
import json, sys
from pathlib import Path
import cv2, numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent; R = HERE.parents[1]; SRC = R / '美术' / '武将动作' / '倒地视频'; OUT = R / '原型' / 'img'
g = {'__file__': str(HERE / 'cut_hunt.py')}; exec((HERE / 'cut_hunt.py').read_text(encoding='utf-8').split('\nfor k in (sys.argv[1:] or MARK):')[0], g); matte = g['matte']
STEP, COLS, SCALE = 4, 6, .5
keys = sys.argv[1:] or ['guan', 'zhang', 'liu']; mp = OUT / 'gfall.json'; meta = json.loads(mp.read_text()) if mp.exists() else {}
for k in keys:
    cap = cv2.VideoCapture(str(SRC / f'{k}_fall.mp4')); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    raw = fr[::STEP]; fr = [matte(f) for f in raw]
    if k == 'liu':   # Veo 在刘备倒下时头顶冒了一大团黑烟：按有颜色或够白的像素（袍子、飘带）找出身子顶，再往上 4 像素以外的全裁掉
        for f, r in zip(fr, raw):
            hsv = cv2.cvtColor(r, cv2.COLOR_BGR2HSV); body = ((hsv[..., 1] > 60) | (hsv[..., 2] > 185)) & (f[..., 3] > 40); body = cv2.morphologyEx(body.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0
            ys = np.where(body.any(axis=1))[0]
            if len(ys): f[:max(0, ys.min() - 4), :, 3] = 0
            robe = (hsv[..., 2] > 185) & (hsv[..., 1] < 70) & (f[..., 3] > 40); ry = np.where(cv2.morphologyEx(robe.astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)).any(axis=1))[0]
            if len(ys) and len(ry):   # 贴着头和飘带的那圈烟：白袍顶往上超过身高 13% 的地方（站着时够放下头，趴下后只剩一点），又黑又没颜色的都去掉
                lim = int(ry.min() - .13 * (ys.max() - ys.min())); smoke = (hsv[..., 2] < 120) & (hsv[..., 1] < 55); smoke[max(0, lim):] = False; f[smoke, 3] = 0
                hh = ys.max() - ys.min(); col = ((hsv[..., 1] > 70) | (hsv[..., 2] > 190)) & (f[..., 3] > 40); nearc = cv2.dilate(col.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
                s2 = (hsv[..., 2] < 150) & (hsv[..., 1] < 50) & ~nearc; s2[int(ry.min() + .25 * hh):] = False; f[s2, 3] = 0   # 上半截里离袍子、飘带 4 像素以外的灰黑：烟
            dark = (hsv[..., 2] < 105) & (hsv[..., 1] < 40); lab, n = g['ndi'].label(dark & (f[..., 3] > 0))   # 身子旁边剩下的大块烟：不贴着有颜色的身子就去掉
            if n:
                near = cv2.dilate(body.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
                for i in range(1, n + 1):
                    m = lab == i
                    if m.sum() > 60 and not (m & near).any(): f[m, 3] = 0
    al = np.max([f[..., 3] for f in fr], axis=0) > 40
    ys, xs = np.where(al); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    a0 = fr[0][..., 3] > 40; y0s, x0s = np.where(a0); foot, top, cx = y0s.max() + 1, y0s.min(), (x0s.min() + x0s.max() + 1) / 2
    fw, fh = round((x1 - x0) * SCALE), round((y1 - y0) * SCALE); rows = -(-len(fr) // COLS); sheet = Image.new('RGBA', (fw * COLS, fh * rows))
    for j, f in enumerate(fr): sheet.alpha_composite(Image.fromarray(f[y0:y1, x0:x1]).resize((fw, fh), Image.Resampling.LANCZOS), ((j % COLS) * fw, (j // COLS) * fh))
    dst = OUT / f'gfall_{k}.webp'; sheet.save(dst, quality=86, method=6)
    meta[k] = {'n': len(fr), 'cols': COLS, 'fw': fw, 'fh': fh, 'ax': round((cx - x0) * SCALE, 1), 'ay': round((foot - y0) * SCALE, 1), 'h0': round((foot - top) * SCALE, 1)}
    print(k, len(fr), '帧 格', fw, fh, '图集', sheet.size, dst.stat().st_size // 1024, 'KB', '首帧脚', foot, '顶', top, meta[k])
mp.write_text(json.dumps(meta))
