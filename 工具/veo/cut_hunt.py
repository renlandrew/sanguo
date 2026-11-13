"""11-13 讨伐怪物 Veo 动作 → 图集。视频在 美术/讨伐/视频/<键><形态>_act.mp4（540×960，96 帧：喘一秒→蓄力→出手→收回）。
每 4 帧取一帧共 24 帧；每帧按四边的灰（巨灵第一形态首帧带一块白底，白也算底）从边上往里抠，边上软一圈；
同一条所有帧用同一个外框，缩到 SCALE，排成 6×4 存 原型/img/monv_<键><形态>.webp；
原型/img/monv_<键>.json 记每个形态的格子大小、脚底锚点、首帧身高和几个关键帧（蓄力从哪帧起、哪帧打到、哪帧收完）。
用法：python3 工具/veo/cut_hunt.py [键 …]
"""
import json, sys
from pathlib import Path
import cv2, numpy as np
from PIL import Image
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[2]; SRC = R / '美术' / '讨伐' / '视频'; OUT = R / '原型' / 'img'
STEP, COLS, SCALES = 4, 6, {'juling': .62, 'shanjun': .8, 'jiao': .9}
MARK = {  # 图集帧号：[蓄力起, 打到, 收完]；待机 = 0 … 蓄力起-1 来回
 'juling': [[7, 14, 20], [7, 13, 19], [6, 11, 19]], 'shanjun': [[5, 13, 19], [6, 15, 20], [5, 17, 21]], 'jiao': [[5, 14, 20], [5, 16, 21], [2, 16, 20]] }
def matte(f, thin=False):
    rgb = f[..., ::-1].astype(np.float32); edge = np.concatenate([rgb[:6].reshape(-1, 3), rgb[-6:].reshape(-1, 3), rgb[:, :6].reshape(-1, 3), rgb[:, -6:].reshape(-1, 3)])
    bg = np.median(edge, axis=0); d = np.sqrt(((rgb - bg) ** 2).sum(axis=2)); mn, mx = rgb.min(axis=2), rgb.max(axis=2)
    white = (mn > 222) & (mx - mn < 22); near = (d < 30) | white
    lab, _ = ndi.label(near); ids = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])); ids = ids[ids > 0]; m = np.isin(lab, ids)
    # 没连到边上的底也要抠：白底大块（只有巨灵第一形态的首帧带白底，Veo 一直留着）、被身子围住的平灰（盘身之间、手臂和身子之间；颜色很平才算，肚皮有纹理不会误伤）
    for mask, need in ((white, 400), (d < 13, 90)):
        l2, n2 = ndi.label(mask & ~m)
        if n2: sz = ndi.sum(np.ones_like(l2), l2, range(1, n2 + 1)); m |= np.isin(l2, 1 + np.where(sz > need)[0])
    soft = np.clip((d - 12) / 26, 0, 1); soft[white] = 0   # 贴着底的那圈按离底色多远给透明度（火光、电光半透明）
    grow = ndi.binary_dilation(m, iterations=3); a = np.where(m, 0, np.where(grow, soft, 1)).astype(np.float32)
    if thin: keep = ndi.binary_dilation(ndi.binary_opening(a > .15, iterations=3), iterations=4); a[~keep] = 0   # 白底那块的边线剩一圈细线：开运算去掉细的
    a = cv2.GaussianBlur(a, (0, 0), .8); a[m] = 0
    return np.dstack([rgb, a * 255]).astype(np.uint8)
for k in (sys.argv[1:] or MARK):
    meta = []
    for n in (1, 2, 3):
        cap = cv2.VideoCapture(str(SRC / f'{k}{n}_act.mp4')); fr = []
        while True:
            ok, f = cap.read()
            if not ok: break
            fr.append(f)
        fr = [matte(f, (k, n) == ('juling', 1)) for f in fr[::STEP]]; al = np.max([f[..., 3] for f in fr], axis=0) > 40
        ys, xs = np.where(al); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        a0 = fr[0][..., 3] > 40; y0s, x0s = np.where(a0); foot, top, cx = y0s.max() + 1, y0s.min(), (x0s.min() + x0s.max() + 1) / 2
        SCALE = SCALES[k]; fw, fh = round((x1 - x0) * SCALE), round((y1 - y0) * SCALE); rows = -(-len(fr) // COLS); sheet = Image.new('RGBA', (fw * COLS, fh * rows))
        for j, f in enumerate(fr): sheet.alpha_composite(Image.fromarray(f[y0:y1, x0:x1]).resize((fw, fh), Image.Resampling.LANCZOS), ((j % COLS) * fw, (j // COLS) * fh))
        dst = OUT / f'monv_{k}{n}.webp'; sheet.save(dst, quality=86, method=6)
        meta.append({'n': len(fr), 'cols': COLS, 'fw': fw, 'fh': fh, 'ax': round((cx - x0) * SCALE, 1), 'ay': round((foot - y0) * SCALE, 1), 'h0': round((foot - top) * SCALE, 1), 'mark': MARK[k][n - 1]})
        print(k, n, len(fr), '帧 格', fw, fh, '图集', sheet.size, dst.stat().st_size // 1024, 'KB', '外框', (x0, y0, x1, y1), '首帧脚', foot, '顶', top)
    (OUT / f'monv_{k}.json').write_text(json.dumps(meta))
